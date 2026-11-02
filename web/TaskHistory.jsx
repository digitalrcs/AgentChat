import React,{useState} from 'react';
import {stamp} from './api';
import {useRoomCollection} from './coordination';

function Events({path,participants}){
  const {data,error,refresh}=useRoomCollection(path);
  const owner=id=>id?(participants.find(person=>person.id===id)?.name||id):'Unclaimed';
  const status=value=>({'open':'Open','in_progress':'In progress','blocked':'Blocked','done':'Done'}[value]||value);
  return error?<p className="error" role="alert">Cannot load task history: {error}<button onClick={refresh}>Retry</button></p>:data===null?<p role="status">Loading task history…</p>:<ol className="task-history">{data.map(event=><li key={event.id}><strong>{event.name}</strong> · {event.action.replaceAll('_',' ')}{Boolean(event.override)&&<b className="override-label"> · Local owner override</b>}<small>{stamp(event.created_at)}</small><p>{event.previous_status?`${status(event.previous_status)} → `:''}{status(event.status)}<br/>{event.previous_owner_id?`${owner(event.previous_owner_id)} → `:''}{owner(event.owner_id)}</p>{event.note&&<p className="task-description">Note: {event.note}</p>}</li>)}</ol>;
}

export default function TaskHistory({task,path,participants}){
  const [open,setOpen]=useState(false);
  return <details className="task-history-details" onToggle={event=>setOpen(event.currentTarget.open)}><summary>Task history</summary>{open&&<Events key={task.updated_at} path={`${path}/${task.id}/history`} participants={participants}/>}</details>;
}
