from django.test import TestCase
from datetime import date
from ta_scheduler.models import Course, CourseSection, LabSection, User, Semester, TACourseAssignment
from core.local_data_classes import CourseFormData, CourseOverview
from core.course_controller.CourseController import CourseController


class CourseControllerTestBase(TestCase):
    def setUp(self):
        self.semester = Semester.objects.create(
            semester_name="Fall 2024", start_date=date(2024, 9, 1), end_date=date(2024, 12, 15)
        )
        self.course_list = [
            ("Test1", "Soft Eng"),
            ("Test2", "Soft Dev"),
            ("Other3", "Comp Arch"),
        ]
        self.add_test_courses()

    def add_test_courses(self):
        user_count = 0
        for code, name in self.course_list:
            course = Course.objects.create(course_code=code, course_name=name, semester=self.semester)
            instructor = User.objects.create_user(
                username=f"user_{user_count}",
                password="password",
                role="Instructor",
                first_name=f"First_{user_count}",
                last_name=f"Last_{user_count}",
            )
            user_count += 1
            CourseSection.objects.create(
                course=course,
                course_section_number=1,
                instructor=instructor,
                start_time="09:00",
                end_time="10:30",
                days="Mon, Wed",
            )
            ta = User.objects.create_user(
                username=f"user_{user_count}",
                password="password",
                role="TA",
                first_name=f"First_{user_count}",
                last_name=f"Last_{user_count}",
            )
            user_count += 1
            TACourseAssignment.objects.create(course=course, grader_status=False, ta=ta)
            LabSection.objects.create(
                course=course, lab_section_number=1, start_time="13:00", end_time="15:00"
            )


# Testing save courses
class TestSaveCourse(CourseControllerTestBase):
    def test_save_new_course(self):
        ta_list = User.objects.filter(role="TA")
        course_ta_list = ta_list[0].username + "," + ta_list[0].username
        course_data = CourseFormData(course_code="NewCourse", course_name="AI and ML", semester=self.semester.semester_name, ta_username_list=course_ta_list)
        CourseController.save_course(course_data)
        self.assertTrue(Course.objects.filter(course_code="NewCourse").exists())
        course = Course.objects.get(course_code="NewCourse")
        self.assertTrue(TACourseAssignment.objects.filter(course=course).exists())
        self.assertEqual(len(TACourseAssignment.objects.filter(course=course)), 2)

    def test_duplicate_course_code_same_semester_fails(self):
        course_data = CourseFormData(course_code="Test1", course_name="Duplicate Course", semester=self.semester, ta_username_list="")
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data)

    def test_empty_course_code_fails(self):
        course_data = CourseFormData(course_code="", course_name="AI and ML", semester=self.semester, ta_username_list="")
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data)

    def test_course_with_no_semester_fails(self):
        course_data = CourseFormData(course_code="NoSemester", course_name="No Semester", semester="", ta_username_list="")
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data)

    def test_modify_existing_course(self):
        course = Course.objects.first()
        course_data = CourseFormData(course_code=course.course_code, course_name="Updated Course", semester=self.semester, ta_username_list="")
        CourseController.save_course(course_data, course_code=course.course_code, semester_name=course.semester)
        self.assertEqual(Course.objects.get(id=course.id).course_name, "Updated Course")

    def test_modify_course_code(self):
        course = Course.objects.first()
        course_data = CourseFormData(course_code="11111", course_name="Updated Course", semester=self.semester, ta_username_list="")
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data, course_code=course.course_code, semester_name=course.semester)

    def test_modify_course_without_changes(self):
        course = Course.objects.first()
        course_data = CourseFormData(course_code=course.course_code, course_name=course.course_name, semester=course.semester, ta_username_list="")
        CourseController.save_course(course_data, course_code=course.course_code, semester_name=course.semester)
        self.assertTrue(Course.objects.get(
            id=course.id,
            course_code=course.course_code,
            course_name=course.course_name,
            semester=course.semester
        ), "Modified course even when passed same data")

    def test_modify_nonexistent_course_fails(self):
        course_data = CourseFormData(course_code="InvalidCode", course_name="Invalid Course", semester=self.semester, ta_username_list="")
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data, course_code=999)

    def test_save_course_duplicate_code_in_differentSemester(self):
        new_semester = Semester.objects.create(
            semester_name="Spring 2025", start_date=date(2025, 1, 1), end_date=date(2025, 5, 15)
        )
        course_data = CourseFormData(course_code="Test1", course_name="Same Code Different Semester", semester=new_semester.semester_name, ta_username_list="")
        CourseController.save_course(course_data)
        self.assertTrue(Course.objects.filter(course_code="Test1", semester=new_semester).exists())

    def test_save_course_modify_semester_into_identical_course(self):
        course = Course.objects.first()
        new_semester = Semester.objects.create(
            semester_name="Spring 2025", start_date=date(2025, 1, 1), end_date=date(2025, 5, 15)
        )
        Course.objects.create(course_name="new test", course_code=course.course_code, semester=new_semester)
        course_data = CourseFormData(course_code=course.course_code, course_name=course.course_name, semester=new_semester.semester_name, ta_username_list="")
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data, course.course_code, course.semester.semester_name)
        self.assertTrue(Course.objects.filter(course_code=course.course_code, semester=course.semester).exists())


# Testing get courses
class TestGetCourse(CourseControllerTestBase):
    def test_get_valid_course_details(self):
        course = Course.objects.first()
        result = CourseController.get_course(course.course_code, course.semester.semester_name)
        self.assertIsInstance(result, CourseOverview)
        self.assertEqual(result.code, course.course_code)
        self.assertEqual(result.name, course.course_name)
        ta_list = TACourseAssignment.objects.filter(course=course)
        self.assertEqual(len(result.ta_list), len(ta_list))

    def test_get_course_lab_sections(self):
        course = Course.objects.first()
        result = CourseController.get_course(course.course_code, course.semester.semester_name)
        lab_sections = LabSection.objects.filter(course=course)
        self.assertEqual(len(result.lab_sections), lab_sections.count())

    def test_get_course_sections(self):
        course = Course.objects.first()
        result = CourseController.get_course(course.course_code, course.semester.semester_name)
        course_sections = CourseSection.objects.filter(course=course)

        self.assertEqual(len(result.course_sections), course_sections.count())
        for section_ref, section in zip(result.course_sections, course_sections):
            self.assertEqual(section_ref.section_number, str(section.course_section_number))
            self.assertEqual(section_ref.instructor.name, f"{section.instructor.first_name} {section.instructor.last_name}")

    def test_get_course_without_sections(self):
        new_course = Course.objects.create(course_code="EmptyCourse", course_name="No Sections", semester=self.semester)
        result = CourseController.get_course(new_course.course_code, new_course.semester.semester_name)
        self.assertEqual(len(result.course_sections), 0)
        self.assertEqual(len(result.lab_sections), 0)

    def test_invalid_course_id_fails(self):
        course = Course.objects.first()
        with self.assertRaises(ValueError):
            CourseController.get_course("FAKE CODE", course.semester.semester_name)


# Testing search courses
class TestSearchCourses(CourseControllerTestBase):
    def test_search_all_courses(self):
        result = CourseController.search_courses("")
        self.assertEqual(len(result), Course.objects.count())

    def test_search_partial_name(self):
        result = CourseController.search_courses("Soft")
        self.assertTrue(all("Soft" in course.course_name for course in result))

    def test_no_matching_courses(self):
        result = CourseController.search_courses("NonExistent")
        self.assertEqual(len(result), 0)

    def test_search_by_semester(self):
        result = CourseController.search_courses("Soft", semester_name="Fall 2024")
        self.assertTrue(all("Soft" in course.course_name for course in result))

    def test_search_courses_in_specific_semester(self):
        result = CourseController.search_courses(course_search="Test", semester_name="Fall 2024")
        self.assertEqual(len(result), 2)

    def test_search_case_insensitive(self):
        result = CourseController.search_courses("soft eng")
        self.assertTrue(any(course.course_name.lower() == "soft eng" for course in result))


# Testing course deletion
class TestDeleteCourse(CourseControllerTestBase):
    def test_delete_valid_course(self):
        course = Course.objects.first()
        CourseController.delete_course(course.course_code, course.semester.semester_name)
        self.assertFalse(Course.objects.filter(id=course.id).exists())

    def test_delete_invalid_course_id_fails(self):
        course = Course.objects.first()
        with self.assertRaises(ValueError):
            CourseController.delete_course(999, course.semester.semester_name)

    def test_cascade_deletion(self):
        course = Course.objects.first()
        CourseController.delete_course(course.course_code, course.semester.semester_name)
        self.assertFalse(CourseSection.objects.filter(course=course).exists())
        self.assertFalse(LabSection.objects.filter(course=course).exists())
        self.assertFalse(TACourseAssignment.objects.filter(course=course).exists())




