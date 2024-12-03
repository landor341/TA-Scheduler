from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginTests(TestCase):
    def setUp(self):
        """
        Set up the test environment, including creating a test user and client.
        """
        self.client = Client()
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('home')
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='password123',
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            role='Instructor',
            phone='1234567890',
            address='123 Test Street'
        )
        self.password = 'password123'

    def test_login_success(self):
        """
        Test successful user login.
        """
        response = self.client.post(self.login_url, {
            'username': self.user.username,
            'password': self.password,
        })
        self.assertRedirects(response, self.profile_url)

    def test_login_failure(self):
        """
        Test user login failure (incorrect password).
        """
        response = self.client.post(self.login_url, {
            'username': self.user.username,
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')

    def test_login_case_sensitivity(self):
        """
        Test if login is case-sensitive.
        """
        response = self.client.post(self.login_url, {
            'username': 'TestUser',  # Incorrect case
            'password': self.password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')



    def test_logout(self):
        """
        Test user logout functionality.
        """
        # Log in first
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)

    def test_profile_page_authenticated(self):
        """
        Test that after login you can access your profile.
        """
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_view/profile.html')

