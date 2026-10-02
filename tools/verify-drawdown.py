# -*- coding: utf-8 -*-
"""真机验证「回撤与修复」。

这一页的量有两个，而且**不成比例**——跌得最深的不一定爬得最久。近十年：纳指 ETF 最深
−25.52%、六个月回到高点；中证500ETF 最深 −56.07%、用了八十六个月；黄金与豆粕到今天还没
爬回去。只印一个数字的话，后两者看起来只是前一者的加重版，实际上不是。所以验证要抓两件事：

1. **两个数字都算对了。** 脚本自己按同一条复权路径独立算一遍，最深值、修复月数、离高点最近
   的那一行，逐项与状态行比对。修复月数必须**分两趟**——最深点先定下来再数爬回来的月数。
   一趟算会怎样，探测那一轮已经演示过：每个标的都报「一两个月就修复了」，而其中有一个
   用了七年。这个错在画面上完全看不出来，因为曲线照画、行照样排序。

2. **复权用对了。** 和第十四页同一条路（TotalReturnBarsAsync）。用反了画面同样合理。

另有两种错只能靠脚本发现：
- **整块板共用一把深度尺。** 若每行按自己最惨的那次缩放，货币 ETF 的 0.2% 会被画成和中证500
  的 56% 一样深。断言渲染器用的是统一的 `state.Depth`，不是每行的 `Deepest`。
- **量词。** 表头「N 个月 · N 个标的」在 UIA 树里没有节点，只有像素——只能做源码级断言。

用法：python tools/verify-drawdown.py
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

# 取到 8 档 · 120 个月 · 最深：中证500ETF −56.07%（86 个月修复） · 离自己高点最近：纳指ETF
FETCHED = re.compile(
    r"(\d+)\s*档\s*·\s*(\d+)\s*个月\s*·\s*最深：(\S+?)\s*([−\-]?\d+\.\d+)\s*%（(.+?)）"
    r"\s*·\s*离自己高点最近：(\S+)")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO, "src/MarketMotionStudio/Market/Drawdown.cs")
PAGE = os.path.join(REPO, "src/MarketMotionStudio/Pages/DrawdownPage.xaml.cs")
RENDER = os.path.join(REPO, "src/MarketMotionStudio/Render/UnderwaterRenderer.cs")

# 默认那一组（全部八档）与默认区间（近十年），与页面的默认值一致。
CODES = [
    ("sh510300", "沪深300ETF"),
    ("sh510500", "中证500ETF"),
    ("sh513100", "纳指ETF"),
    ("sz159920", "恒生ETF"),
    ("sh511010", "国债ETF"),
    ("sh518880", "黄金ETF"),
    ("sz159985", "豆粕ETF"),
    ("sh511880", "货币ETF"),
]

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


def endpoint_for(code):
    """`TencentKline.TotalReturn` 的那张路由表：代码前缀决定端点和复权档。

    自选那一组是跨市场的，脚本若只认通用端点，港股与美股那两行取到的是**另一条序列**——
    数字差几个百分点，而应用照常出榜，两边各说各话谁也不报错。这一条是在回撤页上栽出来的：
    港股那只页面报 −66.86%、脚本按通用端点算成 −69.83%，连「是否已修复」都反过来。
    """
    if code.startswith("hk"):
        return "https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get", "hfq"
    if code.startswith("us"):
        return "https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get", "qfq"
    return "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get", "hfq"


def monthly(code, start, end):
    """源端的月线，**后复权**——和应用里 TotalReturnBarsAsync 用的是同一条路径。

    两条清洗规则一起复刻，否则两边差一个月：
      - `CandlesFromAsync` 丢掉还没走完的月（`IsSettledFor`），十月初取数末月是九月；
      - 同一条调用还按 start/end 裁一遍，因为源端对月线的 start 并不总是买账。
    """
    base, adj = endpoint_for(code)

    url = f"{base}?param={code},month,{start},{end},430,{adj}"

    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30).read().decode("utf-8", "ignore")

    node = json.loads(raw).get("data", {}).get(code, {})

    rows = None
    for key in (adj + "month", "month"):
        value = node.get(key)
        if isinstance(value, list) and value:
            rows = value
            break

    if rows is None:
        for key, value in node.items():
            if "month" in key and isinstance(value, list) and value:
                rows = value
                break

    if not rows:
        return {}

    today = date.today()
    first_of_this_month = today.replace(day=1)

    by_month = {}

    for row in rows:
        day = date.fromisoformat(row[0])

        if float(row[2]) <= 0 or day >= first_of_this_month or day < start or day > end:
            continue

        # 一个月里最后一根就是那个月。
        month = row[0][:7]

        if month not in by_month or row[0] >= by_month[month][0]:
            by_month[month] = row

    return {m: float(r[2]) for m, r in by_month.items()}


# 页面上「股票」那一组，顺序与 AssetClassLists.Equity 一致。
EQUITY = CODES[:4]


def expected(start, end, codes=None):
    """每个标的：最深多少、几个月爬回来、以及到最后一个月的深度。

    两趟，顺序不能倒：最深点必须定下来之后才能开始数修复。一趟算的后果是前面的浅跌先把钟
    设了，后面真正的深跌永远没被计时——探测那一轮每个标的都报「一两个月修复」。
    """
    per = [(name, monthly(code, start, end)) for code, name in (codes or CODES)]

    months = sorted({m for _, series in per for m in series})
    out = []

    for name, series in per:
        own = next((i for i, m in enumerate(months) if m in series), None)

        if own is None:
            continue

        # 缺月沿用上一根：那个洞是源端的，不是持有人的。
        closes = []
        last = series[months[own]]

        for i in range(own, len(months)):
            if months[i] in series:
                last = series[months[i]]

            closes.append(last)

        # 第一趟：每个月当时的高点，以及离它多远。
        high = closes[0]
        highs = []
        under = []

        for close in closes:
            if close > high:
                high = close

            highs.append(high)
            under.append((close / high - 1) * 100)

        # 第二趟：最深那一月，与它跌下去之前的那个高点。
        at = 0
        worst = 0.0

        for i, value in enumerate(under):
            if value < worst:
                worst = value
                at = i

        healed = -1

        if worst < -0.005:
            for i in range(at + 1, len(closes)):
                if closes[i] >= highs[at]:
                    healed = i - at
                    break

        out.append({"name": name, "deepest": worst, "healed": healed, "now": under[-1]})

    return months, out


def heal_text(months):
    if months < 0:
        return "至今未修复"

    return f"{months} 个月修复"


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

    image = whole.crop((0, int(height * 0.10), int(width * 0.62), int(height * 0.92)))
    pixels = image.load()

    coloured = 0

    for y in range(0, image.size[1], 2):
        for x in range(0, image.size[0], 2):
            r, g, b = pixels[x, y]

            if max(r, g, b) > 120 and max(r, g, b) - min(r, g, b) > 60:
                coloured += 1

    return coloured


def drawn_rows(win, name):
    """数一帧上真的画了几行 —— 靠左栏那列的标的名称。

    这一页的行是填充曲线，不是条形：扫描线上的彩色长度随曲线走势变化，同一条曲线会在好几个
    y 上出现，所以「最长色块」那条路（竞速页用的那条）在这里数出来的是锯齿，不是行。

    名称是每行一处、位置固定、白得发亮的文字，扫「低饱和的亮像素」就能一行一处地数出来。
    曲线本身是饱和的彩色，不会被算进白字里。

    只在行数少的档位上断精确值：两行贴太近时它们的文字会连成一带，只会少算不会多算。
    """
    try:
        from PIL import Image
    except ImportError:
        return -1

    path = shot(win, name)
    whole = Image.open(path).convert("RGB")
    pixels = whole.load()
    width, height = whole.size

    def vivid(x, y):
        r, g, b = pixels[x, y]
        return max(r, g, b) - min(r, g, b) > 60 and max(r, g, b) > 60

    # The canvas is found by colour, not by a proportion of the window, because the window's
    # own background is light on a light theme — and a crop that assumed otherwise counted the
    # whole settings panel as one enormous white row.
    #
    # **Vivid, not dark.** "Dark" was the rule here first and it is right about most boards,
    # whose backgrounds are near-black, but on a board whose canvas is tinted it matched the
    # window's own chrome instead and the row count came out as one. Saturation is what the two
    # really differ in: grey chrome has none, whatever its brightness.
    columns = [sum(1 for y in range(0, height, 4) if vivid(x, y)) for x in range(width)]
    widest = max(columns)
    band = [x for x, count in enumerate(columns) if count > widest * 0.5]

    if not band:
        return -1

    left, right = band[0], band[-1]

    across = [sum(1 for x in range(left, right, 4) if vivid(x, y)) for y in range(height)]
    tallest = max(across)
    band = [y for y, count in enumerate(across) if count > tallest * 0.5]

    if not band:
        return -1

    top, bottom = band[0], band[-1]

    # Inside the canvas, over the rows only. The credit line sits below the rows and is bright
    # enough to count as one more, so the scan stops above it rather than counting the board as
    # one row too many.
    first = top + int((bottom - top) * 0.20)
    last = top + int((bottom - top) * 0.85)

    # The name column: the left quarter of the canvas. The title and the date are centred, so they
    # are not in it, and the curve is a saturated colour rather than a bright neutral one.
    name_right = left + int((right - left) * 0.26)

    ys = []

    for y in range(first, last):
        white = 0

        for x in range(left + 2, name_right):
            r, g, b = pixels[x, y]

            if min(r, g, b) > 140 and max(r, g, b) - min(r, g, b) < 60:
                white += 1

        if white >= 2:
            ys.append(y)

    bands = 0
    previous = -10

    for y in ys:
        # A gap of six: a glyph has strokes that come and go over a couple of scanlines, and two
        # rows are fifty apart, so nothing inside one name splits and nothing between two of them
        # merges.
        if y - previous > 6:
            bands += 1

        previous = y

    return bands


def watch_chips(win):
    """自选那一排 chip，每项是 (按钮, 标的名)。

    每个 chip 自己就是删除按钮（点一下就删掉那一条）。两件事都是打印出来才看清的：

      - 那个 `ItemsControl` 在 UIA 里**没有自己的节点**，所以只能从整窗里找；
      - 按钮自己的 `Name` 是**空的**（`Name='' 子树=['贵州茅台', '×']`）—— 名字在子文本里，
        不按按钮名认，否则数出来永远是 0，而画面上三条 chip 好好地在那儿。
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
    """把自选清空。

    **先清空再断言**：这份清单是四页共用、跨会话留下的，上一次跑脚本加的东西还在这里。若
    不清空，取的数是「上次那几只 + 这次这几只」，而脚本按这次这几只重算 —— 两边对不上，
    而画面是一版漂亮的自选榜，看不出它多画了几行。
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
    """在自选的搜索框里填一个代码并提交 —— **提交完还得数一遍**。

    代码走剪贴板而不是按键，回车提交而不是点建议：建议弹层是另一个顶层窗口。而正是那个弹层
    会把回车吃掉：上一轮留下的弹层还开着时，这一下 Enter 落在弹层上而不是提交上，于是这一只
    静静地没进去 —— 不报错、不失败，只是那一排 chip 少一个；后面「至少选 3 只才能竞速」又把
    这笔账算到应用头上。所以提交后数一遍 chip：那只没出现就关掉弹层重来。
    """
    for _ in range(tries):
        box = winui.find(win, lambda c: c.AutomationId == "Search")
        edit = None if box is None else winui.find(
            box, lambda c: c.AutomationId == "TextBox", limit=6)

        if edit is None:
            return False

        # 键盘只发给前台窗口。连着跑几个脚本时，上一个脚本刚把应用重启过，新窗口未必在前台，
        # 于是三个 SendKeys 一个都没落地 —— 表现同样是「这一只静静地没进去」。
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

        if any(n.strip() == name for _, n in watch_chips(win)):
            return True

    return False

def scrub(win, progress):
    """Puts the preview at one moment. The slider is the page's only way in, and a scrub is an
    instruction to look at a moment — the page stops playback wherever it was."""
    slider = winui.find(win, lambda c: c.AutomationId == "Scrub")

    if slider is None:
        return False

    slider.GetRangeValuePattern().SetValue(progress)
    time.sleep(1.6)

    return True


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

    def pct(text):
        # The page writes its minus sign as U+2212, which `float` will not read.
        return float(text.replace("−", "-"))

    return {
        "assets": int(hit.group(1)),
        "months": int(hit.group(2)),
        "deepest": hit.group(3),
        "deepest_pct": pct(hit.group(4)),
        "heal": hit.group(5),
        "shallowest": hit.group(6),
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

    # 与指数长跑相反、与大类资产相同：这一页必须复权。匹配调用而不是名字——注释里会提到
    # RawBarsAsync 是为了解释为什么不用它，所以「名字出现过」不等于「用错了」。
    check("取数走 TotalReturnBarsAsync（复权）", "kline.TotalReturnBarsAsync(" in source)
    check("这一页没有走不复权那条路", "kline.RawBarsAsync(" not in source)
    check("月线，一次拿全历史（不需要分页回溯）", '"month"' in source and "HistoryWalk" not in source)

    kline = open(os.path.join(REPO, "src/MarketMotionStudio/Market/TencentKline.cs"),
                 encoding="utf-8").read()
    check("源端丢掉还没走完的月（脚本也照此复刻）",
          "day < new DateOnly(today.Year, today.Month, 1)" in kline
          and "first_of_this_month" in open(__file__, encoding="utf-8").read())

    # 量词：页面必须自己给，渲染器不许替页面编。
    check("周期词由页面传", 'SpanWord = Strings.Get("MarketCapUnitMonths")' in page)
    check("计数词由页面传", "UnitWord = ChosenUnit()" in page)
    check("自选组的计数词换成「只个股」（基金叫标的，个股不是）",
          'Watchlist.RosterKey ? "SectorUnitStocks" : "AssetRaceUnitAssets"' in page)
    check("渲染器没有写死这一页的量词", "AssetRaceUnitAssets" not in render)

    # ---- 0c) 源码级：自选股这一组
    #
    # 自选能不能画出来不是问题 —— 切回内置组再取数也会成功。问题在**数是谁的**：所以断在
    # 「清单从共享的那份来」而不是「页面上有个搜索框」。
    check("清单里有一组是自选股", '(Watchlist.RosterKey, "SectorListStocks")' in page)
    check("自选组取的是那一份共享清单",
          "ChosenKey() is Watchlist.RosterKey ? Watch.Entries" in page)
    check("自选组的计数词换成「只个股」（基金叫标的，个股不是）",
          'Watchlist.RosterKey ? "SectorUnitStocks"' in page)
    # 换组要把上一份数丢掉：留着的话画面照常漂亮，而标题已经换了名字。分成两段比对，
    # 避免把缩进与换行抄进脚本 —— 抄进去的那天起，断言核对的就是脚本自己的排版。
    check("换了组就把已取的数丢掉",
          "!_prefs.Restoring" in page and "            _series = null;" in page)
    check("增删自选后也把已取的数丢掉", "private void OnWatchChanged" in page)
    check("取数后把名字改成端点叫的", "Watchlist.Rename(entry.Code" in page)
    check("自选不足三只不给取数", "list.Count < Watchlist.Fewest" in page)

    # 还没上场的行：不排名、不画、不占位置。
    check("渲染器只在在场的行之间排序", "i >= _starts[k]" in render)
    check("还没上场的行不画", "state.DayIndex < _starts[k]" in render)
    check("行按自己的第一个月起算（不是按画面第一天）",
          "var own = -1;" in source and "highs[i] = high" in source)

    # 这一页最容易写错的一处：最深点必须先定下来，再数爬回来的月数。
    check("最深点先定下来（第一趟）", "var at = own;" in source and "var worst = 0.0;" in source)
    check("修复从最深点之后开始数（第二趟）",
          "for (var i = at + 1; i < dates.Length; i++)" in source)
    check("爬回去按「跌下去之前的那个高点」判定，不是按「回到 0」", "closes[i] >= from" in source)

    # 整块板共用一把深度尺。
    check("深度是全局的一把尺，不是每行各一把", "value / state.Depth" in render)
    check("渲染器没有拿每行的 Deepest 当尺", "state.Depth" in render and "_series.Deepest[k] / state.Depth" not in render)

    # 状态行是格式化的：带 {0} 的键用 `Strings.Get` 读会把占位符印在卡片上。
    check("状态行格式化而非原样读", 'Strings.Format(\n                "DrawdownFetched"' in page)

    # ---- 1) 页面在
    if not goto(win, "回撤与修复"):
        check("导航里有「回撤与修复」", False)
        return report()

    check("导航里有「回撤与修复」", True)
    check("标的下拉在", winui.find(win, lambda c: c.AutomationId == "ListCombo") is not None)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    note = winui.find(win, lambda c: c.AutomationId == "DrawdownNote")

    if note is not None:
        body = " ".join(texts(note))
        check("说明卡写了曲线才是重点", "曲線" in body or "曲线" in body, body[:60])
        check("说明卡里没有字面 {0}", "{0}" not in body, body[:60])

    method = winui.find(win, lambda c: c.AutomationId == "DrawdownMethodNote")

    if method is not None:
        body = " ".join(texts(method))
        check("口径说明写了月线与复权", "月" in body and ("復原" in body or "复原" in body), body[:60])

    # ---- 2) 档位
    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    options = winui.combo_labels(win, combo) if combo is not None else []

    check("区间下拉是那五档",
          set(options) == {"近 3 年", "近 5 年", "近 10 年", "最长", "自定义"},
          " / ".join(options))

    groups = winui.combo_labels(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"))

    # 四组：三个内置清单 + 读者的自选。少一组说明接线掉了，多一组说明别处也挂上了。
    check("标的组是那四组",
          set(groups) == {"全部八类", "股票", "非股票", "自选股"}, " / ".join(groups))

    # ---- 3) 近 10 年取数
    # Preferences persist, so both dials are set explicitly: a previous run leaves the page on
    # whichever group and span it last used.
    winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "全部八类")
    winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "RangeCombo"), "近 10 年")

    data, status = fetch(win)

    if data is None:
        check("取数成功并报出最深与修复", False, status[:120])
        return report()

    check("取数成功并报出最深与修复", True)

    # 脚本自己按同一条复权路径算一遍。
    today = date.today()
    months, rows = expected(today.replace(year=today.year - 10), today)

    check("月份数与独立算的一致", data["months"] == len(months),
          f"页面 {data['months']} / 脚本 {len(months)}")
    check("八档都在", data["assets"] == len(rows), f"页面 {data['assets']} / 脚本 {len(rows)}")

    deepest = min(rows, key=lambda r: r["deepest"])
    shallowest = max(rows, key=lambda r: r["now"])

    check("最深的是同一档", data["deepest"] == deepest["name"],
          f"页面 {data['deepest']} / 脚本 {deepest['name']}")
    check("最深的深度对得上", abs(data["deepest_pct"] - deepest["deepest"]) < 0.01,
          f"页面 {data['deepest_pct']} / 脚本 {deepest['deepest']:.2f}")
    check("修复月数对得上（这是这一页第二个数字）",
          data["heal"] == heal_text(deepest["healed"]),
          f"页面 {data['heal']} / 脚本 {heal_text(deepest['healed'])}")
    check("离自己高点最近的是同一档", data["shallowest"] == shallowest["name"],
          f"页面 {data['shallowest']} / 脚本 {shallowest['name']}")

    # 「至今未修复」这条分支真的走到了：黄金与豆粕到今天还没爬回去。
    open_ones = [r["name"] for r in rows if r["healed"] < 0]

    check("有行真的没爬回去（未修复这条分支走到了）", len(open_ones) >= 1,
          "、".join(open_ones) or "全都修复了")

    # 这一页存在的理由：两个数字不成比例。断言的方式是找出一对「跌得更浅、却爬得更久」的
    # 标的——只要存在这样一对，「最深」一个数字就没把话说全，这一页就比它多说了一件事。
    # 若怎么找都找不到，那这一页确实只是个更花的条形图。
    by_heal = [r for r in rows if r["healed"] >= 0]
    inverted = [
        (a, b)
        for a in by_heal for b in by_heal
        # 更浅（负数更大）却更久（月数更多）。
        if a["deepest"] > b["deepest"] and a["healed"] > b["healed"]
    ]

    check("跌得更浅的反而爬得更久（深度说不了修复那件事）", len(inverted) > 0,
          "；".join(f"{a['name']} 跌 {a['deepest']:.2f}% 用 {a['healed']} 个月，"
                    f"{b['name']} 跌 {b['deepest']:.2f}% 只用 {b['healed']} 个月"
                    for a, b in inverted[:1]) or "找不到反序的一对")

    check("状态行没有失败字样", not FAIL.search(data["status"]))

    # ---- 4) 画面
    if scrub(win, 1.0):
        painted = frame_pixels(win, "verify-drawdown-final.png")
        check("画面上确实是彩色的一块（不是空板）", painted > 2000, f"{painted} px")

        final = drawn_rows(win, "verify-drawdown-final.png")
        check("最后一帧八行都画了", final == len(rows), f"{final} 行 / 应有 {len(rows)}")

    if scrub(win, 0.06):
        early = drawn_rows(win, "verify-drawdown-early.png")
        check("开头那一帧还没画满（豆粕 2019 才有）", 0 < early < len(rows),
              f"{early} 行 / 满板 {len(rows)}")

    # ---- 5) 换一组
    if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "股票"):
        data4, status4 = fetch(win)

        if data4 is None:
            check("换成「股票」组后再取数", False, status4[:100])
        else:
            check("换成「股票」组后再取数", True)
            check("股票组是四档", data4["assets"] == 4, f"{data4['assets']} 档")

            # 股票组最深的那一档，同样由脚本独立算出来。上一页在这一条上栽过一次：断言
            # 「换组后领先的变了」，而那一档在两组里都是领先——换了组，答案可以不变，不变
            # 不等于没换。所以这里比的是算出来的那两个数，而不是「变了没有」。
            _, rows4 = expected(today.replace(year=today.year - 10), today, EQUITY)
            deep4 = min(rows4, key=lambda r: r["deepest"])

            check("股票组最深的是同一档", data4["deepest"] == deep4["name"],
                  f"页面 {data4['deepest']} / 脚本 {deep4['name']}")
            check("股票组最深的深度对得上", abs(data4["deepest_pct"] - deep4["deepest"]) < 0.01,
                  f"页面 {data4['deepest_pct']} / 脚本 {deep4['deepest']:.2f}")

            if scrub(win, 1.0):
                shot(win, "verify-drawdown-equity.png")

    # ---- 5b) 自选股：一份清单，四页共用，三个市场混装
    #
    # 这一页的量有两个（最深多少 / 多久爬回来），而且必须复权才对。自带那八档是境内基金，
    # 换自选之后放进的是三只**个股与港股**——它们的曲线形状完全不同：茅台 2021 年那次跌了
    # 四成、港股那只跌得更狠。最难的不是画出来，而是证明画面上的两个数真的是这几只的：
    # 切回内置组再取数也会成功、也会给一版漂亮的板。所以脚本自己打源端独立算一遍，最深
    # 那一档的深度与修复月数逐项比对。
    WATCH = [("sh600519", "贵州茅台"), ("sh510300", "沪深300ETF"), ("hk00700", "腾讯控股")]

    if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "自选股"):
        check("清单里多了「自选股」这一组", True)

        # 搜索框只在选中这一组时才在：另外三组是内置清单，没有可填的东西。
        check("选了自选股才出现搜索框",
              winui.find(win, lambda c: c.AutomationId == "Search") is not None)

        check("清空上一次跑脚本留下的自选（这份清单是跨会话共享的）", clear_watch(win))

        for code, name in WATCH:
            if not add_watch(win, code, name):
                check(f"加进自选：{code}", False)

        chips = watch_chips(win)

        check("三只都进了自选（跨市场：A股 + 港股）", len(chips) == len(WATCH),
              " / ".join(n for _, n in chips))

        data5, status5 = fetch(win)

        if data5 is None:
            check("用自选股这一组取数", False, status5[:120])
        else:
            check("用自选股这一组取数", True)
            check("自选组报的是三档", data5["assets"] == len(WATCH), f"{data5['assets']} 档")

            _, rows5 = expected(today.replace(year=today.year - 10), today, WATCH)

            check("自选组三行都算出来了（港股那一行也取到了数）", len(rows5) == len(WATCH),
                  "、".join(r["name"] for r in rows5))

            if len(rows5) == len(WATCH):
                deep5 = min(rows5, key=lambda r: r["deepest"])

                check("自选组最深的是同一只", data5["deepest"] == deep5["name"],
                      f"页面 {data5['deepest']} / 脚本 {deep5['name']}")
                check("自选组最深的深度对得上",
                      abs(data5["deepest_pct"] - deep5["deepest"]) < 0.01,
                      f"页面 {data5['deepest_pct']} / 脚本 {deep5['deepest']:.2f}")
                check("自选组的修复月数对得上（这是这一页第二个数字）",
                      data5["heal"] == heal_text(deep5["healed"]),
                      f"页面 {data5['heal']} / 脚本 {heal_text(deep5['healed'])}")
                # 只有三行、都是个股与港股，深度不可能像货币 ETF 那样只有零点几个百分点 ——
                # 若最深的那一档不到 5%，说明这一组走的是没复权那条路（或干脆没取到数）。
                check("自选组最深那档跌得不轻（不是取到了空序列）",
                      deep5["deepest"] < -5.0, f"{deep5['deepest']:.2f}%")

        # 一份清单，不是四份：在另一页上也看得见这三只。
        if goto(win, "持有胜率"):
            if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "自选股"):
                there = watch_chips(win)

                check("同一份自选在持有胜率页也看得到（不是各存各的）",
                      len(there) == len(WATCH), " / ".join(n for _, n in there))

            goto(win, "回撤与修复")
    else:
        check("清单里多了「自选股」这一组", False)

    # ---- 6) 偏好留住了
    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)

    if goto(win, "回撤与修复"):
        group = winui.find(win, lambda c: c.AutomationId == "ListCombo")
        kept = winui.value(group) if group is not None else None

        # 上一节把这一页留在自选股上，所以重启后记着的应该是自选股。
        check("重启后标的组仍记着（还是「自选股」）", kept == "自选股", str(kept))

        # 共享清单跨重启还在：三只都还在，不是取数时才临时凑出来的。
        check("重启后自选那三只还在（清单存在盘上，不是内存里）",
              len(watch_chips(win)) == len(WATCH),
              " / ".join(n for _, n in watch_chips(win)))

    return report()


if __name__ == "__main__":
    sys.exit(main())
