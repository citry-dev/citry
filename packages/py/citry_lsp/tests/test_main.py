"""Tests for the `citry-lsp` console command."""

from __future__ import annotations

import socket
import subprocess
import sys
import time

import pytest

import citry_lsp.__main__ as main_module


def _free_port() -> int:
    # Bind port 0 so the OS picks a port nothing else is using, then release
    # it, so a server that wrongly accepted the options could claim it.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _accepts_connection(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.2)
        try:
            client.connect(("127.0.0.1", port))
        except OSError:
            return False
        return True


@pytest.mark.parametrize(
    "argv",
    [
        ["--tcp"],
        ["--ws"],
        ["--host", "127.0.0.1"],
        ["--port", "2087"],
        ["--port=2087"],
        ["--tcp", "--host", "127.0.0.1", "--port", "2087"],
        ["--tc"],
        ["--stdio"],
    ],
)
def test_every_option_exits_with_the_stdio_only_error(argv, monkeypatch, capsys):
    # Starting any transport would mean the option was accepted; failing
    # here, rather than serving, keeps a regression from hanging the test.
    for transport in ("start_io", "start_tcp", "start_ws"):
        monkeypatch.setattr(main_module.server, transport, lambda *_: pytest.fail("server started"))

    with pytest.raises(SystemExit) as exited:
        main_module.main(argv)

    assert exited.value.code == 2
    error = capsys.readouterr().err
    assert "usage: citry-lsp" in error
    assert "runs over stdio only" in error
    assert argv[0] in error


def test_no_arguments_start_the_stdio_server(monkeypatch):
    started: list[bool] = []
    monkeypatch.setattr(main_module.server, "start_io", lambda: started.append(True))

    assert main_module.main([]) == 0
    assert started == [True]


def test_help_describes_the_stdio_transport():
    completed = subprocess.run(
        [sys.executable, "-m", "citry_lsp", "--help"],
        check=False,
        capture_output=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr.decode(errors="replace")
    assert b"usage: citry-lsp" in completed.stdout
    assert b"--tcp" not in completed.stdout
    assert b"--port" not in completed.stdout


def test_transport_options_never_open_a_listening_socket():
    port = _free_port()
    # Keep stdin open: a server that ignored the options and started a
    # transport would block here instead of exiting.
    process = subprocess.Popen(
        [sys.executable, "-m", "citry_lsp", "--tcp", "--host", "127.0.0.1", "--port", str(port)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    connected = False
    try:
        # Probe the port for as long as the process runs, so a server that
        # ignored the options and kept listening is caught.
        deadline = time.monotonic() + 30
        while process.poll() is None and time.monotonic() < deadline:
            connected = connected or _accepts_connection(port)
            time.sleep(0.05)
        connected = connected or _accepts_connection(port)
    finally:
        if process.poll() is None:
            process.kill()
        _, stderr = process.communicate(timeout=30)

    assert not connected, "citry-lsp accepted a TCP connection"
    assert process.returncode == 2
    assert b"runs over stdio only" in stderr
