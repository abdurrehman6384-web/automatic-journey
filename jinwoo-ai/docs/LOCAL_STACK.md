# Local-first stack decisions

## Default path

The first runnable profile intentionally stays small:

```text
React/Vite UI → relative /api route → FastAPI → SQLite
                                └→ demo provider / optional local Ollama
```

This works without Docker, PostgreSQL, Redis, GPU hardware or cloud API keys.

## Optional profiles

| Profile | Add only when needed |
|---|---|
| Standard | Ollama or LM Studio plus local LanceDB/Chroma document retrieval |
| Power | PostgreSQL, Redis and vLLM on a suitable GPU/Linux system |
| Observability | Prometheus and Grafana containers |
| Cloud hybrid | Claude, GLM or Hugging Face enabled from secure local settings |

## Multi-agent framework boundary

Jinwoo's native mission engine is the single canonical orchestrator in V1.
Swarms, Agency-Swarm and Ruflo are optional, status-only adapters: the backend
can report whether they are present locally but will not install or execute
them. Any future adapter must return proposed work through Jinwoo's policy,
approval, workspace and audit boundaries. See
[`FRAMEWORK_ADAPTERS.md`](FRAMEWORK_ADAPTERS.md).

## Why Rust and Go are not initial services

Python is the main orchestrator. Rust and Go are excellent later sidecars for a
measured hot path — e.g. high-speed indexing or a bounded concurrent service —
but adding them before profiling would create extra IPC, packaging and debugging
cost without making missions better.

## Memory

SQLite is a durable, local fallback. Vector retrieval can use LanceDB or
ChromaDB later. If the requested "memo API" is Mem0, it becomes an opt-in sync
adapter; it never replaces the user's ability to inspect and delete local data.
