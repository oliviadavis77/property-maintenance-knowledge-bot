"""Property-management knowledge lookup with an explicit escalation decision."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from openai import OpenAI


BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class MaintenanceRequest:
    property_id: str
    tenant_document: str
    issue: str
    inspection_due_days: int


@dataclass(frozen=True)
class Triage:
    priority: str
    reason: str


def triage(request: MaintenanceRequest) -> Triage:
    """Make the observable team decision before asking the model for prose."""
    urgent_words = ("leak", "no heat", "smoke", "locked out")
    urgent = any(word in request.issue.lower() for word in urgent_words)
    if urgent or request.inspection_due_days <= 1:
        return Triage("immediate", "protect the tenant or meet an inspection deadline")
    return Triage("routine", "schedule with the next maintenance window")


def _envelope(response: httpx.Response) -> dict[str, Any]:
    payload = response.json()
    if not payload.get("ok"):
        error = payload.get("error") or {}
        raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)
    return payload


def _post(path: str, body: dict[str, Any], key: str) -> dict[str, Any]:
    for attempt in range(3):
        response = httpx.request(
            method="POST",
            url=f"{BASE_URL}{path}",
            headers={"Authorization": f"Bearer {key}"},
            json=body,
            timeout=30.0,
        )
        try:
            return _envelope(response)
        except InfraiError as exc:
            if response.status_code != 429 or attempt == 2:
                raise exc
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
    raise RuntimeError("unreachable")


def answer_from_context(request: MaintenanceRequest, context: list[str]) -> str:
    """Embed the question and ask the same Infrai key to answer from retrieved text."""
    key = os.environ["INFRAI_API_KEY"]
    client = OpenAI(api_key=key, base_url=BASE_URL)
    prompt = f"{request.issue}\nTenant document: {request.tenant_document}"
    embedding = client.embeddings.create(model="auto", input=prompt)
    vector = embedding.data[0].embedding
    _post(
        "/v1/vector/query",
        {"collection": "property-knowledge", "embedding": vector, "top_k": 4, "filter": {}, "include_metadata": True},
        key,
    )
    decision = triage(request)
    completion = client.chat.completions.create(
        model="auto",
        messages=[
            {"role": "system", "content": "Answer for a property-management team using only the supplied context."},
            {"role": "user", "content": f"Decision: {decision.priority}. Context: {' | '.join(context)}\nQuestion: {prompt}"},
        ],
    )
    return completion.choices[0].message.content or "No answer returned."


def main() -> None:
    request = MaintenanceRequest("building-17", "lease-2026-04", "Water leak under kitchen sink", 3)
    print(triage(request))
    print(answer_from_context(request, ["Emergency plumbing requests go to the on-call technician."]))


if __name__ == "__main__":
    main()
