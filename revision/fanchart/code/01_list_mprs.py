"""Scrape the RBI Monetary Policy Report archive (HalfYearlyPublications.aspx) for all years.
Writes data_raw/mpr_index.csv with year, title, publication date, view URL and PDF URL.
Usage: python -I code/01_list_mprs.py <fanchart_dir>
"""
import re, sys, csv, urllib.request, urllib.parse, http.cookiejar, html, time
from pathlib import Path

root = Path(sys.argv[1])
raw = root / "data_raw"
URL = "https://www.rbi.org.in/Scripts/HalfYearlyPublications.aspx?head=Monetary%20Policy%20Report"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]

def get(url, data=None):
    if data is not None:
        data = urllib.parse.urlencode(data).encode()
    with op.open(url, data, timeout=60) as r:
        return r.read().decode("utf-8", "replace")

page = get(URL)
def hidden(p):
    return {m.group(1): html.unescape(m.group(2)) for m in
            re.finditer(r'name="(__[A-Z]+)" id="[^"]*" value="([^"]*)"', p)}

rows = []
for year in range(2016, 2027):
    for period in ("1", "2"):
        form = hidden(page)
        form.update({"hdnYear": str(year), "hdnperiod": period,
                     "UsrFontCntr$txtSearch": "", "UsrFontCntr$btn": ""})
        p = get(URL, form)
        (raw / f"mpr_index_{year}_{period}.html").write_text(p, encoding="utf-8")
        blocks = re.findall(r"<b>([A-Z][a-z]{2} \d{2}, \d{4})</b>(.*?)(?=<b>[A-Z][a-z]{2} \d{2}, \d{4}</b>|</table>)", p, re.S)
        for date, blk in blocks:
            for m in re.finditer(r"href=PublicationsView\.aspx\?id=(\d+)>.*?/>([^<]*)</a>.*?href='([^']+\.PDF)'", blk, re.S | re.I):
                rows.append(dict(year=year, period=period, date=date, id=m.group(1),
                                 title=html.unescape(m.group(2)).strip(),
                                 view=f"https://www.rbi.org.in/Scripts/PublicationsView.aspx?id={m.group(1)}",
                                 pdf=m.group(3)))
        time.sleep(1)

seen, out = set(), []
for r in rows:
    if r["id"] not in seen:
        seen.add(r["id"]); out.append(r)
with open(raw / "mpr_index.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
for r in out:
    print(r["date"], r["title"], r["pdf"])
