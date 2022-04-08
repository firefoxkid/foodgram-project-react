#!/bin/bash
python manage.py makemigrations
python manage.py migrate
python manage.py loadstatic
export DJANGO_SUPERUSER_PASSWORD=root
export DJANGO_SUPERUSER_EMAIL=root@root.root
export DJANGO_SUPERUSER_USERNAME=root
python manage.py createsuperuser --no-input
gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
