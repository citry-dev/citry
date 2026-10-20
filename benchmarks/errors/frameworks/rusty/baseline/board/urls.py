from django.urls import path

from . import views

urlpatterns = [
    path('', views.page, name='page'),
    path('save/', views.save, name='save'),
    path('about/', views.about, name='about'),
    path('projects/<int:project_id>/', views.project, name='project'),
]
