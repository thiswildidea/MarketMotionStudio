#!/usr/bin/env python
"""Checks every resource key the app asks for against the ones the resw files carry.

Two ways a key is asked for, and they need different names:

    x:Uid="Foo" on a control   ->  the resw entry must be "Foo.Text", "Foo.Content",
                                   "Foo.Header", "Foo.PlaceholderText" ...
    Strings.Get("Foo")         ->  the resw entry must be exactly "Foo"

Getting the first one wrong leaves a control blank (the label next to it still
shows, so it reads as a styling glitch rather than as a missing string); getting
the second one wrong paints the square bracketed key into the frame, which is how
`[CandleLegendUp]` ended up in an exported chart. Neither is caught by the
compiler, and both are caught here.

Run:  python tools/verify-resw-uids.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "src", "MarketMotionStudio")
STRINGS = os.path.join(SOURCE, "Strings")

# The properties a x:Uid can resolve, per the control it sits on. An entry is
# accepted when the suffix is one of these.
SUFFIXES = (".Text", ".Content", ".Header", ".PlaceholderText", ".Description",
            ".OffContent", ".OnContent", ".Title", ".ToolTipService.ToolTip")

UID = re.compile(r'x:Uid="([^"]+)"')
GET = re.compile(r'Strings\.(?:Get|Format)\(\s*"([A-Za-z][A-Za-z0-9_.]*)"')
DATA = re.compile(r'<data name="([^"]+)"')


def files(extension, root=SOURCE):
    for directory, _, names in os.walk(root):
        if os.sep + "obj" + os.sep in directory + os.sep:
            continue
        for name in names:
            if name.endswith(extension):
                yield os.path.join(directory, name)


def resources(tag):
    with open(os.path.join(STRINGS, tag, "Resources.resw"), encoding="utf-8-sig") as handle:
        return set(DATA.findall(handle.read()))


def main():
    tags = sorted(t for t in os.listdir(STRINGS)
                  if os.path.isdir(os.path.join(STRINGS, t)))

    if not tags:
        print("no resource folders found")
        return 1

    reference = resources(tags[0])
    problems = 0

    for tag in tags[1:]:
        other = resources(tag)
        if other != reference:
            problems += 1
            print(f"{tag}: key set differs from {tags[0]}")
            for missing in sorted(reference - other):
                print(f"    missing {missing}")
            for extra in sorted(other - reference):
                print(f"    extra   {extra}")

    keys = reference

    # x:Uid keys, which need one of the suffixes.
    stale = {}
    for path in files(".xaml"):
        with open(path, encoding="utf-8-sig") as handle:
            text = handle.read()
        for uid in UID.findall(text):
            if uid + ".Text" in keys or any(uid + s in keys for s in SUFFIXES):
                continue
            stale.setdefault(uid, []).append(os.path.relpath(path, ROOT))

    if stale:
        problems += len(stale)
        print("\nx:Uid with no matching .Text/.Content/... entry:")
        for uid, where in sorted(stale.items()):
            print(f"    {uid:34s} {', '.join(sorted(set(where)))}")

    # Strings.Get keys, which need the bare name.
    absent = {}
    for path in list(files(".cs")):
        with open(path, encoding="utf-8-sig") as handle:
            text = handle.read()
        for key in GET.findall(text):
            if key in keys or key + ".Text" in keys:
                continue
            absent.setdefault(key, []).append(os.path.relpath(path, ROOT))

    if absent:
        problems += len(absent)
        print("\nStrings.Get key with no entry:")
        for key, where in sorted(absent.items()):
            print(f"    {key:34s} {', '.join(sorted(set(where)))}")

    # A bare key and a `<key>.<Suffix>` key cannot share a stem: MakePri reads the
    # dot as a qualifier separator, so the stem would be defined both as a resource
    # and as a scope, and resource creation fails with PRI278 — at build time, which
    # is the good news, but only for whoever adds the second key.
    collisions = sorted(k for k in keys if "." in k and k.split(".", 1)[0] in keys)

    if collisions:
        problems += len(collisions)
        print("\nkey defined as both a resource and a scope (PRI278):")
        for key in collisions:
            print(f"    {key.split('.', 1)[0]:30s} and {key}")

    print(f"\n{len(tags)} languages, {len(keys)} keys, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
