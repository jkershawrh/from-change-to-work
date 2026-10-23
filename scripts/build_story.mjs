import {spawnSync} from 'node:child_process'
import {cp,mkdir} from 'node:fs/promises'
import {fileURLToPath} from 'node:url'
import {resolve,dirname} from 'node:path'
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..')
const r=spawnSync('npm',['--prefix','presentation','run','build'],{cwd:root,stdio:'inherit'})
if(r.status!==0)process.exit(r.status??1)
await mkdir(resolve(root,'frontend/dist/show'),{recursive:true})
await cp(resolve(root,'presentation/dist'),resolve(root,'frontend/dist/show'),{recursive:true})
console.log('Cinematic story packaged with the dashboard at /show/.')
