const fs=require('fs'),path=require('path'),crypto=require('crypto'),os=require('os');
const {chromium}=require(process.env.GWA_PLAYWRIGHT_MODULE);
const root=__dirname;
const binary=process.env.GWA_CHROMIUM_EXECUTABLE;
const hash=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const states=['login','home','empty','sources','brief','question','running','error','review','export'];
const results=[],errors=[],network=[];fs.mkdirSync(path.join(root,'screenshots'),{recursive:true});
const check=(x,message)=>{if(!x)throw Error(message)};
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:binary,chromiumSandbox:true});
 try {
 for(const [name,viewport] of [['desktop',{width:1280,height:800}],['mobile',{width:375,height:812}]]){
  const context=await browser.newContext({viewport,locale:'es-CL',reducedMotion:'reduce',serviceWorkers:'block',acceptDownloads:false});
  await context.route('**/*',route=>{const url=route.request().url();if(url.startsWith('file://'+root+'/'))return route.continue();network.push(url.split('?')[0]);return route.abort();});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
  for(const [opt,file] of [['a','option-a.html'],['b','option-b.html']]){
   for(const state of states){
    await page.goto('file://'+root+'/'+file+'?screen='+state);await page.locator('#view h1, #view h2').first().waitFor();
    check(await page.locator('#view').innerText().then(t=>t.length>80),'Missing main content');
    const dims=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));check(dims.scroll<=dims.width,'Overflow '+opt+' '+name+' '+state+' '+JSON.stringify(dims));
    const shot='screenshots/'+opt+'-'+state+'-'+name+'.png';await page.screenshot({path:path.join(root,shot),fullPage:true});
    results.push({id:'VIS-'+opt+'-'+state+'-'+name,status:'pass',option:opt,state,viewport,file:shot,sha256:hash(path.join(root,shot))});
   }
   // Protected local flow, entirely synthetic; this tests the prototype, not the future app.
   await page.goto('file://'+root+'/'+file+'?screen=review');
   check(await page.locator('#approve-button').isDisabled(),'Approval should begin disabled');
   await page.locator('#approve').check();check(await page.locator('#approve-button').isEnabled(),'Approval not enabled');
   await page.locator('#edit-toggle').click();await page.locator('#editor').fill('Borrador de ejemplo editado.');check(await page.locator('#approve-button').isDisabled(),'Editing did not revoke approval');
   check(await page.locator('#edit-status').isVisible(),'Missing edit notice');
   await page.locator('#approve').check();await page.locator('#approve-button').click();check(await page.locator('#export-button').isVisible(),'Approval did not reach export');
   await page.locator('#export-button').click();check((await page.locator('#export-status').innerText()).includes('No se descargó'),'Export simulation notice missing');
   await page.locator('#back-edit').click();check(await page.locator('#approve-button').isDisabled(),'Back-to-edit should revoke approval');
   for(const [target,label] of [['sources','Fuentes'],['brief','Encargo'],['question','Pregunta'],['running','En curso'],['error','Fallo']]){
    await page.locator('#screen').selectOption(target);check(await page.locator('#view').isVisible(),label+' not shown');
   }
   await page.locator('#screen').selectOption('login');check(await page.locator('input[type=password]').getAttribute('readonly')!==null,'Password must be demonstration readonly');
   await page.locator('#auth-mode').click();check(await page.locator('input[type=password]').count()===2,'Initial password setup missing');
   await page.screenshot({path:path.join(root,'screenshots/'+opt+'-first-access-'+name+'.png'),fullPage:true});
   results.push({id:'FLOW-'+opt+'-'+name,status:'pass',checks:['approval initially disabled','explicit approval','editing revokes approval','mock export no download','return-to-edit revokes','state navigation','illustrative password setup']});
   await page.locator('#screen').selectOption('brief');await page.getByRole('button',{name:'Empresa Posible patrocinador'}).hover();
   await page.screenshot({path:path.join(root,'screenshots/'+opt+'-pointer-'+name+'.png'),fullPage:true});
   await page.locator('#screen').selectOption('review');await page.locator('#approve').focus();
   check(await page.evaluate(()=>document.activeElement.id==='approve'),'Keyboard focus missing');
   const focus=await page.locator('#approve').evaluate(el=>getComputedStyle(el).outlineWidth);check(focus!=='0px','Visible focus missing');
   await page.screenshot({path:path.join(root,'screenshots/'+opt+'-keyboard-'+name+'.png'),fullPage:true});
   results.push({id:'FOCUS-'+opt+'-'+name,status:'pass',outlineWidth:focus});
  }
  await page.goto('file://'+root+'/index.html');check(await page.locator('img').evaluateAll(imgs=>imgs.every(i=>i.complete&&i.naturalWidth>0)),'Gallery image not loaded');
  check(await page.locator('body').evaluate(el=>el.scrollWidth<=innerWidth),'Gallery overflow');
  await page.screenshot({path:path.join(root,'screenshots/index-'+name+'.png'),fullPage:true});
  await context.close();
 }
 check(errors.length===0,'Browser errors '+errors.join('; '));check(network.length===0,'Unexpected network attempted '+network.join('; '));
 const artifacts=fs.readdirSync(path.join(root,'screenshots')).sort().map(n=>({path:'screenshots/'+n,sha256:hash(path.join(root,'screenshots',n))}));
 const evidence={phase:'design_mockup_review',application_implemented:false,inference_submitted:false,design_approved:false,node:process.version,playwright:require(path.join(process.env.GWA_PLAYWRIGHT_MODULE,'package.json')).version,browser:browser.version(),browser_binary_sha256:hash(binary),mode:'headless isolated BrowserContext; temporary HOME; no personal profile; no external network',viewports:[{width:1280,height:800},{width:375,height:812}],results,artifacts,console_errors:errors,external_requests:network,limits:['prototype simulation only','no authentication or persistence implementation','not application acceptance','no provider or LLM calls','not an OS isolation attestation for untrusted candidate execution']};
 fs.writeFileSync(path.join(root,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');
 console.log(JSON.stringify({status:'pass',checks:results.length,screenshots:artifacts.length,errors:errors.length,externalRequests:network.length,browser:evidence.browser,playwright:evidence.playwright}));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
