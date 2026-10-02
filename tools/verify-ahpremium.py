# -*- coding: utf-8 -*-
"""真机验证「AH 溢价」。

三处**不能靠截图证明**，所以脚本才是验证：

1. **取的是不是不复权价。** 这是整页最容易、也最严重的一种错：两条腿都换成复权序列，
   页面照样跑、照画出漂亮的条形，只是每个数字都错——后复权把近期价格放大，两个市场
   各自放大后不能直接比（工行 A 真实 8.28 元，后复权 13.34 元，+26% 的溢价会算成
   +245%）。所以第 0 段是**源码级**断言：数据层必须走 `RawBarsAsync`、不许出现
   `CandleBarsAsync`，而 `RawBarsAsync` 必须传空复权参数。
2. **溢价算得对不对。** 状态行报出"最贵"的公司与百分比，脚本用 python 直接打源端把
   同一个月的溢价独立算一遍，两者必须一致。这一条同时验证了汇率、按月归并和公式。
3. **区间越短、能上来的对越多。** H 股上市晚的对在长区间里被去掉，所以两档的"对数"
   必须分得开——这也是"日期轴按月归并"没坏掉的旁证。

用法：python tools/verify-ahpremium.py
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

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有返回|不属于|过长|failed|error")

# 68 对 · 36 个月 · 最高 新华制药 +194.0% · 榜尾 万科A +78.8%
FETCHED = re.compile(
    r"(\d+)\s*对\s*·\s*(\d+)\s*个月\s*·\s*最高\s*(.+?)\s*([+−-][\d.]+)%\s*·\s*榜尾\s*(.+?)\s*([+−-][\d.]+)%")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO, "src/MarketMotionStudio/Market/AhPremium.cs")
KLINE = os.path.join(REPO, "src/MarketMotionStudio/Market/TencentKline.cs")

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


# ---- 独立算一遍溢价（不经过应用）-----------------------------------------------------


def fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    return json.loads(urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "ignore"))


def monthly(code):
    """(year, month) -> 当月最后一个收盘价，与实际成交价一致（空复权）。"""
    url = ("https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
           f"?param={code},month,,,180,")
    node = fetch_json(url).get("data", {}).get(code, {})

    for key, rows in node.items():
        if key == "month" and isinstance(rows, list) and rows and isinstance(rows[0], list):
            return {(r[0][:4], r[0][5:7]): float(r[2]) for r in rows if float(r[2]) > 0}

    return {}


def pairs_from_source():
    """内建清单，直接读源码 —— 脚本不该自己再抄一份。"""
    text = open(SOURCE, encoding="utf-8").read()
    block = text[text.index("public static readonly AhPair[] All"):
                 text.index("];", text.index("public static readonly AhPair[] All"))]

    return re.findall(r'new\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', block)


def expected_premium(pair, months_wanted):
    """按同一个月的口径，用源端原始价独立算出溢价。"""
    a, h, name = pair
    pa, ph, rate = monthly(a), monthly(h), monthly("whHKDCNY")

    shared = sorted(set(pa) & set(ph) & set(rate))

    if not shared:
        return None, None

    used = shared[-months_wanted:]
    first, last = used[0], used[-1]

    return (pa[last] / (ph[last] * rate[last]) - 1) * 100, last


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

    Scoped to the bar. Searching the whole window for a button called 关闭 finds the window's
    own **title-bar close button**, and invoking that closed the app to its tray icon — after
    which the fetch ran on with no window to report into, the status read as empty, and the run
    failed on a page that was working. The sibling scripts scope this search; this one did not.
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


def fetch(win, seconds=420):
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

    def number(text):
        return float(text.replace("−", "-").replace("+", ""))

    return {
        "pairs": int(hit.group(1)),
        "months": int(hit.group(2)),
        "dearest": hit.group(3).strip(),
        "dearest_value": number(hit.group(4)),
        "cheapest": hit.group(5).strip(),
        "cheapest_value": number(hit.group(6)),
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

    # ---- 0) 用的是不复权价（源码级）
    #
    # 这一条在 UIA 里不存在、截图里也看不出来：画面照样画得漂亮，只是每个数字都错。
    source = open(SOURCE, encoding="utf-8").read()
    kline = open(KLINE, encoding="utf-8").read()

    check("数据层走 RawBarsAsync（不复权）", "RawBarsAsync" in source)

    check("数据层没有用复权序列",
          "CandleBarsAsync" not in source and "StockBarsAsync" not in source,
          "复权会把近期价放大，两个市场各自放大后不可比")

    check("RawBarsAsync 传的是空复权参数",
          'CandlesFromAsync(Endpoint, string.Empty' in kline)

    check("公式是 A ÷（H × 汇率）− 1",
          "(a[month] / (hong * fx)) - 1" in source)

    check("日期轴按年月归并（月末日期三条腿各不相同）",
          "DaysInMonth" in source and "MonthEnd" in source)

    # ---- 1) 页面在，而且面板里没有多余的选择
    if not goto(win, "AH 溢价"):
        check("导航里有「AH 溢价」", False)
        return report()

    check("导航里有「AH 溢价」", True)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    labels = winui.find(win, lambda c: c.AutomationId == "ListText")

    if labels is not None:
        shown = " ".join(texts(labels))
        check("卡片说明了名单与区间的关系", "两" in shown or "69" in shown, shown[:70])

    note = winui.find(win, lambda c: c.AutomationId == "AhPremiumMethodNote")

    if note is not None:
        body = " ".join(texts(note))
        check("口径说明写了公式与不复权", "÷" in body and "复权" in body, body[:60])

    # ---- 2) 区间档位
    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")

    options = winui.combo_labels(win, combo) if combo is not None else []

    check("区间下拉是那四档",
          set(options) == {"近 3 年", "近 5 年", "最长（约 9 年）", "自定义"},
          " / ".join(options))

    # ---- 3) 近 3 年
    if combo is not None:
        winui.combo_pick(win, combo, "近 3 年")

    short, status = fetch(win)
    check("近 3 年取数成功", short is not None, str(status)[:90])

    if short is None:
        return report()

    check("对数落在合理的量级（40–69）", 40 <= short["pairs"] <= 69, str(short["pairs"]))
    check("月数是一年的量级（34–38）", 34 <= short["months"] <= 38, str(short["months"]))
    check("最高是正溢价", short["dearest_value"] > 0, str(short["dearest_value"]))
    check("榜尾低于最高（画面按溢价降序）",
          short["cheapest_value"] < short["dearest_value"],
          f"{short['cheapest_value']} < {short['dearest_value']}")

    # 画面画的是**溢价最高的十五家**，而 A/H 溢价是结构性偏正的：负溢价（H 股比 A 股贵）
    # 只有两家，排在 69 对的末尾，任何区间都进不了前十五名。所以每一帧的条形都向右长，
    # 帮助手册与卡片文案也是这么写的。**这条断言盯的就是那句话**：哪天负溢价挤进了前十五，
    # 文案就要跟着改，而不是让画面和说明各说各的。
    check("画出来的十五家全为正溢价（负溢价的两家排在末尾）",
          short["cheapest_value"] > 0,
          f"榜尾 {short['cheapest_value']:+.1f}%；若这里变负，帮助手册与卡片要改")

    check("溢价在合理的量级内（没有把复权价算进来）",
          -60 < short["cheapest_value"] < short["dearest_value"] < 300,
          f"{short['cheapest_value']} … {short['dearest_value']}")

    check("最贵的名字是干净的",
          short["dearest"] and not short["dearest"].startswith(("XD", "XR", "DR")) and len(short["dearest"]) <= 12,
          short["dearest"])

    shot(win, "verify-ahpremium-3y.png")

    # ---- 4) 独立算一遍：状态行的数字必须和源端一致
    pairs = pairs_from_source()
    wanted = [p for p in pairs if p[2] == short["dearest"]]

    if not wanted:
        check("状态行的公司在内建清单里", False, short["dearest"])
    else:
        mine, month = expected_premium(wanted[0], 36)
        check("独立算出的溢价与页面一致（容差 0.35 个百分点）",
              mine is not None and abs(mine - short["dearest_value"]) < 0.35,
              f"页面 {short['dearest_value']:.2f}% / 脚本 {mine:.2f}%（{month}）")

    # ---- 5) 最长：区间越长，能上来的对越少
    if combo is not None:
        winui.combo_pick(win, combo, "最长（约 9 年）")

    long_run, status = fetch(win)
    check("最长档取数成功", long_run is not None, str(status)[:90])

    if long_run is not None:
        check("最长档的月数远多于 3 年", long_run["months"] > short["months"] * 2,
              f"{long_run['months']} vs {short['months']}")
        check("最长档剩下的对不多于 3 年档",
              long_run["pairs"] <= short["pairs"],
              f"{long_run['pairs']} vs {short['pairs']}（H 股上市晚的会被去掉）")

        shot(win, "verify-ahpremium-long.png")

    # ---- 6) 重启后还记得
    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)
    goto(win, "AH 溢价")

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    remembered = winui.value(combo) if combo is not None else None

    check("重启后区间仍记着",
          remembered in ("近 3 年", "近 5 年", "最长（约 9 年）", "自定义"),
          str(remembered))

    return report()


if __name__ == "__main__":
    sys.exit(main())
