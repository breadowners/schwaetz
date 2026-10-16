"""Launch the localhost backend with one exact private Tailscale hostname allowed.

This does not install Tailscale, sign in, enable HTTPS, or publish a service.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys


def private_hostname(value):
    host = value.strip().lower().rstrip(".")
    label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    if len(host) > 253 or not re.fullmatch(rf"{label}(?:\.{label})*\.ts\.net", host):
        raise ValueError("Use the Mac's exact Tailscale DNS name ending in .ts.net, without a URL or port.")
    return host


def detect_hostname():
    binary = shutil.which("tailscale")
    bundled = Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale")
    if not binary and bundled.is_file():
        binary = str(bundled)
    if not binary:
        raise ValueError("Install Tailscale on this Mac and your phone, sign in to the same personal account, then retry. https://tailscale.com/download")
    result = subprocess.run([binary, "status", "--json"], capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise ValueError("Open Tailscale on the Mac and connect it, then retry.")
    status = json.loads(result.stdout)
    if status.get("BackendState") != "Running":
        raise ValueError("Connect Tailscale on this Mac, then retry.")
    return private_hostname(status.get("Self", {}).get("DNSName", ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hostname", help="Mac's exact Tailscale DNS name; otherwise detected locally")
    parser.add_argument("--check", action="store_true", help="Show setup commands without starting the app")
    args = parser.parse_args()
    try:
        hostname = private_hostname(args.hostname) if args.hostname else detect_hostname()
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, str(error) + "\n")
    print(f"Phone address: https://{hostname}\n"
          "In another terminal, run:\n  tailscale serve http://127.0.0.1:8765\n"
          "Follow Tailscale's HTTPS setup if prompted. Keep this Mac awake.\n"
          "Use your own Tailscale account on both devices. Audio is processed on this Mac.\n", flush=True)
    if args.check:
        return
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 8765)) == 0:
            parser.exit(1, "Port 8765 is already in use. Stop the existing app server before running npm run phone.\n")
    env = os.environ.copy()
    env["SPEAK_ALLOWED_HOSTS"] = ",".join(filter(None, [env.get("SPEAK_ALLOWED_HOSTS"), hostname]))
    os.chdir(Path(__file__).resolve().parent)
    os.execve(sys.executable, [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1",
                              "--port", "8765", "--no-access-log"], env)


if __name__ == "__main__":
    main()
