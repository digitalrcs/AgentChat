import React,{useState} from 'react';

import {api,stamp} from './api';

import {Field} from './ui';

import {useRoomCollection} from './coordination';
import TaskHistory from './TaskHistory';

import './coordination.css';



const statuses=[['open','Open'],['in_progress','In progress'],['blocked','Blocked'],['done','Done']];

export default function Tasks({room,participants,actor,setActor}) {

  const path=`/conversations/${room.id}/tasks`;

  const {data:tasks,error,refresh}=useRoomCollection(path);

  const [title,setTitle]=useState(''),[description,setDescription]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[actionError,setActionError]=useState('');

  async function act(endpoint,payload,success){

    setBusy(true);setActionError('');setNotice('');

    try{await api(endpoint,{participant_id:actor,...payload});await refresh();setNotice(success);return true}

    catch(e){setActionError(e.message);await refresh();return false}

    finally{setBusy(false)}

  }

  async function create(event){event.preventDefault();if(await act(path,{title:title.trim(),description:description.trim()},'Task added to this conversation.')){setTitle('');setDescription('')}}

  const enabled=!!actor&&!busy&&tasks!==null;

  return <section className="task-board" aria-labelledby="tasks-title">

    <h2 id="tasks-title">Shared tasks</h2><p className="muted">Take ownership of a task before working on it; only one participant can own it at once. Set it to Blocked if you need help, or Done when finished. Releasing makes it available again. Agents use the same board through MCP.</p>

    <Field label="Act as"><select aria-label="Task actor" value={actor} disabled={busy} onChange={event=>setActor(event.target.value)}><option value="">Choose your name</option>{participants.filter(person=>person.kind==='human').map(person=><option key={person.id} value={person.id}>{person.name}</option>)}</select></Field>

    {!actor&&<p className="notice">Choose your name to create or claim work. Add yourself in Participants if needed.</p>}

    {error&&<div className="error" role="alert">Cannot refresh tasks: {error}<button onClick={refresh}>Retry</button></div>}

    {actionError&&<p className="error" role="alert">{actionError}</p>}{notice&&<p role="status" className="notice">{notice}</p>}

    <form className="task-create" onSubmit={create}><Field label="Task title"><input required maxLength={200} value={title} onChange={event=>setTitle(event.target.value)} disabled={busy} placeholder="For example: reproduce the reported error"/></Field><Field label="What needs to be done? (optional)"><textarea rows={2} maxLength={4000} value={description} onChange={event=>setDescription(event.target.value)} disabled={busy}/></Field><button className="primary" disabled={!enabled||!title.trim()}>{busy?'Saving…':'Add task'}</button></form>

    {!tasks&&!error&&<p role="status">Loading tasks…</p>}

    {tasks?.length===0&&<p className="notice">No tasks yet. Add the first job for this conversation.</p>}

    {tasks&&<div className="task-columns">{statuses.map(([status,label])=><section className="task-column" key={status} aria-label={`${label} tasks`}><h3>{label} <span>{tasks.filter(task=>task.status===status).length}</span></h3>{tasks.filter(task=>task.status===status).map(task=><article className="task-card" key={task.id} aria-label={`Task ${task.title}`}><h4>{task.title}</h4>{task.description&&<p className="task-description">{task.description}</p>}<p className="task-owner">{task.owner_id?`Owner: ${task.owner_name}`:'Unclaimed'}</p><small>Added by {task.creator_name} · {stamp(task.created_at)}</small>

      {task.latest_note&&<p className="task-description">Latest update: {task.latest_note}</p>}<div className="task-actions">{!task.owner_id&&status==='open'&&<button disabled={!enabled} onClick={()=>act(`${path}/${task.id}/claim`,{},'Task claimed. You are now its owner.')}>Claim task</button>}{task.owner_id===actor&&<><label className="field"><span>Task status</span><select aria-label={`Status for ${task.title}`} disabled={!enabled} value={task.status} onChange={event=>act(`${path}/${task.id}/status`,{status:event.target.value},'Task status updated.')}><option value="in_progress">In progress</option><option value="blocked">Blocked</option><option value="done">Done</option></select></label><button disabled={!enabled} onClick={()=>act(`${path}/${task.id}/status`,{status:'open'},'Task released. Someone else can claim it.')}>Release task</button></>}{task.owner_id&&task.owner_id!==actor&&<div><p className="muted">Only the owner can change or release this task. As the local owner, you can explicitly release it for reassignment.</p><button disabled={!enabled} onClick={()=>{if(window.confirm(`Release the task "${task.title}" owned by ${task.owner_name}? This override is recorded in task history.`))act(`${path}/${task.id}/status`,{status:'open',override:true,note:'Local human explicitly released this task for reassignment.'},'Task released by local owner override.')}}>Override and release</button></div>}</div>

      <TaskHistory task={task} path={path} participants={participants}/>
    </article>)}</section>)}</div>}

  </section>;

}

