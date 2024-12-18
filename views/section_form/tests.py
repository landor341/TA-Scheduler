from django.test import TestCase, Client
from django.urls import reverse
from datetime import time

from core.local_data_classes import CourseFormData
from ta_scheduler.models import User, Semester, Course, LabSection, CourseSection, TALabAssignment


def loginAsRole(client: Client, role: str, password: str):
    user = User.objects.create_user(
        username='loggedinuser', password=password, email='loginUser@example.com', first_name='log',
        last_name='man', role=role, phone='9990009999', address='123 Logged in'
    )
    client.login(username=user.username, password=password)
    return user


class TestSectionFormTestCase(TestCase):
    def doSetup(self):
        self.client = Client()
        self.semester = Semester.objects.create(
            semester_name="test semester", start_date="2024-09-21", end_date="2024-10-01"
        )
        self.test_instructor = User.objects.create_user(
            username='test_instructor', password="123", email='user@example.com', first_name='instr',
            last_name='uctor', role="Instructor", phone='9990009999', address='123 Logged in'
        )
        self.test_ta = User.objects.create_user(
            username='test_ta', password="123", email='user@example.com', first_name='t',
            last_name='a', role="TA", phone='9990009999', address='123 Logged in'
        )
        self.course = Course.objects.create(
            course_code="5534",
            course_name="Test course",
            semester=self.semester
        )
        # Provide default values for section_number and section_type
        self.new_url = reverse("section-form", kwargs={
            "code": self.course.course_code,
            "semester": self.semester.semester_name,
            "section_number": 0,  # Placeholder for creating new sections
            "section_type": "Lab"
        })

    def get_url(self, section_number: int, section_type: str):
        return reverse("section-form", kwargs={
            "code": self.course.course_code,
            "semester": self.semester.semester_name,
            "section_number": section_number,
            "section_type": section_type,
        })


class TestGetNewSectionForm(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()

    def testTAGetNewSectionForm(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.get(self.new_url)
        self.assertRedirects(response, reverse('home'))

    def testInstructorGetNewUnrelatedCourseForm(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.get(self.new_url)
        self.assertRedirects(response, reverse('home'))

    def testAdminGetNewSectionForm(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.get(self.new_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.context)


class TestAdminGetExistingSectionForm(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()

    def testAdminGetExistingLabSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        section = LabSection.objects.create(
            lab_section_number=3, days="MWF",
            start_time=time(16, 0), end_time=time(17, 30), course=self.course
        )
        response = self.client.get(self.get_url(section.lab_section_number, "Lab"))
        form_data = response.context["data"]

        self.assertEqual(form_data["section_type"], "Lab")
        self.assertEqual(form_data["section_number"], section.lab_section_number)
        self.assertEqual(form_data["start_time"], section.start_time)
        self.assertEqual(form_data["end_time"], section.end_time)
        self.assertEqual(form_data["days"], section.days)

    def testAdminGetExistingCourseSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        section = CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.test_instructor,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        response = self.client.get(self.get_url(section.course_section_number, "Course"))
        form_data = response.context["data"]

        self.assertEqual(form_data["section_type"], "Course")
        self.assertEqual(form_data["section_number"], section.course_section_number)
        self.assertEqual(form_data["start_time"], section.start_time)
        self.assertEqual(form_data["end_time"], section.end_time)
        self.assertEqual(form_data["days"], section.days)


class TestPostSectionFormPermissions(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()

        self.section_test_data = {
            "section_number": "111",
            "section_type": "Lab",
            "start_time": "12:00",
            "end_time": "13:30",
            "days": "MoTu"
        }

    def testAdminPostNewSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.post(self.new_url, self.section_test_data)
        self.assertRedirects(response, reverse('course_view', args=[self.course.course_code, self.semester.semester_name]))
        self.assertTrue(LabSection.objects.filter(
            lab_section_number=self.section_test_data["section_number"]
        ).exists())

    def testTARestrictedFromPostingSection(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.post(self.new_url, self.section_test_data)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(LabSection.objects.filter(
            lab_section_number=self.section_test_data["section_number"]
        ).exists())


class TestAdminDeleteSection(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()
        self.course_section = CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.test_instructor,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        self.lab_section = LabSection.objects.create(
            lab_section_number=1, days="M",
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )

    def testAdminDeleteLabSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.post(self.get_url(self.lab_section.lab_section_number, "Lab"), {
            "delete": "true"
        })
        self.assertRedirects(response, reverse('course_view', args=[self.course.course_code, self.semester.semester_name]))
        self.assertFalse(LabSection.objects.filter(id=self.lab_section.id).exists())

    def testAdminDeleteCourseSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.post(self.get_url(self.course_section.course_section_number, "Course"), {
            "delete": "true"
        })
        self.assertRedirects(response, reverse('course_view', args=[self.course.course_code, self.semester.semester_name]))
        self.assertFalse(CourseSection.objects.filter(id=self.course_section.id).exists())



