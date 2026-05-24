import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'certificate_system.settings')
django.setup()

from requests_app.models import User

# Admin
u, _ = User.objects.get_or_create(username='PROJECTADMIN')
u.set_password('my_project2025')
u.is_staff = True
u.is_superuser = True
u.email = 'anjanak2025473@gmail.com'
u.save()
print('Admin ready!')

# Principal
p, _ = User.objects.get_or_create(username='princi@123')
p.set_password('Bmc@2026')
p.role = 'principal'
p.email = 'principal@gmail.com'
p.save()
print('Principal ready!')