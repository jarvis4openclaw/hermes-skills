# Systemd User Service for Python Dashboards

Pattern for running Python-based dashboard/HTTP servers as user-level systemd services.

## When to Use
- You have a Python HTTP server (or any long-running process) that should:
  - Start automatically on boot
  - Restart on failure
  - Run without a logged-in TTY

## Service File Template

Create `~/.config/systemd/user/<service-name>.service`:

```ini
[Unit]
Description=<Service Description>
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/working/dir
ExecStart=/usr/bin/python3 -m <module>
Restart=on-failure
RestartSec=5
Environment=HERMES_HOME=/home/wahid/.hermes

[Install]
WantedBy=default.target
```

## Commands

```bash
# After creating/editing the service file:
systemctl --user daemon-reload
systemctl --user enable <service-name>
systemctl --user start <service-name>

# Check status:
systemctl --user status <service-name>

# View logs:
journalctl --user -u <service-name> -f

# Stop/restart:
systemctl --user stop <service-name>
systemctl --user restart <service-name>
```

## Key Points
- **User-level services** don't need `sudo` — they run as the user and survive logout (if linger is enabled: `sudo loginctl enable-linger $USER`)
- **`Restart=on-failure`** handles crashes; `RestartSec=5` prevents tight restart loops
- **`After=network.target`** ensures network is available before starting
- Use `ExecStart=/usr/bin/python3 -m <module>` for Python packages with a `__main__.py`
- Add `Environment=` lines for any env vars the service needs
- **No `User=` or `Group=` needed** in user-level services — they run as the invoking user

## Real Example: Mnemosyne Dashboard
See `~/.config/systemd/user/mnemosyne-dashboard.service` — serves the Mnemosyne memory dashboard at `http://192.168.100.52:8765`.
