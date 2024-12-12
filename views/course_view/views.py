from django.views import View
from django.shortcuts import render, get_object_or_404
from ta_scheduler.models import Course, CourseSection, User, TALabAssignment, Semester, LabSection


class CourseView(View):
    def get(self, request, course_code, semester_name):
        """
        Preconditions:
        - `course_code` must be a non-empty string representing a valid course code.
        - `semester_name` must be a non-empty string representing a valid semester name.
        - `request` is a valid HttpRequest object.

        Postconditions:
        - Retrieves the specified course data, its sections, and associated TAs and instructors.
        - Renders the 'selected_course/selected_course.html' template with the retrieved data.
        - Raises Http404 if the semester or course does not exist.

        Side-effects:
        - None.

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - course_code: A string representing the course code to retrieve from the Courses table.
        - semester_name: A string representing the semester name to retrieve from the Semesters table.

        Returns:
        - An HttpResponse object rendering the 'selected_course/selected_course.html' template with course, sections, TAs, and instructors in the context.
        - Raises Http404 if the semester or course does not exist.
        """
        # Get semester object
        semester = get_object_or_404(Semester, semester_name=semester_name)
        # Get course object
        course = get_object_or_404(Course, course_code=course_code, semester=semester)

        sections = CourseSection.objects.filter(course=course)
        ta_assignments = TALabAssignment.objects.filter(lab_section__course=course)
        tas = User.objects.filter(id__in=ta_assignments.values_list('ta', flat=True), role='TA')
        instructors = User.objects.filter(id__in=sections.values_list('instructor', flat=True), role='Instructor')
        lab_section=LabSection.objects.filter(course=course)

        context = {
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'isAdmin': request.user.role == 'Admin',
            'course': course,
            'sections': sections,
            'tas': tas,
            'instructors': instructors,
            'lab_section': lab_section
        }

        return render(request, 'selected_course/selected_course.html', context)
