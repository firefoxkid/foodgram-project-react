#!/bin/bash
python manage.py makemigrations
python manage.py migrate
gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
