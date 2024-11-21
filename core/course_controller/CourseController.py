from typing import List

from core.local_data_classes import CourseFormData, CourseOverview, CourseRef


class CourseController:
    @staticmethod
    def save_course(course_data: CourseFormData, id: str | None = None) -> str:
        """
        Pre-conditions: course_data contains valid information for creating a course.
            if id is provided, it matches an existing course in the Courses table.
        Post-conditions: Returns the id of the modified Courses table object. throws an
            IllegalValue exception if id is invalid or the courseData was invalid.
        Side-effects: Inserts or updates a record in the Courses table with the given
            course_data
        """
        pass



    @staticmethod
    def get_course(course_id: str) -> CourseOverview:
        """
        Pre-conditions: id provided is a valid course_id
        Post-conditions: Returns an object containing course, sections, and assignment
            information for object in the Courses table with the given id.
        Side-effects: N/A
        """
        pass

    @staticmethod
    def search_courses(course_search: str, semester_id: int | None = None) -> List[CourseRef]:
        """
        Pre-conditions: Semester is a valid value if given
        Post-conditions: Returns a list of courses whose title or code
            matches the course_search_str.
        Side-effects: N/A
        """
        pass
    
    @staticmethod
    def delete_course(course_id: int) -> None:
        """
        Pre-conditions: Course id is a valid value matching a record in courses.
        Post-conditions: Removes a record from Course with matching course_id.
        Side-effects: Adds new record to Course table.
        """
        pass