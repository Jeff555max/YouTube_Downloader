# ARCHITECTURE.md — Техническое описание проекта Video Downloader

Этот документ описывает архитектуру проекта, все проблемы которые возникли в процессе разработки и способы их решения. Предназначен для разработчиков и LLM-агентов, которые будут работать с этим кодом.

---

## Стек технологий

| Компонент | Технология | Причина выбора |
|-----------|-----------|----------------|
| GUI | PyQt6 | Нативный вид на Windows, богатый набор виджетов |
| Загрузка видео | yt-dlp | Поддержка 1000+ сайтов, активно поддерживается |
| Конвертация аудио/видео | FFmpeg | Единственный надёжный инструмент для мержа потоков |
| Упаковка в .exe | PyInstaller | Стандарт для Python на Windows |

---

## Архитектура приложения

### Файловая структура

```
YouTube_Downloader/
├── main.py          # GUI — PyQt6 MainWindow, все виджеты, сигналы
├── downloader.py    # Логика — два QThread класса + вспомогательные функции
├── requirements.txt
├── create_shortcut.ps1
└── dist/
    └── VideoDownloader/
        ├── VideoDownloader.exe
        └── ffmpeg.exe   # обязательно рядом с exe
```

### Разделение ответственности

**main.py** — только UI:
- `MainWindow` — главное окно
- `FormatButton` — кнопка-карточка для каждого формата (checkable QPushButton)
- Все сетевые операции делегируются в потоки из `downloader.py`

**downloader.py** — только логика:
- `_ffmpeg_location()` — определяет путь к ffmpeg.exe
- `_base_opts()` — общие настройки yt-dlp (используются и в fetch и в download)
- `FetchFormatsThread(QThread)` — получает список форматов без скачивания
- `DownloadThread(QThread)` — скачивает выбранный формат

### Почему два отдельных потока

GUI в PyQt6 замерзает если делать сетевые запросы в главном потоке. Оба класса наследуют `QThread` и общаются с GUI через сигналы (`pyqtSignal`), что является стандартным паттерном PyQt.

---

## Проблемы и их решения

### Проблема 1: FFmpeg не найден при запуске .exe

**Симптом:**
```
ERROR: You have requested merging of multiple formats but ffmpeg is not installed.
```

**Причина:**
PyInstaller упаковывает Python-код в `_MEIPASS` (временная папка при запуске), но `ffmpeg.exe` — это внешний бинарник, он там не лежит. Первоначальный код искал ffmpeg в `sys._MEIPASS`, что неверно.

**Решение:**
Искать `ffmpeg.exe` рядом с самим `VideoDownloader.exe`, то есть в `os.path.dirname(sys.executable)` когда приложение заморожено (`sys.frozen == True`):

```python
def _ffmpeg_location():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)  # папка с .exe
    else:
        base = os.path.dirname(os.path.abspath(__file__))  # папка с .py
    if os.path.isfile(os.path.join(base, 'ffmpeg.exe')):
        return base
    return None
```

Параметр `ffmpeg_location` в yt-dlp принимает **директорию**, а не путь к файлу.

**Важно:** После каждой пересборки через PyInstaller папка `dist/VideoDownloader/` очищается, поэтому `ffmpeg.exe` нужно копировать заново.

---

### Проблема 2: HTTP Error 403 Forbidden

**Симптом:**
```
ERROR: unable to download video data: HTTP Error 403: Forbidden
```

**Причина:**
YouTube блокирует запросы от стандартного yt-dlp User-Agent. YouTube использует систему защиты от ботов, которая проверяет заголовки запроса и тип клиента.

**Попытки решения которые НЕ сработали:**

1. Стандартный браузерный User-Agent — YouTube всё равно блокировал
2. `player_client: web` — требует cookies и JavaScript challenge
3. `player_client: tv_embedded` — работал для fetch, но давал 403 при download
4. `cookiesfrombrowser: opera` — Opera основана на Chromium и блокирует доступ к своей БД cookies пока открыта, выдавала ошибку копирования

**Решение которое сработало:**
Использовать **Android player client** с соответствующим User-Agent:

```python
"extractor_args": {
    "youtube": {"player_client": ["android"]}
},
"http_headers": {
    "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
},
```

**Почему это работает:**
YouTube предоставляет отдельный API для Android приложения. Этот API возвращает прямые ссылки на видеофайлы без защиты от ботов, так как предполагается что Android-клиент — это официальное приложение YouTube.

---

### Проблема 3: Requested format is not available

**Симптом:**
```
ERROR: [youtube] VIDEO_ID: Requested format is not available.
```

**Причина (первая версия):**
Форматы строились вручную через шаблон строки:
```python
f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/..."
```
Это не гарантировало что такой формат реально существует для конкретного видео.

**Решение первой версии:**
Использовать реальные `format_id` из объекта `info`, полученного при fetch:
```python
for f in info.get("formats", []):
    by_height[height] = {"format_id": f["format_id"], ...}
```

**Причина (вторая версия):**
После перехода на `tv_embedded` клиент форматы при fetch и download получались от разных клиентов YouTube. `tv_embedded` возвращал одни `format_id`, а при download yt-dlp использовал другой клиент и эти ID не существовали.

**Финальное решение:**
Использовать одинаковый `_base_opts()` и для fetch и для download. Поскольку оба вызова используют `android` клиент — форматы совпадают. Download делает свежий запрос по URL (не кэширует info), что также решает проблему протухших URL.

---

### Проблема 4: Cookies из Opera недоступны

**Симптом:**
```
ERROR: Could not copy Chrome cookie database.
See https://github.com/yt-dlp/yt-dlp/issues/7271
```

**Причина:**
Opera основана на Chromium и хранит cookies в SQLite базе данных. Chromium-браузеры блокируют файл БД пока открыты. yt-dlp пытается скопировать файл и получает отказ в доступе.

**Решение:**
Отказаться от cookies полностью. Android player client не требует авторизации для большинства публичных видео, поэтому cookies не нужны.

---

### Проблема 5: Видео без звука

**Симптом:** Скачанный MP4 файл не содержит аудио дорожки.

**Причина:**
YouTube с 2023 года раздаёт видео и аудио как отдельные потоки (DASH). Для их склейки нужен FFmpeg. Без FFmpeg yt-dlp скачивает только видео поток.

**Решение:**
- Обязательно класть `ffmpeg.exe` рядом с `VideoDownloader.exe`
- В коде: `ydl_opts["merge_output_format"] = "mp4"` — указывает yt-dlp смержить потоки в mp4
- Для форматов без аудио явно добавляем `+bestaudio` к format_id:
```python
fmt_str = d["format_id"] if d["has_audio"] else f"{d['format_id']}+bestaudio"
```

---

### Проблема 6: PyInstaller очищает dist/ при каждой сборке

**Симптом:** После `pyinstaller --noconfirm` исчезает `ffmpeg.exe` из `dist/VideoDownloader/`.

**Причина:** Флаг `--noconfirm` заставляет PyInstaller полностью очищать выходную папку перед сборкой.

**Решение:** После каждой сборки копировать ffmpeg заново:
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + ...
Copy-Item (Get-Command ffmpeg).Source 'dist\VideoDownloader\ffmpeg.exe' -Force
```

Долгосрочное решение — добавить `ffmpeg.exe` в `.spec` файл через `binaries=[('path/to/ffmpeg.exe', '.')]`, тогда PyInstaller будет включать его автоматически.

### Проблема 7: KeyError('params') — внутренняя ошибка экстрактора

**Симптом:**
```
ERROR: An extractor error has occurred. (caused by KeyError('params'));
please report this issue on https://github.com/yt-dlp/yt-dlp/issues
```

**Причина:**
Баг внутри yt-dlp при использовании конкретного `player_client`. Возникает когда YouTube меняет формат ответа API, а yt-dlp ещё не обновился. Проявляется непредсказуемо — один клиент может работать сегодня и сломаться завтра.

**Решение:**
Автоматический fallback по списку клиентов `android → ios → web`. Если один клиент падает с любой ошибкой — автоматически пробуется следующий:

```python
PLAYER_CLIENTS = ["android", "ios", "web"]

def _base_opts(player_client="android"):
    opts = {
        "extractor_args": {"youtube": {"player_client": [player_client]}},
        ...
    }
    return opts

# В FetchFormatsThread.run() и DownloadThread.run():
last_error = None
for client in PLAYER_CLIENTS:
    try:
        with yt_dlp.YoutubeDL(_base_opts(client)) as ydl:
            # ... fetch или download
        return  # успех — выходим
    except Exception as e:
        last_error = e
        continue  # пробуем следующий клиент
self.error.emit(str(last_error))  # все клиенты не сработали
```

**Важно:** Fallback применяется и при получении форматов и при скачивании независимо. Это означает что fetch может использовать `android`, а download — `ios`, и `format_id` могут не совпасть. На практике это не проблема, так как при download yt-dlp делает свежий запрос и получает актуальные форматы от того клиента который сработал.

---

### Проблема 8: Таймаут при скачивании

**Симптом:**
```
ERROR: [download] Got error: The read operation timed out.
```

**Причина:**
YouTube периодически throttling-ует соединения для не-браузерных клиентов — намеренно замедляет или обрывает передачу данных. Также может быть нестабильный интернет или большой размер файла.

**Решение:**
Добавить в `_base_opts()` параметры устойчивости:

```python
"retries": 10,                                    # повторов при HTTP ошибке
"fragment_retries": 10,                           # повторов для каждого DASH фрагмента
"retry_sleep_functions": {"http": lambda n: 3*n}, # пауза растёт: 3с, 6с, 9с...
"socket_timeout": 30,                             # таймаут соединения в секундах
```

---

### Определение пути к ffmpeg

```python
def _ffmpeg_location():
    # sys.frozen = True когда запущен как .exe (PyInstaller)
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    if os.path.isfile(os.path.join(base, 'ffmpeg.exe')):
        return base  # yt-dlp ожидает директорию, не путь к файлу
    return None
```

### Android клиент для обхода 403

```python
def _base_opts():
    return {
        "extractor_args": {
            "youtube": {"player_client": ["android"]}
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
        },
        "ffmpeg_location": _ffmpeg_location(),
        ...
    }
```

### Парсинг форматов — берём лучший по bitrate

```python
by_height = {}
for f in info.get("formats", []):
    height = f.get("height")
    if not height or f.get("vcodec", "none") == "none":
        continue
    tbr = f.get("tbr") or 0
    # Для каждой высоты берём формат с максимальным bitrate
    if height not in by_height or tbr > by_height[height]["tbr"]:
        by_height[height] = {"format_id": f["format_id"], ...}
```

---

## Что важно знать при доработке

1. **ffmpeg_location** в yt-dlp принимает **папку**, а не путь к файлу
2. **player_client** должен быть одинаковым при fetch и download — иначе format_id не совпадут
3. **PyInstaller** при `--noconfirm` всегда очищает `dist/` — ffmpeg нужно копировать после каждой сборки
4. **QThread** в PyQt6 — нельзя обновлять UI из потока напрямую, только через `pyqtSignal`
5. **sys.frozen** — флаг PyInstaller, True когда код запущен как .exe
6. **sys._MEIPASS** — временная папка с Python-файлами при запуске .exe, НЕ папка с .exe
7. **sys.executable** — путь к самому .exe файлу, `os.path.dirname(sys.executable)` — его папка
8. **PLAYER_CLIENTS** — список `["android", "ios", "web"]`, оба потока (fetch и download) перебирают его независимо при любой ошибке
