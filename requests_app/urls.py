from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register_student, name='register_student'),
    path('request-certificate/', views.request_certificate, name='request_certificate'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('mark-ready/<int:request_id>/', views.mark_ready, name='mark_ready'),
    path('principal/', views.principal_dashboard, name='principal_dashboard'),
    path('principal/approve/<int:request_id>/', views.principal_approve, name='principal_approve'),
    path('principal/reject/<int:request_id>/', views.principal_reject, name='principal_reject'),
    path('resend-email/<int:request_id>/', views.resend_certificate_email, name='resend_certificate_email'),
]