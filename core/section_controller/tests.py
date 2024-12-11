from core.local_data_classes import LabSectionFormData, CourseSectionFormData
from ta_scheduler.models import Course, CourseSection, LabSection, User, Semester
from core.section_controller.SectionController import SectionController
from datetime import time
from django.test import TestCase


class SectionControllerTestBase(TestCase):
    def setUp(self):
        self.semester = Semester.objects.create(semester_name="Fall 2024", start_date="2024-09-01", end_date="2024-12-31")
        self.course = Course.objects.create(course_code="CS101", course_name="Intro to Programming", semester=self.semester)
        self.instructor = User.objects.create(username="instructor1", role="Instructor", email="instructor1@test.com")
        self.ta = User.objects.create(username="ta1", role="TA", email="ta1@test.com")

        # Lab section setup
        self.lab_data = LabSectionFormData(
            course=self.course,
            section_number=1,
            days="Monday, Wednesday",
            start_time=time(10, 0),
            end_time=time(11, 0),
            section_type="Lab",
        )

        # Course section setup
        self.course_section_data = CourseSectionFormData(
            course=self.course,
            instructor=self.instructor,
            section_number=101,
            days="Tuesday, Thursday",
            start_time=time(9, 0),
            end_time=time(10, 30),
            section_type="Course",
        )



class TestSaveLabSection(SectionControllerTestBase):
    def test_save_new_lab_section(self):
        result = SectionController.save_lab_section(self.lab_data, None)
        lab_section = LabSection.objects.get(course=self.course, lab_section_number=1)

        self.assertIsNotNone(lab_section)
        self.assertEqual(lab_section.days, "Monday, Wednesday")
        self.assertEqual(lab_section.start_time, time(10, 0))
        self.assertEqual(lab_section.end_time, time(11, 0))
        self.assertEqual(result, f"{self.course.id}:{lab_section.lab_section_number}")

    def test_update_existing_lab_section(self):
        lab_section = LabSection.objects.create(
            course=self.course, lab_section_number=1, days="Monday", start_time=time(9, 0), end_time=time(10, 0)
        )
        updated_lab_data = LabSectionFormData(
            course=self.course,
            section_number=1,
            days="Monday, Wednesday",
            start_time=time(10, 0),
            end_time=time(11, 0),
            section_type="Lab",
        )
        result = SectionController.save_lab_section(updated_lab_data, lab_section.id)

        lab_section.refresh_from_db()
        self.assertEqual(lab_section.days, "Monday, Wednesday")
        self.assertEqual(lab_section.start_time, time(10, 0))
        self.assertEqual(lab_section.end_time, time(11, 0))
        self.assertEqual(result, f"{self.course.id}:{lab_section.lab_section_number}")

    def test_create_lab_section_with_duplicate_number(self):
        LabSection.objects.create(
            course=self.course,
            lab_section_number=1,
            days="Monday, Wednesday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        with self.assertRaises(ValueError):
            SectionController.save_lab_section(self.lab_data, None)


class TestDeleteLabSection(SectionControllerTestBase):
    def test_delete_lab_section(self):
        lab_section = LabSection.objects.create(
            course=self.course, lab_section_number=1, days="Monday", start_time=time(9, 0), end_time=time(10, 0)
        )
        SectionController.delete_lab_section(lab_section.id)
        self.assertFalse(LabSection.objects.filter(id=lab_section.id).exists())

    def test_delete_nonexistent_lab_section_raises_error(self):
        with self.assertRaises(ValueError):
            SectionController.delete_lab_section(999)


class TestSaveCourseSection(SectionControllerTestBase):
    def test_save_new_course_section(self):
        result = SectionController.save_course_section(self.course_section_data, None)
        course_section = CourseSection.objects.get(course=self.course, course_section_number=101)

        self.assertIsNotNone(course_section)
        self.assertEqual(course_section.days, "Tuesday, Thursday")
        self.assertEqual(course_section.start_time, time(9, 0))
        self.assertEqual(course_section.end_time, time(10, 30))
        self.assertEqual(course_section.instructor, self.instructor)
        self.assertEqual(result, f"{self.course.id}:{course_section.course_section_number}")

    def test_update_existing_course_section(self):
        course_section = CourseSection.objects.create(
            course=self.course,
            instructor=self.instructor,
            course_section_number=101,
            days="Monday",
            start_time=time(8, 0),
            end_time=time(9, 0),
        )
        updated_course_section_data = CourseSectionFormData(
            course=self.course,
            instructor=self.instructor,
            section_number=101,
            days="Tuesday, Thursday",
            start_time=time(9, 0),
            end_time=time(10, 30),
            section_type="Course",
        )
        result = SectionController.save_course_section(updated_course_section_data, course_section.id)

        course_section.refresh_from_db()
        self.assertEqual(course_section.days, "Tuesday, Thursday")
        self.assertEqual(course_section.start_time, time(9, 0))
        self.assertEqual(course_section.end_time, time(10, 30))
        self.assertEqual(result, f"{self.course.id}:{course_section.course_section_number}")

    def test_create_course_section_with_duplicate_number(self):
        CourseSection.objects.create(
            course=self.course,
            instructor=self.instructor,
            course_section_number=101,
            days="Tuesday, Thursday",
            start_time=time(9, 0),
            end_time=time(10, 30),
        )
        with self.assertRaises(ValueError):
            SectionController.save_course_section(self.course_section_data, None)


class TestDeleteCourseSection(SectionControllerTestBase):
    def test_delete_course_section(self):
        course_section = CourseSection.objects.create(
            course=self.course,
            instructor=self.instructor,
            course_section_number=101,
            days="Monday",
            start_time=time(8, 0),
            end_time=time(9, 0),
        )
        SectionController.delete_course_section(course_section.id)
        self.assertFalse(CourseSection.objects.filter(id=course_section.id).exists())

    def test_delete_nonexistent_course_section_raises_error(self):
        with self.assertRaises(ValueError):
            SectionController.delete_course_section(999)


class TestGetCourseSection(SectionControllerTestBase):
    def test_get_valid_course_section(self):
        course_section = CourseSection.objects.create(
            course=self.course,
            instructor=self.instructor,
            course_section_number=101,
            days="Tuesday, Thursday",
            start_time=time(9, 0),
            end_time=time(10, 30),
        )
        result = SectionController.get_course_section(
            course_code=self.course.course_code,
            semester_name=self.semester.semester_name,
            course_section_number=101,
        )
        self.assertEqual(result, course_section)

    def test_get_nonexistent_course_section(self):
        with self.assertRaises(ValueError):
            SectionController.get_course_section(
                course_code="INVALID_CODE",
                semester_name=self.semester.semester_name,
                course_section_number=999,
            )

    def test_get_course_section_with_invalid_semester(self):
        new_semester = Semester.objects.create(
            semester_name="Spring 2025",
            start_date="2025-01-01",
            end_date="2025-05-31",
        )
        with self.assertRaises(ValueError):
            SectionController.get_course_section(
                course_code=self.course.course_code,
                semester_name=new_semester.semester_name,
                course_section_number=101,
            )


class TestGetLabSection(SectionControllerTestBase):
    def test_get_valid_lab_section(self):
        lab_section = LabSection.objects.create(
            course=self.course,
            lab_section_number=1,
            days="Monday, Wednesday",
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        result = SectionController.get_lab_section(
            course_code=self.course.course_code,
            semester_name=self.semester.semester_name,
            lab_section_number=1,
        )
        self.assertEqual(result, lab_section)

    def test_get_nonexistent_lab_section(self):
        with self.assertRaises(ValueError):
            SectionController.get_lab_section(
                course_code="INVALID_CODE",
                semester_name=self.semester.semester_name,
                lab_section_number=999,
            )

    def test_get_lab_section_with_invalid_semester(self):
        new_semester = Semester.objects.create(
            semester_name="Spring 2025",
            start_date="2025-01-01",
            end_date="2025-05-31",
        )
        with self.assertRaises(ValueError):
            SectionController.get_lab_section(
                course_code=self.course.course_code,
                semester_name=new_semester.semester_name,
                lab_section_number=1,
            )