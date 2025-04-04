from django.urls import path
from video_downloader import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('download/<int:task_id>/', views.download_status, name='download'),
    path('download-file/<int:task_id>/', views.download_file, name='download_file'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)