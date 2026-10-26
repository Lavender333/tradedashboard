const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = process.env.DASHBOARD_URL || 'http://127.0.0.1:8000';
const sample = JSON.parse(fs.readFileSync('data/template-snapshot.json', 'utf8'));
(async () => {
 const browser = await chromium.launch({headless:true});
 try {
  for (const name of ['mes-dashboard.html','trading-template.html','trading-template-es.html','trading-template-zb.html']) {
   const page = await browser.newPage({viewport:{width:390,height:844}});
   if (process.env.STATIC_QUOTES) await page.addInitScript(() => { window.LAVENDER_MARKET_API = 'data/market-quotes.json'; });
   const errors=[];
   page.on('pageerror',error=>errors.push(error.message));
   await page.goto(`${base}/${name}`);
   if(name==='mes-dashboard.html') {
    await page.waitForFunction(()=>document.querySelector('#last-close').textContent !== '-');
   } else {
    await page.waitForFunction(()=>window.templateSnapshot?.instruments?.ES);
    assert.match(await page.locator('#auto-es').textContent(), /ES /);
    await page.locator('#refresh-auto-btn').click();
    await page.waitForFunction(()=>!document.querySelector('#refresh-auto-btn').disabled);
    // The live-data gate must remain closed for the actual delayed feed.
    if(sample.provider.includes('Yahoo')) assert.equal(await page.locator('#gate-short').textContent(),'Fail');
    // A bad browser save must not prevent the next load.
    await page.evaluate(()=>Object.keys(localStorage).forEach(k=>localStorage.setItem(k,'{bad json')));
    await page.reload();await page.waitForFunction(()=>window.templateSnapshot?.instruments?.ES);
    // Expire both the publication time and candles, including previously enabled gates.
    const expired=JSON.parse(JSON.stringify(sample)); expired.generated_at='2020-01-01 12:00 UTC';
    for(const context of Object.values(expired.instruments)) {
     context.last_time='2020-01-01 12:00 UTC';context.data_status='live';
     context.automation.data_quality_pass=true;context.automation.execution_eligible=true;
    }
    await page.route('**/data/template-snapshot.json*',route=>route.fulfill({json:expired}));
    await page.locator('#refresh-auto-btn').click();
    await page.waitForFunction(()=>window.templateSnapshot?.instruments?.ES.data_status==='stale');
    assert.equal(await page.locator('#gate-short').textContent(),'Fail');
    assert.match(await page.locator('#auto-status').textContent(), /stale/);
    await page.unroute('**/data/template-snapshot.json*');
    await page.route('**/data/template-snapshot.json*',route=>route.abort());
    await page.locator('#refresh-auto-btn').click();
    await page.waitForFunction(()=>!document.querySelector('#refresh-auto-btn').disabled);
    assert.equal(await page.locator('#gate-short').textContent(),'Fail');
    assert.match(await page.locator('#auto-status').textContent(), /refresh unavailable/);
    await page.locator('#reset-btn').click();
    assert.equal(await page.locator('#gate-short').textContent(),'Fail');
   }
   assert.deepEqual(errors,[],`${name}: browser errors`);
   console.log(`PASS ${name}: load, refresh, stale/failure handling`);
   await page.close();
  }
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exit(1)});
