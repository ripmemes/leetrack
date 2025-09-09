from flask import Flask, request, abort, redirect, url_for, jsonify, render_template 
from flask_cors import CORS
import os
import json
from flask_wtf import FlaskForm 
from flask_sqlalchemy import SQLAlchemy 
from wtforms import StringField, EmailField, PasswordField, validators , SubmitField


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




if __name__ == "__main__":
    app.run(debug=True)