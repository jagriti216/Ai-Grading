# Running the AI Grading System

Follow these step-by-step commands to start the application.

---

## Step 1: Start the Backend Server

Open a terminal in the project root directory and run the following command to start the FastAPI backend:

```bash
.venv\Scripts\python -m uvicorn stage5_fastapi.main:app --host 127.0.0.1 --port 8000 --reload
```

*Note: For macOS or Linux, use:*
```bash
source .venv/bin/activate
python -m uvicorn stage5_fastapi.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend API will start and be available at [http://127.0.0.1:8000](http://127.0.0.1:8000). You can access the auto-generated Swagger API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## Step 2: Start the Frontend Application

Open a **second** terminal window or tab in the project root directory and run the following commands to navigate to the frontend directory and start the Vite development server:

```bash
cd frontend
npm run dev
```

The frontend application will start and be available in your browser at [http://localhost:5173/](http://localhost:5173/).

---

## Installation & Setup (One-time)

If you haven't installed the dependencies yet:

### Backend Dependencies
Ensure the virtual environment is active, then install the local packages:
```bash
# Windows
.venv\Scripts\python -m pip install -e .

# macOS / Linux
source .venv/bin/activate
python -m pip install -e .
```
*(Use `python -m pip` rather than calling `pip`/`pip.exe` directly — on some Windows setups the standalone `pip.exe` entry point fails silently.)*

### Frontend Dependencies
```bash
cd frontend
npm install
```

---

## Deploying with Docker

A `Dockerfile` (backend), `frontend/Dockerfile` (frontend, served via nginx), and a `docker-compose.yml` are included for containerized deployment:

```bash
cp .env.example .env   # fill in your real secrets first
docker compose up --build
```

This starts the backend on port 8000 and the frontend on port 5173. The app still needs a reachable MongoDB (Atlas or self-hosted) via `MONGODB_URI` in `.env` — Docker Compose does not bundle a database.

Set `CORS_ORIGINS` in `.env` to a comma-separated list of the frontend origin(s) allowed to call the API (defaults to `http://localhost:5173,http://localhost:3000`).
