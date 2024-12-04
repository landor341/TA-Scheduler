from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View


from core.user_controller.UserController import UserController#This import is causing the apps aren't loaded yet error idk how to fix it


class ProfileView(View):
    def get(self, request, username=None):
        if not request.user.is_authenticated:
            return redirect('login')

        # Use UserController to fetch the user profile
        try:
            user_profile = UserController.getUser(username or request.user.username, request.user)
        except ValueError:
            # Handle the case where username or other parameters might be invalid
            raise Http404("User profile not found.")

        context = {
            'user_profile': user_profile,
        }

        return render(request, 'profile_view/profile.html', context)