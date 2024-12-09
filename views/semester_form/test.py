from django.test import TestCase
from ta_scheduler.models import Semester
from core.semester_controller.SemesterController import SemesterController


class TestSaveSemester(TestCase):
    def test_save_valid_semester(self):
        SemesterController.save_semester(
            semester_name="Fall 2023", start_date="2023-08-01", end_date="2023-12-31"
        )
        semester = Semester.objects.get(semester_name="Fall 2023")
        self.assertEqual(semester.start_date.strftime("%Y-%m-%d"), "2023-08-01")
        self.assertEqual(semester.end_date.strftime("%Y-%m-%d"), "2023-12-31")

    def test_save_invalid_date(self):
        with self.assertRaises(ValueError) as context:
            SemesterController.save_semester(
                semester_name="Fall 2023", start_date="2023-12-31", end_date="2023-08-01"
            )
        self.assertEqual(str(context.exception), "start_date cannot be before end_date")

    def test_save_with_missing_name(self):
        with self.assertRaises(ValueError) as context:
            SemesterController.save_semester(
                semester_name=None, start_date="2023-08-01", end_date="2023-12-31"
            )
        self.assertEqual(str(context.exception), "semester_name cannot be None")


class TestGetSemester(TestCase):
    def setUp(self):
        Semester.objects.create(
            semester_name="Fall 2023", start_date="2023-08-01", end_date="2023-12-31"
        )

    def test_get_existing_semester(self):
        semester = SemesterController.get_semester("Fall 2023")
        self.assertEqual(semester.semester_name, "Fall 2023")

    def test_get_nonexistent_semester(self):
        with self.assertRaises(ValueError) as context:
            SemesterController.get_semester("Nonexistent Semester")
        self.assertEqual(str(context.exception), "Semester 'Nonexistent Semester' does not exist.")


class TestDeleteSemester(TestCase):
    def setUp(self):
        Semester.objects.create(
            semester_name="Fall 2023", start_date="2023-08-01", end_date="2023-12-31"
        )

    def test_delete_existing_semester(self):
        SemesterController.delete_semester("Fall 2023")
        self.assertFalse(Semester.objects.filter(semester_name="Fall 2023").exists())

    def test_delete_nonexistent_semester(self):
        with self.assertRaises(ValueError) as context:
            SemesterController.delete_semester("Nonexistent Semester")
        self.assertEqual(str(context.exception), "Semester 'Nonexistent Semester' does not exist.")


class TestSearchSemester(TestCase):
    def setUp(self):
        Semester.objects.create(
            semester_name="Fall 2023", start_date="2023-08-01", end_date="2023-12-31"
        )
        Semester.objects.create(
            semester_name="Spring 2023", start_date="2023-01-01", end_date="2023-05-31"
        )

    def test_search_existing_semester(self):
        results = SemesterController.search_semester("2023")
        self.assertIn("Fall 2023", results)
        self.assertIn("Spring 2023", results)

    def test_search_no_results(self):
        results = SemesterController.search_semester("2024")
        self.assertEqual(results, [])


class TestListSemester(TestCase):
    def setUp(self):
        Semester.objects.create(
            semester_name="Fall 2023", start_date="2023-08-01", end_date="2023-12-31"
        )
        Semester.objects.create(
            semester_name="Spring 2023", start_date="2023-01-01", end_date="2023-05-31"
        )

    def test_list_semesters_order(self):
        results = SemesterController.list_semester()
        self.assertEqual([semester.semester_name for semester in results], ["Spring 2023", "Fall 2023"])