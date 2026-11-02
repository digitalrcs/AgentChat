import React,{useCallback,useEffect,useRef,useState} from 'react';
import {api,discardAttachment,stamp,uploadAttachment} from './api';
import {AttachmentCard,DraftAttachments,MAX_ATTACHMENTS,MAX_FILE_BYTES} from './Attachments';
import {Avatar,Empty} from './ui';

export default function Conversation({room,participants,actor,setActor,onError}) {
  const [messages,setMessages]=useState([]),[draft,setDraft]=useState(''),[reply,setReply]=useState(null),[busy,setBusy]=useState(false),[sync,setSync]=useState('Loading history…');
  const [files,setFiles]=useState([]),[attachments,setAttachments]=useState({}),[uploadNotice,setUploadNotice]=useState('');
  const cursor=useRef(0),pending=useRef(null),fileInput=useRef(null),controllers=useRef(new Map()),mounted=useRef(true);
  const refreshAttachments=useCallback(async()=>{
    const rows=await api(`/conversations/${room.id}/attachments`);
    if(mounted.current)setAttachments(Object.fromEntries(rows.map(item=>[item.id,item])));
    return rows;
  },[room.id]);

  useEffect(()=>{
    mounted.current=true;
    return()=>{mounted.current=false;for(const controller of controllers.current.values())controller.abort();controllers.current.clear()};
  },[]);

  useEffect(()=>{
    let active=true,fetching=false;cursor.current=0;setMessages([]);
    async function refresh(){
      if(fetching)return;fetching=true;
      try {
        let more=true;
        while(more&&active){
          const result=await api(`/conversations/${room.id}/messages?after_id=${cursor.current}&limit=100`);
          if(!active)return;
          cursor.current=result.next_cursor;
          setMessages(old=>[...old,...result.items.filter(message=>!old.some(item=>item.id===message.id))]);
          more=result.has_more;
        }
        if(active)setSync('History saved locally · checking for new messages');
      } catch(error){if(active)setSync('Connection interrupted · retrying…')}
      finally{fetching=false}
    }
    refresh();const timer=setInterval(refresh,2000);
    return()=>{active=false;clearInterval(timer)};
  },[room.id]);

  useEffect(()=>{
    let active=true;
    refreshAttachments().then(rows=>{
      if(!active||!actor)return;
      const drafts=rows.filter(item=>!item.message_id&&item.participant_id===actor);
      setFiles(old=>old.length?old:drafts.map(item=>({...item,key:item.id,status:'uploaded',progress:100})));
      if(drafts.length)setUploadNotice('Your unsent files were restored. Send them with a message or remove them.');
    }).catch(error=>{if(active)setUploadNotice(error.message)});
    const timer=setInterval(()=>refreshAttachments().catch(()=>{}),4000);
    return()=>{active=false;clearInterval(timer)};
  },[actor,refreshAttachments]);

  function updateFile(key,patch){if(mounted.current)setFiles(old=>old.map(item=>item.key===key?{...item,...patch}:item))}

  async function upload(item){
    const controller=new AbortController();controllers.current.set(item.key,controller);
    updateFile(item.key,{status:'uploading',progress:0,error:''});
    try {
      const result=await uploadAttachment(room.id,actor,item.file,item.key,progress=>updateFile(item.key,{progress}),controller.signal);
      updateFile(item.key,{...result,status:'uploaded',progress:100});
    } catch(error){if(error.name!=='AbortError')updateFile(item.key,{status:'error',error:error.message})}
    finally{controllers.current.delete(item.key)}
  }

  function chooseFiles(event){
    const chosen=Array.from(event.target.files||[]);event.target.value='';setUploadNotice('');
    if(!actor){setUploadNotice('Choose your name before attaching a file.');return}
    if(chosen.length+files.length>MAX_ATTACHMENTS){setUploadNotice(`Attach up to ${MAX_ATTACHMENTS} files to one message. Send or remove the current files first.`);return}
    if(chosen.some(file=>file.size>MAX_FILE_BYTES)){setUploadNotice('Each file must be 100 MB or smaller. No files from this selection were uploaded.');return}
    const names=new Set(files.map(file=>file.filename.toLocaleLowerCase()));
    const accepted=chosen.filter(file=>{const key=file.name.toLocaleLowerCase();if(names.has(key))return false;names.add(key);return true});
    if(accepted.length!==chosen.length)setUploadNotice('A file with that name is already attached. The duplicate was skipped. Remove the existing file first if you want to replace it.');
    const queued=accepted.map(file=>({key:crypto.randomUUID(),file,filename:file.name,size_bytes:file.size,status:'uploading',progress:0}));
    setFiles(old=>[...old,...queued]);
    for(const item of queued)upload(item);
  }

  async function removeFile(item){
    setUploadNotice('');
    if(item.status==='uploading'){controllers.current.get(item.key)?.abort();setFiles(old=>old.filter(file=>file.key!==item.key));return}
    if(item.id){
      updateFile(item.key,{status:'removing'});
      try {await discardAttachment(item.id,actor)}
      catch(error){updateFile(item.key,{status:'uploaded',error:error.message});setUploadNotice(error.message);return}
    }
    setFiles(old=>old.filter(file=>file.key!==item.key));
  }

  const humans=participants.filter(person=>person.kind==='human');
  const filesReady=files.every(file=>file.status==='uploaded')&&files.length<=MAX_ATTACHMENTS;
  const canSend=!!actor&&!!(draft.trim()||files.length)&&filesReady&&!busy;

  async function send(event){
    event.preventDefault();if(!canSend)return;
    setBusy(true);onError('');setUploadNotice('');
    const payload={participant_id:actor,body:draft,reply_to:reply?.id||null,attachment_ids:files.map(file=>file.id)};
    const signature=JSON.stringify(payload);
    if(pending.current?.signature!==signature)pending.current={signature,id:crypto.randomUUID()};
    try {
      await api(`/conversations/${room.id}/messages`,{...payload,client_id:pending.current.id});
      setDraft('');setReply(null);setFiles([]);pending.current=null;
      if(payload.attachment_ids.length)setUploadNotice('Files shared. Open a file’s details to add a description or transcript for text-only agents.');
    } catch(error){onError(error.message);setUploadNotice(error.message)}
    finally{setBusy(false)}
  }

  return <div className="conversation">
    <div className="timeline" aria-label="Conversation messages">
      {!messages.length?<Empty title="Start the discussion">Describe the issue, share evidence, and invite a second perspective. You can attach pictures, documents, audio, and video. Every contribution keeps its author.</Empty>:messages.map(message=><article className="message" id={`message-${message.id}`} key={message.id}>
        <Avatar name={message.name} kind={message.kind}/>
        <div className="message-content">
          <div className="message-meta"><strong>{message.name}</strong><span>{message.kind==='agent'?'Agent':'Human'}</span><time dateTime={message.created_at}>{stamp(message.created_at)}</time><button className="text-button" onClick={()=>setReply(message)} aria-label={`Reply to message ${message.id}`}>Reply · #{message.id}</button></div>
          {message.reply_to&&<a className="reply-link" href={`#message-${message.reply_to}`}>In reply to #{message.reply_to}</a>}
          {message.body&&<div className="message-body">{message.body}</div>}
          {!!message.attachments?.length&&<div className="message-attachments">{message.attachments.map(file=><AttachmentCard key={file.id} attachment={attachments[file.id]||file} actor={actor} onChanged={refreshAttachments} onError={onError}/>)}</div>}
        </div>
      </article>)}
    </div>
    <form className="composer" onSubmit={send}>
      {reply&&<div className="replying">Replying to {reply.name} · #{reply.id}<button type="button" className="text-button" onClick={()=>setReply(null)}>Cancel reply</button></div>}
      <div className="composer-heading"><label>Message as <select value={actor} onChange={event=>setActor(event.target.value)} aria-label="Message author" disabled={busy||files.length>0}><option value="">Choose your name</option>{humans.map(person=><option key={person.id} value={person.id}>{person.name}</option>)}</select></label><small>{sync}</small></div>
      <DraftAttachments items={files} onRemove={removeFile} onRetry={upload} busy={busy}/>
      <div className="compose-row"><textarea aria-label="Message" placeholder={humans.length?'Share a finding, question, or next step…':'Add your name in Participants to send a message.'} value={draft} onChange={event=>setDraft(event.target.value)} maxLength={32000} disabled={busy} rows={3}/><button className="primary" disabled={!canSend}>{busy?'Sending…':'Send message'}</button></div>
      <div className="attachment-toolbar"><input ref={fileInput} className="visually-hidden" type="file" multiple onChange={chooseFiles} disabled={busy||!actor||files.length>=MAX_ATTACHMENTS} aria-label="Choose files to attach"/><button type="button" onClick={()=>fileInput.current?.click()} disabled={busy||!actor||files.length>=MAX_ATTACHMENTS}>Attach files</button><span>Images, documents, audio & video · up to 10 files · 100 MB each</span></div>
      {uploadNotice&&<p className="upload-status" role="status">{uploadNotice}</p>}
    </form>
  </div>;
}
