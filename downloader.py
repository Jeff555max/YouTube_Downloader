import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


class FetchFormatsThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
            formats = self._parse_formats(info)
            self.finished.emit(formats)
        except Exception as e:
            self.error.emit(str(e))

    def _parse_formats(self, info):
        result = []
        seen = set()

        # MP3 audio
        result.append({
            "label": "MP3",
            "ext": "mp3",
            "resolution": "Audio",
            "quality": "Audio",
            "format_id": "bestaudio/best",
            "is_audio": True,
        })

        # Video formats
        for f in info.get("formats", []):
            ext = f.get("ext", "")
            height = f.get("height")
            vcodec = f.get("vcodec", "none")
            if not height or vcodec == "none":
                continue
            label = f"{height}p"
            key = (label, "mp4")
            if key in seen:
                continue
            seen.add(key)
            result.append({
                "label": label,
                "ext": "mp4",
                "resolution": label,
                "quality": "HD" if height >= 720 else "SD",
                "format_id": f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]",
                "is_audio": False,
            })

        # Sort video by resolution descending
        video = sorted([f for f in result if not f["is_audio"]], key=lambda x: int(x["resolution"][:-1]), reverse=True)
        audio = [f for f in result if f["is_audio"]]
        return audio + video


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
        try:
            outtmpl = f"{self.save_path}/%(title)s.%(ext)s"
            ydl_opts = {
                "outtmpl": outtmpl,
                "progress_hooks": [self._hook],
                "quiet": True,
                "no_warnings": True,
            }
            if self.fmt["is_audio"]:
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                })
            else:
                ydl_opts["format"] = self.fmt["format_id"]
                ydl_opts["merge_output_format"] = "mp4"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("_speed_str", "")
            eta = d.get("_eta_str", "")
            pct = int(downloaded / total * 100) if total else 0
            self.progress.emit(pct, f"{speed} | ETA: {eta}")
        elif d["status"] == "finished":
            self.progress.emit(100, "Обработка...")
