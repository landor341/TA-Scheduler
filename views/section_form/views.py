from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.urls import reverse
from django.http import HttpResponseRedirect
from core.local_data_classes import LabSectionFormData, CourseSectionFormData
from ta_scheduler.models import Course, LabSection, CourseSection, User
from core.section_controller.SectionController import SectionController


class SectionForm(View):
    def get(self, request, code: str | None = None, semester: str | None = None, section_number: str = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: Renders a form for creating a course section.
            If the request URL contains a valid course ID, semester, and section number that maps
            to a section object then the form is preloaded with that sections current data.
        Side-effects: N/A
        '''
        if not request.user.is_authenticated:
            return redirect(reverse("login"))

        # Restrict access to Admin and Instructors only
        if request.user.role not in ["Admin", "Instructor"]:
            return redirect(reverse('home'))

        # Get course by code and semester
        course = get_object_or_404(Course, course_code=code, semester__semester_name=semester)

        # Restrict Instructor access to their own sections
        if request.user.role == "Instructor":
            if not CourseSection.objects.filter(course=course, instructor=request.user).exists():
                return redirect(reverse('home'))
        # Initialize form_data to None and attempt to get existing section data
        form_data = None
        if section_number:
            section_number = int(section_number)
            try:
                # Attempt to retrieve a CourseSection
                section = CourseSection.objects.get(course=course, course_section_number=section_number)
                form_data = CourseSectionFormData(

                    course=section.course,
                    section_number=section.course_section_number,
                    days=section.days,
                    start_time=section.start_time,
                    end_time=section.end_time,
                    instructor=section.instructor,
                    section_type="Course"
                )
            except CourseSection.DoesNotExist:
                # Attempt to retrieve a LabSection if CourseSection not found
                section = get_object_or_404(LabSection, course=course, lab_section_number=section_number)
                form_data = LabSectionFormData(
                    course=section.course,
                    section_number=section.lab_section_number,
                    days=section.days,
                    start_time=section.start_time,
                    end_time=section.end_time,
                    section_type="Lab"
                )

        return render(request, 'section_form/section_form.html', {
            "data": form_data,
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'isAdmin': request.user.role == 'Admin',
        })


    def post(self, request, code: str | None = None, semester: str | None = None, section_number: str = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the form contains valid data, then the section data is saved
            to the database. If request URL doesn't map to a course section then a new section
            is created. The user is redirected back to the edited courses page.
        Side-effects: New CourseSection or LabSection object is added to DB. Potentially a TALabAssignment.
        '''
        if not request.user.is_authenticated or request.user.role != "Admin":
            return redirect(reverse('home'))

        course = get_object_or_404(Course, course_code=code, semester__semester_name=semester)

        # Retrieve form data from request
        section_type = request.POST.get('section_type')
        section_number = request.POST.get('section_number')
        days = request.POST.get('days')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        # Validate section_number
        try:
            section_number = int(section_number)
        except ValueError:
            return redirect(reverse('home'))

        # Save CourseSection or LabSection depending on the section type
        if section_type == "Course":
            instructor_id = request.POST.get('instructor')
            instructor = get_object_or_404(User, id=instructor_id, role="Instructor")
            course_section_data = CourseSectionFormData(
                course=course,
                section_number=section_number,
                days=days,
                start_time=start_time,
                end_time=end_time,
                instructor=instructor,
                section_type="Course"
            )
            try:
                SectionController.save_course_section(course_section_data, course_section_id=None)
            except ValueError:
                return redirect(reverse('home'))

        elif section_type == "Lab":
            lab_section_data = LabSectionFormData(
                course=course,
                section_number=section_number,
                days=days,
                start_time=start_time,
                end_time=end_time,
                section_type="Lab"
            )
            try:
                SectionController.save_lab_section(lab_section_data, lab_section_id=None)
            except ValueError:
                return redirect(reverse('home'))

        return redirect(reverse('home'))


    def delete(self, request, code: str, semester: str, section_number: str):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the given course code, semester, and section number is a valid
            section and the logged in user is an administrator then the section with the given
            info is deleted from the database along with any linked TACourseAssignments
        Side-effects: Sections/assignments are deleted from DB
        '''
        if request.user.role != "Admin":
            return redirect(reverse('home'))

        course = get_object_or_404(Course, course_code=code, semester__semester_name=semester)

        # Attempt to delete either CourseSection or LabSection
        try:
            section_number = int(section_number)
            section = CourseSection.objects.get(course=course, course_section_number=section_number)
            section.delete()
        except CourseSection.DoesNotExist:
            try:
                section = LabSection.objects.get(course=course, lab_section_number=section_number)
                section.delete()
            except LabSection.DoesNotExist:
                return redirect(reverse('home'))

        return redirect(reverse('home'))


