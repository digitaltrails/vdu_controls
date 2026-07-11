# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import List

from vdu_controls.app_locale import tr
from vdu_controls.icon_utils import si, StdPixmap
from vdu_controls.qt_imports import QDialog, QVBoxLayout
from vdu_controls.qt_imports import QSvgWidget
from vdu_controls.qt_imports import Qt
from vdu_controls.scaling import dpx
from vdu_controls.widgets import SubWinDialog, StdButton

# Creates an SVG of grey rectangles typical of the sort used for VDU calibration.
GREY_SCALE_SVG = f'''
<svg xmlns="http://www.w3.org/2000/svg" version="1.1"  width="256" height="152" viewBox="0 0 256 152">
    <rect width="256" height="152" x="0" y="0" style="fill:rgb(128,128,128);stroke-width:0;" />
    {"".join(
    [f'<rect width="16" height="32" x="{x}" y="38" style="fill:rgb({v},{v},{v});stroke-width:0;" />'
     for x, v in list(zip([x + 48 for x in range(0, 160, 16)], [v for v in range(0, 120, 12)]))]
)}
    {"".join(
    [f'<rect width="16" height="32" x="{x}" y="80" style="fill:rgb({v},{v},{v});stroke-width:0;" />'
     for x, v in list(zip([x + 48 for x in range(0, 160, 16)], [v for v in range(147, 256, 12)]))]
)}
</svg>
'''.encode()

class GrayScaleDialog(SubWinDialog):
    """
    Creates a dialog with a grey scale VDU calibration image.
    Non-model. Have as many as you like - one per VDU.
    """

    # This stops garbage-collection of independent instances of this dialog until the user closes them.
    # If we don't do this, the dialog will disappear before it becomes visible. We could also pass a parent
    # which would achieve the same thing, but would alter where the dialog appears.
    _active_list: List[QDialog] = []

    def __init__(self) -> None:
        super().__init__()
        GrayScaleDialog._active_list.append(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setWindowTitle(tr('Gray Scale Reference'))
        self.setWindowRole('gray-scale-dialog')
        self.setModal(False)
        svg_widget = QSvgWidget()
        renderer = svg_widget.renderer()
        assert renderer is not None
        renderer.load(GREY_SCALE_SVG)
        svg_widget.setMinimumSize(dpx(300), dpx(200))
        svg_widget.setToolTip(tr(
            'Gray Scale Reference for VDU adjustment.\n\n'
            'Set contrast toward the maximum (for HDR monitors\n'
            'try something lower such as 70%) and adjust brightness\n'
            'until as many rectangles as possible can be perceived.\n\n'
            'Use the content-menu to create additional charts and\n'
            'drag them onto each display.\n\nThis chart is resizable. '))
        layout.addWidget(svg_widget)
        close_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr("Close"), clicked=self.hide)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        GrayScaleDialog._active_list.remove(self)
        event.accept()
