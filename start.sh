./venv/bin/gunicorn --bind 0.0.0.0:9527 monsterabc_crm.wsgi:application
./venv/bin/python manage.py runserver 0.0.0.0:9527
