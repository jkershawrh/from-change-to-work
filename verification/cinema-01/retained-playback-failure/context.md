# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cinema.spec.ts >> all cinematic chapters and mechanism reveals fit stage
- Location: visual-tests/cinema.spec.ts:4:104

# Error details

```
Error: expect(locator).toBeEnabled() failed

Locator:  getByRole('button', { name: /Watch the narrated story/ })
Expected: enabled
Received: disabled
Timeout:  30000ms

Call log:
  - Expect "toBeEnabled" getByRole('button', { name: /Watch the narrated story/ }) with timeout 30000ms
  - waiting for getByRole('button', { name: /Watch the narrated story/ })
    48 × locator resolved to <button disabled class="cine-primary">…</button>
       - unexpected value "disabled"

```

```yaml
- button "Watch the narrated story 6:07" [disabled]
```

# Test source

```ts
  1  | import {test,expect} from '@playwright/test'
  2  | import {mkdirSync} from 'node:fs'
  3  | const out='verification/cinema-01'
  4  | for(const [name,width,height] of [['stage',1920,1080],['laptop',1440,900],['mobile',390,844]] as const)test('all cinematic chapters and mechanism reveals fit '+name,async({page})=>{
> 5  |  mkdirSync(out,{recursive:true});await page.setViewportSize({width,height});const writes:string[]=[];page.on('request',r=>{if(r.method()!=='GET'&&r.url().includes('/api/'))writes.push(r.url())});await page.goto('/show/');await expect(page.getByRole('button',{name:/Watch the narrated story/})).toBeEnabled({timeout:30000});await page.waitForTimeout(1500);await page.screenshot({path:out+'/opening-'+name+'.png',fullPage:true})
     |                                                                                                                                                                                                                                                                                                       ^ Error: expect(locator).toBeEnabled() failed
  6  |  const plan=await page.request.get('/show/audio/plan.json').then(r=>r.json());expect(plan.duration).toBeGreaterThan(300)
  7  |  for(let i=0;i<plan.chapters.length;i++){
  8  |   const ch=plan.chapters[i];await page.evaluate(t=>window.__AERIS_CINEMA__!.seek(t),ch.start+(ch.end-ch.start)*.4);await page.waitForTimeout(150)
  9  |   await expect(page.locator('.cinema')).toHaveAttribute('data-chapter',ch.id)
  10 |   if(ch.id==='architecture'){
  11 |    await expect(page.getByRole('heading',{name:'Who asks for the change?'})).toBeVisible();await expect(page.getByText('An operator selects an approved capability.',{exact:true})).toHaveCount(0)
  12 |    for(let j=0;j<4;j++){
  13 |     await page.getByRole('button',{name:'Reveal the answer',exact:true}).click();await expect(page.locator('.cine-architecture b')).toBeVisible()
  14 |     if(width>1000)expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight+2)).toBe(true)
  15 |     if(j<3)await page.getByRole('button',{name:'Ask the next question',exact:true}).click()
  16 |    }
  17 |    await page.getByRole('button',{name:'Blueprint',exact:true}).click();await page.getByLabel('Exploded edge layers').fill('0.65')
  18 |   }
  19 |   if(width>1000){expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight+2)).toBe(true);const b=await page.locator('.cine-copy').boundingBox(),stage=await page.locator('.cine-stage').boundingBox();expect(b!.y+b!.height).toBeLessThanOrEqual(stage!.y+stage!.height+1)}
  20 |   await page.screenshot({path:out+'/'+ch.id+'-'+name+'.png',fullPage:true})
  21 |  }
  22 |  await expect(page.locator('.cine-payoff')).toContainText('NOT OBSERVED');await expect(page.getByRole('link',{name:'Continue into the dashboard'})).toHaveAttribute('href','/')
  23 |  await page.getByRole('button',{name:'Evidence & scope'}).click();await expect(page.getByRole('complementary',{name:'Evidence and qualification'})).toBeVisible();await expect(page.locator('.cine-evidence')).toContainText('No live observation');await page.getByRole('button',{name:'Close evidence'}).click()
  24 |  expect(writes).toEqual([])
  25 | })
  26 | test('voice clock plays, pauses and seeks without running a robot action',async({page})=>{
  27 |  const writes:string[]=[];page.on('request',r=>{if(r.method()!=='GET'&&r.url().includes('/api/'))writes.push(r.url())});await page.goto('/show/');await page.getByRole('button',{name:/Watch the narrated story/}).click();await expect.poll(()=>page.evaluate(()=>window.__AERIS_CINEMA__!.getState().time)).toBeGreaterThan(.5)
  28 |  await page.getByRole('button',{name:'Pause story',exact:true}).click();const t=await page.evaluate(()=>window.__AERIS_CINEMA__!.getState().time);await page.waitForTimeout(500);expect(await page.evaluate(()=>window.__AERIS_CINEMA__!.getState().time)).toBeCloseTo(t,1)
  29 |  await page.getByLabel('Story position').fill('100');expect(await page.evaluate(()=>document.querySelector('audio')!.currentTime)).toBeCloseTo(100,0)
  30 |  await page.getByRole('button',{name:'Read session observations',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Unlock the dashboard');expect(writes).toEqual([])
  31 | })
  32 | 
```