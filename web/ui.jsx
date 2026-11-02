import React from 'react';
export function Avatar({name,kind}) {return <span className={'avatar '+(kind || '')}>{name.slice(0,2).toUpperCase()}</span>}
export function Empty({title,children}) {return <div className="empty"><div className="empty-mark" aria-hidden="true">↔</div><h2>{title}</h2><p>{children}</p></div>}
export function Field({label,children}) {return <label className="field"><span>{label}</span>{children}</label>}
export function Notice({children}) {return children ? <p className="notice" role="status">{children}</p> : null}
