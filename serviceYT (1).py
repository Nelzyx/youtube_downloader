import sys
import os
import threading
import platform
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QMessageBox
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QFileDialog, QLabel, QComboBox, QGroupBox,
    QMessageBox, QProgressBar
)
from PyQt5.QtCore import QSettings, pyqtSignal, QObject
import yt_dlp

class DownloadSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    message = pyqtSignal(str, str)
    progress = pyqtSignal(dict)

class VideoDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("VideoDownloader", "Settings")
        self.download_thread = None
        self.stop_flag = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Video Downloader')
        self.setFixedSize(600, 280)

        layout = QVBoxLayout()

        # URL input
        self.url_label = QLabel('Введите ссылку на видео:')
        layout.addWidget(self.url_label)
        self.url_input = QLineEdit(self)
        layout.addWidget(self.url_input)

        # Path selection
        self.path_label = QLabel('Выберите каталог для сохранения:')
        layout.addWidget(self.path_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self)
        self.path_input.setText(self.settings.value("save_path", ""))
        path_layout.addWidget(self.path_input)
        
        self.browse_button = QPushButton('...', self)
        self.browse_button.setFixedWidth(30)
        self.browse_button.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.browse_button)
        layout.addLayout(path_layout)

        # Parameters
        parameters_group = QGroupBox("Параметры")
        parameters_layout = QHBoxLayout()

        # Format selection
        self.format_label = QLabel('Формат:')
        parameters_layout.addWidget(self.format_label)
        
        self.format_combo = QComboBox(self)
        self.format_combo.addItems(["Видео", "Аудио"])
        self.format_combo.currentIndexChanged.connect(self.update_resolution_options)
        parameters_layout.addWidget(self.format_combo)

        # Resolution selection
        self.resolution_label = QLabel('Разрешение:')
        parameters_layout.addWidget(self.resolution_label)
        
        self.resolution_combo = QComboBox(self)
        parameters_layout.addWidget(self.resolution_combo)
        
        parameters_group.setLayout(parameters_layout)
        layout.addWidget(parameters_group)

        # Progress area
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.progress_info = QLabel('Готов к загрузке')
        self.progress_info.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.progress_info)

        self.speed_info = QLabel('')
        layout.addWidget(self.speed_info)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.download_button = QPushButton('Скачать', self)
        self.download_button.clicked.connect(self.start_download)
        buttons_layout.addWidget(self.download_button)

        self.stop_button = QPushButton('Остановить', self)
        self.stop_button.clicked.connect(self.stop_download)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)
        self.update_resolution_options()

        # Signals
        self.download_signals = DownloadSignals()
        self.download_signals.finished.connect(self.on_download_finished)
        self.download_signals.error.connect(self.show_error)
        self.download_signals.message.connect(self.show_message)
        self.download_signals.progress.connect(self.update_progress)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Выберите каталог')
        if directory:
            self.path_input.setText(directory)
            self.settings.setValue("save_path", directory)

    def update_resolution_options(self):
        self.resolution_combo.clear()
        if self.format_combo.currentText() == "Видео":
            self.resolution_combo.addItems(["1080p", "720p", "480p", "360p"])
        else:
            self.resolution_combo.addItems(["128kbps", "192kbps", "256kbps"])

    def set_ui_enabled(self, enabled):
        """Блокирует/разблокирует элементы интерфейса"""
        self.url_input.setEnabled(enabled)
        self.path_input.setEnabled(enabled)
        self.browse_button.setEnabled(enabled)
        self.format_combo.setEnabled(enabled)
        self.resolution_combo.setEnabled(enabled)
        self.download_button.setEnabled(enabled)
        self.stop_button.setEnabled(not enabled)

    def start_download(self):
        self.stop_flag = False
        self.set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.progress_info.setText("Подготовка к загрузке...")
        self.speed_info.setText("")
        self.download_thread = threading.Thread(target=self.download_video, daemon=True)
        self.download_thread.start()

    def stop_download(self):
        self.stop_flag = True
        self.progress_info.setText("Остановка загрузки...")

    def download_video(self):
        url = self.url_input.text()
        save_path = self.path_input.text()
        format_type = self.format_combo.currentText()
        resolution = self.resolution_combo.currentText()

        if not url or not save_path:
            self.download_signals.error.emit("Пожалуйста, заполните все поля.")
            return

        try:
            # Сначала получаем информацию о видео без скачивания
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                original_filename = ydl.prepare_filename(info)
                base, ext = os.path.splitext(original_filename)
                
                # Формируем окончательное имя файла
                if format_type == "Аудио":
                    ext = ".mp3"  # Для аудио всегда используем .mp3
                final_filename = os.path.join(save_path, f"{os.path.basename(base)}{ext}")
                
                # Проверяем существование файла и генерируем новое имя при необходимости
                counter = 1
                while os.path.exists(final_filename):
                    final_filename = os.path.join(save_path, f"{os.path.basename(base)} ({counter}){ext}")
                    counter += 1

            # Настройки для скачивания
            ydl_opts = {
                'outtmpl': final_filename.replace(ext, '.%(ext)s'),  # Шаблон для yt-dlp
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self.progress_hook],
            }

            if format_type == "Аудио":
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                })
            else:
                ydl_opts['format'] = self.get_video_format(resolution)

            # Запускаем скачивание
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.download_signals.message.emit(
                "Готово!", 
                f"{'Аудио' if format_type == 'Аудио' else 'Видео'} скачано:\n{os.path.basename(final_filename)}"
            )

        except Exception as e:
            error_msg = str(e)
            if 'Requested format is not available' in error_msg:
                error_msg = "Выбранный формат недоступен. Попробуйте другое качество."
            self.download_signals.error.emit(f"Ошибка: {error_msg}")
        finally:
            self.download_signals.finished.emit()

    def progress_hook(self, d):
        if self.stop_flag:
            raise Exception("Загрузка остановлена пользователем")
        
        if d['status'] == 'downloading':
            progress_data = {
                'percent': d.get('_percent_str', '0%'),
                'speed': d.get('_speed_str', 'N/A'),
                'downloaded': d.get('_downloaded_bytes_str', '0'),
                'total': d.get('_total_bytes_str', '?')
            }
            self.download_signals.progress.emit(progress_data)

    def update_progress(self, progress_data):
        try:
            percent = progress_data['percent'].strip('%')
            self.progress_bar.setValue(int(float(percent)))
            
            status_text = f"Загружено: {progress_data['downloaded']}"
            if progress_data['total'] != '?':
                status_text += f" из {progress_data['total']}"
            
            self.progress_info.setText(status_text)
            self.speed_info.setText(f"Скорость: {progress_data['speed']} | Прогресс: {progress_data['percent']}")
        except:
            pass

    def get_video_format(self, resolution):
        # Возвращаем форматы, не требующие FFmpeg для обработки
        return {
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
            "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
            "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]",
        }.get(resolution, "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]")

    def on_download_finished(self):
        self.set_ui_enabled(True)
        self.progress_info.setText("Загрузка завершена")
        self.speed_info.setText("")

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)
        self.set_ui_enabled(True)
        self.progress_info.setText("Ошибка загрузки")
        self.speed_info.setText("")

    def show_message(self, title, message):
        QMessageBox.information(self, title, message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoDownloader()
    ex.show()
    sys.exit(app.exec_())