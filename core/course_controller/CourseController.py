from typing import List

from core.local_data_classes import CourseFormData, CourseOverview, CourseRef, UserRef, CourseSectionRef, LabSectionRef
from django.db import models
from ta_scheduler.models import Course, CourseSection, LabSection, Semester, TACourseAssignment, User


class CourseController:
    @staticmethod
    def save_course(
            course_data: CourseFormData,
            course_code: str | None = None,
            semester_name: str | None = None
    ) -> None:
        """
        Pre-conditions: course_data contains valid information for creating a course.
            course_code is an existing course_code or None.
            semester_name is the name of an existing semester or none
        Post-conditions: throws an IllegalValue exception if course_code is not a valid course_code
            or the course_code is None and there is already a course with the given
            course_data.course_code and course_data.semester.
        Side-effects: Inserts or updates a record in the Courses table with the given
            course_data
        """
        if not course_data.course_code:
            raise ValueError("Course code cannot be empty.")

        if course_code and course_code != course_data.course_code:
            raise ValueError("Cannot change a courses course code")

        if not course_code and not Semester.objects.filter(semester_name=course_data.semester).exists():
            raise ValueError("Valid semester is required for creating a new course.")

        # Check for duplicate course if creating a new course or modifying semester
        if (
            (
                course_code is None
                or (semester_name != course_data.semester)
            ) and Course.objects.filter(
                course_code=course_data.course_code,
                semester__semester_name=course_data.semester
            ).exists()
        ):
            raise ValueError("A course with the same code already exists in the selected semester.")

        # Handle course update
        if course_code:
            try:
                course = Course.objects.get(course_code=course_code, semester__semester_name=semester_name)
            except Course.DoesNotExist:
                raise ValueError("Course code and semester does not match any existing course.")
        else:
            course = Course()
            course.course_code = course_data.course_code

        try:
            semester = Semester.objects.get(semester_name=course_data.semester)
        except Semester.DoesNotExist:
            raise ValueError("Given semester does not exist")

        try:
            for user in course_data.ta_username_list.split(","):
                if user:
                    ta = User.objects.get(username=user)
                    if not TACourseAssignment.objects.filter(course=course, ta=ta).exists():
                        TACourseAssignment.objects.create(
                            course=course,
                            ta=User.objects.get(username=user),
                            grader_status=False
                        )
            for a in TACourseAssignment.objects.filter(course=course):
                found = False
                for user in course_data.ta_username_list.split(","):
                    if user:
                        if a.ta.username == user:
                            found = True
                if not found:
                    a.delete()

        except User.DoesNotExist:
            raise ValueError("One of the users in the TA list does not exist")

        course.course_name = course_data.course_name
        course.semester = semester
        course.save()

    @staticmethod
    def get_course(course_code: str, semester_name: str) -> CourseOverview:
        """
        Pre-conditions: There is a course that has the given course code and who's semester
            has the name the name semester_name
        Post-conditions: Returns an object containing course, sections, and assignment
            information for object in the Courses table with the given course_code and semester_name
        Side-effects: N/A
        """
        try:
            course = Course.objects.get(course_code=course_code, semester__semester_name=semester_name)
        except Course.DoesNotExist:
            raise ValueError("Course with the given code and semester name does not exist.")

        course_sections = []
        lab_sections = []
        ta_list = []

        for ta_assignment in TACourseAssignment.objects.filter(course=course):
            ta = UserRef(
                name=f"{ta_assignment.ta.first_name} {ta_assignment.ta.last_name}",
                username=ta_assignment.ta.username
            )
            ta_list.append(ta)

        # Retrieve course sections
        for section in CourseSection.objects.filter(course=course):
            section_instructor = UserRef(
                name=f"{section.instructor.first_name} {section.instructor.last_name}",
                username=section.instructor.username,
            )
            course_sections.append(CourseSectionRef(
                section_number=str(section.course_section_number),
                instructor=section_instructor,
            ))

        # Retrieve lab sections
        for lab in LabSection.objects.filter(course=course):
            ta = lab.get_ta()
            ta_ref = UserRef(
                name=f"{ta.first_name} {ta.last_name}",
                username=ta.username,
            ) if ta else None
            lab_sections.append(LabSectionRef(
                section_number=str(lab.lab_section_number),
                instructor=ta_ref,
            ))

        return CourseOverview(
            code=course.course_code,
            name=course.course_name,
            semester=course.semester.semester_name,
            course_sections=course_sections,
            ta_list=ta_list,
            lab_sections=lab_sections,
        )

    @staticmethod
    def search_courses(course_search: str, semester_name: str | None = None) -> List[CourseRef]:
        """
        Pre-conditions: Semester is a valid value if given
        Post-conditions: Returns a list of courses whose title or code
            matches the course_search_str.
        Side-effects: N/A
        """
        results = Course.objects.all()

        if semester_name:
            results = results.filter(semester__semester_name=semester_name)

        if course_search:
            results = results.filter(
                models.Q(course_name__icontains=course_search) |
                models.Q(course_code__icontains=course_search)
            )

        return [
            CourseRef(course_code=course.course_code, course_name=course.course_name)
            for course in results
        ]
    
    @staticmethod
    def delete_course(course_code: str, semester_name: str) -> None:
        """
        Pre-conditions: A course with the given course code and whose semester name is semester_name exists
        Post-conditions: Removes a record from Course with matching course_code and semester with name semester_name.
        Side-effects: removes matching record from Course table and any objects with foreign key references to it.
        """
        try:
            course = Course.objects.get(course_code=course_code, semester__semester_name=semester_name)
            course.delete()
        except Course.DoesNotExist:
            raise ValueError("Course with the given code does not exist.")

