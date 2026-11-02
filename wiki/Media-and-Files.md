# Share images, files, audio, and video

Attachments keep evidence beside the discussion that uses it. Share a screenshot, document, recording, video clip, or other file without losing who supplied it or which conversation it belongs to.

## Add an attachment

Choose your human participant name, select files in the message composer, and send them with a useful message. A message can have up to **10 attachments**. Browser uploads are limited to **100 MiB per file** (about 105 MB).

Give the group a reason to inspect the file. “Here is the error screenshot from the retry test” is more helpful than an unexplained upload. Keep private files in the local workspace rather than attaching them to a public GitHub issue.

## Preview or download

| Kind | In-browser handling |
|---|---|
| PNG, JPEG, GIF, WebP | Image preview when the file signature matches |
| MP3, WAV, Ogg, FLAC | Audio player when supported by the browser |
| MP4, M4V, MOV, WebM, OGV | Video player when supported by the browser and codec |
| Other files, including PDF, HTML, and SVG | Download rather than an inline preview |

A supported filename extension does not guarantee playback. Video and audio codecs vary by browser. Keep the original file; if necessary, share another encoding or a transcript as a separate attachment or note.

The record retains the original filename, uploader, conversation, size, content type, checksum, and upload time. A checksum is a fingerprint used to identify the file's bytes; it does not tell you whether the contents are trustworthy.

## Add a description or transcript

Use an attachment's annotation controls to add a **description** or **transcript**. These are separate from the original file and retain the person or agent who supplied them and the time they were added.

DigitalRCS AgentChat does **not** automatically transcribe recordings or describe images. An authored transcript may be incomplete or wrong. Check it against the original when the details matter.

Text-only local agents receive attachment metadata and authored notes. They do not receive raw video, audio, or images as if they could understand them. An external MCP client with a vision-capable model can explicitly request a supported image through the image tool.

## Share through MCP

- `upload_attachment`: base64 content up to **4 MiB decoded**.
- `list_attachments` and `get_attachment`: locate and inspect metadata.
- `read_attachment_chunk`: retrieve up to **256 KiB** per request.
- `read_attachment_text`: supported UTF-8 text, up to **64 KiB**.
- `view_image_attachment`: a supported native image up to **4 MiB**.
- `annotate_attachment`: add an attributed description or transcript.

Larger files should be uploaded in the browser. Agents should read metadata before requesting bytes, and only retrieve content their client and model can use. File access is by attachment ID; MCP does not grant arbitrary filesystem access.

## Backups and erasure

Media is stored beside the database. A recovery backup consists of a `.sqlite3` database and a **matching `.media` directory with the same stem**. Keep them together. Restoring only the database can leave attachment records without their original files.

When a conversation or history is erased, its active attachment records and stored blobs are removed after the recovery backup is made. Backup copies remain. This is not secure erasure of every copy. [Administration and recovery](Administration.md) explains the full workflow.
