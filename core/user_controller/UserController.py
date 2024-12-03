from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.db import models
from django.shortcuts import get_object_or_404
from core.local_data_classes import UserRef, CourseRef, LabSectionRef, TACourseRef, UserProfile, PrivateUserProfile, \
    CourseSectionRef, CourseOverview
from ta_scheduler.models import User, Course, CourseSection, LabSection, TALabAssignment, TACourseAssignment

"""
Helper Methods start with an underscore ______
"""
class UserController:

    @staticmethod
    def getUser(user_id, requesting_user):
        """
        Preconditions: user_id is a valid id matching a record of a user in the Users table.
        Postconditions: Retrieves the user with id of user_id, along with a list of the courses associated with the user.
        If the user is a TA then any assignments are also returned embedded into their courses,
        if the user is an instructor/administrator then any sections they teach are returned embedded into their courses.
        Side-effects: none.
        Parameters: user_id: an id matching a user_id stored in the Users table.
        Returns: Dictionary containing user, courses, course_sections, lab_sections, lab_assignments, and course_assignments
        linked to the specified user.
        """
        if not isinstance(user_id, int) or not user_id:
            raise ValueError("Invalid user_id: must be a non-empty integer")
        if not isinstance(requesting_user, User):
            raise ValueError("Invalid requesting_user: must be a valid User instance")

        user = get_object_or_404(User, id=user_id)
        course_ids = UserController._get_course_ids_based_on_role(user)
        courses = Course.objects.filter(id__in=course_ids)
        course_overviews = UserController._construct_course_overviews(user, courses)

        return UserController._create_user_profile(user, requesting_user, course_overviews)

    @staticmethod
    def _get_course_ids_based_on_role(user):
        if user.role in["Instructor", "Admin"]:
            return user.coursesection_set.values_list("course", flat=True)
        elif user.role == "TA":
            return user.tacourseassignment_set.values_list("course", flat=True)
        return []

    @staticmethod
    def _create_user_profile(user, requesting_user, course_overviews):
        if requesting_user.role == 'Admin' or user == requesting_user:
            return PrivateUserProfile(
                name=f"{user.first_name} {user.last_name}".strip(),
                email=user.email,
                role=user.role,
                office_hours=user.office_hours,
                courses_assigned=course_overviews,
                address=user.address,
                phone=user.phone
            )
        return UserProfile(
            name=f"{user.first_name} {user.last_name}".strip(),
            email=user.email,
            role=user.role,
            office_hours=user.office_hours,
            courses_assigned=course_overviews
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
                lab_sections=UserController._get_lab_section_refs(lab_sections)
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
        Postconditions: Adds a new user record if no id is provided to the Users table or updates the user’s information
        that has a matching id to the one provided as the argument.
        Raises an error if id is invalid or any part of the user_data is invalid.
        Side-effects: Inserts or updates a record in the Users table.
        Parameters: user_data: A dictionary object with the appropriately ordered sequence and data type to match the required fields defined in the Users model.
                    requesting_user: The user making the request.
        Returns: User instance if successful, otherwise raises an exception.
        """
        required_fields = ['username', 'role']
        UserController._validate_user_data(user_data, requesting_user, required_fields)

        user_to_edit = UserController._get_user_by_id(user_data.get('id')) if 'id' in user_data else User()
        UserController._request_permission_check(requesting_user, user_data, user_to_edit)
        UserController._update_user_fields(user_to_edit, user_data)

        try:
            user_to_edit.full_clean(exclude=['password'])
            user_to_edit.save()
            return user_to_edit
        except ValidationError as e:
            raise ValidationError(f"Invalid user data: {e}")

    @staticmethod
    def _validate_user_data(user_data, requesting_user, required_fields):
        for field in required_fields:
            if field not in user_data:
                raise ValidationError(f"Error: '{field}' field is required")

        if not hasattr(requesting_user, 'username'):
            raise ValidationError("Error: 'requesting_user' field is required")

    @staticmethod
    def deleteUser(user_id):
        """
        Preconditions: id provided must be a valid user id.
        Postconditions: Deletes the user with the matching id as the specified id. If no matching records are found, nothing happens.
        Side-effects: Removes a record from the Users table.
        Parameters: user_id: String value for the user_id of the user to be deleted.
        Returns: None
        """
        if not isinstance(user_id, int) or not user_id:
            raise ValueError("Invalid user_id: must be a non-empty integer")

        try:
            User.objects.get(id=user_id).delete()
        except User.DoesNotExist:
            raise ValueError("User not found")

    @staticmethod
    def searchUser(user_search_string):
        """
        Preconditions: N/A
        Postconditions: Returns a list of users matching the search criteria or an error if the string is empty or formatted inappropriately.
        Side-effects: none
        Parameters: user_search_string: String containing valid search parameters in the proper format.
        Returns: A list of matching user objects, containing only the info needed to populate the explore page.
        """
        if not user_search_string:
            raise ValueError("Invalid search: string cannot be empty")

        matching_users = User.objects.filter(
            models.Q(username__icontains=user_search_string) |
            models.Q(first_name__icontains=user_search_string) |
            models.Q(last_name__icontains=user_search_string)
        )

        return [UserRef(name=f"{user.first_name} {user.last_name}", username=user.username)
                for user in matching_users]

    @staticmethod
    def _get_user_by_id(user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ObjectDoesNotExist("Error: User with the provided ID does not exist")

    @staticmethod
    def _request_permission_check(requesting_user, user_data, user_to_edit):
        if requesting_user.role == 'Admin':
            if user_to_edit.id == requesting_user.id and 'role' in user_data and user_data['role'] != user_to_edit.role:
                raise PermissionDenied("Admins cannot change their own role.")

            if user_to_edit.role == 'Admin' and 'role' in user_data and user_data['role'] != user_to_edit.role:
                raise PermissionDenied("Admins cannot change roles for other admins.")
        else:
            if 'role' in user_data and user_data['role'] != user_to_edit.role:
                raise PermissionDenied("Only Admins are allowed to change user roles.")

    @staticmethod
    def _update_user_fields(user, user_data):
        user.password = user_data.get('password', user.password)
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.office_hours = user_data.get('office_hours', user.office_hours)

        UserController._set_unique_fields(user, user_data)

        user.role = user_data.get('role', user.role)

    @staticmethod
    def _set_unique_fields(user, user_data):
        new_username = user_data.get('username', user.username)
        UserController._validate_unique_field(User, 'username', new_username, user.id)
        user.username = new_username

        new_email = user_data.get('email', user.email)
        UserController._validate_unique_field(User, 'email', new_email, user.id)
        user.email = new_email

    @staticmethod
    def _validate_unique_field(model, field, value, exclude_id=None):
        query = models.Q(**{field: value})
        if exclude_id:
            query &= ~models.Q(id=exclude_id)
        if model.objects.filter(query).exists():
            raise ValidationError(f"Error: A user with that {field} already exists.")