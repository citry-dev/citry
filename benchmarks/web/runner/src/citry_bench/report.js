/* Draw the retained observations locally; filters never rerun a benchmark. */
const data = JSON.parse(document.getElementById('report-data').textContent);
const names = {citry:'Citry', django_htmx_alpine:'Django + HTMX + Alpine', fasthtml:'FastHTML',
  tetra:'Tetra', unicorn:'django-unicorn', reactpy:'ReactPy', reflex:'Reflex',
  jinja_htmx_alpine:'Jinja + HTMX + Alpine', django_components:'django-components',
  python_vue:'Python API + Vue', python_react:'Python API + React',
  next:'Next.js', nuxt:'Nuxt', nuxt_csr:'Nuxt CSR control',
  django_rusty_templates:'Rusty + HTMX + Alpine'};
// Frameworks are listed in fixed groups so a reader compares like with like.
// An app missing from these lists still appears, in a last group of its own.
const appGroups=[['Citry',['citry']],
  ['Django libraries',['django_htmx_alpine','django_rusty_templates','jinja_htmx_alpine','tetra','unicorn',
    'django_components']],
  ['Other Python libraries',['fasthtml','reactpy','reflex']],
  ['JavaScript SSR',['next','nuxt']],
  ['Server API + CSR',['python_react','python_vue','nuxt_csr']]];
const palette = ['#087e8b','#4169a8','#bd5d27','#8256a0','#338355','#b34569','#73622d','#4c6291','#a45835','#557b33','#7a4c75'];
const readyPhaseKeys = ['browser_before','server','exchange_residual','response_receive','browser_after','unclassified'];
const phasePalette = {browser_before:'#627d98',server:'#2f855a',exchange_residual:'#d69e2e',
  response_receive:'#dd6b20',browser_after:'#3182ce',unclassified:'#a0aec0',layout_wait:'#805ad5'};
const layoutEndpointVersion = 'second-rAF-layout-opportunity-v1';
const canonical = data.run.scenario_revision === 'canonical-project-v1';
const memoryRecords = [...(data.memory||[]), ...(data.memory_invalid_records||[])];
const countLabel = count => canonical ? `${count} outputs` : `${count} rows`;
const recordedApps = new Set([...(data.profile.apps||[]), ...data.samples.map(row => row.app),
  ...memoryRecords.map(row => row.app)]);
const groupedApps = new Set(appGroups.flatMap(([,members]) => members));
const otherApps = [...recordedApps].filter(app => !groupedApps.has(app)).sort();
const appGroup = new Map([...appGroups, ['Other', otherApps]]
  .flatMap(([group,members]) => members.filter(app => recordedApps.has(app)).map(app => [app,group])));
const apps = [...appGroup.keys()];
// Each bar row gets a y position; a group heading takes extra space above
// the first row of its group. One function places the rows, so every chart
// lines its rows up the same way.
function rowLayout(top, step) {
  const rows=[], headings=[];
  let y=top, previous;
  for(const app of apps) {
    if(appGroup.get(app)!==previous) {
      previous=appGroup.get(app);
      // The first heading sits in the space the chart already reserves above
      // its first row; later headings push their group down.
      if(rows.length) y+=28;
      headings.push({label:previous,y:y-24});
    }
    rows.push({app,y});y+=step;
  }
  return {rows,headings,height:y+46};
}
function drawHeadings(svg, headings, left) {
  for(const {label,y} of headings) {
    // The Citry rows sit first, right under the legend, so their heading is
    // left out to give that gap more room; its space in the layout stays.
    if(label==='Citry') continue;
    // Headings end where the app names end, so each reads as the label of
    // the names below it.
    svg.append(element('text',{x:left-12,y,'font-weight':'700',class:'group-heading','text-anchor':'end'},label));
  }
}
const counts = [...new Set([...(data.profile.counts||[]), ...data.samples.map(row => row.count),
  ...memoryRecords.map(row => row.count)])].sort((a,b) => a-b);
const actions = [...new Set([...data.samples, ...memoryRecords]
  .filter(row => row.action !== 'initial').map(row => row.action))];
const pageLoads = [...new Set([...data.samples, ...memoryRecords]
  .filter(row => row.action === 'initial').map(row => row.page_load ?? 1))]
  .sort((a,b) => a-b);
const countSelect = document.getElementById('count');
const actionSelect = document.getElementById('action');
const pageLoadSelect = document.getElementById('page-load');
document.getElementById('count-label').textContent = canonical ? 'Canonical outputs' : 'Rows';
for (const count of counts) countSelect.add(new Option(countLabel(count), count));
for (const action of actions) actionSelect.add(new Option(action.replaceAll('_',' '), action));
if(!actions.length) { actionSelect.add(new Option('No actions recorded','')); actionSelect.disabled=true; }
for (const load of pageLoads) pageLoadSelect.add(new Option(load===1 ? 'First load' : load===2 ? 'Second load' : `Load ${load}`, load));
if(pageLoads.length<2) pageLoadSelect.disabled=true;
const status = document.getElementById('run-status');
status.textContent = data.run.kind==='memory' ?
  `Memory run ${data.run.id || 'unknown'}: ${data.run.status || 'unknown'}. `+
    `${(data.memory||[]).reduce((sum,row)=>sum+row.successes,0)} scenario-success observations; `+
    `${data.memory_invalid_observations||0} invalid.` :
  `${data.memory_run ? `Latency run ${data.run.id || 'unknown'}: ${data.run.status || 'unknown'}; `+
    `memory run ${data.memory_run.id || 'unknown'}: ${data.memory_run.status || 'unknown'}. ` :
    `Run ${data.run.id || 'unknown'}: ${data.run.status || 'unknown'}. `}` +
    `${data.samples.filter(row=>row.status==='ok').length} successful, ` +
    `${data.samples.filter(row=>!['ok','not-run'].includes(row.status)).length} failed, ` +
    `${data.samples.filter(row=>row.status==='not-run').length} not run (excluding warmups).` +
    (data.run.kind==='derived-latency' ?
      ` Timing reuses normal qualification blocks ${(data.run.selected_blocks||[]).join(', ')}; no separate timing run.` : '') +
    ((data.memory_run || (data.memory||[]).length || data.memory_invalid_observations) ? ` Memory observations were measured separately; `+
      `${data.memory_invalid_observations||0} invalid, ${data.memory_not_run_observations||0} not run.` : '');
const ns = 'http://www.w3.org/2000/svg';
function element(tag, attributes={}, text) {
  const node = document.createElementNS(ns, tag);
  for (const [key,value] of Object.entries(attributes)) node.setAttribute(key,value);
  if (text !== undefined) node.textContent=text;
  return node;
}
function median(values) {
  const ordered=[...values].sort((a,b)=>a-b), mid=Math.floor(ordered.length/2);
  return ordered.length%2 ? ordered[mid] : (ordered[mid-1]+ordered[mid])/2;
}
function format(value, bytes, count=false, memoryBytes=false) {
  if (count) return `${value.toLocaleString('en-US', {maximumFractionDigits:1})}`;
  if (!bytes) return `${value.toFixed(2)} ms`;
  if (memoryBytes) return `${(value/(1024*1024)).toFixed(2)} MiB`;
  return `${value.toLocaleString('en-US', {maximumFractionDigits:1})} B`;
}
let downloads=[];
// Charts and sections render into whichever section body is current.
let target=document.getElementById('charts');
// Collapsed sections and charts are keyed by title, so a redraw after a
// select change keeps them collapsed. The saved copy is a per-viewer
// convenience; storage can be missing or blocked, so the page works without it.
const collapseKey='citry-bench-collapsed';
let collapsed=new Set();
try { collapsed=new Set(JSON.parse(localStorage.getItem(collapseKey)||'[]')); } catch { collapsed=new Set(); }
function saveCollapsed() {
  try { localStorage.setItem(collapseKey,JSON.stringify([...collapsed])); } catch { /* keep in memory only */ }
}
// A heading button that shows or hides the body it controls.
function toggleHeading(tag, key, label, body) {
  const heading=document.createElement(tag);
  const button=document.createElement('button');
  button.type='button';button.className='toggle';button.textContent=label;
  body.id=`panel-${document.querySelectorAll('#charts .toggle').length}`;
  button.setAttribute('aria-controls',body.id);
  const apply=()=>{
    const open=!collapsed.has(key);
    button.setAttribute('aria-expanded',String(open));body.hidden=!open;
  };
  button.addEventListener('click',()=>{
    if(collapsed.has(key)) collapsed.delete(key); else collapsed.add(key);
    saveCollapsed();apply();
  });
  heading.append(button);apply();
  return heading;
}
function beginSection(title) {
  const section=document.createElement('section');section.className='chart-group';
  const body=document.createElement('div');body.className='group-body';
  // Create the heading once the section is in the page.
  section.append(body);document.getElementById('charts').append(section);
  section.prepend(toggleHeading('h2',`section:${title}`,title,body));
  target=body;
}
// The top-of-page selects hold the shared state; a chart's own selects copy
// their options and write back to them, so every select shows the same value.
const controlSelects={count:countSelect,action:actionSelect,load:pageLoadSelect};
const controlLabels={count:canonical ? 'Canonical outputs' : 'Rows',action:'Server action',load:'Load detail'};
let pendingFocus=null;
function inlineSelect(kind, title) {
  const source=controlSelects[kind];
  const select=document.createElement('select');select.className='inline-select';
  select.dataset.control=kind;select.setAttribute('aria-label',`${controlLabels[kind]} for ${title}`);
  for(const option of source.options) select.add(new Option(option.text,option.value));
  select.value=source.value;
  select.addEventListener('change',()=>{
    source.value=select.value;
    // Redrawing replaces this select, so focus returns to its replacement.
    pendingFocus={title,kind};render();
  });
  return select;
}
function chartPanel(title, description, controls=['count']) {
  const panel=document.createElement('article');panel.className='chart';panel.dataset.title=title;
  const body=document.createElement('div');body.className='chart-body';
  const head=document.createElement('div');head.className='chart-head';
  // A disabled global select has nothing to choose, so the chart omits it.
  const selects=controls.filter(kind=>!controlSelects[kind].disabled).map(kind=>inlineSelect(kind,title));
  panel.append(head,body);target.append(panel);
  head.append(toggleHeading('h3',`chart:${title}`,title,body));
  if(selects.length) {
    const group=document.createElement('span');group.className='inline-controls';
    group.append(...selects);head.append(group);
  }
  const note=document.createElement('p');note.className='description';note.textContent=description;
  body.append(note);
  return {panel,body};
}
function chart({title, description, action, field, bytes=false, countUnit=false, pageLoad, memory=false, unrecorded,
  controls}) {
  const count=Number(countSelect.value);
  const memoryBytes=memory && bytes;
  const source=memory ? data.memory : bytes ? data.sizes : data.samples;
  const selected=source.filter(row=>row.count===count && row.action===action &&
    (pageLoad===undefined || row.page_load===pageLoad));
  const observations=(memory ? data.memory : data.samples).filter(row=>row.count===count && row.action===action &&
    (pageLoad===undefined || row.page_load===pageLoad));
  const invalidMemory=(data.memory_invalid_records||[]).filter(row=>row.count===count && row.action===action &&
    (pageLoad===undefined || row.page_load===pageLoad));
  const series=apps.map(app=>({app, values:selected.filter(row=>row.app===app && (memory || row.status==='ok') &&
    typeof row[field]==='number' && Number.isFinite(row[field])).map(row=>row[field]),
    trials:observations.filter(row=>row.app===app)}));
  const retainedBounds=memory ? selected.flatMap(row=>[row[field+'_min'],row[field+'_max']]
    .filter(value=>typeof value==='number')) : [];
  const signed=memory && field.includes('delta');
  const minimum=signed ? Math.min(0,...series.flatMap(row=>row.values),...retainedBounds)*1.12 : 0;
  const maximum=Math.max(0,...series.flatMap(row=>row.values),...retainedBounds)*1.12;
  const limit=maximum>minimum ? maximum : minimum+1;
  const position=value=>left+width*(value-minimum)/(limit-minimum);
  const left=180, width=360, step=54, layout=rowLayout(38,step), height=layout.height;
  const {body}=chartPanel(title,description,controls);
  const descriptionId=`chart-description-${document.querySelectorAll('#charts article').length}`;
  const loadContext=pageLoad===undefined ? '' : `, ${pageLoad===1 ? 'first load' : 'second load'}`;
  const svg=element('svg',{'aria-describedby':descriptionId,viewBox:`0 0 700 ${height}`,role:'img','aria-label':`${title}, ${countLabel(count)}, ${action}${loadContext}`});
  svg.append(element('title',{},`${title}, ${countLabel(count)}, ${action}${loadContext}`));
  const descriptions=[];
  for(let tick=0;tick<=4;tick++) {
    const x=left+width*tick/4;
    svg.append(element('line',{x1:x,x2:x,y1:23,y2:height-36,stroke:'#e0e7ef'}));
    const value=minimum+(limit-minimum)*tick/4;
    svg.append(element('text',{x,y:height-14,'text-anchor':'middle'},
      memoryBytes ? `${(value/(1024*1024)).toFixed(1)} MiB` :
      bytes ? (Math.max(Math.abs(minimum),Math.abs(limit))>=1024 ? `${(value/1024).toFixed(1)} KiB` : `${value.toFixed(1)} B`) :
        countUnit ? value.toFixed(1) : `${value.toFixed(1)} ms`));
  }
  drawHeadings(svg,layout.headings,left);
  series.forEach(({app,values,trials},index)=>{
    const y=layout.rows[index].y, color=palette[index%palette.length];
    svg.append(element('text',{x:left-12,y:y+4,'text-anchor':'end'},names[app]||app));
    const failed=memory ? invalidMemory.filter(row=>row.app===app).length :
      trials.filter(row=>!['ok','not-run'].includes(row.status)).length;
    const skipped=trials.filter(row=>row.status==='not-run').length;
    const successful=trials.filter(row=>row.status==='ok');
    const layoutEndpointMetric=['layout_inclusive_elapsed_ms','layout_extra_wait_ms'].includes(field);
    const unavailable=layoutEndpointMetric ? successful.length-values.length : 0;
    const availability=layoutEndpointMetric ? `; layout-endpoint-unavailable=${unavailable}` : '';
    // A row that never requested the reading (an older run, or not the
    // page's last observation) is labelled as such, not as a failure.
    const neverRecorded=unrecorded && trials.length && !trials.some(row=>row.browser_heap_after_gc_attempts>0);
    const measuredCount=memory ? trials.reduce((sum,row)=>sum+(row[field+'_observations']||0),0) : values.length;
    // An after-GC reading is requested only at some observations, so only
    // requested readings that failed count as unavailable.
    const expectedOf=row=>unrecorded ? (row.browser_heap_after_gc_attempts||0) : (row.successes||0);
    const unavailableCount=memory ? trials.reduce((sum,row)=>sum+Math.max(0,expectedOf(row)-(row[field+'_observations']||0)),0) : 0;
    const unrecordedCount=unrecorded ? trials.reduce((sum,row)=>sum+Math.max(0,(row.successes||0)-expectedOf(row)),0) : 0;
    const diagnostics=`N=${measuredCount}${memory ? `; unavailable=${unavailableCount}${unrecorded ? `; not recorded=${unrecordedCount}` : ''}` : availability}; failed=${failed}; skipped=${skipped}`;
    const rowLabel=`N=${measuredCount}`;
    const notApplicable=field==='server_render_ms' && trials.some(row=>row.server_render_status==='not-applicable');
    const layoutMissing=layoutEndpointMetric && successful.length && !values.length;
    const missing=neverRecorded ? unrecorded : notApplicable ? 'N/A: browser-rendered UI' : layoutMissing ?
      'Layout endpoint unavailable for legacy observations' :
      (trials.length ? 'No successful measurement' : 'No observations recorded');
    descriptions.push(`${names[app]||app}: ${values.length ? 'median '+format(median(values),bytes,countUnit,memoryBytes) : missing}; ${diagnostics}.`);
    const rowDetail=element('text',{x:left,y:y+27,fill:'#526275'},rowLabel);
    rowDetail.append(element('title',{},diagnostics));svg.append(rowDetail);
    if(!values.length) {
      svg.append(element('text',{x:left+8,y:y+4},missing));
      return;
    }
    const mid=median(values), zero=position(0), middle=position(mid);
    if(memory) {
      const lows=trials.map(row=>row[field+'_min']).filter(value=>typeof value==='number');
      const highs=trials.map(row=>row[field+'_max']).filter(value=>typeof value==='number');
      if(lows.length && highs.length) {
        const low=Math.min(...lows),high=Math.max(...highs),lowX=position(low),highX=position(high);
        svg.append(element('line',{x1:lowX,x2:highX,y1:y,y2:y,stroke:color,'stroke-width':2}));
        svg.append(element('text',{x:left,y:y+40,fill:'#526275'},`range ${format(low,bytes,countUnit,memoryBytes)}–${format(high,bytes,countUnit,memoryBytes)}`));
      }
    }
    svg.append(element('rect',{x:Math.min(zero,middle),y:y-10,width:Math.abs(middle-zero),height:20,fill:color,opacity:0.22}));
    svg.append(element('line',{x1:middle,x2:middle,y1:y-12,y2:y+12,stroke:color,'stroke-width':3}));
    if(!memory) values.forEach((value,i)=>{
        // A deterministic vertical offset separates repeated values without altering the x axis.
        const dot=element('circle',{cx:position(value),cy:y+(i%3-1)*4,r:3.5,fill:color,
          tabindex:0,'aria-label':`${names[app]||app}: ${format(value,bytes,countUnit,memoryBytes)}`});
        dot.append(element('title',{},`${names[app]||app}: ${format(value,bytes,countUnit,memoryBytes)}`));svg.append(dot);
      });
    svg.append(element('text',{x:left+width+12,y:y+4},format(mid,bytes,countUnit,memoryBytes)));
  });
  svg.append(element('desc',{id:descriptionId},descriptions.join(' ')));
  body.append(svg);
  const link=document.createElement('a');link.className='download';link.textContent='Download SVG';
  // Export the current filter selection as a standalone vector image.
  const exported=svg.cloneNode(true);exported.setAttribute('xmlns',ns);
  const style=element('style',{},'text{font:12px system-ui;fill:#26394c}text[font-weight="700"]{font-weight:700}');exported.prepend(style);
  const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(exported)],{type:'image/svg+xml'}));
  downloads.push(url);link.href=url;
  link.download=`${field}-${action}-${count}${pageLoad===undefined ? '' : `-load-${pageLoad}`}.svg`;
  body.append(link);
}
function readyEndpoint(row) {
  const value=typeof row.ready_elapsed_ms==='number' ? row.ready_elapsed_ms : row.elapsed_ms;
  return typeof value==='number' && Number.isFinite(value) && value>=0 ? value : null;
}
function layoutEndpointValue(row) {
  if(row.layout_endpoint!==layoutEndpointVersion) return null;
  const layout=row.layout_inclusive_elapsed_ms, ready=row.ready_elapsed_ms, extra=row.layout_extra_wait_ms;
  if([layout,ready,extra].some(value=>typeof value!=='number' || !Number.isFinite(value) || value<0)) return null;
  if(layout<ready || Math.abs(layout-(ready+extra))>1e-6) return null;
  return layout;
}
function phaseVector(row, layoutInclusive=false) {
  const ready=readyEndpoint(row);
  const layout=layoutInclusive ? layoutEndpointValue(row) : null;
  if(ready===null)
    return {segments:{},measured:false,reason:'requested timing endpoint unavailable'};
  const unavailable=(reason)=>({segments:{unclassified:ready,
    ...(layout!==null ? {layout_wait:row.layout_extra_wait_ms} : {})},measured:false,reason,
    layoutWaitAvailable:layout!==null});
  const phase=row.latency_phase;
  if(!phase || !Array.isArray(phase.segments)) return unavailable('phase evidence unavailable');
  const segments={};
  for(const segment of phase.segments) {
    if(!readyPhaseKeys.includes(segment.key) || typeof segment.ms!=='number' || !Number.isFinite(segment.ms) || segment.ms<0)
      return unavailable('invalid retained phase evidence');
    segments[segment.key]=(segments[segment.key]||0)+segment.ms;
  }
  const total=Object.values(segments).reduce((sum,value)=>sum+value,0);
  if(Math.abs(total-ready)>1e-6)
    return unavailable('phase evidence does not sum to ready-only time');
  if(layout!==null) segments.layout_wait=row.layout_extra_wait_ms;
  return {segments,measured:phase.status==='measured',reason:phase.reason,layoutWaitAvailable:layout!==null};
}
function representativePhase(rows, layoutInclusive=false) {
  const endpoint=layoutInclusive ? row=>layoutEndpointValue(row) ?? readyEndpoint(row) : readyEndpoint;
  const ordered=[...rows].sort((a,b)=>endpoint(a)-endpoint(b)), middle=Math.floor(ordered.length/2);
  const selected=ordered.length%2 ? [ordered[middle]] : [ordered[middle-1],ordered[middle]];
  const vectors=selected.map(row=>phaseVector(row,layoutInclusive)), segments={};
  for(const key of Object.keys(phasePalette)) if(vectors.some(vector=>key in vector.segments)) {
    if(key==='layout_wait' && vectors.some(vector=>!vector.layoutWaitAvailable)) continue;
    segments[key]=vectors.reduce((sum,vector)=>sum+(vector.segments[key]||0),0)/vectors.length;
  }
  return {total:median(ordered.map(endpoint)),segments};
}
// FCP and LCP are browser paint times since navigation start, the same zero
// as the initial stacks, so their medians sit directly on those axes.
// FCP sits below the bar and LCP above it, so equal values stay visible.
const paintMarkers={fcp_ms:{label:'FCP',fill:'#ffffff',side:1},lcp_ms:{label:'LCP',fill:'#172638',side:-1}};
const paintTriangle=(x,y,side)=>`M${x-4.5} ${y+side*18}L${x+4.5} ${y+side*18}L${x} ${y+side*11}Z`;
function paintValues(rows, field) {
  return rows.map(row=>row[field]).filter(value=>typeof value==='number' && Number.isFinite(value) && value>=0);
}
function paintNote(rows, field) {
  // Rows from runs before paint timing carry no status; they were never recorded.
  if(!rows.some(row=>row[field.replace('_ms','_status')]!=null)) return 'not recorded';
  const reasons=[...new Set(rows.map(row=>row[field.replace('_ms','_reason')]).filter(Boolean))];
  return reasons.length ? `unavailable: ${reasons.join('; ')}` : 'unavailable';
}
function phaseChart({title,description,action,pageLoad,layoutInclusive=false,controls}) {
  const count=Number(countSelect.value);
  const selected=data.samples.filter(row=>row.count===count && row.action===action &&
    (pageLoad===undefined || row.page_load===pageLoad));
  const series=apps.map(app=>{
    const trials=selected.filter(row=>row.app===app);
    const successfulReady=trials.filter(row=>row.status==='ok' && readyEndpoint(row)!==null);
    const successful=successfulReady;
    const useLayoutInclusive=layoutInclusive && successful.length>0 &&
      successful.every(row=>layoutEndpointValue(row)!==null);
    return {app,trials,successfulReady,successful,
      useLayoutInclusive,endpoint:useLayoutInclusive ? layoutEndpointValue : readyEndpoint,
      representative:successful.length ? representativePhase(successful,useLayoutInclusive) : null};
  });
  // Only initial loads have paint times, and runs before paint timing have no
  // status fields, so their charts stay exactly as they were.
  const showPaint=action==='initial' && selected.some(row=>row.fcp_status!=null || row.lcp_status!=null);
  const paintMedians=showPaint ? series.flatMap(({successful})=>Object.keys(paintMarkers)
    .map(field=>paintValues(successful,field)).filter(values=>values.length).map(median)) : [];
  const maximum=Math.max(0,...series.flatMap(row=>row.successful.map(row.endpoint)),...paintMedians);
  const limit=maximum>0 ? maximum*1.12 : 1;
  // The legend takes three rows; paint markers need room above the first bar.
  const left=180,width=360,top=showPaint ? 108 : 104,step=54,layout=rowLayout(top,step),height=layout.height;
  const {body}=chartPanel(title,description,controls);
  const descriptionId=`chart-description-${document.querySelectorAll('#charts article').length}`;
  const loadContext=pageLoad===undefined ? '' : `, ${pageLoad===1 ? 'first load' : 'second load'}`;
  const svg=element('svg',{'aria-describedby':descriptionId,viewBox:`0 0 700 ${height}`,role:'img',
    'aria-label':`${title}, ${countLabel(count)}, ${action}${loadContext}`});
  svg.append(element('title',{},`${title}, ${countLabel(count)}, ${action}${loadContext}`));
  const labels=action==='initial' ? {browser_before:'Before document request',server:'Main document server',
    exchange_residual:'Document exchange residual',response_receive:'Response receipt',
    browser_after:'Browser + subsequent requests',unclassified:'Unclassified',
    layout_wait:'Additional ready-to-layout wait'} :
    {browser_before:'Browser before exchange',server:'Application server',
      exchange_residual:'Exchange residual',response_receive:'Response receipt',
      browser_after:'Browser after response',unclassified:'Unclassified',
      layout_wait:'Additional ready-to-layout wait'};
  // Three legend columns across the whole chart keep the legend short.
  const legendX=index=>12+(index%3)*229, legendY=index=>12+Math.floor(index/3)*20;
  Object.keys(phasePalette).forEach((key,index)=>{
    const x=legendX(index),y=legendY(index);
    svg.append(element('rect',{x,y,width:11,height:11,fill:phasePalette[key]}));
    svg.append(element('text',{x:x+16,y:y+10},labels[key]));
  });
  if(showPaint) Object.values(paintMarkers).forEach((marker,index)=>{
    const position=Object.keys(phasePalette).length+index;
    const x=legendX(position),y=legendY(position);
    svg.append(element('path',{d:paintTriangle(x+5.5,y+5.5-marker.side*14.5,marker.side),fill:marker.fill,
      stroke:'#172638','stroke-width':1.5}));
    svg.append(element('text',{x:x+16,y:y+10},`${marker.label} median`));
  });
  for(let tick=0;tick<=4;tick++) {
    const x=left+width*tick/4;
    svg.append(element('line',{x1:x,x2:x,y1:top-15,y2:height-36,stroke:'#e0e7ef'}));
    svg.append(element('text',{x,y:height-14,'text-anchor':'middle'},`${(limit*tick/4).toFixed(1)} ms`));
  }
  drawHeadings(svg,layout.headings,left);
  const descriptions=[];
  series.forEach(({app,trials,successfulReady,successful,useLayoutInclusive,endpoint,representative},index)=>{
    const y=layout.rows[index].y;
    svg.append(element('text',{x:left-12,y:y+4,'text-anchor':'end'},names[app]||app));
    const vectors=successful.map(row=>phaseVector(row,useLayoutInclusive));
    const measured=vectors.filter(vector=>vector.measured).length;
    const unavailable=vectors.length-measured;
    const endpointUnavailable=layoutInclusive ? successfulReady.filter(row=>layoutEndpointValue(row)===null).length : 0;
    const failed=trials.filter(row=>!['ok','not-run'].includes(row.status)).length;
    const skipped=trials.filter(row=>row.status==='not-run').length;
    const detail=`N=${successful.length} · phases=${measured}${unavailable ? `/${successful.length}` : ''}`;
    const diagnostics=`N=${successful.length}; phases=${measured} measured/${unavailable} unavailable`+
      `${layoutInclusive ? `; layout-endpoint-unavailable=${endpointUnavailable}` : ''}; failed=${failed}; skipped=${skipped}`+
      `${layoutInclusive && endpointUnavailable ? `; additional wait unavailable=${endpointUnavailable}` : ''}`;
    const rowDetail=element('text',{x:left,y:y+27,fill:'#526275'},detail);
    rowDetail.append(element('title',{},diagnostics));svg.append(rowDetail);
    if(!representative) {
      const missing=layoutInclusive && endpointUnavailable ? 'Layout endpoint unavailable for legacy observations' :
        trials.length ? 'No successful measurement' : 'No observations recorded';
      svg.append(element('text',{x:left+8,y:y+4},missing));
      descriptions.push(`${names[app]||app}: ${missing}; ${diagnostics}.`);
      return;
    }
    let offset=0;
    const phaseDetails=[];
    for(const [key,color] of Object.entries(phasePalette)) {
      if(!(key in representative.segments)) continue;
      const value=representative.segments[key];
      const segment=element('rect',{x:left+width*offset/limit,y:y-10,width:width*value/limit,height:20,fill:color,
        tabindex:0,'aria-label':`${labels[key]}: ${format(value,false)}`});
      segment.append(element('title',{},`${labels[key]}: ${format(value,false)}`));svg.append(segment);
      phaseDetails.push(`${labels[key]} ${format(value,false)}`);
      offset+=value;
    }
    successful.forEach((row,i)=>{
      const value=endpoint(row);
      const dot=element('circle',{cx:left+width*value/limit,cy:y+(i%3-1)*4,r:3.2,fill:'#172638',
        tabindex:0,'aria-label':`${names[app]||app}: ${format(value,false)}`});
      dot.append(element('title',{},`${names[app]||app}: ${format(value,false)}`));svg.append(dot);
    });
    // The total is bold so it stays easy to find beside the paint times below it.
    svg.append(element('text',{x:left+width+12,y:y+4,'font-weight':'700'},format(representative.total,false)));
    const paintDetails=[],paintText=[];
    if(showPaint) for(const [field,marker] of Object.entries(paintMarkers)) {
      const values=paintValues(successful,field);
      if(!values.length) {
        paintDetails.push(`${marker.label} ${paintNote(successful,field)}`);
        paintText.push(`${marker.label} –`);
        continue;
      }
      const value=median(values),x=left+width*value/limit,label=`${marker.label} median ${format(value,false)} (N=${values.length})`;
      svg.append(element('line',{x1:x,x2:x,y1:y,y2:y+marker.side*11,stroke:'#172638','stroke-width':1.5}));
      const shape=element('path',{d:paintTriangle(x,y,marker.side),fill:marker.fill,
        stroke:'#172638','stroke-width':1.5,tabindex:0,'aria-label':`${names[app]||app}: ${label}`});
      shape.append(element('title',{},`${names[app]||app}: ${label}`));svg.append(shape);
      paintDetails.push(label);paintText.push(`${marker.label} ${value.toFixed(1)}`);
    }
    if(paintText.length) svg.append(element('text',{x:left+width+12,y:y+20,fill:'#526275'},paintText.join(' · ')));
    const reasons=[...new Set(vectors.filter(vector=>!vector.measured).map(vector=>vector.reason).filter(Boolean))];
    descriptions.push(`${names[app]||app}: representative segments sum to median ${format(representative.total,false)}: ${phaseDetails.join(', ')}; ${diagnostics}`+
      `${reasons.length ? `; unavailable: ${reasons.join('; ')}` : ''}${paintDetails.length ? `; ${paintDetails.join('; ')}` : ''}.`);
  });
  svg.append(element('desc',{id:descriptionId},descriptions.join(' ')));
  body.append(svg);
  const link=document.createElement('a');link.className='download';link.textContent='Download SVG';
  const exported=svg.cloneNode(true);exported.setAttribute('xmlns',ns);
  exported.prepend(element('style',{},'text{font:12px system-ui;fill:#26394c}text[font-weight="700"]{font-weight:700}'));
  const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(exported)],{type:'image/svg+xml'}));
  downloads.push(url);link.href=url;
  link.download=`latency-phases-${action}-${count}${pageLoad===undefined ? '' : `-load-${pageLoad}`}.svg`;
  body.append(link);
}
// The runner reads the heap after forced garbage collection only at a page's
// last observation, and older runs never read it, so its chart appears only
// for a selection where some row carries the reading.
function hasAfterGcHeap(action, load) {
  const count=Number(countSelect.value);
  return (data.memory||[]).some(row=>row.count===count && row.action===action &&
    (load===undefined || row.page_load===load) && (row.browser_heap_after_gc_attempts||0)>0);
}
const AFTER_GC_UNRECORDED='Not recorded for this app and action';
// Page-load memory charts follow the load-detail select; after-action
// charts follow the action select. DOM counts are not memory, so they get
// their own section.
function renderMemoryCharts(action, load) {
    const loadControls=['count','load'], actionControls=['count','action'];
    beginSection('Memory at page load');
    chart({title:'Server RSS at readiness',description:'Resident bytes for the pinned server process tree, sampled after the common endpoint.',action:'initial',field:'server_rss_bytes',bytes:true,pageLoad:load,memory:true,controls:loadControls});
    chart({title:'Server RSS growth from idle',description:'Resident-byte change from the pinned idle-server baseline; negative values remain in the retained data.',action:'initial',field:'server_rss_idle_delta',bytes:true,pageLoad:load,memory:true,controls:loadControls});
    // macOS refuses the USS read for the server process, so the chart appears
    // only when some row in the whole report carries a reading.
    if((data.memory||[]).some(row=>typeof row.server_uss_bytes==='number'))
      chart({title:'Server USS at readiness',description:'Private bytes for the pinned server process tree, sampled after the common endpoint.',action:'initial',field:'server_uss_bytes',bytes:true,pageLoad:load,memory:true,controls:loadControls});
    chart({title:'Server sampled peak RSS',description:'Maximum complete server RSS sample through the common endpoint.',action:'initial',field:'server_sampled_peak_rss_bytes',bytes:true,pageLoad:load,memory:true,controls:loadControls});
    chart({title:'Browser RSS at readiness',description:'Resident bytes for the dedicated CDP browser process and verified descendants, sampled after the common endpoint.',action:'initial',field:'browser_rss_bytes',bytes:true,pageLoad:load,memory:true,controls:loadControls});
    chart({title:'Browser RSS growth from blank',description:'Resident-byte change from the dedicated blank-browser baseline.',action:'initial',field:'browser_rss_blank_delta',bytes:true,pageLoad:load,memory:true,controls:loadControls});
    chart({title:'JavaScript heap at readiness',description:'Used V8 heap for the measured page, sampled after the common endpoint without forcing garbage collection.',action:'initial',field:'browser_heap_used_bytes',bytes:true,pageLoad:load,memory:true,controls:loadControls});
    chart({title:'JavaScript heap growth from blank',description:'Used-heap byte change from the blank-page baseline.',action:'initial',field:'browser_heap_blank_delta',bytes:true,pageLoad:load,memory:true,controls:loadControls});
    if(hasAfterGcHeap('initial', load)) chart({title:'JavaScript heap after GC at readiness',description:'Used V8 heap for the measured page after the runner forces garbage collection twice, read after every other reading. It shows what the page retains. The runner reads it only at the last observation of a page load, so only a page load without actions has it here.',action:'initial',field:'browser_heap_after_gc_used_bytes',bytes:true,pageLoad:load,memory:true,unrecorded:AFTER_GC_UNRECORDED,controls:loadControls});
    if(action) {
      beginSection('Memory after a server action');
      chart({title:'Server RSS after action',description:`${action}: resident server process-tree bytes sampled after the common endpoint.`,action,field:'server_rss_bytes',bytes:true,memory:true,controls:actionControls});
      chart({title:'Server sampled peak RSS during action',description:`${action}: maximum complete server RSS sample through the common endpoint.`,action,field:'server_sampled_peak_rss_bytes',bytes:true,memory:true,controls:actionControls});
      chart({title:'Browser RSS after action',description:`${action}: dedicated browser resident bytes sampled after the common endpoint.`,action,field:'browser_rss_bytes',bytes:true,memory:true,controls:actionControls});
      chart({title:'JavaScript heap after action',description:`${action}: used page V8 heap sampled after the common endpoint without forcing garbage collection.`,action,field:'browser_heap_used_bytes',bytes:true,memory:true,controls:actionControls});
      if(hasAfterGcHeap(action)) chart({title:'JavaScript heap after GC, after action',description:`${action}: used page V8 heap after the runner forces garbage collection twice, read after every other reading. The runner reads it only at the last action of a page load.`,action,field:'browser_heap_after_gc_used_bytes',bytes:true,memory:true,unrecorded:AFTER_GC_UNRECORDED,controls:actionControls});
    }
    beginSection('DOM size at page load');
    chart({title:'DOM nodes at readiness',description:'Page DOM node count after the common endpoint; this is an explanatory count, not bytes.',action:'initial',field:'dom_nodes',countUnit:true,pageLoad:load,memory:true,controls:loadControls});
    chart({title:'Event listeners at readiness',description:'Page event-listener count reported by CDP after the common endpoint.',action:'initial',field:'dom_listeners',countUnit:true,pageLoad:load,memory:true,controls:loadControls});
}
function renderCharts() {
  const action=actionSelect.value;
  const detailLoad=Number(pageLoadSelect.value || 1);
  if(data.run.kind==='memory') {
    renderMemoryCharts(action, detailLoad);
    return;
  }
  const loadName=detailLoad===1 ? 'first' : 'second';
  const loadDescription='Each load uses a fresh browser context and scenario session on the same server process.'+
    (data.samples.some(row=>row.action==='initial' && (row.fcp_status!=null || row.lcp_status!=null)) ?
      ' Triangles mark median first contentful paint (FCP, below the bar) and largest contentful paint (LCP, above it); all times start at navigation.' : '');
  // Timings: page loads first, then the server action.
  beginSection('Timings');
  phaseChart({title:'First-load time to interactive',description:`Load 1. ${loadDescription}`,action:'initial',pageLoad:1,layoutInclusive:true,controls:['count']});
  if(pageLoads.includes(2)) phaseChart({title:'Second-load time to interactive',description:`Load 2. ${loadDescription}`,action:'initial',pageLoad:2,layoutInclusive:true,controls:['count']});
  if(action) {
    phaseChart({title:'Server-action latency',description:`${action}: browser time around the correlated exchange, measured application-server work, response receipt where available, and exchange residual.`,action,layoutInclusive:true,controls:['count','action']});
  }
  beginSection('Sizes');
  chart({title:'Initial response payload',description:`All HTTP response bodies and socket bootstrap messages for the selected ${loadName} load.`,action:'initial',field:'encoded_response_body_bytes',bytes:true,pageLoad:detailLoad,controls:['count','load']});
  chart({title:'Initial final HTML size',description:`Serialized document after the selected ${loadName} load reaches the common endpoint.`,action:'initial',field:'final_html_bytes',bytes:true,pageLoad:detailLoad,controls:['count','load']});
  chart({title:'Action request size',description:`${action}: outgoing HTTP bodies or socket messages.`,action,field:'request_body_bytes',bytes:true,controls:['count','action']});
  chart({title:'Action response size',description:`${action}: incoming HTTP bodies or socket messages.`,action,field:'encoded_response_body_bytes',bytes:true,controls:['count','action']});
  chart({title:'Updated final HTML size',description:`Serialized document after ${action} reaches the common endpoint.`,action,field:'final_html_bytes',bytes:true,controls:['count','action']});
  if(data.memory_run || (data.memory||[]).length || data.memory_invalid_observations)
    renderMemoryCharts(action, detailLoad);
}
function render() {
  for(const url of downloads) URL.revokeObjectURL(url);
  downloads=[];document.getElementById('charts').replaceChildren();
  target=document.getElementById('charts');
  renderCharts();
  if(pendingFocus) {
    const {title,kind}=pendingFocus;pendingFocus=null;
    [...document.querySelectorAll('#charts article.chart')].find(panel=>panel.dataset.title===title)
      ?.querySelector(`select[data-control="${kind}"]`)?.focus();
  }
}
countSelect.addEventListener('change',render);actionSelect.addEventListener('change',render);
pageLoadSelect.addEventListener('change',render);render();
