from datetime import datetime
from django.test import TestCase, Client
from django.urls import reverse
from ta_scheduler.models import Course, CourseSection, User, TALabAssignment, LabSection, Semester


class CourseViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.instructor = User.objects.create_user(
            username='instructor1',
            password='password',
            role='Instructor'
        )

        self.ta = User.objects.create_user(
            username='ta1',
            password='password',
            role='TA'
        )

        self.semester = Semester.objects.create(
            semester_name='Spring 2000',
            start_date=datetime(2000, 1, 1),
            end_date=datetime(2000, 5, 5)
        )

        self.course = Course.objects.create(
            course_code='CS101',
            course_name='Intro to Computer Science',
            semester=self.semester
        )

        self.course_section = CourseSection.objects.create(
            course=self.course,
            instructor=self.instructor,
            course_section_number=1,
            start_time='10:00',
            end_time='11:00'
        )

        self.lab_section = LabSection.objects.create(
            course=self.course,
            lab_section_number=1,
            start_time='11:00',
            end_time='12:00'
        )

        TALabAssignment.objects.create(
            lab_section=self.lab_section,
            ta=self.ta
        )

    def test_course_view_renders_correct_template(self):
        url = reverse('course_view', args=[self.course.course_code, self.semester.semester_name])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'selected_course/selected_course.html')

    def test_course_view_displays_course_information(self):
        url = reverse('course_view', args=[self.course.course_code, self.semester.semester_name])
        response = self.client.get(url)
        self.assertContains(response, 'Intro to Computer Science')

    def test_course_view_displays_sections(self):
        url = reverse('course_view', args=[self.course.course_code, self.semester.semester_name])
        response = self.client.get(url)
        self.assertContains(response, self.course_section.course_section_number)

    def test_course_view_displays_tas(self):
        url = reverse('course_view', args=[self.course.course_code, self.semester.semester_name])
        response = self.client.get(url)
        self.assertContains(response, self.ta.username)

    def test_course_view_displays_instructors(self):
        url = reverse('course_view', args=[self.course.course_code, self.semester.semester_name])
        response = self.client.get(url)
        self.assertContains(response, self.instructor.username)

    def test_course_view_with_invalid_course_code_and_semester(self):
        url = reverse('course_view', args=['INVALID_CODE', 'INVALID_SEMESTER'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)