"""Shared durable operations for HTTP and MCP. One connection per operation."""
from contextlib import contextmanager, closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sqlite3
import statistics
import shutil
import unicodedata
import uuid
from app.media import MediaStoreMixin, MAX_MESSAGE_ATTACHMENTS

ROOT = Path(__file__).resolve().parent.parent

def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def clean(value, label, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'{label} must contain 1–{maximum} characters.')
    return value.strip()

class Store(MediaStoreMixin):
    def __init__(self, path=None):
        self.path = Path(path or os.environ.get('AGENTCHAT_DB', ROOT / 'data' / 'agentchat.sqlite3')).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS participants (
                  id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE,
                  kind TEXT NOT NULL CHECK(kind IN ('human','agent')), token_hash TEXT,
                  created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS conversations (
                  id TEXT PRIMARY KEY, title TEXT NOT NULL, objective TEXT NOT NULL,
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                  project_id TEXT REFERENCES projects(id));
                CREATE TABLE IF NOT EXISTS projects (
                  id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT NOT NULL DEFAULT '');
                CREATE TABLE IF NOT EXISTS messages (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  conversation_id TEXT NOT NULL REFERENCES conversations(id),
                  participant_id TEXT NOT NULL REFERENCES participants(id),
                  body TEXT NOT NULL, created_at TEXT NOT NULL,
                  reply_to INTEGER REFERENCES messages(id), client_id TEXT,
                  UNIQUE(participant_id, client_id));
                CREATE INDEX IF NOT EXISTS messages_room_id ON messages(conversation_id,id);
                CREATE TABLE IF NOT EXISTS attachments (
                  id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
                  participant_id TEXT NOT NULL REFERENCES participants(id),
                  message_id INTEGER REFERENCES messages(id), filename TEXT NOT NULL,
                  mime_type TEXT NOT NULL, media_kind TEXT NOT NULL, size_bytes INTEGER NOT NULL,
                  sha256 TEXT NOT NULL, created_at TEXT NOT NULL, client_id TEXT,
                  UNIQUE(participant_id,client_id));
                CREATE INDEX IF NOT EXISTS attachments_room ON attachments(conversation_id,message_id);
                CREATE TABLE IF NOT EXISTS attachment_annotations (
                  id INTEGER PRIMARY KEY AUTOINCREMENT, attachment_id TEXT NOT NULL REFERENCES attachments(id) ON DELETE CASCADE,
                  participant_id TEXT NOT NULL REFERENCES participants(id), annotation_kind TEXT NOT NULL,
                  body TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS local_agents (
                  participant_id TEXT PRIMARY KEY REFERENCES participants(id),
                  endpoint TEXT NOT NULL, model TEXT NOT NULL, role TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
                  status TEXT NOT NULL, completed_turns INTEGER NOT NULL DEFAULT 0,
                  total_turns INTEGER NOT NULL, detail TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
            ''')
            columns = {r['name'] for r in db.execute('PRAGMA table_info(conversations)')}
            if 'project_id' not in columns:
                db.execute('ALTER TABLE conversations ADD COLUMN project_id TEXT REFERENCES projects(id)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def participants(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT id,name,kind,created_at FROM participants ORDER BY created_at,id')]

    def register(self, name, kind='human'):
        name = unicodedata.normalize('NFKC', clean(name, 'Name', 60))
        if kind not in ('human', 'agent'):
            raise ValueError('Kind must be human or agent.')
        token = secrets.token_urlsafe(32) if kind == 'agent' else None
        p = dict(id=str(uuid.uuid4()), name=name, kind=kind, created_at=now())
        with self.connect() as db:
            try:
                db.execute('INSERT INTO participants VALUES (?,?,?,?,?,?)',
                    (p['id'], name, name.casefold(), kind, self.digest(token) if token else None, p['created_at']))
            except sqlite3.IntegrityError:
                raise ValueError('That participant name is already registered.') from None
        return p, token

    @staticmethod
    def digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def authenticate(self, token):
        with self.connect() as db:
            row = db.execute('SELECT id,name,kind,created_at FROM participants WHERE token_hash=?', (self.digest(token),)).fetchone()
            if not row:
                raise ValueError('Invalid agent identity credential.')
            return dict(row)

    def create_conversation(self, title, objective='', project_id=None):
        title = clean(title, 'Title', 120)
        if not isinstance(objective, str) or len(objective) > 4000:
            raise ValueError('Objective must be at most 4000 characters.')
        room = dict(id=str(uuid.uuid4()), title=title, objective=objective.strip(), created_at=now(), updated_at=now(),project_id=project_id)
        with self.connect() as db:
            if project_id and not db.execute('SELECT id FROM projects WHERE id=?',(project_id,)).fetchone():
                raise ValueError('Project not found.')
            db.execute('INSERT INTO conversations (id,title,objective,created_at,updated_at,project_id) VALUES (:id,:title,:objective,:created_at,:updated_at,:project_id)', room)
        return room

    def conversations(self, query='', project_id=None):
        if len(query) > 200:
            raise ValueError('Search is limited to 200 characters.')
        with self.connect() as db:
            return [dict(r) for r in db.execute('''SELECT c.*,count(m.id) AS message_count
              FROM conversations c LEFT JOIN messages m ON m.conversation_id=c.id
              WHERE instr(lower(c.title || ' ' || c.objective),lower(?))>0
              AND (? IS NULL OR c.project_id=?)
              GROUP BY c.id ORDER BY c.updated_at DESC,c.id''', (query,project_id,project_id))]

    def projects(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT p.*,count(c.id) AS conversations FROM projects p LEFT JOIN conversations c ON c.project_id=p.id GROUP BY p.id ORDER BY p.name')]

    def create_project(self,name,description=''):
        project = dict(id=str(uuid.uuid4()),name=clean(name,'Project name',100),description=description.strip())
        if len(description)>2000: raise ValueError('Description is limited to 2000 characters.')
        with self.connect() as db:
            try: db.execute('INSERT INTO projects VALUES (:id,:name,:description)',project)
            except sqlite3.IntegrityError: raise ValueError('Project name already exists.') from None
        return project

    def room(self, room_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM conversations WHERE id=?', (room_id,)).fetchone()
            if not row:
                raise ValueError('Conversation not found.')
            return dict(row)

    def messages(self, room_id, after_id=0, limit=100):
        self.room(room_id)
        if not 1 <= limit <= 500 or after_id < 0:
            raise ValueError('Limit must be 1–500 and after_id must be nonnegative.')
        with self.connect() as db:
            rows = db.execute('''SELECT m.*,p.name,p.kind FROM messages m
              JOIN participants p ON p.id=m.participant_id
              WHERE m.conversation_id=? AND m.id>? ORDER BY m.id LIMIT ?''', (room_id, after_id, limit+1)).fetchall()
        items = [dict(r) for r in rows[:limit]]
        for item in items:
            item['attachments']=self.attachments(room_id,item['id'])
        return dict(items=items, next_cursor=items[-1]['id'] if items else after_id, has_more=len(rows)>limit)

    def post(self, room_id, participant_id, body, reply_to=None, client_id=None, human_only=False, attachment_ids=None):
        attachment_ids=attachment_ids or []
        if not isinstance(attachment_ids,list) or len(attachment_ids)>MAX_MESSAGE_ATTACHMENTS or len(set(attachment_ids))!=len(attachment_ids):
            raise ValueError('Attach up to 10 distinct files per message.')
        if not isinstance(body,str) or len(body)>32000 or (not body.strip() and not attachment_ids):
            raise ValueError('Write a message (up to 32000 characters) or attach a file.')
        body=body.strip()
        if client_id is not None:
            client_id = clean(client_id, 'Client id', 100)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self._check_person(db,participant_id,human_only)
            if client_id:
                prior = db.execute('SELECT * FROM messages WHERE participant_id=? AND client_id=?', (participant_id, client_id)).fetchone()
                if prior:
                    prior_ids={r['id'] for r in db.execute('SELECT id FROM attachments WHERE message_id=?',(prior['id'],))}
                    if (prior['conversation_id'],prior['body'],prior['reply_to']) != (room_id,body,reply_to) or prior_ids!=set(attachment_ids):
                        raise ValueError('Client id already used for a different message.')
                    return dict(prior)
            if not db.execute('SELECT id FROM conversations WHERE id=?', (room_id,)).fetchone():
                raise ValueError('Conversation not found.')
            if reply_to is not None and not db.execute('SELECT id FROM messages WHERE id=? AND conversation_id=?', (reply_to, room_id)).fetchone():
                raise ValueError('Reply target must exist in the same conversation.')
            for attachment_id in attachment_ids:
                item=db.execute('SELECT * FROM attachments WHERE id=?',(attachment_id,)).fetchone()
                if not item or item['conversation_id']!=room_id or item['participant_id']!=participant_id or item['message_id'] is not None:
                    raise ValueError('Files must be your own unattached uploads in this conversation.')
            stamp = now()
            result = db.execute('INSERT INTO messages (conversation_id,participant_id,body,created_at,reply_to,client_id) VALUES (?,?,?,?,?,?)',
                (room_id,participant_id,body,stamp,reply_to,client_id))
            for attachment_id in attachment_ids:
                db.execute('UPDATE attachments SET message_id=? WHERE id=?',(result.lastrowid,attachment_id))
            db.execute('UPDATE conversations SET updated_at=? WHERE id=?', (stamp, room_id))
            return dict(db.execute('SELECT * FROM messages WHERE id=?', (result.lastrowid,)).fetchone())

    def stats(self, room_id):
        self.room(room_id)
        with self.connect() as db:
            participants = [dict(r) for r in db.execute('''SELECT p.id,p.name,p.kind,count(*) AS messages,
              sum(length(m.body)) AS characters FROM messages m JOIN participants p ON p.id=m.participant_id
              WHERE m.conversation_id=? GROUP BY p.id ORDER BY messages DESC,p.name''', (room_id,))]
            activity = [dict(r) for r in db.execute('''SELECT substr(created_at,1,10) AS day,count(*) AS messages
              FROM messages WHERE conversation_id=? GROUP BY day ORDER BY day''', (room_id,))]
            timing = db.execute('''SELECT m.created_at,r.created_at AS parent_at FROM messages m
              JOIN messages r ON r.id=m.reply_to WHERE m.conversation_id=?''', (room_id,)).fetchall()
            media=[dict(r) for r in db.execute('SELECT media_kind,count(*) AS files,sum(size_bytes) AS bytes FROM attachments WHERE conversation_id=? AND message_id IS NOT NULL GROUP BY media_kind',(room_id,))]
        delays = [(datetime.fromisoformat(r['created_at'])-datetime.fromisoformat(r['parent_at'])).total_seconds() for r in timing]
        return dict(total_messages=sum(p['messages'] for p in participants), active_participants=len(participants),
          total_characters=sum(p['characters'] for p in participants), explicit_replies=len(delays),
          median_reply_seconds=statistics.median(delays) if delays else None,
          participants=participants, activity=activity, timezone='UTC',
          attachments=media,total_attachments=sum(x['files'] for x in media),attachment_bytes=sum(x['bytes'] for x in media),
          note='Reply timing measures elapsed time from an explicitly linked message, not model inference speed. Activity lists days with messages; omitted days have zero messages.')

    def export(self, room_id):
        room = self.room(room_id)
        with self.connect() as db:
            items = [dict(r) for r in db.execute('''SELECT m.id,m.participant_id,p.name,p.kind,m.body,m.created_at,m.reply_to
              FROM messages m JOIN participants p ON p.id=m.participant_id WHERE conversation_id=? ORDER BY m.id''', (room_id,))]
        for item in items:item['attachments']=self.attachments(room_id,item['id'])
        return dict(conversation=room, messages=items, statistics=self.stats(room_id),
                    attachment_note='This JSON contains attachment metadata and authored notes. Download originals separately, or create an Admin backup to preserve bytes.')

    def search(self, query, limit=50, project_id=None):
        query = clean(query, 'Search', 200)
        if not 1 <= limit <= 100:
            raise ValueError('Limit must be 1–100.')
        with self.connect() as db:
            results = [dict(r) for r in db.execute('''SELECT m.id,m.conversation_id,c.title,p.name,p.kind,
              substr(m.body,1,1200) AS excerpt,m.created_at FROM messages m
              JOIN participants p ON p.id=m.participant_id JOIN conversations c ON c.id=m.conversation_id
              WHERE (instr(lower(m.body),lower(?))>0 OR EXISTS (
                SELECT 1 FROM attachments a LEFT JOIN attachment_annotations n ON n.attachment_id=a.id
                WHERE a.message_id=m.id AND (instr(lower(a.filename),lower(?))>0 OR instr(lower(n.body),lower(?))>0)))
              AND (? IS NULL OR c.project_id=?)
              ORDER BY m.id DESC LIMIT ?''', (query,query,query,project_id,project_id,limit))]
            for result in results:
                result['attachment_matches']=[dict(r) for r in db.execute('''SELECT a.id AS attachment_id,a.filename,
                    n.annotation_kind,substr(n.body,1,600) AS excerpt,p.name AS annotation_author
                    FROM attachments a LEFT JOIN attachment_annotations n ON n.attachment_id=a.id
                    LEFT JOIN participants p ON p.id=n.participant_id WHERE a.message_id=?
                    AND (instr(lower(a.filename),lower(?))>0 OR instr(lower(n.body),lower(?))>0)
                    ORDER BY a.created_at,n.id LIMIT 4''',(result['id'],query,query))]
            return results

    def overview(self):
        with self.connect() as db:
            counts = {t: db.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
                      for t in ('projects','participants','conversations','messages','attachments')}
            media_bytes=db.execute('SELECT coalesce(sum(size_bytes),0) FROM attachments').fetchone()[0]
        return dict(**counts, attachment_bytes=media_bytes,media_directory=str(self.media_dir),database=str(self.path), schema_version=2)

    def backup(self):
        folder = self.path.parent / 'backups'
        folder.mkdir(exist_ok=True)
        target = folder / f'agentchat-{datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")}-{uuid.uuid4().hex[:6]}.sqlite3'
        media_target=target.with_suffix('.media')
        # Hold the writer reservation while snapshotting DB and immutable blob bytes.
        # A separate reader connection is needed: backing up the write transaction itself blocks SQLite.
        try:
            with self.connect() as lock:
                lock.execute('BEGIN IMMEDIATE')
                with self.connect() as source, closing(sqlite3.connect(target)) as destination:
                    source.backup(destination)
                rows=lock.execute('SELECT id,filename,size_bytes,sha256,mime_type FROM attachments').fetchall()
                if rows:
                    media_target.mkdir()
                    for row in rows:
                        source_path=self._media_path(row['id'])
                        if not source_path.is_file():raise ValueError('Backup stopped: attachment bytes are missing.')
                        shutil.copy2(source_path,media_target/row['id'])
                    (media_target/'manifest.json').write_text(json.dumps({'database':target.name,'files':[dict(r) for r in rows]},indent=2),encoding='utf-8')
        except Exception:
            target.unlink(missing_ok=True)
            if media_target.exists() and media_target.resolve().parent==folder.resolve():shutil.rmtree(media_target)
            raise
        return dict(filename=target.name, path=str(target),media_path=str(media_target) if media_target.exists() else None,
                    note='Keep the .sqlite3 file and its matching .media folder together for complete recovery.')

    def erase(self, scope, confirmation, room_id=None):
        expected = {'conversation':'DELETE CONVERSATION','history':'ERASE HISTORY','all':'RESET EVERYTHING'}
        if scope not in expected or confirmation != expected[scope]:
            raise ValueError('Confirmation does not match the selected action.')
        if scope == 'conversation':
            self.room(room_id)
        backup = self.backup()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            media_ids=[r['id'] for r in db.execute('SELECT id FROM attachments WHERE (? IS NULL OR conversation_id=?)',
                (room_id if scope=='conversation' else None,room_id if scope=='conversation' else None))]
            if scope == 'conversation':
                db.execute('DELETE FROM attachments WHERE conversation_id=?',(room_id,))
                db.execute('DELETE FROM runs WHERE conversation_id=?', (room_id,))
                db.execute('DELETE FROM messages WHERE conversation_id=?', (room_id,))
                db.execute('DELETE FROM conversations WHERE id=?', (room_id,))
            else:
                db.execute('DELETE FROM attachments')
                db.execute('DELETE FROM runs')
                db.execute('DELETE FROM messages')
                db.execute('DELETE FROM conversations')
                if scope == 'all':
                    db.execute('DELETE FROM local_agents')
                    db.execute('DELETE FROM participants')
                    db.execute('DELETE FROM projects')
        for attachment_id in media_ids:self._media_path(attachment_id).unlink(missing_ok=True)
        self.cleanup_orphan_media()
        return dict(erased=scope, backup=backup, note='A recovery backup remains on disk. This is not secure file erasure.')

    def revoke_agent(self, participant_id):
        with self.connect() as db:
            result = db.execute("UPDATE participants SET token_hash=NULL WHERE id=? AND kind='agent'", (participant_id,))
            if not result.rowcount:
                raise ValueError('Agent not found.')
        return dict(revoked=participant_id)

    def reissue_agent(self, name):
        name = unicodedata.normalize('NFKC', clean(name,'Name',60))
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT id,name,kind,created_at FROM participants WHERE name_key=?',(name.casefold(),)).fetchone()
            if row:
                if row['kind'] != 'agent': raise ValueError('That name belongs to a human participant.')
                if db.execute('SELECT 1 FROM local_agents WHERE participant_id=?',(row['id'],)).fetchone():
                    raise ValueError('This name belongs to a managed local model profile, not an external MCP agent.')
                db.execute('UPDATE participants SET token_hash=? WHERE id=?',(self.digest(token),row['id']))
                return dict(row),token
        return self.register(name,'agent')
