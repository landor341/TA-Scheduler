from django.test import TestCase
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
import django
django.setup()
from ta_scheduler.models import Course, CourseSection, User, TACourseAssignment, LabSection, TALabAssignment, Semester
from datetime import date
from core.local_data_classes import TACourseRef, UserRef, CourseRef
from core.user_controller.UserController import UserController

def create_user(role, user_count):
    user = User(
        role=role,
        first_name=str(user_count),
        last_name=str(user_count),
        password=str(user_count),
        username=str(user_count)
    )
    user.save()
    return user

def create_course_section(course_id, section_number, instructor):
    section = CourseSection(
        course_id=course_id,
        course_section_number=section_number,
        instructor=instructor,
        start_time="09:00",
        end_time="10:30",
        days="Mon, Wed"
    )
    section.save()
    return section

def create_lab_section(course, section_number):
    lab_section = LabSection(course=course, lab_section_number=section_number, start_time="13:00", end_time="15:00")
    lab_section.save()
    return lab_section

def create_ta_course_assignment(course, ta):
    ta_course_assignment = TACourseAssignment(course=course, grader_status=False, ta=ta)
    ta_course_assignment.save()
    return ta_course_assignment

def create_lab_assignment(lab_section, ta):
    lab_assignment = TALabAssignment(lab_section=lab_section, ta=ta)
    lab_assignment.save()
    return lab_assignment

def setup_database(course_list):
    """
    Generate test courses with sections, instructors, tas,
    Course assignments, and lab assignments
    """
    course_count = 0
    user_count = 0
    semester = Semester.objects.create(
        semester_name="semester_name", start_date=date(2024, 9, 1), end_date=date(2024, 12, 15)
    )
    for code, name in course_list:
        course = Course.objects.create(course_code=code, course_name=name, semester=semester)
        course.save()
        course_count += 1
        for i in range(course_count):
            instructor = create_user("Instructor", user_count)
            user_count += 1
            section = create_course_section(course.id, i, instructor)
            ta = create_user("TA", user_count)
            user_count += 1

            create_ta_course_assignment(course, ta)

            lab_section = create_lab_section(course, i)
            if i % 2 == 1:
                create_lab_assignment(lab_section, ta)

class TestGetUser(TestCase):
    def setUp(self):
        self.course_list = [
            ('Test1', 'Software Engineering'),
            ('Test2', 'Software Development'),
            ('Other3', 'Calculus 777'),
            ('1000000000', '7777777777'),
            ('CS101', 'Intro to CS')
        ]
        setup_database(self.course_list)
        self.unassigned_user = User.objects.create_user(role='Admin', email='EMAIL_TEST', password='PASSWORD_TEST',
                                                        first_name='AdminF_name', last_name='AdminL_name',
                                                        username='AdminUsername')
        self.unassigned_user.save()
        self.course = Course.objects.get(course_code='CS101')

    def setup_lab_assignments(self):
        # Creating a Lab Section and assigning it to TA
        self.semester = Semester.objects.create(semester_name='Fall 2023', start_date='2023-09-01',
                                                end_date='2023-12-31')
        self.instructor_user = User.objects.create_user(role='Instructor', email='INST_TEST', password='PASSWORD_TEST',
                                                        first_name='InstructorF_name', last_name='InstructorL_name',
                                                        username='InstructorUsername')
        self.ta_user = User.objects.create_user(role='TA', email='TA_TEST', password='PASSWORD_TEST',
                                                first_name='TAF_name', last_name='TAL_name', username='TAUsername')

        self.course_section = CourseSection.objects.create(
            course=self.course, instructor=self.instructor_user, course_section_number=1,
            start_time='09:00', end_time='10:00'
        )

        lab_section = LabSection.objects.create(
            course=self.course, lab_section_number=1, start_time='10:00', end_time='12:00'
        )
        TALabAssignment.objects.create(ta=self.ta_user, lab_section=lab_section)

    def test_NoInput(self):
        with self.assertRaises(ValueError):
            UserController.getUser(None)

    def test_InvalidInput(self):
        with self.assertRaises(ValueError):
            UserController.getUser("invalid_id")

    def test_validInputs(self):
        # Set up lab assignments to ensure users and related data are in place
        self.setup_lab_assignments()

        # Iterate over all users in the database
        for user in User.objects.all():
            print(f"Testing user: {user.username} with id {user.id}")

            # Fetch user data from UserController
            res = UserController.getUser(user.id)
            print(f"Result from UserController.getUser: {res}")

            # Check if the returned result is a dictionary
            if isinstance(res, dict):
                # Check 'courses' list
                self.assertIsInstance(res['courses'], list)
                for course in res['courses']:
                    course_tuple = (course.course_code, course.course_name)
                    print(f"Checking course: {course_tuple}")
                    self.assertIn(course_tuple, self.course_list)

                # Check 'course_sections' list
                self.assertIsInstance(res['course_sections'], list)
                for course_section in res['course_sections']:
                    print(f"Checking course section: {course_section}")
                    # Changes made here!
                    self.assertTrue(hasattr(course_section, 'section_number'))  # Verify section_number attribute
                    self.assertTrue(
                        isinstance(course_section.instructor, UserRef))  # Ensure instructor is a UserRef or None

                # Check 'lab_sections' list
                self.assertIsInstance(res['lab_sections'], list)
                for lab_section in res['lab_sections']:
                    print(f"Checking lab section: {lab_section}")
                    # Changes made here!
                    self.assertTrue(hasattr(lab_section, 'section_number'))  # Verify section_number attribute
                    self.assertTrue(
                        isinstance(lab_section.instructor, (UserRef, type(None))))  # Allow for None instructor

                # Additional checks for TA roles
                if user.role == 'TA':
                    print(f"User is a TA, checking lab assignments and course assignments for {user.username}.")
                    self.assertIsInstance(res['lab_assignments'], list)

                    for lab_assignment in res['lab_assignments']:
                        # Changes made here!
                        self.assertIsNotNone(lab_assignment)  # Ensure the assignment is not None

                    self.assertIsInstance(res['course_assignments'], list)
                    for course_assignment in res['course_assignments']:
                        print(f"Checking course assignment: {course_assignment}")
                        # These checks should align with the TACourseRef attributes
                        self.assertTrue(hasattr(course_assignment, 'course_code'))
                        self.assertTrue(hasattr(course_assignment, 'course_name'))

            else:
                self.fail('Expected result to be a dictionary.')

            # Prepare expected assignments for comparison
            expected_assignments = []
            # Fetch all TA assignments for a given user
            for assignment in TALabAssignment.objects.filter(ta=user):
                if user.role == "TA":
                    print(f"Processing TA assignment for {assignment.lab_section.course.course_code}")
                    instructor = None
                    course_section = CourseSection.objects.filter(course=assignment.lab_section.course).first()
                    if course_section and course_section.instructor:
                        instructor = UserRef(username=course_section.instructor.username,
                                             name=course_section.instructor.first_name + " " + course_section.instructor.last_name)

                    is_grader = TACourseAssignment.objects.filter(ta=user, course=assignment.lab_section.course).first()
                    is_grader = is_grader.grader_status if is_grader and is_grader.grader_status else False

                    labs = [lab.lab_section.lab_section_number for lab in TALabAssignment.objects.filter(ta=user)]

                    print(f"Expected lab sections for TA: {labs}")

                    expected_assignments.append(
                        TACourseRef(
                            course_code=assignment.lab_section.course.course_code,
                            course_name=assignment.lab_section.course.course_name,
                            instructor=instructor,
                            is_grader=is_grader,
                            assigned_lab_sections=labs
                        )
                    )

                    # Check if the current course is correctly included in expected assignments
                    print(f"Expected assignments: {expected_assignments}")
                    self.assertIn(
                        TACourseRef(
                            course_code=assignment.lab_section.course.course_code,
                            course_name=assignment.lab_section.course.course_name,
                            instructor=instructor,
                            is_grader=is_grader,
                            assigned_lab_sections=labs
                        ), expected_assignments
                    )
                else:
                    print(f"Non-TA user, checking course reference.")
                    self.assertIn(
                        CourseRef(
                            course_code=assignment.lab_section.course.course_code,
                            course_name=assignment.lab_section.course.course_name,
                        ), expected_assignments
                    )
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

    def test_searchEmptyString(self):
        with self.assertRaises(ValueError):
            UserController.searchUser("")

    def test_searchPartialUsers(self):
        result = UserController.searchUser("In")
        self.assertTrue(
            all("in" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'in': {[(user.username, user.name) for user in result]}"
        )

    def test_emptySearch(self):
        result = UserController.searchUser("NonExistentUser")
        self.assertEqual(len(result), 0)

    def test_ValidString1Character(self):
        result = UserController.searchUser("A")
        self.assertTrue(
            all("a" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'a': {[(user.username, user.name) for user in result]}"
        )

    def test_ValidString1Character0User(self):
        result = UserController.searchUser("0")
        self.assertTrue(
            all("0" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain '0': {[(user.username, user.name) for user in result]}"
        )

    def test_ValidStringFullUserName(self):
        result = UserController.searchUser("AdminUsername")
        self.assertTrue(
            all("adminusername" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'adminusername': {[(user.username, user.name) for user in result]}"
        )

    def test_ValidStringFullFirstName(self):
        result = UserController.searchUser("AdminF_name")
        self.assertTrue(
            all("adminf_name" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'adminf_name': {[(user.username, user.name) for user in result]}"
        )

    def test_ValidStringFullLastName(self):
        result = UserController.searchUser("AdminL_name")
        self.assertTrue(
            all("adminl_name" in (user.username + user.name).lower() for user in result),
            f"Usernames or names in the result do not all contain 'adminl_name': {[(user.username, user.name) for user in result]}"
        )

    def test_ValidStringWierd(self):
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
        setup_database(self.course_list)
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
        UserController.deleteUser(self.unassigned_user.id)
        self.assertNotIn(self.unassigned_user, User.objects.all())

    def test_InValidId_manyCharacters(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("9999999999999999999999999")

    def test_NoId(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("")

    def test_InValidId_1Character(self):
        with self.assertRaises(ValueError):
            UserController.deleteUser("^")

    def test_ValidId_1Character(self):
        UserController.deleteUser(self.one_char_user.id)
        self.assertNotIn(self.one_char_user, User.objects.all())

    def test_checkIfRemovedFromCourses(self):
        UserController.deleteUser(self.assigned_user.id)
        for course_code, course_name in self.course_list:
            course = Course.objects.get(course_code=course_code)
            for section in CourseSection.objects.filter(course=course):
                self.assertNotEqual(section.instructor, self.assigned_user)


class TestSaveUser(TestCase):

    def setUp(self):
        self.admin_user = self._create_and_save_user('Admin', 'admin@test.com', 'password123', 'Admin', 'User',
                                                     'adminuser')
        self.unassigned_user = self._create_and_save_user('TA', 'ta@test.com', 'password123', 'Unassigned', 'TA',
                                                          'unassignedta')
        self.assigned_user = self._create_and_save_user('Instructor', 'instructor@test.com', 'password123', 'Assigned',
                                                        'User', 'assigneduser')
        self.one_char_user = self._create_and_save_user('TA', 'one@test.com', 'password123', 'X', 'Y', 'oneuser')

        self.valid_user_data_new = {
            'username': 'newuser',
            'role': 'TA',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@test.com',
            'password': 'password123'
        }

        self.user_data = {
            'username': 'updateduser',
            'role': 'Instructor',
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updateduser@test.com',
            'password': 'password123'
        }

    # Helper methods
    def _create_and_save_user(self, role, email, password, first_name, last_name, username):
        user = User.objects.create(
            role=role, email=email, password=password,
            first_name=first_name, last_name=last_name, username=username
        )
        return user

    def _verify_user_fields(self, user, user_data):
        self.assertEqual(user.username, user_data['username'])
        self.assertEqual(user.first_name, user_data['first_name'])
        self.assertEqual(user.last_name, user_data['last_name'])
        self.assertEqual(user.role, user_data['role'])
        self.assertEqual(user.email, user_data['email'])

    # Test methods
    def test_valid_user_fields_new_user_plus_admin(self):
        new_user = UserController.saveUser(self.valid_user_data_new, self.admin_user)
        self._verify_user_fields(new_user, self.valid_user_data_new)

    def test_invalid_user_fields_new_user_plus_admin(self):
        new_user = UserController.saveUser(self.valid_user_data_new, self.admin_user)
        with self.assertRaises(ValidationError):
            UserController.saveUser(self.valid_user_data_new, self.admin_user)

    def test_valid_user_id_plus_good_edits_plus_admin_requestor_other_user(self):
        self.user_data['id'] = self.unassigned_user.id
        self.unassigned_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(self.unassigned_user, self.user_data)

    def test_valid_user_id_plus_bad_edits_plus_admin_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        with self.assertRaises(ValidationError):
            self.unassigned_user = UserController.saveUser(self.user_data, self.admin_user)

    def test_invalid_user_id_plus_good_edits_plus_admin_requestor_other_user(self):
        self.user_data['id'] = 99999
        with self.assertRaises(ObjectDoesNotExist):
            self.unassigned_user = UserController.saveUser(self.user_data, self.admin_user)

    def test_invalid_user_id_plus_bad_edits_plus_admin_requestor_other_user(self):
        new_user = UserController.saveUser(self.user_data, self.admin_user)
        self.user_data['id'] = 99999
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
        self.user_data['role'] = 'Instructor'
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.admin_user)

    def test_admin_cannot_change_other_admin_role(self):
        admin_user_2 = self._create_and_save_user(
            'Admin', 'admin2@test.com', 'password123', 'Admin2', 'User', 'adminuser2'
        )
        self.user_data['id'] = admin_user_2.id
        self.user_data['role'] = 'Instructor'
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.admin_user)

    def test_admin_can_change_role_to_instructor(self):
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['role'] = 'Instructor'
        changed_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(changed_user, self.user_data)

    def test_admin_can_change_role_to_ta(self):
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['role'] = 'TA'
        changed_user = UserController.saveUser(self.user_data, self.admin_user)
        self._verify_user_fields(changed_user, self.user_data)

    def test_users_cannot_change_any_role(self):
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['role'] = 'Admin'
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.unassigned_user)
        self.user_data['id'] = self.assigned_user.id
        with self.assertRaises(PermissionDenied):
            UserController.saveUser(self.user_data, self.assigned_user)

    def test_username_conflict_when_user_edits_own_info(self):
        conflicting_user = self._create_and_save_user('TA', 'conflict@test.com', 'password123', 'ConflictFirst',
                                                      'ConflictLast', 'conflictusername')
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['username'] = conflicting_user.username
        self.user_data['role'] = self.unassigned_user.role
        with self.assertRaises(ValidationError):
            UserController.saveUser(self.user_data, self.unassigned_user)

    def test_email_conflict_when_user_edits_own_info(self):
        conflicting_user = self._create_and_save_user('TA', 'conflict@test.com', 'password123', 'ConflictFirst',
                                                      'ConflictLast', 'conflictusername')
        self.user_data['id'] = self.unassigned_user.id
        self.user_data['email'] = conflicting_user.email
        self.user_data['role'] = self.unassigned_user.role
        with self.assertRaises(ValidationError):
            UserController.saveUser(self.user_data, self.unassigned_user)