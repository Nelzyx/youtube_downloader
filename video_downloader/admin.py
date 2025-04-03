from django.contrib import admin
from .models import DownloadTask

@admin.register(DownloadTask)
class DownloadTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'url', 'format_type', 'status')
    list_filter = ('status', 'format_type')
    search_fields = ('url', 'user__username')