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
        self.profile_url = reverse('profile')

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

    def test_login_page_get(self):
        """
        Test the GET request to load the login page.
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/login.html')
        self.assertContains(response, '<h2>Login</h2>')

    def test_login_success(self):
        """
        Test successful user login.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertRedirects(response, self.profile_url)

    def test_login_failure(self):
        """
        Test user login failure (incorrect password).
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')

    def test_logout(self):
        """
        Test user logout functionality.
        """
        # Log in first
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)

    def test_profile_page_authenticated(self):
        """
        Test an authenticated user accessing the profile page.
        """
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/profile.html')
        self.assertContains(response, 'Welcome, Test, User!')
        self.assertContains(response, 'testuser@example.com')
        self.assertContains(response, 'Instructor')
        self.assertContains(response, '1234567890')
        self.assertContains(response, '123 Test Street')

    def test_profile_view_redirect_if_not_logged_in(self):
        """
        Test if an unauthenticated user is redirected to /login when accessing /profile.
        """
        response = self.client.get(self.profile_url)
        # Confirm status code is 302 (redirect)
        self.assertEqual(response.status_code, 302)

        # Confirm redirection to /login
        self.assertRedirects(response, f'{self.login_url}?next={self.profile_url}')

    def test_invalid_profile_url(self):
        """
        Test accessing a nonexistent page (invalid URL).
        """
        response = self.client.get('/invalid-profile/')
        self.assertEqual(response.status_code, 404)

    def test_login_case_sensitivity(self):
        """
        Test if login is case-sensitive.
        """
        response = self.client.post(self.login_url, {
            'username': 'TestUser',  # Incorrect case
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')