from django.views import View


class UserForm(View):
    def get(self, request):
        '''
        Preconditions: Admin user logged in.
        Postconditions: Renders a form for creating a user.
            If the request URL contains a valid user ID that isn't another admin then the
            form is preloaded with that users current data
        Side-effects: N/A
        TODO: Describe request structure when testing
        '''
        pass

    def post(self, request):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the request contains valid course data, then the course data is saved
            to the database. If request URL doesn't contain an ID then a new user
            is created. The user is redirected back to the edited users page.
        Side-effects: New User model is added to the DB
        TODO: Describe request structure when testing
        '''
        pass




