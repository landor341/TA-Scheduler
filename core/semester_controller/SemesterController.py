from datetime import datetime
from typing import List

from django.db import models
from ta_scheduler.models import Semester
class SemesterController:
    @staticmethod
    def save_semester(
        semester_name: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> None:
        """
        Preconditions:
            - `semester_name`, `start_date`, and `end_date` are valid and non-empty strings.

        Postconditions:
            - Inserts or updates a semester record in the `Semester` table.

        Side-effects:
            - Saves a new semester or updates an existing one.

        Parameters:
            - semester_name (str | None): Unique name for the semester.
            - start_date (str | None): Start date of the semester in YYYY-MM-DD format.
            - end_date (str | None): End date of the semester in YYYY-MM-DD format.
        """
        if not semester_name:
            raise ValueError("semester_name cannot be None")
        if not start_date or not end_date:
            raise ValueError("start_date and end_date cannot be None")
        if Semester.objects.filter(semester_name=semester_name).exists():
            semester = Semester.objects.get(semester_name=semester_name)
        else:
            semester = Semester(semester_name=semester_name)
        if SemesterController._not_valid_date(start_date, end_date):
            raise ValueError("start_date cannot be before end_date")
        semester.start_date = start_date
        semester.end_date = end_date
        semester.save()
    @staticmethod
    def _not_valid_date(start_date, end_date) -> bool:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("start_date and end_date cannot be None")
        if start_date > end_date:
            return True
        return False

    @staticmethod
    def get_semester(
        semester_name: str | None = None
    ) -> Semester:
        """
        Preconditions:
            - `semester_name` exists in the database.

        Postconditions:
            - Returns the semester object with the specified name.

        Parameters:
            - semester_name (str | None): The name of the semester to retrieve.

        Returns:
            - Semester: The matching semester object.
         """
        try:
            return Semester.objects.get(semester_name=semester_name)
        except Semester.DoesNotExist:
            raise ValueError(f"Semester '{semester_name}' does not exist.")

    @staticmethod
    def semester_exists(semester_name: str | None = None) -> bool:
        """
        Checks if a semester exists.

        Parameters:
            - semester_name (str | None): The name of the semester to check.

        Returns:
            - bool: `True` if the semester exists, otherwise `False`.
        """
        if Semester.objects.filter(semester_name=semester_name).exists():
            return True
        return False
    @staticmethod
    def search_semester(semester_search: str) -> List[Semester]:
        """
        Parameters:
            - semester_search (str): The search query to match semester names.

        Returns:
            - List[str]: A list of semester names matching the search query.
        """
        results = Semester.objects.filter(semester_name__icontains=semester_search)
        return [semester.semester_name for semester in results]

    @staticmethod
    def delete_semester(semester_name: str | None = None) -> None:
        """
        Preconditions:
            - The semester exists in the database.

        Postconditions:
            - The semester is removed from the database.

        Parameters:
            - semester_name (str | None): The name of the semester to delete.
        """
        try:
            semester = Semester.objects.get(semester_name=semester_name)
            semester.delete()
        except Semester.DoesNotExist:
            raise ValueError(f"Semester '{semester_name}' does not exist.")

    @staticmethod
    def list_semester() -> List[str]:
        """
        Retrieves all semesters sorted by start date.

        Returns:
            - List[str]: A list of all semester names sorted by their start date.
        """
        return Semester.objects.all().order_by("start_date")
