from copy import deepcopy

from django.test import TestCase, Client
from django.urls import reverse

from core.local_data_classes import CourseFormData
from ta_scheduler.models import User, Semester, Course, TACourseAssignment
from views.course_form import CourseForm


def loginAsRole(client: Client, role: str, password: str):
    user = User.objects.create_user(
        username='loggedinuser', password=password, email='loginUser@example.com', first_name='log',
        last_name='man', role=role, phone='9990009999', address='123 Logged in'
    )
    client.login(username=user.username, password=password)
    return user


class TestGetCourseFormRedirects(TestCase):
    def setUp(self):
        self.client = Client()

    def testTAGetNewCourseForm(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.get(reverse("course-creator"))
        self.assertRedirects(response, "home")

    def testInstructorGetNewCourseForm(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.get(reverse("course-creator"))
        self.assertRedirects(response, "home")


class TestAdminGetCourseForm(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = loginAsRole(self.client, "Admin", "test")

    def testGetFake(self):
        response = self.client.get(reverse("course-form", kwargs={
            "code": "3", "semester" : "Spring 2024"
        }))
        self.assertRedirects(response, "home")

    def testGetCreateForm(self):
        response = self.client.get(reverse("course-creator"))
        form: CourseFormData = response.context["data"]
        self.assertIsInstance(form, CourseFormData, "Returnd data of wrong type")
        self.assertEqual(form.semester, "", "Gave a semester when getting create course page")
        self.assertEqual(form.course_code, "", "Gave a course code when getting create course page")
        self.assertEqual(form.course_name, "", "Gave a course name when getting create course page")
        self.assertEqual(form.ta_username_list, "", "Gave a ta list when getting create course page")

    def testGetExisting(self):
        semester = Semester.objects.create(semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01")
        course = Course.objects.create(course_name="test", course_code="1", semester=semester)
        ta1 = User.objects.create_user(
            username="a", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )
        ta2 = User.objects.create_user(
            username="b", password="2", email="2@uwm.edu", first_name="c", last_name="d",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Wednesday"
        )
        ta_assignments = [
            TACourseAssignment.objects.create(ta=ta1, course=course, grader_status=False),
            TACourseAssignment.objects.create(ta=ta2, course=course, grader_status=True)
        ]
        normal_ta_list = "a, b"  # Alphabetical order
        url = reverse("course-form", kwargs={
            "code": course.course_code,
            "semester": semester.semester_name
        })

        response = self.client.get(url)
        form_data: CourseFormData = response.context["data"]
        self.assertIsInstance(form_data, CourseFormData, "Returnd data of wrong type")
        self.assertEqual(form_data.course_name, course.course_name, "Incorrect course name on get course form")
        self.assertEqual(form_data.course_code, course.course_code, "Incorrect course code on get course form")
        self.assertEqual(form_data.semester, semester.semester_name, "Incorrect semester name on get course form")
        self.assertEqual(form_data.ta_username_list, normal_ta_list, "Incorrect TA list on get course form")

class TestPostNewCourseForm(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = loginAsRole(self.client, "Admin", "test")

    def testPostEmpty(self):
        response = self.client.post("course-creater", {
            "code": "",
            "name": "",
            "semester": "",
            "ta_list": ""
        })
        self.assertContains(response, [
            'Course code must be a valid value',
            "Course name must be a valid value",
            "Course semester must be a valid semester"
        ])

    def testPostInvalidCode(self):
        Semester.objects.create(semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01")
        count = 1
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            code = "1234" + c
            name = "course" + str(count)
            response = self.client.post("course-creater", {
                "code": code,
                "name": name,
                "semester": "test semester",
                "ta_list": ""
            })
            self.assertContains(response, ['Course code must be a valid value'])
            self.assertFalse(Course.objects.filter(course_code=code).exists(), "Created course on code error")
            count = count + 1

    def testPostInvalidName(self):
        Semester.objects.create(semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01")
        count = 1
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            code = "course" + str(count)
            name = "1234" + c
            response = self.client.post("course-creater", {
                "code": code,
                "name": name,
                "semester": "test semester",
                "ta_list": ""
            })
            self.assertContains(response, ['Course code must be a valid value'])
            self.assertFalse(Course.objects.filter(course_name=code).exists(), "Created course on name error")
            count = count + 1

    def testPostFakeSemester(self):
        response = self.client.post("course-creater", {
            "code": "1234",
            "name": "test course name",
            "semester": "fake semester",
            "ta_list": ""
        })
        self.assertContains(response, ['Course semester must be a valid semester'])
        self.assertFalse(Course.objects.filter(course_name="1234").exists(), "Created course on name error")

    def testPostFakeTAs(self):
        Semester.objects.create(semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01")
        response = self.client.post("course-creater", {
            "code": "1234",
            "name": "test course name",
            "semester": "test semester",
            "ta_list": "fakerman jr, mr fake guy"
        })
        self.assertContains(response, ['One or more of the selected TAs is not an existing user'])
        self.assertFalse(Course.objects.filter(course_name="1234").exists(), "Created course on TA error")

    def testPostFakeInstructorAsTA(self):
        user1 = User.objects.create_user(
            username="realguy", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="Instructor", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )
        Semester.objects.create(semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01")
        response = self.client.post("course-creater", {
            "code": "1234",
            "name": "test course name",
            "semester": "test semester",
            "ta_list": "realguy"
        })
        self.assertContains(response, ['One or more of the selected TAs is not a TA'])
        self.assertFalse(Course.objects.filter(course_name="1234").exists(), "Created course on TA error")

    def testPostDuplicate(self):
        semester = Semester.objects.create(semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01")
        course = Course.objects.create(course_name="test", course_code="1", semester=semester)
        response = self.client.post("course-creater", {
            "code": course.course_code,
            "name": "overwritten",
            "semester": semester.semester_name,
            "ta_list": "fakerman jr, mr fake guy"
        })
        self.assertContains(response, ['The selected course code already exists for this semester'])
        self.assertFalse(Course.objects.filter(
            course_code=course.course_code,
            course_name="overwritten"
        ).exists(), "Overwrote existing course")


    def testValidWithTAs(self):
        user1 = User.objects.create_user(
            username="realguy", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )
        user2 = User.objects.create_user(
            username="dude", password="2", email="2@uwm.edu", first_name="c", last_name="d",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Wednesday"
        )
        semester = Semester.objects.create(semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01")
        response = self.client.post("course-creater", {
            "code": "1234",
            "name": "course",
            "semester": semester.semester_name,
            "ta_list": "realguy, dude"
        })
        self.assertTrue(Course.objects.filter(
            course_code="1234"
        ).exists(), "Failed to successfully save course")
        self.assertTrue(TACourseAssignment.objects.filter(
            ta=user1
        ).exists(), "Failed to create course assignment for TA")
        self.assertTrue(TACourseAssignment.objects.filter(
            ta=user2
        ).exists(), "Failed to create course assignment for TA")


class TestPostExistingCourseForm(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = loginAsRole(self.client, "Admin", "test")
        self.semester = Semester.objects.create(semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01")
        self.course = Course.objects.create(course_name="test", course_code="1", semester=self.semester)
        self.ta1 = User.objects.create_user(
            username="a", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )
        self.ta2 = User.objects.create_user(
            username="b", password="2", email="2@uwm.edu", first_name="c", last_name="d",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Wednesday"
        )
        self.ta_assignments = [
            TACourseAssignment.objects.create(ta=self.ta1, course=self.course, grader_status=False),
            TACourseAssignment.objects.create(ta=self.ta2, course=self.course, grader_status=True)
        ]
        self.normal_ta_list = "a, b"  # Alphabetical order
        self.url = reverse("course-form", kwargs={
            "code": self.course.course_code,
            "semester": self.semester.semester_name
        })

    def testModifySemesterDuplicate(self):
        second_course = deepcopy(self.course)
        second_course.pk = None
        second_semester = Semester.objects.create(semester_name="second", start_date="2024-09-21", end_date="2024-10-01")
        second_course.semester = second_semester
        self.course.name = "second"
        self.course.save()  # Create duplicate of course

        # Try to save the original course to the same semester as the second course
        response = self.client.post(self.url, {
            "code": self.course.course_code,
            "name": self.course.course_name,
            "semester": second_semester.semester_name,
            "ta_list": self.normal_ta_list
        })
        self.assertContains(response, ['A course with that code and semester already exists'])
        self.assertFalse(Course.objects.filter(
            course_code=self.course.course_code,
            semester=second_semester,
            course_name=self.course.course_name
        ).exists(), "Overwrote existing course on semester change")

    def testModifySemester(self):
        second_semester = Semester.objects.create(semester_name="second", start_date="2024-09-21", end_date="2024-10-01")

        response = self.client.post(self.url, {
            "code": self.course.course_code,
            "name": self.course.course_name,
            "semester": second_semester.semester_name,
            "ta_list": self.normal_ta_list
        })
        self.assertContains(response, ['Cannot change course semester'])
        self.assertFalse(Course.objects.filter(
            course_code=self.course.course_code,
            semester=second_semester
        ).exists(), "Failed to reject course on semester change")

    def testPostModifyCode(self):
        response = self.client.post(self.url, {
            "code": "400",
            "name": self.course.course_name,
            "semester": self.course.semester.semester_name,
            "ta_list": self.normal_ta_list
        })
        self.assertContains(response, ['Cannot change course code'])
        self.assertFalse(Course.objects.filter(
            course_code="400",
        ).exists(), "Failed to save course on valid course code change")

    def testPostModifyName(self):
        response = self.client.post(self.url, {
            "code": "400",
            "name": self.course.course_name,
            "semester": self.course.semester.semester_name,
            "ta_list": self.normal_ta_list
        })
        self.assertTrue(Course.objects.filter(
            course_code="400",
        ).exists(), "Failed to save course on valid course code change")

    def testPostInvalidName(self):
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            name = "1234" + c
            response = self.client.post(self.url, {
                "code": self.course.course_code,
                "name": name,
                "semester": self.course.semester.semester_name,
                "ta_list": self.normal_ta_list
            })
            self.assertContains(response, ['The given course name is invalid'])
            self.assertFalse(Course.objects.filter(
                course_code=self.course.course_code,
                course_name=name
            ).exists(), "Failed to reject invalid course name change for " + c)

    def testRemoveTA(self):
        response = self.client.post(self.url, {
            "code": "400",
            "name": self.course.course_name,
            "semester": self.course.semester.semester_name,
            "ta_list": self.normal_ta_list.split(",")[0]
        })
        self.assertFalse(TACourseAssignment.objects.filter(
            ta=self.ta2,
        ).exists(), "Failed to delete course assignment after removing them on course form")

    def testPostEmpty(self):
        response = self.client.post(self.url, {
            "code": self.course.course_code,
            "name": "",
            "semester": self.course.semester.semester_name,
            "ta_list": ""
        })
        self.assertContains(response, ['Courses must have a valid name'])
        self.assertTrue(Course.objects.filter(
            course_code="400",
        ).exists(), "Failed to reject course on empty form submission")
