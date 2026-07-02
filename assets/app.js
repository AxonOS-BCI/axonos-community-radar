(function(){
  'use strict';
  function __showErr(msg){try{var d=document.getElementById('__err__');if(!d){d=document.createElement('div');d.id='__err__';d.style.cssText='position:fixed;left:0;right:0;bottom:0;z-index:99999;background:rgba(60,0,0,.95);color:#fff;font:12px/1.4 monospace;padding:10px 12px;white-space:pre-wrap;max-height:45%;overflow:auto;border-top:2px solid #f55';document.body.appendChild(d);}d.textContent='Radar error — please screenshot:\n'+msg;}catch(_){}}
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
      quality_flags:{possible_false_positive:!!q.possible_false_positive},
      first_seen:str(p.first_seen,40)};
  }
  function sanitizeData(j){
    if(!j||typeof j!=='object')return DATA;
    var ps=(Array.isArray(j.projects)?j.projects:[]).map(sanitizeProject).filter(Boolean);
    return {projects:ps,generated_at:str(j.generated_at,40)||null,
      counts:(j.counts&&typeof j.counts==='object')?j.counts:{total:ps.length}};
  }
  var state={q:'',cats:{},lang:'',activeOnly:false,newOnly:false,sort:'activity',view:'grid'};
  var points=[];

  function filtered(){
    var q=state.q.toLowerCase(),anyCat=Object.keys(state.cats).some(function(k){return state.cats[k];});
    var arr=DATA.projects.filter(function(p){
      if(state.activeOnly&&!p.active)return false;
      if(state.newOnly&&!p.is_new)return false;
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
  function renderCards(arr){
    var l=$('cards');
    if(!arr.length){l.innerHTML='<div class="empty"><div class="big">'+(DATA.generated_at?'No matches':'Radar warming up')+'</div>'+(DATA.generated_at?(anyFilter()?'Nothing matches these filters — <button class="lnkbtn" id="emptyCl" type="button">clear all</button>.':'No projects yet.'):'The first scan runs on publish and refreshes every 3 hours. Real projects appear here shortly.')+'</div>';var ec=$('emptyCl');if(ec)ec.addEventListener('click',clearFilters);return;}
    var html='';
    for(var i=0;i<arr.length;i++){var p=arr[i],col=catColor(p.category);
      html+='<a class="pc" data-cc="'+esc(col)+'" href="'+esc(safeUrl(p.html_url))+'" target="_blank" rel="noopener">'
        +'<div class="top"><span class="pill">'+esc(p.category)+'</span>'+evBadge(p)+flagBadge(p)
        +(p.rising?'<span class="rise">↑ '+(p.stars_delta_7d>0?('+'+p.stars_delta_7d+'/7d'):'rising')+'</span>':(p.falling?'<span class="fallb">↓ '+p.stars_delta_7d+'/7d</span>':(p.is_new?'<span class="nb">NEW</span>':'')))+'<span class="st">★ '+(p.stars||0)+'</span></div>'
        +'<h3>'+esc(p.full_name)+'</h3><p class="desc">'+esc(p.description||'—')+'</p>'
        +tagRow(p)
        +'<div class="foot"><span class="lng"><span class="ld"></span>'+esc(p.language||'n/a')+'</span>'
        +'<span class="ac"><span class="ad'+(p.active?' on':'')+'"></span>'+fmtAge(p.days_since_push)+'</span></div></a>';}
    l.innerHTML=html;
    var pcs=l.querySelectorAll('.pc');for(var j=0;j<pcs.length;j++){var cc=pcs[j].getAttribute('data-cc');if(cc)pcs[j].style.setProperty('--cc',cc);}
  }

  function anyFilter(){return !!(state.q||state.lang||state.activeOnly||state.newOnly||Object.keys(state.cats).some(function(k){return state.cats[k];}));}
  function clearFilters(){state.q='';state.lang='';state.activeOnly=false;state.newOnly=false;state.cats={};
    var se=$('search');if(se)se.value='';var ls=$('langSel');if(ls)ls.value='';
    ['tAct','tNew'].forEach(function(id){var t=$(id);if(t){t.classList.remove('on');t.setAttribute('aria-pressed','false');}});
    buildChips();render();}
  function readHash(){try{var h=(location.hash||'').replace(/^#/,'');if(!h)return;var p={};h.split('&').forEach(function(kv){var i=kv.indexOf('=');if(i>0)p[kv.slice(0,i)]=decodeURIComponent(kv.slice(i+1).replace(/\+/g,' '));});
    if(p.view==='radar'||p.view==='grid')state.view=p.view;
    if(['activity','stars','rising','new','name'].indexOf(p.sort)>=0)state.sort=p.sort;
    if(p.lang)state.lang=p.lang; if(p.q)state.q=p.q;
    state.activeOnly=p.active==='1'; state.newOnly=p.new==='1';
    if(p.cat)p.cat.split(',').forEach(function(c){if(c)state.cats[c]=true;});}catch(e){}}
  function writeHash(){try{var p=[];
    if(state.view!=='grid')p.push('view='+state.view);
    if(state.sort!=='activity')p.push('sort='+state.sort);
    if(state.lang)p.push('lang='+encodeURIComponent(state.lang));
    if(state.q)p.push('q='+encodeURIComponent(state.q));
    if(state.activeOnly)p.push('active=1'); if(state.newOnly)p.push('new=1');
    var on=Object.keys(state.cats).filter(function(k){return state.cats[k];});
    if(on.length)p.push('cat='+on.map(encodeURIComponent).join(','));
    if(window.history&&history.replaceState)history.replaceState(null,'',p.length?'#'+p.join('&'):location.pathname+location.search);}catch(e){}}
  function reflect(){var se=$('search');if(se)se.value=state.q;var ls=$('langSel');if(ls)ls.value=state.lang;
    [['tAct',state.activeOnly],['tNew',state.newOnly]].forEach(function(x){var t=$(x[0]);if(t){t.classList.toggle('on',x[1]);t.setAttribute('aria-pressed',String(x[1]));}});}
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
  function buildSeg(id,opts,get,set){var c=$(id);if(!c)return;c.innerHTML='';var btns=[];
    opts.forEach(function(o){var b=document.createElement('button');b.className='seg-opt'+(o.v===get()?' on':'');b.textContent=o.l;
      b.setAttribute('role','tab');b.setAttribute('tabindex','0');b.setAttribute('aria-selected',String(o.v===get()));
      b.addEventListener('click',function(){set(o.v);btns.forEach(function(x){x.classList.remove('on');x.setAttribute('aria-selected','false');});b.classList.add('on');b.setAttribute('aria-selected','true');render();});
      btns.push(b);c.appendChild(b);});}

  function buildChips(){var c=$('chips');if(!c)return;c.innerHTML='';
    var counts={};DATA.projects.forEach(function(p){counts[p.category]=(counts[p.category]||0)+1;});
    CATS.forEach(function(cat){if(cat.n==='Other')return;var on=!!state.cats[cat.n],nn=counts[cat.n]||0;
    var el=document.createElement('div');el.className='chip'+(on?' on':'');el.setAttribute('role','button');el.setAttribute('tabindex','0');el.setAttribute('aria-pressed',String(on));
    el.style.setProperty('--cc',cat.c);el.innerHTML='<span class="dot"></span>'+esc(cat.n)+(nn?' <span class="cnt">'+nn+'</span>':'');
    el.addEventListener('click',function(){state.cats[cat.n]=!state.cats[cat.n];el.classList.toggle('on',state.cats[cat.n]);el.setAttribute('aria-pressed',String(!!state.cats[cat.n]));render();});
    c.appendChild(el);});}
  function buildLegend(){var l=$('legend');if(!l)return;l.innerHTML='';CATS.forEach(function(cat){if(cat.n==='Other')return;var s=document.createElement('span');s.style.setProperty('--cc',cat.c);s.innerHTML='<span class="dot"></span>'+esc(cat.n);l.appendChild(s);});var n=document.createElement('span');n.className='leg-note';n.textContent='\u00b7 inner = recent \u00b7 size = stars \u00b7 \u2726 new';l.appendChild(n);}
  function buildLangs(){var sel=$('langSel');if(!sel)return;var langs={};DATA.projects.forEach(function(p){if(p.language)langs[p.language]=(langs[p.language]||0)+1;});
    var arr=Object.keys(langs).sort(function(a,b){return langs[b]-langs[a];});
    sel.innerHTML='<option value="">All languages</option>'+arr.map(function(L){return '<option value="'+esc(L)+'">'+esc(L)+' ('+langs[L]+')</option>';}).join('');
    sel.value=state.lang;}

  function setStats(){
    var c=DATA.counts||{},tot=c.total||DATA.projects.length,act=c.active_30d||0,nw=c.new||0;
    var stars=DATA.projects.reduce(function(s,p){return s+(p.stars||0);},0),cats={};DATA.projects.forEach(function(p){cats[p.category]=1;});
    function k(n){return n>=1000?(n/1000).toFixed(n>=10000?0:1)+'k':String(n);}
    $('stats').innerHTML='<div class="stat a"><b>'+tot+'</b><span>PROJECTS</span></div>'
      +'<div class="stat n"><b>'+nw+'</b><span>NEW THIS WEEK</span></div>'
      +'<div class="stat s"><b>'+k(stars)+'</b><span>TOTAL STARS</span></div>'
      +'<div class="stat c"><b>'+act+'</b><span>ACTIVE 30D</span></div>';
    var u=$('updated');
    if(DATA.generated_at){var d=new Date(DATA.generated_at);u.innerHTML='Updated '+d.toUTCString().replace('GMT','UTC')+' · refreshes every 3h · <a href="./feed.xml">RSS</a>';}
    else u.textContent='Warming up — first scan runs on publish · refreshes every 3h';
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
    bindToggle('tAct','activeOnly');bindToggle('tNew','newOnly');
    var cb=$('clearBtn');if(cb)cb.addEventListener('click',clearFilters);
    $('shareBtn').addEventListener('click',function(){var url='https://axonos-bci.github.io/axonos-community-radar/';
      if(navigator.share){navigator.share({title:'AxonOS Radar',url:location.href}).catch(function(){});}
      else if(navigator.clipboard){navigator.clipboard.writeText(url).then(function(){toast('Link copied');}).catch(function(){toast(url);});}
      else toast(url);});
    document.addEventListener('keydown',function(e){
      var tag=e.target&&e.target.tagName;
      if(e.key==='/'&&['INPUT','SELECT','TEXTAREA'].indexOf(tag)<0){e.preventDefault();var s2=$('search');if(s2&&s2.focus)s2.focus();return;}
      if((e.key==='Enter'||e.key===' ')&&e.target&&e.target.getAttribute&&e.target.getAttribute('role')==='button'){e.preventDefault();e.target.click();}});
    window.addEventListener('resize',function(){drawRadar(filtered());});
    render();
    fetch('./data/radar.json',{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){DATA=sanitizeData(j);buildChips();buildLangs();setStats();render();}).catch(function(err){console.log('radar data not loaded:',err);setStats();render();});
  }
  boot();

  // ── views (beta 3.1.0) ──
  function renderBuilders(){
    var el=$('buildersList'); if(!el)return; var b=(DATA.builders||[]).slice(0,12);
    if(!b.length){el.innerHTML='<div class="muted">No multi-project builders yet — owners appear here once they have 2+ tracked projects.</div>';return;}
    el.innerHTML=b.map(function(x,i){var cats=(x.top_categories||[]).slice(0,2).join(' \u00b7 ');
      return '<a class="lrow" href="'+esc(safeUrl(x.html_url))+'" target="_blank" rel="noopener">'
        +'<span class="rk">'+(i+1)+'</span><span class="who"><b>'+esc(x.owner)+'</b><small>'+(x.project_count||0)+' projects'+(cats?' \u00b7 '+esc(cats):'')+'</small></span>'
        +'<span class="mx"><b>'+(x.total_stars||0)+'</b> \u2605 \u00b7 '+(x.active_projects_30d||0)+' active</span></a>';}).join('');
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
  function renderAxProgress(){var el=$('axProgress');if(!el)return;var cards=document.querySelectorAll('#view-axonos .ax-card');if(!cards.length)return;var o=['shipped','beta','alpha','design','planned'],cnt={};o.forEach(function(k){cnt[k]=0;});for(var i=0;i<cards.length;i++){var s=cards[i].querySelector('.ax-stage');if(s)for(var j=0;j<o.length;j++){if(s.classList.contains('st-'+o[j])){cnt[o[j]]++;break;}}}var total=cards.length,build=cnt.beta+cnt.alpha+cnt.design;var bar='';o.forEach(function(k){if(cnt[k])bar+='<span class="ax-seg seg-'+k+'" data-w="'+(cnt[k]/total*100).toFixed(2)+'"></span>';});el.innerHTML='<div class="ax-bar">'+bar+'</div><div class="ax-prog-txt"><b>'+cnt.shipped+'</b> shipped \u00b7 <b>'+build+'</b> in build \u00b7 <b>'+cnt.planned+'</b> planned <span class="ax-climb">\u2014 and climbing \u2197</span></div>';var segs=el.querySelectorAll('.ax-seg');for(var m=0;m<segs.length;m++){segs[m].style.width=segs[m].getAttribute('data-w')+'%';}}
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
