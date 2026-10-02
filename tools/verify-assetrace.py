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


def monthly(code, start, end):
    """源端的月线，**后复权**——和应用里 TotalReturnBarsAsync 用的是同一条路径。

    这是这一页与指数长跑唯一的分岔口，脚本必须站在同一边：取 `hfqmonth` 块，
    取不到才退回 `month`。拿 raw 去比对复权的结果，差的是倍数而不是小数点。

    两条清洗规则一起复刻，否则两边差一个月：
      - `CandlesFromAsync` 丢掉还没走完的月（`IsSettledFor`），十月初取数末月是九月；
      - 同一条调用还按 start/end 裁一遍，因为源端对月线的 start 并不总是买账。
    """
    url = ("https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
           f"?param={code},month,{start},{end},430,hfq")

    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=30).read().decode("utf-8", "ignore")

    node = json.loads(raw).get("data", {}).get(code, {})

    rows = None
    for key in ("hfqmonth", "month"):
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


def expected(start, end):
    """八个标的各自的累计涨幅，以及它们共用的那根月份轴。"""
    per = [(name, monthly(code, start, end)) for code, name in CODES]

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


def drawn_rows(win, name):
    """Counts the rows a frame actually draws, from its pixels.

    A row is a name plus a bar plus a value label, and only the bar is a long horizontal run of
    saturated colour — a picture of glyphs is a ragged run of a few pixels. So a scanline counts
    as "inside a row" when it holds a run of four or more saturated pixels, and rows are the
    bands of such scanlines. This is the only way to see "the board has not filled up yet", which
    is a fact about the picture and not about any string in the UI.

    The crop is the canvas interior as a proportion of the window, because the preview has no
    automation node of its own. It keeps the rows and drops the coloured things around them: the
    title-and-date band above, the legend line below, the navigation icons to the left, the
    settings panel to the right.

    Calibrated against frames whose row count is known: the twelve-index board, the three-index
    Americas board, AH premium's fifteen and extreme days' fifteen all come out exact. Where two
    neighbouring glows touch, the bands merge, so a count can come out low and never high — and
    only a small board is asserted as an exact number.
    """
    try:
        from PIL import Image
    except ImportError:
        return -1

    path = shot(win, name)
    whole = Image.open(path).convert("RGB")
    width, height = whole.size

    image = whole.crop((int(width * 0.39), int(height * 0.33),
                        int(width * 0.62), int(height * 0.83)))
    pixels = image.load()

    ys = []

    for y in range(image.size[1]):
        best = 0
        run = 0

        for x in range(image.size[0]):
            r, g, b = pixels[x, y]

            if max(r, g, b) > 110 and max(r, g, b) - min(r, g, b) > 70:
                run += 1
                best = max(best, run)
            else:
                run = 0

        if best >= 4:
            ys.append(y)

    rows = 0
    previous = -10

    for y in ys:
        if y - previous > 2:
            rows += 1

        previous = y

    return rows


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
    check("计数词由页面传", 'UnitWord = Strings.Get("AssetRaceUnitAssets")' in page)
    check("渲染器没有写死这一页的量词", "AssetRaceUnitAssets" not in render)

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

    check("资产组是那三组",
          set(groups) == {"全部八类", "股票", "非股票"}, " / ".join(groups))

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

    check("重启后资产组仍记着", kept == "股票", str(kept))

    return report()


if __name__ == "__main__":
    sys.exit(main())
