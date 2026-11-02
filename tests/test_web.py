from fastapi.testclient import TestClient
from app.store import Store
from app.web import create_app

def test_http_flow_and_origin_protection(tmp_path):
    s=Store(tmp_path/'web.sqlite3')
    headers={'X-AgentChat':'local-ui'}
    with TestClient(create_app(s)) as c:
        assert c.post('/api/participants',json={'name':'Human'}).status_code==403
        assert c.post('/api/participants',json={'name':'Human'},headers={**headers,'Origin':'https://evil.example'}).status_code==403
        p=c.post('/api/participants',json={'name':'Human'},headers=headers).json()
        r=c.post('/api/conversations',json={'title':'Test'},headers=headers).json()
        assert c.post(f'/api/conversations/{r["id"]}/messages',json={'participant_id':p['id'],'body':'hello','client_id':'first'},headers=headers).status_code==200
        assert c.get(f'/api/conversations/{r["id"]}/stats').json()['total_messages']==1
        assert c.get('/api/search?q=hello').json()[0]['name']=='Human'
        assert c.get('/api/health',headers={'host':'evil.example'}).status_code==400
        assert c.post('/api/admin/erase',json={'scope':'all','confirmation':'wrong'},headers=headers).status_code==400
