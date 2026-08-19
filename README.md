# Video Downloader

Десктоп приложение для загрузки видео с YouTube, RuTube и VK Video. Написано на Python + PyQt6.

# Пример реализации
- [Демонстрация проекта](https://disk.yandex.ru/i/fprdj8gsGoumMA)

*Нажмите на ссылку для просмотра видео*

## Возможности

- Загрузка видео с **YouTube**, **RuTube**, **VK Video** и 1000+ других сайтов
- Выбор формата: **MP4** (видео) или **MP3** (аудио)
- Выбор разрешения: 144p, 240p, 360p, 480p, 720p, 1080p и выше
- Выбор папки сохранения
- Прогресс-бар со скоростью и ETA
- Работает без браузера — запускается ярлыком с рабочего стола

## Запуск готового приложения

Дважды кликните по ярлыку **Video Downloader** на рабочем столе.

Или запустите напрямую:
```
dist\VideoDownloader\VideoDownloader.exe
```

> Папку `dist\VideoDownloader\` не удалять — в ней все необходимые файлы.

---

## Установка FFmpeg

FFmpeg необходим для:
- Конвертации аудио в **MP3**
- Склейки видео и аудио дорожек при скачивании высоких разрешений (720p, 1080p)

### Способ 1 — автоматически через winget (рекомендуется)

Откройте PowerShell или командную строку и выполните:

```bash
winget install --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
```

После установки скопируйте `ffmpeg.exe` рядом с `VideoDownloader.exe`:

```
dist\VideoDownloader\ffmpeg.exe
```

### Способ 2 — скачать вручную

Скачайте готовую сборку от Gyan.dev (именно эта использовалась при разработке):

**https://github.com/GyanD/codexffmpeg/releases/download/9.0/ffmpeg-9.0-full_build.zip**

Или перейдите на страницу всех релизов:
**https://github.com/GyanD/codexffmpeg/releases**

После скачивания:
1. Распакуйте архив
2. Найдите файл `ffmpeg.exe` в папке `bin\`
3. Скопируйте `ffmpeg.exe` в папку `dist\VideoDownloader\`

> Без FFmpeg приложение скачает видео без звука или аудио в формате `.webm` / `.m4a`.

---

## Устранение возможных проблем

### ❌ ERROR: HTTP Error 403: Forbidden

YouTube заблокировал запрос. Решения:
- Убедитесь что используете последнюю версию приложения
- Попробуйте другое видео для проверки
- Перезапустите приложение и попробуйте снова

### ❌ ERROR: Requested format is not available

Выбранное разрешение недоступно для данного видео. Решения:
- Нажмите **«Получить форматы»** заново
- Выберите другое разрешение из списка

### ❌ ERROR: ffmpeg is not installed / merging formats

FFmpeg не найден. Решения:
- Убедитесь что `ffmpeg.exe` лежит рядом с `VideoDownloader.exe` в папке `dist\VideoDownloader\`
- Установите FFmpeg по инструкции выше

### ❌ Видео скачалось без звука

- Отсутствует `ffmpeg.exe` — установите по инструкции выше
- После установки ffmpeg повторите загрузку

### ❌ Приложение не запускается / вылетает сразу

- Не удаляйте и не перемещайте файлы из папки `dist\VideoDownloader\` — там находятся все зависимости
- Запускайте только через `VideoDownloader.exe` или ярлык на рабочем столе
- Проверьте что антивирус не блокирует файл (добавьте папку в исключения)

### ❌ Медленная загрузка

- Зависит от скорости вашего интернета и серверов платформы
- Попробуйте выбрать разрешение пониже (480p вместо 1080p)

### ❌ Ошибка при загрузке с RuTube или VK

- Убедитесь что ссылка скопирована полностью из адресной строки браузера
- Некоторые видео могут быть закрыты настройками приватности

---

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

После сборки скопируйте `ffmpeg.exe` в папку `dist\VideoDownloader\`.

### Создание ярлыка на рабочем столе

```bash
powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
```

---

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
        ├── VideoDownloader.exe
        └── ffmpeg.exe    # Скопировать сюда вручную
```

## Зависимости

| Пакет | Назначение |
|-------|-----------|
| PyQt6 | GUI фреймворк |
| yt-dlp | Загрузка видео |
| pyinstaller | Сборка в .exe |
