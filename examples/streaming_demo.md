# Streaming Demo

Starland Gateway exposes an OpenAI-compatible streaming surface through:

```text
POST /v1/chat/completions
```

When `stream=true`, the response is returned as server-sent events. The client can render each delta as it arrives while the gateway still owns model routing, context assembly, and post-chat background work.

## Example Request

```json
{
  "model": "openai:gpt-4.1",
  "stream": true,
  "messages": [
    {
      "role": "user",
      "content": "Explain why recent turns should stay in the prompt even when memory recall exists."
    }
  ]
}
```

## Example Stream Shape

```text
data: {"id":"chatcmpl-demo","object":"chat.completion.chunk","model":"openai:gpt-4.1","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-demo","object":"chat.completion.chunk","model":"openai:gpt-4.1","choices":[{"index":0,"delta":{"content":"Recent turns preserve"},"finish_reason":null}]}

data: {"id":"chatcmpl-demo","object":"chat.completion.chunk","model":"openai:gpt-4.1","choices":[{"index":0,"delta":{"content":" the immediate conversational intent."},"finish_reason":null}]}

data: {"id":"chatcmpl-demo","object":"chat.completion.chunk","model":"openai:gpt-4.1","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

## Notes

- The gateway can inspect the upstream response model and apply strict model checks for selected models.
- The final assistant message can be persisted after streaming completes.
- Memory and summary updates are handled by background workers, not by blocking the streaming path.
- This file is a redacted public example. It does not include private prompts, provider keys, or real user data.
