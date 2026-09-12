import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const folder=path.resolve('outputs/bioreaction_atlas_v02/reference_demo/map');
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
try {
  const page=await browser.newPage({viewport:{width:1280,height:920}});
  const errors=[];
  page.on('pageerror', error=>errors.push(error.message));
  // The delivered figure must function without remote scripts or data requests.
  await page.route(/^https?:/, route=>route.abort());
  await page.goto('file://'+path.join(folder,'reaction_map.html'));
  await page.waitForFunction(()=>document.querySelector('.js-plotly-plot')?._fullData?.length===2);
  const initial=await page.evaluate(()=>{
    const p=document.querySelector('.js-plotly-plot');
    return {traces:p._fullData.map(t=>({name:t.name,points:t.x.length,visible:t.visible})),range:p._fullLayout.xaxis.range};
  });
  const snapshot=await page.locator('body').innerText();
  if(!snapshot.includes('reaction map')) throw new Error('Missing map title');
  // Use rendered legend hit targets, then observe Plotly's actual visibility state.
  const legends=page.locator('.legendtoggle');
  if(await legends.count()!==2) throw new Error('Expected two interactive legend entries');
  await legends.first().click();
  await page.waitForFunction(()=>document.querySelector('.js-plotly-plot')._fullData[0].visible==='legendonly');
  await legends.first().click();
  await page.waitForFunction(()=>document.querySelector('.js-plotly-plot')._fullData[0].visible!== 'legendonly');
  await page.getByRole('button',{name:'Zoom in',exact:true}).click();
  const zoomed=await page.evaluate(()=>document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range);
  if(zoomed[1]-zoomed[0]>=initial.range[1]-initial.range[0]) throw new Error('Zoom did not change range');
  await page.getByRole('button',{name:'Reset axes',exact:true}).click();
  // Hit real rendered SVG points, rather than emitting synthetic Plotly events.
  const renderedPoints=page.locator('.scatterlayer .trace').first().locator('.point');
  const hit=await renderedPoints.first().boundingBox();
  if(!hit) throw new Error('No visible reaction point');
  await page.mouse.move(hit.x+hit.width/2,hit.y+hit.height/2);
  await page.waitForFunction(()=>!document.getElementById('hover-card').hidden && document.getElementById('hover-image').naturalWidth>0);
  const hoveredId=await page.locator('#hover-card').getAttribute('data-record-id');
  if(!hoveredId) throw new Error('Hover not linked to reaction identity');
  await page.screenshot({path:path.join(folder,'hover_structure_check.png'),fullPage:true});
  await page.mouse.click(hit.x+hit.width/2,hit.y+hit.height/2);
  await page.waitForFunction(id=>document.getElementById('details').dataset.recordId===id,hoveredId);
  await page.waitForFunction(()=>document.getElementById('detail-image').naturalWidth>0);
  const selected=await page.evaluate(()=>{
    const id=document.getElementById('details').dataset.recordId;
    return JSON.parse(document.getElementById('reaction-records').textContent).find(r=>r.record_id===id);
  });
  if(await page.locator('#detail-smiles').textContent()!==selected.reaction_smiles) throw new Error('Structure identity mismatch');
  if(await page.locator('#evidence-select option').count()!==selected.evidence.length) throw new Error('Missing source records');
  let evidenceSwitch=false;
  if(selected.evidence.length>1) {
    const last=selected.evidence.length-1;
    await page.locator('#evidence-select').selectOption(String(last));
    if(await page.locator('#detail-locator').innerText()!==selected.evidence[last].source_locator) throw new Error('Source switch failed');
    evidenceSwitch=true;
  }
  // Pinned details must survive hovering a different reaction.
  await page.locator('.plot-shell').scrollIntoViewIfNeeded();
  const nextHit=await renderedPoints.nth(40).boundingBox();
  await page.mouse.move(nextHit.x+nextHit.width/2,nextHit.y+nextHit.height/2);
  await page.waitForFunction(id=>!document.getElementById('hover-card').hidden && document.getElementById('hover-card').dataset.recordId!==id,hoveredId);
  if(await page.locator('#details').getAttribute('data-record-id')!==hoveredId) throw new Error('Hover replaced pinned details');
  await page.mouse.move(5,5);
  await page.waitForFunction(()=>document.getElementById('hover-card').hidden);
  // Dense clusters can put a single-source point on top of the first marker.
  // Find an actually selectable multi-source point and check record-specific context.
  if(!evidenceSwitch) {
    const candidates=await page.evaluate(()=>{
      const rows=new Map(JSON.parse(document.getElementById('reaction-records').textContent).map(r=>[r.record_id,r]));
      return document.getElementById('reaction-map').data[0].customdata.map((id,i)=>({i,n:rows.get(id).evidence.length})).filter(r=>r.n>1).slice(0,30).map(r=>r.i);
    });
    for(const i of candidates) {
      const box=await renderedPoints.nth(i).boundingBox();
      await page.mouse.click(box.x+box.width/2,box.y+box.height/2);
      const count=await page.locator('#evidence-select option').count();
      if(count<2) continue;
      await page.locator('#evidence-select').selectOption(String(count-1));
      const matches=await page.evaluate(()=>{
        const id=document.getElementById('details').dataset.recordId;
        const row=JSON.parse(document.getElementById('reaction-records').textContent).find(r=>r.record_id===id);
        const e=row.evidence.at(-1);
        return document.getElementById('detail-locator').textContent===e.source_locator && document.getElementById('detail-context').textContent===JSON.stringify(e.context,null,2);
      });
      if(!matches) throw new Error('Multi-source conditions mixed or incorrectly switched');
      evidenceSwitch=true;break;
    }
    if(!evidenceSwitch) throw new Error('Could not verify multi-source switching');
  }
  await page.mouse.move(5,5);
  await page.screenshot({path:path.join(folder,'browser_verification.png'),fullPage:true});
  if(errors.length) throw new Error('Browser errors: '+errors.join('; '));
  const report={offline:true,legend_toggle:true,zoom:true,structure_hover:true,click_pins_details:true,evidence_switch:evidenceSwitch,hover_preserves_selection:true,errors,traces:initial.traces};
  await fs.writeFile(path.join(folder,'browser_verification.json'),JSON.stringify(report,null,2));
  for(const name of ['query','neighbor_01']) {
    await page.goto('file://'+path.resolve(`outputs/bioreaction_atlas_v02/reference_demo/rxnfp/cards/${name}.svg`));
    await page.locator('svg').waitFor();
    if(await page.locator('svg path').count()<5) throw new Error('Reaction diagram is empty');
    await page.locator('svg').screenshot({path:path.join(folder,`diagram_${name}_check.png`)});
  }
  console.log(JSON.stringify(report));
} finally {
  await browser.close();
}
