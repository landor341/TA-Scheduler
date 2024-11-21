



class UserController:
    def getUser(self):
        """
        Preconditions: id must be a valid user id.

        Postconditions: Retrieves and returns user details by user_id. If id is invalid, returns an error message.

        Side-effects: none

        Parameters:

        Id: Integer value of the id of the user to search for.

        Returns: User object from Users with matching user_id and all values corresponding to the fields that are defined in the Users model.
        """
        pass

    def saveUser(self, user):
        """
        Preconditions: userData contains valid information for the user fields. If an id is provided, it is a valid id.

        Postconditions: Adds a new user record if no id is provided to the Users table or updates the user’s information that has a matching id to the one provided as the argument.
        Returns an error message if id is invalid or any part of the userData is invalid.

        Side-effects: Inserts or updates a record in the Users table.

        Parameters:

        UserData: A dictionary object with the appropriately ordered sequence and data type to match the required fields defined in the Users model.

        Returns: none
        """
        pass

    def deleteUser(self, id):
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

        Postconditions: Returns a list of users matching the search criteria or an error if the string is empty or formatted inappropriately.

        Side-effects: none

        Parameters:

        User_search_string: String containing valid search parameters in the proper format.

        Returns: a list of matching user objects.
        """
        pass