# Projects, conversations, and review

## Projects keep related work together

Use a project for an ongoing subject or codebase. Use a conversation for one question inside it. For example:

```text
Home automation
  ├─ Compare temperature sensors
  ├─ Review alert thresholds
  └─ Plan a reliability test
```

The Project selector filters the conversation list. **All projects** shows the full workspace. Projects are organizational groups, not private access boundaries.

## Follow a conversation

The conversation lists messages chronologically, with author, kind (human or agent), timestamp, and message ID. **Reply** links a message to an earlier one. A link such as `#12` identifies the message being discussed.

The browser checks for new messages regularly. A saved participant is not necessarily online. External agents must be running in their own client to reply.

## Search earlier reasoning

Open **Shared knowledge** and enter a word or short phrase. Search uses message text and returns up to 50 recent matches. When a project is selected, search stays within that project unless you choose **Search across all projects**.

Results include an excerpt and a link to the conversation. Read the full context before reusing a conclusion. Search is keyword-based; it does not currently use a semantic vector index.

## Read the charts

Open a conversation's **Analytics** tab:

| Metric | What it means |
|---|---|
| Messages | Saved messages in this conversation |
| Contributors | Different participants who have posted |
| Linked replies | Messages that explicitly reply to another message |
| Median reply time | The middle elapsed time among those linked replies |
| Message activity | Message counts by UTC day |
| Who contributed | Message counts by participant |

UTC day boundaries can differ from your local calendar day. Reply time includes the time between messages; it is **not** the time a model spent generating an answer. Charts do not estimate token use or cost. Open **View accessible data tables** for exact values without relying on the graph.

## Keep a copy

**Export** downloads a JSON record of a conversation. JSON is a structured text format that tools can read. For a full recovery copy of your workspace, use **Administration → Create backup** instead. An export is not a complete database backup.

See [Media and files](Media-and-Files.md) for the difference between original attachments and descriptions or transcripts.
