# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import locale
import os
from functools import partial
from pathlib import Path
from typing import List, Callable, Dict, Tuple, Mapping
from urllib.error import URLError

from vdu_controls.qt_imports import QSize, pyqtSignal, Qt, QRegularExpression, QDir
from vdu_controls.qt_imports import QValidator, QPalette, QRegularExpressionValidator
from vdu_controls.qt_imports import QVBoxLayout, QTabWidget, QStatusBar, QFrame, QHBoxLayout, QLabel, QWidget, QScrollArea, QGridLayout, \
    QApplication, QCheckBox, QLineEdit, QDoubleSpinBox, QPlainTextEdit, QSizePolicy

from vdu_controls.vdu_controls_config import VduControlsConfig, ConfOpt, ConfType, ConfSec, ConfOptDef
from vdu_controls.config_ini import ConfIni
from vdu_controls.constants import IP_ADDRESS_INFO_URL, CONFIG_FILE_PREFER_QT5
from vdu_controls.icon_utils import si, StdPixmap
from vdu_controls.app_locale import tr
import vdu_controls.logging as log
from vdu_controls.scaling import npx, native_font_height
from vdu_controls.widgets import SubWinDialog, StdButton, MBox, MIcon, MBtn, FasterFileDialog, alter_margins, DialogSingletonMixin


def flag_qt_version_preference(config: ConfIni) -> None:  # use a flag file to work around the chicken-and-egg issue at startup.
    if config.has_section(ConfOpt.PREFER_QT6.conf_section) and config.getboolean(ConfOpt.PREFER_QT6.conf_section,
                                                                                 ConfOpt.PREFER_QT6.conf_name, fallback=True):
        if CONFIG_FILE_PREFER_QT5.exists():
            CONFIG_FILE_PREFER_QT5.unlink()
    else:
        CONFIG_FILE_PREFER_QT5.touch()


class SettingsDialog(SubWinDialog, DialogSingletonMixin):
    """
    Application Settings Editor, edits a default global settings file, and a settings file for each VDU.
    The files are in INI format.  Internally, the settings are VduControlsConfig wrappers around the standard class ConfigIni.
    """

    @staticmethod
    def show_dialog(default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig], change_callback: Callable) -> None:
        SettingsDialog.show_existing_dialog() if SettingsDialog.exists() else SettingsDialog(default_config,
                                                                                             vdu_config_list, change_callback)

    @staticmethod
    def reconfigure_instance(vdu_config_list: List[VduControlsConfig]) -> None:
        if SettingsDialog.exists():
            SettingsDialog.get_instance().reconfigure(vdu_config_list)

    @staticmethod
    def edit_config(config_name: str) -> None:
        if SettingsDialog.exists():
            editor = SettingsDialog.get_instance()
            for tab_number, tab in enumerate(editor.editor_tab_list):
                if tab.config_path == ConfIni.get_path(config_name):
                    editor.tabs_widget.setCurrentIndex(tab_number)
                    editor.make_visible()

    def __init__(self, default_config: VduControlsConfig, vdu_config_list: List[VduControlsConfig], change_callback) -> None:
        super().__init__()
        self.setWindowTitle(tr('Settings'))
        self.setLayout(widget_layout := QVBoxLayout())
        self.tabs_widget = QTabWidget(self)
        widget_layout.addWidget(self.tabs_widget)
        self.editor_tab_list: List[SettingsEditorTab] = []
        self.bottom_status_bar = QStatusBar()
        self.tab_ops = QFrame(self)  # Groups operations that target the current tab
        self.tab_ops.setLayout(tab_ops_layout := QHBoxLayout())
        self.tab_ops_label = QLabel('')
        tab_ops_layout.addWidget(self.tab_ops_label)
        self.change_callback = change_callback

        def _tab_restore_defaults() -> None:
            self.tabs_widget.currentWidget().restore_application_defaults()

        self.tab_restore_defaults_button = StdButton(icon=si(self, StdPixmap.SP_DialogDiscardButton), title=(tr('Defaults')),
                                                     clicked=_tab_restore_defaults)
        tab_ops_layout.addWidget(self.tab_restore_defaults_button)

        def _tab_revert_current_tab() -> None:
            self.tabs_widget.currentWidget().revert_changes()

        self.tab_revert_button = StdButton(icon=si(self, StdPixmap.SP_DialogResetButton), title=(tr('Revert')),
                                           clicked=_tab_revert_current_tab)
        tab_ops_layout.addWidget(self.tab_revert_button)

        def _tab_save_current_tab() -> None:
            self.tabs_widget.currentWidget().save()

        self.tab_save_button = StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), title=(tr('Save')), clicked=_tab_save_current_tab)
        tab_ops_layout.addWidget(self.tab_save_button)

        self.bottom_status_bar.addPermanentWidget(self.tab_ops, 0)
        self.bottom_status_bar.addPermanentWidget(QLabel('                    '))

        save_all_button = StdButton(icon=si(self, StdPixmap.SP_DriveFDIcon), title=(tr("Save All")),
                                    clicked=(partial(self.save_all, True)))
        self.bottom_status_bar.addPermanentWidget(save_all_button, 0)

        quit_button = StdButton(icon=si(self, StdPixmap.SP_DialogCloseButton), title=(tr("Close")), clicked=self.close)
        self.bottom_status_bar.addPermanentWidget(quit_button, 0)

        widget_layout.addWidget(self.bottom_status_bar)

        def _tab_changed(index: int) -> None:
            self.update_tab_ops(self.tabs_widget.widget(index))

        self.tabs_widget.currentChanged.connect(_tab_changed)

        self.resize(npx(1600), npx(1000))
        self.setMinimumSize(npx(1024), npx(800))
        self.reconfigure([default_config, *vdu_config_list])
        self.make_visible()

    def status_message(self, message: str, msecs: int = 0):  # Display a message on the visible tab.
        self.bottom_status_bar.showMessage(message, msecs)

    def sizeHint(self):
        return QSize(npx(1700), npx(1000))

    def update_tab_ops(self, tab: SettingsEditorTab) -> None:
        self.tab_ops_label.setText(tr('{}: ').format(tab.preferred_name))
        self.tab_ops.setToolTip(tr('{0}: {1}').format(tab.preferred_name, tab.config_path.as_posix()))
        self.tab_save_button.setToolTip(tr('Save {0} to \n{1}').format(tab.preferred_name, tab.config_path.as_posix()))
        self.tab_revert_button.setToolTip(tr('Revert {0} from \n{1}').format(tab.preferred_name, tab.config_path.as_posix()))
        self.tab_restore_defaults_button.setToolTip(
            tr('Remove {0}\nand restore {1} to application defaults').format(tab.config_path.as_posix(), tab.preferred_name))

    def reconfigure(self, config_list: List[VduControlsConfig]) -> None:
        for config in config_list:
            vdu_label = config.get_vdu_preferred_name()
            conf_key = ConfIni.get_path(config.config_name)
            if tabs_found := [tab for tab in self.editor_tab_list if tab.config_path == conf_key]:
                assert len(tabs_found) == 1
                tab = tabs_found[0]
            else:
                tab = SettingsEditorTab(self, config, self.change_callback, parent=self.tabs_widget)
                tab.save_all_clicked_qtsignal.connect(self.save_all)  # type: ignore
                self.tabs_widget.addTab(tab, vdu_label)
                self.editor_tab_list.append(tab)
            tab.set_preferred_name(vdu_label)
            self.tabs_widget.setTabText(self.tabs_widget.indexOf(tab), vdu_label)
            if tab == self.tabs_widget.currentWidget():
                self.update_tab_ops(tab)
            if config.file_path:
                self.tabs_widget.setTabToolTip(self.tabs_widget.indexOf(tab), config.file_path.as_posix())

    def cross_validate(self) -> int:
        labels_in_use = {'vdu_controls': 'vdu_controls globals'}
        for tab in self.editor_tab_list:
            if vdu_label := tab.ini_editable.get(*ConfOpt.VDU_NAME.conf_id, fallback=None):
                if existing_use := labels_in_use.get(vdu_label, None):
                    return MBox(MIcon.Critical, msg=tr("Cannot save <tt>{}</tt>").format(tab.config_path.name),
                                info=tr("Duplicate VDU label: <i>{}</i><hr/>Alter the label for {0} or {1} and try again.").format(
                                    vdu_label, tab.config_path.stem, existing_use),
                                buttons=MBtn.Close | MBtn.Discard, default=MBtn.Close).exec()
                else:
                    labels_in_use[vdu_label] = tab.config_path.stem
        return MBtn.Ok

    def save_all(self, warn_if_nothing_to_save: bool = True) -> int:
        what_changed: Dict[str, str] = {}
        try:
            nothing_to_save = True
            self.setEnabled(False)
            save_order = self.editor_tab_list[1:] + [self.editor_tab_list[0]]  # Main config last, it may cause a restart of the app
            for editor in save_order:
                if editor.is_unsaved():
                    nothing_to_save = False
                    if editor.save(what_changed=what_changed, warn_if_no_changes=False) == MBtn.Cancel:
                        return MBtn.Cancel
            if warn_if_nothing_to_save and nothing_to_save:
                if MBox(MIcon.Critical, msg=tr("Nothing needs saving. Do you wish to save anyway?"),
                        buttons=MBtn.Yes | MBtn.No, default=MBtn.No).exec() == MBtn.Yes:
                    for editor in save_order:
                        if editor.save(force=True, what_changed=what_changed, warn_if_no_changes=False) == MBtn.Cancel:
                            return MBtn.Cancel
        finally:
            self.setEnabled(True)
            if len(what_changed) > 0:
                self.change_callback(what_changed)
        return MBtn.Ok

    def closeEvent(self, event) -> None:
        if self.save_all(warn_if_nothing_to_save=False) == MBtn.Cancel:
            event.ignore()
        else:
            super().closeEvent(event)


class SettingsEditorTab(QWidget):
    """A tab corresponding to a settings file, generates UI widgets for each tab based on what's in the config. """
    save_all_clicked_qtsignal = pyqtSignal()

    def __init__(self, editor_dialog: SettingsDialog, vdu_config: VduControlsConfig, change_callback: Callable,
                 parent: QTabWidget) -> None:
        super().__init__(parent=parent)
        widget_map = {ConfType.BOOL: SettingsEditorBooleanWidget, ConfType.FLOAT: SettingsEditorFloatWidget,
                      ConfType.LONG_TEXT: SettingsEditorLongTextWidget, ConfType.TEXT: SettingsEditorTextWidget,
                      ConfType.CSV: SettingsEditorCsvWidget, ConfType.LOCATION: SettingsEditorLocationWidget,
                      ConfType.PATH: SettingsEditorPathWidget, }
        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)
        self.setLayout(widget_layout := QVBoxLayout())
        widget_layout.addWidget(scroll_area)

        self.change_callback = change_callback
        self.unsaved_changes_map: Dict[Tuple[str, str], str] = {}
        self.config_path = ConfIni.get_path(vdu_config.config_name)
        self.ini_before = vdu_config.ini_content
        self.ini_editable = self.ini_before.duplicate()
        self.field_list: List[SettingsEditorFieldBase] = []
        self.editor_dialog = editor_dialog
        self.preferred_name = vdu_config.get_vdu_preferred_name()

        def _field(widget: SettingsEditorFieldBase) -> QWidget:
            self.field_list.append(widget)
            return widget

        for section_def in [ConfSec(section_name) for section_name in self.ini_editable.data_sections()]:

            ordered_by_sub_group: dict[tuple[str, int], tuple[str, ConfOpt]] = {}
            for num, option_name in enumerate(self.ini_editable[section_def]):
                try:
                    option_def = vdu_config.get_conf_option(section_def, option_name)
                    if option_def == ConfOpt.UNKNOWN:  # If it's unknown, it's a boolean switch for a VCP code
                        # Make up a temporary ConfOptDef (which is not an enum value of ConfOpt(Enum))
                        option_def = ConfOptDef(option_name, section_def, ConfType.BOOL, ui_label=option_name.replace('-',' '))
                    ordered_by_sub_group[(option_def.sub_group.value, num)] = (option_name, option_def)
                except ValueError:  # Probably an old no-longer-valid option, or a typo.
                    log.warning(f"Ignoring invalid option name {option_name} in {section_def}")
            ordered_by_sub_group = dict(sorted(ordered_by_sub_group.items()))
            section_title = section_def.localized_name
            content_layout.addWidget(QLabel(f"<b>{section_title}</b>"))
            booleans_grid: QGridLayout | None = None  # Only create when bool_count > 0
            grid_columns = 5  # booleans are counted and laid out according to grid_columns.
            previous_sub_group = None
            row_index = col_index = 0
            for option_name, option_def in ordered_by_sub_group.values():
                try:
                    if option_def.conf_type == ConfType.BOOL:
                        if row_index == 0 and col_index == 0:  # Need to create a grid now
                            booleans_grid = QGridLayout()
                            booleans_grid.setVerticalSpacing(0)
                            booleans_panel = QWidget()
                            booleans_panel.setLayout(booleans_grid)
                            content_layout.addWidget(booleans_panel)
                        if option_def.sub_group and option_def.sub_group != previous_sub_group:
                            if row_index > 0:
                                row_index += 1
                                booleans_grid.setRowMinimumHeight(row_index, npx(20))
                                row_index += 1
                            booleans_grid.addWidget(QLabel(option_def.sub_group.localized_name), row_index, 0)
                            row_index += 1
                            col_index = 0
                            previous_sub_group = option_def.sub_group
                        booleans_grid.addWidget(
                            _field(SettingsEditorBooleanWidget(self, option_def)), row_index, col_index)
                        col_index += 1
                        if col_index == grid_columns:
                            col_index = 0
                            row_index += 1
                    else:
                        content_layout.addWidget(_field(widget_map[option_def.conf_type](self, option_def)))
                except ValueError:  # Probably an old no-longer-valid option, or a typo.
                    log.warning(f"Ignoring invalid option name {option_name} in {section_def}")

    def set_preferred_name(self, label_str):
        self.preferred_name = label_str

    def save(self, force: bool = False, what_changed: Dict[str, str] | None = None, warn_if_no_changes: bool = True) -> int:
        # what_changed is an output parameter, if passed, it will be updated with what has changed.
        if self.is_unsaved() or force:
            try:
                self.setEnabled(False)  # Saving may take a while, give some feedback by disabling and enabling when done
                log.debug(f"{SettingsDialog.exists()=}")
                answer = SettingsDialog.get_instance().cross_validate()
                if answer == MBtn.Ok:
                    msg = (tr('Update existing {}?') if self.config_path.exists() else tr("Create new {}?")).format(
                        self.config_path.as_posix())
                    answer = MBox(MIcon.Question, msg=msg, buttons=MBtn.Save | MBtn.Cancel | MBtn.Discard, default=MBtn.Save).exec()
                if answer == MBtn.Save:
                    message = tr("Saving {} ...").format(self.config_path.name)
                    self.editor_dialog.status_message(message, 0)
                    QApplication.processEvents()
                    self.ini_editable.save(self.config_path)
                    flag_qt_version_preference(self.ini_editable)
                    self.ini_before = self.ini_editable.duplicate()  # Saved ini becomes the new "before"
                    if what_changed is None:  # Not accumulating what has changed, implement change now.
                        self.change_callback(self.unsaved_changes_map)
                    else:  # Accumulating what has changed, just add to the dictionary.
                        what_changed.update(self.unsaved_changes_map)
                    self.unsaved_changes_map = {}
                    message1 = tr("Saved {}").format(self.config_path.name)
                    self.editor_dialog.status_message(message1, 3000)
                elif answer == MBtn.Discard:
                    self.revert_changes()
                return answer
            finally:
                self.setEnabled(True)
        elif warn_if_no_changes:
            MBox(MIcon.Critical, msg=tr('No unsaved changes for {}.').format(self.config_path.name), buttons=MBtn.Ok).exec()
        return MBtn.Cancel

    def reset(self) -> None:
        for field in self.field_list:
            field.reset()

    def revert_changes(self) -> None:
        if self.is_unsaved():
            self.editor_dialog.status_message(tr("Discarded changes to {}").format(self.config_path.name), 3000)
            self.ini_editable = self.ini_before.duplicate()  # Revert
        else:
            self.editor_dialog.status_message(tr("Nothing to discard").format(self.config_path.name), 3000)
        self.reset()

    def restore_application_defaults(self):
        if MBox(MIcon.Critical,
                msg=tr("Are you sure you want to restore {} to application defaults?").format(self.preferred_name),
                info=tr("The file {0} will be renamed to {1}.old").format(self.config_path.name, self.config_path.stem),
                buttons=MBtn.Yes | MBtn.No, default=MBtn.No).exec() == MBtn.No:
            return
        if self.config_path.exists():
            self.config_path.rename(Path(self.config_path.parent, self.config_path.stem + 'old'))
        self.change_callback(None)

    def is_unsaved(self) -> bool:
        if self.config_path.exists():
            self.unsaved_changes_map = self.ini_editable.diff(self.ini_before)
            return len(self.unsaved_changes_map) > 0
        self.unsaved_changes_map = {}
        return True


class SettingsEditorFieldBase(QWidget):
    def __init__(self, section_editor: SettingsEditorTab, option_def: ConfOpt) -> None:
        super().__init__()
        self.section_editor = section_editor
        self.conf_section = option_def.conf_section
        self.conf_name = option_def.conf_name
        self.has_error = False
        self.ui_label_text = option_def.localized_name
        if option_def.help:
            self.setToolTip(option_def.localized_help)


class SettingsEditorBooleanWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option_def: ConfOpt) -> None:
        super().__init__(section_editor, option_def)
        self.setLayout(widget_layout := QHBoxLayout())
        alter_margins(widget_layout, top=0, bottom=0)  # Squish up, save space, stay closer to parent label
        checkbox = QCheckBox(self.ui_label_text)
        checkbox.setChecked(section_editor.ini_editable.getboolean(self.conf_section, self.conf_name))

        def _toggled(is_checked: bool) -> None:
            section_editor.ini_editable[self.conf_section][self.conf_name] = 'yes' if is_checked else 'no'
            if option_def.related:
                MBox(MIcon.Information, msg=tr("You may also wish to set\n{}").format(tr(option_def.related)), buttons=MBtn.Ok).exec()
            if is_checked and option_def.requires:
                MBox(MIcon.Information, msg=tr("You will also need to set\n{}").format(tr(option_def.requires)), buttons=MBtn.Ok).exec()
            if is_checked and option_def.warning:
                MBox(MIcon.Warning, msg=option_def.localized_warning, buttons=MBtn.Ok).exec()
            if not is_checked and option_def.off_warning:
                MBox(MIcon.Warning, msg=option_def.localized_off_warning, buttons=MBtn.Ok).exec()

        checkbox.toggled.connect(_toggled)
        widget_layout.addWidget(checkbox)
        self.checkbox = checkbox

    def reset(self) -> None:
        self.checkbox.setChecked(self.section_editor.ini_before.getboolean(self.conf_section, self.conf_name))


class SettingsEditorLineBase(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option_def: ConfOpt) -> None:
        super().__init__(section_editor, option_def)
        self.editor_layout = QHBoxLayout()
        self.editor_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setLayout(self.editor_layout)
        self.text_label = QLabel(self.ui_label_text)
        self.editor_layout.addWidget(self.text_label)
        self.text_input = QLineEdit()
        self.validator: QValidator | None = None
        self.valid_palette = self.text_input.palette()
        self.error_palette = self.text_input.palette()
        self.error_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.red)
        self.error_palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.red)
        self.text_input.inputRejected.connect(partial(self.set_error_indication, True))
        self.text_input.textEdited.connect(partial(self.set_error_indication, False))
        self.text_input.editingFinished.connect(self.editing_finished)
        self.editor_layout.addWidget(self.text_input, stretch=4)

    def editing_finished(self) -> None:
        text = self.text_input.text()
        if self.validator is not None:
            self.has_error = self.validator.validate(text, 0)[0] != QValidator.State.Acceptable
            self.set_error_indication(self.has_error)
        if not self.has_error:
            internal_value = str(text)  # Why did I do this - is text not really a string?
            if not self.has_error:
                self.section_editor.ini_editable[self.conf_section][self.conf_name] = internal_value

    def set_error_indication(self, has_error: bool) -> None:
        self.has_error = has_error
        self.text_input.setPalette(self.error_palette if has_error else self.valid_palette)

    def reset(self) -> None:
        self.text_input.setText(self.section_editor.ini_before[self.conf_section][self.conf_name])
        self.editing_finished()


class SettingsEditorFloatWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option_def) -> None:
        super().__init__(section_editor, option_def)
        self.setLayout(widget_layout := QHBoxLayout())
        widget_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.text_label = QLabel(self.ui_label_text)
        widget_layout.addWidget(self.text_label)
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(0.0, 4.0)  # TODO this should be looked up in the metadata
        self.spinbox.setSingleStep(0.1)
        try:
            value = float(section_editor.ini_editable[self.conf_section][self.conf_name])
        except ValueError:  # Just in case - rather not fall over
            value = 0.0
        self.spinbox.setValue(value)
        widget_layout.addWidget(self.spinbox)

        def _spinbox_value_changed() -> None:
            section_editor.ini_editable[self.conf_section][self.conf_name] = locale.delocalize(f"{self.spinbox.value():.2f}")

        self.spinbox.valueChanged.connect(_spinbox_value_changed)

    def reset(self) -> None:
        self.spinbox.setValue(float(self.section_editor.ini_before.get(self.conf_section, self.conf_name)))


class SettingsEditorCsvWidget(SettingsEditorLineBase):
    def __init__(self, section_editor: SettingsEditorTab, option_def: ConfOpt) -> None:
        super().__init__(section_editor, option_def)
        # TODO - should probably also allow spaces as well as commas, but the regexp is getting a bit tricky?
        # Validator matches CSV of two digit hex or the empty string.
        self.validator = QRegularExpressionValidator(QRegularExpression(r"^([0-9a-fA-F]{2}([ \t]*,[ \t]*[0-9a-fA-F]{2})*)|$"))
        self.text_input.setText(section_editor.ini_editable[self.conf_section][self.conf_name])


class LatitudeLongitudeValidator(QRegularExpressionValidator):

    def __init__(self) -> None:
        super().__init__(QRegularExpression(r"^([+-]*[0-9.,]+[,;][+-]*[0-9.,]+)([,;]\w+)?|$",
                                            QRegularExpression.PatternOption.UseUnicodePropertiesOption))

    def validate(self, text: str | None, pos: int) -> Tuple[QValidator.State, str, int]:
        result = super().validate(text, pos)
        if result[0] == QValidator.State.Acceptable:
            if text:
                try:
                    lat, lon = [float(i) for i in text.split(',')[:2]]
                    if -90.0 <= lat <= 90.0:
                        if -180.0 <= lon <= 180.0:
                            return QValidator.State.Acceptable, text, pos
                    return QValidator.State.Invalid, text, pos
                except ValueError:
                    return QValidator.State.Intermediate, text, pos
        return result


class SettingsEditorLocationWidget(SettingsEditorLineBase):
    def __init__(self, section_editor: SettingsEditorTab, option_def: ConfOpt) -> None:
        super().__init__(section_editor, option_def)
        self.text_input.setFixedWidth(npx(500))
        self.text_input.setMaximumWidth(npx(500))
        self.text_input.setMaxLength(250)
        self.validator = LatitudeLongitudeValidator()
        self.text_input.setText(section_editor.ini_editable[self.conf_section][self.conf_name])

        def _detection_location() -> None:
            if data_csv := self.location_dialog():
                self.text_input.setText(data_csv)
                self.editing_finished()

        detect_location_button = StdButton(title=tr("Detect"), clicked=_detection_location,
                                           tip=tr("Detect location by querying this desktop's external IP address."))
        self.editor_layout.addWidget(detect_location_button)
        self.editor_layout.addStretch(1)

    def retrieve_ipinfo(self) -> Mapping:
        #  https://stackoverflow.com/a/55432323/609575
        from urllib.request import urlopen
        from json import load
        with urlopen(IP_ADDRESS_INFO_URL) as res:
            return load(res)

    def location_dialog(self) -> str | None:
        if MBox(MIcon.Question, msg=tr('Query {} to obtain information based on your IP-address?').format(IP_ADDRESS_INFO_URL),
                buttons=MBtn.Yes | MBtn.No).exec() == MBtn.Yes:
            try:
                ipinfo = self.retrieve_ipinfo()
                msg = f"{tr('Use the following info?')}\n" f"{ipinfo['loc']}\n" + \
                      ','.join([ipinfo[key] for key in ('city', 'region', 'country') if key in ipinfo])
                details = f"Queried {IP_ADDRESS_INFO_URL}\n" + \
                          '\n'.join([f"{name}: {value}" for name, value in ipinfo.items()])
                if MBox(MIcon.Information, msg=msg, details=details, buttons=MBtn.Yes | MBtn.No).exec() == MBtn.Yes:
                    data = ipinfo['loc']
                    for key in ('city', 'region', 'country'):  # Get location name for weather lookups.
                        if key in ipinfo:
                            data = data + ',' + ipinfo[key]
                            break
                    return data
            except (URLError, KeyError) as e:
                MBox(MIcon.Critical, msg=tr("Failed to obtain info from {0}: {1}").format(IP_ADDRESS_INFO_URL, e)).exec()
        return ''


class SettingsEditorLongTextWidget(SettingsEditorFieldBase):
    def __init__(self, section_editor: SettingsEditorTab, option_def: ConfOpt) -> None:
        super().__init__(section_editor, option_def)
        layout = QVBoxLayout()
        self.setLayout(layout)
        text_label = QLabel(self.ui_label_text)
        layout.addWidget(text_label)
        text_editor = QPlainTextEdit(section_editor.ini_editable[self.conf_section][self.conf_name])
        text_editor.setMinimumHeight(native_font_height(100))
        text_editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        def _text_changed() -> None:
            section_editor.ini_editable[self.conf_section][self.conf_name] = text_editor.toPlainText().strip()

        text_editor.textChanged.connect(_text_changed)
        layout.addWidget(text_editor, stretch=1)
        self.text_editor = text_editor

    def reset(self) -> None:
        self.text_editor.setPlainText(self.section_editor.ini_before[self.conf_section][self.conf_name])


class SettingsEditorTextWidget(SettingsEditorFieldBase):

    def __init__(self, section_editor: SettingsEditorTab, option_def: ConfOpt) -> None:
        super().__init__(section_editor, option_def)
        layout = QVBoxLayout()
        self.setLayout(layout)
        text_label = QLabel(self.ui_label_text)
        layout.addWidget(text_label)
        text_editor = QLineEdit(section_editor.ini_editable[self.conf_section][self.conf_name])

        def _text_changed() -> None:
            section_editor.ini_editable[self.conf_section][self.conf_name] = text_editor.text().strip()

        text_editor.textChanged.connect(_text_changed)
        layout.addWidget(text_editor)
        self.text_editor = text_editor

    def reset(self) -> None:
        self.text_editor.setText(self.section_editor.ini_before[self.conf_section][self.conf_name])


class SettingsEditorPathValidator(QValidator):

    def validate(self, text, pos):
        if text.strip():
            if not Path(text).exists() or not Path(text).is_file():
                MBox(MIcon.Critical, msg=tr("The selected file does not exist or is not an ordinary file.")).exec()
                return QValidator.State.Invalid, text, pos
            elif not os.access(text, os.X_OK):
                MBox(MIcon.Critical, msg=tr("The selected file lacks execute permission.")).exec()
                return QValidator.State.Invalid, text, pos
        return QValidator.State.Acceptable, text, pos


class SettingsEditorPathWidget(SettingsEditorLineBase):

    def __init__(self, section_editor: SettingsEditorTab, option_def: ConfOpt) -> None:
        super().__init__(section_editor, option_def)
        self.text_input.setText(section_editor.ini_editable[self.conf_section][self.conf_name])

        def _choose_emulator(index: int) -> None:
            current_path = self.text_input.text()
            new_path = FasterFileDialog.getOpenFileName(
                self, tr("Select: {}").format(tr(self.text_label.text())), current_path,
                qdir_filter=QDir.Filter.Files | QDir.Filter.Readable | QDir.Filter.Executable)[0]
            self.text_input.setText(new_path)
            self.editing_finished()

        self.editor_layout.addWidget(StdButton(si(self, StdPixmap.SP_DriveFDIcon), clicked=_choose_emulator))
        self.editor_layout.addStretch(1)
        self.validator = SettingsEditorPathValidator()

    def editing_finished(self) -> None:
        super().editing_finished()
        if not self.has_error and self.text_input.text().strip() != '':
            if self.section_editor.ini_editable[self.conf_section][self.conf_name] != self.section_editor.ini_before[self.conf_section][
                self.conf_name]:
                mb = MBox(MIcon.Information,
                          msg="If you've developed a <i>ddcutil-emulator</i> for integrating a non-DDC laptop-panels, "
                              "please consider contributing it to the <b>vdu_controls</b> project."
                              "<br/>_______________________________________________________________________________________</br>",
                          info="Submit feedback and contributions to<br/> "
                               "<a href='https://github.com/digitaltrails/vdu_controls/issues/44'>"
                               "https://github.com/digitaltrails/vdu_controls/issues/44</a><br/>"
                               "or by email to <a href='mailto:michael@actrix.gen.nz?subject=ddcutil-emulator'>"
                               "michael@actrix.gen.nz</a>.", buttons=MBtn.Close)
                mb.setTextFormat(Qt.TextFormat.AutoText)
                mb.exec()
