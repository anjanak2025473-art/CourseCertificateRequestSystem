from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings

from smtplib import SMTPException
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from io import BytesIO
from datetime import date

from .forms import CertificateRequestForm
from .models import CertificateRequest

User = get_user_model()


# =========================================================
# STUDENT REGISTRATION
# =========================================================

def register_student(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        department = request.POST.get('department')

        if not email:
            return render(request, 'register.html', {
                'error': 'Email address is required'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='student',
            department=department
        )

        login(request, user)

        return redirect('student_dashboard')

    return render(request, 'register.html')


# =========================================================
# SAFE PASSWORD RESET
# =========================================================

class SafePasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'

    def form_valid(self, form):
        try:
            return super().form_valid(form)

        except (SMTPException, ConnectionError, OSError):
            messages.error(
                self.request,
                "Could not send email right now. Please try again later."
            )
            return self.form_invalid(form)


# =========================================================
# LOGIN / LOGOUT
# =========================================================

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


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@login_required
def student_dashboard(request):

    if request.user.role != 'student':
        return redirect('login')

    user_requests = CertificateRequest.objects.filter(
        student=request.user
    ).order_by('-created_at')

    return render(request, 'student_dashboard.html', {
        'requests': user_requests
    })


@login_required
def request_certificate(request):

    if request.user.role != 'student':
        return redirect('login')

    if request.method == 'POST':

        form = CertificateRequestForm(request.POST)

        if form.is_valid():
            certificate = form.save(commit=False)

            certificate.student = request.user
            certificate.status = "Pending"

            certificate.save()

            messages.success(
                request,
                "Certificate request submitted successfully."
            )

            return redirect('student_dashboard')

    else:
        form = CertificateRequestForm()

    return render(request, 'request_certificate.html', {
        'form': form
    })


# =========================================================
# HOD DASHBOARD
# =========================================================

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

        messages.success(request, "Request approved successfully.")

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

        certificate.status = "Rejected by HOD"
        certificate.hod_remarks = remarks

        certificate.save()

        messages.error(request, "Request rejected.")

        return redirect('hod_dashboard')

    return render(request, 'reject_request.html', {
        'certificate': certificate
    })


# =========================================================
# PRINCIPAL DASHBOARD
# =========================================================

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

    certificate = get_object_or_404(
        CertificateRequest,
        id=request_id
    )

    if request.method == "POST":

        remarks = request.POST.get('remarks')

        certificate.status = "Principal Approved"
        certificate.principal_remarks = remarks

        certificate.save()

        messages.success(request, "Request approved by Principal.")

        return redirect('principal_dashboard')

    return render(request, 'principal_approve.html', {
        'certificate': certificate
    })


@login_required
def principal_reject(request, request_id):

    if request.user.role != 'principal':
        return redirect('login')

    certificate = get_object_or_404(
        CertificateRequest,
        id=request_id
    )

    if request.method == "POST":

        remarks = request.POST.get('remarks')

        certificate.status = "Rejected by Principal"
        certificate.principal_remarks = remarks

        certificate.save()

        messages.error(request, "Request rejected by Principal.")

        return redirect('principal_dashboard')

    return render(request, 'principal_reject.html', {
        'certificate': certificate
    })


# =========================================================
# STAFF DASHBOARD
# =========================================================

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


# =========================================================
# PDF CERTIFICATE GENERATION
# =========================================================

def generate_certificate(certificate):

    buffer = BytesIO()

    width, height = A4

    pdf = canvas.Canvas(buffer, pagesize=A4)

    # College Heading
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(
        width / 2,
        height - 80,
        "BHARATA MATA COLLEGE (AUTONOMOUS)"
    )

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(
        width / 2,
        height - 105,
        "THRIKKAKARA"
    )

    # Date
    today = date.today().strftime("%d/%m/%Y")

    pdf.setFont("Helvetica", 11)
    pdf.drawRightString(
        width - 50,
        height - 130,
        f"Date: {today}"
    )

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(
        width / 2,
        height - 160,
        "CERTIFICATE"
    )

    pdf.line(
        width / 2 - 70,
        height - 165,
        width / 2 + 70,
        height - 165
    )

    # Body
    pdf.setFont("Helvetica", 12)

    text = pdf.beginText(80, height - 220)

    text.setLeading(25)

    student_name = (
        certificate.student.get_full_name()
        or certificate.student.username
    )

    department = certificate.student.get_department_display()

    year = certificate.created_at.year

    text.textLine(
        f"This is to certify that {student_name}"
    )

    text.textLine(
        f"is a student of {department} Department"
    )

    text.textLine(
        f"for the academic year {year}-{year + 1}."
    )

    text.textLine("")

    text.textLine(
        "His/Her character and conduct have been satisfactory."
    )

    pdf.drawText(text)

    # Signature
    pdf.line(width - 220, 120, width - 60, 120)

    pdf.drawString(width - 170, 100, "Principal")
    pdf.drawString(width - 220, 85, "BHARATA MATA COLLEGE")
    pdf.drawString(width - 200, 70, "THRIKKAKARA")

    # Seal
    pdf.circle(120, 100, 40)
    pdf.drawCentredString(120, 100, "SEAL")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    return buffer


# =========================================================
# MARK CERTIFICATE AS READY
# =========================================================

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

    # Update status
    certificate.status = "Completed"
    certificate.save()

    # Generate PDF
    try:
        pdf_file = generate_certificate(certificate)

    except Exception as e:

        messages.error(
            request,
            f"PDF generation failed: {e}"
        )

        return redirect('staff_dashboard')

    # Send email
    if certificate.student.email:

        try:

            email = EmailMessage(
                subject="Your Certificate is Ready",
                body=(
                    "Dear Student,\n\n"
                    "Please find your certificate attached.\n\n"
                    "Regards,\n"
                    "Bharata Mata College Office"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[certificate.student.email],
            )

            email.attach(
                "Certificate.pdf",
                pdf_file.read(),
                "application/pdf"
            )

            email.send(fail_silently=False)

            messages.success(
                request,
                "Certificate marked as completed and emailed."
            )

        except Exception as e:

            messages.error(
                request,
                f"Email sending failed: {e}"
            )

    return redirect('staff_dashboard')


# =========================================================
# RESEND CERTIFICATE EMAIL
# =========================================================

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

        messages.error(
            request,
            f"{certificate.student.username} has no email address."
        )

        return redirect('staff_dashboard')

    try:

        pdf_file = generate_certificate(certificate)

        email = EmailMessage(
            subject="Your Certificate is Ready",
            body=(
                "Dear Student,\n\n"
                "Please find your certificate attached.\n\n"
                "Regards,\n"
                "Bharata Mata College Office"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[certificate.student.email],
        )

        email.attach(
            "Certificate.pdf",
            pdf_file.read(),
            "application/pdf"
        )

        email.send(fail_silently=False)

        messages.success(
            request,
            "Certificate email resent successfully."
        )

    except Exception as e:

        messages.error(
            request,
            f"Resend failed: {e}"
        )

    return redirect('staff_dashboard')