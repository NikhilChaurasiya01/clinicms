from django.contrib.auth import logout
from django.shortcuts import redirect

class AutoLogoutOnHomeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and visits dashboard
        if request.user.is_authenticated and request.path == '/':
            logout(request)  # destroys session immediately
            return redirect('public_dashboard')
        return self.get_response(request)
