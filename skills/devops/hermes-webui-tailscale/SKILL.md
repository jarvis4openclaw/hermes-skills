---
name: hermes-webui-tailscale
description: "Install and run Hermes Web UI (nesquena/hermes-webui) accessible over Tailscale with password auth and systemd auto-start."
version: 1.1.0
author: Jarvis
metadata:
  hermes:
    trigger_conditions:
      - "hermes webui tailscale"
      - "run hermes webui over tailscale"
      - "hermes web ui accessible over tailscale"
      - "hermes webui tailscale setup"
      - "tailscale hermes web interface"
      - "hermes webui 0.0.0.0"
      - "hermes web ui password auth"
      - "hermes-webui systemd tailscale"
      - "access hermes webui from iphone"
      - "hermes web ui tailnet"
      - "hermes webui hermex"
      - "webui over tailnet"
      - "hermes web interface iphone"
---

# Hermes WebUI via Tailscale

## When to Use

- Deploying Hermes Web UI for the first time with Tailscale access
- Existing WebUI needs Tailscale exposure (was localhost-only)
- iPhone/Hermex can't connect to WebUI over tailnet
- WebUI authentication not working over Tailscale
- Migrating from manual WebUI startup to systemd auto-start
- Need to reconfigure host/port/password for Tailscale deployment
- Troubleshooting "WebUI unreachable" over Tailscale after reboot

## Not For

- **Setting up Hermes Web UI without Tailscale** → use `hermes-webui-setup` for general deployment (covers Tailscale too but less specific)
- **Public internet exposure** → only Tailscale-private access documented
- **Reverse proxying through Nginx/Caddy** → manual proxy config required
- **Installing Hermes Agent CLI** → use `hermes-agent` skill
- **Debugging the WebUI source code (React/Python)** → fork `nesquena/hermes-webui` upstream

## Setup Steps

1. **Clone** (or pull if already cloned):
   ```bash
   git clone https://github.com/nesquena/hermes-webui ~/hermes-webui
   cd ~/hermes-webui && pip install -r requirements.txt -q
   ```

2. **Generate password:**
   ```bash
   python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(24)))"
   ```

3. **Write `~/hermes-webui/.env`** — this is the authoritative source, sourced by bootstrap.py at startup and **overrides** systemd `Environment=` lines:
   ```
   HERMES_WEBUI_HOST=0.0.0.0
   HERMES_WEBUI_PORT=8787
   HERMES_WEBUI_PASSWORD=<your-password>
   ```

4. **Create systemd user service** at `~/.config/systemd/user/hermes-webui.service`:
   ```ini
   [Unit]
   Description=Hermes Web UI
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/home/<user>/hermes-webui
   ExecStart=/usr/bin/python3 /home/<user>/hermes-webui/bootstrap.py --host 0.0.0.0 --no-browser --foreground 8787
   Restart=on-failure
   RestartSec=5
   Environment=HERMES_WEBUI_HOST=0.0.0.0
   Environment=HERMES_WEBUI_PORT=8787
   Environment=HERMES_WEBUI_PASSWORD=<your-password>

   [Install]
   WantedBy=default.target
   ```

5. **Enable linger + start:**
   ```bash
   loginctl enable-linger $USER
   systemctl --user daemon-reload
   systemctl --user enable hermes-webui
   systemctl --user start hermes-webui
   ```

6. **Verify:**
   ```bash
   curl -s http://$(tailscale ip -4):8787/health
   curl -s -X POST http://$(tailscale ip -4):8787/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"password":"<your-password>"}' 
   # Should return {"ok": true}
   ```

## Pitfalls

- **`.env` overrides systemd `Environment=`** — `bootstrap.py` sources `~/hermes-webui/.env` at startup. If both exist and disagree, `.env` wins. Always update `.env` first; keep both in sync.
- **Rogue process blocks port** — if a previous agent session started the WebUI manually, it holds port 8787 and the systemd service crash-loops with `FATAL: Another server is already responding`. Find and kill it: `lsof -i :8787`, then `kill <pid>`, then `systemctl --user restart hermes-webui`.
- **Password cached in process** — `get_password_hash()` caches on first call. Changing `.env` requires a full service restart (`systemctl --user restart hermes-webui`), not just a reload.
- **Tailscale Serve not needed** — binding to `0.0.0.0` makes the server reachable on the Tailscale interface directly. Password auth must be confirmed active before doing this.

## Key File Locations

| File | Purpose |
|------|---------|
| `~/hermes-webui/.env` | **Primary** password/host/port config |
| `~/.config/systemd/user/hermes-webui.service` | Systemd unit (keep in sync with .env) |

## iPhone / Hermex Setup

1. Install Tailscale on iPhone, sign into tailnet
2. Hermex → Settings → Server URL: `http://<tailscale-ip>:8787`
3. Enter password when prompted

## Pitfalls

1. **`.env` overrides systemd `Environment=`** — `bootstrap.py` sources `~/hermes-webui/.env` at startup. If both exist and disagree, `.env` wins. Always update `.env` first; keep both in sync.

2. **Rogue process blocks port** — if a previous agent session started the WebUI manually, it holds port 8787 and the systemd service crash-loops with `FATAL: Another server is already responding`. Find and kill it: `lsof -i :8787`, then `kill <pid>`, then `systemctl --user restart hermes-webui`.

3. **Password cached in process** — `get_password_hash()` caches on first call. Changing `.env` requires a full service restart (`systemctl --user restart hermes-webui`), not just a reload.

4. **Tailscale Serve not needed** — binding to `0.0.0.0` makes the server reachable on the Tailscale interface directly. Password auth must be confirmed active before doing this.

5. **`pip install -r requirements.txt` installs to wrong Python.** If multiple Python versions are present, `pip` may point to Python 2 or a different venv. Use `python3 -m pip install -r requirements.txt` and verify with `python3 -c "import flask"` before starting.

6. **Health check returns 200 but WebUI is blank.** The `/health` endpoint may respond before the frontend assets finish serving. Give systemd 3–5 seconds after start, then reload the browser. If still blank, check `journalctl --user -u hermes-webui` for static asset errors.

7. **Port 8787 conflicts with another service.** Another local service (e.g., a dev server) may already own 8787. Change `HERMES_WEBUI_PORT` in both `.env` and the systemd `ExecStart` args — they must match or the service starts on the wrong port.

8. **systemd unit file uses wrong Python path.** `/usr/bin/python3` may not have the deps installed if the user uses pyenv/conda. Use the full path from `which python3` inside the active environment. Check: `systemctl --user cat hermes-webui | grep ExecStart`.

9. **Tailscale IP changes on reconnect.** The Tailscale IP is stable within a tailnet but may change if the device leaves and rejoins. Use `tailscale ip -4` dynamically; don't hardcode the IP in Hermex or browser bookmarks. Use the MagicDNS hostname (e.g. `hostname.tailnet-name.ts.net`) instead if available.

10. **Linger not enabled.** Without `loginctl enable-linger $USER`, the user systemd slice dies on SSH logout and the WebUI stops. This is the #1 reason "it worked but now it's down."

11. **`--foreground` missing from ExecStart.** Without `--foreground`, `bootstrap.py` spawns `server.py` as a detached child and exits — systemd sees the parent exit and restarts it, creating a loop. With `--foreground`, the server stays as PID 1 of the service.

12. **MagicDNS hostname not resolving.** If `hostname.tailnet-name.ts.net` doesn't resolve from iPhone, verify Tailscale MagicDNS is enabled in the tailnet admin console and the device has a MagicDNS name assigned.

