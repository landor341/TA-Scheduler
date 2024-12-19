from django.http import JsonResponse

from core.user_controller.UserController import UserController


def search_user_api(request, role=None):
    """
    Preconditions:
    - `request` is a valid HttpRequest object.
    - `request.GET` contains an optional "query" parameter, which may be an empty string.
    - `UserController.searchUser` is properly implemented to handle the provided query.

    Postconditions:
    - If a valid query is provided or left empty, a JSON response containing a list of user data (username and name) is returned.
    - If an error occurs (e.g., invalid query), a JSON response with an error message is returned with status 400.

    Side-effects:
    - None.

    Parameters:
    - request: HttpRequest object, containing the GET data with an optional "query" parameter.

    Returns:
    - JsonResponse:
      * On success: A JSON object with a list of users (username and name).
      * On failure: A JSON object with an "error" key and status code 400.
    """
    query = request.GET.get("query", "").strip() if request.GET.get("query", "").strip() else ""
    try:
        print(role)
        if role:
            users = UserController.searchUser(query, role)
        else:
            users = UserController.searchUser(query)
        #convert to dictionary for JSON serialization"
        user_data = [{"username": user.username, "name": user.name} for user in users]
        return JsonResponse(user_data, safe=False)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)