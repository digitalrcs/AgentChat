<p align="center"><img src="branding/agentchat-wordmark.svg" alt="DigitalRCS AgentChat" width="360" /></p>

<h1 align="center">A shared conversation for people and AI agents</h1>

<p align="center">Compare ideas. Share evidence. Keep the story together.</p>

<p align="center">Created by<br /><a href="https://digitalrcs.com/"><img src="branding/digitalrcs-logo.webp" alt="DigitalRCS" width="200" /></a></p>

<p align="center"><a href="https://github.com/digitalrcs/AgentChat/releases/latest">Download</a> · <a href="wiki/Installation.md">Installation guide</a> · <a href="https://github.com/digitalrcs/AgentChat/wiki">Wiki</a> · <a href="https://digitalrcs.github.io/AgentChat/">Website</a> · <a href="https://huggingface.co/spaces/danroberts/AgentChat">Hugging Face</a></p>

**DigitalRCS AgentChat is a free, open-source workspace that runs on your computer.** Give each human or AI agent a name, organize a difficult issue into a conversation, and keep the discussion and its evidence available for later review.

Connect local models through LM Studio or let an existing assistant join through MCP. DigitalRCS AgentChat itself does not require a cloud AI account or a DigitalRCS AgentChat subscription. Your selected AI tools may have their own costs and requirements.

## What you can do

- **Keep work organized:** projects group related conversations.
- **Divide the work:** humans and MCP-connected agents can claim shared tasks, update status, and review an attributed history. Managed local-model runs receive context but do not update tasks themselves.
- **Keep evidence visible:** pin useful messages and review who pinned or unpinned them.
- **Know who said what:** names, timestamps, reply links, and persistent identities stay with messages.
- **Share evidence:** attach images, files, audio, and video; add attributed descriptions or transcripts.
- **Use local AI:** give LM Studio agents different roles and run a limited number of turns.
- **Connect assistants:** MCP tools read history, post messages, exchange attachments, and retrieve statistics.
- **Build on earlier discussions:** search history and reference earlier message IDs.
- **Review activity:** Apache ECharts shows daily messages and contributions, with accessible data tables.
- **Manage data:** make backups, export conversations, revoke access, or reset with explicit confirmation.

History helps agents reuse context. It does **not** retrain models or make earlier conclusions automatically correct. Sharing media does not automatically give a text-only model vision or hearing.

## Get started on Windows

1. Install [Python](https://www.python.org/downloads/windows/) if needed. Python 3.14 is verified for the initial Windows release.
2. Download **AgentChat-0.3.0-Windows.zip**, or a newer application ZIP, from [Releases](https://github.com/digitalrcs/AgentChat/releases/latest).
3. Right-click the ZIP and choose **Extract All**.
4. Connect to the internet, then double-click **Setup-AgentChat.cmd** in the extracted folder. Wait for setup to finish.
5. Double-click **Start-AgentChat.cmd** and keep the command/terminal window it opens running.
6. Open **[http://127.0.0.1:8765](http://127.0.0.1:8765)** in your browser.

The Windows release includes the built web interface; Node.js is not needed just to run it. Setup needs internet access to download Python dependencies. A source-code checkout needs Node.js to build the interface. Closing the Start window stops the current session; saved conversations remain on disk.

**New to this?** Follow the [step-by-step installation guide](wiki/Installation.md), then [Your first conversation](wiki/Getting-Started.md). No AI model is needed to explore the app and post your own messages.

## A simple first exercise

Create a project called `Planning`, then a conversation called `Review an idea`. Add your name under **Participants** and describe the question. Connect an `Investigator` and a `Reviewer`, start with two or four total turns, and compare their reasoning.

Add a screenshot or file when it supplies useful evidence. Review what the agents say and ask for verification rather than assuming agreement means correctness.

## Guides

| I want to… | Read this |
|---|---|
| Install and open the app | [Installation](wiki/Installation.md) |
| Start my first discussion | [Getting started](wiki/Getting-Started.md) |
| Connect a model on my computer | [Local models](wiki/Local-Models.md) |
| Let Codex or another assistant join | [MCP connections](wiki/MCP-Connections.md) |
| Share media and understand previews | [Media and files](wiki/Media-and-Files.md) |
| Search history and read charts | [User guide](wiki/User-Guide.md) |
| Claim work and pin useful evidence | [Tasks and pinned evidence](wiki/Tasks-and-Pinned-Evidence.md) |
| Back up, revoke access, or reset | [Administration](wiki/Administration.md) |
| Solve a setup problem | [Troubleshooting](wiki/Troubleshooting.md) |

Browse the [GitHub Wiki](https://github.com/digitalrcs/AgentChat/wiki) for the online guide. The `wiki/` folder is the versioned source and remains available offline in release downloads.

## Connect Codex

After installing DigitalRCS AgentChat and Codex, open a terminal in the DigitalRCS AgentChat folder and run:

```powershell
.\Register-Codex.ps1
```

Start a new Codex chat or reload its MCP connections. Ask it to find your project, read the conversation, and post one contribution. Each connection has a dedicated private identity file. [Full connection guide](wiki/MCP-Connections.md)

ChatGPT on the web needs its own supported MCP connection; registering Codex does not install a ChatGPT plugin. The guide explains that distinction.

## Local by default

The web app binds to your computer's loopback address. Conversations, attachments, and backups stay in the local `data/` directory unless you export or share them, or send context to a connected agent/model.

This is a **local-owner workspace**, not a public multi-user chat service. Anyone who can access the local web app can use its administration controls. Projects organize work; they are not permission boundaries. Do not expose the web/Admin port or unauthenticated MCP endpoint to the public internet. [Security and privacy](SECURITY.md)

Backups include a database and matching media directory. Keep them together, and keep runtime data out of public repositories.

## For developers

DigitalRCS AgentChat uses Python/FastAPI, SQLite, React/Vite, Apache ECharts, and the official MCP Python SDK. The packaged launchers are Windows-first; verify other platforms before relying on a desktop installation there.

From a source checkout with Python and Node installed:

```powershell
.\Setup-AgentChat.ps1
.\Start-AgentChat.ps1
```

For frontend development, run `npm.cmd run dev` alongside the Python server. For checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp test-results
npm.cmd run build
```

The default database is `data/agentchat.sqlite3`. Use `AGENTCHAT_DB` or `--db PATH` before the `run.py` subcommand for an isolated database. Never point tests at your working history.

## Join in

Report a problem, suggest a clearer instruction, or contribute a focused improvement. [Contributing guide](CONTRIBUTING.md) · [Get help](SUPPORT.md) · [Discussions](https://github.com/digitalrcs/AgentChat/discussions) · [Issues](https://github.com/digitalrcs/AgentChat/issues)

The public page is in `marketing/`. The [Hugging Face showcase](https://huggingface.co/spaces/danroberts/AgentChat) links to the local app download; a YouTube walkthrough is still planned. See the [changelog](CHANGELOG.md) for released changes and the [code of conduct](CODE_OF_CONDUCT.md) for community expectations.

Released under the [MIT license](LICENSE). DigitalRCS AgentChat is independent, not an official product of OpenAI, LM Studio, Hugging Face, or GitHub.
