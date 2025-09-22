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


from datetime import datetime

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url="https://api.groq.com/openai/v1")

app = Flask(__name__,template_folder='../frontend')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Users.sqlite3'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
CORS(app)
app.secret_key = "random_placeholder_key"
ph = PasswordHasher()

# OpenAI setup

# ------ 
# Setting up the database 
# ------
db = SQLAlchemy(app)
class Users(db.Model):
    id = db.Column('id',db.Integer,primary_key=True)
    username = db.Column(db.String(200))
    email = db.Column(db.String(100))
    password = db.Column(db.String(200))
    conversations = db.relationship("Conversations",backref="user",lazy=True)

    # def __init__(self,username,email,password):
    #     self.username = username 
    #     self.email = email 
    #     self.password = ph.hash(password)
    #     print(self.password)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("Messages",backref="conversation",lazy=True)

    # def __init__(self,role,message):
    #     self.role = role 
    #     self.messages = message

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer,db.ForeignKey("conversations.id"),nullable=False)
    role = db.Column(db.String,nullable=False)
    content = db.Column(db.Text,nullable=False)
    created_at = db.Column(db.DateTime,default=datetime.utcnow)

# -----------------
# To build past conversation
# -----------------
def build_prompt(conversation_id):
    msgs = Messages.query.filter_by(conversation_id=conversation_id).order_by(Messages.created_at).all()
    history = [
        {"role":"system","content": "You are an algorithm tutor. Do not provide full code. Only give explanations, hints, and pseudocode."}
    ]
    for m in msgs : 
        history.append({"role":m.role,"content":m.content})
    return history

with app.app_context():
    db.create_all()

#------ Use WTForm ? Keep commented out for now

# class RegisterForm(FlaskForm):
#     username = StringField("username",[validators.DataRequired("Please enter your username")])
#     email = EmailField("e-mail",[validators.DataRequired("Please enter your E-Mail"), validators.Email("Please enter your E-Mail")])
#     password = PasswordField("password",[validators.DataRequired("Please enter your password")])

#     submit = SubmitField("Submit")

# Hashing Function to store passwords

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

    # no need for try block like in sqlite ?
    new_user = Users(username,email,password)
    db.session.add(new_user)
    db.session.commit()
    return { 'message': 'User registered successfully'} , 201


@app.route("/login",methods = ['POST'])
def login():
    data = request.json


    user = Users.query.filter((Users.username == data['username/e-mail']) ).first()

    if not user :
        return {'error': 'User not found'} , 404

    try : 
        ph.verify( user.password , data['password'] )
    except Exception:
        return {'error':"Invalid Password"},404

    return redirect("http://localhost:3000/")


@app.route("/api/daily")
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
def problems():
    query = """
        query problemsetQuestionListV2($limit: Int, $skip: Int) {
        problemsetQuestionListV2(limit: $limit, skip: $skip) {
            questions {
            questionFrontendId
            title
            difficulty
            }
            hasMore
        }
        }
    """

    skip = request.args.get("skip",default=0,type=int)
    limit = request.args.get("limit",default=15,type=int)
    print("skip is " , skip)

    variables = {
        "categorySlug": "all-code-essentials",
        "filters": {},
        "filtersV2": {},
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

        # print(data)
        if (not response.ok):
            raise Exception("Network response was not ok")

        return jsonify(data['data']['problemsetQuestionListV2'] )

    except Exception as e :
        print(f"Request failed : {e}")
        return jsonify({'error':'Fetching failed (backend)'}) , 404

@app.route("/api/ai",methods=['POST'])
def ai():
    data = request.json 
    user_id = data.get("user_id")
    problem_id = data.get("problem_id")
    message_text = data.get("message")

    conversation = Conversations.query.filter_by(user_id=user_id,problem_id=problem_id).first()
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
def convos():
    id = request.args.get('conversation_id')

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
def messages():
    id = request.args.get('conversation_id')
    if not id :
        return {"error": "conversation_id is required"}, 400

    messages = build_prompt(id)
    if not messages :
        return {"error": "Something went wrong while loading the conversation"}, 400

    return jsonify(messages), 200                          




if __name__ == "__main__":
    app.run(debug=True)