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

def test_cross_site_top_level_shell_navigation_only(tmp_path,monkeypatch):
    # Independent of the developer's built assets and live database.
    dist=tmp_path/'dist';dist.mkdir()
    (dist/'index.html').write_text('<!doctype html><title>DigitalRCS AgentChat</title>')
    monkeypatch.setattr('app.web.ROOT',tmp_path)
    s=Store(tmp_path/'navigation.sqlite3')
    navigation={'Sec-Fetch-Site':'cross-site','Sec-Fetch-Mode':'navigate','Sec-Fetch-Dest':'document'}
    with TestClient(create_app(s)) as c:
        for path in ('/','/index.html','/?view=agents&tab=conversation'):
            result=c.get(path,headers=navigation)
            assert result.status_code==200 and 'DigitalRCS AgentChat' in result.text
            assert "frame-ancestors 'none'" in result.headers['content-security-policy']
        assert c.get('/',headers={**navigation,'Origin':'https://evil.example'}).status_code==403
        assert c.get('/',headers={**navigation,'Sec-Fetch-Dest':'iframe'}).status_code==403
        assert c.get('/',headers={**navigation,'Sec-Fetch-Mode':'cors'}).status_code==403
        assert c.get('/api/admin',headers=navigation).status_code==403
        assert c.get('/api/attachments/example/content',headers=navigation).status_code==403
        assert c.post('/api/participants',headers={**navigation,'X-AgentChat':'local-ui'},json={'name':'Intruder'}).status_code==403
        assert c.get('/api/health',headers={'Sec-Fetch-Site':'same-origin'}).status_code==200
        assert s.participants()==[]
