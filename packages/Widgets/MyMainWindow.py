# -*- coding: utf-8 -*-
import os
from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor
from PySide6.QtCore import Qt, QPointF


def create_checkmark_pixmap(size=12, color="#666666", thickness=2):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    pen = QPen(QColor(color))
    pen.setWidth(int(thickness))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    
    padding = 2
    points = [
        QPointF(padding, size / 2),
        QPointF(size / 2 - 1, size - padding),
        QPointF(size - padding, padding)
    ]
    
    for i in range(len(points) - 1):
        painter.drawLine(points[i], points[i + 1])
    
    painter.end()
    
    return pixmap


class MyMainWindow(QMainWindow):
    _checkmark_pixmap = None
    
    def __init__(self, args=None, parent=None):
        super().__init__(parent)
        self.args = args or []
    
    def apply_light_theme(self):
        if MyMainWindow._checkmark_pixmap is None:
            MyMainWindow._checkmark_pixmap = create_checkmark_pixmap(12, "#666666", 2)
        
        temp_path = os.path.join(os.path.dirname(__file__), '..', 'Styles', 'icons', 'checkmark.png')
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        MyMainWindow._checkmark_pixmap.save(temp_path)
        
        checkbox_style = f"""
            QCheckBox {{
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 12px;
                height: 12px;
                border: 1px solid #999999;
                border-radius: 2px;
                background-color: #ffffff;
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid #0078d4;
            }}
            QCheckBox::indicator:disabled {{
                border: 1px solid #cccccc;
                background-color: #f0f0f0;
            }}
            QCheckBox::indicator:checked {{
                background-color: #ffffff;
                border: 1px solid #999999;
                image: url({temp_path.replace(os.sep, '/')});
            }}
            QCheckBox::indicator:unchecked {{
                background-color: #ffffff;
                border: 1px solid #999999;
            }}
        """
        
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: #f5f5f5; }}
            QWidget {{ background-color: #f5f5f5; color: #000000; }}
            QTabWidget::pane {{ border: 1px solid #ccc; background-color: #ffffff; }}
            QTabBar::tab {{ background-color: #e0e0e0; color: #000000; padding: 8px 16px; border: 1px solid #ccc; }}
            QTabBar::tab:selected {{ background-color: #0078d4; color: #ffffff; }}
            QTableWidget {{ background-color: #ffffff; color: #000000; gridline-color: #ccc; }}
            QTableWidget::item:hover {{ background-color: #e6f2ff; }}
            QTableWidget::item:selected {{ background-color: #b3d9ff; color: #000000; }}
            QTableWidget::item:selected:!active {{ background-color: #b3d9ff; color: #000000; }}
            QHeaderView::section {{ background-color: #e0e0e0; color: #000000; padding: 4px; border: 1px solid #ccc; }}
            QPushButton {{ background-color: #e0e0e0; color: #000000; border: 1px solid #ccc; padding: 6px 12px; }}
            QPushButton:hover {{ background-color: #d0d0d0; }}
            QPushButton:pressed {{ background-color: #c0c0c0; }}
            QLineEdit {{ background-color: #ffffff; color: #000000; border: 1px solid #ccc; padding: 4px; }}
            QComboBox {{ background-color: #ffffff; color: #000000; border: 1px solid #ccc; padding: 4px; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background-color: #ffffff; color: #000000; selection-background-color: #0078d4; selection-color: #ffffff; }}
            {checkbox_style}
            QSpinBox, QDoubleSpinBox {{ background-color: #ffffff; color: #000000; border: 1px solid #ccc; }}
            QLabel {{ color: #000000; }}
            QGroupBox {{ color: #000000; border: 1px solid #ccc; margin-top: 8px; padding-top: 8px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 8px; }}
            QProgressBar {{ background-color: #e0e0e0; border: 1px solid #ccc; text-align: center; }}
            QProgressBar::chunk {{ background-color: #0078d4; }}
        """)
