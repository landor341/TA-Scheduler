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
        '''
        Preconditions: Admin user logged in.
        Postconditions: Renders a form for creating a course with sections.
            If the request URL contains a valid course ID then the form is
            preloaded with that courses current data
        Side-effects: N/A
        '''
        if not self.__can_use_form(request.user, code, semester):
            return redirect(reverse("home"))

        course_form = CourseController.get_course(code, semester) if code else {}
        return render(request, 'course_form/course_form.html', {
            "semester": SemesterController.list_semester(),
            "data": course_form,
            "isAdmin": request.user.role == "Admin",
            "isEditing": code is not None,
            'full_name': f"{request.user.first_name} {request.user.last_name}",
        })

    def post(self, request, code: str | None = None, semester: str | None = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the form contains valid data, then the course data is saved
            to the database. If request URL doesn't contain an ID then a new course
            is created. The user is redirected back to the edited courses page.
        Side-effects: New Course, CourseSection, and LabSection models are added to the DB
        '''
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
            })
        #Save course function in dataclass
        form = CourseFormData(
            course_code=course_code,
            semester=selected_semester,
            course_name=course_name,
            ta_username_list=""
        )
        #save func catching course duplication and redirect back to form
        try:
            CourseController.save_course(form, code, semester)
        except ValueError:
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
            })

        return redirect(f"/course/{form.course_code}/{form.semester}")


    def delete(self, request, code: str, semester: str):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the given course code and semester is a valid user and the logged in user is an
            administrator then the course with the given info is deleted from the database
        Side-effects: Course and all linked sections/assignments are deleted
        '''
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


