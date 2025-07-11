"""
URL configuration for AutoGrader project.

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
from grader import views
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('autograder/', include('grader.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/profile/', RedirectView.as_view(url=reverse_lazy('tasks'), permanent= False, query_string=True)),
    path('', RedirectView.as_view(url='accounts/login', permanent= True)),
] +  static(settings.STATIC_URL, document_root=settings.STATIC_URL)
