---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Obsidian, Notes, Vault, Markdown, Knowledge Base]
    trigger_conditions:
      - "read my obsidian note"
      - "search obsidian vault"
      - "create a note in obsidian"
      - "edit obsidian note"
      - "list obsidian notes"
      - "append to obsidian note"
      - "obsidian wikilink"
      - "find note in vault"
      - "open vault"
      - "create daily note"
      - "update my note"
      - "what's in my vault"
      - "search my notes for"
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## When to Use

- Reading a specific note by name or path from the vault
- Searching vault content by keyword or regex across all notes
- Creating new notes with full markdown content
- Appending content to the end of an existing note
- Making targeted inline edits (replace a paragraph, update a link)
- Creating and maintaining [[wikilinks]] between related notes
- Listing all notes in a subfolder for navigation
- Daily note creation with templated content

## Not For

- **Obsidian plugin management** → use Obsidian UI settings pane, not filesystem
- **Syncing vault across devices** → use Obsidian Sync or git, not this skill
- **Obsidian graph view / visual features** → these are UI-only, not available via filesystem
- **Canvas files (.canvas)** → these are JSON-based and this skill focuses on markdown
- **Exporting to PDF/HTML** → use Obsidian's built-in export or Pandoc
- **Note-taking in other apps (Notion, Bear, Logseq)** → use `notion`, `obsidian` (Bear/Logseq not yet skilled)

## Pitfalls

1. **OBSIDIAN_VAULT_PATH not set** — file tools fail with "file not found" because the agent resolves to the wrong directory. Fix: set `OBSIDIAN_VAULT_PATH=/absolute/path/to/vault` in `${HERMES_HOME:-~/.hermes}/.env`. Verify with `test -d "$OBSIDIAN_VAULT_PATH" && echo "OK"`.

2. **Shell variable in file tool path** — `read_file("$OBSIDIAN_VAULT_PATH/note.md")` fails because Hermes file tools don't expand shell variables. Fix: resolve the path first via terminal: `echo "$OBSIDIAN_VAULT_PATH/note.md"`, then pass the concrete path to `read_file`.

3. **Vault path contains spaces** — `read_file("/home/user/My Obsidian Vault/note.md")` may fail on some tool backends. Fix: no escaping needed for Hermes file tools (they handle spaces natively), but always resolve the path first. If it fails, use terminal as fallback.

4. **Wikilink to non-existent note** — `[[New Note]]` creates a broken link if the target note doesn't exist. Fix: check with `search_files(target="files", pattern="New Note.md")` before linking, or create the target note first.

5. **search_files with wrong target** — Using `target="content"` when you meant `target="files"` returns no matches or wrong results. Fix: use `target="files"` for filename searches, `target="content"` for text search within files.

6. **File glob missing for content search** — `search_files(target="content", pattern="TODO")` searches all files including `.obsidian/` config files. Fix: add `file_glob="*.md"` to restrict to markdown notes only.

7. **write_file overwrites without warning** — Creating a note at an existing path silently replaces the file. Fix: read the file first with `read_file` to confirm it doesn't exist or to merge content.

8. **patch anchor mismatch after previous edits** — If you edited the note earlier in the session, the anchor string you memorized may no longer match. Fix: always re-read the note with `read_file` immediately before `patch` to get current anchor text.

9. **Daily note template doesn't exist** — Trying to create a daily note without a template produces an empty file. Fix: read yesterday's daily note as a template, or create a minimal template with `## Tasks\n- [ ] ` and `## Notes`.

10. **Large vault performance** — `search_files(target="content", pattern=".")` on a vault with 10,000+ notes times out or returns partial results. Fix: narrow with `file_glob` or search a subfolder path.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `${HERMES_HOME:-~/.hermes}/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.
