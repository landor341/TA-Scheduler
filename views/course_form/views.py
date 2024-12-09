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
from django.contrib import messages
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
        # Check user
        if not request.user.role == "Admin":
            return redirect(reverse("home"))  # Use reverse for consistent URL resolution.

        form_data = None  # Ensure the variable is always initialized, blank data

        if code and semester:
            try:
                # Fetch course overview using the controller methods
                course_overview = CourseController.CourseController.get_course(code, semester)
                form_data = CourseFormData(
                    course_code=course_overview.code,
                    course_name=course_overview.name,
                    semester=course_overview.semester.semester_name,
                    ta_username_list=", ".join([ta.username for ta in CourseFormData.ta_username_list]),
                )
            except ValueError as e:
                return HttpResponse(f"Error loading course: {str(e)}", status=404)

        if not form_data:
            form_data = CourseFormData(course_code="", course_name="", semester="", ta_username_list="")
        #Not supposed to do this but for testing, direct db access
        semesters = Semester.objects.all()
        courses = Course.objects.all()
        #Use static controller methods for this above logic
        return render(request, "CourseForm/CourseCreateForm.html", {"data": form_data, "semesters": semesters, "courses": courses})

    def post(self, request, code: str | None = None, semester: str | None = None):
        action = request.POST.get('action')
        print(f"Action received: {action}")

        if action == "delete":
            print("Entered delete block in POST")
            code = request.POST.get('code')
            semester = request.POST.get('semester')
            return self.delete(request, code=code, semester=semester)

        elif action == "edit":
            # Fetch the original course
            course_code = request.POST.get('original_code').strip()
            semester_name = request.POST.get('original_semester').strip()
            course = Course.objects.get(course_code=course_code, semester__semester_name=semester_name)

            errors = []

            # Validate inputs
            if not course.course_code or not re.match(r'^[A-Za-z0-9]+$', course.course_code):
                errors.append('Course code must be a valid alphanumeric value.')
                return redirect(reverse("course-creator"))

            if not course.course_name or not re.match(r'^[A-Za-z0-9 ]+$', course.course_name):
                errors.append('Course name must be a valid alphanumeric value.')
                return redirect(reverse("course-creator"))

            if not course.semester:
                errors.append("Semester is required.")
                return redirect(reverse("course-creator"))

            if 'save' in request.POST:
                # Save changes to the course
                course.course_code = request.POST.get('code').strip()
                course.course_name = request.POST.get('name').strip()
                course.semester = Semester.objects.get(semester_name=request.POST.get('semester').strip())
                course.ta_list = request.POST.get('ta_list').strip()  # Adjust field name if needed
                course.save()
                return redirect('course-creator')  # Redirect to course list after saving


            # Render form pre-filled with course data
            context = {
                'data': {
                    'course_code': course.course_code,
                    'course_name': course.course_name,
                    'semester': course.semester,
                },
                'semesters': Semester.objects.all(),
                'action': 'edit',
                'courses': Course.objects.all(),  # Include courses for the table
            }
            return render(request, 'CourseForm/CourseCreateForm.html', context)

        elif action == "create":
            # Authenticate and check user role
            if not request.user.is_authenticated or request.user.role != "Admin":
                return redirect("login")

            # Gather form data for course creation or update
            post_code = request.POST.get("code", "").strip()
            post_name = request.POST.get("name", "").strip()
            post_semester = request.POST.get("semester", "").strip()
            post_ta_list = request.POST.get("ta_list", "").strip()


            # Initialize CourseFormData object
            fData = CourseFormData(
                course_code=post_code,
                course_name=post_name,
                semester=post_semester,
                ta_username_list=post_ta_list,
            )

            # Validate inputs
            errors = {
                "course_code": None,
                "course_name": None,
                "semester": None,
                "ta_username_list": None,
            }

            # Validate course code
            if not post_code:
                errors["course_code"] = "Course code must be a valid value."
                messages.error(request, "Course code must be a valid value.")
                return redirect("course-creator")

            if not re.match(r'^[A-Za-z0-9]+$', post_code):
                errors["course_code"] = "Course code must contain only alphanumeric characters."
                messages.error(request, "Course code must contain only alphanumeric characters.")
                return redirect("course-creator")

            # Validate course name
            if not post_name:
                errors["course_name"] = "Course name must be a valid value."
                messages.error(request, "Course name must be a valid value.")
                return redirect("course-creator")

            if not re.match(r'^[A-Za-z0-9 ]+$', post_name):  # Allow alphanumeric and spaces
                errors["course_name"] = "Course name must contain only alphanumeric characters and spaces."
                messages.error(request, "Course name must contain only alphanumeric characters and spaces.")
                return redirect("course-creator")

            # Validate semester
            try:
                CourseController.CourseController.save_course(course_data=fData, semester_name=post_semester,
                                                              course_code=code)
            except ValueError as e:
                messages.error(request, str(e))
                return redirect("course-creator")
            except Exception as e:
                print(f"Unexpected error: {e}")
                return HttpResponse(
                    repr(["Unexpected error: " + str(e)]),
                    content_type="text/plain",
                    status=500,
                )

            # Handle TA list validation if provided
            if post_ta_list:
                ta_usernames = [ta.strip() for ta in post_ta_list.split(",")]
                non_existent_tas = [
                    ta for ta in ta_usernames if not User.objects.filter(username=ta).exists()
                ]
                if non_existent_tas:
                    errors["ta_username_list"] = "One or more of the selected TAs does not exist."
                    messages.error(request, "One or more of the selected TAs does not exist.")

                invalid_tas = [
                    ta for ta in ta_usernames
                    if not User.objects.filter(username=ta, role="TA").exists()
                ]
                if invalid_tas:
                    errors["ta_username_list"] = "One or more of the selected TAs is not assigned the role of TA."
                    messages.error(request, "One or more of the selected TAs is not assigned the role of TA.")

            # If there are validation errors, return them
            if errors:
                # Prepopulate form data and reload the form
                semesters = Semester.objects.all()
                courses = Course.objects.all()
                eData = {
                    'data': {
                        'course_code': post_code,
                        'course_name': post_name,
                        'semester': post_semester,
                        'ta_username_list': post_ta_list,
                    },
                    'semesters': semesters,
                    'courses': courses,
                    'errors': errors,  # Pass the errors dictionary to the template
                }
                return render(request, "CourseForm/CourseCreateForm.html", {"errors": eData, "data": fData})

            # Confirm successful course save or update
            messages.success(request, "Course has been successfully saved.")

            return render(request, template_name="CourseForm/CourseCreateForm.html", context={"errors": errors, "data": fData})  # Redirect to the course list after creation

    '''
    
     for ta in ta_list:
         TACourseAssignment.objects.create(ta=ta, course_id=course_id, grader_status=False)
         
         No logic for this yet
         
     '''

    def delete(self, request, code: str, semester: str):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the given course code and semester is a valid user and the logged in user is an
            administrator then the course with the given info is deleted from the database
        Side-effects: Course and all linked sections/assignments are deleted
        '''

        print(f"received parameters {code}, {semester}")
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return HttpResponse("User not authenticated.", status=401)

            # Restrict only TAs from deleting courses
        if request.user.role == "TA":
            print("Blocked deletion: User is a TA.")  # Debugging
            messages.success(request, "Permission Denied, TAs cannot delete courses.")
            return HttpResponse("Permission denied. TAs cannot delete courses.", status=403)

        print("about to enter try block")
        try:
            print("entered try block")
            # Fetch the course and ensure it exists
            course = CourseController.CourseController.get_course(course_code=code, semester_name=semester)

            # Only Admins or authorized Instructors can delete
            if request.user.role != "Admin":
                messages.success(request, "You do not have permission to perform this action (Not Admin).")
                return redirect(reverse('course-creator'))
                # return HttpResponse("Permission denied. Only Admins can delete courses.", status=403)
            print("About to delete course")
            CourseController.CourseController.delete_course(course_code=course.code, semester_name=course.semester.semester_name)
            # Redirect to creator for now on success
            return redirect('course-creator')
        except Course.DoesNotExist:
            return HttpResponse("Course not found for deletion.", status=404)
        except ValueError as ve:
            print(f"Error trying to delete course: {ve}")
            return HttpResponse(f"Error: {str(ve)}", status=400)
