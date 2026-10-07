from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from core.models import Student, Note
import os

class Command(BaseCommand):
    help = 'Seeds initial admin user, sample students, and verified academic notes'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting EduShare database seeding...")

        # 1. Create Superuser / Admin
        admin_user, created = User.objects.get_or_create(username='admin')
        if created or not admin_user.is_superuser:
            admin_user.set_password('adminpassword123')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.first_name = "Chief"
            admin_user.last_name = "Administrator"
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Admin user created: admin / adminpassword123"))
        else:
            self.stdout.write("Admin user already exists.")

        # 2. Sample Students
        students_data = [
            {
                'usn': '1RV21CS001',
                'name': 'Rahul Sharma',
                'branch': 'Computer Science & Engineering',
                'semester': 5,
                'section': 'A',
                'status': 'APPROVED',
                'upload_perm': True,
                'password': 'password123',
            },
            {
                'usn': '1RV21CS042',
                'name': 'Priya Nair',
                'branch': 'Information Science & Engineering',
                'semester': 5,
                'section': 'B',
                'status': 'APPROVED',
                'upload_perm': False,  # Approved but NO upload permission
                'password': 'password123',
            },
            {
                'usn': '1RV21EC015',
                'name': 'Karthik Verma',
                'branch': 'Electronics & Communication',
                'semester': 3,
                'section': 'A',
                'status': 'PENDING',  # Waiting for approval
                'upload_perm': False,
                'password': 'password123',
            },
            {
                'usn': '1RV21ME099',
                'name': 'Vikram Rao',
                'branch': 'Mechanical Engineering',
                'semester': 7,
                'section': 'C',
                'status': 'REJECTED',  # Rejected
                'rejection_reason': 'Unverified university credentials. Please contact academic office.',
                'upload_perm': False,
                'password': 'password123',
            },
        ]

        created_students = {}
        for sdata in students_data:
            user, u_created = User.objects.get_or_create(username=sdata['usn'])
            if u_created:
                user.set_password(sdata['password'])
                user.first_name = sdata['name']
                user.save()

            student, s_created = Student.objects.get_or_create(
                user=user,
                defaults={
                    'name': sdata['name'],
                    'usn': sdata['usn'],
                    'branch': sdata['branch'],
                    'semester': sdata['semester'],
                    'section': sdata['section'],
                    'approval_status': sdata['status'],
                    'upload_permission': sdata['upload_perm'],
                    'rejection_reason': sdata.get('rejection_reason'),
                }
            )
            created_students[sdata['usn']] = student
            self.stdout.write(f"[OK] Student prepared: {sdata['name']} ({sdata['usn']}) - Status: {sdata['status']}")

        # 3. Create sample academic notes
        authorized_student = created_students['1RV21CS001']

        sample_notes = [
            {
                'title': 'Operating Systems – CPU Scheduling & Deadlocks Guide',
                'subject': 'Operating Systems',
                'course_id': '21CS44',
                'module': 'Module 2',
                'description': 'Comprehensive handwritten & summarized notes covering FCFS, SJF, Round Robin, Priority Scheduling, Bankers Algorithm, and Resource Allocation Graphs with solved numericals.',
                'status': 'APPROVED',
                'filename': 'OS_Module2_Scheduling_Guide.pdf',
                'file_content': b'%PDF-1.4\n1 0 obj\n<< /Title (Operating Systems Module 2) /Author (Rahul Sharma) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF',
            },
            {
                'title': 'Database Management Systems – Normalization & B+ Trees',
                'subject': 'Database Management Systems',
                'course_id': '21CS53',
                'module': 'Module 3',
                'description': 'Covers 1NF, 2NF, 3NF, BCNF decompositions with dependency preservation, plus indexing mechanisms including B-Trees and B+ Trees with step-by-step diagram illustrations.',
                'status': 'APPROVED',
                'filename': 'DBMS_Module3_Normalization.pdf',
                'file_content': b'%PDF-1.4\n1 0 obj\n<< /Title (DBMS Module 3 Normalization) /Author (Rahul Sharma) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF',
            },
            {
                'title': 'Computer Networks – TCP/IP Protocols & Subnetting Workshop',
                'subject': 'Computer Networks',
                'course_id': '21CS52',
                'module': 'Module 4',
                'description': 'Detailed breakdown of IPv4 address classes, CIDR subnetting techniques, sliding window protocol, and three-way TCP handshake mechanisms.',
                'status': 'PENDING',  # In pending review queue
                'filename': 'CN_Module4_Subnetting_Draft.pdf',
                'file_content': b'%PDF-1.4\n1 0 obj\n<< /Title (Computer Networks Subnetting) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF',
            },
            {
                'title': 'Machine Learning – Supervised Learning Algorithms Summary',
                'subject': 'Machine Learning',
                'course_id': '21CS71',
                'module': 'Module 1',
                'description': 'Linear regression, Logistic regression, Decision trees, and Support Vector Machines with loss function derivations and python scikit-learn snippets.',
                'status': 'APPROVED',
                'filename': 'ML_Module1_Supervised_Learning.pdf',
                'file_content': b'%PDF-1.4\n1 0 obj\n<< /Title (Machine Learning Module 1) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF',
            },
        ]

        for ndata in sample_notes:
            note_obj, n_created = Note.objects.get_or_create(
                title=ndata['title'],
                defaults={
                    'subject': ndata['subject'],
                    'course_id': ndata['course_id'],
                    'module': ndata['module'],
                    'description': ndata['description'],
                    'uploaded_by': authorized_student,
                    'status': ndata['status'],
                    'downloads_count': 14 if ndata['status'] == 'APPROVED' else 0,
                }
            )
            if n_created or not note_obj.file:
                note_obj.file.save(ndata['filename'], ContentFile(ndata['file_content']), save=True)
            self.stdout.write(f"[OK] Note prepared: {ndata['title']} [{ndata['status']}]")

        self.stdout.write(self.style.SUCCESS("EduShare Database Seeding Completed Successfully!"))
