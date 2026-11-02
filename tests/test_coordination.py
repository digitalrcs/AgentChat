from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.store import Store
from app.web import create_app

@pytest.fixture
def board(tmp_path):
    store=Store(tmp_path/'board.sqlite3')
    human,_=store.register('Human')
    a,_=store.register('Agent A','agent')
    b,_=store.register('Agent B','agent')
    room=store.create_conversation('Coordination')
    return store,human,a,b,room['id']

def test_atomic_claim_and_owner_audit(board):
    s,h,a,b,r=board
    task=s.create_task(r,h['id'],'Investigate','Check evidence')
    def claim(person):
        try:return s.change_task(r,task['id'],person['id'],claim=True)
        except ValueError:return None
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(claim,[a,b]))
    winner=next(x for x in results if x)
    assert sum(x is not None for x in results)==1
    owner=winner['owner_id'];other=b['id'] if owner==a['id'] else a['id']
    assert s.change_task(r,task['id'],owner,claim=True)['owner_name']==winner['owner_name']
    with pytest.raises(ValueError):s.change_task(r,task['id'],other,status='done')
    with pytest.raises(ValueError):s.change_task(r,task['id'],other,status='done',override=True)
    s.change_task(r,task['id'],owner,status='blocked',note='Need data')
    s.change_task(r,task['id'],owner,status='open')
    s.change_task(r,task['id'],other,claim=True)
    s.change_task(r,task['id'],other,status='done')
    events=s.task_history(r,task['id'])
    assert [e['action'] for e in events]==['created','claimed','status_changed','released','claimed','status_changed']
    assert events[2]['note']=='Need data'
    assert events[3]['owner_id'] is None
    assert events[-1]['participant_id']==other

def test_revocation_override_room_boundary_and_http(board):
    s,h,a,b,r=board
    other=s.create_conversation('Other')['id']
    t=s.create_task(r,a['id'],'Review')
    s.change_task(r,t['id'],a['id'],claim=True)
    with pytest.raises(ValueError):s.change_task(other,t['id'],a['id'],status='done')
    with pytest.raises(ValueError):s.task_history(other,t['id'])
    s.revoke_agent(a['id'])
    with pytest.raises(ValueError):s.change_task(r,t['id'],a['id'],status='done')
    with TestClient(create_app(s)) as client:
        url=f'/api/conversations/{r}/tasks/{t["id"]}/status'
        headers={'X-AgentChat':'local-ui'}
        assert client.post(url,headers=headers,json={'participant_id':h['id'],'status':'open'}).status_code==400
        result=client.post(url,headers=headers,json={'participant_id':h['id'],'status':'open','override':True,'note':'Recover revoked owner'})
        assert result.status_code==200 and result.json()['owner_id'] is None
        assert client.post(url,headers=headers,json={'participant_id':b['id'],'status':'done','override':True}).status_code==400
    assert s.task_history(r,t['id'])[-1]['override']==1

@pytest.mark.parametrize('scope,confirmation',[('conversation','DELETE CONVERSATION'),('history','ERASE HISTORY'),('all','RESET EVERYTHING')])
def test_pins_backup_export_reset(board,scope,confirmation):
    s,h,a,b,r=board
    other=s.create_conversation('Keep')['id']
    message=s.post(r,a['id'],'Evidence <script>never execute</script>')
    task=s.create_task(r,h['id'],'Check')
    with pytest.raises(ValueError):s.set_pin(other,message['id'],b['id'])
    s.set_pin(r,message['id'],b['id'])
    s.set_pin(r,message['id'],h['id'])
    assert s.pins(r)[0]['pinned_by_name']=='Agent B'
    assert s.pins(r)[0]['name']=='Agent A'
    s.set_pin(r,message['id'],h['id'],False)
    assert len(s.pin_history(r))==2 and not s.pins(r)
    s.set_pin(r,message['id'],h['id'])
    s.revoke_agent(a['id'])
    with pytest.raises(ValueError):s.set_pin(r,message['id'],a['id'],False)
    exported=s.export(r)
    assert exported['tasks'][0]['history'][0]['action']=='created'
    assert exported['pins'][0]['message_id']==message['id']
    result=s.erase(scope,confirmation,r if scope=='conversation' else None)
    restored=Store(Path(result['backup']['path']))
    assert restored.tasks(r)[0]['id']==task['id']
    assert len(restored.pin_history(r))==3
    with s.connect() as db:
        for table in ('tasks','task_events','pins','pin_events'):assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==0
    if scope=='conversation':assert s.room(other)

def test_context_bounds_and_migration(board):
    s,h,a,b,r=board
    message=s.post(r,h['id'],'x'*2000)
    s.set_pin(r,message['id'],a['id'])
    t=s.create_task(r,h['id'],'Check','d'*1000)
    restored=Store(s.path)
    context=restored.coordination_context(r)
    assert len(context['tasks'][0]['description'])==400
    assert len(context['pinned_messages'][0]['body'])==1000
    assert restored.messages(r)['items'][0]['id']==message['id']
    assert restored.tasks(r)[0]['id']==t['id']
