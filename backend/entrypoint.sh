#!/bin/bash
set -e

echo "Creating data directory..."
mkdir -p /app/data

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Starting server..."
exec "$@"
