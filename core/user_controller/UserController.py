from ta_scheduler.models import User
from django.core.exceptions import ValidationError
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
    def saveUser(user, requesting_user):
         """
         Preconditions: userData contains valid information for the user fields. If an id is provided, it is a valid id.

         Postconditions: Adds a new user record if no id is provided to the Users table or updates the user’s information
         that has a matching id to the one provided as the argument.
         Returns an error message if id is invalid or any part of the userData is invalid.

         Side-effects: Inserts or updates a record in the Users table.

         Parameters:

         UserData: A dictionary object with the appropriately ordered sequence and data type to match the required fields
         defined in the Users model.

         Returns: none
         """
         if 'username' not in user:
             return "Error: 'username' field is required"

         if not hasattr(requesting_user, 'username'):
             return "Error: 'requesting_user' field is required"

         if 'id' in user:  # Update existing user
             try:
                current_user = User.objects.get(id=user['id'])
                if requesting_user.role != 'Admin' and current_user.id != requesting_user.id:
                    return "Error: Only administrators can modify other users"

             except User.DoesNotExist:
                 return "Error: User with the provided ID does not exist"
         else:  # Create new user
             current_user = User()

         # Update user fields
         current_user.role = user.get('role', current_user.role)
         current_user.email = user.get('email', current_user.email)
         current_user.password = user.get('password', current_user.password)
         current_user.first_name = user.get('first_name', current_user.first_name)
         current_user.last_name = user.get('last_name', current_user.last_name)
         current_user.username = user.get('username', current_user.username)
         current_user.office_hours = user.get('office_hours', current_user.office_hours)

         try:
             current_user.full_clean()
             current_user.save()
             return current_user
         except ValidationError:
             raise ValidationError("Invalid user data")

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
