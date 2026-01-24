import sys
import dbus
import requests
import traceback

from PIL import Image
from io import BytesIO
from urllib.parse import unquote
from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QPoint
)
from dbus.mainloop.glib import DBusGMainLoop
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QPainter,
    QPainterPath,
    QFontMetrics
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QHBoxLayout
)


class AlbumArtLoader:
    @staticmethod
    def rounded_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
        size = pixmap.size()
        
        rounded = QPixmap(size)
        rounded.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
        
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        return rounded
    
    
    @staticmethod
    def load_artwork(art_url, label, size=184):
        if not art_url:
            label.clear()
            
            return None
        
        try:
            image_data = None
            
            if art_url.startswith('file://'):
                try:
                    with open(unquote(art_url[7:]), 'rb') as file:
                        image_data = file.read()
                except:
                    pass
            
            elif art_url.startswith(('http://', 'https://')):
                request = requests.get(art_url, timeout=5)
                
                if request.status_code == 200:
                    image_data = request.content
            
            if not image_data:
                return None
            
            image = Image.open(BytesIO(image_data)).convert('RGB')
            image = image.resize((size, size), Image.Resampling.LANCZOS)
            
            q_image = QImage(
                image.tobytes('raw', 'RGB'),
                size, size,
                size * 3,
                QImage.Format.Format_RGB888
            )
            
            pixmap = QPixmap.fromImage(q_image)
            pixmap = AlbumArtLoader.rounded_pixmap(pixmap, 14)
            
            label.setPixmap(pixmap)
        except Exception as exception:
            print(exception)
            label.clear()


class MPRIS:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        
        self.bus = dbus.SessionBus()
        self.current_player = None
        self.properties = None
        self.player = None
        self.last_art = None
        self.connected = False
    
    
    def get_players(self):
        try:
            return [
                player for player in self.bus.list_names()
                if player.startswith('org.mpris.MediaPlayer2.')
            ]
        except:
            return []
    
    
    def disconnect(self):
        self.connected = False
        self.current_player = None
        self.properties = None
        self.player = None
    
    
    def _prioritised_players(self):
        players = self.get_players()
        
        if not players:
            return []
        
        
        def state_key(name):
            try:
                object = self.bus.get_object(name, '/org/mpris/MediaPlayer2')
                properties = dbus.Interface(object, 'org.freedesktop.DBus.Properties')
                string = str(
                    properties.Get(
                        'org.mpris.MediaPlayer2.Player',
                        'PlaybackStatus'
                    )
                )
                
                return {'Playing': 0, 'Paused': 1}.get(string, 2)
            except:
                return 3
        
        players.sort(key=lambda n: (state_key(n), n))
        
        return players
    
    
    def connect_any(self):
        self.disconnect()
        
        for candidate in self._prioritised_players():
            if self.connect(candidate):
                return True
        
        return False
    
    
    def connect(self, name):
        try:
            object = self.bus.get_object(name, '/org/mpris/MediaPlayer2')
            self.properties = dbus.Interface(
                object,
                'org.freedesktop.DBus.Properties'
            )
            self.player = dbus.Interface(object, 'org.mpris.MediaPlayer2.Player')
            self.current_player = name
            self.connected = True
            
            return True
        except:
            self.connected = False
            
            return False
    
    
    def metadata(self):
        if not self.properties or not self.connected:
            return {}
        try:
            metadata = self.properties.Get(
                'org.mpris.MediaPlayer2.Player',
                'Metadata'
            )
            
            return {
                'title': metadata.get('xesam:title', ''),
                'artist': ', '.join(metadata.get('xesam:artist', [])),
                'art': metadata.get('mpris:artUrl', ''),
                'length': metadata.get('mpris:length', 0) / 1_000_000
            }
        except dbus.exceptions.DBusException as e:
            if 'NoActivePlayer' in str(e) or 'No player' in str(e):
                self.disconnect()
            
            return {}
        except Exception:
            return {}
    
    
    def position(self):
        try:
            if not self.properties or not self.connected:
                return 0
            
            return self.properties.Get(
                'org.mpris.MediaPlayer2.Player',
                'Position'
            ) / 1_000_000
        except:
            return 0
    
    
    def status(self):
        try:
            if not self.properties or not self.connected:
                return 'Stopped'
            
            return str(
                self.properties.Get(
                    'org.mpris.MediaPlayer2.Player',
                    'PlaybackStatus'
                )
            )
        except:
            return 'Stopped'
    
    
    def play_pause(self):
        if self.player and self.connected:
            try:
                self.player.PlayPause()
            except:
                self.connected = False
    
    
    def next(self):
        if self.player and self.connected:
            try:
                self.player.Next()
            except:
                self.connected = False
    
    
    def prev(self):
        if self.player and self.connected:
            try:
                self.player.Previous()
            except:
                self.connected = False


class AudioPlayer(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.mpris = MPRIS()
        self.build_ui()
        self.start_timer()
        # self.animate_open()
    
    
    def build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        
        art_container = QWidget()
        art_container.setObjectName('art-box')
        art_container.setStyleSheet(
            """
            background-color: rgba(32, 29, 42, 0.85);
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
            """
        )
        art_layout = QVBoxLayout(art_container)
        art_layout.setContentsMargins(8, 8, 8, 0)
        self.art = QLabel()
        self.art.setFixedSize(184, 184)
        self.art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.art.setStyleSheet(
            """
            background-color: #aba3c7;
            border-radius: 14px;
            """
        )
        art_layout.addWidget(self.art)
        root.addWidget(art_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        text_box = QWidget()
        text_box.setObjectName('text-box')
        text_box.setFixedSize(200, 56)
        text_box.setStyleSheet(
            """
            background-color: rgba(32, 29, 42, 0.85);
            color: #efebff;
            """
        )
        text_l = QVBoxLayout(text_box)
        text_l.setContentsMargins(12, 12, 12, 12)
        self.title = QLabel('Нет подключения')
        self.title.setFixedSize(176, 18)
        self.title.setStyleSheet(
            """
            font-size: 14px;
            background: none;
            """
        )
        self.artist = QLabel('')
        self.artist.setFixedSize(176, 14)
        self.artist.setStyleSheet(
            """
            font-size: 12px;
            background: none;
            """
        )
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.title.setCursor(Qt.CursorShape.IBeamCursor)
        self.artist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artist.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.artist.setCursor(Qt.CursorShape.IBeamCursor)
        text_l.addWidget(self.title)
        text_l.addWidget(self.artist)
        root.addWidget(text_box)
        
        slider_box = QWidget()
        slider_box.setObjectName('slider-box')
        slider_box.setFixedSize(200, 12)
        slider_box.setContentsMargins(4, 0, 0, 0)
        slider_box.setStyleSheet(
            """
            background-color: rgba(32, 29, 42, 0.85);
            color: #efebff;
            """
        )
        slider_l = QHBoxLayout(slider_box)
        slider_l.setContentsMargins(12, 0, 12, 0)
        self.time = QLabel('0:00')
        self.time.setStyleSheet(
            """
            background: none;
            font-size: 10px;
            """
        )
        self.duration = QLabel('0:00')
        self.duration.setStyleSheet(
            """
            background: none;
            font-size: 10px;
            """
        )
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)
        self.slider.setStyleSheet(
            """
            QSlider {
                background: none;
            }
            QSlider::groove:horizontal {
                height: 8px;
                padding-left: 8px;
                padding-right: 2px;
                background-color: #aba3c7;
                border-radius: 4px;
            }
            
            QSlider::sub-page:horizontal {
                background-color: #9375f5;
                border-radius: 4px;
            }
            
            QSlider::add-page:horizontal {
                background: none;
            }
            
            QSlider::handle:horizontal {
                background: none;
            }
            """
        )
        slider_l.addWidget(self.time)
        slider_l.addWidget(self.slider, 1)
        slider_l.addWidget(self.duration)
        root.addWidget(slider_box)
        
        controls = QWidget()
        controls.setObjectName('controls')
        controls.setFixedSize(200, 72)
        controls.setStyleSheet(
            """
            background-color: rgba(32, 29, 42, 0.85);
            border-bottom-left-radius: 20px;
            border-bottom-right-radius: 20px;
            """
        )
        cl = QHBoxLayout(controls)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        
        self.prev = QPushButton('  ')
        self.play = QPushButton('')
        self.next = QPushButton(' ')
        
        for button in (self.prev, self.play, self.next):
            button.setFixedSize(56, 56)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setContentsMargins(8, 0, 0, 0)
            button.setStyleSheet(
                """
                QPushButton {
                    background-color: #9375f5;
                    border-radius: 14px;
                    color: #efebff;
                    font-size: 18px;
                }
                
                QPushButton:hover {
                    background-color: #aba3c7;
                }
                """
            )
        
        self.prev.clicked.connect(self.mpris.prev)
        self.play.clicked.connect(self.mpris.play_pause)
        self.next.clicked.connect(self.mpris.next)
        cl.addWidget(self.prev)
        cl.addWidget(self.play)
        cl.addWidget(self.next)
        root.addWidget(controls)
    
    
    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(500)
    
    
    """def animate_open(self):
        screen = QApplication.primaryScreen().availableGeometry()
        start_pos = QPoint(screen.width() // 2 - self.width() // 2, -self.height())
        end_pos = QPoint(screen.width() // 2 - self.width() // 2, 100)  # конечная позиция на экране
        
        self.move(start_pos)
        self.setWindowOpacity(0)  # полностью прозрачный
        
        # Анимация позиции
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(600)  # миллисекунды
        self.pos_anim.setStartValue(start_pos)
        self.pos_anim.setEndValue(end_pos)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)  # плавное движение
        
        # Анимация прозрачности
        self.opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim.setDuration(600)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.Linear)
        
        # Запускаем одновременно
        self.pos_anim.start()
        self.opacity_anim.start()"""
    
    
    def animate_close(self):
        pass
    
    
    def update_ui(self):
        def set_elided_text(label: QLabel, text: str):
            font_metrics = QFontMetrics(label.font())
            elided_text = font_metrics.elidedText(text, Qt.TextElideMode.ElideRight, label.width())
            label.setText(elided_text)
        
        if not self.mpris.connected or not self.mpris.current_player:
            players = self.mpris.get_players()
            connected = False
            
            for p in players:
                if self.mpris.connect(p):
                    connected = True
                    
                    break
            
            if not connected:
                self.title.setText('Нет активного проигрывателя')
                self.artist.setText('')
                self.art.clear()
                self.time.setText('0:00')
                self.duration.setText('0:00')
                self.slider.setValue(0)
                self.play.setText('')
                
                return None
        
        try:
            metadata = self.mpris.metadata()
            
            if not metadata:
                self.mpris.connected = False
                self.title.setText('Нет активного проигрывателя')
                self.artist.setText('')
                
                return None
            
            set_elided_text(self.title, metadata.get('title', 'Без названия') or 'Без названия')
            set_elided_text(self.artist, metadata.get('artist', 'Неизвестный исполнитель') or 'Неизвестный исполнитель')
            
            if metadata.get('art') != self.mpris.last_art:
                self.mpris.last_art = metadata.get('art')
                AlbumArtLoader.load_artwork(metadata.get('art'), self.art)
            
            position = self.mpris.position()
            duration = metadata.get('length', 0)
            
            if duration:
                self.slider.setRange(0, int(duration))
                self.slider.setValue(int(position))
                self.time.setText(f'{int(position)//60}:{int(position)%60:02d}')
                self.duration.setText(f'{int(duration)//60}:{int(duration)%60:02d}')
            
            status = self.mpris.status()
            self.play.setText('' if status == 'Playing' else '')
            
        except Exception as exception:
            print(exception)
            traceback.print_exc()
            
            self.mpris.connected = False
    
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()


if __name__ == '__main__':
    application = QApplication(sys.argv)
    widget = AudioPlayer()
    widget.show()
    sys.exit(application.exec())
