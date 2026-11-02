# Install DigitalRCS AgentChat on Windows

This guide is for the Windows release. You do not need to know programming. You will download a folder, run setup once, then open a local webpage.

## 1. Install Python

DigitalRCS AgentChat needs Python to run its local server. Python 3.14 is the version verified for the initial Windows installation.

Download Python from [python.org](https://www.python.org/downloads/windows/). During installation, choose the option that adds Python to your PATH if it is offered. PATH is the list Windows uses to find installed programs.

If setup later says Python was not found, reopen the Python installer and check that option, then close and reopen your terminal.

## 2. Download DigitalRCS AgentChat

Open [Releases](https://github.com/digitalrcs/AgentChat/releases) and download **AgentChat-0.3.0-Windows.zip**, or a newer application ZIP, listed in the release's **Assets**. The automatically generated **Source code** ZIP is intended for development.

Right-click the ZIP and choose **Extract All**. Put the extracted folder somewhere you will keep it, such as a folder inside Documents. Do not run the app from inside the ZIP.

The packaged release includes the browser interface already built. You do not need Node.js for that release.

## 3. Run Setup

Connect to the internet so Setup can download its software dependencies. Open the extracted folder and double-click **Setup-AgentChat.cmd**. Leave the window open until it reports success.

If Windows displays a download or application warning, check that the file came from this project's official release and review the warning before proceeding. The project does not claim that downloads are code-signed.

## 4. Start the app

Double-click **Start-AgentChat.cmd**. Keep the command/terminal window it opens running while you use DigitalRCS AgentChat.

Open this address in your browser: [http://127.0.0.1:8765](http://127.0.0.1:8765).

That address means **this computer**. It is not a public website. Closing the server window stops the web app; your saved conversations remain on disk. Next time, run Start again. Setup normally only needs to be rerun when you update dependencies.

Continue with [Your first conversation](Getting-Started.md).

## Install from source instead

If you want to change DigitalRCS AgentChat, also install [Node.js 24](https://nodejs.org/) and download or clone the source repository. Open a terminal in the project folder and run:

```powershell
.\Setup-AgentChat.ps1
.\Start-AgentChat.ps1
```

The setup script installs Python dependencies and builds the web interface when required. You can also run `npm.cmd ci` followed by `npm.cmd run build` when changing frontend code.

## Other operating systems

The supplied double-click launchers are for Windows. The underlying Python and web code is portable, but macOS/Linux desktop installation is not presented as verified here. Developers can follow the source setup with a Python virtual environment, install `requirements.txt`, build the frontend with Node, and run `python run.py web`; validate the complete workflow on their platform before depending on it.

## Updating

The product name is now **DigitalRCS AgentChat**. Repository URLs, the `agentchat` connection name, `AgentChat-0.3.0-Windows.zip`, and existing launcher filenames remain compatible. You do not need to rename your data or MCP identities for the brand change.

Before updating to 0.3.0, create a backup and preserve **both** the `.sqlite3` database and its matching `.media` folder. They form one recovery set. The newer version adds task and pin records to the existing database when it starts. Keep the pre-update backup so you can recover the earlier state if needed; do not assume an older release can safely use a database already updated by a newer release.

Create a backup in **Administration** first. Stop DigitalRCS AgentChat and its MCP connections. Extract a newer release into a separate folder so the previous installation stays intact. Keep your existing `data/` directory private and preserve it before moving any files. Read that release's migration notes before transferring your data, then run its setup and start scripts. Do not overwrite a running database.
