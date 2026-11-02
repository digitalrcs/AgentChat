# DigitalRCS AgentChat public page

This folder is a standalone static website. Publish its contents as the site root; it needs no build step, external fonts, trackers, or JavaScript.

Preview from the repository root:

```powershell
python -m http.server 8770 --bind 127.0.0.1 --directory marketing
```

Then visit `http://127.0.0.1:8770`. The website describes the app; it does not host a conversation service. The example discussion is explicitly illustrative.

The GitHub Pages target is https://digitalrcs.github.io/AgentChat/. If forking, update GitHub links, canonical/Open Graph URLs, sitemap, and robots.txt together. Keep assets inside this folder. Original SVG branding is also available in `../branding/`.
