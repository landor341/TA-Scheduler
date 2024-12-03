from django.shortcuts import render
from django.views import View


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
        return render(request, 'login/login.html', {"data": {}})

    def post(self, request, code: str | None = None, semester: str | None = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the form contains valid data, then the course data is saved
            to the database. If request URL doesn't contain an ID then a new course
            is created. The user is redirected back to the edited courses page.
        Side-effects: New Course, CourseSection, and LabSection models are added to the DB
        TODO: Describe request structure when testing
        '''
        return render(request, 'login/login.html')




