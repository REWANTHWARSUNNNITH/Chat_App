# Chat App

A real-time 1-on-1 messaging app built with FastAPI, PostgreSQL, and WebSockets — inspired by WhatsApp's UI. Built as a follow-up project after a FastAPI + Postgres Snake game, to learn real-time architecture (WebSockets, connection management, live presence).

## Features

- **Auth** — signup/login with JWT + bcrypt password hashing
- **Direct messaging** — 1-on-1 real-time chat via WebSockets (no group rooms)
- **Message persistence** — full chat history stored in PostgreSQL, loaded when you open a conversation
- **Online presence** — green dot shows which contacts are currently online
- **Unread message badges** — red count badge appears on a contact when they message you and that chat isn't open
- **WhatsApp-style UI** — dark theme, message bubbles, contact sidebar

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy ORM |
| Real-time | native WebSockets (FastAPI) |
| Auth | JWT (python-jose) + bcrypt |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Deployment | Railway (nixpacks) |

## How it works

Each logged-in user opens **one persistent WebSocket connection** (`/ws?token=...`) when the app loads — not per conversation. The backend's `ConnectionManager` keeps a live map of `user_id -> websocket`. When a message is sent, the server:

1. Saves it to the `direct_messages` table in Postgres
2. Pushes it directly to the recipient's socket, if they're online
3. Echoes it back to the sender's own socket (so multiple open tabs stay in sync)

If the recipient is offline, the message still saves — they'll see it in history next time they open that chat.

Presence (`online_user_ids`) is broadcast to everyone whenever a user connects or disconnects, which drives the green online dots and the "Online"/"Offline" status in the chat header.

## Project Structure

```
chatapp/
├── nixpacks.toml           # Railway build config
├── .env.example             # env var template
└── backend/
    ├── main.py               # FastAPI app entrypoint, mounts routers + static files
    ├── database.py            # SQLAlchemy engine/session setup
    ├── models.py               # User, DirectMessage tables
    ├── auth.py                  # JWT + bcrypt password hashing
    ├── connection_manager.py     # tracks active WebSocket per user
    ├── requirements.txt
    ├── routers/
    │   ├── auth.py                # /api/auth/signup, /api/auth/login
    │   ├── users.py                 # /api/users, /api/dm/{id}/messages
    │   └── ws.py                     # /ws — the WebSocket endpoint
    └── static/
        └── index.html               # entire frontend (HTML/CSS/JS in one file)
```

## Running Locally

**Requirements:** Python 3.11 or 3.12 (avoid 3.14 — some dependencies don't have prebuilt wheels for it yet), PostgreSQL installed and running.

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Create a database:
```sql
CREATE DATABASE chatapp;
```

Set environment variables (PowerShell example):
```powershell
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/chatapp"
$env:SECRET_KEY="any-random-secret-string"
```

Run the server:
```bash
python -m uvicorn main:app --reload
```

Open `http://localhost:8000`. Sign up two accounts in two browser tabs to test real-time DMs.

## Deploying to Railway

1. Push this repo to GitHub
2. Create a new Railway project → **Deploy from GitHub repo**
3. Add a **PostgreSQL** plugin to the project (Railway auto-injects `DATABASE_URL`)
4. Set the `SECRET_KEY` environment variable in Railway's dashboard
5. Railway auto-detects `nixpacks.toml` and runs `uvicorn main:app --host 0.0.0.0 --port $PORT`

Tables are created automatically on first startup (`Base.metadata.create_all`), no manual migration needed.

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string (Railway provides this automatically) |
| `SECRET_KEY` | Secret used to sign JWTs — set this to a long random string in production |

## Known Limitations / Next Steps

- Unread badge counts are frontend-only state — they reset on page refresh
- No typing indicators or read receipts yet
- No media/file sharing (text only)
- No push notifications when the tab is closed
