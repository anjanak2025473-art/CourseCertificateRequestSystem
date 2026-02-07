from django.contrib import admin
from .models import User, CertificateRequest


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role',)
    search_fields = ('username', 'email')


@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'certificate_type', 'status', 'created_at')
    list_filter = ('status', 'certificate_type')
    search_fields = ('student__username',)
