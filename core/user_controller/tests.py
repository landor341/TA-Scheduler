# TODO: Implement user controller tests
from django.test import TestCase
from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
import django
django.setup()
from ta_scheduler.models import Course, CourseSection, User, TACourseAssignment, LabSection, TALabAssignment, Semester
from datetime import date
from core.local_data_classes import TACourseRef, UserRef, CourseRef
from core.user_controller.UserController import UserController

def setupdatabase(course_list):
    """
    Generate test courses with sections, instructors, ta's,
    Course asignments, and lab assignments
    """
    course_count = 0
    user_count = 0
    semester = Semester.objects.create(
        semester_name="semester_name", start_date=date(2024, 9, 1), end_date=date(2024, 12, 15)
    )
    for (code, name) in course_list:
        course = Course.objects.create(course_code=code, course_name=name, semester=semester)
        course.save()
        course_count += 1
        for i in range(course_count):
            instructor = User(
                role="Instructor",
                first_name=str(user_count),
                last_name=str(user_count),
                password=str(user_count),
                username=str(user_count)
            )
            instructor.save()
            user_count += 1
            section = CourseSection(
                course_id=course.id,
                course_section_number=i,
                instructor = instructor,
                start_time = "09:00",
                end_time = "10:30",
                days = "Mon, Wed"
            )
            section.save()

            ta = User(
                role="TA",
                first_name=str(user_count),
                last_name=str(user_count),
                password=str(user_count),
                username=str(user_count)
            )
            ta.save()
            user_count += 1

            courseAssignment = TACourseAssignment(course=course, grader_status=False, ta=ta)
            courseAssignment.save()

            labSection = LabSection(course=course, lab_section_number=i, start_time="13:00", end_time="15:00")
            labSection.save()

            if i % 2 == 1:
                labAssignment = TALabAssignment(lab_section=labSection, ta=ta)
                labAssignment.save()


class TestGetUser(TestCase):

    def setUp(self):
        self.course_list = [
            ('Test1', 'Software Engineering'),
            ('Test2', 'Software Development'),
            ('Other3', 'Calculus 777'),
            ('1000000000', '7777777777')
        ]
        setupdatabase(self.course_list)
        self.unassigned_user = User.objects.create_user(role='Admin', email='EMAIL_TEST', password='PASSWORD_TEST',
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

class TestSearchUser(TestCase):
    def test_EmptyString(self):
        self.assertEqual(True, False)  # add assertion here

    def test_InvalidString(self):
        pass

    def test_ValidString1Character(self):
        pass

    def test_ValidStringManyCharacters(self):
        pass


class TestDeleteUser(TestCase):
    def setUp(self):
        self.course_list = [
            ('Test1', 'Software Engineering'),
            ('Test2', 'Software Development'),
            ('Other3', 'Calculus 777'),
            ('1000000000', '7777777777')
        ]
        setupdatabase(self.course_list)
        self.unassigned_user = User.objects.create_user(role='TA', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                        first_name='TAF_name', last_name='TAL_name', username='TAUsername')
        self.unassigned_user.save()
        self.assigned_user = User.objects.create_user(role='In', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                        first_name='InF_name', last_name='InL_name', username='InUsername')
        self.assigned_user.save()
        self.one_char_user = User.objects.create_user(role='TA', email='EMAIL_TEST_ONE_CHAR', password='PASSWORD_TEST_ONE_CHAR',
                                                      first_name='O', last_name='Char', username='O')
        self.one_char_user.save()
    def test_ValidId(self):
        UserController.deleteUser(self.unassigned_user.username)
        self.assertNotIn(self.unassigned_user, User.objects.all())

    def test_InValidId_manyCharacters(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("aTotallyRealUserName")

    def test_NoId(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("")

    def test_InValidId_1Character(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("^")

    def test_ValidId_1Character(self):
        UserController.deleteUser(self.one_char_user.username)
        self.assertNotIn(self.one_char_user, User.objects.all())

    def test_checkIfRemovedFromCourses(self):
        UserController.deleteUser(self.assigned_user.username)
        for course_code, course_name in self.course_list:
            course = Course.objects.get(course_code=course_code)
            for section in CourseSection.objects.filter(course=course):
                self.assertNotEqual(section.instructor, self.assigned_user)

class TestSaveUser(TestCase):
    def setUp(self):
        self.valid_user_data_new = {
            'username': 'johndoe',
            'email': 'johndoe@example.com',
            'password': 'securepassword123',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'TA',
            'office_hours': '10 AM - 12 PM'
        }
        self.admin_user = User.objects.create_user(role='Admin', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                        first_name='AdminF_name', last_name='AdminL_name', username='AdminUsername')
        self.admin_user.save()
        self.unassigned_user = User.objects.create_user(role='TA', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                        first_name='TAF_name', last_name='TAL_name',
                                                        username='TAUsername')
        self.unassigned_user.save()

        self.assigned_user = User.objects.create_user(role='In', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                      first_name='InF_name', last_name='InL_name',
                                                      username='InUsername')
        self.assigned_user.save()

        self.one_char_user = User.objects.create_user(role='TA', email='EMAIL_TEST_ONE_CHAR',
                                                      password='PASSWORD_TEST_ONE_CHAR',
                                                      first_name='O', last_name='Char', username='O')
        self.one_char_user.save()
    """New User Portion"""
    def test_ValidUserFieldsNewUserPlusAdmin(self):
        newUser= UserController.saveUser(self.valid_user_data_new, self.admin_user)
        self.assertEqual(newUser.role, self.valid_user_data_new['role'])
    def test_InvalidUserFieldsNewUserPlusAdmin(self):
        pass
    """Edit User Portion"""

    def test_ValidUserIdPlusGoodEditsPlusAdminRequestor(self):
        pass

    def test_InvalidUserIdPlusGoodEditsPlusAdminRequestor(self):
        pass

    def test_ValidUserIdPlusBadEditsPlusAdminRequestor(self):
        pass

    def test_InvalidUserIdPlusBadEditsPlusAdminRequestor(self):
        pass

    def test_ValidUserIdPlusGoodEditsPlusTaRequestor(self):
        pass

    def test_InvalidUserIdPlusGoodEditsPlusTaRequestor(self):
        pass

    def test_ValidUserIdPlusBadEditsPlusTaRequestor(self):
        pass

    def test_InvalidUserIdPlusBadEditsPlusTaRequestor(self):
        pass

    def test_ValidUserIdPlusGoodEditsPlusInstructorRequestor(self):
        pass

    def test_InvalidUserIdPlusGoodEditsPlusInstructorRequestor(self):
        pass

    def test_ValidUserIdPlusBadEditsPlusInstructorRequestor(self):
        pass

    def test_InvalidUserIdPlusBadEditsPlusInstructorRequestor(self):
        pass


if __name__ == '__main__':
    import unittest

    unittest.main()