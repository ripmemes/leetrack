from flask import Flask, request, abort, redirect, url_for, jsonify, render_template 
from flask_cors import CORS
from flask_wtf import FlaskForm 
from flask_sqlalchemy import SQLAlchemy 

from argon2 import PasswordHasher
from wtforms import StringField, EmailField, PasswordField, validators , SubmitField
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os 
import jwt

from datetime import datetime, timezone , timedelta
from functools import wraps



load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url="https://api.groq.com/openai/v1")

app = Flask(__name__,template_folder='../frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
CORS(app)
app.secret_key = "random_placeholder_key"
ph = PasswordHasher()
SECRET_KEY = os.getenv("SECRET_AUTHENTIFICATION_KEY") # Configuring authentification key
app.config["SECRET_KEY"] = SECRET_KEY

# ------ 
# Setting up the database 
# ------
db = SQLAlchemy(app)
class Users(db.Model):
    id = db.Column('id',db.Integer,primary_key=True)
    username = db.Column(db.String(200))
    email = db.Column(db.String(100))
    password = db.Column(db.Text,nullable=False) # db.String is apparently  problematic ?
    conversations = db.relationship("Conversations",backref="user",lazy=True, cascade="all, delete-orphan")

# -----
# Problems : To save Problems for each user
# -----
class Problems(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String, nullable = False)
    description = db.Column(db.Text)

# -----
# TODO : make for each problem its own page
# -----

class Conversations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("users.id"))
    problem_id = db.Column(db.Integer, db.ForeignKey("problems.id"))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    messages = db.relationship("Messages",backref="conversation",lazy=True , cascade="all, delete-orphan")

    # def __init__(self,role,message):
    #     self.role = role 
    #     self.messages = message

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer,db.ForeignKey("conversations.id"),nullable=False)
    role = db.Column(db.String,nullable=False)
    content = db.Column(db.Text,nullable=False)
    created_at = db.Column(db.DateTime,default=datetime.now(timezone.utc))

# -----------------
# To build past conversation
# -----------------
def build_prompt(conversation_id):
    msgs = Messages.query.filter_by(conversation_id=conversation_id).order_by(Messages.created_at).all()
    history = [
        {"role":"system","content": (f"{conversation_id}")},
        {"role":"system","content": "You are an algorithm tutor. Do not provide full code. Only give explanations, hints, and pseudocode."}
    ]
    for m in msgs : 
        history.append({"role":m.role,"content":m.content})
    return history

with app.app_context():
    # db.drop_all() # TO REMOVE BEFORE DEPLOYING : DELETES EVERYTHING
    db.create_all()

# ------------------
# JWT Helper
# ------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token : 
            return jsonify({"error": "Token is missing!"}) , 401 # 401 : Unauthorized

        try:
            data = jwt.decode(token, SECRET_KEY,algorithms=["HS256"])
            request.user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}) , 401
        except jwt.InvalidTokenError:
            return jsonify({"error":"Invalid token"}), 401
        
        return f(*args, **kwargs)
    return decorated

@app.route("/")
@token_required
def root():
    print("user id is " ,request.user_id)
    return jsonify({"message": f"Hello user {request.user_id}, welcome!"})

@app.route("/register", methods = ['POST'])
def register():
    if not request.json : 
        return {'error' : 'Invalid request: must be json file'}, 400 

    data = request.json
    print(data)
    username = data.get('username')
    email = data.get('e-mail')
    password = data.get('password')

    if not username or not email or not password : 
        print("error here")
        return {'error' : 'All fields are required'}, 400

    hashed_pw = ph.hash(password)
    new_user = Users(username=username,email=email,password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return { 'message': 'User registered successfully'} , 201


@app.route("/login",methods = ['POST'])
def login():
    
    data = request.json
    
    user = Users.query.filter((Users.username == data['username/e-mail']) ).first()
    print(user.id)
    if not user :
        return {'error': 'User not found'} , 404
    
    try : 
        ph.verify( user.password , data['password'] )
    except Exception:
        return {'error':"Invalid Password"},401
    
    tokenContent = {
        "user_id" : user.id,
        "exp" : datetime.now(timezone.utc) + timedelta(hours=1)
    }

    token = jwt.encode(tokenContent,SECRET_KEY,algorithm="HS256")

    

    return {"token":token} , 200


@app.route("/api/daily")
# @token_required
def daily():
    # using GraphQL query
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
    try : 
        response = requests.post("https://leetcode.com/graphql",
                                    json={"query":query},
                                    headers={"Content-Type": "application/json" })
        if (not response.ok):
            raise Exception("Network response was not ok")
        return jsonify(response.json()['data']['activeDailyCodingChallengeQuestion'])
    except Exception as e : 
        print(f"Request failed : {e}")
        return jsonify({'error':'Fetching failed (backend)'}) , 404
    
@app.route("/api/contest")
def contest():
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
    try : 
        response = requests.post("https://leetcode.com/graphql",
                                 json = {"query": query},
                                 headers ={"Content-Type":"application/json"})
        if (not response.ok):
            raise Exception("Network response was not ok")
        return jsonify(response.json()['data']['upcomingContests'])
    except Exception as e :
        print(f"Request failed : {e}")
        return jsonify ({'error' : 'Fetching failed (backend)'}) , 404
    
@app.route("/api/problems")
# @token_required
def problems():
    query ="""
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
    

    skip = request.args.get("skip",default=0,type=int)
    limit = request.args.get("limit",default=15,type=int)
    difficulties = request.args.getlist("difficulties",type=str)
    languages = request.args.getlist("languages", type=str)
    topics = request.args.getlist("topics",type=str)
    if (difficulties):
        print(difficulties)
        filters["difficultyFilter"]["difficulties"] = [d.upper() for d in difficulties]
    if (languages) : 
        print(languages)
        filters["languageFilter"]["languageSlugs"] = [l.lower() for l in languages]
    if (topics):
        print(topics)
        filters["topicFilter"]["topicSlugs"] = [t.lower() for t in topics]
    
    print("skip is " , skip)

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


    try : 
        response = requests.post("https://leetcode.com/graphql", 
                                 json = {'query' : query , 'variables' : variables},
                                 headers = {'Content-Type' : 'application/json'})
        response.raise_for_status()
        data = response.json()

        if (not response.ok):
            raise Exception("Network response was not ok")

        return jsonify(data['data']['problemsetQuestionListV2'] )

    except Exception as e :
        print(f"Request failed : {e}")
        return jsonify({'error':'Fetching failed (backend)'}) , 404
    

@app.route("/api/ai",methods=['POST'])
# @token_required
def ai():
    data = request.json 
    user_id = data.get("user_id")
    problem_id = data.get("problem_id")
    message_text = data.get("message")

    id = request.args.get("convoId")

    conversation = Conversations.query.filter_by(id=id).first()
    if not conversation : 
        conversation = Conversations(user_id = user_id, problem_id=problem_id)
        db.session.add(conversation)
        db.session.commit()

    user_msg = Messages(conversation_id=conversation.id, role="user",content=message_text)
    db.session.add(user_msg)
    db.session.commit()

    prompt = build_prompt(conversation.id)

    response = client.chat.completions.create(model="llama-3.1-8b-instant",
                                            messages=prompt)

    reply = response.choices[0].message.content

    # TODO : Change this line
    if "```" in reply :
        reply = "⚠️ Debug reply: Full code is not allowed"

    ai_msg = Messages(conversation_id=conversation.id, role="assistant",content=reply)
    db.session.add(ai_msg)
    db.session.commit()

    return jsonify({"reply":reply}) , 200 

@app.route("/api/conversations")
# @token_required
def convos():
    id = request.args.get('conversation_id')

    count = db.session.query(Conversations).count()
    print("/api/conversations : Count of conversations, ", count)

    if not id :
        response = Conversations.query.all()
        result = []
        for convo in response :
            result.append({'id' : convo.id , 'created_at' : convo.created_at, 'user_id' : convo.user_id, 'problem_id'  : convo.problem_id})
        return jsonify(result) , 200
    else :
        response = Conversations.query.filter_by(id = id).first()
        if not response :
            return {'error':'Conversation not found!'}, 404

        return jsonify([{'id' : response.id ,'created_at' : response.created_at, 'user_id' : response.user_id, 'problem_id'  : response.problem_id}]), 200

@app.route("/api/messages")
# @token_required
def messages():
    id = request.args.get('conversation_id')
    if not id :
        return {"error": "conversation_id is required"}, 400

    messages = build_prompt(id)
    if not messages :
        return {"error": "Something went wrong while loading the conversation"}, 400

    return jsonify(messages[2:]), 200    

@app.delete("/api/deleteconvo")
# @token_required
def delconvo():
    
    id = request.args.get('conversation_id')
    if not id : 
        return {"error": "conversation_id is required"} , 400
    
    convo = Conversations.query.filter_by(id = id).first()

    if not convo:
        return {'error':'Conversation not found!'}, 404

    db.session.delete(convo)
    db.session.commit()
    count = db.session.query(Conversations).count()
    return {"success":"Conversation deleted successfully"} ,200




if __name__ == "__main__":
    app.run(debug=True)