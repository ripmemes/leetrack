from dotenv import load_dotenv
import os

from flask import Flask
from flask_cors import CORS
from argon2 import PasswordHasher
from openai import OpenAI
from services.ai_service import AiTutorService
from services.auth_service import AuthService
from services.conversation_service import ConversationService
from services.leetcode_service import LeetCodeService


try: 
    from .cache import RedisCache
    from .models import DatabaseModel, db
    from .routes import Routes
except ImportError:
    from cache import RedisCache
    from models import DatabaseModel, db
    from routes import Routes


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.groq.com/openai/v1")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
CORS(app)
ph = PasswordHasher()
SECRET_KEY = os.getenv("SECRET_AUTHENTIFICATION_KEY")
app.config["SECRET_KEY"] = SECRET_KEY

database = DatabaseModel(app)
database.create_all(app)

cache = RedisCache(url=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
auth_service = AuthService(secret_key=SECRET_KEY, password_hasher=ph)
leetcode_service = LeetCodeService(cache=cache)
conversation_service = ConversationService(cache=cache)
ai_service = AiTutorService(client=client, conversation_service=conversation_service)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

Routes(app, auth_service, leetcode_service, conversation_service, ai_service)


if __name__ == "__main__":
    app.run(debug=True)