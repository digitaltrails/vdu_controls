#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021-2026 Contributors to vdu_controls <https://github.com/digitaltrails/vdu_controls>
# SPDX-License-Identifier: GPL-3.0-or-later
# Headless IPC tests for the single-instance guard.
# Run:  PYTHONPATH=$(pwd)/src python3 tests/test_single_instance.py
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from vdu_controls.qt_imports import QApplication, QtNetwork
from vdu_controls.vdu_controls_application import SingleInstanceServer, _activate_running_instance

PID = os.getpid()
PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"


def _spin(app, predicate, timeout_s: float = 2.0, step_s: float = 0.02) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(step_s)
    return False


def test_no_existing_instance(app) -> None:
    name = f"vdu_controls-test-{PID}-a"
    QtNetwork.QLocalServer.removeServer(name)
    found = _activate_running_instance(name, timeout_ms=200)
    assert not found, "expected False when no server is listening"


def test_server_emits_activate_on_request(app) -> None:
    name = f"vdu_controls-test-{PID}-b"
    QtNetwork.QLocalServer.removeServer(name)
    server = SingleInstanceServer(name)
    assert server._server.isListening(), "server did not start listening"
    activations: list[bool] = []
    server.activate_requested.connect(lambda: activations.append(True))

    found = _activate_running_instance(name, timeout_ms=500)
    assert found, "_activate_running_instance should have returned True"
    assert _spin(app, lambda: bool(activations)), "activate_requested was never emitted"
    server._server.close()


def test_two_clients_each_activate(app) -> None:
    name = f"vdu_controls-test-{PID}-c"
    QtNetwork.QLocalServer.removeServer(name)
    server = SingleInstanceServer(name)
    activations: list[int] = []
    server.activate_requested.connect(lambda: activations.append(len(activations) + 1))

    for _ in range(2):
        assert _activate_running_instance(name, timeout_ms=500)
    assert _spin(app, lambda: len(activations) >= 2), f"expected 2 activations, got {activations}"
    server._server.close()


def test_stale_socket_recovery(app) -> None:
    # Spawn a subprocess that binds a QLocalServer and then dies abruptly (SIGKILL).
    # Whether the kernel leaves a stale socket file depends on Qt's cleanup; the SingleInstanceServer
    # fallback (removeServer + retry listen) should make either outcome work.
    name = f"vdu_controls-test-{PID}-d"
    QtNetwork.QLocalServer.removeServer(name)
    script = textwrap.dedent(f"""
        import sys, time
        sys.path.insert(0, {str(REPO_ROOT / 'src')!r})
        from vdu_controls.qt_imports import QApplication, QtNetwork
        app = QApplication([])
        srv = QtNetwork.QLocalServer()
        assert srv.listen({name!r}), srv.errorString()
        print("READY", flush=True)
        time.sleep(30)
    """)
    proc = subprocess.Popen(
        [sys.executable, "-c", script],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
    )
    try:
        assert proc.stdout is not None
        # qt_imports prints "Trying Qt6"/"Trying Qt5" before our marker - skip until READY
        ready = False
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            line = proc.stdout.readline().strip()
            if line == "READY":
                ready = True
                break
        assert ready, "subprocess never printed READY"
        proc.kill()
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.kill()

    # Some Qt versions clean up on process exit; others don't.  The fallback must handle either.
    server = SingleInstanceServer(name)
    assert server._server.isListening(), f"SingleInstanceServer failed to bind after stale: {server._server.errorString()}"
    # And the recovered server should be reachable.
    activations: list[bool] = []
    server.activate_requested.connect(lambda: activations.append(True))
    assert _activate_running_instance(name, timeout_ms=500), "recovered server unreachable"
    assert _spin(app, lambda: bool(activations)), "recovered server did not emit activate_requested"
    server._server.close()


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # no display needed
    app = QApplication(sys.argv)
    tests = [
        ("no existing instance -> activate returns False", test_no_existing_instance),
        ("server emits activate_requested on connection", test_server_emits_activate_on_request),
        ("two activations from same server", test_two_clients_each_activate),
        ("stale socket recovery via removeServer + retry", test_stale_socket_recovery),
    ]
    failures = 0
    for name, fn in tests:
        try:
            fn(app)
            print(f"  {PASS}  {name}")
        except AssertionError as e:
            print(f"  {FAIL}  {name}: {e}")
            failures += 1
        except Exception as e:
            print(f"  {FAIL}  {name}: {type(e).__name__}: {e}")
            failures += 1
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
