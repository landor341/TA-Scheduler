from django.views import View


from django.shortcuts import render, get_object_or_404
from django.views import View
from ta_scheduler.models import Course, CourseSection, User, TALabAssignment
class CourseView(View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        sections = CourseSection.objects.filter(course=course)

        ta_assignments = TALabAssignment.objects.filter(lab_section__course=course)
        tas = User.objects.filter(id__in=ta_assignments.values_list('ta', flat=True), role='TA')

        instructors = User.objects.filter(id__in=sections.values_list('instructor', flat=True), role='Instructor')

        context = {
            'course': course,
            'sections': sections,
            'tas': tas,
            'instructors': instructors,
        }

        # Ensure this path corresponds to your project's template directory structure
        return render(request, 'selected_course.html', context)
