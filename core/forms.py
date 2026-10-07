from django import forms
from django.contrib.auth.models import User
from .models import Student, Note

BRANCH_CHOICES = [
    ('', '-- Select Branch --'),
    ('Computer Science & Engineering', 'Computer Science & Engineering (CSE)'),
    ('Information Science & Engineering', 'Information Science & Engineering (ISE)'),
    ('Electronics & Communication', 'Electronics & Communication (ECE)'),
    ('Electrical & Electronics', 'Electrical & Electronics (EEE)'),
    ('Mechanical Engineering', 'Mechanical Engineering (ME)'),
    ('Civil Engineering', 'Civil Engineering (CE)'),
    ('Artificial Intelligence & Data Science', 'Artificial Intelligence & Data Science (AI & DS)'),
    ('Biotechnology', 'Biotechnology (BT)'),
]

SEMESTER_CHOICES = [('', '-- Select Semester --')] + [(i, f"Semester {i}") for i in range(1, 9)]

MODULE_CHOICES = [
    ('', '-- Select Module --'),
    ('Module 1', 'Module 1'),
    ('Module 2', 'Module 2'),
    ('Module 3', 'Module 3'),
    ('Module 4', 'Module 4'),
    ('Module 5', 'Module 5'),
    ('Complete Syllabus / All Modules', 'Complete Syllabus / All Modules'),
    ('Question Bank & Solutions', 'Question Bank & Solutions'),
    ('Lab Manual / Viva Prep', 'Lab Manual / Viva Prep'),
]

class StudentRegistrationForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. John Doe',
            'required': True
        })
    )
    usn = forms.CharField(
        max_length=30,
        label="University Seat Number (USN)",
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'e.g. 1RV21CS001',
            'required': True
        })
    )
    branch = forms.ChoiceField(
        choices=BRANCH_CHOICES,
        label="Branch / Department",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    semester = forms.ChoiceField(
        choices=SEMESTER_CHOICES,
        label="Semester",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    section = forms.CharField(
        max_length=5,
        label="Section",
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'e.g. A, B, C',
            'required': True
        })
    )
    password = forms.CharField(
        label="Set Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 6 characters',
            'required': True
        })
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter your password',
            'required': True
        })
    )

    def clean_usn(self):
        usn = self.cleaned_data.get('usn', '').strip().upper()
        if Student.objects.filter(usn=usn).exists():
            raise forms.ValidationError("A student with this USN has already registered.")
        if User.objects.filter(username=usn).exists():
            raise forms.ValidationError("An account with this USN already exists.")
        return usn

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            if len(password) < 6:
                self.add_error('password', "Password must be at least 6 characters.")
        return cleaned_data


class StudentLoginForm(forms.Form):
    usn = forms.CharField(
        max_length=30,
        label="USN",
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'Enter your registered USN',
            'required': True
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'required': True
        })
    )


class AdminLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Admin Username",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter administrator username',
            'required': True
        })
    )
    password = forms.CharField(
        label="Admin Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter administrator password',
            'required': True
        })
    )


class NoteUploadForm(forms.ModelForm):
    module = forms.ChoiceField(
        choices=MODULE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )

    class Meta:
        model = Note
        fields = ['title', 'subject', 'course_id', 'module', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Operating Systems - CPU Scheduling Algorithms',
                'required': True
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Operating Systems',
                'required': True
            }),
            'course_id': forms.TextInput(attrs={
                'class': 'form-control text-uppercase',
                'placeholder': 'e.g. 21CS44 or CS401',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide a brief summary of topics covered in these notes...',
                'required': True
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.pptx,.ppt,.txt,.zip',
                'required': True
            })
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if uploaded_file:
            # 25 MB max
            max_size = 25 * 1024 * 1024
            if uploaded_file.size > max_size:
                raise forms.ValidationError("File size exceeds 25 MB. Please upload a smaller file.")
        return uploaded_file
