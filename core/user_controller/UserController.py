from core.local_data_classes import UserProfile


class UserController:
    def getUser(self, username) -> UserProfile:
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
    # These 2 methods are from the old userService class.  If we want them we can implement them.
    # def saveUser(self, user):
    #     """
    #     Preconditions: userData contains valid information for the user fields. If an id is provided, it is a valid id.
    #
    #     Postconditions: Adds a new user record if no id is provided to the Users table or updates the user’s information that has a matching id to the one provided as the argument.
    #     Returns an error message if id is invalid or any part of the userData is invalid.
    #
    #     Side-effects: Inserts or updates a record in the Users table.
    #
    #     Parameters:
    #
    #     UserData: A dictionary object with the appropriately ordered sequence and data type to match the required fields defined in the Users model.
    #
    #     Returns: none
    #     """
    #     pass
    #
    def deleteUser(self, username):
        """
         Preconditions: id provided must be a valid user id.

         Postconditions: Deletes the user with the matching id as the specified id. If no matching records are found, nothing happens.

         Side-effects: Removes a record from the Users table.

            Parameters:
             Id: Integer value for the user id of the user to be deleted.

         Returns: none
         """
        pass

    def searchUser(user_search_string):
        """

        Preconditions: N/A

        Postconditions: Returns a list of users matching the search criteria or an error if the string is empty or formatted inappropriately. User does not get any contact information they do not have permission to see to.

        Side-effects: none

        Parameters:

            User_search_string: String containing valid search parameters in the proper format.

        Returns: a list of matching user objects, containing only the info needed to populate the explore page.


        """
        pass