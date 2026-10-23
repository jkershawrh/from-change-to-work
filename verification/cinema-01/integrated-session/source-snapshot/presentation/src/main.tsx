import {StrictMode,lazy,Suspense} from 'react'
import {createRoot} from 'react-dom/client'
import './theme.css'
const Story=lazy(()=>import('./cinema/Story'))
const Guided=lazy(()=>import('./App'))
createRoot(document.getElementById('root')!).render(<StrictMode><Suspense fallback={<main style={{padding:40}}>Preparing the capability story…</main>}>{new URLSearchParams(location.search).has('guided')?<Guided/>:<Story/>}</Suspense></StrictMode>)
