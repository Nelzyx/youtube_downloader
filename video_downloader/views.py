import os
import threading
import yt_dlp
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import DownloadTask
from django.http import JsonResponse

@login_required
def index(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        format_type = request.POST.get('format_type')
        resolution = request.POST.get('resolution')
        
        task = DownloadTask.objects.create(
            user=request.user,
            url=url,
            format_type=format_type,
            resolution=resolution
        )
        
        # Запускаем загрузку в фоновом потоке
        thread = threading.Thread(target=download_video, args=(task.id,))
        thread.daemon = True
        thread.start()
        
        messages.info(request, 'Загрузка начата. Обновите страницу для проверки статуса.')
        return redirect('download', task_id=task.id)
    
    return render(request, 'video_downloader/index.html')

@login_required
def download_status(request, task_id):
    task = DownloadTask.objects.get(id=task_id, user=request.user)
    return render(request, 'video_downloader/download.html', {'task': task})

def download_video(task_id):
    task = DownloadTask.objects.get(id=task_id)
    try:
        # Создаем папку для загрузок пользователя, если ее нет
        user_dir = os.path.join(settings.MEDIA_ROOT, 'downloads', str(task.user.id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Получаем информацию о видео
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(task.url, download=False)
            original_filename = ydl.prepare_filename(info)
            base, ext = os.path.splitext(original_filename)
            
            # Формируем имя файла
            if task.format_type == 'audio':
                ext = '.mp3'
            final_filename = os.path.join(user_dir, f"{os.path.basename(base)}{ext}")
            
            # Проверяем существование файла
            counter = 1
            while os.path.exists(final_filename):
                final_filename = os.path.join(user_dir, f"{os.path.basename(base)} ({counter}){ext}")
                counter += 1

        # Настройки загрузки
        ydl_opts = {
            'outtmpl': final_filename.replace(ext, '.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [lambda d: progress_hook(d, task)],
        }

        if task.format_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': 'mp3',
            })
        else:
            ydl_opts['format'] = get_video_format(task.resolution)

        # Загрузка
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([task.url])

        task.status = 'completed'
        task.file_path = os.path.relpath(final_filename, settings.MEDIA_ROOT)
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

@login_required
def download_file(request, task_id):
    task = DownloadTask.objects.get(id=task_id, user=request.user)
    if task.status == 'completed' and task.file_path:
        file_path = os.path.join(settings.MEDIA_ROOT, task.file_path)
        if os.path.exists(file_path):
            from django.http import FileResponse
            return FileResponse(open(file_path, 'rb'), as_attachment=True)
    messages.error(request, 'Файл не найден или загрузка не завершена')
    return redirect('download', task_id=task.id)
