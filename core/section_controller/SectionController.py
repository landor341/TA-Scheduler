from core.local_data_classes import LabSectionFormData, CourseSectionFormData, CourseRef, UserRef
from ta_scheduler.models import CourseSection, LabSection, Course, Semester, User, TALabAssignment


class SectionController:
    @staticmethod
    def save_lab_section(lab_section_data: LabSectionFormData, semester_name: str, lab_section_number: int | None) -> None:
        """
        Pre-conditions: lab section data is valid in the form provided, if the lab_section_id is provided, a lab section with that id exists.
        Post-conditions: Adds/updates a record to the LabSection table with the relation to the course provided in LabFormData.
        Side-effects: new record added to the LabSection table or an existing record is updated if lab_section_id is provided.
        Returns: course id of the course that the lab section was added for and the lab section number.
        """
        course = Course.objects.get(
            course_code=lab_section_data.course.course_code,
            semester__semester_name=semester_name
        )

        # Initialize lab_section to None
        lab_section = None

        # If updating an existing lab section, fetch it
        if lab_section_number is not None:
            try:
                lab_section = LabSection.objects.get(
                    course=course,
                    lab_section_number=lab_section_number
                )
            except LabSection.DoesNotExist:
                raise ValueError(f"Lab section {lab_section_number} does not exist.")

        # Ensure no duplicates excluding the current section's ID
        if LabSection.objects.filter(
                course=course,
                lab_section_number=lab_section_data.section_number
        ).exclude(pk=lab_section.pk if lab_section else None).exists():
            raise ValueError("A lab section with this section number already exists for the course and semester.")

        # Update or create the LabSection
        if lab_section:
            # Update existing section
            lab_section.lab_section_number = lab_section_data.section_number
            lab_section.days = lab_section_data.days
            lab_section.start_time = lab_section_data.start_time
            lab_section.end_time = lab_section_data.end_time
            lab_section.save()
        else:
            # Create new section
            LabSection.objects.create(
                course=course,
                lab_section_number=lab_section_data.section_number,
                days=lab_section_data.days,
                start_time=lab_section_data.start_time,
                end_time=lab_section_data.end_time,
            )


    @staticmethod
    def delete_lab_section(course_code: str, semester_name: str, lab_section_number: int) -> None:
        """
        Pre-conditions: lab_section_id is a valid value matching a record in the LabSection table.
        Post-conditions: Removes a record from the LabSection table with the matching lab_section_id or raises a ValueError if no such lab section exists.
        Side-effects: removes matching record from the LabSection table and any objects with foreign key references to it.
        """
        try:
            # Fetch the related course and semester
            semester = Semester.objects.get(semester_name=semester_name)
            course = Course.objects.get(course_code=course_code, semester=semester)

            # Find and delete the lab section
            lab_section = LabSection.objects.get(course=course, lab_section_number=lab_section_number)
            lab_section.delete()
        except Semester.DoesNotExist:
            raise ValueError(f"Semester '{semester_name}' does not exist.")
        except Course.DoesNotExist:
            raise ValueError(f"Course '{course_code}' does not exist in semester '{semester_name}'.")
        except LabSection.DoesNotExist:
            raise ValueError(
                f"Lab section {lab_section_number} does not exist for course '{course_code}' in semester '{semester_name}'.")

    @staticmethod
    def save_course_section(course_section_data: CourseSectionFormData, semester_name: str, course_section_number: int | None) -> None:
        """
        Pre-conditions: course_section_data is valid in the CourseSectionFormData provided, if course section id is provided, a course section with matching id exists.
        Post-conditions: Adds/updates a record to/in the CourseSection table with the relation to the course provided in CourseFormData.
        Side-effects: new record added to the CourseSection table or an existing record is updated if course_section_id is provided.
        Returns: course id of the course that the lab section was added for and the course section number.
        """
        course = Course.objects.get(
            course_code=course_section_data.course.course_code,
            semester__semester_name=semester_name
        )
        instructor = User.objects.get(username=course_section_data.instructor.username)

        # Initialize course_section to None
        course_section = None

        # If updating an existing course section, fetch it
        if course_section_number is not None:
            try:
                course_section = CourseSection.objects.get(
                    course=course,
                    course_section_number=course_section_number
                )
            except CourseSection.DoesNotExist:
                raise ValueError(f"Course section {course_section_number} does not exist.")

        # Ensure no duplicates excluding the current section's ID
        if CourseSection.objects.filter(
                course=course,
                course_section_number=course_section_data.section_number
        ).exclude(pk=course_section.pk if course_section else None).exists():
            raise ValueError("A course section with this section number already exists for the course and semester.")

        # Update or create the CourseSection
        if course_section:
            # Update existing section
            course_section.course_section_number = course_section_data.section_number
            course_section.instructor = instructor
            course_section.days = course_section_data.days
            course_section.start_time = course_section_data.start_time
            course_section.end_time = course_section_data.end_time
            course_section.save()
        else:
            # Create new section
            CourseSection.objects.create(
                course=course,
                instructor=instructor,
                course_section_number=course_section_data.section_number,
                days=course_section_data.days,
                start_time=course_section_data.start_time,
                end_time=course_section_data.end_time,
            )

    @staticmethod
    def delete_course_section(course_code: str, semester_name: str, course_section_number: int) -> None:
        """
        Pre-conditions: course_section_id is a valid value matching a record in the CourseSection table.
        Post-conditions: Removes a record from the CourseSection table with the matching course_section_id or raises a ValueError if no such lab section exists.
        Side-effects: removes a matching record from the CourseSection table and any objects with foreign key references to it.
        """
        try:
            # Fetch the related course and semester
            semester = Semester.objects.get(semester_name=semester_name)
            course = Course.objects.get(course_code=course_code, semester=semester)

            # Find and delete the course section
            course_section = CourseSection.objects.get(course=course, course_section_number=course_section_number)
            course_section.delete()
        except Semester.DoesNotExist:
            raise ValueError(f"Semester '{semester_name}' does not exist.")
        except Course.DoesNotExist:
            raise ValueError(f"Course '{course_code}' does not exist in semester '{semester_name}'.")
        except CourseSection.DoesNotExist:
            raise ValueError(
                f"Course section {course_section_number} does not exist for course '{course_code}' in semester '{semester_name}'.")

    @staticmethod
    def get_course_section(course_code: str, semester_name: str, course_section_number: int) -> CourseSectionFormData:
        """
        Pre-conditions: course_code is not null and matches an existing course code in the Course record, semester is not null
        and matches an existing record in the semester record, and course_section_number is a valid course section number that exists
        in the CourseSection model.
        Post-conditions: Returns a course section object with the info that matches the search parameters or a value error if no such
        objects exist.
        Side-effects: none.
        """
        try:
            # Fetch semester and course
            semester = Semester.objects.get(semester_name=semester_name)
            course = Course.objects.get(course_code=course_code, semester=semester)

            # Fetch course section
            course_section = CourseSection.objects.get(
                course=course,
                course_section_number=course_section_number
            )

            # Convert to CourseSectionFormData
            instructor = (
                UserRef(name=course_section.instructor.get_full_name(), username=course_section.instructor.username)
                if course_section.instructor else None
            )

            return CourseSectionFormData(
                course=CourseRef(course_code=course.course_code, course_name=course.course_name),
                section_number=course_section.course_section_number,
                days=course_section.days,
                start_time=course_section.start_time,
                end_time=course_section.end_time,
                instructor=instructor,
                section_type="Course",
            )

        except Semester.DoesNotExist:
            raise ValueError(f"Semester '{semester_name}' does not exist.")
        except Course.DoesNotExist:
            raise ValueError(f"Course '{course_code}' does not exist in semester '{semester_name}'.")
        except CourseSection.DoesNotExist:
            raise ValueError(
                f"Course section {course_section_number} does not exist for course '{course_code}' in semester '{semester_name}'."
            )

    @staticmethod
    def get_lab_section(course_code: str, semester_name: str, lab_section_number: int) -> LabSectionFormData:
        """
        Pre-conditions: course_code is not null and matches an existing course code in the Course record, semester is not null
        and matches an existing record in the semester record, and lab_section_number is a valid lab section number that exists
        in the LabSection model.
        Post-conditions: Returns a lab section object with the info that matches the search parameters or a value error if no such
        objects exist.
        Side-effects: none.
        """
        try:
            # Fetch semester and course
            semester = Semester.objects.get(semester_name=semester_name)
            course = Course.objects.get(course_code=course_code, semester=semester)

            # Fetch lab section
            lab_section = LabSection.objects.get(
                course=course,
                lab_section_number=lab_section_number
            )

            return LabSectionFormData(
                course=CourseRef(course_code=course.course_code, course_name=course.course_name),
                section_number=lab_section.lab_section_number,
                days=lab_section.days,
                start_time=lab_section.start_time,
                end_time=lab_section.end_time,
                section_type="Lab",
            )

        except Semester.DoesNotExist:
            raise ValueError(f"Semester '{semester_name}' does not exist.")
        except Course.DoesNotExist:
            raise ValueError(f"Course '{course_code}' does not exist in semester '{semester_name}'.")
        except LabSection.DoesNotExist:
            raise ValueError(
                f"Lab section {lab_section_number} does not exist for course '{course_code}' in semester '{semester_name}'."
            )


    @staticmethod
    def assign_instructor_or_ta(section_type: str, section_number: int, course_code: str, semester_name: str,
                                instructor_ref: UserRef) -> None:
        """
        Preconditions:
        - 'instructor_ref' must be a valid `UserRef` object containing an existing user's username.
        - 'section_type' must be either "Course" or "Lab".
        - 'section_number' must correspond to an existing CourseSection or LabSection in the context of the provided
            course code and semester name.
        - The user in 'instructor_ref' must have a role appropriate for the section type:
            - "Instructor" role for "Course" section.
            - "TA" role for "Lab" section.

        Postconditions:
        - If 'section_type' is "Course", the specified user is assigned as the instructor for the course section.
        - If 'section_type' is "Lab", the specified user is assigned as the TA for the lab section via a TALabAssignment entry.
        - Raises a ValueError if the user, course, or section does not exist, or if invalid data is provided.

        Side-effects:
        - For "Course" sections:
            - Updates the `instructor` field of the relevant CourseSection and saves the changes.
        - For "Lab" sections:
            - Creates or updates a TALabAssignment entry with the TA assigned to the lab section.

        Parameters:
        - section_type: A string indicating the type of section ("Course" or "Lab").
        - section_number: An integer representing the section number.
        - course_code: A string representing the course code.
        - semester_name: A string representing the semester name.
        - instructor_ref: A `UserRef` object containing the `username` of the user to be assigned.

        Returns:
        - None.
        """
        try:
            # Extract username and fetch the user
            if not instructor_ref or not instructor_ref.username:
                raise ValueError("Invalid instructor reference provided.")

            user = User.objects.get(username=instructor_ref.username)

            # Fetch semester and course
            semester = Semester.objects.get(semester_name=semester_name)
            course = Course.objects.get(course_code=course_code, semester=semester)

            if section_type == "Course":
                if user.role != "Instructor":
                    raise ValueError("User must have the 'Instructor' role for Course sections.")
                # Update the instructor for the course section
                section = CourseSection.objects.get(course=course, course_section_number=section_number)
                section.instructor = user
                section.save()

            elif section_type == "Lab":
                if user.role != "TA":
                    raise ValueError("User must have the 'TA' role for Lab sections.")
                # Update the TA for the lab section
                lab_section = LabSection.objects.get(course=course, lab_section_number=section_number)
                TALabAssignment.objects.update_or_create(
                    lab_section=lab_section,
                    defaults={"ta": user}
                )
            else:
                raise ValueError("Invalid section type. Must be 'Course' or 'Lab'.")

        except User.DoesNotExist:
            raise ValueError(f"User '{instructor_ref.username}' does not exist.")
        except CourseSection.DoesNotExist:
            raise ValueError(f"Course section {section_number} does not exist.")
        except LabSection.DoesNotExist:
            raise ValueError(f"Lab section {section_number} does not exist.")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")