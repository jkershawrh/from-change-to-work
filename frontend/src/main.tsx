import { StrictMode,lazy,Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import './theme.css'
const Workbench=lazy(()=>import('./actions/TransferWorkbench'))
const Dashboard=lazy(()=>import('./dashboard/Dashboard'))
const actions=new URLSearchParams(location.search).get('actions')==='1'
createRoot(document.getElementById('root')!).render(<StrictMode><Suspense fallback={<main style={{padding:40}}>Opening the capability lab…</main>}>{actions?<Workbench/>:<Dashboard/>}</Suspense></StrictMode>)
