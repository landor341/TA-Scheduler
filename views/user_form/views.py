from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from core.local_data_classes import UserFormData, UserProfile, PrivateUserProfile
from core.user_controller.UserController import UserController

class UserForm(View):
    def get(self, request, username: str | None = None):
        """
        Preconditions:
        - `username` is an optional parameter that can be a string or `None`.
        - `request` is a valid HttpRequest object.

        Postconditions:
        - Renders the user form for an admin or the specified user.
        - If the role is Admin and username is not provided, a blank form is rendered.
        - If the admin or the user whose username is provided accesses the form, it pre-fills the form with user data.
        - Redirects to home if access is unauthorized.

        Side-effects:
        - None.

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - username: An optional string representing the username in the Users table.

        Returns:
        - An HttpResponse object rendering the 'user_form/user_form.html' template with appropriate user data.
        - Redirects to home if the user does not have the necessary permissions.
        """
        if request.user.role == "Admin" and username is None:
            return render(request, 'user_form/user_form.html', {
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                "data": UserFormData("", "", "", "", "", "", "", ""),
                "isAdmin": True
            })
        elif request.user.role == "Admin" or username == request.user.username:
            user: PrivateUserProfile = UserController.getUser(username, request.user)
            first_name = user.name.split(" ", 1)
            last_name = first_name[1]
            first_name = first_name[0]
            return render(request, 'user_form/user_form.html', {
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                "data": UserFormData(username, first_name, last_name,
                                     user.role, user.office_hours, user.email, user.address, user.phone),
                "password": True,
                "isAdmin": request.user.role == "Admin"
            })
        else:
            return redirect(reverse("home"))

    def post(self, request, username: str | None = None):
        """
        Preconditions:
        - `username` is an optional parameter that can be a string or `None`.
        - `request` is a valid HttpRequest object, containing POST data with user details.

        Postconditions:
        - Saves or updates the user data based on the provided form data.
        - Redirects to the user's profile page after saving.

        Side-effects:
        - Modifies or creates user data in the database.

        Parameters:
        - request: An HttpRequest object containing POST data with user details.
        - username: An optional string representing the username in the Users table.

        Returns:
        - Redirects to the user's profile page after saving the form data.
        """
        if request.user.role == "Admin" and request.POST.get("_method") == "DELETE":
            return self.delete(request, username)
        user_data = {
            "username": request.POST.get("username"),
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "email": request.POST.get("email"),
            "office_hours": request.POST.get("office_hours"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "role": request.POST.get("role")
        }
        password = request.POST.get("password")
        if password:
            user_data["password"] = password
        if user_data["role"] is None:
            del user_data["role"]

        user = UserController.saveUser(user_data, request.user)

        return redirect(reverse("profile", kwargs={"username": user.username}))

    def delete(self, request, username: str):
        """
        Preconditions:
        - `username` must be a non-empty string.
        - `request` is a valid HttpRequest object with an authenticated user who has Admin privileges.

        Postconditions:
        - Deletes the specified user if the request is made by an admin.
        - Redirects to home after deletion.

        Side-effects:
        - Removes user data from the database.

        Parameters:
        - request: An HttpRequest object containing metadata about the request.
        - username: A string representing the username in the Users table to be deleted.

        Returns:
        - Redirects to home after deleting the user if performed by an Admin.
        """
        if request.user.role == "Admin":
            UserController.deleteUser(username, request.user)
        return redirect(reverse("home"))




