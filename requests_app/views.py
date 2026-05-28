import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.contrib import messages
from django.core.mail import EmailMessage, get_connection
from django.conf import settings

from smtplib import SMTPException
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from io import BytesIO
from datetime import date

from .forms import CertificateRequestForm
from .models import CertificateRequest

User = get_user_model()

# Setup logging so you can see email success/failure in terminal
logger = logging.getLogger(__name__)


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

    # Show ALL Principal Approved requests (removed department filter)
    approved_requests = CertificateRequest.objects.filter(
        status="Principal Approved"
    ).order_by('-created_at')

    # Show last 20 completed for resend option
    completed_requests = CertificateRequest.objects.filter(
        status="Completed"
    ).order_by('-updated_at')[:20]

    return render(request, 'admin_dashboard.html', {
        'requests': approved_requests,
        'completed_requests': completed_requests,
    })


# =========================================================
# PDF CERTIFICATE GENERATION
# =========================================================

def generate_certificate(certificate):

    buffer = BytesIO()

    width, height = A4

    pdf = canvas.Canvas(buffer, pagesize=A4)

    # --- College Heading ---
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, height - 60, "BHARATA MATA COLLEGE (AUTONOMOUS),")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(width / 2, height - 80, "THRIKKAKARA")

    # --- Date ---
    today = date.today().strftime("%d/%m/%Y")
    pdf.setFont("Helvetica", 11)
    pdf.drawRightString(width - 60, height - 60, f"Date: {today}")

    # --- Title ---
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 120, "CERTIFICATE")

    # Title underline
    pdf.line(width / 2 - 60, height - 125, width / 2 + 60, height - 125)

    # --- Body ---
    pdf.setFont("Helvetica", 12)
    text = pdf.beginText(80, height - 170)
    text.setLeading(22)

    student_name = (
        certificate.student.get_full_name()
        or certificate.student.username
    )

    year = certificate.created_at.year

    text.textLine("This is to certify that")
    
    # Student name in bold (draw separately for emphasis)
    pdf.drawText(text)
    
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(width / 2, height - 220, student_name)
    
    pdf.setFont("Helvetica", 12)
    text = pdf.beginText(80, height - 245)
    text.setLeading(22)

    text.textLine("is a student of this college for the IIIrd year Computer")
    text.textLine("Science (Aided) B.A./B.Sc./B.Com./BBA/B.S.W./M.A./M.Sc./")
    text.textLine(f"M.S.W./M.Com degree course during the academic year(s) {year}-{year + 1}")
    text.textLine("and that his/her character and conduct have been Good.")

    pdf.drawText(text)

    # --- Seal & Signatures Label ---
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, 180, "Seal & Signatures")

    # --- Left Side: Seal ---
    # Outer circle
    pdf.circle(150, 110, 50)
    # Inner circle
    pdf.circle(150, 110, 40)
    # College name around seal
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawCentredString(150, 140, "BHARATA MATA COLLEGE")
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(150, 130, "B.M.C.")
    pdf.setFont("Helvetica", 6)
    pdf.drawCentredString(150, 120, "(AUTONOMOUS)")
    pdf.drawCentredString(150, 100, "THRIKKAKARA, KOCHI-21")

    # --- Right Side: Signature & Stamp ---
    # Signature line
    pdf.line(width - 200, 145, width - 60, 145)
    
    # Stamp text
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(width - 170, 120, "Principal")
    
    pdf.setFont("Helvetica", 8)
    pdf.drawString(width - 200, 105, "PRINCIPAL IN-CHARGE")
    
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(width - 190, 90, "BHARATA MATA COLLEGE")
    
    pdf.setFont("Helvetica", 8)
    pdf.drawString(width - 190, 78, "(AUTONOMOUS)")
    pdf.drawString(width - 190, 66, "THRIKKAKARA")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)

    return buffer

# =========================================================
# EMAIL SENDING HELPER (SENDGRID API FOR RENDER / GMAIL FOR LOCAL)
# =========================================================

def send_certificate_email(certificate):
    """
    Uses SendGrid HTTP API (works on Render free tier)
    Falls back to Gmail SMTP (works on localhost).
    Returns (success: bool, message: str)
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

    student = certificate.student
    student_email = student.email.strip() if student.email else ''

    # Check 1: Student has an email
    if not student_email:
        logger.warning(f"Request #{certificate.id}: Student '{student.username}' has no email.")
        return False, f"Student '{student.username}' has no email address."

    # Generate PDF
    try:
        pdf_buffer = generate_certificate(certificate)
        import base64
        pdf_data_b64 = base64.b64encode(pdf_buffer.read()).decode()
        pdf_buffer.close()
    except Exception as e:
        logger.error(f"PDF failed for request #{certificate.id}: {e}")
        return False, f"PDF generation failed: {e}"

    # Build email content
    student_name = student.get_full_name() or student.username
    course_name = certificate.certificate_type or "Course"
    subject = f"Course Certificate Issued - {course_name}"

    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;
                border:1px solid #ddd;border-radius:8px;overflow:hidden;">
        <div style="background:#1a237e;padding:25px;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:20px;">Bharata Mata College</h1>
            <p style="color:#90caf9;margin:5px 0 0;font-size:12px;">
                Course Certificate Request System
            </p>
        </div>
        <div style="padding:25px;background:#fafafa;">
            <p>Dear <strong>{student_name}</strong>,</p>
            <p>Your course certificate has been processed and is ready.
               Please find the certificate attached as a PDF.</p>
            <table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;">
                <tr>
                    <td style="padding:10px;background:#e8eaf6;font-weight:600;
                               border:1px solid #c5cae9;">Request ID</td>
                    <td style="padding:10px;background:#fff;
                               border:1px solid #c5cae9;">#{certificate.id}</td>
                </tr>
                <tr>
                    <td style="padding:10px;background:#e8eaf6;font-weight:600;
                               border:1px solid #c5cae9;">Course</td>
                    <td style="padding:10px;background:#fff;
                               border:1px solid #c5cae9;">{course_name}</td>
                </tr>
                <tr>
                    <td style="padding:10px;background:#e8eaf6;font-weight:600;
                               border:1px solid #c5cae9;">Status</td>
                    <td style="padding:10px;background:#fff;border:1px solid #c5cae9;
                               color:#2e7d32;font-weight:600;">Completed</td>
                </tr>
            </table>
            <p style="color:#666;font-size:13px;">
                If you have any queries, contact the college office.</p>
        </div>
        <div style="background:#f5f5f5;padding:15px;text-align:center;
                    font-size:11px;color:#999;">
            Bharata Mata College, Thrikkakara, Kochi - 682041
        </div>
    </div>
    """

    # --- Attempt 1: SendGrid API (Works on Render) ---
    sg_key = os.getenv('SENDGRID_API_KEY', '')
    sg_from = os.getenv('SENDGRID_FROM_EMAIL', '')

    if sg_key and sg_from:
        try:
            message = Mail(
                from_email=sg_from,
                to_emails=student_email,
                subject=subject,
                html_content=body_html
            )

            attachment = Attachment(
                file_content=FileContent(pdf_data_b64),
                file_name=FileName(f"Certificate_{certificate.id}.pdf"),
                file_type=FileType("application/pdf"),
                disposition=Disposition("attachment")
            )
            message.attachment = attachment

            sg = SendGridAPIClient(sg_key)
            response = sg.send(message)

            logger.info(f"Email sent via SendGrid API to {student_email} for request #{certificate.id}")
            return True, f"Certificate emailed via SendGrid to {student_email}"

        except Exception as e:
            logger.warning(f"SendGrid API failed for request #{certificate.id}: {e}")

    # --- Attempt 2: Gmail SMTP (Works on Localhost) ---
    gmail_user = os.getenv('GMAIL_USER', '')
    gmail_pass = os.getenv('GMAIL_PASSWORD', '')
    gmail_from = os.getenv('GMAIL_FROM_EMAIL', '')

    if gmail_user and gmail_pass:
        try:
            connection = get_connection(
                host='smtp.gmail.com',
                port=587,
                username=gmail_user,
                password=gmail_pass,
                use_tls=True,
                timeout=30
            )

            email = EmailMessage(
                subject=subject,
                body=f"Dear {student_name},\n\nYour certificate is attached.",
                from_email=gmail_from,
                to=[student_email],
                connection=connection
            )

            pdf_bytes = base64.b64decode(pdf_data_b64)
            email.attach(f"Certificate_{certificate.id}.pdf", pdf_bytes, "application/pdf")
            email.send(fail_silently=False)

            logger.info(f"Email sent via Gmail to {student_email} for request #{certificate.id}")
            return True, f"Certificate emailed via Gmail to {student_email}"

        except Exception as e:
            logger.warning(f"Gmail failed for request #{certificate.id}: {e}")

    return False, "Both SendGrid and Gmail failed. Check API keys and network."
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
        status="Principal Approved"
    )

    if certificate.status == "Completed":
        messages.warning(request, "This certificate is already completed.")
        return redirect('staff_dashboard')

    # Step 1: Update status FIRST
    certificate.status = "Completed"
    certificate.save()

    # Step 2: Send email using helper
    success, message = send_certificate_email(certificate)

    if success:
        messages.success(request, f"Certificate completed. {message}")
    else:
        messages.warning(
            request,
            f"Certificate marked as completed, but email failed: {message}. "
            f"Use the Resend button to try again."
        )

    return redirect('staff_dashboard')
# =========================================================
# RESEND CERTIFICATE EMAIL
# =========================================================

@login_required
def resend_certificate_email(request, request_id):

    if request.user.role not in ('staff', 'admin'):
        return redirect('login')

    certificate = get_object_or_404(
        CertificateRequest,
        id=request_id,
        status="Completed"
    )

    success, message = send_certificate_email(certificate)

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect('staff_dashboard')
