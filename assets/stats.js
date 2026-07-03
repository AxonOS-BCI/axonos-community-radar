(function(){
  "use strict";
  function $(id){return document.getElementById(id);}
  function safeUrl(u){u=String(u||'');return /^https:\/\/github\.com\//.test(u)?u:'#';}
  function k(n){n=n||0;return n>=1000?(n/1000).toFixed(n>=10000?0:1)+'k':String(n);}
  function el(tag,cls,txt){var e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;}
  var SVGNS='http://www.w3.org/2000/svg';
  function svgEl(tag,attrs){var e=document.createElementNS(SVGNS,tag);for(var a in attrs)e.setAttribute(a,attrs[a]);return e;}
  var CAT_COLORS=['#2dd4ff','#a78bfa','#34d399','#fbbf24','#fb7185','#60a5fa','#f472b6','#22d3ee','#a3e635','#fb923c','#94a3b8'];
  function catColor(i){return CAT_COLORS[i%CAT_COLORS.length];}
  var TIER={L3_EXPLICIT_BCI:['L3','#34d399','Explicit BCI / brain-computer-interface topic'],
            L2_NEURAL_SIGNAL:['L2','#2dd4ff','Neural-signal topic or keyword (EEG, ECoG, …)'],
            L1_CONTEXT_PLUS_NEURO:['L1','#a78bfa','Context topic plus an anchored neuro keyword'],
            L0_WEAK_ADJACENT:['L0','#fb7185','Weak adjacency — flagged for review']};
  var TIER_ORDER=['L3_EXPLICIT_BCI','L2_NEURAL_SIGNAL','L1_CONTEXT_PLUS_NEURO','L0_WEAK_ADJACENT'];

  var DATA={projects:[],builders:[],counts:{},generated_at:null};
  var HIST={snapshots:[]};
  var WEEK=null;

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
    var host=$('metrics');host.textContent='';
    cells.forEach(function(x){var d=el('div','metric '+x[0]);d.appendChild(el('b',null,String(x[1])));d.appendChild(el('span',null,x[2]));host.appendChild(d);});
    var u=$('updated');u.textContent='';
    if(DATA.generated_at){var d2=new Date(DATA.generated_at);
      u.appendChild(document.createTextNode('Updated '+d2.toUTCString().replace('GMT','UTC')+' \u00b7 refreshes every 3h \u00b7 '));
      var r=el('a',null,'RSS');r.href='./feed.xml';u.appendChild(r);
      u.appendChild(document.createTextNode(' \u00b7 '));
      var m=el('a',null,'open the map \u2192');m.href='./';u.appendChild(m);}
    else u.textContent='Warming up \u2014 first scan runs on publish.';
    renderWeekLine();
  }

  function dp(d){var sp=el('span','dp '+(d>0?'up':(d<0?'down':'flat')),d>0?('+'+d):(d<0?('\u2212'+Math.abs(d)):'\u00b10'));return sp;}
  function renderWeekLine(){
    var host=$('wkline');if(!host)return;host.textContent='';
    if(!WEEK||!WEEK.delta){host.classList.add('hidden');return;}
    host.classList.remove('hidden');
    host.appendChild(el('span','wk-t','This week'));
    [['Projects','total'],['Stars','total_stars'],['Active','active_30d'],['Rising','rising']].forEach(function(x){
      var d=el('span','wk-d');d.appendChild(el('b',null,String((WEEK.now&&WEEK.now[x[1]])||0)));
      d.appendChild(document.createTextNode(' '+x[0]+' '));d.appendChild(dp(WEEK.delta[x[1]]|0));host.appendChild(d);});
  }

  function drawGrowth(){
    var snaps=(HIST.snapshots||[]).slice().sort(function(a,b){return String(a.snapshot_at).localeCompare(String(b.snapshot_at));});
    var svg=$('growth'),W=960,H=280,PADL=8,PADR=8,PADT=18,PADB=22;
    var note=$('growthNote');
    while(svg.firstChild)svg.removeChild(svg.firstChild);
    if(!snaps.length){note.textContent='no history yet';return;}
    var pts=snaps.map(function(s){var m=snapMeta(s);return {t:s.snapshot_at,proj:m.total||0,stars:m.total_stars||0};});
    note.textContent=pts.length===1?'1 snapshot \u2014 the curve fills in every 3h':pts.length+' snapshots \u00b7 '+new Date(pts[0].t).toLocaleDateString()+' \u2192 '+new Date(pts[pts.length-1].t).toLocaleDateString();
    var n=pts.length;
    function xs(i){return n===1?W/2:PADL+(W-PADL-PADR)*i/(n-1);}
    function maxOf(key){var mx=0;pts.forEach(function(p){if(p[key]>mx)mx=p[key];});return mx||1;}
    function ys(v,mx){return PADT+(H-PADT-PADB)*(1-v/mx);}
    for(var g=0;g<=3;g++){var gy=(PADT+(H-PADT-PADB)*g/3).toFixed(1);
      svg.appendChild(svgEl('line',{x1:0,y1:gy,x2:W,y2:gy,stroke:'rgba(255,255,255,.05)','stroke-width':1}));}
    function series(key,color,mx,fill){
      if(fill){var a='M'+xs(0).toFixed(1)+' '+(H-PADB)+' ';
        pts.forEach(function(p,i){a+='L'+xs(i).toFixed(1)+' '+ys(p[key],mx).toFixed(1)+' ';});
        a+='L'+xs(n-1).toFixed(1)+' '+(H-PADB)+' Z';
        svg.appendChild(svgEl('path',{d:a,fill:color,opacity:'0.08'}));}
      var d='';pts.forEach(function(p,i){d+=(i?'L':'M')+xs(i).toFixed(1)+' '+ys(p[key],mx).toFixed(1)+' ';});
      svg.appendChild(svgEl('path',{d:d.trim(),fill:'none',stroke:color,'stroke-width':2.5,'stroke-linejoin':'round','stroke-linecap':'round'}));
      pts.forEach(function(p,i){svg.appendChild(svgEl('circle',{cx:xs(i).toFixed(1),cy:ys(p[key],mx).toFixed(1),r:(n===1?4:3),fill:color}));});
    }
    series('stars','#fbbf24',maxOf('stars'),true);
    series('proj','#2dd4ff',maxOf('proj'),true);
  }

  function drawMomentum(){
    var host=$('momentum');if(!host)return;
    var snaps=(HIST.snapshots||[]).filter(function(s){return s.meta&&s.meta.rising!=null;})
      .sort(function(a,b){return String(a.snapshot_at).localeCompare(String(b.snapshot_at));});
    var note=$('momentumNote');
    while(host.firstChild)host.removeChild(host.firstChild);
    if(snaps.length<2){if(note)note.textContent='needs a couple of snapshots \u2014 filling in every 3h';return;}
    var pts=snaps.map(function(s){return {t:s.snapshot_at,up:s.meta.rising|0,down:(s.meta.falling|0)};});
    if(note)note.textContent='projects rising vs falling per snapshot \u00b7 '+pts.length+' snapshots';
    var W=960,H=180,PADL=8,PADR=8,PADT=14,PADB=18,n=pts.length;
    var mx=1;pts.forEach(function(p){mx=Math.max(mx,p.up,p.down);});
    function xs(i){return PADL+(W-PADL-PADR)*i/(n-1);}
    function ys(v){return PADT+(H-PADT-PADB)*(1-v/mx);}
    for(var g=0;g<=2;g++){var gy=(PADT+(H-PADT-PADB)*g/2).toFixed(1);
      host.appendChild(svgEl('line',{x1:0,y1:gy,x2:W,y2:gy,stroke:'rgba(255,255,255,.05)','stroke-width':1}));}
    [['up','#3fd68f'],['down','#ff6b8a']].forEach(function(sr){
      var d='';pts.forEach(function(p,i){d+=(i?'L':'M')+xs(i).toFixed(1)+' '+ys(p[sr[0]]).toFixed(1)+' ';});
      host.appendChild(svgEl('path',{d:d.trim(),fill:'none',stroke:sr[1],'stroke-width':2.5,'stroke-linejoin':'round','stroke-linecap':'round'}));
      pts.forEach(function(p,i){host.appendChild(svgEl('circle',{cx:xs(i).toFixed(1),cy:ys(p[sr[0]]).toFixed(1),r:3,fill:sr[1]}));});
    });
  }

  function muted(elh,txt){elh.textContent='';elh.appendChild(el('div','muted',txt));}
  function bars(elId,rows){
    var host=$(elId);if(!rows.length){muted(host,'No data yet.');return;}
    var mx=rows.reduce(function(m,r){return Math.max(m,r.v);},0)||1;
    host.textContent='';
    rows.forEach(function(r){var pct=Math.max(3,Math.round(r.v/mx*100));
      var row=el('div','bar-row');row.appendChild(el('span','lab',r.l));
      var tr=el('div','bar-track');var fl=el('div','bar-fill');fl.style.width=pct+'%';fl.style.background=r.c;tr.appendChild(fl);row.appendChild(tr);
      row.appendChild(el('span','val',String(r.v)));host.appendChild(row);});
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
    var host=$('tiers');host.textContent='';
    var any=false;
    TIER_ORDER.forEach(function(t){var n=counts[t];if(!n)return;any=true;
      var e=TIER[t],pct=Math.round(n/total*100),cls='tl'+e[0].slice(1);
      var row=el('div','tier');row.appendChild(el('span','tag '+cls,e[0]));
      row.appendChild(el('span','desc',e[2]));
      var nn=el('span','n '+cls,n+' ');var sm=el('small','pct',pct+'%');nn.appendChild(sm);row.appendChild(nn);
      host.appendChild(row);});
    if(!any)muted(host,'No evidence tiers in this dataset.');
  }
  function setBuilders(){
    var b=(DATA.builders||[]).slice(0,8);var host=$('builders');
    if(!b.length){muted(host,'No multi-project builders yet.');return;}
    host.textContent='';
    b.forEach(function(x,i){
      var cats=(x.top_categories||[]).slice(0,2).join(' \u00b7 ');
      var a=el('a','lrow');a.href=safeUrl(x.html_url);a.target='_blank';a.rel='noopener';
      a.appendChild(el('span','rk',String(i+1)));
      var who=el('span','who');var bo=el('b',null,String(x.owner||''));who.appendChild(bo);
      if(x.owner_type){who.appendChild(el('span','ob',x.owner_type==='Organization'?'ORG':'USER'));}
      who.appendChild(el('small',null,(x.project_count||0)+' projects'+(cats?' \u00b7 '+cats:'')+((x.followers|0)>0?(' \u00b7 '+k(x.followers)+' followers'):'')));
      a.appendChild(who);
      var mx=el('span','mx');mx.appendChild(el('b',null,k(x.total_stars||0)));
      mx.appendChild(document.createTextNode(' \u2605 \u00b7 '+(x.active_projects_30d||0)+' active'));
      a.appendChild(mx);host.appendChild(a);});
  }
  function setLangs(){
    var counts={};DATA.projects.forEach(function(p){if(p.language)counts[p.language]=(counts[p.language]||0)+1;});
    var rows=Object.keys(counts).map(function(c){return {l:c,v:counts[c]};}).sort(function(a,b){return b.v-a.v;}).slice(0,8);
    rows.forEach(function(r,i){r.c=catColor(i+2);});
    bars('langs',rows);
  }
  function setRising(){
    var r=DATA.projects.filter(function(p){return p.rising;}).sort(function(a,b){return (b.stars_delta_7d||0)-(a.stars_delta_7d||0);}).slice(0,8);
    var host=$('rising');
    if(!r.length){muted(host,'Nothing rising yet \u2014 velocity needs a few days of history to accumulate.');return;}
    host.textContent='';
    r.forEach(function(p){var li=el('div','li');
      li.appendChild(el('span','rise','\u2191 +'+(p.stars_delta_7d||0)+'/7d'));
      var a=el('a',null,String(p.full_name||''));a.href=safeUrl(p.html_url);a.target='_blank';a.rel='noopener';li.appendChild(a);
      li.appendChild(el('span','st','\u2605 '+(p.stars||0)));host.appendChild(li);});
  }

  function renderAll(){setMetrics();drawGrowth();drawMomentum();setCats();setTiers();setBuilders();setLangs();setRising();}

  function load(url){return fetch(url,{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).catch(function(){return null;});}
  renderAll();
  if(window.__RADAR_DATA__){DATA=window.__RADAR_DATA__;}
  if(window.__RADAR_HISTORY__){HIST=window.__RADAR_HISTORY__;}
  if(window.__RADAR_DATA__||window.__RADAR_HISTORY__){renderAll();}
  else Promise.all([load('./data/radar.json'),load('./data/history.json'),load('./data/weekly.json')]).then(function(res){
    if(res[0])DATA=res[0]; if(res[1])HIST=res[1]; if(res[2])WEEK=res[2];
    if(!DATA.projects)DATA.projects=[];
    renderAll();
  });
  window.addEventListener('resize',function(){drawGrowth();drawMomentum();});
})();
