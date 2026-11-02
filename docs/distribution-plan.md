# Sharing AgentChat more widely

This is a distribution plan, not a claim that a Hugging Face Space or YouTube video has been published. GitHub is the source of truth for code, releases, and versioned guides.

## Recommended next step: a Hugging Face showcase

Publish the existing `marketing/` page as a **Static HTML Space**. It introduces the project and links to the Windows download and guides. It does not run a shared chat server or accept conversations.

Hugging Face documents Static Spaces as free for everyone and supports plain HTML with `sdk: static`. No Python backend is needed for this showcase. [Official Static HTML Spaces guide](https://huggingface.co/docs/hub/spaces-sdks-static)

When the owner is ready to publish:

1. Choose the intended Hugging Face account and create a public Space with the Static SDK and MIT license.
2. Copy `marketing/index.html`, `marketing/style.css`, and `marketing/assets/` into its root. Keep the existing GitHub download links.
3. Add a README with this metadata, followed by a short project description:

```yaml
---
title: AgentChat
emoji: 💬
colorFrom: blue
colorTo: green
sdk: static
app_file: index.html
pinned: false
license: mit
---
```

4. Describe it as a **project showcase for a local application**. Do not imply that visitors can chat on that page.
5. Check the public page on a phone and desktop, and verify its download and documentation links. Add the verified Space URL to the project README only after publication.

Publish only the static files and license. Runtime data, backups, private model endpoints, and agent credentials do not belong in the Space.

## A live hosted demonstration is separate future work

The current app trusts its local owner. Hosting it publicly would require authentication, project permissions, upload quotas, abuse controls, and a persistence/recovery design. A cloud Space also cannot automatically reach an LM Studio server on a visitor's computer. These are architectural changes, not a switch in the marketing page.

Do not advertise a free hosted Docker instance: the current Spaces overview says compute-based Docker/Gradio creation requires an eligible paid plan, even where basic CPU hardware has no hourly charge. Recheck account eligibility and pricing before committing. [Spaces overview](https://huggingface.co/docs/hub/spaces-overview)

Space disks are ephemeral. Hugging Face now documents attached Storage Buckets for persistence; SQLite locking and durability on the chosen storage need separate validation before storing chat history there. [Spaces disk usage](https://huggingface.co/docs/hub/spaces-storage)

## A future YouTube introduction

Use a short, captioned screen recording of a fresh demonstration workspace. Show one project, named participants, a small local-model discussion, an attachment, history search, metrics, and a backup. Keep real personal history and credentials out of the recording. The [walkthrough script](youtube-walkthrough.md) is ready for a later recording session.

## Publication record

After each actual launch, record the public URL, date, version demonstrated, and a link check. Keep planned channels clearly separate from published channels. This research was checked against the official sources on November 1, 2026; hosting policies can change.
