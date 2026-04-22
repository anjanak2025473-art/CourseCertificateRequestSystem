from django.contrib import admin
from django.core.mail import EmailMessage
from django.conf import settings
from .models import User, CertificateRequest
from .views import generate_certificate


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_staff')
    list_filter = ('role', 'department')
    search_fields = ('username', 'email')


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
                except Exception as e:
                    modeladmin.message_user(request, f"Email failed for {certificate.student.username}: {e}", level='error')

mark_ready_and_send_email.short_description = "✅ Mark as Ready & Send Certificate Email"


@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'certificate_type', 'status', 'created_at')
    list_filter = ('status', 'certificate_type')
    search_fields = ('student__username',)
    actions = [mark_ready_and_send_email]
