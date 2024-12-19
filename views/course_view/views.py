from django.views import View
from django.shortcuts import render, get_object_or_404

from core.course_controller.CourseController import CourseController
from ta_scheduler.models import Course, CourseSection, User, TALabAssignment, Semester, LabSection


class CourseView(View):
    def get(self, request, course_code, semester_name):
        """
        Preconditions:
            - `request` must be a valid HttpRequest object, and the user must be authenticated.
            - `course_code` is a string representing the unique code of the course.
            - `semester_name` is a string representing the semester in which the course is offered.

        Postconditions:
            - Fetches course details, including sections, lab sections, and associated instructors/TAs
              using `CourseController.get_course()`.
            - If the course or semester does not exist, renders a 404 error page with an appropriate error message.
            - Renders the `selected_course/selected_course.html` template, displaying:
                * Basic course details (e.g., course code, name, semester).
                * Course sections and their assigned instructors.
                * Lab sections and their assigned TAs.

        Side-effects:
            - Calls `CourseController.get_course()` to retrieve detailed course data.
            - Aggregates instructors and TAs from course sections and lab sections, respectively.

        Parameters:
            - request: The HttpRequest object containing metadata about the HTTP GET request.
            - course_code (str): The unique code for the course to fetch.
            - semester_name (str): The name of the semester to filter the course.

        Returns:
            - If the course exists:
                * An HttpResponse rendering the `selected_course/selected_course.html` template with the following context:
                    - `full_name`: Full name of the logged-in user.
                    - `isAdmin`: Boolean indicating whether the logged-in user has the 'Admin' role.
                    - `course`: A dictionary containing:
                        * `course_code`: The course's unique code.
                        * `course_name`: The full name of the course.
                        * `semester`: A dictionary containing the `semester_name`.
                    - `sections`: List of course sections associated with the course.
                    - `lab_sections`: List of lab sections associated with the course.
                    - `tas`: List of teaching assistants (TAs) assigned to the lab sections.
                    - `instructors`: List of instructors assigned to the course sections.
            - If the course or semester does not exist:
                * An HttpResponse rendering `404.html` with an error message.

        """
        try:
            # Use the static method to fetch the course overview
            course_overview = CourseController.get_course(course_code, semester_name)
        except ValueError as e:
            # Handle case where course or semester does not exist
            return render(request, '404.html', {'error_message': str(e)})

        tas = [lab.instructor for lab in course_overview.lab_sections if lab.instructor]
        instructors = [section.instructor for section in course_overview.course_sections if section.instructor]
        sections = course_overview.course_sections
        lab_sections = course_overview.lab_sections

        context = {
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'isAdmin': request.user.role == 'Admin',
            'course': {
                'course_code': course_overview.code,
                'course_name': course_overview.name,
                'semester': {
                    'semester_name': course_overview.semester,

                }
            },
            'sections': sections,
            'lab_sections': lab_sections,
            'tas': tas,
            'instructors': instructors
        }

        return render(request, 'selected_course/selected_course.html', context)