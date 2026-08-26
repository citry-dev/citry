from django.urls import include, path
from project_explorer.citry_app import citry_app
from project_explorer.views import home

from citry.contrib.django import urlpatterns as citry_urlpatterns

urlpatterns = [
    path("", home, name="home"),
    path(
        "citry/",
        include(citry_urlpatterns(citry_app, prefix="/citry")),
    ),
]
