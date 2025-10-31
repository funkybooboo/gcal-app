from django.urls import path
from . import views

urlpatterns = [
    path("auth/init", views.auth_init, name="auth_init"),
    path("auth/callback", views.auth_callback, name="auth_callback"),
    path("auth/status", views.auth_status, name="auth_status"),
    path("auth/logout", views.auth_logout, name="auth_logout"),
    path("events", views.list_events, name="list_events"),
    path("calendars", views.list_calendars, name="list_calendars"),
]
