import React, {useEffect,useRef,useState} from 'react';
import * as echarts from 'echarts/core';
import {BarChart,LineChart} from 'echarts/charts';
import {GridComponent,TooltipComponent,AriaComponent} from 'echarts/components';
import {SVGRenderer} from 'echarts/renderers';
import {api} from './api';
import {fileSize} from './Attachments';
echarts.use([BarChart,LineChart,GridComponent,TooltipComponent,AriaComponent,SVGRenderer]);

function Chart({option,label}) {
  const ref=useRef(null);
  useEffect(()=>{
    const chart=echarts.init(ref.current,null,{renderer:'svg'});
    chart.setOption({...option,animation:false,aria:{enabled:true},textStyle:{fontFamily:'Segoe UI, sans-serif'},tooltip:{trigger:'axis',renderMode:'richText'}});
    const observer=new ResizeObserver(()=>chart.resize()); observer.observe(ref.current);
    return ()=>{observer.disconnect();chart.dispose()};
  },[option]);
  return <div ref={ref} className="chart" role="img" aria-label={label}/>;
}
export default function Analytics({roomId}) {
  const [data,setData]=useState(null),[error,setError]=useState('');
  useEffect(()=>{let active=true; const refresh=()=>api(`/conversations/${roomId}/stats`).then(d=>{if(active){setData(d);setError('')}}).catch(e=>active&&setError(e.message));refresh();const timer=setInterval(refresh,5000);return()=>{active=false;clearInterval(timer)}},[roomId]);
  if(!data)return <p role="status">{error||'Loading statistics…'}</p>;
  const activityOption={grid:{left:44,right:28,top:28,bottom:48},xAxis:{type:'time',minInterval:86400000,axisLabel:{color:'#65748a',formatter:'{yyyy}-{MM}-{dd}',hideOverlap:true}},yAxis:{type:'value',min:0,minInterval:1,name:'Messages',splitLine:{lineStyle:{color:'#edf0f3'}}},series:[{type:'bar',barMaxWidth:42,itemStyle:{color:'#087e8b',borderRadius:[3,3,0,0]},label:{show:true,position:'top'},data:data.activity.map(d=>[d.day+'T00:00:00Z',d.messages])}],useUTC:true};
  const contributionOption={grid:{left:110,right:44,top:15,bottom:35},xAxis:{type:'value',min:0,minInterval:1},yAxis:{type:'category',inverse:true,data:data.participants.map(p=>p.name),axisLabel:{width:95,overflow:'truncate'},axisTick:{show:false},axisLine:{show:false}},series:[{type:'bar',barMaxWidth:28,label:{show:true,position:'right'},itemStyle:{color:'#087e8b',borderRadius:[0,3,3,0]},data:data.participants.map(p=>p.messages)}]};
  const mediaLabels={image:'Images',audio:'Audio',video:'Video',file:'Other files'};
  const mediaOption={grid:{left:90,right:44,top:15,bottom:35},xAxis:{type:'value',min:0,minInterval:1,name:'Files'},yAxis:{type:'category',inverse:true,data:(data.attachments||[]).map(item=>mediaLabels[item.media_kind]||item.media_kind),axisTick:{show:false},axisLine:{show:false}},series:[{type:'bar',barMaxWidth:28,label:{show:true,position:'right'},itemStyle:{color:'#087e8b',borderRadius:[0,3,3,0]},data:(data.attachments||[]).map(item=>item.files)}]};
  return <div className="analytics"><div className="section-heading"><div><h2>Conversation analytics</h2><p>Measured from saved messages · refreshes every 5 seconds</p></div></div>{error&&<p className="error">{error} Showing last available data.</p>}
    <div className="metrics"><div><strong>{data.total_messages}</strong><span>Messages</span></div><div><strong>{data.active_participants}</strong><span>Contributors</span></div><div><strong>{data.explicit_replies}</strong><span>Linked replies</span></div><div><strong>{data.median_reply_seconds===null?'—':`${Math.round(data.median_reply_seconds)}s`}</strong><span>Median reply time</span></div></div>
    {!data.total_messages?<p className="notice">Send a message to start building this conversation’s statistics.</p>:<><section className="chart-section"><h3>Message activity</h3><p>Messages by UTC day. Days without messages have zero activity.</p><Chart option={activityOption} label="Daily message activity; exact values are available below."/></section><section className="chart-section"><h3>Who contributed</h3><Chart option={contributionOption} label="Message counts by named participant; exact values are available below."/></section></>}
    {!!data.total_attachments&&<section className="chart-section"><h3>Shared media</h3><p>{data.total_attachments} attached files · {fileSize(data.attachment_bytes||0)} total · unsent drafts are excluded</p><Chart option={mediaOption} label="Shared file counts by media type; exact values are available below."/><table><caption>Files by media type</caption><thead><tr><th>Type</th><th>Files</th><th>Size</th></tr></thead><tbody>{(data.attachments||[]).map(item=><tr key={item.media_kind}><td>{mediaLabels[item.media_kind]||item.media_kind}</td><td>{item.files}</td><td>{fileSize(item.bytes)}</td></tr>)}</tbody></table></section>}
    <p className="muted">Reply time uses explicit reply links; it is not model inference speed. Token usage and cost are not estimated.</p>
    <details><summary>View accessible data tables</summary><table><caption>Contributions</caption><thead><tr><th>Participant</th><th>Messages</th><th>Characters</th></tr></thead><tbody>{data.participants.map(p=><tr key={p.id}><td>{p.name}</td><td>{p.messages}</td><td>{p.characters}</td></tr>)}</tbody></table><table><caption>Daily activity (UTC)</caption><thead><tr><th>Date</th><th>Messages</th></tr></thead><tbody>{data.activity.map(d=><tr key={d.day}><td>{d.day}</td><td>{d.messages}</td></tr>)}</tbody></table></details>
  </div>;
}
