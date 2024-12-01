from django.test import TestCase
from django.urls import reverse

from core.local_data_classes import UserProfile, PrivateUserProfile
from ta_scheduler.models import Course, Semester, CourseSection, LabSection, User


class profileAssertions(TestCase):
    def assertUserprofileEqual(
            self, profile: UserProfile, user: User, courses: list[Course],
            courses_labs: list[list[LabSection]], courses_sections: list[list[CourseSection]]
    ):
        self.assertEqual(profile.name, user.first_name + " " + user.last_name, "incorrect name")
        self.assertEqual(profile.email, user.email, "incorrect email")
        self.assertEqual(profile.role, user.role, 'incorrect role')
        self.assertEqual(profile.office_hours, user.office_hours, "incorrect office hours")
        self.assertEqual(len(profile.courses_assigned), len(courses), "profile has the wront number of courses")

        for i in range(len(courses)):
            course = courses[i]
            labs = filter(lambda x: x.instructor == user , courses_labs[i])
            sections = filter(lambda x: x.instructor == user , courses_sections[i])
            profile_course = None
            for c in profile.courses_assigned:
                if c.course_code == course.course_code:
                    profile_course = c
                    break
            self.assertNotEquals(profile_course, None, "profile is missing a course")
            self.assertEqual(len(labs), len(profile_course.lab_sections), "wrong number of lab sections")
            self.assertEqual(len(sections), len(profile_course.course_sections), "wrong number of course sections")
            # TODO: assert that each individual section is the same

    def assertPrivateUserProfileEqual(
            self, profile: PrivateUserProfile, user: User, courses: list[Course],
            courses_labs: list[list[LabSection]], courses_sections: list[list[CourseSection]]
    ):
        self.assertEqual(user.address, profile.address, "Incorrect user address")
        self.assertEqual(user.phone, profile.phone, "Incorrect phone number")
        self.assertUserprofileEqual(profile, user, courses, courses_labs, courses_sections)


class TestGetOwnProfile(TestCase, profileAssertions):
    def setup(self):
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com', first_name='Test',
            last_name='User', role='Instructor', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)

        self.current_semester = Semester.objects.create(semester_name="Current", start_date="07/05/24", end_date="09/23/24")

        self.users_courses = [
            Course.objects.create(course_code="0000", course_name="my test course", semester=self.current_semester),
            Course.objects.create(course_code="1111", course_name="my second test course", semester=self.current_semester)
        ]
        self.user_assigned_course_sections = [
            [ CourseSection.objects.create(course_section_number="420", instructor=self.user, days="MWF",
                                           start_time="9:00", end_time="11:30", course=self.users_courses[0]) ],
            [ CourseSection.objects.create(course_section_number="050", instructor=self.user, days="TuTh",
                                           start_time="2:00", end_time="3:15", course=self.users_courses[1])],
        ]
        self.user_assigned_lab_sections = [
            [
                LabSection.objects.create(lab_section_number="001", instructor=self.user, days="MWF",
                                          start_time="3:00", end_time="3:45",  course=self.users_courses[0]),
                LabSection.objects.create(lab_section_number="003", instructor=self.user, days="MWF",
                                          start_time="4:00", end_time="5:30", course=self.users_courses[0])
             ],
            [],
        ]
    def testEmpty(self):
        response = self.client.get(reverse("home"))
        userProfile: UserProfile = response.data
        self.assertIsInstance(userProfile, PrivateUserProfile, "Incorrect profile type")

        self.assertUserProfileEqual(
            userProfile, self.user, self.users_courses,
            self.user_assigned_course_sections, self.user_assigned_lab_sections
        )

    def testGetSelf(self):
        response = self.client.get(reverse("profile", kwargs={"username": self.user.username}))
        userProfile: UserProfile = response.data
        self.assertIsInstance(userProfile, PrivateUserProfile, "Did not return private profile data")

        self.assertUserProfileEqual(
            userProfile, self.user, self.users_courses,
            self.user_assigned_course_sections, self.user_assigned_lab_sections
        )


class TestGetUnassignedProfile(TestCase, profileAssertions):
    def setup(self):
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com', first_name='Test',
            last_name='User', role='Instructor', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)
        self.unassignedUser: User = User.objects.create_user(
            username="Unassigned", password="Unimportant", email="others@uwm.edu", first_name="unass",
            last_name="igned", role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )
    def testGetUser(self):
        response = self.client.get(reverse("profile", kwargs={"username": self.unassignedUser.username}))
        userProfile: UserProfile = response.data
        self.assertNotIsInstance(userProfile, PrivateUserProfile, "Returned private user data when user does not have access")
        self.assertIsInstance(userProfile, UserProfile, "Incorrect profile data type")
        self.assertUserProfileEqual(userProfile, self.unassignedUser, [], [], [])

class TestAdminGetProfile(TestCase, profileAssertions):
    def setup(self):
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser', password=self.password, email='testuser@example.com', first_name='Test',
            last_name='User', role='Admin', phone='1234567890', address='123 Test Street'
        )
        self.client.login(username=self.user.username, password=self.password)

        self.other_user = User.objects.create_user(
            username="otheruser", password="otherpass", email="otheruser@uwm.edu",
            first_name="otherman", last_name="testly", role="TA", phone="9876543210", address="487 Test Lane"
        )

        self.current_semester = Semester.objects.create(semester_name="Current", start_date="07/05/24", end_date="09/23/24")

        self.others_courses = [
            Course.objects.create(course_code="0000", course_name="my test course", semester=self.current_semester),
            Course.objects.create(course_code="1111", course_name="my second test course", semester=self.current_semester)
        ]
        self.other_assigned_course_sections = [
            [ CourseSection.objects.create(course_section_number="420", instructor=self.user, days="MWF",
                                           start_time="9:00", end_time="11:30", course=self.users_courses[0]) ],
            [ CourseSection.objects.create(course_section_number="050", instructor=self.user, days="TuTh",
                                           start_time="2:00", end_time="3:15", course=self.users_courses[1])],
        ]
        self.other_assigned_lab_sections = [
            [
                LabSection.objects.create(lab_section_number="001", instructor=self.user, days="MWF",
                                          start_time="3:00", end_time="3:45",  course=self.users_courses[0]),
                LabSection.objects.create(lab_section_number="003", instructor=self.user, days="MWF",
                                          start_time="4:00", end_time="5:30", course=self.users_courses[0])
             ],
            [LabSection.objects.create(lab_section_number="002", instructor=self.user, days="TuTh",
                                           start_time="4:30", end_time="6:15",  course=self.users_courses[1])],
        ]

    def getValidProfile(self):
        response = self.client.get(reverse("profile", kwargs={"username": self.user.username}))
        userProfile: UserProfile = response.data
        self.assertIsInstance(userProfile, PrivateUserProfile, "Did not return private profile data")

        self.assertUserProfileEqual(
            userProfile, self.user, self.users_courses,
            self.user_assigned_course_sections, self.user_assigned_lab_sections
        )
    def getFakeUser(self):
        response = self.client.get(reverse("profile", kwargs={"username": self.user.username}))
        # TODO: Assert redirects to home

class NonAdminGetProfileTests(TestCase, profileAssertions):

    def setup(self):
        self.password = 'password123'
        self.user = User.objects.create_user(
            username='testuser',
            password=self.password,
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            role='Instructor',
            phone='1234567890',
            address='123 Test Street'
        )
        User.objects.filter(first_name="Test")
        self.client.login(username=self.user.username, password=self.password)

    def getValidProfile(self):
        pass
    def getFakeUser(self):
        # TODO: Assert redirects to home
        pass

