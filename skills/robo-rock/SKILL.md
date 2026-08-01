---
name: roborock
description: Control Roborock robot vacuums (status, clean, maps, consumables). Use when asked to vacuum, check vacuum status, control robot vacuum, or manage cleaning schedules. Triggers on vacuum, roborock, clean floor, hoover, robot cleaner keywords.
version: 1.1.0
metadata:
  clawdbot:
    emoji: "🧹"
    requires:
      bins: ["roborock"]
    install:
      - id: pipx
        kind: pipx
        package: python-roborock
        bins: ["roborock"]
        label: "Install roborock CLI (pipx)"
  hermes:
    tags: [roborock, vacuum, home-automation, robot]
    trigger_conditions:
      - "vacuum the house"
      - "check vacuum status"
      - "clean a specific room"
      - "return the vacuum to dock"
      - "roborock"
      - "clean floor"
      - "hoover"
      - "robot cleaner"
      - "vacuum consumables filter brush"
      - "when did the vacuum last clean"
      - "send vacuum home"
      - "vacuum map image"
---

# Roborock Vacuum Control

Control Roborock robot vacuums via the `roborock` CLI.

## When to Use

- User asks to vacuum (whole house or a specific room), check vacuum status, or return it to dock.
- Checking consumables (filter, brushes, sensors), volume, DND, or cleaning history.
- Pulling maps/room layout or generating a map image.
- Managing cleaning schedules or interacting with the robot interactively.

## Not For

- **Home Assistant automation for the same vacuum** → if the request is about HA entities/automations (e.g. `ha_list_entities` domain `vacuum`), use the Home Assistant tooling instead of the `roborock` CLI
- **Other robot vacuums (Roomba, Dreame, etc.)** → the `python-roborock` CLI only speaks Roborock/Xiaomi protocols
- **Controlling the vacuum from a phone app** → the CLI is for agent-side automation; the official app is for human manual control

## First-Time Setup

### 1. Install CLI
```bash
pipx install python-roborock
```

### 2. Login to Roborock Account
```bash
roborock login
```
Enter your Roborock/Xiaomi Home app email and password.

### 3. Find Your Device ID
```bash
roborock list-devices
```
Note your device ID (looks like `AbCdEf123456789XyZ`).

### 4. Store Device ID (Optional)
Add to your TOOLS.md for easy reference:
```markdown
## Roborock Vacuum
- **Device ID:** your-device-id-here
- **Model:** Roborock S7 Max Ultra (or your model)
```

## Quick Commands

All commands need `--device_id "YOUR_DEVICE_ID"` — replace with your actual device ID.

### Check Status
```bash
roborock status --device_id "YOUR_DEVICE_ID"
```

### Start Cleaning
```bash
roborock command --device_id "YOUR_DEVICE_ID" start
```

### Stop/Pause
```bash
roborock command --device_id "YOUR_DEVICE_ID" stop
roborock command --device_id "YOUR_DEVICE_ID" pause
```

### Return to Dock
```bash
roborock command --device_id "YOUR_DEVICE_ID" home
```

### Clean Specific Room
First get room IDs:
```bash
roborock rooms --device_id "YOUR_DEVICE_ID"
```
Then clean specific rooms:
```bash
roborock command --device_id "YOUR_DEVICE_ID" segment_clean --rooms 16,17
```

## Maintenance Commands

### Check Consumables
```bash
roborock consumables --device_id "YOUR_DEVICE_ID"
```
Shows filter, brush, sensor lifespans.

### Reset Consumable
```bash
roborock reset-consumable filter --device_id "YOUR_DEVICE_ID"
roborock reset-consumable main_brush --device_id "YOUR_DEVICE_ID"
roborock reset-consumable side_brush --device_id "YOUR_DEVICE_ID"
```

### Last Clean Record
```bash
roborock clean-record --device_id "YOUR_DEVICE_ID"
```

### Clean Summary (All Time)
```bash
roborock clean-summary --device_id "YOUR_DEVICE_ID"
```

## Maps & Rooms

### Get Maps
```bash
roborock maps --device_id "YOUR_DEVICE_ID"
```

### Cache Home Layout
```bash
roborock home
```

### Save Map Image
```bash
roborock map-image --device_id "YOUR_DEVICE_ID" --output /tmp/vacuum-map.png
```

### Room Features
```bash
roborock features --device_id "YOUR_DEVICE_ID"
```

## Settings

### Volume
```bash
roborock volume --device_id "YOUR_DEVICE_ID"
roborock set-volume 50 --device_id "YOUR_DEVICE_ID"
```

### Do Not Disturb
```bash
roborock dnd --device_id "YOUR_DEVICE_ID"
```

### LED Status
```bash
roborock led-status --device_id "YOUR_DEVICE_ID"
```

### Child Lock
```bash
roborock child-lock --device_id "YOUR_DEVICE_ID"
```

## Interactive Session
For multiple commands without repeating device ID:
```bash
roborock session --device_id "YOUR_DEVICE_ID"
```

## Troubleshooting

**Commands fail silently:**
1. Check login: `roborock login`
2. Use debug mode: `roborock -d status --device_id "YOUR_DEVICE_ID"`
3. Ensure vacuum is online and connected to WiFi

**"Device not found":**
- Run `roborock list-devices` to verify device ID
- Make sure you're logged into the correct Roborock account

**"Authentication failed":**
- Re-run `roborock login`
- Check you're using the same account as your Xiaomi Home / Roborock app

## Common Tasks

**"Vacuum the house":**
```bash
roborock command --device_id "YOUR_DEVICE_ID" start
```

**"Vacuum the kitchen":**
```bash
roborock rooms --device_id "YOUR_DEVICE_ID"  # find kitchen room ID
roborock command --device_id "YOUR_DEVICE_ID" segment_clean --rooms <kitchen_id>
```

**"Is the vacuum done?":**
```bash
roborock status --device_id "YOUR_DEVICE_ID"
```

**"Send vacuum home":**
```bash
roborock command --device_id "YOUR_DEVICE_ID" home
```

**"When did it last clean?":**
```bash
roborock clean-record --device_id "YOUR_DEVICE_ID"
```

**"Check brush/filter life":**
```bash
roborock consumables --device_id "YOUR_DEVICE_ID"
```

## Pitfalls

1. **Forgetting `--device_id` on every command** — The CLI requires `--device_id "YOUR_DEVICE_ID"`; omitting it fails or targets the wrong device. Recovery: copy the ID from `roborock list-devices` output and add it to every invocation (or use `roborock session` for interactivity).
2. **Commands fail silently with no output** — Usually a stale login or the robot being offline. Recovery: `roborock login` again, use `roborock -d status --device_id "YOUR_DEVICE_ID"` for debug, and confirm the vacuum is on WiFi.
3. **"Device not found" on a valid-looking ID** — The device ID is the long alphanumeric string from `list-devices`, not the model name or the app's short ID. Recovery: re-run `roborock list-devices` and paste the exact value.
4. **Authentication failed after an app password change** — Roborock accounts re-sync with the Xiaomi/Roborock app; changing the password invalidates the CLI session. Recovery: `roborock login` with the same account as the app.
5. **Room IDs guessed instead of fetched** — `segment_clean --rooms 16,17` uses numeric room IDs from the map, which are NOT sequential. Recovery: `roborock rooms --device_id "YOUR_DEVICE_ID"` to get real room IDs first.
6. **Clean-summary vs clean-record confusion** — `clean-record` gives the last clean; `clean-summary` aggregates all-time stats. Recovery: pick the right command for the question ("last clean" vs "total").
7. **No map cache → map-image fails** — `roborock map-image` needs a cached home layout. Recovery: run `roborock home` first to cache the layout, then `map-image`.

## Supported Models

Works with most Roborock vacuums including:
- Roborock S series (S4, S5, S6, S7, S8)
- Roborock Q series (Q5, Q7, Q8)
- Roborock E series
- Xiaomi Mi Robot Vacuum (Roborock-based)

## Credits

Uses the [python-roborock](https://github.com/humbertogontijo/python-roborock) library.
