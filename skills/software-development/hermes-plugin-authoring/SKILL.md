---
name: hermes-plugin-authoring
description: "Use when writing a native Hermes plugin: hooks, commands."
version: 1.1.0
metadata:
  hermes:
    tags: [hermes, plugin, hooks, ctx-api, authoring]
    related_skills: [hermes-core-architecture, hermes-config-management]
    trigger_conditions:
      - "write a Hermes plugin"
      - "plugin.yaml / register(ctx)"
      - "Hermes plugin hook not firing"
      - "ctx.register_hook / register_command / inject_message"
      - "plugin LLM call ctx.llm"
      - "Rejected config path from plugin"
      - "add a /slash command to Hermes"
      - "register a hook in Hermes"
      - "hermes plugins doctor / plugins enable"
      - "FakeCtx selftest harness for a plugin"
      - "pre_llm_call / pre_verify hook"
      - "PluginLlmTrustError provider override"
      - "how do I extend Hermes with a plugin"
---

# Authoring a native Hermes plugin

A native plugin is a directory under `~/.hermes/plugins/<name>/` containing `plugin.yaml`
and an `__init__.py` that exposes `register(ctx)`.

## When to Use

- Writing a new native Hermes plugin (`~/.hermes/plugins/<name>/`) that adds hooks or slash commands.
- A plugin's hook is registered but appears never to fire — you need the reload/session semantics.
- Adding an in-session `/command` via `ctx.register_command(name, handler, ...)`.
- Injecting model-visible or user-visible context from a hook (`ctx.inject_message`, returning `{"context": ...}`).
- Making a plugin call the host LLM safely (`ctx.llm.complete`) and diagnosing `PluginLlmTrustError`.
- A plugin setting read via `ctx.get_config` silently returns the default (reserved config key).
- Standing up an offline `FakeCtx` selftest harness instead of testing against the live host.

## Not For

- **Modifying the Hermes core itself** (transport, LLM request pipeline, agent loop) → use `hermes-core-architecture` instead.
- **Editing `config.yaml`, credentials, or plugin enable/disable state** → use `hermes-config-management` instead.
- **Packaging or installing a skill bundle (SKILL.md + references)** → use `agent-skills-cli` instead.
- **LLM provider/model selection or API-key wiring for the host** → use `hermes-provider-config` instead.
- **Persisted-memory writes and memory-provider credentials** → use `hermes-memory-provider-management` instead.
- **Writing cron jobs or unattended scripts** → use `cron-noninteractive-guardrails` instead.

## Layout

```
~/.hermes/plugins/<name>/
  plugin.yaml      # name, version, description, author, provides_hooks: [...]
  __init__.py      # def register(ctx): ...
  README.md
  selftest.py      # stub-host harness (see Testing)
```

Enable with `hermes plugins enable <name>` (or `hermes plugins install owner/repo --enable`).
Verify with `hermes plugins doctor <name>` → expect "runtime discovery, manifest parsing,
import, and registration passed" plus `registrations: N tool(s), M hook(s)`.

## ctx API (verified against the running host)

| Call | Purpose |
|---|---|
| `ctx.get_config(key, default)` / `ctx.set_config(key, value)` | read/write `plugins.entries.<id>.settings.<key>` |
| `ctx.register_hook(name, cb)` | see `VALID_HOOKS` in `hermes_cli/plugins.py` |
| `ctx.register_command(name, handler, description=, args_hint=)` | in-session `/name`; `handler(raw_args) -> str \| None` |
| `ctx.inject_message(content, role="user") -> bool` | queue text into the live session's input |
| `ctx.llm.complete(messages, provider=, model=, max_tokens=, timeout=, temperature=, purpose=)` | host-owned completion; result has `.text` and `.usage` |
| `ctx.register_tool` / `register_skill` / `register_auxiliary_task` / `spawn_task` / `emit` / `subscribe` | other surfaces |

### Hook payloads that matter

- **`pre_llm_call`** — fires per model step (so it doubles as your step counter). Kwargs:
  `session_id, task_id, turn_id, user_message, conversation_history (= list(messages)),
  is_first_turn, model, platform, parent_session_id, sender_id`. Returning
  `{"context": str}` injects into the **user message** — the model sees it, the user does not.
- **`pre_verify`** — fires once when the agent edited code and is about to finish. A
  non-None return **keeps the agent going**; return `None` for a pure side-effect trigger.

## Pitfalls

1. **Reserved config keys are rejected, and `get_config` then silently falls back.**
   `ctx.get_config("model")` logs `Rejected config path 'model' from plugin` and returns your
   default, so a "configurable" setting never applies. `provider` is fine; `model` is not.
   Test candidate keys before shipping — `_plugin_relative_segments` in
   `hermes_cli/plugins_state.py` is the validator. Use domain-specific names
   (`side_model`, `endpoint`, `retry.policy`).
2. **LLM overrides are fail-closed.** `provider`/`model`/`agent_id`/`profile` overrides raise
   `PluginLlmTrustError` unless config sets `plugins.entries.<id>.llm.allow_provider_override`
   and `allow_model_override` (optionally with `allowed_models` / `allowed_providers` lists).
   Catch, log, and never assume the override applied.
3. **A plugin file edit is not live.** Plugin code loads at session start or on a gateway plugin
   reload (`hermes plugins enable/disable`). A long-running session keeps running the OLD
   module — re-enable, or verify in a fresh session. Do not conclude your edit failed.
4. **`hermes -z` (one-shot) does not exercise `pre_llm_call`.** Testing hook behaviour with a
   one-shot silently no-ops and looks like a broken plugin. Use a stub-host harness instead.
5. **Sessions with `_persist_disabled` skip pre_llm_call context collection**
   (`agent/turn_context.py` guard) — another reason a hook can appear to do nothing.
6. **Hook callbacks run on a bounded-timeout worker.** Never do slow work inline (network,
   LLM calls); do it on your own `threading.Thread(daemon=True)` so the turn is never blocked.
7. **Keep every hook fail-open.** Wrap the body in try/except and return `None`; an exception
   escaping a hook must never break the user's turn.
8. **`inject_message` queues as *input*.** With the agent running it goes to the interrupt
   queue, so injected text is treated as a user message and the agent may respond. Label
   injected notes clearly and offer a silent mode.
9. **Check `hermes <cmd> --help` before assuming a flag exists** — published builds lag docs
   (e.g. an installer's documented `--dry-run` that the shipped version rejects).

10. **Hook names must exist in `VALID_HOOKS`.** `ctx.register_hook(name, cb)` only dispatches
   names listed in `hermes_cli/plugins.py`; that file is the authoritative list. Recovery: grep
   `VALID_HOOKS` and confirm your hook name is a member before assuming the hook should fire.
11. **`ctx.llm.complete` does not return a string.** The result object carries `.text` and
   `.usage`. Recovery: always read `result.text`; never concatenate or index the result directly.
12. **Reserved-key validation is per-segment.** Nested keys such as `retry.policy` pass while a
   bare `model` is rejected, so the failure only surfaces on the flat key. Recovery: check
   `_plugin_relative_segments` in `hermes_cli/plugins_state.py` before choosing a key name.

## Testing — stub host, not the live one

Build a `FakeCtx` that records `register_hook`/`register_command`, captures `inject_message`,
and returns a canned result from `llm.complete`. Patch the module's state dir to a tempdir,
call `register(ctx)`, then invoke the captured hook callbacks directly with synthetic kwargs.
Deterministic, offline, immune to reload semantics. Reference implementation:
`~/.hermes/plugins/you-should-know/selftest.py` (covers silence, note delivery, first-turn
skip, disabled, silent delivery, backoff guard, and the slash command).

Always also confirm the real side-model call once in a live session via `hermes plugins doctor`
plus the plugin's own JSONL log — the stub proves your logic, not the host wiring.
