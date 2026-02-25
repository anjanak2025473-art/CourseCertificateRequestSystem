from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('hod', 'HOD'),
        ('staff', 'Office Staff'),
    )

    DEPARTMENT_CHOICES = (
        ('CS', 'Computer Science'),
        ('ECO', 'Economics'),
        ('PHY', 'Physics'),
        ('ENG', 'English'),
        ('MAL', 'Malayalam'),
        ('CHEM', 'Chemistry'),
        ('BOT', 'Botany'),
        ('ZOO', 'Zoology'),
        ('MATH', 'Mathematics'),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student'
    )

    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        blank=True
    )

    def __str__(self):
        return f"{self.username} ({self.role} - {self.department})"

class CertificateRequest(models.Model):

    STATUS_CHOICES = (
        ('Pending', 'Pending'),               # Waiting for HOD
        ('HOD Approved', 'HOD Approved'),     # Sent to Staff
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),           # Staff finished
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificate_requests'
    )

    certificate_type = models.CharField(max_length=100)
    purpose = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    hod_remarks = models.TextField(blank=True)
    staff_remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.certificate_type} ({self.status})"
        email = models.EmailField()
