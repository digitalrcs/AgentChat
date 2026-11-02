import React,{useState} from 'react';
import {api,stamp} from './api';
import './attachments.css';

export const MAX_FILE_BYTES=100*1024*1024;
export const MAX_ATTACHMENTS=10;

export function fileSize(bytes) {
  if (bytes<1024) return `${bytes} B`;
  if (bytes<1024*1024) return `${(bytes/1024).toFixed(1)} KB`;
  return `${(bytes/(1024*1024)).toFixed(1)} MB`;
}

function safeFileUrl(value,id,download=false) {
  const fallback=`/api/attachments/${encodeURIComponent(id)}/content${download?'?download=true':''}`;
  if(!value)return fallback;
  try {const parsed=new URL(value,location.origin);return parsed.origin===location.origin&&parsed.pathname.startsWith('/api/attachments/')?parsed.pathname+parsed.search:fallback}
  catch {return fallback}
}

function MediaPreview({attachment}) {
  const [failed,setFailed]=useState(false);
  const source=safeFileUrl(attachment.preview_url,attachment.id);
  if(failed) return <p className="media-fallback">This browser cannot preview the original file. You can still download it below.</p>;
  if(attachment.media_kind==='image') return <a className="image-preview-link" href={source} target="_blank" rel="noreferrer" aria-label={`Open original image ${attachment.filename}`}><img className="attachment-image" src={source} alt={attachment.filename} loading="lazy" onError={()=>setFailed(true)}/></a>;
  if(attachment.media_kind==='audio') return <audio controls preload="none" src={source} aria-label={`Play ${attachment.filename}`} onError={()=>setFailed(true)}>Your browser does not support audio playback.</audio>;
  if(attachment.media_kind==='video') return <video controls preload="metadata" playsInline src={source} aria-label={`Play ${attachment.filename}`} onError={()=>setFailed(true)}>Your browser does not support video playback.</video>;
  return null;
}

export function AttachmentCard({attachment,actor,onChanged,onError}) {
  const [annotationKind,setAnnotationKind]=useState(['audio','video'].includes(attachment.media_kind)?'transcript':'description');
  const [body,setBody]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState('');
  async function save(event) {
    event.preventDefault();if(!actor||!body.trim()||busy)return;
    setBusy(true);setNotice('');
    try {
      await api(`/attachments/${attachment.id}/annotations`,{participant_id:actor,kind:annotationKind,body});
      setBody('');setNotice('Text note saved separately from the original file.');await onChanged();
    } catch(error){onError(error.message);setNotice(error.message)} finally{setBusy(false)}
  }
  const notes=attachment.annotations||[];
  return <section className="attachment-card" aria-label={`Attachment ${attachment.filename}`}>
    <div className="attachment-file-heading"><span className="file-type">{attachment.media_kind||'file'}</span><strong>{attachment.filename}</strong><span className="file-size">{fileSize(attachment.size_bytes||0)}</span></div>
    <MediaPreview attachment={attachment}/>
    <div className="attachment-file-meta"><span>Original file · shared by {attachment.name||'the message author'}</span><a href={safeFileUrl(attachment.download_url,attachment.id,true)} download={attachment.filename}>Download original</a></div>
    <details className="attachment-details"><summary>File details{notes.length?` and ${notes.length} text ${notes.length===1?'note':'notes'}`:''}</summary><dl><dt>Type</dt><dd>{attachment.mime_type||'application/octet-stream'}</dd><dt>Uploaded</dt><dd>{stamp(attachment.created_at)}</dd><dt>File ID</dt><dd>{attachment.id}</dd></dl>
      {notes.map(note=><article className="attachment-annotation" key={note.id}><div><strong>{(note.annotation_kind||note.kind)==='transcript'?'Transcript':'Description'}</strong><span>Added by {note.name} · {note.author_kind==='agent'?'Agent':'Human'} · {stamp(note.created_at)}</span></div><p>{note.body}</p></article>)}
      <p className="media-help">Descriptions and transcripts are contributed notes, not part of the original file. Text-only agents can use these notes; they cannot hear or watch a recording by themselves.</p>
      {actor?<form className="annotation-form" onSubmit={save}><label>Text note type<select value={annotationKind} onChange={event=>setAnnotationKind(event.target.value)} disabled={busy}><option value="description">Description</option><option value="transcript">Transcript</option></select></label><label>Describe the file or paste its transcript<textarea value={body} onChange={event=>setBody(event.target.value)} maxLength={32000} required rows={3} disabled={busy} placeholder="Explain what is in the file. If you used an automated transcript, say so and check it for mistakes."/></label><button type="submit" disabled={busy||!body.trim()}>{busy?'Saving…':'Add text note'}</button></form>:<p className="media-help">Choose your name in the message composer to add a description or transcript.</p>}
      {notice&&<p className="upload-status" role="status">{notice}</p>}
    </details>
  </section>;
}

export function DraftAttachments({items,onRemove,onRetry,busy}) {
  if(!items.length)return null;
  return <ul className="attachment-drafts" aria-label="Files to attach">{items.map(item=><li key={item.key} className={item.status==='error'?'attachment-draft has-error':'attachment-draft'}><div className="draft-file-info"><strong>{item.filename}</strong><span>{fileSize(item.size_bytes)} · {item.status==='uploaded'?'Ready to send':item.status==='uploading'?`Uploading ${item.progress}%`:item.status==='removing'?'Removing…':'Upload failed'}</span>{item.status==='uploading'&&<progress aria-label={`Upload progress for ${item.filename}`} value={item.progress} max={100}/>} {item.error&&<span className="draft-error" role="alert">{item.error}</span>}</div><div className="draft-actions">{item.status==='error'&&item.file&&<button type="button" className="text-button" disabled={busy} onClick={()=>onRetry(item)}>Retry</button>}<button type="button" className="text-button" disabled={busy||item.status==='removing'} onClick={()=>onRemove(item)} aria-label={`Remove ${item.filename}`}>{item.status==='uploading'?'Cancel':'Remove'}</button></div></li>)}</ul>;
}
