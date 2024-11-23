from ta_scheduler.models import User
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.db import models

class UserController:
    def getUser(self, username):
        """

        Preconditions: user_id is a valid id matching a record of a user in the Users table.

        Postconditions: Retrieves the user with id of user_id, along with a list of the courses associated with the user. If the user
        is a TA then any assignments are also returned embedded into their courses, if the user is an instructor/administrator
        then any sections they teach are returned embedded into their courses.

        Side-effects: none.

        Parameters:

        User_id: an id matching a user_id stored in the Users table.

        Returns: List of Courses, CourseSections, and LabSections linked to the specified user.
        """
        pass

    @staticmethod
    def saveUser(user_data, requesting_user):
        """
        Preconditions: user_data contains valid information for the user fields.
        Postconditions: Adds a new user record if no id is provided to the Users table or updates the user’s information
        that has a matching id to the one provided as the argument.
        Raises an error if id is invalid or any part of the user_data is invalid.
        Side-effects: Inserts or updates a record in the Users table.
        Parameters:
        user_data: A dictionary object with the appropriately ordered sequence and data type to match the required fields
        defined in the Users model.
        requesting_user: The user making the request.
        Returns: User instance if successful, otherwise raises an exception.
        """
        required_fields = ['username', 'role']
        for field in required_fields:
            if field not in user_data:
                raise ValidationError(f"Error: '{field}' field is required")

        if not hasattr(requesting_user, 'username'):
            raise ValidationError("Error: 'requesting_user' field is required")

        user_to_edit = None
        if 'id' in user_data:
            try:
                user_to_edit = User.objects.get(id=user_data['id'])
            except User.DoesNotExist:
                raise ObjectDoesNotExist("Error: User with the provided ID does not exist")
        else:
            user_to_edit = User()

        if requesting_user.role == 'Admin':
            if user_to_edit.id == requesting_user.id:
                # Admin editing their own details
                if 'role' in user_data and user_data['role'] != user_to_edit.role:
                    raise PermissionDenied("Admins cannot change their own role.")
            else:
                # Prevent Admin from changing the role of other Admins
                if user_to_edit.role == 'Admin':
                    raise PermissionDenied("Admins cannot change roles for other admins.")
                user_to_edit.role = user_data.get('role', user_to_edit.role)
        else:
            # Only Admins are allowed to change user roles
            if 'role' in user_data and user_data['role'] != user_to_edit.role:
                raise PermissionDenied("Only Admins are allowed to change user roles.")

        user_to_edit.password = user_data.get('password', user_to_edit.password)
        user_to_edit.first_name = user_data.get('first_name', user_to_edit.first_name)
        user_to_edit.last_name = user_data.get('last_name', user_to_edit.last_name)
        new_username = user_data.get('username', user_to_edit.username)
        user_to_edit.office_hours = user_data.get('office_hours', user_to_edit.office_hours)

        existing_user_with_username = User.objects.filter(username=new_username).exclude(id=user_to_edit.id).first()
        if existing_user_with_username:
            raise ValidationError("Error: A user with that username already exists.")

        new_email = user_data.get('email', user_to_edit.email)
        existing_user_with_email = User.objects.filter(email=new_email).exclude(id=user_to_edit.id).first()
        if existing_user_with_email:
            raise ValidationError("Error: A user with that email already exists.")

        user_to_edit.username = new_username
        user_to_edit.email = new_email

        try:
            user_to_edit.full_clean()
            user_to_edit.save()
            return user_to_edit
        except ValidationError as e:
            raise ValidationError(f"Invalid user data: {e}")

    @staticmethod
    def deleteUser(username):
        if not username:  # Check just for empty strings
            raise ValueError("Invalid username: cannot be empty")

        try:
            user_to_delete = User.objects.get(username=username)
            user_to_delete.delete()
        except User.DoesNotExist:
            raise ValueError("User not found")
        """
         Preconditions: id provided must be a valid user id.

         Postconditions: Deletes the user with the matching id as the specified id. If no matching records are found,
         nothing happens.

         Side-effects: Removes a record from the Users table.

            Parameters:
             Id: Integer value for the user id of the user to be deleted.

         Returns: none
         """

    def searchUser(user_search_string):

        """
        Preconditions: N/A

        Postconditions: Returns a list of users matching the search criteria or an error if the string is empty or
            formatted inappropriately. User does not get any contact information they do not have permission to see to.

        Side-effects: none

        Parameters:

            User_search_string: String containing valid search parameters in the proper format.

        Returns: a list of matching user objects, containing only the info needed to populate the explore page.
        """
        if not user_search_string:  # Check for empty strings
            raise ValueError("Invalid search: string cannot be empty")

        #This is a case-insensitive search
        matching_users = User.objects.filter(
            models.Q(username__icontains=user_search_string) |
            models.Q(first_name__icontains=user_search_string) |
            models.Q(last_name__icontains=user_search_string)
        )

        for user in matching_users:
            print(f"Username: {user.username}, First Name: {user.first_name}, Last Name: {user.last_name}")

        return matching_users
