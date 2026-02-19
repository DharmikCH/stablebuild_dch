# Stablebuild: Credit Scoring Platform

Merged repository containing NextJS frontend + FastAPI ML model backend for alternative credit scoring.

## Project Structure

```
stablebuild/
├── frontend/           # Next.js web application
│   ├── app/           # App router pages
│   ├── components/    # React components
│   ├── lib/           # Utilities and API client
│   └── package.json
├── backend/           # FastAPI server + ML model
│   ├── app/          # FastAPI app and model files
│   ├── requirements.txt
│   └── main.py
├── docker-compose.yml # Orchestrate both services
├── Dockerfile.frontend
└── Dockerfile.backend
```

## Quick Start with Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Local Development

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
# Running on http://localhost:3000
```

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Running on http://localhost:8000
```

## API Endpoints

**POST /score** - Score a borrower
- Body: Form fields (monthly_income, profile_type, etc.)
- Returns: alternative_credit_score, risk_band, top_factors, probabilities

**GET /health** - Liveness check

**GET /docs** - Interactive API documentation

## Configuration

The frontend calls the backend via `BASE_URL` environment variable (defaults to `http://localhost:8000`).

In Docker: frontend connects to backend service via internal network.
Locally: ensure both are running on their respective ports.
