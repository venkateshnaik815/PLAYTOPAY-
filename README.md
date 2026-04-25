# Playto Payout Engine

A robust, concurrency-safe payout engine built with Django, DRF, Celery, and React.

## Features
- **Immutable Ledger**: Balance derived directly from DB aggregation.
- **Concurrency Control**: Row-level locking to prevent double-spending.
- **Idempotency**: Scoped per merchant with in-flight request handling.
- **State Machine**: Secure payout lifecycle with atomic refunds.
- **Real-time Dashboard**: Modern React UI with status polling.

## Tech Stack
- **Backend**: Django 4.2+, DRF
- **Database**: PostgreSQL (SQLite used for local demo compatibility)
- **Background Jobs**: Celery + Redis
- **Frontend**: React + Tailwind CSS

## Setup Instructions

### Backend
1. Navigate to `backend/`
2. Create virtual environment: `python -m venv venv`
3. Activate venv: `.\venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Run migrations: `python manage.py migrate`
6. Seed data: `python manage.py seed_data`
7. Start server: `python manage.py runserver`
8. Start Celery (separate terminal): `celery -A payout_engine worker -l info`

### Frontend
1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Start dev server: `npm run dev`

## Running Tests
Run backend tests to verify concurrency and idempotency:
```bash
python manage.py test payouts
```
*Note: The concurrency test uses threads and may require PostgreSQL for full isolation behavior. On SQLite, it may occasionally report 'database is locked'.*
