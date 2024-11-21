from django.shortcuts import render, redirect
from django.views import View

class Profile(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        return render(request, 'profile_view/profile.html', {
            'user': f"{request.user.first_name}, {request.user.last_name}",
            'email': request.user.email,
            'role': request.user.role,
            'phone': request.user.phone,
            'address': request.user.address,
            'office_hours': request.user.office_hours,
        })