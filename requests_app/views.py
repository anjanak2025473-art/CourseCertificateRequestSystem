from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import CertificateRequestForm, LoginForm
from .models import CertificateRequest
from django.core.mail import EmailMessage
from django.conf import settings
from reportlab.pdfgen import canvas
from io import BytesIO



User = get_user_model()


# -------------------------
# STUDENT REGISTRATION
# -------------------------
def register_student(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')   # ✅ ADD THIS
        password = request.POST.get('password')
        role = request.POST.get('role')
        department = request.POST.get('department')

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists'
            })

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


from django.shortcuts import get_object_or_404

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

    certificate = CertificateRequest.objects.get(
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
def staff_dashboard(request):
    if request.user.role != 'staff':
        return redirect('login')

    approved_requests = CertificateRequest.objects.filter(
        status="HOD Approved",
        student__department=request.user.department
    ).order_by('-created_at')

    return render(request, 'admin_dashboard.html', {
        'requests': approved_requests
    })





@login_required
def mark_ready(request, request_id):
    if request.user.role != 'staff':
        return redirect('login')

    certificate = CertificateRequest.objects.get(id=request_id)

    # Set correct final status
    certificate.status = "Completed"
    certificate.save()

    # ------------------------
    # Generate PDF in memory
    # ------------------------
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    p.setFont("Helvetica", 18)
    p.drawString(150, 800, "COURSE COMPLETION CERTIFICATE")

    p.setFont("Helvetica", 12)
    p.drawString(100, 750, f"Student Name: {certificate.student.username}")
    p.drawString(100, 720, f"Certificate Type: {certificate.certificate_type}")
    p.drawString(100, 690, "Status: Successfully Completed")
    p.drawString(100, 650, "Congratulations on your achievement!")

    p.showPage()
    p.save()

    buffer.seek(0)

    # ------------------------
    # Send Email with PDF
    # ------------------------
    if certificate.student.email:   # extra safety check
        email = EmailMessage(
            subject="Your Course Certificate is Ready",
            body="Dear Student,\n\nYour certificate has been completed. Please find the attached certificate.\n\nRegards,\nOffice",
            from_email=settings.EMAIL_HOST_USER,
            to=[certificate.student.email],
        )

        email.attach(
            "Course_Certificate.pdf",
            buffer.getvalue(),
            "application/pdf"
        )

        email.send()

    return redirect('staff_dashboard')
