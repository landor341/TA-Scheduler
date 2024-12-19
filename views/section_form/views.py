from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse
from core.local_data_classes import LabSectionFormData, CourseSectionFormData, UserRef, CourseRef
from core.section_controller.SectionController import SectionController
from core.course_controller.CourseController import CourseController
from core.user_controller.UserController import UserController


def get_instructors(request):
    """
    Preconditions:
    - The request must include a valid 'section_type' query parameter, which should either be 'Course' or 'Lab'.
    Postconditions:
    - Returns a JSON response containing a list of users classified as "Instructors" for 'Course' sections or "TAs"
      for 'Lab' sections.
    Side-effects: None.
    Parameters:
    - request: A Django HttpRequest object that includes a "section_type" query parameter.
    Returns: A JsonResponse containing a list of user dictionaries with 'username' and 'name'. Returns a 400 status
             with an error message if an invalid 'section_type' is provided.
    """
    section_type = request.GET.get('section_type')

    if section_type == "Course":
        users = UserController.searchUser(user_role="Instructor")
    elif section_type == "Lab":
        users = UserController.searchUser(user_role="TA")
    else:
        return JsonResponse({"error": "Invalid section type"}, status=400)

    # Transform the user list into JSON-friendly format
    user_data = [{"username": user.username, "name": user.name} for user in users]

    return JsonResponse({"instructors": user_data})

class SectionForm(View):
    def get(self, request, code: str | None = None, semester: str | None = None, section_number: str = None, section_type: str = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: Renders a form for creating a course section.
            If the request URL contains a valid course ID, semester, and section number that maps
            to a section object then the form is preloaded with that sections current data.
        Side-effects: N/A
        '''
        if not request.user.is_authenticated:
            return redirect(reverse("login"))

        # Restrict access to Admins and Instructors only
        if request.user.role not in ["Admin", "Instructor"]:
            return redirect(reverse('course_view', args=[code, semester]))

        is_admin = request.user.role == "Admin"
        is_instructor = request.user.role == "Instructor"

        if is_instructor:
            section_type="Lab"

        # Initialize empty form_data
        form_data = {
            "section_number": "",
            "section_type": section_type or "",
            "days": "",
            "start_time": "",
            "end_time": "",
            "instructor": "",
            "is_deletable": is_admin,
            "read_only": is_instructor,
        }

        # Fetch user list based on section type/instructors by default on new section creation
        instructor_list = UserController.searchUser(user_role="Instructor")

        if section_type == "Course":
            instructor_list = UserController.searchUser(user_role="Instructor")
        elif section_type == "Lab":
            instructor_list = UserController.searchUser(user_role="TA")

        # Pre-fill form data if URL contains valid section information
        if code and semester and section_number and section_type:
            try:
                section_number = int(section_number)
                if section_type == "Course":
                    section = SectionController.get_course_section(code, semester, section_number)
                    form_data.update({
                        "section_number": section.section_number,
                        "section_type": section.section_type,
                        "days": section.days,
                        "start_time": section.start_time,
                        "end_time": section.end_time,
                        "instructor": section.instructor.username if section.instructor else "",
                    })
                elif section_type == "Lab":
                    section = SectionController.get_lab_section(code, semester, section_number)
                    form_data.update({
                        "section_number": section.section_number,
                        "section_type": section.section_type,
                        "days": section.days,
                        "start_time": section.start_time,
                        "end_time": section.end_time,
                    })

            except ValueError as e:
                print(f"Error: {e}")  # Debugging purpose
                # Redirect back if the section does not exist or is invalid
                return redirect(reverse('course_view', args=[code, semester]))

        return render(request, 'section_form/section_form.html', {
            "data": form_data,
            "code": code,
            "semester": semester,
            "section_type": section_type,
            "instructors": instructor_list,
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'isAdmin': is_admin,
            'isInstructor': is_instructor,
        })


    def post(self, request, code: str | None = None, semester: str | None = None, section_number: str = None, section_type = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the form contains valid data, then the section data is saved
            to the database. If request URL doesn't map to a course section then a new section
            is created. The user is redirected back to the edited courses page.
        Side-effects: New CourseSection or LabSection object is added to DB. Potentially a TALabAssignment.
        '''
        if not request.user.is_authenticated:
            return redirect(reverse('login'))

            # Restrict access to Admins and Instructors only
        if request.user.role not in ["Admin", "Instructor"]:
            return redirect(reverse('course_view', args=[code, semester]))

            # Role check
        is_admin = request.user.role == "Admin"
        is_instructor = request.user.role == "Instructor"

        # Instructors are only allowed to work with Lab sections
        if is_instructor:
            section_type = "Lab"

        # Check if the request is for deleting a section
        if request.POST.get("delete") == "true":
            try:
                if section_type == "Course" and not is_admin:
                    raise ValueError("Instructors cannot delete Course sections.")
                if section_type == "Course" and is_admin:
                    SectionController.delete_course_section(code, semester, int(section_number))
                elif section_type == "Lab":
                    SectionController.delete_lab_section(code, semester, int(section_number))
                return redirect(reverse('course_view', args=[code, semester]))
            except ValueError as e:
                print(f"Error deleting section: {e}")
                return redirect(reverse('course_view', args=[code, semester]))

        # Extract form data
        form_section_number = request.POST.get('section_number')
        instructor_username = request.POST.get('instructor')

        try:
            form_section_number = int(form_section_number)
        except ValueError:
            return redirect(reverse('course_view', args=[code, semester]))

        try:
            # Instructors: Only assign TA for Lab sections
            if is_instructor:
                instructor_ref = UserRef(name="", username=instructor_username)
                SectionController.assign_instructor_or_ta(
                    section_type="Lab",
                    section_number=form_section_number,
                    course_code=code,
                    semester_name=semester,
                    instructor_ref=instructor_ref
                )
                return redirect(reverse('course_view', args=[code, semester]))

            # Admin logic: Full CRUD operations
            if is_admin:
                section_type = request.POST.get('section_type')
                instructor_ref = UserRef(name="", username=instructor_username)

                if section_type == "Course":
                    existing_section = None
                    if section_number:
                        existing_section = SectionController.get_course_section(code, semester, int(section_number))

                    section_data = CourseSectionFormData(
                        course=CourseRef(course_code=code,
                                         course_name=CourseController.get_course(code, semester).name),
                        section_number=form_section_number,
                        days=request.POST.get('days'),
                        start_time=request.POST.get('start_time') or (existing_section.start_time if existing_section else None),
                        end_time=request.POST.get('end_time') or (existing_section.end_time if existing_section else None),
                        instructor=instructor_ref,
                        section_type="Course",
                    )
                    SectionController.save_course_section(section_data, semester, course_section_number=int(
                        section_number) if section_number else None)

                elif section_type == "Lab":
                    existing_section = None
                    if section_number:
                        existing_section = SectionController.get_lab_section(code, semester, int(section_number))

                    section_data = LabSectionFormData(
                        course=CourseRef(course_code=code,
                                         course_name=CourseController.get_course(code, semester).name),
                        section_number=form_section_number,
                        days=request.POST.get('days'),
                        start_time=request.POST.get('start_time') or (existing_section.start_time if existing_section else None),
                        end_time=request.POST.get('end_time') or (existing_section.end_time if existing_section else None),
                        section_type="Lab",
                    )
                    SectionController.save_lab_section(section_data, semester, lab_section_number=int(
                        section_number) if section_number else None)

                    # Assign TA for Lab section
                    SectionController.assign_instructor_or_ta(
                        section_type="Lab",
                        section_number=form_section_number,
                        course_code=code,
                        semester_name=semester,
                        instructor_ref=instructor_ref
                    )
                else:
                    raise ValueError("Invalid section type provided.")

                return redirect(reverse('course_view', args=[code, semester]))

        except ValueError as e:
            print(f"Error saving section: {e}")
            return redirect(reverse('course_view', args=[code, semester]))