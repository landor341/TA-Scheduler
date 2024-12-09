"""
URL configuration for ta_scheduler project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from views.course_form import CourseForm
from views.course_view import CourseView
from views.login import Login, Logout
from views.profile_view import ProfileView
from views.section_form.views import SectionForm
from views.user_form import UserForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', ProfileView.as_view(), name='home'),  # Root
    path('login/', Login.as_view(), name='login'),  # Login Page
    path('course/<str:course_code>/<str:semester_name>/', CourseView.as_view(), name='course_view'), #selected_course view\


    path('profile/<str:username>', ProfileView.as_view(), name='profile'),  # Profile-view
    path('create-user/<str:username>/', UserForm.as_view(), name="user-form"),  # User-form
    path('create-user/', UserForm.as_view(), name="user-creator"),  # User-form
    path('logout/', Logout.as_view(), name='logout'),  # LogOut
   # path('edit-course/<str:code>/<str:semester>/', CourseForm.as_view(), name='course-form'),  # Course-form
    path('create-course/', CourseForm.as_view(), name='course-creator'),  # Course-form
    path('edit-course/<str:code>/<str:semester>/<str:section_number>', SectionForm.as_view(), name='section-form'),  # Section-form
    path('create-section/<str:code>/<str:semester>', SectionForm.as_view(), name='section-creator'),  # Section-form
]
