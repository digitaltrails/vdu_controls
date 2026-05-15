# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from enum import IntEnum, auto
from typing import List, Callable, TYPE_CHECKING, Tuple, Dict

from vdu_controls import logging as log
from vdu_controls.app_locale import tr
from vdu_controls.icon_utils import StdPixmap, si
from vdu_controls.preset import Preset
from vdu_controls.qt_imports import QVariant, Qt, QKeySequence, QIcon, QMenu, QWidget, QAction
from vdu_controls.unicode import MENU_ACTIVE_PRESET_SYMBOL

if TYPE_CHECKING:
    from vdu_controls.vdu_controls_application import VduAppController

PRESET_NAME_PROP = 'preset_name'
PRESET_SHORTCUT_PROP = 'preset_shortcut'
BUSY_DISABLE_PROP = 'busy_disable'
ALT = 'Alt+{}'

Shortcut = namedtuple('Shortcut', ['letter', 'annotated_word'])

class FixedItemKey(IntEnum):
    CONTROL_PANEL = auto()
    PRESETS = auto()
    GREY_SCALE = auto()
    LUX_AUTO_MANUAL = auto()
    LIGHTING_CHECK_NOW = auto()
    LIGHT_METERING_DIALOG = auto()
    SETTINGS_DIALOG = auto()
    REFRESH = auto()
    ABOUT_DIALOG = auto()
    HELP = auto()
    QUIT = auto()

@dataclass
class FixedItemData:
    pixmap_number: int
    title: str
    extra_shortcut: str | None = None
    add_separator: bool = False
    property: Tuple[str, QVariant] | None = None
    separator: QAction | None = None
    action: QAction | None = None

class ContextMenu(QMenu):

    def __init__(self, app_controller: VduAppController, fixed_item_callables: Dict[FixedItemKey, Callable],
                 hide_shortcuts: bool, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self.fixed_item_map: Dict[FixedItemKey, FixedItemData] = {
            FixedItemKey.CONTROL_PANEL: FixedItemData(StdPixmap.SP_ComputerIcon, tr('&Control Panel'), add_separator=True),
            FixedItemKey.PRESETS: FixedItemData(StdPixmap.SP_ComputerIcon, tr('&Presets'),
                                                add_separator=True, property=(BUSY_DISABLE_PROP, QVariant(True))),
            FixedItemKey.GREY_SCALE: FixedItemData(StdPixmap.SP_ComputerIcon, tr('&Grey Scale')),
            FixedItemKey.LUX_AUTO_MANUAL: FixedItemData(StdPixmap.SP_ComputerIcon, tr('&Auto/Manual')),
            FixedItemKey.LIGHTING_CHECK_NOW: FixedItemData(StdPixmap.SP_MediaSeekForward, tr('Lighting &Check')),
            FixedItemKey.LIGHT_METERING_DIALOG: FixedItemData(StdPixmap.SP_ComputerIcon, tr('&Light-Metering')),
            FixedItemKey.SETTINGS_DIALOG: FixedItemData(StdPixmap.SP_ComputerIcon, tr('&Settings'), 'Ctrl+Shift+,'),
            FixedItemKey.REFRESH: FixedItemData(StdPixmap.SP_BrowserReload, tr('&Refresh'), QKeySequence.StandardKey.Refresh),
            FixedItemKey.ABOUT_DIALOG: FixedItemData(StdPixmap.SP_MessageBoxInformation, tr('Abou&t')),
            FixedItemKey.HELP: FixedItemData(StdPixmap.SP_DialogHelpButton, tr('&Help'), QKeySequence.StandardKey.HelpContents),
            FixedItemKey.QUIT: FixedItemData(StdPixmap.SP_DialogCloseButton, tr('&Quit'), QKeySequence.StandardKey.Quit),
        }

        self.app_controller = app_controller
        self.reserved_shortcuts: List[str] = []
        self.hide_shortcuts = hide_shortcuts

        for key, item in self.fixed_item_map.items():
            if fixed_item_callables[key] is not None:
                item.action = self._add_action(item.pixmap_number, item.title, fixed_item_callables[key], extra_shortcut=item.extra_shortcut)
                if item.add_separator:
                    item.separator = self.addSeparator()
                if item.property:
                    item.action.setProperty(*item.property)

        self.reserved_shortcuts_basic = self.reserved_shortcuts.copy()
        self.auto_lux_icon: QIcon | None = None

    def _add_action(self, qt_icon_number: int, text: str, func: Callable, extra_shortcut: str | None = None) -> QAction:
        action = self.addAction(si(self, qt_icon_number), text, func)
        assert action is not None
        amp_pos = text.find('&')
        shortcut_letter = text[amp_pos + 1].upper() if (0 <= amp_pos < len(text) - 1) else None
        if shortcut_letter is not None:
            log.debug(f"Reserve shortcut '{shortcut_letter}'") if log.debug_enabled else None
            if shortcut_letter in self.reserved_shortcuts:
                log.error(f"{shortcut_letter=} already in in {self.reserved_shortcuts=}")
            else:
                self.reserved_shortcuts.append(shortcut_letter)
                action.setShortcuts(self.shortcut_list(ALT.format(shortcut_letter.upper()), extra_shortcut))
                action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        return action

    def get_preset_menu_action(self, name: str) -> QAction | None:
        for action in self.actions():
            if action.property(PRESET_NAME_PROP) == name:
                return action
        return None

    def insert_preset_menu_action(self, preset: Preset, issue_update: bool = True) -> None:

        def _menu_restore_preset() -> None:
            self.app_controller.restore_named_preset(self.sender().property(PRESET_NAME_PROP))

        assert preset.name
        shortcut = self.allocate_preset_shortcut(preset.name)
        action_name = shortcut.annotated_word if shortcut else preset.name
        action = self.addAction(preset.create_icon(), action_name, _menu_restore_preset)  # Have to add it, then move/insert it.
        assert action
        self.insertAction(self.fixed_item_map[FixedItemKey.PRESETS].separator, action)  # Insert before the presets_separator
        action.setProperty(BUSY_DISABLE_PROP, QVariant(True))
        action.setProperty(PRESET_NAME_PROP, preset.name)
        if shortcut:
            action.setProperty(PRESET_SHORTCUT_PROP, shortcut)
            action.setShortcuts(self.shortcut_list(ALT.format(shortcut.letter.upper())))
            action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        else:
            log.warning(f"Failed to allocate shortcut for {preset.name} reserved shortcuts={self.reserved_shortcuts}")
        self.update() if issue_update else None

    def remove_preset_menu_action(self, name: str) -> None:
        if menu_action := self.get_preset_menu_action(name):
            shortcut = menu_action.property(PRESET_SHORTCUT_PROP)
            if shortcut and shortcut in self.reserved_shortcuts:
                self.reserved_shortcuts.remove(shortcut.letter)
            self.removeAction(menu_action)
            self.update()

    def refresh_preset_menu(self, palette_change: bool = False, reorder: bool = False) -> None:
        changed = 0
        if reorder:  # Remove them all to get them reinserted, icons updated, names updated, etc.
            self.reserved_shortcuts = self.reserved_shortcuts_basic.copy()  # Reset shortcuts
            for action in self.actions():
                self.removeAction(action) if action.property(PRESET_NAME_PROP) is not None else None
        for name, preset in self.app_controller.preset_controller.find_presets_map().items():
            menu_action = self.get_preset_menu_action(name)
            if menu_action is None or not menu_action.property(PRESET_NAME_PROP):
                self.insert_preset_menu_action(preset, False)
                changed += 1
            elif palette_change:  # Must redraw icons in case desktop theme changed between light/dark.
                menu_action.setIcon(preset.create_icon())
                changed += 1
        self.update() if changed else None

    def indicate_preset_active(self, preset: Preset | None) -> None:
        changed = 0
        for action in self.actions():
            if action_preset_name := action.property(PRESET_NAME_PROP):  # Mark active preset or un-mark previous active
                shortcut = action.property(PRESET_SHORTCUT_PROP)
                suffix = (' ' + MENU_ACTIVE_PRESET_SYMBOL) if preset is not None and preset.name == action_preset_name else ''
                new_text = (shortcut.annotated_word if shortcut else action_preset_name) + suffix
                if new_text != action.text():
                    action.setText(new_text)
                    changed += 1
        self.update() if changed else None

    def indicate_busy(self, is_busy: bool = True) -> None:
        changed = 0
        for action in self.actions():
            if action.property(BUSY_DISABLE_PROP):
                if (is_busy and action.isEnabled()) or (not is_busy and not action.isEnabled()):
                    action.setDisabled(is_busy)
                    changed += 1
        self.update() if changed else None

    def update_lux_auto_icon(self, icon: QIcon) -> None:
        if self.auto_lux_icon != icon:
            self.auto_lux_icon = icon
            self.fixed_item_map[FixedItemKey.LUX_AUTO_MANUAL].action.setIcon(icon)
            self.update()

    def allocate_preset_shortcut(self, word: str) -> Shortcut | None:
        for letter in list(word):
            upper_letter = letter.upper()
            if upper_letter not in self.reserved_shortcuts:
                self.reserved_shortcuts.append(upper_letter)
                return Shortcut(letter=upper_letter, annotated_word=word[:word.index(letter)] + '&' + word[word.index(letter):])
        return None

    def shortcut_list(self, primary: str | QKeySequence, extra: str | QKeySequence | None = None) -> List[str | QKeySequence]:
        shortcuts = [primary] + ([extra] if extra else [])
        return ([''] + shortcuts) if self.hide_shortcuts else shortcuts  # Empty string causes shortcuts to be hidden.
