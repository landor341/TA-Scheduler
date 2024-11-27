from django.views import View


class CourseView(View):
    def get(self, request):
        '''
        Preconditions: Request URL contains a valid course id
        Postconditions: Renders a page displaying the courses data including
            sections, TAs, and instructors
        Side-effects: N/A
        TODO: Describe request structure when testing
        '''
        pass




