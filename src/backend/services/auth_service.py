# src/backend/services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt

from models import Users, db


class AuthService:
    """Handles user registration, authentication, and token management."""

    def __init__(self, secret_key: str, password_hasher: PasswordHasher) -> None:
        """Initializes the AuthService with necessary cryptographic dependencies.

        Args:
            secret_key: Secret key used to sign and decode JWT tokens.
            password_hasher: Argon2 password hasher instance.
        """
        self.secret_key = secret_key
        self.ph = password_hasher

    def register_user(self, username: str, email: str, password: str) -> Users:
        """Registers a new user in the system.

        Args:
            username: The unique user handle.
            email: The user's email address.
            password: Raw plain-text password to hash.

        Returns:
            The created Users database model instance.

        Raises:
            ValueError: If required fields are missing or user already exists.
        """
        existing_user = Users.query.filter(
            (Users.username == username) | (Users.email == email)
        ).first()
        if existing_user:
            raise ValueError("Username or email already in use.")

        hashed_password = self.ph.hash(password)
        user = Users(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return user

    def authenticate(self, identifier: str, password: str) -> str:
        """Verifies credentials and returns a signed JWT access token.

        Args:
            identifier: Either username or email.
            password: Plain-text password.

        Returns:
            Encoded JWT token string.

        Raises:
            ValueError: When credentials do not match or user is not found.
        """
        user = Users.query.filter(
            (Users.username == identifier) | (Users.email == identifier)
        ).first()
        if not user:
            raise ValueError("User not found.")

        try:
            self.ph.verify(user.password, password)
        except VerifyMismatchError as exc:
            raise ValueError("Invalid password.") from exc

        token_content: dict[str, Any] = {
            "user_id": user.id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        return jwt.encode(token_content, self.secret_key, algorithm="HS256")

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decodes and validates a JWT token.

        Args:
            token: The raw JWT string.

        Returns:
            Dictionary containing the decoded payload.

        Raises:
            jwt.ExpiredSignatureError: If token has expired.
            jwt.InvalidTokenError: If token is malformed or invalid.
        """
        return jwt.decode(token, self.secret_key, algorithms=["HS256"])
