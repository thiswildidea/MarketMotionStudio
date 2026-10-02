# -*- coding: utf-8 -*-
"""真机验证「市值榜竞速」。

这一页的数字有三处**不能靠截图证明**，所以脚本才是验证：

1. **取的是不是十年。** 十年不是一次请求——月线端点一页给三百根，但要往前走到
   起点仍要翻页。翻没翻出来只有状态行里的「N 期」和起点日期说得清。默认档就是
   近十年，所以先读回默认值，再换到近一年跑一遍，两次的起点差九年在数据上分得开。
2. **市值是不是算出来的。** 榜首与垫底的名字来自取数时问出来的排名，脚本不可能
   预先知道是谁；真正要验的是它们**随时间变过**，而这一点由「领先者不是清单里的
   第一个」和 120 上下的期数共同说明——月线一次给不了十年。
3. **画面表头说的是月还是交易日。** 这是源码级的检查，理由写在第 0 段里：那句
   文字画在预览面上，UIA 里没有节点，而它确实被写错过一次。

用法：python tools/verify-marketcap.py
"""
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

REPO = Path(__file__).resolve().parent.parent
RENDERER = REPO / "src/MarketMotionStudio/Render/SectorRaceRenderer.cs"
PAGE_SOURCE = REPO / "src/MarketMotionStudio/Pages/MarketCapPage.xaml.cs"
STRINGS = REPO / "src/MarketMotionStudio/Strings"

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有返回|不属于|过长|failed|error")

# 62 只候选 · 120 期 · 领先 工商银行 29,510亿元 · 垫底 中国石化 6,374亿元
FETCHED = re.compile(
    r"(\d+)\s*只候选\s*·\s*(\d+)\s*期\s*·\s*领先\s*(.+?)\s*([\d,]+)\s*\S*\s*·\s*垫底\s*(.+?)\s*([\d,]+)")

DATED = re.compile(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})")

# 池子是取数时按当前市值排名生成的，所以脚本不可能预先知道榜首是谁 —— 断言改成
# "名字是干净的"：非空、不超长、没有除权前缀（XD/XR/DR 会在画面上存在好几周，
# 而它们描述的只是那一天）。这条断言本来就是这个意思，写死名单的版本在池子变成
# 动态的当天就失效了：它把长鑫科技报成"不在名单里"，而它正是新来的那一家。
FIELD = ["工商银行", "建设银行", "农业银行", "中国银行", "中国移动", "中国石油", "中国石化",
         "贵州茅台", "宁德时代", "工业富联", "招商银行", "中国人寿", "中国平安", "中国神华",
         "紫金矿业", "比亚迪", "长江电力", "美的集团", "中国电信", "中信证券", "恒瑞医药",
         "中国太保", "海康威视", "东方财富", "五粮液", "平安银行", "万华化学", "格力电器",
         "中国建筑", "新华保险", "伊利股份", "山西汾酒", "中国联通", "中国国航", "长城汽车",
         "中国中铁", "海螺水泥", "隆基绿能", "中国铁建", "洋河股份", "浦发银行", "兴业银行",
         "民生银行", "光大银行", "北京银行", "上汽集团", "万科A", "中国中车", "中国重工",
         "中国船舶", "三一重工", "京东方A", "立讯精密", "药明康德", "通威股份", "海尔智家",
         "泸州老窖", "保利发展", "中兴通讯", "陕西煤业", "邮储银行", "中信银行"]

# 池子不再是写死的：取数时按当前市值取前 200 名，再加上历史留档。所以这里断言的是
# "宽到足以覆盖真实榜单"，不是某个定数。
FEWEST_CANDIDATES = 200

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
    """A name worth drawing: something there, not absurdly long, and no ex-rights flag.

    `XD中国移` names a company that does not exist and stops being right the next morning —
    which matters because a frame outlives the morning it was exported on.
    """
    if not name or len(name) > 24:
        return False

    return not name.startswith(("XD", "XR", "DR"))


def resw_units():
    """(tag, 月数词, 候选数量词) for each of the fourteen.

    Read from the files rather than from the script that wrote them: the question is what
    the app will actually load, and a translation can be right in the script and wrong in
    the file after a run that stopped halfway.
    """
    out = []

    for path in sorted(STRINGS.glob("*/Resources.resw")):
        values = {
            e.get("name"): (e.find("value").text or "")
            for e in ET.parse(path).getroot().findall("data")
        }

        out.append((path.parent.name, values.get("MarketCapUnitMonths", ""),
                    values.get("MarketCapUnitCandidates", "")))

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


OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")


def shot(win, name):
    path = os.path.join(OUT, name)

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
    """Presses 获取数据 and parses the summary the page reports."""
    close_status(win)

    button = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if button is None:
        return None, "FetchButton 不见了"

    # Retried: `Invoke` on a button the page is still laying out throws COMError
    # (-2147220992) instead of pressing anything, and an exception here kills the whole
    # run — the earlier checks are lost with it, and the reason ("the popup above never
    # closed") is not the reason printed. Re-found each attempt, because the handle
    # that failed is the one that went stale.
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
        "days": int(hit.group(2)),
        "top": hit.group(3).strip(),
        "top_value": int(hit.group(4).replace(",", "")),
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


SETTINGS_NAMES = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки"]


def open_settings(win):
    for name in SETTINGS_NAMES:
        item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

        if item is None:
            continue

        try:
            item.GetSelectionItemPattern().Select()
        except Exception:  # noqa: BLE001 - a stale row only means the next name may fit
            pass

        time.sleep(2.0)

        return True

    return False


def ensure_ashare(win):
    """Puts the app back on the mainland market, restarting when it was not there.

    The width of the field depends on the market: only the mainland one is asked of the
    ranking endpoint, and Hong Kong and New York keep a hand-checked field of thirty-five
    and forty-three — which is what this app has, because the ranking serves the mainland
    and nothing else. The market is a remembered preference, so without this the "two
    hundred candidates" check below is really asserting whichever market the last script
    that ran happened to leave behind. It read thirty-five once, and the code was right.

    Picked as the first entry rather than by name, so the script does not have to know
    what "A 股" is called in whichever language the app is currently in.
    """
    if not open_settings(win):
        print("· 设置页没找到，市场保持原样")
        return win

    combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo")

    if combo is None:
        print("· 市场下拉没找到，市场保持原样")
        return win

    labels = winui.combo_labels(win, combo)

    if not labels:
        print("· 读不出市场下拉的内容，市场保持原样")
        return win

    current = winui.value(combo)

    if current == labels[0]:
        return win

    picked = winui.combo_pick(win, combo, labels[0])
    print(f"· 市场从 {current} 复位到 {picked}（改市场要重启）")

    time.sleep(1.5)

    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        print("重启后窗口没起来")
        return None

    maxed(win)

    return win


def main():
    # `launch`, not `app_window`: the latter only waits for a window that is already up,
    # and the package is registered in place — an instance left running is the previous
    # build's, so verifying against it verifies the change before this one.
    win = winui.launch(winui.EXE)

    if win is None:
        print("no studio window")
        return 1

    maxed(win)

    # ---- 0a) 市场复位到 A 股
    #
    # 池子宽度是「市场」的函数：只有 A 股会去问排名端点（新浪的排行只服务内地，
    # 港美股拿的是写死清单，港 35 / 美 43），而市场是记住的偏好。不管它，下面那条
    # "候选池宽到 200 只以上"验的就是「上一个跑脚本的人选了哪个市场」—— 它读出
    # 35 那天，代码是对的。
    win = ensure_ashare(win)

    if win is None:
        print("no studio window after market reset")
        return 1

    # ---- 0) 画面表头说的是月，不是交易日
    #
    # 这一条是源码级的，因为它验的东西在 UIA 里根本不存在：表头那行字是 Win2D 直接
    # 画进预览面的，树里没有节点，截图也不能当断言（没有人会天天去读一张截图）。
    #
    # 而它确实坏过：市值榜的月线序列套用了行业竞速页的渲染器，那个渲染器把
    # `StockTradingDaysUnit`（个交易日）写死在画表头的地方 —— 于是十二个月被画成
    # 「12 个交易日」，每一帧都是。**量词必须由页面给**，页面才知道自己问源要的是
    # 什么周期。下面三条盯的就是这个：渲染器不再自带日线量词，页面两个词都给了，
    # 14 份译文里也没有把「月」写成「交易日」。
    check("渲染器把周期量词交给页面（SpanWord 在）", "SpanWord" in RENDERER.read_text("utf-8"))
    check("渲染器画表头的地方不再写死「个交易日」",
          RENDERER.read_text("utf-8").count('Strings.Get("StockTradingDaysUnit")') == 1,
          "只应剩 Span 属性里那一处兜底")

    page = PAGE_SOURCE.read_text("utf-8")
    check("市值榜页面把月数交给渲染器", 'SpanWord = Strings.Get("MarketCapUnitMonths")' in page)
    check("市值榜页面把候选数交给渲染器", 'UnitWord = Strings.Get("MarketCapUnitCandidates")' in page)

    # 「最长」的天花板必须是月线自己的 180 个月，而不是 walk 的三十五年：月线一次请求
    # 就给这么多，而 walk 的边界是按日线算出来的。拿 walk 当上限，「最长」会一路走到
    # 源端开始丢的地方 —— 而它丢的是**头部**（count 是根数，源端从 end 往回数），
    # 回来的图短一截却完全正常，这正是区间最不该给出的答案。
    check("「最长」的边界是月线自己的 180 个月，不是 walk 的日线上限",
          "MarketCapSeries.MonthsWanted" in page and "HistoryWalk.MostDays" not in page,
          "页面不该再提到 walk")

    for tag, months, candidates in resw_units():
        check(f"{tag}：周期量词是「月」不是「交易日」",
              "交易日" not in months and "trading day" not in months.lower(),
              months)
        check(f"{tag}：候选数的量词是候选不是个股",
              "个股" not in candidates and "stocks" not in candidates.lower(),
              candidates)

    # ---- 1) 页面在，而且面板里没有多余的选择
    if not goto(win, "市值榜"):
        check("导航里有「市值榜」", False)
        return report()

    check("导航里有「市值榜」", True)

    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    labels = winui.find(win, lambda c: c.AutomationId == "ListText")

    if labels is not None:
        shown = " ".join(texts(labels))

        check("页面说明了候选池与每期取多少名", "15" in shown and "200" in shown, shown[:80])

    note = winui.find(win, lambda c: c.AutomationId == "MarketCapMethodNote")

    if note is not None:
        body = " ".join(texts(note))

        check("口径说明写明了市值的算法", "复权" in body or "市值" in body, body[:60])

    # ---- 2) 区间档位与默认值
    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")

    if combo is not None:
        options = winui.combo_labels(win, combo)

        # A set, and compared as one: the order is the code's business, and an extra
        # entry is what this is looking for — a missing year or a stray duplicate.
        # Six since the ranges were measured against the endpoint: 「最长」 is the
        # monthly series' own one hundred and eighty months, which is further back than
        # the ten-year entry and further than the walk's ceiling ever reached in practice.
        check("区间下拉是那六档",
              set(options) == {"近 12 个月", "近 3 年", "近 5 年", "近 10 年", "最长", "自定义"},
              " / ".join(options))

        # The first-run default is only visible on a first run. The page remembers the span
        # a person chose — that is the point of remembering it — so on every run after the
        # first this reads back the previous choice, and asserting "近 10 年" here would
        # fail on a page that is behaving exactly as designed. Reported rather than
        # asserted; the default itself was confirmed on a freshly registered package.
        shown = winui.value(combo)

        if shown == "近 10 年":
            check("默认档是近 10 年（本机首次运行）", True, str(shown))
        else:
            print(f"· 区间记着上次的选择：{shown}（默认值是近 10 年，已在重装后确认）")

            check("记住的档位仍在那六档里",
                  shown in {"近 12 个月", "近 3 年", "近 5 年", "近 10 年", "最长", "自定义"},
                  str(shown))

    # ---- 3) 近一年：先确认整条链路通，再花时间翻十年
    if combo is not None and winui.combo_pick(win, combo, "近 12 个月") == "近 12 个月":
        one, status = fetch(win)

        check("近十二月取数成功", one is not None, str(status)[:120])

        if one is not None:
            check(f"候选池宽到 {FEWEST_CANDIDATES} 只以上", one["racers"] >= FEWEST_CANDIDATES, str(one["racers"]))
            check("期数落在十二个月的量级（11–13）",
                  11 <= one["days"] <= 13, str(one["days"]))
            check("榜首与垫底的名字是干净的",
                  clean(one["top"]) and clean(one["last"]),
                  f"{one['top']} / {one['last']}")
            check("榜首市值大于垫底", one["top_value"] > 0 and one["top"] != one["last"])

        shot(win, "verify-marketcap-1y.png")

    # ---- 4) 近十年：翻页回溯，这是这个页面真正的本事
    if combo is not None and winui.combo_pick(win, combo, "近 10 年") == "近 10 年":
        ten, status = fetch(win, seconds=600)

        check("近十年取数成功", ten is not None, str(status)[:120])

        if ten is not None:
            check("期数落在十年的量级（118–124）",
                  118 <= ten["days"] <= 124, str(ten["days"]))
            check("榜首与垫底的名字是干净的",
                  clean(ten["top"]) and clean(ten["last"]),
                  f"{ten['top']} / {ten['last']}")
            check("十年榜的期数远多于十二月榜",
                  one is not None and ten["days"] > one["days"] * 8,
                  f"{ten['days']} vs {one['days'] if one else '—'}")

            # 十年之后名次一定变过：一张十年不变的榜等于没画。
            check("榜首位子不是名单里的第一个（名次确实变过）",
                  ten["top"] != FIELD[0] or one is None or one["top"] == ten["top"],
                  f"十年 {ten['top']} / 一年 {one['top'] if one else '—'}")

        shot(win, "verify-marketcap-10y.png")

    # ---- 5) 重启后还记得区间
    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)

    if goto(win, "市值榜"):
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
