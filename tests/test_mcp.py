import asyncio
import base64
import json
from pathlib import Path
import sys
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from app.store import Store,ROOT

def test_real_stdio_protocol_and_history(tmp_path):
    s=Store(tmp_path/'mcp.sqlite3')
    person,token=s.register('Protocol Agent','agent')
    identity=tmp_path/'identity.json'
    identity.write_text(json.dumps({'token':token}),encoding='utf-8')
    params=StdioServerParameters(command=sys.executable,args=[str(ROOT/'run.py'),'--db',str(s.path),'mcp','--identity-file',str(identity)])
    async def exercise():
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer) as session:
                await session.initialize()
                tools=await session.list_tools()
                names={t.name for t in tools.tools}
                assert {'who_am_i','search_history','post_message','list_projects','conversation_statistics'} <= names
                assert not any('erase' in name or 'admin' in name for name in names)
                async def call(name,args={}):
                    result=await session.call_tool(name,args)
                    assert not result.isError, result
                    if result.structuredContent is not None:
                        return result.structuredContent.get('result',result.structuredContent)
                    return json.loads(result.content[0].text)
                me=await call('who_am_i');assert me['id']==person['id']
                project=await call('create_project',{'name':'Protocol project'})
                room=await call('create_conversation',{'title':'Protocol test','project_id':project['id']})
                posted=await call('post_message',{'conversation_id':room['id'],'body':'MCP works','client_id':'test-1'})
                assert posted['participant_id']==person['id']
                history=await call('read_messages',{'conversation_id':room['id']})
                assert history['items'][0]['name']=='Protocol Agent'
                assert (await call('conversation_statistics',{'conversation_id':room['id']}))['total_messages']==1
                png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1kAAAAASUVORK5CYII='
                attachment=await call('upload_attachment',{'conversation_id':room['id'],'filename':'image.png','content_base64':png,'client_id':'image-1'})
                assert attachment['participant_id']==person['id']
                linked=await call('post_message',{'conversation_id':room['id'],'body':'','client_id':'with-image','attachment_ids':[attachment['id']]})
                await call('annotate_attachment',{'attachment_id':attachment['id'],'kind':'description','body':'Authored test interpretation, not a verified claim.'})
                item=await call('get_attachment',{'attachment_id':attachment['id']})
                assert item['annotations'][0]['name']=='Protocol Agent'
                chunk=await call('read_attachment_chunk',{'attachment_id':attachment['id'],'max_bytes':12})
                assert chunk['next_offset']==12 and not chunk['eof']
                assert base64.b64decode(chunk['content_base64'])==base64.b64decode(png)[:12]
                image=await session.call_tool('view_image_attachment',{'attachment_id':attachment['id']})
                assert not image.isError
                assert image.content[0].type=='image' and image.content[0].mimeType=='image/png'
                assert image.content[0].data==png
                task=await call('create_task',{'conversation_id':room['id'],'title':'Review protocol'})
                assert task['created_by']==person['id']
                claimed=await call('claim_task',{'conversation_id':room['id'],'task_id':task['id']})
                assert claimed['owner_id']==person['id']
                await call('update_task_status',{'conversation_id':room['id'],'task_id':task['id'],'status':'done','note':'Checked'})
                events=await call('task_history',{'conversation_id':room['id'],'task_id':task['id']})
                assert events[-1]['participant_id']==person['id'] and events[-1]['note']=='Checked'
                await call('pin_message',{'conversation_id':room['id'],'message_id':posted['id']})
                pins=await call('list_pinned_messages',{'conversation_id':room['id']})
                assert pins[0]['participant_id']==person['id']
                s.revoke_agent(person['id'])
                result=await session.call_tool('who_am_i',{})
                assert result.isError
    asyncio.run(exercise())
