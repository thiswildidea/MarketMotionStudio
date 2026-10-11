# -*- coding: utf-8 -*-
"""两个源到底握着一个币多久的日线 —— 「最长」那一档真正的尽头是哪一天。

**不放大上限时**量到的是应用自己的十年：`YahooMostDays = 3650` 下这一档就是
2016-10-13 起、共 3650 天。要看源端的尽头，先把 `CryptoQuotes.YahooMostDays`
临时放大（`5000` 就够，BTC 的第一根在 2014-09-17）：

    1. `Market/CryptoQuotes.cs`：`YahooMostDays = 3650` → `5000`
    2. 杀进程 → `dotnet build … -p:Platform=x64 -p:Configuration=Debug` → 注册
    3. `python tools/probe-crypto-source-floor.py`
    4. 改回 3650，再编译注册一次（那一步不能忘，否则留在机器上的是一个被放大过的版本）

实测 2026-10-11：放大到 5000 后，定投区间=最长 回报
「2 份计划 · 4407 天（2014-09-17 至 2026-10-11）」—— 即 Yahoo 上 BTC 的第一根
日线是 2014-09-17（ETH 更晚，板取两只的并集，所以起点是 BTC 的）。
截图按当时的 `YahooMostDays` 命名（`crypto-source-floor-5000d.png`）。

为什么要用「加密定投页 + 定投区间=最长」：那一档的区间就是 `(Oldest, today)`，而
`Oldest` 是 `today - YahooMostDays`。放大上限之后那里问的就是「源端从头给我」，
状态行回报的起始日就是源端第一根日线的日期。

日期框（DatePicker）读不出也写不进（只有 FlyoutButton 与一串文本，没有可设值的
模式），所以「自定义 + 自己填一个很早的起始日」这条路走不通 —— 档位下拉可以按名字
选，这就是这个探针走档位不走日期框的原因。

    python tools/probe-crypto-source-floor.py
"""
import re
import sys
import time

sys.path.insert(0, r"D:\software\MarketMotionStudio\tools")

import winui

SOURCE = r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Market\CryptoQuotes.cs"

with open(SOURCE, encoding="utf-8") as handle:
    MOST_DAYS = int(re.search(r"YahooMostDays = (\d+)", handle.read()).group(1))

OUT = r"D:\software\MarketMotionStudio\artifacts\crypto-source-floor-%dd.png" % MOST_DAYS

print("YahooMostDays =", MOST_DAYS, "→", OUT)


def find(control, condition, depth=0, limit=25):
    if control is None or depth > limit:
        return None

    try:
        if condition(control):
            return control
    except Exception:  # noqa: BLE001
        return None

    for child in control.GetChildren():
        found = find(child, condition, depth + 1, limit)

        if found is not None:
            return found

    return None


def find_all(control, condition, depth=0, limit=25, out=None):
    out = [] if out is None else out

    if control is None or depth > limit:
        return out

    try:
        if condition(control):
            out.append(control)
    except Exception:  # noqa: BLE001
        return out

    for child in control.GetChildren():
        find_all(child, condition, depth + 1, limit, out)

    return out


def status_text(win):
    bar = find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return None

    texts = [t.Name for t in find_all(bar, lambda c: c.ControlTypeName == "TextControl", limit=8)
             if t.Name]

    return max(texts, key=len) if texts else None


win = winui.app_window("MarketMotionStudio.exe", wait_seconds=5)

if win is None:
    win = winui.launch("MarketMotionStudio.exe", wait_seconds=60)

assert win is not None, "窗口未找到"

win.SetActive()
time.sleep(1.0)

nav = winui.find_all(win, lambda c: c.ControlTypeName == "ListItemControl", limit=14)
print("导航项:", [i.Name for i in nav])

for item in nav:
    if item.Name and "定投" in item.Name:
        winui.invoke_click(item)
        time.sleep(1.5)
        break

combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
assert combo is not None, "定投区间下拉未找到"

print("可选:", winui.combo_labels(win, combo))
print("选中:", winui.combo_pick(win, combo, "最长"))

fetch = winui.find(win, lambda c: c.AutomationId == "FetchButton")
assert fetch is not None, "取数按钮未找到"

winui.invoke_click(fetch)

# 一个通用的「有结论了」判据：状态行里出现某个数字加单位。币的页面说的是「天」，
# 股票的页面说「个交易日」/`trading days` —— 这里只关心它不再停在「正在取数」。
deadline = time.time() + 600
seen = None

while time.time() < deadline:
    text = status_text(win)

    if text and text != seen:
        seen = text
        print("  状态行:", text)

        if any(unit in text for unit in ("天", "days", "根", "bars")):
            break

    time.sleep(2)

print("截图:", winui.shot(win, OUT))
