from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
import requests
from flask import jsonify, request

try:
    from .models import Conversations, Messages, Users, build_prompt
except ImportError:
    from models import Conversations, Messages, Users, build_prompt


class Routes:
    def __init__(self, app, db, ph, client, secret_key, cache=None):
        self.app = app
        self.db = db
        self.ph = ph
        self.client = client
        self.secret_key = secret_key
        self.cache = cache
        self.register_routes()

    def token_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if "Authorization" in request.headers:
                auth_header = request.headers["Authorization"]
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
            if not token:
                return jsonify({"error": "Token is missing!"}), 401

            try:
                data = jwt.decode(token, self.secret_key, algorithms=["HS256"])
                request.user_id = data["user_id"]
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            return f(*args, **kwargs)

        return decorated

    def _invalidate_conversation_cache(self, user_id, conversation_id=None):
        if self.cache is None:
            return
        if conversation_id is not None:
            self.cache.delete(f"conversation:{conversation_id}")
        self.cache.delete(f"conversations:user:{user_id}")
        self.cache.delete(f"messages:conversation:{conversation_id}:user:{user_id}")

    def register_routes(self):
        @self.app.route("/")
        @self.token_required
        def root():
            print("user id is ", request.user_id)
            return jsonify({"message": f"Hello user {request.user_id}, welcome!"})

        @self.app.route("/userId")
        @self.token_required
        def userId():
            return jsonify({"userId": request.user_id})

        @self.app.route("/register", methods=['POST'])
        def register():
            if not request.json:
                return {'error': 'Invalid request: must be json file'}, 400

            data = request.json
            print(data)
            username = data.get('username')
            email = data.get('e-mail')
            password = data.get('password')

            if not username or not email or not password:
                print("error here")
                return {'error': 'All fields are required'}, 400

            hashed_pw = self.ph.hash(password)
            new_user = Users(username=username, email=email, password=hashed_pw)
            self.db.session.add(new_user)
            self.db.session.commit()
            return {'message': 'User registered successfully'}, 201

        @self.app.route("/login", methods=['POST'])
        def login():
            data = request.json

            user = Users.query.filter((Users.username == data['username/e-mail'])).first()
            print(user.id)
            if not user:
                return {'error': 'User not found'}, 404

            try:
                self.ph.verify(user.password, data['password'])
            except Exception:
                return {'error': "Invalid Password"}, 401

            tokenContent = {
                "user_id": user.id,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1)
            }

            token = jwt.encode(tokenContent, self.secret_key, algorithm="HS256")
            return {"token": token}, 200

        @self.app.route("/api/daily")
        def daily():
            cache_key = "leetcode:daily"
            cached = self.cache.get_json(cache_key) if self.cache is not None else None
            if cached is not None:
                return jsonify(cached)

            query = """query questionOfToday {
                activeDailyCodingChallengeQuestion{
                    date
                    link
                    question{
                        title
                    }
                }
            }
            """
            try:
                response = requests.post("https://leetcode.com/graphql",
                                         json={"query": query},
                                         headers={"Content-Type": "application/json"})
                if (not response.ok):
                    raise Exception("Network response was not ok")
                payload = response.json()['data']['activeDailyCodingChallengeQuestion']
                if self.cache is not None:
                    self.cache.set_json(cache_key, payload, ttl=600)
                return jsonify(payload)
            except Exception as e:
                print(f"Request failed : {e}")
                return jsonify({'error': 'Fetching failed (backend)'}) , 404

        @self.app.route("/api/contest")
        def contest():
            cache_key = "leetcode:contest"
            cached = self.cache.get_json(cache_key) if self.cache is not None else None
            if cached is not None:
                return jsonify(cached)

            query = """query upcomingContests {
            upcomingContests {
             title
             titleSlug
              startTime
              duration
              __typename
              }
             }
             """
            try:
                response = requests.post("https://leetcode.com/graphql",
                                         json={"query": query},
                                         headers={"Content-Type": "application/json"})
                if (not response.ok):
                    raise Exception("Network response was not ok")
                payload = response.json()['data']['upcomingContests']
                if self.cache is not None:
                    self.cache.set_json(cache_key, payload, ttl=600)
                return jsonify(payload)
            except Exception as e:
                print(f"Request failed : {e}")
                return jsonify({'error': 'Fetching failed (backend)'}) , 404

        @self.app.route("/api/problems")
        def problems():
            query = """
                query problemsetQuestionListV2($filters: QuestionFilterInput, $limit: Int, $skip: Int, $sortBy: QuestionSortByInput, $categorySlug: String, $searchKeyword: String) {
                  problemsetQuestionListV2(
                    filters: $filters
                    limit: $limit
                    skip: $skip
                    sortBy: $sortBy
                    categorySlug: $categorySlug
                    searchKeyword: $searchKeyword
                  ) {
                    questions {
                      questionFrontendId
                      title
                      difficulty
                    }
                    hasMore
                  }
                }
            """

            filters = {
                "filterCombineType": "ALL",
                "difficultyFilter": {"difficulties": [], "operator": "IS"},
                "languageFilter": {"languageSlugs": [], "operator": "IS"},
                "topicFilter": {"topicSlugs": [], "operator": "IS"},
            }

            skip = request.args.get("skip", default=0, type=int)
            limit = request.args.get("limit", default=15, type=int)
            difficulties = request.args.getlist("difficulties", type=str)
            languages = request.args.getlist("languages", type=str)
            topics = request.args.getlist("topics", type=str)
            if (difficulties):
                print(difficulties)
                filters["difficultyFilter"]["difficulties"] = [d.upper() for d in difficulties]
            if (languages):
                print(languages)
                filters["languageFilter"]["languageSlugs"] = [l.lower() for l in languages]
            if (topics):
                print(topics)
                filters["topicFilter"]["topicSlugs"] = [t.lower() for t in topics]

            print("skip is ", skip)

            variables = {
                "categorySlug": "all-code-essentials",
                "filters": filters,
                "filtersV2": filters,
                "limit": limit,
                "skip": skip,
                "searchKeyword": "",
                "sortBy": {
                    "sortField": "CUSTOM",
                    "sortOrder": "ASCENDING"
                }
            }

            cache_key = f"leetcode:problems:skip={skip}:limit={limit}:difficulties={','.join(difficulties)}:languages={','.join(languages)}:topics={','.join(topics)}"
            cached = self.cache.get_json(cache_key) if self.cache is not None else None
            if cached is not None:
                return jsonify(cached)

            try:
                response = requests.post("https://leetcode.com/graphql",
                                         json={'query': query, 'variables': variables},
                                         headers={'Content-Type': 'application/json'})
                response.raise_for_status()
                data = response.json()

                if (not response.ok):
                    raise Exception("Network response was not ok")

                payload = data['data']['problemsetQuestionListV2']
                if self.cache is not None:
                    self.cache.set_json(cache_key, payload, ttl=600)
                return jsonify(payload)

            except Exception as e:
                print(f"Request failed : {e}")
                return jsonify({'error': 'Fetching failed (backend)'}) , 404

        @self.app.route("/api/ai", methods=['POST'])
        def ai():
            data = request.json
            user_id = data.get("user_id")
            problem_id = data.get("problem_id")
            message_text = data.get("message")

            id = request.args.get("convoId")

            conversation = Conversations.query.filter_by(id=id, user_id=user_id).first()
            if not conversation:
                conversation = Conversations(user_id=user_id, problem_id=problem_id)
                self.db.session.add(conversation)
                self.db.session.flush() # else conversation.id will be None. and we need to create Message object and in build_prompt

            user_msg = Messages(conversation_id=conversation.id, user_id=user_id, role="user", content=message_text)
            self.db.session.add(user_msg)
    

            prompt = build_prompt(conversation.id, user_id)

            response = self.client.chat.completions.create(model="groq/compound-mini",
                                                          messages=prompt)

            reply = response.choices[0].message.content

            if "```" in reply:
                reply = "⚠️ Debug reply: Full code is not allowed"

            ai_msg = Messages(conversation_id=conversation.id, user_id=user_id, role="assistant", content=reply)
            self.db.session.add(ai_msg)
            self.db.session.commit()

            if self.cache is not None:
                self.cache.delete(f"messages:conversation:{conversation.id}:user:{user_id}")
                self.cache.delete(f"conversation:{conversation.id}")
                self.cache.delete(f"conversations:user:{user_id}")

            return jsonify({"reply": reply}), 200

        @self.app.route("/api/conversations")
        def convos():
            print("here?")
            id = request.args.get('conversation_id')
            user_id = request.args.get('user_id')

            if not user_id:
                return {"error": "user_id is required"}, 400

            count = self.db.session.query(Conversations).count()
            print("/api/conversations : Count of conversations, ", count)

            if not id:
                cache_key = f"conversations:user:{user_id}"
                cached = self.cache.get_json(cache_key) if self.cache is not None else None
                if cached is not None:
                    return jsonify(cached), 200

                response = Conversations.query.filter_by(user_id=user_id)
                result = []
                for convo in response:
                    result.append({'id': convo.id, 'created_at': convo.created_at, 'user_id': convo.user_id, 'problem_id': convo.problem_id})
                if self.cache is not None:
                    self.cache.set_json(cache_key, result, ttl=600)
                return jsonify(result), 200
            else:
                cache_key = f"conversation:{id}"
                cached = self.cache.get_json(cache_key) if self.cache is not None else None
                if cached is not None:
                    return jsonify(cached), 200

                response = Conversations.query.filter_by(id=id).first()
                if not response:
                    return {'error': 'Conversation not found!'}, 404
                payload = [{'id': response.id, 'created_at': response.created_at, 'user_id': response.user_id, 'problem_id': response.problem_id}]
                if self.cache is not None:
                    self.cache.set_json(cache_key, payload, ttl=600)
                return jsonify(payload), 200

        @self.app.route("/api/messages")
        def messages():
            id = request.args.get('conversation_id')
            user_id = request.args.get('user_id')
            if not id:
                return {"error": "conversation_id is required"}, 400
            if not user_id:
                return {"error": "user_id is required"}, 400

            cache_key = f"messages:conversation:{id}:user:{user_id}"
            cached = self.cache.get_json(cache_key) if self.cache is not None else None
            if cached is not None:
                return jsonify(cached), 200

            messages_list = build_prompt(id, user_id)
            if not messages_list:
                return {"error": "Something went wrong while loading the conversation"}, 400

            payload = messages_list[2:]
            if self.cache is not None:
                self.cache.set_json(cache_key, payload, ttl=600)
            return jsonify(payload), 200

        @self.app.delete("/api/deleteconvo")
        def delconvo():
            id = request.args.get('conversation_id')
            user_id = request.args.get('user_id')
            if not id:
                return {"error": "conversation_id is required"}, 400

            if not user_id:
                return {"error": "user_id is required"}, 400

            convo = Conversations.query.filter_by(id=id, user_id=user_id).first()

            if not convo:
                return {'error': 'Conversation not found!'}, 404

            self.db.session.delete(convo)
            self.db.session.commit()

            if self.cache is not None:
                self._invalidate_conversation_cache(user_id, id)

            return {'message': 'Conversation deleted successfully'}, 200
