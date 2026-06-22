# -*- coding: utf-8 -*-
"""可复用的浮动重排序按钮组件。

用于 Audio/Subtitle/Attachment 三个 Tab 中的文件列表重排序。
提供统一的浮动按钮UI、淡出动画和点击外部自动隐藏功能。

用法:
    self.floating_btns = FloatingReorderButtons(self.xxx_table)
    self.floating_btns.move_up.connect(self.move_xxx_up)
    self.floating_btns.move_down.connect(self.move_xxx_down)

    # 在 itemClicked 中显示
    self.floating_btns.show_for_row(row, global_pos)

    # 在 hideEvent / mousePressEvent 中隐藏
    self.floating_btns.hide_buttons()
    # 或自动检测点击外部
    self.floating_btns.check_click_outside(global_pos)
"""
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton


_STYLE_SHEET = """
    QFrame {
        background-color: #f0f0f0;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    QPushButton {
        background-color: #ffffff;
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 2px 8px;
        min-width: 30px;
    }
    QPushButton:hover {
        background-color: #e0e0e0;
    }
    QPushButton:pressed {
        background-color: #d0d0d0;
    }
"""


class FloatingReorderButtons(QFrame):
    """浮动上移/下移按钮组件，内置自动隐藏和淡出动画。"""

    move_up = Signal(int)      # row: 当前选中行
    move_down = Signal(int)    # row: 当前选中行

    def __init__(self, parent_table, parent=None):
        super().__init__(parent_table)
        self._parent_table = parent_table

        # 窗口标志：无边框浮窗
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(_STYLE_SHEET)

        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        self._up_btn = QPushButton("↑上移")
        self._up_btn.setFixedHeight(24)
        self._up_btn.clicked.connect(self._on_up_clicked)

        self._down_btn = QPushButton("↓下移")
        self._down_btn.setFixedHeight(24)
        self._down_btn.clicked.connect(self._on_down_clicked)

        layout.addWidget(self._up_btn)
        layout.addWidget(self._down_btn)

        # 鼠标悬停控制
        self.enterEvent = self._on_frame_enter
        self.leaveEvent = self._on_frame_leave

        # 自动隐藏计时器与淡出动画
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)
        self._fade_animation = None

        self._current_row = -1
        self.hide()

    # ── 公开 API ─────────────────────────────────────────

    def show_for_row(self, row, global_pos=None):
        """在指定行显示按钮。

        Args:
            row: 目标行号 (0-based)
            global_pos: 鼠标全局坐标 (QPoint)，用于定位按钮
        """
        self._hide_timer.stop()
        self._stop_animation()

        if row < 0 or row >= self._parent_table.rowCount():
            self.hide()
            return

        self._current_row = row

        # 计算按钮位置
        if global_pos:
            x = global_pos.x() - self.sizeHint().width() - 10
            y = global_pos.y() - self.sizeHint().height() // 2
        else:
            # 回退：以当前行的右侧为基准
            item = self._parent_table.item(row, 1)
            if item is None:
                self.hide()
                return
            rect = self._parent_table.visualItemRect(item)
            table_pos = self._parent_table.mapToGlobal(rect.topRight())
            x = table_pos.x() - self.sizeHint().width() - 5
            y = table_pos.y() + (rect.height() - self.sizeHint().height()) // 2

        self.move(x, y)
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()

        self._up_btn.setEnabled(row > 0)
        self._down_btn.setEnabled(row < self._parent_table.rowCount() - 1)

        self._hide_timer.start(3000)

    def hide_buttons(self):
        """立即隐藏按钮并停止所有计时器/动画。"""
        self._hide_timer.stop()
        self._stop_animation()
        self.hide()

    def check_click_outside(self, global_pos):
        """检查全局坐标是否在表格和浮动按钮之外，若是则自动隐藏。

        Args:
            global_pos: 鼠标全局坐标

        Returns:
            bool: True 表示点击在外部并已隐藏
        """
        if not self.isVisible():
            return False

        table_rect = self._parent_table.rect()
        table_rect.moveTo(self._parent_table.mapToGlobal(table_rect.topLeft()))
        frame_rect = self.rect()
        frame_rect.moveTo(self.pos())

        if not table_rect.contains(global_pos) and not frame_rect.contains(global_pos):
            self.hide_buttons()
            return True
        return False

    # ── 内部实现 ─────────────────────────────────────────

    def _on_up_clicked(self):
        self.move_up.emit(self._current_row)

    def _on_down_clicked(self):
        self.move_down.emit(self._current_row)

    def _start_fade_out(self):
        self._stop_animation()

        self._fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self._fade_animation.setDuration(500)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._fade_animation.finished.connect(self.hide)
        self._fade_animation.start()

    def _stop_animation(self):
        if self._fade_animation:
            self._fade_animation.stop()
            self._fade_animation = None

    def _on_frame_enter(self, event):
        self._hide_timer.stop()
        self._stop_animation()
        self.setWindowOpacity(1.0)

    def _on_frame_leave(self, event):
        self._hide_timer.start(5000)
