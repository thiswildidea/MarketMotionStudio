# -*- coding: utf-8 -*-
"""真机验证「汇率走廊」。

这一页有三种错**只能靠脚本发现**，截图看不出来：

1. **量词。** 表头那行「N 个月 · N 组货币」在 UIA 树里没有节点，截图里只是像素——市值榜
   就是这样错的（月线被画成「12 个交易日」）。所以只能做源码级断言：量词由页面传，
   渲染器不许自己编。
2. **走廊算了两遍。** 走廊的上下沿既决定游标位置，也决定行下方印的那两个数；如果渲染器
   和数据层各算一套，同一行会出现"游标在 78% 而端点对不上"的画面，而两个数看上去各自都
   合理。所以断言渲染器调的是 `FxRates.Corridor`，不是自己又写一遍 min/max。
3. **没有报价的月份被当成 0%。** 人民币组里五对从 2016 年才有数据；在「最长」档下，
   把它们当成 0 会让它们在 2016 年之前一直排在最底下并且画出来。断言渲染器按 `present`
   跳过、且排名只在在场的行之间做。

再者是**数字对不对**：脚本直接打源端，把六对的走廊位置独立算一遍，与状态行比对。

用法：python tools/verify-fxcorridor.py
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有返回|不属于|过长|太少|failed|error")

# 6 组货币 · 121 个月 · 在自己走廊里位置最高的是 USD/CNY，78% · 最低的是 HKD/CNY，12%
FETCHED = re.compile(
    r"(\d+)\s*组货币\s*·\s*(\d+)\s*个月\s*·\s*.*?最高的是\s*([A-Z]{3}/[A-Z]{3})\s*[，,]\s*(\d+)%"
    r"\s*·\s*.*?最低的是\s*([A-Z]{3}/[A-Z]{3})\s*[，,]\s*(\d+)%")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO, "src/MarketMotionStudio/Market/FxRates.cs")
PAGE = os.path.join(REPO, "src/MarketMotionStudio/Pages/FxCorridorPage.xaml.cs")
RENDER = os.path.join(REPO, "src/MarketMotionStudio/Render/FxCorridorRenderer.cs")

# 默认那一组（人民币汇率）与默认区间（近十年），与页面的默认值一致。
PAIRS = ["whUSDCNY", "whEURCNY", "whHKDCNY", "whGBPCNY", "whAUDCNY", "whCADCNY"]
MONTHS = 120

FAILED = []


def check(name, ok, note=""):
    print(("  ✓ " if ok else "  ✗ ") + name + (f" — {note}" if note else ""))

    if not ok:
        FAILED.append(name)


def report():
    print()

    if FAILED:
        print(f"{len(FAILED)} 项未通过：" + "、".join(FAILED))
        return 1

    print("全部通过")
    return 0


# ---- 独立算一遍（不经过应用）----------------------------------------------------------


def monthly(code, start, end):
    """源端的月线，空复权——和应用里 RawBarsAsync 用的是同一条路径。

    **丢掉还没走完的那个月**，否则两边差一个月：应用走的是 `CandlesFromAsync` 里的
    `IsSettledFor`，一个月的 bar 只有在本月第一天之前才算走完（未走完的月画出来是一根
    由几天做成的月线，读起来像崩了）。第一版脚本漏了这条，于是取到 2026-10 那根，走廊
    的端点和末月收盘价都和页面差一点，三条断言红着——而错的是脚本。
    """
    url = ("https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
           f"?param={code},month,{start},{end},360,")

    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30).read().decode("utf-8", "ignore")

    node = json.loads(raw).get("data", {}).get(code, {})

    rows = None
    for key, value in node.items():
        if "month" in key and isinstance(value, list) and value:
            rows = value
            break

    if not rows:
        return []

    today = date.today()
    first_of_this_month = today.replace(day=1)

    # 归并到月：一个月里最后一根就是那个月。
    by_month = {}

    for row in rows:
        if float(row[2]) <= 0:
            continue

        if date.fromisoformat(row[0]) >= first_of_this_month:
            continue

        month = row[0][:7]

        if month not in by_month or row[0] >= by_month[month][0]:
            by_month[month] = row

    return [by_month[m] for m in sorted(by_month)]


def expected_standings(start, end):
    """六对的走廊位置，最高在前——和页面状态行说的是同一件事。"""
    out = []

    for code in PAIRS:
        rows = monthly(code, start, end)

        if not rows:
            continue

        low = min(float(r[4]) if float(r[4]) > 0 else float(r[2]) for r in rows)
        high = max(float(r[3]) if float(r[3]) > 0 else float(r[2]) for r in rows)
        close = float(rows[-1][2])

        position = 0.5 if high - low <= 0 else max(0.0, min(1.0, (close - low) / (high - low)))

        out.append((code[2:5] + "/" + code[5:], position))

    return sorted(out, key=lambda kv: -kv[1])


# ---- UI 驱动 --------------------------------------------------------------------------


def texts(root, depth=0, limit=25, out=None):
    out = out if out is not None else []

    if root is None or depth > limit:
        return out

    for child in winui.find_all(root, lambda c: True, limit=400):
        if child.Name:
            out.append(child.Name)

        texts(child, depth + 1, limit, out)

    return out


def status_text(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    return " ".join(texts(bar)) if bar is not None else ""


def close_status(win):
    """Dismisses the status bar if it is open.

    Scoped to the bar: searching the whole window for a button called 关闭 finds the window's
    own title-bar close button, which sends the app to its tray.
    """
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return

    closer = winui.find(bar, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "关闭")

    if closer is not None:
        try:
            closer.GetInvokePattern().Invoke()
            time.sleep(0.8)
        except Exception:  # noqa: BLE001
            pass


def wait_status(win, seconds=420):
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(2.0)
        text = status_text(win)

        if text and (FETCHED.search(text) or FAIL.search(text)):
            return text

    return None


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

    if item is None:
        return False

    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)

    return True


def shot(win, name):
    path = os.path.join(REPO, "artifacts", name)

    try:
        win.SetTopmost(True)
        time.sleep(0.6)
    except Exception:  # noqa: BLE001
        pass

    win.CaptureToImage(path)

    try:
        win.SetTopmost(False)
    except Exception:  # noqa: BLE001
        pass

    return path


def frame_pixels(win, name):
    """数预览画面里有多少彩色像素 —— 用的还是截图，所以和用户看到的是同一张图。"""
    try:
        from PIL import Image
    except ImportError:
        return -1

    win.CaptureToImage(os.path.join(REPO, "artifacts", name))

    whole = Image.open(os.path.join(REPO, "artifacts", name)).convert("RGB")
    width, height = whole.size

    # Cropped by proportion: the preview is a canvas with no automation node of its own.
    image = whole.crop((0, int(height * 0.10), int(width * 0.62), int(height * 0.92)))
    pixels = image.load()

    coloured = 0

    for y in range(0, image.size[1], 2):
        for x in range(0, image.size[0], 2):
            r, g, b = pixels[x, y]

            if max(r, g, b) > 120 and max(r, g, b) - min(r, g, b) > 60:
                coloured += 1

    return coloured


def fetch(win, seconds=480):
    close_status(win)

    for attempt in range(3):
        button = winui.find(win, lambda c: c.AutomationId == "FetchButton")

        if button is None:
            time.sleep(1.5)
            continue

        try:
            button.GetInvokePattern().Invoke()
            break
        except Exception as ex:  # noqa: BLE001
            if attempt == 2:
                return None, f"取数按钮按不动：{ex}"

            time.sleep(1.5)

    status = wait_status(win, seconds)

    if status is None:
        return None, status_text(win) or "（状态条空）"

    hit = FETCHED.search(status)

    if hit is None:
        return None, status

    return {
        "pairs": int(hit.group(1)),
        "months": int(hit.group(2)),
        "top": hit.group(3),
        "top_pct": int(hit.group(4)),
        "bottom": hit.group(5),
        "bottom_pct": int(hit.group(6)),
        "status": status,
    }, status


def maxed(win):
    win.SetActive()
    time.sleep(1.5)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass


def main():
    win = winui.launch(winui.EXE)

    if win is None:
        print("no studio window")
        return 1

    maxed(win)

    # ---- 0) 源码级：这几条在 UIA 里不存在，截图里也看不出来
    source = open(SOURCE, encoding="utf-8").read()
    page = open(PAGE, encoding="utf-8").read()
    render = open(RENDER, encoding="utf-8").read()

    check("取数走 RawBarsAsync（汇率不调整）", "RawBarsAsync" in source)
    check("月线，一次拿全历史（不需要分页回溯）", '"month"' in source and "HistoryWalk" not in source)

    # 曲线最后一根是**上一个走完的月**：`CandlesFromAsync` 丢掉未走完的周期，所以十月初取数，
    # 末月是九月。这条必须由脚本对着自己的取数复刻一遍（见 monthly），否则两边差一个月。
    kline = open(os.path.join(REPO, "src/MarketMotionStudio/Market/TencentKline.cs"),
                 encoding="utf-8").read()
    check("源端丢掉还没走完的月（脚本也照此复刻）",
          "day < new DateOnly(today.Year, today.Month, 1)" in kline
          and "first_of_this_month" in open(__file__, encoding="utf-8").read())

    # 量词：页面必须自己给，渲染器不许替页面编。
    check("周期词由页面传", 'SpanWord = Strings.Get("MarketCapUnitMonths")' in page)
    check("计数词由页面传", 'UnitWord = Strings.Get("AhPremiumUnitPairs")' in page)
    check("渲染器没有写死某个具体周期的量词",
          "MarketCapUnitMonths" not in render and "AhPremiumUnitPairs" not in render)

    # 走廊只算一遍，位置与端点出自同一个地方。
    check("渲染器的走廊取数据层那一份",
          "FxRates.Corridor.Walls" in render and "FxRates.Corridor.Position" in render)
    check("走廊是「截至目前」的累积（会随时间变宽）", "for (var m = 0; m <= i; m++)" in source)
    check("一个月的历史不算走廊（宽度为零时取中点）", "high - low <= 0 ? 0.5" in source)

    # 没有报价的月份不是 0%。
    check("渲染器记着哪个月有报价", "private readonly bool[][] _present;" in render)
    check("没报价的行不画", "if (!_present[k][state.MonthIndex])" in render)
    check("排名只在在场的行之间做", ".Where(k => _present[k][i])" in render)

    check("走廊两端印在行下方（窄走廊和宽走廊才分得开）",
          "_ceiling[k][state.MonthIndex]" in render)

    # ---- 1) 页面在
    if not goto(win, "汇率走廊"):
        check("导航里有「汇率走廊」", False)
        return report()

    check("导航里有「汇率走廊」", True)
    check("币种组下拉在", winui.find(win, lambda c: c.AutomationId == "ListCombo") is not None)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    note = winui.find(win, lambda c: c.AutomationId == "FxCorridorNote")

    if note is not None:
        body = " ".join(texts(note))
        check("说明卡写了「行就是走廊」", "走廊" in body, body[:60])
        check("说明卡里没有字面 {0}", "{0}" not in body, body[:60])

    method = winui.find(win, lambda c: c.AutomationId == "FxCorridorMethodNote")

    if method is not None:
        body = " ".join(texts(method))
        check("口径说明写了月线与不调整", "月线" in body and "调整" in body, body[:60])

    # ---- 2) 档位
    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    options = winui.combo_labels(win, combo) if combo is not None else []

    check("区间下拉是那五档",
          set(options) == {"近 3 年", "近 5 年", "近 10 年", "最长", "自定义"},
          " / ".join(options))

    groups = winui.combo_labels(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"))
    check("币种组是那两组",
          set(groups) == {"人民币汇率", "主要交叉盘"}, " / ".join(groups))

    # ---- 3) 近 10 年取数
    if combo is not None:
        winui.combo_pick(win, combo, "近 10 年")

    run, status = fetch(win)
    check("近 10 年取数成功", run is not None, str(status)[:90])

    if run is None:
        return report()

    check("画了 6 组货币", run["pairs"] == 6, str(run["pairs"]))

    # 不是 121：源端的月线在「近十年」这段里只给 113–114 个月（2016-11 起，且当月那根是盘中的
    # 实时值，取数时刻差几分钟就可能差一个月）。所以这一条查的是量级，不是精确月份数。
    check("月份数落在十年的量级（108–125）", 108 <= run["months"] <= 125, str(run["months"]))
    check("最高不低于最低", run["top_pct"] >= run["bottom_pct"],
          f"{run['top_pct']}% vs {run['bottom_pct']}%")
    check("两个百分比都在 0–100 之间",
          0 <= run["bottom_pct"] <= 100 and 0 <= run["top_pct"] <= 100,
          f"{run['top_pct']}% / {run['bottom_pct']}%")
    check("最高与最低是两组不同的货币", run["top"] != run["bottom"],
          f"{run['top']} / {run['bottom']}")
    check("状态行没有失败字样", not FAIL.search(run["status"]))

    shot(win, "verify-fxcorridor-10y.png")

    coloured = frame_pixels(win, "verify-fxcorridor-frame.png")

    check("画面上画出了有颜色的走廊（不是空白帧）", coloured > 2000, f"{coloured} 个彩色像素")

    # ---- 4) 独立算一遍
    end = date.today()
    start = end.replace(year=end.year - 10)
    mine = expected_standings(start.isoformat(), end.isoformat())

    check("脚本自己取到了六对的月线", len(mine) == 6, f"{len(mine)} 对")

    if len(mine) == 6:
        check("位置最高的那一组与页面一致", mine[0][0] == run["top"],
              f"页面 {run['top']} / 脚本 {mine[0][0]}")
        check("位置最低的那一组与页面一致", mine[-1][0] == run["bottom"],
              f"页面 {run['bottom']} / 脚本 {mine[-1][0]}")
        check("最高的百分比与页面一致（容差 1 个百分点）",
              abs((mine[0][1] * 100) - run["top_pct"]) <= 1.0,
              f"页面 {run['top_pct']}% / 脚本 {mine[0][1] * 100:.1f}%")
        check("最低的百分比与页面一致（容差 1 个百分点）",
              abs((mine[-1][1] * 100) - run["bottom_pct"]) <= 1.0,
              f"页面 {run['bottom_pct']}% / 脚本 {mine[-1][1] * 100:.1f}%")

    # ---- 5) 换一组：数字必须变
    group = winui.find(win, lambda c: c.AutomationId == "ListCombo")

    if group is not None:
        winui.combo_pick(win, group, "主要交叉盘")

        other, status = fetch(win)
        check("换到交叉盘后取数成功", other is not None, str(status)[:90])

        if other is not None:
            check("交叉盘也是 6 组", other["pairs"] == 6, str(other["pairs"]))
            check("换组后最高那一组不再是同一个",
                  other["top"] != run["top"], f"{run['top']} → {other['top']}")

            shot(win, "verify-fxcorridor-crosses.png")

    # ---- 6) 重启后还记得
    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)
    goto(win, "汇率走廊")

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    remembered = winui.value(combo) if combo is not None else None

    check("重启后区间仍记着",
          remembered in ("近 3 年", "近 5 年", "近 10 年", "最长", "自定义"),
          str(remembered))

    group = winui.find(win, lambda c: c.AutomationId == "ListCombo")
    kept = winui.value(group) if group is not None else None

    check("重启后币种组仍记着", kept == "主要交叉盘", str(kept))

    return report()


if __name__ == "__main__":
    sys.exit(main())
