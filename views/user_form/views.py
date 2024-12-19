import re
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from core.local_data_classes import UserFormData, PrivateUserProfile, UserRef
from core.user_controller.UserController import UserController
from ta_scheduler.models import User

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
                "data": UserFormData("", "", "", "", "", "", "", "", []),  # Initialize empty skills list
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
                                     user.role, user.office_hours, user.email, user.address, user.phone, user.skills),
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

        # Extract user data from the request
        user_data = {
            "username": request.POST.get("username"),
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "email": request.POST.get("email"),
            "office_hours": request.POST.get("office_hours"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "role": request.POST.get("role"),
            "skills": request.POST.getlist("skills"),
        }

        # Add password if provided
        password = request.POST.get("password")
        if password:
            user_data["password"] = password

        # Perform field validation and collect errors
        errors = self.validate_user_data(user_data)

        # If there are validation errors, render the form with the errors and 400 status
        if errors:
            if UserController.existUser(user_data["username"]):
                return render(request, "user_form/user_form.html", {
                    "errors": errors,
                    "data": user_data,
                    "full_name": f"{request.user.first_name} {request.user.last_name}",
                    "isAdmin": request.user.role == "Admin",
                }, status=400)
            else:
                return render(request, "user_form/user_form.html", {
                    "errors": errors,
                    "full_name": f"{request.user.first_name} {request.user.last_name}",
                    "isAdmin": request.user.role == "Admin",
                }, status=400)

        # Try saving the user, handling potential ValidationError exceptions from the controller
        try:
            user = UserController.saveUser(user_data, request.user)
        except ValidationError as e:
            return render(request, "user_form/user_form.html", {
                "errors": e.messages,
                "data": user_data,
                "full_name": f"{request.user.first_name} {request.user.last_name}",
                "isAdmin": request.user.role == "Admin",
            }, status=400)

        # If successful, redirect to the user's profile page
        return redirect(reverse("profile", kwargs={"username": user.username}))

    def validate_user_data(self, user_data):
        """
        Performs validation on user data and returns a list of errors, if any.
        """
        errors = []

        # Username validation
        user_id = user_data.get("id")  # Assume `id` is passed for existing users
        existing_user = None
        if user_id:
            # Try to fetch existing user
            try:
                existing_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                errors.append("User does not exist")
                return errors
        if existing_user:
            # If modifying an existing user, ensure username is not changed
            if user_data["username"].strip() != existing_user.username:
                errors.append("Cannot change username")
        else:
            # If creating a new user, validate username format
            if not user_data.get("username") or not user_data["username"].strip():
                errors.append("Username must be a valid value")
            elif not re.match(r"^[a-zA-Z0-9]+$", user_data["username"].strip()):
                errors.append("Username must only contain letters, numbers, and underscores")
            elif User.objects.filter(username=User.username).exists():
                errors.append("Username already exists")

        # Email validation
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not user_data["email"] or not re.match(email_regex, user_data["email"]):
            errors.append("Email must be a valid value")

        # Role validation
        if not user_data["role"] or user_data["role"] not in ["Admin", "Instructor", "TA"]:
            errors.append("Role must be a valid value")

        # First name and Last name validation
        name_regex = r"^[a-zA-Z]+(?:[ '-][a-zA-Z]+)*$"
        if not user_data["first_name"] or not re.match(name_regex, user_data["first_name"]):
            errors.append("First name must be a valid value")
        if not user_data["last_name"] or not re.match(name_regex, user_data["last_name"]):
            errors.append("Last name must be a valid value")

        # Skills validation
        skills = user_data.get("skills", [])
        if isinstance(skills, str):
            skills = [skills.strip()]
        elif not isinstance(skills, list):
            errors.append("Skills must be a valid value")
            skills = []
        print("skills", skills)
        for skill in skills:
            if not skill:
                errors.append("Skill must be a valid value")
        if not skills or any(
                not re.match(r"^[a-zA-Z0-9,-]+$", skill.strip()) for skill in skills if skill.strip()):
            errors.append("Skills must be a valid value")
        # Phone validation
        phone_regex = r"^\d{10}$"  # Check for a valid 10-digit phone number
        if not user_data["phone"] or not re.match(phone_regex, user_data["phone"]):
            errors.append("Phone must be a valid 10-digit value")

        # Address validation
        address_regex = r"^[a-zA-Z0-9\s,.\-/]+$"
        if not user_data.get("address") or not user_data["address"].strip() or not re.match(address_regex,
            user_data["address"]): errors.append("Address must be a valid value")


        print("Validation Errors:", errors)


        return errors

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
            if request.user.username == username:
                return redirect(reverse("user-form", kwargs={"username": username}))

            UserController.deleteUser(username, request.user)
        return redirect(reverse("home"))