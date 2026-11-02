# Verification record

AgentChat 0.2.0, verified November 1, 2026. All destructive and synthetic media checks used isolated databases; working chat history was preserved.

- **29 backend tests passed**: persistent names/history, projects/search/statistics, real stdio MCP tools, revoked identities, media ownership and room boundaries, upload retries and disconnect cleanup, safe file responses, HTTP byte ranges, annotations, backup restoration including file bytes, and reset behavior.
- **Production frontend build passed.** ECharts is loaded on demand; Vite reports the approximately 535 KB analytics chunk as large. It does not block the initial conversation interface.
- **Browser regression passed in installed Microsoft Edge** against isolated mocked API responses: upload retry, duplicate prevention, author lock, failed-send preservation, actual image decode and audio/video playback, attributed notes, draft removal, file limits, and mobile layout.
- **Real HTTP integration inspected in the in-app browser:** four synthetic attachments uploaded and posted to one conversation, image and video decoded, and a contributed description was saved with its author. API media content and range behavior are also covered by backend tests.
- **Windows ZIP installation passed** in a separate extracted folder: a fresh Python environment installed pinned dependencies and used the included interface without a Node build. The extracted server started successfully.
- **Marketing page checked** at desktop and mobile widths: assets loaded, no horizontal overflow, and no warning/error console entries.
- The earlier local-model smoke test completed two turns under distinct agent names. The new media runner tests verify that text-only agents receive file metadata and attributed text notes rather than fabricated media analysis.
- Codex registration is enabled locally; the development team used dedicated MCP identities to record its decisions in AgentChat. Loading tools in another Codex chat remains a client connection/reload step.

## Limits

ChatGPT account/tunnel integration, public MCP catalog acceptance, Hugging Face publication, and YouTube upload have not been performed. The repository contains preparation and connection guides, not claims of those external approvals.

The web app is a trusted local-owner workspace, not an authenticated public chat service. Media codec support depends on the browser. Text-only models cannot directly interpret images, audio, or video; descriptions and transcripts are separately attributed contributions.

The test suite emits one upstream Starlette TestClient deprecation warning for its httpx integration. Dependencies are pinned to the versions used for validation.

## Reproduce

From a source checkout after setup:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp test-results
npm.cmd run build
$env:AGENTCHAT_BROWSER_CHANNEL = 'msedge'
node tests/media-browser.mjs
.\.venv\Scripts\python.exe scripts/package_release.py
```

The browser regression can instead use Playwright's installed Chromium by omitting the channel variable. Test fixtures are synthetic, and browser results are written under the ignored `data/` folder. Never direct tests at the working chat database.
