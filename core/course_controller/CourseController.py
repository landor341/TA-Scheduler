from typing import List

from core.local_data_classes import CourseFormData, CourseOverview, CourseRef
from ta_scheduler.models import Course, CourseSection, LabSection, Semester,User


class CourseController:
    @staticmethod
    def save_course(course_data: CourseFormData, course_code: str | None = None) -> str:
        """
        Pre-conditions: course_data contains valid information for creating a course.
            if course_code is provided, it matches an existing course in the Courses table.
        Post-conditions: Returns the id of the modified Courses table object. throws an
            IllegalValue exception if course_code is invalid or the courseData was invalid.
        Side-effects: Inserts or updates a record in the Courses table with the given
            course_data
        Returns: the id of the modified Courses table object. throws an
            IllegalValue exception if course_code is invalid or the courseData was invalid.
        """
        pass

    @staticmethod
    def get_course(course_code: str) -> CourseOverview:
        """
        Pre-conditions: course_code provided is a valid course_code
        Post-conditions: Returns an object containing course, sections, and assignment
            information for object in the Courses table with the given course_code.
        Side-effects: N/A
        """
        pass

    @staticmethod
    def search_courses(course_search: str, semester_name: str | None = None) -> List[CourseRef]:
        """
        Pre-conditions: Semester is a valid value if given
        Post-conditions: Returns a list of courses whose title or code
            matches the course_search_str.
        Side-effects: N/A
        """
        pass
    
    @staticmethod
    def delete_course(course_code: str) -> None:
        """
        Pre-conditions: Course id is a valid value matching a record in courses.
        Post-conditions: Removes a record from Course with matching course_id.
        Side-effects: removes matching record from Course table and any objects with foreign key references to it.
        """
        pass

    @staticmethod
    def save_lab_sections(course_data: CourseFormData) -> str:
        """
        Helper method for save course to handle adding new lab sections.

        Pre-conditions: course_data is valid in the CourseFormData provided (course_code is provided).
        Post-conditions: Adds record(s) to the LabSection table with the relation to the course_code provided in CourseFormData.
        Side-effects: new record(s) added to the LabSection table.
        Returns: list of id(s) of the new lab section objects added to the table or an IllegalValueException if CourseFormData
            has no course code.
        """
        pass

    @staticmethod
    def save_course_sections(course_data: CourseFormData) -> str:
        """
        Helper method for save course to handle adding new course sections.

        Pre-conditions: course_data is valid in the CourseFormData provided (course_code is provided).
        Post-conditions: Adds record(s) to the CourseSection table with the relation to the course_code provided in CourseFormData.
        Side-effects: new record(s) added to the CourseSection table.
        Returns: list of id(s) of the new course section objects added to the table or an IllegalValueException if CourseFormData
            doesn't have a course_code.
        """
        pass