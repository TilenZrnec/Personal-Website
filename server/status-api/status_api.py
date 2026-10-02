#!/usr/bin/env python3
"""Status API for tilenserver.com.

Serves GET /api/status as JSON on 127.0.0.1:8090. Only cloudflared talks to it.
Uses only Python's standard library, so there is nothing to pip install.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LISTEN = ("127.0.0.1", 8090)
ALLOWED_ORIGINS = {"https://www.tilenserver.com", "https://tilenserver.com"}
SAMPLE_EVERY_S = 5

latest = None  # The JSON answer as bytes, rebuilt every SAMPLE_EVERY_S seconds.


def cpu_times():
    # First line of /proc/stat: "cpu user nice system idle iowait irq softirq steal ..."
    fields = [int(x) for x in Path("/proc/stat").read_text().splitlines()[0].split()[1:9]]
    idle = fields[3] + fields[4]  # idle + iowait
    return idle, sum(fields)


def memory_percent():
    info = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        info[key] = int(value.split()[0])
    return 100 * (info["MemTotal"] - info["MemAvailable"]) / info["MemTotal"]


def temperature_c():
    temps = {}
    for zone in Path("/sys/class/thermal").glob("thermal_zone*"):
        try:
            temps[(zone / "type").read_text().strip()] = int((zone / "temp").read_text()) / 1000
        except (OSError, ValueError):
            pass
    # Prefer the CPU package sensor, then the firmware's CPU and ACPI sensors.
    for name in ("x86_pkg_temp", "TCPU", "acpitz"):
        if name in temps:
            return round(temps[name], 1)
    return None


def services():
    # Tailscale's network interface only exists while tailscaled is running.
    # Steps 5 and 6 add Music and Photos here, checked by connecting to their local ports.
    return [{"name": "Tailscale", "up": Path("/sys/class/net/tailscale0").exists()}]


def sampler():
    global latest
    prev_idle, prev_total = cpu_times()
    while True:
        time.sleep(SAMPLE_EVERY_S)
        try:
            idle, total = cpu_times()
            busy = 1 - (idle - prev_idle) / max(total - prev_total, 1)
            prev_idle, prev_total = idle, total
            status = {
                "uptime_seconds": int(float(Path("/proc/uptime").read_text().split()[0])),
                "cpu_percent": round(100 * busy, 1),
                "memory_percent": round(memory_percent(), 1),
                "temperature_c": temperature_c(),
                "services": services(),
            }
            latest = json.dumps(status).encode()
        except Exception as error:
            print(f"Sampling failed: {error!r}", flush=True)


class Handler(BaseHTTPRequestHandler):
    # Hide the Python version that http.server puts in the Server header by default.
    server_version = "status-api"
    sys_version = ""

    def do_GET(self):
        if self.path != "/api/status":
            self.send_error(404)
            return
        body = latest
        if body is None:  # The first sample isn't ready yet (first few seconds after start).
            self.send_error(503)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # CORS: let the website's JavaScript read this answer. Browsers send Origin; it must match exactly.
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Don't log every request: each visitor polls every 30 s.


if __name__ == "__main__":
    threading.Thread(target=sampler, daemon=True).start()
    ThreadingHTTPServer(LISTEN, Handler).serve_forever()
