from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('sumRecord/', views.sumRecord, name="sumRecord"),
]
