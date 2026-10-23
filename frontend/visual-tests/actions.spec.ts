import { test,expect } from '@playwright/test'
import { readFileSync,mkdirSync } from 'node:fs'
import { join } from 'node:path'
const out=process.env.AERIS_TEST_OUTPUT??'verification/action-workbench-01'
test('operator transfers, cuts actual data plane, observes completion, interrupts and explicitly recovers',async({page})=>{
 test.skip(!process.env.AERIS_TEST_STATE,'requires a freshly provisioned real simulator lab')
 mkdirSync(out,{recursive:true});await page.setViewportSize({width:1440,height:900});await page.goto('/?actions=1')
 await page.getByRole('button',{name:'Live simulation',exact:true}).click()
 const code=readFileSync(join(process.env.AERIS_TEST_STATE!,'central/private/operator-code'),'utf8').trim()
 await page.getByLabel('Lab access code').fill(code);await page.getByRole('button',{name:'Unlock lab controls'}).click()
 const transfer=page.getByRole('button',{name:'Transfer & execute'})
 await expect(transfer).toBeEnabled({timeout:20000});await transfer.click()
 await expect(page.getByRole('button',{name:'Disconnect central link',exact:true})).toBeEnabled({timeout:25000})
 const initial=await page.request.get('/api/action-demo/state').then(r=>r.json());expect(initial.task.status).toBe('RUNNING')
 await page.getByRole('button',{name:'Disconnect central link',exact:true}).click()
 await expect(page.locator('.action-stage-title')).toContainText('CENTRAL CUT',{timeout:20000})
 await expect.poll(async()=>{const r=await page.request.get('/api/action-demo/state');const s=await r.json();return s.task?.status},{timeout:60000}).toBe('COMPLETE')
 const isolated=await page.request.get('/api/action-demo/state').then(r=>r.json());expect(isolated.link.connected).toBe(false);expect(isolated.central).toBe('UNREACHABLE');expect(isolated.task.ticks).toBeGreaterThan(initial.task.ticks)
 await page.screenshot({path:out+'/live-disconnected.png',fullPage:true})
 await page.getByRole('button',{name:'Reconnect central link',exact:true}).click();await expect(transfer).toBeEnabled({timeout:20000})
 await transfer.click();const retry=await page.request.get('/api/action-demo/state').then(r=>r.json());expect(retry.task.ticks).toBe(isolated.task.ticks);expect(retry.task.task).toBe(isolated.task.task)
 await page.getByRole('combobox',{name:'Capability',exact:true}).selectOption('rework-positioning');await page.getByRole('button',{name:'New deliberate action ID'}).click();await transfer.click()
 const interrupt=page.getByRole('button',{name:'Interrupt simulator executor',exact:true});await expect(interrupt).toBeEnabled({timeout:30000});await interrupt.click()
 await expect(page.locator('.action-state-overlay strong')).toHaveText('RECOVERY REQUIRED',{timeout:20000});await expect(transfer).toBeDisabled()
 await page.getByRole('button',{name:'Explicitly recover executor'}).click();await expect(page.locator('.action-state-overlay strong')).toHaveText('INTERRUPTED',{timeout:20000})
 await page.getByRole('button',{name:'New deliberate action ID'}).click();await expect(transfer).toBeEnabled();await transfer.click();await expect(page.locator('.action-state-overlay strong')).toHaveText('COMPLETE',{timeout:60000})
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export session observations'}).click();await (await download).saveAs(out+'/browser-session.json')
 await page.getByRole('button',{name:'Rubric',exact:true}).click();await page.screenshot({path:out+'/live-recovered.png',fullPage:true})
 const exported=JSON.parse(readFileSync(out+'/browser-session.json','utf8'));expect(exported.physical_motion_authorized).toBe(false);expect(exported.journal.some((e:{event:string})=>e.event==='DISCONNECT')).toBe(true);expect(exported.journal.some((e:{event:string})=>e.event==='RECOVER')).toBe(true)
})
for(const [name,width,height] of [['stage',1920,1080],['laptop',1440,900],['mobile',390,844]] as const){test('recorded proof stays labeled and fits '+name,async({page})=>{
 mkdirSync(out,{recursive:true});await page.setViewportSize({width,height});await page.goto('/?actions=1');await expect(page.getByText('RETAINED FLIGHTPATH PROOF',{exact:true})).toBeVisible();await expect(page.locator('.action-metric-pair').getByText('761',{exact:true})).toBeVisible()
 await expect(page.getByRole('button',{name:'Transfer & execute'})).toHaveCount(0)
 await page.getByLabel('Exploded presentation view').fill('0.4');await page.getByRole('button',{name:'Solid model',exact:true}).click();await page.waitForTimeout(1500)
 await page.screenshot({path:out+'/recorded-'+name+'.png',fullPage:true})
 if(width>1000){expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight+2)).toBe(true)}
})}
