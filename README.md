# Social Readia

## Project Overview

**Social Readia** is a full-stack social reading platform that allows users to log books, write thoughtful reviews, and interact with other readers through likes and comments.

Originally built as a personal Reading Tracker, the project evolved into a social feed-driven application that emphasizes reflective writing, clean UI design, and scalable backend architecture.

The goal is to combine structured reading logs with lightweight social media interaction, without sacrificing performance or maintainability.

---

## Key Features

- **Secure Authentication**
  - JWT-based token authentication
  - Registration & login with protected routes
  - Persistent login state on the frontend

- **Public Social Feed**
  - Browse public reviews from other users
  - Cursor-based pagination
  - Multiple sorting modes (newest, oldest, review length, review type)

- **Likes & Comments**
  - Users can like reviews
  - Comment system with real-time count updates
  - Expandable "Read more / Read less" preview UX

- **Review System**
  - Review types (Recommended / Not Recommended / Neutral)
  - Preview truncation with toggle expansion
  - Review date tracking

- **Interactive UI**
  - Responsive grid layout
  - Clean card-based feed design
  - Reactive state management using Svelte stores

- **Full CRUD Functionality**
  - Create, edit, delete book entries
  - Backend-validated data
  - ORM-managed database models

- **Database Migrations**
  - Schema evolution handled via Alembic
  - Structured enums for review types and visibility

---

## Tech Stack

This project uses a modern, production-oriented full-stack architecture.

### Frontend
- **SvelteKit**
- **TypeScript**
- Reactive Svelte stores
- Custom CSS

### Backend
- **FastAPI (Python)**
- RESTful API design
- JWT authentication
- Structured service layer

### Database
- **SQLite (development)**
- Managed with:
  - **SQLAlchemy ORM**
  - **Alembic migrations**

### Deployment
- Backend: Render
- Frontend: Vercel (static adapter)

---

## Architecture Overview

The application follows a clean separation of concerns:

- `api/`
  - Models
  - Service layer
  - Routers
  - JWT utilities
  - Database configuration

- `src/`
  - SvelteKit routes
  - Reusable components
  - API client helpers
  - Auth store

This structure allows the backend to scale independently while the frontend remains modular and reactive.

---

## Local Development Setup

To run this application locally, you need:

- Node.js (v18+ recommended)
- Python (3.10+ recommended)

---

### 1. Clone and Initialize

```sh
# Clone the repository
git clone https://github.com/SkutM/reading-tracker
cd full-stack-svelte-project

# Install frontend dependencies
npm install
```

---

### 2. Backend Setup

```sh
# Navigate to API directory
cd api

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
. .\.venv\Scripts\Activate.ps1

# Or activate (Bash)
# source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Return to project root
cd ..
```

---

### 3. Database Migration

Run Alembic to generate the SQLite database.

```sh
cd api
alembic upgrade head
cd ..
```

This creates the local `db.sqlite` file using the latest schema.

---

### 4. Run the Full Stack

Run backend and frontend simultaneously in separate terminals.

Terminal 1 — Backend:

```sh
uvicorn api.main:app --reload
```

Terminal 2 — Frontend:

```sh
npm run dev
```

The app will be available at:

http://localhost:5173

API documentation:

http://127.0.0.1:8000/docs

---

## Testing Authentication Flow

1. Open the API docs at `/docs`.
2. Use `/auth/register` to create a user.
3. Use `/auth/login` to retrieve an access token.
4. Log in via the frontend and test:
   - Creating reviews
   - Liking reviews
   - Commenting
   - Sorting the public feed

---

## Project Evolution

This project began as a personal Reading Tracker focused on individual book logging.

It evolved into **Social Readia**, introducing:

- Public feeds
- Social interaction
- Pagination
- Advanced filtering
- Backend service abstractions
- Production-ready deployment

The evolution demonstrates incremental feature scaling, database migrations, and architectural refinement.
