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
  function score100(v){v=Number(v);if(!isFinite(v))return null;return Math.max(0,Math.min(100,Math.round(v)));}
  var HDIMS=['license','maintenance','momentum','adoption','team','docs'];
  var HBASIS={'enriched':1,'partial':1,'search-only':1};
  function sanitizeSignals(s){
    if(!s||typeof s!=='object')return null;
    var ov=score100(s.overall);if(ov==null)return null;
    var out={overall:ov,basis:HBASIS[s.basis]?s.basis:'search-only',
      badges:(Array.isArray(s.badges)?s.badges:[]).slice(0,6).map(function(b){return str(b,24);})};
    HDIMS.forEach(function(d){var v=score100(s[d]);if(v!=null)out[d]=v;});
    return out;
  }
  // v6 "Solid Ground": interop labels mirror data/interop-vocab.json — the
  // documentation-coverage gate (scripts/check_methodology.py) keeps them in sync.
  var IOPL={'lsl':'LSL','brainflow':'BrainFlow','bids':'BIDS','edf':'EDF','mne':'MNE',
    'eeglab':'EEGLAB','openvibe':'OpenViBE','timeflux':'Timeflux','openbci':'OpenBCI',
    'emotiv':'Emotiv','neurosity':'Neurosity','gtec':'g.tec','muse':'Muse','ads1299':'ADS1299',
    'freeeeg':'FreeEEG','ros':'ROS','unity':'Unity','arduino':'Arduino','esp32':'ESP32','ble':'BLE'};
  var FKEYS=['license_file','readme','contributing','code_of_conduct','citation','security_policy','ci'];
  var FLABEL={license_file:'Licence file',readme:'README',contributing:'CONTRIBUTING',
    code_of_conduct:'Code of conduct',citation:'CITATION.cff',security_policy:'SECURITY.md',ci:'CI workflows'};
  function sanitizeFoundation(f){
    if(!f||typeof f!=='object')return null;
    var out={},n=0;
    FKEYS.forEach(function(k){out[k]=f[k]===true;if(out[k])n++;});
    var hp=score100(f.health_pct);out.health_pct=hp;
    out.count=n;   // recomputed locally — never trust a shipped count
    return out;
  }
  function sanitizeProject(p){
    if(!p||typeof p!=='object')return null;
    var q=p.quality_flags&&typeof p.quality_flags==='object'?p.quality_flags:{};
    return {full_name:str(p.full_name,140),html_url:safeUrl(p.html_url),
      description:str(p.description,300),category:str(p.category,60)||'Other',
      language:str(p.language,40),stars:num(p.stars),forks:num(p.forks),
      days_since_push:num(p.days_since_push),active:!!p.active,is_new:!!p.is_new,
      rising:!!p.rising,falling:!!p.falling,stars_delta_7d:num(p.stars_delta_7d),
      evidence_tier:str(p.evidence_tier,40),inclusion_reason:str(p.inclusion_reason,200),
      brs:num(p.brs),relevance_tier:str(p.relevance_tier,40),
      relevance_ledger:(Array.isArray(p.relevance_ledger)?p.relevance_ledger:[]).slice(0,24).map(function(e){
        return {points:num(e&&e.points),kind:str(e&&e.kind,20),reason:str(e&&e.reason,160)};}),
      topics:(Array.isArray(p.topics)?p.topics:[]).slice(0,12).map(function(t){return str(t,50);}),
      license:str(p.license,40),has_license:!!p.has_license,
      quality_flags:{possible_false_positive:!!q.possible_false_positive},
      ecosystem:!!p.ecosystem,ecosystem_role:str(p.ecosystem_role,80),
      ecosystem_note:str(p.ecosystem_note,200),
      org_domicile:str(p.org_domicile,60),funding_round:str(p.funding_round,40),
      interop:(Array.isArray(p.interop)?p.interop:[]).slice(0,8).map(function(t){return str(t,24).toLowerCase();}).filter(function(t){return !!IOPL[t];}),
      foundation:sanitizeFoundation(p.foundation),
      first_seen:str(p.first_seen,40),signals:sanitizeSignals(p.signals)};
  }
  function sanitizeBuilder(b){
    if(!b||typeof b!=='object')return null;
    return {owner:str(b.owner,80),html_url:safeUrl(b.html_url),
      project_count:num(b.project_count),total_stars:num(b.total_stars),
      active_projects_30d:num(b.active_projects_30d),
      top_categories:(Array.isArray(b.top_categories)?b.top_categories:[]).slice(0,4).map(function(t){return str(t,60);}),
      owner_type:str(b.owner_type,20),followers:num(b.followers)};
  }
  function sanitizeEcosystem(e){
    if(!e||typeof e!=='object')return null;
    function owner(o){if(!o||typeof o!=='object')return null;
      return {login:str(o.login,80),type:str(o.type,20),name:str(o.name,120),
        company:str(o.company,120),location:str(o.location,120),bio:str(o.bio,200),
        blog:safeUrlAny(o.blog),followers:num(o.followers),public_repos:num(o.public_repos),
        html_url:safeUrl(o.html_url),
        members:(Array.isArray(o.members)?o.members:[]).slice(0,8).map(function(m){
          return {login:str(m.login,80),html_url:safeUrl(m.html_url)};})};}
    var owners={};if(e.owners&&typeof e.owners==='object'){Object.keys(e.owners).slice(0,10).forEach(function(k){var o=owner(e.owners[k]);if(o)owners[str(k,80)]=o;});}
    return {owners:owners,
      links:(Array.isArray(e.links)?e.links:[]).slice(0,20).map(function(l){
        return {a:str(l.a,140),b:str(l.b,140),weight:num(l.weight),
          shared:(Array.isArray(l.shared)?l.shared:[]).slice(0,6).map(function(x){return str(x,80);})};}),
      key_people:(Array.isArray(e.key_people)?e.key_people:[]).slice(0,12).map(function(kp){
        return {login:str(kp.login,80),reach:num(kp.reach),
          repos:(Array.isArray(kp.repos)?kp.repos:[]).slice(0,10).map(function(x){return str(x,140);})};}),
      repo_count:num(e.repo_count)};
  }
  function sanitizeMap(cm,sg){
    var out={coverage_matrix:null,standards_graph:null};
    if(cm&&typeof cm==='object'&&Array.isArray(cm.stages)&&Array.isArray(cm.grid)){
      out.coverage_matrix={
        stages:cm.stages.map(function(s){return str(s,40);}),
        modalities:(Array.isArray(cm.modalities)?cm.modalities:[]).map(function(s){return str(s,40);}),
        grid:cm.grid.map(function(r){return {modality:str(r&&r.modality,40),
          cells:(Array.isArray(r&&r.cells)?r.cells:[]).map(function(n){return Math.max(0,parseInt(n,10)||0);}),
          total:Math.max(0,parseInt(r&&r.total,10)||0)};}),
        stage_totals:(Array.isArray(cm.stage_totals)?cm.stage_totals:[]).map(function(n){return Math.max(0,parseInt(n,10)||0);}),
        n_projects:Math.max(0,parseInt(cm.n_projects,10)||0)};
    }
    if(sg&&typeof sg==='object'&&Array.isArray(sg.standards)){
      out.standards_graph={
        standards:sg.standards.map(function(s){return {standard:str(s&&s.standard,40),
          count:Math.max(0,parseInt(s&&s.count,10)||0),
          repos:(Array.isArray(s&&s.repos)?s.repos:[]).slice(0,40).map(function(r){return str(r,120);})};}),
        n_standards:Math.max(0,parseInt(sg.n_standards,10)||0),
        n_repos_with_standards:Math.max(0,parseInt(sg.n_repos_with_standards,10)||0),
        interop_edges:Math.max(0,parseInt(sg.interop_edges,10)||0)};
    }
    return out;
  }
  function sanitizeData(j){
    if(!j||typeof j!=='object')return DATA;
    var ps=(Array.isArray(j.projects)?j.projects:[]).map(sanitizeProject).filter(Boolean);
    var bs=(Array.isArray(j.builders)?j.builders:[]).map(sanitizeBuilder).filter(Boolean);
    var eco=sanitizeEcosystem(j.ecosystem);
    var mp=sanitizeMap(j.coverage_matrix,j.standards_graph);
    return {projects:ps,builders:bs,ecosystem:eco,generated_at:str(j.generated_at,40)||null,
      counts:(j.counts&&typeof j.counts==='object')?j.counts:{total:ps.length},
      coverage_matrix:mp.coverage_matrix,standards_graph:mp.standards_graph};
  }
  // Dogecoin support address. Empty string = the card stays hidden.
  // Set at publish time; keeps the radar's scans, enrichment budget and
  // hosting free for everyone.
  var DONATE_DOGE='DMwHAhqVNWf7dyEznukxCufNS5rjuP5MTp';
  var state={q:'',cats:{},lang:'',activeOnly:false,newOnly:false,fallingOnly:false,tiers:{},iops:{},dens:false,sort:'activity',view:'grid'};
  var points=[];

  function filtered(){
    var q=state.q.toLowerCase(),anyCat=Object.keys(state.cats).some(function(k){return state.cats[k];});
    var anyTier=Object.keys(state.tiers).some(function(k){return state.tiers[k];});
    var arr=DATA.projects.filter(function(p){
      if(state.activeOnly&&!p.active)return false;
      if(state.newOnly&&!p.is_new)return false;
      if(state.fallingOnly&&!p.falling)return false;
      var ion=Object.keys(state.iops).filter(function(k){return state.iops[k];});
      if(ion.length&&!ion.some(function(t){return (p.interop||[]).indexOf(t)>=0;}))return false;
      if(anyTier&&!state.tiers[p.evidence_tier])return false;
      if(anyCat&&!state.cats[p.category])return false;
      if(state.lang&&(p.language||'')!==state.lang)return false;
      if(q){var hay=(p.full_name+' '+(p.description||'')+' '+(p.language||'')+' '+(p.topics||[]).join(' ')).toLowerCase();if(hay.indexOf(q)<0)return false;}
      return true;
    });
    function hov(p){return (p.signals&&typeof p.signals.overall==='number')?p.signals.overall:-1;}
    arr.sort(state.sort==='stars'?function(a,b){return (b.stars||0)-(a.stars||0);}
      :state.sort==='relevance'?function(a,b){function bs(p){return typeof p.brs==='number'?p.brs:-1;}return (bs(b)-bs(a))||((b.stars||0)-(a.stars||0));}
      :state.sort==='health'?function(a,b){return (hov(b)-hov(a))||((b.stars||0)-(a.stars||0));}
      :state.sort==='rising'?function(a,b){return ((b.stars_delta_7d||0)-(a.stars_delta_7d||0))||((b.stars||0)-(a.stars||0));}
      :state.sort==='foundation'?function(a,b){function fc(p){return p.foundation?p.foundation.count:-1;}return (fc(b)-fc(a))||(hov(b)-hov(a))||((b.stars||0)-(a.stars||0));}
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
  function safeUrlAny(u){u=String(u||'');if(!u)return '';if(/^https?:\/\//.test(u))return u;if(/^[\w.-]+\.[a-z]{2,}(\/.*)?$/i.test(u))return 'https://'+u;return '';}
  function el(tag,cls,txt){var e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;}
  function tagRowEl(p){var t=(p.topics||[]).filter(function(x){return !GENERIC[String(x).toLowerCase()];}).slice(0,3);
    if(!t.length)return null;var d=el('div','tags');t.forEach(function(x){d.appendChild(el('span','tag',x));});return d;}
  function evBadgeEl(p){var t=p.evidence_tier;if(!t)return null;var e=TIER[t]||['\u2022','tl0'];
    var sp=el('span','ev '+e[1],e[0]);sp.title=p.inclusion_reason||t;return sp;}
  // v7.1 "Legible": the BCI Relevance Score, and the signed evidence ledger that
  // produced it — the "why included" that no other radar shows. The badge is a
  // real control on an otherwise-link card: clicking it reveals the ledger
  // inline instead of navigating.
  var RTIER={L4_EXPLICIT_BCI:'Explicit BCI',L3_STANDARD_OR_HARDWARE:'Standard / hardware',
    L3_MODALITY_OR_PARADIGM:'Modality / paradigm',L2_NEURO_TERM:'Neuro term',
    L1_WEAK_KEEP:'Weak keep',L0_REJECTED:'Rejected'};
  function brsClass(v){return v>=80?'brs-hi':(v>=55?'brs-md':'brs-lo');}
  function brsBadgeEl(p,panel){
    if(p.brs==null||!(p.relevance_ledger&&p.relevance_ledger.length))return evBadgeEl(p);
    var b=el('span','brs '+brsClass(p.brs));
    b.setAttribute('role','button');b.setAttribute('tabindex','0');
    b.appendChild(el('span','brs-k','BRS'));
    b.appendChild(el('span','brs-v',String(p.brs)));
    var tierTxt=RTIER[p.relevance_tier]||p.relevance_tier||'';
    b.setAttribute('aria-label','BCI Relevance Score '+p.brs+(tierTxt?(' \u2014 '+tierTxt):'')+'. Show why it\u2019s included.');
    b.title='BCI Relevance Score '+p.brs+'/100'+(tierTxt?(' \u00b7 '+tierTxt):'')+' \u2014 tap for the evidence';
    b.setAttribute('aria-expanded','false');
    function toggle(ev){
      ev.preventDefault();ev.stopPropagation();
      if(!panel)return;
      var open=panel.classList.toggle('open');
      b.setAttribute('aria-expanded',String(open));
    }
    b.addEventListener('click',toggle);
    b.addEventListener('keydown',function(ev){
      if(ev.key==='Enter'||ev.key===' '||ev.key==='Spacebar'||ev.keyCode===13||ev.keyCode===32)toggle(ev);
    });
    return b;
  }
  function ledgerPanelEl(p){
    if(p.brs==null||!(p.relevance_ledger&&p.relevance_ledger.length))return null;
    var wrap=el('div','ledger');
    var head=el('div','ledger-h');
    head.appendChild(el('span','ledger-title','Why it\u2019s included'));
    var tierTxt=RTIER[p.relevance_tier]||'';
    if(tierTxt)head.appendChild(el('span','ledger-tier',tierTxt));
    wrap.appendChild(head);
    p.relevance_ledger.forEach(function(e){
      var neg=e.points<0;
      var row=el('div','lg-row'+(neg?' neg':' pos'));
      var pts=el('span','lg-pts',(neg?'':'+')+e.points);
      row.appendChild(pts);
      row.appendChild(el('span','lg-reason',e.reason));
      wrap.appendChild(row);
    });
    var foot=el('div','ledger-f');
    foot.appendChild(document.createTextNode('Score '+p.brs+'/100. A repo is kept only when BCI-specific evidence outweighs generic-ML signals.'));
    wrap.appendChild(foot);
    // v12 "Badges": the scored badge, ready to paste. Derived from the last
    // scan — the engine writes it, nobody grants it.
    if(p.full_name&&/^[A-Za-z0-9._-]+\/[A-Za-z0-9._-]+$/.test(p.full_name)){
      var SITE='https://axonos-bci.github.io/axonos-community-radar';
      var md='[![AxonOS Radar](https://img.shields.io/endpoint?url='+encodeURIComponent(SITE+'/badges/'+p.full_name+'.json')+')]('+SITE+'/)';
      var bd=el('div','ledger-badge');
      var btn=document.createElement('button');
      btn.type='button';btn.className='badge-copy';btn.textContent='Copy badge';
      btn.title='Copy the embeddable scored badge (Markdown) for '+p.full_name;
      btn.setAttribute('aria-label','Copy the embeddable scored badge markdown for '+p.full_name);
      btn.addEventListener('click',function(ev){
        ev.preventDefault();ev.stopPropagation();
        function ok(){btn.textContent='Copied \u2713';btn.classList.add('done');
          setTimeout(function(){btn.textContent='Copy badge';btn.classList.remove('done');},1600);}
        function fallback(){var ta=document.createElement('textarea');ta.value=md;
          ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);
          ta.select();try{document.execCommand('copy');ok();}catch(e){}document.body.removeChild(ta);}
        if(navigator.clipboard&&navigator.clipboard.writeText){
          navigator.clipboard.writeText(md).then(ok,fallback);
        }else{fallback();}
      });
      bd.appendChild(btn);
      bd.appendChild(el('span','badge-hint','embeddable \u00b7 live \u00b7 scored by the engine'));
      wrap.appendChild(bd);
    }
    return wrap;
  }
  function flagBadgeEl(p){var q=p.quality_flags||{};var hit=Array.isArray(q)?q.indexOf('possible_false_positive')>=0:!!q.possible_false_positive;
    if(!hit)return null;var sp=el('span','flag','\u26A0 review');sp.title='Borderline match \u2014 flagged for review';return sp;}
  // Ecosystem Health meter: a visible 0-100 bar (band-coloured) with the full
  // per-dimension breakdown in the accessible title, so the card stays a link.
  var HBAND=[[80,'strong','var(--emerald)'],[60,'solid','var(--accent)'],[40,'developing','var(--amber)'],[0,'early','var(--rose)']];
  var HLABEL={license:'Licence',maintenance:'Maintenance',momentum:'Momentum',adoption:'Adoption',team:'Team',docs:'Doc signals'};
  function hband(v){for(var i=0;i<HBAND.length;i++)if(v>=HBAND[i][0])return HBAND[i];return HBAND[HBAND.length-1];}
  function healthEl(p){
    var s=p.signals;if(!s)return null;
    var b=hband(s.overall);
    var wrap=el('div','hlth');wrap.style.setProperty('--hc',b[2]);
    var head=el('div','hlth-h');
    head.appendChild(el('span','hlth-k','Health'));
    var val=el('span','hlth-v');val.appendChild(document.createTextNode(String(s.overall)));
    var band=el('span','hlth-band',b[1]);val.appendChild(band);head.appendChild(val);
    wrap.appendChild(head);
    var track=el('div','hlth-bar');var fill=el('span','hlth-fill');fill.style.width=s.overall+'%';track.appendChild(fill);wrap.appendChild(track);
    // breakdown in the title (keyboard/hover accessible, no link break)
    var parts=[];HDIMS.forEach(function(d){if(s[d]!=null)parts.push(HLABEL[d]+' '+s[d]);});
    var basis=s.basis==='search-only'?' \u00b7 search-only (momentum/team not measured)':(s.basis==='partial'?' \u00b7 partial data':'');
    wrap.title='Health '+s.overall+'/100 \u2014 '+parts.join(' \u00b7 ')+basis+
      (s.badges&&s.badges.length?('\n'+s.badges.join(' \u00b7 ')):'')+
      '\nComputed from public GitHub signals \u2014 a maturity read-out, not an endorsement.';
    return wrap;
  }
  function iopRowEl(p){var t=(p.interop||[]);if(!t.length)return null;
    var d=el('div','iops');t.slice(0,5).forEach(function(x){
      var sp=el('span','iop',IOPL[x]||x);
      sp.title='Speaks / built for '+(IOPL[x]||x)+' \u2014 detected from topics & description (heuristic, see Methodology).';
      d.appendChild(sp);});
    return d;}
  function fndEl(p){var f=p.foundation;if(!f)return null;
    var sp=el('span','fnd');sp.appendChild(el('b',null,f.count+'/7'));sp.appendChild(document.createTextNode(' foundation'));
    var lines=FKEYS.map(function(k){return (f[k]?'\u2713 ':'\u2717 ')+FLABEL[k];});
    sp.title='Foundation signals \u2014 checkable repo facts, not a quality score:\n'+lines.join('\n')+
      (f.health_pct!=null?('\nCommunity profile '+f.health_pct+'%'):'')+
      '\nAbsence of a check means the file was not found \u2014 it says nothing about code quality.';
    return sp;}
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
      var a=el('a','pc'+(p.ecosystem?' eco':''));a.href=safeUrl(p.html_url);a.target='_blank';a.rel='noopener';a.style.setProperty('--cc',col);
      var top=el('div','top');
      if(p.ecosystem){var eb=el('span','ecobadge','\u25C8 AxonOS');eb.title='AxonOS ecosystem project';top.appendChild(eb);}
      top.appendChild(el('span','pill',p.category));
      var lpanel=ledgerPanelEl(p);
      var ev=brsBadgeEl(p,lpanel);if(ev)top.appendChild(ev);
      var fl=flagBadgeEl(p);if(fl)top.appendChild(fl);
      if(p.rising){top.appendChild(el('span','rise','\u2191 '+(p.stars_delta_7d>0?('+'+p.stars_delta_7d+'/7d'):'rising')));}
      else if(p.falling){top.appendChild(el('span','fallb','\u2193 '+p.stars_delta_7d+'/7d'));}
      else if(p.is_new){top.appendChild(el('span','nb','NEW'));}
      if(!p.license){var lic=el('span','lic','\u26A0 no licence');lic.title='No licence detected \u2014 reuse rights unclear';top.appendChild(lic);}
      else if(p.license==='NOASSERTION'){var lu=el('span','lic','\u26A0 licence unclear');lu.title='GitHub cannot classify this licence (NOASSERTION)';top.appendChild(lu);}
      top.appendChild(el('span','st','\u2605 '+(p.stars||0)));
      a.appendChild(top);
      a.appendChild(el('h3',null,p.full_name));
      if(p.ecosystem&&p.ecosystem_role){a.appendChild(el('div','ecorole',p.ecosystem_role));}
      a.appendChild(el('p','desc',p.description||(p.ecosystem&&p.ecosystem_note?p.ecosystem_note:'\u2014')));
      var tr=tagRowEl(p);if(tr)a.appendChild(tr);
      var ir=iopRowEl(p);if(ir)a.appendChild(ir);
      if(lpanel)a.appendChild(lpanel);
      var hl=healthEl(p);if(hl)a.appendChild(hl);
      var foot=el('div','foot');
      var lng=el('span','lng');lng.appendChild(el('span','ld'));lng.appendChild(document.createTextNode(p.language||'n/a'));foot.appendChild(lng);
      var ac=el('span','ac');ac.appendChild(el('span','ad'+(p.active?' on':'')));ac.appendChild(document.createTextNode(fmtAge(p.days_since_push)));foot.appendChild(ac);
      var fn=fndEl(p);if(fn)foot.appendChild(fn);
      a.appendChild(foot);
      l.appendChild(a);
    })(arr[i]);}
  }

  function anyFilter(){return !!(state.q||state.lang||state.activeOnly||state.newOnly||Object.keys(state.cats).some(function(k){return state.cats[k];})||Object.keys(state.iops).some(function(k){return state.iops[k];}));}
  function clearFilters(){state.q='';state.lang='';state.activeOnly=false;state.newOnly=false;state.fallingOnly=false;state.cats={};state.tiers={};state.iops={};
    var se=$('search');if(se)se.value='';var ls=$('langSel');if(ls)ls.value='';
    ['tAct','tNew','tFall'].forEach(function(id){var t=$(id);if(t){t.classList.remove('on');t.setAttribute('aria-pressed','false');}});
    buildChips();buildTierChips();buildIopChips();render();}
  function readHash(){try{var h=(location.hash||'').replace(/^#/,'');if(!h)return;var p={};h.split('&').forEach(function(kv){var i=kv.indexOf('=');if(i>0)p[kv.slice(0,i)]=decodeURIComponent(kv.slice(i+1).replace(/\+/g,' '));});
    if(p.view==='radar'||p.view==='grid')state.view=p.view;
    if(['activity','relevance','health','stars','rising','foundation','new','name'].indexOf(p.sort)>=0)state.sort=p.sort;
    if(p.lang)state.lang=p.lang; if(p.q)state.q=p.q;
    state.activeOnly=p.active==='1'; state.newOnly=p.new==='1'; state.fallingOnly=p.fall==='1'; state.dens=p.d==='1';
    if(p.cat)p.cat.split(',').forEach(function(c){if(c)state.cats[c]=true;});
    if(p.tier)p.tier.split(',').forEach(function(t){if(t)state.tiers[t]=true;});
    if(p.iop)p.iop.split(',').forEach(function(t){if(t)state.iops[t]=true;});}catch(e){}}
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
    var inr=Object.keys(state.iops).filter(function(k){return state.iops[k];});
    if(inr.length)p.push('iop='+inr.map(encodeURIComponent).join(','));
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
  function buildIopChips(){var c=$('iopChips');if(!c)return;c.textContent='';
    var counts={};DATA.projects.forEach(function(p){(p.interop||[]).forEach(function(t){counts[t]=(counts[t]||0)+1;});});
    var tags=Object.keys(counts).sort(function(a,b){return counts[b]-counts[a]||a.localeCompare(b);});
    if(!tags.length){c.classList.add('hidden');return;}c.classList.remove('hidden');
    var lab=el('span','iop-lab','Speaks');lab.title='Protocols, formats and hardware this project integrates with \u2014 heuristic detection, documented in Methodology.';c.appendChild(lab);
    tags.forEach(function(t){var on=!!state.iops[t];
      var ch=document.createElement('div');ch.className='chip iopc'+(on?' on':'');ch.setAttribute('role','button');ch.setAttribute('tabindex','0');ch.setAttribute('aria-pressed',String(on));
      ch.appendChild(document.createTextNode(IOPL[t]||t));
      var cn=document.createElement('span');cn.className='cnt';cn.textContent=String(counts[t]);ch.appendChild(document.createTextNode(' '));ch.appendChild(cn);
      ch.addEventListener('click',function(){state.iops[t]=!state.iops[t];ch.classList.toggle('on',state.iops[t]);ch.setAttribute('aria-pressed',String(!!state.iops[t]));render();});
      c.appendChild(ch);});}
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

  function ghUser(login){var a=el('a','eco-person');a.href=safeUrl('https://github.com/'+login);a.target='_blank';a.rel='noopener';
    var av=el('img','eco-av');av.src='https://avatars.githubusercontent.com/'+login+'?s=48';av.alt='';av.width=24;av.height=24;av.loading='lazy';a.appendChild(av);
    a.appendChild(el('span',null,login));return a;}
  function renderEcosystem(){
    var host=$('ecosystem');if(!host)return;var e=DATA.ecosystem;
    if(!e||!e.owners||!Object.keys(e.owners).length){host.classList.add('hidden');return;}
    host.textContent='';host.classList.remove('hidden');
    var head=el('div','eco-head');
    head.appendChild(el('span','eco-mark','\u25C8'));
    var ht=el('div','eco-htext');
    ht.appendChild(el('h2',null,'The AxonOS ecosystem'));
    ht.appendChild(el('p','eco-sub','The project behind this radar \u2014 its repositories, the people building them, and how they connect. Live from public GitHub.'));
    head.appendChild(ht);host.appendChild(head);

    // owner cards (org profile + members)
    var owners=Object.keys(e.owners);
    var og=el('div','eco-owners');
    owners.forEach(function(k){var o=e.owners[k];
      var card=el('div','eco-owner');
      var row=el('div','eco-orow');
      var oa=el('a','eco-oname');oa.href=safeUrl(o.html_url);oa.target='_blank';oa.rel='noopener';
      oa.appendChild(el('b',null,o.name||o.login));
      var badge=el('span','eco-otype',o.type==='Organization'?'ORG':'USER');oa.appendChild(badge);
      row.appendChild(oa);card.appendChild(row);
      if(o.bio)card.appendChild(el('div','eco-bio',o.bio));
      var meta=el('div','eco-ometa');
      if(o.location){meta.appendChild(el('span','eco-chip','\uD83D\uDCCD '+o.location));}
      if(o.company){meta.appendChild(el('span','eco-chip',o.company));}
      if(o.followers){meta.appendChild(el('span','eco-chip',o.followers+' followers'));}
      if(o.public_repos){meta.appendChild(el('span','eco-chip',o.public_repos+' repos'));}
      if(o.blog){var bl=el('a','eco-chip eco-link','\uD83D\uDD17 site');bl.href=safeUrl(o.blog);bl.target='_blank';bl.rel='noopener';meta.appendChild(bl);}
      if(meta.childNodes.length)card.appendChild(meta);
      if(o.members&&o.members.length){
        var pl=el('div','eco-people');pl.appendChild(el('span','eco-plabel','People'));
        o.members.forEach(function(m){pl.appendChild(ghUser(m.login));});
        card.appendChild(pl);
      }
      og.appendChild(card);
    });
    host.appendChild(og);

    // Cross-repo people: contributors who genuinely span multiple repos.
    // Only real humans reach here (orgs/owner accounts are filtered upstream),
    // so if the list is empty the section is simply omitted — no filler.
    var people=(e.key_people||[]).filter(function(p2){return p2.login&&p2.reach>=2;});
    if(people.length){
      var kp=el('div','eco-block');
      var kh=el('div','eco-bhead');
      kh.appendChild(el('span','eco-blabel','Building across the stack'));
      kh.appendChild(el('span','eco-bhint',people.length+(people.length===1?' person spans':' people span')+' multiple repositories'));
      kp.appendChild(kh);
      var wrap=el('div','eco-kpwrap');
      people.slice(0,12).forEach(function(p2){
        var card=el('a','eco-personcard');
        card.href=safeUrl('https://github.com/'+p2.login);card.target='_blank';card.rel='noopener';
        var av=el('img','eco-av');av.src='https://avatars.githubusercontent.com/'+p2.login+'?s=56';av.alt='';av.width=28;av.height=28;av.loading='lazy';
        card.appendChild(av);
        var meta=el('span','eco-pcmeta');
        meta.appendChild(el('span','eco-pcname',p2.login));
        meta.appendChild(el('span','eco-pcreach',p2.reach+' repositories'));
        card.appendChild(meta);
        card.title=(p2.repos||[]).map(function(r){return r.split('/')[1]||r;}).join(' \u00b7 ');
        wrap.appendChild(card);
      });
      kp.appendChild(wrap);host.appendChild(kp);
    }

    // Shared-maintainer links: only meaningful when a real person maintains
    // both repos. Since owner/org accounts are filtered out of `shared`, a
    // link whose shared list is now empty carries no signal — drop it. If
    // nothing survives, omit the whole section rather than show noise.
    var links=(e.links||[]).filter(function(l){return l.shared&&l.shared.length;});
    if(links.length){
      var lk=el('div','eco-block');
      var lh=el('div','eco-bhead');
      lh.appendChild(el('span','eco-blabel','Shared maintainers'));
      lh.appendChild(el('span','eco-bhint','repositories that share a maintainer'));
      lk.appendChild(lh);
      var lwrap=el('div','eco-linkgrid');
      links.slice(0,8).forEach(function(l){
        var row2=el('div','eco-linkcard');
        var pair=el('div','eco-lpair');
        pair.appendChild(el('span','eco-lrepo',l.a.split('/')[1]||l.a));
        pair.appendChild(el('span','eco-ljoin','\u2194'));
        pair.appendChild(el('span','eco-lrepo',l.b.split('/')[1]||l.b));
        row2.appendChild(pair);
        var who=el('div','eco-lwho');
        who.textContent='via '+l.shared.join(', ');
        row2.appendChild(who);
        lwrap.appendChild(row2);
      });
      lk.appendChild(lwrap);host.appendChild(lk);
    }
  }
  function renderDonate(){
    var host=$('donate');if(!host||!DONATE_DOGE)return;
    host.textContent='';
    var inner=document.createElement('div');inner.className='dg-inner';
    var mark=document.createElement('div');mark.className='dg-mark';mark.textContent='\u0110';inner.appendChild(mark);
    var body=document.createElement('div');body.className='dg-body';
    var h=document.createElement('div');h.className='dg-t';
    h.appendChild(document.createTextNode('Fuel the radar'));
    var pill=document.createElement('span');pill.className='dg-pill';pill.textContent='Dogecoin';h.appendChild(pill);
    body.appendChild(h);
    var tx=document.createElement('div');tx.className='dg-x';
    tx.textContent='Every scan runs every 3 hours \u2014 discovery, enrichment and the new per-project health scoring all burn API budget. The map, stats, health signals and report stay free for everyone, with no paywalled features. A \u0110 1000 tip powers a full refresh-and-rescore cycle for the whole field.';
    body.appendChild(tx);
    var row=document.createElement('div');row.className='dg-row';
    var amt=document.createElement('span');amt.className='dg-amt';amt.textContent='\u0110 1000';row.appendChild(amt);
    var ad=document.createElement('code');ad.className='dg-addr';ad.textContent=DONATE_DOGE;ad.title='Dogecoin address';row.appendChild(ad);
    var btn=document.createElement('button');btn.type='button';btn.className='dg-copy';btn.textContent='Copy';
    btn.addEventListener('click',function(){
      var done=function(){btn.textContent='Copied \u2713';setTimeout(function(){btn.textContent='Copy';},1600);toast('DOGE address copied');};
      if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(DONATE_DOGE).then(done,function(){fallback();});}
      else fallback();
      function fallback(){var ta=document.createElement('textarea');ta.value=DONATE_DOGE;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(ta);}
    });
    row.appendChild(btn);body.appendChild(row);
    var note=document.createElement('span');note.className='dg-note';
    note.textContent='DOGE only \u00b7 a voluntary donation address, not a payment for goods or services.';
    body.appendChild(note);
    inner.appendChild(body);
    host.appendChild(inner);
    host.classList.remove('hidden');
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

  // ── v6.0.1 HTML self-heal ──────────────────────────────────────────────
  // ?v= stamping covers assets; the HTML DOCUMENT itself can still be served
  // stale (mobile session-restore, Pages max-age). The deploy publishes
  // data/build.json and injects <meta name="radar-build"> into every page;
  // on mismatch we navigate ONCE per build per session to ?b=<build> — a
  // document URL the cache has never seen — so a stale shell cannot survive
  // a launch. No meta (dev / pre-6.0.1 build) → do nothing.
  window.__radarNav = window.__radarNav || function(u){try{location.replace(u);}catch(e){}};
  function selfHeal(){
    try{
      var m=document.querySelector('meta[name="radar-build"]');
      if(!m||!m.getAttribute('content'))return;
      var mine=m.getAttribute('content');
      fetch('./data/build.json',{cache:'no-store'}).then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(j){
        var live=j&&typeof j.build==='string'?j.build:'';
        if(!live||live===mine)return;
        var KEY='radar_heal_'+live;
        try{if(sessionStorage.getItem(KEY))return;sessionStorage.setItem(KEY,'1');}catch(e){}
        var q=(location.search||'').replace(/^\?/,'').split('&').filter(function(kv){return kv&&kv.indexOf('b=')!==0;});
        q.push('b='+encodeURIComponent(live));
        window.__radarNav(location.pathname+'?'+q.join('&')+(location.hash||''));
      }).catch(function(){});
    }catch(e){}
  }
  selfHeal();

  function boot(){
    readHash();
    buildSeg('segView',[{v:'grid',l:'☰ Grid'},{v:'radar',l:'◎ Radar'}],function(){return state.view;},function(v){state.view=v;});
    buildSeg('segSort',[{v:'activity',l:'Activity'},{v:'relevance',l:'Relevance'},{v:'health',l:'Health'},{v:'stars',l:'Stars'},{v:'rising',l:'Rising'},{v:'foundation',l:'Foundation'},{v:'new',l:'Newest'},{v:'name',l:'A–Z'}],function(){return state.sort;},function(v){state.sort=v;});
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
    fetch('./data/radar.json',{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){DATA=sanitizeData(j);document.body.classList.remove('loading');buildChips();buildTierChips();buildIopChips();buildLangs();setStats();renderEcosystem();render();}).catch(function(err){console.log('radar data not loaded:',err);document.body.classList.remove('loading');setStats();render();});
    renderDonate();
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
  function heatColor(v,max){
    if(!v)return 'rgba(120,140,160,.06)';
    var t=max>0?v/max:0;                       // 0..1
    // teal ramp: dark → bright AxonOS cyan
    var a=(0.12+t*0.78).toFixed(3);
    return 'rgba(70,208,224,'+a+')';
  }
  function renderMap(){
    var host=$('mapHost');if(!host||host.dataset.done)return;
    var cm=DATA.coverage_matrix,sg=DATA.standards_graph;
    host.textContent='';
    if(!cm&&!sg){var e=document.createElement('p');e.className='map-empty';e.textContent='Ecosystem map data is not available in this snapshot.';host.appendChild(e);return;}

    // ── intro line: what this is and why GitHub can't show it ──
    var intro=document.createElement('p');intro.className='map-intro';
    intro.textContent='The ecosystem as a connected system — not a list you could assemble yourself, but the field\u2019s shape and its connective tissue, computed from evidence and refreshed automatically.';
    host.appendChild(intro);

    // ── Signal-chain coverage matrix ──
    if(cm&&cm.grid&&cm.grid.length){
      var h1=document.createElement('h3');h1.className='map-h';h1.textContent='Signal-chain coverage';host.appendChild(h1);
      var sub=document.createElement('p');sub.className='map-sub';
      sub.textContent='How many projects cover each biosignal \u00d7 pipeline stage. Bright cells are crowded; empty cells are where the ecosystem is thin \u2014 an opening.';
      host.appendChild(sub);
      var max=0;cm.grid.forEach(function(r){r.cells.forEach(function(c){if(c>max)max=c;});});
      var tbl=document.createElement('table');tbl.className='cov';
      var thead=document.createElement('thead');var htr=document.createElement('tr');
      var corner=document.createElement('th');corner.className='cov-corner';corner.textContent='';htr.appendChild(corner);
      cm.stages.forEach(function(s){var th=document.createElement('th');th.textContent=s;htr.appendChild(th);});
      var thT=document.createElement('th');thT.className='cov-tot';thT.textContent='\u03a3';htr.appendChild(thT);
      thead.appendChild(htr);tbl.appendChild(thead);
      var tb=document.createElement('tbody');
      cm.grid.forEach(function(r){
        var tr=document.createElement('tr');
        var rh=document.createElement('th');rh.className='cov-mod';rh.textContent=r.modality;tr.appendChild(rh);
        r.cells.forEach(function(c){
          var td=document.createElement('td');td.className='cov-cell'+(c?'':' cov-zero');
          td.style.background=heatColor(c,max);
          td.textContent=c?String(c):'\u00b7';
          td.title=r.modality+' \u00b7 '+c+' project'+(c===1?'':'s');
          tr.appendChild(td);
        });
        var tt=document.createElement('td');tt.className='cov-tot';tt.textContent=String(r.total);tr.appendChild(tt);
        tb.appendChild(tr);
      });
      // stage totals row
      var ftr=document.createElement('tr');ftr.className='cov-foot';
      var fh=document.createElement('th');fh.className='cov-mod';fh.textContent='\u03a3';ftr.appendChild(fh);
      (cm.stage_totals||[]).forEach(function(n){var td=document.createElement('td');td.className='cov-tot';td.textContent=String(n);ftr.appendChild(td);});
      var blank=document.createElement('td');blank.className='cov-tot';ftr.appendChild(blank);
      tb.appendChild(ftr);
      tbl.appendChild(tb);host.appendChild(tbl);

      // desert callouts — modalities with zero coverage among the canonical set
      var canon=['EEG','ECoG','EMG','fNIRS','MEG','EOG','spikes/LFP'];
      var present={};cm.grid.forEach(function(r){if(r.total>0)present[r.modality]=1;});
      var deserts=canon.filter(function(m){return !present[m];});
      if(deserts.length){
        var dz=document.createElement('p');dz.className='map-desert';
        dz.appendChild(document.createTextNode('Deserts (zero coverage): '));
        var b=document.createElement('b');b.textContent=deserts.join(', ');dz.appendChild(b);
        host.appendChild(dz);
      }
    }

    // ── Standards interoperability graph ──
    if(sg&&sg.standards&&sg.standards.length){
      var h2=document.createElement('h3');h2.className='map-h';h2.textContent='Standards \u0026 interoperability';host.appendChild(h2);
      var sub2=document.createElement('p');sub2.className='map-sub';
      sub2.textContent='The connective tissue: each field standard and the projects that speak it. Two projects sharing a standard can pipe into each other.';
      host.appendChild(sub2);
      var stat=document.createElement('div');stat.className='map-stats';
      function chip(n,l){var d=document.createElement('div');d.className='map-stat';var b=document.createElement('b');b.textContent=String(n);d.appendChild(b);d.appendChild(document.createTextNode(' '+l));return d;}
      stat.appendChild(chip(sg.n_standards,'standards'));
      stat.appendChild(chip(sg.n_repos_with_standards,'projects wired'));
      stat.appendChild(chip(sg.interop_edges,'interop links'));
      host.appendChild(stat);
      var maxc=sg.standards[0]?sg.standards[0].count:1;
      var wrap=document.createElement('div');wrap.className='std-wrap';
      sg.standards.forEach(function(s){
        var row=document.createElement('div');row.className='std-row';
        var head=document.createElement('div');head.className='std-head';
        var nm=document.createElement('span');nm.className='std-name';nm.textContent=s.standard;head.appendChild(nm);
        var ct=document.createElement('span');ct.className='std-count';ct.textContent='\u00d7'+s.count;head.appendChild(ct);
        row.appendChild(head);
        var bar=document.createElement('div');bar.className='std-bar';
        var fill=document.createElement('span');fill.className='std-fill';fill.style.width=(maxc>0?(s.count/maxc*100):0).toFixed(1)+'%';bar.appendChild(fill);
        row.appendChild(bar);
        var reps=document.createElement('div');reps.className='std-repos';
        s.repos.slice(0,10).forEach(function(r){
          var a=document.createElement('a');a.className='std-repo';a.href='https://github.com/'+r;a.target='_blank';a.rel='noopener';a.textContent=r.split('/').pop();reps.appendChild(a);
        });
        if(s.repos.length>10){var more=document.createElement('span');more.className='std-more';more.textContent='+'+(s.repos.length-10);reps.appendChild(more);}
        row.appendChild(reps);
        wrap.appendChild(row);
      });
      host.appendChild(wrap);
    }

    var foot=document.createElement('p');foot.className='map-foot';
    foot.textContent='Each project passes the BCI Relevance Engine (v7): a scored, auditable gate that keeps a repo only when BCI-specific evidence outweighs generic-ML signals. Generic ML \u2014 even ML that says \u201cneural\u201d \u2014 is filtered out.';
    host.appendChild(foot);
    host.dataset.done='1';
  }
  function switchView(v){
    ['projects','builders','methodology','axonos','map'].forEach(function(name){var el=$('view-'+name);if(el)el.hidden=(name!==v);});
    var tabs=document.querySelectorAll('#tabs .tab');
    for(var i=0;i<tabs.length;i++){tabs[i].classList.toggle('on',tabs[i].getAttribute('data-view')===v);}
    if(v==='builders')renderBuilders();
    if(v==='map')renderMap();
    try{location.hash=v==='projects'?'':('#'+v);}catch(e){}
  }
  function stageRank(c){var s=c.querySelector('.ax-stage');var o=['shipped','beta','alpha','design','planned'];for(var i=0;i<o.length;i++){if(s&&s.classList.contains('st-'+o[i]))return i;}return 9;}
  function orderAxCards(){var g=document.querySelector('#view-axonos .ax-grid');if(!g)return;var cs=Array.prototype.slice.call(g.querySelectorAll('.ax-card'));cs.sort(function(a,b){return stageRank(a)-stageRank(b);});cs.forEach(function(c){g.appendChild(c);});}
  function renderAxProgress(){var host=$('axProgress');if(!host)return;var cards=document.querySelectorAll('#view-axonos .ax-card');if(!cards.length)return;var o=['shipped','beta','alpha','design','planned'],cnt={};o.forEach(function(k){cnt[k]=0;});for(var i=0;i<cards.length;i++){var st=cards[i].querySelector('.ax-stage');if(st)for(var j=0;j<o.length;j++){if(st.classList.contains('st-'+o[j])){cnt[o[j]]++;break;}}}var total=cards.length,build=cnt.beta+cnt.alpha+cnt.design;host.textContent='';var bar=document.createElement('div');bar.className='ax-bar';o.forEach(function(k){if(!cnt[k])return;var sg=document.createElement('span');sg.className='ax-seg seg-'+k;sg.style.width=(cnt[k]/total*100).toFixed(2)+'%';bar.appendChild(sg);});host.appendChild(bar);var tx=document.createElement('div');tx.className='ax-prog-txt';function bpart(n,label){var b=document.createElement('b');b.textContent=String(n);tx.appendChild(b);tx.appendChild(document.createTextNode(label));}bpart(cnt.shipped,' shipped \u00b7 ');bpart(build,' in build \u00b7 ');bpart(cnt.planned,' planned ');var cl=document.createElement('span');cl.className='ax-climb';cl.textContent='\u2014 and climbing \u2197';tx.appendChild(cl);host.appendChild(tx);}
  function downloadData(){try{var blob=new Blob([JSON.stringify(DATA,null,2)],{type:'application/json'});var u=URL.createObjectURL(blob);var a=document.createElement('a');a.href=u;a.download='axonos-radar.json';document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(u);},1000);}catch(e){}}
  (function(){var tabs=document.querySelectorAll('#tabs .tab');
    for(var i=0;i<tabs.length;i++){tabs[i].addEventListener('click',function(){switchView(this.getAttribute('data-view'));});}
    function applyHash(){var h=(location.hash||'').replace('#','');
      if(h==='builders'||h==='methodology'||h==='axonos'||h==='map')switchView(h);}
    applyHash();
    window.addEventListener('hashchange',applyHash);
    orderAxCards();renderAxProgress();var dl=document.getElementById('dlBtn');if(dl)dl.addEventListener('click',downloadData);
  })();

})();
(function(){var b=document.getElementById('dogeCopy');if(!b)return;
  b.addEventListener('click',function(){var a=document.getElementById('dogeAddr');var t=a?(a.textContent||'').trim():'';
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){b.textContent='Copied \u2713';setTimeout(function(){b.textContent='Copy';},1600);},function(){b.textContent='Copy failed';});}
    else{try{var r=document.createRange();r.selectNodeContents(a);var s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy');s.removeAllRanges();b.textContent='Copied \u2713';setTimeout(function(){b.textContent='Copy';},1600);}catch(e){b.textContent='Select & copy';}}
  });})();
