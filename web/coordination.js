import {useCallback,useEffect,useRef,useState} from 'react';
import {api} from './api';

// A response started before a mutation or room change must never replace newer data.
export function useRoomCollection(path) {
  const [data,setData]=useState(null),[error,setError]=useState('');
  const generation=useRef(0),active=useRef(false);
  const refresh=useCallback(async()=>{
    const current=++generation.current;
    try{const result=await api(path);if(active.current&&current===generation.current){setData(result);setError('')}}
    catch(e){if(active.current&&current===generation.current){setData(null);setError(e.message)}}
  },[path]);
  useEffect(()=>{active.current=true;setData(null);setError('');refresh();const timer=setInterval(refresh,4000);return()=>{active.current=false;generation.current++;clearInterval(timer)}},[refresh]);
  return {data,error,refresh};
}
