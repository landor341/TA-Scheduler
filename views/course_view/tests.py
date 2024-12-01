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

        self.semester = Semester.objects.create(start_date=datetime(2000, 1, 1),
                                                end_date=datetime(2000, 5, 5))

        self.course = Course.objects.create(
            course_code='CS101',
            course_name='Intro to Computer Science',
            semester_id=1
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
        response = self.client.get(reverse('course_view', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'selected_course/selected_course.html')

    def test_course_view_displays_course_information(self):
        response = self.client.get(reverse('course_view', args=[self.course.id]))
        self.assertContains(response, 'Intro to Computer Science')

    def test_course_view_displays_sections(self):
        response = self.client.get(reverse('course_view', args=[self.course.id]))
        self.assertContains(response, self.course_section.course_section_number)

    def test_course_view_displays_tas(self):
        response = self.client.get(reverse('course_view', args=[self.course.id]))
        self.assertContains(response, self.ta.username)

    def test_course_view_displays_instructors(self):
        response = self.client.get(reverse('course_view', args=[self.course.id]))
        self.assertContains(response, self.instructor.username)

    def test_course_view_with_invalid_course_id(self):
        response = self.client.get(reverse('course_view', args=[999]))  # Assuming 999 is an invalid ID
        self.assertEqual(response.status_code, 404)