from dotenv import load_dotenv
import os

from flask import Flask
from flask_cors import CORS
from argon2 import PasswordHasher
from openai import OpenAI

try:
    from .models import DatabaseModel, db
    from .routes import Routes
except ImportError:
    from models import DatabaseModel, db
    from routes import Routes


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.groq.com/openai/v1")

app = Flask(__name__, template_folder='../frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
CORS(app)
app.secret_key = "random_placeholder_key"
ph = PasswordHasher()
SECRET_KEY = os.getenv("SECRET_AUTHENTIFICATION_KEY")
app.config["SECRET_KEY"] = SECRET_KEY

database = DatabaseModel(app)
database.create_all(app)

Routes(app, db, ph, client, SECRET_KEY)


if __name__ == "__main__":
    app.run(debug=True)