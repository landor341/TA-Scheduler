from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.views import View


class Login(View):
    def get(self, request):
        """
        Preconditions: None

        Postconditions: Renders the login page to the user.

        Side-effects: None

        Parameters:
        - request: The HTTP request object containing metadata and state.

        Returns: An HttpResponse object rendering the 'login/login.html' template.
        """
        return render(request, 'login/login.html')
    def post(self, request):
        """
        Preconditions:
        - 'username' and 'password' fields must be provided in the POST request.

        Postconditions: Authenticates the user with the provided credentials. Logs the user in if authentication is successful or displays an error message otherwise.

        Side-effects: Sets the user's session to a logged-in state if authentication is successful. Displays an error message on failed authentication.

        Parameters:
        - request: The HTTP request object containing metadata and state.

        Returns:
        - On successful authentication, redirects the user to the 'home' page.
        - On failed authentication, returns an HttpResponse object rendering the 'login/login.html' template with an error message.
        """

        username = request.POST.get('username')  # Get the username from form
        password = request.POST.get('password')  # Get the password from form

        # Authenticate username and password
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # Setting the user to login state
            return redirect('home')  # Redirect to profile view
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login/login.html')


class Logout(View):
    """
    Preconditions: The user must be logged in.

    Postconditions: Logs the user out and redirects to the login page.

    Side-effects: Ends the user's session and logs them out.

    Parameters:
    - request: The HTTP request object containing metadata and state.

    Returns: Redirects the user to the 'login' page.
    """
    def get(self, request):
        logout(request)
        return redirect('login')



