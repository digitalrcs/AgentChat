"""Durable, attributed coordination; transactions serialize competing claims."""
from datetime import datetime, timezone
import uuid

SCHEMA = '''
CREATE TABLE IF NOT EXISTS tasks (
 id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
 title TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL,
 created_by TEXT NOT NULL REFERENCES participants(id), owner_id TEXT REFERENCES participants(id),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS tasks_room ON tasks(conversation_id,created_at);
CREATE TABLE IF NOT EXISTS task_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
 participant_id TEXT NOT NULL REFERENCES participants(id), action TEXT NOT NULL,
 previous_status TEXT, status TEXT NOT NULL, previous_owner_id TEXT, owner_id TEXT,
 override INTEGER NOT NULL DEFAULT 0, note TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pins (
 message_id INTEGER PRIMARY KEY REFERENCES messages(id),
 conversation_id TEXT NOT NULL REFERENCES conversations(id),
 participant_id TEXT NOT NULL REFERENCES participants(id), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pin_events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL REFERENCES conversations(id),
 message_id INTEGER NOT NULL REFERENCES messages(id), participant_id TEXT NOT NULL REFERENCES participants(id),
 pinned INTEGER NOT NULL, created_at TEXT NOT NULL);
'''

def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

class CoordinationMixin:
    def tasks(self, room_id):
        self.room(room_id)
        with self.connect() as db:
            return [dict(r) for r in db.execute('''SELECT t.*,c.name AS creator_name,o.name AS owner_name,
                (SELECT e.note FROM task_events e WHERE e.task_id=t.id ORDER BY e.id DESC LIMIT 1) AS latest_note
                FROM tasks t JOIN participants c ON c.id=t.created_by LEFT JOIN participants o ON o.id=t.owner_id
                WHERE t.conversation_id=? ORDER BY t.created_at,t.id''',(room_id,))]

    def _task(self, db, room_id, task_id):
        row=db.execute('SELECT * FROM tasks WHERE id=? AND conversation_id=?',(task_id,room_id)).fetchone()
        if not row:raise ValueError('Task not found in this conversation.')
        return row

    def create_task(self, room_id, participant_id, title, description='', human_only=False):
        if not isinstance(title,str) or not title.strip() or len(title)>200:raise ValueError('Task title must contain 1–200 characters.')
        if not isinstance(description,str) or len(description)>4000:raise ValueError('Task description is limited to 4000 characters.')
        tid=str(uuid.uuid4());stamp=timestamp()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE');self._check_person(db,participant_id,human_only)
            if not db.execute('SELECT id FROM conversations WHERE id=?',(room_id,)).fetchone():raise ValueError('Conversation not found.')
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?)',(tid,room_id,title.strip(),description.strip(),'open',participant_id,None,stamp,stamp))
            db.execute('INSERT INTO task_events (task_id,participant_id,action,status,note,created_at) VALUES (?,?,?,?,?,?)',(tid,participant_id,'created','open','',stamp))
        return next(t for t in self.tasks(room_id) if t['id']==tid)

    def change_task(self, room_id, task_id, participant_id, status=None, claim=False, override=False, note='', human_only=False):
        if not isinstance(note,str) or len(note)>2000:raise ValueError('Task note is limited to 2000 characters.')
        if not claim and status not in ('open','in_progress','blocked','done'):raise ValueError('Unknown task status.')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            person=self._check_person(db,participant_id,human_only);task=self._task(db,room_id,task_id)
            if override and (not human_only or person['kind']!='human'):raise ValueError('Only an explicit local human operation can override task ownership.')
            if claim:
                if task['owner_id']==participant_id and task['status']=='in_progress':return next(t for t in self.tasks(room_id) if t['id']==task_id)
                if task['owner_id'] is not None or task['status']!='open':raise ValueError('Task is already claimed or closed. Refresh the task board.')
                owner=participant_id;status='in_progress';action='claimed'
            else:
                if task['owner_id']!=participant_id and not override:raise ValueError('Only the task owner can update or release it. Claim an open task first.')
                owner=None if status=='open' else (task['owner_id'] or participant_id)
                action='released' if status=='open' else 'status_changed'
            stamp=timestamp()
            db.execute('UPDATE tasks SET status=?,owner_id=?,updated_at=? WHERE id=?',(status,owner,stamp,task_id))
            db.execute('''INSERT INTO task_events (task_id,participant_id,action,previous_status,status,previous_owner_id,owner_id,override,note,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)''',(task_id,participant_id,action,task['status'],status,task['owner_id'],owner,int(override),note.strip(),stamp))
        return next(t for t in self.tasks(room_id) if t['id']==task_id)

    def task_history(self, room_id, task_id):
        with self.connect() as db:
            self._task(db,room_id,task_id)
            return [dict(r) for r in db.execute('''SELECT e.*,p.name,p.kind FROM task_events e JOIN participants p ON p.id=e.participant_id
                WHERE e.task_id=? ORDER BY e.id''',(task_id,))]

    def pins(self, room_id):
        self.room(room_id)
        with self.connect() as db:
            return [dict(r) for r in db.execute('''SELECT x.*,m.body,m.participant_id AS author_id,a.name,a.kind,p.name AS pinned_by_name
                FROM pins x JOIN messages m ON m.id=x.message_id JOIN participants a ON a.id=m.participant_id
                JOIN participants p ON p.id=x.participant_id WHERE x.conversation_id=? ORDER BY x.created_at,x.message_id''',(room_id,))]

    def set_pin(self, room_id, message_id, participant_id, pinned=True, human_only=False):
        if not isinstance(pinned,bool):raise ValueError('pinned must be a boolean.')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE');self._check_person(db,participant_id,human_only)
            if not db.execute('SELECT id FROM messages WHERE id=? AND conversation_id=?',(message_id,room_id)).fetchone():raise ValueError('Message not found in this conversation.')
            old=db.execute('SELECT 1 FROM pins WHERE message_id=?',(message_id,)).fetchone()
            if bool(old)!=pinned:
                stamp=timestamp()
                if pinned:db.execute('INSERT INTO pins VALUES (?,?,?,?)',(message_id,room_id,participant_id,stamp))
                else:db.execute('DELETE FROM pins WHERE message_id=?',(message_id,))
                db.execute('INSERT INTO pin_events (conversation_id,message_id,participant_id,pinned,created_at) VALUES (?,?,?,?,?)',(room_id,message_id,participant_id,int(pinned),stamp))
        return {'message_id':message_id,'pinned':pinned}

    def pin_history(self, room_id):
        self.room(room_id)
        with self.connect() as db:
            return [dict(r) for r in db.execute('''SELECT e.*,p.name,p.kind FROM pin_events e JOIN participants p ON p.id=e.participant_id
                WHERE e.conversation_id=? ORDER BY e.id''',(room_id,))]

    def coordination_export(self, room_id):
        tasks=self.tasks(room_id)
        return {'tasks':[dict(t,history=self.task_history(room_id,t['id'])) for t in tasks],
                'pins':self.pins(room_id),'pin_history':self.pin_history(room_id)}

    def coordination_context(self, room_id):
        return {'tasks':[{'id':t['id'],'title':t['title'],'status':t['status'],'owner':t['owner_name'],'description':t['description'][:400],'latest_note':t['latest_note'][:400]}
                         for t in self.tasks(room_id) if t['status']!='done'][:20],
                'pinned_messages':[{'message_id':p['message_id'],'author':p['name'],'pinned_by':p['pinned_by_name'],'body':p['body'][:1000]} for p in self.pins(room_id)[-10:]]}
