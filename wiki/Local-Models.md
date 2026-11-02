# Connect a local AI model

A local model runs on your computer, or on another computer you control, rather than through a cloud AI service. AgentChat connects to [LM Studio](https://lmstudio.ai/), which manages and serves those models.

## Prepare LM Studio

1. Install LM Studio from its official website.
2. Download a model suitable for chat or instructions. Choose one that fits your computer's available memory.
3. Start LM Studio's local server and note its address. A common example is `http://127.0.0.1:1234`.

Follow the current [LM Studio server documentation](https://lmstudio.ai/docs/developer) for its interface. Model size, speed, capabilities, and license vary. AgentChat does not download models or choose a model for you.

## Add an agent in AgentChat

1. Open **Local agents**.
2. Enter the server's base URL ending in `/v1`, such as `http://127.0.0.1:1234/v1`.
3. Select **Discover models**.
4. Choose an exact model ID from the list. Use a chat model, not an embedding model.
5. Give the agent a unique name, such as `Investigator`.
6. Write its perspective: `State assumptions, inspect evidence, and propose a next step.`
7. Select **Add local agent**.

You can add a second agent named `Reviewer` with a role such as `Look for unsupported claims and suggest a way to test the proposal.` Both can use the same model, but different role prompts do not make them independent sources of truth.

## Run a discussion

First select a conversation. Return to **Local agents**, select the participants, and choose **Total turns** between 1 and 12. The number is the total messages generated across the selected agents, not turns per agent.

Optionally enter a search term to retrieve relevant past discussions from the conversation's project. Select **Start discussion**. Agents take turns in order; their replies appear in the conversation. Only one local discussion runs at a time.

**Stop run** stops further local work. The model server may finish a request that was already submitted, even after the app cancels waiting for it.

## What an agent receives

The runner supplies the objective, recent conversation text, relevant attachment context where supported, and optional past-history excerpts. The runner does not give models a shell or arbitrary file access. Text-only models need descriptions or transcripts to reason about media; attaching a video does not automatically make the model understand it.

The current adapter is for unauthenticated LM Studio endpoints on loopback or private IPv4 addresses. It does not automatically fall back to a cloud service. Only send content appropriate for the computer hosting the model.

The connection uses LM Studio's documented [OpenAI-compatible endpoints](https://lmstudio.ai/docs/developer/openai-compat). “OpenAI-compatible” describes the request format; it does not mean requests are sent to OpenAI.
