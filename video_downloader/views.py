import os
import threading
import yt_dlp
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from .models import DownloadTask
from django.http import JsonResponse, FileResponse

def index(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        quality = request.POST.get('quality', '720p')
        task = DownloadTask.objects.create(url=url, quality=quality, status='pending')
        threading.Thread(target=download_video, args=(task.id,)).start()
        return redirect('index')
    
    tasks = DownloadTask.objects.all()
    return render(request, 'video_downloader/index.html', {'tasks': tasks})

def download_status(request, task_id):
    task = get_object_or_404(DownloadTask, id=task_id)
    return render(request, 'video_downloader/download.html', {'task': task})

def download_video(task_id):
    task = DownloadTask.objects.get(id=task_id)
    try:
        download_dir = os.path.join('downloads')
        os.makedirs(download_dir, exist_ok=True)
        
        ydl_opts = {
            'outtmpl': 'media/downloads/%(title)s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(task.url, download=False)
            
            # Определяем формат
            if 'entries' in info:  # Для плейлистов
                info = info['entries'][0]
            
            # Сохраняем формат перед скачиванием
            task.format = info.get('ext', 'mp4')  # По умолчанию mp4
            task.save()
            
            # Начинаем скачивание
            ydl.download([task.url])
            
            # Обновляем информацию после скачивания
            task.status = 'completed'
            task.file_path = f"media/downloads/{info['title']}.{task.format}"
            task.save()
            
            
    except Exception as e:
        task.status = 'failed'
        task.error_message = str(e)
        task.save()

def progress_hook(d, task):
    if d['status'] == 'downloading':
        task.status = f"downloading {d.get('_percent_str', '0%')}"
        task.save()

def get_video_format(resolution):
    formats = {
        "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
        "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
        "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
        "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]",
    }
    return formats.get(resolution, "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]")

def download_file(request, task_id):
    task = get_object_or_404(DownloadTask, id=task_id)  # Убрали проверку пользователя
    
    if task.status == 'completed' and task.file_path:
        try:
            return FileResponse(open(task.file_path, 'rb'), as_attachment=True)
        except FileNotFoundError:
            task.status = 'failed'
            task.error_message = "Файл не найден"
            task.save()
    
    return redirect('index')