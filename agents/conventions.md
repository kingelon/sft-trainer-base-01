# Directory Conventions

> Referenced from `agents.md`. Details on where agents vs humans write files.

## Ownership Rules

| Directory | Owner | Purpose |
|-----------|-------|---------|
| `notes/` | **Vamsi (human)** | Personal thoughts, scratch notes, run logs. Agents should NOT write here. |
| `docs/` | **Agent** | Agent-generated documentation, state transfer docs, concept explainers, deep dives |
| `agents/` | **Agent** | Agentic context files, conventions, decision logs, comms |
| `presentations/` | **Agent** | Presentation artifacts (Reveal.js HTML files) |
| `scripts/` | **Shared** | Standalone runnable scripts |
| `configs/` | **Shared** | YAML recipes and configuration |
| `src/` | **Shared** | Core library code |

## Key Distinction

- **`notes/`** = Vamsi's space. Don't create files here.
- **`docs/`** = Agent's general documentation output. Use slugged subdirs if a topic grows (e.g., `docs/lead-brief/`).
- **`agents/`** = Agent meta-files only (conventions, logs, comms). Not for project docs.
