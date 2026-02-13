from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

User = get_user_model()


# -------------------------
# STUDENT REGISTRATION
# -------------------------
def register_student(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = User.objects.create_user(
            username=username,
            password=password,
            role='student'
        )

        login(request, user)
        return redirect('student_dashboard')

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

            # Redirect based on role
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'hod':
                return redirect('hod_dashboard')
            elif user.role == 'staff':
                return redirect('staff_dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


# -------------------------
# LOGOUT
# -------------------------


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
    return render(request, 'student_dashboard.html')




@login_required
def hod_dashboard(request):
    if request.user.role != 'hod':
        return redirect('login')
    return render(request, 'hod_dashboard.html')




@login_required
def admin_dashboard(request):
    if request.user.role != 'staff':
        return redirect('login')
    return render(request, 'admin_dashboard.html')

