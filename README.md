# Leetrack

A simple LeetCode progress tracker , **Flask** backend + **React** frontend.  
Work-in-progress: built to learn full-stack patterns, track practice, and prototype an AI-assisted algorithm tutor.

---

## 🔧 Quick setup

> **Frontend**
```bash
cd frontend
npm install
npm start
# Frontend runs on http://localhost:3000 by default
```

> **Backend**
```bash
# create & activate virtualenv (example for Linux/macOS)
python3 -m venv .venv
source .venv/bin/activate

# (Windows - PowerShell)
# .venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt

# create a .env file in backend (see example below), then start:
python3 src/backend/app.py
# Backend runs on http://localhost:5000 by default
```

**Example `.env`** (place in `backend/` or where `app.py` reads it):
```
OPENAI_API_KEY=your_openai_or_groq_api_key_here
SECRET_AUTHENTIFICATION_KEY=your_jwt_secret_here
DATABASE_URL=sqlite:///leetrack.db
```

---

## ✨ Current features (backend & frontend)

- **Authentication**
  - Registration & login endpoints using **Argon2** (argon2-cffi) for password hashing.
  - JWT-based tokens issued on login (stored in localStorage by the frontend for now).
- **LeetCode integration**
  - Fetches daily challenge, upcoming contests and problem lists using LeetCode GraphQL.
- **Problems UI**
  - Infinite scroll / lazy loading of problems and client-side filters (difficulty / language / topic).
- **AI tutoring (prototype)**
  - Conversations are stored per-user; backend forwards conversation history to an LLM (via OpenAI/Groq client) and stores assistant replies.
  - Notes: assistant replies are post-processed to avoid returning full code blocks, DON'T FORGET to add your openai or groq api key in .env.
- **Basic React UI**
  - Pages for home, login, register; components for contests, daily challenge, problem list and AI chat. Tailwind used for styling.

---

## 🧭 API endpoints (summary)

- `POST /register` — create user (expects JSON: `username`, `e-mail`, `password`)
- `POST /login` — log in (returns JWT token)
- `GET /userId` — returns `userId` for the token
- `GET /api/daily` — LeetCode daily challenge
- `GET /api/contest` — upcoming LeetCode contests
- `GET /api/problems` — problem list (supports `skip`, `limit`, `difficulties`, `languages`, `topics`)
- `POST /api/ai?convoId=<id>` — send user message to the AI assistant (body: `user_id`, `problem_id`, `message`)
- `GET /api/conversations?user_id=<id>` — list user conversations
- `GET /api/messages?conversation_id=<id>&user_id=<id>` — retrieve conversation messages
- `DELETE /api/deleteconvo?conversation_id=<id>&user_id=<id>` — delete a conversation

> Some routes require a `Authorization: Bearer <token>` header (see `Home.js` / login flow).

---

## 🔐 Current security notes & limitations

- **Passwords** are hashed with Argon2 .  
- **JWT tokens** are currently stored in the browser's `localStorage` by the frontend — this is easier for development but less secure than HttpOnly cookies (XSS risk). See TODOs for planned improvements.
- `app.run(debug=True)` and any `db.drop_all()` usage must **never** be used in production — they are useful for local dev only.
- Make sure to **never** commit your `.env` containing secrets.

---

## 🛠️ Roadmap / TODOs

- [ ] **Code Execution Page** — a sandboxed editor where users submit code and see test results (secure runner or third-party service).  
- [ ] **Move JWTs to HttpOnly cookies** (server-set cookies) for better security and CSRF protection.  
- [ ] **Per-problem pages** with detailed statements, tags and user progress tracking (solved / attempted / starred).  
- [ ] **Statistics dashboard** (charts for solved problems by difficulty/topic).  
- [ ] **Pagination & backend optimizations** (reduce overfetching / improve response times).  
- [ ] **CI / tests / Dockerization** for reproducible setup and deployment.  
- [ ] **Improve LLM moderation** and ensure the assistant never returns full working code (only hints/pseudocode).
