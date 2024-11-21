# TODO: Implement user controller tests
import os
import django
from datetime import date
from django.test import TestCase
import unittest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ta_scheduler.settings')
django.setup()
from django.contrib.auth.middleware import get_user
from ta_scheduler.models import Course, CourseSection, User, TACourseAssignment, LabSection, TALabAssignment, Semester
def setupdatabase(course_list):
    """
    Generate test courses with sections, instructors, ta's,
    Course asignments, and lab assignments
    """
    course_count = 0
    user_count = 0

    for (code, name) in course_list:
        course = Course.objects.create(course_code=code, course_name=name)
        course.save()
        course_count += 1
        for i in range(course_count):
            instructor = User(
                role="Instructor", first_name=user_count, last_name=user_count,
                password=user_count, username=user_count
            )
            instructor.save()
            user_count += 1
            section = CourseSection(
            course_id=course,
            course_section_number=i,
            instructor=instructor
            )
            section.save()

            ta = User(
            role="TA", first_name=user_count, last_name=user_count,
            password=user_count, username=user_count
            )
            ta.save()
            user_count += 1

            courseAssignment = TACourseAssignment(course=course, grader_status=False, ta=ta)
            courseAssignment.save()

            labSection = LabSection(course=course, lab_section_number=i)
            labSection.save()

            if i % 2 == 1:
                labAssignment = TALabAssignment(lab_section=labSection, ta=ta)
                labAssignment.save()


class TestGetUser(unittest.TestCase):
    def setUp(self):
        self.course_list = [
            ('Test1', 'Software Engineering'),
            ('Test2', 'Software Development'),
            ('Other3', 'Calculus 777'),
            ('1000000000', '7777777777')
        ]
        setupdatabase(self.course_list)

        new_user = self.objects.create_user(role='Admin', email='<EMAIL_TEST>', password='<PASSWORD_TEST>',
                                            first_name='AdminF_name', last_name='AdminL_name', username='AdminUsername')
        new_user.save()
    def test_username(self):
        self.assertEqual(self.new_user.username, 'AdminUsername')
    def test_firstname(self):
        pass
    def test_lastname(self):
        pass
    def test_email(self):
        pass
    def test_role(self):
        pass
    def test_phone(self):
        pass
    def test_address(self):
        pass
    def test_office_hours(self):
        pass
    def test_NoInputId(self):
        pass
    def test_InvalidIdInput(self):
        pass

    def test_validInputId(self):
        pass

class TestSearchUser(unittest.TestCase):
    def test_EmptyString(self):
        self.assertEqual(True, False)  # add assertion here

    def test_InvalidString(self):
        pass

    def test_ValidString1Character(self):
        pass

    def test_ValidStringManyCharacters(self):
        pass


class TestDeleteUser(unittest.TestCase):
    def setUp(self):
        pass
    def test_ValidId(self):
        self.assertEqual(True, False)  # add assertion here
    def test_InValidId(self):
        pass
    def test_NoId(self):
        pass
    def test_InValidId1Character(self):
        pass


if __name__ == '__main__':
    unittest.main()
