(function(){
  'use strict';
  function __showErr(msg){try{var d=document.getElementById('__err__');if(!d){d=document.createElement('div');d.id='__err__';d.className='radar-fatal';document.body.appendChild(d);}d.textContent='Radar error — please screenshot:\n'+msg;}catch(_){}}
  window.addEventListener('error',function(e){__showErr((e.message||'')+'  @'+(e.lineno||0)+':'+(e.colno||0));});
  window.addEventListener('unhandledrejection',function(e){__showErr('promise: '+((e.reason&&e.reason.message)||e.reason));});

  var CATS=[{n:'Hardware & Acquisition',c:'#2dd4ff'},{n:'Signal Processing',c:'#38bdf8'},{n:'Decoding & ML',c:'#a78bfa'},
    {n:'Privacy & Security',c:'#fb7185'},{n:'Real-time & Embedded',c:'#34d399'},{n:'Protocols & OS',c:'#fbbf24'},{n:'Other',c:'#94a3b8'}];
  var NS=6;
  function catColor(n){for(var i=0;i<CATS.length;i++)if(CATS[i].n===n)return CATS[i].c;return '#94a3b8';}
  function catIndex(n){for(var i=0;i<CATS.length;i++)if(CATS[i].n===n)return i;return CATS.length-1;}
  function $(id){return document.getElementById(id);}
  function hash(s){var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=(h*16777619)>>>0;}return h;}
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function safeUrl(u){u=String(u||'');return /^https:\/\/github\.com\//.test(u)?u:'#';}
  function fmtAge(d){if(d==null||d>=9000)return '—';if(d<=0)return 'today';if(d<7)return d+'d';if(d<60)return Math.round(d/7)+'w';if(d<730)return Math.round(d/30)+'mo';return Math.round(d/365)+'y';}

  var DATA={projects:[],generated_at:null,counts:{total:0,active_30d:0,new:0}};
  // Ingress validation (defense-in-depth): if radar.json is ever compromised,
  // every field the UI touches is coerced to its expected type and URLs pass
  // the github.com allowlist BEFORE any rendering. esc() remains the second wall.
  function str(v,max){v=(v==null?'':String(v));return v.length>max?v.slice(0,max):v;}
  function num(v){v=Number(v);return isFinite(v)?v:0;}
  function sanitizeProject(p){
    if(!p||typeof p!=='object')return null;
    var q=p.quality_flags&&typeof p.quality_flags==='object'?p.quality_flags:{};
    return {full_name:str(p.full_name,140),html_url:safeUrl(p.html_url),
      description:str(p.description,300),category:str(p.category,60)||'Other',
      language:str(p.language,40),stars:num(p.stars),forks:num(p.forks),
      days_since_push:num(p.days_since_push),active:!!p.active,is_new:!!p.is_new,
      rising:!!p.rising,falling:!!p.falling,stars_delta_7d:num(p.stars_delta_7d),
      evidence_tier:str(p.evidence_tier,40),inclusion_reason:str(p.inclusion_reason,200),
      topics:(Array.isArray(p.topics)?p.topics:[]).slice(0,12).map(function(t){return str(t,50);}),
      license:str(p.license,40),has_license:!!p.has_license,
      quality_flags:{possible_false_positive:!!q.possible_false_positive},
      first_seen:str(p.first_seen,40)};
  }
  function sanitizeBuilder(b){
    if(!b||typeof b!=='object')return null;
    return {owner:str(b.owner,80),html_url:safeUrl(b.html_url),
      project_count:num(b.project_count),total_stars:num(b.total_stars),
      active_projects_30d:num(b.active_projects_30d),
      top_categories:(Array.isArray(b.top_categories)?b.top_categories:[]).slice(0,4).map(function(t){return str(t,60);}),
      owner_type:str(b.owner_type,20),followers:num(b.followers)};
  }
  function sanitizeData(j){
    if(!j||typeof j!=='object')return DATA;
    var ps=(Array.isArray(j.projects)?j.projects:[]).map(sanitizeProject).filter(Boolean);
    var bs=(Array.isArray(j.builders)?j.builders:[]).map(sanitizeBuilder).filter(Boolean);
    return {projects:ps,builders:bs,generated_at:str(j.generated_at,40)||null,
      counts:(j.counts&&typeof j.counts==='object')?j.counts:{total:ps.length}};
  }
  var state={q:'',cats:{},lang:'',activeOnly:false,newOnly:false,fallingOnly:false,tiers:{},dens:false,sort:'activity',view:'grid'};
  var points=[];

  function filtered(){
    var q=state.q.toLowerCase(),anyCat=Object.keys(state.cats).some(function(k){return state.cats[k];});
    var anyTier=Object.keys(state.tiers).some(function(k){return state.tiers[k];});
    var arr=DATA.projects.filter(function(p){
      if(state.activeOnly&&!p.active)return false;
      if(state.newOnly&&!p.is_new)return false;
      if(state.fallingOnly&&!p.falling)return false;
      if(anyTier&&!state.tiers[p.evidence_tier])return false;
      if(anyCat&&!state.cats[p.category])return false;
      if(state.lang&&(p.language||'')!==state.lang)return false;
      if(q){var hay=(p.full_name+' '+(p.description||'')+' '+(p.language||'')+' '+(p.topics||[]).join(' ')).toLowerCase();if(hay.indexOf(q)<0)return false;}
      return true;
    });
    arr.sort(state.sort==='stars'?function(a,b){return (b.stars||0)-(a.stars||0);}
      :state.sort==='rising'?function(a,b){return ((b.stars_delta_7d||0)-(a.stars_delta_7d||0))||((b.stars||0)-(a.stars||0));}
      :state.sort==='new'?function(a,b){return String(b.first_seen||'').localeCompare(String(a.first_seen||''));}
      :state.sort==='name'?function(a,b){return a.full_name.toLowerCase().localeCompare(b.full_name.toLowerCase());}
      :function(a,b){return (a.days_since_push||9999)-(b.days_since_push||9999);});
    return arr;
  }

  // ── radar ──
  var cv=$('radar'),ctx=cv.getContext('2d'),DPR=1,S=460;
  function layout(){var rect=cv.getBoundingClientRect();S=Math.round(rect.width)||((cv.parentNode.clientWidth||356)-44);if(!S||S<200)S=Math.max(200,((cv.parentNode.clientWidth||356)-44));DPR=Math.min(2,window.devicePixelRatio||1);cv.width=Math.round(S*DPR);cv.height=Math.round(S*DPR);ctx.setTransform(DPR,0,0,DPR,0,0);}
  function tierFrac(d){if(d==null||d>=9000)return .88;if(d<=7)return .22;if(d<=30)return .46;if(d<=90)return .68;return .85;}
  function drawRadar(arr){
    if(state.view!=='radar')return;
    layout();var cx=S/2,cy=S/2,R=S/2-12;ctx.clearRect(0,0,S,S);
    for(var s=0;s<NS;s++){var a0=(s/NS)*6.283-Math.PI/2,a1=((s+1)/NS)*6.283-Math.PI/2;
      ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,R,a0,a1);ctx.closePath();ctx.fillStyle=CATS[s].c;ctx.globalAlpha=.08;ctx.fill();ctx.globalAlpha=1;
      ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+Math.cos(a0)*R,cy+Math.sin(a0)*R);ctx.strokeStyle='rgba(160,180,220,.1)';ctx.lineWidth=1;ctx.stroke();}
    ctx.beginPath();ctx.arc(cx,cy,R,0,6.283);ctx.strokeStyle='rgba(170,190,230,.2)';ctx.lineWidth=1.5;ctx.stroke();
    var rings=[{f:.22,l:'7d'},{f:.46,l:'30d'},{f:.68,l:'90d'}];
    for(var r=0;r<rings.length;r++){var rr=R*rings[r].f;ctx.beginPath();ctx.arc(cx,cy,rr,0,6.283);ctx.strokeStyle='rgba(170,190,230,'+(.18-r*.03)+')';ctx.lineWidth=1;ctx.stroke();
      var ly=cy-rr;ctx.fillStyle='rgba(6,7,11,.82)';ctx.fillRect(cx-15,ly-7.5,30,15);ctx.fillStyle='rgba(214,223,242,.9)';ctx.font='600 10px ui-monospace,monospace';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(rings[r].l,cx,ly);}
    ctx.beginPath();ctx.arc(cx,cy,4.5,0,6.283);ctx.fillStyle='#fff';ctx.shadowColor='#2dd4ff';ctx.shadowBlur=14;ctx.fill();ctx.shadowBlur=0;
    points=[];
    for(var i=0;i<arr.length;i++){var p=arr[i];var si=catIndex(p.category);if(si>=NS)si=hash(p.full_name)%NS;
      var h=hash(p.full_name);
      var ang=((si+0.5)/NS)*6.283-Math.PI/2+((h%50)-25)/25*(6.283/NS)*0.40;
      var fr=Math.min(.96,tierFrac(p.days_since_push)*(0.94+((h>>6)%12)/100));
      var x=cx+Math.cos(ang)*R*fr,y=cy+Math.sin(ang)*R*fr;
      var rad=4.5+Math.min(11,Math.log((p.stars||0)+1)/Math.LN10*2.6),col=CATS[si].c;
      ctx.shadowColor=col;ctx.shadowBlur=p.active?15:6;
      ctx.beginPath();ctx.arc(x,y,rad,0,6.283);ctx.fillStyle=col;ctx.globalAlpha=p.active?1:.5;ctx.fill();ctx.globalAlpha=1;ctx.shadowBlur=0;
      ctx.beginPath();ctx.arc(x,y,rad,0,6.283);ctx.strokeStyle='rgba(255,255,255,.55)';ctx.lineWidth=1;ctx.stroke();
      if(p.is_new){ctx.beginPath();ctx.arc(x,y,rad+4,0,6.283);ctx.strokeStyle='#fde68a';ctx.globalAlpha=.9;ctx.lineWidth=1.5;ctx.stroke();ctx.globalAlpha=1;}
      points.push({x:x,y:y,r:rad+6,p:p});
    }
    var cats={};arr.forEach(function(p){cats[p.category]=1;});var nw=arr.filter(function(p){return p.is_new;}).length;
    var alt='Radar showing '+arr.length+' projects across '+Object.keys(cats).length+' categories'+(nw?', '+nw+' new':'')+'.';
    var ra=$('radar-alt');if(ra)ra.textContent=alt;cv.setAttribute('aria-label',alt);
  }
  function showTip(pt,mx,my){var t=$('tip');if(!t)return;var p=pt.p;
    t.textContent='';var b=document.createElement('b');b.textContent=p.full_name+(p.is_new?' \u2726':'');
    var m=document.createElement('span');m.className='m';
    m.textContent='\u2b50 '+(p.stars||0)+' \u00b7 '+(p.language||'n/a')+' \u00b7 '+p.category+' \u00b7 '+fmtAge(p.days_since_push);
    t.appendChild(b);t.appendChild(document.createElement('br'));t.appendChild(m);
    t.style.left=Math.min(mx+12,cv.clientWidth-220)+'px';t.style.top=Math.max(0,my-10)+'px';t.style.opacity=1;}
  cv.addEventListener('pointermove',function(e){var r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,best=null,bd=1e9;for(var i=0;i<points.length;i++){var dx=mx-points[i].x,dy=my-points[i].y,d=dx*dx+dy*dy;if(d<points[i].r*points[i].r&&d<bd){bd=d;best=points[i];}}if(best){showTip(best,mx,my);cv.style.cursor='pointer';}else{var tp=$('tip');if(tp)tp.style.opacity=0;cv.style.cursor='default';}});
  cv.addEventListener('pointerleave',function(){var tp=$('tip');if(tp)tp.style.opacity=0;});
  cv.addEventListener('click',function(e){var r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top;for(var i=0;i<points.length;i++){var dx=mx-points[i].x,dy=my-points[i].y;if(dx*dx+dy*dy<points[i].r*points[i].r){var u=safeUrl(points[i].p.html_url);if(u!=='#')window.open(u,'_blank','noopener');return;}}});

  var GENERIC={rust:1,python:1,c:1,'c-plus-plus':1,cpp:1,javascript:1,typescript:1,go:1,'no-std':1};
  function tagRow(p){var t=(p.topics||[]).filter(function(x){return !GENERIC[String(x).toLowerCase()];}).slice(0,3);
    return t.length?'<div class="tags">'+t.map(function(x){return '<span class="tag">'+esc(x)+'</span>';}).join('')+'</div>':'';}
  var TIER={L3_EXPLICIT_BCI:['L3','tl3'],L2_NEURAL_SIGNAL:['L2','tl2'],L1_CONTEXT_PLUS_NEURO:['L1','tl1'],L0_WEAK_ADJACENT:['L0','tl0']};
  function evBadge(p){var t=p.evidence_tier;if(!t)return '';var e=TIER[t]||['\u2022','tl0'];
    return '<span class="ev '+e[1]+'" title="'+esc(p.inclusion_reason||t)+'">'+e[0]+'</span>';}
  function flagBadge(p){var q=p.quality_flags||{};var hit=Array.isArray(q)?q.indexOf('possible_false_positive')>=0:!!q.possible_false_positive;return hit?'<span class="flag" title="Borderline match \u2014 flagged for review">\u26A0 review</span>':'';}
  function el(tag,cls,txt){var e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;}
  function tagRowEl(p){var t=(p.topics||[]).filter(function(x){return !GENERIC[String(x).toLowerCase()];}).slice(0,3);
    if(!t.length)return null;var d=el('div','tags');t.forEach(function(x){d.appendChild(el('span','tag',x));});return d;}
  function evBadgeEl(p){var t=p.evidence_tier;if(!t)return null;var e=TIER[t]||['\u2022','tl0'];
    var sp=el('span','ev '+e[1],e[0]);sp.title=p.inclusion_reason||t;return sp;}
  function flagBadgeEl(p){var q=p.quality_flags||{};var hit=Array.isArray(q)?q.indexOf('possible_false_positive')>=0:!!q.possible_false_positive;
    if(!hit)return null;var sp=el('span','flag','\u26A0 review');sp.title='Borderline match \u2014 flagged for review';return sp;}
  function renderCards(arr){
    var l=$('cards');l.textContent='';
    if(!arr.length){
      var em=el('div','empty');em.appendChild(el('div','big',DATA.generated_at?'No matches':'Radar warming up'));
      if(!DATA.generated_at){em.appendChild(document.createTextNode('The first scan runs on publish and refreshes every 3 hours. Real projects appear here shortly.'));}
      else if(anyFilter()){em.appendChild(document.createTextNode('Nothing matches these filters \u2014 '));
        var bb=el('button','lnkbtn','clear all');bb.type='button';bb.addEventListener('click',clearFilters);em.appendChild(bb);em.appendChild(document.createTextNode('.'));}
      else{em.appendChild(document.createTextNode('No projects yet.'));}
      l.appendChild(em);return;}
    for(var i=0;i<arr.length;i++){(function(p){
      var col=catColor(p.category);
      var a=el('a','pc');a.href=safeUrl(p.html_url);a.target='_blank';a.rel='noopener';a.style.setProperty('--cc',col);
      var top=el('div','top');top.appendChild(el('span','pill',p.category));
      var ev=evBadgeEl(p);if(ev)top.appendChild(ev);
      var fl=flagBadgeEl(p);if(fl)top.appendChild(fl);
      if(p.rising){top.appendChild(el('span','rise','\u2191 '+(p.stars_delta_7d>0?('+'+p.stars_delta_7d+'/7d'):'rising')));}
      else if(p.falling){top.appendChild(el('span','fallb','\u2193 '+p.stars_delta_7d+'/7d'));}
      else if(p.is_new){top.appendChild(el('span','nb','NEW'));}
      if(!p.license){var lic=el('span','lic','\u26A0 no licence');lic.title='No licence detected \u2014 reuse rights unclear';top.appendChild(lic);}
      else if(p.license==='NOASSERTION'){var lu=el('span','lic','\u26A0 licence unclear');lu.title='GitHub cannot classify this licence (NOASSERTION)';top.appendChild(lu);}
      top.appendChild(el('span','st','\u2605 '+(p.stars||0)));
      a.appendChild(top);
      a.appendChild(el('h3',null,p.full_name));
      a.appendChild(el('p','desc',p.description||'\u2014'));
      var tr=tagRowEl(p);if(tr)a.appendChild(tr);
      var foot=el('div','foot');
      var lng=el('span','lng');lng.appendChild(el('span','ld'));lng.appendChild(document.createTextNode(p.language||'n/a'));foot.appendChild(lng);
      var ac=el('span','ac');ac.appendChild(el('span','ad'+(p.active?' on':'')));ac.appendChild(document.createTextNode(fmtAge(p.days_since_push)));foot.appendChild(ac);
      a.appendChild(foot);
      l.appendChild(a);
    })(arr[i]);}
  }

  function anyFilter(){return !!(state.q||state.lang||state.activeOnly||state.newOnly||Object.keys(state.cats).some(function(k){return state.cats[k];}));}
  function clearFilters(){state.q='';state.lang='';state.activeOnly=false;state.newOnly=false;state.fallingOnly=false;state.cats={};state.tiers={};
    var se=$('search');if(se)se.value='';var ls=$('langSel');if(ls)ls.value='';
    ['tAct','tNew','tFall'].forEach(function(id){var t=$(id);if(t){t.classList.remove('on');t.setAttribute('aria-pressed','false');}});
    buildChips();buildTierChips();render();}
  function readHash(){try{var h=(location.hash||'').replace(/^#/,'');if(!h)return;var p={};h.split('&').forEach(function(kv){var i=kv.indexOf('=');if(i>0)p[kv.slice(0,i)]=decodeURIComponent(kv.slice(i+1).replace(/\+/g,' '));});
    if(p.view==='radar'||p.view==='grid')state.view=p.view;
    if(['activity','stars','rising','new','name'].indexOf(p.sort)>=0)state.sort=p.sort;
    if(p.lang)state.lang=p.lang; if(p.q)state.q=p.q;
    state.activeOnly=p.active==='1'; state.newOnly=p.new==='1'; state.fallingOnly=p.fall==='1'; state.dens=p.d==='1';
    if(p.cat)p.cat.split(',').forEach(function(c){if(c)state.cats[c]=true;});
    if(p.tier)p.tier.split(',').forEach(function(t){if(t)state.tiers[t]=true;});}catch(e){}}
  function writeHash(){try{var p=[];
    if(state.view!=='grid')p.push('view='+state.view);
    if(state.sort!=='activity')p.push('sort='+state.sort);
    if(state.lang)p.push('lang='+encodeURIComponent(state.lang));
    if(state.q)p.push('q='+encodeURIComponent(state.q));
    if(state.activeOnly)p.push('active=1'); if(state.newOnly)p.push('new=1'); if(state.fallingOnly)p.push('fall=1'); if(state.dens)p.push('d=1');
    var on=Object.keys(state.cats).filter(function(k){return state.cats[k];});
    if(on.length)p.push('cat='+on.map(encodeURIComponent).join(','));
    var tn=Object.keys(state.tiers).filter(function(k){return state.tiers[k];});
    if(tn.length)p.push('tier='+tn.map(encodeURIComponent).join(','));
    if(window.history&&history.replaceState)history.replaceState(null,'',p.length?'#'+p.join('&'):location.pathname+location.search);}catch(e){}}
  function reflect(){var se=$('search');if(se)se.value=state.q;var ls=$('langSel');if(ls)ls.value=state.lang;
    [['tAct',state.activeOnly],['tNew',state.newOnly],['tFall',state.fallingOnly]].forEach(function(x){var t=$(x[0]);if(t){t.classList.toggle('on',x[1]);t.setAttribute('aria-pressed',String(x[1]));}});
    document.body.classList.toggle('compact',state.dens);
    var db=$('densBtn');if(db)db.setAttribute('aria-pressed',String(state.dens));
    buildTierChips();}
  function render(){
    var arr=filtered();
    $('radarSec').classList.toggle('hidden',state.view!=='radar');
    $('cards').classList.toggle('hidden',false);
    drawRadar(arr);renderCards(arr);
    $('gcount').textContent='Showing '+arr.length+' of '+DATA.projects.length+' projects';
    var cb=$('clearBtn');if(cb)cb.classList.toggle('hidden',!anyFilter());
    writeHash();
  }

  // ── Apple-style segmented controls (built in JS → testable + reliable) ──
  function buildSeg(id,opts,get,set){var c=$(id);if(!c)return;c.textContent='';var btns=[];
    opts.forEach(function(o){var b=document.createElement('button');b.className='seg-opt'+(o.v===get()?' on':'');b.textContent=o.l;
      b.setAttribute('role','tab');b.setAttribute('tabindex','0');b.setAttribute('aria-selected',String(o.v===get()));
      b.addEventListener('click',function(){set(o.v);btns.forEach(function(x){x.classList.remove('on');x.setAttribute('aria-selected','false');});b.classList.add('on');b.setAttribute('aria-selected','true');render();});
      btns.push(b);c.appendChild(b);});}

  function buildChips(){var c=$('chips');if(!c)return;c.textContent='';
    var counts={};DATA.projects.forEach(function(p){counts[p.category]=(counts[p.category]||0)+1;});
    CATS.forEach(function(cat){if(cat.n==='Other')return;var on=!!state.cats[cat.n],nn=counts[cat.n]||0;
    var el=document.createElement('div');el.className='chip'+(on?' on':'');el.setAttribute('role','button');el.setAttribute('tabindex','0');el.setAttribute('aria-pressed',String(on));
    el.style.setProperty('--cc',cat.c);
    var dt=document.createElement('span');dt.className='dot';el.appendChild(dt);el.appendChild(document.createTextNode(cat.n));
    if(nn){var cn=document.createElement('span');cn.className='cnt';cn.textContent=String(nn);el.appendChild(document.createTextNode(' '));el.appendChild(cn);}
    el.addEventListener('click',function(){state.cats[cat.n]=!state.cats[cat.n];el.classList.toggle('on',state.cats[cat.n]);el.setAttribute('aria-pressed',String(!!state.cats[cat.n]));render();});
    c.appendChild(el);});}
  var TIER_ORDER=['L3_EXPLICIT_BCI','L2_NEURAL_SIGNAL','L1_CONTEXT_PLUS_NEURO','L0_WEAK_ADJACENT'];
  function buildTierChips(){var c=$('tierChips');if(!c)return;c.textContent='';
    var counts={};DATA.projects.forEach(function(p){var t=p.evidence_tier;if(t)counts[t]=(counts[t]||0)+1;});
    TIER_ORDER.forEach(function(t){var lab=(TIER[t]||['?'])[0],on=!!state.tiers[t],nn=counts[t]||0;
      var el=document.createElement('div');el.className='chip'+(on?' on':'');el.setAttribute('role','button');el.setAttribute('tabindex','0');el.setAttribute('aria-pressed',String(on));
      el.appendChild(document.createTextNode(lab));
      if(nn){var cn=document.createElement('span');cn.className='cnt';cn.textContent=String(nn);el.appendChild(document.createTextNode(' '));el.appendChild(cn);}
      el.title=(TIER[t]?({L3_EXPLICIT_BCI:'Explicit BCI focus',L2_NEURAL_SIGNAL:'Neural-signal tooling',L1_CONTEXT_PLUS_NEURO:'Neuro context',L0_WEAK_ADJACENT:'Weak adjacency (review)'})[t]:'');
      el.addEventListener('click',function(){state.tiers[t]=!state.tiers[t];el.classList.toggle('on',state.tiers[t]);el.setAttribute('aria-pressed',String(!!state.tiers[t]));render();});
      c.appendChild(el);});}
  function buildLegend(){var l=$('legend');if(!l)return;l.textContent='';CATS.forEach(function(cat){if(cat.n==='Other')return;var s=document.createElement('span');s.style.setProperty('--cc',cat.c);var d=document.createElement('span');d.className='dot';s.appendChild(d);s.appendChild(document.createTextNode(cat.n));l.appendChild(s);});var n=document.createElement('span');n.className='leg-note';n.textContent='\u00b7 inner = recent \u00b7 size = stars \u00b7 \u2726 new';l.appendChild(n);}
  function buildLangs(){var sel=$('langSel');if(!sel)return;var langs={};DATA.projects.forEach(function(p){if(p.language)langs[p.language]=(langs[p.language]||0)+1;});
    var arr=Object.keys(langs).sort(function(a,b){return langs[b]-langs[a];});
    sel.textContent='';var o0=document.createElement('option');o0.value='';o0.textContent='All languages';sel.appendChild(o0);
    arr.forEach(function(L){var o=document.createElement('option');o.value=L;o.textContent=L+' ('+langs[L]+')';sel.appendChild(o);});
    sel.value=state.lang;}

  function setStats(){
    var c=DATA.counts||{},tot=c.total||DATA.projects.length,act=c.active_30d||0,nw=c.new||0;
    var stars=DATA.projects.reduce(function(s,p){return s+(p.stars||0);},0),cats={};DATA.projects.forEach(function(p){cats[p.category]=1;});
    function k(n){return n>=1000?(n/1000).toFixed(n>=10000?0:1)+'k':String(n);}
    var st=$('stats');st.textContent='';
    [['a',tot,'PROJECTS'],['n',nw,'NEW THIS WEEK'],['s',k(stars),'TOTAL STARS'],['c',act,'ACTIVE 30D']].forEach(function(x){
      var d=document.createElement('div');d.className='stat '+x[0];
      var b=document.createElement('b');b.textContent=String(x[1]);d.appendChild(b);
      var sp=document.createElement('span');sp.textContent=x[2];d.appendChild(sp);st.appendChild(d);});
    var u=$('updated');u.textContent='';
    if(DATA.generated_at){var d2=new Date(DATA.generated_at);
      u.appendChild(document.createTextNode('Updated '+d2.toUTCString().replace('GMT','UTC')+' \u00b7 refreshes every 3h \u00b7 '));
      var ra=document.createElement('a');ra.href='./feed.xml';ra.textContent='RSS';u.appendChild(ra);}
    else u.textContent='Warming up \u2014 first scan runs on publish \u00b7 refreshes every 3h';
  }

  function dpEl(d){var sp=document.createElement('span');
    sp.className='dp '+(d>0?'up':(d<0?'down':'flat'));
    sp.textContent=d>0?('+'+d):(d<0?('\u2212'+Math.abs(d)):'\u00b10');return sp;}
  function renderWeekly(w){
    var host=$('weekly');if(!host||!w||!w.delta)return;
    host.textContent='';
    host.appendChild((function(){var t=document.createElement('span');t.className='wk-t';t.textContent='This week';return t;})());
    [['Projects','total'],['Stars','total_stars'],['Active','active_30d'],['Rising','rising']].forEach(function(x){
      var d=document.createElement('span');d.className='wk-d';
      var b=document.createElement('b');b.textContent=String((w.now&&w.now[x[1]])||0);d.appendChild(b);
      d.appendChild(document.createTextNode(' '+x[0]+' '));d.appendChild(dpEl((w.delta[x[1]]|0)));
      host.appendChild(d);});
    var movers=(w.top_risers||[]).slice(0,3);
    if(movers.length){var sep=document.createElement('span');sep.className='wk-sep';sep.textContent='\u00b7';host.appendChild(sep);
      var m=document.createElement('span');m.className='wk-m';m.appendChild(document.createTextNode('Movers: '));
      movers.forEach(function(x,i){if(i){m.appendChild(document.createTextNode(', '));}
        var a=document.createElement('a');a.href=safeUrl('https://github.com/'+String(x.full_name||''));a.target='_blank';a.rel='noopener';
        a.textContent=String(x.full_name||'').split('/')[1]||x.full_name;m.appendChild(a);
        m.appendChild(document.createTextNode(' '));m.appendChild(dpEl(x.d7|0));});
      host.appendChild(m);}
    if((w.entrants||[]).length){var s2=document.createElement('span');s2.className='wk-sep';s2.textContent='\u00b7';host.appendChild(s2);
      var e=document.createElement('span');e.className='wk-d';var b2=document.createElement('b');b2.textContent=String(w.entrants.length);
      e.appendChild(b2);e.appendChild(document.createTextNode(' new entrants'));host.appendChild(e);}
    host.classList.remove('hidden');
  }
  function toast(msg){var t=$('toast');t.textContent=msg;t.classList.add('show');setTimeout(function(){t.classList.remove('show');},1800);}

  function bindToggle(id,key){$(id).addEventListener('click',function(){state[key]=!state[key];this.classList.toggle('on',state[key]);this.setAttribute('aria-pressed',String(state[key]));render();});}

  function boot(){
    readHash();
    buildSeg('segView',[{v:'grid',l:'☰ Grid'},{v:'radar',l:'◎ Radar'}],function(){return state.view;},function(v){state.view=v;});
    buildSeg('segSort',[{v:'activity',l:'Activity'},{v:'stars',l:'Stars'},{v:'rising',l:'Rising'},{v:'new',l:'Newest'},{v:'name',l:'A–Z'}],function(){return state.sort;},function(v){state.sort=v;});
    buildChips();buildLegend();buildLangs();setStats();reflect();
    $('search').addEventListener('input',function(e){state.q=e.target.value;render();});
    $('langSel').addEventListener('change',function(e){state.lang=e.target.value;render();});
    bindToggle('tAct','activeOnly');bindToggle('tNew','newOnly');bindToggle('tFall','fallingOnly');
    var db=$('densBtn');if(db)db.addEventListener('click',function(){state.dens=!state.dens;document.body.classList.toggle('compact',state.dens);db.setAttribute('aria-pressed',String(state.dens));writeHash();});
    var cb=$('clearBtn');if(cb)cb.addEventListener('click',clearFilters);
    $('shareBtn').addEventListener('click',function(){var url='https://axonos-bci.github.io/axonos-community-radar/';
      if(navigator.share){navigator.share({title:'AxonOS Radar',url:location.href}).catch(function(){});}
      else if(navigator.clipboard){navigator.clipboard.writeText(url).then(function(){toast('Link copied');}).catch(function(){toast(url);});}
      else toast(url);});
    document.addEventListener('keydown',function(e){
      var tag=e.target&&e.target.tagName;
      if(e.key==='/'&&['INPUT','SELECT','TEXTAREA'].indexOf(tag)<0){e.preventDefault();var s2=$('search');if(s2&&s2.focus)s2.focus();return;}
      if(e.key==='Escape'&&state.q){state.q='';var s3=$('search');if(s3)s3.value='';render();return;}
      if((e.key==='Enter'||e.key===' ')&&e.target&&e.target.getAttribute&&e.target.getAttribute('role')==='button'){e.preventDefault();e.target.click();}});
    window.addEventListener('resize',function(){drawRadar(filtered());});
    document.body.classList.add('loading');
    render();
    fetch('./data/radar.json',{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){DATA=sanitizeData(j);document.body.classList.remove('loading');buildChips();buildTierChips();buildLangs();setStats();render();}).catch(function(err){console.log('radar data not loaded:',err);document.body.classList.remove('loading');setStats();render();});
    fetch('./data/weekly.json',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(renderWeekly).catch(function(){});
  }
  boot();

  // ── views (beta 3.1.0) ──
  function renderBuilders(){
    var el=$('buildersList'); if(!el)return; var b=(DATA.builders||[]).slice(0,12);
    el.textContent='';
    if(!b.length){var m=document.createElement('div');m.className='muted';m.textContent='No multi-project builders yet \u2014 owners appear here once they have 2+ tracked projects.';el.appendChild(m);return;}
    b.forEach(function(x,i){var cats=(x.top_categories||[]).slice(0,2).join(' \u00b7 ');
      var a=document.createElement('a');a.className='lrow';a.href=safeUrl(x.html_url);a.target='_blank';a.rel='noopener';
      var rk=document.createElement('span');rk.className='rk';rk.textContent=String(i+1);a.appendChild(rk);
      var who=document.createElement('span');who.className='who';
      var bo=document.createElement('b');bo.textContent=String(x.owner||'');who.appendChild(bo);
      if(x.owner_type){var ob=document.createElement('span');ob.className='ob';ob.textContent=(x.owner_type==='Organization'?'ORG':'USER');who.appendChild(ob);}
      var sm=document.createElement('small');
      sm.textContent=(x.project_count||0)+' projects'+(cats?' \u00b7 '+cats:'')+((x.followers|0)>0?(' \u00b7 '+x.followers+' followers'):'');
      who.appendChild(sm);a.appendChild(who);
      var mx=document.createElement('span');mx.className='mx';
      var tb=document.createElement('b');tb.textContent=String(x.total_stars||0);mx.appendChild(tb);
      mx.appendChild(document.createTextNode(' \u2605 \u00b7 '+(x.active_projects_30d||0)+' active'));a.appendChild(mx);
      el.appendChild(a);});
  }
  function switchView(v){
    ['projects','builders','methodology','axonos'].forEach(function(name){var el=$('view-'+name);if(el)el.hidden=(name!==v);});
    var tabs=document.querySelectorAll('#tabs .tab');
    for(var i=0;i<tabs.length;i++){tabs[i].classList.toggle('on',tabs[i].getAttribute('data-view')===v);}
    if(v==='builders')renderBuilders();
    try{location.hash=v==='projects'?'':('#'+v);}catch(e){}
  }
  function stageRank(c){var s=c.querySelector('.ax-stage');var o=['shipped','beta','alpha','design','planned'];for(var i=0;i<o.length;i++){if(s&&s.classList.contains('st-'+o[i]))return i;}return 9;}
  function orderAxCards(){var g=document.querySelector('#view-axonos .ax-grid');if(!g)return;var cs=Array.prototype.slice.call(g.querySelectorAll('.ax-card'));cs.sort(function(a,b){return stageRank(a)-stageRank(b);});cs.forEach(function(c){g.appendChild(c);});}
  function renderAxProgress(){var host=$('axProgress');if(!host)return;var cards=document.querySelectorAll('#view-axonos .ax-card');if(!cards.length)return;var o=['shipped','beta','alpha','design','planned'],cnt={};o.forEach(function(k){cnt[k]=0;});for(var i=0;i<cards.length;i++){var st=cards[i].querySelector('.ax-stage');if(st)for(var j=0;j<o.length;j++){if(st.classList.contains('st-'+o[j])){cnt[o[j]]++;break;}}}var total=cards.length,build=cnt.beta+cnt.alpha+cnt.design;host.textContent='';var bar=document.createElement('div');bar.className='ax-bar';o.forEach(function(k){if(!cnt[k])return;var sg=document.createElement('span');sg.className='ax-seg seg-'+k;sg.style.width=(cnt[k]/total*100).toFixed(2)+'%';bar.appendChild(sg);});host.appendChild(bar);var tx=document.createElement('div');tx.className='ax-prog-txt';function bpart(n,label){var b=document.createElement('b');b.textContent=String(n);tx.appendChild(b);tx.appendChild(document.createTextNode(label));}bpart(cnt.shipped,' shipped \u00b7 ');bpart(build,' in build \u00b7 ');bpart(cnt.planned,' planned ');var cl=document.createElement('span');cl.className='ax-climb';cl.textContent='\u2014 and climbing \u2197';tx.appendChild(cl);host.appendChild(tx);}
  function downloadData(){try{var blob=new Blob([JSON.stringify(DATA,null,2)],{type:'application/json'});var u=URL.createObjectURL(blob);var a=document.createElement('a');a.href=u;a.download='axonos-radar.json';document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(u);},1000);}catch(e){}}
  (function(){var tabs=document.querySelectorAll('#tabs .tab');
    for(var i=0;i<tabs.length;i++){tabs[i].addEventListener('click',function(){switchView(this.getAttribute('data-view'));});}
    var h=(location.hash||'').replace('#','');
    if(h==='builders'||h==='methodology'||h==='axonos')switchView(h);
    orderAxCards();renderAxProgress();var dl=document.getElementById('dlBtn');if(dl)dl.addEventListener('click',downloadData);
  })();

})();
(function(){var b=document.getElementById('dogeCopy');if(!b)return;
  b.addEventListener('click',function(){var a=document.getElementById('dogeAddr');var t=a?(a.textContent||'').trim():'';
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){b.textContent='Copied \u2713';setTimeout(function(){b.textContent='Copy';},1600);},function(){b.textContent='Copy failed';});}
    else{try{var r=document.createRange();r.selectNodeContents(a);var s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy');s.removeAllRanges();b.textContent='Copied \u2713';setTimeout(function(){b.textContent='Copy';},1600);}catch(e){b.textContent='Select & copy';}}
  });})();
