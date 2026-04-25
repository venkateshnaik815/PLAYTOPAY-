#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations to ensure database is connected and ready
python backend/manage.py migrate

# Collect static files for production UI
python backend/manage.py collectstatic --no-input

# Seed data if it's the first run (optional but helpful)
python backend/manage.py seed_data || true
