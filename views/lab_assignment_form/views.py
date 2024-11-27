from django.views import View


class LabAssignmentForm(View):
    def get(self, request):
        '''
        Preconditions: Admin user logged in. Get request URL contains a valid course id
        Postconditions: Renders a course form page with the selected courses info preloaded.
        Side-effects: N/A
        TODO: Describe request structure when testing
        '''
        pass

    def post(self, request):
        '''
        Preconditions: Admin or instructor for selected course is logged in.
            Requests URL contains a valid course id
        Postconditions: If the form contains valid data, then new TALabAssignment models
            are created
        Side-effects: New TACourseAssignments are added to the DB
        TODO: Describe request structure when testing
        '''
        pass




