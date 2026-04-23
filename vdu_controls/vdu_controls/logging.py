# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from datetime import datetime
import io
import syslog
import traceback

LOG_SYSLOG_CAT = {syslog.LOG_INFO: "INFO:", syslog.LOG_ERR: "ERROR:", syslog.LOG_WARNING: "WARNING:", syslog.LOG_DEBUG: "DEBUG:"}
log_to_syslog = False
log_debug_enabled = False  # Often used to guard needless computation: log_debug(needless) if log_debug_enabled else None


def log_set_syslog(enable: bool) -> None:
    global log_to_syslog
    log_info("logging: logging to syslog is enabled")
    log_to_syslog = enable


def log_set_debug(enable: bool) -> None:
    global log_debug_enabled
    log_warning("logging: debug is enabled")
    log_debug_enabled = enable

def log_wrapper(severity, *args, trace=False) -> None:
    with io.StringIO() as output:
        print(*args, file=output, end='')
        message = output.getvalue()
        prefix = LOG_SYSLOG_CAT[severity]
        if log_to_syslog:
            syslog_message = prefix + " " + message if severity == syslog.LOG_DEBUG else message
            syslog.syslog(severity, syslog_message)
        else:
            print(datetime.now().strftime("%H:%M:%S"), prefix, message)
    if log_debug_enabled and trace:
        log_debug("TRACEBACK:", ''.join(traceback.format_stack()))


def log_debug(*args, trace=False) -> None:
    log_wrapper(syslog.LOG_DEBUG, *args, trace=trace) if log_debug_enabled else None


def log_info(*args, trace=False) -> None:
    log_wrapper(syslog.LOG_INFO, *args, trace=trace)


def log_warning(*args, trace=False) -> None:
    log_wrapper(syslog.LOG_WARNING, *args, trace=trace)


def log_error(*args, trace=False) -> None:
    log_wrapper(syslog.LOG_ERR, *args, trace=trace)
