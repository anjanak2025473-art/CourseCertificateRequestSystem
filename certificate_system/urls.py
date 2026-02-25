from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from requests_app import views

urlpatterns = [
    path('', lambda request: redirect('login')),

    path('admin/', admin.site.urls),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register_student, name='register_student'),

    path('student/', views.student_dashboard, name='student_dashboard'),
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),

    path('request/', views.request_certificate, name='request_certificate'),

    path('approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('mark-ready/<int:request_id>/', views.mark_ready, name='mark_ready'),
]
