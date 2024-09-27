from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QBrush, QColor, QFont, QPainter


class LEDIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = {
            'skaal_red': QColor('#9E2A2C'), 
            'skaal_gray': QColor('#8E8D8D'), 
            'skaal_green': QColor("#0B782A")
        }
        self.reset()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self.color))
        self.drawLED(painter)
    
    def drawLED(self, painter): ...

    def resize(self, width, height):
        self.setFixedSize(width, height)
        
    def reset(self):
        self.color = self.colors['skaal_gray']
        self.update()

    def on(self):
        self.color = self.colors['skaal_green']
        self.update()

    def off(self):
        self.color = self.colors['skaal_red']
        self.update()


class ConnectionIndicator(LEDIndicator):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.led_size = 14
        self.font_size = 10

    def drawLED(self, painter):
        painter.setFont(QFont("Arial", self.font_size))
        painter.drawText(self.width()-65, int((self.height()+self.font_size)/2), "Status")
        painter.drawEllipse(self.width()-20, (self.height()-self.led_size)/2, self.led_size, self.led_size)
