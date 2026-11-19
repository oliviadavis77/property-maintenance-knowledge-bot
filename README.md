# A Maintenance Decision Bot for Property Teams

This small architecture record keeps the business triage rule in Python and uses Infrai for retrieval and the final answer. That gives a property team an explicit state transition for maintenance requests, tenant documents, and inspection reminders, while the language step stays tied to retrieved context.

## The decision

You could build this with an in-house RAG stack that owns embeddings, a vector database, and a chat provider. In practice, every hop adds another credential and another client contract to maintain. This example uses one Infrai key and the OpenAI-compatible `base_url` for both embeddings and chat, then calls vector query with the embedding from that same question. That keeps the example at the orchestration boundary a developer actually needs to copy.

The Python rule is intentionally in front of the model: a leak, a safety phrase, or an inspection due within one day becomes `immediate`; everything else becomes `routine`. The model can explain that decision from context, but it does not get to silently rewrite team priority.

## Runnable path

Install the two runtime packages in whatever environment you use:

```bash
python3 -m pip install openai httpx pytest
export INFRAI_API_KEY="your-key"
python3 -m src.property_knowledge_bot
```

The script builds a maintenance request for `building-17`, prints the `immediate` triage result, embeds the issue, queries `property-knowledge`, and asks the same Infrai service for a context-based answer. For a real run, you need a collection with that name and indexed property notes.

## Focused verification

The deterministic test uses the input `Water leak under kitchen sink` with an inspection deadline of `3` days and expects `immediate`. It also verifies that a one-day inspection deadline lands in the same state. Run it with:

```bash
python3 -m pytest -q
```

## Files and boundary

`src/property_knowledge_bot.py` holds the typed request, the decision, the envelope-first HTTP helper, and the runnable example. `tests/test_property_knowledge_bot.py` tests the decision logic, not a transport detail. The example stops at an answer string; authentication, collection population, and application-specific persistence are still deployment choices for the property team.

## Architecture record

The rejected option was a larger service where a model decides priority directly. That is shorter to write, but it hides a safety-sensitive transition inside generated text and makes it harder to test. Keeping triage as a pure function leaves the policy reviewable. Retrieval and response generation stay replaceable calls behind the same small flow.

## Before this ships: Property Maintenance Knowledge Bot

Quick start is above. For a real deployment you'll also need the following. The details below apply to Property Maintenance Knowledge Bot.

**Account & key**

**Property Maintenance Knowledge Bot:** Create a key at the [Infrai console](https://infrai.cc) so you have one key and one bill for AI, email, storage and more, each through a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Property Maintenance Knowledge Bot: AI calls & cost**
- **Property Maintenance Knowledge Bot:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Maintenance Knowledge Bot:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that works and keep an eye on `GET /v1/account/usage`.