# -*- coding: utf-8 -*-
"""真机验证「大类资产」。

这一页和第十三页（指数长跑）是同一副算术的两端，所以**最该被抓住的错是复权用反了**：
那一页必须不复权，这一页必须复权。用反了画面完全合理——条形照样长、状态行照样有数，
只有数字是错的，而且错得不显眼：

- 货币 ETF 的价格十三年从 100.161 走到 100.901，不复权是 **+0.0%**：唯一从没跌过的那一行
  会被画成垫底，读出来是「持有现金是最差的选择」。
- 纳指 ETF 拆过份额，不复权只有 +136%，而它跟踪的指数同期涨了六倍。

所以这里做两件事：源码级断言这一页走的是 `TotalReturnBarsAsync`（复权）而不是
`RawBarsAsync`；真机取数后**脚本自己按同一条复权路径独立算一遍**，与状态行逐项比对。

另有两种错只能靠脚本发现，截图看不出来：

1. **量词。** 表头「N 个月 · N 个标的」在 UIA 树里没有节点，只有像素——所以只能做源码级
   断言：量词由页面传，渲染器不许自己编。
2. **还没上场的行占了位置。** 豆粕 ETF 2019 年才有。把它当成 0% 会排在每一个下跌过的资产
   **之上**。所以断言排名只在在场的行之间做。

用法：python tools/verify-assetrace.py
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

# 8 个标的 · 120 个月 · 领先的是 纳指ETF，+578.20% · 垫底的是 货币ETF，+18.76%
FETCHED = re.compile(
    r"(\d+)\s*个标的\s*·\s*(\d+)\s*个月\s*·\s*领先的是\s*(\S+?)\s*[，,]\s*([+−\-]?\d+\.\d+)%"
    r"\s*·\s*垫底的是\s*(\S+?)\s*[，,]\s*([+−\-]?\d+\.\d+)%")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO, "src/MarketMotionStudio/Market/AssetRace.cs")
PAGE = os.path.join(REPO, "src/MarketMotionStudio/Pages/AssetRacePage.xaml.cs")
RENDER = os.path.join(REPO, "src/MarketMotionStudio/Render/SectorRaceRenderer.cs")
SERIES = os.path.join(REPO, "src/MarketMotionStudio/Market/SectorSeries.cs")

# 默认那一组（全部八类）与默认区间（近十年），与页面的默认值一致。
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
    数字差几个百分点，而应用照常出榜，两边各说各话谁也不报错。（在回撤页上栽出来的同一条：
    港股那只页面 −66.86%、脚本按通用端点算成 −69.83%。）
    """
    if code.startswith("hk"):
        return "https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get", "hfq"
    if code.startswith("us"):
        return "https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get", "qfq"
    return "https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get", "hfq"


def monthly(code, start, end):
    """源端的月线，**后复权**——和应用里 TotalReturnBarsAsync 用的是同一条路径。

    这是这一页与指数长跑唯一的分岔口，脚本必须站在同一边：取 `hfqmonth` 块，
    取不到才退回 `month`。拿 raw 去比对复权的结果，差的是倍数而不是小数点。

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


def expected(start, end, codes=None):
    """每个标的的累计涨幅，以及它们共用的那根月份轴。

    `codes` 给的是自选那组：同一套算术，只是名单从读者来。不给就用内置那八档。
    """
    per = [(name, monthly(code, start, end)) for code, name in (codes or CODES)]

    months = sorted({m for _, series in per for m in series})

    out = []

    for name, series in per:
        own = next((m for m in months if m in series), None)

        if own is None:
            continue

        out.append((name, (series[months[-1]] / series[own] - 1) * 100))

    return months, sorted(out, key=lambda kv: -kv[1])


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


def canvas_box(whole):
    """The canvas rectangle, found by colour.

    Not by a proportion of the window: the crop that used to be here ("the canvas is 39%–62%
    across") counted one row on this page's frames, because the window layout is not a fixed
    fraction and the preview has no automation node to measure. Saturation is what the canvas
    and the window around it really differ in: grey chrome has none, whatever its brightness,
    and every canvas in this app has a lot.
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


def drawn_rows(win, name):
    """Counts the rows a frame actually draws, from its pixels.

    A row is a name plus a bar plus a value label. The name is the dependable part: it sits at a
    fixed place in every row and it is bright and nearly grey, while the bar beside it is
    saturated colour and so never counts as a glyph. Where two rows are close their names merge,
    so a count can come out low and never high.
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

    # Over the rows only: the title above and the credit below are bright enough to count as one
    # more row each.
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


def add_watch(win, code):
    """在自选的搜索框里填一个代码并提交。

    代码走剪贴板而不是按键，回车提交而不是点建议：建议弹层是另一个顶层窗口。
    """
    box = winui.find(win, lambda c: c.AutomationId == "Search")
    edit = None if box is None else winui.find(box, lambda c: c.AutomationId == "TextBox", limit=6)

    if edit is None:
        return False

    edit.SetFocus()
    time.sleep(0.3)
    edit.SendKeys("{Ctrl}a", waitTime=0.3)
    auto.SetClipboardText(code)
    edit.SendKeys("{Ctrl}v", waitTime=0.5)
    time.sleep(1.0)
    edit.SendKeys("{Enter}", waitTime=0.5)
    time.sleep(2.0)

    return True


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
        return float(text.replace("−", "-").replace("+", ""))

    return {
        "assets": int(hit.group(1)),
        "months": int(hit.group(2)),
        "top": hit.group(3),
        "top_pct": pct(hit.group(4)),
        "bottom": hit.group(5),
        "bottom_pct": pct(hit.group(6)),
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
    series = open(SERIES, encoding="utf-8").read()

    # 这一页与指数长跑唯一的分岔：复权。用反了画面照样合理，所以只能断言在源码里。
    # 匹配的是调用而不是名字：这一页的注释里正大光明地提到了 RawBarsAsync——那段注释讲的就是
    # 为什么这一页不能用它，所以「名字出现过」不等于「用错了」。
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
    check("上场月份由数据层带出来", "IReadOnlyList<int>? Starts = null" in series)
    check("渲染器读的是数据层那一份", "series.StartOf(k)" in render)
    check("排名只在在场的行之间做", "i >= _starts[k]" in render)
    check("还没上场的行不画", "state.DayIndex < _starts[k]" in render)
    check("晚来的行按自己的第一个月起算（不是按画面第一天）",
          "var own = -1;" in source and "@base" in source)

    # 状态行是格式化的：带 {0} 的键用 `Strings.Get` 读会把占位符印在卡片上。
    check("状态行格式化而非原样读", 'Strings.Format(\n                "AssetRaceFetched"' in page)

    # ---- 1) 页面在
    if not goto(win, "大类资产"):
        check("导航里有「大类资产」", False)
        return report()

    check("导航里有「大类资产」", True)
    check("资产下拉在", winui.find(win, lambda c: c.AutomationId == "ListCombo") is not None)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    note = winui.find(win, lambda c: c.AutomationId == "AssetRaceNote")

    if note is not None:
        body = " ".join(texts(note))
        check("说明卡写了分红算回去了", "分红" in body, body[:60])
        check("说明卡里没有字面 {0}", "{0}" not in body, body[:60])

    method = winui.find(win, lambda c: c.AutomationId == "AssetRaceMethodNote")

    if method is not None:
        body = " ".join(texts(method))
        check("口径说明写了月线与复权", "月线" in body and "复权" in body, body[:60])

    # ---- 2) 档位
    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    options = winui.combo_labels(win, combo) if combo is not None else []

    check("区间下拉是那五档",
          set(options) == {"近 3 年", "近 5 年", "近 10 年", "最长", "自定义"},
          " / ".join(options))

    groups = winui.combo_labels(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"))

    # 四组：三个内置清单 + 读者的自选。少一组说明接线掉了，多一组说明别处也挂上了。
    check("资产组是那四组",
          set(groups) == {"全部八类", "股票", "非股票", "自选股"}, " / ".join(groups))

    # ---- 3) 近 10 年取数
    # Preferences persist, so both dials are set explicitly: a previous run leaves the page on
    # whichever group and span it last used.
    winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "全部八类")

    if combo is not None:
        winui.combo_pick(win, combo, "近 10 年")

    run, status = fetch(win)
    check("近 10 年取数成功", run is not None, str(status)[:90])

    if run is None:
        return report()

    check("画了 8 个标的", run["assets"] == 8, str(run["assets"]))

    # 不是 121：源端的月线在「近十年」这段里只给 113–114 个月，见汇率走廊页那条同样的注。
    check("月份数落在十年的量级（108–125）", 108 <= run["months"] <= 125, str(run["months"]))
    check("领先的不低于垫底的", run["top_pct"] >= run["bottom_pct"],
          f"{run['top_pct']}% vs {run['bottom_pct']}%")
    check("领先与垫底是两个不同的标的", run["top"] != run["bottom"],
          f"{run['top']} / {run['bottom']}")
    check("状态行没有失败字样", not FAIL.search(run["status"]))

    # 复权有没有生效，看的是现金那一行：不复权它是 +0.0%，复权它是十几个百分点。
    check("垫底那一行不是 0.00%（复权生效了，现金不是零收益）",
          abs(run["bottom_pct"]) > 1.0, f"{run['bottom_pct']}%")

    shot(win, "verify-assetrace-10y.png")

    coloured = frame_pixels(win, "verify-assetrace-frame.png")

    check("画面上画出了有颜色的条形（不是空白帧）", coloured > 2000, f"{coloured} 个彩色像素")

    # ---- 4) 榜是「长出来」的：豆粕 ETF 2019 年才有，所以第一帧比最后一帧少一行
    early = -1

    if scrub(win, 0.06):
        early = drawn_rows(win, "verify-assetrace-early.png")

    scrub(win, 1.0)

    final = drawn_rows(win, "verify-assetrace-final.png")

    # 数出来的行数是保守的（两行的发光糊在一起就少算一行），所以最后一帧只断言「画满了」，
    # 开头那一帧的断言是「比最后一帧少」。
    check("最后一帧把榜画满了（7 行以上）", final >= 7, f"{final} 行")
    check("开头那一帧比最后一帧少（晚来的还没上场）", 0 < early < final,
          f"{early} 行 vs 最后一帧 {final} 行")

    # ---- 5) 独立算一遍
    end = date.today()
    start = end.replace(year=end.year - 10)
    months, mine = expected(start, end)

    check("脚本自己取到了八个标的的月线", len(mine) == 8, f"{len(mine)} 个")
    check("脚本的月份轴与页面一致（容差 1 个月）", abs(len(months) - run["months"]) <= 1,
          f"页面 {run['months']} / 脚本 {len(months)}")

    if len(mine) == 8:
        check("领先的标的与页面一致", mine[0][0] == run["top"],
              f"页面 {run['top']} / 脚本 {mine[0][0]}")
        check("垫底的标的与页面一致", mine[-1][0] == run["bottom"],
              f"页面 {run['bottom']} / 脚本 {mine[-1][0]}")
        check("领先的涨幅与页面一致（容差 0.5 个百分点）",
              abs(mine[0][1] - run["top_pct"]) <= 0.5,
              f"页面 {run['top_pct']}% / 脚本 {mine[0][1]:.2f}%")
        check("垫底的涨幅与页面一致（容差 0.5 个百分点）",
              abs(mine[-1][1] - run["bottom_pct"]) <= 0.5,
              f"页面 {run['bottom_pct']}% / 脚本 {mine[-1][1]:.2f}%")

    # ---- 6) 换一组：只剩四个，垫底也换了人
    group = winui.find(win, lambda c: c.AutomationId == "ListCombo")

    if group is not None:
        winui.combo_pick(win, group, "股票")

        other, status = fetch(win)
        check("换到股票组后取数成功", other is not None, str(status)[:90])

        if other is not None:
            check("股票组是 4 个标的", other["assets"] == 4, str(other["assets"]))

            # 四行全是境内外的股票，垫底从「现金」换成这组里最差的那只。
            check("换组后垫底变了", other["bottom"] != run["bottom"],
                  f"{run['bottom']} → {other['bottom']}")

            # 四行是这一档的全部，且四行间隔大不会糊在一起，所以数得准。
            scrub(win, 1.0)

            four = drawn_rows(win, "verify-assetrace-equity.png")

            check("股票组画面上只有 4 行", four == 4, f"{four} 行")

    # ---- 6b) 自选股：一份清单，四页共用，三个市场混装
    #
    # 这一页本来只有那八档境内基金，而且**只有复权这一条路是对的**（不复权的货币 ETF 是
    # +0.0%，会变成垫底）。自选里放进一只拆过份额的或一只高分红的，走错路的代价立刻现形；
    # 但更难的是证明画面上的数真的是这几只的 —— 切回内置组再取数也会成功、也会给一版漂亮
    # 的榜。所以脚本自己打源端独立算一遍再逐项比对，而且这三只里有一只在另一个端点上
    # （hk → hkfqkline + hfq）。
    WATCH = [("sh600519", "贵州茅台"), ("sh510300", "沪深300ETF"), ("hk00700", "腾讯控股")]

    if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "自选股"):
        check("清单里多了「自选股」这一组", True)

        # 搜索框只在选中这一组时才在：另外三组是内置清单，没有可填的东西。
        check("选了自选股才出现搜索框",
              winui.find(win, lambda c: c.AutomationId == "Search") is not None)

        check("清空上一次跑脚本留下的自选（这份清单是跨会话共享的）", clear_watch(win))

        for code, _ in WATCH:
            if not add_watch(win, code):
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

            _, mine5 = expected(start, end, WATCH)

            check("自选组三行都在（港股那一行也取到了数）", len(mine5) == len(WATCH),
                  "、".join(n for n, _ in mine5))

            if len(mine5) == len(WATCH):
                check("自选组领先的是同一只", mine5[0][0] == data5["top"],
                      f"页面 {data5['top']} / 脚本 {mine5[0][0]}")
                check("自选组领先的涨幅对得上（容差 0.5 个百分点）",
                      abs(mine5[0][1] - data5["top_pct"]) <= 0.5,
                      f"页面 {data5['top_pct']}% / 脚本 {mine5[0][1]:.2f}%")
                # 垫底也要比对：只比领先的话，中间那几行（尤其是跨市场那只，脚本容易走错
                # 端点）算错了也没人发现。
                check("自选组垫底的是同一只", mine5[-1][0] == data5["bottom"],
                      f"页面 {data5['bottom']} / 脚本 {mine5[-1][0]}")
                check("自选组垫底的涨幅对得上（容差 0.5 个百分点）",
                      abs(mine5[-1][1] - data5["bottom_pct"]) <= 0.5,
                      f"页面 {data5['bottom_pct']}% / 脚本 {mine5[-1][1]:.2f}%")
                # 茅台十年分红不算多，但拆过的 ETF 与高分红的个股只有复权才算得平 —— 垫底
                # 那一行的绝对值必须大于 1%，否则说明这一组又走了不复权那条路。
                check("自选组垫底那行不是 0.00%（复权生效了）",
                      abs(data5["bottom_pct"]) > 1.0, f"{data5['bottom_pct']}%")

        # 一份清单，不是四份：在另一页上也看得见这三只。
        if goto(win, "回撤与修复"):
            if winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "自选股"):
                there = watch_chips(win)

                check("同一份自选在回撤页也看得到（不是各存各的）",
                      len(there) == len(WATCH), " / ".join(n for _, n in there))

            goto(win, "大类资产")
    else:
        check("清单里多了「自选股」这一组", False)

    # ---- 7) 重启后还记得
    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)
    goto(win, "大类资产")

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    remembered = winui.value(combo) if combo is not None else None

    check("重启后区间仍记着",
          remembered in ("近 3 年", "近 5 年", "近 10 年", "最长", "自定义"),
          str(remembered))

    group = winui.find(win, lambda c: c.AutomationId == "ListCombo")
    kept = winui.value(group) if group is not None else None

    # 上一节把这一页留在自选股上，所以重启后记着的应该是自选股。
    check("重启后资产组仍记着（还是「自选股」）", kept == "自选股", str(kept))

    # 共享清单跨重启还在：三只都还在，不是取数时才临时凑出来的。
    check("重启后自选那三只还在（清单存在盘上，不是内存里）",
          len(watch_chips(win)) == len(WATCH),
          " / ".join(n for _, n in watch_chips(win)))

    return report()


if __name__ == "__main__":
    sys.exit(main())
