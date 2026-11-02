"""Build a clean, prebuilt Windows ZIP without copying runtime data or credentials."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parent.parent
FILES = ['README.md','LICENSE','SECURITY.md','CONTRIBUTING.md','SUPPORT.md','CODE_OF_CONDUCT.md','CHANGELOG.md','requirements.txt','requirements.lock.txt','run.py',
         'Setup-AgentChat.cmd','Setup-AgentChat.ps1','Start-AgentChat.cmd','Start-AgentChat.ps1','Register-Codex.ps1']
DIRECTORIES = ['app','dist','branding','wiki']

def files():
    for name in FILES:
        path=ROOT/name
        if not path.is_file(): raise RuntimeError(f'Required release file missing: {name}')
        yield path
    for directory in DIRECTORIES:
        for path in sorted((ROOT/directory).rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc': continue
            if path.is_symlink(): raise RuntimeError(f'Symlink not allowed in release: {path}')
            yield path
    # Public prose only: keep design evidence and local screenshots out of the installer.
    for path in sorted((ROOT/'docs').glob('*.md')):
        yield path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default=json.loads((ROOT/'package.json').read_text())['version'])
    args=parser.parse_args()
    if not all(c.isalnum() or c in '.-_' for c in args.version): raise SystemExit('Invalid version')
    if not (ROOT/'dist/index.html').is_file(): raise SystemExit('Run npm run build before packaging.')
    output=ROOT/'release';output.mkdir(exist_ok=True)
    archive=output/f'AgentChat-{args.version}-Windows.zip'
    prefix=f'AgentChat-{args.version}'
    try: commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError: commit='uncommitted'
    manifest={'product':'DigitalRCS AgentChat','version':args.version,'commit':commit,'built_at':datetime.now(timezone.utc).isoformat(),'contains_user_data':False}
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in files(): z.write(path,f'{prefix}/{path.relative_to(ROOT).as_posix()}')
        z.writestr(f'{prefix}/BUILD.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(archive) as z:
        bad=[n for n in z.namelist() if any(p in n.split('/') for p in ['data','.venv','.git','identities','node_modules']) or n.endswith(('.sqlite3','.log','.pyc'))]
        if bad: raise RuntimeError(f'Unsafe paths in archive: {bad}')
        if z.testzip(): raise RuntimeError('Archive integrity check failed')
    checksum=hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/'SHA256SUMS.txt').write_text(f'{checksum}  {archive.name}\n',encoding='utf-8')
    print(f'{archive.name}: {archive.stat().st_size:,} bytes, SHA256 {checksum}')

if __name__=='__main__':main()
