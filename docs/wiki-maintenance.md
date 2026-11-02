# Maintaining the GitHub Wiki

The public Wiki is at <https://github.com/digitalrcs/AgentChat/wiki>. Its editable source is the main repository's `wiki/` directory, which is also included in Windows downloads. Propose documentation changes there so they can be reviewed with pull requests.

GitHub stores a native Wiki in a separate Git repository. Enabling the feature alone does not create its first page. A maintainer must create and save an initial Home page through GitHub's website once. See [GitHub's Wiki instructions](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).

After the initial page exists, publish reviewed guides from the project root:

```powershell
git clone https://github.com/digitalrcs/AgentChat.wiki.git .wiki-publish
.\.venv\Scripts\python.exe scripts/prepare_wiki.py
git -C .wiki-publish diff --check
git -C .wiki-publish diff
git -C .wiki-publish add -- '*.md'
git -C .wiki-publish commit -m "Update user guides"
git -C .wiki-publish push origin HEAD
```

If the checkout already exists, run `git -C .wiki-publish pull --ff-only` instead of cloning. Review any web edits and bring useful changes back into `wiki/` before preparing another publication. The preparation script replaces matching page files but does not delete extra pages or publish anything itself. It translates `.md` links to native Wiki page URLs and rejects missing page references.

Verify Home, the sidebar, and at least one linked guide on the public website after pushing. Keep credentials out of scripts and source files; use the maintainer's existing Git credential helper. Wiki publication is a separate explicit step, so a main-repository push alone does not update the Wiki.
