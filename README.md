# Canvas

CLI + importable library for managing ephemeral org-aware Claude Code workspaces.

Canvas creates dated session directories with rendered `CLAUDE.md` templates,
auto-launches Claude, and maintains a session registry.

## Install

```bash
pip install -e .
```

## Usage

```bash
# Create a new workspace session
canvas new [label]

# List active sessions
canvas list

# Archive a session (marks inactive, preserves on disk)
canvas archive <slug>

# Permanently destroy a session
canvas nuke <slug>

# Rename a session
canvas rename <slug> <label>
```

## Configuration

Canvas reads its config from `~/.canvas/config`:

```json
{
  "org": "personal"
}
```

Sessions are tracked in `~/.canvas/registry.json` and live at `~/canvas/<slug>/`.
