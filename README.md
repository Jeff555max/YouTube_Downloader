# Video Downloader

Десктоп приложение для загрузки видео с YouTube, RuTube и VK Video. Написано на Python + PyQt6.

## Возможности

- Загрузка видео с **YouTube**, **RuTube**, **VK Video** и 1000+ других сайтов
- Выбор формата: **MP4** (видео) или **MP3** (аудио)
- Выбор разрешения: 144p, 240p, 360p, 480p, 720p, 1080p и выше
- Выбор папки сохранения
- Прогресс-бар со скоростью и ETA
- Работает **без браузера и без VS Code** — запускается ярлыком с рабочего стола

## Запуск готового приложения

Дважды кликните по ярлыку **Video Downloader** на рабочем столе.

Или запустите напрямую:
```
dist\VideoDownloader\VideoDownloader.exe
```

> Папку `dist\VideoDownloader\` не удалять — в ней все необходимые файлы.

## Сборка из исходников

### Требования

- Python 3.10+
- Windows 10/11 64-bit

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск без сборки

```bash
python main.py
```

### Сборка .exe

```bash
python -m PyInstaller --noconfirm --onedir --windowed --name "VideoDownloader" --add-data "downloader.py;." main.py
```

Готовый `.exe` появится в папке `dist\VideoDownloader\`.

### Создание ярлыка на рабочем столе

```bash
powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
```

## Структура проекта

```
YouTube_Downloader/
├── main.py               # GUI (PyQt6)
├── downloader.py         # Логика загрузки (yt-dlp)
├── requirements.txt      # Зависимости
├── create_shortcut.ps1   # Скрипт создания ярлыка
├── VideoDownloader.spec  # Конфиг PyInstaller
└── dist/
    └── VideoDownloader/  # Готовое приложение
        └── VideoDownloader.exe
```

## Зависимости

| Пакет | Назначение |
|-------|-----------|
| PyQt6 | GUI фреймворк |
| yt-dlp | Загрузка видео |
| pyinstaller | Сборка в .exe |

## Примечание про MP3

Для конвертации в MP3 требуется [FFmpeg](https://ffmpeg.org/download.html).  
Скачайте и добавьте в `PATH`, либо положите `ffmpeg.exe` рядом с `VideoDownloader.exe`.

Без FFmpeg приложение скачает аудио в формате `.webm` или `.m4a`.
