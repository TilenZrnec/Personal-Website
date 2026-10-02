// Fetches the home server's status and shows it in the "Live status" card.
// If the server or the Cloudflare Tunnel is down, the request fails and the card says "Offline".

// The status endpoint on the server (server/status-api/), published through a Cloudflare Tunnel. It returns JSON like:
// {
//   "uptime_seconds": 86400,
//   "cpu_percent": 12.5,
//   "memory_percent": 41.0,
//   "temperature_c": 48.2,
//   "services": [{ "name": "Tailscale", "up": true }]
// }
// The server lets this site read it (CORS) by sending Access-Control-Allow-Origin: https://www.tilenserver.com
const STATUS_URL = "https://lab.tilenserver.com/api/status";
const REFRESH_EVERY_MS = 30000;

function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days} d ${hours} h`;
  if (hours > 0) return `${hours} h ${minutes} min`;
  return `${minutes} min`;
}

function formatPercent(value) {
  return value == null ? "–" : `${Math.round(value)}%`;
}

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

// Fills a bar under a number: 0–100 percent of its width.
function setMeter(id, percent) {
  const width = percent == null ? 0 : Math.min(100, Math.max(0, percent));
  document.getElementById(id).style.width = `${width}%`;
}

function showOnline(status) {
  document.getElementById("lab-state").dataset.state = "up";
  setText("lab-state-text", "Online");
  setText("uptime", formatUptime(status.uptime_seconds));
  setText("cpu", formatPercent(status.cpu_percent));
  setText("memory", formatPercent(status.memory_percent));
  setMeter("cpu-meter", status.cpu_percent);
  setMeter("memory-meter", status.memory_percent);
  setText("temperature", status.temperature_c == null ? "–" : `${Math.round(status.temperature_c)} °C`);

  // Build the list with textContent, not innerHTML, so text from the server can never inject HTML.
  const list = document.getElementById("services");
  list.replaceChildren();
  for (const service of status.services ?? []) {
    const item = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = service.name;
    const state = document.createElement("span");
    state.className = service.up ? "state up" : "state down";
    state.textContent = service.up ? "Up" : "Down";
    item.append(name, state);
    list.append(item);
  }
  setText("lab-note", `Updated at ${new Date().toLocaleTimeString()}`);
}

function showOffline() {
  document.getElementById("lab-state").dataset.state = "down";
  setText("lab-state-text", "Offline");
  for (const id of ["uptime", "cpu", "memory", "temperature"]) {
    setText(id, "–");
  }
  setMeter("cpu-meter", null);
  setMeter("memory-meter", null);
  document.getElementById("services").replaceChildren();
  setText("lab-note", "The server isn't answering. It may be rebooting, or I'm still building it.");
}

async function refresh() {
  try {
    const response = await fetch(STATUS_URL, { signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    showOnline(await response.json());
  } catch {
    showOffline();
  }
}

refresh();
setInterval(refresh, REFRESH_EVERY_MS);
