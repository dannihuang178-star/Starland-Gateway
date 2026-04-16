"""
Redacted memory and context interfaces for Starland Gateway.

This file shows the high-level retrieval and prompt-assembly pipeline without
including private prompts, real schemas, or personal memory content.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class Message:
    role: Role
    content: str


@dataclass
class Memory:
    id: str
    summary: str
    tags: list[str]
    importance: Literal["low", "medium", "high"]
    weight: float
    created_at: datetime


@dataclass
class RecallResult:
    selected_memories: list[Memory]
    debug: dict[str, Any]


class MemoryStore:
    """
    Storage adapter boundary.

    The production implementation talks to Supabase Postgres and embedding
    tables. This skeleton intentionally avoids real table names beyond generic
    concepts.
    """

    async def recent_messages(
        self,
        user_id: str,
        conversation_id: str | None,
        limit: int,
    ) -> list[Message]:
        _ = (user_id, conversation_id, limit)
        return []

    async def candidate_memories(
        self,
        user_id: str,
        query: str,
        limit: int,
    ) -> list[Memory]:
        _ = (user_id, query, limit)
        return []

    async def rolling_summaries(
        self,
        user_id: str,
        conversation_id: str | None,
        limit: int,
    ) -> list[str]:
        _ = (user_id, conversation_id, limit)
        return []


class MemoryRetriever:
    """
    Query-time recall pipeline.

    Production flow:
      candidate -> vector/keyword merge -> scoring -> rerank -> diversity select
    """

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    async def recall(
        self,
        user_id: str,
        query: str,
        limit: int,
    ) -> RecallResult:
        candidates = await self.store.candidate_memories(
            user_id=user_id,
            query=query,
            limit=limit * 10,
        )
        scored = self.score_candidates(candidates, query=query)
        reranked = self.rerank(scored, query=query)
        selected = self.diversity_select(reranked, limit=limit)
        return RecallResult(
            selected_memories=selected,
            debug={
                "candidate_count": len(candidates),
                "selected_count": len(selected),
            },
        )

    def score_candidates(self, candidates: list[Memory], query: str) -> list[Memory]:
        _ = query
        return sorted(
            candidates,
            key=lambda m: (self.importance_score(m), m.weight, m.created_at),
            reverse=True,
        )

    def rerank(self, memories: list[Memory], query: str) -> list[Memory]:
        _ = query
        return memories

    def diversity_select(self, memories: list[Memory], limit: int) -> list[Memory]:
        selected: list[Memory] = []
        seen_tags: set[str] = set()
        for memory in memories:
            signature = self.memory_signature(memory)
            if signature in seen_tags and len(selected) < limit - 1:
                continue
            selected.append(memory)
            seen_tags.add(signature)
            if len(selected) >= limit:
                break
        return selected

    def importance_score(self, memory: Memory) -> int:
        return {"low": 0, "medium": 1, "high": 2}.get(memory.importance, 0)

    def memory_signature(self, memory: Memory) -> str:
        for tag in memory.tags:
            if tag.startswith("klass:"):
                return tag
        return "generic"


class ContextAssembler:
    """
    Builds final model input from request messages and memory layers.
    """

    def __init__(self, memory_store: MemoryStore) -> None:
        self.store = memory_store
        self.retriever = MemoryRetriever(store=memory_store)

    async def build_context(
        self,
        user_id: str,
        conversation_id: str | None,
        requested_messages: list[Message],
        model_ref: str,
    ) -> list[Message]:
        latest_user_text = self.latest_user_text(requested_messages)
        recent_turns = await self.store.recent_messages(
            user_id=user_id,
            conversation_id=conversation_id,
            limit=12,
        )
        summaries = await self.store.rolling_summaries(
            user_id=user_id,
            conversation_id=conversation_id,
            limit=2,
        )
        recall = await self.retriever.recall(
            user_id=user_id,
            query=latest_user_text,
            limit=self.recall_limit_for_model(model_ref),
        )

        messages: list[Message] = []
        messages.append(self.persona_system_message())
        if recall.selected_memories:
            messages.append(self.memories_system_message(recall.selected_memories))
        if summaries:
            messages.append(self.summary_system_message(summaries))
        messages.extend(recent_turns)
        messages.extend(requested_messages)
        return self.trim_to_budget(messages, model_ref=model_ref)

    def latest_user_text(self, messages: list[Message]) -> str:
        for message in reversed(messages):
            if message.role == "user":
                return message.content
        return ""

    def persona_system_message(self) -> Message:
        return Message(
            role="system",
            content="[redacted persona/system instruction]",
        )

    def memories_system_message(self, memories: list[Memory]) -> Message:
        lines = ["Relevant long-term memories:"]
        for memory in memories:
            lines.append(f"- {memory.summary}")
        return Message(role="system", content="\n".join(lines))

    def summary_system_message(self, summaries: list[str]) -> Message:
        lines = ["Recent conversation summaries:"]
        lines.extend(f"- {summary}" for summary in summaries)
        return Message(role="system", content="\n".join(lines))

    def recall_limit_for_model(self, model_ref: str) -> int:
        if "opus" in model_ref.lower():
            return 3
        return 5

    def trim_to_budget(self, messages: list[Message], model_ref: str) -> list[Message]:
        _ = model_ref
        # Production code estimates tokens and preserves system + recent turns.
        return messages
