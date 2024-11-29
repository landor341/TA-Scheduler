from typing import List

from core.local_data_classes import CourseFormData, CourseOverview, CourseRef, UserRef, CourseSectionRef, LabSectionRef
from django.db import models
from ta_scheduler.models import Course, CourseSection, LabSection, User


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
        if not course_data.course_code:
            raise ValueError("Course code cannot be empty.")

        # Handle course update
        if course_code:
            try:
                course = Course.objects.get(course_code=course_code)
            except Course.DoesNotExist:
                raise ValueError("Course code does not match any existing course.")
            course.course_name = course_data.course_name or course.course_name
            course.semester = course_data.semester or course.semester
            course.save()
        else:
            # Handle new course creation
            if Course.objects.filter(course_code=course_data.course_code).exists():
                raise ValueError("Course code already exists.")
            if not course_data.semester:
                raise ValueError("Semester is required for creating a new course.")

            course = Course.objects.create(
                course_code=course_data.course_code,
                course_name=course_data.course_name,
                semester=course_data.semester,
            )

        # Save lab sections
        if course_data.lab_sections_codes:
            CourseController.save_lab_sections(course_data)

        # Save course sections
        if course_data.course_sections_codes:
            CourseController.save_course_sections(course_data)

        return str(course.id)

    @staticmethod
    def get_course(course_code: str) -> CourseOverview:
        """
        Pre-conditions: course_code provided is a valid course_code
        Post-conditions: Returns an object containing course, sections, and assignment
            information for object in the Courses table with the given course_code.
        Side-effects: N/A
        """
        try:
            course = Course.objects.get(course_code=course_code)
        except Course.DoesNotExist:
            raise ValueError("Course with the given code does not exist.")

        default_section = CourseSection.objects.filter(course=course).first()
        instructor = UserRef(
            name=f"{default_section.instructor.first_name} {default_section.instructor.last_name}",
            username=default_section.instructor.username,
        )
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
            instructor=instructor,
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
    def delete_course(course_code: str) -> None:
        """
        Pre-conditions: Course id is a valid value matching a record in courses.
        Post-conditions: Removes a record from Course with matching course_id.
        Side-effects: removes matching record from Course table and any objects with foreign key references to it.
        """
        try:
            course = Course.objects.get(course_code=course_code)
            course.delete()
        except Course.DoesNotExist:
            raise ValueError("Course with the given code does not exist.")

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
        if not course_data.course_code:
            raise ValueError("Course code is required for saving lab sections.")

        if not course_data.lab_sections_codes:
            # If no lab sections are provided, return early
            return "No lab sections to add."

        try:
            course = Course.objects.get(course_code=course_data.course_code)
        except Course.DoesNotExist:
            raise ValueError("Course with the given code does not exist.")

        existing_sections = LabSection.objects.filter(course=course).values_list('lab_section_number', flat=True)

        for section_number in course_data.lab_sections_codes:
            if section_number in existing_sections:
                raise ValueError(f"Duplicate lab section number: {section_number}")
            LabSection.objects.create(
                course=course,
                lab_section_number=section_number,
                start_time="00:00",
                end_time="00:00",
            )

        return f"Lab sections added to course {course_data.course_code}"

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
        if not course_data.course_code:
            raise ValueError("Course code is required for saving course sections.")

        if not course_data.instructor:
            raise ValueError("Instructor is required for saving course sections.")

        if not course_data.course_sections_codes:
            # If no course sections are provided, return early
            return "No course sections to add."

        try:
            course = Course.objects.get(course_code=course_data.course_code)
        except Course.DoesNotExist:
            raise ValueError("Course with the given code does not exist.")

        try:
            instructor = User.objects.get(username=course_data.instructor.username, role="Instructor")
        except User.DoesNotExist:
            raise ValueError("The provided instructor does not exist or is not an Instructor.")

        existing_sections = CourseSection.objects.filter(course=course).values_list('course_section_number', flat=True)

        for section_number in course_data.course_sections_codes:
            if section_number in existing_sections:
                raise ValueError(f"Duplicate course section number: {section_number}")
            CourseSection.objects.create(
                course=course,
                course_section_number=section_number,
                instructor=instructor,
                start_time="00:00",
                end_time="00:00",
            )

        return f"Course sections added to course {course_data.course_code}"