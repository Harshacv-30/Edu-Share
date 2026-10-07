from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.views.decorators.http import require_POST
import os

from .models import Student, Note
from .forms import StudentRegistrationForm, StudentLoginForm, AdminLoginForm, NoteUploadForm
from .decorators import student_approved_required, student_upload_required, admin_required


# ==============================================================================
# PUBLIC PAGES & HOME
# ==============================================================================

def home(request):
    """
    Landing page showcasing EduShare platform features, statistics,
    and latest approved academic notes.
    """
    approved_notes = Note.objects.filter(status='APPROVED').select_related('uploaded_by')[:6]
    total_approved = Note.objects.filter(status='APPROVED').count()
    total_students = Student.objects.filter(approval_status='APPROVED').count()
    branches_count = Student.objects.filter(approval_status='APPROVED').values('branch').distinct().count()

    # Get popular subjects
    popular_subjects = Note.objects.filter(status='APPROVED').values('subject').annotate(total=Count('id')).order_by('-total')[:8]

    context = {
        'recent_notes': approved_notes,
        'total_notes': total_approved,
        'total_students': total_students,
        'branches_count': branches_count or 6,
        'popular_subjects': popular_subjects,
    }
    return render(request, 'core/home.html', context)


# ==============================================================================
# STUDENT AUTHENTICATION & APPROVAL STATUS
# ==============================================================================

def student_register(request):
    """
    Student Registration page.
    Required fields: Full Name, USN, Branch, Semester, Section, Password.
    After registration:
    - Student status = PENDING
    - Show: 'Registration successful. Please wait for Admin approval.'
    - A pending student must NOT access the Student Dashboard.
    """
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        try:
            student = request.user.student_profile
            if student.is_approved:
                return redirect('student_dashboard')
        except Student.DoesNotExist:
            pass

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            usn = form.cleaned_data['usn'].strip().upper()
            branch = form.cleaned_data['branch']
            semester = int(form.cleaned_data['semester'])
            section = form.cleaned_data['section'].strip().upper()
            password = form.cleaned_data['password']

            # Create Django user
            user = User.objects.create_user(
                username=usn,
                first_name=name,
                password=password
            )

            # Create Student profile with PENDING status and upload_permission=False
            student = Student.objects.create(
                user=user,
                name=name,
                usn=usn,
                branch=branch,
                semester=semester,
                section=section,
                approval_status='PENDING',
                upload_permission=False
            )

            messages.success(request, "Registration successful. Please wait for Admin approval.")
            return redirect(f"/waiting-approval/?usn={usn}")
    else:
        form = StudentRegistrationForm()

    return render(request, 'core/student_register.html', {'form': form})


def student_login(request):
    """
    Student Login page using USN and Password.
    Enforces approval workflow:
    - Pending students cannot access dashboard.
    - Rejected students cannot access dashboard.
    - Approved students access dashboard.
    """
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        try:
            student = request.user.student_profile
            if student.is_approved:
                return redirect('student_dashboard')
            elif student.is_pending:
                return redirect('waiting_approval')
        except Student.DoesNotExist:
            pass

    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            usn = form.cleaned_data['usn'].strip().upper()
            password = form.cleaned_data['password']

            user = authenticate(request, username=usn, password=password)

            if user is not None:
                # Check if superuser/staff
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    messages.success(request, f"Welcome Administrator ({user.username}).")
                    return redirect('admin_dashboard')

                try:
                    student = user.student_profile
                    if student.approval_status == 'PENDING':
                        messages.warning(request, "Your registration is currently PENDING Admin approval. Please wait for approval before accessing the dashboard.")
                        return redirect(f"/waiting-approval/?usn={student.usn}")
                    elif student.approval_status == 'REJECTED':
                        reason_msg = f" Reason: {student.rejection_reason}" if student.rejection_reason else ""
                        messages.error(request, f"Registration Rejected by Admin.{reason_msg} Access denied.")
                        return render(request, 'core/student_login.html', {'form': form})
                    elif student.approval_status == 'APPROVED':
                        login(request, user)
                        messages.success(request, f"Welcome back, {student.name}!")
                        return redirect('student_dashboard')
                except Student.DoesNotExist:
                    messages.error(request, "No student profile associated with this account.")
            else:
                messages.error(request, "Invalid USN or password. Please try again.")
    else:
        form = StudentLoginForm()

    return render(request, 'core/student_login.html', {'form': form})


def waiting_approval(request):
    """
    Waiting for Approval page:
    Shows pending status, info message, and includes a live USN lookup box
    allowing any student to check their real-time approval status.
    """
    usn_query = request.GET.get('usn', '').strip().upper()
    student = None
    searched = False

    if usn_query:
        searched = True
        student = Student.objects.filter(usn=usn_query).first()

    return render(request, 'core/waiting_approval.html', {
        'usn_query': usn_query,
        'student': student,
        'searched': searched
    })


def user_logout(request):
    """
    Logs out the student or admin and redirects to home.
    """
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


# ==============================================================================
# STUDENT DASHBOARD & NOTES
# ==============================================================================

@student_approved_required
def student_dashboard(request):
    """
    Student Dashboard for APPROVED students.
    Shows:
    - Welcome message
    - Browse Notes preview & search
    - Search by: Note Title, Subject, Course ID, Module
    - Upload Notes button ONLY if upload_permission == True
    - My Uploaded Notes summary
    """
    student = request.user.student_profile if hasattr(request.user, 'student_profile') else None

    # Search & filters for quick browse from dashboard
    query = request.GET.get('q', '').strip()
    subject_filter = request.GET.get('subject', '').strip()
    course_id_filter = request.GET.get('course_id', '').strip()
    module_filter = request.GET.get('module', '').strip()

    notes_qs = Note.objects.filter(status='APPROVED').select_related('uploaded_by')

    if query:
        notes_qs = notes_qs.filter(
            Q(title__icontains=query) |
            Q(subject__icontains=query) |
            Q(course_id__icontains=query) |
            Q(module__icontains=query) |
            Q(description__icontains=query)
        )
    if subject_filter:
        notes_qs = notes_qs.filter(subject__iexact=subject_filter)
    if course_id_filter:
        notes_qs = notes_qs.filter(course_id__icontains=course_id_filter)
    if module_filter:
        notes_qs = notes_qs.filter(module__iexact=module_filter)

    recent_notes = notes_qs[:12]

    # Student's own notes
    my_notes = Note.objects.filter(uploaded_by=student).order_by('-uploaded_at')[:5] if student else []
    my_notes_count = Note.objects.filter(uploaded_by=student).count() if student else 0

    # Available filter options
    distinct_subjects = Note.objects.filter(status='APPROVED').values_list('subject', flat=True).distinct()
    distinct_courses = Note.objects.filter(status='APPROVED').values_list('course_id', flat=True).distinct()

    context = {
        'student': student,
        'notes': recent_notes,
        'total_results': notes_qs.count(),
        'my_notes': my_notes,
        'my_notes_count': my_notes_count,
        'distinct_subjects': distinct_subjects,
        'distinct_courses': distinct_courses,
        'q': query,
        'selected_subject': subject_filter,
        'selected_course': course_id_filter,
        'selected_module': module_filter,
    }
    return render(request, 'core/student_dashboard.html', context)


def browse_notes(request):
    """
    Public / Student Note Browsing Page with complete search and filter.
    Search approved notes using:
    - Note Title
    - Subject
    - Course ID
    - Module
    """
    query = request.GET.get('q', '').strip()
    subject_filter = request.GET.get('subject', '').strip()
    course_id_filter = request.GET.get('course_id', '').strip()
    module_filter = request.GET.get('module', '').strip()

    notes_qs = Note.objects.filter(status='APPROVED').select_related('uploaded_by')

    if query:
        notes_qs = notes_qs.filter(
            Q(title__icontains=query) |
            Q(subject__icontains=query) |
            Q(course_id__icontains=query) |
            Q(module__icontains=query) |
            Q(description__icontains=query)
        )
    if subject_filter:
        notes_qs = notes_qs.filter(subject__iexact=subject_filter)
    if course_id_filter:
        notes_qs = notes_qs.filter(course_id__icontains=course_id_filter)
    if module_filter:
        notes_qs = notes_qs.filter(module__iexact=module_filter)

    distinct_subjects = Note.objects.filter(status='APPROVED').values_list('subject', flat=True).distinct()
    distinct_courses = Note.objects.filter(status='APPROVED').values_list('course_id', flat=True).distinct()
    modules = ['Module 1', 'Module 2', 'Module 3', 'Module 4', 'Module 5', 'Complete Syllabus / All Modules', 'Question Bank & Solutions']

    context = {
        'notes': notes_qs,
        'total_count': notes_qs.count(),
        'distinct_subjects': distinct_subjects,
        'distinct_courses': distinct_courses,
        'modules': modules,
        'q': query,
        'selected_subject': subject_filter,
        'selected_course': course_id_filter,
        'selected_module': module_filter,
    }
    return render(request, 'core/browse_notes.html', context)


def note_details(request, note_id):
    """
    View note details.
    Only approved notes are publicly visible, unless accessed by the uploader or admin.
    """
    note = get_object_or_404(Note.objects.select_related('uploaded_by'), id=note_id)

    # Permission check for non-approved notes
    if note.status != 'APPROVED':
        is_owner = False
        if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
            if note.uploaded_by == request.user.student_profile:
                is_owner = True
        is_staff = request.user.is_authenticated and request.user.is_staff
        if not (is_owner or is_staff):
            raise Http404("Note not found or pending admin approval.")

    context = {
        'note': note,
    }
    return render(request, 'core/note_details.html', context)


def download_note(request, note_id):
    """
    Download note file and increment downloads counter.
    """
    note = get_object_or_404(Note, id=note_id)

    # If note is not approved, only owner or admin can download
    if note.status != 'APPROVED':
        is_owner = False
        if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
            if note.uploaded_by == request.user.student_profile:
                is_owner = True
        is_staff = request.user.is_authenticated and request.user.is_staff
        if not (is_owner or is_staff):
            raise Http404("Note not found or pending approval.")

    if not note.file or not os.path.exists(note.file.path):
        messages.error(request, "File not found on server storage.")
        return redirect('note_details', note_id=note.id)

    # Increment download counter
    note.downloads_count += 1
    note.save(update_fields=['downloads_count'])

    filename = os.path.basename(note.file.name)
    response = FileResponse(open(note.file.path, 'rb'), as_attachment=True, filename=filename)
    return response


# ==============================================================================
# NOTE UPLOAD & MY NOTES (STUDENT)
# ==============================================================================

@student_upload_required
def upload_note(request):
    """
    Upload Notes page:
    Only accessible if student is approved AND admin has granted upload_permission.
    After upload:
    - Note status = PENDING
    - Note must NOT immediately appear to other students.
    """
    student = request.user.student_profile

    if request.method == 'POST':
        form = NoteUploadForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.uploaded_by = student
            note.status = 'PENDING'  # Explicit pending status
            note.save()

            messages.success(request, f"Note '{note.title}' uploaded successfully! It is now PENDING Admin review and will be visible once approved.")
            return redirect('my_notes')
    else:
        form = NoteUploadForm()

    return render(request, 'core/upload_note.html', {
        'form': form,
        'student': student
    })


@student_approved_required
def my_notes(request):
    """
    Shows all notes uploaded by the current student along with their
    approval status (PENDING, APPROVED, REJECTED).
    """
    student = request.user.student_profile
    notes = Note.objects.filter(uploaded_by=student).order_by('-uploaded_at')

    context = {
        'student': student,
        'notes': notes,
        'pending_count': notes.filter(status='PENDING').count(),
        'approved_count': notes.filter(status='APPROVED').count(),
        'rejected_count': notes.filter(status='REJECTED').count(),
    }
    return render(request, 'core/my_notes.html', context)


# ==============================================================================
# ADMIN PORTAL
# ==============================================================================

def admin_login(request):
    """
    Secure Admin Login page.
    Admin and students use the SAME WEBSITE URL.
    """
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None and (user.is_staff or user.is_superuser):
                login(request, user)
                messages.success(request, f"Welcome to EduShare Admin Portal, {user.username}!")
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Invalid administrator credentials or unauthorized account.")
    else:
        form = AdminLoginForm()

    return render(request, 'core/admin_login.html', {'form': form})


@admin_required
def admin_dashboard(request):
    """
    Admin Dashboard containing:
    - Pending Student Registrations
    - Approved Students
    - Rejected Students
    - Upload Permissions
    - Pending Notes
    - Approved Notes
    - Rejected Notes
    """
    # Counts
    pending_students_count = Student.objects.filter(approval_status='PENDING').count()
    approved_students_count = Student.objects.filter(approval_status='APPROVED').count()
    rejected_students_count = Student.objects.filter(approval_status='REJECTED').count()
    upload_granted_count = Student.objects.filter(approval_status='APPROVED', upload_permission=True).count()

    pending_notes_count = Note.objects.filter(status='PENDING').count()
    approved_notes_count = Note.objects.filter(status='APPROVED').count()
    rejected_notes_count = Note.objects.filter(status='REJECTED').count()

    # Recent lists for quick action
    pending_students = Student.objects.filter(approval_status='PENDING').order_by('-created_at')[:6]
    pending_notes = Note.objects.filter(status='PENDING').select_related('uploaded_by').order_by('-uploaded_at')[:6]
    recent_approved_notes = Note.objects.filter(status='APPROVED').select_related('uploaded_by').order_by('-uploaded_at')[:6]

    context = {
        'pending_students_count': pending_students_count,
        'approved_students_count': approved_students_count,
        'rejected_students_count': rejected_students_count,
        'upload_granted_count': upload_granted_count,
        'pending_notes_count': pending_notes_count,
        'approved_notes_count': approved_notes_count,
        'rejected_notes_count': rejected_notes_count,
        'pending_students': pending_students,
        'pending_notes': pending_notes,
        'recent_approved_notes': recent_approved_notes,
    }
    return render(request, 'core/admin_dashboard.html', context)


@admin_required
def admin_manage_students(request):
    """
    Manage Students page:
    View all students, filter by Pending/Approved/Rejected,
    Approve student, Reject student, Grant/Revoke upload permission.
    """
    status_filter = request.GET.get('status', 'all').upper()
    search = request.GET.get('q', '').strip()

    students_qs = Student.objects.all().order_by('-created_at')

    if status_filter in ['PENDING', 'APPROVED', 'REJECTED']:
        students_qs = students_qs.filter(approval_status=status_filter)

    if search:
        students_qs = students_qs.filter(
            Q(name__icontains=search) |
            Q(usn__icontains=search) |
            Q(branch__icontains=search)
        )

    context = {
        'students': students_qs,
        'status_filter': status_filter,
        'search': search,
        'total_count': students_qs.count(),
        'pending_count': Student.objects.filter(approval_status='PENDING').count(),
        'approved_count': Student.objects.filter(approval_status='APPROVED').count(),
        'rejected_count': Student.objects.filter(approval_status='REJECTED').count(),
    }
    return render(request, 'core/admin_manage_students.html', context)


@admin_required
@require_POST
def admin_student_action(request, student_id, action):
    """
    Admin actions on student:
    - approve
    - reject
    - grant_upload
    - revoke_upload
    """
    student = get_object_or_404(Student, id=student_id)

    if action == 'approve':
        student.approval_status = 'APPROVED'
        student.rejection_reason = None
        student.save()
        messages.success(request, f"Student {student.name} ({student.usn}) has been APPROVED successfully.")

    elif action == 'reject':
        reason = request.POST.get('reason', 'Application rejected by administration.')
        student.approval_status = 'REJECTED'
        student.rejection_reason = reason
        student.upload_permission = False
        student.save()
        messages.warning(request, f"Student {student.name} ({student.usn}) has been REJECTED.")

    elif action == 'grant_upload':
        if student.approval_status != 'APPROVED':
            messages.error(request, f"Cannot grant upload permission: Student {student.name} is not approved yet.")
        else:
            student.upload_permission = True
            student.save()
            messages.success(request, f"Upload permission GRANTED to {student.name} ({student.usn}).")

    elif action == 'revoke_upload':
        student.upload_permission = False
        student.save()
        messages.info(request, f"Upload permission REVOKED from {student.name} ({student.usn}).")

    # Redirect back to referring page or manage students
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'admin_manage_students'
    return redirect(next_url)


@admin_required
def admin_upload_permissions(request):
    """
    Upload Permissions Management:
    Student Name | USN | Upload Permission | Action
    Actions: Grant Permission / Remove Permission
    """
    search = request.GET.get('q', '').strip()
    perm_filter = request.GET.get('perm', 'all')

    # Only approved students are eligible for upload permission management
    students_qs = Student.objects.filter(approval_status='APPROVED').order_by('name')

    if perm_filter == 'granted':
        students_qs = students_qs.filter(upload_permission=True)
    elif perm_filter == 'not_granted':
        students_qs = students_qs.filter(upload_permission=False)

    if search:
        students_qs = students_qs.filter(
            Q(name__icontains=search) |
            Q(usn__icontains=search) |
            Q(branch__icontains=search)
        )

    context = {
        'students': students_qs,
        'search': search,
        'perm_filter': perm_filter,
        'total_approved': Student.objects.filter(approval_status='APPROVED').count(),
        'granted_count': Student.objects.filter(approval_status='APPROVED', upload_permission=True).count(),
        'not_granted_count': Student.objects.filter(approval_status='APPROVED', upload_permission=False).count(),
    }
    return render(request, 'core/admin_upload_permissions.html', context)


@admin_required
def admin_pending_notes(request):
    """
    Pending Notes Queue:
    Admin can view note information, open/download file, Approve, Reject.
    """
    notes = Note.objects.filter(status='PENDING').select_related('uploaded_by').order_by('-uploaded_at')
    return render(request, 'core/admin_pending_notes.html', {'notes': notes})


@admin_required
def admin_approved_notes(request):
    """
    Approved Notes list:
    Active academic notes currently visible to students.
    """
    notes = Note.objects.filter(status='APPROVED').select_related('uploaded_by').order_by('-uploaded_at')
    return render(request, 'core/admin_approved_notes.html', {'notes': notes})


@admin_required
def admin_rejected_notes(request):
    """
    Rejected Notes list:
    Notes rejected during admin review with reason.
    """
    notes = Note.objects.filter(status='REJECTED').select_related('uploaded_by').order_by('-uploaded_at')
    return render(request, 'core/admin_rejected_notes.html', {'notes': notes})


@admin_required
@require_POST
def admin_note_action(request, note_id, action):
    """
    Admin actions on notes:
    - approve
    - reject
    """
    note = get_object_or_404(Note, id=note_id)

    if action == 'approve':
        note.status = 'APPROVED'
        note.rejection_reason = None
        note.save()
        messages.success(request, f"Note '{note.title}' has been APPROVED and is now live for students.")

    elif action == 'reject':
        reason = request.POST.get('reason', 'Quality or formatting requirements not met.')
        note.status = 'REJECTED'
        note.rejection_reason = reason
        note.save()
        messages.warning(request, f"Note '{note.title}' has been REJECTED.")

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'admin_pending_notes'
    return redirect(next_url)
