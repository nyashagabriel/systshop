#!/usr/bin/env bash
# Render Build Script – runs automatically on every deploy
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py createcachetable --noinput || true
