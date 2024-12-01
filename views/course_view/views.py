from django.views import View


from django.shortcuts import render, get_object_or_404
from django.views import View
from ta_scheduler.models import Course, CourseSection, User, TALabAssignment
class CourseView(View):
    def get(self, request, course_id):
        '''
        Preconditions: Request URL contains a valid course id
        Postconditions: Renders a page displaying the courses data including
            sections, TAs, and instructors
        Side-effects: N/A
        TODO: Describe request structure when testing
        '''
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

        return render(request, 'selected_course/selected_course.html', context)
