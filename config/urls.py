"""
URL configuration for nivetha_pm project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('core.urls')),
    path('panel/', admin.site.urls),
]

