"""
URL configuration for lkprofessionals project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.conf import settings
from django.urls import include, path
from django.views.static import serve

from pages import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('assets/<path:path>', serve, {'document_root': settings.BASE_DIR / 'static' / 'assets'}),
    path('partials/<path:partial_path>', views.partial, name='partial'),
    path('', include('pages.urls')),
]
