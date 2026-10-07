from django.urls import path
from . import views

urlpatterns = [
    # 1. Home
    path('', views.home, name='home'),

    # 2. Student Registration
    path('register/', views.student_register, name='student_register'),

    # 3. Student Login / Access
    path('login/', views.student_login, name='student_login'),
    path('student/login/', views.student_login, name='student_login_alias'),

    # 4. Waiting for Approval
    path('waiting-approval/', views.waiting_approval, name='waiting_approval'),

    # 5. Student Dashboard
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),

    # 6. Browse Notes
    path('notes/', views.browse_notes, name='browse_notes'),

    # 7. Note Details
    path('notes/<int:note_id>/', views.note_details, name='note_details'),

    # Note Download
    path('notes/<int:note_id>/download/', views.download_note, name='download_note'),

    # 8. Upload Note
    path('notes/upload/', views.upload_note, name='upload_note'),

    # 9. My Notes
    path('student/my-notes/', views.my_notes, name='my_notes'),

    # 10. Admin Login
    path('admin-portal/login/', views.admin_login, name='admin_login'),

    # 11. Admin Dashboard
    path('admin-portal/dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # 12. Manage Students
    path('admin-portal/students/', views.admin_manage_students, name='admin_manage_students'),
    path('admin-portal/students/<int:student_id>/<str:action>/', views.admin_student_action, name='admin_student_action'),

    # 13. Upload Permissions
    path('admin-portal/permissions/', views.admin_upload_permissions, name='admin_upload_permissions'),

    # 14. Pending Notes
    path('admin-portal/notes/pending/', views.admin_pending_notes, name='admin_pending_notes'),

    # 15. Approved Notes
    path('admin-portal/notes/approved/', views.admin_approved_notes, name='admin_approved_notes'),

    # 16. Rejected Notes
    path('admin-portal/notes/rejected/', views.admin_rejected_notes, name='admin_rejected_notes'),
    path('admin-portal/notes/<int:note_id>/<str:action>/', views.admin_note_action, name='admin_note_action'),

    # Logout
    path('logout/', views.user_logout, name='logout'),
]
