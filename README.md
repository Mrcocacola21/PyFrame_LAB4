# Python Frameworks

FastAPI application for authenticated IP geolocation lookups with a web UI, REST API, and MongoDB-backed history.

## Requirements

- `uv`
- Python 3.12+
- MongoDB

## Setup

1. Install dependencies:

```powershell
uv sync --dev
```

2. Create the environment file:

```powershell
Copy-Item .env.example .env
```

3. Update `.env` with your local values.

Required variables:

- `JWT_SECRET_KEY`
- `MONGODB_URI`

All available variables are listed in `.env.example`.

## Run

Start the development server:

```powershell
uv run uvicorn app.main:app --reload
```

The app will be available at `http://127.0.0.1:8000`.

## Tests

Run the test suite:

```powershell
uv run pytest
```

## Routes

Web pages:

- `/`
- `/login`
- `/register`
- `/result`

API endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/lookups`
- `GET /api/v1/lookups/history`
- `GET /api/v1/health`
