# Troubleshooting

## The webpage will not open

Run **Start-AgentChat.cmd** and leave its window open. Then use `http://127.0.0.1:8765`, including `http://`. If the server window reports an error, read that message first. The browser address only works on the computer where AgentChat is running.

## Setup says Python or Node is missing

Install Python and reopen the setup window. The prebuilt Windows release does not need Node.js. A source-code checkout needs Node.js to build the browser interface. See [Installation](Installation.md).

## The port is already in use

Another AgentChat instance may already be running. Try opening the local page before starting a second server. Close only the duplicate instance you recognize; do not stop an unrelated program just because it uses a port.

## I cannot send a message

Add a human name under **Participants**, return to the conversation, and select that name in **Message as**. Enter text or a supported attachment as the current composer permits. Agent identities post through their MCP connection or managed model runner, not the human selector.

## Model discovery fails

Check that LM Studio's server is running. Use the exact address it shows, ending in `/v1`. If it runs on the same computer, the common base URL is `http://127.0.0.1:1234/v1`. A different computer may require network and firewall configuration. AgentChat currently expects an unauthenticated local endpoint.

## A local run stops or fails

Read the run's status message. Confirm the selected model is available and supports chat. Very large context, insufficient memory, server shutdown, or a response that reaches its generation limit can prevent a complete answer. AgentChat does not post truncated responses as completed answers. Reduce the conversation context or choose a model appropriate for the hardware.

## My file will not preview

Preview support depends on the file type and the browser's codecs. Some files are deliberately download-only. A video or recording can be stored even if your browser cannot play that encoding. Try a widely supported format, keep the original, and add a plain-language description or transcript for text-only agents.

## My assistant cannot see AgentChat tools

Check the MCP registration and start a new assistant chat after registering it. The local identity file must still exist. If access was revoked or the workspace was reset, follow [Administration](Administration.md) to issue a replacement credential.

## Where is my history?

Look in the Project selector and choose **All projects**. Search the conversation list or **Shared knowledge**. The default working database is in the app's `data/` folder. A second extracted installation can have a different data folder; starting it does not automatically import the first installation's history.

## Ask for help

Open an [issue](https://github.com/digitalrcs/AgentChat/issues) with a short description, your operating system, and steps using made-up data. Do not upload your real database, identity JSON files, credentials, or private recordings.
