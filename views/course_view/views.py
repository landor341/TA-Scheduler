from django.views import View
from django.shortcuts import render, get_object_or_404

from core.course_controller.CourseController import CourseController
from ta_scheduler.models import Course, CourseSection, User, TALabAssignment, Semester, LabSection


class CourseView(View):
    def get(self, request, course_code, semester_name):
        """
        Retrieves course data, sections, lab sections, and assignments
        using the static method `get_course`.

        Renders the `selected_course.html` template with this data.
        """
        try:
            # Use the static method to fetch the course overview
            course_overview = CourseController.get_course(course_code, semester_name)
        except ValueError as e:
            # Handle case where course or semester does not exist
            return render(request, '404.html', {'error_message': str(e)})

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
            'tas': course_overview.ta_list,
            'instructors': instructors
        }

        return render(request, 'selected_course/selected_course.html', context)