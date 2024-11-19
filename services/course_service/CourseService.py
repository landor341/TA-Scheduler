

class CourseService:
    @staticmethod
    def saveCourse(course_data, id=None):
        """
        Pre-conditions: courseData contains valid information for creating a course.
            if id is provided, it matches an existing course in the Courses table
        Post-conditions: Returns the value of the modified Courses table object. throws an
            IllegalValue exception if id is invalid or the courseData was invalid.
        Side-effects: Inserts or updates a record in the Courses table with the given
            course_data
        """
        pass

    @staticmethod
    def getCourse(id):
        """
        Pre-conditions: id provided is a valid course_id
        Post-conditions: Returns an object containing course, sections, and assignment
            information for object in the Courses table with the given id.
        Side-effects: N/A
        """
        pass


    @staticmethod
    def searchCourses(course_search_str, semester_id=None):
        """
        Pre-conditions: Semester is a valid value if given
        Post-conditions: Returns an array of courses whose title or code
            matches the course_search_str.
        Side-effects: N/A
        """
        pass
