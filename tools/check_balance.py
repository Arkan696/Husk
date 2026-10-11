#!/usr/bin/env python3
# Tokenizer-level balance check for Swift sources (no swiftc available).
# Tracks () {} [] while correctly skipping line/block comments and string
# literals, INCLUDING \( ... ) interpolations (whose inner parens are code and
# must balance; the closing paren that returns to the string is not counted).
import os, sys

ROOT=sys.argv[1] if len(sys.argv)>1 else "src/app"

def check(src):
    frames=['code']   # stack of 'code' / 'str' modes
    stack=[]          # open brackets in code frames; '\\(' marks an interpolation start
    i=0; n=len(src); line=1
    while i<n:
        c=src[i]
        kind=frames[-1]
        if c=='\n': line+=1
        if kind=='code':
            if c=='/' and i+1<n and src[i+1]=='/':
                j=src.find('\n',i); i=(n if j<0 else j); continue
            if c=='/' and i+1<n and src[i+1]=='*':
                end=src.find('*/',i+2); i=(n if end<0 else end+2); continue
            if c=='"':
                frames.append('str'); i+=1; continue
            if c in '([{':
                stack.append((c,line)); i+=1; continue
            if c in ')]}':
                if not stack: return f"extra closing {c} at line {line}"
                op,ol=stack[-1]
                if c==')' and op=='\\(':
                    # this closes a string interpolation, not a normal group
                    stack.pop(); frames.pop(); i+=1; continue
                if c!= {'(':')','[':']','{':'}','\\(':')'}[op]:
                    return f"mismatch {op} (line {ol}) closed by {c} (line {line})"
                stack.pop(); i+=1; continue
            i+=1; continue
        else:  # str
            if c=='\\':
                if i+1<n and src[i+1]=='(':
                    frames.append('code'); stack.append(('\\(',line)); i+=2; continue
                i+=2; continue  # escaped char
            if c=='"':
                frames.pop(); i+=1; continue
            i+=1; continue
    if frames!=['code']:
        return f"unterminated frame, frames={frames}"
    if stack:
        return f"unclosed {stack[-3:]}"
    return None

bad=0; total=0
for dp,_,ns in os.walk(ROOT):
    for nm in ns:
        if nm.endswith(".swift"):
            total+=1
            fp=os.path.join(dp,nm)
            err=check(open(fp,encoding="utf-8").read())
            if err:
                bad+=1; print(f"IMBALANCE {os.path.relpath(fp,ROOT)}: {err}")
print(f"checked {total} Swift files, {bad} imbalanced")
sys.exit(1 if bad else 0)
