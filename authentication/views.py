from django.shortcuts import render, redirect

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Replace 'dashboard' with your actual dashboard URL name
    return render(request, 'frontend/authlogin.html')
