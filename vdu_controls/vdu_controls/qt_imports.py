# SPDX-FileCopyrightText: 2021-2026 Michael Hamilton
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

from vdu_controls.constants import CONFIG_FILE_PREFER_QT5



for qt_version in (5, 6) if CONFIG_FILE_PREFER_QT5.exists() else (6, 5):
    print(f"Trying Qt{qt_version}")
    try:
        if qt_version == 6:
            from PyQt6 import QtCore, QtNetwork
            from PyQt6.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QPoint, QObject, QEvent, \
                QSettings, QSize, QTimer, QTranslator, QLocale, QT_TR_NOOP, QVariant, pyqtSlot, QMetaType, QDir, \
                QRegularExpression, QPointF, QRect, QSocketNotifier, QMargins
            from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusArgument, QDBusVariant
            from PyQt6.QtGui import QAction, QShortcut, QPixmap, QIcon, QCursor, QImage, QPainter, QRegularExpressionValidator, \
                QPalette, QGuiApplication, QColor, QValidator, QPen, QFont, QFontMetrics, QMouseEvent, QResizeEvent, QKeySequence, QPolygon, \
                QDoubleValidator
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtSvgWidgets import QSvgWidget
            from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
                QSplashScreen, QPushButton, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
                QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QMainWindow, QToolBar, QToolButton, QFileDialog, \
                QWidgetItem, QScrollArea, QGroupBox, QFrame, QSplitter, QSpinBox, QDoubleSpinBox, QInputDialog, QStatusBar, \
                QSpacerItem, QListWidget, QListWidgetItem, QLayout
            QT5_USE_HIGH_DPI_PIXMAPS = None
            QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING = None
        elif qt_version == 5:  # Covers all other values.
            from PyQt5 import QtCore, QtNetwork
            from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QPoint, QObject, QEvent, \
                QSettings, QSize, QTimer, QTranslator, QLocale, QT_TR_NOOP, QVariant, pyqtSlot, QMetaType, QDir, \
                QRegularExpression, QPointF, QRect, QSocketNotifier, QMargins
            from PyQt5.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusArgument, QDBusVariant
            from PyQt5.QtGui import QPixmap, QIcon, QCursor, QImage, QPainter, QRegularExpressionValidator, \
                QPalette, QGuiApplication, QColor, QValidator, QPen, QFont, QFontMetrics, QMouseEvent, QResizeEvent, QKeySequence, QPolygon, \
                QDoubleValidator
            from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
            from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
                QSplashScreen, QPushButton, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
                QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QAction, QMainWindow, QToolBar, QToolButton, QFileDialog, \
                QWidgetItem, QScrollArea, QGroupBox, QFrame, QSplitter, QSpinBox, QDoubleSpinBox, QInputDialog, QStatusBar, QShortcut, \
                QSpacerItem, QListWidget, QListWidgetItem, QLayout
            QT5_USE_HIGH_DPI_PIXMAPS = Qt.ApplicationAttribute.AA_UseHighDpiPixmaps
            QT5_QPAINTER_HIGH_QUALITY_ANTIALIASING = QPainter.RenderHint.HighQualityAntialiasing
        break
    except (ImportError, ModuleNotFoundError) as no_qt_exc:
        print(f"Failed to import PyQt6: {repr(no_qt_exc)}", file=sys.stderr)



