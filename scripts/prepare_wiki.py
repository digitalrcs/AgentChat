"""Copy versioned guides into a GitHub Wiki checkout with Wiki-compatible links.

Does not commit, push, delete pages, or read credentials. Initialize the Wiki's
first page on GitHub, then clone its .wiki.git repository before publishing.
"""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
WIKI_URL = 'https://github.com/digitalrcs/AgentChat/wiki/'


def render(text, pages):
    def replace(match):
        target, anchor = match.group(1), match.group(2) or ''
        if target not in pages:
            raise ValueError(f'Unknown local Wiki page: {target}')
        return f']({WIKI_URL}{target}{anchor})'
    return re.sub(r'\]\(([\w-]+)\.md(#[^)]*)?\)', replace, text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=ROOT/'.wiki-publish')
    args = parser.parse_args()
    destination = args.destination.resolve()
    source = ROOT/'wiki'
    if destination == ROOT or destination == source or source in destination.parents:
        raise SystemExit('Choose a separate staging directory or Wiki checkout.')
    guides = sorted(source.glob('*.md'))
    pages = {p.stem for p in guides}
    rendered = [(p.name, render(p.read_text(encoding='utf-8-sig'), pages)) for p in guides]
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in rendered:
        (destination/name).write_text(content, encoding='utf-8')
    print(f'Prepared {len(rendered)} Wiki files in {destination}. Review the diff before committing and pushing.')


if __name__ == '__main__':
    main()
