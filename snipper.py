import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QRect

class SnippingWidget(QWidget):
    def __init__(self):
        super().__init__()

        # -- Window Setup --
        # Make window frameless, fullscreen
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # Makes the background transparent

        # -- Initialize Variables --
        self.is_snipping = False
        self.begin_point = None
        self.end_point = None

    def mousePressEvent(self, event):
        self.is_snipping = True
        self.begin_point = event.pos()
        self.end_point = event.pos()
        self.update # Repaint

    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        # On mouse release, stop snipping
        self.is_snipping = False
        
        # Perform the screen capture
        self.capture_screen()
        
        # Close the snipping widget
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw the semi-transparent overlay over the entire screen
        overlay_color = QColor(0, 0, 0, 120) # Black with ~50% opacity
        painter.fillRect(self.rect(), overlay_color)

        if self.is_snipping:
            # Create the selection rectangle from the start and end points
            selection_rect = QRect(self.begin_point, self.end_point).normalized()
            
            # Clear the area inside the selection rectangle, making it visible
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Draw a border around the selection
            pen = QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(selection_rect)

    def capture_screen(self):
        # Define the rectangle to capture
        capture_rect = QRect(self.begin_point, self.end_point).normalized()
        
        # Grab the content of the root window (the entire screen)
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0, capture_rect.x(), capture_rect.y(), capture_rect.width(), capture_rect.height())
        
        # Save the captured pixmap to a file
        pixmap.save("capture.png", "png")
        print("Screenshot saved as capture.png")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    snipping_widget = SnippingWidget()
    snipping_widget.showFullScreen()
    sys.exit(app.exec())