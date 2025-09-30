import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, 
                              QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRect, QPoint
from enum import Enum

class CaptureMode(Enum):
    SINGLE = "single"
    MANUAL = "manual"

class SnippingWidget(QWidget):
    def __init__(self, mode=CaptureMode.SINGLE):
        super().__init__()
        
        self.mode = mode
        self.captures = []  # Store multiple captures in manual mode
        self.current_capture_type = None  # Track what we're capturing
        
        # -- Window Setup --
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # -- Initialize Variables --
        self.is_snipping = False
        self.begin_point = None
        self.end_point = None
        
        # Setup UI based on mode
        self.setup_ui()
        
    def setup_ui(self):
        """Setup control buttons and instructions"""
        # Create container for controls
        self.control_widget = QWidget(self)
        self.control_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 230);
                border-radius: 8px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton#exitBtn {
                background-color: #f44336;
            }
            QPushButton#exitBtn:hover {
                background-color: #d32f2f;
            }
            QPushButton#captureBtn {
                background-color: #4CAF50;
            }
            QPushButton#captureBtn:hover {
                background-color: #388E3C;
            }
            QLabel {
                color: white;
                font-size: 12px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(self.control_widget)
        
        # Instructions label
        self.instruction_label = QLabel()
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(self.instruction_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        if self.mode == CaptureMode.SINGLE:
            self.instruction_label.setText("Draw a rectangle to capture the entire event")
            
            exit_btn = QPushButton("Exit")
            exit_btn.setObjectName("exitBtn")
            exit_btn.setFixedSize(100, 35)
            exit_btn.clicked.connect(self.close)
            button_layout.addWidget(exit_btn)
            
        else:  # Manual mode
            self.instruction_label.setText("Click a button below, then draw a rectangle")
            
            # Capture type buttons
            title_btn = QPushButton("Capture Title")
            title_btn.setObjectName("captureBtn")
            title_btn.setFixedSize(120, 35)
            title_btn.clicked.connect(lambda: self.start_capture("title"))
            button_layout.addWidget(title_btn)
            
            date_btn = QPushButton("Capture Date")
            date_btn.setObjectName("captureBtn")
            date_btn.setFixedSize(120, 35)
            date_btn.clicked.connect(lambda: self.start_capture("date"))
            button_layout.addWidget(date_btn)
            
            time_btn = QPushButton("Capture Time")
            time_btn.setObjectName("captureBtn")
            time_btn.setFixedSize(120, 35)
            time_btn.clicked.connect(lambda: self.start_capture("time"))
            button_layout.addWidget(time_btn)
            
            location_btn = QPushButton("Capture Location")
            location_btn.setObjectName("captureBtn")
            location_btn.setFixedSize(130, 35)
            location_btn.clicked.connect(lambda: self.start_capture("location"))
            button_layout.addWidget(location_btn)
            
            # Finish and Exit buttons
            finish_btn = QPushButton("Finish & Process")
            finish_btn.setFixedSize(140, 35)
            finish_btn.clicked.connect(self.finish_captures)
            button_layout.addWidget(finish_btn)
            
            exit_btn = QPushButton("Cancel")
            exit_btn.setObjectName("exitBtn")
            exit_btn.setFixedSize(100, 35)
            exit_btn.clicked.connect(self.close)
            button_layout.addWidget(exit_btn)
        
        layout.addLayout(button_layout)
        
        # Position control widget at top center
        self.control_widget.setFixedHeight(100)
        self.position_controls()
        
    def position_controls(self):
        """Position control widget at top center of screen"""
        screen_width = self.width()
        widget_width = self.control_widget.sizeHint().width() + 40
        x = (screen_width - widget_width) // 2
        self.control_widget.setGeometry(x, 20, widget_width, 100)
        
    def resizeEvent(self, event):
        """Reposition controls when window is resized"""
        super().resizeEvent(event)
        self.position_controls()
        
    def start_capture(self, capture_type):
        """Prepare to capture a specific type of information"""
        self.current_capture_type = capture_type
        self.instruction_label.setText(f"Drawing rectangle for: {capture_type.upper()}")
        self.control_widget.setStyleSheet(self.control_widget.styleSheet() + """
            QWidget {
                border: 3px solid #4CAF50;
            }
        """)
        
    def mousePressEvent(self, event):
        # Ignore clicks on control widget
        if self.control_widget.geometry().contains(event.pos()):
            return
            
        # Only allow snipping if in single mode or a capture type is selected
        if self.mode == CaptureMode.SINGLE or self.current_capture_type:
            self.is_snipping = True
            self.begin_point = event.pos()
            self.end_point = event.pos()
            self.update()
        
    def mouseMoveEvent(self, event):
        if self.is_snipping:
            self.end_point = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if not self.is_snipping:
            return
            
        self.is_snipping = False
        
        if self.mode == CaptureMode.SINGLE:
            # Single capture mode - capture and close
            self.capture_screen()
            self.close()
        else:
            # Manual mode - capture region and continue
            if self.current_capture_type:
                self.capture_region(self.current_capture_type)
                self.current_capture_type = None
                self.instruction_label.setText("Capture complete! Select another or click Finish")
                # Reset border
                self.setup_ui()
        
        # Reset selection
        self.begin_point = None
        self.end_point = None
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw semi-transparent overlay
        overlay_color = QColor(0, 0, 0, 120)
        painter.fillRect(self.rect(), overlay_color)
        
        # Draw previous captures in manual mode
        if self.mode == CaptureMode.MANUAL:
            for capture in self.captures:
                rect = capture['rect']
                # Highlight captured areas
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                highlight_color = QColor(76, 175, 80, 60)  # Green tint
                painter.fillRect(rect, highlight_color)
                
                # Draw border
                pen = QPen(QColor(76, 175, 80), 2, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawRect(rect)
                
                # Draw label
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.setPen(Qt.GlobalColor.white)
                label_rect = QRect(rect.x(), rect.y() - 20, 200, 20)
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft, 
                               f"✓ {capture['type'].upper()}")
        
        # Draw current selection
        if self.is_snipping and self.begin_point and self.end_point:
            selection_rect = QRect(self.begin_point, self.end_point).normalized()
            
            # Clear the area inside selection
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # Draw border
            border_color = QColor(33, 150, 243) if self.mode == CaptureMode.SINGLE else QColor(76, 175, 80)
            pen = QPen(border_color, 3, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(selection_rect)
            
            # Draw dimensions
            painter.setFont(QFont("Arial", 9))
            painter.setPen(Qt.GlobalColor.white)
            dims = f"{selection_rect.width()} × {selection_rect.height()}"
            painter.drawText(selection_rect.x(), selection_rect.y() - 5, dims)
    
    def capture_screen(self, filename="capture.png"):
        """Capture single screenshot"""
        if not self.begin_point or not self.end_point:
            return
            
        capture_rect = QRect(self.begin_point, self.end_point).normalized()
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0, capture_rect.x(), capture_rect.y(), 
                                   capture_rect.width(), capture_rect.height())
        pixmap.save(filename, "png")
        print(f"Screenshot saved as {filename}")
    
    def capture_region(self, capture_type):
        """Capture a labeled region in manual mode"""
        if not self.begin_point or not self.end_point:
            return
            
        capture_rect = QRect(self.begin_point, self.end_point).normalized()
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0, capture_rect.x(), capture_rect.y(),
                                   capture_rect.width(), capture_rect.height())
        
        # Save with labeled filename
        filename = f"capture_{capture_type}.png"
        pixmap.save(filename, "png")
        
        # Store capture info
        self.captures.append({
            'type': capture_type,
            'rect': capture_rect,
            'filename': filename
        })
        
        print(f"Captured {capture_type}: {filename}")
    
    def finish_captures(self):
        """Complete manual capture process"""
        if not self.captures:
            print("No captures made!")
            return
            
        print(f"\n{'='*50}")
        print(f"Manual Capture Complete: {len(self.captures)} regions captured")
        print(f"{'='*50}")
        
        for capture in self.captures:
            print(f"  • {capture['type'].upper()}: {capture['filename']}")
        
        print(f"{'='*50}\n")
        
        # Process captures here or return data
        # You can integrate with your OCR scanner here
        
        self.close()

class ModeSelectionWindow(QWidget):
    """Initial mode selection window"""
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Select Capture Mode")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        label = QLabel("Choose Capture Mode:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(label)
        
        btn_single = QPushButton("Single Capture Mode")
        btn_single.clicked.connect(self.start_single_mode)
        layout.addWidget(btn_single)
        
        btn_manual = QPushButton("Manual Multi-Region Mode")
        btn_manual.clicked.connect(self.start_manual_mode)
        layout.addWidget(btn_manual)
        
        self.setLayout(layout)
    
    def start_single_mode(self):
        """Launch Single Capture Mode"""

        self.close()
        self.snipping_widget = SnippingWidget(mode=CaptureMode.SINGLE)
        self.snipping_widget.showFullScreen()
    
    def start_manual_mode(self):
        self.close()
        self.snipping_widget = SnippingWidget(mode=CaptureMode.MANUAL)
        self.snipping_widget.showFullScreen()

class SnippingApp:
    """Main application wrapper"""
    
    @staticmethod
    def start_single_capture():
        """Start single capture mode"""
        app = QApplication(sys.argv)
        widget = SnippingWidget(mode=CaptureMode.SINGLE)
        widget.showFullScreen()
        sys.exit(app.exec())
    
    @staticmethod
    def start_manual_capture():
        """Start manual multi-region capture mode"""
        app = QApplication(sys.argv)
        widget = SnippingWidget(mode=CaptureMode.MANUAL)
        widget.showFullScreen()
        sys.exit(app.exec())


if __name__ == '__main__':
    # Choose mode
    app = QApplication(sys.argv)

    mode_window = ModeSelectionWindow()
    mode_window.show()
    sys.exit(app.exec())   
   