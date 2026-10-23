import {test,expect} from '@playwright/test'
import {readFileSync,mkdirSync} from 'node:fs'
import {join} from 'node:path'
const out=process.env.AERIS_TEST_OUTPUT??'verification/onboarding-01'
test('agent packet separates proposed hardware, observed readiness and missing audit',async({page})=>{
 test.skip(!process.env.AERIS_TEST_STATE,'requires the actual configured console')
 mkdirSync(out,{recursive:true});await page.goto('/');await expect(page.getByRole('heading',{name:'A capability delivered. A cell that keeps control.'})).toBeVisible()
 expect((await page.request.get('/api/action-demo/readiness')).status()).toBe(401)
 const code=readFileSync(join(process.env.AERIS_TEST_STATE!,'central/private/viewer-code'),'utf8').trim()
 await page.getByLabel('Dashboard access code').fill(code);await page.getByRole('button',{name:'Unlock dashboard'}).click();await page.getByRole('button',{name:'Check console host',exact:true}).click()
 await expect(page.locator('.dash-metrics').getByText('Ready for simulation',{exact:true})).toBeVisible({timeout:30000})
 await expect(page.locator('.dash-readiness')).toContainText('UNVERIFIED');await expect(page.getByText('VIEWER SESSION',{exact:true})).toBeVisible()
 await expect(page.locator('.dash-metrics')).toContainText('Pending validation')
 expect((await page.request.post('/api/action-demo/controls/disconnect',{headers:{Origin:new URL(page.url()).origin,'X-Aeris-Action':'v1'},data:{}})).status()).toBe(403)
 await page.getByRole('button',{name:'Hardware intake',exact:true}).click()
 await page.getByLabel('Test stage').selectOption('two-host');await page.getByLabel('Compute model / CPU / architecture').fill('Intel candidate; edge CPU not measured');await page.getByLabel('OS / kernel / platform').fill('RHEL planned');await page.getByLabel('Test and acceptance owner').fill('Preston')
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download this hardware handoff'}).click();await(await download).saveAs(out+'/agent-packet.json')
 const packet=JSON.parse(readFileSync(out+'/agent-packet.json','utf8'));expect(packet.proposed_hardware.evidence_status).toBe('UNVERIFIED_OPERATOR_INPUT');expect(packet.proposed_hardware.deployment).toBe('two-host');expect(packet.observed_readiness.measurement_scope).toBe('CURRENT_PROCESS_HOST_ONLY');expect(packet.observed_readiness.physical_motion_authorized).toBe(false);expect(packet.independent_execution_audit).toBe('NOT_INCLUDED');expect(JSON.stringify(packet)).not.toContain(code)
 await page.getByRole('button',{name:'Agent onboarding',exact:true}).click();await expect(page.getByLabel('Agent due diligence prompt')).toContainText('Read AGENTS.md');await expect(page.getByText('From clone to retained evidence.',{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Acceptance gates',exact:true}).click();await expect(page.getByText('Earn each result in its own scope.',{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Demo dashboard',exact:true}).click();await page.getByRole('link',{name:'Open transfer workbench',exact:true}).click();await expect(page.locator('.action-role')).toContainText('VIEWER');await expect(page.getByRole('button',{name:'Transfer & execute'})).toBeDisabled()
})
for(const [name,width,height] of [['desktop',1440,1000],['mobile',390,844]] as const){test('dashboard and agent guide fit '+name,async({page})=>{
 mkdirSync(out,{recursive:true});await page.setViewportSize({width,height});await page.goto('/');await expect(page.locator('.dash-history strong')).toHaveText('7,610');await page.waitForTimeout(1200)
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:out+'/dashboard-'+name+'.png',fullPage:true})
 await page.getByRole('button',{name:'Agent onboarding',exact:true}).click();await expect(page.getByLabel('Agent due diligence prompt')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:out+'/agent-'+name+'.png',fullPage:true})
})}

for(const [name,width,height] of [['desktop',1440,1000],['mobile',390,844]] as const){test('pilot roadmap preserves baseline scope and fits '+name,async({page})=>{
 mkdirSync(out,{recursive:true});let mutations=0;page.on('request',r=>{if(r.method()!=='GET'&&r.url().includes('/api/action-demo'))mutations++})
 await page.setViewportSize({width,height});await page.goto('/?roadmap=1')
 await expect(page.getByRole('heading',{name:'Starting metrics',exact:true})).toBeVisible()
 await expect(page.locator('.dash-pilot-metrics strong')).toHaveText(Array(6).fill('Not measured'))
 await expect(page.locator('.dash-pilot')).toContainText('Standards interoperability is pending')
 await expect(page.locator('.dash-pilot-stages')).toContainText('Historical scope only')
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.screenshot({path:out+'/roadmap-'+name+'.png',fullPage:true})
 await page.getByRole('button',{name:'Demo dashboard',exact:true}).click()
 await page.getByRole('button',{name:'Roadmap & starting metrics',exact:true}).click()
 await expect(page.getByRole('heading',{name:'Starting metrics',exact:true})).toBeVisible()
 expect(mutations).toBe(0)
})}
