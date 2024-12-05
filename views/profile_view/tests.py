from django.test import TestCase, Client
from django.urls import reverse

from core.local_data_classes import UserProfile, PrivateUserProfile
from ta_scheduler.models import User, Semester, Course, TACourseAssignment, CourseSection, LabSection, TALabAssignment


class ProfileAssertions(TestCase):
    def setUp(self):
        print("Setting up test client.")
        self.client = Client()

    def _loginAsAdmin(self):
        print("Creating and logging in as Admin user.")
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com',
            first_name='Test', last_name='User', role='Admin', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)

    def _loginAsInstructor(self):
        print("Creating and logging in as Instructor user.")
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com',
            first_name='Test', last_name='User', role='Instructor', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)

    def _loginAsTA(self):
        print("Creating and logging in as TA user.")
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com',
            first_name='Test', last_name='User', role='TA', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)

    def _assertSameUser(self, user, profile: UserProfile | PrivateUserProfile):
        print(f"Asserting user details for {user.username}.")
        if isinstance(profile, PrivateUserProfile):
            self.assertEqual(user.address, profile.address, "Incorrect address")
            self.assertEqual(user.phone, profile.phone, "Incorrect phone")
        self.assertEqual(user.first_name + " " + user.last_name, profile.name, "Incorrect name")
        self.assertEqual(user.email, profile.email, "Incorrect email")
        self.assertEqual(user.role, profile.role, "Incorrect role")


class TestGetOwnProfile(ProfileAssertions):
    def _assignUser(self):
        print("Assigning user to roles and courses.")
        self.current_semester = Semester.objects.create(
            semester_name="Current", start_date="2024-07-05", end_date="2024-09-23"
        )

        self.users_courses = [
            Course.objects.create(course_code="0000", course_name="my test course", semester=self.current_semester),
            Course.objects.create(course_code="1111", course_name="my second course", semester=self.current_semester)
        ]
        self.course_assignments = [
            TACourseAssignment(ta=self.user, course_id=self.users_courses[0], grader_status=False),
            TACourseAssignment(ta=self.user, course_id=self.users_courses[1], grader_status=True)
        ]

        self.user_assigned_course_sections = [
            [CourseSection.objects.create(course_section_number="420", instructor=self.user, days="MWF",
                                          start_time="9:00", end_time="11:30", course=self.users_courses[0])],
            [CourseSection.objects.create(course_section_number="050", instructor=self.user, days="TuTh",
                                          start_time="2:00", end_time="3:15", course=self.users_courses[1]),
             CourseSection.objects.create(course_section_number="051", instructor=self.user, days="We",
                                          start_time="2:30", end_time="3:15", course=self.users_courses[1])
             ],
        ]
        self.user_assigned_lab_sections = [
            [
                LabSection.objects.create(lab_section_number="001", days="MWF",
                                          start_time="3:00", end_time="3:45", course=self.users_courses[0]),
                LabSection.objects.create(lab_section_number="003", days="MWF",
                                          start_time="4:00", end_time="5:30", course=self.users_courses[0])
            ],
            [],
        ]

        self.lab_assignments = [
            [
                TALabAssignment.objects.create(lab_section=self.user_assigned_lab_sections[0][0], ta=self.user),
                TALabAssignment.objects.create(lab_section=self.user_assigned_lab_sections[0][1], ta=self.user)
            ],
            []
        ]

    def _assert_is_own_profile(self, url):
        print(f"Checking own profile access via URL: {url}")
        response = self.client.get(url)

        if 'user_profile' in response.context:
            profile = response.context["user_profile"]
            self.assertIsInstance(profile, PrivateUserProfile, "Incorrect profile type")
            self._assertSameUser(self.user, profile)
        else:
            self.fail("The 'user_profile' context key was not found in the response.")

    def test_AdminGetDefault(self):
        print("Testing Admin default profile retrieval.")
        self._loginAsAdmin()
        self._assignUser()
        self._assert_is_own_profile(reverse("home"))
        print("Admin default profile retrieval test completed.")

    def test_AdminGetSelf(self):
        print("Testing Admin self profile retrieval.")
        self._loginAsAdmin()
        self._assignUser()
        self._assert_is_own_profile(reverse("profile", kwargs={"username": self.user.username}))
        print("Admin self profile retrieval test completed.")

    def test_InstructorGetDefault(self):
        print("Testing Instructor default profile retrieval.")
        self._loginAsInstructor()
        self._assignUser()
        self._assert_is_own_profile(reverse("home"))
        print("Instructor default profile retrieval test completed.")

    def test_InstructorGetSelf(self):
        print("Testing Instructor self profile retrieval.")
        self._loginAsInstructor()
        self._assignUser()
        self._assert_is_own_profile(reverse("profile", kwargs={"username": self.user.username}))
        print("Instructor self profile retrieval test completed.")

    def test_TAGetDefault(self):
        print("Testing TA default profile retrieval.")
        self._loginAsTA()
        self._assignUser()
        self._assert_is_own_profile(reverse("home"))
        print("TA default profile retrieval test completed.")

    def test_TAGetSelf(self):
        print("Testing TA self profile retrieval.")
        self._loginAsTA()
        self._assignUser()
        self._assert_is_own_profile(reverse("profile", kwargs={"username": self.user.username}))
        print("TA self profile retrieval test completed.")


class TestGetFakeUser(ProfileAssertions):
    def test_TAGetFakeUser(self):
        print("Testing TA access to fake user profile.")
        self._loginAsTA()
        response = self.client.get(reverse("profile", kwargs={"username": "theFakestUsernameEver"}))
        expected_redirect_url = reverse('home')
        self.assertRedirects(response, expected_redirect_url)
        print("TA fake user profile access test completed.")

    def test_InstructorGetFakeUser(self):
        print("Testing Instructor access to fake user profile.")
        self._loginAsInstructor()
        response = self.client.get(reverse("profile", kwargs={"username": "theFakestUsernameEver"}))
        expected_redirect_url = reverse('home')
        self.assertRedirects(response, expected_redirect_url)
        print("Instructor fake user profile access test completed.")

    def test_AdminGetFakeUser(self):
        print("Testing Admin access to fake user profile.")
        self._loginAsAdmin()
        response = self.client.get(reverse("profile", kwargs={"username": "theFakestUsernameEver"}))
        expected_redirect_url = reverse('home')
        self.assertRedirects(response, expected_redirect_url)
        print("Admin fake user profile access test completed.")


class TestGetUnassignedProfile(ProfileAssertions):
    def setUp(self):
        super().setUp()
        print("Setting up unassigned user profile.")
        self.unassignedUser: User = User.objects.create_user(
            username="Unassigned", password="Unimportant", email="others@uwm.edu",
            first_name="unass", last_name="igned", role="TA", phone="1222333444", address="888 poodle drive",
            office_hours="Tuesday"
        )

    def test_TAGetUnassignedUser(self):
        print("Testing TA access to unassigned user profile.")
        self._loginAsTA()
        response = self.client.get(reverse("profile", kwargs={"username": self.unassignedUser.username}))
        user_profile: UserProfile = response.context.get("user_profile")
        assert user_profile is not None, "The 'user_profile' context key was not found in the response."

        print("Asserting user profile type is UserProfile, not PrivateUserProfile.")
        self.assertNotIsInstance(user_profile, PrivateUserProfile,
                                 "Returned private user data when user does not have access")
        self.assertIsInstance(user_profile, UserProfile, "Incorrect profile data type")
        self.assertEqual([], user_profile.courses_assigned, "Returned courses assigned for user with no assignments")
        self._assertSameUser(self.unassignedUser, user_profile)
        print("TA unassigned user profile access test completed.")

    def test_InstructorGetUnassignedUser(self):
        print("Testing Instructor access to unassigned user profile.")
        self._loginAsInstructor()
        response = self.client.get(reverse("profile", kwargs={"username": self.unassignedUser.username}))
        user_profile: UserProfile = response.context.get("user_profile")
        assert user_profile is not None, "The 'user_profile' context key was not found in the response."

        print("Asserting user profile type is UserProfile, not PrivateUserProfile.")
        self.assertNotIsInstance(user_profile, PrivateUserProfile,
                                 "Returned private user data when user does not have access")
        self.assertIsInstance(user_profile, UserProfile, "Incorrect profile data type")
        self.assertEqual([], user_profile.courses_assigned, "Returned courses assigned for user with no assignments")
        self._assertSameUser(self.unassignedUser, user_profile)
        print("Instructor unassigned user profile access test completed.")

    def test_AdminGetUnassignedUser(self):
        print("Testing Admin access to unassigned user profile.")
        self._loginAsAdmin()
        response = self.client.get(reverse("profile", kwargs={"username": self.unassignedUser.username}))
        user_profile: PrivateUserProfile = response.context.get("user_profile")
        assert user_profile is not None, "The 'user_profile' context key was not found in the response."

        print("Asserting user profile type is PrivateUserProfile.")
        self.assertIsInstance(user_profile, PrivateUserProfile, "Failed to return private user profile data for admin")
        self._assertSameUser(self.unassignedUser, user_profile)
        print("Admin unassigned user profile access test completed.")


class TestGetProfileWithAssignments(ProfileAssertions):
    def setUp(self):
        super().setUp()
        print("Setting up profile with assignments.")
        self.current_semester = Semester.objects.create(
            semester_name="Current", start_date="2024-07-05", end_date="2024-09-23"
        )

        self.other_user = User.objects.create(
            username='assigneduser', password="notImportant", email='assignuser@example.com',
            first_name='assign', last_name='person', role='Instructor', phone='1334577890',
            address='135 assign Street'
        )

        self.courses = [
            Course.objects.create(course_code="1111", course_name="my second course", semester=self.current_semester),
            Course.objects.create(course_code="0000", course_name="my test course", semester=self.current_semester)
        ]
        self.course_assignments = [
            TACourseAssignment.objects.create(ta=self.other_user, course=self.courses[0], grader_status=False),
            TACourseAssignment.objects.create(ta=self.other_user, course=self.courses[1], grader_status=True)
        ]

        self.assigned_course_sections = [
            [CourseSection.objects.create(course_section_number="420", instructor=self.other_user, days="MWF",
                                          start_time="9:00", end_time="11:30", course=self.courses[0])],
            [CourseSection.objects.create(course_section_number="054", instructor=self.other_user, days="TuTh",
                                          start_time="2:00", end_time="3:15", course=self.courses[1]),
             CourseSection.objects.create(course_section_number="051", instructor=self.other_user, days="We",
                                          start_time="2:30", end_time="3:15", course=self.courses[1])
             ],
        ]
        self.assigned_lab_sections = [
            [
                LabSection.objects.create(lab_section_number="003", days="MWF",
                                          start_time="4:00", end_time="5:30", course=self.courses[0]),
                LabSection.objects.create(lab_section_number="001", days="MWF",
                                          start_time="3:00", end_time="3:45", course=self.courses[0])
            ],
            [],
        ]

        self.lab_assignments = [
            [
                TALabAssignment.objects.create(lab_section=self.assigned_lab_sections[0][0], ta=self.other_user),
                TALabAssignment.objects.create(lab_section=self.assigned_lab_sections[0][1], ta=self.other_user)
            ],
            []
        ]

    def test_AdminGetCorrectUser(self):
        print("Testing Admin access to correct user profile.")
        self._loginAsAdmin()
        response = self.client.get(reverse("profile", kwargs={"username": self.other_user.username}))
        user_profile: PrivateUserProfile = response.context.get("user_profile")
        assert user_profile is not None, "The 'user_profile' context key was not found in the response."

        print("Asserting user profile type is PrivateUserProfile.")
        self.assertIsInstance(user_profile, PrivateUserProfile, "Did not return private profile data for admin")
        self._assertSameUser(self.other_user, user_profile)
        print("Admin correct user profile access test completed.")

    def test_AdminGetCorrectCoursesAssigned(self):
        print("Testing Admin access for correct courses assigned.")
        self._loginAsAdmin()
        response = self.client.get(reverse("profile", kwargs={"username": self.other_user.username}))
        user_profile: PrivateUserProfile = response.context.get("user_profile")
        assert user_profile is not None, "The 'user_profile' context key was not found in the response."

        print("Asserting courses and sections are correctly assigned.")
        self.assertIsInstance(user_profile, PrivateUserProfile, "Did not return private profile data for admin")
        self.assertEqual(len(user_profile.courses_assigned), len(self.courses))
        for i in range(len(self.courses)):
            self.assertEqual(self.courses[i].course_code, user_profile.courses_assigned[i].code,
                             "Course has incorrect code")
            self.assertEqual(self.courses[i].course_name, user_profile.courses_assigned[i].name,
                             "Course has incorrect name")
            self.assertEqual(self.courses[i].semester.semester_name,
                             user_profile.courses_assigned[i].semester.semester_name,
                             "Course has incorrect semester")

            assigned_sections = self.assigned_course_sections[i]
            profile_sections = user_profile.courses_assigned[i].course_sections
            self.assertEqual(len(assigned_sections), len(profile_sections), "Course has wrong number of sections")
            for j in range(len(self.assigned_course_sections[i])):
                self.assertEqual(int(profile_sections[j].section_number),
                                 int(assigned_sections[j].course_section_number),
                                 "One of the sections is out of order")
                self.assertEqual(profile_sections[j].instructor.username, self.other_user.username,
                                 "Returned section user isn't assigned to")

            assigned_lab_sections = self.assigned_lab_sections[i]
            profile_lab_sections = user_profile.courses_assigned[i].lab_sections
            self.assertEqual(len(assigned_lab_sections), len(profile_lab_sections),
                             "Course has wrong number of sections")

            for j in range(len(assigned_lab_sections)):
                self.assertEqual(int(profile_lab_sections[j].section_number),
                                 int(assigned_lab_sections[j].lab_section_number),
                                 "One of the lab sections is out of order")
                self.assertEqual(profile_lab_sections[j].instructor.username, self.other_user.username,
                                 "Returned lab section someone else is assigned to")
        print("Admin correct courses assigned test completed.")