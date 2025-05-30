from django.urls import path
from . import views

urlpatterns = [
    path('api/generate-code/', views.generate_code, name='generate_code'),
    path('push-code-to-github/', views.push_code_to_github, name='push_code_to_github'),
]
