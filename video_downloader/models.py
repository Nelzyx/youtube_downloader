from django.db import models

class DownloadTask(models.Model):
    url = models.URLField(max_length=500)
    format_type = models.CharField(max_length=10, choices=[('video', 'Видео'), ('audio', 'Аудио')])
    format = models.CharField(max_length=10, blank=True)
    quality = models.CharField(max_length=20, default='720p')
    resolution = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.url} - {self.get_format_type_display()}"
    