# -*- coding: utf-8 -*-
r"""Probe the bond / fixed-income pool for page seventeen.

Page seventeen was asked for as "债市固收竞速: 国债、企债、公司债、中证全债、中证转债" —
five instruments named by the user. Two of them turned out to be unusable, and this
pass exists to find out what replaces them:

*   ``sh000023`` was asked for as 中证全债. The snapshot says its real name is
    沪分离债 and its **monthly series stops at 2015-08** — a bar race would freeze
    the row eleven years before the animation ends.
*   ``sh000145`` was asked for as a treasury index. The snapshot says it is 优势资源,
    an equity index.

So this script does what every earlier pass did, but over a **wider bond roster** so
the page can be designed with a pool that is known to answer:

1. What is the instrument actually *called*? Snapshot field 1, because a code is a
   guess and the name is what goes on screen.
2. Does the endpoint return a **monthly series**, how long, and does it reach the
   present? A row that stops mid-window is the 沪分离债 bug again.
3. Does it **move**? Treasury indices move a few percent a decade; if two rows move
   by the same amount the race never reorders.

The pool a design can be drawn from is whatever survives all three.

Run:

    C:/Users/user/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
        tools/probe-next-indicators-6.py
"""

import json
import urllib.request
from datetime import date

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"

MONTHS = 400


def get(url, referer=None, encoding="utf-8", timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})

    if referer:
        req.add_header("Referer", referer)

    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(encoding, "replace")


def names(codes):
    """Snapshot names, because a code is a guess and the label is what ships."""
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    out = {}

    try:
        text = get(url, referer="https://gu.qq.com/", encoding="gbk")
    except Exception:  # noqa: BLE001 - an unreachable snapshot is an answer
        return {}

    for line in text.split(";"):
        line = line.strip()

        if not line.startswith("v_"):
            continue

        head, _, body = line.partition("=")
        fields = body.strip().strip('"').split("~")
        out[head[2:].strip()] = (fields[1] if len(fields) > 1 else "").strip()

    return out


def series(code, period="month", adj="", count=MONTHS):
    """newfqkline is the endpoint that carries full history."""
    url = (
        "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
        f"?param={code},{period},,,{count},{adj}"
    )

    try:
        j = json.loads(get(url, referer="https://gu.qq.com/"))
    except Exception:  # noqa: BLE001 - a refused class is the answer, not a crash
        return None

    data = (j.get("data") or {}).get(code) or {}

    for key in (adj + period, period):
        rows = data.get(key)

        if isinstance(rows, dict):
            rows = next((v for v in rows.values()
                         if isinstance(v, list) and v), None)

        if isinstance(rows, list) and rows and isinstance(rows[0], list):
            return rows

    return None


def settled(rows):
    """Drop the month still in progress, the way the app does."""
    today = date.today().strftime("%Y-%m")

    return [r for r in rows if str(r[0])[:7] < today] if rows else []


def gaps(rows):
    """Missing months inside the window, because a hole is a wrong-looking row."""
    if len(rows) < 2:
        return 0

    spans = []
    prev = None

    for r in rows:
        y, m = int(str(r[0])[:4]), int(str(r[0])[5:7])
        cur = y * 12 + m

        if prev is not None:
            spans.append(cur - prev - 1)

        prev = cur

    return sum(spans)


def holes(rows):
    """Where the missing months are, not just how many.

    A hole early in history is survivable — the row simply starts later. A hole
    *inside* the animated window makes a bar jump, which is what disqualified
    沪分离债. So report each gap as a span plus the start of the trailing run.
    """
    if len(rows) < 2:
        return [], None

    spans = []
    prev = None
    start = str(rows[0][0])[:7]

    for r in rows:
        y, m = int(str(r[0])[:4]), int(str(r[0])[5:7])
        cur = y * 12 + m

        if prev is not None and cur - prev > 1:
            a, b = prev + 1, cur - 1
            spans.append("%d-%02d..%d-%02d" % (a // 12, a % 12 or 12,
                                               b // 12, b % 12 or 12))
            start = str(r[0])[:7]

        prev = cur

    return spans, start


def pct(rows, months):
    """Return over the trailing `months` months, or None when history is shorter."""
    if len(rows) <= months:
        return None

    try:
        a = float(rows[-1 - months][2])
        b = float(rows[-1][2])
    except (ValueError, IndexError, TypeError):
        return None

    return (b / a - 1.0) * 100.0 if a else None


# Codes are guesses by class. Treasury and credit indices first because those are
# the ones the user named, then bond ETFs as the fallback when an index is dead.
CANDIDATES = [
    ("sh000833", "中高企债"),
    ("sz399301", "深信用债"),
    ("sz399302", "深公司债"),
    ("sz399307", "深证转债"),
    ("sz399413", "国证转债"),
    ("sz399923", "公司债"),
    ("sz399289", "碳中和债"),
    ("sz399290", "深转交债"),
    ("sh000012", "上证国债"),
    ("sh000013", "上证企债"),
    ("sh000022", "沪公司债"),
    ("sh000832", "中证转债"),
    ("sh000923", "公司债指"),
    ("sh000023", "全债?(实测名 沪分离债, 停更)"),
    ("sh000145", "国债?(实测名 优势资源)"),
    ("sh000140", "上证10年国债?"),
    ("sh000141", "上证5年国债?"),
    ("sh000139", "上证5年国债?"),
    ("sh000061", "沪企债30?"),
    ("sh000926", "中证全债?"),
    ("sh000922", "中证公司债?"),
    ("sh000924", "中证公司债?"),
    ("sh000925", "中证债?"),
    ("sz399481", "深证企债?"),
    ("sz399482", "深证国债?"),
    ("sz399483", "深证债?"),
    ("sh511010", "国债ETF"),
    ("sh511260", "十年国债ETF"),
    ("sh511090", "30年国债ETF"),
    ("sh511130", "30年国债ETF?"),
    ("sh511020", "活跃国债ETF?"),
    ("sh511030", "公司债ETF?"),
    ("sh511070", "信用债ETF?"),
    ("sh511220", "城投债ETF"),
    ("sh511360", "短融ETF?"),
    ("sh511380", "可转债ETF"),
    ("sh511180", "可转债ETF?"),
    ("sh019547", "国债现券?"),
]


# The eight that survived: names the snapshot confirms are bonds, monthly series that
# reach the present, and no hole inside a ten-year window.
POOL = [
    ("sh000012", "国债指数"),
    ("sh000013", "企债指数"),
    ("sh000022", "沪公司债"),
    ("sh000061", "沪企债30"),
    ("sh000832", "中证转债"),
    ("sh000139", "上证转债"),
    ("sz399307", "深证转债"),
    ("sz399301", "深信用债"),
    ("sz399302", "深公司债"),
]


def race(rows_by_code, months=120):
    """Replay the board the way the renderer will, to see whether it reorders.

    A bar race is only worth a page if the order changes; eight bond indices that
    all gain forty-some per cent over a decade would be a table with animation on
    it. Each row joins on the month its own history starts and is measured from
    there — the rule the asset race already uses — so count how often the leader
    changes hands and how far each row travels.
    """
    series = {}

    for code in rows_by_code:
        rows = settled(rows_by_code[code] or [])

        if len(rows) < 2:
            continue

        series[code] = rows[-months:] if len(rows) > months else rows

    span = max((len(r) for r in series.values()), default=0)

    if span == 0:
        return None

    order = []
    leaders = []
    seen = set()

    for i in range(span):
        board = []

        for code, rows in series.items():
            if i >= len(rows):
                continue

            base = float(rows[0][2])

            try:
                value = (float(rows[i][2]) / base - 1.0) * 100.0
            except (ValueError, ZeroDivisionError, TypeError):
                continue

            board.append((value, code))

        if len(board) < 2:
            continue

        board.sort(reverse=True)
        top = board[0][1]

        if leaders and leaders[-1] != top:
            seen.add(top)

        leaders.append(top)
        order.append([c for _, c in board])

    travel = {}

    for code in series:
        places = [row.index(code) + 1 for row in order if code in row]

        if places:
            travel[code] = (min(places), max(places))

    final = [(round((float(rows[-1][2]) / float(rows[0][2]) - 1.0) * 100.0, 2), code)
             for code, rows in series.items() if len(rows) > 1]
    final.sort(reverse=True)

    return span, leaders, travel, sorted(seen), final


def main():
    codes = [c for c, _ in CANDIDATES]
    label = names(codes)
    guess = {c: g for c, g in CANDIDATES}

    print("月度序列 (newfqkline, 已按应用规则丢弃未完成月)")
    print("代码       快照真名            月数  起点     末月     末值       十年      五年     缺月")

    for code in codes:
        rows = settled(series(code) or [])
        real = label.get(code, "(快照无)")
        flag = "" if guess[code] == real else "  <-- 名不副实"

        if not rows:
            print(f"{code:<10}  {real:<16}  -     -        -        -          -         -        -"
                  f"{flag}")
            continue

        first = str(rows[0][0])[:7]
        last = str(rows[-1][0])[:7]
        close = rows[-1][2]
        y10 = pct(rows, 120)
        y5 = pct(rows, 60)

        def fmt(v):
            return "-" if v is None else f"{v:+.2f}%"

        print(f"{code:<10}  {real:<16}  {len(rows):<4}  {first}  {last}  {close:<9}  "
              f"{fmt(y10):<8}  {fmt(y5):<7}  {gaps(rows)}{flag}")

    print()
    print("缺口位置 (洞在动画窗口里 = 条形会跳)")
    print("代码       快照真名            缺月  缺口区间")

    for code in codes:
        rows = settled(series(code) or [])
        real = label.get(code, "(快照无)")

        if not rows:
            continue

        spans, _ = holes(rows)
        print(f"{code:<10}  {real:<16}  {gaps(rows):<4}  " + (", ".join(spans) or "-"))

    print()
    print("日线可得性 (竞速页的短区间档位要用)")

    for code in codes:
        rows = series(code, period="day", count=640) or []
        real = label.get(code, "(快照无)")

        if not rows:
            print(f"{code:<10}  {real:<16}  日线 无")
            continue

        print(f"{code:<10}  {real:<16}  日线 {len(rows)} 根  "
              f"{str(rows[0][0])} -> {str(rows[-1][0])}")

    print()
    print("竞速模拟 (各行从自己首月起算, 看名次会不会变)")

    rows_by_code = {c: series(c) for c, _ in POOL}
    labels = dict(POOL)

    for months in (120, 60, 36):
        out = race(rows_by_code, months)

        if out is None:
            print(f"  近{months}月: 无数据")
            continue

        span, leaders, travel, winners, final = out
        changes = sum(1 for a, b in zip(leaders, leaders[1:]) if a != b)

        print(f"  近{months}月 ({span} 帧): 领先者易主 {changes} 次, "
              f"先后由 {len(winners)} 个标的领跑 -> {', '.join(labels[c] for c in winners)}")

        if months == 120:
            print("      末帧 (各自起点起算):")

            for value, code in final:
                best, worst = travel[code]
                print(f"         {labels[code]:<8} {value:+7.2f}%   名次 {best}..{worst}")


if __name__ == "__main__":
    main()
