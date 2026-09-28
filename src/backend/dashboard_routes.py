"""Dashboard HTTP endpoints.

Registered under /api/dashboard/* on the existing Flask app.

Public vs. private is cleanly separated:
  /api/dashboard/public/*   — only requires a LeetCode username
  /api/dashboard/private/*  — additionally requires X-LC-Session header
  /api/dashboard/account/*  — modifies the linked handle stored in our DB
"""
from __future__ import annotations

from typing import Any, Callable

import jwt
from flask import Flask, jsonify, request

from models import Users, db
from services.auth_service import AuthService
from services.dashboard.dashboard_service import DashboardService


class DashboardRoutes:
    """Registers /api/dashboard/* routes on the provided Flask app."""

    def __init__(
        self,
        app: Flask,
        auth_service: AuthService,
        dashboard_service: DashboardService,
    ) -> None:
        self.app = app
        self.auth_service = auth_service
        self.dashboard_service = dashboard_service
        self._register_routes()

    # ── auth decorator ───────────────────────────────────────────────────────

    def _token_required(self, f: Callable[..., Any]) -> Callable[..., Any]:
        from functools import wraps

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

    def _get_linked_handle(self) -> str | None:
        """Returns the LeetCode handle linked to the current authenticated user."""
        user = db.session.get(Users, request.user_id)
        return user.leetcode_handle if user else None

    # ── routes ───────────────────────────────────────────────────────────────

    def _register_routes(self) -> None:

        # ── account (handle linking) ──────────────────────────────────────

        @self.app.route("/api/dashboard/account/link", methods=["POST"])
        @self._token_required
        def link_handle() -> tuple[Any, int]:
            """Links a LeetCode username to the current user (only the string is stored)."""
            body = request.get_json(silent=True) or {}
            handle = (body.get("handle") or "").strip()
            if not handle:
                return jsonify({"error": "handle is required"}), 400

            user = db.session.get(Users, request.user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            user.leetcode_handle = handle
            db.session.commit()
            return jsonify({"message": f"Linked to {handle}"}), 200

        @self.app.route("/api/dashboard/account/unlink", methods=["POST"])
        @self._token_required
        def unlink_handle() -> tuple[Any, int]:
            """Removes the linked LeetCode username."""
            user = db.session.get(Users, request.user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            handle = user.leetcode_handle
            user.leetcode_handle = None
            db.session.commit()
            if handle:
                self.dashboard_service.invalidate_profile(handle)
            return jsonify({"message": "Handle unlinked"}), 200

        @self.app.route("/api/dashboard/account/status")
        @self._token_required
        def handle_status() -> tuple[Any, int]:
            """Returns the currently linked LeetCode handle (or null)."""
            handle = self._get_linked_handle()
            return jsonify({"handle": handle}), 200

        # ── public endpoints ──────────────────────────────────────────────

        @self.app.route("/api/dashboard/public/profile")
        @self._token_required
        def public_profile() -> tuple[Any, int]:
            """Returns public profile stats for the linked LC handle."""
            handle = self._get_linked_handle()
            if not handle:
                return jsonify({"error": "No LeetCode handle linked"}), 400
            try:
                data = self.dashboard_service.get_public_profile(handle)
                return jsonify(data), 200
            except RuntimeError as exc:
                return jsonify({"error": str(exc)}), 502

        @self.app.route("/api/dashboard/public/recommendations")
        @self._token_required
        def public_recommendations() -> tuple[Any, int]:
            """Returns problem recommendations based on public profile.

            Query params:
              mode: 'interview' (default) | 'weakness'
              top_n: integer (default 5)
            """
            handle = self._get_linked_handle()
            if not handle:
                return jsonify({"error": "No LeetCode handle linked"}), 400
            mode = request.args.get("mode", "interview")
            if mode not in ("interview", "weakness"):
                return jsonify({"error": "mode must be 'interview' or 'weakness'"}), 400
            top_n = request.args.get("top_n", default=5, type=int)
            try:
                data = self.dashboard_service.get_public_recommendations(handle, mode=mode, top_n=top_n)  # type: ignore[arg-type]
                return jsonify(data), 200
            except RuntimeError as exc:
                return jsonify({"error": str(exc)}), 502

        @self.app.route("/api/dashboard/public/sync", methods=["POST"])
        @self._token_required
        def public_sync() -> tuple[Any, int]:
            """Invalidates cached profile and returns fresh data."""
            handle = self._get_linked_handle()
            if not handle:
                return jsonify({"error": "No LeetCode handle linked"}), 400
            self.dashboard_service.invalidate_profile(handle)
            try:
                data = self.dashboard_service.get_public_profile(handle)
                return jsonify(data), 200
            except RuntimeError as exc:
                return jsonify({"error": str(exc)}), 502

        # ── private endpoints (require X-LC-Session header) ───────────────

        @self.app.route("/api/dashboard/private/profile")
        @self._token_required
        def private_profile() -> tuple[Any, int]:
            """Returns extended profile using the provided session cookie.

            Requires header: X-LC-Session: <LEETCODE_SESSION value>
            The cookie is NEVER stored — used only for the upstream GraphQL call.
            """
            session_cookie = request.headers.get("X-LC-Session", "").strip()
            if not session_cookie:
                return jsonify({"error": "X-LC-Session header is required for private mode"}), 400
            handle = self._get_linked_handle()
            if not handle:
                return jsonify({"error": "No LeetCode handle linked"}), 400
            try:
                data = self.dashboard_service.get_private_profile(handle, session_cookie)
                return jsonify(data), 200
            except RuntimeError as exc:
                return jsonify({"error": str(exc)}), 502

        @self.app.route("/api/dashboard/private/recommendations")
        @self._token_required
        def private_recommendations() -> tuple[Any, int]:
            """Returns recommendations using extended private profile data.

            Requires header: X-LC-Session: <LEETCODE_SESSION value>
            Query params: mode ('interview'|'weakness'), top_n (int).
            """
            session_cookie = request.headers.get("X-LC-Session", "").strip()
            if not session_cookie:
                return jsonify({"error": "X-LC-Session header is required for private mode"}), 400
            handle = self._get_linked_handle()
            if not handle:
                return jsonify({"error": "No LeetCode handle linked"}), 400
            mode = request.args.get("mode", "interview")
            if mode not in ("interview", "weakness"):
                return jsonify({"error": "mode must be 'interview' or 'weakness'"}), 400
            top_n = request.args.get("top_n", default=5, type=int)
            try:
                data = self.dashboard_service.get_private_recommendations(
                    handle, session_cookie, mode=mode, top_n=top_n  # type: ignore[arg-type]
                )
                return jsonify(data), 200
            except RuntimeError as exc:
                return jsonify({"error": str(exc)}), 502
