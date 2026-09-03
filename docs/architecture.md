# Architecture Seed

## Goal

Create a personal intelligence system that improves continuously without treating every new statement as a permanent neural-weight update.

The design separates three timescales:

- **Immediate:** raw events are archived.
- **Continuous:** durable memories are extracted, linked, ranked, corrected, and retrieved.
- **Periodic:** high-quality examples are turned into training data and evaluated before a new adapter/model is promoted.

## Data Flow

```text
conversation / email / task / code / calendar / device event
                         │
                         ▼
                  append-only archive
                         │
                         ▼
                  memory compiler
                         │
       ┌─────────────────┼──────────────────┐
       ▼                 ▼                  ▼
 semantic memory    episodic memory    relationship graph
       └─────────────────┼──────────────────┘
                         ▼
                   context builder
                         │
                         ▼
                  reasoning model
                         │
                         ▼
             response + feedback + trace
                         │
                         ├──> archive / memory updates
                         └──> evaluation / training pool
```

## Memory Record v0

A memory should be an inspectable object, not a hidden blob.

```json
{
  "id": "mem_...",
  "kind": "decision | fact | preference | person | project | task | relationship | lesson",
  "subject": "...",
  "content": "...",
  "source": {
    "type": "conversation",
    "source_id": "...",
    "timestamp": "..."
  },
  "valid_from": "...",
  "valid_until": null,
  "confidence": 0.95,
  "importance": 0.7,
  "supersedes": null,
  "tags": [],
  "embedding_ref": null
}
```

Important rule: **the original source stays available.** Summaries can be wrong; provenance lets the organism recover.

## Retrieval

Retrieval should combine:

1. semantic similarity,
2. named entities/projects,
3. recency,
4. importance,
5. temporal validity,
6. relationship distance,
7. explicit pinned/canonical memories.

The context builder should return both the selected memories and a machine-readable explanation of why each was selected.

## Forgetting and Correction

Memory must support:

- explicit deletion,
- superseding an old fact,
- expiration of short-lived state,
- conflict detection,
- keeping historical truth without presenting it as current truth.

Deleting a memory should not require retraining the entire model. This is a major reason long-term facts live outside model weights.

## Training Loop

Training is downstream of memory, not a replacement for it.

Candidate examples can come from interactions where:

- the user explicitly approved/corrected an answer,
- a task was successfully completed,
- retrieved context clearly improved the response,
- a stable style/workflow pattern repeats many times.

A training job produces an adapter/checkpoint candidate. It is tested against a frozen evaluation suite before promotion.

```text
production interactions
       ↓
curated examples
       ↓
train candidate
       ↓
run eval suite
       ↓
compare to current model
       ↓
 promote / reject / rollback
```

## Evaluation Seed

The first evaluation suite should test:

- recall of stable facts,
- distinction between old and current facts,
- project continuity,
- resistance to invented memories,
- correct use of provenance,
- honoring a user's request to forget something,
- useful behavior when memories conflict,
- model/provider swaps without memory loss.

## v0.1 Implementation Shape

Keep it boring and portable initially:

- Python service
- SQLite as canonical structured store
- FTS/vector extension or separate vector index
- JSONL append-only raw event archive
- HTTP/CLI ingest and retrieval endpoints
- provider-neutral model adapter interface

A graph database can come later if relationship queries justify the operational cost. The schema should remain graph-friendly from day one.

## Long-Term Direction

Eventually the Digital Organism can coordinate memory from conversations, code repositories, email, calendars, files, devices, and agents. Local/open-weight models can handle background compilation while stronger remote models can be invoked for difficult reasoning.

The valuable artifact is not any one model checkpoint. It is the **continuously improving, user-owned intelligence substrate** that survives model changes.
