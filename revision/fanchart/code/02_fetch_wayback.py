"""Fetch full MPR PDFs from Internet Archive Wayback captures of the official rbidocs.rbi.org.in URLs.
(Direct download from rbidocs is blocked by a bot-check page; the Wayback copies are byte copies
of the official files captured at the stated timestamps.)
Usage: python -I code/02_fetch_wayback.py <fanchart_dir> [issue_filter]
Writes data_raw/pdf/MPR_<yyyy>_<Mon>.pdf and appends to data_raw/pdf_provenance.csv
"""
import csv, subprocess, sys, time, json
from pathlib import Path
import pymupdf

root = Path(sys.argv[1]); raw = root / "data_raw"; flt = sys.argv[2] if len(sys.argv) > 2 else ""
(raw / "pdf").mkdir(exist_ok=True)

def curl(args, t=280):
    return subprocess.run(["curl", "-sS", "-L", "-m", str(t)] + args, capture_output=True, text=True)

def valid(fn):
    try:
        d = pymupdf.open(fn); n = d.page_count
        txt = "".join(d[i].get_text() for i in range(min(n, 3)))
        return n > 10 and "JavaScript" not in txt[:200], n
    except Exception:
        return False, 0

prov = raw / "pdf_provenance.csv"
done = {}
if prov.exists():
    done = {r["file"]: r for r in csv.DictReader(open(prov, encoding="utf-8"))}
for r in csv.DictReader(open(raw / "mpr_index.csv", encoding="utf-8")):
    mon = r["title"].split()[-2][:3]; yr = r["title"].split()[-1]
    fn = raw / "pdf" / f"MPR_{yr}_{mon}.pdf"
    if flt and flt not in fn.name: continue
    if fn.exists() and valid(fn)[0]:
        print("ok already", fn.name); continue
    caps = []
    for attempt in range(4):
        o = curl([f"https://web.archive.org/cdx/search/cdx?url={r['pdf']}&output=json&fl=timestamp,mimetype,statuscode,length"], 90)
        try:
            js = json.loads(o.stdout); caps = [c for c in js[1:] if c[1] == "application/pdf" and c[2] == "200"]
            break
        except Exception:
            time.sleep(10)
    caps.sort(key=lambda c: -int(c[3]))
    got = False
    for ts, mt, sc, ln in caps:
        if int(ln) < 1_100_000:
            continue  # truncated 1 MB captures
        for attempt in range(3):
            o = curl(["-o", str(fn), f"https://web.archive.org/web/{ts}id_/{r['pdf']}"], 400)
            ok, n = valid(fn)
            if ok:
                got = True; break
            time.sleep(15)
        if got:
            with open(prov, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if f.tell() == 0: w.writerow(["file", "official_url", "wayback_url", "pages", "accessed_utc"])
                w.writerow([fn.name, r["pdf"], f"https://web.archive.org/web/{ts}/{r['pdf']}", n, time.strftime("%Y-%m-%d", time.gmtime())])
            print("GOT", fn.name, ts, n, "pages"); break
    if not got:
        print("FAILED", fn.name, "captures:", caps)
