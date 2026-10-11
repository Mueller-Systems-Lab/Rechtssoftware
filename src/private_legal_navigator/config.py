"""Application configuration via environment variables."""

import ipaddress
import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

# Hostnames always accepted as loopback even though they are not literals.
_LOOPBACK_ALIASES = frozenset({"localhost"})


def _is_loopback_host(host: str) -> bool:
    """Return True when *host* binds to the local loopback interface only.

    Accepts literal loopback addresses (all of ``127.0.0.0/8`` and ``::1``), with
    or without brackets, plus the ``localhost`` alias. Wildcard addresses such as
    ``0.0.0.0`` and ``::`` are deliberately **not** loopback: they accept
    connections from every interface.
    """
    candidate = host.strip()
    if candidate.lower() in _LOOPBACK_ALIASES:
        return True
    # Strip IPv6 brackets and any zone index (fe80::1%eth0 style).
    candidate = candidate.strip("[]").split("%", 1)[0]
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


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
        PLN_HOST: Host to bind to (must be a loopback address; default 127.0.0.1)
        PLN_PORT: Port to listen on (default: 8000)
        PLN_CSRF_SECRET: Shared secret for CSRF token signing (auto-generated if not set)
        PLN_ALLOWED_HOSTS: Comma-separated list of allowed Host header values
    """

    data_dir: Path = field(default_factory=lambda: Settings._default_data_dir())
    host: str = field(default_factory=lambda: os.environ.get("PLN_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.environ.get("PLN_PORT", "8000")))
    csrf_secret: str = field(default_factory=_generate_csrf_secret)

    def __post_init__(self) -> None:
        """Refuse to bind beyond loopback. Not configurable, by design.

        Loopback binding is the only control that keeps case processing on this
        machine: the application has no authentication, and Host-header
        validation is not an access control because the caller chooses the Host
        header. Without this check, setting ``PLN_HOST=0.0.0.0`` silently exposed
        every case endpoint to the local network (verified: HTTP 200 for
        ``/api/v1/cases`` over the LAN address).

        The project's local-only rule is absolute unless an explicit, documented
        architecture decision authorises otherwise. An environment variable is
        not such a decision — it leaves a one-word switch that silently publishes
        case data — so there is deliberately no opt-in flag here. Deviating means
        changing this code together with an ADR, which is the decision record the
        rule asks for.
        """
        if _is_loopback_host(self.host):
            return
        raise ValueError(
            f"PLN_HOST={self.host!r} is not a loopback address; refusing to start. "
            "This application has no authentication, so binding to a non-loopback "
            "address would expose case data to the network. The local-only rule in "
            "the project constitution permits that only after an explicit documented "
            "architecture decision, which is a code change plus an ADR — not an "
            "environment variable. Use 127.0.0.1 (or another 127.0.0.0/8 address, "
            "::1, or localhost)."
        )

    @property
    def is_loopback_bind(self) -> bool:
        """True when the configured bind address stays on the loopback interface.

        Always true after construction; it exists so callers can assert the
        invariant instead of re-deriving it.
        """
        return _is_loopback_host(self.host)

    @property
    def database_path(self) -> Path:
        """Full path to the SQLite database file."""
        return self.data_dir / "private_legal_navigator.db"

    @property
    def allowed_hosts(self) -> list[str]:
        """Explicit host allowlist derived from host and port.

        Returns exact host:port combinations. No wildcards, no subdomains.

        The configured host is included, not just the canonical 127.0.0.1: the
        loopback check accepts all of 127.0.0.0/8, so binding (say) 127.0.0.2
        must also let the UI answer on that address. Omitting it made the server
        bind an address its own Host validation then rejected with 400.
        """
        env_hosts = os.environ.get("PLN_ALLOWED_HOSTS")
        if env_hosts:
            return [h.strip() for h in env_hosts.split(",") if h.strip()]

        hosts: list[str] = []
        for candidate in (self.host, "127.0.0.1", "localhost", "[::1]"):
            entry = f"{candidate}:{self.port}"
            if entry not in hosts:
                hosts.append(entry)
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
