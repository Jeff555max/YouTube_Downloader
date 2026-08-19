import os
import sys
import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


def _ffmpeg_location():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    if os.path.isfile(os.path.join(base, 'ffmpeg.exe')):
        return base
    return None


PLAYER_CLIENTS = ["android", "ios", "web"]


def _base_opts(player_client="android"):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {"player_client": [player_client]}
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        },
        "retries": 10,
        "fragment_retries": 10,
        "retry_sleep_functions": {"http": lambda n: 3 * n},
        "socket_timeout": 30,
    }
    ffmpeg = _ffmpeg_location()
    if ffmpeg:
        opts["ffmpeg_location"] = ffmpeg
    return opts


class FetchFormatsThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        last_error = None
        for client in PLAYER_CLIENTS:
            try:
                with yt_dlp.YoutubeDL(_base_opts(client)) as ydl:
                    info = ydl.extract_info(self.url, download=False)
                self.finished.emit(self._parse_formats(info))
                return
            except Exception as e:
                last_error = e
                continue
        self.error.emit(str(last_error))

    def _parse_formats(self, info):
        result = [{"label": "MP3", "ext": "mp3", "resolution": "Audio",
                   "quality": "Audio", "format_id": "bestaudio/best", "is_audio": True}]

        by_height = {}
        for f in info.get("formats", []):
            height = f.get("height")
            if not height or f.get("vcodec", "none") == "none":
                continue
            tbr = f.get("tbr") or 0
            if height not in by_height or tbr > by_height[height]["tbr"]:
                by_height[height] = {
                    "format_id": f["format_id"],
                    "has_audio": f.get("acodec", "none") not in ("none", None),
                    "tbr": tbr,
                }

        for height in sorted(by_height.keys(), reverse=True):
            d = by_height[height]
            fmt_str = d["format_id"] if d["has_audio"] else f"{d['format_id']}+bestaudio"
            result.append({
                "label": f"{height}p", "ext": "mp4", "resolution": f"{height}p",
                "quality": "HD" if height >= 720 else "SD",
                "format_id": fmt_str, "is_audio": False,
            })
        return result


class DownloadThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, fmt, save_path):
        super().__init__()
        self.url = url
        self.fmt = fmt
        self.save_path = save_path

    def run(self):
        last_error = None
        for client in PLAYER_CLIENTS:
            try:
                ydl_opts = _base_opts(client)
                ydl_opts["outtmpl"] = f"{self.save_path}/%(title)s.%(ext)s"
                ydl_opts["progress_hooks"] = [self._hook]

                if self.fmt["is_audio"]:
                    ydl_opts["format"] = "bestaudio/best"
                    ydl_opts["postprocessors"] = [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }]
                else:
                    ydl_opts["format"] = self.fmt["format_id"]
                    ydl_opts["merge_output_format"] = "mp4"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.url])
                self.finished.emit()
                return
            except Exception as e:
                last_error = e
                continue
        self.error.emit(str(last_error))

    def _hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            pct = int(downloaded / total * 100) if total else 0
            self.progress.emit(pct, f"{d.get('_speed_str','')} | ETA: {d.get('_eta_str','')}")
        elif d["status"] == "finished":
            self.progress.emit(100, "Обработка...")
