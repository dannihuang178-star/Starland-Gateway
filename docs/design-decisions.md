# Design Decisions

This document explains the main architectural tradeoffs behind Starland Gateway. It is written as a public-facing companion to the codebase, focusing on why the system is shaped this way rather than listing every implementation detail.

## 1. Gateway Instead of Direct Frontend-to-LLM Calls

### Decision

Use a server-side gateway between clients and model providers.

### Why

Direct frontend-to-provider calls are simpler at first, but they make long-term behavior difficult to control. A gateway creates one place to manage:

- Provider keys and database credentials.
- Model routing and provider fallback.
- Prompt/context assembly.
- Memory retrieval and writing.
- Cost controls and token budgets.
- Observability and debugging.
- Cross-client consistency between Telegram, web clients, and OpenAI-compatible clients.

### Tradeoff

The gateway adds backend complexity and operational responsibility. In return, it turns LLM calls into a controllable application layer rather than isolated API calls from each client.

## 2. Summary Layers Instead of Full Conversation History

### Decision

Use rolling conversation summaries and slower weekly/monthly summaries instead of sending full history on every request.

### Why

Long-running conversations produce too much raw history to send repeatedly. Full-history prompting increases cost, latency, and the chance that stale context overwhelms the current user intent.

Summary layers preserve continuity while compressing older context into smaller, purpose-built blocks. They are especially useful for:

- Long conversations.
- Cold-start windows where the client sends only a new user message.
- Preserving narrative continuity without persistent token inflation.
- Separating immediate context from slower background patterns.

### Tradeoff

Summaries are lossy. The system must still preserve recent turns and raw messages for moments where exact wording matters.

## 3. Keeping Recent Turns Alongside Memory Recall

### Decision

Always prioritize recent user/assistant turns in the final context window.

### Why

Recent turns are usually the strongest signal for what the user is asking right now. Memory recall is useful, but it can be stale, partial, or only indirectly related. Keeping recent turns helps prevent old memories from overriding the live conversation.

This is especially important because fast recall is treated as reference context, not absolute truth.

### Tradeoff

Keeping recent turns consumes token budget. The gateway balances this with compression, summary layers, and context trimming.

## 4. Separate Chat Response From Memory Workloads

### Decision

Return the chat response first, then run memory and summary jobs in an async post-chat queue.

### Why

Memory generation, embedding writes, and summary maintenance can be slow or fail independently. Running them inline would make every chat request depend on all downstream jobs succeeding.

The async pipeline improves:

- User-perceived latency.
- Fault isolation.
- Operational resilience.
- Ability to add heavier memory jobs without slowing normal chat.

### Tradeoff

Memory is eventually consistent. A just-finished conversation turn may not immediately appear in all summary or embedding layers.

## 5. Vector + Keyword Retrieval Instead of Vector-Only Search

### Decision

Use both vector recall and keyword recall, then merge/rerank/select with diversity controls.

### Why

Vector recall handles semantic similarity well, but it can miss exact names, rare symbols, and specific phrases. Keyword recall protects those exact-match cases. Weight, importance, and recency remain active ranking signals so the system can prefer memories that are useful, important, and recently reinforced.

### Tradeoff

This is more complex than a single embedding query. The benefit is better recall behavior for personal, symbolic, and long-running context.

## 6. Context Compression Cache

### Decision

Compress older upstream history and cache the compressed result.

### Why

Some clients send a large message history on every request. Recompressing the same old context repeatedly wastes time and tokens. A cache lets the gateway reuse previous compression results and only update when enough new overflow appears.

### Tradeoff

Compression introduces another layer of state. Debug endpoints and logs are needed so it remains observable.

## 7. Model Routing With Strict Matching

### Decision

Use explicit `provider:model` routing and strict response-model checks for selected models.

### Why

Different providers, aliases, and snapshots can have different behavior or cost profiles. A strict model check helps catch cases where a request intended for one model is silently served by a different snapshot or variant.

### Tradeoff

Strictness can cause requests to fail when provider metadata changes unexpectedly. The benefit is safer cost and behavior control for models where exact routing matters.

## 8. Telegram as a Lightweight Interaction Surface

### Decision

Support Telegram as a side-window client rather than only building a web UI.

### Why

Telegram provides a natural, low-friction chat surface. It also forces the system to handle real interaction constraints: short messages, bursts, voice, images, stickers, delayed replies, and proactive nudges.

### Tradeoff

Telegram adds integration complexity and channel-specific behavior. The gateway keeps it separate enough that Telegram-specific logic does not dominate the main `/chat` flow.

## 9. MCP Tools for Obsidian Instead of Direct Model Access

### Decision

Expose Obsidian note operations through controlled MCP-style tools.

### Why

The model should be able to search and use the knowledge base, but not with unconstrained filesystem access. Tool schemas, path rules, and gateway-side execution keep the integration explicit and auditable.

### Tradeoff

Tool use adds latency and complexity. The gateway limits tool calls and injects tool instructions conditionally to avoid unnecessary every-turn overhead.

## 10. Service-Side Database Access

### Decision

Keep Supabase access behind the gateway using server-side credentials.

### Why

The database contains conversations, memories, summaries, and operational state. Keeping access server-side avoids exposing service keys or raw tables to clients and lets the gateway enforce application-level behavior.

### Tradeoff

The backend becomes the primary access path and must be deployed reliably. This is acceptable because the gateway already owns model routing and memory behavior.

## 11. Debug Endpoints as a First-Class Feature

### Decision

Add debug endpoints for context, recall, traces, and memory health.

### Why

LLM systems fail in subtle ways. A wrong answer might be caused by bad recall, missing summaries, stale memory, excessive compression, or prompt ordering. Debug endpoints make these layers visible and reduce guesswork.

### Tradeoff

Debug endpoints must be handled carefully in deployment because they can expose sensitive operational context. They are valuable for development and maintenance, but should not be treated as public product endpoints.

## Summary

The main design pattern is to keep the realtime chat path small and stable, while moving memory, summarization, and reflection into observable background layers. This creates a system that behaves more like a maintainable LLM application platform than a single chatbot script.
