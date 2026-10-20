from django.urls import path

from . import views

urlpatterns = [
    path('', views.page, name='page'),
    path('save/', views.save, name='save'),
]
