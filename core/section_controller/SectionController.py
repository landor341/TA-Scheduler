from core.local_data_classes import LabFormData, CourseSectionFormData
from ta_scheduler.models import CourseSection, LabSection

class SectionController:
    @staticmethod
    def save_lab_section(lab_section_data: LabFormData, lab_section_id: int | None) -> str:
        """
        Pre-conditions: lab section data is valid in the form provided, if the lab_section_id is provided, a lab section with that id exists.
        Post-conditions: Adds/updates a record to the LabSection table with the relation to the course provided in LabFormData.
        Side-effects: new record added to the LabSection table or an existing record is updated if lab_section_id is provided.
        Returns: course id of the course that the lab section was added for and the lab section number.
        """
        if not lab_section_id:
            # Check for duplicate lab section number within the same course
            if LabSection.objects.filter(
                course=lab_section_data.course,
                lab_section_number=lab_section_data.lab_section_number,
            ).exists():
                raise ValueError("A lab section with this section number already exists for the course.")

        # If lab_section_id is provided, update the existing LabSection
        if lab_section_id:
            try:
                lab_section = LabSection.objects.get(id=lab_section_id)
                lab_section.course = lab_section_data.course
                lab_section.lab_section_number = lab_section_data.lab_section_number
                lab_section.days = lab_section_data.days
                lab_section.start_time = lab_section_data.start_time
                lab_section.end_time = lab_section_data.end_time
                lab_section.save()
            except LabSection.DoesNotExist:
                raise ValueError(f"Lab section with id {lab_section_id} does not exist.")
        else:
            # Create a new LabSection
            lab_section = LabSection.objects.create(
                course=lab_section_data.course,
                lab_section_number=lab_section_data.lab_section_number,
                days=lab_section_data.days,
                start_time=lab_section_data.start_time,
                end_time=lab_section_data.end_time,
            )

        return f"{lab_section.course.id}:{lab_section.lab_section_number}"

    @staticmethod
    def delete_lab_section(lab_section_id: int) -> None:
        """
        Pre-conditions: lab_section_id is a valid value matching a record in the LabSection table.
        Post-conditions: Removes a record from the LabSection table with the matching lab_section_id or raises a ValueError if no such lab section exists.
        Side-effects: removes matching record from the LabSection table and any objects with foreign key references to it.
        """
        try:
            lab_section = LabSection.objects.get(id=lab_section_id)
            lab_section.delete()
        except LabSection.DoesNotExist:
            raise ValueError(f"Lab section with id {lab_section_id} does not exist.")

    @staticmethod
    def save_course_section(course_section_data: CourseSectionFormData, course_section_id: int | None) -> str:
        """
        Pre-conditions: course_section_data is valid in the CourseSectionFormData provided, if course section id is provided, a course section with matching id exists.
        Post-conditions: Adds/updates a record to/in the CourseSection table with the relation to the course provided in CourseFormData.
        Side-effects: new record added to the CourseSection table or an existing record is updated if course_section_id is provided.
        Returns: course id of the course that the lab section was added for and the course section number.
        """
        if not course_section_id:
            # Check for duplicate course section number within the same course
            if CourseSection.objects.filter(
                course=course_section_data.course,
                course_section_number=course_section_data.course_section_number,
            ).exists():
                raise ValueError("A course section with this section number already exists for the course.")

        # If course_section_id is provided, update the existing CourseSection
        if course_section_id:
            try:
                course_section = CourseSection.objects.get(id=course_section_id)
                course_section.course = course_section_data.course
                course_section.instructor = course_section_data.instructor
                course_section.course_section_number = course_section_data.course_section_number
                course_section.days = course_section_data.days
                course_section.start_time = course_section_data.start_time
                course_section.end_time = course_section_data.end_time
                course_section.save()
            except CourseSection.DoesNotExist:
                raise ValueError(f"Course section with id {course_section_id} does not exist.")
        else:
            # Create a new CourseSection
            course_section = CourseSection.objects.create(
                course=course_section_data.course,
                instructor=course_section_data.instructor,
                course_section_number=course_section_data.course_section_number,
                days=course_section_data.days,
                start_time=course_section_data.start_time,
                end_time=course_section_data.end_time,
            )

        return f"{course_section.course.id}:{course_section.course_section_number}"

    @staticmethod
    def delete_course_section(course_section_id: int) -> None:
        """
        Pre-conditions: course_section_id is a valid value matching a record in the CourseSection table.
        Post-conditions: Removes a record from the CourseSection table with the matching course_section_id or raises a ValueError if no such lab section exists.
        Side-effects: removes a matching record from the CourseSection table and any objects with foreign key references to it.
        """
        try:
            course_section = CourseSection.objects.get(id=course_section_id)
            course_section.delete()
        except CourseSection.DoesNotExist:
            raise ValueError(f"Course section with id {course_section_id} does not exist.")