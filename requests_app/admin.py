from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import EmailMessage
from django.conf import settings
from .models import User, CertificateRequest
from .views import generate_certificate


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_staff')
    list_filter = ('role', 'department')
    search_fields = ('username', 'email')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'department')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets


def mark_ready_and_send_email(modeladmin, request, queryset):
    for certificate in queryset:
        if certificate.status == "Principal Approved":
            certificate.status = "Completed"
            certificate.save()
            pdf_file = generate_certificate(certificate)
            if certificate.student.email:
                try:
                    email = EmailMessage(
                        subject="Your Certificate is Ready",
                        body="Dear Student,\n\nPlease find your certificate attached.\n\nRegards,\nBharata Mata College Office",
                        from_email=settings.EMAIL_HOST_USER,
                        to=[certificate.student.email],
                    )
                    email.attach("Certificate.pdf", pdf_file.read(), "application/pdf")
                    email.send(fail_silently=False)
                    modeladmin.message_user(request, f"Email sent to {certificate.student.email} ✅")
                except Exception as e:
                    modeladmin.message_user(request, f"Email FAILED: {e}", level='error')
            else:
                modeladmin.message_user(request, f"No email for {certificate.student.username}", level='warning')
        else:
            modeladmin.message_user(request, f"Skipped - status is {certificate.status}", level='warning')

mark_ready_and_send_email.short_description = "✅ Mark as Ready & Send Certificate Email"


@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'certificate_type', 'status', 'created_at')
    list_filter = ('status', 'certificate_type')
    search_fields = ('student__username',)
    actions = [mark_ready_and_send_email]