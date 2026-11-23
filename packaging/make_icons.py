"""Draw the app icon with Qt and write icon.png / icon.ico / icon.icns next to this file."""
import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter

here = Path(__file__).parent
app = QGuiApplication(sys.argv)
img = QImage(512, 512, QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
p.setBrush(QColor("#2b579a"))                      # Word-ish blue
p.setPen(Qt.NoPen)
p.drawRoundedRect(QRectF(16, 16, 480, 480), 96, 96)
p.setBrush(QColor("white"))                        # sound-wave bars
for i, h in enumerate([120, 220, 300, 220, 120]):
    p.drawRoundedRect(QRectF(106 + i * 66, 256 - h / 2, 36, h), 18, 18)
p.end()
img.save(str(here / "icon.png"))
img.save(str(here / "icon.ico"))
try:
    img.save(str(here / "icon.icns"))
except Exception:
    pass
