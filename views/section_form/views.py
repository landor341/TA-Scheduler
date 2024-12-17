from django.shortcuts import render, redirect
from django.views import View
from django.urls import reverse
from core.local_data_classes import LabSectionFormData, CourseSectionFormData, UserRef, CourseRef
from core.section_controller.SectionController import SectionController
from core.course_controller.CourseController import CourseController


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

        # Restrict access to Admins only
        if request.user.role != "Admin":
            return redirect(request.META.get('HTTP_REFERER', reverse('home')))

        # Initialize empty form_data
        form_data = {
            "section_number": "",
            "section_type": section_type or "",
            "days": "",
            "start_time": "",
            "end_time": "",
            "is_deletable": False,
        }

        # Pre-fill form data if URL contains valid section information
        if code and semester and section_number and section_type:
            try:
                section_number = int(section_number)
                if section_type == "Course":
                    section = SectionController.get_course_section(code, semester, section_number)
                else:
                    section = SectionController.get_lab_section(code, semester, section_number)

                # Populate form_data with details from returned dataclass
                form_data.update({
                    "section_number": section.section_number,
                    "section_type": section.section_type,
                    "days": section.days,
                    "start_time": section.start_time,
                    "end_time": section.end_time,
                    "is_deletable": True,
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
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'isAdmin': request.user.role == 'Admin',
        })


    def post(self, request, code: str | None = None, semester: str | None = None, section_number: str = None, section_type = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the form contains valid data, then the section data is saved
            to the database. If request URL doesn't map to a course section then a new section
            is created. The user is redirected back to the edited courses page.
        Side-effects: New CourseSection or LabSection object is added to DB. Potentially a TALabAssignment.
        '''
        if not request.user.is_authenticated or request.user.role != "Admin":
            return redirect(reverse('course_view', args=[code, semester]))

        # Check if the request is for deleting a section
        if request.POST.get("delete") == "true":
            try:
                section_number = int(section_number)  # Ensure section_number is an integer

                if section_type == "Course":
                    SectionController.delete_course_section(code, semester, section_number)
                elif section_type == "Lab":
                    SectionController.delete_lab_section(code, semester, section_number)
                else:
                    raise ValueError("Invalid section type provided.")

                return redirect(reverse('course_view', args=[code, semester]))

            except ValueError as e:
                print(f"Error deleting section: {e}")
                return redirect(reverse('course_view', args=[code, semester]))

        # Extract form data
        section_type = request.POST.get('section_type')
        section_number = request.POST.get('section_number')
        days = request.POST.get('days')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        try:
            section_number = int(section_number)
        except ValueError:
            return redirect(reverse('course_view', args=[code, semester]))

        try:
            if section_type == "Course":
                section_data = CourseSectionFormData(
                    course=CourseRef(course_code=code, course_name=CourseController.get_course(code, semester).name),
                    section_number=section_number,
                    days=days,
                    start_time=start_time,
                    end_time=end_time,
                    instructor=UserRef(name=request.user.get_full_name(), username=request.user.username),
                    section_type="Course",
                )
                SectionController.save_course_section(section_data, semester, course_section_number=None)

            elif section_type == "Lab":
                section_data = LabSectionFormData(
                    course=CourseRef(course_code=code, course_name=CourseController.get_course(code, semester).name),
                    section_number=section_number,
                    days=days,
                    start_time=start_time,
                    end_time=end_time,
                    section_type="Lab",
                )
                SectionController.save_lab_section(section_data, semester, lab_section_number=None)

            return redirect(reverse('course_view', args=[code, semester]))

        except ValueError as e:
            print(f"Error saving section: {e}")
            return redirect(reverse('course_view', args=[code, semester]))


