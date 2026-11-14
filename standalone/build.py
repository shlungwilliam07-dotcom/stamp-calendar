import os,shutil,json
here=os.path.dirname(os.path.abspath(__file__)); src=open(os.path.join(here,'..','index.html'),encoding='utf-8').read()
def r(a,b):
    global src
    assert src.count(a)==1,a; src=src.replace(a,b)
FB='10.12.2'
r('<meta name="viewport" content="width=device-width, initial-scale=1">','''<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="印章行事曆">
<meta name="theme-color" content="#ffffff">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">''')
r('</style>','''header{padding-top:calc(18px + env(safe-area-inset-top))}
nav{padding-bottom:env(safe-area-inset-bottom)}
#sheet .panel{padding-bottom:calc(26px + env(safe-area-inset-bottom))}
#sheet .panel.full{padding-top:calc(12px + env(safe-area-inset-top))}
#gate{position:fixed;inset:0;z-index:50;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;padding:32px;text-align:center}
#gate[hidden],#gate [hidden]{display:none}
#gate img{width:96px;height:96px;border-radius:22px;border:1px solid var(--line)}
#gate h2{font-family:var(--display);font-weight:500;font-size:24px;margin:0;letter-spacing:.06em}
#gate p{margin:0;color:var(--muted);font-size:14px;max-width:280px}
#gate .btn{max-width:280px}
html,body{overscroll-behavior:none;-webkit-user-select:none;user-select:none}
input,textarea{-webkit-user-select:text;user-select:text}
</style>''')
r('<div id="toast" role="status"></div>','''<div id="toast" role="status"></div>
<div id="gate" hidden><img src="icon-192.png" alt=""><h2>印章行事曆</h2><p id="gate-msg"></p>
  <button class="btn" id="gate-login" hidden>使用 Google 登入</button><button class="btn ghost" id="gate-out" hidden>換一個帳號</button></div>
<script src="https://www.gstatic.com/firebasejs/%s/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/%s/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/%s/firebase-firestore-compat.js"></script>
<script src="config.js"></script>
<script src="app.js"></script>'''%(FB,FB,FB))
r('預覽模式：資料只存在這台裝置，登入後才會兩人同步。','尚未設定 Firebase：資料只存在這台裝置。')
dist=os.path.join(here,'..','docs'); os.makedirs(dist,exist_ok=True)
open(os.path.join(dist,'index.html'),'w',encoding='utf-8').write(src)
for f in ['config.js','app.js']: shutil.copy(os.path.join(here,f),dist)
json.dump({"name":"印章行事曆","short_name":"印章行事曆","start_url":"./","scope":"./","display":"standalone","background_color":"#ffffff","theme_color":"#ffffff","lang":"zh-Hant",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png"},{"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}]},
  open(os.path.join(dist,'manifest.webmanifest'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('built',dist)
