"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('landingpage.urls')),  # Landing page URLs
    path('', include('authentication.urls')),  # Authentication URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('blog/', views.load_blog, name='blog'),
    path('settings/', views.load_settings, name='settings'),
    path('reports/', views.load_reports, name='reports'),
    path('reports/monthly/', views.load_monthly_reports, name='monthly_reports'),
    path('reports/annual/', views.load_annual_reports, name='annual_reports'),
    path('reports/custom/', views.load_custom_reports, name='custom_reports'),
]


