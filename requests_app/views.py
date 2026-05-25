from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.conf import settings

from .forms import CertificateRequestForm
from .models import CertificateRequest

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from datetime import date



User = get_user_model()


# -------------------------
# STUDENT REGISTRATION
# -------------------------
def register_student(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = 'student'
        department = request.POST.get('department')

        if not email:                          # ← ADD THIS CHECK
            return render(request, 'register.html', {
                'error': 'Email address is required'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists'
            })
        # ... rest of the function
        user = User.objects.create_user(
            username=username,
            email=email,          # ✅ SAVE EMAIL
            password=password,
            role = role,
            department=department
        )

        login(request, user)

        return redirect('student_dashboard')

    return render(request, 'register.html')


from django.contrib.auth.views import PasswordResetView
from django.contrib import messages
from smtplib import SMTPException

class SafePasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except (SMTPException, ConnectionError, OSError) as e:
            messages.error(
                self.request,
                "Could not send email right now. Please try again later or contact admin."
            )
            return self.form_invalid(form)
# -------------------------
# LOGIN (ALL USERS)
# -------------------------

def user_login(request):

    if request.method == "POST":

        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():

            user = form.get_user()
            login(request, user)

            if user.role == 'student':
                return redirect('student_dashboard')

            elif user.role == 'hod':
                return redirect('hod_dashboard')

            elif user.role == 'principal':
                return redirect('principal_dashboard')

            elif user.role == 'staff':
                return redirect('staff_dashboard')

    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})
# -------------------------
# REQUEST CERTIFICATE
# -------------------------
@login_required
def request_certificate(request):
    if request.user.role != 'student':
        return redirect('login')

    if request.method == 'POST':
        form = CertificateRequestForm(request.POST)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.student = request.user
            certificate.status = "Pending"   # ensure default
            certificate.save()
            return redirect('student_dashboard')
    else:
        form = CertificateRequestForm()

    return render(request, 'request_certificate.html', {'form': form})


# -------------------------
# LOGOUT
# -------------------------
@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


# -------------------------
# DASHBOARDS
# -------------------------
@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')

    # Get only this student's requests
    user_requests = CertificateRequest.objects.filter(
        student=request.user
    ).order_by('-created_at')

    return render(request, 'student_dashboard.html', {
        'requests': user_requests
    })


@login_required
def hod_dashboard(request):
    if request.user.role != 'hod':
        return redirect('login')

    pending_requests = CertificateRequest.objects.filter(
        status="Pending",
        student__department=request.user.department
    ).order_by('-created_at')

    return render(request, 'hod_dashboard.html', {
        'requests': pending_requests
    })


@login_required
def approve_request(request, request_id):
    if request.user.role != 'hod':
        return redirect('login')

    certificate = get_object_or_404(
        CertificateRequest,
        id=request_id,
        student__department=request.user.department
    )

    if request.method == "POST":
        remarks = request.POST.get('remarks')
        certificate.status = "HOD Approved"
        certificate.hod_remarks = remarks
        certificate.save()
        return redirect('hod_dashboard')

    return render(request, 'approve_request.html', {
        'certificate': certificate
    })


@login_required
def resend_certificate_email(request, request_id):
    if request.user.role != 'staff':
        return redirect('login')

    certificate = get_object_or_404(
        CertificateRequest,
        id=request_id,
        student__department=request.user.department
    )

    if not certificate.student.email:
        return render(request, 'admin_dashboard.html', {
            'requests': CertificateRequest.objects.filter(
                status="Principal Approved",
                student__department=request.user.department
            ).order_by('-created_at'),
            'error': f"Student {certificate.student.username} has no email address saved."
        })

    try:
        pdf_file = generate_certificate(certificate)
        email = EmailMessage(
            subject="Your Certificate is Ready",
            body="Dear Student,\n\nPlease find your certificate attached.\n\nRegards,\nBharata Mata College Office",
            from_email=settings.EMAIL_HOST_USER,
            to=[certificate.student.email],
        )
        email.attach("Certificate.pdf", pdf_file.read(), "application/pdf")
        email.send(fail_silently=False)
    except Exception as e:
        return render(request, 'admin_dashboard.html', {
            'requests': CertificateRequest.objects.filter(
                status="Principal Approved",
                student__department=request.user.department
            ).order_by('-created_at'),
            'error': f"Resend failed: {e}"
        })

    return redirect('staff_dashboard')