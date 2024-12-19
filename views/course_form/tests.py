from django.test import TestCase, Client
from django.urls import reverse
from datetime import time

from ta_scheduler.models import User, Semester, Course, LabSection, CourseSection


def loginAsRole(client: Client, role: str, password: str):
    user = User.objects.create_user(
        username='loggedinuser', password=password, email='loginUser@example.com',
        first_name='log', last_name='man', role=role,
        phone='9990009999', address='123 Logged in'
    )
    client.login(username=user.username, password=password)
    return user


class TestSectionFormTestCase(TestCase):
    def doSetup(self):
        self.client = Client()
        self.semester = Semester.objects.create(
            semester_name="Fall 2024", start_date="2024-09-01", end_date="2024-12-15"
        )
        self.test_instructor = User.objects.create_user(
            username='test_instructor', password="123", email='instructor@example.com',
            first_name='Test', last_name='Instructor', role="Instructor",
            phone='9990009999', address='123 Instructor St'
        )
        self.test_ta = User.objects.create_user(
            username='test_ta', password="123", email='ta@example.com',
            first_name='Test', last_name='TA', role="TA",
            phone='9990009999', address='123 TA St'
        )
        self.course = Course.objects.create(
            course_code="CS101",
            course_name="Intro to Computer Science",
            semester=self.semester
        )
        # URL for creating a new Lab section
        self.new_url = reverse("section-form", kwargs={
            "code": self.course.course_code,
            "semester": self.semester.semester_name,
            "section_number": 1,  # Avoid section_number=0
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

    def test_ta_get_new_section_form(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.get(self.new_url)
        self.assertRedirects(response, reverse('home'))

    def test_instructor_get_new_section_form(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.get(self.new_url)
        self.assertRedirects(response, reverse('course_view', args=[self.course.course_code, self.semester.semester_name]))

    def test_admin_get_new_section_form(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.get(self.new_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.context)


class TestAdminGetExistingSectionForm(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()

    def test_admin_get_existing_lab_section(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        section = LabSection.objects.create(
            lab_section_number=2, days="MWF",
            start_time=time(16, 0), end_time=time(17, 30), course=self.course
        )
        response = self.client.get(self.get_url(section.lab_section_number, "Lab"))
        form_data = response.context["data"]

        self.assertEqual(form_data["section_type"], "Lab")
        self.assertEqual(form_data["section_number"], section.lab_section_number)
        self.assertEqual(form_data["start_time"], section.start_time)
        self.assertEqual(form_data["end_time"], section.end_time)
        self.assertEqual(form_data["days"], section.days)

    def test_admin_get_existing_course_section(self):
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
            "section_number": "2",
            "section_type": "Lab",
            "start_time": "12:00",
            "end_time": "13:30",
            "days": "MoTu",
            "instructor": self.test_instructor.username
        }

    def test_admin_post_new_lab_section(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.post(self.new_url, self.section_test_data)
        self.assertRedirects(response, reverse('course_view', args=[self.course.course_code, self.semester.semester_name]))
        self.assertTrue(LabSection.objects.filter(
            lab_section_number=2, course=self.course
        ).exists())

    def test_ta_restricted_from_posting_section(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.post(self.new_url, self.section_test_data)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(LabSection.objects.filter(
            lab_section_number=2, course=self.course
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

    def test_admin_delete_lab_section(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.post(self.get_url(self.lab_section.lab_section_number, "Lab"), {
            "delete": "true"
        })
        self.assertRedirects(response, reverse('course_view', args=[self.course.course_code, self.semester.semester_name]))
        self.assertFalse(LabSection.objects.filter(id=self.lab_section.id).exists())

    def test_admin_delete_course_section(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.post(self.get_url(self.course_section.course_section_number, "Course"), {
            "delete": "true"
        })
        self.assertRedirects(response, reverse('course_view', args=[self.course.course_code, self.semester.semester_name]))
        self.assertFalse(CourseSection.objects.filter(id=self.course_section.id).exists())



