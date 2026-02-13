from django.contrib import admin
from django.urls import path
from requests_app import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register_student, name='register_student'),

    path('student/', views.student_dashboard, name='student_dashboard'),
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('staff/', views.admin_dashboard, name='staff_dashboard'),

]
