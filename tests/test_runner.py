import asyncio
import base64
import json
import httpx
import pytest
from app.store import Store
from app.local_llm import Runner,endpoint_url

@pytest.mark.parametrize('url',['https://api.openai.com/v1','http://169.254.169.254/v1','http://127.0.0.1:1234/v1?x=1','http://user:secret@127.0.0.1/v1','file:///v1'])
def test_reject_nonlocal_targets(url):
    with pytest.raises(ValueError):endpoint_url(url)

def test_cancel_and_restart_state(tmp_path,monkeypatch):
    s=Store(tmp_path/'runner.sqlite3');r=s.create_conversation('Runner');p,_=s.register('Local','agent')
    with s.connect() as db:db.execute('INSERT INTO local_agents VALUES (?,?,?,?)',(p['id'],'http://127.0.0.1:1234/v1','test-model','Reviewer'))
    runner=Runner(s)
    async def exercise():
        async def blocked(*args):
            try:await asyncio.sleep(30)
            except asyncio.CancelledError:
                runner.update(args[0],'stopped');raise
        monkeypatch.setattr(runner,'work',blocked)
        await runner.start(r['id'],[p['id']],2)
        await asyncio.sleep(0)
        with pytest.raises(ValueError):await runner.start(r['id'],[p['id']],1)
        await runner.stop()
        assert runner.status(r['id'])['status']=='stopped'
    asyncio.run(exercise())

def test_local_runner_receives_authored_notes_not_raw_media(tmp_path,monkeypatch):
    s=Store(tmp_path/'media-runner.sqlite3')
    human,_=s.register('Human');agent,_=s.register('Local reviewer','agent')
    room=s.create_conversation('Discuss picture','Discuss supplied evidence without inventing image analysis.')
    raw=b'\x89PNG\r\n\x1a\nsynthetic bytes'
    image=s.upload_bytes(room['id'],human['id'],'sample.png',raw)
    s.annotation(image['id'],human['id'],'description','The uploaded diagram is described as containing two boxes.')
    s.post(room['id'],human['id'],'Review this description.',attachment_ids=[image['id']])
    with s.connect() as db:db.execute('INSERT INTO local_agents VALUES (?,?,?,?)',(agent['id'],'http://127.0.0.1:1234/v1','test-model','Reviewer'))
    captured=[]
    class FakeClient:
        def __init__(self,**kwargs):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def post(self,url,json):
            captured.append(json)
            return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'I can review the supplied description but have not inspected the image.'}}]},request=httpx.Request('POST',url))
    monkeypatch.setattr('app.local_llm.httpx.AsyncClient',FakeClient)
    runner=Runner(s)
    async def exercise():
        await runner.start(room['id'],[agent['id']],1)
        await runner.task
    asyncio.run(exercise())
    assert runner.status(room['id'])['status']=='completed'
    system=captured[0]['messages'][0]['content']
    context=json.loads(captured[0]['messages'][1]['content'])
    assert 'never raw media' in system
    note=context['attachment_metadata_and_notes'][0]['notes'][0]
    assert note['author']=='Human' and note['kind']=='description'
    assert 'two boxes' in note['authored_interpretation']
    assert base64.b64encode(raw).decode() not in captured[0]['messages'][1]['content']
