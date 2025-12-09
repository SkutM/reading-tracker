# Reading Tracker

## Project Overview

The Reading Tracker is a full-stack web application designed to help users log, review, and organize the works they read. It encourages reflective review over simple tracking, allowing users to apply deep thoughts to their reading journey.

### Key Features
* **Secure User Authentication:** Token-based login/registration ensures personal reading data is stored privately.
* **Interactive Reading Grid:** Books are displayed as aesthetic cards in a responsive grid layout.
* **3D Card Flip UX:** Clicking a book card triggers a 3D flip animation to reveal the user's detailed review and rating.
* **External API Integration:** Automatically fetches book cover images from the Open Library API upon entry.
* **Full CRUD Functionality:** Users can Create, Read, Update, and Delete their book records directly from the frontend.

---

## Tech Stack

This project uses a modern, high-performance full-stack architecture:

* **Frontend (UI):** **SvelteKit** with **TypeScript** for fast, reactive, and easily maintainable user interfaces.
* **Backend (API):** **FastAPI** (Python) for a highly efficient REST API.
* **Database (DB):** **SQLite** for development (managed by **SQLAlchemy** ORM and **Alembic** migrations).
* **Styling:** Custom CSS, including complex 3D transforms for the card flip effect.

---

## Local Development Setup

To run this application on your local machine, you need Node.js (for the frontend) and Python (for the backend).

### 1. Clone and Initialize

```sh
# Clone the repository
git clone https://github.com/SkutM/reading-tracker
cd full-stack-svelte-project

# Install Node dependencies (SvelteKit/Vite)
npm install
```

### 2. Backend Setup

```sh
# Navigate to the API directory
cd api

# Create and activate the Python virtual environment
python -m venv .venv
# For Windows PowerShell:
. .\.venv\Scripts\Activate.ps1
# For Bash/Git Bash:
# source .venv/Scripts/activate

# Install Python dependencies (FastAPI/SQLAlchemy/Passlib)
pip install -r requirements.txt 

# Navigate back to the project root
cd ..
```

### 3. Database Migration

The database structure must be created from your models.

```sh
# Navigate back to the API folder to run Alembic
cd api
# Execute the migration (creates db.sqlite file)
alembic upgrade head
# Navigate back to the root
cd ..
```

### 4. Run the Full Stack

You must run the backend and frontend simultaneously in two separate terminal tabs.

Terminal 1 (Backend)

```sh

uvicorn api.main:app --reload
```

Terminal 2 (Frontend)

```sh
npm run dev
```

The application will be accessible at http://localhost:5173.

## Testing Authentication

1. Access the API Docs at http://127.0.0.1:8000/docs.

2. Use the /auth/register endpoint to create an initial user.

3. Use the /auth/login endpoint to generate an Access Token.

4. Use the token on the frontend to test the full application flow.
