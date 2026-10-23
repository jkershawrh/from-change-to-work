import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import TransferWorkbench from './actions/TransferWorkbench'
import './theme.css'
createRoot(document.getElementById('root')!).render(<StrictMode><TransferWorkbench/></StrictMode>)
