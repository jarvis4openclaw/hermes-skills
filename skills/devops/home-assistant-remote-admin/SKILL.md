---
name: home-assistant-remote-admin
description: "Manage HA dashboards, HACS, Alarmo, automations headlessly."
version: 1.1.0
metadata:
  hermes:
    tags: [home-assistant, lovelace, hacs, alarmo, websocket]
    trigger_conditions:
      - "home assistant dashboard"
      - "clone lovelace"
      - "hacs install"
      - "alarmo config"
      - "ha automation edit"
      - "ha websocket"
      - "lovelace resources"
      - "hacs repository download"
      - "home assistant alarm test"
      - "automation trace ha"
      - "add camera to home assistant"
      - "home assistant logbook"
---

# Home Assistant Remote Admin (headless)

Wahid's HA: `HASS_URL` + `HASS_TOKEN` in `~/.hermes/.env` (instance 192.168.200.20:8123). Helper scripts live at `/home/wahid/ha-dashboard-project/ha_ws.py` (websocket) and `ha_rest.py` (REST POST/DELETE). Reusable anywhere.

## When to Use
- User asks to create, edit, clone, or back up a Lovelace dashboard (including named dashboards like `lovelace-office`).
- User wants to install or update a HACS plugin/custom card and register its JS resources.
- User needs to change an HA automation or script (edit, create, reload, debug via traces/logbook).
- User wants to arm/disarm/test an Alarmo alarm or modify alarm sensors/automations/areas.
- User needs to add a new integration camera headlessly via config flow (rroller, dahua, Amcrest AD410, etc.).
- User reports a dashboard, automation, or alarm behaving incorrectly and asks to inspect HA state.

## Not For
- **Setting up Home Assistant from scratch or configuring the host OS** → use `home-assistant-setup` instead (if present) or the official HA docs.
- **Interacting with Zigbee/Z-Wave devices, pairing, or device-specific firmware** → use `home-assistant-device-integrations` instead (or the HA docs).
- **Advanced YAML-mode Lovelace templating or Jinja2 debugging** → use `home-assistant-yaml-mode` instead (or the HA templating docs).
- **Energy monitoring / power usage analytics** → use `home-assistant-energy` instead (or the HA energy dashboard docs).

## Connection
- Websocket: `ws://<host>/api/websocket`, auth with `{"type":"auth","access_token":TOKEN}` after `auth_required`. Python `websockets` lib is preinstalled system-wide.
- The built-in `ha_*` Hermes tools only cover get_states/call_service. Dashboards, resources, traces, HACS, and Alarmo need raw websocket/REST.

## Lovelace dashboards (storage mode)
```python
{'type':'lovelace/config'}                                  # default Overview dashboard
{'type':'lovelace/config', 'url_path':'lovelace-office'}     # named dashboard
{'type':'lovelace/dashboards/list'}                         # NOTE plural /list; bare 'lovelace/dashboards' = unknown_command
{'type':'lovelace/dashboards/create', 'url_path':..., 'title':..., 'icon':'mdi:...', 'show_in_sidebar':True}
{'type':'lovelace/config/save', 'url_path':..., 'config':{...}}   # full overwrite
{'type':'lovelace/resources'}                                # custom card JS registrations
```
Clone recipe: GET config → write to local JSON backup → `dashboards/create` → `config/save`. Always read back and diff view count.

## Config gotchas
- Dashboard/view JSON is **pure JSON** — Jinja templates are plain strings, no `{% raw %}` wrappers (those are only for YAML mode).
- Sections views: `"type":"sections"`, sections are `{"type":"grid","cards":[...]}`, inner grids use `"columns":2,"square":false`.
- Entity audit before save: regex all `entity/entity_id` values out of the config and check against `get_states`.

## Installing HACS plugins programmatically
```
{'type':'hacs/repositories/list'}                # full catalog w/ ids + installed flags
{'type':'hacs/repository/download', 'repository': <numeric id>}   # SINGULAR repository
```
Download auto-registers `/hacsfiles/<name>/...` in lovelace resources (~5s). Verify by fetching the resource URL with the Bearer token → expect 200.

## Editing automations/scripts (REST, not websocket)
- `GET  /api/config/automation/config/<numeric_id>` (the `id:` field inside the automation, NOT entity_id; websocket `config/automation/config` is unknown_command on 2026.x)
- `POST same URL` with full config body → 200 `{result: ok}`. Creating new: still needs an unused numeric id in the path (bare trailing-slash path 404s).
- Modern trigger key is `triggers`; GET returns modern shape, POST accepts it back verbatim.
- After writes: `POST /api/services/automation/reload`.
- Debug a run via ws: `{'type':'trace/list','domain':'automation','item_id':'automation.xxx'}` then `trace/get` with run_id (empty list is normal for fast state-trigger automations — use logbook instead). Logbook: `GET /api/logbook/<ISO time>`.

## Alarmo (v1.10.x)
- Reads are websocket (`alarmo/config|areas|sensors|automations|entities`). Writes are **HTTP POST**: `/api/alarmo/sensors`, `/api/alarmo/automations`, `/api/alarmo/config` — each takes the full entry dict; sensor entries need `entity_id` + fields (`type`,`modes`,`use_entry_delay`,`enabled`,`area`,...); add `"remove": true` to delete.
- Sensor create/update via POST works reliably. **`type:"action"` automations created via POST silently fail to persist** (only notification type survives) — implement siren/light responses as regular HA automations triggering on `alarm_control_panel.<area>` state → `triggered` instead.
- Notification automations support wildcards: `{{open_sensors}}`, `{{open_sensors|format=short}}`, `{{bypassed_sensors}}`, `{{arm_mode}}`, `{{delay}}`, `{{changed_by}}`.

## Adding an integration camera via config flow (programmatic)
`POST /api/config/config_entries/flow {"handler":"<domain>"}` → returns `flow_id` + `step_id`; POST each step's fields to `/api/config/config_entries/flow/<flow_id>` until `type=="create_entry"`. Works headlessly (used for rroller/dahua). Amcrest AD410 doorbell: stripped firmware — CGI mostly "Invalid Authority", no ONVIF, RTSP user = local device admin (NOT the Amcrest Smart Home cloud/app login); working URL `rtsp://admin:<localpass>@<ip>/cam/realmonitor?channel=1&subtype=0&authbasic=64`. An empty config entry (`data == {}`, `created_at == modified_at`) is a half-finished add — its entities 500 on camera_proxy; fix by completing the flow, migrating dependent automations/dashboard refs to the NEW entity ids, then DELETE the husk entry. Old Konnected→ESPHome leftovers: delete the `not_loaded` legacy entry once nothing references it.

## Testing an alarm safely
1. Arm away → expect `arming` + exit beeper; disarm within exit window → `disarmed`.
2. Actuate siren switch directly for ~1s blip, force off.
3. Full chain: call `alarm_control_panel.alarm_trigger` on the panel, wait ~8s, verify siren/lights via states AND logbook (states may catch strobe mid-off-phase), then disarm and verify silence. Expect real noise during step 3.

## Pitfalls
1. **execute_code sandbox lacks project modules** — The sandbox has no `bash` and no `/home/wahid/ha-dashboard-project` on sys.path, so `ha_ws.py`/`ha_rest.py` imports fail with ModuleNotFoundError. Recovery: `sys.path.insert(0,'/home/wahid/ha-dashboard-project')` before importing, or run the helper via `terminal()` instead of `execute_code`.
2. **web_search provider misconfigured** — `web_search` may fail with 'brave' unregistered. Recovery: use `mcp__hound__mcp_smart_search` / `mcp__hound__mcp_smart_fetch` for lookups instead of the built-in web_search tool.
3. **Alarmo ghost entries after Konnected→ESPHome migration** — The old integration leaves a `not_loaded` config entry plus an orphan `alarm_control_panel` entity with NO registry entry; automations targeting it fail silently. Recovery: audit `entity_registry` vs `device_registry`, remove the husk entry, and repoint automations to the new entity ids.
4. **HA 400 on automation POST without error detail** — Usually a transient/voluptuous quirk rather than a real schema error. Recovery: retry the POST once before dissecting the payload.
5. **`lovelace/dashboards` (no /list) returns unknown_command** — The endpoint is plural `/list`; the bare `lovelace/dashboards` message is rejected. Recovery: always use `{'type':'lovelace/dashboards/list'}`.
6. **Alarmo `type:"action"` automations silently fail to persist** — POST to `/api/alarmo/automations` returns success but the action automation is gone on reload; only notification-type survives. Recovery: implement siren/light responses as regular HA automations triggered on `alarm_control_panel.<area>` state → `triggered`.
7. **Empty config entry = half-finished camera add** — An entry with `data == {}` and `created_at == modified_at` has entities that 500 on camera_proxy. Recovery: complete the config flow, migrate dependent automations/dashboard refs to the NEW entity ids, then DELETE the husk entry.
8. **Amcrest AD410 credentials mismatch** — RTSP uses the local device admin account (NOT the Amcrest Smart Home cloud/app login), and CGI is mostly "Invalid Authority" (stripped firmware). Recovery: use `rtsp://admin:<localpass>@<ip>/cam/realmonitor?channel=1&subtype=0&authbasic=64`.
9. **States may miss strobe mid-off-phase during alarm test** — Reading `get_states` right after triggering may show the siren off because the strobe is in its off phase. Recovery: verify via states AND logbook (`GET /api/logbook/<ISO time>`) before declaring the test failed.
