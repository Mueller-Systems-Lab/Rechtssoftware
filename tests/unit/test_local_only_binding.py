"""Local-only binding is enforced and cannot be configured away.

The application has no authentication, and Host-header validation cannot stand in
for one (a caller chooses the Host header). The bind address is therefore the
only control keeping case processing on the local machine.

Before this enforcement existed, ``PLN_HOST=0.0.0.0`` silently published every
case endpoint to the local network: a request to ``/api/v1/cases`` from a LAN
address returned HTTP 200 with case data, and a spoofed ``Host: 127.0.0.1`` header
was accepted too.

The refusal is deliberately not configurable. The constitution allows a
local-only deviation only after an explicit, documented architecture decision; an
environment variable is a one-word switch that silently publishes case data, so
deviating requires changing this code together with an ADR.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from private_legal_navigator.config import Settings, _is_loopback_host


@pytest.fixture
def clean_host_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.delenv("PLN_HOST", raising=False)
    monkeypatch.delenv("PLN_ALLOW_NON_LOOPBACK", raising=False)
    return monkeypatch


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "127.0.0.2",  # the whole 127.0.0.0/8 block is loopback
        "localhost",
        "::1",
        "[::1]",
    ],
)
def test_loopback_hosts_are_accepted(clean_host_env: pytest.MonkeyPatch, host: str) -> None:
    clean_host_env.setenv("PLN_HOST", host)
    settings = Settings()
    assert settings.host == host
    assert settings.is_loopback_bind is True


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.168.1.210", "example.com", "10.0.0.5"])
def test_non_loopback_hosts_are_refused(clean_host_env: pytest.MonkeyPatch, host: str) -> None:
    clean_host_env.setenv("PLN_HOST", host)
    with pytest.raises(ValueError) as excinfo:
        Settings()
    message = str(excinfo.value)
    assert host in message
    assert "loopback" in message


def test_default_host_is_loopback(clean_host_env: pytest.MonkeyPatch) -> None:
    settings = Settings()
    assert settings.host == "127.0.0.1"
    assert settings.is_loopback_bind is True


def test_no_environment_variable_can_authorise_a_non_loopback_bind(
    clean_host_env: pytest.MonkeyPatch,
) -> None:
    """The refusal must not be bypassable by configuration."""
    clean_host_env.setenv("PLN_HOST", "0.0.0.0")
    clean_host_env.setenv("PLN_ALLOW_NON_LOOPBACK", "1")
    clean_host_env.setenv("PLN_ALLOW_NON_LOOPBACK_REASON", "operator asked")
    with pytest.raises(ValueError):
        Settings()


def test_loopback_detection_helper_rejects_wildcards() -> None:
    # Wildcards accept connections from every interface, so they are not loopback
    # even though they are commonly written next to 127.0.0.1 in examples.
    assert _is_loopback_host("0.0.0.0") is False
    assert _is_loopback_host("::") is False
    assert _is_loopback_host("127.0.0.1") is True
    assert _is_loopback_host("127.1.2.3") is True
    assert _is_loopback_host("not-a-host") is False


def test_cli_refuses_cleanly_without_a_traceback(clean_host_env: pytest.MonkeyPatch) -> None:
    """The refusal must be a clear message, not an unhandled exception."""
    clean_host_env.setenv("PLN_HOST", "0.0.0.0")
    result = subprocess.run(
        [sys.executable, "-m", "private_legal_navigator", "serve"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 2, result
    assert "Traceback" not in result.stderr, result.stderr
    assert "loopback" in result.stderr
