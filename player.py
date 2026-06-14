#! /usr/bin/env python3

import sys

from PyQt6.QtWidgets import (QApplication, QWidget, QToolTip, QPushButton, 
                             QMessageBox, QMainWindow, QMenu, QTextEdit)
from PyQt6.QtGui import (QContextMenuEvent, QFont, QIcon, QAction)


class Player(QMainWindow):
    """播放器主窗口类，继承自QMainWindow"""
    
    def __init__(self) -> None:
        """初始化播放器窗口"""
        super().__init__()
        
        self.initGUI()


    def initGUI(self) -> None:
        """初始化GUI组件"""
        # 设置字体
        QToolTip.setFont(QFont("Times New Roman", 12))
        # 设置窗口悬停提示
        self.setToolTip("Timer & Player")
        
        textEdit = QTextEdit()
        self.setCentralWidget(textEdit)
        
        # 设置 Exit 行动及快捷键
        exitAct = QAction(QIcon("exit24.png"), "Exit", self)
        exitAct.setShortcut("Ctrl+Q")
        exitAct.setStatusTip("Exit the application")
        exitAct.triggered.connect(QApplication.instance().quit)
        
        # 设置工具栏
        self.toolbar = self.addToolBar("Exit")
        self.toolbar.addAction(exitAct)
        
        # 设置状态栏
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Ready")
        
        # 设置菜单栏
        menuBar = self.menuBar()
        # 添加 File 菜单
        fileMenu = menuBar.addMenu("&File")
        # 在 File 菜单中添加 Exit 行动
        fileMenu.addAction(exitAct)
        
        impMenu = QMenu("Import", self)
        impAct = QAction("Import file", self)
        impMenu.addAction(impAct)
        # 在 File 菜单中添加 Import 菜单
        fileMenu.addMenu(impMenu)
        
        viewMenu = menuBar.addMenu("&View")
        viewstatAct = QAction("View statusbar", self, checkable=True)
        viewstatAct.setStatusTip("View statusbar")
        viewstatAct.setChecked(True)
        viewstatAct.triggered.connect(self.toggleMenu)
        viewMenu.addAction(viewstatAct)
        
        # 创建计时器按钮
        start_button = QPushButton("Start", self)
        stop_button = QPushButton("Stop", self)
        reset_button = QPushButton("Reset", self)
        # 设置按钮悬停提示
        start_button.setToolTip("Start the timer")
        stop_button.setToolTip("Stop the timer")
        reset_button.setToolTip("Reset the timer")
        # 设置按钮位置
        start_button.move(50, 480)
        stop_button.move(150, 480)
        reset_button.move(250, 480)
        # 设置退出按钮
        exit_button = QPushButton("Exit", self)
        exit_button.clicked.connect(QApplication.instance().quit)
        exit_button.setToolTip("Exit the application")
        exit_button.move(350, 480)
        
        # 显示窗口
        self.resize(1280, 720)
        self.center()
        self.setWindowTitle("Timer & Player")
        self.show()


    def center(self) -> None:
        """将窗口居中显示"""
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        
        qr.moveCenter(cp)
        self.move(qr.topLeft())


    def closeEvent(self, event: QCloseEvent | None) -> None:
        """关闭事件，弹出确认对话框"""
        reply = QMessageBox.question(self, "Exit", "Are you sure you want to exit?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


    def toggleMenu(self, state: bool) -> None:
        """切换状态栏显示"""
        if state:
            self.statusBar.show()
        else:
            self.statusBar.hide()


    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        """右键菜单事件，显示上下文菜单"""
        if not event:
            return
        contextMenu = QMenu(self)
        newAct = contextMenu.addAction("New")
        openAct = contextMenu.addAction("Open")
        quitAct = contextMenu.addAction("Quit")
        action = contextMenu.exec(self.mapToGlobal(event.pos()))
        
        if action == quitAct:
            QApplication.instance().quit()

def main() -> None:
    """主函数，创建应用程序和窗口"""
    MusicPlayer = QApplication(sys.argv)
    # 设置窗口
    player = Player()
    
    sys.exit(MusicPlayer.exec())

if __name__ == "__main__":
    """实现简单的计时器和播放器界面"""
    main()