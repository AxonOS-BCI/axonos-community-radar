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

  // ── v8.1 "Dashboards": the field's shape, from the engine's own output ──
  // Everything here is computed from data the radar already publishes
  // (coverage_matrix, standards_graph, brs, signals) — no new inputs, no
  // hand-entered figures.
  function heat(v,max){                    // viridis-ish ramp, dark → bright
    if(!v)return 'rgba(120,140,160,.07)';
    var t=Math.min(1,v/(max||1));
    var s=[[38,20,72],[45,90,140],[35,160,140],[130,200,80],[250,230,60]];
    var i=Math.min(s.length-2,Math.floor(t*(s.length-1))),f=t*(s.length-1)-i;
    var c=s[i].map(function(x,j){return Math.round(x+(s[i+1][j]-x)*f);});
    return 'rgb('+c[0]+','+c[1]+','+c[2]+')';
  }
  function drawCoverage(){
    var host=$('coverage'); if(!host)return;
    var cm=DATA.coverage_matrix;
    if(!cm||!cm.grid||!cm.grid.length){muted(host,'Coverage matrix appears once the engine publishes a v7+ payload.');$('covNote')&&($('covNote').textContent='');return;}
    var stages=cm.stages||[],grid=cm.grid;
    var max=0;grid.forEach(function(r){(r.cells||[]).forEach(function(c){if(c>max)max=c;});});
    var deserts=0;
    host.textContent='';
    host.style.setProperty('--cols',String(stages.length));
    host.appendChild(el('div','cov-c cov-h',''));           // corner
    stages.forEach(function(s){host.appendChild(el('div','cov-c cov-h',s));});
    grid.forEach(function(row){
      host.appendChild(el('div','cov-c cov-m',row.modality));
      (row.cells||[]).forEach(function(v,i){
        var c=el('div','cov-c cov-v'+(v?'':' cov-0'),v?String(v):'·');
        c.style.background=heat(v,max);
        if(v>max*0.55)c.style.color='#08131a';
        c.title=row.modality+' · '+(stages[i]||'')+': '+(v||0)+' project'+(v===1?'':'s')+(v?'':' — an opening');
        if(!v)deserts++;
        host.appendChild(c);
      });
    });
    var n=$('covNote'); if(n)n.textContent=deserts+' empty cells — where the field is thin, and open';
  }
  function drawBrs(){
    var svg=$('brs'); if(!svg)return;
    var vals=DATA.projects.map(function(p){return p.brs;}).filter(function(v){return typeof v==='number';});
    var note=$('brsNote');
    if(!vals.length){svg.textContent='';if(note)note.textContent='Appears once the engine publishes scored projects.';return;}
    var lo=40,hi=100,bins=10,step=(hi-lo)/bins,cnt=new Array(bins).fill(0);
    vals.forEach(function(v){var i=Math.min(bins-1,Math.max(0,Math.floor((v-lo)/step)));cnt[i]++;});
    var maxc=Math.max.apply(null,cnt)||1,W=960,H=200,pad=26,bw=(W-pad*2)/bins;
    svg.textContent='';
    cnt.forEach(function(c,i){
      var h=Math.round((H-pad*2)*(c/maxc)),x=pad+i*bw,y=H-pad-h;
      svg.appendChild(svgEl('rect',{x:x+2,y:y,width:bw-4,height:Math.max(h,c?2:0),rx:3,fill:'#2dd4ff','fill-opacity':'.85'}));
      if(c){var t=svgEl('text',{x:x+bw/2,y:y-5,'text-anchor':'middle',fill:'#8a97a6','font-size':'11'});t.textContent=String(c);svg.appendChild(t);}
      var lb=svgEl('text',{x:x+bw/2,y:H-8,'text-anchor':'middle',fill:'#8a97a6','font-size':'10'});
      lb.textContent=String(Math.round(lo+i*step));svg.appendChild(lb);
    });
    var mean=vals.reduce(function(a,b){return a+b;},0)/vals.length;
    var mx=pad+((mean-lo)/(hi-lo))*(W-pad*2);
    svg.appendChild(svgEl('line',{x1:mx,y1:pad-8,x2:mx,y2:H-pad,stroke:'#fbbf24','stroke-width':'1.5','stroke-dasharray':'5 4'}));
    var mt=svgEl('text',{x:mx+6,y:pad-1,fill:'#fbbf24','font-size':'11'});mt.textContent='mean '+mean.toFixed(0);svg.appendChild(mt);
    if(note)note.textContent='BRS 0\u2013100 \u00b7 gate at 40 \u00b7 '+vals.length+' scored projects';
  }
  function hbars(host,rows,note,noteTxt,empty){
    if(!host)return;
    if(!rows.length){muted(host,empty);if(note)note.textContent='';return;}
    var max=Math.max.apply(null,rows.map(function(r){return r.v;}))||1;
    host.textContent='';
    rows.forEach(function(r){
      var row=el('div','hb');
      row.appendChild(el('span','hb-l',r.l));
      var track=el('div','hb-t'),fill=el('div','hb-f');
      fill.style.width=Math.max(2,Math.round(r.v/max*100))+'%';
      if(r.c)fill.style.background=r.c;
      track.appendChild(fill);row.appendChild(track);
      row.appendChild(el('span','hb-v',String(r.v)));
      if(r.t)row.title=r.t;
      host.appendChild(row);
    });
    if(note)note.textContent=noteTxt;
  }
  function drawStandards(){
    var sg=DATA.standards_graph;
    var rows=(sg&&sg.standards?sg.standards:[]).slice(0,8).map(function(s){
      return {l:s.standard,v:s.count,c:'#a78bfa',t:s.count+' project'+(s.count===1?'':'s')+' speak '+s.standard};});
    hbars($('standards'),rows,$('stdNote'),
      (sg?((sg.n_standards||0)+' standards \u00b7 '+(sg.n_repos_with_standards||0)+' projects wired \u00b7 '+(sg.interop_edges||0)+' interop links'):''),
      'Standards graph appears once the engine publishes a v7+ payload.');
  }
  function drawHealth(){
    var hv=DATA.projects.map(function(p){return p.signals&&typeof p.signals.overall==='number'?p.signals.overall:null;})
                        .filter(function(v){return v!==null;});
    var bandsDef=[[80,101,'Strong','#34d399'],[60,80,'Solid','#2dd4ff'],[40,60,'Developing','#fbbf24'],[0,40,'Early','#fb7185']];
    var rows=bandsDef.map(function(b){
      var n=hv.filter(function(v){return v>=b[0]&&v<b[1];}).length;
      return {l:b[2]+' \u00b7 '+b[0]+'\u2013'+(b[1]>100?100:b[1]-1),v:n,c:b[3],
              t:n+' project'+(n===1?'':'s')+' scored '+b[0]+'\u2013'+(b[1]>100?100:b[1]-1)};});
    var med=hv.length?hv.slice().sort(function(a,b){return a-b;})[Math.floor(hv.length/2)]:0;
    hbars($('health'),rows,$('healthNote'),'median health '+med+' \u00b7 a triage signal, never a verdict',
      'Health bands appear once the engine publishes signals.');
  }

  function renderAll(){setMetrics();drawCoverage();drawBrs();drawStandards();drawHealth();drawGrowth();drawMomentum();setCats();setTiers();setBuilders();setLangs();setRising();}

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
