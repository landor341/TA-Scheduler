from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.views import View


class Login(View):
    def get(self, request):
        return render(request, 'login/login.html')
    def post(self, request):
        username = request.POST.get('username')  # Get the username from form
        password = request.POST.get('password')  # Get the password from form

        # Authenticate username and password
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # Setting the user to login state
            return redirect('profile')  # Redirect to profile view
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login/login.html')


class Logout(View):
    def get(self, request):
        logout(request)
        return redirect('login')



