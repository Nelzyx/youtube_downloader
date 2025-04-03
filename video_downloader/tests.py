from django.test import TestCase
from django.contrib.auth.models import User
from .models import DownloadTask

class DownloadTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_task_creation(self):
        task = DownloadTask.objects.create(
            user=self.user,
            url='https://youtube.com/watch?v=dQw4w9WgXcQ',
            format_type='video',
            resolution='1080p'
        )
        self.assertEqual(str(task), 'https://youtube.com/watch?v=dQw4w9WgXcQ - Видео')
        