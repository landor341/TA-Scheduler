from django.core.exceptions import ValidationError, PermissionDenied
from django.test import TestCase, Client
from django.urls import reverse

from core.local_data_classes import UserFormData
from ta_scheduler.models import User, Course


def loginAsRole(client: Client, role: str, password: str):
    user = User.objects.create_user(
        username='loggedinuser', password=password, email='loginUser@example.com', first_name='log',
        last_name='man', role=role, phone='9990009999', address='123 Logged in', office_hours="Loginstuff",
        skills=["Python", "Django"]
    )
    client.login(username=user.username, password=password)
    return user

class UserFormAssertions(TestCase):
    def assertCorrectProfile(self, form_data: UserFormData, user: User):
        self.assertIsInstance(form_data, UserFormData, "Returned data of wrong type")
        self.assertEqual(form_data.username, user.username, "Incorrect username returned")
        self.assertEqual(form_data.first_name, user.first_name, "Incorrect first name returned")
        self.assertEqual(form_data.last_name, user.last_name, "Incorrect last name returned")
        self.assertEqual(form_data.office_hours, user.office_hours, "Incorrect office hours returned")
        self.assertEqual(form_data.email, user.email, "Incorrect email returned")
        self.assertEqual(form_data.phone, user.phone, "Incorrect phone returned")
        self.assertEqual(form_data.address, user.address, "Incorrect address returned")
        self.assertEqual(form_data.role, user.role, "Incorrect role returned")
        form_skills = form_data.skills or []
        user_skills = user.skills or []

        self.assertEqual(form_skills, user_skills, "Incorrect skills returned")


class TestGetUserFormPermissions(UserFormAssertions):
    def setUp(self):
        self.client = Client()

    def testTAGetNewUserForm(self):
        self.user = loginAsRole(self.client, "TA", "test")
        response = self.client.get(reverse("user-creator"))
        self.assertRedirects(response, reverse("home"))

    def testInstructorGetNewUserForm(self):
        self.user = loginAsRole(self.client, "Instructor", "test")
        response = self.client.get(reverse("user-creator"))
        self.assertRedirects(response, reverse("home"))

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
            "phone": "1111111111",
            "address": "New address",
            "role": self.user.role,
            "skills": ["Python, Java"],
        })
        self.assertTrue(User.objects.filter(
            username=self.user.username,
            first_name="newman",
            last_name="newguy",
            office_hours="NEW HOURS",
            email="newguy@gmail.com",
            phone="1111111111",
            address="New address",
            role=self.user.role,
            skills=["Python, Java"],
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
            "phone": "1111111111",
            "address": "New address",
            "role": self.user.role,
            "skills": ["Python, Java"],
        })
        self.assertTrue(User.objects.filter(
            username=self.user.username,
            first_name="newman",
            last_name="newguy",
            office_hours="NEW HOURS",
            email="newguy@gmail.com",
            phone="1111111111",
            address="New address",
            role=self.user.role,
            skills=["Python, Java"],
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
            "skills": self.user.skills,
        })
        self.assertFalse(User.objects.filter(username=self.user.username, role="TA").exists(),
                         "Failed to stop instructor from changing their own role")

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
            "skills": self.user.skills,
        })
        self.assertFalse(User.objects.filter(username=self.user.username, role="Instructor").exists(),
                         "Failed to stop TA from changing their own role")


class TestGetUserFormAdminPermissions(UserFormAssertions):
    def setUp(self):
        self.client = Client()
        self.user = loginAsRole(self.client, "Admin", "testtesttest")
        self.url = reverse("user-form", kwargs={
            "username": self.user.username
        })

    def testAdminPostValidUser(self):
        admin_user = User.objects.create(
            username="admin", first_name="Admin", last_name="User", email="admin@example.com", role="Admin"
        )
        self.client.force_login(admin_user)

        url = reverse("user-creator")
        response = self.client.post(url, {
            "username": "newuser",
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "phone": "5555555555",
            "address": "123 Main St",
            "role": "Instructor",
            "office_hours": "9am-5pm",
            "skills": ["Python", "Data-Analysis"],
        })

        if response.status_code == 400:
            print("ERRORS:", response.content.decode())

        self.assertIn(response.status_code, [200, 302], "Failed to create a user")

        self.assertTrue(User.objects.filter(
            username="newuser",
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            phone="5555555555",
            address="123 Main St",
            role="Instructor",
            office_hours="9am-5pm",
            skills=["Python", "Data-Analysis"],
        ).exists(), "Failed to save valid user")

    def testInvalidMissingUsername(self):
        response = self.client.post(
            self.url,
            {
                "username": "",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "role": "TA",
            },
        )
        self.assertContains(response, "Username must be a valid value", status_code=400)

    def test_invalid_skills_type(self):
        """Tests if a ValidationError is raised when 'skills' is not a list."""
        url = reverse("user-creator")
        response = self.client.post(url, {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "phone": "111-111-1111",
            "address": "Test address",
            "role": "TA",
            "office_hours": "9-5",
            "skills": [123, {}],  # Invalid skills type
        })
        self.assertContains(response, "Skills must be a valid value", status_code=400)

    def testAdminPostInvalidUser(self):
        url = reverse("user-creator")
        response = self.client.post(url, {
            "username": "",
            "first_name": "newguy",
            "last_name": "newman",
            "email": "newguy@gmail.com",
            "phone": "111-111-1111",
            "address": "New address",
            "role": "TA",
            "office_hours": "NEW HOURS",
            "skills": ["Python", "Java"],
        })
        self.assertContains(response, "Username must be a valid value", status_code=400)

    def testAdminPostOnOtherUser(self):
        other = User.objects.create(
            username="testuser",
            first_name="Test",
            last_name="User",
            phone="3333333333",
            address="Here's a problem",
            office_hours="my hours",
            email="test@gmail.com",
            role="TA",
            skills="SQL",
        )

        url = reverse("user-creator")
        response = self.client.post(url, {
            "username": "testuser",
            "first_name": "master",
            "last_name": "chief",
            "email": "masterchief@halo.com",
            "phone": "7777777777",
            "address": "Noble Street",
            "role": "Instructor",
            "office_hours": "6 AM - 8 PM",
            "skills": ["Leadership", "Strategy"],
        })

        self.assertIn(response.status_code, [200, 302], "Failed to handle saving valid update for other users")

        self.assertTrue(User.objects.filter(
            username="testuser",
            first_name="master",
            last_name="chief",
            email="masterchief@halo.com",
            phone="7777777777",
            address="Noble Street",
            role="Instructor",
            office_hours="6 AM - 8 PM",
            skills=["Leadership", "Strategy"]
        ).exists(), "Failed to save updates for user")

class TestPostNewUserForm(UserFormAssertions):
    def setUp(self):
        self.client = Client()
        self.user = loginAsRole(self.client, "Admin", "test")

    def testPostEmpty(self):
        response = self.client.post(reverse("user-form", kwargs={"username": "testuser"}), {
            "username": "",
            "first_name": "",
            "last_name": "",
            "office_hours": "",
            "email": "",
            "phone": "",
            "address": "",
            "role": "",
            "skills": [],
        })

        # Access response.context['errors'] instead of 'form'
        if response.status_code == 400:
            print("Validation Errors:", response.context['errors'])

        self.assertFalse(User.objects.filter(username="").exists(), "Created user with empty data")
        self.assertIn("Username must be a valid value", response.context['errors'])
        self.assertIn("First name must be a valid value", response.context['errors'])

    def testPostInvalidUsername(self):
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":  # Iterate invalid characters
            value = "user" + c
            response = self.client.post(reverse("user-creator"), {
                "username": value,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
                "skills": self.user.skills,
            })

            # Debug the response in case of missing context
            if response.context is None:
                print("Response Context is None")
                print("Response Status Code:", response.status_code)
                print("Raw Response Content:", response.content.decode())
                self.fail("Response did not include context for validation errors.")

            # Validate error message
            errors = response.context.get('errors', [])
            print("Validation Errors:", errors)  # Debugging
            self.assertTrue(
                any("Username must be a valid value" in e for e in errors),
                f"Expected 'Username must be a valid value', got {errors}"
            )
            self.assertFalse(User.objects.filter(username=value).exists(), "Created user with invalid username")

    def testPostInvalidFirstName(self):
        count = 1
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post(reverse("user-creator"), {
                "username": "test" + str(count),
                "first_name": value,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
                "skills": self.user.skills,
            })
            if response.status_code == 400:
                print("Validation Errors:", response.context['errors'])

            self.assertIn("First name must be a valid value", response.context['errors'])
            self.assertFalse(User.objects.filter(username=self.user.username, first_name=value).exists(),
                             "Created user with invalid first name")
            count += 1

    def testPostInvalidLastname(self):
        count = 1
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\":
            value = "user" + c
            response = self.client.post(reverse("user-creator"), {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": value,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
                "skills": self.user.skills,
            })
            if response.status_code == 400:
                print("Validation Errors:", response.context['errors'])

            self.assertIn("Last name must be a valid value", response.context['errors'])
            self.assertFalse(User.objects.filter(username=self.user.username, last_name=value).exists(),
                             "Created user with invalid last name")
            count += 1

    def testPostInvalidSkills(self):
        response = self.client.post(reverse("user-form", kwargs={"username": "invalid_username"}), {
            "username": "valid_username",
            "first_name": "ValidFirstName",
            "last_name": "ValidLastName",
            "skills": "!@#$%^&*()",
        })

        # Adjust debugging to print raw response content
        if response.status_code == 400:
            print("Validation Errors:", response.context['errors'])

        self.assertIn("Skills must be a valid value", response.context['errors'])

    def testPostDuplicate(self):
        test_user = User.objects.create_user(
            username="realguy", password="1", email="realguy@example.com",
            first_name="a", last_name="b", role="TA", phone="1234567890",
            address="123 Main St", office_hours="Mon-Fri", skills=["Python", "SQL"]
        )
        response = self.client.post(reverse("user-form", kwargs={"username": test_user.username}), {
            "username": "realguy",
            "first_name": "override",
            "last_name": test_user.last_name,
            "email": test_user.email,
            "role": test_user.role,
            "skills": test_user.skills,
        })

        # Gracefully handle missing context
        if response.context is None:
            print("Response Context is None")
            print("Response Status Code:", response.status_code)
            print("Raw Response Content:", response.content.decode())
            self.fail("Response did not include validation error context.")

        # Validate specific error messages
        errors = response.context.get('errors', [])
        print("Validation Errors:", errors)
        self.assertTrue(
            any("username already exists" in e.lower() for e in errors),
            f"Expected 'username already exists' error, got {errors}"
        )

    def testValid(self):
        response = self.client.post(reverse("user-creator"), {
            "username": "testuser",
            "first_name": "Johnny",
            "last_name": "Testman",
            "email": "johnnytest@example.com",
            "role": "Instructor",
            "skills": ["Python", "Django"],
        })
        self.assertTrue(
            User.objects.filter(username="testuser", email="johnnytest@example.com").exists(),
            "Failed to successfully save new user"
        )

    def testPostInvalidEmail(self):
        count = 1
        for c in "!#$%^&*()_=+`~'\"|]}[{<>?/\\":  # Iterate invalid characters in email
            value = f"user{c}@example.com"
            response = self.client.post(reverse("user-creator"), {
                "username": f"test{count}",
                "first_name": "ValidFirstName",
                "last_name": "ValidLastName",
                "email": value,
                "phone": "1234567890",
                "role": "Instructor",
            })

            # Gracefully handle missing context
            if response.context is None:
                print("Response Context is None")
                print("Response Status Code:", response.status_code)
                print("Raw Response Content:", response.content.decode())
                self.fail("Response did not include validation error context.")

            # Validate specific error messages
            errors = response.context.get('errors', [])
            print("Validation Errors:", errors)
            self.assertTrue(
                any("Email must be a valid value" in e.lower() for e in errors),
                f"Expected 'email must be a valid value', got {errors}"
            )
            count += 1

    def testPostInvalidPhone(self):
        count = 1
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\abcdefghijklmnopqrstuvwxyz":
            value = "123444555" + c
            response = self.client.post(reverse("user-creator"), {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": value,
                "address": self.user.address,
                "role": self.user.role,
            })
            if response.status_code == 400:
                print("Validation Errors:", response.context['errors'])

            self.assertIn("Phone must be a valid value", response.context['errors'])
            self.assertFalse(User.objects.filter(username=self.user.username, phone=value).exists(),
                             "Created user with invalid phone #")
            count += 1

    def testPostInvalidAddress(self):
        count = 1
        for c in "!@$%^*()_=+`~\"|]}[{<>?\\":
            value = "324 test lane " + c
            response = self.client.post(reverse("user-creator"), {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": value,
                "role": self.user.role,
            })
            if response.status_code == 400:
                print("Validation Errors:", response.context['errors'])

            self.assertIn("Address must be a valid value", response.context['errors'])
            self.assertFalse(User.objects.filter(username=self.user.username, address=value).exists(),
                             "Created user with invalid address")
            count += 1

    def testPostInvalidRole(self):
        count = 1
        for value in ["", "FakeRole", "1213", "`^7"]:
            response = self.client.post(reverse("user-creator"), {
                "username": "test" + str(count),
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": value,
            })
            if response.status_code == 400:
                print("Validation Errors:", response.context['errors'])

            self.assertIn("Role must be a valid value", response.context['errors'])
            self.assertFalse(User.objects.filter(username=self.user.username, role=value).exists(),
                             "Created user with role")
            count += 1

class TestPostExistingUserForm(UserFormAssertions):
    def setUp(self):
        self.client = Client()
        self.login_user = loginAsRole(self.client, "Admin", "test")

        self.user = User.objects.create_user(
            username="realguy", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday", skills=["Python, SQL"]
        )

        self.url = reverse("user-form", kwargs={
            "username": self.user.username
        })

    def testPostModifyUsername(self):
        """Test that modifying the username is not allowed."""
        new_username = "new_username"
        response = self.client.post(self.url, {
            "username": new_username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "office_hours": self.user.office_hours,
            "email": self.user.email,
            "phone": self.user.phone,
            "address": self.user.address,
            "role": self.user.role,
            "skills": self.user.skills,
        })
        self.assertContains(response, "Cannot change username", status_code=400)
        self.assertFalse(User.objects.filter(username="new username").exists(), "Accepted illegal username change")

    def testPostInvalidUsername(self):
        """Test that empty or invalid usernames are rejected."""
        invalid_usernames = ["", " ", "user@name", "user.name", "user name", "user-name!", "123@456"]

        for username in invalid_usernames:
            response = self.client.post(self.url, {
                "username": username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
                "skills": self.user.skills,
            })

            self.assertContains(response, "Username must be a valid value", status_code=400)
            self.assertFalse(
                User.objects.filter(username=username).exists(),
                f"Invalid username '{username}' was saved in the database")

    def testPostInvalidSkills(self):
        """Test invalid skills containing special characters."""
        for c in "!@$%^*()_=+`~\"|]}[{<>?/\\":
            value = "skill" + c
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
                "skills": value,
            })
            self.assertContains(response, "Skills must be a valid value", status_code=400)
            self.assertFalse(User.objects.filter(username=self.user.username, skills=value).exists(),
                             "Saved user with invalid skills")

    def testPostInvalidSkillsEdgeCases(self):
        """Test invalid edge cases for skills."""
        invalid_skill_cases = [
            "",
            " ",
            "python*",
            ["Skill1", ""]
            ["ValidSkill", "Invalid*"],
            123,
            {"key": "val"}
        ]

        for case in invalid_skill_cases:
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
                "skills": case,
            })
            self.assertContains(
                response, "Skills must be a valid value", status_code=400)
            self.assertFalse(
                User.objects.filter(username=self.user.username, skills=case).exists(),
                f"Saved user with invalid skills: {case}")

    def testPostValidSkills(self):
        """Test valid skills."""
        valid_skill_cases = [
            "Python",
            ["Skill1", "Skill-2"],
            "Machine Learning",
            ["Python, Django", "AI"],
            "Data-Science",
        ]

        for case in valid_skill_cases:
            response = self.client.post(self.url, {
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "office_hours": self.user.office_hours,
                "email": self.user.email,
                "phone": self.user.phone,
                "address": self.user.address,
                "role": self.user.role,
                "skills": case,
            })
            self.assertNotContains(
                response, "Skills must be a valid value", status_code=200
            )
            self.assertTrue(
                User.objects.filter(username=self.user.username, skills=case).exists(),
                f"Failed to save user with valid skills: {case}"
            )

    def testModifyAll(self):
        """Test updating all fields successfully."""
        response = self.client.post(self.url, {
            "username": self.user.username,
            "first_name": "newman",
            "last_name": "newguy",
            "office_hours": "NEW HOURS",
            "email": "newguy@gmail.com",
            "phone": "1111111111",
            "address": "New address",
            "role": "TA",
            "skills": ["Machine Learning, AI"],
        })
        self.assertRedirects(response, reverse("profile", kwargs={"username": self.user.username}))
        self.assertTrue(User.objects.filter(
            username=self.user.username,
            first_name="newman",
            last_name="newguy",
            office_hours="NEW HOURS",
            email="newguy@gmail.com",
            phone="1111111111",
            address="New address",
            role="TA",
            skills=["Machine Learning, AI"]
        ).exists(), "Failed to save modified user")

    def testPostEmpty(self):
        """Test attempting to submit a form with all empty fields."""
        response = self.client.post(self.url, {
            "username": "",
            "first_name": "",
            "last_name": "",
            "office_hours": "",
            "email": "",
            "phone": "",
            "address": "",
            "role": "",
            "skills": "",
        })
        self.assertContains(response, "Username must be a valid value", status_code=400)
        self.assertContains(response, "Email must be a valid value", status_code=400)
        self.assertContains(response, "Role must be a valid value", status_code=400)
        self.assertContains(response, "First name must be a valid value", status_code=400)
        self.assertContains(response, "Last name must be a valid value", status_code=400)
        self.assertFalse(User.objects.filter(first_name="").exists(), "Created user with empty data")

    def testPostInvalidRole(self):
        """Test invalid roles."""
        invalid_roles = ["", "FakeRole", "1213", "`^7"]
        for value in invalid_roles:
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
            self.assertContains(response, "Role must be a valid value", status_code=400)
            self.assertFalse(
                User.objects.filter(username=self.user.username, role=value).exists(),
                f"Saved user with invalid role: {value}")

    def testPostValidRole(self):
        """Test saving valid roles."""
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
            self.assertRedirects(response, reverse("profile", kwargs={"username": self.user.username}))
            self.assertTrue(User.objects.filter(username=self.user.username, role=value).exists(),
                            "Failed to save user with valid role")

    def testPostInvalidEmail(self):
        """Test emails with invalid formats."""
        for value in ["invalid_email", "user@", "user@domain", "user!@email.com"]:
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
            self.assertContains(response, "Email must be a valid value", status_code=400)
            self.assertFalse(User.objects.filter(username=self.user.username, email=value).exists(),
                             "Saved user with invalid email")

    def testPostInvalidFirstName(self):
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\1234567890":  # Invalid characters
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
            self.assertContains(
                response, "First name must be a valid value", status_code=400)
            self.assertFalse(
                User.objects.filter(username=self.user.username, first_name=value).exists(),
                f"Saved user with invalid first name: {value}")

    def testPostInvalidLastName(self):
        for c in "!@#$%^&*()_=+`~'\"|]}[{<>?/\\1234567890":  # Invalid characters
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
            self.assertContains(
                response, "Last name must be a valid value", status_code=400)
            self.assertFalse(
                User.objects.filter(username=self.user.username, last_name=value).exists(),
                f"Saved user with invalid last name: {value}")

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
            self.assertContains(response, 'Phone must be a valid 10-digit value', status_code=400)
            self.assertFalse(User.objects.filter(username=self.user.username, phone=value).exists(),
                             "Saved user with invalid phone #")

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

            print(response.content.decode())

            self.assertContains(response, "Address must be a valid value", status_code=400)
            self.assertFalse(User.objects.filter(username=self.user.username, address=value).exists(),
                             f"Saved user with invalid address: {value}")

class TestDeleteUser(UserFormAssertions):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="realguy", password="1", email="1@uwm.edu", first_name="a", last_name="b",
            role="TA", phone="1222333444", address="888 poodle drive", office_hours="Tuesday", skills="Python, SQL"
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
        ).exists(), "Allowed admin to delete themselves")