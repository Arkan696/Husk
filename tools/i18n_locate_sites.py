#!/usr/bin/env python3
# Locate code sites that need explicit localization (the auto LocalizedStringKey
# path already covers single literal arguments).
import os, re, json
ROOT=os.path.join(os.path.dirname(__file__),"..","src","app")
UI=["Text","Button","Label","TextField","SecureField","Toggle","Picker","Section",
    "Menu","navigationTitle","alert","confirmationDialog","LabeledContent","GroupBox",
    "ProgressView","Stepper","navigationSubtitle","help"]
uire="(?:^|[.\s])("+"|".join(UI)+r")\s*\((.*)$"
# string concatenation involving literals:  "..." +  or + "..."
concat=re.compile(r'"[^"\n]*"\s*\+|\+\s*"[^"\n]*"')
# a quoted literal that contains interpolation
interp=re.compile(r'"[^"\n]*\\\([^"\n]*"')
def first_arg_is_nonliteral(argstr):
    a=argstr.strip()
    if a.startswith('"'): return False
    # strip leading "localized:" style labels none here
    return True
out={}
for dp,_,ns in os.walk(ROOT):
    for n in sorted(ns):
        if not n.endswith(".swift"): continue
        fp=os.path.join(dp,n); rel=os.path.relpath(fp,ROOT)
        lines=open(fp,encoding="utf-8").read().split("\n")
        hits=[]
        for i,l in enumerate(lines):
            if re.search(r'\b('+"|".join(UI)+r')\s*\(',l):
                m=re.search(r'\b('+"|".join(UI)+r')\s*\((.*)$',l)
                if m and first_arg_is_nonliteral(m.group(2)):
                    # skip if it's clearly an action closure or systemImage arg list start
                    hits.append(["NONLIT",i+1,l.strip()[:150]])
            if concat.search(l) and not re.search(r'(HuskLog|os_log|NSLog|logger|print\()',l):
                # only care if nearby UI words on same/prev/next line
                ctx=" ".join(lines[max(0,i-1):i+2])
                if re.search(r'\b(Text|Label|Button|title|detail|message|header|footer|prompt|navigationTitle|alert|confirmationDialog|Menu|Section|Toggle|Picker|TextField)\b',ctx):
                    hits.append(["CONCAT",i+1,l.strip()[:150]])
        if hits: out[rel]=hits
tot=sum(len(v) for v in out.values())
print("files with sites:",len(out)," total sites:",tot)
for rel,h in out.items():
    print(f"\n### {rel}  ({len(h)})")
    for t,ln,txt in h:
        print(f"  {t:7s} L{ln}: {txt}")
json.dump(out,open(os.path.join(os.path.dirname(__file__),"i18n_sites.json"),"w"),ensure_ascii=False,indent=2)
