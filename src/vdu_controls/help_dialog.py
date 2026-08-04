# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import subprocess
from functools import partial

from vdu_controls import constants

from vdu_controls.app_locale import tr
from vdu_controls.constants import VDU_CONTROLS_HELP_URL
from vdu_controls.misc import generate_slug, is_gnome
from vdu_controls.qt_imports import (
    QVBoxLayout, QSize, QTextBrowser,
    QUrl, QDesktopServices, QTimer,
    QDialogButtonBox, QTabWidget, QWidget, QHBoxLayout, QListWidget, QListWidgetItem, Qt, QSplitter,
)
from vdu_controls.scaling import dpx
from vdu_controls.widgets import SubWinDialog, DialogSingletonMixin
import vdu_controls.app_locale as app_locale
import vdu_controls.app_logging as log
import re

class MarkdownHelpViewer(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.toc_widget = QListWidget()
        # Set a minimum width so the user can't squash it to zero accidentally
        self.toc_widget.setMinimumWidth(dpx(100))
        self.toc_widget.itemClicked.connect(self.on_toc_clicked)
        self.toc_widget.setViewportMargins(dpx(10), dpx(10), dpx(15), dpx(15))

        self.text_browser = QTextBrowser()
        self.text_browser.setViewportMargins(dpx(40), dpx(40), dpx(25), dpx(15))
        self.text_browser.setOpenExternalLinks(True)

        splitter.addWidget(self.toc_widget)
        splitter.addWidget(self.text_browser)

        splitter.setSizes([dpx(300), dpx(900)])

        # Make the browser stretch more eagerly when the window resizes
        # Stretch factor 0 for TOC (doesn't grow), 1 for browser (takes extra space)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        self.load_markdown()

    def load_markdown(self):
        # Do a bit of preprocessing to fix breaks so qt processes the markdown correctly
        help_text = app_locale.load_docs_text(constants.HELP_FILENAME)
        #qt_markdown = re.sub(r"\n\n", r"\n<br/>\n\n", help_text, flags=re.MULTILINE)
        qt_markdown = help_text
        # Improve paragraph spacing.
        # Ugly, but setting css disables dark/ligh theme changes, so we do this instead.
        qt_markdown = re.sub(r"\n\n([^\s])", r"\n<br/>\n\n\1", qt_markdown, flags=re.MULTILINE)
        # Improve header spacing
        qt_markdown = re.sub(r'^((#{1,6})\s+(.*))$', r"<br/>\n\1\n", qt_markdown, flags=re.MULTILINE)

        html_with_anchors, headings = self.parse_headings(qt_markdown)
        self.text_browser.setMarkdown(html_with_anchors)
        #self.toc_widget.clear()
        for heading in headings:
            # Indent based on heading level
            item = QListWidgetItem("  " * (heading['level'] - 1) + heading['title'])
            item.setData(Qt.ItemDataRole.UserRole, heading['id'])
            self.toc_widget.addItem(item)

    def on_toc_clicked(self, item):
        anchor_id = item.data(Qt.ItemDataRole.UserRole)
        if anchor_id:
            self.text_browser.scrollToAnchor(anchor_id)

    def parse_headings(self, markdown_text):
        """
        Parse headings from Markdown text, generating HTML with anchor IDs
        and a list of heading information.
        """
        headings = []
        # Match ATX-style Markdown headings, e.g., # Heading 1
        heading_pattern = re.compile(r'^(#{1,6})\s+(.*)$', re.MULTILINE)

        def replace_heading(match):
            level = len(match.group(1))
            title = match.group(2).strip()
            anchor_id = generate_slug(title)
            headings.append({'level': level, 'title': title, 'id': anchor_id})
            return f'<h{level} id="{anchor_id}">{title}</h{level}>'

        html_with_anchors = heading_pattern.sub(replace_heading, markdown_text)
        return html_with_anchors, headings

class OnlineHelpViewer(QTextBrowser):

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setViewportMargins(dpx(40), dpx(40), dpx(25), dpx(15))
        self.setHtml(self.localized_text())
        if is_gnome():
            self.setOpenLinks(False)
            self.setOpenExternalLinks(False)
            self.anchorClicked.connect(self.gnome_open_url_safely)
        else:
            self.setOpenExternalLinks(True)

    def localized_text(self):
        # Doing this dynamically to more easily get translations
        html_refs = [f"<a style='text-decoration: none;' href='{k}'>{t}</a>" for t, k in self.links()]
        html_refs_text = "</h4>\n<h4>".join(html_refs)
        return f"""<html><body style='line-height: 1.6;'>
                    <h2>{tr('VDU Controls Online Help')}</h2>
                    {tr('Links to the most up‑to‑date documentation, tutorials, and support:')}
                    <br/>
                    <blockquote>
                        <h4>{html_refs_text}</h4>
                    </blockquote>
                    <br/>
                    <hr/>
                    </body>
                    """

    def links(self):
        # Doing this dynamically to more easily get translations
        return [(tr("General Help"), "https://digitaltrails.github.io/vdu_controls/"),
                 (tr("Semi-Auto Howto"), "https://digitaltrails.github.io/vdu_controls/assets/semi-auto-howto/"),
                 (tr("Navigable Manual page"), "https://digitaltrails.github.io/vdu_controls/manual/"),
                 (tr("Change Log"), "https://digitaltrails.github.io/vdu_controls/changelog/"),
                 (tr("Releases"), "https://github.com/digitaltrails/vdu_controls/releases"),
                 (tr("Issues"), "https://github.com/digitaltrails/vdu_controls/issues"),
                 (tr("License"), "https://digitaltrails.github.io/vdu_controls/LICENSE/"),
                 ]

    # Fix for browser opening - safer for gnome if running
    # under xwayland.
    @staticmethod
    def gnome_open_url_safely(url: QUrl):
        log.debug("OnlineHelpViewer: Using gnome url open")
        def _open_url_with_xdg(url: QUrl):
            try:
                # Start xdg-open as a detached process
                subprocess.Popen(['xdg-open', url.toString()],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Failed to open URL: {e}")

        # Use a single-shot timer to prevent event loop reentrancy
        QTimer.singleShot(0, partial(_open_url_with_xdg, url))


class HelpDialog(SubWinDialog, DialogSingletonMixin):

    @staticmethod
    def show_dialog() -> None:
        HelpDialog.show_existing_dialog() if HelpDialog.exists() else HelpDialog()

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(tr('Help'))
        self.setWindowRole('help-dialog')

        layout = QVBoxLayout()
        tab_widget = QTabWidget()

        online_help_view = OnlineHelpViewer()
        help_view = MarkdownHelpViewer()

        tab_widget.addTab(help_view, tr("Manual Page"))
        tab_widget.addTab(online_help_view, tr("Online Help"))
        layout.addWidget(tab_widget)

        buttons = QDialogButtonBox.StandardButton.Close
        button_box = QDialogButtonBox(buttons)

        def online_help():
            QDesktopServices.openUrl(QUrl(VDU_CONTROLS_HELP_URL))

        button_box.helpRequested.connect(online_help)
        button_box.rejected.connect(self.close)
        button_box.button(QDialogButtonBox.StandardButton.Close).setDefault(True)

        layout.addWidget(button_box)

        self.setLayout(layout)
        self.make_visible()


    def sizeHint(self) -> QSize:
        return QSize(dpx(1024), dpx(650))