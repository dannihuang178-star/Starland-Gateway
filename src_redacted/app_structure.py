"""
Redacted application structure for Starland Gateway.

This file is intentionally incomplete. It shows the public architecture shape of
the gateway without private prompts, provider keys, database schema details, or
business-specific memory rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request

from routing_interface import ModelRouter, ProviderClient
from memory_interface import ContextAssembler, MemoryStore


Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ChatMessage:
    role: Role
    content: str


@dataclass
class ChatRequest:
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    user_id: str = "demo-user"
    conversation_id: str | None = None


@dataclass
class ChatResponse:
    conversation_id: str
    assistant_message: str


app = FastAPI(title="Starland Gateway (Redacted)")
router = ModelRouter()
memory_store = MemoryStore()
context_assembler = ContextAssembler(memory_store=memory_store)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Native gateway endpoint.

    The real implementation also persists messages, handles telemetry, and
    schedules background post-chat tasks.
    """
    provider, model_name = router.resolve(req.model)
    client = ProviderClient.for_provider(provider)

    assembled_messages = await context_assembler.build_context(
        user_id=req.user_id,
        conversation_id=req.conversation_id,
        requested_messages=req.messages,
        model_ref=req.model,
    )

    assistant_message = await client.complete(
        model=model_name,
        messages=assembled_messages,
    )

    conversation_id = req.conversation_id or "generated-conversation-id"
    await enqueue_post_chat_work(
        user_id=req.user_id,
        conversation_id=conversation_id,
        user_messages=req.messages,
        assistant_message=assistant_message,
    )

    return ChatResponse(
        conversation_id=conversation_id,
        assistant_message=assistant_message,
    )


@app.post("/v1/chat/completions")
async def openai_compatible_chat(req: dict[str, Any]) -> dict[str, Any]:
    """
    OpenAI-compatible surface for clients that already speak the Chat
    Completions protocol.
    """
    try:
        provider, model_name = router.resolve(str(req.get("model", "")))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    messages = [
        ChatMessage(role=item["role"], content=item["content"])
        for item in req.get("messages", [])
    ]
    assembled_messages = await context_assembler.build_context(
        user_id=str(req.get("user_id", "demo-user")),
        conversation_id=req.get("conversation_id"),
        requested_messages=messages,
        model_ref=str(req.get("model", "")),
    )

    client = ProviderClient.for_provider(provider)
    assistant_message = await client.complete(
        model=model_name,
        messages=assembled_messages,
    )
    router.assert_response_model_matches(
        requested_model=model_name,
        response_model=model_name,
    )

    return {
        "id": "chatcmpl-redacted",
        "object": "chat.completion",
        "model": req.get("model"),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": assistant_message},
                "finish_reason": "stop",
            }
        ],
    }


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> dict[str, str]:
    """
    Redacted Telegram entrypoint.

    The real service validates Telegram's secret header, checks an allowed chat
    list, normalizes text/voice/image/sticker inputs, and routes them through a
    Telegram-specific lightweight context builder.
    """
    _ = await request.json()
    return {"status": "accepted"}


@app.post("/mcp")
async def mcp_entrypoint(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Redacted MCP entrypoint.

    The real implementation exposes controlled knowledge-base tools such as
    note search, note read, note write, and note listing.
    """
    return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {}}


async def enqueue_post_chat_work(
    user_id: str,
    conversation_id: str,
    user_messages: list[ChatMessage],
    assistant_message: str,
) -> None:
    """
    Schedule memory and summary jobs after the response path completes.

    The production version uses an async queue and worker loop. This skeleton
    only shows the boundary between realtime chat and heavier background work.
    """
    _ = (user_id, conversation_id, user_messages, assistant_message)
