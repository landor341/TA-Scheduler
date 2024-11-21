# TODO: Implement user controller tests
import os
import django
from django.test import TestCase
import unittest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ta_scheduler.settings')
django.setup()
from django.contrib.auth.middleware import get_user
from ta_scheduler.models import Course, CourseSection, User, TACourseAssignment, LabSection, TALabAssignment

class TestGetUser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user1 = User.objects.create_user(
            first_name='Admin',
            last_name='User',
            username='testadmin',
            email='testadmin@example.com',
            password='securepassword123',
            role='Admin',
            phone='123-456-7890',
            address='123 Main St, Springfield',
            office_hours='Mon, Wed, Fri: 10am - 12pm',
        )
        user1.save()
        cls.user2 = User.objects.create_user(
            first_name='Bob',
            last_name='Marley',
            username='newuser22222',
            email='newuser@example.com',
            password='securepassword123',
            role='Instructor',  # Possible values are 'Instructor', 'TA', 'Admin'
            phone='123-456-7890',
            address='123 Main St, Springfield',
            office_hours='Mon, Wed, Fri: 10am - 12pm',
        )
        cls.user2.save()
    def test_username(self):
        new_user = get_user(self.user2)
        self.assertEqual(new_user.username, 'newuser22222')

    def test_firstname(self):
        new_user = get_user(self.user2)
        self.assertEqual(new_user.first_name, 'Bob')

    def test_lastname(self):
        new_user = get_user(self.user2)
        self.assertEqual(new_user.last_name, 'Marley')

    def test_email(self):
        new_user = get_user(self.user2)
        self.assertEqual(new_user.email, 'newuser@example.com')

    def test_role(self):
        new_user = get_user(self.user2)
        self.assertEqual(new_user.role, 'Instructor')

    def test_phone(self):
        new_user = get_user(self.user2)
        self.assertEqual(new_user.phone, '123-456-7890')

    def test_address(self):
        new_user = get_user(self.user2)
        self.assertEqual(new_user.address, '123 Main St, Springfield')

    def test_office_hours(self):
        new_user = get_user(self.user2)
        self.assertEqual(new_user.office_hours, 'Mon, Wed, Fri: 10am - 12pm')

    def test_NoInput(self):
        pass

    def test_InvalidInput(self):
        pass

    def test_validInput(self):
        pass

class TestSearchUser(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
