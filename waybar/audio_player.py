import sys
import dbus
import requests

from PIL import Image
from io import BytesIO
from urllib.parse import unquote
from dbus.mainloop.glib import DBusGMainLoop

from PyQt6.QtCore import Qt, QTimer
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
                    with open(unquote(art_url[7:]), 'rb') as f:
                        image_data = f.read()
                except:
                    pass
            
            elif art_url.startswith(('http://', 'https://')):
                r = requests.get(art_url, timeout=5)
                if r.status_code == 200:
                    image_data = r.content
            
            if not image_data:
                return None
            
            image = Image.open(BytesIO(image_data)).convert('RGB')
            image = image.resize((size, size), Image.Resampling.LANCZOS)
            
            qimage = QImage(
                image.tobytes('raw', 'RGB'),
                size, size,
                size * 3,
                QImage.Format.Format_RGB888
            )
            
            pixmap = QPixmap.fromImage(qimage)
            pixmap = AlbumArtLoader.rounded_pixmap(pixmap, 14)
            label.setPixmap(pixmap)
        except Exception as exception:
            print('AlbumArt error:', exception)
            label.clear()


class MPRIS:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        
        self.bus = dbus.SessionBus()
        self.current_player = None
        self.properties = None
        self.player = None
        self.last_art = None
    
    
    def get_players(self):
        return [
            s for s in self.bus.list_names()
            if s.startswith('org.mpris.MediaPlayer2.')
        ]
    
    
    def connect(self, name):
        try:
            obj = self.bus.get_object(name, '/org/mpris/MediaPlayer2')
            
            self.properties = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
            self.player = dbus.Interface(obj, 'org.mpris.MediaPlayer2.Player')
            self.current_player = name
            
            return True
        except:
            return False
    
    
    def metadata(self):
        if not self.properties:
            return {}
        
        md = self.properties.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        
        return {
            'title': md.get('xesam:title', ''),
            'artist': ', '.join(md.get('xesam:artist', [])),
            'art': md.get('mpris:artUrl', ''),
            'length': md.get('mpris:length', 0) / 1_000_000
        }
    
    
    def position(self):
        try:
            return self.properties.Get(
                'org.mpris.MediaPlayer2.Player',
                'Position'
            ) / 1_000_000
        except:
            return 0
    
    
    def status(self):
        try:
            return str(self.properties.Get(
                'org.mpris.MediaPlayer2.Player', 'PlaybackStatus'
            ))
        except:
            return 'Stopped'
    
    
    def play_pause(self):
        if self.player:
            self.player.PlayPause()
    
    
    def next(self):
        if self.player:
            self.player.Next()
    
    
    def prev(self):
        if self.player:
            self.player.Previous()


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
    
    
    def build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        
        art_container = QWidget()
        art_container.setObjectName('art-box')
        art_container.setStyleSheet(
            """
            background-color: rgba(32, 29, 42, 0.85);
            border-radius: 20px;
            """
        )
        art_layout = QVBoxLayout(art_container)
        art_layout.setContentsMargins(8, 8, 8, 8)
        self.art = QLabel()
        self.art.setFixedSize(184, 184)
        self.art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.art.setStyleSheet(
            """
            background-color: rgba(10, 9, 8, 0.85);
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
            border-radius: 10px;
            color: #efebff;
            """
        )
        text_l = QVBoxLayout(text_box)
        text_l.setContentsMargins(12, 12, 12, 12)
        self.title = QLabel("Нет подключения")
        self.title.setFixedSize(176, 18)
        self.title.setStyleSheet(
            """
            font-size: 14px;
            background: none;
            """
        )
        self.artist = QLabel("")
        self.artist.setFixedSize(176, 14)
        self.artist.setStyleSheet(
            """
            font-size: 10px;
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
        slider_box.setFixedSize(200, 40)
        slider_box.setStyleSheet(
            """
            background-color: rgba(32, 29, 42, 0.85);
            border-radius: 8px;
            color: #efebff;
            """
        )
        slider_l = QHBoxLayout(slider_box)
        slider_l.setContentsMargins(12, 8, 12, 8)
        self.time = QLabel("0:00")
        self.time.setStyleSheet(
            """
            background: none;
            font-size: 9px;
            """
        )
        self.duration = QLabel("0:00")
        self.duration.setStyleSheet(
            """
            background: none;
            font-size: 9px;
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
        controls.setFixedSize(200, 60)
        cl = QHBoxLayout(controls)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)
        self.prev = QPushButton("")
        self.play = QPushButton("")
        self.next = QPushButton("")
        for button in (self.prev, self.play, self.next):
            button.setFixedSize(60, 60)
            button.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(32, 29, 42, 0.85);
                    border-radius: 10px;
                    color: #efebff;
                    text-align: center;
                    font-size: 18px;
                }
                
                QPushButton:hover {
                    background-color: rgba(10, 9, 8, 0.85);
                }
                """
            )
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev.clicked.connect(self.mpris.prev)
        self.play.clicked.connect(self.mpris.play_pause)
        self.next.clicked.connect(self.mpris.next)
        cl.addWidget(self.prev)
        cl.addWidget(self.play)
        cl.addWidget(self.next)
        root.addWidget(controls)
    
    
    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(500)
    
    
    def update(self):
        def set_elided_text(label: QLabel, text: str):
            fm = QFontMetrics(label.font())
            elided = fm.elidedText(text, Qt.TextElideMode.ElideRight, label.width())
            label.setText(elided)
        
        if not self.mpris.current_player:
            for p in self.mpris.get_players():
                if self.mpris.connect(p):
                    break
            
            return None
        
        md = self.mpris.metadata()
        
        set_elided_text(self.title, md.get('title', ''))
        set_elided_text(self.artist, md.get('artist', ''))
        
        if md.get('art') != self.mpris.last_art:
            self.mpris.last_art = md.get('art')
            
            AlbumArtLoader.load_artwork(md.get('art'), self.art)
        
        pos = self.mpris.position()
        dur = md.get('length', 0)
        
        if dur:
            self.slider.setRange(0, int(dur))
            self.slider.setValue(int(pos))
            self.time.setText(f"{int(pos)//60}:{int(pos)%60:02d}")
            self.duration.setText(f"{int(dur)//60}:{int(dur)%60:02d}")
        
        self.play.setText("" if self.mpris.status() == 'Playing' else "")
    
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = AudioPlayer()
    w.show()
