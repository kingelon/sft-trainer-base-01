# ADR Log — Architecture Decision Records

Incremental log of decisions, actions, and observations. Append-only.

---

## ADR-001: Scaffold Creation
- **Date**: 2026-02-11
- **Context**: Setting up finetuning experimentation workspace from scratch. Vamsi wants standalone scripts, not a monolithic framework. Focus on Llama 3.1 8B and Mistral 7B.
- **Decision**: Created a directory-based scaffold with `agents/`, `docs/`, `notes/`, `src/`, `scripts/`, `data/`, `models/`, `outputs/`, `tests/`. Agent meta files in `agents/`. Shared config/utils in `src/`. Numbered script stubs in `scripts/`.
- **Consequences**: Easy to add new experiments as numbered scripts. `src/` can grow organically. No framework lock-in.

## ADR-002: Centralized HF Cache
- **Date**: 2026-02-11
- **Context**: Models are large (16-32GB). Multiple projects may need the same models.
- **Decision**: Target `/Users/vamsi/01_BUILD/_meta/models` as `HF_HOME`. Setup deferred — will configure env var when ready.
- **Consequences**: Single download per model across all projects. Repo stays lightweight.
