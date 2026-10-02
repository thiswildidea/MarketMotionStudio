# -*- coding: utf-8 -*-
"""真机验证四个页面的数据区间：档位是否覆盖到接口实际能给的范围。

这一页组的错法是同一个，而且**画面上看不出来**：区间比接口能给的长，源端就只把最近的一段
交出来（`tools/probe-range-limits.py` 实测：日线一次给 640 **根**，不是 640 天），于是图表
短一截而看起来完全正常。反过来也成立：区间比接口能给的短，是白丢能力——K线日线走分页能到
约 15 年，菜单却停在 3 年。

所以这里验两件事，缺一不可：

  1. 菜单里有没有那一档（UIA 里读得到，源码里也断得到）；
  2. 选了最长的那一档，真的取得到数（真机取数，状态行不出错）。

第 2 条是主要的：一个能选但取不到的档位，比没有这一档更坏。

用法：python tools/verify-range-limits.py
"""
import os
import re
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有返回|过长|太少|failed|error")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))

    print(f"  {'✓' if ok else '✗'} {name}" + (f" — {detail}" if detail else ""))
    sys.stdout.flush()


def report():
    bad = [c for c in CHECKS if not c[1]]

    print()
    if bad:
        print(f"{len(bad)} 项未通过：" + "、".join(c[0] for c in bad))
        return 1

    print("全部通过")
    return 0


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8-sig") as handle:
        return handle.read()


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

    if item is None:
        return False

    item.GetSelectionItemPattern().Select()
    time.sleep(2.0)

    return True


def open_popup_items(win):
    """打开着那个下拉的项，从根窗口的浮层里读（浮层是另一个顶层窗口，按进程号认）。"""
    found = []

    for top in auto.GetRootControl().GetChildren():
        if top.ProcessId != win.ProcessId:
            continue

        found += winui.find_all(top, lambda c: c.ControlTypeName == "ListItemControl" and c.Name)

    return found


def combo_labels(win, automation_id):
    """一个下拉的全部选项名，读完把它收起来。"""
    combo = winui.find(win, lambda c: c.AutomationId == automation_id)

    if combo is None:
        return None, None

    combo.GetExpandCollapsePattern().Expand()
    time.sleep(1.0)

    labels = [i.Name for i in open_popup_items(win)]

    combo.GetExpandCollapsePattern().Collapse()
    time.sleep(0.6)

    return combo, labels


def combo_pick(win, combo, name):
    """按下拉选项的名字选，不按位置 —— 位置会随档位增减而变。"""
    combo.GetExpandCollapsePattern().Expand()
    time.sleep(1.0)

    items = [i for i in open_popup_items(win) if i.Name == name]

    if not items:
        combo.GetExpandCollapsePattern().Collapse()
        return None

    items[0].GetSelectionItemPattern().Select()
    time.sleep(1.2)

    return items[0].Name


def status(win):
    """状态行的消息。

    InfoBar 的文本节点是 `[图标字形, '“成功”图标', '', '2462 根日K（…）', '关闭按钮字形']` —— 中间
    **有一个空名的节点**，不过滤空串的话所谓「第三个」读到的是那个空的，于是等取数等到超时而
    取数其实两秒前就报完了。过滤之后第三个才是消息。
    """
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return ""

    texts = [t.Name for t in winui.find_all(
        bar, lambda c: c.ControlTypeName == "TextControl", limit=8) if t.Name]

    return texts[2] if len(texts) > 2 else " / ".join(texts)


# 取数中途的进度是「贵州茅台 (3/15)」这种，结果才是「根 / 个月 / 个交易日 / 只」。不靠这条
# 区分，一个慢标的就会让脚本把进度当成结果。
DONE = ("根", "个月", "个交易日", "只")


def fetch(win, seconds=300):
    """按取数并等它报出一个结果，返回状态行的消息。"""
    button = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if button is None:
        return None

    button.GetInvokePattern().Invoke()

    deadline = time.time() + seconds
    last = None

    while time.time() < deadline:
        time.sleep(2.0)
        seen = status(win)

        if FAIL.search(seen):
            return seen

        # 稳定下来才算报完：两次读到同一句。
        if seen and any(word in seen for word in DONE) and seen == last:
            return seen

        last = seen

    return last or "(超时)"


def ok(said):
    """一句话：这次取数真的成了。

    超时**不算**成功。「没出错」如果只写成「不含失败字样」，那么一句 (超时) —— 状态行根本没
    读到 —— 也会通过，而它通过的是一项根本没验过的东西。这一轮就是这么被骗过一次的。
    """
    return bool(said) and "超时" not in said and not FAIL.search(said)


def main():
    win = winui.launch(winui.EXE)

    if win is None:
        print("no studio window")
        return 1

    win.SetActive()
    time.sleep(1.0)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass

    # ---- 0) 源码级：这几条在 UIA 里读不到，而它们正是「能不能给」的根据

    kline = read("src/MarketMotionStudio/Market/TencentKline.cs")
    candles = read("src/MarketMotionStudio/Market/CandleSeries.cs")
    caps = read("src/MarketMotionStudio/Market/MarketCaps.cs")
    cap_page = read("src/MarketMotionStudio/Pages/MarketCapPage.xaml.cs")
    sector = read("src/MarketMotionStudio/Pages/SectorRacePage.xaml.cs")
    volume = read("src/MarketMotionStudio/Pages/StockVolumePage.xaml.cs")

    check("「一次请求能盖多少天」是一个常量，不是散落各页的魔法数",
          "public const int MostDaysPerRequest = 900" in kline)
    # 断言的是一句能认出来的话，不是把它整句抄进来 —— 抄进来就连注释里的 markdown 星号一起
    # 要求了，而那不是代码的一部分。
    check("常量旁边写明了它是一次请求的根数折算来的",
          "MostBarsPerRequest" in kline and "not of days" in kline)

    check("日线菜单给到了 5 年", 'new(60, "DcaRange5Y")' in candles)
    check("日线菜单给到了 10 年", 'new(120, "DcaRange10Y")' in candles)

    check("板块竞速用天数常量作上限", "TencentKline.MostDaysPerRequest" in sector)
    check("板块竞速菜单多了 2 年", '(24, "StudioRange24M")' in sector)
    check("板块竞速的日期选择器也停在同一条线上", "FromDate.MinYear = oldest" in sector)

    check("成交量页用同一个天数常量", "TencentKline.MostDaysPerRequest" in volume)
    check("成交量页菜单多了 2 年", '(24, "StudioRange24M")' in volume)
    check("成交量页的日期选择器也停在同一条线上", "FromDate.MinYear = oldest" in volume)

    check("市值榜的上限取自月线自己的常量（不是 walk 的 35 年）",
          "MarketCapSeries.MonthsWanted" in cap_page and "HistoryWalk.MostDays" not in cap_page)
    check("那个常量是公开的，页面才读得到它",
          "public const int MonthsWanted = 180" in caps)
    check("市值榜菜单多了「最长」", '(0, "IndexRaceRangeMax")' in cap_page)
    check("市值榜的「自定义」换了另一个 tag（0 让给了最长）",
          '(CustomMonths, "StudioRangeCustom")' in cap_page and "private const int CustomMonths = -1" in cap_page)

    resw = read("src/MarketMotionStudio/Strings/en-US/Resources.resw")
    check("新档位的文案进了资源（14 语言由 verify-resw-uids 保齐）",
          'name="StudioRange24M"' in resw)

    help_en = read("src/MarketMotionStudio/Assets/Help/help-en-US.md")
    check("板块竞速的帮助跟着改了",
          "1, 3, 6, 12 or 24 months" in help_en)

    # 涨跌日历页那条是同一句话的邻居，**不能**被顺手改掉：它一次只问一个标的、要每一天都有数，
    # 640 天那条保守的线是对的。
    calendar = [line for line in help_en.splitlines()
                if line.startswith("- ") and "1, 3, 6" in line and "24" not in line]
    check("涨跌日历那条没被误改（它的限制本来就该更紧）", len(calendar) == 1,
          f"{len(calendar)} 条")

    # ---- 1) K线：菜单里的 5 年 / 10 年，以及选了 10 年真的取得到

    if not goto(win, "K线"):
        check("切到 K线", False)
        return report()

    period = winui.find(win, lambda c: c.AutomationId == "PeriodCombo")

    if period is not None:
        combo_pick(win, period, "日K")

    range_combo, labels = combo_labels(win, "RangeCombo")

    if labels is None:
        check("K线区间下拉在", False)
        return report()

    check("K线日线有「近 5 年」", "近 5 年" in labels, " / ".join(labels))
    check("K线日线有「近 10 年」", "近 10 年" in labels, " / ".join(labels))

    if range_combo is not None and "近 10 年" in labels:
        picked = combo_pick(win, range_combo, "近 10 年")
        check("选中「近 10 年」", picked == "近 10 年", str(picked))

        # 十年日线是 2520 根，一次请求只给 640，所以这一条同时验了分页：取数不出错、并且报出来的
        # 根数必须是五位数里的四位数（2000 根以上），否则说明它只拿回了最近一年半。
        said = fetch(win)
        check("十年日线取数没出错", ok(said), (said or "")[:90])

        bars = re.search(r"(\d[\d,]*)\s*根", said or "")
        count = int(bars.group(1).replace(",", "")) if bars else 0
        check("拿回的是十年的根数（≥2000 根，说明分页走到了）", count >= 2000, f"{count} 根")

    # ---- 2) 板块竞速：2 年这一档以前会被当成「过长」拦下

    if not goto(win, "行业板块竞速"):
        check("切到 行业板块竞速", False)
        return report()

    combo, labels = combo_labels(win, "RangeCombo")

    if labels is None:
        check("板块竞速区间下拉在", False)
    else:
        check("板块竞速有「近 2 年」", "近 2 年" in labels, " / ".join(labels))

        if combo is not None and "近 2 年" in labels:
            picked = combo_pick(win, combo, "近 2 年")
            check("选中「近 2 年」", picked == "近 2 年", str(picked))

            said = fetch(win)
            check("两年区间没有被当成「过长」拦下（旧阈值是 640 天）",
                  ok(said) and "过长" not in said, (said or "")[:90])
            check("两年区间取数没出错", ok(said), (said or "")[:90])

    # ---- 3) 市值榜：最长那一档 = 一次请求的 180 个月

    if not goto(win, "市值榜"):
        check("切到 市值榜", False)
        return report()

    combo, labels = combo_labels(win, "RangeCombo")

    if labels is None:
        check("市值榜区间下拉在", False)
    else:
        check("市值榜有「最长」", "最长" in labels, " / ".join(labels))
        check("市值榜的「自定义」还在", "自定义" in labels, " / ".join(labels))

        if combo is not None and "最长" in labels:
            picked = combo_pick(win, combo, "最长")
            check("选中「最长」", picked == "最长", str(picked))

            said = fetch(win, seconds=240)
            check("「最长」取数没出错", ok(said), (said or "")[:90])

    # ---- 4) 成交量换手率：菜单（取数路径与板块竞速同一条，所以这里只读菜单）

    if not goto(win, "成交量换手率"):
        check("切到 成交量换手率", False)
        return report()

    _, labels = combo_labels(win, "RangeCombo")

    if labels is None:
        check("成交量页区间下拉在", False)
    else:
        check("成交量页有「近 2 年」", "近 2 年" in labels, " / ".join(labels))

    return report()


if __name__ == "__main__":
    sys.exit(main())
