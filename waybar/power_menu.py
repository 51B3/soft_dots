import sys
import subprocess

from PyQt6.QtCore import (
    Qt,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QEasingCurve,
    QTimer
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton
)


class PowerMenu(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.commands = [
            ('S', ['systemctl', 'poweroff']),
            ('󰌾', ['hyprlock']),
            ('', ['systemctl', 'reboot']),
            ('', ['hyprctl', 'dispatch', 'exit']),
        ]
        self.buttons = []
        self.animations = []
        
        for text, command in self.commands:
            button = QPushButton(text, self)
            button.setFixedSize(40, 40)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.move(8, 8)
            button.clicked.connect(
                lambda _, command=command: self.execute(command)
            )
            
            self.buttons.append(button)
        
        self.resize(56, 200)
        self.show()
        self.animate_open()
    
    
    def animate_open(self):
        count = len(self.buttons)
        
        self.animations.clear()
        
        for i, button in enumerate(self.buttons):
            animation = QPropertyAnimation(button, b'pos', self)
            animation.setStartValue(QPoint(8, 8))
            animation.setEndValue(QPoint(8, 8 + i * 48))
            animation.setDuration(180)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            self.animations.append(animation)
            
            QTimer.singleShot(
                (count - 1 - i) * 90,
                animation.start
            )
    
    
    def animate_close(self):
        count = len(self.buttons)
        
        self.animations.clear()
        
        for i, button in enumerate(self.buttons):
            animation = QPropertyAnimation(button, b'pos', self)
            animation.setStartValue(button.pos())
            animation.setEndValue(QPoint(8, 8))
            animation.setDuration(180)
            animation.setEasingCurve(QEasingCurve.Type.InCubic)
            self.animations.append(animation)
            
            QTimer.singleShot(
                i * 90,
                animation.start
            )
            
            if i == count - 1:
                animation.finished.connect(QApplication.quit)
    
    
    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.animate_close()
        
        super().changeEvent(event)
    
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.animate_close()
    
    
    def execute(self, command):
        subprocess.Popen(command)
        QApplication.quit()


if __name__ == '__main__':
    application = QApplication(sys.argv)
    widget = PowerMenu()
    widget.setStyleSheet(
        """
        QPushButton {
            background-color: #9375f5;
            color: #efebff;
            border-radius: 20px;
            font-size: 14px;
        }
        """
    )
    sys.exit(application.exec())
