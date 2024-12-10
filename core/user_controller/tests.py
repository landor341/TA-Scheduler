import django
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.test import TestCase

django.setup()
from datetime import date
from ta_scheduler.models import (
    Course, CourseSection, User, TACourseAssignment, LabSection, TALabAssignment, Semester)
from core.user_controller.UserController import UserController


# Helper Functions
def _create_user(role, user_count):
    return User.objects.create(
        role=role,
        first_name=str(user_count),
        last_name=str(user_count),
        password=str(user_count),
        username=str(user_count),
        phone=str(user_count),
        address=str(user_count),
        office_hours=str(user_count)
    )


def _create_course_section(course, section_number, instructor):
    return CourseSection.objects.create(
        course=course,
        course_section_number=section_number,
        instructor=instructor,
        start_time="09:00",
        end_time="10:30",
        days="Mon, Wed"
    )


def _create_lab_section(course, section_number):
    return LabSection.objects.create(
        course=course,
        lab_section_number=section_number,
        start_time="13:00",
        end_time="15:00"
    )


def _create_ta_course_assignment(course, ta):
    return TACourseAssignment.objects.create(course=course, grader_status=False, ta=ta)


def _create_lab_assignment(lab_section, ta):
    return TALabAssignment.objects.create(lab_section=lab_section, ta=ta)


def _setup_database(course_list):
    course_count = 0
    user_count = 0
    semester = Semester.objects.create(
        semester_name="semester_name", start_date=date(2024, 9, 1),
        end_date=date(2024, 12, 15))

    for code, name in course_list:
        course = Course.objects.create(course_code=code, course_name=name, semester=semester)
        course_count += 1
        for i in range(course_count):
            instructor = _create_user("Instructor", user_count)
            user_count += 1
            _create_course_section(course, i, instructor)
            ta = _create_user("TA", user_count)
            user_count += 1
            _create_ta_course_assignment(course, ta)
            lab_section = _create_lab_section(course, i)
            if i % 2 == 1:
                _create_lab_assignment(lab_section, ta)


class TestGetUser(TestCase):
    def setUp(self):
        self.course_list = [
            ('Test1', 'Software Engineering'),
            ('Test2', 'Software Development'),
            ('Other3', 'Calculus 777'),
            ('1000000000', '7777777777'),
            ('CS101', 'Intro to CS')
        ]
        _setup_database(self.course_list)
        self.admin_user = _create_user("Admin", 11111)
        self.instructor = _create_user("Instructor", 88888)
        self.ta = _create_user("TA", 99999)
        self.course = Course.objects.get(course_code='CS101')
        _create_course_section(self.course, 0, self.instructor)
        _create_course_section(self.course, 1, self.admin_user)
        _create_ta_course_assignment(self.course, self.ta)
        self.lab_section = _create_lab_section(self.course, 0)
        _create_lab_assignment(self.lab_section, self.ta)

    def test_validAssignments_for_instructor(self):
        profile = UserController.getUser(self.instructor.username, self.admin_user)
        self._assert_instructor_profile_fields(profile, self.instructor)
        self._assert_course_overviews(profile.courses_assigned, expected_course_codes=['CS101'],
                                      expected_lab_sections=True)

    def test_validAssignments_for_ta(self):
        profile = UserController.getUser(self.ta.username, self.admin_user)
        self._assert_ta_profile_fields(profile, self.ta)
        self._assert_course_overviews(profile.courses_assigned, expected_course_codes=['CS101'],
                                      expected_lab_sections=True)

    def test_validAssignments_for_admin(self):
        profile = UserController.getUser(self.admin_user.username, self.admin_user)
        self._assert_admin_profile_fields(profile, self.admin_user)
        self._assert_course_overviews(profile.courses_assigned, expected_course_codes=['CS101'],
                                      expected_lab_sections=True)

    def _assert_instructor_profile_fields(self, profile, user):
        self.assertEqual(profile.role, 'Instructor')
        self._assert_private_profile_fields(profile, user)

    def _assert_ta_profile_fields(self, profile, user):
        self.assertEqual(profile.role, 'TA')
        self._assert_private_profile_fields(profile, user)

    def _assert_admin_profile_fields(self, profile, user):
        self.assertEqual(profile.role, 'Admin')
        self._assert_private_profile_fields(profile, user)

    def _assert_course_overviews(self, course_overviews, expected_course_codes, expected_lab_sections=False):
        self.assertIsInstance(course_overviews, list)
        actual_course_codes = [overview.code for overview in course_overviews]
        self.assertEqual(set(actual_course_codes), set(expected_course_codes), "Course overviews do not match")

        for overview in course_overviews:
            if expected_lab_sections:
                self.assertGreater(len(overview.lab_sections), 0, "Expected lab sections, but none found")
            else:
                self.assertEqual(len(overview.lab_sections), 0, "Found lab sections, but none were expected")

    def _assert_private_profile_fields(self, profile, user):
        self.assertEqual(profile.address, user.address)
        self.assertEqual(profile.phone, user.phone)


class TestSearchUserCaseInsensitive(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            role='Admin', email='EMAIL_TEST', password='PASSWORD_TEST',
            first_name='AdminF_name', last_name='AdminL_name', username='AdminUsername')
        self.unassigned_user = User.objects.create_user(
            role='TA', email='EMAIL_TEST', password='PASSWORD_TEST',
            first_name='TAF_name', last_name='TAL_name', username='TAUsername')
        self.assigned_user = User.objects.create_user(
            role='Instructor', email='EMAIL_TEST', password='PASSWORD_TEST',
            first_name='InF_name', last_name='InL_name', username='InUsername')
        self.one_char_user_ta = User.objects.create_user(
            role='TA', email='EMAIL_TEST_ONE_CHAR', password='PASSWORD_TEST_ONE_CHAR',
            first_name='7O', last_name='70', username='7O')
        self.one_char_user_in = User.objects.create_user(
            role='Instructor', email='EMAIL_TEST_ONE_CHAR', password='PASSWORD_TEST_ONE_CHAR',
            first_name='O', last_name='0', username='O')

    def test_search_empty_string(self):
        result = UserController.searchUser("")
        self.assertTrue(
            all("" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'in': {[(user.username, user.name)for user in result]}")

    def test_search_partial_users(self):
        result = UserController.searchUser("In")
        self.assertTrue(
            all("in" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'in': {[(user.username, user.name)for user in result]}")

    def test_empty_search(self):
        result = UserController.searchUser("NonExistentUser")
        self.assertEqual(len(result), 0)

    def test_valid_string_1_character(self):
        result = UserController.searchUser("A")
        self.assertTrue(
            all("a" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'a': {[(user.username, user.name)for user in result]}"
        )

    def test_valid_string_1_character_0_user(self):
        result = UserController.searchUser("0")
        self.assertTrue(
            all("0" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain '0': {[(user.username, user.name)for user in result]}"
        )

    def test_valid_string_full_username(self):
        result = UserController.searchUser("AdminUsername")
        self.assertTrue(
            all("adminusername" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'adminusername': {[(user.username, user.name) for user in result]}"
        )

    def test_valid_string_full_first_name(self):
        result = UserController.searchUser("AdminF_name")
        self.assertTrue(
            all("adminf_name" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'adminf_name': {[(user.username, user.name) for user in result]}"
        )

    def test_valid_string_full_last_name(self):
        result = UserController.searchUser("AdminL_name")
        self.assertTrue(
            all("adminl_name" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'adminl_name': {[(user.username, user.name) for user in result]}"
        )

    def test_valid_string_wierd(self):
        result = UserController.searchUser("tAuSeRnAmE")
        self.assertTrue(
            all("tausername" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'tausername': {[(user.username, user.name) for user in result]}"
        )


class TestDeleteUser(TestCase):
    def setUp(self):
        self.course_list = [
            ('Test1', 'Software Engineering'),
            ('Test2', 'Software Development'),
            ('Other3', 'Calculus 777'),
            ('1000000000', '7777777777')
        ]
        _setup_database(self.course_list)
        self.unassigned_user = User.objects.create_user(
            role='TA', email='EMAIL_TEST', password='PASSWORD_TEST',
            first_name='TAF_name', last_name='TAL_name', username='TAUsername')
        self.assigned_user = User.objects.create_user(
            role='Instructor', email='EMAIL_TEST', password='PASSWORD_TEST',
            first_name='InF_name', last_name='InL_name', username='InUsername')
        self.one_char_user = User.objects.create_user(
            role='TA', email='EMAIL_TEST_ONE_CHAR', password='PASSWORD_TEST_ONE_CHAR',
            first_name='O', last_name='Char', username='O')
        self.admin_user = User.objects.create_user(
            role='Admin', email='admin@example.com', password='AdminPass',
            first_name='Admin', last_name='User', username='adminuser')

    def test_valid_username(self):
        UserController.deleteUser(self.unassigned_user.username, self.admin_user)
        self.assertNotIn(self.unassigned_user, User.objects.all())

    def test_invalid_username_many_characters(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("nonexistentusername", self.admin_user)

    def test_no_username(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("", self.admin_user)

    def test_invalid_username_1_character(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("^", self.admin_user)

    def test_valid_username_1_character(self):
        UserController.deleteUser(self.one_char_user.username, self.admin_user)
        self.assertNotIn(self.one_char_user, User.objects.all())

    def test_check_if_removed_from_courses(self):
        UserController.deleteUser(self.assigned_user.username, self.admin_user)
        for course_code, course_name in self.course_list:
            course = Course.objects.get(course_code=course_code)
            for section in CourseSection.objects.filter(course=course):
                self.assertNotEqual(section.instructor, self.assigned_user)

    def test_non_admin_user_cannot_delete(self):
        with self.assertRaises(PermissionDenied):
            UserController.deleteUser(self.assigned_user.username, self.unassigned_user)


class TestSaveUser(TestCase):
    def setUp(self):
        self.admin_user = self._create_and_save_user(
            'Admin', 'admin@test.com', 'password123', 'Admin', 'User', 'adminuser'
        )
        self.unassigned_user = self._create_and_save_user(
            'TA', 'ta@test.com', 'password123', 'Unassigned', 'TA', 'unassignedta'
        )
        self.assigned_user = self._create_and_save_user(
            'Instructor', 'instructor@test.com', 'password123', 'Assigned',
            'User', 'assigneduser'
        )
        self.one_char_user = self._create_and_save_user(
            'TA', 'one@test.com', 'password123', 'X', 'Y', 'oneuser'
        )

        self.valid_user_data_new = {
            'username': 'newuser',
            'role': 'TA',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@test.com',
            'password': 'password123',
            'phone': '',
            'address': '',
        }

        self.user_data = {
            'username': 'updateduser',
            'role': 'Instructor',
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updateduser@test.com',
            'password': 'password123',
            'phone': '',
            'address': ''
        }

    # Helper methods
    def _create_and_save_user(self, role, email, password, first_name, last_name, username, phone=None, address=None):
        return User.objects.create(
            role=role, email=email, password=password,
            first_name=first_name, last_name=last_name, username=username,
            phone=phone, address=address
        )

    def _verify_user_fields(self, user, user_data):
        self.assertEqual(user.username, user_data['username'])
        self.assertEqual(user.first_name, user_data['first_name'])
        self.assertEqual(user.last_name, user_data['last_name'])
        self.assertEqual(user.role, user_data['role'])
        self.assertEqual(user.email, user_data['email'])
        self.assertEqual(user.phone, user_data['phone'])
        self.assertEqual(user.address, user_data['address'])

    def test_save_user_with_phone_and_address(self):
        self.user_data['phone'] = '1234567890'
        self.user_data['address'] = '123 Main St, Springfield, USA'
        updated_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(updated_user, self.user_data)

    def test_update_user_phone_and_address(self):
        self.user_data['username'] = self.unassigned_user.username
        self.user_data['phone'] = '9876543210'
        self.user_data['address'] = '456 Elm St, Metropolis, USA'
        updated_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(updated_user, self.user_data)

    def test_valid_user_fields_new_user_plus_admin(self):
        new_user = UserController.saveUser(self.valid_user_data_new, self.admin_user)
        self._verify_user_fields(new_user, self.valid_user_data_new)

    def test_valid_user_id_plus_bad_edits_plus_ta_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        with self.assertRaises(PermissionDenied):
            self.unassigned_user = UserController.saveUser(self.user_data, self.one_char_user)

    def test_valid_user_id_plus_good_edits_plus_instructor_requestor_other_user(self):
        self.user_data['username'] = self.unassigned_user.username
        with self.assertRaises(PermissionDenied):
            self.unassigned_user = UserController.saveUser(self.user_data, self.assigned_user)

    def test_invalid_user_id_plus_good_edits_plus_instructor_requestor_other_user(self):
        self.user_data['id'] = 99999
        with self.assertRaises(PermissionDenied):
            self.unassigned_user = UserController.saveUser(self.user_data, self.assigned_user)

    def test_valid_user_id_plus_bad_edits_plus_instructor_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        with self.assertRaises(PermissionDenied):
            self.unassigned_user = UserController.saveUser(self.user_data, self.assigned_user)

    def test_invalid_user_id_plus_bad_edits_plus_instructor_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        self.user_data['id'] = 99999
        with self.assertRaises(PermissionDenied):
            self.unassigned_user = UserController.saveUser(self.user_data, self.assigned_user)

    def test_ta_user_can_edit_own_info(self):
        self.user_data['username'] = self.unassigned_user.username
        self.user_data['role'] = self.unassigned_user.role
        edited_user = UserController.saveUser(self.user_data, self.unassigned_user)
        self._verify_user_fields(edited_user, self.user_data)

    def test_instructor_user_can_edit_own_info(self):
        self.user_data['username'] = self.assigned_user.username
        self.assigned_user = UserController.saveUser(self.user_data, self.assigned_user)
        self._verify_user_fields(self.assigned_user, self.user_data)

    def test_admin_user_can_edit_own_info(self):
        self.user_data['username'] = self.admin_user.username
        self.user_data['role'] = self.admin_user.role
        edited_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(edited_user, self.user_data)

    def test_admin_cannot_change_own_role(self):
        self.user_data['username'] = self.admin_user.username
        self.user_data['role'] = 'Instructor'
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.admin_user)

    def test_admin_cannot_change_other_admin_role(self):
        admin_user_2 = self._create_and_save_user(
            'Admin', 'admin2@test.com', 'password123', 'Admin2', 'User', 'adminuser2'
        )
        self.user_data['username'] = admin_user_2.username
        self.user_data['role'] = 'Instructor'
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.admin_user)

    def test_admin_can_change_role_to_instructor(self):
        self.user_data['username'] = self.unassigned_user.username
        self.user_data['role'] = 'Instructor'
        changed_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(changed_user, self.user_data)

    def test_admin_can_change_role_to_ta(self):
        self.user_data['username'] = self.unassigned_user.username
        self.user_data['role'] = 'TA'
        changed_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(changed_user, self.user_data)

    def test_users_cannot_change_any_role(self):
        self.user_data['username'] = self.unassigned_user.username
        self.user_data['role'] = 'Admin'
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.unassigned_user)
        self.user_data['username'] = self.assigned_user.username
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.assigned_user)

    def test_email_conflict_when_user_edits_own_info(self):
        conflicting_user = self._create_and_save_user(
            'TA', 'conflict@test.com', 'password123', 'ConflictFirst',
            'ConflictLast', 'conflictusername'
        )
        self.user_data['username'] = self.unassigned_user.username
        self.user_data['email'] = conflicting_user.email
        self.user_data['role'] = self.unassigned_user.role
        with self.assertRaises(ValidationError):
            UserController.saveUser(self.user_data, self.unassigned_user)