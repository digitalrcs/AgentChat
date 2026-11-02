"""Prepare public files for upload to the AgentChat Static Hugging Face Space."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent.parent
out = ROOT / '.publish-staging' / 'huggingface'
out.mkdir(parents=True, exist_ok=True)
html = (ROOT / 'marketing/index.html').read_text(encoding='utf-8').replace('assets/', '')
# Hugging Face embeds the page: external destinations must open outside its iframe.
html = re.sub(r'<a href="(https://[^"]+)"', r'<a target="_blank" rel="noopener noreferrer" href="\1"', html)
html = re.sub(r'<a class="([^"]+)" href="(https://[^"]+)"', r'<a class="\1" target="_blank" rel="noopener noreferrer" href="\2"', html)
(out / 'index.html').write_text(html, encoding='utf-8')
for source in [ROOT/'marketing/style.css', ROOT/'LICENSE', ROOT/'huggingface/README.md', *(ROOT/'marketing/assets').glob('*.svg')]:
    shutil.copy2(source, out/source.name)
print(f'Upload the seven public files from {out} to the Space root.')
