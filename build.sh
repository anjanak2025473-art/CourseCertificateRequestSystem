#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py migrate

python manage.py shell -c "
from requests_app.models import User
if not User.objects.filter(username='PROJECTADMIN').exists():
    User.objects.create_superuser('PROJECTADMIN', 'anjanak2025473@gmail.com', 'my_project2025')
    print('Superuser created!')
else:
    u = User.objects.get(username='PROJECTADMIN')
    u.set_password('my_project2025')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('Superuser password reset!')
"