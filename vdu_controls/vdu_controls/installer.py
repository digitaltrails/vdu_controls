# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
import stat
import sys
import textwrap
from pathlib import Path

from vdu_controls.constants import APPNAME
from vdu_controls.logging import *
from vdu_controls.icon_utils import get_splash_image


def install_as_desktop_application(uninstall: bool = False) -> None:
    """Self install this script in the current Linux user's bin directory and desktop applications->settings menu."""
    desktop_dir = Path.home().joinpath('.local', 'share', 'applications')
    icon_dir = Path.home().joinpath('.local', 'share', 'icons')

    if not desktop_dir.exists():
        log_error(f"No desktop directory is present:{desktop_dir.as_posix()}"
                  " Cannot proceed - is this a non-standard desktop?")
        return

    bin_dir = Path.home().joinpath('bin')
    if not bin_dir.is_dir():
        log_warning(f"creating:{bin_dir.as_posix()}")
        os.mkdir(bin_dir)

    if not icon_dir.is_dir():
        log_warning("creating:{icon_dir.as_posix()}")
        os.mkdir(icon_dir)

    installed_script_path = bin_dir.joinpath("vdu_controls")
    desktop_definition_path = desktop_dir.joinpath("vdu_controls.desktop")
    icon_path = icon_dir.joinpath("vdu_controls.png")

    if uninstall:
        os.remove(installed_script_path)
        log_info(f"Removed {installed_script_path.as_posix()}")
        os.remove(desktop_definition_path)
        log_info(f"Removed {desktop_definition_path.as_posix()}")
        os.remove(icon_path)
        log_info(f"Removed {icon_path.as_posix()}")
        return

    if installed_script_path.exists():
        log_warning(f"reinstalling {installed_script_path.as_posix()}, assuming an upgrade is required.")

    source = open(__file__).read()
    source = source.replace("#!/usr/bin/python3", '#!' + sys.executable)
    log_info(f"Creating {installed_script_path.as_posix()}")
    open(installed_script_path, 'w').write(source)
    log_info(f"chmod u+rwx {installed_script_path.as_posix()}")
    os.chmod(installed_script_path, stat.S_IRWXU)

    if desktop_definition_path.exists():
        log_warning(f"Skipping installation of {desktop_definition_path.as_posix()}, it is already present.")
    else:
        log_info(f"Creating {desktop_definition_path.as_posix()}")
        desktop_definition = textwrap.dedent(f"""
            [Desktop Entry]
            Type=Application
            Exec={installed_script_path.as_posix()}
            Name={APPNAME}
            GenericName=DDC control panel for monitors
            Comment=Virtual Control Panel for externally connected VDUs
            Icon={icon_path.as_posix()}
            Categories=Qt;Settings;
            """)
        open(desktop_definition_path, 'w').write(desktop_definition)

    if icon_path.exists():
        log_warning(f"skipping installation of {icon_path.as_posix()}, it is already present.")
    else:
        log_info(f"Creating {icon_path.as_posix()}")
        get_splash_image().save(icon_path.as_posix())

    log_info(f"Installation complete. Your desktop->applications->settings should now contain {APPNAME}")
