from django.test import TestCase, Client
from django.urls import reverse

from core.local_data_classes import UserFormData
from ta_scheduler.models import User, Course


def loginAsRole(client: Client, role: str, password: str):
    user = User.objects.create_user(
        username='loggedinuser', password=password, email='loginUser@example.com', first_name='log',
        last_name='man', role=role, phone='9990009999', address='123 Logged in', office_hours="Loginstuff"
    )
    client.login(username=user.username, password=password)
    return user

class UserFormAssertions(TestCase):
    def assertCorrectProfile(self, form_data: UserFormData, user: User):
        self.assertIsInstance(form_data, UserFormData, "Returnd data of wrong type")
        self.assertEqual(form_data.username, user.username, "Incorrect username returned")
        self.assertEqual(form_data.first_name, user.first_name, "Incorrect first name returned")
        self.assertEqual(form_data.last_name, user.last_name, "Incorrect last name returned")
        self.assertEqual(form_data.office_hours, user.office_hours, "Incorrect office hours returned")
        self.assertEqual(form_data.email, user.email, "Incorrect email returned")
        self.assertEqual(form_data.phone, user.phone, "Incorrect phone returned")
        self.assertEqual(form_data.address, user.address, "Incorrect address returned")
        self.assertEqual(form_data.role, user.role, "Incorrect role returned")


class TestGetUserFormPermissions(UserFormAssertions):
    def setUp(self):
        self.client = Client()

    def testTAGetNewUserForm(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.get(reverse("user-creator"))
        self.assertRedirects(response, "home")

    def testInstructorGetNewUserForm(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.get(reverse("user-creator"))
        self.assertRedirects(response, "home")

    def testTAGetSelf(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.get(reverse("user-form", kwargs={
            "username": self.user.username
        }))
        self.assertCorrectProfile(response.context["data"], self.user)

    def testInstructorGetSelf(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.get(reverse("user-form", kwargs={
            "username": self.user.username
        }))
        self.assertCorrectProfile(response.context["data"], self.user)

    def testAdminGetSelf(self):
        self.user = loginAsRole(self.client, "Admin", "test")
        response = self.client.get(reverse("user-form", kwargs={
            "username": self.user.username
        }))
        self.assertCorrectProfile(response.context["data"], self.user)

    def testTAModifySelf(self):
        self.user = loginAsRole(self.client, "TA", "test")
        self.url = reverse("user-form", kwargs={
            "username": self.user.username
        })
        response = self.client.post(self.url, {
            "username": self.user.username,
            "first_name": "newman",
            "last_name": "newguy",
            "office_hours": "NEW HOURS",
            "email": "newguy@gmail.com",
            "phone": "111-111-1111",
            "address": "New address",
            "role": self.user.role,
        })
        self.assertTrue(User.objects.filter(
            username=self.user.username,
            first_name="newman",
            last_name="newguy",
            office_hours="NEW HOURS",
            email="newguy@gmail.com",
            phone="111-111-1111",
            address="New address",
            role=self.user.role
        ).exists(), "Failed to allow TA to edit their own info")

    def testInstructorModifySelf(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        self.url = reverse("user-form", kwargs={
            "username": self.user.username
        })
        response = self.client.post(self.url, {
            "username": self.user.username,
            "first_name": "newman",
            "last_name": "newguy",
            "office_hours": "NEW HOURS",
            "email": "newguy@gmail.com",
            "phone": "111-111-1111",
            "address": "New address",
            "role": self.user.role,
        })
        self.assertTrue(User.objects.filter(
            username=self.user.username,
            first_name="newman",
            last_name="newguy",
            office_hours="NEW HOURS",
            email="newguy@gmail.com",
            phone="111-111-1111",
            address="New address",
            role=self.user.role
        ).exists(), "Failed to allow instructor to edit their own info")

    def testInstructorModifyRole(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        self.url = reverse("user-form", kwargs={
            "username": self.user.username
        })
        response = self.client.post(self.url, {
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "office_hours": self.user.office_hours,
            "email": self.user.email,
            "phone": self.user.phone,
            "address": self.user.address,
            "role": "TA",
        })
        self.assertFalse(User.objects.filter(username=self.user.username, role="TA").exists(), "Failed to stop instructor from changing their own role")

    def testTAModifyRole(self):
        self.user = loginAsRole(self.client, "TA", "test")
        self.url = reverse("user-form", kwargs={
            "username": self.user.username
        })
        response = self.client.post(self.url, {
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "office_hours": self.user.office_hours,
            "email": self.user.email,
            "phone": self.user.phone,
            "address": self.user.address,
            "role": "Instructor",
        })
        self.assertFalse(User.objects.filter(username=self.user.username, role="Instructor").exists(), "Failed to stop TA from changing their own role")


class TestAdminGetUserForm(UserFormAssertions):
    def setUp(self):
        self.client = Client()
        self.user = loginAsRole(self.client, "Admin", "test")

    def testGetFake(self):
        response = self.client.get(reverse("user-form", kwargs={
            "username": "fakityfakeuser"
        }))
        self.assertRedirects(response, "home")

    def testGetCreateForm(self):
        response = self.client.get(reverse("course-creator"))
        form_data: UserFormData = response.context["data"]
        self.assertIsInstance(form_data, UserFormData, "Returned data of wrong type")
        self.assertEqual(form_data.username, "", "Form prefilled username on new user form")
        self.assertEqual(form_data.first_name, "", "Form prefilled first name on new user form")
        self.assertEqual(form_data.last_name, "", "Form prefilled last name on new user form")
        self.assertEqual(form_data.office_hours, "", "Form prefilled office hours on new user form")
        self.assertEqual(form_data.email, "", "Form prefilled email on new user form")
        self.assertEqual(form_data.phone, "", "phone")
        self.assertEqual(form_data.address, "", "address")
        self.assertEqual(form_data.role, "", "Form prefilled role on new user form")

    def testGetExisting(self):
        test_user = User.objects.create_user(
            username="a", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )
        url = reverse("user-form", kwargs={
            "username": test_user.username
        })

        response = self.client.get(url)
        form_data: UserFormData = response.context["data"]
        self.assertCorrectProfile(form_data, test_user)


class TestPostNewCourseForm(UserFormAssertions):
    def setUp(self):
        self.client = Client()
        self.user = loginAsRole(self.client, "Admin", "test")

    def testPostEmpty(self):
        response = self.client.post("course-creater", {
            "username": "",
            "first_name": "",
            "last_name": "",
            "office_hours": "",
            "email": "",
            "phone": "",
            "address": "",
            "role": "",
        })
        self.assertFalse(User.objects.filter(first_name="").exists(), "Created user with empty data")
        self.assertContains(response, [
            "username must be a valid value",
            'first name must be a valid value',
            'last name name must be a valid value',
            'office hours name must be a valid value',
            'email name must be a valid value',
            'phone name must be a valid value',
            'address must be a valid value',
            'role must be a valid role',
        ])

    def testPostInvalidUsername(self):
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post("course-creater", {
                "username": value,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['username must be a valid value'])
            self.assertFalse(User.objects.filter(username=value).exists(), "Created user with invalid username")

    def testPostInvalidFirstName(self):
        count = 1
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post("course-creater", {
                "username": "test" + str(count),
                "first_name": value,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['first name must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, first_name=value).exists(), "Created user with invalid first name")
            count = count + 1

    def testPostInvalidLastname(self):
        count = 1
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post("course-creater", {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": value,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['last name must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, last_name=value).exists(), "Created user with invalid last name")
            count = count + 1

    def testPostInvalidEmail(self):
        count = 1
        for c in "!#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post("course-creater", {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": value,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['email must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, email=value).exists(), "Created user with invalid email")
            count = count + 1

    def testPostInvalidPhone(self):
        count = 1
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\abcdefghijklmnopqrstuvwxyz":
            value = "123444555" + c
            response = self.client.post("course-creater", {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": value,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['phone must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, phone=value).exists(), "Created user with invalid phone #")
            count = count + 1

    def testPostInvalidAddress(self):
        count = 1
        for c in "!@$%^*()_=+`~\"|]}[{<>?\\":
            value = "324 test lane " + c
            response = self.client.post("course-creater", {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": value,
                "role": self.user.role,
            })
            self.assertContains(response, ['address must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, address=value).exists(), "Created user with invalid address")
            count = count + 1

    def testPostInvalidRole(self):
        count = 1
        for value in ["", "FakeRole", "1213", "\`^7"]:
            response = self.client.post("course-creater", {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": value,
            })
            self.assertContains(response, ['role must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, role=value).exists(), "Created user with role")
            count = count + 1

    def testPostDuplicate(self):
        test = User.objects.create_user(
            username="realguy", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )
        response = self.client.post("user-creater", {
                "username": test.username,
                "first_name": "override",
                "last_name": test.last_name,
                "office_hours": test.office_hours,
                "email": test.email,
                "phone": test.phone,
                "address": test.address,
                "role": test.role,
        })
        self.assertContains(response, ['Someone with that username already exists'])
        self.assertFalse(Course.objects.filter(
            username=test.username,
            first_name="override"
        ).exists(), "Overwrote existing user")

    def testValid(self):
        response = self.client.post("user-creater", {
                "username": "1234",
                "first_name": "testdood",
                "last_name": "man",
                "office_hours": "1-3 MF",
                "email": "12test@gmail.com",
                "phone": "222-444-6704",
                "address": "man road",
                "role": "Admin",
        })
        self.assertTrue(User.objects.filter(
            username="1234"
        ).exists(), "Failed to successfully save new user")


class TestPostExistingUserForm(UserFormAssertions):
    def setUp(self):
        self.client = Client()
        self.login_user = loginAsRole(self.client, "Admin", "test")

        self.user = User.objects.create_user(
            username="realguy", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )

        self.url = reverse("user-form", kwargs={
            "username": self.user.username
        })

    def testPostModifyUsername(self):
        response = self.client.post(self.url, {
                "username": "new username",
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
        })
        self.assertContains(response, ['Cannot change username'])
        self.assertFalse(User.objects.filter(
            username="new username",
        ).exists(), "Accepted illegal username change")

    def testPostInvalidFirstName(self):
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": value,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['first name must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, first_name=value).exists(), "Saved user with invalid first name")

    def testPostInvalidLastname(self):
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": value,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['last name must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, last_name=value).exists(), "Saved user with invalid last name")

    def testPostInvalidEmail(self):
        for c in "!#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": value,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['email must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, email=value).exists(), "saved user with invalid email")

    def testPostInvalidPhone(self):
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\abcdefghijklmnopqrstuvwxyz":
            value = "123444555" + c
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": value,
                "address": self.user.address,
                "role": self.user.role,
            })
            self.assertContains(response, ['phone must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, phone=value).exists(), "Saved user with invalid phone #")

    def testPostInvalidAddress(self):
        for c in "!@$%^*()_=+`~\"|]}[{<>?\\":
            value = "324 test lane " + c
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": value,
                "role": self.user.role,
            })
            self.assertContains(response, ['address must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, address=value).exists(), "Saved user with invalid address")

    def testPostInvalidRole(self):
        count = 1
        for value in ["", "FakeRole", "1213", "\`^7"]:
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": value,
            })
            self.assertContains(response, ['role must be a valid value'])
            self.assertFalse(User.objects.filter(username=self.user.username, role=value).exists(), "Saved user with invalid role")
            count = count + 1

    def testPostValidRole(self):
        count = 1
        for value in ["Admin", "Instructor", "TA"]:
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": value,
            })
            self.assertTrue(User.objects.filter(username=self.user.username, role=value).exists(), "Failed to save user with valid role")
            count = count + 1

    def testPostEmpty(self):
        response = self.client.post(self.url, {
            "username": "",
            "first_name": "",
            "last_name": "",
            "office_hours": "",
            "email": "",
            "phone": "",
            "address": "",
            "role": "",
        })
        self.assertFalse(User.objects.filter(first_name="").exists(), "Created user with empty data")
        self.assertContains(response, [
            "username must be a valid value",
            'first name must be a valid value',
            'last name name must be a valid value',
            'office hours name must be a valid value',
            'email name must be a valid value',
            'phone name must be a valid value',
            'address must be a valid value',
            'role must be a valid role',
        ])

    def testModifyAll(self):
        response = self.client.post(self.url, {
            "username": self.user.username,
            "first_name": "newman",
            "last_name": "newguy",
            "office_hours": "NEW HOURS",
            "email": "newguy@gmail.com",
            "phone": "111-111-1111",
            "address": "New address",
            "role": "TA",
        })
        self.assertTrue(User.objects.filter(
            username=self.user.username,
            first_name="newman",
            last_name="newguy",
            office_hours="NEW HOURS",
            email="newguy@gmail.com",
            phone="111-111-1111",
            address="New address",
            role="TA"
        ).exists(), "Failed to save modified user")


class TestDeleteUser(UserFormAssertions):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="realguy", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday"
        )

        self.url = reverse("user-form", kwargs={
            "username": self.user.username
        })

    def testTADeleteOther(self):
        self.login_user = loginAsRole(self.client, "TA", "test")
        response = self.client.delete(self.url)

        self.assertTrue(User.objects.filter(
            username=self.user.username,
        ).exists(), "Allowed TA to delete a user")

    def testTADeleteSelf(self):
        self.login_user = loginAsRole(self.client, "TA", "test")
        self.login_user_url = reverse("user-form", kwargs={
            "username": self.login_user.username
        })
        response = self.client.delete(self.login_user_url)

        self.assertTrue(User.objects.filter(
            username=self.login_user.username,
        ).exists(), "Allowed TA to delete themselves")

    def testInstructorDeleteOther(self):
        self.login_user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.delete(self.url)

        self.assertTrue(User.objects.filter(
            username=self.user.username,
        ).exists(), "Allowed instructor to delete a user")

    def testInstructorDeleteSelf(self):
        self.login_user = loginAsRole(self.client, "Instructor", "test")
        self.login_user_url = reverse("user-form", kwargs={
            "username": self.login_user.username
        })
        response = self.client.delete(self.login_user_url)

        self.assertTrue(User.objects.filter(
            username=self.login_user.username,
        ).exists(), "Allowed instructor to delete themselves")

    def testAdminDeleteOther(self):
        self.login_user = loginAsRole(self.client, "Admin", "test")
        response = self.client.delete(self.url)

        self.assertFalse(User.objects.filter(
            username=self.user.username,
        ).exists(), "Didn't Allow admin to delete a user")

    def testAdminDeleteSelf(self):
        self.login_user = loginAsRole(self.client, "Admin", "test")
        self.login_user_url = reverse("user-form", kwargs={
            "username": self.login_user.username
        })
        response = self.client.delete(self.login_user_url)

        self.assertTrue(User.objects.filter(
            username=self.login_user.username,
        ).exists(), "Allowed instructor to delete themselves")

