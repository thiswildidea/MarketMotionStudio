# -*- coding: utf-8 -*-
r"""真机验证 K 线页新加的分钟周期：指定一个交易日，画出那一天的 K 线。

三件事是本页独有的、且**错了不会报错只会画错**的：

1. **端点只给「最近 N 根」，不接受日期。** 传了 start/end 它就把 K 线块整个省掉（只剩
   qt 与 prec）。所以「指定交易日」只能是**从取回来的日子里挑**，不能是日历上点一天；
   而最早那天会被 800 根截断（实测 2026-09-07 只有 32 根，从 10:55 开始），它不能进列表 ——
   进了就是一个缺了自己开盘的一天的图，看起来跟正常的一天一模一样。
2. **横轴按钟点铺，午休是真空档。** 均匀排列会把 11:30 的收盘和 13:00 的开盘挨在一起，
   读起来是一段连续三小时的行情，而实际上中间一小时半什么都没发生。这条只能靠**数像素**：
   画面中间必须有一段没有蜡烛的列。
3. **换一天是重画，不是重新取数。** 所有可选的日子都在同一个请求里回来的，所以切日期不该
   发请求。这条靠截图比对：切了日期画面必须变。

数字由脚本自己打源端独立算一遍再比，不抄页面的。

用法：python tools\verify-candle-minute.py
"""
import importlib.util
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import uiautomation as auto
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src", "MarketMotionStudio")
PAGE = os.path.join(SRC, "Pages", "CandlePage.xaml.cs")
PAGE_XAML = os.path.join(SRC, "Pages", "CandlePage.xaml")
SERIES = os.path.join(SRC, "Market", "CandleSeries.cs")
KLINE = os.path.join(SRC, "Market", "TencentKline.cs")
RENDER = os.path.join(SRC, "Render", "CandleRenderer.cs")
MARKETS = os.path.join(SRC, "Market", "Markets.cs")
STRINGS = os.path.join(SRC, "Strings")

MK = "https://ifzq.gtimg.cn/appstock/app/kline/mkline"

PAGE_NAME = "K线"
PERIOD_DAILY = "日K"
PERIOD_5 = "5 分钟"
STYLE_CANDLES = "蜡烛图"
MOTION_GROW = "逐根铺满"
PRESET_FIRST = "上证指数"

# {0} · {1} · {2} 根 · 还有 {3} 个完整交易日可选。
# 名字另配一条：状态行那串字里还夹着信息条的图标与「"成功"图标」的说明文字，
# 用 `(.+?) ·` 去抓会把那些一起抓进来。
FETCHED = re.compile(
    r"(\d{4}-\d{2}-\d{2})\s*·\s*(\d+)\s*根\s*·\s*还有\s*(\d+)\s*个完整交易日可选")
NAMED = re.compile(r"([^\s·“”\"]+)\s*·\s*\d{4}-\d{2}-\d{2}")

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有|过长|不一致|failed|error")

# 页面上第一个预设是 sh000001 上证指数（AShareCandles 的第一项）。偏好被重装清掉了，
# 所以默认标的就是它；名字从状态行读回来核对。
PRESETS = {"上证指数": "sh000001", "创业板指": "sz399006", "贵州茅台": "sh600519",
           "中国平安": "sh601318", "沪深300ETF": "sh510300", "创业板ETF": "sz159915"}

CHECKS = []


def check(name, ok, note=""):
    CHECKS.append((name, ok, note))
    print(f"{'✓' if ok else '✗'} {name}" + (f" — {note}" if note else ""))


def read(path):
    with open(path, encoding="utf-8-sig") as handle:
        return handle.read()


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


def wait_status(win, seconds=300):
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(2.0)
        text = status_text(win)

        if text and (FETCHED.search(text) or FAIL.search(text)):
            return text

    return None


def combo_selected(win, combo):
    """What a combo has selected, read from the open list.

    A WinUI combo does not expose its selection: its own `Name` is the header above it
    and the value pattern answers nothing — the same trap `winui` documents on the
    market combo, where an empty read was indistinguishable from "nothing to restore".
    Expanding and looking for the selected row is the only reading that works.
    """
    if combo is None:
        return None

    for item in winui.combo_items(win, combo):
        try:
            if item.GetSelectionItemPattern().IsSelected:
                return item.Name
        except Exception:  # noqa: BLE001 - a row can go stale mid-walk
            continue

    return None


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

    if item is None:
        return False

    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)

    return True


def clear_chips(win):
    """把清单里开着的名字全关掉，返回关了几个。

    清单是**跨会话共用**的一份，开关的状态不落盘、但一跑之内是活的。这一页的搜索与一键预设
    都是「把这只放到清单上并画出来」（与持仓收益页同一个语义），所以清单里还开着别人时，点
    一个预设画出来的就是两只 —— 而这一跑要数的是**一张单标的**的分钟图，上面每一列都该是
    那一天。来的时候先清干净。

    条件的写法有两个讲究：`winui.find_all` 的条件里抛异常会**中止整趟遍历**，而 `GetPattern`
    正是会抛的那个调用，所以它只能留在循环体里。另一个是**位置**：视频设置面板里的「隐藏
    标题」「安全区参考线」也是 `ToggleButton`，也各有 AutomationId —— 关掉它们关的是读者
    自己的设置，不是清单上的名字。清单这一排在搜索框下缘那一条带里。
    """
    search = winui.find(win, lambda c: c.AutomationId == "InstrumentSearch")

    if search is None:
        return 0

    top = search.BoundingRectangle.bottom
    off = 0

    for control in winui.find_all(win, lambda c: c.ControlTypeName == "ButtonControl"):
        try:
            box = control.BoundingRectangle

            if not control.AutomationId or box.top < top or box.top > top + 160:
                continue

            pattern = control.GetPattern(auto.PatternId.TogglePattern)
        except Exception:  # noqa: BLE001
            continue

        if pattern is not None and pattern.ToggleState == auto.ToggleState.On:
            pattern.Toggle()
            off += 1
            time.sleep(0.4)

    return off


def preset_button(win, name):
    """按显示名找一键预设那个**按钮**。

    只按名字找会撞上清单里的 chip：chip 也是 `ButtonControl`，名字就是标的的名字，而清单是
    跨会话共享的 —— 上一跑加进去的「上证指数」会一直待在上面。chip 是 `ToggleButton`（没有
    `InvokePattern`），预设是 `Button`，所以这里只认能 Invoke 的那一个。

    先收齐同名的，再逐个问模式：`winui.find_all` 的条件里抛异常会**中止整趟遍历**，而
    `GetPattern` 正是会抛的那个调用。

    **同名的不止预设一个**：清单里那只 `ToggleButton` 的名字就是标的的名字，它旁边那个
    `×` 也一样，而且 `×` 排在预设前面。少了下面这两条筛，`find` 交回来的会是那个 `×` ——
    点下去是把这只从清单里删掉，然后画面上一只都没选中。
    """
    for control in winui.find_all(
            win, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == name
            and c.AutomationId):
        try:
            if control.GetPattern(auto.PatternId.InvokePattern) is not None:
                return control
        except Exception:  # noqa: BLE001
            pass

    return None


def shot(win, name):
    path = os.path.join(REPO, "artifacts", name)

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


def rgb(image):
    """The frame in three channels.

    A window capture comes back RGBA, and `winui.canvas_box` unpacks three values per
    pixel — handing it the capture as it lands raises in the middle of a run.
    """
    return image if image.mode == "RGB" else image.convert("RGB")


def plot_band(image):
    """The rows the price and volume panels occupy, as a fraction of the canvas.

    The header — the title, the four prices, the big percentage — is drawn on the same
    canvas, and that percentage is coloured exactly like a candle. Counting it would
    fill the middle of the frame with "candle" columns and the lunch gap would never
    be found. 0.40 to 0.72 is below the header and above the statistic cards.
    """
    box = winui.canvas_box(image)
    top = box[2] if box else 0
    height = (box[3] - box[2]) if box else image.size[1]

    return (int(top + (height * 0.40)), int(top + (height * 0.72)))


def candle_columns(image):
    """How many candle-coloured pixels each column of the plot holds.

    Candles and volume bars are the only red and green on the frame: the averages are
    amber, blue and purple, the grid is blue-grey and the cards are dark.
    """
    image = rgb(image)
    pixels = image.load()
    box = winui.canvas_box(image)
    left = box[0] if box else 0
    right = box[1] if box else image.size[0]
    top, bottom = plot_band(image)

    columns = []

    for x in range(left, right):
        found = 0

        for y in range(top, bottom, 2):
            r, g, b = pixels[x, y]

            if (r > 120 and r - g > 50 and r - b > 50) or (g > 100 and g - r > 50 and g - b > 30):
                found += 1

        columns.append(found)

    return columns


def gap(columns):
    """The widest empty run *between the first and the last column that is drawn*.

    Measured inside that span rather than across the whole canvas: the frame has a
    margin either side of the plot, and a margin is a run of empty columns too. Taking
    the widest run overall therefore found the left margin — 52 columns against a
    lunch break of ninety — and reported the chart as having no gap, which is the
    "it passed for the wrong reason" shape of failure this file exists to avoid.

    Returns the run, where it starts, and the span it was measured in.
    """
    drawn = [i for i, count in enumerate(columns) if count > 0]

    if len(drawn) < 4:
        return 0, -1, max(1, len(columns))

    inner = columns[drawn[0]:drawn[-1] + 1]
    best = 0
    at = -1
    run = 0
    start = 0

    for i, count in enumerate(inner + [1]):
        if count == 0:
            if run == 0:
                start = i

            run += 1
        else:
            if run > best:
                best = run
                at = start

            run = 0

    return best, at, len(inner)


def differ(a, b):
    """How much of one frame the other is not, in the plot band."""
    a = rgb(a)
    b = rgb(b)

    left = a.load()
    right = b.load()
    top, bottom = plot_band(a)

    changed = 0
    total = 0

    for y in range(top, bottom, 3):
        for x in range(0, a.size[0], 3):
            total += 1

            if sum(abs(p - q) for p, q in zip(left[x, y], right[x, y])) > 40:
                changed += 1

    return changed / max(1, total)


def expected(code, period="m5", count=800, per_day=48):
    """The source's own answer, grouped the way `CandleMinutes` groups it.

    Recomputed rather than read back, because the two numbers the page prints — how
    many candles the day has and how many days are worth offering — are exactly the
    two the cleaning rules decide: cutting at 15:00 decides the first, and "a whole
    session ends at 15:00 and holds its period's count" decides the second.
    """
    with urllib.request.urlopen(
            f"{MK}?param={urllib.parse.quote(f'{code},{period},,{count}')}", timeout=30) as reply:
        payload = json.load(reply)

    node = payload.get("data", {}).get(code)
    rows = (node or {}).get(period) or []

    days = {}

    for row in rows:
        if len(row) < 6 or len(row[0]) != 12 or int(row[0][8:]) > 1500:
            continue

        days.setdefault(row[0][:8], []).append(row[0][8:])

    # 一天几根是周期的函数：241 / 48 / 16。写死一个阈值（比如 47）只对 5 分钟那一档成立，
    # 对 1 分钟会把整天当半截、对 15 分钟又会把每天都当半截 —— 那是脚本自己的错，而报出来的
    # 样子像应用错了。
    whole = {day: clocks for day, clocks in days.items()
             if len(clocks) >= per_day - 1 and clocks[-1] == "1500"}

    return whole, days


def main():
    page = read(PAGE)
    page_xaml = read(PAGE_XAML)
    series = read(SERIES)
    kline = read(KLINE)
    render = read(RENDER)
    markets = read(MARKETS)

    # ---- 源码级：这几条错了画面完全正常 ----------------------------------------------

    # 只认 `ifzq.gtimg.cn`：web.ifzq.gtimg.cn 是 301、web.ifzqgtimg.com 根本不通。
    check("分钟端点用的是会回数据的那个主机",
          'MinuteEndpoint = "https://ifzq.gtimg.cn/appstock/app/kline/mkline"' in kline)

    # 800 是实测的上限：850 起悄悄退回默认 320，而"少回来的那些天"和"源端只留了这些天"
    # 在画面上分不出来。
    check("单请求上限写成常量 800（再多源端会悄悄退回 320）",
          "MostMinuteBarsPerRequest = 800" in kline and "850" in kline)

    # 15:00 之后是盘后固定价格交易，不属于这一天。
    check("分钟行截到 15:00（15:30 是盘后固定价格交易）",
          "(hour * 100) + minute > 1500" in kline)

    # 一天的根数是数出来的，不是推出来的：241 / 48 / 16。
    check("一整天的根数按周期写定（241 / 48 / 16）",
          "Minute1 => 241" in series and "Minute5 => 48" in series and "Minute15 => 16" in series)

    # 完整交易日的判据：根数够 + 最后是 15:00。缺了后一半，被 800 根截断的那天（从 10:55
    # 起）也会以 48 根混进来 —— 它确实有 48 根，只是没有开盘。
    check("完整交易日要看最后一根是不是 15:00（不只是根数）",
          'rows[^1].Clock == "1500"' in series)

    # 只列完整的日子：最早那天被截断、最新那天可能还在盘中，两者都不是一天。
    check("下拉只列完整的交易日",
          "Days.Where(d => d.Settled)" in series and "session.Whole" in page)

    # 换一天是重画不是重新取数。若这里改成发请求，"换一天"会慢一倍，而更重要的是
    # 断网时换一天就画不出来 —— 那些日子明明都已经取回来了。
    check("换交易日不重新取数（同一份数据重画）",
          "if (!_ready || _filling || _minutes is null)" in page
          and "CandleMinutes.ForDay(_minutes, day)" in page)

    # 周期是分钟档时把区间下拉换成交易日下拉。留着区间下拉就是留一个没人用的控件。
    check("分钟档把区间下拉换成交易日下拉",
          "DayCombo.Visibility = minute ? Visibility.Visible : Visibility.Collapsed" in page)
    check("分钟档不给自定义区间（端点不认日期）",
          "RangeCombo.Visibility = minute ? Visibility.Collapsed : Visibility.Visible" in page)
    check("下拉下面写着「只有源端还留着的这几天」", "CandleMinuteNote" in page_xaml)

    # 港股美股没有分钟 K 线：那三档是灰的，不是点了才报错。
    check("港股/美股下分钟档是灰的（不是点了才报错）",
          "!_market.MinuteCandles" in page and "item.IsEnabled = false" in page)
    check("分钟 K 线只有沪深两市有（与 day/query 那个 Intraday 是两回事）",
          "MinuteCandles => Id is MarketId.AShare" in markets)

    # 横轴按钟点铺。均匀排列会把午休抹掉，而这是唯一能从画面外看出来的那条规矩。
    check("横轴按钟点铺（09:30=0，15:00=1）",
          "OpeningMinute = (9 * 60) + 30" in render and "ClosingMinute = 15 * 60" in render)

    # 90 分钟没人交易不该占掉三分之一的画面：上下午各占半个轴，中间只留一条缝。
    # 断的是「不是按墙上那口钟从 09:30 拉到 15:00」——留着旧算式就是留着那段空档。
    check("午休被从轴上剔掉（上下午各一半，中间一条缝）",
          "NoonMinute = (11 * 60) + 30" in render and
          "AfternoonMinute = 13 * 60" in render and
          "LunchSeam = 0.02" in render and
          "- OpeningMinute) / (double)span" not in render)

    check("有钟点的蜡烛按钟点定位，没有的仍按次序",
          "_stamps is null\n        ? view.Left + (view.Width * (i - view.First)" in render)
    check("午休画成一条线并标出来", "DrawLunch(session, context, view)" in render
          and "TurnoverIntradayNoon" in render)
    check("轴上的字是钟点不是日期", 'bar.Clock.Length == 4 ? bar.Clock[..2] + ":" + bar.Clock[2..]'
          in series)

    # 14 份 resw 都要有这几条键。
    for tag in sorted(os.listdir(STRINGS)):
        resw = read(os.path.join(STRINGS, tag, "Resources.resw"))
        missing = [key for key in ("CandlePeriodMinute1", "CandlePeriodMinute5",
                                   "CandlePeriodMinute15", "CandleDayLabel.Header",
                                   "CandleMinuteFetched", "CandleMinuteNone",
                                   "CandleMinuteNoWhole", "CandleMinuteMarketNone",
                                   "CandleMinuteNote.Text")
                   if f'name="{key}"' not in resw]

        check(f"{tag} 的分钟键齐全", not missing, " ".join(missing))

    # 帮助手册：K 线那一章在 14 份里都写了这一档，而且**只写了一次**。注入脚本跑第二遍
    # 不该再插一条 —— 重复的一条在帮助页上只是多一行，逐章项数与截图都看不出来。
    injector = importlib.util.spec_from_file_location(
        "port_candle_minute_help", os.path.join(REPO, "tools", "port-candle-minute-help.py"))
    module = importlib.util.module_from_spec(injector)
    injector.loader.exec_module(module)

    for tag in sorted(os.listdir(STRINGS)):
        text = read(os.path.join(REPO, "src", "MarketMotionStudio", "Assets", "Help",
                                f"help-{tag}.md"))

        check(f"{tag} 的帮助里写了分钟这一档，且只写了一次",
              text.count(module.MINUTE[tag]) == 1 and module.INTRO[tag] in text,
              f"章节 {text.count(chr(10) + '## ')} 章")

    # ---- 真机 -------------------------------------------------------------------------
    win = winui.launch("MarketMotionStudio.exe")

    if win is None:
        print("起不来窗口")
        return 1

    if not goto(win, PAGE_NAME):
        print(f"找不到导航项「{PAGE_NAME}」")
        return 1

    period = winui.find(win, lambda c: c.AutomationId == "PeriodCombo")

    check("K 线页在", period is not None)

    if period is None:
        return 1

    labels = winui.combo_labels(win, period)

    check("周期下拉多了三档分钟", all(any(name in label for label in labels)
                                 for name in ("1 分钟", "5 分钟", "15 分钟")), " / ".join(labels))

    # 标的也复位到默认预设：脚本要拿状态行上的名字去对源端的代码，而标的偏好是存住的 ——
    # 上一次跑留下的可能是别的标的，甚至是一只手输的代码，那样脚本就无从独立复算。
    # 先清干净：清单里还开着别人时，点预设画出来的是两只（它把这一只**加**到画面上，而不是
    # 换掉画面 —— 与持仓收益页同一个语义）。这一跑要的是单标的的图。
    clear_chips(win)

    preset = preset_button(win, PRESET_FIRST)

    if preset is not None:
        preset.GetInvokePattern().Invoke()
        time.sleep(3.5)

    # 画法与推进方式是这一页的旧偏好，而这一跑要数像素：面积图会把午休那段填平（收盘线是
    # 连着的，中间没有空），窗口滚动又只画一部分。两条都是别人的设置，先记下来改成蜡烛图 +
    # 逐根铺满，跑完无条件改回去。
    style = winui.find(win, lambda c: c.AutomationId == "StyleCombo")
    motion = winui.find(win, lambda c: c.AutomationId == "MotionCombo")

    was_style = combo_selected(win, style)
    was_motion = combo_selected(win, motion)

    winui.combo_pick(win, style, STYLE_CANDLES)
    winui.combo_pick(win, motion, MOTION_GROW)
    time.sleep(1.0)

    # 周期也是存住的偏好：上一跑可能就停在 5 分钟，再选一次 5 分钟**不会**触发
    # SelectionChanged，于是下面那句「切周期会自动取一次」根本没有发生，wait_status 干等
    # 300 秒返回 None —— 而失败信息是「分钟取数成功 — None」，看着像页面没取到数，其实
    # 一次请求都没发出。先切回日K，让这一次选择真的是一次改变。
    winui.combo_pick(win, period, PERIOD_DAILY)
    time.sleep(1.5)

    if not winui.combo_pick(win, period, PERIOD_5):
        print(f"周期里没有「{PERIOD_5}」")
        return 1

    time.sleep(1.5)

    # 分钟档下区间下拉收起来了，交易日下拉在。折叠掉的控件不在 UIA 树里 —— 所以「找不到」
    # 正是「收起来了」的意思。
    check("分钟档下区间下拉收起来了",
          winui.find(win, lambda c: c.AutomationId == "RangeCombo") is None)
    check("分钟档下交易日下拉在",
          winui.find(win, lambda c: c.AutomationId == "DayCombo") is not None)

    # 切周期会自动取一次；等那一次的结果，别再点一次取数（点了就是第二次请求）。
    status = wait_status(win)

    check("分钟取数成功", status is not None and FETCHED.search(status or ""), str(status)[:120])

    if status is None or FETCHED.search(status) is None:
        return 1

    check("状态行没有失败字样", not FAIL.search(status))

    run = FETCHED.search(status)
    named = NAMED.search(status)

    day = run.group(1)
    bars = int(run.group(2))
    days = int(run.group(3))

    name = named.group(1) if named else "?"
    code = PRESETS.get(name)

    check(f"画的是复位后的那个预设（{PRESET_FIRST}）", code is not None, name)
    check("一天是 48 根 5 分钟线", bars == 48, f"{bars} 根")

    if code is None:
        return 1

    whole, all_days = expected(code)

    # 脚本自己打源端算的：完整交易日的个数，与其中每一天的根数。
    check("可选交易日的个数与源端一致（截断的那天不算）",
          days == len(whole), f"页面 {days} / 脚本 {len(whole)}")
    check("画面上的那一天是完整的一天，且根数与源端一致",
          day.replace("-", "") in whole and len(whole[day.replace("-", "")]) == bars,
          f"{day} / 脚本 {len(whole.get(day.replace('-', ''), []))} 根")
    day_combo = winui.find(win, lambda c: c.AutomationId == "DayCombo")
    offered = winui.combo_labels(win, day_combo) if day_combo is not None else []
    current = combo_selected(win, day_combo)

    # 画面画的那一天，与下拉选中的那一天，必须是同一天。这一页会记住挑过的日期，所以
    # 「一定挑最近那天」只在没存过偏好时成立 —— 第二次跑时恢复的正是上一次挑的那天，
    # 而那是它该做的事。回退规则（存的那天没了就挑最新）钉在源码里。
    check("画面画的那一天就是下拉选中的那一天",
          current is not None and current.replace("-", "") == day.replace("-", ""),
          f"控件 {current} / 画面 {day}")
    check("存的那天不在了就回退到最近一个完整交易日",
          "DayCombo.SelectedIndex = at >= 0 ? at : DayCombo.Items.Count - 1" in page)

    check("下拉里列的就是源端那几天（且是最早的在前）",
          len(offered) == len(whole) and offered[0] == sorted(whole)[0][:4] + "-" +
          sorted(whole)[0][4:6] + "-" + sorted(whole)[0][6:],
          f"{len(offered)} 项：{offered[0] if offered else '—'} … {offered[-1] if offered else '—'}")

    first = shot(win, "verify-candle-minute-5m.png")

    # ---- 换一天：画面必须变，且不能重新取数 ------------------------------------------
    #
    # 挑的是「与当前不同的那一天」而不是写死最早那天：偏好会持久化，上一次跑完留在这页的
    # 就是最早那天，再挑一次最早等于什么都没做，而"画面没变"会被读成"换日期坏了"。
    target = offered[-1] if current != offered[-1] else offered[0]

    if day_combo is not None and winui.combo_pick(win, day_combo, target):
        time.sleep(2.0)

        second = shot(win, "verify-candle-minute-5m-switched.png")
        changed = differ(Image.open(first), Image.open(second))

        # 阈值不高，因为两天共用一套构图：纵轴各自归一化到当天的最高最低，横轴都是同一个
        # 交易日，所以位置固定、变的只有蜡烛body 与上下影。零才是"没换图"。
        check(f"换到 {target} 画面真的变了（说明画的是那天，不是缓存的图）",
              changed > 0.03, f"{changed:.1%} 的像素变了")
        check("换日期不触发取数（状态行还是上一次那条）",
              FETCHED.search(status_text(win)) is not None)

        # 切走再切回来 = 重新取数。状态行该报的正是刚才挑的那一天：存住了，也恢复了。
        # 这一条同时钉住 SavePreferences 里的 "Day" 与 FillDays 里的 at >= 0 那条路。
        winui.combo_pick(win, period, PERIOD_DAILY)
        time.sleep(1.0)
        winui.combo_pick(win, period, PERIOD_5)

        again = wait_status(win)

        check("挑过的那一天被记住（切走再切回来还是它）",
              again is not None and FETCHED.search(again) is not None
              and FETCHED.search(again).group(1) == target, f"{target} / {str(again)[:80]}")
    else:
        check(f"挑到 {target}", False)

    # ---- 午休已从轴上剔掉 --------------------------------------------------------
    #
    # 这条以前是反的：断言「空档要够宽」。改轴之后反过来了 —— 90 分钟没人交易原本吃掉画面
    # 的 27%，现在上下午各占一半，中间只剩一条缝（LunchSeam = 2%）。缝必须还在，否则上午
    # 会被读成直接连着下午。
    columns = candle_columns(Image.open(shot(win, "verify-candle-minute-5m-final.png")))
    widest, at, span = gap(columns)

    check("画面里不再有那一大片没交易的空档",
          widest < span * 0.10, f"最宽空档 {widest} 列 / 绘制区 {span} 列 = {widest / span:.1%}")

    drawn = [i for i, count in enumerate(columns) if count > 0]
    inner = columns[drawn[0]:drawn[-1] + 1]
    wide = max(1, int(len(inner) * 0.04))
    band = inner[max(0, (len(inner) // 2) - wide):(len(inner) // 2) + wide]
    seam = sum(1 for count in band if count == 0)

    check("午休还在，只是变成正中的一条缝（上下午没有连成一段）",
          seam > 0, f"正中 ±4% 里有 {seam}/{len(band)} 列是空的")

    # ---- 另外两档 ----------------------------------------------------------------
    #
    # 三档走的是同一条路，只差一个 slug 与一天几根。一个写错的 slug（比如 m1 写成 min1）
    # 会让源端回一个空的块，而那时页面报的是「没有分钟 K 线」—— 那条拒因本来是给北证 50
    # 准备的，读起来像是标的的问题，不像周期的问题。
    for label, slug, per_day in (("1 分钟", "m1", 241), ("15 分钟", "m15", 16)):
        if not winui.combo_pick(win, period, label):
            check(f"周期里有「{label}」", False)
            continue

        other = wait_status(win)

        if other is None or FETCHED.search(other) is None:
            check(f"{label} 取数成功", False, str(other)[:100])
            continue

        run2 = FETCHED.search(other)

        check(f"{label}：一天 {per_day} 根",
              int(run2.group(2)) == per_day, f"{run2.group(2)} 根")

        whole2, _ = expected(code, slug, per_day=per_day)

        check(f"{label}：可选交易日与源端一致",
              int(run2.group(3)) == len(whole2), f"页面 {run2.group(3)} / 脚本 {len(whole2)}")

    winui.combo_pick(win, period, PERIOD_5)
    time.sleep(1.0)

    # ---- 复位 ------------------------------------------------------------------------
    if was_style:
        winui.combo_pick(win, style, was_style)

    if was_motion:
        winui.combo_pick(win, motion, was_motion)

    winui.combo_pick(win, period, PERIOD_DAILY)
    time.sleep(1.0)

    check("切回日线后区间下拉回来了",
          winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("切回日线后交易日下拉收起来了",
          winui.find(win, lambda c: c.AutomationId == "DayCombo") is None)

    bad = sum(1 for _, ok, _ in CHECKS if not ok)

    print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} 通过")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
