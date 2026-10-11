#!/usr/bin/env python3
"""Find sentence-like string literals that are NOT already captured as SwiftUI
LocalizedStringKey first-args: these are plain String user-facing text candidates
(alert titles/messages passed via variables, toasts, errors, helpers).

We then heuristically drop logging / symbols / paths / urls and emit a manual
review list with surrounding context.
"""
import os, re, json

ROOT = os.path.join(os.path.dirname(__file__), "..", "src", "app")
STR = re.compile(r'"((?:\\.|[^"\\\n]){6,})"')

# sentence-like: at least two alpha words and a space, mostly letters
WORD = re.compile(r'[A-Za-z][A-Za-z\'’\-]*')
def sentence_like(s):
    if '\\(' in s:           # interpolation handled separately
        return False
    if 'http' in s or '://' in s: return False
    words = WORD.findall(s)
    if len(words) < 2: return False
    # require a space and a lowercase word (real prose), not CamelCase identifiers
    if ' ' not in s: return False
    letters = sum(c.isalpha() for c in s)
    if letters < 8: return False
    # exclude things that are mostly symbols/paths
    if s.count('/') > 2 or s.count('.') > 6: return False
    return True

LOG_LINE = re.compile(r'(logger|huskLog|os_log|NSLog|print|assertionFailure|preconditionFailure|fatalError|\.debug\(|\.error\(|\.fault\(|\.info\(|\.notice\(|\.warning\(|\.log\()', re.I)

def main():
    known = set(json.load(open(os.path.join(os.path.dirname(__file__),"i18n_strings.json")))["all_swiftui"].keys())
    cands = {}
    for dp,_,ns in os.walk(ROOT):
        for n in ns:
            if not n.endswith('.swift'): continue
            fp=os.path.join(dp,n); rel=os.path.relpath(fp,ROOT)
            lines=open(fp,encoding='utf-8').read().split('\n')
            for i,line in enumerate(lines):
                if LOG_LINE.search(line): continue
                for m in STR.finditer(line):
                    s=m.group(1)
                    if s in known: continue
                    if not sentence_like(s): continue
                    cands.setdefault(s,[]).append(f"{rel}:{i+1}")
    ks=sorted(cands)
    print(f"plain-String prose candidates: {len(ks)}")
    for k in ks:
        print(f"{cands[k][0]:45s} | {k}")
    json.dump({k:v for k,v in cands.items()},
              open(os.path.join(os.path.dirname(__file__),"i18n_dynamic_review.json"),"w"),
              ensure_ascii=False,indent=2)

if __name__=="__main__": main()
