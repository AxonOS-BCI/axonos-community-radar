(function(){
  "use strict";
  function $(id){return document.getElementById(id);}
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function safeUrl(u){u=String(u||'');return /^https:\/\/github\.com\//.test(u)?u:'#';}
  function k(n){n=n||0;return n>=1000?(n/1000).toFixed(n>=10000?0:1)+'k':String(n);}
  var CAT_COLORS=['#2dd4ff','#a78bfa','#34d399','#fbbf24','#fb7185','#60a5fa','#f472b6','#22d3ee','#a3e635','#fb923c','#94a3b8'];
  function catColor(i){return CAT_COLORS[i%CAT_COLORS.length];}
  var TIER={L3_EXPLICIT_BCI:['L3','#34d399','Explicit BCI / brain-computer-interface topic'],
            L2_NEURAL_SIGNAL:['L2','#2dd4ff','Neural-signal topic or keyword (EEG, ECoG, …)'],
            L1_CONTEXT_PLUS_NEURO:['L1','#a78bfa','Context topic plus an anchored neuro keyword'],
            L0_WEAK_ADJACENT:['L0','#fb7185','Weak adjacency — flagged for review']};
  var TIER_ORDER=['L3_EXPLICIT_BCI','L2_NEURAL_SIGNAL','L1_CONTEXT_PLUS_NEURO','L0_WEAK_ADJACENT'];

  var DATA={projects:[],builders:[],counts:{},generated_at:null};
  var HIST={snapshots:[]};

  function snapMeta(s){
    if(s.meta)return s.meta;
    var stars=s.stars||{},tot=Object.keys(stars).length,sum=0;
    for(var kk in stars)sum+=stars[kk]||0;
    return {total:tot,total_stars:sum,active_30d:null,new:null,rising:null};
  }

  function setMetrics(){
    var p=DATA.projects,c=DATA.counts||{};
    var tot=c.total||p.length;
    var stars=p.reduce(function(s,x){return s+(x.stars||0);},0);
    var active=c.active_30d!=null?c.active_30d:p.filter(function(x){return x.active;}).length;
    var nw=c.new!=null?c.new:p.filter(function(x){return x.is_new;}).length;
    var rising=c.rising!=null?c.rising:p.filter(function(x){return x.rising;}).length;
    var builders=(DATA.builders&&DATA.builders.length)||c.builders||0;
    var cells=[['m1',tot,'Projects'],['m2',k(stars),'Total stars'],['m3',active,'Active 30d'],
               ['m4',nw,'New this week'],['m5',rising,'Rising'],['m6',builders,'Builders']];
    $('metrics').innerHTML=cells.map(function(x){return '<div class="metric '+x[0]+'"><b>'+x[1]+'</b><span>'+x[2]+'</span></div>';}).join('');
    var u=$('updated');
    if(DATA.generated_at){var d=new Date(DATA.generated_at);u.innerHTML='Updated '+d.toUTCString().replace('GMT','UTC')+' · refreshes every 6h · <a href="./feed.xml">RSS</a> · <a href="./">open the map →</a>';}
    else u.textContent='Warming up — first scan runs on publish.';
  }

  function drawGrowth(){
    var snaps=(HIST.snapshots||[]).slice().sort(function(a,b){return String(a.snapshot_at).localeCompare(String(b.snapshot_at));});
    var svg=$('growth'),W=960,H=280,PADL=8,PADR=8,PADT=18,PADB=22;
    var note=$('growthNote');
    if(!snaps.length){svg.innerHTML='';note.textContent='no history yet';return;}
    var pts=snaps.map(function(s){var m=snapMeta(s);return {t:s.snapshot_at,proj:m.total||0,stars:m.total_stars||0};});
    note.textContent=pts.length===1?'1 snapshot — the curve fills in every 6h':pts.length+' snapshots · '+new Date(pts[0].t).toLocaleDateString()+' → '+new Date(pts[pts.length-1].t).toLocaleDateString();
    var n=pts.length;
    function xs(i){return n===1?W/2:PADL+(W-PADL-PADR)*i/(n-1);}
    function maxOf(key){var mx=0;pts.forEach(function(p){if(p[key]>mx)mx=p[key];});return mx||1;}
    function ys(v,mx){return PADT+(H-PADT-PADB)*(1-v/mx);}
    function series(key,color,mx,fill){
      var d='',a='';
      pts.forEach(function(p,i){var X=xs(i),Y=ys(p[key],mx);d+=(i?'L':'M')+X.toFixed(1)+' '+Y.toFixed(1)+' ';});
      var dots=pts.map(function(p,i){return '<circle cx="'+xs(i).toFixed(1)+'" cy="'+ys(p[key],mx).toFixed(1)+'" r="'+(n===1?4:3)+'" fill="'+color+'"/>';}).join('');
      var area='';
      if(fill){a='M'+xs(0).toFixed(1)+' '+(H-PADB)+' ';pts.forEach(function(p,i){a+='L'+xs(i).toFixed(1)+' '+ys(p[key],mx).toFixed(1)+' ';});a+='L'+xs(n-1).toFixed(1)+' '+(H-PADB)+' Z';
        area='<path d="'+a+'" fill="'+color+'" opacity="0.08"/>';}
      return area+'<path d="'+d.trim()+'" fill="none" stroke="'+color+'" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'+dots;
    }
    var mxP=maxOf('proj'),mxS=maxOf('stars');
    var grid='';
    for(var g=0;g<=3;g++){var gy=(PADT+(H-PADT-PADB)*g/3).toFixed(1);grid+='<line x1="0" y1="'+gy+'" x2="'+W+'" y2="'+gy+'" stroke="rgba(255,255,255,.05)" stroke-width="1"/>';}
    svg.innerHTML=grid+series('stars','#fbbf24',mxS,true)+series('proj','#2dd4ff',mxP,true);
  }

  function bars(elId,rows){
    var el=$(elId);if(!rows.length){el.innerHTML='<div class="muted">No data yet.</div>';return;}
    var mx=rows.reduce(function(m,r){return Math.max(m,r.v);},0)||1;
    el.innerHTML=rows.map(function(r){var pct=Math.max(3,Math.round(r.v/mx*100));
      return '<div class="bar-row"><span class="lab">'+esc(r.l)+'</span><div class="bar-track"><div class="bar-fill" data-w="'+pct+'" data-c="'+esc(r.c)+'"></div></div><span class="val">'+r.v+'</span></div>';}).join('');
    var fills=el.querySelectorAll('.bar-fill');for(var i=0;i<fills.length;i++){fills[i].style.width=fills[i].getAttribute('data-w')+'%';fills[i].style.background=fills[i].getAttribute('data-c');}
  }

  function setCats(){
    var counts={};DATA.projects.forEach(function(p){var c=p.category||'Other';counts[c]=(counts[c]||0)+1;});
    var rows=Object.keys(counts).map(function(c){return {l:c,v:counts[c]};}).sort(function(a,b){return b.v-a.v;});
    rows.forEach(function(r,i){r.c=catColor(i);});
    bars('cats',rows);
  }
  function setTiers(){
    var counts={};DATA.projects.forEach(function(p){if(p.evidence_tier)counts[p.evidence_tier]=(counts[p.evidence_tier]||0)+1;});
    var total=DATA.projects.length||1;var have=Object.keys(counts).length;
    $('tierNote').textContent=have?'why each project qualifies':'enable v3 data';
    var el=$('tiers');
    el.innerHTML=TIER_ORDER.filter(function(t){return counts[t];}).map(function(t){var e=TIER[t],n=counts[t];
      var pct=Math.round(n/total*100);
      var cls='tl'+e[0].slice(1);
      return '<div class="tier"><span class="tag '+cls+'">'+e[0]+'</span>'
        +'<span class="desc">'+esc(e[2])+'</span><span class="n '+cls+'">'+n+' <small class="pct">'+pct+'%</small></span></div>';}).join('')
      || '<div class="muted">No evidence tiers in this dataset.</div>';
  }
  function setBuilders(){
    var b=(DATA.builders||[]).slice(0,8);var el=$('builders');
    if(!b.length){el.innerHTML='<div class="muted">No multi-project builders yet.</div>';return;}
    el.innerHTML=b.map(function(x,i){
      var cats=(x.top_categories||[]).slice(0,2).join(' · ');
      return '<a class="lrow" href="'+esc(safeUrl(x.html_url))+'" target="_blank" rel="noopener">'
        +'<span class="rk">'+(i+1)+'</span>'
        +'<span class="who"><b>'+esc(x.owner)+'</b><small>'+x.project_count+' projects'+(cats?' · '+esc(cats):'')+'</small></span>'
        +'<span class="mx"><b>'+k(x.total_stars||0)+'</b> ★ · '+(x.active_projects_30d||0)+' active</span></a>';}).join('');
  }
  function setLangs(){
    var counts={};DATA.projects.forEach(function(p){if(p.language)counts[p.language]=(counts[p.language]||0)+1;});
    var rows=Object.keys(counts).map(function(c){return {l:c,v:counts[c]};}).sort(function(a,b){return b.v-a.v;}).slice(0,8);
    rows.forEach(function(r,i){r.c=catColor(i+2);});
    bars('langs',rows);
  }
  function setRising(){
    var r=DATA.projects.filter(function(p){return p.rising;}).sort(function(a,b){return (b.stars_delta_7d||0)-(a.stars_delta_7d||0);}).slice(0,8);
    var el=$('rising');
    if(!r.length){el.innerHTML='<div class="muted">Nothing rising yet — velocity needs a few days of history to accumulate.</div>';return;}
    el.innerHTML=r.map(function(p){return '<div class="li"><span class="rise">↑ +'+(p.stars_delta_7d||0)+'/7d</span>'
      +'<a href="'+esc(safeUrl(p.html_url))+'" target="_blank" rel="noopener">'+esc(p.full_name)+'</a>'
      +'<span class="st">★ '+(p.stars||0)+'</span></div>';}).join('');
  }

  function renderAll(){setMetrics();drawGrowth();setCats();setTiers();setBuilders();setLangs();setRising();}

  function load(url){return fetch(url,{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).catch(function(){return null;});}
  renderAll();
  if(window.__RADAR_DATA__){DATA=window.__RADAR_DATA__;}
  if(window.__RADAR_HISTORY__){HIST=window.__RADAR_HISTORY__;}
  if(window.__RADAR_DATA__||window.__RADAR_HISTORY__){renderAll();}
  else Promise.all([load('./data/radar.json'),load('./data/history.json')]).then(function(res){
    if(res[0])DATA=res[0]; if(res[1])HIST=res[1];
    if(!DATA.projects)DATA.projects=[];
    renderAll();
  });
  window.addEventListener('resize',function(){drawGrowth();});
})();
