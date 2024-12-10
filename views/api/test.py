from django.test import TestCase, Client
from ta_scheduler.models import User

class TestSearchUserAPI(TestCase):
    def setUp(self):
        self.client = Client()
        User.objects.create(username='jboy', first_name='John', last_name='Boyland', password='password')
        User.objects.create(username='lanfar', first_name='Landon', last_name='Faris', password='password')

    def test_search_user_api(self):
        response = self.client.get('/api/search/user/?query=j')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Boyland")
        self.assertNotContains(response, "Landon Faris")
