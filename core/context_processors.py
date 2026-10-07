from .models import Student, Note

def edushare_context(request):
    """
    Context processor to provide global stats and current student profile.
    """
    context = {
        'current_student': None,
        'is_student': False,
        'is_admin': False,
        'pending_students_count': 0,
        'pending_notes_count': 0,
        'total_approved_notes_count': 0,
    }

    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            context['is_admin'] = True
            context['pending_students_count'] = Student.objects.filter(approval_status='PENDING').count()
            context['pending_notes_count'] = Note.objects.filter(status='PENDING').count()
        else:
            try:
                student = request.user.student_profile
                context['current_student'] = student
                context['is_student'] = True
            except Student.DoesNotExist:
                pass

    context['total_approved_notes_count'] = Note.objects.filter(status='APPROVED').count()
    return context
