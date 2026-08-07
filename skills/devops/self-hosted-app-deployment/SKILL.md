---
name: self-hosted-app-deployment
description: Deploy a third-party GitHub repo as a self-hosted service. Use when asked to spin up, self-host, or fully install an unfamiliar repo on Proxmox LXC + Docker — includes the pre-flight review (hardcoded vendor URLs, missing data files, undeclared deps, broken compose).
version: 1.1.0
metadata:
  hermes:
    tags: [self-host, deploy, docker, proxmox, lxc, github]
    trigger_conditions:
      - "spin up"
      - "deploy this repo"
      - "self-host"
      - "get it fully installed"
      - "docker compose"
      - "deploy a github repo"
      - "third-party app deployment"
      - "evaluate / try out this app"
      - "self-hosted service"
      - "deploy on a container / CT"
---

# Self-Hosted App Deployment from a Third-Party Repo

Deploying an unfamiliar third-party repo as a self-hosted service. Applies to Proxmox LXC + Docker deployments (see `proxmox-host-management` for the PVE mechanics — this skill is the app-level review that precedes it).

## When to Use

- The user wants to deploy a third-party GitHub repo (especially a small solo project) as a self-hosted service on a Proxmox LXC or Docker host.
- The user asks to "spin up", "self-host", or "get fully installed" an unfamiliar app from source.
- A deployment fails at build/start and you need the systematic pre-flight review (hardcoded vendor URLs, missing data files, undeclared deps, broken compose).
- The user wants a throwaway evaluation CT with Docker for an app whose real mode needs an external daemon (LND node, Bitcoin Core, etc.) the homelab lacks.

## Not For

- Managing Proxmox CT/VM lifecycle mechanics (create, SSH, hardening) → use `proxmox-ssh-lifecycle` / `proxmox` first; this skill is the app-level review that feeds those steps.
- Day-2 operations of an already-deployed service (updates, backups, monitoring) → use `server-health` / `nas-management` style ops skills.
- Building a new app from scratch or writing compose files by hand without a repo → this skill is for reviewing and adapting an existing third-party repo.
- Starting a Start9 / Embassy service → use `startos` / `start-tunnel` instead.

## THE Core Lesson: Review the repo BEFORE deploying

Third-party repos, especially small solo projects, routinely ship in a state where the advertised install path **cannot work as-is**. The failures are not random — they cluster into predictable classes. Review every one of these before building:

### 1. Hardcoded vendor-host URLs (SECURITY + functionality)
- **`login.html` / frontend JS may hardcode the vendor's hosted domain** (e.g. `https://lcc.satslist.shop/`) for auth POSTs and post-login redirects.
- Left unpatched: **the user's login password is POSTed to the vendor's server**, and a successful login redirects away from your instance.
- Fix pattern:
  ```bash
  grep -rl "vendor.example.com" /path/to/app --include="*.html" --include="*.js" | while read f; do
    sed -i "s|https://vendor.example.com/|/|g" "$f"
  done
  grep -rn "vendor.example.com" /path/to/app --include="*.html" --include="*.js"  # confirm zero remain
  ```
- Also patch cosmetic display strings (`<span>vendor.example.com</span>`) — they're not links but still point at the vendor.
- **Rule of thumb:** if the app has a hosted demo, `grep -r` its domain across the whole repo and rewrite to root-relative before first boot.

### 2. Required-but-absent data files
- The app may `json.load(open("data.json"))` **unconditionally at import**, yet the file is not in the repo (gitignored or private). Without it, uvicorn/gunicorn crash-loops at boot with `FileNotFoundError`.
- **Find these with:** `grep -n "open(" *.py | grep -E "json|data|config"` and check the Dockerfile/`.dockerignore` — a `data.json` mount in compose that doesn't exist will also fail `docker compose up`.
- Reconstruct from the **live demo API** (`curl https://demo.example.com/api/<endpoint>`) — the response shapes ARE the file's schema. Read the API routes to learn which top-level keys the file must carry (e.g. `lcc_password`, `node`, `wallet`, `channels`).

### 3. Missing Python dependencies
- Module-level imports (`from dotenv import load_dotenv`, `from nostr_sdk import Keys`) are frequently **not declared in requirements.txt**.
- Container crash-loops with `ModuleNotFoundError`. Diagnosis: `docker logs <container> 2>&1 | tail -40` — the traceback names the module.
- Fix: add to requirements.txt (`python-dotenv`, `nostr-sdk`, etc.) and rebuild. Check PyPI for a manylinux wheel before assuming it'll build from source (`curl -s https://pypi.org/pypi/<pkg>/json`).

### 4. Broken docker-compose.yml
- `network_mode: host` combined with `ports:` is a conflict (compose errors).
- Compose mounting files that don't exist in the repo (`./data.json:...`) fails at `up`.
- Volumes referencing node paths (`~/.lnd:/root/.lnd:ro`) are presumptuous — drop them unless the app genuinely needs a node.
- Rewrite to minimal clean bridge networking:
  ```yaml
  services:
    app:
      build: .
      container_name: <name>
      restart: unless-stopped
      ports: ["8765:8765"]
      environment: [APP_MOCK=true]
  ```

### 5. Mock mode for evaluation
- If the app needs an external daemon (LND node, Bitcoin Core) the homelab lacks, run in mock mode (`LCC_MOCK=true` etc.) so the dashboard renders sample data. Document that real mode needs the node before wiring.

## Deployment Sequence (LXC + Docker)
1. `pct create <ctid>` with `--features nesting=1` (Docker requires it)
2. Bootstrap SSH keys + harden sshd (see `proxmox-ssh-lifecycle`)
3. Install Docker: `curl -fsSL https://get.docker.com | sh` (Engine + compose plugin)
4. `git clone` repo → apply the review fixes (above) → `docker compose up -d --build`
5. **Verify from outside the CT**: `curl http://<ip>:<port>/dashboard` → 200; exercise the login API; confirm wrong password rejected.

## Verification Checklist
- [ ] Zero hardcoded vendor URLs remain (`grep -r vendor.example.com` → none)
- [ ] Required data files exist on disk and are valid JSON
- [ ] All module-level imports present in requirements.txt
- [ ] Compose file builds and starts (no network_mode+ports conflict)
- [ ] HTTP 200 on the app root and dashboard from the LAN
- [ ] Auth endpoint: correct password → `{"authorized":true}`, wrong → `false`
- [ ] Container restart policy is `unless-stopped`

## Pitfalls
1. **A "working" demo at the vendor domain means nothing for your instance** — the demo's frontend and API are their deployment, not yours. Always localize the frontend URLs.
2. **Do not trust README/INSTALL.md commands blindly** — the one-command `install.sh` may do an interactive password prompt (blocks in SSH) and assume a node exists. The Docker path is cleaner for throwaway evaluation CTs.
3. **`docker compose up` succeeding ≠ app healthy** — check `docker ps` status; `Restarting (1)` means crash-loop. Always read `docker logs`.
4. **Verify auth locally, not just page load** — a 200 on `/dashboard` can hide a login page that posts to a dead remote endpoint.
5. **The demo API is a schema source, not a spec** — reconstructing `data.json` from live demo endpoints works, but demo response shapes can drift from what the code actually parses. Verify by launching the app and hitting the real endpoint, not just by eye-matching keys.
6. **Skipping the `grep` for hardcoded domains** — the vendor URL can hide in JS bundles, service workers, or `<meta>` tags, not just `login.html`. Run `grep -r` across the whole repo (including minified assets) and confirm zero matches remain before first boot.
7. **Missing deps that only surface at runtime** — `ModuleNotFoundError` in `docker logs` names the module, but some imports are conditional (only on certain code paths). Exercise the main flows (login, dashboard, an API call) before declaring the deploy done.
8. **`network_mode: host` + `ports:` is an instant compose error** — a copy-pasted compose from the vendor often carries this conflict. Rewrite to clean bridge networking with explicit ports and `restart: unless-stopped`.
9. **Forgetting `nesting=1` on the CT** — Docker inside an LXC fails with permission errors if `--features nesting=1` wasn't set at `pct create`. This is the #1 first-boot failure for LXC+Docker.
10. **Declaring victory from a single 200** — the verification checklist exists because a 200 on the root proves nothing about auth, data files, or external daemons. Walk the full checklist (auth endpoint, wrong-password rejection, LAN access, restart policy) before reporting success.

## References
- `references/lightning-control-center-deploy.md` — full worked example: LCC deploy on PVE CT 204 (missing data.json reconstruction, SatsList URL hardcoding, missing deps, broken compose).
