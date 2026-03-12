# Client Work — Prompt Engineering Projects

> Index of all client-facing prompt engineering projects.
> Each project is a self-contained scaffold with components, schema, and version history.

## Projects

| Project | Path | Description | Status |
|---|---|---|---|
| **Lead Brief** | [lead_brief/](lead_brief/) | AI-powered lead briefing — pitch generation, lead summaries, qualification reasoning | 🟡 Pitch active, others TBD |

## Project Scaffold Pattern

Every project follows this structure:

```
project_name/
├── README.md           ← project overview, component index, business rules
├── _schema/            ← shared data field definitions
├── _docs/              ← requirements, planning, client communication
├── component_a/        ← each output type gets its own folder
│   ├── prompt_v{N}.md  ← current production prompt
│   ├── context/        ← domain knowledge files
│   ├── examples/       ← sample inputs/outputs
│   └── _iterations/    ← version history
└── component_b/
    └── ...
```

## Adding a New Project

1. Create `clientwork/{project_name}/`
2. Add `README.md`, `_schema/`, first component folder
3. Register it in the table above
