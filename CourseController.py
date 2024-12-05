from typing import List

from core.local_data_classes import CourseFormData, CourseOverview, CourseRef, UserRef, CourseSectionRef, LabSectionRef
from django.db import models
from ta_scheduler.models import Course, CourseSection, LabSection, Semester


class CourseController:
    @staticmethod
    def save_course(course_data: CourseFormData, course_id: int | None = None) -> str:
        """
        Pre-conditions: course_data contains valid information for creating a course.
            if course_id is provided, it matches an existing course in the Courses table.
        Post-conditions: Returns the id of the modified Courses table object. throws an
            IllegalValue exception if course_id is invalid or the courseData was invalid.
        Side-effects: Inserts or updates a record in the Courses table with the given
            course_data
        Returns: the id of the modified Courses table object. throws an
            IllegalValue exception if course_id is invalid or the courseData was invalid.
        """
        if not course_data.course_code:
            raise ValueError("Course code cannot be empty.")

        # Check for duplicate course_code within the same semester
        if course_data.semester:
            duplicate_course = Course.objects.filter(
                course_code=course_data.course_code,
                semester=course_data.semester,
            )
            # Exclude the current course being updated
            if course_id:
                duplicate_course = duplicate_course.exclude(id=course_id)
            if duplicate_course.exists():
                raise ValueError("A course with the same code already exists in the selected semester.")

        # Handle course update
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise ValueError("Course code does not match any existing course.")
            course.course_name = course_data.course_name or course.course_name
            course.semester = course_data.semester or course.semester
            course.save()
        else:
            # Handle new course creation
            if not course_data.semester:
                raise ValueError("Semester is required for creating a new course.")

            course = Course.objects.create(
                course_code=course_data.course_code,
                course_name=course_data.course_name,
                semester=course_data.semester,
            )

        return str(course.id)

    @staticmethod
    def get_course(course_id: int) -> CourseOverview:
        """
        Pre-conditions: course_id provided is a valid course id
        Post-conditions: Returns an object containing course, sections, and assignment
            information for object in the Courses table with the given course_code.
        Side-effects: N/A
        """
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise ValueError("Course with the given code does not exist.")

        course_sections = []
        lab_sections = []

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
            semester=course.semester,
            course_sections=course_sections,
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
    def delete_course(course_id: int) -> None:
        """
        Pre-conditions: Course id is a valid value matching a record in courses.
        Post-conditions: Removes a record from Course with matching course_id.
        Side-effects: removes matching record from Course table and any objects with foreign key references to it.
        """
        try:
            course = Course.objects.get(id=course_id)
            course.delete()
        except Course.DoesNotExist:
            raise ValueError("Course with the given code does not exist.")

    @staticmethod
    def validate_semester(semester_name: str) -> bool:
        """
        Validates whether a semester with the given name exists.

        Args:
            semester_name (str): The name of the semester to validate.

        Returns:
            bool: True if the semester exists, False otherwise.
        """
        try:
            # Query the database for the semester using the model
            return Semester.objects.filter(semester_name=semester_name).exists()
        except Exception as e:
            # Log error or handle it as needed (example: log to a monitoring system)
            print(f"Error validating semester: {e}")
            return False



