#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies (from the current directory)
pip install -r requirements.txt

# Run migrations (manage.py is in the current directory now)
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# Seed data
python manage.py seed_data || true
