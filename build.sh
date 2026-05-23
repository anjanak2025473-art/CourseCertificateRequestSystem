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

if not User.objects.filter(username='princi@123').exists():
    User.objects.create_user(username='princi@123', password='Bmc@2026', email='principal@gmail.com', role='principal')
    print('Principal created!')
else:
    p = User.objects.get(username='princi@123')
    p.set_password('Bmc@2026')
    p.role = 'principal'
    p.save()
    print('Principal password reset!')
"