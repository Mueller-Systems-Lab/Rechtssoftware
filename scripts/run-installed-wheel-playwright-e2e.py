#!/usr/bin/env python3
"""Installed-wheel Playwright E2E harness.

Builds a wheel from the current checkout, installs it into a throwaway venv,
verifies that imports resolve from site-packages, starts the server from that
installed package, seeds synthetic data over HTTP and runs the browser suite
against it. Set PLN_E2E_HEADED=1 for a visible browser window (required for
release evidence).

Usage:
  env -u LD_LIBRARY_PATH .venv/bin/python scripts/run-installed-wheel-playwright-e2e.py

Steps:
  1. Reserve free loopback port
  2. Create temp data directory outside repo
  3. Record provenance (candidate SHA, dirty flag, headed flag)
  4. Build wheel from current checkout
  5. Install wheel in temp venv (NOT editable)
  6. Verify import from site-packages
  7. Start server from site-packages
  8. Wait for /health
  9. Seed synthetic data via HTTP API
  10. Run Playwright tests (headed when PLN_E2E_HEADED=1)
  11. Stop server
"""

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_free_port() -> int:
    """Find a free TCP port on loopback."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def build_wheel() -> Path:
    """Build wheel from the current checkout, return path."""
    subprocess.run(
        [sys.executable, "-m", "build"],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )
    wheels = list((REPO_ROOT / "dist").glob("*.whl"))
    if not wheels:
        raise RuntimeError("No wheel found after build")
    return wheels[0]


def record_provenance(temp_dir: Path) -> str:
    """Record the exact commit the wheel was built from.

    Evidence is only meaningful when it is bound to a commit; the original run of
    this harness produced a report with no SHA, which made it impossible to tie
    the recorded result to any revision.
    """
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sha, dirty = "UNKNOWN", ""
    record = {
        "candidate_sha": sha,
        "working_tree_dirty": bool(dirty),
        "headed": os.environ.get("PLN_E2E_HEADED") == "1",
        "python": sys.version.split()[0],
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (temp_dir / "run-provenance.json").write_text(json.dumps(record, indent=2))
    print(f"  Provenance: {sha}{' (DIRTY TREE)' if dirty else ''}")
    return sha


def install_and_verify(wheel: Path, venv_dir: Path) -> str:
    """Install wheel in temp venv, verify import from site-packages."""
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True, capture_output=True,
    )
    pip = venv_dir / "bin" / "pip"
    subprocess.run(
        [str(pip), "install", str(wheel)],
        check=True, capture_output=True,
    )

    # Verify import from site-packages (not repo src)
    result = subprocess.run(
        [str(venv_dir / "bin" / "python"), "-c",
         "import private_legal_navigator; "
         "p = __import__('pathlib').Path(private_legal_navigator.__file__); "
         "print('site-packages' if 'site-packages' in str(p) else 'SOURCE_CHECKOUT'); "
         "print(p)"],
        capture_output=True, text=True, check=True,
    )
    output = result.stdout.strip()
    if "SOURCE_CHECKOUT" in output:
        raise RuntimeError(f"Import NOT from site-packages: {output}")
    lines = output.splitlines()
    print(f"  Import verified: {lines[1] if len(lines) > 1 else output}")
    return output


def seed_via_http(base_url: str, temp_dir: Path) -> dict:
    """Seed synthetic test data via the HTTP API (not direct DB)."""
    import urllib.request
    import urllib.error

    # Create case
    case_data = json.dumps({"title": "SYNTHETISCH – Playwright E2E Testfall"}).encode()
    req = urllib.request.Request(
        f"{base_url}/api/v1/cases",
        data=case_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        case = json.loads(resp.read())
        case_id = case["case_id"]
        print(f"  Case created: {case_id}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Failed to create case: {e.code} {body}")

    # Upload synthetic PDF
    import io
    import pymupdf

    pdf_writer = pymupdf.open()
    page = pdf_writer.new_page(width=595, height=842)
    test_text = (
        "Bescheid vom 15.06.2026\n\n"
        "Sehr geehrte Damen und Herren,\n\n"
        "hiermit ergeht folgender Bescheid. Sie k\u00f6nnen innerhalb von 14 Tagen "
        "Widerspruch einlegen. Die Frist beginnt mit der Bekanntgabe.\n\n"
        "Mit freundlichen Gr\u00fc\u00dfen\nDie Beh\u00f6rde\n"
    )
    page.insert_text((72, 72), test_text, fontsize=11)
    pdf_buffer = io.BytesIO()
    pdf_writer.save(pdf_buffer)
    pdf_writer.close()
    pdf_bytes = pdf_buffer.getvalue()

    # Multipart upload
    boundary = "----PlaywrightE2EBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="SYNTHETISCH-Testbescheid.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{base_url}/api/v1/cases/{case_id}/documents",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Origin": base_url,
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req)
        doc = json.loads(resp.read())
        document_id = doc.get("document_id", "")
        print(f"  Document uploaded: {document_id}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Failed to upload document: {e.code} {body}")

    seed = {
        "case_id": case_id,
        "document_id": document_id,
        "base_url": base_url,
    }
    seed_file = temp_dir / "seed_data.json"
    seed_file.write_text(json.dumps(seed, indent=2))

    # Seed a second case for cross-case-isolation tests
    case2_data = json.dumps({"title": "SYNTHETISCH – Playwright E2E Case B"}).encode()
    req2 = urllib.request.Request(
        f"{base_url}/api/v1/cases",
        data=case2_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp2 = urllib.request.urlopen(req2)
    case2 = json.loads(resp2.read())
    seed["case_b_id"] = case2["case_id"]
    print(f"  Case B created: {case2['case_id']}")

    seed_file.write_text(json.dumps(seed, indent=2))
    return seed


def start_server(venv_dir: Path, port: int, data_dir: Path) -> subprocess.Popen:
    """Start the app from site-packages."""
    env = os.environ.copy()
    env["PLN_PORT"] = str(port)
    env["PLN_HOST"] = "127.0.0.1"
    env["PLN_DATA_DIR"] = str(data_dir)

    # Disable any repo-PYTHONPATH leakage
    env.pop("PYTHONPATH", None)

    proc = subprocess.Popen(
        [str(venv_dir / "bin" / "python"), "-m", "private_legal_navigator", "serve"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tempfile.gettempdir(),  # Ensure NOT in repo
    )
    return proc


def wait_for_health(base_url: str, timeout: float = 30.0) -> bool:
    """Poll /health until ready or timeout."""
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(f"{base_url}/health", timeout=2)
            if resp.status == 200:
                data = json.loads(resp.read())
                if data.get("status") in ("healthy", "ok"):
                    print(f"  Server ready: {data}")
                    return True
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            pass
        time.sleep(0.5)
    return False


def run_playwright(base_url: str, seed_file: Path) -> int:
    """Run Playwright tests.

    Set PLN_E2E_HEADED=1 to run with a visible browser window. Release evidence
    requires a headed run: a headless pass does not demonstrate that the UI is
    usable, only that it is reachable.
    """
    env = os.environ.copy()
    env["PLN_E2E_BASE_URL"] = base_url
    env["PLN_E2E_SEED_FILE"] = str(seed_file)
    env.pop("PYTHONPATH", None)

    cmd = ["npx", "playwright", "test"]
    if os.environ.get("PLN_E2E_HEADED") == "1":
        cmd.append("--headed")

    result = subprocess.run(cmd, cwd=REPO_ROOT, env=env)
    return result.returncode


def main():
    print("=== RC-026-R2 Playwright E2E Harness ===")
    print(f"  Repo: {REPO_ROOT}")
    print(f"  Python: {sys.executable}")

    # 1. Reserve port
    port = find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    print(f"  Port: {port}")

    # 2. Temp directories (outside repo)
    temp_base = Path(tempfile.mkdtemp(prefix="pln-e2e-"))
    data_dir = temp_base / "data"
    venv_dir = temp_base / "venv"
    data_dir.mkdir(parents=True)
    print(f"  Temp: {temp_base}")

    server_proc = None
    try:
        # 3. Record provenance, then build wheel
        record_provenance(temp_base)
        print("  Building wheel...")
        wheel = build_wheel()
        print(f"  Wheel: {wheel.name}")

        # 4. Install + verify
        print("  Installing wheel...")
        install_and_verify(wheel, venv_dir)

        # 5. Start server
        print("  Starting server...")
        server_proc = start_server(venv_dir, port, data_dir)

        # 6. Wait for health
        if not wait_for_health(base_url):
            raise RuntimeError("Server failed to start")

        # 7. Seed data via HTTP
        print("  Seeding test data...")
        seed = seed_via_http(base_url, temp_base)
        seed_file = temp_base / "seed_data.json"
        seed_file.write_text(json.dumps(seed, indent=2))

        # 8. Run Playwright
        print("  Running Playwright...")
        exit_code = run_playwright(base_url, seed_file)

        if exit_code != 0:
            print(f"  Playwright exit code: {exit_code}")
            sys.exit(exit_code)

        print("  ALL PLAYWRIGHT TESTS PASSED")

    finally:
        if server_proc:
            print("  Stopping server...")
            server_proc.send_signal(signal.SIGTERM)
            try:
                server_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait()
        # Keep temp dir for debugging; clean up in CI
        print(f"  Temp data preserved at: {temp_base}")


if __name__ == "__main__":
    main()
