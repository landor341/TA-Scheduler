from django.test import TestCase, Client

from ta_scheduler.models import User


# Test getting course form for new course (only admin can get)
# Test getting course form for existing course (only admin can get)
# Test getting course form for fake course (redirect to home)
# Test saving new course form with empty data
# Test saving new course form with malformed data
# Test saving new course form with good data
# Test saving existing course with empty data
# Test saving existing course with malformed data
# Test saving existing course with good data

def loginAsRole(client: Client, role: str, password: str):
    user = User.objects.create_user(
        username='loggedinuser', password=password, email='loginUser@example.com', first_name='log',
        last_name='man', role=role, phone='9990009999', address='123 Logged in'
    )
    client.login(username=user.username, password=password)
    return user


class TestGetNewCourseFormPermissions(TestCase):
    def testTAGetNewCourseForm(self):
        loginAsRole(self.client, "TA", "test")
        response = self.client.get("course_form")




class TestPostNewCourseForm(TestCase):
    pass # NOTE: Make sure to test that admins cant edit each other

class TestPostNewCourseForm(TestCase):
    pass # NOTE: Make sure to test that admins cant edit each other
    # TODO: Test you cannot modify existing courses semester or code