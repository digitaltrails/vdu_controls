# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
from typing import Callable, Any, Tuple, Dict, Type

from PyQt5.QtCore import QTimer, Qt, QRect
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon
from PyQt5.QtWidgets import QToolButton, QWidget

from vdu_controls.logging import *
from vdu_controls.constants import RESIZABLE_MESSAGEBOX_HACK, APPNAME
from vdu_controls.icon_utils import polychrome_light_or_dark, handle_theme, create_icon_from_svg_bytes
from vdu_controls.qt_imports import *
from vdu_controls.qt_imports import QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING
from vdu_controls.scaling import native_font_height, npx

def alter_margins(target: QWidget | QLayout,
                  left: int | None = None, top: int | None = None, right: int | None = None, bottom: int | None = None,
                  default: QStyle | None = None) -> None:
    current = target.contentsMargins()
    if left is None:
        left = default.pixelMetric(QStyle.PixelMetric.PM_LayoutLeftMargin) if default else current.left()
    if top is None:
        top = default.pixelMetric(QStyle.PixelMetric.PM_LayoutTopMargin) if default else current.top()
    if right is None:
        right = default.pixelMetric(QStyle.PixelMetric.PM_LayoutRightMargin) if default else current.right()
    if bottom is None:
        bottom = default.pixelMetric(QStyle.PixelMetric.PM_LayoutBottomMargin) if default else current.bottom()
    target.setContentsMargins(QMargins(left, top, right, bottom))


class ThemedSvgWidget(QSvgWidget):

    def __init__(self, icon_source: bytes, width: int, height: int, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.icon_source = icon_source
        self.setFixedSize(width, height)
        self.load_from_icon_source(self.icon_source)

    def load_from_icon_source(self, icon_source: bytes):
        self.icon_source = icon_source
        self.load(handle_theme(self.icon_source, polychrome_light_or_dark()))

    def event(self, event: QEvent | None) -> bool:
        if event and event.type() == QEvent.Type.PaletteChange:  # PalletChange happens after the new style sheet is in use.
            self.load_from_icon_source(self.icon_source)
        return super().event(event)


class StdButton(QPushButton):  # Reduce some repetitiveness in the code

    def __init__(self, icon: QIcon | None = None, title: str = '', clicked: Callable | None = None, auto_default=True,
                 tip: str | None = None, flat: bool = False, margins: bool = True, icon_size: QSize | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setIcon(icon) if icon else None
        self.setIconSize(icon_size) if icon_size else None
        self.setText(title) if title else None
        self.clicked.connect(clicked) if clicked else None
        self.setToolTip(tip) if tip else None
        self.setFlat(flat)
        self.setContentsMargins(0, 0, 0, 0) if not margins else None
        self.setAutoDefault(auto_default)


class ThemedSvgButton(StdButton):

    def __init__(self, icon_source: bytes, title: str = '', clicked: Callable | None = None, auto_default=True,
                 tip: str | None = None, flat: bool = False, margins: bool = True, icon_size: QSize | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(icon := create_icon_from_svg_bytes(icon_source), title, clicked, auto_default, tip, flat, margins,
                         icon_size, parent)
        self.icon_source = icon_source

    def event(self, event: QEvent | None) -> bool:
        if event and event.type() == QEvent.Type.PaletteChange:  # PalletChange happens after the new style sheet is in use.
            self.setIcon(create_icon_from_svg_bytes(self.icon_source))
        return super().event(event)


class TitleButton(StdButton):
    def __init__(self, icon_source: bytes, main_text: str, sub_text: str, clicked: Callable | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(icon=None, title=None, clicked=clicked, flat=True, parent=parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.svg_icon = ThemedSvgWidget(icon_source, native_font_height(scaled=1.8), native_font_height(scaled=1.8), parent=self)
        layout.addWidget(self.svg_icon)
        self.label = QLabel(f"<span style='font-weight:bold;'>{main_text}<br/>"
                            f"<span style='font-size:{native_font_height(0.5)}px; font-weight:normal;'>{sub_text}</span>")
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Prevent label from swollowing clicks
        self.label.adjustSize()  # Adjust down to actual text height before accessing its height
        layout.addWidget(self.label)
        self.setMinimumHeight(max(self.svg_icon.height(), self.label.height()) +  # Avoids size issues if embedded in a layout
                              self.style().pixelMetric(QStyle.PixelMetric.PM_LayoutTopMargin) +
                              self.style().pixelMetric(QStyle.PixelMetric.PM_LayoutBottomMargin))


class FasterFileDialog(QFileDialog):  # Takes 5 seconds versus 30+ seconds for QFileDilog.getOpenFileName() on KDE.
    os.putenv('QT_LOGGING_RULES', 'kf.kio.widgets.kdirmodel.warning=false')  # annoying KDE message

    @staticmethod
    def getOpenFileName(parent: QWidget | None = None, caption: str = '', directory: str = '', filter_str: str = '',
                        initial_filter: str = '',
                        options: Any = QFileDialog.Option.ReadOnly,
                        qdir_filter: Any = QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.Hidden | QDir.Filter.System) -> \
    Tuple[str, str]:
        original_handler = QtCore.qInstallMessageHandler(lambda mode, context, message: None)
        try:  # Get rid of another annoying message: 'qtimeline::start: already running'
            dialog = QFileDialog(parent=parent, caption=caption, directory=directory, filter=filter_str)
            dialog.setOptions(options)
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            dialog.setFilter(qdir_filter)
            return (dialog.selectedFiles()[0], filter) if dialog.exec() else ('', '')  # match QFileDilog.getOpenFileName()
        finally:
            QtCore.qInstallMessageHandler(original_handler)


MIcon = QMessageBox.Icon
MBtn = QMessageBox.StandardButton


class MBox(QMessageBox):

    def __init__(self, icon: QMessageBox.Icon, msg: str | None = None, info: str | None = None, details: str | None = None,
                 buttons: QMessageBox.StandardButton = MBtn.NoButton,
                 default: QMessageBox.StandardButton | None = None) -> None:
        super().__init__(icon, APPNAME, '', buttons=buttons)
        if RESIZABLE_MESSAGEBOX_HACK:
            self.setMouseTracking(True)
            self.setSizeGripEnabled(True)
        self.setDefaultButton(default) if default else None
        self.setText(msg) if msg else None
        self.setInformativeText(info) if info else None
        self.setDetailedText(details) if details else None

    def event(self, event: QEvent | None):
        # https://www.qtcentre.org/threads/24888-Resizing-a-MsgBox.p=251312#post251312
        # The "least evil" way to make MsgBox.resizable, by ArmanS
        result = super().event(event)
        if RESIZABLE_MESSAGEBOX_HACK and event:
            if event.type() == QEvent.Type.MouseMove or event == QEvent.Type.MouseButtonPress:
                self.setMaximumSize(npx(1200), npx(800))
                if text_edit_field := self.findChild(QTextEdit):
                    text_edit_field.setMaximumHeight(npx(600))
        return result


class PushButtonLeftJustified(QPushButton):
    def __init__(self, text: str | None = None, parent: QWidget | None = None, flat: bool = False) -> None:
        super().__init__(parent=parent)
        self.label = QLabel()
        self.setContentsMargins(npx(10), 0, npx(10), 0)  # Not sure if this helps
        self.setLayout(widget_layout := QVBoxLayout())
        widget_layout.addWidget(self.label)
        widget_layout.setContentsMargins(0, 0, 0, 0)  # Seems to fix top/bottom clipping on openbox and xfce
        self.setText(text) if text is not None else None
        self.setFlat(flat)

    def setText(self, text: str | None) -> None:
        self.label.setText(text)


def is_subwin_desktop() -> bool:
    return os.environ.get('XDG_CURRENT_DESKTOP', default='unknown').lower() in ['gnome', 'cosmic']


class SubWinDialog(QDialog):  # Fix for gnome: QDialog must be a subwindow, otherwise it will always stay on top of other windows.

    def __init__(self, parent: QWidget | None = None) -> None:
        # On gnome this allows the subwindow to surface properly, on others it may anoyingly keep
        # the window on top - which is not always desirable.
        super().__init__(parent, Qt.WindowType.SubWindow if is_subwin_desktop() else Qt.WindowType.Window)


class ClickableSlider(QSlider):  # loosely based on https://stackoverflow.com/a/29639127/609575

    def mousePressEvent(self, event: QMouseEvent | None):  # On mouse click, set value to the value at the click position
        if event:
            self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.pos().x(), self.width()))
        super().mousePressEvent(event)


class LineEditAll(QLineEdit):  # On mouse click, select the entire text - Make it easier to over-type
    def __init__(self, *args):
        super().__init__(*args)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.selectAll()


class DialogSingletonMixin:
    """
    A mixin that can augment a QDialog or QMessageBox with code to enforce a singleton UI.
    For example, it is used so that only one settings editor can be active at a time.
    """
    _dialogs_map: Dict[str, 'DialogSingletonMixin'] = {}

    def __init__(self) -> None:
        """Registers the concrete class as a singleton, so it can be reused later."""
        super().__init__()
        class_name = self.__class__.__name__
        if class_name in DialogSingletonMixin._dialogs_map:
            raise TypeError(f"ERROR: More than one instance of {class_name} cannot exist.")
        log_debug(f'SingletonDialog created for {class_name}') if log_debug_enabled else None
        DialogSingletonMixin._dialogs_map[class_name] = self

    def closeEvent(self, event) -> None:
        """Subclasses that implement their own closeEvent must call this closeEvent to deregister the singleton"""
        class_name = self.__class__.__name__
        log_debug(f"SingletonDialog remove {class_name} "
                  f"registered={class_name in DialogSingletonMixin._dialogs_map}") if log_debug_enabled else None
        if class_name in DialogSingletonMixin._dialogs_map:
            del DialogSingletonMixin._dialogs_map[class_name]
        event.accept()

    def make_visible(self) -> None:
        """ If the dialog exists(), call this to make it visible by raising it.
        Internal, used by the class method show_existing_dialog()"""
        self.show()  # type: ignore
        self.raise_()  # type: ignore
        self.activateWindow()  # type: ignore

    @classmethod
    def show_existing_dialog(cls: Type) -> None:
        """If the dialog exists(), call this to make it visible by raising it."""
        class_name = cls.__name__
        log_debug(f'SingletonDialog show existing {class_name}') if log_debug_enabled else None
        DialogSingletonMixin._dialogs_map[class_name].make_visible()

    @classmethod
    def exists(cls: Type) -> bool:
        """Returns true if the dialog has already been created."""
        class_name = cls.__name__
        log_debug(f"SingletonDialog exists {class_name} "
                  f"{class_name in DialogSingletonMixin._dialogs_map}") if log_debug_enabled else None
        return class_name in DialogSingletonMixin._dialogs_map

    @classmethod
    def get_instance(cls: Type) -> 'DialogSingletonMixin | None':
        return DialogSingletonMixin._dialogs_map.get(cls.__name__)


class ToolButton(QToolButton):
    def __init__(self, svg_source: bytes, tip: str | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        if tip is not None:
            self.setToolTip(tip)
        self.svg_source = svg_source
        self._original_icon = None
        self._busy_timer = QTimer(self)
        self._busy_timer.timeout.connect(self._update_busy_icon)
        self._busy_angle = 0
        self._busy_now = False
        self.refresh_icon()

    def refresh_icon(self, svg_source: bytes | None = None):
        if svg_source is not None:
            self.svg_source = svg_source
        self._original_icon = create_icon_from_svg_bytes(self.svg_source)  # Store the original icon so we can restore it later
        if not self._busy_now:
            self.setIcon(self._original_icon)

    def setBusy(self, busy: bool):  # Start or stop the busy spinner animation.
        if busy == self._busy_now:
            return
        self._busy_now = busy
        if busy:  # Start spinning
            self._busy_angle = 0
            self._busy_timer.start(30)  # ~33 fps
        else:  # Stop spinning and restore original icon
            self._busy_timer.stop()
            self.setIcon(self._original_icon)

    def _update_busy_icon(self):
        size = self.iconSize()  # Use the button's icon size (or a default size if none)
        if size.width() <= 0 or size.height() <= 0:
            size = self.size()  # fallback to button size
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING:
            painter.setRenderHint(QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING)
        pen_width = max(npx(2), size.width() // 10)  # Determine a good pen width relative to size
        painter.setPen(QPen(self.palette().buttonText().color(), pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        rect = QRect(0, 0, size.width(), size.height()).adjusted(margin := pen_width // npx(2) + npx(1), margin, -margin, -margin)
        painter.drawArc(rect, self._busy_angle * 16, 270 * 16)  # Draw the rotating arc (270 degrees)
        painter.end()
        self.setIcon(QIcon(pixmap))
        self._busy_angle = (self._busy_angle + 8) % 360  # Advance the angle for the next frame
