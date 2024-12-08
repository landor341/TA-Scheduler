from re import search

from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from core.semester_controller.SemesterController import SemesterController
from core.user_controller.UserController import UserController


class SemesterFormView(View):
    def get(self, request, semester_name: str | None = None):
        """
        Preconditions:
        - `semester_name` is an optional parameter that can be a string or `None`.
        - `request` is a valid HttpRequest object.

        Postconditions:
        - Renders the semester form for an admin or the specified semester.
        - If the role is Admin and semester_name is not provided, a blank form is rendered.
        - Redirects to home if access is unauthorized.

        Side-effects:
        - None.

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - semester_name: An optional string representing the name of the semester in the Semester table.

        Returns:
        - An HttpResponse object rendering the 'semester_form/semester_form.html' template with appropriate semester data.
        - Redirects to home if the user does not have the necessary permissions.
        """
        if request.user.role != "Admin":
            return redirect("home")
        if semester_name is None:
            return render(request, 'semester_form/semester_form.html', {
                "creator": True,
                "existSemester": SemesterController.list_semester(),
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                "data": {"semester_name": "", "start_date": "", "end_date": ""},
                "isAdmin": True
            })
        try:
            semester = SemesterController.get_semester(semester_name)
        except ValueError:
            return redirect("home")
        return render(request, 'semester_form/semester_form.html', {
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            "data": {"semester_name": semester.semester_name, "start_date": semester.start_date.strftime('%Y-%m-%d'), "end_date": semester.end_date.strftime('%Y-%m-%d')},
            "isAdmin": True
        })
    def post(self, request, semester_name: str | None = None):
        """
        Preconditions:
        - `semester_name` is an optional parameter that can be a string or `None`.
        - `request` is a valid HttpRequest object, containing POST data with semester details.

        Postconditions:
        - Saves or updates the semester data based on the provided form data.
        - Redirects to the semester list or detail page after saving.

        Side-effects:
        - Modifies or creates semester data in the database.

        Parameters:
        - request: An HttpRequest object containing POST data with semester details.
        - semester_name: An optional string representing the name of the semester in the Semester table.

        Returns:
        - Redirects to the Create Semester page.
        """
        if request.user.role != "Admin":
            return redirect("home")
        if request.POST.get("_method") == "DELETE":
            return self.delete(request, semester_name)
        semester_data = {
            "semester_name": request.POST.get("semester_name"),
            "start_date": request.POST.get("start_date"),
            "end_date": request.POST.get("end_date"),
        }
        if SemesterController.semester_exists(semester_data.get("semester_name")) and request.POST.get("isCreator") == "True":
            return render(request, 'semester_form/semester_form.html', {
                "existSemester": SemesterController.list_semester(),
                "creator": True,
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                "data": {"semester_name": "", "start_date": "", "end_date": ""},
                "isAdmin": True,
                "error": "Semester Already Exist",
            })
        try:
            SemesterController.save_semester(
                semester_name = semester_data.get("semester_name"),
                start_date=semester_data.get("start_date"),
                end_date=semester_data.get("end_date"),
            )
        except ValueError as e:
            return render(request, 'semester_form/semester_form.html', {
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                "data": semester_data,
                "isAdmin": True,
                "error": str(e),
            })
        return redirect("semester-creator")

    def delete(self, request, semester_name: str):
        """
        Preconditions:
        - `semester_name` must be a non-empty string.
        - `request` is a valid HttpRequest object with an authenticated user who has Admin privileges.

        Postconditions:
        - Deletes the specified semester if the request is made by an admin.
        - Redirects to home after deletion.

        Side-effects:
        - Removes semester data from the database.

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - semester_name: A string representing the name of the semester in the Semester table to be deleted.

        Returns:
        - Redirects to home after deleting the semester if performed by an Admin.
        """
        try:
            SemesterController.delete_semester(semester_name)
        except ValueError as e:
            if semester_name is None:
                semester_name = 'NonExistentSemester'
            return render(request, 'semester_form/semester_form.html', {
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                "data": {"semester_name": semester_name, "start_date": "", "end_date": ""},
                "error": str(e),
                "isAdmin": True,
            })
        return redirect("semester-creator")