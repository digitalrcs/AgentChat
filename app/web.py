from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.store import ROOT, Store
from app.local_llm import Runner, discover
from app.media import MAX_ATTACHMENT_BYTES, MAX_MESSAGE_ATTACHMENTS, safe_filename
from contextlib import asynccontextmanager
import httpx

def create_app(store=None):
    store = store or Store()
    runner = Runner(store)
    @asynccontextmanager
    async def lifespan(app):
        yield
        await runner.stop()
    app = FastAPI(title='DigitalRCS AgentChat', docs_url=None, redoc_url=None,lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1','localhost','testserver'])

    @app.middleware('http')
    async def local_only(request: Request, call_next):
        origin = request.headers.get('origin')
        allowed = {f'{request.url.scheme}://{request.url.netloc}','http://127.0.0.1:5173','http://localhost:5173'}
        # Links and browser extensions may open the app with cross-site fetch metadata.
        # Only the public app shell can be opened this way, never data/API endpoints.
        shell_navigation = (request.method == 'GET' and request.url.path in ('/', '/index.html')
            and request.headers.get('sec-fetch-mode') == 'navigate'
            and request.headers.get('sec-fetch-dest') == 'document')
        if (origin and origin not in allowed) or (request.headers.get('sec-fetch-site') == 'cross-site' and not shell_navigation):
            return JSONResponse({'detail':'Cross-origin requests are not allowed.'}, status_code=403)
        if request.method in ('POST','PUT','DELETE','PATCH') and request.headers.get('x-agentchat') != 'local-ui':
            return JSONResponse({'detail':'Missing local UI request header.'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        response.headers.setdefault('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        return response

    @app.exception_handler(ValueError)
    async def invalid(request, error):
        return JSONResponse({'detail':str(error)}, status_code=400)

    @app.exception_handler(httpx.HTTPError)
    async def connection_failed(request, error):
        return JSONResponse({'detail':'LM Studio could not be reached. Check its address and running server.'},status_code=502)

    @app.get('/api/health')
    def health(): return {'status':'ok','service':'agentchat','version':'0.3.0'}
    @app.get('/api/participants')
    def participants(): return store.participants()
    @app.post('/api/participants')
    def register(data: Person): return store.register(data.name)[0]
    @app.get('/api/conversations')
    def conversations(q: str='',project_id: str | None=None): return store.conversations(q,project_id)
    @app.post('/api/conversations')
    def create(data: Conversation): return store.create_conversation(data.title,data.objective,data.project_id)
    @app.get('/api/projects')
    def projects(): return store.projects()
    @app.post('/api/projects')
    def project(data: Project): return store.create_project(data.name,data.description)
    @app.get('/api/conversations/{room_id}/messages')
    def messages(room_id: str, after_id: int=0, limit: int=100): return store.messages(room_id,after_id,limit)
    @app.post('/api/conversations/{room_id}/messages')
    def post(room_id: str, data: Message):
        return store.post(room_id,data.participant_id,data.body,data.reply_to,data.client_id,human_only=True,attachment_ids=data.attachment_ids)
    @app.get('/api/conversations/{room_id}/tasks')
    def tasks(room_id: str):return store.tasks(room_id)
    @app.post('/api/conversations/{room_id}/tasks')
    def create_task(room_id: str,data: TaskCreate):return store.create_task(room_id,data.participant_id,data.title,data.description,human_only=True)
    @app.post('/api/conversations/{room_id}/tasks/{task_id}/claim')
    def claim_task(room_id: str,task_id: str,data: Actor):return store.change_task(room_id,task_id,data.participant_id,claim=True,human_only=True)
    @app.post('/api/conversations/{room_id}/tasks/{task_id}/status')
    def update_task(room_id: str,task_id: str,data: TaskStatus):return store.change_task(room_id,task_id,data.participant_id,status=data.status,override=data.override,note=data.note,human_only=True)
    @app.get('/api/conversations/{room_id}/tasks/{task_id}/history')
    def task_history(room_id: str,task_id: str):return store.task_history(room_id,task_id)
    @app.get('/api/conversations/{room_id}/pins')
    def pins(room_id: str):return store.pins(room_id)
    @app.get('/api/conversations/{room_id}/pins/history')
    def pin_history(room_id: str):return store.pin_history(room_id)
    @app.post('/api/conversations/{room_id}/pins/{message_id}')
    def pin(room_id: str,message_id: int,data: Pin):return store.set_pin(room_id,message_id,data.participant_id,data.pinned,human_only=True)
    @app.get('/api/media-limits')
    def media_limits():
        return {'max_file_bytes':MAX_ATTACHMENT_BYTES,'max_files_per_message':MAX_MESSAGE_ATTACHMENTS,
                'note':'Media stays on this computer. Playback depends on browser codec support. Transcripts and descriptions are supplied notes, not automatic analysis.'}
    @app.post('/api/conversations/{room_id}/attachments')
    async def upload(room_id: str, request: Request, participant_id: str, filename: str, client_id: str | None=None):
        filename=safe_filename(filename)
        store.validate_upload_owner(room_id,participant_id,human_only=True)
        content_length=request.headers.get('content-length')
        if content_length:
            try:declared=int(content_length)
            except ValueError:raise HTTPException(400,'Invalid Content-Length.') from None
            if declared<0:raise HTTPException(400,'Invalid Content-Length.')
            if declared>MAX_ATTACHMENT_BYTES:raise HTTPException(413,'Each file must be 100 MiB or smaller.')
        staged=store.new_upload_path()
        try:
            received=0
            with staged.open('xb') as output:
                async for chunk in request.stream():
                    received+=len(chunk)
                    if received>MAX_ATTACHMENT_BYTES:raise HTTPException(413,'Each file must be 100 MiB or smaller.')
                    output.write(chunk)
            return store.finish_upload(staged,room_id,participant_id,filename,human_only=True,client_id=client_id)
        finally:
            staged.unlink(missing_ok=True)
    @app.get('/api/conversations/{room_id}/attachments')
    def attachments(room_id: str):return store.attachments(room_id)
    @app.get('/api/attachments/{attachment_id}')
    def attachment(attachment_id: str):return store.attachment(attachment_id)
    @app.get('/api/attachments/{attachment_id}/content')
    def content(attachment_id: str, download: bool=False):
        info,path=store.attachment_file(attachment_id)
        return FileResponse(path,media_type=info['mime_type'],filename=info['filename'],
            content_disposition_type='attachment' if download or info['media_kind']=='file' else 'inline',
            headers={'Content-Security-Policy':"default-src 'none'; sandbox; frame-ancestors 'none'"})
    @app.post('/api/attachments/{attachment_id}/annotations')
    def annotate(attachment_id: str,data: Annotation):
        return store.annotation(attachment_id,data.participant_id,data.kind,data.body,human_only=True)
    @app.delete('/api/attachments/{attachment_id}')
    def discard(attachment_id: str,participant_id: str):
        return store.discard_upload(attachment_id,participant_id,human_only=True)
    @app.get('/api/conversations/{room_id}/stats')
    def stats(room_id: str): return store.stats(room_id)
    @app.get('/api/conversations/{room_id}/export')
    def export(room_id: str):
        return JSONResponse(store.export(room_id), headers={'Content-Disposition':f'attachment; filename="conversation-{room_id}.json"'})
    @app.get('/api/search')
    def search(q: str,project_id: str | None=None): return store.search(q,project_id=project_id)
    @app.get('/api/admin')
    def admin(): return store.overview()
    @app.post('/api/admin/backup')
    def backup(): return store.backup()
    @app.post('/api/admin/media-cleanup')
    def cleanup_media():return store.cleanup_orphan_media()
    @app.post('/api/admin/erase')
    def erase(data: Erase):
        if runner.active(): raise ValueError('Stop the local discussion before erasing data.')
        return store.erase(data.scope,data.confirmation,data.room_id)
    @app.post('/api/admin/revoke/{participant_id}')
    def revoke(participant_id: str): return store.revoke_agent(participant_id)
    @app.get('/api/local-agents')
    def local_agents(): return runner.profiles()
    @app.post('/api/local-agents/models')
    async def models(data: Endpoint): return await discover(data.endpoint)
    @app.post('/api/local-agents')
    async def add_agent(data: LocalAgent): return await runner.add(data.name,data.endpoint,data.model,data.role)
    @app.get('/api/conversations/{room_id}/run')
    def run_status(room_id: str): return runner.status(room_id)
    @app.post('/api/conversations/{room_id}/run')
    async def start(room_id: str,data: Run): return await runner.start(room_id,data.agent_ids,data.turns,data.knowledge_query)
    @app.post('/api/local-agents/stop')
    async def stop(): return await runner.stop()
    dist = ROOT / 'dist'
    if dist.exists():
        app.mount('/', StaticFiles(directory=dist, html=True), name='ui')
    return app

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')
class Person(Input):
    name: str = Field(min_length=1,max_length=60)
class Conversation(Input):
    title: str = Field(min_length=1,max_length=120)
    objective: str = Field(default='',max_length=4000)
    project_id: str | None = None
class Project(Input):
    name: str = Field(min_length=1,max_length=100)
    description: str = Field(default='',max_length=2000)
class Message(Input):
    participant_id: str
    body: str = Field(default='',max_length=32000)
    reply_to: int | None = None
    client_id: str = Field(min_length=1,max_length=100)
    attachment_ids: list[str] = Field(default_factory=list,max_length=MAX_MESSAGE_ATTACHMENTS)
class Annotation(Input):
    participant_id: str
    kind: str
    body: str = Field(min_length=1,max_length=32000)
class Erase(Input):
    scope: str
    confirmation: str
    room_id: str | None = None
class Endpoint(Input):
    endpoint: str
class LocalAgent(Endpoint):
    name: str
    model: str
    role: str
class Run(Input):
    agent_ids: list[str]
    turns: int = 4
    knowledge_query: str = ''

class Actor(Input):
    participant_id: str
class TaskCreate(Actor):
    title: str = Field(min_length=1,max_length=200)
    description: str = Field(default='',max_length=4000)
class TaskStatus(Actor):
    status: str
    override: bool = False
    note: str = Field(default='',max_length=2000)
class Pin(Actor):
    pinned: bool = True
