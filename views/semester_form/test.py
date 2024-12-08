from django.test import TestCase, Client
from django.urls import reverse
from ta_scheduler.models import Semester, User
from core.semester_controller.SemesterController import SemesterController


class TestSemesterFormView(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_user = User.objects.create_user(
            username="admin", password="adminpass", role="Admin"
        )
        self.non_admin_user = User.objects.create_user(
            username="nonadmin", password="nonadminpass", role="TA"
        )

        self.semester_1 = Semester.objects.create(
            semester_name="Fall 2023",
            start_date="2023-08-15",
            end_date="2023-12-15",
        )
        self.semester_2 = Semester.objects.create(
            semester_name="Spring 2024",
            start_date="2024-01-10",
            end_date="2024-05-10",
        )

    def test_get_creator_mode(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("semester-creator"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["creator"])
        self.assertEqual(len(response.context["existSemester"]), 2)

    def test_get_editor_mode(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("semester-editor", args=["Fall 2023"]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context.get("creator", False))
        self.assertEqual(response.context["data"]["semester_name"], "Fall 2023")

    def test_get_redirect_for_non_admin(self):
        self.client.login(username="nonadmin", password="nonadminpass")
        response = self.client.get(reverse("semester-creator"))
        self.assertRedirects(response, reverse("home"))

    def test_post_create_new_semester(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.post(
            reverse("semester-creator"),
            data={
                "semester_name": "Summer 2024",
                "start_date": "2024-06-01",
                "end_date": "2024-08-01",
                "isCreator": "True",
            },
        )
        self.assertRedirects(response, reverse("semester-creator"))
        self.assertTrue(Semester.objects.filter(semester_name="Summer 2024").exists())

    def test_post_update_existing_semester(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.post(
            reverse("semester-editor", args=["Fall 2023"]),
            data={
                "semester_name": "Fall 2023",
                "start_date": "2023-08-20",
                "end_date": "2023-12-20",
            },
        )
        self.assertRedirects(response, reverse("semester-creator"))
        semester = Semester.objects.get(semester_name="Fall 2023")
        self.assertEqual(semester.start_date.strftime("%Y-%m-%d"), "2023-08-20")
        self.assertEqual(semester.end_date.strftime("%Y-%m-%d"), "2023-12-20")

    def test_post_create_existing_semester(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.post(
            reverse("semester-creator"),
            data={
                "semester_name": "Fall 2023",
                "start_date": "2023-08-15",
                "end_date": "2023-12-15",
                "isCreator": "True",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Semester Already Exist")

    def test_delete_existing_semester(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.post(
            reverse("semester-editor", args=["Fall 2023"]),
            data={"_method": "DELETE"},
        )
        self.assertRedirects(response, reverse("semester-creator"))
        self.assertFalse(Semester.objects.filter(semester_name="Fall 2023").exists())

    def test_delete_nonexistent_semester(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.post(
            reverse("semester-editor", args=["Nonexistent Semester"]),
            data={"_method": "DELETE"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Semester 'Nonexistent Semester' does not exist.", response.context["error"])

    def test_post_redirect_for_non_admin(self):
        self.client.login(username="nonadmin", password="nonadminpass")
        response = self.client.post(
            reverse("semester-creator"),
            data={
                "semester_name": "Test Semester",
                "start_date": "2024-06-01",
                "end_date": "2024-08-01",
            },
        )
        self.assertRedirects(response, reverse("home"))