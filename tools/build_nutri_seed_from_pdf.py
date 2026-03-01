#!/usr/bin/env python3
import argparse, csv, json, re
from pathlib import Path
import pdfplumber

CID_MAP = {'(cid:1)':'č','(cid:2)':'ć','(cid:3)':'č','(cid:4)':'ž','(cid:5)':'ć','(cid:6)':'đ'}
STR_REPL = {
    'PIRINAć':'PIRINAČ','PŠENIćNE':'PŠENIČNE','PŠENIćNI':'PŠENIČNI','PŠENIćNO':'PŠENIČNO',
    'JAGNJEčE':'JAGNJEĆE','OVćETINA':'OVČETINA','PAćJE':'PAČJE','čUREčE':'ĆUREĆE',
    'čUREčA':'ĆUREĆA','PILEčA':'PILEĆA','VOćE':'VOĆE','VOćNI':'VOĆNI','POVRćE':'POVRĆE',
    'POVRćA':'POVRĆA','ŠEćER':'ŠEĆER','PIćA':'PIĆA','PIćE':'PIĆE','ZAčINI':'ZAČINI',
    'KUKURUZ ŠEčERAC':'KUKURUZ ŠEĆERAC','MLEćNA':'MLEČNA','MLEćNI':'MLEČNI',
    'MLEčNI':'MLEČNI','MLEčA':'MLEČA','MLEč':'MLEČ',
    'čOKOLADA':'ČOKOLADA','čOKOLADNI':'ČOKOLADNI','KREM SUPA OD POVRčA':'KREM SUPA OD POVRĆA',
    'KUćNI':'KUĆNI','čIŠćENJE':'ČIŠĆENJE','TRčANJE':'TRČANJE','GOVEžA':'GOVEĐA',
    'TELEčI':'TELEĆI','GUŠćJE':'GUŠČJE'
}
CATEGORY_NAMES = {
    'ŽITARICE I PROIZVODI OD ŽITA','MESO, RIBA, JAJA','MLEKO I MLEČNI PROIZVODI',
    'SIR BILJNOG POREKLA','VOĆE I VOĆNI PROIZVOD','POVRĆE I PROIZVODI OD POVRĆA',
    'MASTI I ULJA','ŠEĆER, MED I SLATKIŠI','PIĆA, NAPICI I OSTALO','ZAČINI I INDUSTRIJSKE SUPE'
}
def clean_text(s):
    if s is None:
        return None
    for a,b in CID_MAP.items():
        s = s.replace(a,b)
    s = s.replace('–','-').replace('—','-')
    for a,b in STR_REPL.items():
        s = s.replace(a,b)
    return re.sub(r'\s+', ' ', s).strip()
def num_or_none(s):
    if s in (None, '', '-'):
        return None
    return float(s.replace(',','.')) if re.match(r'^\d+(?:,\d+)?$', s) else None
def slugify(s):
    s=s.lower()
    for a,b in {'č':'c','ć':'c','š':'s','ž':'z','đ':'dj'}.items():
        s=s.replace(a,b)
    return re.sub(r'[^a-z0-9]+','_',s).strip('_')
def parse_pdf(pdf_path: Path):
    items=[]; current_category=None
    num_re=re.compile(r'^-?\d+(?:,\d+)?$|^-$')
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_no, page in enumerate(pdf.pages[:5], start=1):
            for table in page.extract_tables() or []:
                for row in table:
                    row=[clean_text(x) for x in row]
                    nonempty=[x for x in row if x]
                    if not nonempty:
                        continue
                    joined=' '.join(nonempty)
                    if (
                        'KALORIJSKE VREDNOSTI' in joined or
                        'NAMIRNICA' in joined or
                        joined.startswith('Odnos između') or
                        joined.startswith('Od ukupnog') or
                        joined.startswith('Preporučuje')
                    ):
                        continue
                    if len(nonempty)==1 and nonempty[0] in CATEGORY_NAMES:
                        current_category=nonempty[0]
                        continue
                    name=next((x for x in row if x), '')
                    nums=[x for x in row[1:] if x and num_re.match(x)]
                    if len(nums) >= 5:
                        items.append({
                            'id': slugify(name),
                            'naziv': name,
                            'grupa': current_category,
                            'page': page_no,
                            'source_pdf': pdf_path.name,
                            'nutri_per_100g': {
                                'kcal': num_or_none(nums[0]),
                                'p_g': num_or_none(nums[1]),
                                'm_g': num_or_none(nums[2]),
                                'uh_g': num_or_none(nums[3]),
                                'holesterol_mg': num_or_none(nums[4]),
                            }
                        })
    seen=set(); ded=[]
    for it in items:
        key=(it['naziv'], it['grupa'])
        if key not in seen:
            seen.add(key)
            ded.append(it)
    return ded

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--out', default='.')
    args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    items=parse_pdf(Path(args.pdf))
    (out/'ingredient_nutri_pdf_raw.json').write_text(
        json.dumps({'source_pdf':Path(args.pdf).name,'items':items}, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    with open(out/'ingredient_nutri_pdf_raw.csv','w',encoding='utf-8',newline='') as f:
        w=csv.writer(f)
        w.writerow(['id','naziv','grupa','page','kcal','p_g','m_g','uh_g','holesterol_mg'])
        for it in items:
            n=it['nutri_per_100g']
            w.writerow([it['id'],it['naziv'],it['grupa'],it['page'],n['kcal'],n['p_g'],n['m_g'],n['uh_g'],n['holesterol_mg']])
    print(f'OK: extracted {len(items)} nutritive rows into {out}')
if __name__ == '__main__':
    main()
