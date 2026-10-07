from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from core.models import Student, Note

class EduShareWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create administrator account
        self.admin_user = User.objects.create_superuser(
            username='campus_admin',
            password='AdminPassword123!',
            email='admin@edushare.edu'
        )

    def test_complete_end_to_end_workflow(self):
        """
        Tests the entire specified workflow:
        1. Student registers -> Status = PENDING
        2. Student cannot access Student Dashboard while PENDING
        3. Admin logs in using SAME website URL
        4. Admin sees student in pending registrations
        5. Admin approves student
        6. Student logs in using SAME website URL and accesses Student Dashboard
        7. Student cannot upload notes yet (upload_permission is False)
        8. Admin grants upload permission
        9. Student uploads note -> Note status = PENDING
        10. Other students / public cannot see pending note in approved list
        11. Note appears under Admin's Pending Notes
        12. Admin approves note -> Note status = APPROVED
        13. Approved note becomes visible to students
        14. Student downloads note -> download count increments
        15. Test with second student (Meera) who is approved without upload permission:
            cannot access upload view.
        """
        # ====================================================================
        # Step 1: Student 1 Registers
        # ====================================================================
        reg_response = self.client.post(reverse('student_register'), {
            'name': 'Aarav Patel',
            'usn': '1RV21CS101',
            'branch': 'Computer Science & Engineering',
            'semester': 5,
            'section': 'A',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        })
        self.assertEqual(reg_response.status_code, 302)
        self.assertIn('waiting-approval', reg_response.url)

        # Verify in DB: Student exists, status is PENDING, upload_permission is False
        student_aarav = Student.objects.get(usn='1RV21CS101')
        self.assertEqual(student_aarav.approval_status, 'PENDING')
        self.assertFalse(student_aarav.upload_permission)

        # ====================================================================
        # Step 2: Pending student tries to access Student Dashboard -> BLOCKED
        # ====================================================================
        # Log in as pending student
        login_res = self.client.post(reverse('student_login'), {
            'usn': '1RV21CS101',
            'password': 'Password123!'
        })
        # Must redirect to waiting_approval, NOT student_dashboard
        self.assertEqual(login_res.status_code, 302)
        self.assertIn('waiting-approval', login_res.url)

        # Direct GET on student_dashboard while pending must be redirected
        dash_res = self.client.get(reverse('student_dashboard'))
        self.assertEqual(dash_res.status_code, 302)
        self.assertNotEqual(dash_res.url, reverse('student_dashboard'))

        # ====================================================================
        # Step 3: Admin logs in on SAME website URL
        # ====================================================================
        admin_login_res = self.client.post(reverse('admin_login'), {
            'username': 'campus_admin',
            'password': 'AdminPassword123!'
        })
        self.assertEqual(admin_login_res.status_code, 302)
        self.assertIn(reverse('admin_dashboard'), admin_login_res.url)

        # ====================================================================
        # Step 4: Admin sees student under Pending Registrations
        # ====================================================================
        admin_dash = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(admin_dash.status_code, 200)
        self.assertContains(admin_dash, 'Aarav Patel')
        self.assertContains(admin_dash, '1RV21CS101')

        # ====================================================================
        # Step 5: Admin approves student
        # ====================================================================
        approve_res = self.client.post(reverse('admin_student_action', kwargs={
            'student_id': student_aarav.id,
            'action': 'approve'
        }))
        self.assertEqual(approve_res.status_code, 302)

        student_aarav.refresh_from_db()
        self.assertEqual(student_aarav.approval_status, 'APPROVED')
        # Crucial: upload permission must STILL be False
        self.assertFalse(student_aarav.upload_permission)

        # Admin logs out
        self.client.get(reverse('logout'))

        # ====================================================================
        # Step 6: Student logs in on SAME website URL and accesses dashboard
        # ====================================================================
        stud_login_res = self.client.post(reverse('student_login'), {
            'usn': '1RV21CS101',
            'password': 'Password123!'
        })
        self.assertEqual(stud_login_res.status_code, 302)
        self.assertIn(reverse('student_dashboard'), stud_login_res.url)

        # Open Student Dashboard
        dash_view = self.client.get(reverse('student_dashboard'))
        self.assertEqual(dash_view.status_code, 200)
        self.assertContains(dash_view, 'Aarav Patel')
        # Upload button must NOT be present since upload_permission is False
        self.assertNotContains(dash_view, '+ Upload New Note')

        # ====================================================================
        # Step 7: Direct access to Upload Note view is blocked
        # ====================================================================
        upload_view_blocked = self.client.get(reverse('upload_note'))
        self.assertEqual(upload_view_blocked.status_code, 302)
        self.assertIn(reverse('student_dashboard'), upload_view_blocked.url)

        # Student logs out
        self.client.get(reverse('logout'))

        # ====================================================================
        # Step 8: Admin logs in and grants upload permission
        # ====================================================================
        self.client.post(reverse('admin_login'), {
            'username': 'campus_admin',
            'password': 'AdminPassword123!'
        })

        grant_res = self.client.post(reverse('admin_student_action', kwargs={
            'student_id': student_aarav.id,
            'action': 'grant_upload'
        }))
        self.assertEqual(grant_res.status_code, 302)

        student_aarav.refresh_from_db()
        self.assertTrue(student_aarav.upload_permission)

        # Admin logs out
        self.client.get(reverse('logout'))

        # ====================================================================
        # Step 9: Student logs in and uploads a note
        # ====================================================================
        self.client.post(reverse('student_login'), {
            'usn': '1RV21CS101',
            'password': 'Password123!'
        })

        # Dashboard now shows "+ Upload New Note"
        dash_view_allowed = self.client.get(reverse('student_dashboard'))
        self.assertContains(dash_view_allowed, '+ Upload New Note')

        dummy_pdf = SimpleUploadedFile(
            "Compiler_Design_Module1.pdf",
            b"%PDF-1.4 Lexical Analysis notes",
            content_type="application/pdf"
        )

        upload_res = self.client.post(reverse('upload_note'), {
            'title': 'Compiler Design - Lexical Analysis and DFA Minimization',
            'subject': 'Compiler Design',
            'course_id': '21CS61',
            'module': 'Module 1',
            'description': 'Complete handwritten guide with solved problems on Thompson construction and DFA minimization.',
            'file': dummy_pdf,
        }, follow=True)
        self.assertRedirects(upload_res, reverse('my_notes'))

        # Verify in DB: Note is created with PENDING status
        new_note = Note.objects.get(course_id='21CS61')
        self.assertEqual(new_note.status, 'PENDING')
        self.assertEqual(new_note.uploaded_by, student_aarav)

        # ====================================================================
        # Step 10: Note does NOT appear in public or student Browse Notes
        # ====================================================================
        browse_res = self.client.get(reverse('browse_notes'))
        self.assertNotContains(browse_res, 'Compiler Design - Lexical Analysis and DFA Minimization')

        # Student logs out
        self.client.get(reverse('logout'))

        # ====================================================================
        # Step 11: Note appears under Admin's Pending Notes
        # ====================================================================
        self.client.post(reverse('admin_login'), {
            'username': 'campus_admin',
            'password': 'AdminPassword123!'
        })

        pending_notes_res = self.client.get(reverse('admin_pending_notes'))
        self.assertEqual(pending_notes_res.status_code, 200)
        self.assertContains(pending_notes_res, 'Compiler Design - Lexical Analysis and DFA Minimization')

        # ====================================================================
        # Step 12: Admin approves note
        # ====================================================================
        approve_note_res = self.client.post(reverse('admin_note_action', kwargs={
            'note_id': new_note.id,
            'action': 'approve'
        }))
        self.assertEqual(approve_note_res.status_code, 302)

        new_note.refresh_from_db()
        self.assertEqual(new_note.status, 'APPROVED')

        # ====================================================================
        # Step 13: Approved note becomes visible to students in Browse Notes
        # ====================================================================
        browse_res2 = self.client.get(reverse('browse_notes'))
        self.assertContains(browse_res2, 'Compiler Design - Lexical Analysis and DFA Minimization')

        # ====================================================================
        # Step 14: Student downloads note and download counter increments
        # ====================================================================
        initial_downloads = new_note.downloads_count
        download_res = self.client.get(reverse('download_note', kwargs={'note_id': new_note.id}))
        self.assertEqual(download_res.status_code, 200)

        new_note.refresh_from_db()
        self.assertEqual(new_note.downloads_count, initial_downloads + 1)

        # Admin logs out
        self.client.get(reverse('logout'))

        # ====================================================================
        # Step 15: Second student testing
        # ====================================================================
        # Student 2 registers
        self.client.post(reverse('student_register'), {
            'name': 'Meera Sen',
            'usn': '1RV21IS055',
            'branch': 'Information Science & Engineering',
            'semester': 5,
            'section': 'B',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        })
        student_meera = Student.objects.get(usn='1RV21IS055')
        self.assertEqual(student_meera.approval_status, 'PENDING')

        # Admin approves Student 2 but does NOT grant upload permission
        student_meera.approval_status = 'APPROVED'
        student_meera.upload_permission = False
        student_meera.save()

        # Student 2 logs in
        self.client.post(reverse('student_login'), {
            'usn': '1RV21IS055',
            'password': 'Password123!'
        })
        # Student 2 can browse and see Aarav's approved note
        s2_dash = self.client.get(reverse('student_dashboard'))
        self.assertContains(s2_dash, 'Compiler Design')
        # Student 2 CANNOT see upload button
        self.assertNotContains(s2_dash, '+ Upload New Note')

        # Student 2 direct upload POST is rejected
        dummy_pdf2 = SimpleUploadedFile("fake.pdf", b"fake", content_type="application/pdf")
        unauthorized_upload = self.client.post(reverse('upload_note'), {
            'title': 'Unauthorized Note',
            'subject': 'Math',
            'course_id': 'MAT101',
            'module': 'Module 1',
            'description': 'test',
            'file': dummy_pdf2,
        })
        self.assertEqual(unauthorized_upload.status_code, 302)
        self.assertFalse(Note.objects.filter(title='Unauthorized Note').exists())

    def test_search_and_filter_notes(self):
        """Test searching approved notes by title, subject, course_id, and module"""
        # Create an approved student
        u = User.objects.create_user(username='1RV21CS099', password='pass')
        s = Student.objects.create(
            user=u, name='Test Author', usn='1RV21CS099',
            branch='Computer Science & Engineering', semester=6, section='A',
            approval_status='APPROVED', upload_permission=True
        )
        pdf = SimpleUploadedFile("dummy.pdf", b"%PDF-1.4 sample", content_type="application/pdf")
        
        n1 = Note.objects.create(
            title='Data Structures - Binary Search Trees',
            subject='Data Structures',
            course_id='21CS32',
            module='Module 3',
            description='BST insertions and deletions',
            file=pdf, uploaded_by=s, status='APPROVED'
        )
        n2 = Note.objects.create(
            title='Software Engineering - Agile Methodologies',
            subject='Software Engineering',
            course_id='21CS41',
            module='Module 1',
            description='Scrum, sprints, and user stories',
            file=pdf, uploaded_by=s, status='APPROVED'
        )

        # Search by title query
        res = self.client.get(reverse('browse_notes') + '?q=Binary')
        self.assertContains(res, 'Binary Search Trees')
        self.assertNotContains(res, 'Agile Methodologies')

        # Filter by Subject
        res = self.client.get(reverse('browse_notes') + '?subject=Software Engineering')
        self.assertContains(res, 'Software Engineering')
        self.assertNotContains(res, 'Binary Search Trees')

        # Filter by Course ID
        res = self.client.get(reverse('browse_notes') + '?course_id=21CS32')
        self.assertContains(res, '21CS32')
        self.assertNotContains(res, '21CS41')

        # Filter by Module
        res = self.client.get(reverse('browse_notes') + '?module=Module 1')
        self.assertContains(res, 'Agile Methodologies')
        self.assertNotContains(res, 'Binary Search Trees')

    def test_rejected_student_cannot_access_dashboard(self):
        """Test that a rejected student cannot access dashboard and is shown rejection notice"""
        u = User.objects.create_user(username='1RV21CS088', password='pass')
        Student.objects.create(
            user=u, name='Rejected Student', usn='1RV21CS088',
            branch='Computer Science & Engineering', semester=4, section='A',
            approval_status='REJECTED', rejection_reason='Incorrect branch certificate provided'
        )

        login_res = self.client.post(reverse('student_login'), {
            'usn': '1RV21CS088',
            'password': 'pass'
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertContains(login_res, 'Registration Rejected by Admin')
        self.assertContains(login_res, 'Incorrect branch certificate provided')

    def test_status_lookup_page(self):
        """Test status lookup on /waiting-approval/ by entering USN"""
        u = User.objects.create_user(username='1RV21CS077', password='pass')
        Student.objects.create(
            user=u, name='Pending Student', usn='1RV21CS077',
            branch='Mechanical Engineering', semester=3, section='B',
            approval_status='PENDING'
        )

        res = self.client.get(reverse('waiting_approval') + '?usn=1RV21CS077')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'STATUS: PENDING APPROVAL')
        self.assertContains(res, 'Pending Student')
        self.assertContains(res, '1RV21CS077')
