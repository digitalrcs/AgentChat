/** Repeatable UI regression with isolated, mocked API data. Never mutates a real database.
 * Run: node tests/media-browser.mjs
 * Optional: AGENTCHAT_BASE_URL=http://127.0.0.1:8768 (uses that server's built UI only).
 * Browser plugin is not available to standalone scripts; uses installed Playwright.
 */
import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium,expect} from '@playwright/test';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const results=path.join(root,'data','ui-test-results');await fs.mkdir(results,{recursive:true});
let server;
let baseURL=process.env.AGENTCHAT_BASE_URL;
if(!baseURL){
  const dist=path.join(root,'dist');
  server=createServer(async(request,response)=>{
    const pathname=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname);
    const file=path.resolve(dist,'.'+(pathname==='/'?'/index.html':pathname));
    if(!file.startsWith(dist+path.sep)){response.writeHead(403).end();return}
    try{const body=await fs.readFile(file);response.writeHead(200,{'Content-Type':({'.html':'text/html','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml','.png':'image/png'})[path.extname(file)]||'application/octet-stream'}).end(body)}catch{response.writeHead(404).end()}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  baseURL=`http://127.0.0.1:${server.address().port}`;
}
const browser=await chromium.launch({headless:true,...(process.env.AGENTCHAT_BROWSER_CHANNEL?{channel:process.env.AGENTCHAT_BROWSER_CHANNEL}:{})});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const pageErrors=[];page.on('pageerror',error=>pageErrors.push(error.message));
const people=[{id:'human-1',name:'Test participant',kind:'human',created_at:new Date().toISOString()}];
const room={id:'room-1',title:'Media verification',objective:'Synthetic browser test for safe media sharing.',project_id:null,created_at:new Date().toISOString(),updated_at:new Date().toISOString(),message_count:0};
const files=[],messages=[],bytes=new Map(),uploadAttempts=new Map();
let nextId=0,failNextPost=false;
const json=(route,data,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
await page.route('**/api/**',async route=>{
  const request=route.request(),url=new URL(request.url()),p=url.pathname,method=request.method();
  if(p==='/api/participants')return json(route,people);
  if(p==='/api/projects')return json(route,[]);
  if(p==='/api/conversations')return json(route,[{...room,message_count:messages.length}]);
  if(p==='/api/conversations/room-1/attachments'){
    if(method==='GET')return json(route,files);
    assert.equal(request.headers()['x-agentchat'],'local-ui');
    const key=url.searchParams.get('client_id');assert.ok(key);
    uploadAttempts.set(key,(uploadAttempts.get(key)||0)+1);
    if(url.searchParams.get('filename')==='retry.txt'&&uploadAttempts.get(key)===1)return json(route,{detail:'Simulated temporary upload failure.'},503);
    const buffer=request.postDataBuffer()||Buffer.alloc(0),mime=request.headers()['content-type'];
    const id=`file-${++nextId}`;
    const file={id,conversation_id:room.id,participant_id:'human-1',message_id:null,filename:url.searchParams.get('filename'),mime_type:mime,media_kind:mime.startsWith('image/')?'image':mime.startsWith('audio/')?'audio':mime.startsWith('video/')?'video':'file',size_bytes:buffer.length,sha256:'test-only',created_at:new Date().toISOString(),name:'Test participant',kind:'human',preview_url:`/api/attachments/${id}/content`,download_url:`/api/attachments/${id}/content?download=true`,annotations:[]};
    bytes.set(id,buffer);files.push(file);return json(route,file);
  }
  if(p==='/api/conversations/room-1/messages'){
    if(method==='GET'){const found=messages.filter(m=>m.id>Number(url.searchParams.get('after_id')||0));return json(route,{items:found,next_cursor:found.at(-1)?.id||Number(url.searchParams.get('after_id')||0),has_more:false})}
    if(failNextPost){failNextPost=false;return json(route,{detail:'Simulated message send failure.'},503)}
    const data=request.postDataJSON();assert.equal(data.participant_id,'human-1');assert.ok(data.client_id);
    const attachments=data.attachment_ids.map(id=>files.find(f=>f.id===id));assert.ok(attachments.every(Boolean));
    const message={...data,id:messages.length+1,conversation_id:room.id,name:'Test participant',kind:'human',created_at:new Date().toISOString(),attachments};
    attachments.forEach(file=>file.message_id=message.id);messages.push(message);return json(route,message);
  }
  const content=p.match(/^\/api\/attachments\/([^/]+)\/content$/);
  if(content){const f=files.find(f=>f.id===content[1]);return route.fulfill({status:200,headers:{'Content-Type':f.mime_type,...(url.searchParams.has('download')?{'Content-Disposition':`attachment; filename="${f.filename}"`}:{})},body:bytes.get(f.id)})}
  const annotation=p.match(/^\/api\/attachments\/([^/]+)\/annotations$/);
  if(annotation){const f=files.find(f=>f.id===annotation[1]),data=request.postDataJSON();f.annotations.push({id:`note-${f.annotations.length}`,attachment_id:f.id,participant_id:'human-1',name:'Test participant',author_kind:'human',annotation_kind:data.kind,body:data.body,created_at:new Date().toISOString()});return json(route,f)}
  const remove=p.match(/^\/api\/attachments\/([^/]+)$/);
  if(remove&&method==='DELETE'){const index=files.findIndex(f=>f.id===remove[1]);assert.equal(files[index].message_id,null);files.splice(index,1);return json(route,{removed:true})}
  return json(route,{detail:`Unexpected test request ${method} ${p}`},404);
});

function wav(){const rate=8000,samples=1600,b=Buffer.alloc(44+samples*2);b.write('RIFF');b.writeUInt32LE(b.length-8,4);b.write('WAVE',8);b.write('fmt ',12);b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);b.writeUInt32LE(rate,24);b.writeUInt32LE(rate*2,28);b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(samples*2,40);for(let i=0;i<samples;i++)b.writeInt16LE(Math.round(4000*Math.sin(i*2*Math.PI*440/rate)),44+i*2);return b}
try{
  await page.goto(baseURL+'/?room=room-1&view=chat');
  await expect(page.getByRole('heading',{name:'Media verification',exact:true})).toBeVisible();
  await page.getByRole('combobox',{name:'Message author'}).selectOption('human-1');
  const input=page.getByLabel('Choose files to attach');
  await input.setInputFiles({name:'retry.txt',mimeType:'text/plain',buffer:Buffer.from('A synthetic log line.')});
  await expect(page.getByText('Simulated temporary upload failure.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Retry',exact:true}).click();
  await expect(page.getByText(/Ready to send/)).toBeVisible();
  assert.equal([...uploadAttempts.values()][0],2,'Upload retry should reuse the same client ID');
  await input.setInputFiles({name:'retry.txt',mimeType:'text/plain',buffer:Buffer.from('A synthetic log line.')});
  await expect(page.getByText(/duplicate was skipped/)).toBeVisible();assert.equal(files.length,1);
  await expect(page.getByRole('combobox',{name:'Message author'})).toBeDisabled();
  failNextPost=true;
  await page.getByRole('button',{name:'Send message',exact:true}).click();
  await expect(page.getByText(/Ready to send/)).toBeVisible();assert.equal(messages.length,0);
  await page.getByRole('button',{name:'Send message',exact:true}).click();
  await expect(page.getByRole('region',{name:'Attachment retry.txt',exact:true})).toBeVisible();
  await expect(page.getByRole('combobox',{name:'Message author'})).toBeEnabled();
  const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64');
  const videoBuffer=await fs.readFile(path.join(root,'tests','fixtures','test-video.mp4'));
  await input.setInputFiles([{name:'image.png',mimeType:'image/png',buffer:png},{name:'recording.wav',mimeType:'audio/wav',buffer:wav()},{name:'clip.mp4',mimeType:'video/mp4',buffer:videoBuffer}]);
  await expect(page.getByText(/Ready to send/)).toHaveCount(3);
  await page.getByRole('textbox',{name:'Message',exact:true}).fill('Synthetic image, audio and video for the browser test.');
  await page.getByRole('button',{name:'Send message',exact:true}).click();
  const imageCard=page.getByRole('region',{name:'Attachment image.png',exact:true});
  await expect(imageCard).toBeVisible();await expect(imageCard.locator('img')).toBeVisible();
  assert.ok(await imageCard.locator('img').evaluate(image=>image.complete&&image.naturalWidth>0));
  await expect(page.locator('audio')).toHaveCount(1);await expect(page.locator('video')).toHaveCount(1);
  await page.locator('audio').evaluate(async media=>{media.muted=true;await media.play();media.pause()});
  await page.locator('video').evaluate(async media=>{media.muted=true;await media.play();media.pause()});
  await imageCard.getByText('File details',{exact:true}).click();
  await imageCard.getByLabel('Describe the file or paste its transcript').fill('Human description: a tiny synthetic test image.');
  await imageCard.getByRole('button',{name:'Add text note',exact:true}).click();
  await expect(imageCard.getByText('Human description: a tiny synthetic test image.',{exact:true})).toBeVisible();
  await expect(imageCard.getByText(/Added by Test participant/)).toBeVisible();
  await input.setInputFiles({name:'discard.txt',mimeType:'text/plain',buffer:Buffer.from('Discard this draft.')});
  await expect(page.getByText(/Ready to send/)).toBeVisible();
  await page.getByRole('button',{name:'Remove discard.txt',exact:true}).click();
  await expect(page.getByRole('list',{name:'Files to attach'})).toHaveCount(0);
  assert.equal(files.filter(f=>f.message_id===null).length,0);
  await input.setInputFiles(Array.from({length:11},(_,index)=>({name:`too-many-${index}.txt`,mimeType:'text/plain',buffer:Buffer.from('x')})));
  await expect(page.getByText(/Attach up to 10 files to one message/)).toBeVisible();assert.equal(files.length,4);
  await page.screenshot({path:path.join(results,'media-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile page must not overflow horizontally');
  await page.screenshot({path:path.join(results,'media-mobile.png'),fullPage:true});
  assert.deepEqual(pageErrors,[]);
  console.log('PASS: upload retry, duplicate prevention, author lock, failed-send preservation, image/audio/video rendering and playback, attributed notes, draft removal, file count limit and mobile layout.');
  console.log(`Screenshots: ${results}`);
}catch(error){console.error(JSON.stringify({files:files.map(f=>({id:f.id,name:f.filename,kind:f.media_kind,size:f.size_bytes})),messages:messages.map(m=>({id:m.id,attachments:m.attachments.map(a=>a.filename)})),body:await page.locator('main').innerText()},null,2));await page.screenshot({path:path.join(results,'failure.png'),fullPage:true});throw error}
finally{await browser.close();if(server)await new Promise(resolve=>server.close(resolve))}
