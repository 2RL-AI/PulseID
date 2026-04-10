# PulseID Access Badge System

Modern NFC access badge management for the workplace. Track employee presence, stay
compliant with European labor regulations, and generate professional PDF reports — all
from one secure web dashboard.

**Open-source** | [GitHub](https://github.com/2RL-AI/PulseID) | Developed by [2RL.AI](https://2rl.ai)

## Architecture

| Layer    | Technology                          | Port |
|----------|-------------------------------------|------|
| Frontend | Vue 3 + Vuetify 3 (Nginx)          | 8080 |
| Backend  | Python / Flask 3 (Gunicorn)         | 5005 |
| Database | PostgreSQL 16                       | 5432 |

All three services are orchestrated with **Docker Compose**. The backend runs a
background reader service that continuously listens for NFC badge scans.

## Quick Start

```bash
# 1. Copy and edit environment variables
cp example.env .env

# 2. Build and start all services
make build
make up

# 3. Open the application
open http://localhost:8080
```

Default credentials (change in `.env`):
- **Username:** `admin`
- **Password:** `admin`

## NFC Reader Setup

Before starting Docker, detect your NFC reader on the host:

```bash
make detect-readers
```

Then uncomment the `privileged` and `volumes` lines in `docker-compose.yml` under
the `backend` service to give it access to the USB reader.

## Makefile Targets

| Target              | Description                              |
|---------------------|------------------------------------------|
| `make build`        | Build all Docker containers              |
| `make up`           | Start all services in background         |
| `make down`         | Stop all services                        |
| `make restart`      | Restart all services                     |
| `make logs`         | Tail service logs                        |
| `make test`         | Run all tests                            |
| `make test-backend` | Run backend tests (SQLite in-memory)     |
| `make clean`        | Stop, remove volumes and images          |
| `make shell-backend`| Open shell in backend container          |
| `make db-reset`     | Reset the database                       |
| `make detect-readers`| Detect NFC readers on the host          |

## Features

### Dashboard (Drawer Navigation)
- **Employees** — Full CRUD for employee profiles (name, email, phone, position, department)
- **Badges** — Assign/unassign NFC badges to employees; live scan feed with real-time polling
- **Records** — Paginated access log with filters by employee and event type; PDF report download
- **Users** — CRUD for application login accounts

### Badge System
- Background reader service continuously polls the NFC reader
- Automatic recording: badge scan → `NEW_RECORD` in database
- Badge registration: assign next scan → `BADGE_CREATION` + link to employee
- Reader status visible in the dashboard

### Landing Page
- Product showcase with animated hero, features, how-it-works, and pricing
- 2RL.AI company branding and GitHub repository link
- EU/Luxembourg labor law compliance messaging

## API Endpoints

All endpoints require `X-API-Key` header (injected by nginx proxy in Docker).

### Authentication

| Method | Endpoint           | Auth  | Description              |
|--------|--------------------|-------|--------------------------|
| POST   | `/api/auth/login`  | —     | Login (returns JWT)      |
| GET    | `/api/auth/me`     | JWT   | Current user info        |

### Employees (JWT required)

| Method | Endpoint                              | Description                  |
|--------|---------------------------------------|------------------------------|
| GET    | `/api/employees`                      | List all employees           |
| POST   | `/api/employees`                      | Create employee              |
| GET    | `/api/employees/:id`                  | Get employee                 |
| PUT    | `/api/employees/:id`                  | Update employee              |
| DELETE | `/api/employees/:id`                  | Delete employee              |
| POST   | `/api/employees/:id/assign-badge`     | Assign badge (blocks for reader) |
| DELETE | `/api/employees/:id/assign-badge`     | Unassign badge               |

### Records & Reports (JWT required)

| Method | Endpoint                                 | Description                     |
|--------|------------------------------------------|---------------------------------|
| GET    | `/api/records`                           | Paginated access logs           |
| GET    | `/api/records/latest`                    | Recent records (for polling)    |
| POST   | `/api/records/remove-period`             | Remove records for a month      |
| POST   | `/api/records/remove-before-current-month` | Remove old records            |
| GET    | `/api/available-months`                  | Months with recorded data       |
| POST   | `/api/reports/download`                  | Download PDF report             |

### Users (JWT required)

| Method | Endpoint         | Description    |
|--------|------------------|----------------|
| GET    | `/api/users`     | List users     |
| POST   | `/api/users`     | Create user    |
| PUT    | `/api/users/:id` | Update user    |
| DELETE | `/api/users/:id` | Delete user    |

### Reader (JWT required)

| Method | Endpoint             | Description              |
|--------|----------------------|--------------------------|
| GET    | `/api/reader/status` | Reader connection status |
| GET    | `/api/reader/detect` | Detect available readers |

## Development

### Backend (local)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://pulseid:pulseid_secret@localhost:5432/pulseid
python wsgi.py
```

### Frontend (local)

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://localhost:5005`.

## Requirements

- Docker & Docker Compose
- NFC/PC/SC reader (for badge operations)

## Legacy CLI

The original single-file CLI (`pulseid.py`) is preserved in the repository root
for backward compatibility.
