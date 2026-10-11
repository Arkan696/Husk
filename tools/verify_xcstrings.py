#!/usr/bin/env python3
# Verify every localizable string the (post-refactor) code actually emits has a
# zh-Hans entry in Localizable.xcstrings. Reports MISSING (would show English).
import os, re, json, glob
HERE=os.path.dirname(__file__)
ROOT=os.path.join(HERE,"..","src","app")
cat=json.load(open(os.path.join(HERE,"..","src","app","Husk","Localizable.xcstrings"),encoding="utf-8"))["strings"]

# import helpers from builder
import importlib.util
spec=importlib.util.spec_from_file_location("bx",os.path.join(HERE,"build_xcstrings.py"))
bx=importlib.util.module_from_spec(spec); spec.loader.exec_module(bx)

# Gather raw strings:
#  (a) all String(localized: " ... ")  [single-line; multiline rare]
#  (b) SwiftUI first-arg literals via the same keyword set
UI=["Text","Button","Label","TextField","SecureField","Toggle","Picker","Section","Menu",
    "navigationTitle","alert","confirmationDialog","LabeledContent","GroupBox","ProgressView",
    "Stepper","navigationSubtitle"]
uire=re.compile(r'(?:^|[.\s])(?:'+"|".join(map(re.escape,UI))+r')\s*\(\s*("(?:\\.|[^"\\])*")',re.S)
sl_re=re.compile(r'String\s*\(\s*localized\s*:\s*("(?:\\.|[^"\\])*")',re.S)
# also NSLocalizedString( VAR ) we cannot resolve statically; skip (data-driven,
# covered by registries).

# catalog skeleton set: normalise every specifier to <*>
def skel_cat(k): return re.sub(r'%(?:\d+\$)?(?:lld|lf|ld|@|d|f|s)','<*>',k)
SKELS={skel_cat(k) for k in cat if '%' in k}

def skel_code(r):
    base,exprs=bx.split_interps(r)
    base=base.replace('\x00','<*>')
    return bx.esc_percent(base), len(exprs)

TECH=re.compile(r'(python3|\.py\b|<folder>|https?://|^[A-Za-z_][\w.]*$)')

def unq(lit):
    # lit includes surrounding quotes; decode Swift escapes minimally
    inner=lit[1:-1]
    return inner.encode().decode('unicode_escape') if False else inner.replace('\\"','"').replace("\\\\","\\")

missing=[]; truncated=[]; checked=0
files=[]
for dp,_,ns in os.walk(ROOT):
    for n in ns:
        if n.endswith(".swift"): files.append(os.path.join(dp,n))
for fp in files:
    rel=os.path.relpath(fp,ROOT)
    src=open(fp,encoding="utf-8").read()
    raws=set()
    for m in sl_re.finditer(src): raws.add(unq(m.group(1)))
    for m in uire.finditer(src):
        s=unq(m.group(1))
        if s.strip(): raws.add(s)
    for r in raws:
        # ignore obvious non-UI
        if r.startswith("http") or re.fullmatch(r'[\d\s.,×%/\-–—]+',r): continue
        checked+=1
        if '\\(' not in r:
            if r not in cat and not TECH.search(r): missing.append((rel,"static",r))
        else:
            try:
                sk,n=skel_code(r)
            except AssertionError:
                truncated.append((rel,r)); continue  # interpolation contains inner quotes; reviewed manually
            if sk=='<*>' or n==0:
                continue  # pure runtime value (counts, codes) -> falls back, fine
            if sk not in SKELS:
                missing.append((rel,"interp",sk+"   <= "+r))

print("checked raw UI strings:",checked)
print("MISSING:",len(missing))
for rel,k,v in missing:
    print(f"  [{rel}] {k}: {v}")
print("TRUNCATED (inner-quote interp, manually reviewed):",len(truncated))
for rel,v in truncated:
    print(f"  [{rel}] {v[:90]}")
