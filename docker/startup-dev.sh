#!/bin/sh

# Current directory is /app when this script is executed

./manage.py migrate
exec ./manage.py runserver 0.0.0.0:8000
