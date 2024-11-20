from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

def home_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    return redirect('login')
def login_view(request):
    if request.method == 'POST':  # Process the form
        username = request.POST.get('username')  # Get the username from form
        password = request.POST.get('password')  # Get the password from form

        # Anthenticate username and password
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # Setting the user to login state
            return redirect('profile')  # Redirect to profile view
        else:
            messages.error(request, 'Invalid username or password.')
    # If is a get request, then render the empty form
    return render(request, 'login/login.html')
@login_required  # Ensure only login user can access
def profile_view(request):
    return render(request, 'login/profile.html', {
        'user': f"{request.user.first_name}, {request.user.last_name}",
        'email': request.user.email,
        'role': request.user.role,
        'phone': request.user.phone,
        'address': request.user.address,
        'office_hours': request.user.office_hours,
    })
def logout_view(request):
    logout(request)  # logout the user
    return redirect('login')  # redirect to the login page
