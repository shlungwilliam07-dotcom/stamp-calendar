const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();
for(const n of [180,192,512]){const p=await b.newPage({viewport:{width:n,height:n}});
await p.setContent(`<body style="margin:0;background:#fff"><svg width="${n}" height="${n}" viewBox="0 0 100 100"><rect width="100" height="100" fill="#fff"/>
<g transform="rotate(-8 50 50)"><circle cx="50" cy="50" r="30" fill="none" stroke="#c8281e" stroke-width="4"/><circle cx="50" cy="50" r="24.5" fill="none" stroke="#c8281e" stroke-width="1.2"/>
<circle cx="42.5" cy="44" r="2.8" fill="#c8281e"/><circle cx="57.5" cy="44" r="2.8" fill="#c8281e"/><path d="M39 53 Q50 64 61 53" fill="none" stroke="#c8281e" stroke-width="3.2" stroke-linecap="round"/></g></svg></body>`);
await p.screenshot({path:path.join(__dirname,'..','docs','icon-'+n+'.png')});await p.close()}
await b.close()})();
