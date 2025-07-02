# core/tests.py
from django.test import TestCase
from django.urls import reverse
from .models import User, Department, StudentProfile

class UserModelTest(TestCase):
    def test_student_creation(self):
        user = User.objects.create_user(username='teststudent', password='password', role='STUDENT')
        self.assertEqual(user.role, 'STUDENT')

class ViewAccessTest(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='student1', password='password', role='STUDENT')
        self.admin = User.objects.create_user(username='admin1', password='password', role='ADMIN', is_staff=True, is_superuser=True)

    def test_student_cannot_access_admin_dashboard(self):
        self.client.login(username='student1', password='password')
        response = self.client.get(reverse('admin_dashboard'))
        # Should redirect to login page
        self.assertRedirects(response, '/login/?next=/admin/dashboard/')

    def test_admin_can_access_admin_dashboard(self):
        self.client.login(username='admin1', password='password')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)