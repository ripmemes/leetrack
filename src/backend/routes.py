from functools import wraps
from typing import Any, Callable
from flask import Flask, jsonify, request
import jwt

from services.ai_service import AiTutorService
from services.auth_service import AuthService
from services.conversation_service import ConversationService
from services.leetcode_service import LeetCodeService


class Routes:
    """Registers application HTTP endpoints with injected domain services."""

    def __init__(
        self,
        app: Flask,
        auth_service: AuthService,
        leetcode_service: LeetCodeService,
        conversation_service: ConversationService,
        ai_service: AiTutorService,
    ) -> None:
        """Injects domain services and registers routes."""
        self.app = app
        self.auth_service = auth_service
        self.leetcode_service = leetcode_service
        self.conversation_service = conversation_service
        self.ai_service = ai_service
        self._register_routes()

    def token_required(self, f: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator ensuring the request carries a valid Bearer token."""
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Token is missing!"}), 401

            token = auth_header.split(" ")[1]
            try:
                payload = self.auth_service.decode_token(token)
                request.user_id = payload["user_id"]
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            return f(*args, **kwargs)

        return decorated

    def _register_routes(self) -> None:
        @self.app.route("/register", methods=["POST"])
        def register() -> tuple[dict[str, str], int]:
            data = request.get_json(silent=True) or {}
            username = data.get("username")
            email = data.get("e-mail")
            password = data.get("password")

            if not username or not email or not password:
                return {"error": "All fields are required"}, 400

            try:
                self.auth_service.register_user(username, email, password)
                return {"message": "User registered successfully"}, 201
            except ValueError as e:
                return {"error": str(e)}, 400

        @self.app.route("/login", methods=["POST"])
        def login() -> tuple[dict[str, str], int]:
            data = request.get_json(silent=True) or {}
            identifier = data.get("username/e-mail")
            password = data.get("password")

            if not identifier or not password:
                return {"error": "Missing credentials"}, 400

            try:
                token = self.auth_service.authenticate(identifier, password)
                return {"token": token}, 200
            except ValueError as e:
                return {"error": str(e)}, 401
        
        @self.app.route("/")
        @self.token_required
        def root() -> Any:
            """Validates authentication token on app load."""
            return jsonify({"message": f"Hello user {request.user_id}, welcome!"})
        @self.app.route("/userId")
        @self.token_required
        def user_id() -> Any:
            """Returns the authenticated user ID."""
            return jsonify({"userId": request.user_id})
        @self.app.route("/api/contest")
        def contest() -> Any:
            """Fetches upcoming LeetCode contests."""
            try:
                data = self.leetcode_service.get_upcoming_contests()
                return jsonify(data)
            except RuntimeError:
                return jsonify({"error": "Fetching contests failed"}), 404
        @self.app.route("/api/conversations")
        def conversations() -> tuple[Any, int]:
            """Fetches user conversations or a single conversation."""
            user_id = request.args.get("user_id", type=int)
            if not user_id:
                return jsonify({"error": "user_id is required"}), 400
            data = self.conversation_service.get_user_conversations(user_id)
            return jsonify(data), 200
        @self.app.route("/api/messages")
        def messages() -> tuple[Any, int]:
            """Fetches message history for a given conversation."""
            convo_id = request.args.get("conversation_id", type=int)
            user_id = request.args.get("user_id", type=int)
            if not convo_id or not user_id:
                return jsonify({"error": "conversation_id and user_id are required"}), 400
            data = self.conversation_service.get_conversation_messages(convo_id, user_id)
            return jsonify(data), 200

        @self.app.route("/api/daily")
        def daily() -> Any:
            try:
                data = self.leetcode_service.get_daily_challenge()
                return jsonify(data)
            except RuntimeError:
                return jsonify({"error": "Fetching daily challenge failed"}), 404

        @self.app.route("/api/problems")
        def problems() -> Any:
            skip = request.args.get("skip", default=0, type=int)
            limit = request.args.get("limit", default=15, type=int)
            difficulties = request.args.getlist("difficulties", type=str)
            languages = request.args.getlist("languages", type=str)
            topics = request.args.getlist("topics", type=str)

            try:
                data = self.leetcode_service.get_problems(
                    skip=skip,
                    limit=limit,
                    difficulties=difficulties,
                    languages=languages,
                    topics=topics,
                )
                return jsonify(data)
            except Exception:
                return jsonify({"error": "Fetching problems failed"}), 404

        @self.app.route("/api/ai", methods=["POST"])
        def ai() -> tuple[Any, int]:
            data = request.get_json(silent=True) or {}
            user_id = data.get("user_id")
            problem_id = data.get("problem_id")
            message = data.get("message")
            convo_id = request.args.get("convoId", type=int)

            if not user_id or not message:
                return jsonify({"error": "user_id and message are required"}), 400

            reply, convo_id = self.ai_service.chat(
                user_id=user_id,
                message_text=message,
                problem_id=problem_id,
                conversation_id=convo_id,
            )
            return jsonify({"reply": reply, "conversation_id": convo_id}), 200

        @self.app.delete("/api/deleteconvo")
        def delconvo() -> tuple[dict[str, str], int]:
            conversation_id = request.args.get("conversation_id", type=int)
            user_id = request.args.get("user_id", type=int)

            if not conversation_id or not user_id:
                return {"error": "conversation_id and user_id are required"}, 400

            deleted = self.conversation_service.delete_conversation(conversation_id, user_id)
            if not deleted:
                return {"error": "Conversation not found!"}, 404

            return {"message": "Conversation deleted successfully"}, 200
