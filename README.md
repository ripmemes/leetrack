# Leetrack (WIP)

A LeetCode progress tracker and AI-assisted tutor built with Flask, React, and Tailwind CSS.

---

## Quick Setup

### 1. Backend
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start Redis (required for caching)
docker-compose up -d

# Start backend server (runs on http://localhost:5000)
python3 src/backend/app.py
```

Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_groq_or_openai_api_key
SECRET_AUTHENTIFICATION_KEY=your_jwt_secret
DATABASE_URL=sqlite:///Users.sqlite3
REDIS_URL=redis://localhost:6379/0
```

### 2. Frontend
```bash
npm install
npm start  # Runs on http://localhost:3000
```

---

## Key Features

- **Authentication**: Registration and login endpoints using Argon2 hashing and JWT access tokens.
- **LeetCode Integration**: Fetches daily challenges, upcoming contests, and problem lists directly via LeetCode GraphQL endpoints.
- **Analytics Dashboard**: 
  - Tracks solved problem distribution (Easy, Medium, Hard).
  - Displays topic proficiency breakdowns and a yearly submission activity heatmap.
  - Generates personalized problem recommendations tailored for new users, inactive users, and active practice in **Interview** or **Weakness** modes.
  - Supports optional private mode via Chrome extension session cookie injection.
- **AI Algorithm Tutor**: Context-aware assistant providing targeted hints and guidance without leaking full code solutions.
- **Caching**: Multi-level Redis caching for GraphQL query results, user profile data, and conversation history.

---

## API Summary

### Authentication & Core
- `POST /register` — Register a new user (`username`, `e-mail`, `password`)
- `POST /login` — Authenticate and receive a JWT token (`username/e-mail`, `password`)
- `GET /userId` — Retrieve current user ID *(Requires Bearer token)*

### LeetCode & Public Data
- `GET /api/daily` — Fetch LeetCode daily challenge
- `GET /api/contest` — Fetch upcoming contests
- `GET /api/problems` — Filterable problem list (`skip`, `limit`, `difficulties`, `languages`, `topics`)

### Dashboard
- `POST /api/dashboard/account/link` — Link LeetCode handle *(Requires Bearer token)*
- `POST /api/dashboard/account/unlink` — Unlink LeetCode handle *(Requires Bearer token)*
- `GET /api/dashboard/account/status` — Get handle link status *(Requires Bearer token)*
- `GET /api/dashboard/public/profile` — Get public stats and activity *(Requires Bearer token)*
- `GET /api/dashboard/public/recommendations` — Fetch recommendations (`mode=interview|weakness`) *(Requires Bearer token)*
- `POST /api/dashboard/public/sync` — Refresh profile cache *(Requires Bearer token)*
- `GET /api/dashboard/private/profile` — Get private profile *(Requires Bearer token & `X-LC-Session` header)*
- `GET /api/dashboard/private/recommendations` — Fetch private recommendations *(Requires Bearer token & `X-LC-Session` header)*

### AI Assistant
- `POST /api/ai?convoId=<id>` — Send message to AI assistant (`user_id`, `problem_id`, `message`)
- `GET /api/conversations?user_id=<id>` — List active user conversations
- `GET /api/messages?conversation_id=<id>&user_id=<id>` — Retrieve conversation history
- `DELETE /api/deleteconvo?conversation_id=<id>&user_id=<id>` — Delete a conversation
