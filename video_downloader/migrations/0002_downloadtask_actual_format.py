# Generated by Django 5.2 on 2025-04-04 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_downloader', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='downloadtask',
            name='actual_format',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
