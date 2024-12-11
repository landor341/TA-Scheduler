from django.test import TestCase, Client
from ta_scheduler.models import User
from core.user_controller.UserController import UserController

class TestSearchUserAPI(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin', first_name='Admin', last_name='User', password='adminpass', role='Admin'
        )
        self.client = Client()
        self.client.login(username='admin', password='adminpass')

        self.user1 = User.objects.create_user(username='jboy', first_name='John', last_name='Boyland',
                                              password='password')
        self.user2 = User.objects.create_user(username='lanfar', first_name='Landon', last_name='Faris',
                                              password='password')


    def test_api_search_users(self):
        queries = ['j', '', 'lanfar', 'faris', 'l', 'jb', 'admin']
        for query in queries:
            with self.subTest(query=query):
                expected_results = [
                    {"username": user.username, "name": user.name}
                    for user in UserController.searchUser(query)
                ]
                response = self.client.get(f"/api/search/user/?query={query}")
                self.assertEqual(response.status_code, 200, msg=f"Failed for query: {query}")
                self.assertJSONEqual(
                    response.content,
                    expected_results,
                    msg=f"Unexpected JSON response for query: {query}"
                )
