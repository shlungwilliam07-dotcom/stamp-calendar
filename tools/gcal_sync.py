"""把 Google 日曆（iCal 私人網址）同步到 app 的列表（Google 日曆 -> 列表，單向）。

環境變數：GCAL_ICS_URL（日曆的「iCal 格式私人網址」）、FIREBASE_SERVICE_ACCOUNT、
GCAL_OWNER（long|zhen，預設 long）、GCAL_FROM（起始日 YYYY-MM-DD，預設今天）、GCAL_DAYS（往後幾天，預設 90）。
"""
import datetime as dt, json, os, re, sys, time, uuid
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Taipei")
WD = "日一二三四五六"
DATE_RE = re.compile(r"^\s*(\d{1,2})/(\d{1,2})")


def clean(i):
    return {"id": str(i.get("id")), "text": str(i.get("text") or ""), "done": bool(i.get("done")),
            "indent": 1 if i.get("indent") else 0, "both": bool(i.get("both")), "k": bool(i.get("k")), "g": bool(i.get("g"))}


def wd(d):
    return WD[(d.weekday() + 1) % 7]


def fmt(start, end, title, all_day):
    """start/end 為台北時間；all_day 時為 date，end 為最後一天（含）。"""
    if all_day:
        if end > start:
            return "%d/%d - %d/%d %s" % (start.month, start.day, end.month, end.day, title)
        return "%d/%d (%s) %s" % (start.month, start.day, wd(start), title)
    if end.date() != start.date():
        return "%d/%d - %d/%d %s" % (start.month, start.day, end.month, end.day, title)
    return "%d/%d (%s) %02d%02d - %02d%02d %s" % (start.month, start.day, wd(start), start.hour, start.minute, end.hour, end.minute, title)


def calendar_rows(ics_bytes, start_day, days):
    import icalendar, recurring_ical_events
    cal = icalendar.Calendar.from_ical(ics_bytes)
    window_end = start_day + dt.timedelta(days=days)
    rows, seen = [], set()
    for ev in recurring_ical_events.of(cal).between(start_day, window_end):
        if str(ev.get("STATUS", "")).upper() == "CANCELLED":
            continue
        title = " ".join(str(ev.get("SUMMARY", "")).split())[:120] or "（無標題）"
        loc = " ".join(str(ev.get("LOCATION", "") or "").split()).replace("@", "")
        if loc:
            title += " @" + loc.split(",")[0].strip()[:40]
        s, e = ev.get("DTSTART").dt, (ev.get("DTEND") or ev.get("DTSTART")).dt
        if isinstance(s, dt.datetime):
            if s.tzinfo is None:
                s = s.replace(tzinfo=TZ)
            if isinstance(e, dt.datetime) and e.tzinfo is None:
                e = e.replace(tzinfo=TZ)
            s, e = s.astimezone(TZ), e.astimezone(TZ)
            if s.date() < start_day:
                continue
            key, text = (title, s.isoformat()), fmt(s, e, title, False)
            sort = (s.date(), s.hour * 60 + s.minute)
        else:
            last = e - dt.timedelta(days=1) if e > s else s  # iCal 的 DTEND 不含當天
            if last < start_day:
                continue
            s = max(s, start_day)
            key, text = (title, s.isoformat()), fmt(s, last, title, True)
            sort = (s, -1)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"text": text, "sort": sort})
    rows.sort(key=lambda r: r["sort"])
    return [r["text"] for r in rows]


def item_date(text, year):
    m = DATE_RE.match(text)
    if not m:
        return None
    try:
        return dt.date(year, int(m.group(1)), int(m.group(2)))
    except ValueError:
        return None


def sort_by_date(items, today):
    """未完成的項目依開頭日期排序（子項目跟著主項目），沒有日期的排在最後，已完成的維持在尾端。"""
    open_, done = [i for i in items if not i["done"]], [i for i in items if i["done"]]
    groups = []
    for i in open_:
        if not i["indent"] or not groups:
            groups.append([i])
        else:
            groups[-1].append(i)

    def key(g):
        m = DATE_RE.match(g[0]["text"])
        if not m:
            return ("~", 0)
        best = None
        for y in (today.year - 1, today.year, today.year + 1):
            try:
                d = dt.date(y, int(m.group(1)), int(m.group(2)))
            except ValueError:
                return ("~", 0)
            if best is None or abs((d - today).days) < abs((best - today).days):
                best = d
        return (best.isoformat(), 0)
    order = sorted(range(len(groups)), key=lambda n: (key(groups[n]), n))
    return [i for n in order for i in groups[n]] + done


def merge(old, texts, today):
    """日曆項目以日曆為準；其他項目（Keep 來的、手動加的）原位保留；新日曆項目依日期插入。"""
    old = [clean(i) for i in old]
    keep = [i for i in old if not i["g"] or i["text"] in texts]
    have = {i["text"] for i in keep if i["g"]}
    out = list(keep)
    for text in texts:
        if text in have:
            continue
        d = item_date(text, today.year)
        pos = len(out)
        for n, it in enumerate(out):
            if it["indent"] or it["done"]:
                continue
            od = item_date(it["text"], today.year)
            if od and d and od > d:
                pos = n
                break
        if pos == len(out):
            pos = max([n + 1 for n, it in enumerate(out) if not it["done"]] or [0])
        out.insert(pos, {"id": uuid.uuid4().hex[:14], "text": text, "done": False, "indent": 0, "both": False, "k": False, "g": True})
    out = sort_by_date(out, today)
    first = next((i for i in out if not i["done"]), None)
    if first:
        first["indent"] = 0
    return out


def main():
    if not os.environ.get("GCAL_ICS_URL") or not os.environ.get("FIREBASE_SERVICE_ACCOUNT"):
        print("尚未設定 GCAL_ICS_URL，略過"); return
    import requests, firebase_admin
    from firebase_admin import credentials, firestore
    today = dt.datetime.now(TZ).date()
    start = max(today, dt.date.fromisoformat(os.environ["GCAL_FROM"])) if os.environ.get("GCAL_FROM") else today
    days = int(os.environ.get("GCAL_DAYS") or 90)
    url = os.environ["GCAL_ICS_URL"].strip()
    if "/private-" not in url or not url.endswith(".ics"):
        sys.exit("GCAL_ICS_URL 看起來不是「iCal 格式的私人網址」（應含 /private-… 並以 .ics 結尾）。請到 Google 日曆設定 → 整合日曆 重新複製。")
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        hint = {404: "網址錯誤或已重設，請重新複製私人網址", 401: "沒有權限，請確認是「私人網址」不是「公開網址」", 403: "沒有權限，請確認是「私人網址」不是「公開網址」"}.get(r.status_code, "")
        sys.exit("讀取 Google 日曆失敗：HTTP %d。%s" % (r.status_code, hint))
    texts = calendar_rows(r.content, start, days)
    who = os.environ.get("GCAL_OWNER") or "long"
    if who not in ("long", "zhen"):
        sys.exit("GCAL_OWNER 只能是 long 或 zhen")
    firebase_admin.initialize_app(credentials.Certificate(json.loads(os.environ["FIREBASE_SERVICE_ACCOUNT"])))
    ref = firestore.client().document("checklists/" + who)
    snap = ref.get()
    old = [clean(i) for i in ((snap.to_dict() or {}).get("items") or [])] if snap.exists else []
    new = merge(old, texts, today)
    if new == old:
        print("沒有變動（日曆 %d 筆）" % len(texts)); return
    ref.set({"items": new, "uts": int(time.time() * 1000)})
    print("已更新：日曆 %d 筆，列表共 %d 個項目" % (len(texts), len(new)))


if __name__ == "__main__":
    main()
