# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import re

from vdu_controls import constants
from vdu_controls.icon_utils import StdPixmap, si
from vdu_controls.app_locale import tr
from vdu_controls.qt_imports import QVBoxLayout, QSize, QTextEdit, Qt
from vdu_controls.scaling import npx
from vdu_controls.widgets import SubWinDialog, StdButton, DialogSingletonMixin
import vdu_controls.app_locale as app_locale

class HelpDialog(SubWinDialog, DialogSingletonMixin):

    @staticmethod
    def invoke() -> None:
        HelpDialog.show_existing_dialog() if HelpDialog.exists() else HelpDialog()

    def __init__(self) -> None:
        super().__init__()

        qt_markdown = self.load_help_text()

        self.setWindowTitle(tr('Help'))
        layout = QVBoxLayout()
        markdown_view = QTextEdit()
        markdown_view.setReadOnly(True)
        markdown_view.setViewportMargins(npx(80), npx(80), npx(50), npx(30))
        markdown_view.setMarkdown(qt_markdown)
        layout.addWidget(markdown_view)
        close_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr("Close"), clicked=self.hide)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)
        self.make_visible()

    def load_help_text(self) -> str:
        help_text = app_locale.load_docs_text(constants.HELP_FILENAME)
        # Hack normal markdown to something Qt can use:
        qt_markdown = re.sub(r"\n\n", r"\n<br/>\n\n", help_text, flags=re.MULTILINE)
        return qt_markdown

    def sizeHint(self) -> QSize:
        return QSize(npx(1600), npx(1000))
