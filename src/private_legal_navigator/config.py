"""Application configuration via environment variables."""

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

# Host values that keep the case-processing API on the local machine. Anything
# else is treated as a deliberate, documented deviation from the local-only rule.
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})


def _generate_csrf_secret() -> str:
    """Generate a random CSRF secret on first access.

    Persisted across app restarts via environment variable.
    If not set, generates a new secret per process (acceptable for local use).
    """
    env_secret = os.environ.get("PLN_CSRF_SECRET")
    if env_secret:
        return env_secret
    return secrets.token_hex(32)


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables.

    Environment variables:
        PLN_DATA_DIR: Directory for the SQLite database (default: ~/.private-legal-navigator)
        PLN_HOST: Host to bind to (default: 127.0.0.1)
        PLN_PORT: Port to listen on (default: 8000)
        PLN_CSRF_SECRET: Shared secret for CSRF token signing (auto-generated if not set)
        PLN_ALLOWED_HOSTS: Comma-separated list of allowed Host header values
        PLN_ALLOW_NON_LOOPBACK: Set to "1" to permit binding beyond loopback (see below)
    """

    data_dir: Path = field(default_factory=lambda: Settings._default_data_dir())
    host: str = field(default_factory=lambda: os.environ.get("PLN_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.environ.get("PLN_PORT", "8000")))
    csrf_secret: str = field(default_factory=_generate_csrf_secret)

    def __post_init__(self) -> None:
        """Refuse to bind beyond loopback unless that is an explicit decision.

        Loopback binding is the only control that keeps case processing local:
        the application has no authentication, and Host-header validation is not
        an access control because a caller controls the Host header. Without this
        check, setting ``PLN_HOST=0.0.0.0`` silently exposed every case endpoint
        to the local network.

        The constitution requires local-only processing unless an explicit,
        documented architecture decision authorises otherwise, so a non-loopback
        bind must be opted into deliberately and can be pointed at that decision
        in ``PLN_ALLOW_NON_LOOPBACK_REASON``.
        """
        if self.host in _LOOPBACK_HOSTS:
            return
        if os.environ.get("PLN_ALLOW_NON_LOOPBACK") == "1":
            return
        raise ValueError(
            f"PLN_HOST={self.host!r} would bind the case-processing API beyond loopback. "
            "This application has no authentication and Host-header validation cannot "
            "protect it, so binding to a non-loopback address exposes case data to the "
            "network. The project's local-only rule requires an explicit, documented "
            "decision for that. Re-run with 127.0.0.1 (recommended), or set "
            "PLN_ALLOW_NON_LOOPBACK=1 together with PLN_ALLOW_NON_LOOPBACK_REASON to "
            "record the authorising decision."
        )

    @property
    def non_loopback_authorised(self) -> bool:
        """True when a non-loopback bind was deliberately opted into."""
        return self.host not in _LOOPBACK_HOSTS

    @property
    def database_path(self) -> Path:
        """Full path to the SQLite database file."""
        return self.data_dir / "private_legal_navigator.db"

    @property
    def allowed_hosts(self) -> list[str]:
        """Explicit host allowlist derived from host and port.

        Returns exact host:port combinations. No wildcards, no subdomains.
        """
        env_hosts = os.environ.get("PLN_ALLOWED_HOSTS")
        if env_hosts:
            return [h.strip() for h in env_hosts.split(",") if h.strip()]

        hosts: list[str] = []
        hosts.append(f"127.0.0.1:{self.port}")
        hosts.append(f"localhost:{self.port}")
        # IPv6 loopback optional
        hosts.append(f"[::1]:{self.port}")
        return hosts

    @property
    def template_dir(self) -> Path:
        """Absolute path to the Jinja2 template directory."""
        return Path(__file__).parent / "presentation" / "templates"

    @property
    def static_dir(self) -> Path:
        """Absolute path to the static assets directory."""
        return Path(__file__).parent / "presentation" / "static"

    @staticmethod
    def _default_data_dir() -> Path:
        """Default data directory: PLN_DATA_DIR env var or ~/.private-legal-navigator."""
        if env_dir := os.environ.get("PLN_DATA_DIR"):
            return Path(env_dir)
        return Path.home() / ".private-legal-navigator"
