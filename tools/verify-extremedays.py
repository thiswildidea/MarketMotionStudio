# -*- coding: utf-8 -*-
"""真机验证「极端交易日」。

这一页有三种错**只能靠脚本发现**，截图看不出来：

1. **排名按符号而不是按幅度。** 画面照样画得漂亮，只是所有的跌都会沉到所有的涨下面，
   榜单变成"涨得最好的日子"。所以第 0 段是源码级断言：页面必须传 `RankByMagnitude`，
   渲染器必须用 `Math.Abs` 排序。
2. **没发生的日子也占着榜。** 24 个候选中只有 5 个已经发生时，画面仍然有十五行，
   其中十行写着 0.00%。所以断言 `HideEmptyRows` 与渲染器里那句按日取值判空的判断。
3. **画面上的量词写死在渲染器里。** 表头那行「N 个交易日 · N 个候选日」在 UIA 树里
   没有节点，截图里只是像素——所以只能断言"量词由页面传、渲染器不许自己编"。

再者是**数字对不对**：状态行报出最大单日涨跌幅，脚本直接打源端把同一段日线独立算一遍。

用法：python tools/verify-extremedays.py
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date, timedelta

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有返回|不属于|过长|太少|failed|error")

# 24 个候选日 · 2432 个交易日 · 最大 2008-09-19 +9.45% · 榜尾 2015-07-09 −5.90%
FETCHED = re.compile(
    r"(\d+)\s*个候选日\s*·\s*(\d+)\s*个交易日\s*·\s*最大\s*(\d{4}-\d{2}-\d{2})\s*"
    r"([+−-][\d.]+)%\s*·\s*榜尾\s*(\d{4}-\d{2}-\d{2})\s*([+−-][\d.]+)%")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(REPO, "src/MarketMotionStudio/Market/ExtremeDays.cs")
PAGE = os.path.join(REPO, "src/MarketMotionStudio/Pages/ExtremeDaysPage.xaml.cs")
RENDER = os.path.join(REPO, "src/MarketMotionStudio/Render/SectorRaceRenderer.cs")

# 与页面「近 10 年」同一段区间，也用同一个端点与同一档复权。
CODE = "sh000001"
YEARS = 10

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


def daily_closes(code, start, end):
    """源端的复权日线收盘价，按应用里 HistoryWalk 的方式一页一页往回走。"""
    url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
    closes = {}
    cursor = end
    earliest_seen = end

    for _ in range(20):
        if cursor < start:
            break

        param = f"{code},day,{start},{cursor},640,hfq"
        raw = urllib.request.urlopen(
            urllib.request.Request(f"{url}?param={param}", headers={"User-Agent": "Mozilla/5.0"}),
            timeout=30).read().decode("utf-8", "ignore")

        node = json.loads(raw).get("data", {}).get(code, {})

        # **同一个端点，指数与个股给的键名不同**：指数是 `day`，个股和基金是 `hfqday`
        # （不复权的 `day` 只在指数那一侧出现）。只认 `day` 的话，个股这一路取到的是一张
        # 空表 —— 脚本于是一行也没算，而应用那一侧照常取数、照常给出一版漂亮的榜，
        # 两条线各说各话，谁也不报错。
        rows = None

        for key in ("hfqday", "qfqday", "day"):
            value = node.get(key)

            if isinstance(value, list) and value and isinstance(value[0], list):
                rows = value
                break

        if not rows:
            break

        for row in rows:
            close = float(row[2])

            # **源端的 K 线忽略 start** —— 它只认 count，往回给满一页。所以裁剪是客户端
            # 的事，应用那边做，脚本这边也得做：少这一步，个股三年会取到 1280 天（多出来的
            # 是 start 之前那一段），而多出来的那一段里最大的一天不是这三年里最大的一天。
            if close > 0 and start <= row[0] <= end:
                closes[row[0]] = close

        earliest = rows[0][0]

        if earliest >= earliest_seen or earliest <= start:
            break

        earliest_seen = earliest
        cursor = (date.fromisoformat(earliest) - timedelta(days=1)).isoformat()

    return dict(sorted(closes.items()))


def expected_board(closes, field=24, board=15):
    """独立的「最大单日涨跌幅」榜：返回（榜首幅度, 榜尾幅度, 交易日数）。"""
    days = list(closes)
    moves = {days[i]: (closes[days[i]] / closes[days[i - 1]] - 1) * 100
             for i in range(1, len(days)) if closes[days[i - 1]] > 0}

    ranked = sorted(moves.items(), key=lambda kv: (-abs(kv[1]), kv[0]))[:field]

    return {
        "days": len(days),
        "top": ranked[0][1],
        "bottom": ranked[min(board, len(ranked)) - 1][1],
    }


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

    def number(text):
        return float(text.replace("−", "-").replace("+", ""))

    return {
        "field": int(hit.group(1)),
        "days": int(hit.group(2)),
        "top_day": hit.group(3),
        "top": number(hit.group(4)),
        "bottom_day": hit.group(5),
        "bottom": number(hit.group(6)),
        "status": status,
    }, status


def search_text(win):
    box = winui.find(win, lambda c: c.AutomationId == "InstrumentSearch")
    edit = None if box is None else winui.find(box, lambda c: c.AutomationId == "TextBox", limit=6)

    if edit is None:
        return None

    try:
        return edit.GetValuePattern().Value.strip()
    except Exception:  # noqa: BLE001
        return ""


def pick_instrument(win, code):
    """把搜索框填成这只代码并提交。

    代码走剪贴板而不是按键：中文打不进 AutoSuggestBox，虽然代码只有数字，两条路用同一条
    比记着哪条需要哪条便宜。回车提交而不是点建议 —— 裸代码自己就能解析，而建议弹层是另一个
    顶层窗口。
    """
    box = winui.find(win, lambda c: c.AutomationId == "InstrumentSearch")
    edit = None if box is None else winui.find(box, lambda c: c.AutomationId == "TextBox", limit=6)

    if edit is None:
        return False

    edit.SetFocus()
    time.sleep(0.3)
    edit.SendKeys("{Ctrl}a", waitTime=0.3)
    auto.SetClipboardText(code)
    edit.SendKeys("{Ctrl}v", waitTime=0.5)

    deadline = time.time() + 5

    while time.time() < deadline:
        if search_text(win) == code:
            break

        time.sleep(0.3)

    edit.SendKeys("{Enter}", waitTime=0.5)
    time.sleep(2.0)

    return True


def frame_colours(win):
    """数预览画面里的红/绿像素 —— 用的还是截图，所以和用户看到的是同一张图。"""
    try:
        from PIL import Image
    except ImportError:
        return -1, -1

    # Cropped by proportion rather than by the control's rectangle: `PreviewSurface` has no
    # automation node of its own (a canvas), so the frame is found the way the other colour checks
    # in this project find things in a screenshot — take the region it must be in, and take the
    # fraction of it. Left 62% and above the play bar, which excludes the status bar's own green
    # tick (a darker green than a bar, and dark enough not to pass the test below anyway).
    path = os.path.join(REPO, "artifacts", "verify-extremedays-frame-crop.png")

    try:
        win.SetTopmost(True)
        time.sleep(0.5)
    except Exception:  # noqa: BLE001
        pass

    win.CaptureToImage(path)

    try:
        win.SetTopmost(False)
    except Exception:  # noqa: BLE001
        pass

    whole = Image.open(path).convert("RGB")
    width, height = whole.size

    image = whole.crop((0, int(height * 0.10), int(width * 0.62), int(height * 0.92)))

    red = green = 0
    pixels = image.load()

    for y in range(image.size[1]):
        for x in range(image.size[0]):
            r, g, b = pixels[x, y]

            if r > 180 and g < 110 and b < 110:
                red += 1
            elif g > 150 and r < 110 and b < 130:
                green += 1

    return red, green


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

    # ---- 0) 源码级：这三条在 UIA 里不存在，截图里也看不出来
    source = open(SOURCE, encoding="utf-8").read()
    page = open(PAGE, encoding="utf-8").read()
    render = open(RENDER, encoding="utf-8").read()

    check("数据层走 HistoryWalk（复权日线，分页回溯）", "HistoryWalk.ClosesAsync" in source)

    check("涨跌幅按上一交易日的复权收盘价算",
          "closes[dates[i]] / before) - 1" in source)

    # **构造参数，不是属性。** 排名表在渲染器的构造函数里就建好了，对象初始化器跑在它之后——
    # 写成属性时这句被读成默认的 false，画面于是按符号排序：八根最大的涨、七根最小的跌，
    # 是一张看着完全合理的错榜。断言断在构造参数上，才拦得住。
    check("页面把「按幅度排名」当构造参数传", "rankByMagnitude: true" in page)
    check("页面没有把它写成属性（写成属性会被读得太晚）",
          "RankByMagnitude = true" not in page)
    check("渲染器的排名用绝对值", "? Math.Abs(value) : value;" in render)
    check("渲染器把它存成只读字段（构造时读一次）",
          "private readonly bool _rankByMagnitude;" in render)

    check("页面要求隐藏尚未发生的日", "HideEmptyRows = true" in page)
    check("渲染器按当天的值判空（不是按插值后的值）",
          "HideEmptyRows && raw[k][state.DayIndex] == 0" in render)

    check("页面要求按涨跌着色", "ColourBySign = true" in page)
    check("渲染器的涨是红、跌是绿",
          "Rgb(0xEF, 0x44, 0x44)" in render and "Rgb(0x22, 0xC5, 0x5E)" in render)

    # 量词：页面必须自己给，渲染器不许替页面编。市值榜就是这样错的（月线画成「12 个交易日」）。
    check("周期词由页面传", 'SpanWord = Strings.Get("StockTradingDaysUnit")' in page)
    check("计数词由页面传", 'UnitWord = Strings.Get("ExtremeDaysUnitCandidates")' in page)
    check("渲染器没有写死某个具体周期的量词",
          "MarketCapUnitMonths" not in render and "AhPremiumUnitPairs" not in render)

    # ---- 0b) 源码级：任意标的（个股 / ETF）也得能上这一页
    #
    # 数据层本来就接任何 RaceEntry，所以放开的是页面。页面曾经从下拉读当前标的，那样搜索
    # 出来的东西无处可放 —— 断言断在「当前标的由字段持有」上，才拦得住退回旧写法。
    check("页面有搜索框（不是只有那一份固定清单）", "OnSearchSubmitted" in page)
    check("当前标的由字段持有，不是从下拉读回来的",
          "private RaceEntry ChosenInstrument() => new(_instrumentCode, _instrumentName);" in page)
    check("从建议里选中会设置当前标的", "ChooseInstrument(pick.Code, pick.Name);" in page)
    check("手输代码也会设置当前标的", "ChooseInstrument(code, code);" in page)
    check("搜索结果按当前市场过滤", "_market.Accepts(r.Code)" in page)
    check("手输代码先过规范化再判市场", "StockDirectory.Normalize(sender.Text)" in page)
    check("偏好多记一个名字（只有代码的话画面会用代码当标题）",
          '_prefs.Save("Name", _instrumentName);' in page)
    check("换市场时不把别处的代码带过来", "if (_market.Accepts(code))" in page)

    # ---- 1) 页面在
    if not goto(win, "极端交易日"):
        check("导航里有「极端交易日」", False)
        return report()

    check("导航里有「极端交易日」", True)

    # **先复位，再断言。** 标的偏好是持久的：上一次跑脚本时选的东西会留在这里，脚本若
    # 默认页面还在上证指数上，第一次取数就会拿别人的数跟上证的数比，然后报「不一致」——
    # 而这一页此时接了搜索框，上次留下的很可能是一只根本不在清单里的 ETF。
    winui.combo_pick(win, winui.find(win, lambda c: c.AutomationId == "InstrumentCombo"), "上证指数")

    check("标的下拉在", winui.find(win, lambda c: c.AutomationId == "InstrumentCombo") is not None)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)

    card = winui.find(win, lambda c: c.AutomationId == "ListText")

    if card is not None:
        body = " ".join(texts(card))
        check("卡片说明了画面画几天", "15" in body, body[:70])
        check("卡片里的 {0} 已被替换（没有字面占位符）", "{0}" not in body, body[:70])

    note = winui.find(win, lambda c: c.AutomationId == "ExtremeDaysMethodNote")

    if note is not None:
        body = " ".join(texts(note))
        check("口径说明写了复权与按幅度排序", "复权" in body and "幅度" in body, body[:60])

    # ---- 2) 档位
    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    options = winui.combo_labels(win, combo) if combo is not None else []

    check("区间下拉是那五档",
          set(options) == {"近 3 年", "近 5 年", "近 10 年", "最长（约 35 年）", "自定义"},
          " / ".join(options))

    instruments = winui.combo_labels(win, winui.find(win, lambda c: c.AutomationId == "InstrumentCombo"))
    check("标的下拉是宽基指数（至少 5 个）", len(instruments) >= 5, " / ".join(instruments[:8]))

    # ---- 3) 近 10 年取数
    if combo is not None:
        winui.combo_pick(win, combo, "近 10 年")

    run, status = fetch(win)
    check("近 10 年取数成功", run is not None, str(status)[:90])

    if run is None:
        return report()

    check("候选日是 24 天（画面画其中 15 天）", run["field"] == 24, str(run["field"]))
    check("交易日数落在十年的量级（2200–2600）", 2200 <= run["days"] <= 2600, str(run["days"]))
    check("榜首幅度大于榜尾幅度", abs(run["top"]) > abs(run["bottom"]),
          f"{run['top']:+.2f}% vs {run['bottom']:+.2f}%")
    check("榜首是个像样的单日波动（>3%）", abs(run["top"]) > 3.0, f"{run['top']:+.2f}%")
    check("榜首与榜尾都是日期", bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", run["top_day"])), run["top_day"])
    check("状态行没有失败字样", not FAIL.search(run["status"]))

    shot(win, "verify-extremedays-10y.png")

    # **画面上的红绿像素。** 这是唯一能抓住「排序按符号」那个 bug 的检查：状态行的数字由页面
    # 自己按幅度算，所以它一直是对的，错的是渲染器画出来的那张榜。上证指数近十年最大的波动里
    # 第 2、3、4 名都是暴跌，按幅度排画面必然同时有红条和绿条；按符号排则只有红条。
    red, green = frame_colours(win)

    check("画面里同时有涨（红）与跌（绿）", red > 200 and green > 200, f"红 {red} / 绿 {green}")

    # ---- 4) 独立算一遍
    end = date.today()
    start = end.replace(year=end.year - YEARS)
    closes = daily_closes(CODE, start.isoformat(), end.isoformat())
    mine = expected_board(closes)

    check("脚本自己取到了同一段日线", len(closes) > 2000, f"{len(closes)} 天")

    check("最大单日涨跌幅与页面一致（容差 0.06 个百分点）",
          abs(abs(mine["top"]) - abs(run["top"])) < 0.06,
          f"页面 {run['top']:+.2f}% / 脚本 {mine['top']:+.2f}%")

    check("榜尾幅度与页面一致（容差 0.06 个百分点）",
          abs(abs(mine["bottom"]) - abs(run["bottom"])) < 0.06,
          f"页面 {run['bottom']:+.2f}% / 脚本 {mine['bottom']:+.2f}%")

    # ---- 5) 换一个标的：数字必须变
    instrument = winui.find(win, lambda c: c.AutomationId == "InstrumentCombo")

    if instrument is not None and len(instruments) >= 2:
        winui.combo_pick(win, instrument, instruments[1])

        other, status = fetch(win)
        check("换标的后取数成功", other is not None, str(status)[:90])

        if other is not None:
            check("换标的后榜首不再是同一个数",
                  abs(abs(other["top"]) - abs(run["top"])) > 1e-9,
                  f"{run['top']:+.2f}% → {other['top']:+.2f}%")

            shot(win, "verify-extremedays-other.png")

    # ---- 6) 任意标的：一只个股和一只 ETF，各自独立算一遍
    #
    # 这一页的标的曾经只能是下拉里那八只宽基指数。搜索框接上之后要证明的不是「框在」——
    # 框在是可以断言的，而**数字是这只个股自己的**只能靠脚本另算一遍：把下拉换成默认标的
    # 再取数也会成功，也会给一版漂亮的榜。
    check("页面上有搜索框", winui.find(win, lambda c: c.AutomationId == "InstrumentSearch") is not None)

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")

    if combo is not None:
        winui.combo_pick(win, combo, "近 3 年")

    short_end = date.today()
    short_start = short_end.replace(year=short_end.year - 3)

    # 贵州茅台：一只个股，涨停板日会进榜；沪深300ETF：一只基金。两只都不在那份指数清单里。
    etf = None

    for label, code in (("个股", "sh600519"), ("ETF", "sh510300")):
        if not pick_instrument(win, code):
            check(f"{label} {code} 能填进搜索框", False)
            continue

        check(f"{label} {code} 能填进搜索框", True)

        empty = winui.value(winui.find(win, lambda c: c.AutomationId == "InstrumentCombo"))
        check(f"{label}不在预设清单里时下拉不再指着别的东西", empty in (None, ""), str(empty))

        run2, status = fetch(win)
        check(f"{label} {code} 取数成功", run2 is not None, str(status)[:90])

        if run2 is None:
            continue

        etf = run2
        theirs = expected_board(daily_closes(code, short_start.isoformat(), short_end.isoformat()))

        check(f"{label}的交易日数与脚本一致（容差 5 天）",
              abs(theirs["days"] - run2["days"]) <= 5,
              f"页面 {run2['days']} / 脚本 {theirs['days']}")

        check(f"{label}的最大单日波动与脚本独立算的一致（容差 0.06 个百分点）",
              abs(abs(theirs["top"]) - abs(run2["top"])) < 0.06,
              f"页面 {run2['top']:+.2f}% / 脚本 {theirs['top']:+.2f}%")

        shot(win, f"verify-extremedays-{code}.png")

    # ---- 7) 重启后还记得
    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)
    goto(win, "极端交易日")

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    remembered = winui.value(combo) if combo is not None else None

    check("重启后区间仍记着",
          remembered in ("近 3 年", "近 5 年", "近 10 年", "最长（约 35 年）", "自定义"),
          str(remembered))

    instrument = winui.find(win, lambda c: c.AutomationId == "InstrumentCombo")
    kept = winui.value(instrument) if instrument is not None else None

    # 记住的是搜索出来的那只 ETF，不是清单里的某一项。搜索框是空的（它是个输入框，不是
    # 当前状态的显示器），画布上的标题才写着名字，而画布没有 UIA 节点 —— 所以只能用
    # 「再取一次数，数字还是那只 ETF 的数字」来证明。
    check("重启后下拉仍然是空的（那只 ETF 不在清单里）", kept in (None, ""), str(kept))

    if etf is not None:
        again, status = fetch(win)

        check("重启后取数成功", again is not None, str(status)[:90])

        if again is not None:
            check("重启后仍记着搜索出来的那只 ETF（天数与榜首都对得上）",
                  again["days"] == etf["days"] and abs(again["top"] - etf["top"]) < 1e-6,
                  f"{etf['days']} 天 / {etf['top']:+.2f}% → {again['days']} 天 / {again['top']:+.2f}%")

    return report()


if __name__ == "__main__":
    sys.exit(main())
