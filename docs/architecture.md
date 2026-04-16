# Starland Gateway Architecture

Starland Gateway is a FastAPI-based application layer for long-running LLM experiences. It sits between clients, model providers, memory storage, and knowledge tools so that conversation behavior can be controlled in one place instead of being scattered across frontends.

The gateway is designed around four goals:

- Keep model routing, context assembly, and memory behavior consistent across clients.
- Preserve long-term conversational continuity without sending unbounded history to the model.
- Separate latency-sensitive chat responses from heavier background memory workloads.
- Keep provider keys, database access, and operational controls server-side.

## System Overview

```text
Clients
  -> Caddy / HTTPS edge
  -> FastAPI Gateway
  -> context assembly + model routing
  -> LLM providers
  -> response to client
  -> async post-chat queue
  -> memory, summaries, embeddings, diagnostics
```

The service exposes several client-facing surfaces:

- `POST /chat` for the native gateway chat API.
- `POST /v1/chat/completions` for OpenAI-compatible clients.
- `POST /telegram/webhook` for Telegram-side interaction.
- `/mcp` and related endpoints for Obsidian/knowledge-base tools.
- `/debug/*` endpoints for context, recall, memory health, and operational inspection.

In deployment, Caddy terminates HTTPS and proxies requests to Uvicorn on `127.0.0.1:8000`. UFW only exposes SSH and Caddy ports publicly, while the Python app remains local to the server.

## Core Components

### 1. Client and Edge Layer

The gateway supports multiple client types while keeping the LLM application logic centralized:

- Telegram webhook for low-friction chat interaction.
- OpenAI-compatible clients that call `/v1/chat/completions`.
- Custom frontends that call `/chat`.
- MCP-compatible tool calls for Obsidian note search, read, and write operations.

This keeps clients relatively thin. They do not need to know how memory, summary injection, provider fallback, or model-specific safeguards work.

### 2. API and Routing Layer

The FastAPI layer validates incoming requests, resolves the requested model, and routes calls to the correct provider. Models are addressed as `provider:model`, which makes provider selection explicit and reduces accidental routing ambiguity.

The routing layer supports:

- Multiple LLM providers behind one application interface.
- OpenAI-compatible request handling.
- Strict model matching for selected models where snapshot/alias confusion would affect cost or behavior.
- High-cost model profiles that use more conservative context budgets.

### 3. Context Assembly Layer

Before each model call, the gateway builds the prompt context from several layers:

- Persona/system instructions.
- Fast recall memories selected for the current query.
- Recent conversation turns for local coherence.
- Rolling conversation summaries for longer-range continuity.
- Cold-start history when a client sends only a new user message.
- Upstream compression blocks when client-provided history is too long.

The goal is to preserve useful continuity while keeping prompt size bounded. Recent turns are kept because they are the strongest signal for immediate conversational intent; summary and memory layers provide slower background continuity.

### 4. Memory and Retrieval Layer

The memory system is not a single vector search call. It is a multi-stage retrieval pipeline:

```text
candidate collection
  -> vector + keyword merge
  -> scoring with weight / importance / recency
  -> reranking
  -> diversity selection
  -> short context injection
```

This design avoids over-relying on any single retrieval signal. Vector search helps with semantic similarity, keyword search protects exact names and symbols, and reranking/diversity selection reduce repetitive or stale recall.

The gateway also supports citation feedback. When a model marks a memory as used, the gateway can store that citation and increase the memory weight, creating a lightweight learning loop for future recall.

### 5. Async Post-Chat Pipeline

The chat response path and memory-writing path are intentionally separated. After a user receives a response, heavier work is placed into a background queue:

- Memory generation.
- Conversation summary generation.
- Weekly/monthly summary maintenance.
- Relationship/state merge routines.
- Embedding generation and backfills.

This protects response latency and makes post-processing failures less disruptive. If a memory job fails, the chat response can still succeed.

### 6. Data Layer

Supabase Postgres stores the core application state:

- Conversations and messages.
- Memories and memory citations.
- Conversation summaries.
- Embedding tables for semantic recall.
- Telegram-specific state such as nudges and sticker aliases.
- Higher-level state/snapshot tables for slower continuity layers.

The gateway uses server-side service credentials and does not require public clients to talk directly to the database. This keeps database access behind the application layer.

### 7. Knowledge Tool Layer

The Obsidian MCP integration lets the model inspect or write notes through controlled tools rather than direct filesystem access. Tool calls are registered in the gateway and constrained by path rules, so the model can use the knowledge base without bypassing application-level controls.

### 8. Observability and Debugging

The gateway includes debug endpoints for inspecting:

- Assembled prompt context.
- Recall candidates and selected memories.
- Memory health.
- Citation feedback.
- Summary and state layers.
- Recent traces and pollution scans.

These endpoints make LLM behavior debuggable. Instead of treating each answer as a black box, the system can show which context blocks were included and why.

## Main Data Flow

1. A user sends a message through Telegram, a frontend, or an OpenAI-compatible client.
2. FastAPI validates the request and resolves the target model.
3. The context assembly layer selects relevant recent turns, memories, summaries, and compression blocks.
4. The gateway calls the selected LLM provider.
5. The response is returned to the client.
6. A background task is queued for memory/summary maintenance.
7. Supabase and embedding tables are updated asynchronously.
8. Future requests can retrieve and reuse the updated memory state.

## Security Boundary

The intended trust boundary is:

- Public internet reaches Caddy over HTTPS.
- Caddy proxies to the local FastAPI service.
- The FastAPI service owns provider keys and Supabase service access.
- Clients should not receive database service keys or provider keys.
- Uvicorn is not exposed directly on a public port.

This architecture keeps user-facing clients simple while centralizing sensitive operations in the gateway.

## Current Scope

This project is a personal, production-style AI system rather than a packaged SaaS product. The most important engineering focus is the LLM application layer: memory quality, context control, cost control, tool integration, and operational stability.
