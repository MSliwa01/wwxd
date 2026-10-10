import json, re, pathlib
import trafilatura
from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein
from wwxd.lint import normalize
from wwxd import rawdoc
html=open('/tmp/ycroot/page.html').read(); body=trafilatura.extract(html); body=body[body.index('Transcript'):]
turns=[normalize(m.group(1)) for m in re.finditer(r'(?:^|\n)(?:Garry|Sam):\s*(.*)', body)]
turns=[t for t in turns if len(t.split())>=12]
def clean(t): return normalize(t.replace('>>',' '))
cands={'youtube auto-captions':' '.join(s.text for s in rawdoc.read(pathlib.Path.home()/'wwxd-lab/vaults/yc/raw/yt-ZIaOBAjvc38.md').segments)}
w=json.load(open('/tmp/wwxd-scripts/whisper_runs.json'))
for k,v in w.items(): cands[f'whisper {k}']=v['text']
print('reference turns used',len(turns),'words',sum(len(t.split()) for t in turns))
for k,t in cands.items():
    H=clean(t); err=n=0; found=0
    for ref in turns:
        al=fuzz.partial_ratio_alignment(ref,H)
        if al is None or al.score<60: err+=len(ref.split()); n+=len(ref.split()); continue
        found+=1
        hyp=H[al.dest_start:al.dest_end].split(); r=ref.split()
        err+=Levenshtein.distance(r,hyp); n+=len(r)
    sec=w.get(k.replace('whisper ',''),{}).get('seconds','-')
    print(f'{k:28} WER {100*err/n:5.1f}%   turns aligned {found}/{len(turns)}   time {sec}s')
