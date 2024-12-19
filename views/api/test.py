from django.test import TestCase, Client
from ta_scheduler.models import User
import json

class TestSearchUserAPI(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin', first_name='Admin', last_name='User', password='adminpass', role='Admin'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass')

        self.user1 = User.objects.create_user(username='jboy', first_name='John', last_name='Boyland',
                                              password='password', role="Instructor")
        self.user2 = User.objects.create_user(username='lanfar', first_name='Landon', last_name='Faris',
                                              password='password', role="TA")

    def test_api_search_users_with_empty(self):
        responses = self.client.get('/api/search/user/?query=')
        self.assertEqual(responses.status_code, 200)
        response_data = json.loads(responses.content)
        self.assertEqual(len(response_data), 3)
        self.assertEqual(response_data[0]['username'], 'admin')
        self.assertEqual(response_data[1]['username'], 'jboy')
        self.assertEqual(response_data[2]['username'], 'lanfar')

    def test_api_search_users_with_single_user(self):
        responses = self.client.get('/api/search/user/?query=jboy')
        self.assertEqual(responses.status_code, 200)

        response_data = json.loads(responses.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['username'], self.user1.username)

    def test_api_search_users_with_multiple_users(self):
        responses = self.client.get('/api/search/user/?query=and')
        self.assertEqual(responses.status_code, 200)

        response_data = json.loads(responses.content)
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]['username'], self.user1.username)
        self.assertEqual(response_data[1]['username'], self.user2.username)

    def test_api_search_with_role(self):
        response = self.client.get('/api/search/user/TA/?query=and')
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['username'], self.user2.username)