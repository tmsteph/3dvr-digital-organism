# 3DVR Digital Organism

An open-source personal intelligence layer that **remembers, retrieves, evaluates, and gradually learns** from a person's digital life without locking that history to one model provider.

> **Canonical runtime:** active implementation now lives in [`tmsteph/3dvr-portal/apps/agent`](https://github.com/tmsteph/3dvr-portal/tree/main/apps/agent). This repository is the public architecture/reference, seed implementation, and future extraction target. We intentionally avoid maintaining two competing runtimes while the interfaces are still evolving.

## Vision

Most assistants begin each conversation partially amnesiac. The Digital Organism treats the user's accumulated context as a first-class, user-owned system.

The core loop is:

**experience → capture → remember → retrieve → reason → evaluate → learn**

The system should feel continuously alive while keeping long-term memory separate from model weights. Facts can be corrected or forgotten immediately; model training happens deliberately against tested datasets.

## Principles

- **User-owned memory** — portable, inspectable, exportable, deletable.
- **Model independent** — hosted or local models can share the same memory substrate.
- **Retrieval before retraining** — fresh facts belong in memory first.
- **Provenance** — memories retain their source, time, confidence, and revision history.
- **Continual learning with gates** — new adapters/models are promoted only when evaluations improve.
- **Local-first where practical** — sensitive archives should not require a third-party cloud.
- **Open source** — the organism should survive any single company, API, or model.

## Seed Architecture

1. **Archive** — immutable raw conversations/events.
2. **Memory compiler** — extracts people, projects, decisions, preferences, tasks, facts, and relationships.
3. **Memory store** — structured records + semantic search + temporal history.
4. **Context builder** — retrieves only the memories relevant to the current request.
5. **Reasoning model** — interchangeable hosted or local LLM.
6. **Evaluator** — tests recall, consistency, usefulness, hallucination resistance, and forgetting.
7. **Trainer** — periodically produces fine-tuning/adapter datasets from high-confidence interactions.
8. **Promotion gate** — replaces a trained model only when it beats the previous version.

See [`docs/architecture.md`](docs/architecture.md) for the first design sketch and [`ROADMAP.md`](ROADMAP.md) for the seed milestones.

## Provider Independence

The organism owns memory and builds context locally. A reasoning model is attached only through the small provider boundary in [`providers.py`](providers.py).

No external provider is selected implicitly. You choose one each time you use `ask`, and `context` lets you inspect the exact retrieved memory context first.

```bash
python organism.py context "what servers are we using?"

# Fully local reasoning through Ollama
python organism.py ask "what servers are we using?" \
  --provider ollama \
  --model qwen3:8b

# Any hosted or local server implementing /v1/chat/completions
export ORGANISM_API_KEY="..."
python organism.py ask "what servers are we using?" \
  --provider openai-compatible \
  --base-url https://example.invalid/v1 \
  --model example-model
```

The wire format can be compatible with an existing API without making that company a dependency. The memory database, retrieval logic, context builder, and evaluation loop remain ours.

## Relationship to 3DVR Portal

The standalone seed is useful for keeping the architecture small, understandable, and independently reusable. Product development happens in the Portal monorepo because `apps/agent` already owns local execution, model routing, worker processes, installation, and 3DVR's portable context systems.

Once the memory/provider interfaces stabilize and prove useful in real workflows, reusable pieces can be extracted from Portal into this repository as a clean library rather than copied between projects.

## First Milestone

Build a tiny local service that can ingest a conversation, extract durable memory records, retrieve relevant records for a new prompt, and expose why each memory was selected.

No fine-tuning is required for v0.1. If memory and retrieval are excellent, the system already solves most cross-conversation forgetting.

## Status

🌱 Seed planted — September 2026.

The first provider-independent reasoning seam is implemented here as a reference. Active integration and real-world hardening continue in `3dvr-portal/apps/agent`.
