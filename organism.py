#!/usr/bin/env python3
"""Tiny seed for the 3DVR Digital Organism.

Stdlib-only local memory store. This is intentionally simple: prove durable memory,
provenance, retrieval, correction/deletion, and evaluation before adding model or
vector-database complexity.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from providers import make_provider

DB_PATH = Path("organism.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL DEFAULT 'fact',
    subject TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    source_id TEXT,
    created_at TEXT NOT NULL,
    valid_until TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    importance REAL NOT NULL DEFAULT 0.5,
    deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_memories_subject ON memories(subject);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def remember(
    content: str,
    *,
    kind: str = "fact",
    subject: str = "",
    source_type: str = "manual",
    source_id: str | None = None,
) -> str:
    memory_id = f"mem_{uuid.uuid4().hex[:12]}"
    with connect() as db:
        db.execute(
            "INSERT INTO memories "
            "(id, kind, subject, content, source_type, source_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (memory_id, kind, subject, content, source_type, source_id, now()),
        )
    return memory_id


def tokens(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z0-9][a-z0-9._-]+", text.lower())
        if len(t) > 1
    }


def recall(query: str, limit: int = 5) -> list[tuple[float, sqlite3.Row]]:
    q = tokens(query)
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM memories WHERE deleted_at IS NULL"
        ).fetchall()

    ranked = []
    for row in rows:
        haystack = tokens(f"{row['subject']} {row['content']} {row['kind']}")
        overlap = len(q & haystack)
        union = max(1, len(q | haystack))
        lexical = overlap / union
        score = (
            lexical * 0.75
            + float(row["importance"]) * 0.15
            + float(row["confidence"]) * 0.10
        )
        if overlap or not q:
            ranked.append((score, row))
    return sorted(ranked, key=lambda item: item[0], reverse=True)[:limit]


def ingest(path: str) -> int:
    count = 0
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            content = item.get("content") or item.get("text") or item.get("message")
            if not content:
                continue
            remember(
                str(content),
                kind=str(item.get("kind", "event")),
                subject=str(item.get("subject", "")),
                source_type=str(item.get("source_type", "jsonl")),
                source_id=str(item.get("source_id", f"{path}:{line_no}")),
            )
            count += 1
    return count


def explain(memory_id: str) -> None:
    with connect() as db:
        row = db.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
    if not row:
        raise SystemExit(f"Memory not found: {memory_id}")
    print(json.dumps(dict(row), indent=2))


def forget(memory_id: str) -> None:
    with connect() as db:
        result = db.execute(
            "UPDATE memories SET deleted_at = ? "
            "WHERE id = ? AND deleted_at IS NULL",
            (now(), memory_id),
        )
    if not result.rowcount:
        raise SystemExit(f"Active memory not found: {memory_id}")


def context_for(query: str, limit: int = 5) -> str:
    """Build the auditable user-owned context supplied to a reasoning provider."""

    hits = recall(query, limit)
    if not hits:
        return "No relevant stored memories were retrieved."

    lines = [
        "Retrieved user-owned memories follow.",
        "Treat them as context, not unquestionable truth; provenance is included.",
    ]
    for score, row in hits:
        source = row["source_type"]
        if row["source_id"]:
            source = f"{source}:{row['source_id']}"
        subject = f" subject={row['subject']!r}" if row["subject"] else ""
        lines.append(
            f"- id={row['id']} score={score:.3f} kind={row['kind']}"
            f"{subject} source={source!r}: {row['content']}"
        )
    return "\n".join(lines)


def ask(
    prompt: str,
    *,
    provider_name: str,
    model: str | None,
    base_url: str | None,
    api_key: str | None,
    limit: int,
) -> str:
    provider = make_provider(
        provider_name,
        model=model,
        base_url=base_url,
        api_key=api_key,
    )
    context = context_for(prompt, limit)
    messages = [
        {
            "role": "system",
            "content": (
                "You are the reasoning engine inside a user-owned personal "
                "intelligence system. Use the supplied memory context when relevant. "
                "Do not claim a memory is current when its provenance is insufficient.\n\n"
                f"{context}"
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return provider.complete(messages)


def self_eval() -> int:
    probe = f"eval-{uuid.uuid4().hex[:8]}"
    memory_id = remember(
        f"The evaluation token is {probe}.",
        kind="lesson",
        subject="self-evaluation",
    )
    hits = recall(f"What is the evaluation token {probe}?")
    ok = any(row["id"] == memory_id for _, row in hits)
    forget(memory_id)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="organism",
        description="3DVR Digital Organism memory seed",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("remember")
    p.add_argument("content")
    p.add_argument("--kind", default="fact")
    p.add_argument("--subject", default="")

    p = sub.add_parser("recall")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)

    p = sub.add_parser("context")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)

    p = sub.add_parser("ask")
    p.add_argument("prompt")
    p.add_argument(
        "--provider",
        required=True,
        choices=("echo", "ollama", "openai-compatible"),
        help="Explicit reasoning provider. No external provider is chosen implicitly.",
    )
    p.add_argument("--model")
    p.add_argument("--base-url")
    p.add_argument(
        "--api-key-env",
        default="ORGANISM_API_KEY",
        help="Environment variable containing the provider API key.",
    )
    p.add_argument("--limit", type=int, default=5)

    p = sub.add_parser("ingest")
    p.add_argument("path")

    p = sub.add_parser("explain")
    p.add_argument("memory_id")

    p = sub.add_parser("forget")
    p.add_argument("memory_id")

    sub.add_parser("eval")

    args = parser.parse_args()

    if args.command == "remember":
        print(remember(args.content, kind=args.kind, subject=args.subject))
    elif args.command == "recall":
        for score, row in recall(args.query, args.limit):
            print(
                f"{score:.3f}\t{row['id']}\t"
                f"[{row['kind']}] {row['subject']} — {row['content']}"
            )
    elif args.command == "context":
        print(context_for(args.query, args.limit))
    elif args.command == "ask":
        try:
            print(
                ask(
                    args.prompt,
                    provider_name=args.provider,
                    model=args.model,
                    base_url=args.base_url,
                    api_key=os.getenv(args.api_key_env),
                    limit=args.limit,
                )
            )
        except (RuntimeError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc
    elif args.command == "ingest":
        print(f"ingested {ingest(args.path)} records")
    elif args.command == "explain":
        explain(args.memory_id)
    elif args.command == "forget":
        forget(args.memory_id)
        print(f"forgot {args.memory_id}")
    elif args.command == "eval":
        return self_eval()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
