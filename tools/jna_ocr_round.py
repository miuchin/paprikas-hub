#!/usr/bin/env python3
import argparse, csv, json, subprocess, re
from pathlib import Path

KEYWORDS = [
    'potrebno', 'priprema', 'sastojci', 'peći', 'peci', 'kuvati', 'dinstati',
    'dodati', 'iseći', 'iseci', 'g', 'kg', 'ml', 'kašika', 'kasika', 'rerna'
]

def run(cmd):
    subprocess.run(cmd, check=True)

def score_text(txt: str) -> int:
    t=txt.lower()
    score=0
    for kw in KEYWORDS:
        if kw in t:
            score += 1
    if re.search(r'\b\d+\s?(g|kg|ml)\b', t):
        score += 2
    return score

def main():
    ap=argparse.ArgumentParser(description='OCR round for scan-heavy cookbooks such as JNA kuvar.')
    ap.add_argument('pdf')
    ap.add_argument('--out', required=True)
    ap.add_argument('--lang', default='srp_latn+srp+hrv+eng')
    ap.add_argument('--first-page', type=int, default=1)
    ap.add_argument('--last-page', type=int, default=0, help='0 = all pages')
    args=ap.parse_args()

    pdf=Path(args.pdf)
    out=Path(args.out)
    img_dir=out/'pages'
    txt_dir=out/'txt'
    out.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)

    prefix = img_dir/'page'
    pdftoppm_cmd=['pdftoppm','-png']
    if args.first_page:
        pdftoppm_cmd += ['-f', str(args.first_page)]
    if args.last_page:
        pdftoppm_cmd += ['-l', str(args.last_page)]
    pdftoppm_cmd += [str(pdf), str(prefix)]
    run(pdftoppm_cmd)

    page_rows=[]
    for img in sorted(img_dir.glob('page-*.png')):
        stem = img.stem
        txt_base = txt_dir/stem
        run(['tesseract', str(img), str(txt_base), '-l', args.lang, '--psm', '6'])
        txt_file = txt_base.with_suffix('.txt')
        text = txt_file.read_text(encoding='utf-8', errors='ignore')
        score = score_text(text)
        page_rows.append({
            'page_image': img.name,
            'text_file': txt_file.name,
            'chars': len(text),
            'score': score,
            'recipe_like': score >= 3,
            'sample': text[:240].replace('\n',' ')
        })

    with open(out/'page_index.csv','w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f, fieldnames=['page_image','text_file','chars','score','recipe_like','sample'])
        w.writeheader()
        w.writerows(page_rows)

    (out/'candidate_recipe_pages.json').write_text(
        json.dumps([r for r in page_rows if r['recipe_like']], ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    (out/'ocr_round_report.json').write_text(
        json.dumps({
            'pdf': pdf.name,
            'pages_processed': len(page_rows),
            'ocr_lang': args.lang,
            'candidate_recipe_pages': sum(1 for r in page_rows if r['recipe_like'])
        }, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    with open(out/'text_dump.ndjson','w',encoding='utf-8') as f:
        for row in page_rows:
            txt = (txt_dir/row['text_file']).read_text(encoding='utf-8', errors='ignore')
            f.write(json.dumps({'page_image':row['page_image'],'recipe_like':row['recipe_like'],'score':row['score'],'text':txt}, ensure_ascii=False))
            f.write('\n')
    print(f'OK: OCR round complete for {pdf.name} -> {out}')

if __name__ == '__main__':
    main()
