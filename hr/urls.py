from django.urls import path

from . import public



urlpatterns = [
    path("careers/apply/", public.apply_for_job, name="apply_for_job"),
]
