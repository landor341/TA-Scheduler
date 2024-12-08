from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from core.course_controller.CourseController import CourseController
from core.local_data_classes import CourseFormData
from ta_scheduler.models import User


class CourseForm(View):
    def get(self, request, code: str | None = None, semester: str | None = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: Renders a form for creating a course with sections.
            If the request URL contains a valid course ID then the form is
            preloaded with that courses current data
        Side-effects: N/A
        '''
        if not self.__can_use_form(request.user, code, semester):
            return redirect(reverse("home"))

        return render(request, 'course_form/course_form.html', {
            "existSemester": SemesterController.list_semester(),
            "data": CourseForm,
            "isAdmin": request.user.role == "Admin",
            "isEditing": code is not None,
            'full_name': f"{request.user.first_name} {request.user.last_name}",
        })

    def post(self, request, code: str | None = None, semester: str | None = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the form contains valid data, then the course data is saved
            to the database. If request URL doesn't contain an ID then a new course
            is created. The user is redirected back to the edited courses page.
        Side-effects: New Course, CourseSection, and LabSection models are added to the DB
        '''
        if not self.__can_use_form(request.user, code, semester):
            return redirect(reverse("home"))

        form = CourseFormData(
            course_code=request.POST.get('course_code'),
            semester=request.POST.get('semester'),
            course_name=request.POST.get('course_name'),
            ta_username_list=""
        )

        CourseController.save_course(form, code, semester)

        return redirect(f"/course/{form.course_code}/{form.semester}")


    def delete(self, request, code: str, semester: str):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the given course code and semester is a valid user and the logged in user is an
            administrator then the course with the given info is deleted from the database
        Side-effects: Course and all linked sections/assignments are deleted
        '''
        if not self.__can_use_form(request.user, code, semester):
            return redirect(reverse("home"))

        CourseController.delete_course(code, semester)

        #  Included so that tests fail instead of throwing errors
        return redirect(reverse("home"))


    def __can_use_form(self, user: User, code: str, semester: str):
        # Need to check permissions. Could refactor in future to be controller method
        if user.role != "Admin":
            if code is None:
                return False
            course_form = CourseController.get_course(code, semester)
            for section in course_form.course_sections:
                if section.instructor.username == user.username:
                    return True
            return False
        return True


