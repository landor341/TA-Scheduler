from copy import deepcopy

from django.test import TestCase, Client
from django.urls import reverse
from datetime import time

from core.local_data_classes import CourseFormData, SectionFormData
from ta_scheduler.models import User, Semester, Course, TACourseAssignment, LabSection, TALabAssignment, CourseSection
from views.course_form import CourseForm


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
        self.semester = Semester.objects.create(semester_name="test semester", start_date="2024-09-21",end_date="2024-10-01")
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
        self.new_url = reverse("course-form", kwargs={
            "code": self.course.course_code,
            "semester": self.semester.semester_name
        })

    def get_url(self, section_number: int):
        return reverse("section-form", kwargs={
            "code": self.course.course_code,
            "semester": self.semester.semester_name,
            "section_number": section_number
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

    def testInstructorGetNewRelatedCourseForm(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.user,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        response = self.client.get(self.new_url)
        self.assertRedirects(response, reverse('home'))


class TestInstructorGetExistingSectionForm(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()

    def testInstructorGetUnrelatedExistingLabSection(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        section = LabSection.objects.create(
            lab_section_number=3, days="MWF",
            start_time=time(16, 0), end_time=time(17, 30), course=self.course
        )
        response = self.client.get(self.get_url(section.lab_section_number))
        self.assertRedirects(response, reverse('home'))

    def testInstructorGetRelatedExistingLabSection(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.user,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        section = LabSection.objects.create(
            lab_section_number=3, days="MWF",
            start_time=time(16, 0), end_time=time(17, 30), course=self.course
        )
        response = self.client.get(self.get_url(section.lab_section_number))
        self.assertIsInstance(
            response.context["data"],
            SectionFormData,
            "Failed to return proper response type for managing instructor editing lab"
        )

    def testInstructorGetRelatedExistingCourseSection(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        section = CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.user,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        response = self.client.get(self.get_url(section.course_section_number))
        self.assertRedirects(response, reverse('home'))


class TestAdminGetExistingSectionForm(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()

    def testAdminGetExistingLabSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        section = LabSection.objects.create(
            lab_section_number=3, days="MWF",
            start_time=time(16, 0), end_time=time(17,30), course=self.course
        )
        response = self.client.get(self.get_url(section.lab_section_number))
        form: SectionFormData = response.context["data"]
        self.assertIsInstance(
            form,
            SectionFormData,
            "Failed to return proper response type for admin editing lab section"
        )
        self.assertEqual(form.section_type, "Lab", "Returned incorrect section type")
        self.assertEqual(form.section_number, section.lab_section_number, "Returned incorrect lab section number")
        self.assertEqual(form.start_time, section.start_time, "Returned incorrect start time")
        self.assertEqual(form.end_time, section.end_time, "Returned incorrect end time")
        self.assertEqual(form.days, section.days, "Returned incorrect days")

    def testAdminGetExistingCourseSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        section = CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.test_instructor,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        response = self.client.get(self.get_url(section.course_section_number))
        form: SectionFormData = response.context["data"]
        self.assertIsInstance(
            form,
            SectionFormData,
            "Failed to return proper response type for admin editing course section"
        )
        self.assertEqual(form.section_type, "Course", "Returned section type")
        self.assertEqual(form.section_number, section.course_section_number, "Returned incorrect course section number")
        self.assertEqual(form.start_time, section.start_time, "Returned incorrect start time")
        self.assertEqual(form.end_time, section.end_time, "Returned incorrect end time")
        self.assertEqual(form.days, section.days, "Returned incorrect days")

class TestPostSectionFormPermissions(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()

        self.section_test_data = {
            "section_number": "111",
            "section_type": "Lab",
            "start_time": "12:00",
            "end_time": "1:30",
            "days": "MoTu"
        }

    def testTAPostNewSectionForm(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.post(self.new_url, self.section_test_data)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(LabSection.objects.filter(
            lab_section_number=self.section_test_data["section_number"]
        ), "Allowed TA to post new lab section")

    def testInstructorPostNewRelatedCourseForm(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.user,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        response = self.client.post(self.new_url, self.section_test_data)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(LabSection.objects.filter(
            lab_section_number=self.section_test_data["section_number"]
        ), "Allowed Instructor to post new lab section")

    def testAdminPostNewRelatedCourseForm(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.test_instructor,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        response = self.client.post(self.new_url, self.section_test_data)
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(LabSection.objects.filter(
            lab_section_number=self.section_test_data["section_number"]
        ), "Failed to allow admin to post new lab section")


class TestAdminPostExistingSectionForm(TestSectionFormTestCase):
    def setUp(self):
        self.doSetup()
        self.user = loginAsRole(self.client, "Instructor", "test")
        self.course_section = CourseSection.objects.create(
            course_section_number=1, days="M", instructor=self.test_instructor,
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        self.lab_section = LabSection.objects.create(
            lab_section_number=3, days="Tu",
            start_time=time(14, 0), end_time=time(20, 30), course=self.course
        )
        TALabAssignment.objects.create(
            ta=self.test_ta, lab_section=self.lab_section
        )

    def testDuplicateSectionNumber(self):
        response = self.client.post(self.get_url(self.lab_section.lab_section_number), {
            "section_number": self.course_section.course_section_number,
            "section_type": "Lab",
            "start_time": self.lab_section.start_time,
            "end_time": self.lab_section.end_time,
            "days": self.lab_section.days
        })
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(LabSection.objects.filter(
            lab_section_number=self.course_section.course_section_number
        ), "Allowed lab section to have same section number as course section")

    def testEditLabSection(self):
        response = self.client.post(self.get_url(self.course_section.course_section_number), {
            "section_number": 999,
            "section_type": "Course",
            "start_time": time(16, 0),
            "end_time": time(17, 0),
            "days": "Sa"
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(CourseSection.objects.filter(
            course_section_number=999,
            start_time=time(16, 0),
            end_time=time(17, 0),
            days="Sa"
        ), "Did not allow admin to modify section data")

    def testChangeSectionType(self):
        response = self.client.post(self.get_url(self.course_section.course_section_number), {
            "section_number": self.course_section.course_section_number,
            "section_type": "Lab",
            "start_time": self.course_section.start_time,
            "end_time": self.course_section.end_time,
            "days": self.course_section.days
        })
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(LabSection.objects.filter(
            lab_section_number=self.course_section.course_section_number
        ), "Allowed admin to change course section into lab section")


class TestDeleteSectionFormPermissions(TestSectionFormTestCase):
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
        self.lab_assignment = TALabAssignment.objects.create(lab_section=self.lab_section, ta=self.test_ta)


    def testAdminDeleteCourseSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")

        response = self.client.delete(self.get_url(self.course_section.course_section_number))

        self.assertFalse(CourseSection.objects.filter(
            id=self.course_section.id,
        ).exists(), "Failed to allow admin to delete course section")

    def testAdminDeleteLabSection(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.delete(self.get_url(self.lab_section.lab_section_number))
        self.assertFalse(LabSection.objects.filter(
            id=self.lab_section.id,
        ).exists(), "Failed to allow admin to delete lab section")
        self.assertFalse(TALabAssignment.objects.filter(
            id=self.lab_assignment.id,
        ).exists(), "Failed to delete ta lab assignment on lab section deletion")

    def testTADeleteLab(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.delete(self.get_url(self.lab_section.lab_section_number))
        self.assertFalse(LabSection.objects.filter(
            id=self.lab_section.id,
        ).exists(), "Allowed TA to delete lab section")

    def testInstructorDeleteLab(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.delete(self.get_url(self.lab_section.lab_section_number))
        self.assertFalse(LabSection.objects.filter(
            id=self.lab_section.id,
        ).exists(), "Allowed instructor to delete lab section")

    def testTADeleteCourseSection(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.delete(self.get_url(self.course_section.course_section_number))
        self.assertFalse(CourseSection.objects.filter(
            id=self.course_section.id,
        ).exists(), "Allowed TA to delete course section")

    def testInstructorDeleteCourseSection(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.delete(self.get_url(self.course_section.course_section_number))
        self.assertFalse(CourseSection.objects.filter(
            id=self.course_section.id,
        ).exists(), "Allowed instructor to delete course section")


