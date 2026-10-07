from django.contrib import admin
from .models import Student, Note

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'usn', 'branch', 'semester', 'section', 'approval_status', 'upload_permission', 'created_at')
    list_filter = ('approval_status', 'upload_permission', 'branch', 'semester')
    search_fields = ('name', 'usn', 'branch')
    actions = ['approve_students', 'reject_students', 'grant_upload', 'revoke_upload']

    def approve_students(self, request, queryset):
        queryset.update(approval_status='APPROVED')
    approve_students.short_description = "Approve selected students"

    def reject_students(self, request, queryset):
        queryset.update(approval_status='REJECTED')
    reject_students.short_description = "Reject selected students"

    def grant_upload(self, request, queryset):
        queryset.update(upload_permission=True)
    grant_upload.short_description = "Grant upload permission"

    def revoke_upload(self, request, queryset):
        queryset.update(upload_permission=False)
    revoke_upload.short_description = "Revoke upload permission"


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'course_id', 'module', 'uploaded_by', 'status', 'downloads_count', 'uploaded_at')
    list_filter = ('status', 'subject', 'course_id', 'module')
    search_fields = ('title', 'subject', 'course_id', 'uploaded_by__name', 'uploaded_by__usn')
    actions = ['approve_notes', 'reject_notes']

    def approve_notes(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_notes.short_description = "Approve selected notes"

    def reject_notes(self, request, queryset):
        queryset.update(status='REJECTED')
    reject_notes.short_description = "Reject selected notes"
