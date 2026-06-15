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
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QMainWindow, QMessageBox, QAction,
)


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TIMER_TEXT_FILE = "./timer_text.txt"
CONFIG_FILE = "./player.ini"
TIMER_INTERVAL_MS = 100


def load_config(path: str) -> List[dict]:
    """读取 player.ini 配置"""
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
    """从文件中读取自定义文本"""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "专注时刻"


def generate_qr_pixmap(data: str, size: int = 200) -> QPixmap:
    """生成二维码并返回 QPixmap"""
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # 转换为 QPixmap
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
    """加载专辑封面图片"""
    pix = QPixmap(path)
    if pix.isNull():
        pix = QPixmap(size[0], size[1])
        pix.fill(QColor("#cccccc"))
    return pix.scaled(
        size[0], size[1], Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )


# ── 计时器组件 ────────────────────────────────────────────────────────────

class TimerWidget(QWidget):
    """正计时器组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._elapsed_ms = 0  # 累计毫秒数

        # 计时 QTimer（每 100ms 触发一次）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._init_ui()
        self._update_display()

    def _init_ui(self):
        # 自定义文本标签
        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)
        font_text = QFont("Microsoft YaHei", 18, QFont.Bold)
        self.text_label.setFont(font_text)
        self.text_label.setStyleSheet("color: #333333;")

        # 计时器显示标签
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        font_time = QFont("Consolas", 64, QFont.Bold)
        self.time_label.setFont(font_time)
        self.time_label.setStyleSheet("color: #222222;")

        # 布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addStretch(2)
        layout.addWidget(self.text_label)
        layout.addSpacing(20)
        layout.addWidget(self.time_label)
        layout.addStretch(3)
        self.setLayout(layout)

    def load_text(self, path: str):
        """加载自定义文本"""
        text = load_custom_text(path)
        self.text_label.setText(text)

    def _tick(self):
        """计时器 tick"""
        self._elapsed_ms += TIMER_INTERVAL_MS
        self._update_display()

    def _update_display(self):
        total_sec = self._elapsed_ms // 1000
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        self.time_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def start(self):
        """开始计时"""
        if not self._running:
            self._timer.start(TIMER_INTERVAL_MS)
            self._running = True
            self._set_normal_style()

    def stop(self):
        """停止计时"""
        if self._running:
            self._timer.stop()
            self._running = False
            self._set_faded_style()

    def toggle(self):
        """切换 启动/暂停"""
        if self._running:
            self.stop()
        else:
            self.start()

    def reset(self):
        """重置计时器"""
        self._timer.stop()
        self._elapsed_ms = 0
        self._running = False
        self._update_display()
        self._set_normal_style()

    def is_running(self) -> bool:
        return self._running

    def _set_faded_style(self):
        """设置淡出样式"""
        self.text_label.setStyleSheet("color: #aaaaaa;")
        self.time_label.setStyleSheet("color: #aaaaaa;")

    def _set_normal_style(self):
        """设置正常样式"""
        self.text_label.setStyleSheet("color: #333333;")
        self.time_label.setStyleSheet("color: #222222;")


# ── 音乐播放器组件 ────────────────────────────────────────────────────────

class MusicPlayerWidget(QWidget):
    """本地音乐播放器组件"""

    def __init__(self, songs: List[dict], parent=None):
        super().__init__(parent)
        self._songs = songs
        self._current_index = 0
        self._player = QMediaPlayer(self)
        self._player.setVolume(50)

        self._init_ui()
        self._load_current_song()

    def _init_ui(self):
        # 专辑封面
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setFixedSize(340, 340)

        # 作者
        self.author_label = QLabel()
        self.author_label.setAlignment(Qt.AlignCenter)
        font_author = QFont("Microsoft YaHei", 16, QFont.Bold)
        self.author_label.setFont(font_author)
        self.author_label.setStyleSheet("color: #444444;")

        # 歌曲名
        self.song_label = QLabel()
        self.song_label.setAlignment(Qt.AlignCenter)
        font_song = QFont("Microsoft YaHei", 14)
        self.song_label.setFont(font_song)
        self.song_label.setStyleSheet("color: #666666;")

        # 二维码
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedSize(220, 220)

        # 控制按钮
        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.setFixedWidth(120)
        self.play_btn.clicked.connect(self._toggle_playback)

        btn_font = QFont("Microsoft YaHei", 12)
        self.play_btn.setFont(btn_font)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white;
                border: none; border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """)

        # 布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(self.cover_label, alignment=Qt.AlignCenter)
        layout.addSpacing(12)
        layout.addWidget(self.author_label)
        layout.addWidget(self.song_label)
        layout.addSpacing(16)
        layout.addWidget(self.qr_label, alignment=Qt.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(self.play_btn, alignment=Qt.AlignCenter)
        layout.addStretch(2)
        self.setLayout(layout)

    def _load_current_song(self):
        """加载当前歌曲信息"""
        if not self._songs or self._current_index >= len(self._songs):
            return
        cfg = self._songs[self._current_index]

        # 封面图片
        cover_path = cfg.get("cover_image", "")
        if cover_path:
            pix = load_cover_pixmap(cover_path, (320, 320))
            self.cover_label.setPixmap(pix)

        # 作者 & 歌曲名
        self.author_label.setText(cfg.get("author", "未知作者"))
        self.song_label.setText(cfg.get("song_name", "未知歌曲"))

        # 二维码
        song_url = cfg.get("song_url", "")
        if song_url:
            qr_pix = generate_qr_pixmap(song_url, 200)
            self.qr_label.setPixmap(qr_pix)

        # 音频文件
        audio_file = cfg.get("audio_file", "")
        if audio_file and Path(audio_file).exists():
            self._player.setMedia(
                QMediaContent(QUrl.fromLocalFile(str(Path(audio_file).resolve())))
            )

    def _toggle_playback(self):
        """切换播放/暂停"""
        state = self._player.state()
        if state == QMediaPlayer.PlayingState:
            self._player.pause()
            self.play_btn.setText("▶ 播放")
        else:
            self._player.play()
            self.play_btn.setText("⏸ 暂停")

    def set_songs(self, songs: List[dict]):
        """更新歌曲列表并重新加载"""
        self._songs = songs
        self._current_index = 0
        self._load_current_song()


# ── 主窗口 ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._config = load_config(CONFIG_FILE)

        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self):
        self.setWindowTitle("Timer & Player")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._center()

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 左侧：音乐播放器 ──
        left_widget = MusicPlayerWidget(self._config)
        left_widget.setStyleSheet("background-color: #f5f5f5;")
        main_layout.addWidget(left_widget, 6)  # 60%

        # ── 右侧：计时器 ──
        self.timer_widget = TimerWidget()
        self.timer_widget.setStyleSheet("background-color: #ffffff;")
        self.timer_widget.load_text(TIMER_TEXT_FILE)
        main_layout.addWidget(self.timer_widget, 4)  # 40%

        # 状态栏
        self.statusBar().showMessage(
            "就绪  |  Ctrl+F 切换计时  |  Ctrl+R 重置计时"
        )

    def _center(self):
        """窗口居中"""
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+F: 切换计时
        toggle_action = QAction("切换计时", self)
        toggle_action.setShortcut("Ctrl+F")
        toggle_action.triggered.connect(self.timer_widget.toggle)
        self.addAction(toggle_action)

        # Ctrl+R: 重置计时
        reset_action = QAction("重置计时", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.timer_widget.reset)
        self.addAction(reset_action)

    def closeEvent(self, event):
        """关闭确认"""
        reply = QMessageBox.question(
            self, "退出", "确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        """按 Esc 关闭窗口"""
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)


# ── 入口 ──────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 全局样式
    app.setStyleSheet("""
        QMainWindow { background-color: #fafafa; }
        QStatusBar {
            background-color: #e8e8e8; color: #555; font-size: 12px;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()