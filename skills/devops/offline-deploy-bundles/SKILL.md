---
name: offline-deploy-bundles
description: Use when a deploy is a bundled handoff, not a push.
version: 1.1.0
category: devops
metadata:
  hermes:
    tags: [deploy, bundle, static-site, plesk, ftp, upload, verification, privacy]
    trigger_conditions:
      - 'build me a deploy zip'
      - 'give me the scp command for the bundle'
      - 'update the live site (upload / file manager / FTP)'
      - 'Plesk or shared hosting deploy'
      - 'offline / USB / air-gapped deploy'
      - 'the host must not be touched from this machine'
      - 'prove the upload landed'
      - 'checklist to ship with the bundle'
      - 'hand the deploy over to the operator'
      - 'build a zip for someone else to upload'
      - 'the site is on shared hosting with no ssh'
      - 'air-gapped or usb-stick deploy'
      - 'verify an upload landed on a third-party host'
---

# Offline / Uploaded Deploy Bundles

For deploys that are **packaged and handed over** rather than pushed: no CI to query, no deploy API, and
usually a host the agent is told not to touch. The failure modes are all about the *artifact* — what it
carries, what it leaks, and whether anyone can tell it arrived.

Use it when the host is unreachable by policy (privacy product, third-party VPS the owner administers) or
has no SSH/deploy API: static hosting behind a file manager, FTP, Plesk, a USB stick. Also whenever the
user asks for "a zip I can upload", "the scp command", or "something to update the live site".

## When to Use

- The deploy is a **bundled handoff** the user uploads themselves — they ask for "a zip I can
  upload", "the scp command for the bundle", or "something to update the live site".
- The target is **static hosting behind a file manager, FTP, or Plesk** — no CI to query, no deploy API.
- The host is **unreachable by policy** (privacy product, third-party VPS the owner administers) or
  **air-gapped / offline** (USB stick, physically transported media).
- You must ship a **checklist** so the operator can prove the upload landed.
- A bundle needs an **identity/secret gate** so nothing private leaves this machine.
- A previous bundle needs a **rebuild + re-stamp**, and the doc of record kept in sync.

## Not For

- Hosts with a deploy API or a git-connected build → use `render-deploy` plus
  `static-site-deploy-verify` instead (build status, production branch, CDN staleness).
- Copying individual files to a host you *can* reach over SSH → use `ssh-file-deploy` instead.
- Running or administering a service on infrastructure you own → use `self-hosted-app-deployment` instead.
- Setting up the origin/proxy in front of a static site → use `caddy-proxy-management` instead.
- Diagnosing why a live static site serves stale or missing files → use `static-site-deploy-verify` instead.
- Publishing a temporary public preview of a static bundle → use `cloudflare-temp-accounts` instead.

## Procedure

### 1. Decide what ships — the host serves everything it can see

Ship the **served tree** plus, at most: an origin server script if the host can run one, and a checklist
for the operator. Never ship source, docs, tests, `.git`, dependency trees, or the recovery/secret kit.
A file merely present in the web root is a URL whether or not anything links to it.

### 2. Build it with a script, never by hand

Hand-built archives drift and cannot be re-checked. Keep a builder in the repo (starter:
`templates/build-deploy-bundle.py`) that:

- **identity-gates every shipped file** — scan each file binary-safe for the owner's name, repo/host/CT
  names, internal and public IPs, and DNS/hosting providers; **abort the build** on a hit. A manual grep
  happens only when someone remembers. When infrastructure moves, deleting a marker is a decision.
- **stamps the build** — write the hash (md5/sha256) of every served bundle into a file that ships *with*
  the bundle, so step 6 has something to compare against without reading it off a build log in chat.
- **archives the previous artifact** as `…-<date>.zip`, keeping "which build is on the host" answerable.
- prints a manifest: file count, size, hashes, and an explicit assertion that no private path is included.

### 3. Keep the served root nested — and say so where the extraction happens

A bundle shaped `public/… + server.py + checklist` is the safe shape: unpacking it *at* the web root would
publish the server script and the checklist as pages. That means the operator must extract the **contents
of `public/`** into the web root, so the checklist has to say it, at the extraction step, in those words —
name the trap ("do not unpack `public/`, `deploy/` and `server.py` straight into `httpdocs/`") rather than
expecting it to be inferred.

### 4. Explain the update shape: full replacement, not a patch

Say plainly that the bundle replaces the site. The operator keeps host-local config (an `.htaccess`, a
vhost snippet) unless the bundle explicitly ships a new one — and if it does, name the file and where it
goes (`deploy/htaccess-for-httpdocs.txt` → `httpdocs/.htaccess`).

### 5. Hand it over with the fetch command for THEIR machine

Deliver the file itself *and* the command that pulls it, using the SSH config **alias** for this machine
(e.g. `scp <alias>:/home/<user>/site-deploy.zip .`) — offer the raw-IP form only as a fallback for a
client that lacks the alias. A path on this host is useless to a user sitting somewhere else.

### 6. Verify before handoff, and give the operator a post-upload check

Your side: extract the finished archive to scratch and prove the served tree is byte-identical to the
repo build (`diff -r`), that those hashes equal both the stamp and what the staging origin serves, and
that the checklist's stamp is the *current* one — not last build's.

Their side (in the checklist's AFTER section):

```
md5sum httpdocs/v2/app.js   -> <hash stamped at build time>
md5sum httpdocs/app.js      -> <hash stamped at build time>
```

A mismatch is a stale or partial upload, not a cache. Never let "the page looks right" stand in for this,
and when a bundle is requested with a cache-buster (`/app.js?v=N`), a bundle change must bump `N` or
cached clients keep the old file.

### 7. Keep the doc of record in sync

These deploys have a wiki page or a checklist that *is* the procedure for the next person. When the
shipped set, the builder, or the host changes, update it in the same pass — a checklist that still names
a registrar the domain no longer uses, or omits config files it now ships, is worse than none.

## Pitfalls

1. **A human grep is not a gate.** Make the build fail on an identity/secret marker; a leak in a bundle is
   on a third party's disk, where removing it is someone else's afternoon.
2. **Stale stamp.** Rebuilds reuse the same filename — copy the stamp into the checklist at *build* time
   and re-verify the extracted archive, or the operator verifies successfully against the wrong build.
3. **Extraction nesting.** Unpacking the archive at the web root publishes the server script and the
   checklist. Keep the served root nested in the archive; the checklist says which directory's contents
   go where.
4. **Publish-style leaks.** Never place a bundle, its source, or a git bundle of it inside a directory
   that is itself backed up to a public repository. An artifact destined for a third-party host must be
   clean *before* it leaves this machine.
5. **Hashing the wrong thing.** Compare the *served* bundle's hash — not a directory listing, not a
   timestamp, not the upload tool's "transfer complete". An interrupted extraction leaves the old file in
   place while every UI signal still says success.
6. **Zip member permissions.** Members written programmatically default to `0600` and extract unreadable
   by the webserver user. Set `0644` on generated members.
7. **Verify the artifact against a second path, not just itself.** Re-derive at least one shipped value
   independently (a second tool, the staging origin, the engine that produced it) — an archive that only
   agrees with the script that wrote it proves nothing about what a browser or a host will do with it.

## Verification Checklist

- [ ] Builder ran (not a hand-made archive) and reported zero identity-marker hits
- [ ] Manifest confirms: no `src/`, `docs/`, `.git`, dependency tree, or recovery kit inside
- [ ] Extracted served tree is `diff -r`-identical to the build, and its hashes equal the staging origin
- [ ] Checklist stamp equals the hashes of the bundles in *this* archive
- [ ] Checklist states the extraction target explicitly (contents of the served dir → web root)
- [ ] Fetch command given, using this machine's SSH alias, with the raw-IP fallback noted
- [ ] Wiki/checklist doc of record updated for anything the bundle now carries
