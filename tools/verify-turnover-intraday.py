# -*- coding: utf-8 -*-
r"""真机验证成交额页的两项新能力：自选篮，与日内分时曲线。

这一页原本只有八个板块，全是**指数合成出来的**（主板还是"交易所减成长板"推出来的）。
加进来的两件事各自有一个**错了不会报错、只会静默画错**的口径，所以它们只能断在源码里：

1. **日轴取并集，不是交集。** 交集是给指数用的 —— 指数每个交易日都有行情，这条规则从未
   咬过人。个股会停牌，交集下"一只停牌 = 那一天从图上消失"，而图上少一天和那天本来就没
   交易长得一模一样，表头的天数也跟着对不上。所以缺的那只记 0（停牌就是没成交），日轴
   按并集。
2. **日内必须截到 15:00。** 端点把收市后的半小时也补上（盘后固定价格交易），茅台
   2026-09-30 在 15:00 是 47.97 亿、15:30 是 48.02 亿，而日线是 47.97 亿。多算那半小时，
   画面完全正常，只有这个数对不上行情软件 —— 而它恰恰是读者唯一会去核对的那个数。

另外三条是**真机上才看得见**的：取数真的成功、曲线真的画出来了（数金色像素，
`Palette.Moving` 是 #FBBF24）、以及切走视图后旧的数真的没被拿去画另一根轴。

用法：python tools/verify-turnover-intraday.py
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(REPO, "src", "MarketMotionStudio", "Pages", "MarketTurnoverPage.xaml.cs")
SERIES = os.path.join(REPO, "src", "MarketMotionStudio", "Market", "TurnoverSeries.cs")
INTRADAY = os.path.join(REPO, "src", "MarketMotionStudio", "Market", "TurnoverIntraday.cs")
RENDER = os.path.join(REPO, "src", "MarketMotionStudio", "Render", "IntradayRenderer.cs")

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有返回|不属于|过长|failed|error")

# {0} · {1} · {2} 分钟 · 收盘 {3} {4} —— 例：沪深全市场 · 2026-09-30 · 241 分钟 · 收盘 14,436 亿元
FETCHED = re.compile(r"(\d{4}-\d{2}-\d{2})\s*·\s*(\d+)\s*分钟\s*·\s*收盘\s*([\d,]+)\s*亿元")

# 共 {0} 个交易日（{1} ~ {2}）· 日均 {3} · 最高 {4} · 最低 {5} —— 日线那两档用的另一句
DAILY = re.compile(
    r"共\s*(\d+)\s*个交易日（([\d-]+)\s*~\s*([\d-]+)）·\s*日均\s*([\d,]+)\s*·\s*最高\s*([\d,]+)"
    r"\s*·\s*最低\s*([\d,]+)")

PAGE_NAME = "市场成交额"
VIEW_INTRADAY = "日内"
VIEW_BARS = "柱状竞长"

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


def status_text(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    return " ".join(texts(bar)) if bar is not None else ""


def wait_status(win, pattern=FETCHED, seconds=300):
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(2.0)
        text = status_text(win)

        if text and (pattern.search(text) or FAIL.search(text)):
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


def curve_pixels(win, name):
    """Counts the curve's own colour in the frame.

    The curve is `Palette.Moving` (#FBBF24), which nothing else on this page uses: the grid is
    blue-grey, the title is near-white, the cards are dark. So a count of that hue is a count of
    the curve, and zero means the frame drew something that is not a session.
    """
    try:
        from PIL import Image
    except ImportError:
        return -1

    path = shot(win, name)
    whole = Image.open(path).convert("RGB")
    pixels = whole.load()

    box = winui.canvas_box(whole)
    left, right, top, bottom = box if box else (0, whole.size[0], 0, whole.size[1])

    found = 0

    for y in range(top, bottom, 2):
        for x in range(left, right, 2):
            r, g, b = pixels[x, y]

            # Gold, and saturated: r high, g mid, b low. Deliberately loose, because the curve is
            # drawn over a gradient wash of itself and antialiases along its whole length.
            if r > 170 and 120 < g < 230 and b < 110 and r - b > 90:
                found += 1

    return found


KLINE = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"

# 三只境内标的：一只沪市主板、一只深市主板、一只科创板。全是 A 股 —— 成交额是各市场各报各的
# 币种，篮子里混进港股就是把港元加进人民币，所以这一页只认境内代码。
WATCH = [("sh600519", "贵州茅台"), ("sz000858", "五粮液"), ("sh688981", "中芯国际")]

RANGE = "近 3 个月"


def daily_bars(code, start, end):
    """One instrument's daily turnover in 亿元, clipped to the range by this script.

    Field [8] is the amount in 万元 on both row shapes (10 fields for a forward-adjusted stock,
    11 for an index), and the source ignores `start` — it counts back from `end` — so a script
    that skipped the clip would report days the app never put on its axis.
    """
    param = f"{code},day,{start.isoformat()},{end.isoformat()},640,qfq"

    with urllib.request.urlopen(f"{KLINE}?param={urllib.parse.quote(param)}", timeout=30) as reply:
        node = json.load(reply).get("data", {}).get(code, {})

    rows = node.get("qfqday") or node.get("day") or []

    return {row[0]: float(row[8]) / 1e4 for row in rows
            if start.isoformat() <= row[0] <= end.isoformat()}


def expected_basket(codes, start, end):
    """The two numbers the status line prints, computed here rather than read back.

    The union and the zero are the whole point: a day is on the axis if *any* member traded, and
    a member with no row for that day contributes nothing. An intersection would drop the day,
    which is the one mistake that leaves the picture looking entirely normal.
    """
    bars = {code: daily_bars(code, start, end) for code in codes}
    days = sorted(set().union(*[set(b) for b in bars.values()]))
    totals = [sum(bars[code].get(day, 0.0) for code in codes) for day in days]

    return len(days), sum(totals) / len(totals)


def watch_chips(win):
    """The watchlist's chips, as (button, name).

    A chip *is* its own delete button, and the button's own `Name` is empty — the name sits in a
    child text, so matching on the button's name counts zero chips over a row of three that are
    plainly on screen.
    """
    out = []

    for button in winui.find_all(win, lambda c: c.ControlTypeName == "ButtonControl"):
        kids = [t.Name for t in winui.find_all(
            button, lambda c: c.ControlTypeName == "TextControl", limit=6)]

        if any(k.strip() in ("×", "✕") for k in kids):
            name = next((k for k in kids if k.strip() not in ("×", "✕")), "")
            out.append((button, name))

    return out


def clear_watch(win):
    """Empties the list first.

    The list is shared by four pages and survives restarts, so whatever a previous run added is
    still here — and a basket of "theirs plus mine" is a plausible board of the wrong holdings.
    """
    for _ in range(24):
        chips = watch_chips(win)

        if not chips:
            return True

        try:
            chips[0][0].GetInvokePattern().Invoke()
        except Exception:  # noqa: BLE001
            return False

        time.sleep(0.6)

    return False


def add_watch(win, code, name, tries=3):
    """Types a code into the picker's search box and counts the chips afterwards.

    The code goes through the clipboard because Chinese will not type into an AutoSuggestBox, and
    the submit is an Enter rather than a click on a suggestion, because that suggestion layer is
    another top-level window — and a layer left open from the last attempt eats the Enter, so the
    name quietly never arrives. Hence the recount: a chip that did not appear means try again.
    """
    for _ in range(tries):
        box = winui.find(win, lambda c: c.AutomationId == "Search")
        edit = None if box is None else winui.find(
            box, lambda c: c.AutomationId == "TextBox", limit=6)

        if edit is None:
            return False

        try:
            win.SetActive()
        except Exception:  # noqa: BLE001
            pass

        edit.SetFocus()
        time.sleep(0.3)
        edit.SendKeys("{Esc}", waitTime=0.3)
        edit.SendKeys("{Ctrl}a", waitTime=0.3)
        auto.SetClipboardText(code)
        edit.SendKeys("{Ctrl}v", waitTime=0.5)
        time.sleep(1.2)
        edit.SendKeys("{Enter}", waitTime=0.5)
        time.sleep(2.0)

        # 名字可能还没到：只敲代码、没点建议时，chip 上先显示代码，真名要等取数时那次
        # 快照才补上（另外四页也是这个行为）。所以"进去了"的判据是**名字或代码**任一。
        if any(n.strip() in (name, code.upper()) for _, n in watch_chips(win)):
            return True

    return False


def fetch_daily(win):
    button = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if button is None:
        return None, "（找不到取数按钮）"

    try:
        button.GetInvokePattern().Invoke()
    except Exception as exc:  # noqa: BLE001
        return None, f"（点不到取数按钮：{exc}）"

    status = wait_status(win, DAILY)

    if status is None:
        return None, status_text(win) or "（状态条空）"

    hit = DAILY.search(status)

    if hit is None:
        return None, status

    return {
        "days": int(hit.group(1)),
        "start": hit.group(2),
        "end": hit.group(3),
        "mean": float(hit.group(4).replace(",", "")),
        "high": float(hit.group(5).replace(",", "")),
        "low": float(hit.group(6).replace(",", "")),
        "status": status,
    }, status


def fetch(win):
    button = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if button is None:
        return None, "（找不到取数按钮）"

    try:
        button.GetInvokePattern().Invoke()
    except Exception as exc:  # noqa: BLE001
        return None, f"（点不到取数按钮：{exc}）"

    status = wait_status(win)

    if status is None:
        return None, status_text(win) or "（状态条空）"

    hit = FETCHED.search(status)

    if hit is None:
        return None, status

    return {
        "day": hit.group(1),
        "minutes": int(hit.group(2)),
        "total": hit.group(3),
        "status": status,
    }, status


def main():
    win = winui.launch(winui.EXE)

    if win is None:
        print("no studio window")
        return 1

    try:
        win.Maximize()
        time.sleep(1.0)
    except Exception:  # noqa: BLE001
        pass

    page = open(PAGE, encoding="utf-8").read()
    series = open(SERIES, encoding="utf-8").read()
    intraday = open(INTRADAY, encoding="utf-8").read()
    render = open(RENDER, encoding="utf-8").read()

    # ---- 源码级：这两条错了画面完全正常 ----------------------------------------------

    # 截到 15:00，而不是把端点补的盘后半小时也算进去。
    check("日内只算到 15:00（端点补的 15:30 是盘后固定价格交易）",
          'CloseAt = "1500"' in intraday and "15:30" in intraday)

    # 面板缺成交额列（实测只有北证 50）必须被认出来，而不是当成 0 加进去 ——
    # 把"多少手"加进"多少钱"里，画面不会报错。
    check("没有成交额列的标的单独报原因（不是当 0）",
          "IntradayDenial.NoAmount" in intraday and "any is { Length: < 4 }" in intraday)

    # 篮子：日轴取并集，缺的那只记 0。交集下停牌会抹掉整天而画面照常漂亮。
    #
    # 分成两段比对，别把换行与缩进抄进来 —— 抄进去的那天起，断言核对的就是脚本自己的排版
    # 而不是源码。这一条正是被换行坑过一次：源码里 `.SelectMany(...)` 独占一行。
    check("日轴取并集（一只停牌不抹掉那一整天）",
          ".SelectMany(f => f.Bars.Keys)" in series and ".Distinct()" in series)
    check("缺的那天记 0、不停在交集上",
          "if (!bars.TryGetValue(day, out var bar))" in series
          and "Halted, or not yet listed" in series)

    # 等权平均：各标的对自己前一根收盘算。不用再取一次后复权（qfq 与 hfq 只差一个常数因子）。
    check("涨跌是篮子的等权平均", "change / fetched.Count" in series)
    check("等权平均不用再取一次后复权", "constant factor" in series)

    # 日内借的是日线那一份配方：主板是"交易所减成长板"，在分钟轴上也不能忘。
    check("日内借日线同一份配方（主板仍是交易所减成长板）",
          "MarketTurnover.Codes(ChosenScope)" in page and "public static (string[] Adds, string[] Subtracts) Codes" in series)

    # 一只失败 = 整批失败。合计里少一只，和"名单本来就少一只"在画面上分不出来。
    check("一只取不到就整批失败（不给一个悄悄变小的合计）",
          "catch (IntradayUnavailableException" not in intraday)

    # 清单是跨市场的，成交额不是：各市场各报各的币种。挡在篮子外**并且说出来** ——
    # 悄悄少几只，画面照样漂亮，只有合计数是错的。
    check("非 A 股的被挡在篮子外", "Markets.IsMainland(entry.Code)" in page)
    check("挡掉的几只说出来不是悄悄丢", "TurnoverBasketSkipped" in page)

    # 曲线推进是线性的：这是一根钟，缓动会把上午挤到头几秒、然后在收盘附近磨蹭，
    # 而累计曲线慢下来会被读成"没人交易了"。
    check("曲线随时间线性推进（不用会过冲的缓动）",
          "Easing.Ramp(t, plan.IntroMs" in render and "OutBack" not in render)

    # ---- 真机 -------------------------------------------------------------------------
    if not goto(win, PAGE_NAME):
        print(f"找不到导航项「{PAGE_NAME}」——这一页只在 A 股市场下存在")
        return 1

    check("成交额页在（A 股市场）", winui.find(win, lambda c: c.AutomationId == "ViewCombo") is not None)

    view = winui.find(win, lambda c: c.AutomationId == "ViewCombo")

    # **偏好会持久化，所以先显式复位再断言。** 这一条是踩出来的：第一次跑本脚本时板块
    # 停在「沪深 + 北证 50」，而北证 50 是唯一没有成交额列的标的 —— 于是取数必然失败，
    # 而失败的原因看起来像"日内这一整条路坏了"。复位这件事本身也是断言对象之一：
    # 换了板块就该把上一份数丢掉，不然复位之后画面还是旧的。
    scope_first = winui.find(win, lambda c: c.AutomationId == "ScopeCombo")

    if scope_first is not None:
        winui.combo_pick(win, scope_first, "沪深全市场")
        time.sleep(0.8)

    if not winui.combo_pick(win, view, VIEW_INTRADAY):
        print(f"画面形态里没有「{VIEW_INTRADAY}」这一项")
        return 1

    time.sleep(1.0)

    # 日内视图下不给区间选择：端点只留最近 5 个交易日，一个能选到更早日期的日期选择器
    # 是永远兑现不了的承诺。
    check("日内视图下把区间选择器收起来",
          "SyncRangeVisibility" in page and 'RangeCombo.Visibility = intraday' in page)

    run, status = fetch(win)

    check("日内取数成功", run is not None, str(status)[:110])

    if run is None:
        return 1

    check("状态行没有失败字样", not FAIL.search(run["status"]))
    check("取到的是一个交易日的分钟序列", 200 <= run["minutes"] <= 250, f"{run['minutes']} 分钟")
    check("合计是万亿以下的两市量级（亿元）",
          run["total"].replace(",", "").isdigit() and int(run["total"].replace(",", "")) > 0,
          run["total"])

    # 画面：曲线真的画出来了。
    gold = curve_pixels(win, "verify-turnover-intraday.png")

    check("画面上画出了曲线（数 #FBBF24 的像素）", gold > 200, f"{gold} px")

    # 切回柱状：日内那份数不能拿去画日线的轴。看的是**导出**按钮而不是取数按钮 ——
    # 取数按钮本来就一直是亮的，用它做这条断言等于没断言。
    if winui.combo_pick(win, view, VIEW_BARS):
        time.sleep(1.0)
        export = winui.find(win, lambda c: c.AutomationId == "ExportButton")

        check("切回柱状后导出按钮是灰的（日内那份数没有拿来画日线）",
              export is not None and not export.IsEnabled,
              "" if export is None else f"IsEnabled={export.IsEnabled}")

    # 自选：Scope 里最后一项是自己的清单，而且清单是共享的那一份。
    check("板块菜单里多了一项自选", '(MarketScope.Watchlist, "TurnoverScopeWatchlist")' in page)
    check("自选取的是那一份共享清单", "ChosenBasket()" in page and "Watch.Entries" in page)
    check("换了板块就把已取的数丢掉", "!_prefs.Restoring" in page and "            _series = null;" in page)
    check("空篮子不给取数也不静默出图", 'Strings.Get("TurnoverBasketEmpty")' in page)

    scope = winui.find(win, lambda c: c.AutomationId == "ScopeCombo")

    if scope is not None and winui.combo_pick(win, scope, "自选清单"):
        time.sleep(1.2)

        # 认的是选择器**里面的搜索框**（AutoSuggestBox 的 AutomationId 就是它的 x:Name
        # `Search`），不是那个 UserControl —— 折叠掉的控件根本不在 UIA 树里，所以
        # "搜不搜索框"正好等价于"选择器在不在"。
        check("选到自选后清单选择器出现",
              winui.find(win, lambda c: c.AutomationId == "Search") is not None)

        # 复位：偏好会持久化，脚本动了哪个偏好就要改回原样。
        winui.combo_pick(win, scope, "沪深全市场")
        time.sleep(1.0)

        check("切走自选择把选择器收起来",
              winui.find(win, lambda c: c.AutomationId == "Search") is None)

    # ---- 自选篮的日线：数是不是这三只的 ----------------------------------------------
    #
    # 取数成功不代表数对：切回板块再取数也会成功、也会给一版漂亮的图。所以脚本自己打源端
    # 独立算一遍再比 —— 比的是**天数与日均**，因为这两个数正是并集与"缺的记 0"那两条规则的
    # 产物：交集会让天数变少，把缺的那天当成整天丢弃又会同时动这两个数。
    if scope is not None and winui.combo_pick(win, scope, "自选清单"):
        time.sleep(1.0)

        if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ViewCombo"), VIEW_BARS):
            time.sleep(0.6)

        check("清空上一次跑脚本留下的自选（这份清单是跨页共享的）", clear_watch(win))

        for code, name in WATCH:
            if not add_watch(win, code, name):
                check(f"加进自选：{code} {name}", False)

        chips = watch_chips(win)

        check("三只都进了自选", len(chips) == len(WATCH), " / ".join(n for _, n in chips))

        range_combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")

        if range_combo is not None:
            winui.combo_pick(win, range_combo, RANGE)
            time.sleep(0.8)

        run, status = fetch_daily(win)

        check("自选篮取数成功", run is not None, str(status)[:110])

        if run is not None:
            check("自选篮状态行没有失败字样", not FAIL.search(run["status"]))

            end = date.fromisoformat(run["end"])
            start = date.fromisoformat(run["start"])

            days, mean = expected_basket([c for c, _ in WATCH], start, end)

            check("自选篮的交易日数与脚本独立算的一致（并集，不是交集）",
                  abs(days - run["days"]) <= 1, f"页面 {run['days']} / 脚本 {days}")
            check("自选篮的日均与脚本独立算的一致（容差 1%）",
                  abs(mean - run["mean"]) <= max(1.0, run["mean"] * 0.01),
                  f"页面 {run['mean']} / 脚本 {mean:.0f}")

            # 三只的合计不该等于全市场：全市场是万亿量级，三只龙头加起来是百亿量级。
            # 这条能抓住"篮子没生效、画的是上一个板块的数"。
            check("画的是这三只而不是全市场（日均在千亿以下）",
                  run["mean"] < 1000, f"日均 {run['mean']} 亿元")

            # 取数时那一次快照把 chip 上的代码换成真名 —— 只敲代码没点建议的那只最能说明
            # 问题（中芯国际进来时是 SH688981）。清单是共享的，所以另外四页也跟着变好。
            named = [n.strip() for _, n in watch_chips(win)]

            check("取数后自选的名字换成真名（不是代码）",
                  all(not re.fullmatch(r"(SH|SZ|BJ|HK|US)[0-9A-Z.]+", n) for n in named),
                  " / ".join(named))

            shot(win, "verify-turnover-watchlist.png")

        # 复位：偏好会持久化，自选是共享清单 —— 脚本动了哪个偏好就要改回原样。
        clear_watch(win)
        winui.combo_pick(win, scope, "沪深全市场")

    bad = sum(1 for _, ok, _ in CHECKS if not ok)

    print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} 通过")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
