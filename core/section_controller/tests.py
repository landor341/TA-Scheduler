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
        SectionController.save_lab_section(self.lab_data, self.semester.semester_name, None)
        lab_section = LabSection.objects.get(course=self.course, lab_section_number=1)

        self.assertIsNotNone(lab_section)
        self.assertEqual(lab_section.days, "Monday, Wednesday")
        self.assertEqual(lab_section.start_time, time(10, 0))
        self.assertEqual(lab_section.end_time, time(11, 0))

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
        SectionController.save_lab_section(updated_lab_data, self.semester.semester_name, lab_section.lab_section_number)

        lab_section.refresh_from_db()
        self.assertEqual(lab_section.days, "Monday, Wednesday")
        self.assertEqual(lab_section.start_time, time(10, 0))
        self.assertEqual(lab_section.end_time, time(11, 0))

    def test_create_lab_section_with_duplicate_number(self):
        LabSection.objects.create(
            course=self.course,
            lab_section_number=1,
            days="Monday, Wednesday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        with self.assertRaises(ValueError):
            SectionController.save_lab_section(self.lab_data, self.semester.semester_name, None)


class TestDeleteLabSection(SectionControllerTestBase):
    def test_delete_lab_section(self):
        lab_section = LabSection.objects.create(
            course=self.course, lab_section_number=1, days="Monday", start_time=time(9, 0), end_time=time(10, 0)
        )

        SectionController.delete_lab_section(self.course.course_code, self.semester.semester_name,
                                             lab_section.lab_section_number)

        self.assertFalse(LabSection.objects.filter(lab_section_number=lab_section.lab_section_number).exists())

    def test_delete_nonexistent_lab_section_raises_error(self):
        with self.assertRaises(ValueError):
            SectionController.delete_lab_section(self.course.course_code, self.semester.semester_name, 999)


class TestSaveCourseSection(SectionControllerTestBase):
    def test_save_new_course_section(self):
        SectionController.save_course_section(self.course_section_data, self.semester.semester_name, None)
        course_section = CourseSection.objects.get(course=self.course, course_section_number=101)

        self.assertIsNotNone(course_section)
        self.assertEqual(course_section.days, "Tuesday, Thursday")
        self.assertEqual(course_section.start_time, time(9, 0))
        self.assertEqual(course_section.end_time, time(10, 30))
        self.assertEqual(course_section.instructor, self.instructor)

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
        SectionController.save_course_section(updated_course_section_data, self.semester.semester_name, course_section.course_section_number)

        course_section.refresh_from_db()
        self.assertEqual(course_section.days, "Tuesday, Thursday")
        self.assertEqual(course_section.start_time, time(9, 0))
        self.assertEqual(course_section.end_time, time(10, 30))

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
            SectionController.save_course_section(self.course_section_data, self.semester.semester_name, None)


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

        SectionController.delete_course_section(self.course.course_code, self.semester.semester_name, course_section.course_section_number)

        self.assertFalse(CourseSection.objects.filter(course_section_number=course_section.course_section_number).exists())

    def test_delete_nonexistent_course_section_raises_error(self):
        with self.assertRaises(ValueError):
            SectionController.delete_course_section(self.course.course_code, self.semester.semester_name, 999)


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

        # Verify result is of type CourseSectionFormData
        self.assertIsInstance(result, CourseSectionFormData)
        self.assertEqual(result.course.course_code, self.course.course_code)
        self.assertEqual(result.section_number, course_section.course_section_number)
        self.assertEqual(result.days, course_section.days)
        self.assertEqual(result.start_time, course_section.start_time)
        self.assertEqual(result.end_time, course_section.end_time)
        self.assertEqual(result.instructor.username, self.instructor.username)

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

        # Verify result is of type LabSectionFormData
        self.assertIsInstance(result, LabSectionFormData)
        self.assertEqual(result.course.course_code, self.course.course_code)
        self.assertEqual(result.section_number, lab_section.lab_section_number)
        self.assertEqual(result.days, lab_section.days)
        self.assertEqual(result.start_time, lab_section.start_time)
        self.assertEqual(result.end_time, lab_section.end_time)

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