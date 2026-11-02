import base64
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
import sqlite3
import time
from urllib.parse import urlencode
from fastapi.testclient import TestClient
from starlette.requests import Request, ClientDisconnect
import pytest
from app.store import Store
from app.web import create_app
from app.media import media_type

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1kAAAAASUVORK5CYII=')

@pytest.fixture
def media(tmp_path):
    store=Store(tmp_path/'workspace.sqlite3')
    person,_=store.register('Uploader')
    room=store.create_conversation('Media test')
    return store,person,room

def test_upload_provenance_attach_and_retry(media):
    s,p,r=media
    a=s.upload_bytes(r['id'],p['id'],'../photo.png',PNG,'same-upload')
    retry=s.upload_bytes(r['id'],p['id'],'photo.png',PNG,'same-upload')
    assert a['id']==retry['id']
    assert a['filename']=='photo.png'
    assert a['media_kind']=='image'
    assert a['sha256']==hashlib.sha256(PNG).hexdigest()
    assert a['name']=='Uploader' and a['message_id'] is None
    m=s.post(r['id'],p['id'],'',client_id='message',attachment_ids=[a['id']])
    assert s.post(r['id'],p['id'],'',client_id='message',attachment_ids=[a['id']])['id']==m['id']
    assert s.messages(r['id'])['items'][0]['attachments'][0]['id']==a['id']
    assert s.stats(r['id'])['total_attachments']==1
    with pytest.raises(ValueError):s.upload_bytes(r['id'],p['id'],'photo.png',b'different','same-upload')
    with pytest.raises(ValueError):s.post(r['id'],p['id'],'',client_id='message')

def test_foreign_room_author_reuse_and_limit(media):
    s,p,r=media
    other,_=s.register('Other');room2=s.create_conversation('Elsewhere')
    a=s.upload_bytes(r['id'],p['id'],'file.txt',b'notes')
    with pytest.raises(ValueError):s.post(r['id'],other['id'],'forged',attachment_ids=[a['id']])
    with pytest.raises(ValueError):s.post(room2['id'],p['id'],'wrong room',attachment_ids=[a['id']])
    with pytest.raises(ValueError):s.post(r['id'],p['id'],'duplicates',attachment_ids=[a['id'],a['id']])
    with pytest.raises(ValueError):s.post(r['id'],p['id'],'too many',attachment_ids=[str(i) for i in range(11)])
    s.post(r['id'],p['id'],'shared',attachment_ids=[a['id']])
    with pytest.raises(ValueError):s.post(r['id'],p['id'],'reuse',attachment_ids=[a['id']])
    with pytest.raises(ValueError):s.discard_upload(a['id'],p['id'])

def test_annotations_are_attributed_searchable_and_original_unchanged(media):
    s,p,r=media
    agent,token=s.register('Reviewer','agent')
    a=s.upload_bytes(r['id'],p['id'],'recording.wav',b'RIFF'+b'\0'*4+b'WAVE'+b'data')
    m=s.post(r['id'],p['id'],'',attachment_ids=[a['id']])
    item=s.annotation(a['id'],agent['id'],'transcript','The retry policy needs a hard cap.')
    note=item['annotations'][0]
    assert note['name']=='Reviewer' and note['author_kind']=='agent' and note['annotation_kind']=='transcript'
    assert item['sha256']==a['sha256']
    assert s.search('hard cap')[0]['id']==m['id']
    assert s.search('recording.wav')[0]['id']==m['id']
    with pytest.raises(ValueError):s.annotation(a['id'],p['id'],'verified truth','not a supported label')
    s.revoke_agent(agent['id'])
    with pytest.raises(ValueError):s.annotation(a['id'],agent['id'],'description','should fail')

def test_backup_restore_and_reset_preserve_backup_bytes(media):
    s,p,r=media
    a=s.upload_bytes(r['id'],p['id'],'photo.png',PNG)
    s.annotation(a['id'],p['id'],'description','A one-pixel test image.')
    s.post(r['id'],p['id'],'image',attachment_ids=[a['id']])
    result=s.erase('conversation','DELETE CONVERSATION',r['id'])
    assert not s._media_path(a['id']).exists()
    recovered=Store(result['backup']['path'])
    info,path=recovered.attachment_file(a['id'])
    assert path.read_bytes()==PNG
    assert info['annotations'][0]['body']=='A one-pixel test image.'
    assert recovered.messages(r['id'])['items'][0]['attachments'][0]['sha256']==a['sha256']
    assert result['backup']['media_path']==str(recovered.media_dir)

def test_pending_discard_ownership_and_cascade(media):
    s,p,r=media
    other,_=s.register('Other')
    a=s.upload_bytes(r['id'],p['id'],'draft.txt',b'draft')
    s.annotation(a['id'],p['id'],'description','Draft interpretation')
    with pytest.raises(ValueError):s.discard_upload(a['id'],other['id'])
    s.discard_upload(a['id'],p['id'])
    assert not s._media_path(a['id']).exists()
    with s.connect() as db:assert db.execute('SELECT count(*) FROM attachment_annotations').fetchone()[0]==0

@pytest.mark.parametrize('filename,data',[('active.svg',b'<svg onload="alert(1)"></svg>'),('page.html',b'<script>alert(1)</script>'),('fake.png',b'<svg onload="alert(1)"></svg>')])
def test_active_or_spoofed_files_download(media,filename,data):
    s,p,r=media
    a=s.upload_bytes(r['id'],p['id'],filename,data)
    with TestClient(create_app(s)) as client:
        response=client.get(a['download_url'].split('?')[0])
        assert response.headers['content-type']=='application/octet-stream'
        assert response.headers['content-disposition'].startswith('attachment;')
        assert response.headers['x-content-type-options']=='nosniff'
        assert 'sandbox' in response.headers['content-security-policy']

def test_http_streaming_ranges_and_ownership(media):
    s,p,r=media
    agent,_=s.register('Remote','agent')
    headers={'X-AgentChat':'local-ui','Content-Type':'audio/wav'}
    with TestClient(create_app(s)) as client:
        url=f'/api/conversations/{r["id"]}/attachments?'+urlencode({'participant_id':p['id'],'filename':'tone.wav','client_id':'range-test'})
        raw=b'RIFF'+b'\0'*4+b'WAVE'+bytes(range(100))
        response=client.post(url,content=raw,headers=headers)
        assert response.status_code==200,response.text
        a=response.json()
        assert a['media_kind']=='audio'
        preview=client.get(a['preview_url'])
        assert preview.content==raw and preview.headers['content-disposition'].startswith('inline;')
        partial=client.get(a['preview_url'],headers={'Range':'bytes=4-11'})
        assert partial.status_code==206 and partial.content==raw[4:12]
        assert partial.headers['content-range']==f'bytes 4-11/{len(raw)}'
        suffix=client.get(a['preview_url'],headers={'Range':'bytes=-8'})
        assert suffix.status_code==206 and suffix.content==raw[-8:]
        assert client.get(a['preview_url'],headers={'Range':'bytes=99999-'}).status_code==416
        assert client.get('/api/attachments/../../run.py/content').status_code!=200
        bad_url=f'/api/conversations/{r["id"]}/attachments?'+urlencode({'participant_id':agent['id'],'filename':'bad.txt'})
        assert client.post(bad_url,content=b'bad',headers=headers).status_code==400

def test_oversize_and_interrupted_upload_cleanup(media,monkeypatch):
    s,p,r=media
    import app.web as web
    monkeypatch.setattr(web,'MAX_ATTACHMENT_BYTES',20)
    url=f'/api/conversations/{r["id"]}/attachments?'+urlencode({'participant_id':p['id'],'filename':'large.txt'})
    with TestClient(create_app(s)) as client:
        assert client.post(url,content=b'x'*21,headers={'X-AgentChat':'local-ui'}).status_code==413
        # An undeclared/chunked body is also counted before any metadata is committed.
        response=client.post(url,content=iter([b'x'*11,b'x'*11]),headers={'X-AgentChat':'local-ui','Transfer-Encoding':'chunked'})
        assert response.status_code==413
        assert s.attachments(r['id'])==[]
        assert not list((s.media_dir/'.incoming').glob('*.part'))

def test_client_disconnect_removes_partial_upload(media):
    s,p,r=media
    app=create_app(s)
    upload=next(route.endpoint for route in app.routes if getattr(route,'path',None)=='/api/conversations/{room_id}/attachments' and 'POST' in getattr(route,'methods',set()))
    events=iter([{'type':'http.request','body':b'partial bytes','more_body':True},{'type':'http.disconnect'}])
    async def receive():return next(events)
    async def exercise():
        request=Request({'type':'http','method':'POST','headers':[]},receive=receive)
        with pytest.raises(ClientDisconnect):
            await upload(r['id'],request,p['id'],'partial.mp4')
    asyncio.run(exercise())
    assert s.attachments(r['id'])==[]
    assert not list((s.media_dir/'.incoming').glob('*.part'))

def test_text_bounds_and_binary_rejection(media):
    s,p,r=media
    a=s.upload_bytes(r['id'],p['id'],'notes.txt','abcédef'.encode())
    excerpt=s.read_attachment_text(a['id'],4)
    assert excerpt['text']=='abc' and excerpt['truncated']
    invalid=s.upload_bytes(r['id'],p['id'],'binary.txt',b'\xff\x00')
    with pytest.raises(ValueError):s.read_attachment_text(invalid['id'])
    with pytest.raises(ValueError):s.read_attachment_text(a['id'],65537)

def test_backup_fails_closed_if_original_missing(media):
    s,p,r=media
    a=s.upload_bytes(r['id'],p['id'],'missing.txt',b'important')
    s._media_path(a['id']).unlink()
    with pytest.raises(ValueError):s.erase('history','ERASE HISTORY')
    assert s.room(r['id'])['id']==r['id']
    assert not list((s.path.parent/'backups').glob('*.sqlite3'))

def test_orphan_cleanup_never_removes_saved_drafts_or_fresh_parts(media):
    s,p,r=media
    a=s.upload_bytes(r['id'],p['id'],'saved-draft.txt',b'keep')
    old=s.new_upload_path();old.write_bytes(b'old')
    fresh=s.new_upload_path();fresh.write_bytes(b'new')
    yesterday=time.time()-90000
    os.utime(old,(yesterday,yesterday));os.utime(s._media_path(a['id']),(yesterday,yesterday))
    result=s.cleanup_orphan_media()
    assert result['removed_files']==1
    assert not old.exists() and fresh.exists() and s._media_path(a['id']).exists()
