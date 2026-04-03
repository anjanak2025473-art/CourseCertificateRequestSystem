from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from requests_app.views import SafePasswordResetView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Root → redirect to login
    path('', include('requests_app.urls')),

    # Password Reset URLs
    path('password-reset/',
         SafePasswordResetView.as_view(),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='password_reset_confirm.html'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='password_reset_complete.html'
         ),
         name='password_reset_complete'),
]