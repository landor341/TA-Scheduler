from django.test import TestCase
from ta_scheduler.models import Course, User, TACourseAssignment, LabSection, TALabAssignment, Semester, CourseSection
from datetime import date
from core.local_data_classes import CourseFormData, CourseOverview
from core.course_controller.CourseController import CourseController


# Helper function to generate test data
def setup_database(course_list, semester_name="Fall 2024"):
    """
        Generate test courses with ta's,
        course assignments, and lab assignments
    """
    semester = Semester.objects.create(
        semester_name=semester_name, start_date=date(2024, 9, 1), end_date=date(2024, 12, 15)
    )
    course_count = 0
    user_count = 0

    for (code, name) in course_list:
        course = Course.objects.create(course_code=code, course_name=name, semester=semester)
        course_count += 1

        for i in range(course_count):
            instructor = User.objects.create_user(
                username=f"user_{user_count}",
                password="password",
                role="Instructor",
                first_name=f"First_{user_count}",
                last_name=f"Last_{user_count}"
            )
            user_count += 1

            section = CourseSection.objects.create(
                course=course,
                course_section_number=i,
                instructor=instructor,
                start_time="09:00",
                end_time="10:30",
                days="Mon, Wed"
            )

            ta = User.objects.create_user(
                username=f"user_{user_count}",
                password="password",
                role="TA",
                first_name=f"First_{user_count}",
                last_name=f"Last_{user_count}"
            )
            user_count += 1

            TACourseAssignment.objects.create(course=course, grader_status=False, ta=ta)

            lab_section = LabSection.objects.create(
                course=course, lab_section_number=i, start_time="13:00", end_time="15:00"
            )

            if i % 2 == 1:
                TALabAssignment.objects.create(lab_section=lab_section, ta=ta)


# Test cases for save_course
class TestSaveCourses(TestCase):
    def setUp(self):
        self.course_list = [
            ("Test1", "Soft Eng"),
            ("Test2", "Soft Dev"),
            ("Other3", "Comp Arch")
        ]
        setup_database(self.course_list)
        self.semester = Semester.objects.get(semester_name="Fall 2024")

    def test_saveNewCourse_succeeds(self):
        course_data = CourseFormData(course_code="NewCourse", course_name="AI and ML", semester=self.semester)
        result = CourseController.save_course(course_data)
        self.assertIsNotNone(result)
        self.assertTrue(Course.objects.filter(course_code="NewCourse").exists())

    def test_duplicateCourseCodeInSameSemesterFails(self):
        course_data = CourseFormData(course_code="Test1", course_name="Duplicate Course", semester=self.semester)
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data)

    def test_saveNewCourse_emptyCourseCodeFails(self):
        course_data = CourseFormData(course_code=None, course_name="AI and ML", semester=self.semester)
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data)

    def test_courseWithNoSemesterFails(self):
        course_data = CourseFormData(course_code="NoSemester", course_name="No Semester", semester=None)
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data)

    def test_modifyExistingCourse(self):
        course = Course.objects.first()
        course_data = CourseFormData(course_code=course.course_code, course_name="Updated Course", semester=self.semester)
        result = CourseController.save_course(course_data, course_id=course.id)
        self.assertEqual(result, str(course.id))
        self.assertEqual(Course.objects.get(id=course.id).course_name, "Updated Course")

    def test_modifyCourse_withoutChanges(self):
        course = Course.objects.first()
        course_data = CourseFormData(course_code=course.course_code, course_name=course.course_name, semester=course.semester)
        result = CourseController.save_course(course_data, course_id=course.id)
        self.assertEqual(result, str(course.id))

    def test_modifyNonexistentCourseFails(self):
        course_data = CourseFormData(course_code="InvalidCode", course_name="Invalid Course", semester=self.semester)
        with self.assertRaises(ValueError):
            CourseController.save_course(course_data, course_id=999)

    def test_saveCourse_duplicateCodeInDifferentSemester(self):
        new_semester = Semester.objects.create(
            semester_name="Spring 2025", start_date=date(2025, 1, 1), end_date=date(2025, 5, 15)
        )
        course_data = CourseFormData(course_code="Test1", course_name="Same Code Different Semester", semester=new_semester)
        result = CourseController.save_course(course_data)
        self.assertIsNotNone(result)
        self.assertTrue(Course.objects.filter(course_code="Test1", semester=new_semester).exists())


# Test cases for get_course
class TestGetCourses(TestCase):
    def setUp(self):
        self.course_list = [
            ("Test1", "Soft Eng"),
            ("Test2", "Soft Dev"),
            ("Other3", "Comp Arch")
        ]
        setup_database(self.course_list)
        self.semester = Semester.objects.get(semester_name="Fall 2024")

    def test_getValidCourseDetails(self):
        course = Course.objects.first()
        result = CourseController.get_course(course.id)
        self.assertIsInstance(result, CourseOverview)
        self.assertEqual(result.code, course.course_code)
        self.assertEqual(result.name, course.course_name)

    def test_getValidCourseLabSections(self):
        course = Course.objects.first()
        result = CourseController.get_course(course.id)
        lab_sections = LabSection.objects.filter(course=course)

        self.assertEqual(len(result.lab_sections), lab_sections.count())
        for lab_ref, lab in zip(result.lab_sections, lab_sections):
            self.assertEqual(lab_ref.section_number, str(lab.lab_section_number))
            if lab.get_ta():
                self.assertEqual(lab_ref.instructor.name, f"{lab.get_ta().first_name} {lab.get_ta().last_name}")
            else:
                self.assertIsNone(lab_ref.instructor)

    def test_getValidCourseSections(self):
        course = Course.objects.first()
        result = CourseController.get_course(course.id)
        course_sections = CourseSection.objects.filter(course=course)

        self.assertEqual(len(result.course_sections), course_sections.count())
        for section_ref, section in zip(result.course_sections, course_sections):
            self.assertEqual(section_ref.section_number, str(section.course_section_number))
            self.assertEqual(section_ref.instructor.name, f"{section.instructor.first_name} {section.instructor.last_name}")

    def test_getCourse_withoutSections(self):
        new_course = Course.objects.create(course_code="EmptyCourse", course_name="No Sections", semester=self.semester)
        result = CourseController.get_course(new_course.id)
        self.assertEqual(len(result.course_sections), 0)
        self.assertEqual(len(result.lab_sections), 0)


    def test_getInvalidCourseFails(self):
        with self.assertRaises(ValueError):
            CourseController.get_course(course_id=999)


# Test cases for search_courses
class TestSearchCourses(TestCase):
    def setUp(self):
        self.course_list = [
            ("Test1", "Soft Eng"),
            ("Test2", "Soft Dev"),
            ("Other3", "Comp Arch")
        ]
        setup_database(self.course_list)

    def test_searchEmptyParameter(self):
        result = CourseController.search_courses("")
        self.assertEqual(len(result), Course.objects.count())

    def test_searchPartialCourses(self):
        result = CourseController.search_courses("Soft")
        self.assertTrue(all("Soft" in course.course_name for course in result))

    def test_noMatchingSearch(self):
        result = CourseController.search_courses("NonExistent")
        self.assertEqual(len(result), 0)

    def test_searchBySemester(self):
        result = CourseController.search_courses("Soft", semester_name="Fall 2024")
        self.assertTrue(all("Soft" in course.course_name for course in result))

    def test_searchCoursesInSpecificSemester(self):
        result = CourseController.search_courses(course_search="Test", semester_name="Fall 2024")
        self.assertEqual(len(result), 2)

    def test_searchCaseInsensitive(self):
        result = CourseController.search_courses("soft eng")
        self.assertTrue(any(course.course_name.lower() == "soft eng" for course in result))



# Test cases for course deletion
class TestDeleteCourse(TestCase):
    def setUp(self):
        self.course_list = [
            ("Test1", "Soft Eng"),
            ("Test2", "Soft Dev"),
            ("Other3", "Comp Arch")
        ]
        setup_database(self.course_list)

    def test_deleteValidCourse(self):
        course = Course.objects.first()
        CourseController.delete_course(course.id)
        self.assertFalse(Course.objects.filter(id=course.id).exists())

    def test_deleteInvalidCourseFails(self):
        with self.assertRaises(ValueError):
            CourseController.delete_course(course_id=999)

    def test_cascadeDeletion(self):
        course = Course.objects.first()
        CourseController.delete_course(course.id)
        self.assertFalse(CourseSection.objects.filter(course=course).exists())
        self.assertFalse(LabSection.objects.filter(course=course).exists())



