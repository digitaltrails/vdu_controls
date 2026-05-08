# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import math
import time
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Callable, Dict, List, Tuple, TYPE_CHECKING

from vdu_controls.qt_imports import QSize, QEvent, Qt, pyqtSignal, QPoint, QRegularExpression
from vdu_controls.qt_imports import QFontMetrics, QFont, QImage, QPixmap, QPainter, QColor, QPen, QPolygon, QMouseEvent, QDoubleValidator, \
    QResizeEvent, QValidator, QRegularExpressionValidator
from vdu_controls.qt_imports import QWidget, QHBoxLayout, QSizePolicy, QApplication, QVBoxLayout, QLabel, QComboBox, QScrollArea, QMenu, \
    QAction, QSpinBox, QCheckBox, QLineEdit, QSlider, QSplitter, QGroupBox, QToolButton, QSpacerItem, QStatusBar, QFrame

from vdu_controls.vdu_controls_config import VduControlsConfig, ConfOpt
from vdu_controls.config_ini import ConfIni
from vdu_controls.constants import STANDARD_ICON_PATHS, CONFIG_DIR_PATH, WEATHER_FORECAST_URL, EASTERN_SKY, WESTERN_SKY
from vdu_controls.icon_utils import si, StdPixmap, create_icon_from_path, polychrome_light_or_dark, create_image_from_svg_bytes, \
    SVG_LIGHT_THEME_COLOR
from vdu_controls.app_locale import tr, translate_option
import vdu_controls.logging as log
from vdu_controls.misc import zoned_now, proper_name, GeoLocation
from vdu_controls.preset import Preset, PresetTransitionFlag, PresetScheduleStatus
from vdu_controls.scaling import npx, native_font_height
from vdu_controls.solar_calc import SolarElevationKey, SolarElevationData, create_elevation_map, calc_solar_lux, \
    format_solar_elevation_abbreviation, parse_solar_elevation_ini_text, format_solar_elevation_ini_text
from vdu_controls.svg import SUN_SVG, VDU_POWER_ON_ICON_SOURCE
from vdu_controls.unicode import TIME_CLOCK_SYMBOL, DEGREE_SYMBOL, WARNING_SYMBOL
from vdu_controls.vdu_bulk_change import BulkChangeWorker
import vdu_controls.weather_util as weather_util
from vdu_controls.widgets import alter_margins, StdButton, PushButtonLeftJustified, FasterFileDialog, MBox, MIcon, MBtn, \
    SubWinDialog, DialogSingletonMixin, ToolButton

if TYPE_CHECKING:
    from vdu_controls.vdu_controls_application import VduAppController

class PresetItemWidget(QWidget):
    def __init__(self, preset: Preset, restore_action: Callable, save_action: Callable, delete_action: Callable,
                 edit_action: Callable, up_action: Callable, down_action: Callable, protect_nvram: bool):
        super().__init__()
        self.name = preset.name
        self.preset = preset
        line_layout = QHBoxLayout()
        line_layout.setSpacing(0)
        alter_margins(line_layout, top=0, bottom=npx(1))  # Why?
        self.setLayout(line_layout)

        self.preset_name_button = PresetActivationButton(preset)
        line_layout.addWidget(self.preset_name_button)
        self.preset_name_button.clicked.connect(partial(edit_action, preset=preset))
        self.preset_name_button.setToolTip(tr('Activate this Preset and edit its options.'))
        self.preset_name_button.setAutoDefault(False)
        self.preset_name_button.setFixedSize(QSize(npx(300), native_font_height(scaled=1.5)))
        line_layout.addSpacing(npx(20))
        for button in (
                StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), tip=tr("Update this preset from the current VDU settings."),
                          clicked=partial(save_action, from_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_ArrowUp), tip=tr("Move up the menu order."),
                          clicked=partial(up_action, preset=preset, target_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_ArrowDown), tip=tr("Move down the menu order."),
                          clicked=partial(down_action, preset=preset, target_widget=self), flat=True),
                StdButton(icon=si(self, StdPixmap.SP_DialogDiscardButton), tip=tr('Delete this preset.'),
                          clicked=partial(delete_action, preset=preset, target_widget=self), flat=True)):
            button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
            line_layout.addWidget(button)

        if not protect_nvram:
            preset_transition_button = PushButtonLeftJustified(flat=True)
            preset_transition_button.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
            width = QFontMetrics(preset_transition_button.font()).horizontalAdvance(">____99")
            preset_transition_button.setMaximumWidth(width + 5)
            preset_transition_button.setText(
                f"{preset.get_transition_type().abbreviation()}"
                f"{str(preset.get_step_interval_seconds()) if preset.get_step_interval_seconds() > 0 else ''}")
            if preset.get_step_interval_seconds() > 0:
                preset_transition_button.setToolTip(tr("Transition to {0}, each step is {1} seconds. {2}").format(
                    preset.get_title_name(), preset.get_step_interval_seconds(), preset.get_transition_type().description()))
            else:
                preset_transition_button.setToolTip(tr("Transition to {0}. {1}").format(
                    preset.get_title_name(), preset.get_transition_type().description()))
            preset_transition_button.clicked.connect(partial(restore_action, preset=preset,
                                                             immediately=preset.get_transition_type() == PresetTransitionFlag.NONE))
            preset_transition_button.setAutoDefault(False)
            if preset.get_transition_type() == PresetTransitionFlag.NONE:
                preset_transition_button.setDisabled(True)
                preset_transition_button.setText('')
            line_layout.addWidget(preset_transition_button)

        line_layout.addSpacing(5)
        self.timer_control_button = PushButtonLeftJustified(parent=self, flat=True)
        self.timer_control_button.setAutoDefault(False)

        if preset.get_solar_elevation() is not None or preset.get_at_time() is not None:
            def _toggle_timer(_) -> None:
                preset.toggle_timer()
                self.update_timer_button()

            self.timer_control_button.clicked.connect(_toggle_timer)

        line_layout.addWidget(self.timer_control_button)
        self.update_timer_button()

    def update_timer_button(self):
        self.timer_control_button.setEnabled(
            self.preset.schedule_status in (PresetScheduleStatus.SCHEDULED, PresetScheduleStatus.SUSPENDED))
        if self.preset.schedule_status == PresetScheduleStatus.SCHEDULED:
            action_desc = tr("Press to skip: ")
        elif self.preset.schedule_status == PresetScheduleStatus.SUSPENDED:
            action_desc = tr("Press to re-enable: ")
        else:
            action_desc = ''
        tip_text = f"{action_desc} {self.preset.get_schedule_description()}"
        self.timer_control_button.setText(self.preset.get_solar_elevation_abbreviation())
        if tip_text.strip():
            self.timer_control_button.setToolTip(tip_text)

    def indicate_active(self, active: bool):
        weight = QFont.Weight.Bold if active else QFont.Weight.Normal
        font = self.preset_name_button.font()
        if font.weight() != weight:
            font.setWeight(weight)
            self.preset_name_button.setFont(font)


class PresetActivationButton(StdButton):
    def __init__(self, preset: Preset) -> None:
        super().__init__(icon=preset.create_icon(), icon_size=QSize(native_font_height(), native_font_height()),
                         title=preset.get_title_name(), tip=tr("Restore {} (immediately)").format(preset.get_title_name()))
        self.preset = preset

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            self.setIcon(self.preset.create_icon())
        return super().event(event)


class PresetIconPickerButton(StdButton):

    def __init__(self) -> None:
        super().__init__(icon_size=QSize(native_font_height(), native_font_height()),
                         clicked=self.choose_preset_icon_action, flat=True, auto_default=False,
                         tip=tr('Choose a preset icon.'))
        self.setIcon(si(self, PresetsDialog.NO_ICON_ICON_NUMBER))
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.last_selected_icon_path: Path | None = None
        self.last_icon_dir = Path.home()
        for path in STANDARD_ICON_PATHS:
            if path.exists():
                self.last_icon_dir = path
                break
        self.preset: Preset | None = None

    def set_preset(self, preset: Preset | None) -> None:
        self.preset = preset
        if preset is not None:
            self.last_selected_icon_path = preset.get_icon_path()
        if self.last_selected_icon_path is not None:
            self.last_icon_dir = self.last_selected_icon_path.parent
        self.update_icon()

    def choose_preset_icon_action(self) -> None:
        try:
            PresetsDialog.get_instance().setDisabled(True)
            PresetsDialog.get_instance().status_message(TIME_CLOCK_SYMBOL + ' ' + tr("Select an icon..."))
            QApplication.processEvents()
            icon_file = FasterFileDialog.getOpenFileName(self, tr('Icon SVG or PNG file'), self.last_icon_dir.as_posix(),
                                                         'SVG or PNG (*.svg *.png)')
            self.last_selected_icon_path = Path(icon_file[0]) if icon_file[0] != '' else None
            if self.last_selected_icon_path:
                self.last_icon_dir = self.last_selected_icon_path.parent
            self.update_icon()
        finally:
            PresetsDialog.get_instance().status_message('')
            PresetsDialog.get_instance().setDisabled(False)

    def update_icon(self) -> None:
        if self.last_selected_icon_path:
            self.setIcon(create_icon_from_path(self.last_selected_icon_path, polychrome_light_or_dark()))
        elif self.preset:
            self.setIcon(self.preset.create_icon(polychrome_light_or_dark()))
        else:
            self.setIcon(si(self, PresetsDialog.NO_ICON_ICON_NUMBER))

    def reset(self):
        self.last_selected_icon_path = None
        self.preset = None
        self.update_icon()

    def event(self, event: QEvent | None) -> bool:
        if event and event.type() == QEvent.Type.PaletteChange:  # PalletChange happens after the new style sheet is in use.
            self.update_icon()
        return super().event(event)


class PresetWeatherWidget(QWidget):
    default_weather_conditions = {
        CONFIG_DIR_PATH.joinpath('good.weather'): "113 Sunny\n116 Partly Cloudy\n119 Cloudy\n",
        CONFIG_DIR_PATH.joinpath('bad.weather'):
            "143 Fog\n179 Light Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 "
            "Light Snow\n230 Heavy Snow\n248 Fog\n260 Fog\n266 Light Rain\n281 Light Sleet\n284 Light "
            "Sleet\n293 Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 "
            "Heavy Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
            "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
            "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
            "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
            "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
            "Thundery Snow Showers\n395 HeavySnowShowers\n",
        CONFIG_DIR_PATH.joinpath('all.weather'):
            "113 Sunny\n116 Partly Cloudy\n119 Cloudy\n122 Very Cloudy\n143 Fog\n176 Light Showers\n179 Light "
            "Sleet Showers\n182 Light Sleet\n185 Light Sleet\n200 Thundery Showers\n227 Light Snow\n230 Heavy "
            "Snow\n248 Fog\n260 Fog\n263 Light Showers\n266 Light Rain\n281 Light Sleet\n284 Light Sleet\n293 "
            "Light Rain\n296 Light Rain\n299 Heavy Showers\n302 Heavy Rain\n305 Heavy Showers\n308 Heavy "
            "Rain\n311 Light Sleet\n314 Light Sleet\n317 Light Sleet\n320 Light Snow\n323 Light Snow "
            "Showers\n326 Light Snow Showers\n329 Heavy Snow\n332 Heavy Snow\n335 Heavy Snow Showers\n338 "
            "Heavy Snow\n350 Light Sleet\n353 Light Showers\n356 Heavy Showers\n359 Heavy Rain\n362 Light "
            "Sleet Showers\n365 Light Sleet Showers\n368 Light Snow Showers\n371 Heavy Snow Showers\n374 "
            "Light Sleet Showers\n377 Light Sleet\n386 Thundery Showers\n389 Thundery Heavy Rain\n392 "
            "Thundery Snow Showers\n395 Heavy Snow Showers\n"}

    def __init__(self, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.init_weather()
        self.main_config = main_config
        self.location = main_config.get_location()
        self.required_weather_filepath: Path | None = None
        self.setLayout(widget_layout := QVBoxLayout())
        self.label = QLabel(tr("Additional weather requirements"))
        self.label.setToolTip(tr("Weather conditions will be retrieved from {}").format(WEATHER_FORECAST_URL))
        widget_layout.addWidget(self.label)
        self.chooser = QComboBox()

        def _select_action(index: int) -> None:
            self.required_weather_filepath = self.chooser.itemData(index)
            if self.chooser.itemData(index) is None:
                self.info_label.setText('')
            else:
                assert self.location is not None
                self.verify_weather_location(self.location)
                path = self.chooser.itemData(index)
                if path.exists():
                    with open(path, encoding="utf-8") as weather_file:
                        code_list = weather_file.read()
                        self.info_label.setText(code_list)
                else:
                    self.chooser.removeItem(index)
                    self.chooser.setCurrentIndex(0)
            self.populate()

        self.chooser.currentIndexChanged.connect(_select_action)
        self.chooser.setToolTip(self.label.toolTip())
        widget_layout.addWidget(self.chooser)
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.populate()
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.info_label)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setWidgetResizable(True)
        widget_layout.addWidget(scroll_area)

    def init_weather(self) -> None:
        for condition_path, condition_content in PresetWeatherWidget.default_weather_conditions.items():
            if not condition_path.exists():
                with open(condition_path, 'w', encoding="utf-8") as weather_file:
                    log.info(f"Creating {condition_path.as_posix()}")
                    weather_file.write(condition_content)

    def verify_weather_location(self, location: GeoLocation) -> None:
        if not self.main_config.is_set(ConfOpt.WEATHER_ENABLED):
            return
        place_name = location.place_name if location.place_name is not None else 'IP-address'
        # Only do this check if the location has changed.
        vf_file_path = CONFIG_DIR_PATH.joinpath('verified_weather_location.txt')
        if vf_file_path.exists():
            with open(vf_file_path, encoding="utf-8") as vf:
                if vf.read() == place_name:
                    return
        try:
            log.info(f"Verifying weather location by querying {WEATHER_FORECAST_URL}.")
            weather = weather_util.WeatherQuery(location)
            weather.run_query()
            if weather.proximity_ok:
                MBox(MIcon.Information,
                     msg=tr("Weather for {0} will be retrieved from {1}").format(place_name, WEATHER_FORECAST_URL)).exec()
                with open(vf_file_path, 'w', encoding="utf-8") as vf:
                    vf.write(place_name)
            else:
                weather_util.weather_bad_location_dialog(weather)
        except ValueError as e:
            log.error(f"Failed to validate location: {e}", trace=True)
            MBox(MIcon.Critical, msg=tr("Failed to validate weather location: {}").format(e.args[0]), info=e.args[1]).exec()

    def populate(self) -> None:
        if self.chooser.count() == 0:
            self.chooser.addItem(tr("None"), None)
        existing_paths = [self.chooser.itemData(i) for i in range(1, self.chooser.count())]
        for path in sorted(CONFIG_DIR_PATH.glob("*.weather")):
            if path not in existing_paths:
                weather_name = path.stem.replace('_', ' ')
                self.chooser.addItem(weather_name, path)

    def get_required_weather_filepath(self) -> Path | None:
        return self.required_weather_filepath if self.required_weather_filepath is not None else None

    def set_required_weather_filepath(self, weather_filename: str | None) -> None:
        if weather_filename is None:
            self.required_weather_filepath = None
            self.chooser.setCurrentIndex(0)
            self.info_label.setText('')
            return
        self.required_weather_filepath = Path(weather_filename)
        for i in range(1, self.chooser.count()):
            if self.chooser.itemData(i).as_posix() == self.required_weather_filepath.as_posix():
                self.chooser.setCurrentIndex(i)
                return

    def update_location(self, location: GeoLocation) -> None:
        self.location = location
        self.verify_weather_location(self.location)


class PresetTransitionWidget(QWidget):

    def __init__(self) -> None:
        super().__init__()
        self.setToolTip(tr("Choose whether this Preset should transition when activated a particular way."))
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        layout.addWidget(QLabel(tr("Transition")), alignment=Qt.AlignmentFlag.AlignLeft)
        self.transition_type_widget = StdButton(title=PresetTransitionFlag.NONE.description())
        self.button_menu = QMenu()
        self.transition_type = PresetTransitionFlag.NONE
        self.is_setting = False

        for transition_type in PresetTransitionFlag.ALWAYS.component_values():
            action = QAction(transition_type.description(), self.button_menu)
            action.setData(transition_type)
            action.setCheckable(True)
            action.toggled.connect(self.update_value)
            self.button_menu.addAction(action)

        self.transition_type_widget.setMenu(self.button_menu)
        layout.addWidget(self.transition_type_widget, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(20)
        layout.addWidget(QLabel(tr("Transition step")), alignment=Qt.AlignmentFlag.AlignRight)
        self.step_seconds_widget = QSpinBox()
        self.step_seconds_widget.setRange(0, 60)
        layout.addWidget(self.step_seconds_widget, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QLabel(tr("sec.")), alignment=Qt.AlignmentFlag.AlignRight)

    def update_value(self, checked: bool) -> None:
        if self.is_setting:
            return
        if checked:
            MBox(MIcon.Warning,
                 msg=tr('Transitions have been deprecated to minimize wear on VDU NVRAM.'),
                 info=tr('Transitions are slated for removal, please contact the developer if you wish to retain them.')).exec()
        for act in self.button_menu.actions():
            if act.isChecked():
                self.transition_type |= act.data()
            elif act.data() in self.transition_type:
                self.transition_type ^= act.data()
        self.transition_type_widget.setText(str(self.transition_type.description()))

    def set_transition_type(self, transition_type: PresetTransitionFlag) -> None:
        try:
            self.is_setting = True
            self.transition_type = transition_type
            for act in self.button_menu.actions():
                act.setChecked(self.transition_type & act.data())
            self.transition_type_widget.setText(str(self.transition_type.description()))
        finally:
            self.is_setting = False

    def set_step_seconds(self, seconds: int) -> None:
        self.step_seconds_widget.setValue(seconds)

    def get_transition_type(self) -> PresetTransitionFlag:
        return self.transition_type

    def get_step_seconds(self) -> int:
        return self.step_seconds_widget.value()


class PresetElevationChartWidget(QLabel):
    selected_elevation_qtsignal = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(npx(300), npx(350))
        self.sun_image: QImage | None = None
        self.setMouseTracking(True)
        self.in_drag = False
        self.current_pos: QPoint | None = None
        self.cache_solar_by_elevation: Dict[SolarElevationKey, SolarElevationData] = {}
        self.elevation_key: SolarElevationKey | None = None
        self.location: GeoLocation | None = None
        self.elevation_steps: List[SolarElevationKey] = []
        for i in range(-19, 90):
            self.elevation_steps.append(SolarElevationKey(EASTERN_SKY, i))
        for i in range(90, -20, -1):
            self.elevation_steps.append(SolarElevationKey(WESTERN_SKY, i))
        self.noon_x: int = npx(100)
        self.noon_y: int = npx(25)
        self.horizon_y: int = npx(75)
        self.radius_of_deletion = npx(50)
        self.solar_max_t: datetime | None = None
        self.last_event_time = time.time()
        self.cache_key: Tuple[datetime, int, int, int] | None = None
        self.cache_curve_points: List[QPoint] = []

    def has_elevation_key(self, key: SolarElevationKey) -> bool:
        return key in self.elevation_steps

    def get_elevation_data(self, elevation_key: SolarElevationKey) -> SolarElevationData | None:
        assert self.cache_solar_by_elevation is not None
        return self.cache_solar_by_elevation[elevation_key] if elevation_key in self.cache_solar_by_elevation else None

    def set_elevation_key(self, elevation_key: SolarElevationKey | None) -> None:
        self.elevation_key = elevation_key
        self.create_plot()

    def configure_for_location(self, location: GeoLocation | None) -> None:
        self.location = location
        if location is not None:
            self.cache_key = None
            self.elevation_key = None
            self.create_plot()

    def _reverse_X(self, x: int) -> int:  # makes thinking right-to-left a bit easier. MAYBE
        return self.width() - x

    def create_plot(self) -> None:
        ev_key = self.elevation_key
        logical_width, logical_height = self.width(), self.height()
        origin_iy, range_iy = round(logical_height / 2), round(logical_height / 2.5)
        self.radius_of_deletion = round(range_iy * 0.8)
        self.horizon_y = origin_iy
        line_width = npx(4)
        thin_line_width = npx(2)
        dp_ratio = self.devicePixelRatio()
        pixmap = QPixmap(round(logical_width * dp_ratio), round(logical_height * dp_ratio))
        pixmap.setDevicePixelRatio(dp_ratio)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(0, 0, logical_width, origin_iy, QColor(0x5b93c5))
        painter.fillRect(0, origin_iy, logical_width, logical_height, QColor(0x7d5233))
        painter.setPen(QPen(Qt.GlobalColor.white, line_width))  # Horizon
        painter.drawLine(0, origin_iy, logical_width, origin_iy)

        _reverse_x = self._reverse_X

        if self.location is not None:
            self.refresh_day_cache(logical_width, origin_iy, range_iy)
            curve_points = self.cache_curve_points
            solar_noon_x, solar_noon_y = self.noon_x, self.noon_y,
            if ev_key and (solar_data := self.cache_solar_by_elevation.get(ev_key)):
                seconds_since_midnight = (
                            solar_data.when - solar_data.when.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                sun_plot_time = solar_data.when
                sun_plot_x = round(logical_width * seconds_since_midnight / (60.0 * 60.0 * 24.0))
                sun_height = math.sin(math.radians(90.0 - solar_data.zenith)) * range_iy
                sun_plot_y = origin_iy - round(sun_height)
            else:
                sun_plot_time = None
                sun_plot_x = self.noon_x
                sun_plot_y = self.noon_y

            # Draw an elevation curve for today from the accumulated plot points:
            painter.setPen(QPen(QColor(0xff965b), line_width))
            painter.drawPoints(QPolygon(curve_points))

            # Draw various annotations such the horizon-line, noon-line, E & W, and the current degrees:
            painter.setPen(QPen(Qt.GlobalColor.white, line_width))
            painter.drawLine(_reverse_x(0), origin_iy, _reverse_x(logical_width), origin_iy)
            painter.drawLine(_reverse_x(solar_noon_x), origin_iy, _reverse_x(solar_noon_x), 0)
            painter.setPen(QPen(Qt.GlobalColor.white, line_width))
            painter.setFont(QFont(QApplication.font().family(), pt := 18, QFont.Weight.Bold))
            painter.drawText(QPoint(_reverse_x((txt_margin := npx(25)) + pt), origin_iy - npx(32)), tr("E"))
            painter.drawText(QPoint(_reverse_x(logical_width - txt_margin), origin_iy - npx(32)), tr("W"))
            time_text = sun_plot_time.strftime("%H:%M") if sun_plot_time else "____"
            painter.drawText(_reverse_x(solar_noon_x + logical_width // 4), logical_height - npx(25),
                             f"{ev_key.elevation if ev_key else 0:3d}{DEGREE_SYMBOL} {time_text}")

            # Draw pie/compass angle
            if ev_key:
                angle_above_horz = ev_key.elevation if ev_key.direction == EASTERN_SKY else (
                            180 - ev_key.elevation)  # anticlockwise from 0
            else:
                angle_above_horz = 180 + 19
            _, pos_as_radius = self.calc_angle_radius(self.current_pos) if self.current_pos else (0, 21)
            pie_width = pie_height = range_iy * 2
            span_angle = -(angle_above_horz + 19)  # From start angle spanning counterclockwise back toward the right to -19.
            painter.setPen(
                QPen(QColor(
                    0xffffff if self.current_pos is None or self.in_drag or pos_as_radius > self.radius_of_deletion else 0xff0000),
                     2))
            painter.setBrush(QColor(255, 255, 255, 64))
            painter.drawPie(_reverse_x(solar_noon_x) - pie_width // 2, origin_iy - pie_height // 2, pie_width, pie_height,
                            angle_above_horz * 16, span_angle * 16)

            # Draw drag-dot
            painter.setFont(QFont(QApplication.font().family(), 8, QFont.Weight.Normal))
            if self.current_pos is not None or self.in_drag or pos_as_radius >= self.radius_of_deletion:
                painter.setPen(QPen(Qt.GlobalColor.red, npx(6)))
                painter.setBrush(Qt.GlobalColor.white)
                ddot_radians = math.radians(angle_above_horz if ev_key else -19)
                ddot_radius = npx(8)
                ddot_x = round(range_iy * math.cos(ddot_radians)) - ddot_radius
                ddot_y = round(range_iy * math.sin(ddot_radians)) + ddot_radius
                painter.drawEllipse(_reverse_x(solar_noon_x - ddot_x), origin_iy - ddot_y, ddot_radius * 2, ddot_radius * 2)
                if not self.in_drag:
                    painter.setPen(QPen(Qt.GlobalColor.black, 1))
                    painter.drawText(QPoint(_reverse_x(solar_noon_x - ddot_x) + npx(10), origin_iy - ddot_y - npx(5)),
                                     tr("Drag to change."))

            # Draw origin-dot
            painter.setPen(QPen(QColor(0xff965b), thin_line_width))
            if self.current_pos is not None and not self.in_drag:
                if pos_as_radius < self.radius_of_deletion:
                    painter.setPen(QPen(Qt.GlobalColor.black, npx(1)))
                    painter.drawText(QPoint(_reverse_x(solar_noon_x + 8) + npx(10), origin_iy - npx(8) - npx(5)),
                                     tr("Click to delete."))
                    painter.setPen(QPen(Qt.GlobalColor.red, thin_line_width))
            odot_radius = npx(8)
            painter.setBrush(painter.pen().color())
            painter.drawEllipse(_reverse_x(solar_noon_x + odot_radius), origin_iy - odot_radius, odot_radius * 2, odot_radius * 2)

            if ev_key:
                # Draw a line representing the slider degrees and Twilight indicator - may be higher than the sun for today:
                sky_line_y = origin_iy - round(math.sin(math.radians(ev_key.elevation)) * range_iy)
                if sky_line_y >= solar_noon_y:
                    sky_line_pen = QPen(Qt.GlobalColor.white, thin_line_width)
                else:
                    sky_line_pen = QPen(QColor(0xcccccc), thin_line_width)
                    sky_line_pen.setStyle(Qt.PenStyle.DotLine)
                painter.setPen(sky_line_pen)
                painter.setBrush(painter.pen().color())

                pyramid_base = npx(16)
                if ev_key.direction == EASTERN_SKY:  # Triangle pointing up
                    pyramid = [(-pyramid_base // 2, 0), (0, -pyramid_base), (pyramid_base // 2, 0)]
                    painter.drawLine(_reverse_x(0), sky_line_y, _reverse_x(solar_noon_x), sky_line_y)
                    painter.setPen(QPen(painter.pen().color(), 1))
                    painter.drawPolygon(
                        QPolygon([QPoint(_reverse_x(0 + npx(20) + tx), sky_line_y - npx(10) + ty) for tx, ty in pyramid]))
                else:  # Triangle pointing down
                    inverted_pyramid = [(-pyramid_base // 2, 0), (0, pyramid_base), (pyramid_base // 2, 0)]
                    painter.drawLine(_reverse_x(solar_noon_x), sky_line_y, _reverse_x(logical_width), sky_line_y)
                    painter.setPen(QPen(painter.pen().color(), 1))
                    painter.drawPolygon(
                        QPolygon([QPoint(_reverse_x(logical_width - npx(18)) + tx, sky_line_y + npx(10) + ty)
                                  for tx, ty in inverted_pyramid]))
                # Draw the sun
                painter.setPen(QPen(QColor(0xff4a23), line_width))
                if self.sun_image is None:
                    sun_image = create_image_from_svg_bytes(SUN_SVG.replace(SVG_LIGHT_THEME_COLOR, b"#fecf70"))
                    self.sun_image = sun_image.scaled(npx(sun_image.width()), npx(sun_image.height()))
                painter.drawImage(QPoint(_reverse_x(sun_plot_x) - self.sun_image.width() // 2,
                                         sun_plot_y - self.sun_image.height() // 2), self.sun_image)
        painter.end()
        self.setPixmap(pixmap)

    def refresh_day_cache(self, logical_width: int, origin_iy: int, range_iy: int) -> None:
        # Perform computations for today's curve and maxima.
        _reverse_x = self._reverse_X
        new_cache_key = ((zoned_now().replace(hour=0, minute=0, second=0, microsecond=0)), logical_width, origin_iy, range_iy)
        if self.cache_key and new_cache_key == self.cache_key:
            return
        log.debug(f"PresetElevationChartWidget: change of key values {new_cache_key=}, recalculating")
        self.cache_key = new_cache_key
        max_sun_height = npx(-90.0)
        solar_noon_x, solar_noon_y = 0, 0  # Solar noon
        curve_points = []

        def _create_curve(a, z, t):  # Gets called for every 1-minute point - to create a smooth curve.
            nonlocal max_sun_height, solar_noon_x, solar_noon_y
            second_of_day = (t - t.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            x = round(logical_width * second_of_day / (60.0 * 60.0 * 24.0))
            sun_height = math.sin(math.radians(90.0 - z)) * range_iy
            y = origin_iy - round(sun_height)
            curve_points.append(QPoint(_reverse_x(x), y))  # Save the plot points to a list
            if sun_height > max_sun_height:
                max_sun_height = sun_height
                solar_noon_x, solar_noon_y = x, y
                self.solar_max_t = t

        self.cache_solar_by_elevation = create_elevation_map(zoned_now(),
                                                             latitude=self.location.latitude, longitude=self.location.longitude,
                                                             callback=_create_curve)
        self.noon_x = solar_noon_x
        self.noon_y = solar_noon_y
        self.cache_curve_points = curve_points

    def calc_angle_radius(self, pos: QPoint) -> Tuple[int, int]:
        x, y = pos.x(), pos.y()
        adjacent = x - self._reverse_X(self.noon_x)
        opposite = self.horizon_y - y
        angle = 90 if adjacent == 0 else round(math.degrees(math.atan(opposite / adjacent)))
        radius = round(math.sqrt(adjacent ** 2 + opposite ** 2))
        return angle, radius

    def update_current_pos(self, local_pos: QPoint) -> QPoint | None:
        self.current_pos = local_pos if (0 < local_pos.x() < self.width() and 0 <= local_pos.y() < self.height()) else None
        return self.current_pos

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event:
            if pos := self.update_current_pos(event.pos()):
                angle, radius = self.calc_angle_radius(pos)
                if radius <= self.radius_of_deletion:
                    self.set_elevation_key(None)
                    self.selected_elevation_qtsignal.emit(None)
                else:
                    self.in_drag = True
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event:
            self.update_current_pos(event.pos())
            self.in_drag = False
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event:
            event.accept()
            if (now := time.time()) - self.last_event_time < 0.1:  # Prevent event overload on Qt6 kwin-wayland
                return
            self.last_event_time = now
            pos = self.update_current_pos(event.pos())
            if pos is not None and 0 <= pos.x() < self.width() and 0 <= pos.y() < self.height():
                angle, radius = self.calc_angle_radius(pos)
                if self.in_drag:
                    self.current_pos = pos
                    angle = -angle if pos.x() < self._reverse_X(self.noon_x) else angle
                    eastern = pos.x() >= self._reverse_X(self.noon_x)
                    key = SolarElevationKey(EASTERN_SKY if eastern else WESTERN_SKY, angle)
                    if not key in self.elevation_steps:
                        key = self.elevation_steps[0 if eastern else -1]
                    self.set_elevation_key(key)
                    self.selected_elevation_qtsignal.emit(key)
            self.create_plot()  # necessary to detect deletions

    def leaveEvent(self, event: QEvent | None) -> None:
        self.current_pos = None
        self.create_plot()
        super().leaveEvent(event)


class PresetDaylightFactorWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setLayout(QHBoxLayout())
        self.df_checkbox = QCheckBox()
        self.df_label = QLabel(tr("Daylight-Factor"))
        self.df_input = QLineEdit()
        self.df_input.setValidator(QDoubleValidator())
        self.setEnabled(False)
        self.df_checkbox.toggled.connect(self.setEnabled)
        self.setToolTip(tr("Save the current semi-automatic Light-Metering Daylight-Factor (DF) as part of the Preset."))

        def df_init(state):
            if state == Qt.CheckState.Checked:
                if self.df_input.text() == '':
                    from lux_meters import LuxMeterSemiAutoDevice
                    self.df_input.setText(f"{LuxMeterSemiAutoDevice.get_daylight_factor():.4f}")
            else:
                self.df_input.setText('')

        self.df_checkbox.stateChanged.connect(df_init)
        for widget in (self.df_checkbox, self.df_label, self.df_input):
            self.layout().addWidget(widget)

    def setEnabled(self, enabled):
        self.df_checkbox.setChecked(enabled)
        self.df_label.setEnabled(enabled)
        self.df_input.setEnabled(enabled)


class PresetScheduleAtWidgetBase(QWidget):  # Abstract

    def __init__(self, description: str):
        super().__init__()
        self.description = description
        self.all_schedule_chooser_widgets: List[PresetScheduleAtWidgetBase] = []

    def set_schedule_widgets(self, all_widgets: List[PresetScheduleAtWidgetBase]):
        self.all_schedule_chooser_widgets = all_widgets

    def clear_others(self, _=None) -> bool:  # Only allow a Preset to be scheduled once.
        others = [w for w in self.all_schedule_chooser_widgets if w != self and w.is_set()]
        if others and MBox(MIcon.Question, msg=tr('Preset already scheduled. Clear existing {}?').format(others[0].description),
                           info=tr('Duplicate the preset if you need to schedule it more than once.'),
                           buttons=MBtn.Ok | MBtn.Cancel).exec() == MBtn.Cancel:
            return False
        for schedule_chooser in others:
            schedule_chooser.clear()
        return True

    def is_set(self) -> bool:  # Abstract
        return False

    def clear(self) -> None:  # Abstract
        pass


class PresetScheduleAtElevationWidget(PresetScheduleAtWidgetBase):
    _slider_select_elevation_qtsignal = pyqtSignal(object)

    def __init__(self, main_config: VduControlsConfig) -> None:
        super().__init__(description=tr("elevation-trigger"))
        self.elevation_key: SolarElevationKey | None = None
        self.location = main_config.get_location()
        self.setLayout(main_layout := QVBoxLayout())
        self.title_prefix = tr("Trigger at solar elevation:")
        self.title_label = QLabel(self.title_prefix)
        self.title_label.setFixedHeight(
            native_font_height(scaled=1.5))  # Stop ascenders/descenders in Unicode from altering layout.
        self.title_label.setToolTip(tr("Trigger at a set solar elevation (sun angle at your geolocation and time)."))
        main_layout.addWidget(self.title_label)

        self.elevation_chart = PresetElevationChartWidget()
        self.elevation_chart.selected_elevation_qtsignal.connect(self.set_elevation_key)

        self.df_widget = PresetDaylightFactorWidget()

        self.slider_last_event_time = time.time()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(-1)
        self.slider.setValue(-1)
        self.slider.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.slider.setTickInterval(5)
        self.slider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self._slider_select_elevation_qtsignal.connect(self.set_elevation_key)

        bottom_layout = QHBoxLayout()
        main_layout.addLayout(bottom_layout)

        chart_and_slider_layout = QVBoxLayout()
        chart_and_slider_layout.addWidget(self.elevation_chart, 1)
        chart_and_slider_layout.addWidget(self.slider)
        chart_and_slider_layout.addWidget(self.df_widget, 0)
        bottom_layout.addLayout(chart_and_slider_layout, 1)

        self.weather_widget = PresetWeatherWidget(main_config)
        bottom_layout.addWidget(self.weather_widget, 0)
        self.configure_for_location(self.location)
        self.slider.valueChanged.connect(self.sliding)

        self.setMinimumWidth(npx(400))
        self.sun_image: QImage | None = None

    def is_set(self) -> bool:
        return self.elevation_key is not None

    def clear(self) -> None:
        self.set_elevation_key(None)

    def sliding(self) -> None:
        if (now := time.time()) - self.slider_last_event_time < 0.1:  # Prevent event overload on Qt6 kwin-wayland
            return
        self.slider_last_event_time = now
        value = self.slider.value()
        if value == -1:
            self._slider_select_elevation_qtsignal.emit(None)
            return
        chart = self.elevation_chart
        self._slider_select_elevation_qtsignal.emit(
            chart.elevation_steps[value] if 0 <= value < len(chart.elevation_steps) else None)

    def show_elevation_description(self) -> None:
        if self.elevation_key is None:
            self.title_label.setText(self.title_prefix)
            return
        elevation_data = self.elevation_chart.get_elevation_data(self.elevation_key)
        occurs_at = elevation_data.when if elevation_data is not None else None  # No elev data => sun doesn't rise this high today
        if occurs_at:
            when_text = tr("today at {}").format(occurs_at.strftime('%H:%M'))
        else:
            when_text = tr("the sun does not rise this high today")
        # https://en.wikipedia.org/wiki/Twilight
        if self.elevation_key.elevation < 1:
            if self.elevation_key.elevation >= -6:
                when_text += " " + (tr("dawn") if self.elevation_key.direction == EASTERN_SKY else tr("dusk"))
            elif self.elevation_key.elevation >= -18:  # Astronomical twilight
                when_text += " " + tr("twilight")
            else:
                when_text += " " + tr("nighttime")
        if elevation_data is not None and self.location:
            if lux := calc_solar_lux(elevation_data.when, self.location, 1.0):
                when_text += tr(" {:,} lux").format(lux)
        desc_text = tr("{0} {1} ({2}, {3})").format(
            self.title_prefix, format_solar_elevation_abbreviation(self.elevation_key), tr(self.elevation_key.direction), when_text)
        if desc_text != self.title_label.text():
            self.title_label.setText(desc_text)

    def configure_for_location(self, location: GeoLocation | None) -> None:
        self.elevation_chart.configure_for_location(location)
        self.location = location
        if location is None:
            self.title_label.setText(self.title_prefix + tr("location undefined (see settings)"))
            self.slider.setDisabled(True)
            return
        self.slider.setEnabled(True)
        self.slider.setMaximum(len(self.elevation_chart.elevation_steps) - 1)
        self.slider.setValue(-1)
        self.sliding()
        self.weather_widget.update_location(location)
        if self.elevation_chart.solar_max_t is not None:
            snt = self.elevation_chart.solar_max_t
            if snt.hour > (15 if snt.tzname() == 'CST' else 14) or snt.hour < 10:  # Solar midday seems too far from 12:00 midday.
                log.warning(f"Location {location.longitude},{location.latitude} and timezone {snt.tzname()} seem mismatched.")

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self.elevation_chart.set_elevation_key(self.elevation_key)

    def set_elevation_from_text(self, elevation_text: str | None) -> None:
        if elevation_text is not None and elevation_text.strip() != '' and len(self.elevation_chart.elevation_steps) != 0:
            elevation_key = parse_solar_elevation_ini_text(elevation_text)
            if self.elevation_chart.has_elevation_key(elevation_key):
                self.set_elevation_key(elevation_key)
                return
        self.set_elevation_key(None)

    def set_elevation_key(self, elevation_key: SolarElevationKey | None) -> None:
        if elevation_key is not None:
            if self.clear_others():
                if self.elevation_chart.has_elevation_key(elevation_key):
                    self.elevation_key = elevation_key
                    self.slider.setValue(self.elevation_chart.elevation_steps.index(self.elevation_key))
                    self.slider.setToolTip(f"{self.elevation_key.elevation}{DEGREE_SYMBOL}")
                    self.elevation_chart.set_elevation_key(self.elevation_key)
                    self.weather_widget.setEnabled(True)
                    self.show_elevation_description()
                    return
        self.elevation_key = None
        self.slider.setValue(-1)
        self.elevation_chart.set_elevation_key(None)
        self.weather_widget.setEnabled(False)
        self.weather_widget.chooser.setCurrentIndex(0)
        self.show_elevation_description()

    def get_required_weather_filename(self) -> str | None:
        path = self.weather_widget.get_required_weather_filepath()
        return path.as_posix() if path else None

    def set_required_weather_filename(self, weather_filename: str | None) -> None:
        self.weather_widget.set_required_weather_filepath(weather_filename)


class PresetScheduleAtTimeWidget(PresetScheduleAtWidgetBase):
    class TimeFieldValidator(QValidator):

        def validate(self, text, pos):
            if len(text) < 4:
                return QValidator.State.Intermediate, text, pos
            state = QValidator.State.Invalid
            for acceptable_format in ['%H:%M', '%H%M']:
                try:
                    datetime.strptime(text, acceptable_format)
                    state = QValidator.State.Acceptable
                    break
                except ValueError:
                    pass
            return state, text, pos

    def __init__(self):
        super().__init__(description=tr("time-trigger"))
        self.setToolTip(tr("Trigger at the same time (hh:mm) each day."))
        self.setLayout(at_time_layout := QHBoxLayout())
        at_time_layout.addWidget(QLabel(tr("Trigger at time:")))
        self.editor_at_time_field = QLineEdit()
        self.editor_at_time_field.setValidator(PresetScheduleAtTimeWidget.TimeFieldValidator())
        at_time_layout.addWidget(self.editor_at_time_field)

        def clear_others_ask(_: str):
            if not self.clear_others():
                self.clear()

        self.editor_at_time_field.textChanged.connect(clear_others_ask)
        at_time_layout.addStretch(1)
        at_time_layout.setContentsMargins(0, 0, 0, 0)

    def is_set(self) -> bool:
        return len(self.text()) != 0

    def clear(self) -> None:
        if self.text():
            self.setText('')

    def setText(self, text: str) -> None:
        self.editor_at_time_field.setText(text)

    def text(self) -> str:
        if text := self.editor_at_time_field.text():
            if len(text) == 4:
                text = f"{text[:2]}:{text[2:]}"
        return text


class PresetsDialog(SubWinDialog, DialogSingletonMixin):  # TODO has become rather complex - break into parts?
    """A dialog for creating/updating/removing presets."""
    NO_ICON_ICON_NUMBER = StdPixmap.SP_ComputerIcon

    @staticmethod
    def invoke(main_controller: VduAppController, main_config: VduControlsConfig) -> None:
        PresetsDialog.show_existing_dialog() if PresetsDialog.exists() else PresetsDialog(main_controller, main_config)
        PresetsDialog.show_status_message('')

    @staticmethod
    def show_status_message(message: str = '', timeout: int = 0) -> None:
        if presets_dialog := PresetsDialog.get_instance():  # type: ignore
            if message != '':
                presets_dialog.status_message(message, timeout=timeout)
            elif not presets_dialog.main_config.is_set(ConfOpt.SCHEDULE_ENABLED):
                presets_dialog.status_message(
                    WARNING_SYMBOL + ' ' + tr('Preset scheduling is disabled in the Setting-Dialog.'))
            elif not presets_dialog.main_config.is_set(ConfOpt.WEATHER_ENABLED):
                presets_dialog.status_message(WARNING_SYMBOL + ' ' + tr('Weather lookup is disabled in the Setting-Dialog.'),
                                              timeout=60000)
            else:
                presets_dialog.status_message('')

    @staticmethod
    def reconfigure_instance() -> None:
        if presets_dialog := PresetsDialog.get_instance():  # type: ignore
            presets_dialog.reconfigure()

    @staticmethod
    def is_instance_editing() -> bool:
        if presets_dialog := PresetsDialog.get_instance():
            return presets_dialog.preset_name_edit.text() != ''
        return False

    @staticmethod
    def instance_indicate_active_preset(preset: Preset | None = None):
        if presets_dialog := PresetsDialog.get_instance():
            presets_dialog.indicate_active_preset(preset)

    @staticmethod
    def instance_edit_preset(preset: Preset | None = None):
        if presets_dialog := PresetsDialog.get_instance():
            presets_dialog.edit_preset(preset)

    def __init__(self, main_controller: VduAppController, main_config: VduControlsConfig) -> None:
        super().__init__()
        self.setWindowTitle(tr('Presets'))
        self.main_controller = main_controller
        self.main_config = main_config
        self.content_controls_map: Dict[Tuple[str, str], QCheckBox] = {}
        self.resize(npx(1800), npx(1200))
        self.setMinimumSize(npx(1350), npx(600))
        layout = QVBoxLayout()
        self.setLayout(layout)

        dialog_splitter = QSplitter()
        dialog_splitter.setOrientation(Qt.Orientation.Horizontal)
        dialog_splitter.setHandleWidth(npx(10))
        layout.addWidget(dialog_splitter, stretch=1)

        preset_list_panel = QGroupBox()
        preset_list_panel.setMinimumWidth(npx(550))
        preset_list_panel.setFlat(True)
        preset_list_layout = QVBoxLayout()
        preset_list_panel.setLayout(preset_list_layout)
        preset_list_title = QLabel(tr("Presets"))
        preset_list_title.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        preset_list_layout.addWidget(preset_list_title)
        self.preset_widgets_scroll_area = QScrollArea(parent=self)
        preset_widgets_content = QWidget()
        self.preset_widgets_layout = QVBoxLayout()
        self.preset_widgets_layout.setSpacing(0)
        preset_widgets_content.setLayout(self.preset_widgets_layout)
        self.preset_widgets_scroll_area.setWidget(preset_widgets_content)
        self.preset_widgets_scroll_area.setWidgetResizable(True)
        preset_list_layout.addWidget(self.preset_widgets_scroll_area)
        dialog_splitter.addWidget(preset_list_panel)

        main_controller.refresh_preset_menu()
        self.base_ini = ConfIni()  # Create a temporary holder of preset values
        main_controller.populate_ini_from_vdus(self.base_ini)

        self.populate_presets_display_list()

        self.edit_panel = QWidget(parent=self)
        edit_panel_layout = QHBoxLayout()
        self.edit_panel.setLayout(edit_panel_layout)
        self.edit_panel.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))

        self.edit_choose_icon_button = PresetIconPickerButton()
        edit_panel_layout.addWidget(self.edit_choose_icon_button)

        self.preset_name_edit = QLineEdit()
        self.preset_name_edit.setToolTip(tr('Enter a new preset name.'))
        self.preset_name_edit.setClearButtonEnabled(True)
        self.preset_name_edit.textChanged.connect(self.change_edit_group_title)
        self.preset_name_edit.setValidator(QRegularExpressionValidator(QRegularExpression("[A-Za-z0-9][A-Za-z0-9_ .-]{0,60}")))

        self.vip_menu = QMenu()
        self.vip_menu.triggered.connect(self.vip_menu_triggered)
        edit_panel_layout.addWidget(self.preset_name_edit)
        self.vdu_init_button = ToolButton(VDU_POWER_ON_ICON_SOURCE, tr("Create VDU specific\nInitialization-Preset"), self)
        self.vdu_init_button.setMenu(self.vip_menu)
        self.vdu_init_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        edit_panel_layout.addWidget(self.vdu_init_button)

        self.editor_groupbox = QGroupBox()
        self.editor_groupbox.setFlat(True)
        self.editor_groupbox.setMinimumSize(npx(550), npx(768))
        self.editor_layout = QVBoxLayout()
        self.editor_layout.setSpacing(npx(20))
        self.editor_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        self.editor_title = QLabel(tr("New Preset:"))
        self.editor_title.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        self.editor_layout.addWidget(self.editor_title)
        self.editor_groupbox.setLayout(self.editor_layout)

        self.editor_controls_widget = QScrollArea(parent=self)
        self.populate_editor_controls_widget()
        self.editor_layout.addWidget(self.edit_panel)

        self.controls_title_widget = self.editor_controls_prompt = QLabel(tr("Controls to include:"))
        self.controls_title_widget.setDisabled(True)
        self.editor_layout.addWidget(self.controls_title_widget)
        self.editor_layout.addWidget(self.editor_controls_widget)

        self.editor_transitions_widget = PresetTransitionWidget()
        if self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED):
            self.editor_layout.addItem(QSpacerItem(1, 10))
        else:
            self.editor_layout.addWidget(self.editor_transitions_widget)

        self.editor_at_time_widget = PresetScheduleAtTimeWidget()
        self.editor_layout.addWidget(self.editor_at_time_widget)

        self.editor_at_elevation_widget = PresetScheduleAtElevationWidget(main_config)
        self.editor_layout.addWidget(self.editor_at_elevation_widget)

        possibles = [self.editor_at_time_widget, self.editor_at_elevation_widget]
        for schedule_choice_widget in possibles:
            schedule_choice_widget.set_schedule_widgets(possibles)

        dialog_splitter.addWidget(self.editor_groupbox)
        dialog_splitter.setCollapsible(0, False)
        dialog_splitter.setCollapsible(1, False)
        dialog_splitter.setSizes([preset_list_panel.minimumSize().width(), self.editor_groupbox.minimumSize().width()])

        self.status_bar = QStatusBar()

        def _revert_callable() -> None:
            preset_widget = self.find_preset_widget(self.preset_name_edit.text().strip())
            if preset_widget is None:
                self.preset_name_edit.setText('')
            else:
                self.edit_preset(preset_widget.preset)

        self.edit_clear_button = StdButton(icon=si(self, StdPixmap.SP_DialogCancelButton), title=tr('Clear'),
                                           clicked=self.reset_editor,
                                           tip=tr("Clear edits and enter a new preset using the defaults."))
        self.edit_save_button = StdButton(icon=si(self, StdPixmap.SP_DialogSaveButton), title=tr('Save'), clicked=self.save_preset,
                                          tip=tr("Save current VDU settings to Preset."))
        self.edit_revert_button = StdButton(icon=si(self, StdPixmap.SP_DialogResetButton), title=tr('Revert'),
                                            clicked=_revert_callable,
                                            tip=tr("Abandon edits, revert VDU and Preset settings."))
        self.close_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=tr('Close'), clicked=self.close)
        for button in (self.edit_clear_button, self.edit_save_button, self.edit_revert_button, self.close_button):
            self.status_bar.addPermanentWidget(button)
        layout.addWidget(self.status_bar)

        self.edit_choose_icon_button.set_preset(None)
        self.editor_controls_widget.setDisabled(True)
        self.editor_at_time_widget.setDisabled(True)
        self.editor_transitions_widget.setDisabled(True)
        self.editor_at_elevation_widget.setDisabled(True)
        self.edit_save_button.setDisabled(True)
        self.edit_revert_button.setDisabled(True)

        self.indicate_active_preset(self.main_controller.which_preset_is_active())
        self.editor_controls_widget.adjustSize()
        self.make_visible()

    def sizeHint(self) -> QSize:
        return QSize(npx(1200), npx(768))

    def populate_presets_display_list(self) -> None:
        for i in range(self.preset_widgets_layout.count() - 1, -1, -1):  # Remove existing entries
            if item := self.preset_widgets_layout.itemAt(i):
                w = item.widget()
                if isinstance(w, PresetItemWidget):
                    self.preset_widgets_layout.removeWidget(w)
                    w.deleteLater()
                else:
                    self.preset_widgets_layout.removeItem(item)
        for preset_def in self.main_controller.preset_controller.find_presets_map().values():  # Populate new entries
            self.preset_widgets_layout.addWidget(self.create_preset_widget(preset_def))
        self.preset_widgets_layout.addStretch(1)

    def reconfigure(self) -> None:
        self.populate_presets_display_list()
        existing_content = self.editor_controls_widget.takeWidget()
        existing_content.deleteLater() if existing_content is not None else None
        self.base_ini = ConfIni()
        self.main_controller.populate_ini_from_vdus(self.base_ini)
        self.populate_editor_controls_widget()
        self.reset_editor()
        self.editor_at_elevation_widget.configure_for_location(self.main_config.get_location())

    def reset_editor(self):
        self.preset_name_edit.setText('')
        self.edit_choose_icon_button.reset()
        for checkbox in self.content_controls_map.values():
            checkbox.setChecked(True)

    def status_message(self, message: str, timeout: int = 0) -> None:
        self.status_bar.showMessage(message, msecs=3000 if timeout == -1 else timeout)

    def vip_menu_triggered(self, action: QAction):
        vdu_stable_id = action.data()
        if MBox(MIcon.Information, msg=tr('Create an initialization-preset for {}.').format(action.text()),
                info=tr('Initialization-presets are restored at startup or when ever the VDU is subsequently detected.'),
                buttons=MBtn.Ok | MBtn.Cancel).exec() == MBtn.Cancel:
            return
        self.preset_name_edit.setText(vdu_stable_id)
        for (section, option), checkbox in self.content_controls_map.items():
            checkbox.setChecked(section == vdu_stable_id)

    def find_preset_widget(self, preset_name: str) -> PresetItemWidget | None:
        for i in range(self.preset_widgets_layout.count()):
            w = self.preset_widgets_layout.itemAt(i).widget()
            if isinstance(w, PresetItemWidget) and w.name == preset_name:
                return w
        return None

    def indicate_active_preset(self, preset: Preset | None = None):
        self.preset_widgets_layout.findChildren(PresetItemWidget)
        for i in range(self.preset_widgets_layout.count()):
            if item := self.preset_widgets_layout.itemAt(i):
                w = item.widget()
                if isinstance(w, PresetItemWidget):
                    w.update_timer_button()
                    w.indicate_active(preset is not None and w.name == preset.name)

    def populate_editor_controls_widget(self):
        container = self.editor_controls_widget
        container.setMinimumHeight(native_font_height(scaled=6))  # making this too big throws the parent layout out of wack
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.content_controls_map = {}
        self.vip_menu.clear()  # VIP - VDU Initialization Preset
        for count, vdu_section_name in enumerate(self.base_ini.data_sections()):
            vdu_name = self.main_controller.get_vdu_preferred_name(vdu_section_name)
            if count > 0:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                layout.addWidget(line)
            group_box = QGroupBox(vdu_name)
            group_box.setFlat(True)
            group_box.setToolTip(tr("Choose which settings to save for {}").format(vdu_name))
            group_layout = QHBoxLayout()
            group_box.setLayout(group_layout)
            for option in self.base_ini[vdu_section_name]:
                option_control = QCheckBox(translate_option(option))
                group_layout.addWidget(option_control)
                self.content_controls_map[(vdu_section_name, option)] = option_control
                option_control.setChecked(True)
            layout.addWidget(group_box)
            vip_action = QAction(f"{vdu_section_name} ({vdu_name})" if vdu_section_name != vdu_name else vdu_section_name,
                                 self.vip_menu)
            vip_action.setData(vdu_section_name)
            self.vip_menu.addAction(vip_action)
        container.setWidget(widget)

    def set_widget_values_from_preset(self, preset: Preset):
        self.preset_name_edit.setText(preset.name)
        self.edit_choose_icon_button.set_preset(preset)
        for key, item in self.content_controls_map.items():
            item.setChecked(preset.preset_ini.has_option(key[0], key[1]))
        if preset.preset_ini.has_section('preset'):
            self.editor_at_elevation_widget.clear()  # Clear both fields to stop any cross-field validation triggers.
            self.editor_at_time_widget.clear()
            self.editor_at_time_widget.setText(preset.get_at_time().strftime("%H:%M") if preset.get_at_time() else '')
            self.editor_at_elevation_widget.set_elevation_from_text(
                preset.preset_ini.get('preset', 'solar-elevation', fallback=None))
            self.editor_at_elevation_widget.set_required_weather_filename(
                preset.preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None))
            self.editor_transitions_widget.set_transition_type(preset.get_transition_type())
            self.editor_transitions_widget.set_step_seconds(preset.get_step_interval_seconds())
            df = preset.get_daylight_factor()
            self.editor_at_elevation_widget.df_widget.setEnabled(df is not None)
            self.editor_at_elevation_widget.df_widget.df_input.setText(f"{df:.4f}" if df is not None else '')

    def has_changes(self, preset: Preset) -> bool:
        preset_ini_copy = preset.preset_ini.duplicate()
        self.populate_ini_from_gui(preset_ini_copy)  # get ini options from GUI checkbox and field values
        self.main_controller.populate_ini_from_vdus(preset_ini_copy, update_only=True)  # get current VDU values for ini options
        log.debug(f"has_changes {preset.preset_ini.diff(preset_ini_copy)=}") if log.debug_enabled else None
        return len(preset.preset_ini.diff(preset_ini_copy)) > 0

    def populate_ini_from_gui(self, preset_ini: ConfIni) -> None:  # initialise ini options based on GUI checkbox and field values
        for key, checkbox in self.content_controls_map.items():  # Populate ini options to indicate which settings need to be saved
            section, option = key
            if checkbox.isChecked():  # If this property is enabled, set its value
                if not preset_ini.has_section(section):
                    preset_ini.add_section(section)
                value = self.base_ini.get(section, option, fallback="%should not happen%")
                preset_ini.set(section, option, value)  # Just an initial value, it will be updated with the current VDU value later
            elif preset_ini.has_section(section) and preset_ini.has_option(section, option):
                preset_ini.remove_option(section, option)
        if not preset_ini.has_section('preset'):
            preset_ini.add_section('preset')
        if self.edit_choose_icon_button.last_selected_icon_path:
            preset_ini.set("preset", "icon", self.edit_choose_icon_button.last_selected_icon_path.as_posix())
        preset_ini.set('preset', 'at-time', self.editor_at_time_widget.text())
        preset_ini.set('preset', 'solar-elevation', format_solar_elevation_ini_text(self.editor_at_elevation_widget.elevation_key))
        if weather_filename := self.editor_at_elevation_widget.get_required_weather_filename():
            preset_ini.set('preset', 'solar-elevation-weather-restriction', weather_filename)
        elif preset_ini.get('preset', 'solar-elevation-weather-restriction', fallback=None):
            preset_ini.remove_option('preset', 'solar-elevation-weather-restriction')  # Remove existing restriction from ini
        preset_ini.set('preset', 'transition-type', str(self.editor_transitions_widget.get_transition_type()))
        preset_ini.set('preset', 'transition-step-interval-seconds', str(self.editor_transitions_widget.get_step_seconds()))
        preset_ini.set('preset', 'daylight-factor', str(self.editor_at_elevation_widget.df_widget.df_input.text()))

    def get_preset_widgets(self) -> List[PresetItemWidget]:
        return [self.preset_widgets_layout.itemAt(i).widget()
                for i in range(0, self.preset_widgets_layout.count() - 1)
                if isinstance(self.preset_widgets_layout.itemAt(i).widget(), PresetItemWidget)]

    def get_preset_names_in_order(self) -> List[str]:
        return [w.name for w in self.get_preset_widgets()]

    def add_preset_widget(self, preset_widget: PresetItemWidget) -> None:
        # Insert before trailing stretch item
        self.preset_widgets_layout.insertWidget(self.preset_widgets_layout.count() - 1, preset_widget)

    def up_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index > 0:
            self.preset_widgets_layout.removeWidget(target_widget)
            self.preset_widgets_layout.insertWidget(index - 1, self.create_preset_widget(preset))
            target_widget.deleteLater()
            self.main_controller.save_preset_order(self.get_preset_names_in_order())
            self.preset_widgets_scroll_area.updateGeometry()

    def down_action(self, preset: Preset, target_widget: QWidget) -> None:
        index = self.preset_widgets_layout.indexOf(target_widget)
        if index < self.preset_widgets_layout.count() - 2:
            self.preset_widgets_layout.removeWidget(target_widget)
            self.preset_widgets_layout.insertWidget(index + 1, self.create_preset_widget(preset))
            target_widget.deleteLater()
            self.main_controller.save_preset_order(self.get_preset_names_in_order())
            self.preset_widgets_scroll_area.updateGeometry()

    def restore_preset(self, preset: Preset, immediately: bool = True) -> None:
        self.main_controller.restore_preset(preset, immediately=immediately)

    def delete_preset(self, preset: Preset, target_widget: QWidget) -> None:
        if MBox(MIcon.Question, msg=tr('Delete {}?').format(preset.name),
                buttons=MBtn.Ok | MBtn.Cancel, default=MBtn.Cancel).exec() == MBtn.Cancel:
            return
        self.main_controller.delete_preset(preset)
        self.preset_widgets_layout.removeWidget(target_widget)
        target_widget.deleteLater()
        self.main_controller.save_preset_order(self.get_preset_names_in_order())
        self.preset_name_edit.setText('')
        self.preset_widgets_scroll_area.updateGeometry()
        self.status_message(tr("Deleted {}").format(preset.name), timeout=-1)

    def change_edit_group_title(self) -> None:
        changed_text = self.preset_name_edit.text()
        if disable_controls := changed_text.strip() == "":
            self.edit_revert_button.setDisabled(True)
            self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include:"))
        else:
            if self.find_preset_widget(changed_text):  # Already exists
                self.edit_revert_button.setDisabled(False)
                self.editor_title.setText(tr("Edit {}:").format(changed_text))
            else:
                self.edit_revert_button.setDisabled(True)
                self.editor_title.setText(tr("Create new preset:"))
            self.editor_controls_prompt.setText(tr("Controls to include in {}:").format(changed_text))
        self.editor_controls_widget.setDisabled(disable_controls)
        self.editor_transitions_widget.setDisabled(disable_controls)
        self.editor_at_time_widget.setDisabled(disable_controls)
        self.editor_at_elevation_widget.setDisabled(disable_controls)
        self.controls_title_widget.setDisabled(disable_controls)
        self.editor_transitions_widget.setDisabled(disable_controls)
        self.edit_save_button.setDisabled(disable_controls)
        self.edit_clear_button.setDisabled(disable_controls)

    def edit_preset(self, preset: Preset) -> None:

        def _begin_editing(worker: BulkChangeWorker | None = None) -> None:
            if worker is None or worker.completed:
                self.set_widget_values_from_preset(preset)
            else:
                self.status_message(tr(f"Failed to restore {preset.name} for editing."))
            self.setEnabled(True)

        if preset:
            self.setDisabled(True)  # Stop any editing until after the preset is restored.
            self.main_controller.restore_preset(preset, finished_func=_begin_editing, immediately=True)

    def save_preset(self, _: bool = False, from_widget: PresetItemWidget | None = None,
                    quiet: bool = False) -> MBtn:
        preset: Preset | None = None
        widget_to_replace: PresetItemWidget | None = None
        if from_widget:  # A from_widget is requesting that the Preset's VDU current settings be updated.
            widget_to_replace = None  # Updating from widget, no change to icons or symbols, so no need to update the widget.
            preset = from_widget.preset  # Just update the widget's preset from the VDUs current settings
        elif preset_name := self.preset_name_edit.text().strip().replace('_',
                                                                         ' '):  # Saving from the save button, this may be new Preset or update.
            if widget_to_replace := self.find_preset_widget(preset_name):  # Already exists, update preset, replace widget
                preset = widget_to_replace.preset  # Use the widget's existing Preset.
            else:
                preset = Preset(preset_name)  # New Preset
        if preset is None or (quiet and not self.has_changes(preset)):  # Not found (weird), OR don't care if no changes made.
            return MBtn.Ok  # Nothing more to do, everything is OK

        preset_path = ConfIni.get_path(proper_name('Preset', preset.name))
        if preset_path.exists():  # Existing Preset
            if from_widget:  # The from_widget PresetWidget is initiating an update to the Preset from the VDUs settings.
                question = tr('Update existing {} preset with current monitor settings?').format(preset.name)
            else:  # The Preset Editor tab is modifying a Preset and it's PresetWidget.
                question = tr("Replace existing '{}' preset?").format(preset.name)
        else:  # New Preset
            question = tr("Save current edit?")
        answer = MBox(MIcon.Question, msg=question, buttons=MBtn.Save | MBtn.Discard | MBtn.Cancel, default=MBtn.Save).exec()
        if answer == MBtn.Discard:
            self.reset_editor()
            return MBtn.Ok
        elif answer == MBtn.Cancel:
            return MBtn.Cancel

        self.populate_ini_from_gui(preset.preset_ini)  # Initialises the options from the GUI, but does not get the VDU values.
        self.main_controller.populate_ini_from_vdus(preset.preset_ini, update_only=True)  # populate from VDU control values.

        if duplicated_presets := [other_preset for other_name, other_preset in self.main_controller.find_presets_map().items()
                                  if other_name != preset.name
                                     and preset.preset_ini.diff(other_preset.preset_ini, vdu_settings_only=True) == {}]:
            if MBox(MIcon.Warning, msg=tr("Duplicates existing Preset {}, save anyway?").format(duplicated_presets[0].name),
                    buttons=MBtn.Save | MBtn.Cancel, default=MBtn.Cancel).exec() == MBtn.Cancel:
                return MBtn.Cancel

        self.main_controller.save_preset(preset)

        if not from_widget:  # Which means the editor needs to update/create the PresetWidget, its icon, transition, weather, etc
            replacement_widget = self.create_preset_widget(preset)  # Create a new widget - an easy way to update the icon.
            if widget_to_replace:  # Existing widget need to update
                self.preset_widgets_layout.replaceWidget(widget_to_replace, replacement_widget)
                # The deleteLater removes the widget from the tree so that it is no longer findable and can be freed.
                widget_to_replace.deleteLater()
                self.make_visible()
            else:  # Must be a new Preset - create a new widget
                self.add_preset_widget(replacement_widget)
                self.main_controller.save_preset_order(self.get_preset_names_in_order())
                self.preset_widgets_scroll_area.ensureWidgetVisible(replacement_widget)
                QApplication.processEvents()  # TODO figure out why this does not work

        self.reset_editor()
        self.status_message(tr("Saved {}").format(preset.name), timeout=-1)
        return MBtn.Save

    def create_preset_widget(self, preset) -> PresetItemWidget:
        return PresetItemWidget(preset, restore_action=self.restore_preset, save_action=self.save_preset,
                                delete_action=self.delete_preset, edit_action=self.edit_preset,
                                up_action=self.up_action, down_action=self.down_action,
                                protect_nvram=self.main_config.is_set(ConfOpt.PROTECT_NVRAM_ENABLED))

    def event(self, event: QEvent | None) -> bool:
        # PalletChange happens after the new style sheet is in use.
        if event and event.type() == QEvent.Type.PaletteChange:
            self.repaint()
            self.vdu_init_button.refresh_icon()
        return super().event(event)

    def closeEvent(self, event) -> None:
        if self.save_preset(quiet=True) == MBtn.Cancel:
            event.ignore()
        else:
            self.reset_editor()
            super().closeEvent(event)
