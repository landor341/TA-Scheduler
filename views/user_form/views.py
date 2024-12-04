from django.shortcuts import render
from django.views import View


class UserForm(View):
    def get(self, request, username: str | None = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: Renders a form for creating a user.
            If the request URL contains a valid user ID that isn't another admin then the
            form is preloaded with that users current data
        Side-effects: N/A
        '''
        #  Included so that tests fail instead of throwing errors
        return render(request, 'login/login.html', {"data": {}})

    def post(self, request, username: str | None = None):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the request contains valid user data, then the user data is saved
            to the database. If request URL doesn't contain an ID then a new user
            is created. The user is redirected back to the edited users page.
            Valid data contains the following keys:
            "username","first_name","last_name","office_hours","email","phone","address","role"
        Side-effects: New User model is added to the DB
        '''
        #  Included so that tests fail instead of throwing errors
        return render(request, 'login/login.html', {"data": {}})

    def delete(self, request, username: str):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the given username is a valid user and the logged in user is an
            administrater then the user with the given username is deleted from the database
        Side-effects: User model is deleted from DB
        '''
        #  Included so that tests fail instead of throwing errors
        return render(request, 'login/login.html', {"data": {}})




