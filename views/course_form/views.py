from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from core.semester_controller.SemesterController import SemesterController
from core.course_controller.CourseController import CourseController
from core.local_data_classes import CourseFormData
from ta_scheduler.models import User
import re


class CourseForm(View):
    def get(self, request, code: str | None = None, semester: str | None = None):
        """
        Preconditions:
        - `request` is a valid HttpRequest object representing a GET request.
        - `code` is an optional course code string; can be `None`.
        - `semester` is an optional semester string; can be `None`.

        Postconditions:
        - Renders the course creation or editing form.
        - Pre-fills the form with existing course data if `code` and `semester` are valid.
        - Redirects unauthorized users to the home page.

        Side-effects:
        - None.

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - code: An optional string representing the course code.
        - semester: An optional string representing the semester.

        Returns:
        - An HttpResponse rendering the 'course_form/course_form.html' template with the form data and additional context.
        - Redirects to home if the user does not have the necessary permissions.
        """
        if not self.__can_use_form(request.user, code, semester):
            return redirect(reverse("home"))

        course_form = CourseController.get_course(code, semester) if code else {}

        if code:
            ta_list = ""
            for ta in course_form.ta_list:
                ta_list += ta.username + ","

        return render(request, 'course_form/course_form.html', {
            "semester": SemesterController.list_semester(),
            "data": course_form,
            "isAdmin": request.user.role == "Admin",
            "isEditing": code is not None,
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            "preselected_users": ta_list if code else "",
            "user_search_role": "TA"
        })

    def post(self, request, code: str | None = None, semester: str | None = None):
        """
        Preconditions:
        - `request` is a valid HttpRequest object representing a POST request.
        - `code` is an optional course code string; can be `None`.
        - `semester` is an optional semester string; can be `None`.

        Postconditions:
        - Validates form inputs and saves new or updated course data to the database.
        - Deletes a course if the 'delete' action is specified.
        - Renders the course form with error messages if the form contains invalid data.
        - Redirects unauthorized users or after successful operations.

        Side-effects:
        - Modifies course data in the database (saving or deleting course records).

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - code: An optional string representing the course code.
        - semester: An optional string representing the semester.

        Returns:
        - An HttpResponse rendering the 'course_form/course_form.html' template with form errors and context if validation errors are present.
        - Redirects to the course page or home page after successful operations or unauthorized access.
        """
        if not self.__can_use_form(request.user, code, semester):
            return redirect(reverse("home"))

            # Handle delete action
        if request.POST.get('action') == 'delete':
            # Check if the user is an admin
            if request.user.role != "Admin":
                return redirect(reverse("home"))  # Redirect non-admins to home
            CourseController.delete_course(code, semester)
            return redirect(reverse("home"))

        #validation checks
        #gather input data
        course_code = request.POST.get('course_code', '').strip()
        course_name = request.POST.get('course_name', '').strip()
        selected_semester = request.POST.get('semester', '').strip()

        # Validation errors dictionary
        errors = {
            "course_code": "",
            "course_name": "",
            "semester": "",
        }
        #General errors for non-field-specific errors
        errors_list = []

        # Validation checks
        if not course_code:
            errors["course_code"] = "Field empty"
        elif not re.match(r'^[A-Za-z0-9]+$', course_code):
            errors["course_code"] = "Course code must be a valid alphanumeric value."

        if not course_name:
            errors["course_name"] = "Field empty"
        elif not re.match(r'^[A-Za-z0-9 ]+$', course_name):
            errors["course_name"] = "Course name must be a valid alphanumeric value."

        valid_semesters = [s.semester_name for s in SemesterController.list_semester()]

        if not selected_semester:
            errors["semester"] = "Field empty"
        elif selected_semester not in valid_semesters:
            errors["semester"] = "The selected semester doesn't exist."
        #General error
        if len(course_name) > 70:
            errors_list.append("Course name must be less than 70 characters.")

        # Check if there are any errors
        if any(errors.values()) or errors_list:
            ta_list = request.POST.get("selected-users")
            if not ta_list:
                ta_list = ""

            # Re-render the form with errors and previous inputs
            return render(request, 'course_form/course_form.html', {
                "semester": SemesterController.list_semester(),
                "data": {
                    "code": course_code,
                    "name": course_name,
                    "semester": selected_semester,
                },
                "errors": errors,  # Pass errors to the template
                "errors_list": errors_list, #Pass any general errors
                "isAdmin": request.user.role == "Admin",
                "isEditing": code is not None,
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                "preselected_users": ta_list,
                "user_search_role": "TA"
            })

        ta_list = request.POST.get("selected-users")
        if not ta_list:
            ta_list = ""

        #Save course function in dataclass
        form = CourseFormData(
            course_code=course_code,
            semester=selected_semester,
            course_name=course_name,
            ta_username_list=ta_list
        )
        #save func catching course duplication and redirect back to form
        try:
            CourseController.save_course(form, code, semester)
        except ValueError as e:
                errors_list.append(e)
                errors_list.append("Course already exists in the selected semester.")
                return render(request, 'course_form/course_form.html', { "semester": SemesterController.list_semester(),
                "data": {
                    "code": course_code,
                    "name": course_name,
                    "semester": selected_semester,
                },
                "errors": errors,  # Pass errors to the template
                "errors_list": errors_list, #Pass any general errors
                "isAdmin": request.user.role == "Admin",
                "isEditing": code is not None,
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                "preselected_users": ta_list,
                "user_search_role": "TA"
            })

        return redirect(f"/course/{form.course_code}/{form.semester}")


    def delete(self, request, code: str, semester: str):
        """
        Preconditions:
        - `request` is a valid HttpRequest object representing a DELETE request.
        - `code` and `semester` represent a valid course and semester.

        Postconditions:
        - Deletes the specified course and all its associated sections and assignments.
        - Redirects unauthorized users or after successful deletion.

        Side-effects:
        - Deletes course data from the database.

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - code: A string representing the course code.
        - semester: A string representing the semester.

        Returns:
        - Redirects to the home page after deletion or unauthorized access.
        """
        if not self.__can_use_form(request.user, code, semester):
            return redirect(reverse("home"))


        CourseController.delete_course(code, semester)

        #  Included so that tests fail instead of throwing errors
        return redirect(reverse("home"))


    def __can_use_form(self, user: User, code: str, semester: str):
        # Need to check permissions. Could refactor in future to be controller method
        if user.role != "Admin":
            if code is None:
                return False
            course_form = CourseController.get_course(code, semester)
            for section in course_form.course_sections:
                if section.instructor.username == user.username:
                    return True
            return False
        return True


