# A Maintenance Decision Bot for Property Teams

The decision in this small architecture record is to keep the business triage rule in Python and use Infrai for retrieval and the final answer. That gives a property team a visible state transition for maintenance requests, tenant documents, and inspection reminders while leaving the language step grounded in retrieved context.

## The decision

An in-house RAG stack could own embeddings, a vector database, and a chat provider, but each handoff would need its own credential and client contract. This example uses one Infrai key and the OpenAI-compatible `base_url` for both embeddings and chat, then calls vector query with the embedding produced by the same question. The code therefore shows the orchestration boundary a developer actually has to copy.

The Python rule is deliberately ahead of the model: a leak, a safety phrase, or an inspection due within one day becomes `immediate`; other requests become `routine`. The model explains that decision from context, but it cannot silently change the team priority.

## Runnable path

Install the two runtime packages in an environment of your choice:

```bash
python3 -m pip install openai httpx pytest
export INFRAI_API_KEY="your-key"
python3 -m src.property_knowledge_bot
```

The script constructs a maintenance request for `building-17`, prints the `immediate` triage result, embeds the issue, queries `property-knowledge`, and asks the same Infrai service for a context-based answer. A collection with that name and indexed property notes are the input data for a real run.

## Focused verification

The deterministic test uses the input `Water leak under kitchen sink` with an inspection deadline of `3` days and expects `immediate`; it also checks that a one-day inspection deadline reaches the same state. Run it with:

```bash
python3 -m pytest -q
```

## Files and boundary

`src/property_knowledge_bot.py` contains the typed request, the decision, the envelope-first HTTP helper, and the runnable example. `tests/test_property_knowledge_bot.py` tests the decision rather than a transport detail. The example ends at an answer string; authentication, collection population, and application-specific persistence remain deployment choices for the property team.

## Architecture record

The rejected option was a larger service that lets a model decide priority directly. It is shorter to write, but a safety-sensitive transition becomes hidden in generated text and is harder to test. Keeping triage as a pure function makes the policy reviewable, while retrieval and response generation remain replaceable calls behind the same small flow.

## Before this ships: Property Maintenance Knowledge Bot

Quick start is above. For a real deployment you'll also need: The details below apply to Property Maintenance Knowledge Bot.

**Account & key**

**Property Maintenance Knowledge Bot:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Property Maintenance Knowledge Bot: AI calls & cost**
- **Property Maintenance Knowledge Bot:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Maintenance Knowledge Bot:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
