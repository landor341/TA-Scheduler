from django.shortcuts import render
from django.views import View

from core.user_controller.UserController import UserController
from core.course_controller.CourseController import CourseController
from ta_scheduler.models import Semester


class SearchView(View):
    def get(self, request, type: str):
        """
        GET request is used to initialize the page:
        - If type is "course", all courses are displayed.
        - If type is "user", display prompt information or empty content.
        """
        context = {
            'full_name': f"{request.user.first_name} {request.user.last_name}",
            'isAdmin': request.user.role == 'Admin',
            "type": type,
            "search_results": [],
        }

        if type == "course":
            context["semesters"] = Semester.objects.all()
            for semester in Semester.objects.all():
                semester_courses = CourseController.search_courses("", semester.semester_name)
                context["search_results"].append({
                    "semester": semester.semester_name,
                    "courses": semester_courses,
                })
        else:
            context["search_results"] = UserController.searchUser("")
        return render(request, 'search_view/search_view.html', context)

    def post(self, request, type: str):
        """
        POST requests are used to handle search requests:
        - Call UserController or CourseController based on type to search.
        - If it is a course, it also supports filtering by semester.
        """
        query = request.POST.get("query", "")
        semester_name = request.POST.get("semester_name", None)

        if type == "user":
            try:
                search_results = UserController.searchUser(query)
            except ValueError as e:
                return render(request, 'search_view/search_view.html', {
                    'full_name': f"{request.user.first_name} {request.user.last_name}",
                    'isAdmin': request.user.role == 'Admin',
                    "type": type,
                    "error": str(e),
                    "search_results": [],
                    "semesters": Semester.objects.all(),
                })
        elif type == "course":
            search_results = []
            if semester_name:
                search_results.append({
                    "semester": semester_name,
                    "courses": CourseController.search_courses(query, semester_name),
                })
            else:
                for semester in Semester.objects.all():
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
            "semesters": Semester.objects.all(),
            "query": query,
            "selected_semester": semester_name,
        })