'use client';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import type {ReactNode} from 'react';

const nav=[['/','➤','Campaigns'],['/templates','▤','Templates'],['/contacts','●','Contacts']];

export default function AppShell({children,user}:{children:ReactNode;user?:{name?:string|null;email?:string}|null}){
  const path=usePathname();
  return <div className="app-shell"><aside className="sidebar"><Link href="/" className="brand"><span className="brand-mark">M</span><span>mailpilot</span></Link><div className="nav-group">{nav.map(([href,icon,label])=>{const active=href==='/'?(path==='/'||path.startsWith('/campaigns')):path.startsWith(href);return <Link key={href} href={href} className={`nav-item ${active?'active':''}`}><span className="nav-icon">{icon}</span><span>{label}</span></Link>})}</div><div className="nav-label">Workspace</div><div className="nav-group"><span className="nav-item"><span className="nav-icon">⌁</span><span>Integrations</span></span><span className="nav-item"><span className="nav-icon">⚙</span><span>Settings</span></span></div><div className="sidebar-bottom"><span className="nav-item"><span className="nav-icon">?</span><span>Help center</span></span></div></aside><main className="main"><header className="topbar"><div className="search"><input aria-label="Search campaigns" placeholder="Search campaigns, contacts…"/></div><div className="top-actions"><span className="btn small">Google connected</span><span className="avatar">{(user?.name||user?.email||'U').slice(0,1).toUpperCase()}</span></div></header>{children}</main></div>;
}
