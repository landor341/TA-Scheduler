from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from core.local_data_classes import CourseFormData
from core.course_controller import CourseController
from ta_scheduler.models import Semester, Course, TACourseAssignment, User
from django.core.exceptions import PermissionDenied
import re

@method_decorator(login_required, name='dispatch')
class CourseForm(View):
    def get(self, request, code: str | None = None, semester: str | None = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: Renders a form for creating a course with sections.
            If the request URL contains a valid course ID then the form is
            preloaded with that courses current data
        Side-effects: N/A
        TODO: Describe request structure when testing
        '''

        if not request.user.role == "Admin":
            return redirect(reverse("home"))  # Use reverse for consistent URL resolution.

        course = None
        form_data = None  # Ensure the variable is always initialized

        if code and semester:
            try:
                course = Course.objects.get(course_code=code, semester__semester_name=semester)
            except Course.DoesNotExist:
                return redirect(reverse("home"))

        try:
            form_data = CourseFormData(
                course_code=course.course_code if course else "",
                course_name=course.course_name if course else "",
                semester=course.semester.semester_name if course else "",
                ta_username_list=", ".join(
                    TACourseAssignment.objects.filter(course=course).values_list("ta__username", flat=True)
                ) if course else "",
            )
        except Exception as e:
            # Handle any issues in creating the form data
            return HttpResponse(f"Error creating form data: {str(e)}", status=500)

        if form_data is None:
            return HttpResponse("Failed to create form data.", status=500)

        return render(request, "login/login.html", {"data": form_data})

    def post(self, request, code: str | None = None, semester: str | None = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the form contains valid data, then the course data is saved
            to the database. If request URL doesn't contain an ID then a new course
            is created. The user is redirected back to the edited courses page.
        Side-effects: New Course, CourseSection, and LabSection models are added to the DB
        TODO: Describe request structure when testing
        '''

        if not request.user.is_authenticated or request.user.role != "Admin":
            return redirect("login")

            # Gather form data
        code = request.POST.get("code", "").strip()
        name = request.POST.get("name", "").strip()
        semester = request.POST.get("semester", "").strip()
        ta_list = request.POST.get("ta_list", "").strip()

        # Validate inputs
        errors = []

        # Critical validation: Duplicate course code
        if Course.objects.filter(course_code=code, semester__semester_name=semester).exists():
            return HttpResponse(repr(['The selected course code already exists for this semester']),
                                content_type="text/plain", status=200)

        # Validate course code
        if not code:
            errors.append('Course code must be a valid value')
            # use regex to check for invalid characters
        elif not re.match(r'^[A-Za-z0-9]+$', code):
            errors.append("Course code must be a valid value")  # Same error message for consistency

            # validate name
        if not name:
            errors.append('Course name must be a valid value')
        elif not re.match(r'^[A-Za-z0-9 ]+$', name):  # Allow alphanumeric and spaces
            errors.append('Course name must be a valid value')

        # Validate semester
        if not CourseController.CourseController.validate_semester(semester):
            return HttpResponse(
                repr(["Course semester must be a valid semester"]),
                content_type="text/plain",
                status=200
            )

        if not CourseController.CourseController.validate_semester(semester):
            errors.append('Course semester must be a valid semester')

            # Validate TA list
        if ta_list:
            ta_usernames = [ta.strip() for ta in ta_list.split(",")]
            non_existent_tas = [
                ta for ta in ta_usernames if not User.objects.filter(username=ta).exists()
            ]
            if non_existent_tas:
                errors.append('One or more of the selected TAs is not an existing user')

        # TA Role validation
        if ta_list:
            ta_usernames = [ta.strip() for ta in ta_list.split(",")]
            invalid_tas = [
                ta for ta in ta_usernames
                if not User.objects.filter(username=ta, role="TA").exists()
            ]
            if invalid_tas:
                errors.append('One or more of the selected TAs is not a TA')

        # If validation fails, return errors in the response
        if errors:
            print(errors)
            return HttpResponse(repr(errors), content_type="text/plain", status=200)

            # Check if the course exists
        try:
            course = Course.objects.get(course_code=code)
            # Check if the semester is being changed
            if course.semester.semester_name != semester:
                errors.append("Cannot change course semester")
        except Course.DoesNotExist:
            course = None  # For new courses, allow creation

        semester_instance = Semester.objects.get(semester_name=semester)
        # Create course data and call save_course
        try:
            course_data = CourseFormData(
                course_code=code,
                course_name=name,
                semester=semester,
                ta_username_list=ta_list,
            )
            course_id = CourseController.CourseController.save_course(course_data)
        except ValueError as e:
            print(f"Error saving course: {e}")
            return HttpResponse(str(e), status=400)

        # Assign TAs to the course
        for ta in ta_list:
            TACourseAssignment.objects.create(ta=ta, course_id=course_id, grader_status=False)

        if Course.objects.filter(id=course_id).exists():
            print(f"Course saved successfully: {course_id}")
            return HttpResponse("Course saved successfully.", status=200)

        else:
            return HttpResponse("Failed to save course.", status=500)


        return render(request, 'CourseForm/CourseCreateForm.html', {"errors": errors, "form_data": request.POST})

    def delete(self, request, code: str, semester: str):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the given course code and semester is a valid user and the logged in user is an
            administrator then the course with the given info is deleted from the database
        Side-effects: Course and all linked sections/assignments are deleted
        '''

        print(f"User Role: {request.user.role}")  # Debugging
        print(f"User Authenticated: {request.user.is_authenticated}")


        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return HttpResponse("User not authenticated.", status=401)

            # Restrict only TAs from deleting courses
        if request.user.role == "TA":
            print("Blocked deletion: User is a TA.")  # Debugging
            raise PermissionDenied("TAs cannot delete courses")
            #return HttpResponse("Permission denied. TAs cannot delete courses.", status=403)
        print("about to enter try block")
        try:
            print("entered try block")
            # Fetch the course and ensure it exists
            course = get_object_or_404(Course, course_code=code, semester__semester_name=semester)

            # Only Admins or authorized Instructors can delete
            if request.user.role != "Admin":
                print("Entered admin check in try block")
                raise PermissionDenied("Admins cannot delete courses")
                #return HttpResponse("Permission denied. Only Admins can delete courses.", status=403)

            # Delete the course and related objects via the controller
            CourseController.CourseController.delete_course(course.id)
            print("Course was deleted")
            # Redirect to home on successful deletion
            return redirect(reverse("home"))
        except Course.DoesNotExist:
            return HttpResponse("Course not found for deletion.", status=404)
        except ValueError as ve:
            return HttpResponse(f"Error: {str(ve)}", status=400)



