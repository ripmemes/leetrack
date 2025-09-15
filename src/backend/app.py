from flask import Flask, request, abort, redirect, url_for, jsonify, render_template 
from flask_cors import CORS
import os
import json
from flask_wtf import FlaskForm 
from flask_sqlalchemy import SQLAlchemy 
from wtforms import StringField, EmailField, PasswordField, validators , SubmitField
import requests


app = Flask(__name__,template_folder='../frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
CORS(app)
app.secret_key = "random_placeholder_key"

#------ Setting up the database 
db = SQLAlchemy(app)
class users(db.Model):
    id = db.Column('user_id',db.Integer,primary_key=True)
    username = db.Column(db.String(200))
    email = db.Column(db.String(100))
    password = db.Column(db.String(50))

    def __init__(self,username,email,password):
        self.username = username 
        self.email = email 
        # -------- Preliminary, actual secure authentification in the next update
        self.password = password
with app.app_context():
    db.create_all()

#------ Use WTForm ? Keep commented out for now

# class RegisterForm(FlaskForm):
#     username = StringField("username",[validators.DataRequired("Please enter your username")])
#     email = EmailField("e-mail",[validators.DataRequired("Please enter your E-Mail"), validators.Email("Please enter your E-Mail")])
#     password = PasswordField("password",[validators.DataRequired("Please enter your password")])

#     submit = SubmitField("Submit")


@app.route("/register", methods = ['POST'])
def register():
    if not request.json : 
        return {'error' : 'Invalid request: must be json file'}, 400 \
    
    data = {k.lower(): v for k,v in request.json.items() }

    username = data.get('username')
    email = data.get('e-mail')
    password = data.get('password')

    if not username or not email or not password : 
        return {'error' : 'All fields are required'}, 400
    
    # no need for try block like in sqlite ?
    new_user = users(username,email,password)
    db.session.add(new_user)
    db.session.commit()
    return { 'message': 'User registered successfully'} , 201

@app.route("/login",methods = ['POST'])
def login():
    data = {k.lower() : v for k,v in request.json.items()}

    user = users.query.filter( (users.username == data['username/e-mail']) & (users.password == data['password']) ).first()

    if not user :
        return {'error': 'User not found'} , 404
    
    return {'message' : f'Welcome {user.username} !'}


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
        return jsonify(response.json()["data"]["activeDailyCodingChallengeQuestion"])
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
        return jsonify(response.json()["data"]["upcomingContests"])
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
    

if __name__ == "__main__":
    app.run(debug=True)