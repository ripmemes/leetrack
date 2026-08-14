from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class DatabaseModel:
    def __init__(self, app=None):
        self.db = db
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.db.init_app(app)

    def create_all(self, app):
        with app.app_context():
            self.db.create_all()


class Users(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column(db.String(200))
    email = db.Column(db.String(100))
    password = db.Column(db.Text, nullable=False)
    conversations = db.relationship("Conversations", backref="user", lazy=True, cascade="all, delete-orphan")


class Problems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)


class Conversations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    problem_id = db.Column(db.Integer, db.ForeignKey("problems.id"))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    messages = db.relationship("Messages", backref="conversation", lazy=True, cascade="all, delete-orphan")


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    role = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))


def build_prompt(conversation_id, user_id):
    msgs = Messages.query.filter_by(conversation_id=conversation_id, user_id=user_id).order_by(Messages.created_at).all()
    history = [
        {"role": "system", "content": (f"{conversation_id}")},
        {"role": "system", "content": "You are an algorithm tutor. Do not provide full code. Only give explanations, hints, and pseudocode."}
    ]
    for m in msgs:
        history.append({"role": m.role, "content": m.content})
    return history
