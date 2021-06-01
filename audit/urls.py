from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('audit/', views.audit, name="audit"),
    path('export/', views.export_csv, name="export"),

]
