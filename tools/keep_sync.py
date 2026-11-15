"""把一則 Google Keep 清單記事同步到 app 的列表（Keep -> Firestore，單向）。

使用非官方的 gkeepapi，Google 隨時可能讓它失效。記事內容不會印到記錄檔。
環境變數：KEEP_EMAIL, KEEP_MASTER_TOKEN, KEEP_NOTE_TITLE, FIREBASE_SERVICE_ACCOUNT, KEEP_OWNER (long|zhen，預設 zhen)
"""
import json, os, sys, time, uuid


def clean(i):
    return {"id": str(i.get("id")), "text": str(i.get("text") or ""), "done": bool(i.get("done")),
            "indent": 1 if i.get("indent") else 0, "both": bool(i.get("both")), "k": bool(i.get("k")), "g": bool(i.get("g"))}


def merge(old, rows):
    """與網頁端 keepMerge 相同：Keep 項目以 Keep 為準；已勾選但 app 裡沒有的不進來；app 自己加的項目留在原本的相對位置。"""
    old = [clean(i) for i in old]
    used, out = set(), []
    skip_children = False
    for x in rows:
        m = next((i for i in old if i["k"] and i["id"] not in used and i["text"] == x["text"] and i["indent"] == x["indent"]), None) \
            or next((i for i in old if not i["k"] and i["id"] not in used and i["text"] == x["text"] and i["indent"] == x["indent"]), None)
        # 在 Keep 已勾選、但 app 裡還沒有的項目不同步（連同它的子項目）
        if not x["indent"]:
            skip_children = x["done"] and m is None
            if skip_children:
                continue
        elif skip_children or (x["done"] and m is None):
            continue
        if m:
            used.add(m["id"]); out.append({**m, "done": x["done"], "k": True})
        else:
            out.append({"id": uuid.uuid4().hex[:14], "text": x["text"], "done": x["done"], "indent": x["indent"], "both": False, "k": True, "g": False})
    last = -1
    for it in old:
        at = next((n for n, o in enumerate(out) if o["id"] == it["id"]), -1)
        if at >= 0:
            last = at
        elif not it["k"]:
            pos = last + 1
            if not it["indent"]:
                while pos < len(out) and out[pos]["indent"]:
                    pos += 1
            out.insert(pos, dict(it)); last = pos
    first = next((i for i in out if not i["done"]), None)
    if first:
        first["indent"] = 0
    return out


def keep_rows():
    import gkeepapi
    keep = gkeepapi.Keep()
    email, token = os.environ["KEEP_EMAIL"], os.environ["KEEP_MASTER_TOKEN"]
    (getattr(keep, "authenticate", None) or keep.resume)(email, token)
    title = os.environ["KEEP_NOTE_TITLE"].strip()
    note = next((n for n in keep.all() if isinstance(n, gkeepapi.node.List) and not n.trashed and n.title.strip() == title), None)
    if note is None:
        sys.exit("找不到這個標題的清單記事（請確認 KEEP_NOTE_TITLE，且該記事是核取方塊清單）")
    rows = []
    for it in note.items:
        text = (it.text or "").strip()[:300]
        if text:
            rows.append({"text": text, "indent": 1 if it.indented else 0, "done": bool(it.checked)})
    return rows


def main():
    need = ["KEEP_EMAIL", "KEEP_MASTER_TOKEN", "KEEP_NOTE_TITLE", "FIREBASE_SERVICE_ACCOUNT"]
    if any(not os.environ.get(k) for k in need):
        print("尚未設定 Secrets，略過"); return
    import firebase_admin
    from firebase_admin import credentials, firestore
    rows = keep_rows()
    firebase_admin.initialize_app(credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])))
    who = os.environ.get("KEEP_OWNER") or "zhen"
    if who not in ("long", "zhen"):
        sys.exit("KEEP_OWNER 只能是 long 或 zhen")
    ref = firestore.client().document("checklists/" + who)
    snap = ref.get()
    old = [clean(i) for i in ((snap.to_dict() or {}).get("items") or [])] if snap.exists else []
    new = merge(old, rows)
    if new == old:
        print("沒有變動"); return
    ref.set({"items": new, "uts": int(time.time() * 1000)})
    print("已更新，共 %d 個項目" % len(new))


if __name__ == "__main__":
    main()
