from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View


class ProfileView(View):
    def get(self, request, username=None):
        #intentionally delay import to avoid apps not loaded error
        from core.user_controller.UserController import UserController

        if not request.user.is_authenticated:
            return redirect('login')

        try:
            user_profile = UserController.getUser(username or request.user.username, request.user)
        except ValueError:
            raise Http404("User profile not found.")

        context = {
            'user_profile': user_profile,
        }

        return render(request, 'profile_view/profile.html', context)