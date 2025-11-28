release: python manage.py migrate --noinput
web: gunicorn clinicms.wsgi:application --bind 0.0.0.0:$PORT
