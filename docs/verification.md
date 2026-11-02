# Verification record

DigitalRCS AgentChat 0.3.0, verified November 1, 2026. Destructive checks and synthetic conversations used isolated databases. Working chat history was preserved and backed up before upgrade.

- **36 backend tests passed**: persistent identities/history, projects/search/statistics, real stdio MCP, revocation, media ownership and retries, safe downloads and byte ranges, backup/restore, reset behavior, atomic task claims and ownership conflicts, audited status changes, pins, exports, and local-model context.
- **Production frontend build passed.** ECharts loads on demand. Vite reports the approximately 535 KB analytics chunk as large; it does not block the initial conversation interface.
- **Edge browser regression passed** with isolated mocked APIs: media playback and upload recovery, task creation/claim/status/history, conflict refresh, explicit human override, stale-data failure handling, pins, and mobile layout.
- **Real HTTP workflow checked in Brave** with an isolated database: created and claimed a task, completed it, and pinned a message with original-author and pinner attribution. The DigitalRCS branding and marketing page were visually checked.
- Opening the app from another site now permits only top-level navigation to its app shell. Regression tests confirm that cross-origin API access, downloads, iframe embedding, and writes remain blocked.
- An existing database backup was upgraded separately: original participant, conversation, message, and attachment counts were unchanged, and SQLite integrity checking passed.
- The earlier local-model smoke test completed two turns under distinct agent names. Runner tests verify bounded task/pin context and attributed media notes. The built-in text-only runner does not invoke MCP tools or automatically claim tasks.
- Codex registration is enabled locally. The development team used dedicated MCP identities to record decisions in the application. Reloading a Codex connection is needed to discover newly added tools.

## Publication and limits

Source, installation guides, and release downloads are published on GitHub. GitHub Actions verifies Windows/Python 3.14 and Ubuntu/Python 3.12; inspect the workflow attached to the release commit for its current result. The Hugging Face Space is a static product and download showcase, not a hosted chat backend. GitHub Pages hosts the marketing page. Wiki-style guides are maintained in the repository's `wiki/` folder.

The web app is a trusted local-owner workspace, not an authenticated public chat service. ChatGPT account/tunnel integration, public MCP catalog acceptance, and YouTube upload have not been performed. Media codec support depends on the browser. Text-only models use descriptions/transcripts, not direct media interpretation. Shared knowledge is retrieved context, not model training.

The suite emits one upstream Starlette TestClient deprecation warning for its httpx integration. Dependencies are pinned to the validated versions.

## Reproduce

From a source checkout after setup:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp test-results
npm.cmd run build
$env:AGENTCHAT_BROWSER_CHANNEL = 'msedge'
node tests/media-browser.mjs
.\.venv\Scripts\python.exe scripts/package_release.py
```

The browser regression can use Playwright's installed Chromium by omitting the channel variable. Fixtures are synthetic; browser results are written under ignored `data/`. Never direct tests at the working chat database. Windows release ZIPs include the built interface and can be installed without Node.js.
