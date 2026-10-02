# tilenserver.com

My personal website and homelab. The website is live at https://www.tilenserver.com.

## Working with me
- I'm a CS student and new to homelabbing. Explain the *why* behind every command and setting, not just the commands, and point out gotchas.
- I work from Windows 11 (PowerShell) and manage the server over SSH from my PC and laptop. Give server commands as copy-pasteable blocks; multi-line pastes should start with `sudo -v`.
- **This repo is public.** Never commit hostnames, usernames, IP addresses, tailnet names, tokens or other secrets.

## Repo
- On GitHub as `TilenZrnec/tilenserver-homelab` (renamed from `Personal-Website` on 2026-10-02). The site's only GitHub link ("Source on GitHub") points there.
- `site/`: static site (`index.html`, `style.css`, `script.js`), no build step, deployed by Cloudflare Pages.
- Tab icon: `site/icon.svg` (a small server rack in the site's blue), with `favicon.ico` and `apple-touch-icon.png` drawn from the same shapes for browsers and iPhones that don't use SVG. If the SVG changes, regenerate those two to match.
- `site/script.js` polls `https://lab.tilenserver.com/api/status` every 30 s and expects JSON like `{ "uptime_seconds", "cpu_percent", "memory_percent", "temperature_c", "services": [{ "name", "up" }] }`. If the request fails, the card shows "Offline".
- The collapsible "Server specs" card in `site/index.html` mirrors "Server" below (hardware, OS and how it's reached; nothing identifying). Update it when the hardware changes, e.g. the storage for step 6.
- `server/status-api/`: the status endpoint (`status_api.py`, Python standard library only) and its systemd unit (`status-api.service`). The server runs copies at `/opt/status-api/status_api.py` and `/etc/systemd/system/status-api.service`; after changing them here, copy them over and run `sudo systemctl daemon-reload && sudo systemctl restart status-api`.

## Roadmap
1. **Website on Cloudflare Pages**: done.
2. **Server**: done. An ASUS laptop instead of the originally planned ThinkCentre (see "Server" below).
3. **Linux, SSH and Tailscale**: done 2026-10-01.
   - SSH with keys only, from the PC and the laptop; no open ports on the router.
   - Tailscale on the server, PC, laptop and phone.
4. **Server status on the website**: done 2026-10-02.
   - A small status endpoint on the server, coarse data only (no hostnames, IPs or versions).
   - A Cloudflare Tunnel publishes it as `https://lab.tilenserver.com/api/status`, so nothing at home is exposed.
   - The website shows the status and shows "Offline" when the server or the tunnel is down (tested, including a reboot).
5. **Music**: next.
   - Self-hosted music streaming.
   - Use it alongside Spotify for a month, then cancel Spotify.
6. **Photos**
   - Self-hosted photos.
   - Encrypted, versioned backups: home PC, an offsite external HDD and an encrypted cloud copy.
   - Restore from a backup, then delete the photos from Google.

## Server (set up 2026-10-01; status API and tunnel added 2026-10-02)
- **Hardware:** ASUS ExpertBook B1502CBA laptop: i3-1215U (6 cores, Intel UHD with Quick Sync), 24 GB RAM, a single 512 GB NVMe SSD (the only M.2 slot), gigabit Ethernet. The battery doubles as a small UPS.
- **OS:** Ubuntu Server 26.04 LTS (`sudo` is `sudo-rs`). LVM, root volume extended to the whole disk, no disk encryption so it can reboot unattended. Security updates install automatically (`unattended-upgrades`, Ubuntu's default). Packages from third-party apt repos only update automatically if their origin is allowed: `origin=cloudflared` and `origin=Tailscale` are, in `/etc/apt/apt.conf.d/52unattended-upgrades-cloudflared` and `52unattended-upgrades-tailscale`. Check with `sudo unattended-upgrade --dry-run --debug 2>&1 | grep -i "allowed origins"`.
- **Laptop-as-server tweaks:**
  - Lid switch ignored: `/etc/systemd/logind.conf.d/lid.conf`.
  - `sleep`, `suspend`, `hibernate` and `hybrid-sleep` targets masked.
  - Battery charge capped at 80% by `battery-limit.service`, which writes `charge_control_end_threshold`.
  - Fixed LAN IP through a DHCP reservation on the router.
- **SSH:** OpenSSH, ed25519 keys only, one key per device (PC and laptop), in `~/.ssh/authorized_keys`. `/etc/ssh/sshd_config.d/01-hardening.conf` sets `PasswordAuthentication no`, `KbdInteractiveAuthentication no` and `PermitRootLogin no`. It's named `01-` because sshd keeps the first value it reads, so it wins over Ubuntu's `50-cloud-init.conf`. The fallback is the laptop's own screen and keyboard.
- **Tailscale:** on the server, PC, laptop and phone. MagicDNS is on, so SSH from anywhere uses the server's tailnet name. Key expiry is disabled for the server.
- **Status API:** `status-api.service` runs `/opt/status-api/status_api.py` (source in `server/status-api/`), listening only on `127.0.0.1:8090`. It measures every 5 s and serves the cached JSON. CORS allows `https://www.tilenserver.com` and `https://tilenserver.com`. Sandboxed with `DynamicUser=yes`, `ProtectSystem=strict` and related options, and it may only open `AF_INET`/`AF_INET6` sockets.
  - `systemctl is-active` doesn't work inside this sandbox (D-Bus drops the connection: "Transport endpoint is not connected"), so service checks don't ask systemd. Tailscale counts as up while `/sys/class/net/tailscale0` exists; check the apps from steps 5 and 6 by connecting to their local ports.
- **Cloudflare Tunnel:** `cloudflared` from Cloudflare's apt repo (`pkg.cloudflare.com`), running as `cloudflared.service` with `--no-autoupdate` and `--token-file /etc/cloudflared/token` (`-rw-------`, readable by root only). The tunnel is managed in the dashboard (Networking → Tunnels → `homelab`); its one published application route is `lab.tilenserver.com` → `http://127.0.0.1:8090`. cloudflared only connects outwards, so UFW needs no rule.
  - The token is a secret. If it leaks: Refresh token in the dashboard, `sudo cloudflared service uninstall`, then reinstall with the new token (paste the command with a leading space so bash leaves it out of the history).
  - New hostnames: if a name was looked up before it existed (the website polls every 30 s), the home router or ISP can cache "does not exist" for up to 30 min (the zone's SOA minimum TTL). Test around it with `Resolve-DnsName <name> -Type A -Server 1.1.1.1` or `curl.exe --doh-url https://1.1.1.1/dns-query …`.
- **Firewall (UFW):** deny incoming and allow outgoing by default; allow 22/tcp from the home LAN; allow everything on `tailscale0`. Docker bypasses UFW, so deal with that when Docker arrives in step 5.
- **Network:** behind NAT (possibly CGNAT) with a dynamic public IP, so no port forwarding. Anything reaching the server goes through outbound tunnels: Tailscale for private access, Cloudflare Tunnel for public access. `tailscale netcheck` shows easy NAT (`MappingVariesByDestIP: false`) and working UDP, so Tailscale usually connects directly. No IPv6 and no UPnP. The nearest relay is Frankfurt.

## Open issues
- **Step 6, storage:** there is about 1 TB of photos already, and the original plan left room for 2 TB, but the server has a single 512 GB SSD. It needs a bigger NVMe drive or an external drive on the USB-C 3.2 Gen 2 port.
