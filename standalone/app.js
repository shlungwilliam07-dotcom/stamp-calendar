// 獨立版外殼：Google 登入 + Firestore，對內提供和原頁面相同的資料介面。
(function () {
  "use strict";
  var cfg = (window.APP_CONFIG || {}).firebase || {};
  var gate = document.getElementById("gate"), msg = document.getElementById("gate-msg"),
      btn = document.getElementById("gate-login"), out = document.getElementById("gate-out");
  if (!cfg.apiKey || !window.firebase) { gate.hidden = true; return; } // 沒設定時：本機預覽模式
  firebase.initializeApp(cfg);
  var auth = firebase.auth(), fs = firebase.firestore();
  fs.enablePersistence({ synchronizeTabs: true }).catch(function () {});
  var role = null, done, ready = new Promise(function (r) { done = r; });
  function show(text, login, signout) { gate.hidden = false; msg.textContent = text; btn.hidden = !login; out.hidden = !signout; }
  show("讀取中…", false, false);
  auth.onAuthStateChanged(function (u) {
    if (!u) { show("用 Google 帳號登入，兩個人的資料會自動同步。", true, false); return; }
    show("讀取中…", false, false);
    fs.doc("roles/" + u.uid).get().then(function (s) {
      role = s.exists ? s.data().role : null; gate.hidden = true; done(u);
    }).catch(function (e) {
      if (e && e.code === "permission-denied") show(u.email + " 沒有使用權限。請改用被允許的 Google 帳號。", false, true);
      else show("連不上資料庫，請檢查網路後重新開啟。", false, true);
    });
  });
  btn.addEventListener("click", function () {
    var p = new firebase.auth.GoogleAuthProvider(); p.setCustomParameters({ prompt: "select_account" });
    auth.signInWithPopup(p).catch(function (e) {
      var c = e && e.code;
      if (c === "auth/popup-blocked" || c === "auth/operation-not-supported-in-this-environment" || c === "auth/web-storage-unsupported") auth.signInWithRedirect(p);
      else if (c !== "auth/popup-closed-by-user" && c !== "auth/cancelled-popup-request") show("登入失敗：" + (e.message || c), true, false);
    });
  });
  out.addEventListener("click", function () { auth.signOut().then(function () { location.reload(); }); });
  window.claude = { use: function (n) { return ready.then(function () {
    if (n === "db") return fs;
    if (n === "user") return { isOwner: function () { return Promise.resolve(role === "long" ? true : role === "zhen" ? false : null); } };
    return null; }); } };
  window.appSetRole = function (r) { var u = auth.currentUser; if (u) fs.doc("roles/" + u.uid).set({ role: r, email: u.email }).catch(function () {}); };
  window.appSignOut = function () { auth.signOut().then(function () { location.reload(); }); };
})();
