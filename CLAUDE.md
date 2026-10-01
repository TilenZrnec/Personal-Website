# tilenserver.com

My personal website and homelab. The website is live at https://www.tilenserver.com.

## Working with me
- I'm a CS student and new to homelabbing. Explain the *why* behind every command and setting, not just the commands, and point out gotchas.
- I work from Windows 11 (PowerShell) and manage the server over SSH from my PC and laptop. Give server commands as copy-pasteable blocks; multi-line pastes should start with `sudo -v`.
- **This repo is public.** Never commit hostnames, usernames, IP addresses, tailnet names, tokens or other secrets.

## Repo
- `site/`: static site (`index.html`, `style.css`, `script.js`), no build step, deployed by Cloudflare Pages.
- `site/script.js` polls `https://lab.tilenserver.com/api/status` every 30 s and expects JSON like `{ "uptime_seconds", "cpu_percent", "memory_percent", "temperature_c", "services": [{ "name", "up" }] }`. If the request fails, the card shows "Offline".
- The "What I'm building" list in `site/index.html` mirrors the roadmap below; update its tags as steps finish.

## Roadmap
1. **Website on Cloudflare Pages**: done.
2. **Server**: done. An ASUS laptop instead of the originally planned ThinkCentre (see "Server" below).
3. **Linux, SSH and Tailscale**: done 2026-10-01.
   - SSH with keys only, from the PC and the laptop; no open ports on the router.
   - Tailscale on the server, PC, laptop and phone.
4. **Server status on the website**: next.
   - A small status endpoint on the server, coarse data only (no hostnames, IPs or versions).
   - A Cloudflare Tunnel to it, so nothing at home is exposed.
   - The website shows the status and copes when the server is offline.
5. **Music**
   - Self-hosted music streaming.
   - Use it alongside Spotify for a month, then cancel Spotify.
6. **Photos**
   - Self-hosted photos.
   - Encrypted, versioned backups: home PC, an offsite external HDD and an encrypted cloud copy.
   - Restore from a backup, then delete the photos from Google.

## Server (as set up on 2026-10-01)
- **Hardware:** ASUS ExpertBook B1502CBA laptop: i3-1215U (6 cores, Intel UHD with Quick Sync), 24 GB RAM, a single 512 GB NVMe SSD (the only M.2 slot), gigabit Ethernet. The battery doubles as a small UPS.
- **OS:** Ubuntu Server 26.04 LTS (`sudo` is `sudo-rs`). LVM, root volume extended to the whole disk, no disk encryption so it can reboot unattended. Security updates install automatically (`unattended-upgrades`, Ubuntu's default).
- **Laptop-as-server tweaks:**
  - Lid switch ignored: `/etc/systemd/logind.conf.d/lid.conf`.
  - `sleep`, `suspend`, `hibernate` and `hybrid-sleep` targets masked.
  - Battery charge capped at 80% by `battery-limit.service`, which writes `charge_control_end_threshold`.
  - Fixed LAN IP through a DHCP reservation on the router.
- **SSH:** OpenSSH, ed25519 keys only, one key per device (PC and laptop), in `~/.ssh/authorized_keys`. `/etc/ssh/sshd_config.d/01-hardening.conf` sets `PasswordAuthentication no`, `KbdInteractiveAuthentication no` and `PermitRootLogin no`. It's named `01-` because sshd keeps the first value it reads, so it wins over Ubuntu's `50-cloud-init.conf`. The fallback is the laptop's own screen and keyboard.
- **Tailscale:** on the server, PC, laptop and phone. MagicDNS is on, so SSH from anywhere uses the server's tailnet name. Key expiry is disabled for the server.
- **Firewall (UFW):** deny incoming and allow outgoing by default; allow 22/tcp from the home LAN; allow everything on `tailscale0`. Docker bypasses UFW, so deal with that when Docker arrives in step 5.
- **Network:** behind NAT (possibly CGNAT) with a dynamic public IP, so no port forwarding. Anything reaching the server goes through outbound tunnels: Tailscale for private access, Cloudflare Tunnel for public access. `tailscale netcheck` shows easy NAT (`MappingVariesByDestIP: false`) and working UDP, so Tailscale usually connects directly. No IPv6 and no UPnP. The nearest relay is Frankfurt.

## Open issues
- **Step 4, CORS:** the comment in `script.js` says to allow the origin `https://tilenserver.com`, but the site is served from `https://www.tilenserver.com`. The `Origin` header must match exactly, so allow the `www` origin (or both).
- **Step 6, storage:** there is about 1 TB of photos already, and the original plan left room for 2 TB, but the server has a single 512 GB SSD. It needs a bigger NVMe drive or an external drive on the USB-C 3.2 Gen 2 port.
