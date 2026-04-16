"""
Redacted model routing interface for Starland Gateway.

The real service supports multiple providers and provider-specific clients.
This skeleton shows the routing contract without exposing keys or private
configuration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelRef:
    provider: str
    model: str


class CompletionClient(Protocol):
    async def complete(self, model: str, messages: list[object]) -> str:
        ...


class ModelRouter:
    """
    Resolve explicit `provider:model` strings and enforce optional strict model
    checks for models where alias/snapshot confusion matters.
    """

    strict_models: set[str] = {"gpt-4.1", "gpt-5.1"}

    def resolve(self, model_ref: str) -> tuple[str, str]:
        value = model_ref.strip()
        if ":" not in value:
            raise ValueError("Expected model ref in provider:model format.")

        provider, model = value.split(":", 1)
        provider = provider.strip().lower()
        model = model.strip()
        if not provider or not model:
            raise ValueError("Provider and model must both be present.")

        # Date snapshots are normalized for comparison and cost-control
        # reasoning, while product variants such as mini/nano stay distinct.
        model = self.normalize_snapshot_alias(model)
        return provider, model

    def normalize_snapshot_alias(self, model: str) -> str:
        lowered = model.strip().lower()
        if re.match(r"^gpt-4\.1-\d{4}-\d{2}-\d{2}$", lowered):
            return "gpt-4.1"
        if re.match(r"^gpt-5\.1-\d{4}-\d{2}-\d{2}$", lowered):
            return "gpt-5.1"
        return model

    def assert_response_model_matches(
        self,
        requested_model: str,
        response_model: str | None,
    ) -> None:
        requested = self.normalize_snapshot_alias(requested_model).lower()
        actual = self.normalize_snapshot_alias(response_model or "").lower()

        if requested not in self.strict_models:
            return
        if not actual:
            raise RuntimeError("Provider response did not include a model name.")
        if actual != requested:
            raise RuntimeError(
                f"Strict model mismatch: requested={requested}, response={actual}"
            )


class ProviderClient:
    """
    Factory for provider clients.

    In production, each provider client owns API-specific request/response
    handling. This redacted example returns a demo client.
    """

    @staticmethod
    def for_provider(provider: str) -> CompletionClient:
        if provider not in {"openai", "claude", "deepseek", "zhipu"}:
            raise ValueError(f"Unsupported provider: {provider}")
        return DemoCompletionClient(provider=provider)


@dataclass
class DemoCompletionClient:
    provider: str

    async def complete(self, model: str, messages: list[object]) -> str:
        _ = (model, messages)
        return (
            f"[redacted demo] Response generated through the {self.provider} "
            "provider interface."
        )
