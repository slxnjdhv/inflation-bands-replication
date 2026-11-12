"""Report page size and the set of (font, size) of all text spans in the figure PDFs.
Run: python -I revision2/code/check_fonts.py"""
from pathlib import Path
import pymupdf
R2 = Path(__file__).resolve().parents[1]
TW = 372 / 72.27 * 72  # sn-jnl textwidth in PostScript points
for f in ("Fig1.pdf", "Fig2.pdf", "Fig1_174mm.pdf", "Fig2_174mm.pdf"):
    doc = pymupdf.open(R2 / f); pg = doc[0]
    w, h = pg.rect.width, pg.rect.height
    spans = [(s["font"], round(s["size"], 2)) for b in pg.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"] if s["text"].strip()]
    sizes = sorted({s for _, s in spans}); fonts = sorted({f_ for f_, _ in spans})
    print(f"{f}: {w/72*25.4:.1f} x {h/72*25.4:.1f} mm; spans {len(spans)}; fonts {fonts}; sizes {sizes}; "
          f"printed size at \textwidth (130.7 mm): {[round(s*TW/w,2) for s in sizes]}; at 174 mm: {[round(s*174/(w/72*25.4),2) for s in sizes]}")
