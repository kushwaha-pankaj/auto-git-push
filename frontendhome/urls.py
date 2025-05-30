from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.profile, name='dashboard'),
    path('api/user-info/', views.user_info, name='user_info'),
    
    # github auto push code
    path('select-repository/', views.repository_select_view, name='select_repository'),
    path('save-selected-repo/', views.save_selected_repo, name='save_selected_repo'),
    path('auto-settings/', views.auto_settings_view, name='auto_settings'),
    path('auto-settings/save/', views.save_auto_settings, name='save_auto_settings'),
    path('load_push_history/', views.load_push_history, name='load_push_history'),
    
    # toggle button for auto push
    path('get_auto_push_state/', views.get_auto_push_state, name='get_auto_push_state'),
    path('update_auto_push_state/', views.update_auto_push_state, name='update_auto_push_state'),
    
    # code generation and push progress
    path('get_push_progress/', views.get_push_progress, name='get_push_progress'),
    
]