#!/usr/bin/env python3
# Build src/app/Husk/Localizable.xcstrings from:
#   tools/i18n_zh/static_*.json   (en -> zh-Hans, no placeholders)
#   tools/i18n_zh/interp.json     (per-template arg types + zh, aligned to the
#                                  interpolation templates in _merged_en.json)
import os, re, json, glob

HERE=os.path.dirname(__file__)
ROOT=os.path.join(HERE,"..")
MERGED=os.path.join(HERE,"i18n_keys","_merged_en.json")

# Code-side plural-suffix normalisations applied AFTER the Swift refactor that
# removed the manual "(s)" ternaries. Keeps the catalog keys identical to the
# built LocalizationValue format strings.
PLURAL_FIX=[
 ('Metadata for \\(n) of your app\\(n == 1 ? "" : "s") has been updated. Would you like to download the updates?',
  'Metadata for \\(n) of your apps has been updated. Would you like to download the updates?'),
 ('Restored \\(n) file\\(n == 1 ? "" : "s") from \\(url.lastPathComponent).',
  'Restored \\(n) file(s) from \\(url.lastPathComponent).'),
 ('\\(r.dexCount) DEX file\\(r.dexCount == 1 ? "" : "s"), \\(bytes(r.dexBytes))',
  '\\(r.dexCount) DEX file(s), \\(bytes(r.dexBytes))'),
]
PH={'@':'%@','d':'%lld','f':'%lf'}

def split_interps(t):
    """Return (template_with_NUL_markers, [expr]) handling nested () and quotes."""
    out=[]; exprs=[]; i=0
    while i<len(t):
        if t[i:i+2]=='\\(':
            j=i+2; depth=1; instr=False; esc=False
            while j<len(t) and depth>0:
                c=t[j]
                if instr:
                    if esc: esc=False
                    elif c=='\\': esc=True
                    elif c=='"': instr=False
                else:
                    if c=='"': instr=True
                    elif c=='(': depth+=1
                    elif c==')': depth-=1
                j+=1
            assert depth==0, f"unbalanced interpolation in: {t!r}"
            exprs.append(t[i+2:j-1]); out.append('\x00'); i=j
        else:
            out.append(t[i]); i+=1
    return ''.join(out), exprs

def esc_percent(s):
    # escape literal % that is not part of a generated/positional specifier
    return re.sub(r'%(?!(?:%|@|lld|lf|ld|d|s|f|\d+\$))','%%',s)

def main():
    strings={}
    # static
    nstatic=0
    for fp in sorted(glob.glob(os.path.join(HERE,"i18n_zh","static_*.json"))):
        for en,zh in json.load(open(fp,encoding="utf-8")).items():
            assert en not in strings, f"dup static {en!r}"
            strings[en]=zh; nstatic+=1
    # extra data-driven words
    strings.setdefault("software","软件")

    # interpolation templates: skeleton-keyed dict ("{}" marks one argument).
    # The English format key is produced by substituting each {} per `a`
    # (@->%@, d->%lld, f->%lf). Independent of Swift expression text/variables.
    idict=json.load(open(os.path.join(HERE,"i18n_zh","interp_dict.json"),encoding="utf-8"))
    ninterp=0
    for skel,spec in idict.items():
        types=spec['a']; zh=spec['zh']
        assert skel.count('{}')==len(types), f"arg count mismatch: {skel!r} vs {types}"
        en=skel
        for ty in types:
            assert ty in PH, f"bad type {ty} in {skel!r}"
            en=en.replace('{}',PH[ty],1)
        en=esc_percent(en)
        if en in strings:
            assert strings[en]==zh, f"conflicting translation for {en!r}"
            continue
        strings[en]=zh; ninterp+=1

    cat={
        "sourceLanguage":"en",
        "strings":{k:{"localizations":{"zh-Hans":{"stringUnit":{"state":"translated","value":v}}}}
                   for k,v in sorted(strings.items())},
        "version":"1.0",
    }
    dst=os.path.join(ROOT,"src","app","Husk","Localizable.xcstrings")
    with open(dst,"w",encoding="utf-8") as f:
        json.dump(cat,f,ensure_ascii=False,indent=2)
        f.write("\n")
    print(f"static {nstatic} + interpolation {ninterp} (+software) = {len(strings)} keys")
    print("wrote",os.path.relpath(dst,ROOT))

if __name__=="__main__":
    main()
