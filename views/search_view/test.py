from django.test import TestCase, Client
from django.urls import reverse
from ta_scheduler.models import Semester, Course, User

class TestSearchCourses(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin', first_name='Admin', last_name='User', password='adminpass', role='Admin'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass')

        self.semester = Semester.objects.create(semester_name="Fall 2024", start_date="2024-08-01", end_date="2024-12-31")
        self.course = Course.objects.create(course_code="CS101", course_name="Intro to CS", semester=self.semester)

    def test_get_course_initial_load(self):
        response = self.client.get(reverse('search', args=['course']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fall 2024")
        self.assertContains(response, "CS101")

    def test_post_course_search_with_semester(self):
        response = self.client.post(reverse('search', args=['course']), {
            'query': 'CS101',
            'semester_name': 'Fall 2024'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CS101")

    def test_post_course_search_without_semester(self):
        response = self.client.post(reverse('search', args=['course']), {
            'query': 'CS'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CS101")


class TestSearchUsers(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin', first_name='Admin', last_name='User', password='adminpass', role='Admin'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass')

        self.user1 = User.objects.create_user(username='jboy', first_name='John', last_name='Boyland', password='password')
        self.user2 = User.objects.create_user(username='lanfar', first_name='Landon', last_name='Faris', password='password')

    def test_get_user_initial_load(self):
        response = self.client.get(reverse('search', args=['user']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Boyland")
        self.assertContains(response, "Landon Faris")

    def test_post_user_search(self):
        response = self.client.post(reverse('search', args=['user']), {
            'query': 'jb'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Boyland")
        self.assertNotContains(response, "Landon Faris")

class TestSearchViewPermissions(TestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(
            username='jboy', first_name='John', last_name='Boyland', password='password', role='User'
        )
        self.client = Client()
        self.client.login(username='jboy', password='password')

    def test_non_admin_access(self):
        response = self.client.get(reverse('search', args=['course']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Explorer")
        self.assertNotContains(response, "Add Course")
        self.assertNotContains(response, "Create Semester")