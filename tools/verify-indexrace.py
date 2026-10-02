# -*- coding: utf-8 -*-
"""真机验证「指数长跑」。

这一页有两种错**只能靠脚本发现**，截图看不出来：

1. **量词。** 表头那行「N 个月 · N 个指数」在 UIA 树里没有节点，截图里只是像素——市值榜
   就是这样错的（月线被画成「12 个交易日」）。所以只能做源码级断言：量词由页面传，
   渲染器不许自己编。
2. **还没上场的行占了位置。** 标普 500 能追溯到 1950 年，道琼斯只到 2009 年，恒生科技
   2020 年才有。把它们当成 0% 有两重错：一是画面上会出现一排 0.00%，二是 0 会排在每一个
   下跌过的指数**之上**，画面中间出现空洞。所以断言排名只在在场的行之间做，且渲染器按
   每行的上场月份跳过。

再者是**数字对不对**：脚本直接打源端，把十二个指数的累计涨幅独立算一遍，与状态行比对。

用法：python tools/verify-indexrace.py
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

# 12 个指数 · 120 个月 · 领先的是 标普500，+273.13% · 垫底的是 恒生科技，−12.10%
FETCHED = re.compile(
    r"(\d+)\s*个指数\s*·\s*(\d+)\s*个月\s*·\s*领先的是\s*(\S+?)\s*[，,]\s*([+−\-]?\d+\.\d+)%"
    r"\s*·\s*垫底的是\s*(\S+?)\s*[，,]\s*([+−\-]?\d+\.\d+)%")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO, "src/MarketMotionStudio/Market/IndexRace.cs")
PAGE = os.path.join(REPO, "src/MarketMotionStudio/Pages/IndexRacePage.xaml.cs")
RENDER = os.path.join(REPO, "src/MarketMotionStudio/Render/SectorRaceRenderer.cs")
SERIES = os.path.join(REPO, "src/MarketMotionStudio/Market/SectorSeries.cs")

# 默认那一组（全部十二个）与默认区间（近十年），与页面的默认值一致。
CODES = [
    ("sh000001", "上证指数"), ("sh000300", "沪深300"), ("sz399001", "深证成指"),
    ("sh000905", "中证500"), ("sz399006", "创业板指"), ("sh000016", "上证50"),
    ("hkHSI", "恒生指数"), ("hkHSCEI", "国企指数"), ("hkHSTECH", "恒生科技"),
    ("usINX", "标普500"), ("usIXIC", "纳斯达克"), ("usDJI", "道琼斯"),
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
    """`TencentKline.TotalReturn` 的那张路由表。

    这一页 2026-10-02 起走的是复权路径（为了能放个股），脚本必须走同一条 —— 若脚本还用空
    复权，两边数字一样（源端对指数忽略复权参数），于是「改了调用」这件事在验证里永远看不
    出来，而个股一旦进来两边就分叉。
    """
    if code.startswith("hk"):
        return "https://web.ifzq.gtimg.cn/appstock/app/hkfqkline/get", "hfq"
    if code.startswith("us"):
        return "https://web.ifzq.gtimg.cn/appstock/app/usfqkline/get", "qfq"
    return "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get", "hfq"


def monthly(code, start, end):
    """源端的月线，复权——和应用里 TotalReturnBarsAsync 用的是同一条路径。

    两条清洗规则必须一起复刻，否则两边差一个月：
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
    """每个标的各自的累计涨幅，以及它们共用的那根月份轴。"""
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


def scrub(win, progress):
    """Puts the preview at one moment. The slider is the page's only way in, and a scrub is an
    instruction to look at a moment — the page stops playback wherever it was."""
    slider = winui.find(win, lambda c: c.AutomationId == "Scrub")

    if slider is None:
        return False

    slider.GetRangeValuePattern().SetValue(progress)
    time.sleep(1.6)

    return True


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
        "indices": int(hit.group(1)),
        "months": int(hit.group(2)),
        "top": hit.group(3),
        "top_pct": pct(hit.group(4)),
        "bottom": hit.group(5),
        "bottom_pct": pct(hit.group(6)),
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
    """把自选清空 —— 这份清单跨会话、四页共用，上一次跑脚本加的东西还在这里。"""
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
    render = open(RENDER, encoding="utf-8").read()
    series = open(SERIES, encoding="utf-8").read()

    # 这一页原来是「不调整」的，理由与 AH 页相同（调整会把一条序列重新定基）。改成复权是为了
    # 能放个股：不复权的个股曲线上有持有人没承受过的断崖（苹果十年 193% vs 1183%）。而指数
    # 不受影响 —— 源端对指数忽略复权参数，所以下面那条「十二个指数的数字没变」是真的在验它。
    check("取数走 TotalReturnBarsAsync（复权，个股才不会少算）",
          "kline.TotalReturnBarsAsync(" in source)
    check("这一页不再走空复权那条路", "kline.RawBarsAsync(" not in source)
    check("月线，一次拿全历史（不需要分页回溯）", '"month"' in source and "HistoryWalk" not in source)

    # 页面上还有一句话在说这些数字是怎么算的。脚本断的是调用，断不到那句话 —— 上一轮把调用
    # 从 RawBarsAsync 改成 TotalReturnBarsAsync、把帮助第十四章也改了，唯独漏了 resw 里这一
    # 句，于是页面在十四种语言里说着与代码相反的话，而这一页五十八条断言一条没红。**只有读
    # 那句话本身才抓得到**，所以这里读它。
    xaml = open(os.path.join(REPO, "src/MarketMotionStudio/Pages/IndexRacePage.xaml"),
                encoding="utf-8").read()
    check("页面上确实写着一句方法说明（读者看得到）", 'x:Uid="IndexRaceMethodNote"' in xaml)

    STALE = {
        "en-US": "unadjusted", "de": "nicht bereinigt", "es": "sin ajustar",
        "fr": "non ajustées", "it": "non rettificate", "pl": "bez korekty",
        "pt-BR": "sem ajuste", "cs": "bez úprav", "tr": "düzeltilmemiş",
        "ru": "без корректировки", "ja": "調整なし", "ko": "조정 없음",
        "zh-Hans": "不调整", "zh-Hant": "不調整",
    }
    stale = []

    for folder, word in STALE.items():
        resw = open(os.path.join(REPO, f"src/MarketMotionStudio/Strings/{folder}/Resources.resw"),
                    encoding="utf-8-sig").read()
        said = re.search(r'<data name="IndexRaceMethodNote\.Text"[^>]*>\s*<value>(.*?)</value>',
                         resw, re.S)

        if said is None or word in said.group(1):
            stale.append(folder)

    check("十四份资源里那句说明都不再说「不调整」", not stale, " / ".join(stale) or "-")

    english = open(os.path.join(REPO, "src/MarketMotionStudio/Strings/en-US/Resources.resw"),
                   encoding="utf-8-sig").read()
    said = re.search(r'<data name="IndexRaceMethodNote\.Text"[^>]*>\s*<value>(.*?)</value>',
                     english, re.S)
    said = said.group(1) if said else ""

    # 那一句得说清两件事，缺一件就是另一种错：改成复权了，以及随之而来的口径差别（指数行是
    # 价格回报，个股行是总回报）。只写「复权」会让读者以为已发布的数字变了。
    check("英文那句说明了是复权", "adjusted" in said and "unadjusted" not in said)
    check("英文那句写明了口径差别（价格回报 vs 总回报）",
          "price return" in said and "total return" in said)

    kline = open(os.path.join(REPO, "src/MarketMotionStudio/Market/TencentKline.cs"),
                 encoding="utf-8").read()
    check("源端丢掉还没走完的月（脚本也照此复刻）",
          "day < new DateOnly(today.Year, today.Month, 1)" in kline
          and "first_of_this_month" in open(__file__, encoding="utf-8").read())

    # 量词：页面必须自己给，渲染器不许替页面编。
    check("周期词由页面传", 'SpanWord = Strings.Get("MarketCapUnitMonths")' in page)
    check("计数词由页面传", "UnitWord = ChosenUnit()" in page)
    check("自选组的计数词换成「只个股」（指数叫个指数，个股不是）",
          'Watchlist.RosterKey ? "SectorUnitStocks" : "IndexRaceUnitIndices"' in page)
    check("渲染器没有写死这一页的量词", "IndexRaceUnitIndices" not in render)

    # ---- 0c) 源码级：自选股这一组
    check("清单里有一组是自选股", '(Watchlist.RosterKey, "SectorListStocks")' in page)
    check("自选组取的是那一份共享清单",
          "ChosenKey() is Watchlist.RosterKey ? Watch.Entries" in page)
    check("换了组就把已取的数丢掉",
          "if (!_prefs.Restoring)\n        {\n            _series = null;" in page)
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
    check("状态行格式化而非原样读", 'Strings.Format(\n                "IndexRaceFetched"' in page)

    # ---- 1) 页面在
    if not goto(win, "指数长跑"):
        check("导航里有「指数长跑」", False)
        return report()

    check("导航里有「指数长跑」", True)
    check("指数组下拉在", winui.find(win, lambda c: c.AutomationId == "ListCombo") is not None)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    note = winui.find(win, lambda c: c.AutomationId == "IndexRaceNote")

    if note is not None:
        body = " ".join(texts(note))
        check("说明卡写了「晚来的指数缺席」", "缺席" in body, body[:60])
        check("说明卡里没有字面 {0}", "{0}" not in body, body[:60])

    method = winui.find(win, lambda c: c.AutomationId == "IndexRaceMethodNote")

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

    # 五组：四个内置清单 + 读者的自选。少一组说明接线掉了，多一组说明别处也挂上了。
    check("指数组是那五组",
          set(groups) == {"全部十二个", "A股", "港股", "美股", "自选股"}, " / ".join(groups))

    # ---- 3) 近 10 年取数
    # Preferences persist, so both dials are set explicitly: a previous run leaves the page on
    # whichever group and span it last used, and a "twelve indices" assertion run against the
    # A-share group fails for no reason anyone would guess from the output.
    winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "ListCombo"), "全部十二个")

    if combo is not None:
        winui.combo_pick(win, combo, "近 10 年")

    run, status = fetch(win)
    check("近 10 年取数成功", run is not None, str(status)[:90])

    if run is None:
        return report()

    check("画了 12 个指数", run["indices"] == 12, str(run["indices"]))

    # 不是 121：源端的月线在「近十年」这段里只给 113–114 个月，见汇率走廊页那条同样的注。
    check("月份数落在十年的量级（108–125）", 108 <= run["months"] <= 125, str(run["months"]))
    check("领先的不低于垫底的", run["top_pct"] >= run["bottom_pct"],
          f"{run['top_pct']}% vs {run['bottom_pct']}%")
    check("领先与垫底是两个不同的指数", run["top"] != run["bottom"],
          f"{run['top']} / {run['bottom']}")
    check("状态行没有失败字样", not FAIL.search(run["status"]))

    shot(win, "verify-indexrace-10y.png")

    coloured = frame_pixels(win, "verify-indexrace-frame.png")

    check("画面上画出了有颜色的条形（不是空白帧）", coloured > 2000, f"{coloured} 个彩色像素")

    # ---- 4) 榜是「长出来」的：恒生科技 2020 年才有，所以第一帧比最后一帧少一行
    #
    # 这一条只能数像素：行的缺席在 UIA 树里不存在，截图里也只是"少了一条"。近十年这一档里
    # 恒生科技的头一个月在 2020-07，而画面的第一个月是 2016-10，所以开头那几十帧只有 11 行。
    early = -1

    if scrub(win, 0.06):
        early = drawn_rows(win, "verify-indexrace-early.png")

    scrub(win, 1.0)

    final = drawn_rows(win, "verify-indexrace-final.png")

    # 数出来的行数是保守的（两行的发光糊在一起就少算一行），所以最后一帧只断言「画满了」，
    # 开头那一帧的断言是「比最后一帧少」：恒生科技 2020-07 才有，近十年这一档画的是
    # 2016-10 起，所以开头那一段它还没上场。
    check("最后一帧把榜画满了（11 行以上）", final >= 11, f"{final} 行")
    check("开头那一帧比最后一帧少一行（晚来的还没上场）", 0 < early < final,
          f"{early} 行 vs 最后一帧 {final} 行")

    # ---- 5) 独立算一遍
    end = date.today()
    start = end.replace(year=end.year - 10)
    months, mine = expected(start, end)

    check("脚本自己取到了十二个指数的月线", len(mine) == 12, f"{len(mine)} 个")
    check("脚本的月份轴与页面一致（容差 1 个月）", abs(len(months) - run["months"]) <= 1,
          f"页面 {run['months']} / 脚本 {len(months)}")

    if len(mine) == 12:
        check("领先的指数与页面一致", mine[0][0] == run["top"],
              f"页面 {run['top']} / 脚本 {mine[0][0]}")
        check("垫底的指数与页面一致", mine[-1][0] == run["bottom"],
              f"页面 {run['bottom']} / 脚本 {mine[-1][0]}")
        check("领先的涨幅与页面一致（容差 0.5 个百分点）",
              abs(mine[0][1] - run["top_pct"]) <= 0.5,
              f"页面 {run['top_pct']}% / 脚本 {mine[0][1]:.2f}%")
        check("垫底的涨幅与页面一致（容差 0.5 个百分点）",
              abs(mine[-1][1] - run["bottom_pct"]) <= 0.5,
              f"页面 {run['bottom_pct']}% / 脚本 {mine[-1][1]:.2f}%")

    # ---- 5) 换一组：只剩三个
    group = winui.find(win, lambda c: c.AutomationId == "ListCombo")

    if group is not None:
        winui.combo_pick(win, group, "美股")

        other, status = fetch(win)
        check("换到美股组后取数成功", other is not None, str(status)[:90])

        if other is not None:
            check("美股组是 3 个指数", other["indices"] == 3, str(other["indices"]))

            # The leader can stay the leader — Nasdaq led the twelve and leads the three. What
            # must change is the loser: with only New York on the board, the bottom of it is not
            # the Hang Seng Tech index any more.
            check("换组后垫底变了", other["bottom"] != run["bottom"],
                  f"{run['bottom']} → {other['bottom']}")

            # 三行是这一档的全部，所以数得准：换个组，画面上的行也真的跟着少到三条。
            scrub(win, 1.0)

            three = drawn_rows(win, "verify-indexrace-us.png")

            check("美股组画面上只有 3 行", three == 3, f"{three} 行")

    # ---- 5b) 自选股：这一页也能跑一组自己的，A股 + 港股 + 美股混装
    #
    # 这一页的口径刚改过（不调整 → 复权），改的理由就是这一段：不复权的个股曲线上有持有人
    # 根本没承受过的断崖。而**十二个指数的数字必须一个都没变** —— 源端对指数忽略复权参数，
    # 上面第 5 步那条比对（脚本走复权路径重算，与页面数字对上）验的就是这件事。
    WATCH = [("sh600519", "贵州茅台"), ("sh510300", "沪深300ETF"), ("hk00700", "腾讯控股")]

    group = winui.find(win, lambda c: c.AutomationId == "ListCombo")

    if winui.combo_pick(win, group, "自选股"):
        check("清单里多了「自选股」这一组", True)
        check("选了自选股才出现搜索框",
              winui.find(win, lambda c: c.AutomationId == "Search") is not None)
        check("清空上一次跑脚本留下的自选", clear_watch(win))

        for code, name in WATCH:
            if not add_watch(win, code, name):
                check(f"加进自选：{code}", False)

        chips = watch_chips(win)

        check("三只都进了自选（跨市场：A股 + 港股）", len(chips) == len(WATCH),
              " / ".join(n for _, n in chips))

        owned, status = fetch(win)

        if owned is None:
            check("用自选股这一组取数", False, str(status)[:120])
        else:
            check("用自选股这一组取数", True)
            check("自选组报的是三只", owned["indices"] == len(WATCH), str(owned["indices"]))

            watch_months, watch_mine = expected(start, end, WATCH)

            check("自选组三只都取到了月线（港股那只也一样）", len(watch_mine) == len(WATCH),
                  "、".join(n for n, _ in watch_mine))

            if watch_mine:
                check("自选组领先的是同一只", owned["top"] == watch_mine[0][0],
                      f"页面 {owned['top']} / 脚本 {watch_mine[0][0]}")
                check("自选组领先的涨幅对得上（容差 0.5 个百分点）",
                      abs(watch_mine[0][1] - owned["top_pct"]) <= 0.5,
                      f"页面 {owned['top_pct']}% / 脚本 {watch_mine[0][1]:.2f}%")
                check("自选组的月份轴是它自己的（不是十二个指数那根）",
                      abs(len(watch_months) - owned["months"]) <= 1,
                      f"页面 {owned['months']} / 脚本 {len(watch_months)}")
    else:
        check("清单里多了「自选股」这一组", False)

    # ---- 6) 重启后还记得
    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)
    goto(win, "指数长跑")

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    remembered = winui.value(combo) if combo is not None else None

    check("重启后区间仍记着",
          remembered in ("近 3 年", "近 5 年", "近 10 年", "最长", "自定义"),
          str(remembered))

    group = winui.find(win, lambda c: c.AutomationId == "ListCombo")
    kept = winui.value(group) if group is not None else None

    # 上一节把这一页留在自选股上，所以重启后记着的应该是自选股。
    check("重启后指数组仍记着（还是「自选股」）", kept == "自选股", str(kept))

    # 共享清单跨重启还在：三只都还在，不是取数时才临时凑出来的。
    check("重启后自选那三只还在（清单存在盘上，不是内存里）",
          len(watch_chips(win)) == len(WATCH),
          " / ".join(n for _, n in watch_chips(win)))

    return report()


if __name__ == "__main__":
    sys.exit(main())
