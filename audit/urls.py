from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.audit, name="audit"),
    path('audit/', views.audit, name="audit"),
    path('export/', views.export_csv, name="export"),
    path('import/', views.importFile, name="import"),

]
