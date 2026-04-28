# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import shutil
import stat
import sys
import textwrap
from pathlib import Path

from vdu_controls.constants import APPNAME
import vdu_controls.logging as log
from vdu_controls.icon_utils import get_splash_pixmap


def install_as_desktop_application(uninstall: bool = False) -> None:
    """Self install this script in the current Linux user's bin directory and desktop applications->settings menu."""
    desktop_dir = Path.home().joinpath('.local', 'share', 'applications')
    icon_dir = Path.home().joinpath('.local', 'share', 'vdu_controls', 'icons')
    bin_dir = Path.home().joinpath('.local', 'bin')

    if not desktop_dir.exists():
        log.error(f"No desktop directory is present:{desktop_dir.as_posix()}"
                  " Cannot proceed - is this a non-standard desktop?")
        return

    if not bin_dir.is_dir():
        log.warning(f"creating:{bin_dir.as_posix()}")
        os.mkdir(bin_dir)

    if not icon_dir.is_dir():
        log.warning("creating:{icon_dir.as_posix()}")
        os.mkdir(icon_dir)

    installed_script_path = bin_dir.joinpath("vdu_controls")
    desktop_definition_path = desktop_dir.joinpath("vdu_controls.desktop")
    app_icon_path = icon_dir.joinpath("vdu_controls.png")

    if uninstall:
        os.remove(installed_script_path)
        log.info(f"Removed {installed_script_path.as_posix()}")
        os.remove(desktop_definition_path)
        log.info(f"Removed {desktop_definition_path.as_posix()}")
        os.remove(app_icon_path)
        log.info(f"Removed {app_icon_path.as_posix()}")
        return

    if installed_script_path.exists():
        log.warning(f"reinstalling {installed_script_path.as_posix()}, assuming an upgrade is required.")

    log.info(f"Copying {__file__} to  {installed_script_path.as_posix()}")
    shutil.copy2(__file__, installed_script_path)
    log.info(f"chmod u+rwx {installed_script_path.as_posix()}")
    os.chmod(installed_script_path, stat.S_IRWXU)

    if desktop_definition_path.exists():
        log.warning(f"Skipping installation of {desktop_definition_path.as_posix()}, it is already present.")
    else:
        log.info(f"Creating {desktop_definition_path.as_posix()}")
        desktop_definition = textwrap.dedent(f"""
            [Desktop Entry]
            Type=Application
            Exec={installed_script_path.as_posix()}
            Name={APPNAME}
            GenericName=DDC control panel for monitors
            Comment=Virtual Control Panel for externally connected VDUs
            Icon={app_icon_path.as_posix()}
            Categories=Qt;Settings;
            """)
        open(desktop_definition_path, 'w').write(desktop_definition)

    if app_icon_path.exists():
        log.warning(f"skipping installation of {app_icon_path.as_posix()}, it is already present.")
    else:
        log.info(f"Creating {app_icon_path.as_posix()}")
        get_splash_pixmap().save(app_icon_path.as_posix())



    log.info(f"Installation complete. Your desktop->applications->settings should now contain {APPNAME}")
