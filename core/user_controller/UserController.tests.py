# TODO: Implement user controller tests
import os
import django
from datetime import date
from django.test import TestCase
import unittest

from core.local_data_classes import TACourseRef, UserRef, CourseRef
from core.user_controller.UserController import UserController

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ta_scheduler.settings')
django.setup()
from django.contrib.auth.middleware import get_user
from ta_scheduler.models import Course, CourseSection, User, TACourseAssignment, LabSection, TALabAssignment, Semester
def setupDatabase(course_list):
    """
    Generate test courses with sections, instructors, ta's,
    Course asignments, and lab assignments
    """
    course_count = 0
    user_count = 0

    for (code, name) in course_list:
        course = Course(course_code=code, course_name="name")
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
        setupDatabase(self.courseList)

        self.unassigned_user = User.objects.create_user(role='Admin', email='<EMAIL_TEST>', password='<PASSWORD_TEST>',
                                                        first_name='AdminF_name', last_name='AdminL_name', username='AdminUsername')
        self.unassigned_user.save()
    def test_NoInput(self):
        with self.assertRaises(ValueError):
            UserController.getUser()

    def test_InvalidInput(self):
        with self.assertRaises(ValueError):
            UserController.getUser("Really fake username")

    def test_validInputs(self):
        for user in User.objects.all():
            res = UserController.getUser(user.username)
            self.assertEqual(res.name, user.first_name + user.last_name)
            self.assertEqual(res.role, user.role)
            self.assertEqual(res.email, user.email)
            self.assertEqual(res.office_hours, user.office_hours)
            expected_assignments = []
            for assignment in TALabAssignment.objects.filter(ta=user):
                if (user.role == "TA"):
                    instructor = CourseSection.instructor
                    if instructor is not None:
                        instructor = UserRef(username=instructor.username, name=instructor.first_name + instructor.last_name)
                    else:
                        instructor = None

                    isGrader = TACourseAssignment.objects.filter(ta=user, course=assignment.lab_section.course).first()
                    if isGrader.grader_status:
                        isGrader = True
                    else:
                        isGrader = False

                    labs = []
                    for lab in TALabAssignment.objects.filter(ta=user):
                        labs.append(lab.lab_section_number)

                    self.assertIn(
                        TACourseRef(
                            course_code=assignment.lab_section.course.course_code,
                            course_name=assignment.lab_section.course.course_name,
                            instructor=instructor,
                            is_grader=isGrader,
                            assigned_lab_sections=labs
                        )
                    )
                else: #Admin or instructor
                    self.assertIn(
                        CourseRef(
                            course_code=assignment.lab_section.course.course_code,
                            course_name=assignment.lab_section.course.course_name,
                        )
                    )


class TestSearchUser(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

class TestDeleteUser(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
