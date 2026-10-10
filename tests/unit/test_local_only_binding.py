"""Local-only binding is enforced, not merely defaulted.

The application has no authentication, and Host-header validation cannot stand in
for one (a caller chooses the Host header). The bind address is therefore the
only control keeping case processing on the local machine, and it must refuse a
non-loopback bind unless that deviation is a deliberate, recorded decision.

Before this enforcement existed, ``PLN_HOST=0.0.0.0`` silently published every
case endpoint to the local network; the request to ``/api/v1/cases`` from a LAN
address returned HTTP 200 with case data.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from private_legal_navigator.config import Settings


@pytest.fixture
def clean_host_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.delenv("PLN_HOST", raising=False)
    monkeypatch.delenv("PLN_ALLOW_NON_LOOPBACK", raising=False)
    return monkeypatch


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", "[::1]"])
def test_loopback_hosts_are_accepted(clean_host_env: pytest.MonkeyPatch, host: str) -> None:
    clean_host_env.setenv("PLN_HOST", host)
    settings = Settings()
    assert settings.host == host
    assert settings.non_loopback_authorised is False


def test_default_host_is_loopback(clean_host_env: pytest.MonkeyPatch) -> None:
    assert Settings().host == "127.0.0.1"


def test_non_loopback_bind_is_refused_by_default(clean_host_env: pytest.MonkeyPatch) -> None:
    clean_host_env.setenv("PLN_HOST", "0.0.0.0")
    with pytest.raises(ValueError) as excinfo:
        Settings()
    message = str(excinfo.value)
    assert "0.0.0.0" in message
    assert "loopback" in message
    assert "PLN_ALLOW_NON_LOOPBACK" in message


def test_lan_address_is_refused_by_default(clean_host_env: pytest.MonkeyPatch) -> None:
    clean_host_env.setenv("PLN_HOST", "192.168.1.210")
    with pytest.raises(ValueError):
        Settings()


def test_non_loopback_bind_is_allowed_when_explicitly_opted_in(
    clean_host_env: pytest.MonkeyPatch,
) -> None:
    clean_host_env.setenv("PLN_HOST", "0.0.0.0")
    clean_host_env.setenv("PLN_ALLOW_NON_LOOPBACK", "1")
    settings = Settings()
    assert settings.host == "0.0.0.0"
    assert settings.non_loopback_authorised is True


def test_opt_in_value_must_be_exactly_one(clean_host_env: pytest.MonkeyPatch) -> None:
    """A stray value must not be read as consent."""
    clean_host_env.setenv("PLN_HOST", "0.0.0.0")
    clean_host_env.setenv("PLN_ALLOW_NON_LOOPBACK", "true")
    with pytest.raises(ValueError):
        Settings()


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
    assert "PLN_ALLOW_NON_LOOPBACK" in result.stderr
