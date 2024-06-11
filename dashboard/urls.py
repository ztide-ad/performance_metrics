from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('user_issues/', views.user_issues, name='user_issues'),
    path('', views.home, name='home'),
]
