from django.shortcuts import render
from django.views import View


class SectionForm(View):
    def get(self, request, code: str | None = None, semester: str | None = None, section_number: str = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: Renders a form for creating a course section.
            If the request URL contains a valid course ID, semester, and section number that maps
            to a section object then the form is preloaded with that sections current data.
        Side-effects: N/A
        '''
        return render(request, 'login/login.html', {"data": {}})

    def post(self, request, code: str | None = None, semester: str | None = None, section_number: str = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the form contains valid data, then the section data is saved
            to the database. If request URL doesn't map to a course section then a new section
            is created. The user is redirected back to the edited courses page.
        Side-effects: New CourseSection or LabSection object is added to DB. Potentially a TALabAssignment.
        '''
        return render(request, 'login/login.html')


    def delete(self, request, code: str, semester: str, section_number: str):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the given course code, semester, and section number is a valid
            section and the logged in user is an administrator then the section with the given
            info is deleted from the database along with any linked TACourseAssignments
        Side-effects: Sections/assignments are deleted from DB
        '''
        #  Included so that tests fail instead of throwing errors
        return render(request, 'login/login.html')


