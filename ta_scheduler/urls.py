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
from views.login import Login, Logout
from views.profile_view import ProfileView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', ProfileView.as_view(), name='home'),  # Root
    path('login/', Login.as_view(), name='login'),  # Login Page
    path('profile/<str:username>', ProfileView.as_view(), name='profile'),  # Profile-view
    path('logout/', Logout.as_view(), name='logout'),  # LogOut
]
