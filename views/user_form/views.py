from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from core.local_data_classes import UserFormData, UserProfile, PrivateUserProfile
from core.user_controller.UserController import UserController


class UserForm(View):
    def get(self, request, username: str | None = None):
        '''
        Preconditions: Admin user logged in or username is logged in users username.
        Postconditions: Renders a form for creating a user.
            If the request URL contains a valid user ID then the
            form is preloaded with that users current data
        Side-effects: N/A
        '''
        if request.user.role == "Admin" and username is None:
            return render(request, 'user_form/user_form.html', {
                "data": UserFormData("", "", "", "", "", "", "", "")
            })
        elif request.user.role == "Admin" or username == request.user.username:
            user: PrivateUserProfile = UserController.getUser(username, request.user)
            first_name = user.name.split(" ", 1)
            last_name = first_name[1]
            first_name = first_name[0]

            return render(request, 'user_form/user_form.html', {
                "data": UserFormData(username, first_name, last_name,
                                     user.role, user.office_hours, user.email, user.address, user.phone),
                "password": True,
                "isAdmin": request.user.role == "Admin"
            })
        else:
            return redirect(reverse("home"))

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
        user_data = {
            "username": request.POST.get("username"),
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "email": request.POST.get("email"),
            "office_hours": request.POST.get("office_hours"),
            "phone_number": request.POST.get("phone_number"),
            "address": request.POST.get("address"),
            "role": request.POST.get("role")
        }
        password = request.POST.get("password")
        if password:
            user_data["password"] = password

        user = UserController.saveUser(user_data, request.user)

        return redirect(reverse("profile", kwargs={"username": user.username}))

    def delete(self, request, username: str):
        '''
        Preconditions: Admin user logged in.
        Postconditions: If the given username is a valid user and the logged in user is an
            administrater then the user with the given username is deleted from the database
        Side-effects: User model is deleted from DB
        '''
        if request.user.role == "Admin":
            UserController.deleteUser(username)
        return redirect(reverse("home"))




