from django.test import TestCase
from ta_scheduler.models import Course, CourseSection, User, TACourseAssignment, LabSection, TALabAssignment


# TOOD: Write tests. You can use the below generator if it looks useful
def setupDatabase(course_list):
    """
        Generate test courses with sections, instructors, ta's,
        Course asignments, and lab assignments
    """
    course_count = 0
    user_count = 0

    for (code, name) in course_list:
        course = Course(course_code=code, course_name="name")
        course.save()
        course_count += 1

        for i in range(course_count):
            instructor = User(
                role="Instructor", first_name=user_count, last_name=user_count,
                password=user_count, username=user_count
            )
            instructor.save()
            user_count += 1

            section = CourseSection(
                course_id=course,
                course_section_number=i,
                instructor=instructor
            )
            section.save()

            ta = User(
                role="TA", first_name=user_count, last_name=user_count,
                password=user_count, username=user_count
            )
            ta.save()
            user_count += 1

            courseAssignment = TACourseAssignment(course=course, grader_status=False, ta=ta)
            courseAssignment.save()

            labSection = LabSection(course=course, lab_section_number=i)
            labSection.save()

            if i % 2 == 1:
                labAssignment = TALabAssignment(lab_section=labSection, ta=ta)
                labAssignment.save()


class TestSaveCourses(TestCase):
    course_list = [
        ("Test1", "Soft Eng"),
        ("Test2", "Soft Dev"),
        ("Other3", "Comp Arch")
    ]

    def setup(self):
        setupDatabase(self.course_list)

    def test_saveNewCourse(self):
        pass

    def test_modifyCourse(self):
        pass

    def test_badNewCourse(self):
        pass

    def test_badModifyCourse(self):
        pass



class TestGetCourses(TestCase):
    course_list = [
        ("Test1", "Soft Eng"),
        ("Test2", "Soft Dev"),
        ("Other3", "Comp Arch")
    ]

    def setup(self):
        setupDatabase(self.course_list)

    def test_getValidCourse(self):
        pass

    def test_getInvalidCourse(self):
        pass

    def test_getNoneCourse(self):
        pass

class TestSearchCourses(TestCase):
    course_list = [
        ("Test1", "Soft Eng"),
        ("Test2", "Soft Dev"),
        ("Other3", "Comp Arch")
    ]

    def setup(self):
        setupDatabase(self.course_list)

    def test_searchEmptyParameter(self):
        pass # TODO: Should get all courses

    def test_searchPartialCourses(self):
        pass

    def test_emptySearch(self):
        pass

    def test_specificSemester(self):
        pass
