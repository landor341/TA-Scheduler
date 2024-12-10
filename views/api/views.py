from django.http import JsonResponse

from core.user_controller.UserController import UserController


def search_user_api(request):
    query = request.GET.get("query", "").strip() if request.GET.get("query", "").strip() else ""
    try:
        users = UserController.searchUser(query)
        user_data = [{"username": user.username, "name": user.name} for user in users]
        return JsonResponse(user_data, safe=False)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)