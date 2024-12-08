from django.test import TestCase
from ta_scheduler.models import Semester
from core.semester_controller.SemesterController import SemesterController
from datetime import datetime


class TestSemesterController(TestCase):
    def setUp(self):
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

    def test_save_semester_create_new(self):
        SemesterController.save_semester(
            semester_name="Summer 2024",
            start_date="2024-06-01",
            end_date="2024-08-01",
        )
        self.assertTrue(Semester.objects.filter(semester_name="Summer 2024").exists())

    def test_save_semester_update_existing(self):
        SemesterController.save_semester(
            semester_name="Fall 2023",
            start_date="2023-08-20",
            end_date="2023-12-20",
        )
        semester = Semester.objects.get(semester_name="Fall 2023")
        self.assertEqual(semester.start_date.strftime('%Y-%m-%d'), "2023-08-20")
        self.assertEqual(semester.end_date.strftime('%Y-%m-%d'), "2023-12-20")

    def test_save_semester_invalid_date(self):
        with self.assertRaises(ValueError) as context:
            SemesterController.save_semester(
                semester_name="Invalid Semester",
                start_date="2024-12-01",
                end_date="2024-01-01",
            )
        self.assertEqual(str(context.exception), "start_date cannot be before end_date")

    def test_save_semester_invalid_format(self):
        with self.assertRaises(ValueError) as context:
            SemesterController.save_semester(
                semester_name="Invalid Format",
                start_date="01-01-2024",
                end_date="12-31-2024",
            )
        self.assertEqual(str(context.exception), "start_date and end_date cannot be None")

    def test_get_semester(self):
        semester = SemesterController.get_semester("Fall 2023")
        self.assertEqual(semester.semester_name, "Fall 2023")
        self.assertEqual(semester.start_date.strftime('%Y-%m-%d'), "2023-08-15")

    def test_get_nonexistent_semester(self):
        with self.assertRaises(ValueError) as context:
            SemesterController.get_semester("Nonexistent Semester")
        self.assertEqual(str(context.exception), "Semester 'Nonexistent Semester' does not exist.")

    def test_semester_exists(self):
        self.assertTrue(SemesterController.semester_exists("Fall 2023"))
        self.assertFalse(SemesterController.semester_exists("Nonexistent Semester"))

    def test_search_semester(self):
        results = SemesterController.search_semester("Fall")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "Fall 2023")

    def test_delete_semester(self):
        SemesterController.delete_semester("Fall 2023")
        self.assertFalse(Semester.objects.filter(semester_name="Fall 2023").exists())

    def test_delete_nonexistent_semester(self):
        with self.assertRaises(ValueError) as context:
            SemesterController.delete_semester("Nonexistent Semester")
        self.assertEqual(str(context.exception), "Semester 'Nonexistent Semester' does not exist.")

    def test_list_semester(self):
        semesters = SemesterController.list_semester()
        self.assertEqual(len(semesters), 2)
        self.assertEqual(semesters[0].semester_name, "Fall 2023")
        self.assertEqual(semesters[1].semester_name, "Spring 2024")