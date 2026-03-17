# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Qt, QRect, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF


class CustomCheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._check_color = QColor(0, 0, 0)
        self._border_color = QColor(51, 51, 51)
        self._hover_border_color = QColor(0, 120, 212)
        self._background_color = QColor(255, 255, 255)
        self._is_hovering = False
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        indicator_size = 18
        indicator_rect = QRect(0, (self.height() - indicator_size) // 2, indicator_size, indicator_size)
        
        painter.setBrush(QBrush(self._background_color))
        
        if self._is_hovering:
            painter.setPen(QPen(self._hover_border_color, 2))
        else:
            painter.setPen(QPen(self._border_color, 2))
        
        painter.drawRoundedRect(indicator_rect, 3, 3)
        
        if self.isChecked():
            pen = QPen(self._check_color, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            
            check_rect = indicator_rect.adjusted(4, 4, -4, -4)
            
            points = [
                (check_rect.left(), check_rect.center().y()),
                (check_rect.center().x() - 1, check_rect.bottom()),
                (check_rect.right(), check_rect.top())
            ]
            
            polygon = QPolygonF()
            for x, y in points:
                polygon.append(QPointF(x, y))
            
            painter.drawPolyline(polygon)
        
        painter.end()
        
        self.setStyleSheet("QCheckBox { spacing: 8px; }")
        
        super().paintEvent(event)
    
    def enterEvent(self, event):
        self._is_hovering = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._is_hovering = False
        self.update()
        super().leaveEvent(event)
