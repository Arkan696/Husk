#!/usr/bin/env python3
"""Extract candidate user-facing, localizable strings from Husk Swift sources.

Two buckets:
  * swiftui  : literals passed to SwiftUI APIs that take LocalizedStringKey
               (these localize automatically once a catalog exists).
  * dynamic  : literals that look user-facing but are plain String / interpolation
               (alert message variables, toasts, Error text, helpers) which need
               String(localized:) wrapping -- collected for manual review.

Outputs JSON for the translation/build step.
"""
import os, re, json, sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "src", "app")
OUT = os.path.join(os.path.dirname(__file__), "i18n_strings.json")

# SwiftUI initializers/modifiers whose first explicit string argument is a
# LocalizedStringKey (auto-localized). Order matters only for reporting.
SWIFTUI_KEYS = [
    "Text", "Button", "Label", "TextField", "SecureField", "Toggle", "Picker",
    "Section", "Menu", "navigationTitle", "alert", "confirmationDialog",
    "LabeledContent", "GroupBox", "ProgressView", "Stepper", "DatePicker",
    "navigationSubtitle", "searchable", "help", "tabItem",
]

# A normal single-line Swift string literal (handles escapes), no interpolation
# capture here; we separately flag whether the literal contained \( ... ).
STR = r'"((?:\\.|[^"\\\n])*)"'

def swiftui_pattern():
    # keyword(  then allow whitespace/newlines, then a string literal as the
    # FIRST argument. For modifiers like .navigationTitle("x") this is exact.
    alt = "|".join(re.escape(k) for k in SWIFTUI_KEYS)
    # word boundary / dot before keyword, then '('
    return re.compile(r'(?:(?<=[.\s])|^)\b(?:' + alt + r')\s*\(\s*' + STR, re.M)

# Multi-line Swift string literals """ ... """
TRISTR = re.compile(r'"""(.*?)"""', re.S)

def has_interp(s):
    return "\\(" in s

def main():
    pat = swiftui_pattern()
    swiftui = {}   # key -> list of (file, has_interp)
    tristrings = []
    files = []
    for dirpath, _, names in os.walk(ROOT):
        for n in names:
            if n.endswith(".swift"):
                files.append(os.path.join(dirpath, n))
    for fp in sorted(files):
        rel = os.path.relpath(fp, ROOT)
        with open(fp, encoding="utf-8") as f:
            src = f.read()
        for m in pat.finditer(src):
            lit = m.group(1)
            # Skip obvious non-UI: empty, SF Symbol names, systemImage handled,
            # format strings that are pure interpolation with no words.
            if not lit.strip():
                continue
            swiftui.setdefault(lit, []).append([rel, has_interp(lit)])
        for m in TRISTR.finditer(src):
            block = m.group(1).strip()
            if block:
                tristrings.append([rel, block])

    # Report
    static_keys = sorted(k for k in swiftui if not has_interp(k))
    interp_keys = sorted(k for k in swiftui if has_interp(k))
    print(f"Swift files scanned: {len(files)}")
    print(f"SwiftUI unique literals: {len(swiftui)}  (static {len(static_keys)}, interpolation {len(interp_keys)})")
    print(f"Triple-quoted blocks: {len(tristrings)}")
    print("\n--- interpolation keys (need format-spec care) ---")
    for k in interp_keys:
        print("  ", repr(k))
    print("\n--- triple-quoted blocks ---")
    for rel, b in tristrings:
        print(f"  [{rel}] {b[:80]!r}")

    data = {
        "swiftui_static": static_keys,
        "swiftui_interp": interp_keys,
        "tristrings": [{"file": r, "text": b} for r, b in tristrings],
        "all_swiftui": {k: v for k, v in swiftui.items()},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\nwrote", OUT)

if __name__ == "__main__":
    main()
