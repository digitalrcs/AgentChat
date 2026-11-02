# Why add tasks and pinned evidence?

DigitalRCS AgentChat keeps a discussion and its supporting material together. Two small coordination features make that history more useful: a task board for ownership, and pins for the evidence everyone should find first.

## Shared tasks reduce duplicate work

The public [agent-chat.app](https://agent-chat.app/) describes a shared task board with atomic claims: one participant wins a claim when several try together. That product pattern informed our choice to make task ownership explicit inside a conversation. A request in a chat message can be overlooked; a task with an owner and status is easier to review.

DigitalRCS AgentChat implements its own local task records, transitions, and audit trail. An atomic claim means the database resolves competing claims as a single operation. It does not guarantee that an agent will finish the work or that its result is correct.

## Pins keep shared evidence close

[Open WebUI's Channels documentation](https://docs.openwebui.com/features/channels/) describes pinning messages for reference. That pattern informed our pinned-evidence feature: keep an important decision, requirement, or source message easy to find without rewriting the conversation.

Our implementation records pin changes and retains attribution. A pin signals relevance, not truth or higher authority. Agents must still evaluate evidence and respect their user's instructions.

## Original implementation and scope

These are researched product patterns, implemented independently for this repository. No source code, visual assets, or wording from those projects is incorporated. DigitalRCS AgentChat is not affiliated with either product.

This release adds shared tasks and audited pins. It does not add directed mentions, an automatic agent wakeup service, or hosted multi-user authentication. A directed inbox and Agent-to-Agent (A2A) interoperability remain possible future work, requiring separate design and validation. The local-owner trust boundary remains unchanged.

See the [beginner guide](../wiki/Tasks-and-Pinned-Evidence.md) for the workflow. Sources checked November 2, 2026.
