from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pytest
from app.store import Store

@pytest.fixture
def setup(tmp_path):
    s=Store(tmp_path/'test.sqlite3')
    p,_=s.register('Human')
    r=s.create_conversation('Issue','Check evidence')
    return s,p,r

def test_identity_unique_and_revocable(setup):
    s,p,r=setup
    with pytest.raises(ValueError): s.register('human')
    a,token=s.register('Reviewer','agent')
    assert s.authenticate(token)['id']==a['id']
    with pytest.raises(ValueError): s.post(r['id'],a['id'],'forged',human_only=True)
    s.revoke_agent(a['id'])
    with pytest.raises(ValueError): s.authenticate(token)
    restored,new_token=s.reissue_agent('Reviewer')
    assert restored['id']==a['id']
    assert s.authenticate(new_token)['id']==a['id']
    with pytest.raises(ValueError):s.authenticate(token)

def test_concurrent_durable_idempotent_posts(setup):
    s,p,r=setup
    def send(i): return s.post(r['id'],p['id'],f'message {i}',client_id=str(i))
    with ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(send,list(range(30))*2))
    restarted=Store(s.path)
    assert restarted.stats(r['id'])['total_messages']==30
    page=restarted.messages(r['id'],limit=7)
    ids=[m['id'] for m in page['items']]
    while page['has_more']:
        page=restarted.messages(r['id'],page['next_cursor'],7)
        ids.extend(m['id'] for m in page['items'])
    assert len(ids)==len(set(ids))==30
    with pytest.raises(ValueError): s.post(r['id'],p['id'],'different',client_id='0')

def test_reply_stats_and_cross_room_rejected(setup):
    s,p,r=setup
    assert s.stats(r['id'])['median_reply_seconds'] is None
    a=s.post(r['id'],p['id'],'parent')
    b=s.post(r['id'],p['id'],'linked',reply_to=a['id'])
    s.post(r['id'],p['id'],'unlinked')
    with s.connect() as db:
        db.execute('UPDATE messages SET created_at=? WHERE id=?',('2026-11-01T23:59:50+00:00',a['id']))
        db.execute('UPDATE messages SET created_at=? WHERE id=?',('2026-11-02T00:00:10+00:00',b['id']))
    stats=s.stats(r['id'])
    assert stats['median_reply_seconds']==20
    assert stats['explicit_replies']==1
    other=s.create_conversation('Other')
    with pytest.raises(ValueError): s.post(other['id'],p['id'],'invalid',reply_to=a['id'])

def test_project_search_isolation_and_export(setup):
    s,p,r=setup
    a=s.create_project('A'); b=s.create_project('B')
    r1=s.create_conversation('One',project_id=a['id']);r2=s.create_conversation('Two',project_id=b['id'])
    s.post(r1['id'],p['id'],'retry knowledge');s.post(r2['id'],p['id'],'retry knowledge')
    assert len(s.search('retry'))==2
    assert len(s.search('retry',project_id=a['id']))==1
    assert len(s.conversations(project_id=b['id']))==1
    assert s.export(r1['id'])['messages'][0]['name']=='Human'

def test_backup_reset_requires_exact_confirmation(setup):
    s,p,r=setup
    a=s.post(r['id'],p['id'],'preserve');s.post(r['id'],p['id'],'reply',reply_to=a['id'])
    with pytest.raises(ValueError):s.erase('all','yes')
    assert s.stats(r['id'])['total_messages']==2
    result=s.erase('history','ERASE HISTORY')
    assert s.overview()['messages']==0
    assert s.overview()['participants']==1
    recovered=Store(result['backup']['path'])
    assert recovered.stats(r['id'])['total_messages']==2
    s.erase('all','RESET EVERYTHING')
    assert s.overview()['participants']==0

def test_empty_and_validation(setup):
    s,p,r=setup
    stats=s.stats(r['id'])
    assert stats['total_messages']==stats['active_participants']==0
    assert stats['activity']==[]
    with pytest.raises(ValueError):s.post(r['id'],p['id'],'  ')
    with pytest.raises(ValueError):s.messages(r['id'],limit=501)
