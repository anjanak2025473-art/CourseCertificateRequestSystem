from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


YEAR_CHOICES = [
    ('I Year', 'I Year'),
    ('II Year', 'II Year'),
    ('III Year', 'III Year'),
    ('IV Year', 'IV Year'),
    ('I Year PG', 'I Year PG'),
    ('II Year PG', 'II Year PG'),
]


class User(AbstractUser):
    email = models.EmailField(unique=False)

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('hod', 'HOD'),
        ('principal', 'Principal'),
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
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )

    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class CertificateRequest(models.Model):

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('HOD Approved', 'HOD Approved'),
        ('Principal Approved', 'Principal Approved'),
        ('Rejected by HOD', 'Rejected by HOD'),
        ('Rejected by Principal', 'Rejected by Principal'),
        ('Completed', 'Completed'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificate_requests'
    )

    certificate_type = models.CharField(max_length=100)
    purpose = models.TextField(blank=True)
    year_of_study = models.CharField(max_length=20, choices=YEAR_CHOICES, default='III Year')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    hod_remarks = models.TextField(blank=True, null=True)
    principal_remarks = models.TextField(blank=True, null=True)
    staff_remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.username} - {self.certificate_type}"