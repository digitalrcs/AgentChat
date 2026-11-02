export async function api(path, data) {
  const response = await fetch('/api' + path, data === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-AgentChat':'local-ui'},body:JSON.stringify(data)});
  if (!response.ok) {
    const error = await response.json().catch(()=>({detail:response.statusText}));
    throw new Error(typeof error.detail === 'string' ? error.detail : 'Check the supplied fields.');
  }
  return response.json();
}
export function stamp(value) {return new Date(value).toLocaleString([], {month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});}

export async function discardAttachment(id, participantId) {
  const response = await fetch(`/api/attachments/${encodeURIComponent(id)}?participant_id=${encodeURIComponent(participantId)}`, {
    method: 'DELETE', headers: {'X-AgentChat':'local-ui'},
  });
  if (!response.ok) {
    const error = await response.json().catch(()=>({detail:response.statusText}));
    throw new Error(typeof error.detail === 'string' ? error.detail : 'The draft file could not be removed.');
  }
}

export function uploadAttachment(roomId, participantId, file, clientId, onProgress, signal) {
  return new Promise((resolve,reject)=>{
    const request = new XMLHttpRequest();
    const query = new URLSearchParams({participant_id:participantId,filename:file.name,client_id:clientId});
    const abort = ()=>request.abort();
    const cleanup = ()=>signal?.removeEventListener('abort',abort);
    request.open('POST',`/api/conversations/${encodeURIComponent(roomId)}/attachments?${query}`);
    request.setRequestHeader('X-AgentChat','local-ui');
    request.setRequestHeader('Content-Type',file.type || 'application/octet-stream');
    request.upload.onprogress = event=>{
      if (event.lengthComputable) onProgress(Math.round(event.loaded/event.total*100));
    };
    request.onload = ()=>{
      cleanup();
      let result;
      try {result=JSON.parse(request.responseText)} catch {reject(new Error('The server returned an unreadable upload response.'));return}
      if (request.status>=200 && request.status<300) resolve(result);
      else reject(new Error(typeof result.detail==='string' ? result.detail : 'This file could not be uploaded.'));
    };
    request.onerror = ()=>{cleanup();reject(new Error('Upload connection lost. Retry the file or remove it.'))};
    request.onabort = ()=>{cleanup();reject(new DOMException('Upload canceled.','AbortError'))};
    signal?.addEventListener('abort',abort,{once:true});
    if(signal?.aborted){cleanup();reject(new DOMException('Upload canceled.','AbortError'));return}
    request.send(file);
  });
}
