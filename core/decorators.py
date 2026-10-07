from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Student

def student_approved_required(view_func):
    """
    Decorator ensuring only approved students can access the view.
    Pending or rejected students cannot access student dashboard or features.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in with your USN to access the student dashboard.")
            return redirect('student_login')
        
        # If admin tries to access student dashboard, allow viewing or redirect to admin
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            messages.error(request, "No student profile found for this account.")
            return redirect('student_login')

        if student.approval_status == 'PENDING':
            messages.warning(request, "Your registration is currently PENDING Admin approval. You cannot access the student dashboard yet.")
            return redirect('waiting_approval')
        elif student.approval_status == 'REJECTED':
            messages.error(request, f"Your registration was rejected by Admin. Reason: {student.rejection_reason or 'Contact department administration.'}")
            return redirect('student_login')
        elif student.approval_status != 'APPROVED':
            messages.error(request, "Access denied. Your account is not approved.")
            return redirect('student_login')

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_upload_required(view_func):
    """
    Decorator ensuring only approved students who have been explicitly
    granted upload_permission by Admin can upload notes.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to upload notes.")
            return redirect('student_login')

        if request.user.is_staff or request.user.is_superuser:
            messages.warning(request, "Admins can manage notes through the Admin Portal.")
            return redirect('admin_dashboard')

        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            messages.error(request, "No student profile found.")
            return redirect('student_login')

        if student.approval_status != 'APPROVED':
            messages.error(request, "Only approved students can upload notes.")
            return redirect('waiting_approval' if student.approval_status == 'PENDING' else 'student_login')

        if not student.upload_permission:
            messages.error(request, "Upload permission not granted! Admin must grant you upload permission before you can upload notes.")
            return redirect('student_dashboard')

        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """
    Decorator ensuring only Admin/staff can access the admin dashboard and management actions.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Please log in as Administrator.")
            return redirect('admin_login')
        
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "Unauthorized access. Administrator privileges required.")
            return redirect('home')

        return view_func(request, *args, **kwargs)
    return _wrapped_view
