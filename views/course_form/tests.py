from django.test import TestCase, Client
from django.urls import reverse

from ta_scheduler.models import User



def loginAsRole(client: Client, role: str, password: str):
    user = User.objects.create_user(
        username='loggedinuser', password=password, email='loginUser@example.com', first_name='log',
        last_name='man', role=role, phone='9990009999', address='123 Logged in'
    )
    client.login(username=user.username, password=password)
    return user


class TestGetCourseFormRedirects(TestCase):
    def setUp(self):
        self.client = Client()

    def testTAGetNewCourseForm(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.get(reverse("course-creator"))
        self.assertRedirects(response, "home", "Failed to redirect TA to home")

    def testInstructorGetNewCourseForm(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.get(reverse("course-creator"))
        self.assertRedirects(response, "home", "Failed to redirect instructor to home")


class TestAdminGetCourseForm(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = loginAsRole(self.client, "Admin", "test")

    def testGetFake(self):
        response = self.client.get(reverse("course-form", kwargs={code="3", semester="Spring 2024"}))
        self.assertRedirects(response, "home", "Failed to redirect TA to home")
        pass
    def testGetCreateForm(self):
        pass
    def testGetExisting(self):
        pass

class TestPostNewCourseForm(TestCase):
    pass # TODO: Make sure they all redirect
    # Post malformed for different fields
    # On failure returns course form page with data you had sent and an error
    def testPostEmpty(self):
        pass
    def testValid(self):
        pass


class TestPostExistingCourseForm(TestCase):
    pass # TODO: Make sure they all redirect
    # TODO: Test you cannot modify existing courses semester or code
    # Post malformed for different fields
    def testPostModifyCode(self):
        pass
    def testModifySemesterDuplicate(self):
        pass
    def testModifySemesterValid(self):
        pass

    def testPostEmpty(self):
        pass
    def testValid(self):
        pass