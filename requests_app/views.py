from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.conf import settings

from .forms import CertificateRequestForm, LoginForm
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
        role = request.POST.get('role')
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
            role=role,
            department=department
        )

        login(request, user)

        if role == 'student':
            return redirect('student_dashboard')
        elif role == 'hod':
            return redirect('hod_dashboard')
        elif role == 'staff':
            return redirect('staff_dashboard')

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
            elif user.role == 'staff':
                return redirect('staff_dashboard')
            elif user.role == 'principal':
                return redirect('principal_dashboard')
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
def reject_request(request, request_id):
    if request.user.role != 'hod':
        return redirect('login')

    certificate = get_object_or_404(
        CertificateRequest,
        id=request_id,
        student__department=request.user.department
    )

    if request.method == "POST":
        remarks = request.POST.get('remarks')
        certificate.status = "Rejected"
        certificate.hod_remarks = remarks
        certificate.save()
        return redirect('hod_dashboard')

    return render(request, 'reject_request.html', {
        'certificate': certificate
    })




@login_required
def principal_dashboard(request):
    if request.user.role != 'principal':
        return redirect('login')

    requests = CertificateRequest.objects.filter(
        status="HOD Approved"
    ).order_by('-created_at')

    return render(request, 'principal_dashboard.html', {
        'requests': requests
    })



@login_required
def principal_approve(request, request_id):
    if request.user.role != 'principal':
        return redirect('login')

    certificate = get_object_or_404(CertificateRequest, id=request_id)

    if request.method == "POST":
        remarks = request.POST.get('remarks')
        certificate.status = "Principal Approved"
        certificate.staff_remarks = remarks   # or create principal_remarks
        certificate.save()

        return redirect('principal_dashboard')

    return render(request, 'principal_approve.html', {
        'certificate': certificate
    })


@login_required
def principal_reject(request, request_id):
    if request.user.role != 'principal':
        return redirect('login')

    certificate = get_object_or_404(CertificateRequest, id=request_id)

    if request.method == "POST":
        remarks = request.POST.get('remarks')
        certificate.status = "Rejected"
        certificate.staff_remarks = remarks
        certificate.save()

        return redirect('principal_dashboard')

    return render(request, 'principal_reject.html', {
        'certificate': certificate
    })



@login_required
def staff_dashboard(request):
    if request.user.role != 'staff':
        return redirect('login')

    approved_requests = CertificateRequest.objects.filter(
        status="Principal Approved",
        student__department=request.user.department
    ).order_by('-created_at')

    return render(request, 'admin_dashboard.html', {
        'requests': approved_requests
    })



def generate_certificate(certificate):
    buffer = BytesIO()
    width, height = A4
    p = canvas.Canvas(buffer, pagesize=A4)

    # College Name
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width / 2, height - 80,
        "BHARATA MATA COLLEGE (AUTONOMOUS)")

    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, height - 105,
        "THRIKKAKARA")

    # Date (Right side)
    today = date.today().strftime("%d/%m/%Y")
    p.setFont("Helvetica", 11)
    p.drawRightString(width - 50, height - 130,
        f"Date: {today}")

    # Certificate Title
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 160,
        "CERTIFICATE")
    p.line(width/2 - 70, height - 165, width/2 + 70, height - 165)

    # Body
    p.setFont("Helvetica", 12)
    text = p.beginText(80, height - 210)
    text.setLeading(25)

    text.textLine(
    f"This is to certify that {certificate.student.get_full_name() or certificate.student.username}"
    )
    text.textLine(
        f"is a student of {certificate.student.get_department_display()} Department")
    text.textLine(
        f"for the academic year {certificate.created_at.year}-{certificate.created_at.year + 1}.")
    text.textLine("")
    text.textLine("His/Her character and conduct have been satisfactory.")

    p.drawText(text)

    # Principal Signature Area
    p.line(width - 220, 120, width - 60, 120)
    p.drawString(width - 170, 100, "Principal")
    p.drawString(width - 220, 85, "BHARATA MATA COLLEGE")
    p.drawString(width - 200, 70, "THRIKKAKARA")

    # Seal Circle
    p.circle(120, 100, 40)
    p.drawCentredString(120, 100, "SEAL")

    p.showPage()
    p.save()
    buffer.seek(0)

    return buffer

@login_required
def mark_ready(request, request_id):
    if request.user.role != 'staff':
        return redirect('login')

    certificate = get_object_or_404(
        CertificateRequest,
        id=request_id,
        student__department=request.user.department
    )

    if certificate.status == "Completed":
        return redirect('staff_dashboard')

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
            print(f"Email sending failed: {e}")

    return redirect('staff_dashboard')

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
        # No email on record — show error
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
        print(f"Email resent to {certificate.student.email}")
    except Exception as e:
        print(f"Resend failed: {e}")

    return redirect('staff_dashboard')