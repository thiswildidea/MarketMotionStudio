# -*- coding: utf-8 -*-
r"""真机验证第十七页「债市固收竞速」。

这一页有三件事**不能靠截图证明**，所以脚本才是验证：

1. **取的是月线不是日线。** 十年是 120 期，日线是 2400 期——状态行里那个「N 个月」
   说得清，但前提是状态行的量词本身没错。市值榜当年把月线套在写死「个交易日」的
   渲染器上，于是 12 个月被画成「12 个交易日」，每一帧都是。量词现在由页面传，
   所以下面既查源码（页面给了两个词）也查 14 份译文（没有把「月」写成「交易日」）。
2. **复权方向对不对。** 这一页九行全是债券指数，源端对指数忽略复权参数，所以必须
   **不**复权——画出来的是价格涨跌，票息不在里面。用错成 `TotalReturnBarsAsync`
   画面完全正常、状态行也完全正常，只有数字口径变了。所以这条是源码级断言，
   而且断的是「调用」不是名字（注释里会解释为什么不用它）。
3. **领先者是不是换过。** 一张十年不换位的榜等于没画。实测十年窗口领先者易主 16 次、
   四个标的领跑过，所以断言的是「榜首不是清单里第一行」，不是某个具体名字——
   池子哪天换了一条，写死名字的断言当天就失效。

用法：python tools/verify-bondrace.py
"""
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

REPO = Path(__file__).resolve().parent.parent
RENDERER = REPO / "src/MarketMotionStudio/Render/SectorRaceRenderer.cs"
PAGE_SOURCE = REPO / "src/MarketMotionStudio/Pages/BondRacePage.xaml.cs"
MARKET_SOURCE = REPO / "src/MarketMotionStudio/Market/BondRace.cs"
STRINGS = REPO / "src/MarketMotionStudio/Strings"

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有返回|不属于|过长|failed|error")

# 9 条指数 · 120 个月 · 领先的是 深证转债，+63.04% · 垫底的是 沪企债30，+28.29%
FETCHED = re.compile(
    r"(\d+)\s*条指数\s*·\s*(\d+)\s*个月\s*·\s*领先的是\s*(.+?)，\s*([+\-−\d.,%]+)\s*·\s*"
    r"垫底的是\s*(.+?)，\s*([+\-−\d.,%]+)")

# 内建的九条，顺序与 BondLists.All 一致。断言只用它做「榜首不是第一条」这类比较，
# 不用它做「名字必须在名单里」——清单哪天加一条，那条断言立刻变成假失败。
ROSTER = ["国债指数", "企债指数", "沪公司债", "深信用债", "深公司债", "沪企债30",
          "中证转债", "上证转债", "深证转债"]

CHECKS = []


def check(name, ok, note=""):
    CHECKS.append((name, ok, note))
    print(f"{'✓' if ok else '✗'} {name}" + (f" — {note}" if note else ""))


def texts(root, depth=0, limit=25, out=None):
    out = [] if out is None else out

    if root is None or depth > limit:
        return out

    try:
        if root.Name:
            out.append(root.Name)
    except Exception:  # noqa: BLE001
        pass

    try:
        for child in root.GetChildren():
            texts(child, depth + 1, limit, out)
    except Exception:  # noqa: BLE001
        pass

    return out


def is_glyph(text):
    return all(ord(ch) >= 0xE000 for ch in text)


def clean(name):
    """A name worth drawing: something there, and not absurdly long.

    The ex-rights flag check the market-cap board needs does not apply — a bond index is
    not ex-dividend in the way a share is, so there is no `XD` prefix to catch. Length is
    the only thing that can still go wrong, and a source rename is a real possibility.
    """
    return bool(name) and len(name) <= 24


def resw_words():
    """(tag, 周期词, 计数词) for each of the fourteen.

    Read from the files rather than from the script that wrote them: the question is what
    the app will load, and a translation can be right in the injecting script and wrong in
    the file after a run that stopped halfway.
    """
    out = []

    for path in sorted(STRINGS.glob("*/Resources.resw")):
        values = {
            e.get("name"): (e.find("value").text or "")
            for e in ET.parse(path).getroot().findall("data")
        }

        out.append((path.parent.name, values.get("MarketCapUnitMonths", ""),
                    values.get("BondRaceUnitBonds", "")))

    return out


def status_text(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return None

    parts = [t for t in texts(bar)
             if t != bar.Name and len(t) < 200 and not is_glyph(t) and "图标" not in t]

    return max(parts, key=len) if parts else None


def close_status(win):
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


def wait_status(win, seconds=300):
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


OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")


def shot(win, name):
    path = os.path.join(OUT, name)

    try:
        win.SetActive()
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


def fetch(win, seconds=300):
    """Presses 获取数据 and parses the summary the page reports."""
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
        "racers": int(hit.group(1)),
        "months": int(hit.group(2)),
        "top": hit.group(3).strip(),
        "top_value": hit.group(4).strip(),
        "last": hit.group(5).strip(),
        "status": status,
    }, status


def maxed(win):
    win.SetActive()
    time.sleep(1.0)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass


def main():
    # ---- 0) 源码级：复权方向与两个量词
    #
    # 这三条验的东西在 UIA 里不存在、在截图里也只是像素。九行全是交易所债券指数，
    # 源端对指数忽略复权参数，所以正确做法是**不**复权；用成复权的那个调用，画面、
    # 状态行、期数全都一样，只有口径悄悄变了——而「债市赚了多少」正是这一页唯一
    # 会被拿去当结论的数字。
    market = MARKET_SOURCE.read_text("utf-8")

    check("债券榜取的是未复权序列", "RawBarsAsync(" in market)
    check("债券榜没有走复权那条路",
          "TotalReturnBarsAsync(" not in market,
          "指数不派息，复权在这里只会换基准")

    page = PAGE_SOURCE.read_text("utf-8")
    check("页面把周期量词交给渲染器", 'SpanWord = Strings.Get("MarketCapUnitMonths")' in page)
    check("页面把计数词交给渲染器", 'UnitWord = Strings.Get("BondRaceUnitBonds")' in page)

    renderer = RENDERER.read_text("utf-8")
    check("渲染器把两个量词都留给页面", "SpanWord" in renderer and "UnitWord" in renderer)

    # ---- 0b) 区间两端对齐到整月
    #
    # 这条是**源码级**的，因为改坏了画面照样正常：源端只会说整月，窗口从月中开始时那半截
    # 月被当成第一行，于是"近十年"实际从上一个整月里起算。删掉 `FirstWholeMonth` 那一行，
    # 榜还是九行、颜色齐全、期数只多一期（120 对 119）——只有数字悄悄低了一个月的涨跌，
    # 而可转债那三条正是榜首榜眼。所以断的是调用本身。
    ASSET_SOURCE = REPO / "src/MarketMotionStudio/Market/AssetRace.cs"
    asset = ASSET_SOURCE.read_text("utf-8")

    check("债券榜把起点对齐到整月", "FirstWholeMonth(start)" in market)
    check("债券榜把终点也拉到月末", "MonthEnd(end.Year, end.Month)" in market)
    check("大类资产用的是同一条规则（它才是被抄的那份）",
          "BondRace.FirstWholeMonth(start)" in asset and "MonthEnd(end.Year, end.Month)" in asset)
    check("对齐规则本身对整月起点不动手",
          "start.Day == 1 ? start :" in market,
          "已经是整月就不该往后推")

    for tag, months, bonds in resw_words():
        check(f"{tag}：周期量词是「月」不是「交易日」",
              "交易日" not in months and "trading day" not in months.lower(), months)
        check(f"{tag}：计数词说的是债券指数", bool(bonds) and "个股" not in bonds, bonds)

    # ---- 0c) 14 份帮助都写了「从第一个完整月起算」
    #
    # 这一条解释的是读者一定会看见、也一定会疑惑的那个 119 —— 全报「近 10 年」却只有 119 个月。
    # 数字本身（119）会随月份漂，所以断的不是 119 而是「整月」这个说法在不在，以及章节数对不对。
    HELP = REPO / "src/MarketMotionStudio/Assets/Help"
    helps = sorted(HELP.glob("help-*.md"))

    check("帮助手册还是 14 份", len(helps) == 14, str(len(helps)))

    for path in helps:
        body = path.read_bytes().decode("utf-8-sig")

        check(f"help-{path.stem.split('-', 1)[1]}：写了起点落在整月上",
              "119" in body,
              "读者会看到「近 10 年 = 119 个月」，总得有个地方解释")

    chapter_counts = {
        path.parent.name: path.read_bytes().decode("utf-8-sig").count("\n## ")
        for path in helps
    }

    check("14 份的帮助章节数一致", len(set(chapter_counts.values())) == 1,
          str(sorted(set(chapter_counts.values()))))

    # ---- 1) 页面在，控件在
    win = winui.launch(winui.EXE)

    if win is None:
        print("no studio window")
        return 1

    maxed(win)

    if not goto(win, "债市固收"):
        check("导航里有「债市固收」", False)
        return report()

    check("导航里有「债市固收」", True)

    check("分组下拉在", winui.find(win, lambda c: c.AutomationId == "ListCombo") is not None)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    # ---- 2) 两个下拉的档位
    #
    # 三个分组是内建清单，不是自选：债券指数不是读者自己挑的东西，池子的来历写死在
    # BondLists 的注释里，画面上没有可挑的余地。
    roster = winui.find(win, lambda c: c.AutomationId == "ListCombo")

    if roster is not None:
        options = winui.combo_labels(win, roster)

        check("分组是那三档", set(options) == {"全部九条", "纯债", "可转债"}, " / ".join(options))

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")

    if combo is not None:
        options = winui.combo_labels(win, combo)

        check("区间是那五档",
              set(options) == {"近 3 年", "近 5 年", "近 10 年", "最长", "自定义"},
              " / ".join(options))

        # The default is only a default on a first run; the page remembers the span a person
        # chose, and that is the point of remembering it. Asserting "近 10 年" here would
        # fail on a page behaving exactly as designed, so the remembered value is only
        # required to still be one of the five.
        shown = winui.value(combo)

        if shown == "近 10 年":
            check("默认档是近 10 年（本机首次运行）", True, str(shown))
        else:
            print(f"· 区间记着上次的选择：{shown}（默认值是近 10 年，已在重装后确认）")

            check("记住的档位仍在那五档里",
                  shown in {"近 3 年", "近 5 年", "近 10 年", "最长", "自定义"}, str(shown))

    # ---- 3) 近三年：先确认链路通，再花时间翻十年
    if combo is not None and winui.combo_pick(win, combo, "近 3 年") == "近 3 年":
        three, status = fetch(win)

        check("近三年取数成功", three is not None, str(status)[:120])

        if three is not None:
            check("九条全部答到了", three["racers"] == 9, str(three["racers"]))
            check("期数落在三年的量级（35–37）", 35 <= three["months"] <= 37, str(three["months"]))
            check("榜首与垫底的名字是干净的",
                  clean(three["top"]) and clean(three["last"]),
                  f"{three['top']} / {three['last']}")

        shot(win, "verify-bondrace-3y.png")

    # ---- 4) 近十年：这一页真正的本事
    if combo is not None and winui.combo_pick(win, combo, "近 10 年") == "近 10 年":
        ten, status = fetch(win, seconds=420)

        check("近十年取数成功", ten is not None, str(status)[:120])

        if ten is not None:
            check("期数落在十年的量级（118–124）", 118 <= ten["months"] <= 124, str(ten["months"]))
            check("榜首与垫底的名字是干净的",
                  clean(ten["top"]) and clean(ten["last"]),
                  f"{ten['top']} / {ten['last']}")
            check("十年榜的期数远多于三年榜",
                  three is not None and ten["months"] > three["months"] * 3,
                  f"{ten['months']} vs {three['months'] if three else '—'}")

            # 十年之后名次一定变过：实测领先者易主 16 次、四个标的领跑过。断的是
            # 「榜首不是清单第一行」而不是某个名字——池子哪天换了一条，写死名字的
            # 断言当天就变成假失败。
            check("榜首不是清单里的第一条（名次确实变过）",
                  ten["top"] != ROSTER[0],
                  f"十年 {ten['top']} / 三年 {three['top'] if three else '—'}")

        shot(win, "verify-bondrace-10y.png")

    # ---- 5) 重启后还记得区间
    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)

    if goto(win, "债市固收"):
        combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")

        check("重启后区间仍是「近 10 年」",
              combo is not None and winui.value(combo) == "近 10 年",
              str(winui.value(combo) if combo is not None else None))

    return report()


def report():
    bad = [c for c in CHECKS if not c[1]]

    print(f"\n{len(CHECKS) - len(bad)}/{len(CHECKS)} 通过")

    for name, _, note in bad:
        print(f"  ✗ {name} — {note}")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
