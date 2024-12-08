from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View


class ProfileView(View):
    def get(self, request, username=None):
        """
        Preconditions:
        - `username` is an optional parameter which can be a string representing the username or `None`.
        - `request` is a valid HttpRequest object and must have an authenticated user.

        Postconditions:
        - Retrieves the specified user's profile data and renders the 'profile_view/profile.html' template.
        - If the user is not authenticated, redirects to the login page.
        - If the specified user profile is not found, redirects to the home page.

        Side-effects:
        - Importing `UserController` within the method to avoid "apps not loaded" error.

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - username: An optional string representing the username in the Users table. If `None`, the authenticated user's username is used.

        Returns:
        - An HttpResponse object rendering the 'profile_view/profile.html' template with user profile data in the context.
        - Redirects to 'login' if the user is not authenticated.
        - Redirects to 'home' if user profile is not found due to `ValueError` or `Http404`.
        """
        #intentionally delay import to avoid apps not loaded error
        from core.user_controller.UserController import UserController

        if not request.user.is_authenticated:
            return redirect('login')

        try:
            user_profile = UserController.getUser(username or request.user.username, request.user)
        except ValueError:
            return redirect('home')
        except Http404:
            return redirect('home')
        context = {
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'user_profile': user_profile,
            'isAdmin': request.user.role == 'Admin',
            'self': username == None or username == request.user.username,
            'username': request.user.username if username is None else username,
        }

        return render(request, 'profile_view/profile.html', context)