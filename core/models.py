from django.db import models
from django.contrib.auth.models import User
import os

class Student(models.Model):
    APPROVAL_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    name = models.CharField(max_length=150, help_text="Full Name of the Student")
    usn = models.CharField(max_length=30, unique=True, db_index=True, help_text="University Seat Number")
    branch = models.CharField(max_length=100, help_text="Engineering/Academic Branch")
    semester = models.IntegerField(help_text="Current Semester (e.g. 1-8)")
    section = models.CharField(max_length=10, help_text="Section (e.g. A, B, C)")
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='PENDING', db_index=True)
    upload_permission = models.BooleanField(default=False, help_text="Explicit admin permission to upload notes")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason if student registration was rejected")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.name} ({self.usn}) - {self.approval_status}"

    @property
    def is_approved(self):
        return self.approval_status == 'APPROVED'

    @property
    def is_pending(self):
        return self.approval_status == 'PENDING'

    @property
    def is_rejected(self):
        return self.approval_status == 'REJECTED'

    @property
    def can_upload(self):
        return self.is_approved and self.upload_permission


class Note(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    title = models.CharField(max_length=255, help_text="Note Title")
    subject = models.CharField(max_length=150, db_index=True, help_text="Subject / Course Name")
    course_id = models.CharField(max_length=50, db_index=True, help_text="Course ID / Subject Code (e.g. CS501)")
    module = models.CharField(max_length=50, db_index=True, help_text="Module (e.g. Module 1, Module 2)")
    description = models.TextField(blank=True, help_text="Detailed summary of notes content")
    file = models.FileField(upload_to='notes_files/', help_text="Uploaded notes document")
    uploaded_by = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    rejection_reason = models.TextField(blank=True, null=True, help_text="Feedback if note was rejected")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    downloads_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Academic Note'
        verbose_name_plural = 'Academic Notes'

    def __str__(self):
        return f"{self.title} ({self.subject} - {self.course_id}) [{self.status}]"

    @property
    def file_extension(self):
        if self.file:
            _, ext = os.path.splitext(self.file.name)
            return ext.replace('.', '').upper()
        return 'FILE'

    @property
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        return 'No File'

    @property
    def is_pdf(self):
        return self.file_extension == 'PDF'
