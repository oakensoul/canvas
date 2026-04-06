# Canvas — Architecture

## What is Canvas?

Canvas is a CLI + importable Python package for managing ephemeral, org-aware Claude Code workspaces. Each canvas session is a dated directory with a rendered `CLAUDE.md` that gives Claude full context for the active org — personal, work, or a side project. Sessions auto-launch `claude` on creation.

A canvas is a **working surface with no implied scope** — brainstorming, planning, research, code spikes, anything. The org determines what context Claude has, not the task type.

---

## Ecosystem Position

```
loadout            ← writes ~/.canvas/config on init, sets active org
canvas             ← this package
aida-canvas-plugin ← thin AIDA skill wrapper around canvas.core
iTerm2             ← one profile per org, "Send text at start" fires canvas new
```

The AIDA plugin imports directly from this package:

```python
from canvas.core import new_session, list_sessions
```

---

## CLI Interface

```bash
canvas new                        # new session, auto-slug, launch claude
canvas new "okr planning"         # named session, launch claude
canvas list                       # show all sessions
canvas archive <slug>             # mark as archived (keep for reference)
canvas nuke <slug>                # delete session directory + remove from registry
canvas rename <slug> <label>      # rename a session
canvas open <slug>                # re-enter an existing session, launch claude
```

---

## Session Lifecycle

### `canvas new`

1. Read active org from `~/.canvas/config`
2. Generate slug: `<date>-<random-word>-<random-word>` (e.g. `2026-03-13-electric-penguin`)
3. Create directory at `~/.canvas/sessions/<slug>/`
4. Render `CLAUDE.md` from `~/.dotfiles-private/canvas/orgs/<org>/CLAUDE.md.tmpl`
5. Register session in `~/.canvas/registry.json`
6. `cd ~/.canvas/sessions/<slug>/`
7. Launch `claude`

If a label is provided (`canvas new "okr planning"`), it's stored in the registry alongside the slug. The slug stays as the directory name; the label is human-readable display.

### `canvas archive`

Marks session status as `archived` in the registry. Directory is preserved for reference.

### `canvas nuke`

Deletes the session directory and removes the entry from the registry. No recovery.

### `canvas rename`

Updates the label in the registry. Slug and directory name are unchanged.

### `canvas open`

Re-enters an existing session: looks up the slug in the registry, `cd`s into the session directory, and launches `claude`. No template re-rendering — the CLAUDE.md from creation time is used as-is. Works with both active and archived sessions.

---

## Config

`~/.canvas/config` — written once by `loadout init`, tells canvas which org is active:

```json
{
  "org": "work"
}
```

No env vars, no flags, no detection logic. The config is user-scoped — `alice` has one config, another user has another. Each reads its own.

---

## Registry

`~/.canvas/registry.json` — session index:

```json
{
  "sessions": [
    {
      "slug": "2026-03-13-electric-penguin",
      "org": "personal",
      "created": "2026-03-13",
      "label": null,
      "status": "active"
    },
    {
      "slug": "2026-03-10-okr-planning",
      "org": "work",
      "created": "2026-03-10",
      "label": "okr planning",
      "status": "active"
    }
  ]
}
```

---

## Slug Generation

Slugs follow the pattern `<YYYY-MM-DD>-<word>-<word>`:

- **No label**: `2026-03-18-electric-penguin` — random adjective + noun
- **With label**: `2026-03-18-okr-planning` — label is kebab-cased into the slug
- Date prefix makes them sortable chronologically
- Random words make them memorable and visually distinct
- When a label is provided, the original text is stored in the registry for display
- Slugs are permanent identifiers — `canvas rename` changes the label, never the slug or directory

---

## CLAUDE.md Templates

Templates live in `~/.dotfiles-private/canvas/orgs/<org>/CLAUDE.md.tmpl`. Each org has its own template providing Claude with full context for that org's stack, priorities, and conventions.

Example variables available in templates:

```
{{ org }}
{{ date }}
{{ slug }}
{{ label }}
```

Rendered output is written to `~/.canvas/sessions/<slug>/CLAUDE.md` at session creation time.

---

## iTerm2 Integration

One iTerm2 profile per org, configured with "Send text at start":

```bash
canvas new && exit   # new session, launch claude, close shell on claude exit
```

This means opening the `Work` iTerm2 profile automatically creates a new canvas session with that org's context and launches Claude. No manual steps.

Profiles are created by `loadout init` per org, using the color scheme conventions from the devbox iTerm2 setup:

| Org | Scheme |
|-----|--------|
| personal | Dracula / Catppuccin |
| work | Nord |
| creative | Tokyo Night |

---

## `loadout check` Integration

```
🎨  CANVAS
✅ 2026-03-13-okr-planning (work) — 2d ago
⚠️  2026-02-01-electric-penguin (personal) — 39d ago  ← consider archiving or nuking
```

Sessions older than 30 days with status `active` trigger a warning.

---

## Package Structure

```
canvas/
├── __init__.py
├── cli.py          # Click CLI
├── config.py       # config + path resolution (CanvasPaths)
├── core.py         # importable by aida-canvas-plugin
├── exceptions.py   # domain exception hierarchy
├── registry.py     # ~/.canvas/registry.json read/write
├── template.py     # CLAUDE.md rendering from org template
└── slug.py         # date + random word generation
```

---

## Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Session slugs | `YYYY-MM-DD-word-word` | `2026-03-13-electric-penguin` |
| Labels | kebab-case | `okr-planning` |
| Session directories | slug only | `~/.canvas/sessions/2026-03-13-electric-penguin/` |
| Org names | kebab-case | `personal`, `work`, `creative` |

---

## Platform Support

macOS primary — iTerm2 profile integration is macOS-only. The core session management (slug generation, registry, template rendering, claude launch) is fully portable to Linux/*nix. A future `terminal.py` module can abstract the iTerm2-specific pieces.
