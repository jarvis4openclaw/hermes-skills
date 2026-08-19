---
name: findmy
description: "Track Apple devices/AirTags via FindMy.app on macOS."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [FindMy, AirTag, location, tracking, macOS, Apple]
    trigger_conditions:
      - "where is my device"
      - "find my iPhone"
      - "track my AirTag"
      - "where are my keys"
      - "find my cat"
      - "device location"
      - "AirTag patrol route"
      - "check AirPods location"
      - "track my bag"
      - "FindMy app"
      - "lost device find"
      - "monitor item movement"
---

# Find My (Apple)

Track Apple devices and AirTags via the FindMy.app on macOS. Since Apple doesn't
provide a CLI for FindMy, this skill uses AppleScript to open the app and
screen capture to read device locations.

## Prerequisites

- **macOS** with Find My app and iCloud signed in
- Devices/AirTags already registered in Find My
- Screen Recording permission for terminal (System Settings → Privacy → Screen Recording)
- **Optional but recommended**: Install `peekaboo` for better UI automation:
  `brew install steipete/tap/peekaboo`

## When to Use

- User asks "where is my [device/cat/keys/bag]?"
- Tracking AirTag locations
- Checking device locations (iPhone, iPad, Mac, AirPods)
- Monitoring pet or item movement over time (AirTag patrol routes)

## Not For

- **Android / Google Find My Device** — different platform, different tooling → use Google's Find My Device web UI.
- **Tile / Samsung SmartThings trackers** — FindMy.app only shows Apple-registered devices → use the vendor's own app.
- **Historical location analytics** — FindMy only shows current location, not history → log screenshots over time via cron and compile the route yourself.
- **Locating a lost device that is offline** — if the device hasn't reported in, FindMy shows the last-known location, not live → tell the user it's last-known and suggest Play Sound.

## Method 1: AppleScript + Screenshot (Basic)

### Open FindMy and Navigate

```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'

# Wait for it to load
sleep 3

# Take a screenshot of the Find My window
screencapture -w -o /tmp/findmy.png
```

Then use `vision_analyze` to read the screenshot:
```
vision_analyze(image_url="/tmp/findmy.png", question="What devices/items are shown and what are their locations?")
```

### Switch Between Tabs

```bash
# Switch to Devices tab
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Devices" of toolbar 1 of window 1
    end tell
end tell'

# Switch to Items tab (AirTags)
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
```

## Method 2: Peekaboo UI Automation (Recommended)

If `peekaboo` is installed, use it for more reliable UI interaction:

```bash
# Open Find My
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Capture and annotate the UI
peekaboo see --app "FindMy" --annotate --path /tmp/findmy-ui.png

# Click on a specific device/item by element ID
peekaboo click --on B3 --app "FindMy"

# Capture the detail view
peekaboo image --app "FindMy" --path /tmp/findmy-detail.png
```

Then analyze with vision:
```
vision_analyze(image_url="/tmp/findmy-detail.png", question="What is the location shown for this device/item? Include address and coordinates if visible.")
```

## Workflow: Track AirTag Location Over Time

For monitoring an AirTag (e.g., tracking a cat's patrol route):

```bash
# 1. Open FindMy to Items tab
osascript -e 'tell application "FindMy" to activate'
sleep 3

# 2. Click on the AirTag item (stay on page — AirTag only updates when page is open)

# 3. Periodically capture location
while true; do
    screencapture -w -o /tmp/findmy-$(date +%H%M%S).png
    sleep 300  # Every 5 minutes
done
```

Analyze each screenshot with vision to extract coordinates, then compile a route.

## Limitations

- FindMy has **no CLI or API** — must use UI automation
- AirTags only update location while the FindMy page is actively displayed
- Location accuracy depends on nearby Apple devices in the FindMy network
- Screen Recording permission required for screenshots
- AppleScript UI automation may break across macOS versions

## Pitfalls

1. **AirTag location goes stale when the window is minimized** — AirTags only update while the FindMy page is actively displayed. Recovery: keep FindMy foreground during tracking (see Rules), and note the "last updated" timestamp.
2. **Screenshot capture without Screen Recording permission** — `screencapture` silently captures the desktop wallpaper or nothing when the terminal lacks Screen Recording permission. Recovery: System Settings → Privacy & Security → Screen Recording, grant the terminal, restart it.
3. **Reading pixels instead of using vision_analyze** — trying to parse the screenshot with image libraries is slow and error-prone. Recovery: pass the PNG to `vision_analyze` and ask for device names + locations.
4. **AirTag missing from Items tab** — the item may be on a different tab, or the app hasn't refreshed. Recovery: switch to the Items tab, wait, re-capture; if still absent, check the FindMy app directly.
5. **Cron tracking loop without keeping the page open** — a background loop that captures while FindMy is minimized gets stale data. Recovery: the loop must keep the app foregrounded (or accept last-known locations).
6. **Locating an offline device and reporting it as live** — FindMy shows last-known when the device is offline. Recovery: say "last seen <time>" and suggest Play Sound / Notify When Found.

## Rules

1. Keep FindMy app in the foreground when tracking AirTags (updates stop when minimized)
2. Use `vision_analyze` to read screenshot content — don't try to parse pixels
3. For ongoing tracking, use a cronjob to periodically capture and log locations
4. Respect privacy — only track devices/items the user owns
