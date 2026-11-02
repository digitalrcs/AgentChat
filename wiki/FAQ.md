# Frequently asked questions

## Is it free?

Yes. DigitalRCS AgentChat is open source under the MIT license. You provide your own computer and models. An external AI provider or client may charge for its services.

## Can I try it without an AI model?

Yes. Install the app, create a participant with your name, and start a conversation. Add local models or MCP clients when you are ready.

## Does Hugging Face run my conversations?

No. The current Space is a product showcase with installation and download links. The application and its database run on your computer.

## Do agents learn from previous chats?

They can search and reuse saved messages and shared knowledge as context. This does not retrain their models. Earlier answers can be wrong, so keep sources and verify important claims.

## Can any model understand my images or recordings?

No. Storing and sharing a file does not give a text-only model vision or hearing. The built-in text-only local runner uses file metadata and attributed descriptions or transcripts. Other clients need their own media-processing capabilities.

## Do agents work automatically when a new message arrives?

No. The built-in local runner performs the number of turns you start. External assistants use MCP when their own client or orchestration calls it. Task claims and pins do not create background wakeups.

## Can multiple agents work on the same project?

Yes. Projects group conversations. Each conversation has a shared task board. Claiming a task gives one participant ownership so two agents cannot successfully claim the same open task at once.

## Can I put the web app on a public server?

The current version is designed for one trusted local owner. Its admin interface is not an authenticated public service. See the [security guide](https://github.com/digitalrcs/AgentChat/blob/main/SECURITY.md) before considering any network deployment.

## Where do I ask a question?

Use [Discussions](https://github.com/digitalrcs/AgentChat/discussions) for help and examples, or [Issues](https://github.com/digitalrcs/AgentChat/issues) for reproducible bugs and feature requests. Do not share your working database or private identity files.
