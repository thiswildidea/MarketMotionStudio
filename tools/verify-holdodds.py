# -*- coding: utf-8 -*-
"""真机验证「持有胜率」。

前两页（大类资产 / 回撤与修复）都只用了区间的两个端点：一个进场、一个出场。这一页用的是
区间里**每一次**进场。近十年、持有三年：纳指 ETF 八十四次进场全部是赚的，恒生 ETF 只有四成
——而这两档在前两页里是被十年总收益拉开的。所以验证抓三件事：

1. **胜率算对了。** 脚本自己按同一条复权路径独立算一遍，最常赚的那档与它的胜率、最不常赚的
   那档与它的胜率、档数、月份数，逐项与状态行比对。
2. **「走完」的定义对了。** 一次持有从**它走完的那个月**才计入。若按买入的月份计，区间末尾
   三年买进的会被算成亏损，每一行在动画最后都会被日历压弯——画面照常排序、照常竞速，看不出来。
3. **门槛对了。** 一次持有是 0% 或 100%，一个有六次以下观测的胜率会霸住排名的一端。行要等到
   第六次持有走完才上板，所以开头的帧不满板。

另有两种错只能靠脚本发现：
- **复权用对了。** 和前两页同一条路（TotalReturnBarsAsync）。用反了画面同样合理。
- **量词。** 表头「N 个月 · N 个标的」在 UIA 树里没有节点，只有像素——只能做源码级断言。

用法：python tools/verify-holdodds.py
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

# 取到 8 档 · 84 个月 · 持有 36 个月 · 最常赚：纳指ETF 100.0% · 最不常赚：恒生ETF 40.5%
FETCHED = re.compile(
    r"(\d+)\s*档\s*·\s*(\d+)\s*个月\s*·\s*持有\s*(\d+)\s*个月\s*·\s*最常赚：(\S+?)\s*(\d+\.\d)%"
    r"\s*·\s*最不常赚：(\S+?)\s*(\d+\.\d)%")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO, "src/MarketMotionStudio/Market/HoldOdds.cs")
PAGE = os.path.join(REPO, "src/MarketMotionStudio/Pages/HoldOddsPage.xaml.cs")

# 默认那一组（全部八档）与默认区间（近十年）、默认持有期（三年），与页面的默认值一致。
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

# 页面上「股票」那一组，顺序与 AssetClassLists.Equity 一致。
EQUITY = CODES[:4]

FEWEST = 6

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

    自选股是跨市场的（这一页不看市场设置），脚本若只认通用端点，港股和美股那两行会一路
    取到空表 —— 而应用照常出榜，两边各说各话谁也不报错。
    """
    if code.startswith("hk"):
        return "https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get", "hfq"
    if code.startswith("us"):
        return "https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get", "qfq"
    return "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get", "hfq"


def monthly(code, start, end):
    """源端的月线，**复权**——和应用里 TotalReturnBarsAsync 用的是同一条路径。

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


def expected(start, end, hold, codes=None):
    """每个标的：到最后一个月为止，已走完的持有中赚钱的那一部分占多少。

    复刻两处容易写错的地方，两处错了画面都照常：
      - 一次持有记在**走完的那个月**，不是买入的那个月；
      - 板面从第一个可能有持有走完的月份开始（前面 `hold` 个月没有已完成的持有）。
    """
    per = [(name, monthly(code, start, end)) for code, name in (codes or CODES)]

    months = sorted({m for _, series in per for m in series})
    days = len(months) - hold
    out = []

    for name, series in per:
        own = next((i for i, m in enumerate(months) if m in series), None)

        if own is None:
            continue

        # 缺月沿用上一根：那个洞是源端的，不是持有人的。全长数组，`own` 之前留零——那一档
        # 当时还不存在，循环也从 `own` 开始，所以那些位置永远不会被读。
        closes = [0.0] * len(months)
        last = series[months[own]]

        for i in range(own, len(months)):
            if months[i] in series:
                last = series[months[i]]

            closes[i] = last

        wins_at = [0] * len(months)
        ends_at = [0] * len(months)

        for i in range(own, len(months) - hold):
            if closes[i] <= 0:
                continue

            ends_at[i + hold] += 1

            if closes[i + hold] > closes[i]:
                wins_at[i + hold] += 1

        running = 0
        won = 0
        rate = 0.0
        begun = None

        for t in range(days):
            running += ends_at[hold + t]
            won += wins_at[hold + t]

            if running >= FEWEST:
                rate = won * 100.0 / running

                if begun is None:
                    begun = t

        if running < FEWEST:
            continue

        out.append({"name": name, "rate": rate, "windows": running, "joined": begun})

    return days, out


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


def canvas_box(whole):
    """The canvas rectangle, found by colour.

    Not by a proportion of the window: on a light theme the window's own background is light,
    and a crop that assumed the canvas fills the frame counted the whole settings panel as one
    enormous white row.

    **Vivid, not dark.** "Dark" was the first rule here and it works on most boards, whose
    backgrounds are near-black — but this page's canvas is a deep red, so `max(r, g, b) < 95`
    matched the window's own chrome instead and the row count came out as one. Saturation is
    what those two really differ in: a grey window has none, whatever its brightness, and every
    canvas in this app has a lot.
    """
    pixels = whole.load()
    width, height = whole.size

    def vivid(x, y):
        r, g, b = pixels[x, y]
        return max(r, g, b) - min(r, g, b) > 60 and max(r, g, b) > 60

    columns = [sum(1 for y in range(0, height, 4) if vivid(x, y)) for x in range(width)]
    widest = max(columns)
    band = [x for x, count in enumerate(columns) if count > widest * 0.5]

    if not band:
        return None

    left, right = band[0], band[-1]

    across = [sum(1 for x in range(left, right, 4) if vivid(x, y)) for y in range(height)]
    tallest = max(across)
    band = [y for y, count in enumerate(across) if count > tallest * 0.5]

    if not band:
        return None

    return left, right, band[0], band[-1]


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

    名称是每行一处、位置固定、白得发亮的文字；条形本身是饱和的彩色，不会被算进白字里。
    只在两行贴太近时它们的文字会连成一带，所以只会少算不会多算。
    """
    try:
        from PIL import Image
    except ImportError:
        return -1

    path = shot(win, name)
    whole = Image.open(path).convert("RGB")
    pixels = whole.load()

    box = canvas_box(whole)

    if box is None:
        return -1

    left, right, top, bottom = box

    # Over the rows only: the credit line sits below them and is bright enough to count as one
    # more row.
    first = top + int((bottom - top) * 0.20)
    last = top + int((bottom - top) * 0.85)

    # The name column: the left quarter of the canvas. The title and the date are centred, so
    # they are not in it.
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
        # A gap of six: a glyph's strokes come and go over a couple of scanlines, and two rows
        # are fifty apart, so nothing inside one name splits and nothing between two merges.
        if y - previous > 6:
            bands += 1

        previous = y

    return bands


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

    return {
        "assets": int(hit.group(1)),
        "months": int(hit.group(2)),
        "hold": int(hit.group(3)),
        "best": hit.group(4),
        "best_pct": float(hit.group(5)),
        "worst": hit.group(6),
        "worst_pct": float(hit.group(7)),
        "status": status,
    }, status


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

    # 与前两页同一条路：这一页必须复权。匹配调用而不是名字——注释里会提到 RawBarsAsync 是为
    # 了解释为什么不用它，所以「名字出现过」不等于「用错了」。
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

    # 一次持有从**走完的那个月**才计入，不是从买入的那个月。
    check("持有记在走完的那个月（不是买入的那个月）", "endsAt[i + hold]++" in source)
    check("只有走完的才计入（起点推到 hold 之后）", "for (var i = own; i + hold < all.Length; i++)" in source)
    check("板面从第一个可能有持有走完的月份开始", "var days = all.Length - hold;" in source)
    check("胜率是赚钱的次数除以走完的次数", "row[t] = (won * 100.0) / running;" in source)

    # 门槛：一次持有是 0% 或 100%，不够六次不上板。
    check("不够六次的持有不画（门槛）", "if (running >= FewestWindows)" in source)
    check("门槛是常量而不是写死在判断里", "public const int FewestWindows = 6;" in source)

    # 行按自己的第一个月起算：2019 年才有的那一档没有更早的进场可以计胜負。
    check("行按自己的第一个月起算（不是按画面第一天）",
          "var own = -1;" in source and "closes[i] = last;" in source)

    # 状态行是格式化的：带 {0} 的键用 `Strings.Get` 读会把占位符印在卡片上。
    check("状态行格式化而非原样读", 'Strings.Format(\n                "HoldOddsFetched"' in page)

    # ---- 0c) 源码级：自选股这一组
    #
    # 自选能不能画出来不是问题 —— 切回内置组再取数也会成功。问题在**数是谁的**：所以断在
    # 「清单从共享的那份来」而不是「页面上有个搜索框」。
    check("清单里有一组是自选股", '(Watchlist.RosterKey, "SectorListStocks")' in page)
    check("自选组取的是那一份共享清单",
          "ChosenKey() is Watchlist.RosterKey ? Watch.Entries" in page)
    check("自选组的计数词换成「只个股」（基金叫标的，个股不是）",
          'Watchlist.RosterKey ? "SectorUnitStocks"' in page)

    # 换组/增删之后必须把上一份数丢掉：留着的话，画面照常漂亮而标题已经换了名字。
    check("换了组就把已取的数丢掉", "if (!_prefs.Restoring)\n        {\n            _series = null;" in page)
    check("增删自选后也把已取的数丢掉", "private void OnWatchChanged" in page)

    # 名字由端点纠正一次，四页读的是同一个名字。
    check("取数后把名字改成端点叫的", "Watchlist.Rename(entry.Code" in page)
    check("自选不足三只不给取数", "list.Count < Watchlist.Fewest" in page)

    store = open(os.path.join(REPO, "src/MarketMotionStudio/Pages/Watchlist.cs"),
                encoding="utf-8").read()

    check("自选是一份共享的集合，不是每页各读一次",
          "public static ObservableCollection<RaceEntry> Picks" in store)
    check("自选存在盘上（重启还在）", 'StudioPreferences Store = new("Watchlist.")' in store)
    check("自选有上限（和板块竞速那一份一致）", "public const int Most = 16;" in store)

    picker = open(os.path.join(REPO, "src/MarketMotionStudio/Views/WatchlistPicker.xaml.cs"),
                 encoding="utf-8").read()

    # 这一页不看市场设置，所以搜索不能只问一个市场 —— 否则港股和美股搜不出来，而它们能画。
    check("自选的搜索问三个市场", "foreach (var id in Markets.All)" in picker)

    # ---- 1) 页面在
    if not goto(win, "持有胜率"):
        check("导航里有「持有胜率」", False)
        return report()

    check("导航里有「持有胜率」", True)
    check("标的下拉在", winui.find(win, lambda c: c.AutomationId == "ListCombo") is not None)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("持有期下拉在", winui.find(win, lambda c: c.AutomationId == "HoldCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    note = winui.find(win, lambda c: c.AutomationId == "HoldOddsNote")

    if note is not None:
        body = " ".join(texts(note))
        check("说明卡写了胜率是走完的持有中的占比", "比率" in body or "八十四次" in body, body[:60])
        check("说明卡里没有字面 {0}", "{0}" not in body, body[:60])

    method = winui.find(win, lambda c: c.AutomationId == "HoldOddsMethodNote")

    if method is not None:
        body = " ".join(texts(method))
        check("口径说明写了从走完的那个月起算", "走完" in body, body[:60])
        check("口径说明写了六次这个门槛", "六" in body, body[:60])

    # ---- 2) 档位
    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    options = winui.combo_labels(win, combo) if combo is not None else []

    check("区间下拉是那五档",
          set(options) == {"近 3 年", "近 5 年", "近 10 年", "最长", "自定义"},
          " / ".join(options))

    groups = winui.combo_labels(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"))

    check("标的组是那四组（多了自选股）",
          set(groups) == {"全部八类", "股票", "非股票", "自选股"}, " / ".join(groups))

    holds = winui.combo_labels(win, winui.find(win, lambda c: c.AutomationId == "HoldCombo"))

    check("持有期是那四档",
          set(holds) == {"1 年", "2 年", "3 年", "5 年"}, " / ".join(holds))

    # ---- 3) 近 10 年 · 持有 3 年
    # Preferences persist, so every dial is set explicitly: a previous run leaves the page on
    # whichever group, span and holding period it last used.
    winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "全部八类")
    winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "RangeCombo"), "近 10 年")
    winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "HoldCombo"), "3 年")

    data, status = fetch(win)

    if data is None:
        check("取数成功并报出胜率", False, status[:120])
        return report()

    check("取数成功并报出胜率", True)

    # 脚本自己按同一条复权路径算一遍。
    today = date.today()
    start = today.replace(year=today.year - 10)
    days, rows = expected(start, today, 36)

    check("持有期是三年", data["hold"] == 36, f"{data['hold']} 个月")
    check("月份数与独立算的一致（板面从第一个走完的月份起）", data["months"] == days,
          f"页面 {data['months']} / 脚本 {days}")
    check("八档都在", data["assets"] == len(rows), f"页面 {data['assets']} / 脚本 {len(rows)}")

    best = max(rows, key=lambda r: r["rate"])
    worst = min(rows, key=lambda r: r["rate"])

    check("最常赚的是同一档", data["best"] == best["name"],
          f"页面 {data['best']} / 脚本 {best['name']}")
    check("最常赚的胜率对得上", abs(data["best_pct"] - best["rate"]) < 0.06,
          f"页面 {data['best_pct']} / 脚本 {best['rate']:.2f}")
    check("最不常赚的是同一档", data["worst"] == worst["name"],
          f"页面 {data['worst']} / 脚本 {worst['name']}")
    check("最不常赚的胜率对得上", abs(data["worst_pct"] - worst["rate"]) < 0.06,
          f"页面 {data['worst_pct']} / 脚本 {worst['rate']:.2f}")

    # 这一页存在的理由：两个数字差得足够远。前两页按十年总收益排出来的名次，到这里会重排。
    check("同一批标的里胜率拉得开（这一页比前两页多说了一件事）",
          best["rate"] - worst["rate"] > 20,
          f"{best['name']} {best['rate']:.1f}% vs {worst['name']} {worst['rate']:.1f}%")

    # 有档位真的每次都赚、也有档位真的不是每次都赚——否则胜率这一列就是一个常数。
    check("有档位不是每次都赚（胜率不是常数 100%）", worst["rate"] < 90,
          f"最低 {worst['name']} {worst['rate']:.1f}%")

    # 每一个进场的次数：十年、三年持有 → 每行八十四次左右，豆粕因为 2019 年才有而更少。
    check("每行的持有次数够多（不是三次观测撑出来的比率）",
          all(r["windows"] >= 24 for r in rows),
          "、".join(f"{r['name']} {r['windows']}" for r in rows))

    check("状态行没有失败字样", not FAIL.search(data["status"]))

    # ---- 4) 画面
    if scrub(win, 1.0):
        painted = frame_pixels(win, "verify-holdodds-final.png")
        check("画面上确实是彩色的一块（不是空板）", painted > 2000, f"{painted} px")

        final = drawn_rows(win, "verify-holdodds-final.png")
        check("最后一帧八行都画了", final == len(rows), f"{final} 行 / 应有 {len(rows)}")

    if scrub(win, 0.15):
        early = drawn_rows(win, "verify-holdodds-early.png")
        check("开头那一帧还没画满（六次门槛 + 豆粕 2019 才有）", 0 < early < len(rows),
              f"{early} 行 / 满板 {len(rows)}")

    # ---- 5) 换持有期：同样的十年，问题变了，答案也变
    if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "HoldCombo"), "1 年"):
        data1, status1 = fetch(win)

        if data1 is None:
            check("换成持有一年后再取数", False, status1[:100])
        else:
            check("换成持有一年后再取数", True)
            check("持有期报的是一年", data1["hold"] == 12, f"{data1['hold']} 个月")

            days1, rows1 = expected(start, today, 12)

            check("一年的月份数与独立算的一致", data1["months"] == days1,
                  f"页面 {data1['months']} / 脚本 {days1}")

            best1 = max(rows1, key=lambda r: r["rate"])

            check("一年最常赚的是同一档", data1["best"] == best1["name"],
                  f"页面 {data1['best']} / 脚本 {best1['name']}")
            check("一年最常赚的胜率对得上", abs(data1["best_pct"] - best1["rate"]) < 0.06,
                  f"页面 {data1['best_pct']} / 脚本 {best1['rate']:.2f}")

            # 同一批标的、同一段十年，持有一年与持有三年不是一个问题，所以答案也不是同一组
            # 数字。比整组胜率而不比「最常赚」那一个：那一档在这里是 100%，一年的也是 100%，
            # 拿它当证据等于没验证。若一档都没变，说明持有期这个下拉根本没接进取数。
            rates3 = {r["name"]: r["rate"] for r in rows}
            rates1 = {r["name"]: r["rate"] for r in rows1}
            moved = [n for n in rates3 if n in rates1 and abs(rates3[n] - rates1[n]) > 0.05]

            check("持有一年与持有三年的胜率不同（下拉真的接进去了）", len(moved) >= 3,
                  "、".join(f"{n} {rates3[n]:.1f}%→{rates1[n]:.1f}%" for n in moved[:4])
                  or "一档都没变")

    # ---- 6) 换一组
    if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "股票"):
        data4, status4 = fetch(win)

        if data4 is None:
            check("换成「股票」组后再取数", False, status4[:100])
        else:
            check("换成「股票」组后再取数", True)
            check("股票组是四档", data4["assets"] == 4, f"{data4['assets']} 档")

            # 股票组最常赚的那一档，同样由脚本独立算出来。前两页在这一条上栽过：断言
            # 「换组后领先的变了」，而那一档在两组里都是领先——换了组，答案可以不变，
            # 不变不等于没换。所以这里比的是算出来的那两个数，而不是「变了没有」。
            _, rows4 = expected(start, today, 12, EQUITY)
            best4 = max(rows4, key=lambda r: r["rate"])

            check("股票组最常赚的是同一档", data4["best"] == best4["name"],
                  f"页面 {data4['best']} / 脚本 {best4['name']}")
            check("股票组最常赚的胜率对得上", abs(data4["best_pct"] - best4["rate"]) < 0.06,
                  f"页面 {data4['best_pct']} / 脚本 {best4['rate']:.2f}")

            if scrub(win, 1.0):
                shot(win, "verify-holdodds-equity.png")

    # ---- 6b) 自选股：一份清单，四页共用，三个市场混装
    #
    # 这一页本来只有那八档境内基金。加了自选之后，最难的不是画出来，而是**证明画面上的数
    # 真的是这几只的**：切回内置组再取数也会成功、也会给一版漂亮的榜。所以脚本自己打源端
    # 独立算一遍胜率再逐项比对 —— 而且这三只里有一只在另一个端点上（hk → hkfqkline）。
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
            check("自选组报的是三只", data5["assets"] == len(WATCH), f"{data5['assets']} 只")

            _, rows5 = expected(start, today, 12, WATCH)

            check("自选组三行都在（港股那一行也取到了数）", len(rows5) == len(WATCH),
                  "、".join(r["name"] for r in rows5))

            if rows5:
                best5 = max(rows5, key=lambda r: r["rate"])
                worst5 = min(rows5, key=lambda r: r["rate"])

                check("自选组最常赚的是同一只", data5["best"] == best5["name"],
                      f"页面 {data5['best']} / 脚本 {best5['name']}")
                check("自选组最常赚的胜率对得上",
                      abs(data5["best_pct"] - best5["rate"]) < 0.06,
                      f"页面 {data5['best_pct']} / 脚本 {best5['rate']:.2f}")
                check("自选组最不常赚的胜率对得上",
                      abs(data5["worst_pct"] - worst5["rate"]) < 0.06,
                      f"页面 {data5['worst_pct']} / 脚本 {worst5['rate']:.2f}")

        # 一份清单，不是四份：在另一页上也看得见这三只。
        if goto(win, "回撤与修复"):
            if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "自选股"):
                there = watch_chips(win)

                check("同一份自选在回撤页也看得到（不是各存各的）",
                      len(there) == len(WATCH), " / ".join(n for _, n in there))

            goto(win, "持有胜率")
    else:
        check("清单里多了「自选股」这一组", False)

    # ---- 7) 偏好留住了
    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)

    if goto(win, "持有胜率"):
        group = winui.find(win, lambda c: c.AutomationId == "ListCombo")
        kept = winui.value(group) if group is not None else None

        check("重启后标的组仍记着（还是「自选股」）", kept == "自选股", str(kept))

        # 共享的那份清单跨重启还在：三只都还在，不是取数时才临时凑出来的。
        check("重启后自选那三只还在（清单存在盘上，不是内存里）",
              len(watch_chips(win)) == len(WATCH),
              " / ".join(n for _, n in watch_chips(win)))

        hold = winui.find(win, lambda c: c.AutomationId == "HoldCombo")
        kept_hold = winui.value(hold) if hold is not None else None

        check("重启后持有期仍记着（还是「1 年」）", kept_hold == "1 年", str(kept_hold))

    return report()


if __name__ == "__main__":
    sys.exit(main())
