from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.db import models
from django.shortcuts import get_object_or_404
from core.local_data_classes import UserRef, LabSectionRef, UserProfile, PrivateUserProfile, CourseSectionRef, CourseOverview
from ta_scheduler.models import User, Course, CourseSection, LabSection

"""
Helper Methods start with an underscore ______
"""
class UserController:

    @staticmethod
    def getUser(username, requesting_user):
        """
        Preconditions:
        - 'username' must be a non-empty string.
        - 'requesting_user' must be a valid User instance.
        Postconditions: Retrieves the user data with the given username, including courses and their assignments or sections
        based on the user's role. Returns embedded information for TAs and instructors/administrators.
        Side-effects: None.
        Parameters:
        - username: A string representing the username in the Users table.
        - requesting_user: An instance of the User who is making the request.
        Returns: A PrivateUserProfile object if the requesting user is an Admin or accessing their own profile;
                 otherwise, returns a UserProfile object.
        """
        if not isinstance(username, str) or not username:
            raise ValueError("Invalid username: must be a non-empty string")
        if not isinstance(requesting_user, User):
            raise ValueError("Invalid requesting_user: must be a valid User instance")

        user = get_object_or_404(User, username=username)
        course_ids = UserController._get_course_ids_based_on_role(user)
        courses = Course.objects.filter(id__in=course_ids)
        course_overviews = UserController._construct_course_overviews(user, courses)

        return UserController._create_user_profile(user, requesting_user, course_overviews)

    @staticmethod
    def _get_course_ids_based_on_role(user):
        if user.role in ["Instructor", "Admin"]:
            return user.coursesection_set.values_list("course", flat=True)
        elif user.role == "TA":
            return user.tacourseassignment_set.values_list("course", flat=True)
        return []

    @staticmethod
    def _create_user_profile(user, requesting_user, course_overviews):

        skills = user.skills if isinstance(user.skills, list) else []

        if requesting_user.role == 'Admin' or user == requesting_user:
            return PrivateUserProfile(
                name=f"{user.first_name} {user.last_name}".strip(),
                email=user.email,
                role=user.role,
                office_hours=user.office_hours,
                courses_assigned=course_overviews,
                address=user.address,
                phone=user.phone,
                skills=skills
            )
        return UserProfile(
            name=f"{user.first_name} {user.last_name}".strip(),
            email=user.email,
            role=user.role,
            office_hours=user.office_hours,
            courses_assigned=course_overviews,
            skills = skills
        )

    @staticmethod
    def _construct_course_overviews(user, courses):
        course_overviews = []
        for course in courses:
            if user.role in ["Instructor", "Admin"]:
                course_sections = CourseSection.objects.filter(course=course, instructor=user)
                lab_sections = LabSection.objects.filter(course=course)
            elif user.role == "TA":
                course_sections = CourseSection.objects.filter(course=course)
                lab_sections = LabSection.objects.filter(course=course, talabassignment_set__ta=user)

            course_overviews.append(CourseOverview(
                code=course.course_code,
                name=course.course_name,
                semester=course.semester,
                course_sections=UserController._get_course_section_refs(course_sections),
                lab_sections=UserController._get_lab_section_refs(lab_sections),
                ta_list=[]
            ))

        return course_overviews

    @staticmethod
    def _get_course_section_refs(course_sections):
        return [
            CourseSectionRef(
                section_number=str(s.course_section_number),
                instructor=UserRef(name=s.instructor.get_full_name(), username=s.instructor.username)
            )
            for s in course_sections
        ]

    @staticmethod
    def _get_lab_section_refs(lab_sections):
        return [
            LabSectionRef(
                section_number=str(ls.lab_section_number),
                instructor=(
                    UserRef(
                        name=f"{ls.get_ta().first_name} {ls.get_ta().last_name}".strip(),
                        username=ls.get_ta().username
                    ) if ls.get_ta() else None)
            )
            for ls in lab_sections
        ]

    @staticmethod
    def saveUser(user_data, requesting_user):
        """
        Preconditions: user_data contains valid information for the user fields.
        Postconditions: Adds a new user record to the Users table or updates the user’s information
        that has a matching username to the one provided as the argument.
        Raises an error if username is invalid or any part of the user_data is invalid.
        Side-effects: Inserts or updates a record in the Users table.
        Parameters:
        - user_data: A dictionary with user fields required by the Users model.
        - requesting_user: The user instance making the request.
        Returns: A User instance if the process is successful; otherwise, raises an exception.
        """
        if requesting_user.role != "Admin" and user_data["username"] != requesting_user.username:
            raise PermissionDenied(f"Non admins can only edit themselves")

        required_fields = ['username']
        UserController._validate_user_data(user_data, requesting_user, required_fields)
        try:
            user_to_edit = User.objects.get(username=user_data.get('username'))
        except ObjectDoesNotExist:
            required_fields = ['role']
            UserController._validate_user_data(user_data, requesting_user, required_fields)
            user_to_edit = User()
            user_to_edit.username = user_data.get("username")
        UserController._request_permission_check(requesting_user, user_data, user_to_edit)
        UserController._update_user_fields(user_to_edit, user_data)

        try:
            user_to_edit.full_clean(exclude=['password'])
            user_to_edit.save()
            if "skills" in user_data:
                skills = user_data.get("skills")
                if isinstance(skills, list):
                    filtered_skills = [skill for skill in skills if skill.strip()]
                    user_to_edit.skills = filtered_skills
                else:
                    raise ValidationError("Invalid data for skills. It must be a list.")
                user_to_edit.save()
            return user_to_edit
        except ValidationError as e:
            raise ValidationError(f"Invalid user data: {e}")

    @staticmethod
    def _validate_user_data(user_data, requesting_user, required_fields):
        """
        Preconditions: N/A
        Postconditions: Validates the presence of required fields in 'user_data' and checks 'requesting_user'.
        Raises an error if any field is missing or invalid.
        Side-effects: None.
        Parameters:
        - user_data: A dictionary containing potential user field values.
        - requesting_user: User making the request.
        - required_fields: List of fields that must be present in 'user_data'.
        Returns: None.
        """

        for field in required_fields:
            if field not in user_data:
                raise ValidationError(f"Error: '{field}' field is required")

        if not hasattr(requesting_user, 'username'):
            raise ValidationError("Error: 'requesting_user' field is required")

    @staticmethod
    def deleteUser(username, requesting_user):
        """
        Preconditions:
        - 'username' must be a non-empty string representing an existing user.
        - 'requesting_user' must be an admin user to perform this operation.

        Postconditions: Deletes the user with the specified 'username'. Raises an error if no matching user is found or if the requesting user is not an admin.
        Side-effects: Removes the record from the Users table.

        Parameters:
        - username: A string representing the user's username in the Users table.
        - requesting_user: An instance of the User making the request, which must have an admin role.

        Returns: None.
        """
        if not isinstance(username, str) or not username:
            raise ValueError("Invalid username: must be a non-empty string")

        if requesting_user.role != 'Admin':
            raise PermissionDenied("Only administrators can delete users.")

        try:
            user = User.objects.get(username=username)
            user.delete()
        except User.DoesNotExist:
            raise ValueError(f"User {username} does not exist.")

    @staticmethod
    def searchUser(user_search_string="", user_role=None):
        """
        Preconditions: 'user_search_string' can be empty.
        Postconditions: Returns a list of users that match the search criteria and role (if provided)
                        or raises an error if the input is invalid/empty.
        Side-effects: None.
        Parameters:
        - user_search_string: A string containing search parameters for finding users.
        - user_role: Optional role parameter to filter users by a specific role.
        Returns: A list of matching user objects, containing minimal info for displaying in an explore page.
        """

        query = models.Q(username__icontains=user_search_string) | \
                models.Q(first_name__icontains=user_search_string) | \
                models.Q(last_name__icontains=user_search_string)

        if user_role:
            matching_users = User.objects.filter(query, role=user_role)
        else:
            matching_users = User.objects.filter(query)

        return [
            UserRef(name=f"{user.first_name} {user.last_name}", username=user.username)
            for user in matching_users
        ]

    @staticmethod
    def _request_permission_check(requesting_user, user_data, user_to_edit):
        """
        Preconditions: The 'requesting_user' must be an Admin if changes involve user roles.
        Postconditions: Validates permission for the requesting user to modify 'user_data'.
        Raises a Permission Denied error if unauthorized.
        Side-effects: None.
        Parameters:
        - requesting_user: User instance making the request.
        - user_data: Dictionary object containing changes to be made.
        - user_to_edit: User instance being edited.
        Returns: None.
        """
        if requesting_user.role == 'Admin':
            if user_to_edit.username == requesting_user.username and 'role' in user_data and user_data['role'] != user_to_edit.role:
                raise PermissionDenied("Admins cannot change their own role.")

            if user_to_edit.role == 'Admin' and 'role' in user_data and user_data['role'] != user_to_edit.role:
                raise PermissionDenied("Admins cannot change roles for other admins.")
        else:
            if 'role' in user_data and user_data['role'] != user_to_edit.role:
                raise PermissionDenied("Only Admins are allowed to change user roles.")

    @staticmethod
    def _update_user_fields(user, user_data):
        """
        Preconditions: 'user_data' must contain valid field values.
        Postconditions: Updates fields of 'user' with values from 'user_data', excluding unique fields.
        Side-effects: Modifies the 'user' object.
        Parameters:
        - user: User instance being updated.
        - user_data: Dictionary with user field values.
        Returns: None.
        """
        user.password = user_data.get('password', user.password)
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.office_hours = user_data.get('office_hours', user.office_hours)
        user.phone = user_data.get('phone', user.phone)
        user.address = user_data.get('address', user.address)
        UserController._set_unique_fields(user, user_data)

        user.role = user_data.get('role', user.role)

    @staticmethod
    def _set_unique_fields(user, user_data):
        """
        Preconditions: Field values must be unique.
        Postconditions: Validates and sets unique fields (username, email) for the 'user'.
        Raises a ValidationError if duplicates exist.
        Side-effects: Modifies 'user'.
        Parameters:
        - user: User instance being updated.
        - user_data: Dictionary with user field values.
        Returns: None.
        """
        new_username = user_data.get('username', user.username)
        UserController._validate_unique_field(User, 'username', new_username, user.id)
        user.username = new_username
        
        new_email = user_data.get('email', user.email)
        UserController._validate_unique_field(User, 'email', new_email, user.id)
        user.email = new_email

    @staticmethod
    def _validate_unique_field(model, field, value, exclude_id=None):
        """
        Preconditions: The 'model' must be the correct database model.
        Postconditions: Ensures 'value' for 'field' is unique in 'model'. Raises an error if not.
        Side-effects: None.
        Parameters:
        - model: The ORM model to query.
        - field: The field to validate for uniqueness.
        - value: The field value being checked.
        - exclude_id: Optional ID to exclude from check.
        Returns: None.
        """
        query = models.Q(**{field: value})
        if exclude_id:
            query &= ~models.Q(id=exclude_id)
        if model.objects.filter(query).exists():
            raise ValidationError(f"Error: A user with that {field} already exists.")