# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re

from vdu_controls import constants

from vdu_controls.app_locale import tr
from vdu_controls.constants import VDU_CONTROLS_HELP_URL
from vdu_controls.qt_imports import QVBoxLayout, QSize, QTextEdit, QUrl, QDesktopServices, QDialogButtonBox
from vdu_controls.scaling import dpx
from vdu_controls.widgets import SubWinDialog, DialogSingletonMixin
import vdu_controls.app_locale as app_locale


class HelpDialog(SubWinDialog, DialogSingletonMixin):

    @staticmethod
    def show_dialog() -> None:
        HelpDialog.show_existing_dialog() if HelpDialog.exists() else HelpDialog()

    def __init__(self) -> None:
        super().__init__()

        qt_markdown = self.load_help_text()

        self.setWindowTitle(tr('Help'))
        layout = QVBoxLayout()
        markdown_view = QTextEdit()
        markdown_view.setReadOnly(True)
        markdown_view.setViewportMargins(dpx(40), dpx(40), dpx(25), dpx(15))
        markdown_view.setMarkdown(qt_markdown)
        layout.addWidget(markdown_view)

        buttons = QDialogButtonBox.StandardButton.Help | QDialogButtonBox.StandardButton.Close
        button_box = QDialogButtonBox(buttons)  # pyright:ignore

        def online_help():
            QDesktopServices.openUrl(QUrl(VDU_CONTROLS_HELP_URL))

        button_box.helpRequested.connect(online_help)
        button_box.rejected.connect(self.close)  # pyright:ignore
        button_box.button(QDialogButtonBox.StandardButton.Close).setDefault(True)  # pyright:ignore
        help_button = button_box.button(QDialogButtonBox.StandardButton.Help)
        help_button.setText(tr("Online Help"))  # pyright:ignore
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.make_visible()

    def load_help_text(self) -> str:
        help_text = app_locale.load_docs_text(constants.HELP_FILENAME)
        # Hack normal markdown to something Qt can use:
        qt_markdown = re.sub(r"\n\n", r"\n<br/>\n\n", help_text, flags=re.MULTILINE)
        return qt_markdown

    def sizeHint(self) -> QSize:
        return QSize(dpx(800), dpx(500))
