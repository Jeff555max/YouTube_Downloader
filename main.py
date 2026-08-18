import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFileDialog, QProgressBar,
    QScrollArea, QFrame, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QClipboard

from downloader import FetchFormatsThread, DownloadThread


STYLE = """
QMainWindow, QWidget#central {
    background: #f0f4f8;
}
QLineEdit#url_input {
    border: 2px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    background: white;
}
QPushButton#btn_paste {
    background: #64748b;
    color: white;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#btn_paste:hover { background: #475569; }
QPushButton#btn_fetch {
    background: #e53e3e;
    color: white;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#btn_fetch:hover { background: #c53030; }
QPushButton#btn_folder {
    background: #3b82f6;
    color: white;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
}
QPushButton#btn_folder:hover { background: #2563eb; }
QPushButton#btn_download {
    background: #16a34a;
    color: white;
    border-radius: 8px;
    padding: 10px 32px;
    font-size: 15px;
    font-weight: bold;
}
QPushButton#btn_download:hover { background: #15803d; }
QPushButton#btn_download:disabled { background: #9ca3af; }
QLabel#title {
    font-size: 28px;
    font-weight: bold;
    color: #1e293b;
}
QLabel#subtitle {
    font-size: 13px;
    color: #64748b;
}
QFrame#formats_card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}
QPushButton.format_btn {
    border-radius: 8px;
    padding: 14px 10px;
    font-size: 13px;
    text-align: left;
    border: 2px solid transparent;
}
QPushButton.format_btn:checked {
    border: 2px solid #3b82f6;
    background: #eff6ff;
}
QProgressBar {
    border-radius: 6px;
    background: #e2e8f0;
    height: 12px;
    text-align: center;
}
QProgressBar::chunk {
    border-radius: 6px;
    background: #3b82f6;
}
"""

QUALITY_COLORS = {
    "HD": ("#fed7aa", "#ea580c"),
    "SD": ("#bfdbfe", "#2563eb"),
    "Audio": ("#d1fae5", "#059669"),
}


class FormatButton(QPushButton):
    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.setCheckable(True)
        self.setProperty("class", "format_btn")
        self._build(fmt)

    def _build(self, fmt):
        q_bg, q_fg = QUALITY_COLORS.get(fmt["quality"], ("#e2e8f0", "#374151"))
        if fmt["is_audio"]:
            self.setText(f"  🎵  MP3\n  Audio")
        else:
            self.setText(f"  {fmt['resolution']}\n  {fmt['ext'].upper()}")
        self.setStyleSheet(f"""
            QPushButton {{
                background: #f8fafc;
                border-radius: 8px;
                padding: 12px 10px;
                font-size: 13px;
                text-align: left;
                border: 2px solid #e2e8f0;
                color: #1e293b;
            }}
            QPushButton:checked {{
                border: 2px solid #3b82f6;
                background: #eff6ff;
            }}
            QPushButton:hover {{ background: #f1f5f9; }}
        """)
        self.setMinimumSize(QSize(140, 70))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Downloader")
        self.setMinimumWidth(700)
        self.setStyleSheet(STYLE)
        self.save_path = os.path.expanduser("~/Downloads")
        self.formats = []
        self.fetch_thread = None
        self.dl_thread = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(20)

        # Title
        title = QLabel("Video Downloader")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("YouTube • RuTube • VK Video  |  MP4 / MP3")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        root.addWidget(sub)

        # URL row
        url_row = QHBoxLayout()
        self.btn_paste = QPushButton("📋 Вставить")
        self.btn_paste.setObjectName("btn_paste")
        self.btn_paste.clicked.connect(self._paste)
        self.url_input = QLineEdit()
        self.url_input.setObjectName("url_input")
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.btn_fetch = QPushButton("Получить форматы")
        self.btn_fetch.setObjectName("btn_fetch")
        self.btn_fetch.clicked.connect(self._fetch_formats)
        url_row.addWidget(self.btn_paste)
        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(self.btn_fetch)
        root.addLayout(url_row)

        # Status label
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #64748b; font-size: 13px;")
        root.addWidget(self.lbl_status)

        # Formats card
        self.formats_card = QFrame()
        self.formats_card.setObjectName("formats_card")
        self.formats_card.hide()
        card_layout = QVBoxLayout(self.formats_card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        lbl_avail = QLabel("Доступные форматы")
        lbl_avail.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        card_layout.addWidget(lbl_avail)

        self.formats_grid = QHBoxLayout()
        self.formats_grid.setSpacing(10)
        self.formats_grid_widget = QWidget()
        self.formats_grid_widget.setLayout(self.formats_grid)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.formats_grid_widget)
        scroll.setMaximumHeight(160)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        card_layout.addWidget(scroll)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        # Save path row
        path_row = QHBoxLayout()
        self.lbl_path = QLabel(self.save_path)
        self.lbl_path.setStyleSheet("color: #475569; font-size: 13px;")
        self.lbl_path.setWordWrap(True)
        btn_folder = QPushButton("📁 Папка сохранения")
        btn_folder.setObjectName("btn_folder")
        btn_folder.clicked.connect(self._choose_folder)
        path_row.addWidget(QLabel("Сохранить в:"))
        path_row.addWidget(self.lbl_path, 1)
        path_row.addWidget(btn_folder)
        card_layout.addLayout(path_row)

        # Download button
        self.btn_download = QPushButton("⬇  Скачать")
        self.btn_download.setObjectName("btn_download")
        self.btn_download.setEnabled(False)
        self.btn_download.clicked.connect(self._start_download)
        card_layout.addWidget(self.btn_download, alignment=Qt.AlignmentFlag.AlignCenter)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.lbl_speed = QLabel("")
        self.lbl_speed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_speed.setStyleSheet("color: #64748b; font-size: 12px;")
        card_layout.addWidget(self.progress_bar)
        card_layout.addWidget(self.lbl_speed)

        root.addWidget(self.formats_card)
        root.addStretch()

    def _paste(self):
        text = QApplication.clipboard().text()
        if text:
            self.url_input.setText(text.strip())

    def _fetch_formats(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Ошибка", "Введите URL видео")
            return
        self.lbl_status.setText("⏳ Получение информации о видео...")
        self.btn_fetch.setEnabled(False)
        self.formats_card.hide()
        self.fetch_thread = FetchFormatsThread(url)
        self.fetch_thread.finished.connect(self._on_formats)
        self.fetch_thread.error.connect(self._on_error)
        self.fetch_thread.start()

    def _on_formats(self, formats):
        self.formats = formats
        self.lbl_status.setText(f"✅ Найдено форматов: {len(formats)}")
        self.btn_fetch.setEnabled(True)
        self._populate_formats(formats)
        self.formats_card.show()

    def _populate_formats(self, formats):
        # Clear old buttons
        for btn in self.btn_group.buttons():
            self.btn_group.removeButton(btn)
        while self.formats_grid.count():
            item = self.formats_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for fmt in formats:
            btn = FormatButton(fmt)
            self.btn_group.addButton(btn)
            self.formats_grid.addWidget(btn)
            btn.clicked.connect(lambda checked, b=btn: self._on_format_selected(b))

        self.formats_grid.addStretch()
        self.btn_download.setEnabled(False)

    def _on_format_selected(self, btn):
        self.btn_download.setEnabled(True)

    def _choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку", self.save_path)
        if path:
            self.save_path = path
            self.lbl_path.setText(path)

    def _start_download(self):
        selected = self.btn_group.checkedButton()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите формат")
            return
        fmt = selected.fmt
        url = self.url_input.text().strip()
        self.btn_download.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.lbl_speed.setText("")
        self.dl_thread = DownloadThread(url, fmt, self.save_path)
        self.dl_thread.progress.connect(self._on_progress)
        self.dl_thread.finished.connect(self._on_done)
        self.dl_thread.error.connect(self._on_error)
        self.dl_thread.start()

    def _on_progress(self, pct, info):
        self.progress_bar.setValue(pct)
        self.lbl_speed.setText(info)

    def _on_done(self):
        self.progress_bar.setValue(100)
        self.lbl_speed.setText("✅ Загрузка завершена!")
        self.btn_download.setEnabled(True)
        QMessageBox.information(self, "Готово", f"Файл сохранён в:\n{self.save_path}")

    def _on_error(self, msg):
        self.btn_fetch.setEnabled(True)
        self.btn_download.setEnabled(True)
        self.lbl_status.setText("❌ Ошибка")
        QMessageBox.critical(self, "Ошибка", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
