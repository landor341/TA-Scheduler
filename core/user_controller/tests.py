# TODO: Implement user controller tests
from django.test import TestCase
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
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


class TestSearchUserCaseInsensitive(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(role='Admin', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                        first_name='AdminF_name', last_name='AdminL_name', username='AdminUsername')
        self.admin_user.save()
        self.unassigned_user = User.objects.create_user(role='TA', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                        first_name='TAF_name', last_name='TAL_name',
                                                        username='TAUsername')
        self.unassigned_user.save()

        self.assigned_user = User.objects.create_user(role='Instructor', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                      first_name='InF_name', last_name='InL_name',
                                                      username='InUsername')
        self.assigned_user.save()

        self.one_char_user_ta = User.objects.create_user(role='TA', email='EMAIL_TEST_ONE_CHAR',
                                                      password='PASSWORD_TEST_ONE_CHAR',
                                                      first_name='7O', last_name='70', username='7O')
        self.one_char_user_ta.save()
        self.one_char_user_in = User.objects.create_user(role='Instructor', email='EMAIL_TEST_ONE_CHAR',
                                                      password='PASSWORD_TEST_ONE_CHAR',
                                                      first_name='O', last_name='0', username='O')
        self.one_char_user_in.save()

    def test_searchEmptyString(self):
        with self.assertRaises(ValueError):
            UserController.searchUser("")

    def test_searchPartialUsers(self):
        result = UserController.searchUser("In")
        self.assertTrue(all("in" in (user.username + user.first_name + user.last_name).lower() for user in result),
                        f"Usernames, first names, or last names in the result do not all contain 'in': "
                        f"{[(user.username, user.first_name, user.last_name) for user in result]}")

    def test_emptySearch(self):
        result = UserController.searchUser("NonExistentUser")
        self.assertEqual(len(result), 0)

    def test_ValidString1Character(self):
        result = UserController.searchUser("A")
        # Assert that the search string is found in the username, firstname, or lastname
        self.assertTrue(all("a" in (user.username + user.first_name + user.last_name).lower() for user in result),
                        f"Usernames, first names, or last names in the result do not all contain 'a': "
                        f"{[(user.username, user.first_name, user.last_name) for user in result]}")
    def test_ValidString1Character0User(self):
        result = UserController.searchUser("0")
        # Assert that the search string is found in the username, firstname, or lastname
        self.assertTrue(all("0" in (user.username + user.first_name + user.last_name).lower() for user in result),
                        f"Usernames, first names, or last names in the result do not all contain '0': "
                        f"{[(user.username, user.first_name, user.last_name) for user in result]}")

    def test_ValidStringFullUserName(self):
        result = UserController.searchUser("AdminUsername")
        # Assert that the search string is found in the username, firstname, or lastname
        self.assertTrue(all("adminusername" in (user.username + user.first_name + user.last_name).lower() for user in result),
                        f"Usernames, first names, or last names in the result do not all contain 'adminusername': "
                        f"{[(user.username, user.first_name, user.last_name) for user in result]}")

    def test_ValidStringFullFirstName(self):
        result = UserController.searchUser("AdminF_name")
        # Assert that the search string is found in the username, firstname, or lastname
        self.assertTrue(
            all("adminf_name" in (user.username + user.first_name + user.last_name).lower() for user in result),
            f"Usernames, first names, or last names in the result do not all contain 'adminf_name': "
            f"{[(user.username, user.first_name, user.last_name) for user in result]}")

    def test_ValidStringFullLasttName(self):
        result = UserController.searchUser("AdminL_name")
        # Assert that the search string is found in the username, firstname, or lastname
        self.assertTrue(
            all("adminl_name" in (user.username + user.first_name + user.last_name).lower() for user in result),
            f"Usernames, first names, or last names in the result do not all contain 'adminl_name': "
            f"{[(user.username, user.first_name, user.last_name) for user in result]}")

    def test_ValidStringWierd(self):
        result = UserController.searchUser("tAuSeRnAmE")
        # Assert that the search string is found in the username, firstname, or lastname
        self.assertTrue(
            all("tausername" in (user.username + user.first_name + user.last_name).lower() for user in result),
            f"Usernames, first names, or last names in the result do not all contain 'tausername': "
            f"{[(user.username, user.first_name, user.last_name) for user in result]}")

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
        self.assigned_user = User.objects.create_user(role='Instructor', email='EMAIL_TEST', password='PASSWORD_TEST',
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
        self.TA = 'TA'
        self.INSTRUCTOR = 'Instructor'
        self.ADMIN = 'Admin'

        self.valid_user_data_new = {
            'username': 'johndoe',
            'email': 'johndoe@example.com',
            'password': 'securepassword123',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': self.TA,
            'office_hours': '10 AM - 12 PM'
        }
        self.user_data = {
            'email': 'new.email@test.com',
            'first_name': 'NewFirstName',
            'last_name': 'NewLastName',
            'role': self.INSTRUCTOR,
            'password': 'newPassword123',
            'username': 'newUsername'
        }
        self.admin_user = self._create_and_save_user(self.ADMIN, 'EMAIL_TEST', 'PASSWORD_TEST', 'AdminF_name',
                                                     'AdminL_name',
                                                     'AdminUsername')
        self.unassigned_user = self._create_and_save_user(self.TA, 'EMAIL_TEST', 'PASSWORD_TEST', 'TAF_name',
                                                          'TAL_name',
                                                          'TAUsername')
        self.assigned_user = self._create_and_save_user(self.INSTRUCTOR, 'EMAIL_TEST', 'PASSWORD_TEST', 'InF_name',
                                                        'InL_name', 'InUsername')
        self.one_char_user = self._create_and_save_user(self.TA, 'EMAIL_TEST_ONE_CHAR', 'PASSWORD_TEST_ONE_CHAR', 'O',
                                                        'Char', 'O')

    def _create_and_save_user(self, role, email, password, first_name, last_name, username):
        user = User.objects.create_user(
            role=role,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        user.save()
        return user

    def _verify_user_fields(self, user, expected_data):
        for key, expected_value in expected_data.items():
            actual_value = getattr(user, key)
            print(f"Checking field '{key}': expected '{expected_value}', got '{actual_value}'")
            self.assertEqual(actual_value, expected_value,
                             f"Field '{key}' does not match: expected '{expected_value}', got '{actual_value}'")


    #New User Section
    def test_valid_user_fields_new_user_plus_admin(self):
        new_user = UserController.saveUser(self.valid_user_data_new, self.admin_user)
        self._verify_user_fields(new_user, self.valid_user_data_new)

    def test_invalid_user_fields_new_user_plus_admin(self):
        new_user = UserController.saveUser(self.valid_user_data_new, self.admin_user)
        with self.assertRaises(ValidationError):
            UserController.saveUser(self.valid_user_data_new, self.admin_user)


    #Edit User Section
    def test_valid_user_id_plus_good_edits_plus_admin_requestor_other_user(self):
        self.user_data['id'] = self.unassigned_user.id
        self.unassigned_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(self.unassigned_user, self.user_data)

    def test_valid_user_id_plus_bad_edits_plus_admin_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        with self.assertRaises(ValidationError):
            self.unassigned_user= UserController.saveUser(self.user_data, self.admin_user)

    def test_invalid_user_id_plus_good_edits_plus_admin_requestor_other_user(self):
        self.user_data['id']=99999
        with self.assertRaises(ObjectDoesNotExist):
            self.unassigned_user = UserController.saveUser(self.user_data, self.admin_user)

    def test_invalid_user_id_plus_bad_edits_plus_admin_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        self.user_data['id']=99999
        with self.assertRaises((ObjectDoesNotExist, ValidationError)):
            self.unassigned_user = UserController.saveUser(self.user_data, self.admin_user)

    def test_valid_user_id_plus_good_edits_plus_ta_requestor_other_user(self):
        self.user_data['id'] = self.unassigned_user.id
        with self.assertRaises(PermissionDenied):
            self.unassigned_user = UserController.saveUser(self.user_data, self.one_char_user)

    def test_invalid_user_id_plus_good_edits_plus_ta_requestor_other_user(self):
        self.user_data['id'] = 99999
        with self.assertRaises((ObjectDoesNotExist, PermissionDenied)):
            self.unassigned_user = UserController.saveUser(self.user_data, self.one_char_user)

    def test_valid_user_id_plus_bad_edits_plus_ta_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        with self.assertRaises((PermissionDenied, ValidationError)):
            self.unassigned_user = UserController.saveUser(self.user_data, self.one_char_user)

    def test_invalid_user_id_plus_bad_edits_plus_ta_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        self.user_data['id'] = 99999
        with self.assertRaises((ObjectDoesNotExist, ValidationError, PermissionDenied)):
            self.unassigned_user = UserController.saveUser(self.user_data, self.one_char_user)

    def test_valid_user_id_plus_good_edits_plus_instructor_requestor_other_user(self):
        self.user_data['id'] = self.unassigned_user.id
        with self.assertRaises(PermissionDenied):
            self.unassigned_user = UserController.saveUser(self.user_data, self.assigned_user)

    def test_invalid_user_id_plus_good_edits_plus_instructor_requestor_other_user(self):
        self.user_data['id'] = 99999
        with self.assertRaises((ObjectDoesNotExist, PermissionDenied)):
            self.unassigned_user = UserController.saveUser(self.user_data, self.assigned_user)

    def test_valid_user_id_plus_bad_edits_plus_instructor_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        with self.assertRaises((PermissionDenied, ValidationError)):
            self.unassigned_user = UserController.saveUser(self.user_data, self.assigned_user)

    def test_invalid_user_id_plus_bad_edits_plus_instructor_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        self.user_data['id'] = 99999
        with self.assertRaises((ObjectDoesNotExist, ValidationError, PermissionDenied)):
            self.unassigned_user = UserController.saveUser(self.user_data, self.assigned_user)

    #Users editing their own information section
    def test_ta_user_can_edit_own_info(self):
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['role'] = self.unassigned_user.role
        edited_user = UserController.saveUser(self.user_data, self.unassigned_user)
        self._verify_user_fields(edited_user, self.user_data)

    def test_instructor_user_can_edit_own_info(self):
        self.user_data['id'] = self.assigned_user.id
        self.assigned_user = UserController.saveUser(self.user_data, self.assigned_user)
        self._verify_user_fields(self.assigned_user, self.user_data)

    def test_admin_user_can_edit_own_info(self):
        self.user_data['id'] = self.admin_user.id
        self.user_data['role'] = self.admin_user.role
        edited_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(edited_user, self.user_data)

    def test_admin_cannot_change_own_role(self):
        self.user_data['id'] = self.admin_user.id
        self.user_data['role'] = self.INSTRUCTOR

        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.admin_user)

    def test_admin_cannot_change_other_admin_role(self):
        # Create a second admin
        admin_user_2 = self._create_and_save_user(self.ADMIN, 'EMAIL_TEST_2', 'PASSWORD_TEST_2', 'AdminF_name_2',
                                                  'AdminL_name_2', 'AdminUsername_2')

        self.user_data['id'] = admin_user_2.id
        self.user_data['role'] = self.INSTRUCTOR

        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.admin_user)

    def test_admin_can_change_role_to_instructor(self):
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['role'] = self.INSTRUCTOR

        changed_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(changed_user, self.user_data)

    def test_admin_can_change_role_to_ta(self):
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['role'] = self.TA

        changed_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(changed_user, self.user_data)

    def test_users_cannot_change_any_role(self):
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['role'] = self.ADMIN

        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.unassigned_user)

        self.user_data['id'] = self.assigned_user.id
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.assigned_user)

    def test_username_conflict_when_user_edits_own_info(self):
        conflicting_user = self._create_and_save_user(self.TA, 'conflict@test.com', 'PASSWORD', 'ConflictFirst',
                                                      'ConflictLast', 'conflictusername')
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['username'] = conflicting_user.username
        self.user_data['role'] = self.unassigned_user.role
        with self.assertRaises(ValidationError):
            UserController.saveUser(self.user_data, self.unassigned_user)

    def test_email_conflict_when_user_edits_own_info(self):
        conflicting_user = self._create_and_save_user(self.TA, 'conflict@test.com', 'PASSWORD', 'ConflictFirst',
                                                      'ConflictLast', 'conflictusername')
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['email'] = conflicting_user.email
        self.user_data['role'] = self.unassigned_user.role
        with self.assertRaises(ValidationError):
            UserController.saveUser(self.user_data, self.unassigned_user)


if __name__ == '__main__':
    import unittest

    unittest.main()