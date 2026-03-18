# IP Geolocation Service

Production-ready FastAPI service with a JWT-protected REST API, a Jinja2 server-rendered frontend, and MongoDB-backed lookup history.

## Features

- Layered architecture with routers, services, repositories, and schemas
- User registration and login with `bcrypt` password hashing
- JWT-protected IP geolocation lookup endpoint
- Server-rendered frontend with Jinja2 templates and static assets
- Async MongoDB access via `motor`
- Request history persistence
- Request logging middleware and custom exception handlers
- Automated tests for API and frontend auth/lookup flows


## Required Environment Variables

- `JWT_SECRET_KEY` with at least 32 characters
- `MONGODB_URI`

Optional variables are documented in `.env.example`.

## Web UI

- `/` dashboard and lookup form
- `/login` login page
- `/register` registration page
- `/result` latest lookup result

## API Overview

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/lookups`
- `GET /api/v1/lookups/history`
- `GET /api/v1/health`
