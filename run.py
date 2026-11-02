import argparse
import json
from pathlib import Path
from app.store import ROOT, Store

def main():
    parser = argparse.ArgumentParser(description='AgentChat local web application and MCP server')
    parser.add_argument('--db',type=Path,default=None)
    sub = parser.add_subparsers(dest='command',required=True)
    web = sub.add_parser('web')
    web.add_argument('--port',type=int,default=8765)
    web.add_argument('--open-browser',action='store_true',help='Open the local app after its health check responds.')
    agent = sub.add_parser('register-agent')
    agent.add_argument('--name',required=True)
    agent.add_argument('--identity-file',type=Path,required=True)
    agent.add_argument('--replace-identity',action='store_true',help='Explicitly reissue an external agent credential after revocation or reset.')
    mcp = sub.add_parser('mcp')
    mcp.add_argument('--identity-file',type=Path,required=True)
    mcp.add_argument('--transport',choices=['stdio','streamable-http'],default='stdio')
    mcp.add_argument('--port',type=int,default=8766)
    args = parser.parse_args()
    store = Store(args.db)
    if args.command == 'web':
        import uvicorn
        from app.web import create_app
        if not 1 <= args.port <= 65535: raise SystemExit('Port must be between 1 and 65535.')
        if args.open_browser:
            import threading
            import time
            import urllib.request
            import webbrowser
            def open_when_ready():
                url=f'http://127.0.0.1:{args.port}'
                for _ in range(60):
                    try:
                        with urllib.request.urlopen(url+'/api/health',timeout=1) as response:
                            if json.load(response).get('service') == 'agentchat':
                                webbrowser.open(url)
                                return
                    except (OSError,ValueError): pass
                    time.sleep(.25)
            threading.Thread(target=open_when_ready,daemon=True).start()
        uvicorn.run(create_app(store),host='127.0.0.1',port=args.port)
    elif args.command == 'register-agent':
        if args.identity_file.exists() and not args.replace_identity:
            raise SystemExit('Identity file already exists; refusing to overwrite.')
        args.identity_file.parent.mkdir(parents=True,exist_ok=True)
        person, token = store.reissue_agent(args.name) if args.replace_identity else store.register(args.name,'agent')
        with args.identity_file.open('w' if args.replace_identity else 'x',encoding='utf-8') as output:
            json.dump({'participant_id':person['id'],'name':person['name'],'token':token},output)
        print(f'Registered {person["name"]}. Credential saved locally; keep this file private.')
    else:
        from app.mcp_server import create_mcp
        create_mcp(store,args.identity_file,args.port).run(transport=args.transport)

if __name__ == '__main__': main()
