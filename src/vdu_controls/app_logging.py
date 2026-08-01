# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from datetime import datetime
import io
import syslog
import traceback

_LOG_SYSLOG_CAT = {syslog.LOG_INFO: "INFO:", syslog.LOG_ERR: "ERROR:", syslog.LOG_WARNING: "WARNING:", syslog.LOG_DEBUG: "DEBUG:"}


to_syslog = False
debug_enabled = False  # Often used to guard needless computation: log.debug(needless) if debug_enabled else None


def set_syslog(enable: bool) -> None:
    global to_syslog
    info("logging: logging to syslog is enabled")
    to_syslog = enable


def set_debug(enable: bool) -> None:
    global debug_enabled
    warning("logging: debug is enabled")
    debug_enabled = enable

def _log_wrapper(severity, *args, trace=False) -> None:
    with io.StringIO() as output:
        print(*args, file=output, end='')
        message = output.getvalue()
        prefix = _LOG_SYSLOG_CAT[severity]
        if to_syslog:
            syslog_message = prefix + " " + message if severity == syslog.LOG_DEBUG else message
            syslog.syslog(severity, syslog_message)
        else:
            print(datetime.now().strftime("%H:%M:%S"), prefix, message)
    if debug_enabled and trace:
        debug("TRACEBACK:", ''.join(traceback.format_stack()))


def debug(*args, trace=False) -> None:
    _log_wrapper(syslog.LOG_DEBUG, *args, trace=trace) if debug_enabled else None


def info(*args, trace=False) -> None:
    _log_wrapper(syslog.LOG_INFO, *args, trace=trace)


def warning(*args, trace=False) -> None:
    _log_wrapper(syslog.LOG_WARNING, *args, trace=trace)


def error(*args, trace=False) -> None:
    _log_wrapper(syslog.LOG_ERR, *args, trace=trace)
