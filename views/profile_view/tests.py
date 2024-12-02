from django.test import TestCase, Client
from django.urls import reverse

from core.local_data_classes import UserProfile, PrivateUserProfile
from ta_scheduler.models import Course, Semester, CourseSection, LabSection, User, TALabAssignment, TACourseAssignment


class ProfileAssertions(TestCase):
    def setUp(self):
        self.client = Client()

    def loginAsAdmin(self):
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com', first_name='Test',
            last_name='User', role='Admin', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)

    def loginAsInstructor(self):
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com', first_name='Test',
            last_name='User', role='Instructor', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)

    def loginAsTA(self):
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com', first_name='Test',
            last_name='User', role='TA', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)

    def assertSameUser(self, user, profile: UserProfile | PrivateUserProfile):
        if isinstance(profile, PrivateUserProfile):
            self.assertEqual(user.address, profile.address, "Incorrect address")
            self.assertEqual(user.phone, profile.phone, "Incorrect phone")
        self.assertEqual(user.first_name + " " + user.last_name, profile.name, "Incorrect name")
        self.assertEqual(user.email, profile.email, "Incorrect email")
        self.assertEqual(user.role, profile.role, "Incorrect role")
        self.assertEqual(user.office_hours, profile.office_hours, "Incorrect office hours")


class TestGetOwnProfile(ProfileAssertions):
    '''
    Tests that a user getting their own profile will retrieve the private version of their profile.
    '''

    def __assignUser(self):
        self.current_semester = Semester.objects.create(semester_name="Current", start_date="2024-07-05", end_date="2024-09-23")

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
                                          start_time="3:00", end_time="3:45",  course=self.users_courses[0]),
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

    def __assert_is_own_profile(self, url, ):
        response = self.client.get(url)
        profile: PrivateUserProfile = response.context["data"]
        self.assertIsInstance(profile, PrivateUserProfile, "Incorrect profile type")
        self.assertSameUser(self.user, profile)

    def testAdminGetDefault(self):
        self.loginAsAdmin()
        self.__assignUser()
        self.__assert_is_own_profile(reverse("home"))

    def testAdminGetSelf(self):
        self.loginAsAdmin()
        self.__assignUser()
        self.__assert_is_own_profile(reverse("profile", kwargs={"username": self.user.username}))


    def testInstructorGetDefault(self):
        self.loginAsInstructor()
        self.__assignUser()
        self.__assert_is_own_profile(reverse("home"))

    def testInstructorGetSelf(self):
        self.loginAsInstructor()
        self.__assignUser()
        self.__assert_is_own_profile(reverse("profile", kwargs={"username": self.user.username}))


    def testTAGetDefault(self):
        self.loginAsTA()
        self.__assignUser()
        self.__assert_is_own_profile(reverse("home"))

    def testTAGetSelf(self):
        self.loginAsTA()
        self.__assignUser()
        self.__assert_is_own_profile(reverse("profile", kwargs={"username": self.user.username}))

class TestGetFakeUser(ProfileAssertions):
    def testTAGetFakeUser(self):
        self.loginAsTA()

        response = self.client.get(reverse("profile", kwargs={"username": "theFakestUsernameEver"}))
        self.assertRedirects(response, "home")

    def testInstructorGetFakeUser(self):
        self.loginAsInstructor()

        response = self.client.get(reverse("profile", kwargs={"username": "theFakestUsernameEver"}))
        self.assertRedirects(response, "home")

    def testAdminGetFakeUser(self):
        self.loginAsAdmin()

        response = self.client.get(reverse("profile", kwargs={"username": "theFakestUsernameEver"}))
        self.assertRedirects(response, "home")


class TestGetUnassignedProfile(ProfileAssertions):
    def setUp(self):
        self.unassignedUser: User = User.objects.create_user(
            username="Unassigned", password="Unimportant", email="others@uwm.edu", first_name="unass",
            last_name="igned", role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )

    def testTAGetUnassignedUser(self):
        self.loginAsTA()

        response = self.client.get(reverse("profile", kwargs={"username": self.unassignedUser.username}))
        user_profile: UserProfile = response.context["data"]
        self.assertNotIsInstance(user_profile, PrivateUserProfile, "Returned private user data when user does not have access")
        self.assertIsInstance(user_profile, UserProfile, "Incorrect profile data type")
        self.assertEqual([], user_profile.courses_assigned, "Returned courses assigned for user with no assignments")
        self.assertSameUser(self.unassignedUser, user_profile)

    def testInstructorGetUnassignedUser(self):
        self.loginAsInstructor()

        response = self.client.get(reverse("profile", kwargs={"username": self.unassignedUser.username}))
        user_profile: UserProfile = response.context["data"]
        self.assertNotIsInstance(user_profile, PrivateUserProfile,
                                 "Returned private user data when user does not have access")
        self.assertIsInstance(user_profile, UserProfile, "Incorrect profile data type")
        self.assertEqual([], user_profile.courses_assigned, "Returned courses assigned for user with no assignments")
        self.assertSameUser(self.unassignedUser, user_profile)

    def testAdminGetUnassignedUser(self):
        self.loginAsAdmin()

        response = self.client.get(reverse("profile", kwargs={"username": self.unassignedUser.username}))
        user_profile: PrivateUserProfile = response.context["data"]
        self.assertIsInstance(user_profile, PrivateUserProfile,"Failed to return private user profile data for admin")
        self.assertEqual([], user_profile.courses_assigned, "Returned courses assigned for user with no assignments")
        self.assertSameUser(self.unassignedUser, user_profile)


class TestGetProfileWithAssignments(ProfileAssertions):

    def setUp(self):
        self.current_semester = Semester.objects.create(semester_name="Current", start_date="2024-07-05", end_date="2024-09-23")

        self.other_user = User.objects.create(
            username='assigneduser', password="notImportnat", email='assignuser@example.com', first_name='assign',
            last_name='person', role='Instructor', phone='1334577890', address='135 assign Street'
        )

        self.courses = [
            Course.objects.create(course_code="1111", course_name="my second course", semester=self.current_semester),
            Course.objects.create(course_code="0000", course_name="my test course", semester=self.current_semester)
        ]
        self.course_assignments = [
            TACourseAssignment(ta=self.other_user, course_id=self.courses[0], grader_status=False),
            TACourseAssignment(ta=self.other_user, course_id=self.courses[1], grader_status=True)
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
        # TODO: Add additional data that shouldn't be included in tests

        self.lab_assignments = [
            [
              TALabAssignment.objects.create(lab_section=self.assigned_lab_sections[0][0], ta=self.other_user),
              TALabAssignment.objects.create(lab_section=self.assigned_lab_sections[0][1], ta=self.other_user)
            ],
            []
        ]

    def testAdminGetCorrectUser(self):
        self.loginAsAdmin()

        response = self.client.get(reverse("profile", kwargs={"username": self.other_user.username}))
        user_profile: PrivateUserProfile = response.context["data"]
        self.assertIsInstance(user_profile, PrivateUserProfile, "Did not return private profile data for admin")
        self.assertSameUser(self.other_user, user_profile)


    def testAdminGetCorrectCoursesAssigned(self):
        self.loginAsAdmin()

        response = self.client.get(reverse("profile", kwargs={"username": self.other_user.username}))
        user_profile: PrivateUserProfile = response.context["data"]
        self.assertIsInstance(user_profile, PrivateUserProfile, "Did not return private profile data for admin")
        self.assertEqual(len(user_profile.courses_assigned), len(self.courses))
        for i in range(len(self.courses)):
            self.assertEqual(self.courses[i].course_code, user_profile.courses_assigned[i].code, "Sections are not in descending order by course number")
            self.assertEqual(self.courses[i].course_name, user_profile.courses_assigned[i].name, "Course has incorrect name")
            self.assertEqual(self.courses[i].semester.semester_name, user_profile.courses_assigned[i].semester, "Course has incorrect semester")

            assigned_sections = self.assigned_course_sections[i]
            profile_sections = user_profile.courses_assigned[i].course_sections
            self.assertEqual(len(assigned_sections),len(profile_sections),"Course has wrong number of sections")
            for j in range(len(self.assigned_course_sections[i])):
                self.assertEqual(profile_sections[j].section_number, assigned_sections[j].course_section_number, "One of the sections is out of order")
                self.assertEqual(profile_sections[j].instructor.username, self.other_user.username, "Returned section user isn't assigned to")

            assigned_lab_sections = self.assigned_lab_sections[i]
            lab_assignments = self.lab_assignments[i]
            profile_lab_sections = user_profile.courses_assigned[i].lab_sections
            self.assertEqual(len(assigned_lab_sections),len(profile_lab_sections),"Course has wrong number of sections")
            for j in range(len(self.assigned_course_sections[i])):
                self.assertEqual(profile_lab_sections[j].section_number, assigned_lab_sections[j].course_section_number,
                                 "One of the sections is out of order")
                self.assertEqual(lab_assignments[j].ta.username, self.other_user.username,
                                 "Returned section someone else is assigned to")
