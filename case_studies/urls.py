from django.urls import path

from . import public


urlpatterns = [
    path('', public.case_studies, name='case_studies'),
    path('<slug:slug>/', public.case_study_detail, name='case_study_detail'),
]
