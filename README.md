# Vehicle Rental Management System (VRMS)

A full-stack vehicle rental platform for a single-agency car and two-wheeler
rental business. Built as the semester project for the Software Engineering
course, Department of Computer Engineering, Sardar Patel Institute of
Technology, Mumbai.

VRMS replaces a manual register-and-telephone booking process with a
responsive web application backed by a REST API, eliminating double bookings,
disputes over charges, and missed vehicle servicing.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Project Documentation](#project-documentation)
- [Team](#team)

---

## Features

**Customer**
- Browse the vehicle catalogue and view published tariffs without an account
- Real-time availability search with filters for type, category, fuel,
  transmission, price and rating
- Book a car or two-wheeler with a 15-minute vehicle hold during checkout
- Modify, extend or cancel a booking under a published cancellation policy
- Pay by card, online transfer, wallet, or cash on branch collection
- Rental history with downloadable invoices, rental agreements and condition
  reports
- Rate the vehicle and the service after a completed rental

**Branch Staff**
- Retrieve a booking by reference, pickup code or customer mobile number
- Photographic handover and return checklists with digital customer signature
- Automatic itemised settlement against the security deposit
- Flag a vehicle for maintenance during return

**Maintenance Technician**
- Receive assigned jobs, record work, parts and labour cost
- Close a job and return the vehicle to service

**Administrator**
- Fleet master data, statutory document tracking and vehicle retirement
- Tariff definition with effective dates and full historical retention
- Staff account management and customer blacklist
- Refund approval above the automatic threshold
- Utilisation, revenue and maintenance-cost reporting
- Complete, non-editable audit log

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2 LTS, Django REST Framework |
| Database | PostgreSQL 16 |
| Async tasks | Celery + Redis, Celery Beat for scheduled jobs |
| Auth | JWT (SimpleJWT), bcrypt password hashing |
| API docs | drf-spectacular (OpenAPI 3.0) |
| Frontend | React 18, TypeScript, Vite |
| Styling | Tailwind CSS, shadcn/ui (Radix primitives) |
| Data fetching | TanStack Query |
| Forms | React Hook Form + Zod |
| Charts | Recharts |
| Testing | pytest, pytest-django, factory-boy, Vitest |

---

## Architecture

Clients (responsive web) communicate with a single Django REST API over
HTTPS. All business logic — availability, pricing, eligibility and
authorisation — is enforced server-side; client-side validation exists for
usability only.

Three external services are integrated behind interfaces so that each can be
replaced or mocked:

- **Payment Gateway** — authorisation, capture and refund. No card data is
  stored, logged or transmitted by VRMS.
- **Notification Service** — transactional e-mail and SMS, queued so that a
  provider outage cannot fail a booking transaction.
- **Maps Service** — geocoding and distance for branch sorting and delivery
  address validation.

Concurrency safety for bookings is enforced at the database level using a
PostgreSQL range exclusion constraint, so no two Confirmed or Active bookings
for the same vehicle can ever overlap.

---

## Getting Started

### Prerequisites

- Python 3.12
- Node.js 20 LTS
- PostgreSQL 16
- Redis 7
- Git

### Clone

```bash
git clone https://github.com/rohansd05/vehicle-rental-management-system.git
cd vehicle-rental-management-system
```

### Backend setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements-dev.txt
```

Create the database:

```bash
psql -U postgres -c "CREATE DATABASE vrms;"
psql -U postgres -c "CREATE USER vrms_user WITH PASSWORD 'your_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE vrms TO vrms_user;"
```

Apply migrations and create an administrator:

```bash
cp ../.env.example .env      # then edit .env
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/demo_data.json
```

### Frontend setup

```bash
cd ../frontend
npm install
```

---

## Configuration

All configuration is read from `backend/.env`. Copy `.env.example` and fill in
your own values. Never commit `.env`.

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` in development only |
| `DATABASE_URL` | `postgres://user:pass@localhost:5432/vrms` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `PAYMENT_GATEWAY_KEY_ID` | Gateway test-mode key |
| `PAYMENT_GATEWAY_KEY_SECRET` | Gateway test-mode secret |
| `SMS_ACCOUNT_SID` | SMS provider account identifier |
| `SMS_AUTH_TOKEN` | SMS provider token |
| `EMAIL_HOST` / `EMAIL_HOST_USER` | Mail service credentials |
| `MEDIA_URL_EXPIRY_SECONDS` | Signed document link lifetime (default 900) |

All external integrations run in **sandbox mode**. No live financial
settlement takes place.

---

## Running the Application

Four processes, each in its own terminal:

```bash
# 1. API server
cd backend && python manage.py runserver

# 2. Celery worker
cd backend && celery -A config worker -l info

# 3. Celery Beat scheduler
cd backend && celery -A config beat -l info

# 4. Frontend dev server
cd frontend && npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000/api/v1/ |
| API docs (Swagger) | http://localhost:8000/api/docs/ |
| Django admin | http://localhost:8000/admin/ |

Alternatively, bring up Postgres and Redis with Docker:

```bash
docker compose up -d
```

### Demo accounts

| Role | E-mail | Password |
|---|---|---|
| Customer | customer@vrms.test | Demo@1234 |
| Branch Staff | staff@vrms.test | Demo@1234 |
| Technician | tech@vrms.test | Demo@1234 |
| Administrator | admin@vrms.test | Demo@1234 |

---

## Testing

```bash
cd backend

pytest                                    # full suite
pytest --cov=apps --cov-report=html       # with coverage report
pytest apps/bookings/tests/ -v            # one app
pytest -m concurrency                     # concurrency suite only
```

```bash
cd frontend
npm run test
```

Coverage targets: at least 70% of business logic overall, and 100% of the
pricing, availability and settlement logic.

---

## API Documentation

Interactive documentation is generated from the code and served at
`/api/docs/`. To export the schema:

```bash
python manage.py spectacular --file ../docs/api/openapi.yaml
```

---

## Project Documentation

Course deliverables are in `docs/experiments/`:

| # | Deliverable |
|---|---|
| 1 | Software Requirements Specification (IEEE 830) |
| 2 | Use Case Diagram and Descriptions |
| 3 | Class Diagram |
| 4 | Interaction Diagrams (Sequence, Collaboration) |
| 5 | Activity Diagram |
| 6 | Data Flow Diagrams (Level 0 and 1) |
| 7 | Work Breakdown Structure and Schedule |
| 8 | Risk Mitigation, Monitoring and Management Plan |
| 9 | Module Implementation |
| 10 | Test Cases and Unit Testing |

The SRS is the authoritative specification. Business rules BR-1 to BR-16
in Section 5.5 are referenced throughout the codebase; any change to a rule
must be reflected in every requirement and test that references it.

---

## Team

| Name | UID | Division | Batch |
|---|---|---|---|
| Rohan Dhumal | 2024300049 | A | A3 |
| Nidhi Rajkamal Dhyani | 2024300050 | A | A3 |

Department of Computer Engineering
Sardar Patel Institute of Technology, Andheri (W), Mumbai

---

## Licence

Academic project. Not licensed for commercial use.