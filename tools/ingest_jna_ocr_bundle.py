#!/usr/bin/env python3
import argparse, json, re, zipfile
from pathlib import Path

def norm(s):
    s=str(s).lower()
    s=s.translate(str.maketrans("čćžšđ", "cczsd"))
    s=re.sub(r'[^a-z0-9]+',' ',s).strip()
    return s

def guess_category(title):
    t=norm(title)
    if any(k in t for k in ['caj','kafa','mleko','limunada','kakao','jogurt']): return 'napici'
    if any(k in t for k in ['supa','corba']): return 'supe_i_corbe'
    if any(k in t for k in ['sos']): return 'sosovi'
    if any(k in t for k in ['jaja','kajgana','omlet','przenice']): return 'jela_od_jaja'
    if 'salata' in t: return 'salate'
    if any(k in t for k in ['kolac','snita','pita','baklava','gibanica','burek','koh','krem','palacinke','puding','knedle']): return 'testa_i_slano_slatko'
    if any(k in t for k in ['kupus','krompir','grasak','boranija','karfiol','kelj','paprika','tikvice','spanac','pirinac','pasulj','sarma','musaka']): return 'povrce_i_prilozi'
    if any(k in t for k in ['goved','junec','telec','svinj','pile','pilic','pilet','june','ovc','jagnj','riba','riblj','snicla','odrezak','gulas','paprikas']): return 'glavna_jela_i_meso'
    return 'ostalo'

def block_preview(raw_lines):
    rows=[x.strip() for x in raw_lines if x.strip() and not re.match(r'^===== STRANA \d+ =====$',x.strip())]
    start=0
    for idx,row in enumerate(rows):
        if re.search(r'\bOva[jl]\s+normativ\b', row, re.I):
            start=idx; break
    rows=rows[start:]
    kept=[]
    for row in rows:
        letters=sum(ch.isalpha() for ch in row)
        digits=sum(ch.isdigit() for ch in row)
        bad=len(re.findall(r'[=|_/\[\]{}<>*"]', row))
        if letters < 8 or digits > letters*0.25 or bad > max(1, letters*0.06): continue
        if re.search(r'VRSTA NAMIRNICE|Vitamini|Mineral|Ukupno|hranljivi i zaštitni sastojci', row, re.I): continue
        kept.append(row)
    return re.sub(r'\s+', ' ', ' '.join(kept[:8])).strip()

def main():
    ap=argparse.ArgumentParser(description='Pretvara JNA OCR bundle u bridge JSON za Biblioteku')
    ap.add_argument('bundle_zip')
    ap.add_argument('--out', required=True)
    args=ap.parse_args()

    out=Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.bundle_zip) as z:
        txt_name=next((n for n in z.namelist() if n.endswith('.txt')), None)
        if not txt_name:
            raise SystemExit('TXT nije pronađen u bundle-u')
        text=z.read(txt_name).decode('utf-8', errors='ignore')

    lines=text.splitlines()
    page=1; page_at_line={}
    for i,l in enumerate(lines):
        m=re.match(r'^===== STRANA (\d+) =====$', l.strip())
        if m: page=int(m.group(1))
        page_at_line[i]=page

    headings=[]
    for i,l in enumerate(lines):
        s=l.strip()
        m=re.match(r'^(\d{1,3})\.\s*[—-]\s*(.+)$', s)
        if m: headings.append((i,int(m.group(1)),m.group(2).strip()))

    items=[]
    for idx,(ln,num,title) in enumerate(headings):
        end=headings[idx+1][0] if idx+1 < len(headings) else len(lines)
        raw_lines=lines[ln+1:end]
        preview=block_preview(raw_lines)
        items.append({
            "id": f"jna-{num:03d}-{re.sub(r'[^a-z0-9]+','-', norm(title)).strip('-')[:60]}",
            "broj": num,
            "naziv": title,
            "page_start": page_at_line.get(ln),
            "category_guess": guess_category(title),
            "preview": preview
        })

    out.write_text(json.dumps({
        "version":"jna-ocr-bridge-tool-v1",
        "indexed_recipe_titles": len(items),
        "items": items
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'OK: {len(items)} stavki -> {out}')

if __name__ == '__main__':
    main()
