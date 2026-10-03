# -*- coding: utf-8 -*-
r"""Scan the exchange code space for every index whose name says 债.

Page seventeen was asked for as "国债、企债、公司债、中证全债、中证转债". Four of the
five resolve to a code the endpoint answers. 中证全债 does not: the guesses that
looked right either stop in 2015 (``sh000023`` is 沪分离债) or are not bonds at all
(``sh000145`` is 优势资源, ``sh000926`` is 中证央企).

中证全债 is a 中证指数公司 index (H11001) and may simply never have been given a
quote code the Tencent endpoint knows. Rather than guess again one code at a time,
this script asks the snapshot for the **whole 000xxx and 399xxx index space** and
keeps every name containing 债/券/国债/转债. The snapshot takes a hundred codes per
call, so this is twenty calls for a thousand codes — cheaper than guessing.

The answer wanted is one line: does a 全债 code exist that returns a live monthly
series, or is the design going to have to name the fifth row something else.

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-bond-index-scan.py
"""

import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

# 债 covers 国债/企债/公司债/转债/城投债; 券 catches 债券 names that skip the word.
NEEDLES = ("债", "券")


def get(url, referer=None, encoding="utf-8", timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})

    if referer:
        req.add_header("Referer", referer)

    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(encoding, "replace")


def batch(codes):
    """Snapshot names for up to a hundred codes in one call."""
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    out = {}

    try:
        text = get(url, referer="https://gu.qq.com/", encoding="gbk")
    except Exception:  # noqa: BLE001 - a refused batch is an answer
        return {}

    for line in text.split(";"):
        line = line.strip()

        if not line.startswith("v_"):
            continue

        head, _, body = line.partition("=")
        fields = body.strip().strip('"').split("~")
        name = (fields[1] if len(fields) > 1 else "").strip()

        if name:
            out[head[2:].strip()] = name

    return out


def main():
    found = {}

    for prefix, lo, hi in (("sh", 1, 999), ("sz", 399001, 399999)):
        lo = max(lo, 1 if prefix == "sh" else 399001)
        codes = ["%s%06d" % (prefix, n) for n in range(lo, hi + 1)]

        for i in range(0, len(codes), 100):
            found.update(batch(codes[i:i + 100]))

    print("名字里带 债/券 的指数 (%d 个)" % len(
        [1 for n in found.values() if any(k in n for k in NEEDLES)]))

    for code in sorted(found):
        name = found[code]

        if any(k in name for k in NEEDLES):
            print(f"{code:<10}  {name}")


if __name__ == "__main__":
    main()
