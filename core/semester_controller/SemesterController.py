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
        Pre-conditions: semester_name, start_date, and end_date are valid and non-empty.
        Post-conditions: Saves or updates a semester record.
        Side-effects: Inserts or updates a record in the Semesters table.
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
         Pre-conditions: semester_name corresponds to an existing semester.
         Post-conditions: Returns the semester with the specified name.
         Side-effects: N/A
         """
        try:
            return Semester.objects.get(semester_name=semester_name)
        except Semester.DoesNotExist:
            raise ValueError(f"Semester '{semester_name}' does not exist.")

    @staticmethod
    def semester_exists(semester_name: str | None = None) -> bool:
        if Semester.objects.filter(semester_name=semester_name).exists():
            return True
        return False
    @staticmethod
    def search_semester(semester_search: str) -> List[Semester]:
        """
        Pre-conditions: N/A
        Post-conditions: Returns a list of semester names matching the search string.
        Side-effects: N/A
        """
        results = Semester.objects.filter(semester_name__icontains=semester_search)
        return [semester.semester_name for semester in results]

    @staticmethod
    def delete_semester(semester_name: str | None = None) -> None:
        """
        Pre-conditions: A semester with the given name exists.
        Post-conditions: Removes the semester with the given name.
        Side-effects: Removes the matching record from the Semester table.
        """
        try:
            semester = Semester.objects.get(semester_name=semester_name)
            semester.delete()
        except Semester.DoesNotExist:
            raise ValueError(f"Semester '{semester_name}' does not exist.")

    @staticmethod
    def list_semester() -> List[str]:
        return Semester.objects.all().order_by("start_date")
