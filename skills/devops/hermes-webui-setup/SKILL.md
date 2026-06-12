---
name: hermes-webui-setup
description: "Deploy Hermes Web UI as a persistent systemd user service accessible over Tailscale."
version: 1.1.0
author: Jarvis (agent-created)
tags: [hermes, webui, systemd, tailscale, deployment]
metadata:
  hermes:
    trigger_conditions:
      - "set up hermes webui"
      - "deploy hermes web ui"
      - "hermes webui not reachable"
      - "hermes webui down after reboot"
      - "configure tailscale for hermes webui"
      - "hermes web ui systemd service"
      - "webui password not working"
      - "hermes web interface setup"
      - "hermes-webui install"
      - "hermes webui systemd"
      - "hermes ui over tailscale"
      - "hermes webui 8787"
      - "hermes web portal setup"
---

# Hermes Web UI Setup

Deploy the Hermes Web UI (`github.com/nesquena/hermes-webui`) as a persistent
systemd user service, accessible over Tailscale from iPhone (Hermex or browser).

## When to Use

- Setting up Hermes Web UI for the first time
- Migrating WebUI to systemd from manual startup
- Configuring Tailscale-accessible WebUI bind
- Fixing "WebUI not reachable" after reboot or SSH logout
- Reconfiguring host/port/password for the WebUI service

## Not For

- **Installing Hermes Agent itself** → use `hermes-agent` skill for agent CLI setup
- **Reverse proxying the WebUI through Nginx/Caddy** → configure your proxy manually; this skill covers direct Tailscale access only
- **Accessing the WebUI on public internet** → only Tailscale-private access is documented here; public exposure is out of scope
- **OpenClaw or mission control web interfaces** → use `openclaw-config-management` for OpenClaw-specific UI
- **Troubleshooting the WebUI source code (React/Python)** → fork `nesquena/hermes-webui` and debug upstream

## Setup Overview

| Decision | What to do |
|----------|-------------|
| App type | **Python** — `bootstrap.py` → `server.py`. No Node.js, no npm. |
| Start command | `python3 bootstrap.py --host <HOST> --no-browser --foreground <PORT>` |
| Password | `HERMES_WEBUI_PASSWORD` env var |
| Host binding | `HERMES_WEBUI_HOST` (default `127.0.0.1`) |
| Port | `HERMES_WEBUI_PORT` (default `8787`) |
| Systemd | User service at `~/.config/systemd/user/hermes-webui.service` |

## Steps

### 1. Clone and install dependencies

```bash
git clone https://github.com/nesquena/hermes-webui ~/hermes-webui
cd ~/hermes-webui
pip install -r requirements.txt
```

### 2. Generate a password

```bash
python3 -c "import secrets, string; chars = string.ascii_letters + string.digits; print(''.join(secrets.choice(chars) for _ in range(24)))"
```

### 3. Create the systemd user service

Use the template at `templates/systemd-service.service` (pre-filled for this machine — adjust paths and password). Fill in:
- `WorkingDirectory` → absolute path to repo
- `ExecStart` → full python3 path + bootstrap.py with `--host <bind> --no-browser --foreground <port>`
- `Environment=HERMES_WEBUI_PASSWORD=<value>`
- Add `HERMES_WEBUI_HOST` and `HERMES_WEBUI_PORT` env vars matching ExecStart args

**Critical flags:**
- `--foreground` — keeps process in foreground so systemd can track it
- `--no-browser` — don't try to open a browser tab on the server

### 4. Enable linger and start

```bash
loginctl enable-linger $USER
systemctl --user daemon-reload
systemctl --user enable hermes-webui
systemctl --user start hermes-webui
```

Without `enable-linger`, the user slice terminates on SSH logout, killing the WebUI.

### 5. Verify health

```bash
TAILSCALE_IP=$(tailscale ip -4)
curl -s http://$TAILSCALE_IP:8787/health
# Expect: {"status": "ok", ...}
```

### 6. Tailscale access (no Cloudflare, no tunnels)

**If Tailscale Serve is enabled:** open firewall port on tailnet.

**If Tailscale Serve is NOT enabled** (most common): bind to `0.0.0.0` instead of `127.0.0.1` so the server listens on the Tailscale interface (`tailscale0`). The tailnet IP is already routable between devices.

**Never expose without auth.** The server blocks this: if `HOST != localhost` and no password is set, it prints a warning and start.sh refuses. Set `HERMES_WEBUI_PASSWORD` before binding to `0.0.0.0`.

## iPhone Setup

1. Install Tailscale from the App Store, sign into your tailnet
2. Open Hermex → Settings → Server URL → `http://<TAILSCALE_IP>:8787`
3. Enter the password when prompted

Or use Safari directly: `http://<TAILSCALE_IP>:8787`

## Management

```bash
systemctl --user status hermes-webui   # Check status
systemctl --user restart hermes-webui  # Restart after config changes
journalctl --user -u hermes-webui -f   # Tail logs
```

To run a full post-deploy verification (process owner, health, auth status, systemd state):

```bash
bash ~/.hermes/skills/devops/hermes-webui-setup/scripts/verify-auth.sh
```

See `scripts/verify-auth.sh` for the full script.

## Pitfalls

1. **It's Python, not Node.js.** The repo has `package.json` for linting only. The server is `server.py` + `bootstrap.py`. Don't try `npm install` or `npm start`.

2. **Secret redaction in terminal output.** Some shell/agent tooling redacts passwords in stdout. Don't assume the file is corrupted — verify with Python: check password length and prefix/suffix in the service file.

3. **Linger is mandatory.** Without `loginctl enable-linger`, the user systemd slice dies on SSH logout and the WebUI stops. This is the #1 reason "it worked but now it's down."

4. **`--foreground` is mandatory under systemd.** Without it, `bootstrap.py` spawns `server.py` as a detached child and exits — systemd sees the parent exit and restarts it, creating a loop. With `--foreground`, the server stays as PID 1 of the service.

5. **Password auth overrides settings password.** `HERMES_WEBUI_PASSWORD` env var takes precedence over any password set via the WebUI settings page. If the user changes it in settings, it won't stick across restarts while the env var is set — move it to settings first, then remove the env var.

6. **Check Tailscale connectivity first.** If health check fails, verify `tailscale ip -4` returns an IP and `tailscale status` shows the node as connected.

7. **Rogue WebUI process from a prior agent session.** Previous Hermes agent runs may have spawned a `server.py` directly (not via systemd) that still owns the port. The systemd service will fail with `FATAL: Another server is already responding on 127.0.0.1:8787`. Kill it:

```bash
lsof -i :8787              # Find the rogue PID
kill <PID>                  # Kill it
systemctl --user restart hermes-webui  # Let systemd take over
```

8. **"Invalid password" even with correct env var.** If another process is already listening on that port, you're hitting the *wrong server* — not the systemd one. Always verify with `lsof -i :8787` which process owns the port, and check its env with `cat /proc/<PID>/environ | tr '\0' '\n' | grep HERMES_WEBUI_PASSWORD` to confirm what password that process was started with. If it's a stale process from a prior session, kill it and let systemd restart.

9. **`pip install -r requirements.txt` installs to wrong Python.** If multiple Python versions are present, `pip` may point to Python 2 or a different venv. Use `python3 -m pip install -r requirements.txt` and verify with `python3 -c "import flask"` (or whichever dep) before starting.

10. **Health check returns 200 but WebUI is blank.** The `/health` endpoint may respond before the frontend assets finish serving. Give systemd 3–5 seconds after start, then reload the browser. If still blank, check `journalctl --user -u hermes-webui` for static asset errors.

11. **Port 8787 conflicts with another service.** Another local service (e.g., a dev server) may already own 8787. Change `HERMES_WEBUI_PORT` in both `.env` and the systemd `ExecStart` args — they must match or the service starts on the wrong port.

12. **systemd unit file uses wrong Python path.** `/usr/bin/python3` may not have the deps installed if the user uses pyenv/conda. Use the full path from `which python3` inside the active environment. Check: `systemctl --user cat hermes-webui | grep ExecStart`.

13. **Tailscale IP changes on reconnect.** The Tailscale IP is stable within a tailnet but may change if the device leaves and rejoins. Use `tailscale ip -4` dynamically; don't hardcode the IP in Hermex or browser bookmarks. Use the MagicDNS hostname (e.g. `hostname.tailnet-name.ts.net`) instead if available.

