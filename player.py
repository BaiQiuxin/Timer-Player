#! /usr/bin/env python3
"""
Timer & Player
A simple desktop application that combines a local music player with a timer.
"""

import sys
import configparser
from pathlib import Path
from typing import List

import qrcode

from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QFont, QPixmap, QImage, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QMainWindow, QAction,
)


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TIMER_TEXT_FILE = "./timer_text.txt"
CONFIG_FILE = "./player.ini"
TIMER_INTERVAL_MS = 100
MAX_SONGS_VOLUME = 100


def load_config(path: str) -> List[dict]:
    """Load configuration from player.ini"""
    cfg = configparser.ConfigParser()
    cfg.read(path, encoding="utf-8")
    sections = cfg.sections()
    songs = []
    for section_name in sections:
        if section_name.startswith("Song"):
            section = cfg[section_name]
            songs.append({
                "audio_file": section.get("audio_file", ""),
                "author": section.get("author", ""),
                "song_name": section.get("song_name", ""),
                "song_url": section.get("song_url", ""),
                "cover_image": section.get("cover_image", ""),
            })
    return songs


def load_custom_text(path: str) -> str:
    """Read custom text for timer from file"""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "Nah, just a timer. No custom text found."


def generate_qr_pixmap(data: str, size: int = 200) -> QPixmap:
    """Generate QR code and return QPixmap"""
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # Convert to QPixmap
    img = img.convert("RGB")
    qimage = QImage(
        img.tobytes(), img.width, img.height, img.width * 3,
        QImage.Format_RGB888
    )
    return QPixmap.fromImage(qimage).scaled(
        size, size, Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )


def load_cover_pixmap(path: str, size: tuple = (320, 320)) -> QPixmap:
    """Load album cover image"""
    pix = QPixmap(path)
    if pix.isNull():
        pix = QPixmap(size[0], size[1])
        pix.fill(QColor("#ffffff"))
    return pix.scaled(
        size[0], size[1], Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )


# Timer

class TimerWidget(QWidget):
    """Timer component with custom text and time display"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._elapsed_ms = 0  # Accumulated elapsed time in milliseconds

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._init_ui()
        self._update_display()

    def _init_ui(self) -> None:
        # Custom text label
        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        font_text = QFont("Microsoft YaHei", 18, QFont.Bold)
        self.text_label.setFont(font_text)
        self.text_label.setStyleSheet("color: #000000;")

        # Time display label
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        font_time = QFont("Consolas", 64, QFont.Bold)
        self.time_label.setFont(font_time)
        self.time_label.setStyleSheet("color: #000000;")

        # Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addStretch(2)
        layout.addWidget(self.text_label)
        layout.addSpacing(30)
        layout.addWidget(self.time_label)
        layout.addStretch(2)
        self.setLayout(layout)

    def load_text(self, path: str) -> None:
        """Load custom text for the timer"""
        text = load_custom_text(path)
        self.text_label.setText(text)

    def _tick(self) -> None:
        """Timer tick"""
        self._elapsed_ms += TIMER_INTERVAL_MS
        self._update_display()

    def _update_display(self) -> None:
        total_sec = self._elapsed_ms // 1000
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        self.time_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def start(self) -> None:
        """Start the timer"""
        if not self._running:
            self._timer.start(TIMER_INTERVAL_MS)
            self._running = True
            self._set_normal_style()

    def stop(self) -> None:
        """Stop the timer"""
        if self._running:
            self._timer.stop()
            self._running = False
            self._set_faded_style()

    def toggle(self) -> None:
        """Toggle start/pause"""
        if self._running:
            self.stop()
        else:
            self.start()

    def reset(self) -> None:
        """Reset the timer"""
        self._timer.stop()
        self._elapsed_ms = 0
        self._running = False
        self._update_display()
        self._set_normal_style()

    def is_running(self) -> bool:
        return self._running

    def _set_faded_style(self) -> None:
        """Set faded style"""
        self.text_label.setStyleSheet("color: #aaaaaa;")
        self.time_label.setStyleSheet("color: #aaaaaa;")

    def _set_normal_style(self) -> None:
        """Set normal style"""
        self.text_label.setStyleSheet("color: #000000;")
        self.time_label.setStyleSheet("color: #000000;")


# Music Player

class MusicPlayerWidget(QWidget):
    """Local music player component with album cover, song info, QR code, and controls"""

    def __init__(self, songs: List[dict], parent=None):
        super().__init__(parent)
        self._songs = songs
        self._current_index = 0
        self._player = QMediaPlayer(self)
        self._player.setVolume(MAX_SONGS_VOLUME)

        self._init_ui()
        self._load_current_song()

        # Playback finished signal to auto-play next song
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

    def _init_ui(self):
        # Album cover
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setFixedSize(340, 340)

        # Author name
        self.author_label = QLabel()
        self.author_label.setAlignment(Qt.AlignCenter)
        font_author = QFont("Microsoft YaHei", 16, QFont.Bold)
        self.author_label.setFont(font_author)
        self.author_label.setStyleSheet("color: #000000;")

        # Song name
        self.song_label = QLabel()
        self.song_label.setAlignment(Qt.AlignCenter)
        font_song = QFont("Microsoft YaHei", 14)
        self.song_label.setFont(font_song)
        self.song_label.setStyleSheet("color: #000000;")

        # QR code
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedSize(220, 220)

        # Overall layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)
        layout.addSpacing(12)
        layout.addWidget(self.author_label)
        layout.addWidget(self.song_label)
        layout.addSpacing(16)
        layout.addWidget(self.qr_label, alignment=Qt.AlignCenter)
        layout.addStretch(2)
        self.setLayout(layout)

    def _load_current_song(self):
        """Load current song info, cover, QR code, and audio file"""
        if not self._songs or self._current_index >= len(self._songs):
            return
        cfg = self._songs[self._current_index]

        # Cover image
        cover_path = cfg.get("cover_image", "")
        if cover_path:
            pix = load_cover_pixmap(cover_path, (320, 320))
            self.cover_label.setPixmap(pix)

        # Author and song name
        self.author_label.setText(cfg.get("author", "未知作者"))
        self.song_label.setText(cfg.get("song_name", "未知歌曲"))

        # QR code for song URL
        song_url = cfg.get("song_url", "")
        if song_url:
            qr_pix = generate_qr_pixmap(song_url, 200)
            self.qr_label.setPixmap(qr_pix)

        # Audio file
        audio_file = cfg.get("audio_file", "")
        if audio_file and Path(audio_file).exists():
            self._player.setMedia(
                QMediaContent(QUrl.fromLocalFile(str(Path(audio_file).resolve())))
            )

    def _toggle_playback(self) -> None:
        """Switch between play and pause states"""
        state = self._player.state()
        if state == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _prev_song(self) -> None:
        """Previous song"""
        if not self._songs:
            return
        self._current_index = (self._current_index - 1) % len(self._songs)
        self._load_current_song()
        # Play if currently playing
        if self._player.state() == QMediaPlayer.PlayingState:
            self._player.play()

    def _next_song(self) -> None:
        """Next song"""
        if not self._songs:
            return
        self._current_index = (self._current_index + 1) % len(self._songs)
        self._load_current_song()
        # Play if currently playing
        if self._player.state() == QMediaPlayer.PlayingState:
            self._player.play()

    def _on_media_status_changed(self, status):
        """Play next song when current song finishes"""
        if status == QMediaPlayer.EndOfMedia:
            self._next_song()

    def set_songs(self, songs: List[dict]):
        """Refresh song list and reset to first song"""
        self._songs = songs
        self._current_index = 0
        self._load_current_song()


# Main Window

class MainWindow(QMainWindow):
    """Main application window that combines TimerWidget and MusicPlayerWidget"""

    def __init__(self):
        super().__init__()
        self._config = load_config(CONFIG_FILE)

        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self):
        self.setWindowTitle("Timer & Player")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._center()

        # Central widget with horizontal layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left side: Timer
        self.timer_widget = TimerWidget()
        self.timer_widget.setStyleSheet("background-color: #ffffff;")
        self.timer_widget.load_text(TIMER_TEXT_FILE)
        main_layout.addWidget(self.timer_widget, 4)  # 40%

        # Right side: Music Player
        self.player_widget = MusicPlayerWidget(self._config)
        self.player_widget.setStyleSheet("background-color: #ffffff;")
        main_layout.addWidget(self.player_widget, 6)  # 60%

        # Status bar with instructions
        self.statusBar().showMessage(
            "Ctrl+F Switch Timer  |  Ctrl+R Reset Timer  |  ← Previous Song  |  → Next Song |  Space Play/Pause  |  Esc Exit"
        )

    def _center(self):
        """Center the window on the screen"""
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Ctrl+F: Switch timer
        toggle_action = QAction("Switch Timer", self)
        toggle_action.setShortcut("Ctrl+F")
        toggle_action.triggered.connect(self.timer_widget.toggle)
        self.addAction(toggle_action)

        # Ctrl+R: Reset timer
        reset_action = QAction("Reset Timer", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.timer_widget.reset)
        self.addAction(reset_action)

        # ←: Previous song
        prev_action = QAction("Previous Song", self)
        prev_action.setShortcut(Qt.Key_Left)
        prev_action.triggered.connect(self.player_widget._prev_song)
        self.addAction(prev_action)

        # →: Next song
        next_action = QAction("Next Song", self)
        next_action.setShortcut(Qt.Key_Right)
        next_action.triggered.connect(self.player_widget._next_song)
        self.addAction(next_action)
        
        # Space: Play/Pause
        play_pause_action = QAction("Play/Pause", self)
        play_pause_action.setShortcut(Qt.Key_Space)
        play_pause_action.triggered.connect(self.player_widget._toggle_playback)
        self.addAction(play_pause_action)


    def keyPressEvent(self, event):
        """Press Esc to close the window"""
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)


# Application Entry Point

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Global style
    app.setStyleSheet("""
        QMainWindow { background-color: #ffffff; }
        QStatusBar {
            background-color: #e8e8e8; color: #555; font-size: 12px;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()