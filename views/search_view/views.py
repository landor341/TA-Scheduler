from django.shortcuts import render
from django.views import View

from core.user_controller.UserController import UserController
from core.course_controller.CourseController import CourseController
from core.semester_controller.SemesterController import SemesterController


class SearchView(View):
    def get(self, request, type: str):
        """
        Preconditions:
        - `request` is a valid HttpRequest object.
        - `type` is a string indicating the search type ("course" or "user").

        Postconditions:
        - If type is "course", all courses grouped by semester are displayed.
        - If type is "user", an empty or initialized user search context is displayed.

        Side-effects:
        - Retrieves all courses and semesters for course type.
        - Initializes search results for user type.

        Returns:
        - Renders the 'search_view/search_view.html' template with appropriate context:
          * `search_results`: List of courses or users.
          * `semesters`: List of all semesters (if type is "course").
        """
        context = {
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'isAdmin': request.user.role == 'Admin',
            "type": type,
        }

        if type == "course":
            context["search_results"] = []
            context["semesters"] = SemesterController.list_semester()
            for semester in SemesterController.list_semester():
                semester_courses = CourseController.search_courses("", semester.semester_name)
                context["search_results"].append({
                    "semester": semester.semester_name,
                    "courses": semester_courses,
                })
        return render(request, 'search_view/search_view.html', context)

    def post(self, request, type: str):
        """
        Preconditions:
        - `request` is a valid HttpRequest object with POST data containing:
          * `query` (optional): The search string.
          * `semester_name` (optional): The semester name for filtering courses.
        - `type` is a string indicating the search type ("course" or "user").

        Postconditions:
        - Processes the search query and returns filtered results:
          * Users matching the search query (for "user" type).
          * Courses matching the search query, optionally filtered by semester (for "course" type).

        Side-effects:
        - Calls `UserController.searchUser` for user search.
        - Calls `CourseController.search_courses` for course search.

        Returns:
        - Renders the 'search_view/search_view.html' template with appropriate context:
          * `search_results`: List of matching courses or users.
          * `semesters`: List of all semesters.
          * `query`: The search query (if provided).
          * `selected_semester`: The selected semester (if provided).
        """
        query = request.POST.get("query", "")
        semester_name = request.POST.get("semester_name", None)

        if type == "user":
            return render(request, 'search_view/search_view.html', {
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                'isAdmin': request.user.role == 'Admin',
                "type": type,
            })
        elif type == "course":
            search_results = []
            if semester_name:
                search_results.append({
                    "semester": semester_name,
                    "courses": CourseController.search_courses(query, semester_name),
                })
            else:
                for semester in SemesterController.list_semester():
                    semester_courses = CourseController.search_courses(query, semester.semester_name)
                    search_results.append({
                        "semester": semester.semester_name,
                        "courses": semester_courses,
                    })
        else:
            search_results = []

        return render(request, 'search_view/search_view.html', {
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'isAdmin': request.user.role == 'Admin',
            "type": type,
            "search_results": search_results,
            "semesters": SemesterController.list_semester(),
            "query": query,
            "selected_semester": semester_name,
        })