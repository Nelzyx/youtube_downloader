from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('download/<int:task_id>/', views.download_status, name='download'),
    path('download-file/<int:task_id>/', views.download_file, name='download_file'),
]
