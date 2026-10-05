# -*- coding: utf-8 -*-
"""真机验证「持仓收益」的多标的对比与曲线末端标签。

这一页原来只有一只标的：搜索框填一个代码，画面上一条曲线、一个本金线、一个收益率。
现在它是**一份清单上的若干只**——清单就是八个榜单共用的那份自选，chip 逐个决定哪几只
上这一帧（这一页的 chip 是开关，别的榜是「点一下就删掉」，所以是两个按钮而不是一个）。

三件事只能这样验：

1. **画面上的钱对不对。** 大数字和每个胶囊里的金额都画在画布上，画布在 UIA 树里没有
   节点，字读不出来。所以脚本自己打源端按同一条路（`newfqkline` + `hfq`，与
   `HistoryWalk.ClosesAsync` 同一张路由表）把三只的收盘价拉下来、自己算一遍市值，然后
   拿**几何**去比：每只的收益 = 末值 − 本金，而画面上白点离本金线多远正比于这个数。
   三个两两斜率（白点一律画在线上方 4 基线像素，那是一个常数偏移，两两一比就没了）必须
   一致 —— 一致才说明每只的价格序列、本金、买入日都对上了，而不只是「画了三条线」。

2. **标签确实跟着曲线走、一条都不少，而且骑在线头右边。** 判据是像素：胶囊的上下边是
   **同一颜色一段很长的水平连续像素**（量到 64～74），而曲线本身是斜的，一行里最多 7 个
   像素（差一个数量级）。末端白点给曲线条数：每只一个，画在**自己那条线**的末端，判据是
   「白点挨着一条曲线」—— 标题、大数字、坐标数字都是近白的，但它们旁边没有彩色曲线。
   白点同时给胶囊的**位置**基准：胶囊的左缘在白点右边、右缘还在画面里，两条都量。

3. **不能按绝对 RGB 认颜色。** 曲线只有一个多像素宽，抗锯齿把它冲淡到七成：令牌紫
   (168,85,247) 落成 (126,66,187)，离调色板比容差还远。临时探针就是这么把紫色的胶囊量成
   「没有」的，而画面上那条紫线好好地画着。所以按**色相 + 饱和度**认：底色近黑、文字近
   灰，饱和度低，一并滤掉；色相不受冲淡影响。

4. **两种推进方式（整段铺满 / 窗口滚动）**的差别也全落在像素上，而且正好是**头部的位置**：
   同一个进度（0.5）下，整段铺满的曲线头跟着进度走到中段，窗口滚动的头贴着右缘 —— 窗口的
   右端就是它。两帧用同一个进度比，所以不依赖任何绝对坐标。头部就是白点（见 `end_dots`），
   但要取 **x 最大**的那一个，不能拿 `[-1]`：白点是按 y 排的，最后那个是画面最下面那只。

画面的裁框也不是白拿的：`winui.canvas_box` 的下缘偏低几十像素（预览下面那一排控件也是
深色，走列的那次遍历跨过了它们），要拿 `winui.frame_bottom` 重算 —— 算准了才能断言画面
是 9:16，而量出来是 0.5622。

只有**这几只**参与像素量测，也是选过的：A股那七只预设里有四只挤在 1.22～1.28 百万之间，
轴上一共三个像素，两个末端白点会叠成一个 —— 画面完全正确，而「几个白点」要按观测到的每
像素多少元算出来，不能写死。见 `六只都有胶囊标签` 那一段。

另有三处只能靠源码断言：`MostTracks = 6` 的拒绝分支（少画一只的画面看起来完全正常）、
跨市场标的的过滤（清单是三地混装的，而这一页的金额是本市场的钱）、以及这一页的标的
不进偏好而是进那份共享清单。

用法：python tools/verify-position.py
"""
import colorsys
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

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src/MarketMotionStudio")

SERIES = os.path.join(SRC, "Market/PositionSeries.cs")
RENDERER = os.path.join(SRC, "Render/PositionRenderer.cs")
PAGE = os.path.join(SRC, "Pages/PositionPage.xaml.cs")
XAML = os.path.join(SRC, "Pages/PositionPage.xaml")
PALETTE = os.path.join(SRC, "Render/Palette.cs")
PICKER = os.path.join(SRC, "Views/WatchlistPicker.xaml.cs")
PICKER_XAML = os.path.join(SRC, "Views/WatchlistPicker.xaml")
STORE = os.path.join(SRC, "Pages/Watchlist.cs")

FAIL = re.compile(r"失败|错误|无法|不可用|异常|没有返回|不属于|过长|太少|failed|error")

# 「已取 726 个交易日（2023-10-09 至 2026-09-30），持有 1087 天」
# 或「已取 3 只标的 · 726 个交易日（2023-10-09 至 2026-09-30）」
FETCHED = re.compile(r"已取\s*(?:(\d+)\s*只标的\s*·\s*)?(\d+)\s*个交易日（(\S+?)\s*至\s*(\S+?)）")

# 「最多同时对比 6 只，现在勾了 7 只」
TOO_MANY = re.compile(r"最多同时对比\s*(\d+)\s*只，现在勾了\s*(\d+)\s*只")

# 市场里的那份预设（A股），与 Markets.AShareHoldings 同序。前三只就是脚本要对比的三只，
# 后四只是拿来撞六只上限的。
PRESETS = [
    ("sh601318", "中国平安"),
    ("sh600519", "贵州茅台"),
    ("sh600036", "招商银行"),
    ("sh600900", "长江电力"),
    ("sz000858", "五粮液"),
    ("sh510300", "沪深300ETF"),
    ("sh000001", "上证指数"),
]

# Palette.Tracks，六条。颜色按**位置**取，不按代码哈希。
TRACKS = [
    (0xFF, 0x6B, 0x6B), (0x06, 0xB6, 0xD4), (0xA8, 0x55, 0xF7),
    (0x22, 0xC5, 0x5E), (0x3B, 0x82, 0xF6), (0xEC, 0x48, 0x99),
]

# Palette.Moving：本金线，全部曲线底下那一根。特意不在 Tracks 里。
CAPITAL = (0xFB, 0xBF, 0x24)

# 画面上出现的**全部**颜色，一个像素归给其中最近的那个（见 `painted`）。名字不叫
# `PALETTE` —— 那个名字上面已经给了 `Render/Palette.cs` 的路径，撞上去会让 `source()`
# 拿一张颜色表去 `open()`。
PALETTE_RGB = TRACKS + [CAPITAL]

CAPITAL_AMOUNT = 1_000_000

# 跨市场用的那一只：这一页只认本市场的钱，清单却八个榜共用、三地混装。
FOREIGN = ("hk00700", "腾讯控股")

SHOTS = ("verify-position-one.png", "verify-position-two.png", "verify-position-three.png",
         "verify-position-six.png", "verify-position-early.png", "verify-position-late.png",
         "verify-position-limit.png", "verify-position-filtered.png",
         "verify-position-grow.png", "verify-position-scroll.png")

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


def add_months(day, months):
    """`DateOnly.AddMonths` 的口径：落在目标月里，不是溢出到下个月。"""
    total = (day.year * 12) + (day.month - 1) + months
    year, month = divmod(total, 12)
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    last = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]

    return date(year, month + 1, min(day.day, last))


def bars(code, cursor, count=640):
    """`TencentKline.StockBarsAsync` 的那一次请求：通用端点、后复权、按 end 往回数。"""
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/newfqkline/get"
           f"?param={code},day,,{cursor},{count},hfq")

    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
        timeout=40).read().decode("utf-8", "ignore")

    node = json.loads(raw).get("data", {}).get(code, {})

    # 同一个端点对指数返 `day`、对个股与基金返 `hfqday` —— 只认一个键会得到一张空表，
    # 而脚本会把它读成「这只在区间里没有数据」。
    rows = node.get("hfqday") or node.get("day") or []

    return {date.fromisoformat(r[0]): float(r[2]) for r in rows if float(r[2]) > 0}


def closes(code, start, end):
    """`HistoryWalk.ClosesAsync` 的复刻：一次 640 根，按最早那根往回挪，直到越过 start。"""
    out = {}
    cursor = end
    seen = end

    for _ in range(6):
        if cursor < start:
            break

        page = bars(code, cursor)

        if not page:
            break

        for day, close in page.items():
            if start <= day <= end:
                out[day] = close

        earliest = min(page)

        if earliest >= seen or earliest <= start:
            break

        seen = earliest
        cursor = earliest - timedelta(days=1)

    return out


def expected(start, end, picks):
    """一份持仓板：日期轴取并集，每只按自己的首个交易日买入同一笔本金。"""
    walks = {code: closes(code, start, end) for code, _ in picks}

    union = sorted(set().union(*walks.values()))
    tracks = []

    for code, name in picks:
        days = sorted(walks[code])

        if len(days) < 2:
            continue

        shares = CAPITAL_AMOUNT / walks[code][days[0]]
        held = shares * walks[code][days[0]]
        peak = held
        worst = 0.0

        for day in days:
            held = shares * walks[code][day]
            peak = max(peak, held)
            worst = max(worst, (1 - held / peak) * 100 if peak > 0 else 0)

        value = shares * walks[code][days[-1]]

        tracks.append({
            "code": code,
            "name": name,
            "first": days[0],
            "last": days[-1],
            "value": value,
            "profit": value - CAPITAL_AMOUNT,
            "return": (value / CAPITAL_AMOUNT - 1) * 100,
            "drawdown": worst,
        })

    return union, tracks


# ---- 像素 ----------------------------------------------------------------------------

def hue_of(rgb):
    h, _, _ = colorsys.rgb_to_hsv(*[v / 255 for v in rgb])

    return h * 360


def hsv_rows(img, box):
    """画布每个像素的 (色相, 饱和度, 明度)。只算一遍：七种颜色各扫一次太慢。"""
    pixels = img.load()
    rows = []

    for y in range(box[2], box[3] + 1):
        row = []

        for x in range(box[0], box[1] + 1):
            r, g, b = pixels[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            row.append((h * 360, s, v))

        rows.append(row)

    return rows


def painted(rows, box, rgb, window=20, saturation=0.45, value=0.35, palette=None):
    """画布上属于这个颜色的像素。

    **按色相认，不按绝对 RGB。** 曲线只有一个多像素宽，抗锯齿把它冲淡到七成：令牌紫
    (168,85,247) 落成 (126,66,187)，离调色板比容差还远。临时探针按 RGB 量，把紫色的胶囊
    判成「没有」，而画面上那条紫线好好地画着。

    饱和度与明度是门槛，不是颜色的一部分：底色近黑、坐标与说明文字近灰，两者都过不去，
    于是「画面上有没有紫色」不需要先知道背景是什么样。

    **但一个像素只归给它最近的那个颜色。** 色相是抗锯齿唯一守得住的东西（与黑混合不变色
    相），可惜它在这里太粗：调色板里红(0°)与粉(330.4°)只差 30°，而窗口是 ±20° —— 两者在
    340°~350° 上重叠。曲线画在**深蓝**底上，边缘像素被底色拖走十来度，于是红色胶囊的下边
    整行落进粉色的窗口：「六份都有末端胶囊」报出「第 6 条有 2 颗」，画面上明明只有一颗。
    实测那一行 (226,96,99)、色相 349° —— 离红 11°、离粉 19°。谁近就是谁的，重叠带里不再
    两头都认领（青 187° 与蓝 217° 是同一对毛病）。

    `palette` 传全表（`TRACKS` + `CAPITAL`），不传就只有窗口这一条判据（老行为）。
    """
    target = hue_of(rgb)

    def away(h, other):
        return min((h - other) % 360, (other - h) % 360)

    others = [hue_of(c) for c in (palette or []) if away(hue_of(c), target) > 0]

    left, top = box[0], box[2]
    out = set()

    for j, row in enumerate(rows):
        for i, (h, s, v) in enumerate(row):
            if s < saturation or v < value:
                continue

            mine = away(h, target)

            if mine > window:
                continue

            if others and min(away(h, other) for other in others) <= mine:
                continue

            out.add((left + i, top + j))

    return out


def best_run(points, y):
    """某一行里这些像素的最长连续段，以及那一段的左端。"""
    xs = sorted(x for (x, yy) in points if yy == y)

    if not xs:
        return 0, None

    longest = run = 1
    start = xs[0]

    for i in range(1, len(xs)):
        if xs[i] == xs[i - 1] + 1:
            run += 1

            if run > longest:
                longest, start = run, xs[i] - run + 1
        else:
            run = 1

    return longest, start


def widest(points, y0, y1):
    """一段行范围里最长的同色水平连续段，以及那一段所在的行。"""
    best, at = 0, None

    for y in range(y0, y1 + 1):
        longest, _ = best_run(points, y)

        if longest > best:
            best, at = longest, y

    return best, at


def blocks(points):
    """连通块，按大小倒序。"""
    remaining = set(points)
    out = []

    while remaining:
        seed = remaining.pop()
        stack = [seed]
        comp = [seed]

        while stack:
            x, y = stack.pop()

            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy) in remaining:
                        remaining.discard((x + dx, y + dy))
                        stack.append((x + dx, y + dy))
                        comp.append((x + dx, y + dy))

        out.append(comp)

    return sorted(out, key=len, reverse=True)


def blobs(rows, box, hit, lo=4, hi=200, span=13):
    """画面上符合条件的**小**连通块，返回 (重心 x, 重心 y, 像素数)。

    只收小的：曲线末端的白点是 `Px(6)` 的圆，落在屏幕上四五个像素见方；标题的笔画、大
    数字、卡片里的金额都比它大，而且形状是横的或竖的。
    """
    left, top = box[0], box[2]
    pts = set()

    for j, row in enumerate(rows):
        for i, (h, s, v) in enumerate(row):
            if hit(h, s, v):
                pts.add((left + i, top + j))

    out = []

    for comp in blocks(pts):
        if not (lo <= len(comp) <= hi):
            continue

        xs = [p[0] for p in comp]
        ys = [p[1] for p in comp]

        if max(xs) - min(xs) > span or max(ys) - min(ys) > span:
            continue

        out.append((sum(xs) / len(xs), sum(ys) / len(ys), len(comp)))

    return out


def end_dots(frame, point_sets):
    """每条曲线末端的白点，按 y 从小到大。

    判据只有一条：**band（绘图区）里的一个近白块，且挨着这条线自己的像素。** 三条理由：

    * **为什么限定在 band 里。** 近白的东西满画面都是：标题、中间那个大数字、收尾卡片里的
      字。实测单只那一帧 15 个近白块里 14 个在 band 之外（标题在 y≈265、卡片在 y≈723，而
      band 是画面的 45%～74%），band 之内只剩曲线末端那个圆点。这个界与 `measure` 算横排时
      用的是同一个，两处必须一致。
    * **为什么必须「挨着这条线自己」。** 两条线的末端在同一个最后交易日上，也就是**同一列**；
      只按位置挑，两条线会挑中同一个白点，去重以后只剩一个 —— 「两只就是两个白点」从 2 掉到
      1，紧接着 `ends` 里有一只取不到 y，`<` 比 `None` 直接把脚本崩在半路。而「挨着这条线
      自己」认不错：末端的点离自己的末端两三个像素，离别的线的末端十几像素。
    * **为什么不能是「离这条颜色最右那一列最近」。** 那正是这条判据原来的样子，而它对**胶囊**
      ——一个与曲线同色的东西——是敏感的。胶囊锚在曲线头**左边**时，最右那一列天然就是线头，
      一切正常；这一轮把它挪到了线头**右边**，最右的一列成了胶囊的右端，真正的白点离它有
      十几像素、一个也命中不了。单只那只于是量出「0 个白点」、脚本崩在半路，而画面完全正常。

      想把胶囊从同色的曲线里摘出去是走不通的：它的左端离线头只有一个 `Px(LabelGap)`，而且
      它自己会被拆成好几块互不相邻的连通块（边框一圈、里面每个字一块 —— 实测单只那一帧是
      184 / 70 / 17 / 14 / 9 像素的五块）。所以判据不再提「哪一端是最右」：少一个前提，就少
      一种会被布局改动弄坏的方式。

      （更早的版本还用过「在画布右半边」，那条在整段铺满走到一半时会把点整个滤掉 —— 头部
      正好压在中线上。两次都是同一个毛病：拿画面上的一个**位置**去认一个**东西**。）

    也不能按「离这条线末端的高度最近」挑：末端的高度要从这条线最右那一列的像素里读，而那一列
    上不只有末端 —— 胶囊和收尾卡片那圈同色的边框也压在同一列上（实测第三只：末端在 y=514–515，
    边框在 y=697–740），取中位数就被拽到 715，于是它去挑离 715 最近的点，挑中的是**第二条**的点。

    一条曲线出一个点；两条末端完全叠在一起的算一个（同一个连通块，去重）。
    """
    if not point_sets or not any(point_sets):
        return []

    # 所有曲线颜色合起来那一份，只给最后那条兜底判据用。
    any_line = set().union(*point_sets)

    top, bottom = frame.box[2], frame.box[3]
    height = bottom - top
    band = (top + (height * 45 // 100), top + (height * 74 // 100))

    def gap(dot, pts, reach=6):
        """这个近白块离这堆像素有多远（切比雪夫距离），超出 `reach` 一律算 `reach + 1`。

        从 0 开始一圈圈往外找，所以返回的就是**最小**的那一圈 —— 而且比「整个集合扫一遍取
        最近」便宜得多（集合只有几百个点，但这一步每帧每只都要做）。
        """
        x, y = dot[0], dot[1]

        for r in range(0, reach + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if (x + dx, y + dy) in pts:
                        return r

        return reach + 1

    # 下限放到 2：白点是 `Px(6)` 的圆，屏幕上四五个像素见方，而发光让边缘变淡，真正落进
    # 「近白」那一档的有时只有两三个像素。
    lights = blobs(frame.rows, frame.box, lambda h, s, v: s < 0.13 and v > 0.78, lo=2, hi=200)

    # 重心是小数，而曲线像素是按整点收在集合里的 —— 不取整，邻域查表一个也命中不了，
    # 于是「每个白点都找得到自己那条曲线」全成了 0 个白点。
    lights = [(round(cx), round(cy), n) for cx, cy, n in lights]

    out = []
    seen = set()

    for pts in point_sets:
        if not pts:
            continue

        line = {(x, y) for (x, y) in pts if band[0] <= y <= band[1]} or pts

        # band 里的近白块，且挨着这条线自己的像素 —— 见 docstring 里那三条理由（尤其第三条：
        # 这条判据**不能**再提「哪一端是最右」，胶囊与曲线同色而它就挂在最右端）。
        #
        # 半径给到 6，不是 3：**白点自己把线头那几像素盖住了**。点画在线末端的上一格
        # （`Points[^1].Y - Px(4)`），而它是实心白的，于是这条颜色在点底下那几个像素根本不
        # 出现。实测滚动那一帧，三只里两只离自己的线 2～3 像素，第三只离 **4** —— 差一个
        # 像素的事，`±3` 那一版就把它整只丢掉了（「三条曲线都还在窗口里」那条断言报「2 个
        # 白点」）。6 ≈ 点的半径 + 那格偏移 + 抗锯齿，再留一点。
        own = [d for d in lights
               if band[0] <= d[1] <= band[1] and gap(d, line) <= 6]

        # 一条也没有时（点太淡、或者线头那几像素整格被盖掉）退到「挨着任意一条线」——
        # 这一步只为了让 `measure` 不至于少一只，选谁并不准，所以放在最后。
        nearby = own or [d for d in lights
                         if band[0] <= d[1] <= band[1] and gap(d, any_line) <= 6]

        if not nearby:
            continue

        # 几个都沾上时（两条线的末端挨在一起，两个点都算「挨着这条线」）：
        # 先取离这条线**自己**最近的，再取最靠右的那个 —— 曲线头永远在绘图区右端那一侧。
        dot = min(nearby, key=lambda d: (gap(d, line), -d[0]))

        if (dot[0], dot[1]) in seen:
            continue

        seen.add((dot[0], dot[1]))
        out.append(dot)

    return sorted(out, key=lambda d: d[1])


def owners(point_sets, dot, near=3):
    """一个白点骑在哪几条曲线上 —— 曲线的末端挨在一起时会是两条。"""
    x, y, _ = dot

    return [i for i, pts in enumerate(point_sets)
            if any(abs(px - x) <= near and abs(py - y) <= near for (px, py) in pts)]


def label_of(points, band, least=45):
    """一只的胶囊标签：几只、最长那条边在哪一行、那一条从哪一列开始。

    数的是**长段**。胶囊的上下边是同一颜色一段很长的水平连续像素（量到 64～74），而曲线
    本身是斜的，一行里最多 7 个像素 —— 差一个数量级，所以「≥45」这条线两边都够不着。

    数出来是**段数**而不是只数：一只胶囊有两条边，相邻两只之间只留 `Px(8)`（不到三像素），
    下面那只的**上边**会被上面那只的底边压掉，于是偶尔只剩一条边。所以向上取整。

    行范围限制在 `band` 里：收尾那排卡片也是圆角的、也带曲线色的边框，整幅扫会把它们一并
    数成标签。
    """
    rows = []

    for y in range(band[0], band[1] + 1):
        longest, start = best_run(points, y)

        if longest >= least:
            rows.append((y, longest, start))

    if not rows:
        return 0, None, None

    segments = 1

    for k in range(1, len(rows)):
        if rows[k][0] - rows[k - 1][0] > 2:
            segments += 1

    best = max(rows, key=lambda r: r[1])

    return (segments + 1) // 2, best[0], best[2]


class Frame:
    """一张预览截图，按画面裁出来量。"""

    def __init__(self, win, name):
        from PIL import Image

        self.path = shot(win, name)
        self.image = Image.open(self.path).convert("RGB")

        # **抓错了就不量。** `capture` 会重试四次、四次都把最后一张图写下来、并把
        # 「这是不是这个窗口」作为返回值交出来。不看它的后果是量出一整串「有道理的数字」：
        # 一张锁屏壁纸的「画布」是整张图，于是六条曲线数出两条、胶囊「不在」、绘图区右缘
        # 变成 1919 —— 八条断言失败，报的却像是「胶囊竖栏把画面画坏了」。
        self.ok = winui.capture(win, self.path)

        if not self.ok:
            print(f"  ! {name}：抓到的不是应用窗口（屏幕锁了/息屏了？）—— 这一张不量数")
            self.box = self.rows = None
            return

        box = winui.canvas_box(self.image)

        if box is None:
            self.ok = False
            self.box = self.rows = None
            return

        # 下缘重算：`canvas_box` 给的那个偏低几十像素，见 `winui.frame_bottom`。
        self.box = (box[0], box[1], box[2], winui.frame_bottom(self.image, box))
        self.rows = hsv_rows(self.image, self.box)

    def of(self, rgb, trim=4):
        """画面上属于这个颜色的像素。

        `trim` 让掉最底下那几行：那里是**进度条**，它的渐变里正好有 `Tracks` 的青与蓝、
        也有本金线的琥珀（`Palette.ProgressFill` 就是蓝→青→琥珀）。不让掉它，「每种颜色
        各有多少像素」会把进度条算进好几条曲线里。
        """
        return {(x, y) for (x, y) in painted(self.rows, self.box, rgb, palette=PALETTE_RGB)
                if y <= self.box[3] - trim}


def shot(win, name):
    """抓一张画面，路径由 `winui.capture` 写、它抓错窗口时**如实返回 False**。

    抓错的那张是别的窗口的截图（锁屏、编辑器、桌面），而接下来每一条量出来的数都成了
    假话 —— 见那个函数的说明。`Frame` 看这个布尔值决定量不量。
    """
    path = os.path.join(REPO, "artifacts", name)

    winui.capture(win, path)

    try:
        win.SetTopmost(False)
    except Exception:  # noqa: BLE001
        pass

    return path


def measure(win, name, count=None):
    """量一张画面：白点、每条曲线的胶囊标签、本金线、每种颜色各有多少像素。

    行范围是从白点推出来的，不是按画面高度切一刀 —— 见 `label_of`。取不到白点时（动画刚
    起步，标签叠在线末端上把点盖住了）退到画面中间那一段：上面是标题和大数字，下面是收尾
    卡片，中间那三成才是绘图区。
    """
    colours = TRACKS if count is None else TRACKS[:count]
    frame = Frame(win, name)

    if frame.box is None or frame.rows is None:
        return None

    left, right, top, bottom = frame.box
    points = [frame.of(rgb) for rgb in colours]
    out = {"frame": frame, "box": frame.box, "bottom": bottom,
           "pixels": [len(pts) for pts in points]}

    capital = frame.of(CAPITAL)
    out["capital"] = widest(capital, top, bottom) if capital else (0, None)

    dots = end_dots(frame, points)
    out["dots"] = dots
    out["rides"] = [owners(points, dot) for dot in dots]

    # 每只的白点落在哪一列 —— 「标签骑在头的**右边**」要拿它当基准。几只的曲线头本来就
    # 同一列（都画在同一个 `moving` 上），所以这张表里几个值相同是可以预期的。
    out["dotx"] = {}

    for dot, who in zip(dots, out["rides"]):
        for i in who:
            out["dotx"].setdefault(i, dot[0])

    ys = [d[1] for d in dots]

    if ys:
        band = (int(min(ys)) - 45, int(max(ys)) + 70)
    else:
        height = bottom - top
        band = (top + (height * 45 // 100), top + (height * 74 // 100))

    out["band"] = band
    out["labels"] = [label_of(pts, band) for pts in points]

    out["ends"] = {}

    for i in range(len(points)):
        hit = next((dot for dot, who in zip(dots, out["rides"]) if i in who), None)
        out["ends"][i] = hit[1] if hit is not None else None

    return out


# ---- 真机 ----------------------------------------------------------------------------

def texts(root):
    return [c.Name for c in winui.find_all(root, lambda c: c.Name, limit=4000) if c.Name]


def status_text(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    return " ".join(texts(bar)) if bar is not None else ""


def close_status(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return

    closer = winui.find(bar, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "关闭")

    if closer is not None:
        try:
            press(closer, win)
            time.sleep(0.7)
        except Exception:  # noqa: BLE001
            pass


def status_until(win, patterns, seconds=300):
    """等到状态行出现某几个样子之一。

    不能只等「有字」：取数过程中状态行一直有字（「中国平安: 320 …」），所以等到的一定是
    一个**样子** —— 取数完成了，或者被拒绝了。
    """
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(1.5)
        text = status_text(win)

        if not text:
            continue

        if any(p.search(text) for p in patterns) or FAIL.search(text):
            return text

    return None


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

    if item is None:
        return False

    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)

    return True


def maxed(win):
    """把窗口最大化，并把「真的最大了吗」量出来。

    以前的写法把 `SetWindowVisualState` 的异常吞掉就完事。那是危险的：清单那一排是横向
    滚动的，窗口窄一些，第二只 chip 就落到面板外面、矩形被量成 0×0；而那一排正是这一页
    唯一要真点 chip 的地方。最大化成功与否，决定了那一下点得着点不着。
    """
    win.SetActive()
    time.sleep(1.0)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass

    try:
        box = win.BoundingRectangle

        return box.width() > 400 and box.height() > 400
    except Exception:  # noqa: BLE001
        return False


def toggle_of(control):
    try:
        return control.GetTogglePattern()
    except Exception:  # noqa: BLE001
        return None


def press(control, win=None):
    """按一下一个控件，并在**真的按到了**时才返回 True。

    三种按法依次退化：`InvokePattern` 是正规的；取不到时真点一下；还不行退到键盘。

    退化是必需的，而且每一条都踩过：

      - **清单的 chip 根本没有 `InvokePattern`。** 实测两只 chip —— 一只已在清单里、一只刚
        加进来 —— `GetInvokePattern()` 都返回 None（`Toggle` 与 `Legacy` 都有，就是
        `Invoke` 没有）。所以这一路对 chip 从来就没生效过，脚本一直靠真点。
      - **`Click` 在矩形为空时静默跳过这一下，却照样正常返回。** `uiautomation` 的
        `Click` 走 `MoveCursorToInnerPos`，矩形算不出内点时返回空，而调用处是 `if point:`
        —— 没有点，没有异常。清单那一排是横向滚动的，面板外的 chip 矩形正是 0×0，于是
        「按过了」成了一句谎话，而它的勾选态照常读得到，看起来只像没生效。

    所以这里做两件事：点之前先看矩形是否为空（空的直接报失败，不再谎报），点之前先把
    窗口激活（真点是按屏幕坐标点的，窗口不在最上层时那一下落在别人身上）。
    """
    if win is not None:
        try:
            win.SetActive()
            time.sleep(0.25)
        except Exception:  # noqa: BLE001
            pass

    try:
        pattern = control.GetInvokePattern()
    except Exception:  # noqa: BLE001
        pattern = None

    if pattern is not None:
        try:
            pattern.Invoke()
            return True
        except Exception:  # noqa: BLE001
            pass

    try:
        box = control.BoundingRectangle

        # 见 docstring：矩形为空时 Click 什么都不做也不报错。
        if box.width() <= 0 or box.height() <= 0:
            return False
    except Exception:  # noqa: BLE001
        return False

    try:
        control.Click(simulateMove=False)
        return True
    except Exception:  # noqa: BLE001
        pass

    try:
        control.SetFocus()
        time.sleep(0.3)
        control.SendKeys("{Space}", waitTime=0.3)
        return True
    except Exception:  # noqa: BLE001
        return False


def chip(win, code):
    """清单里某一只的名字开关。

    按**代码**寻址，不按 14 种语言拼写的名字：chip 的 ToggleButton 带着
    `AutomationProperties.AutomationId="{x:Bind Code}"`。同一个代码在页面上还出现一次
    （下面那一排一键预设），靠 TogglePattern 把两者分开。
    """
    return winui.find(win, lambda c: c.AutomationId == code and toggle_of(c) is not None)


def chip_state(win, code):
    found = chip(win, code)

    if found is None:
        return None

    pattern = toggle_of(found)

    return pattern.ToggleState if pattern is not None else None


def chip_names(win):
    """清单里每一只的 (代码, 名字)，按清单自己的顺序。

    名字读 ToggleButton 的 Name（模板里就写着 `{x:Bind Name}`），代码读它的 AutomationId
    —— 两者是同一个 RaceEntry 的两面，所以这一对不可能错位。
    """
    out = []

    for control in winui.find_all(win, lambda c: c.ControlTypeName == "ButtonControl"):
        if toggle_of(control) is None or not control.AutomationId:
            continue

        if re.fullmatch(r"(sh|sz|bj|hk|us)[A-Za-z0-9.]+", control.AutomationId):
            out.append((control.AutomationId, control.Name))

    return out


def preset(win, code):
    """那一排一键预设里的一个。与 chip 同代码，但没有 TogglePattern。"""
    return winui.find(win, lambda c: c.AutomationId == code and toggle_of(c) is None)


def remove_chip(win, name):
    """chip 右半边那个 ×。两个按钮同名（都是这只标的的名字），靠子文本里的 × 分开。"""
    for control in winui.find_all(win,
                                  lambda c: c.ControlTypeName == "ButtonControl" and c.Name == name):
        kids = [t.Name for t in winui.find_all(
            control, lambda c: c.ControlTypeName == "TextControl", limit=4)]

        if any(k.strip() in ("×", "✕") for k in kids):
            return control

    return None


def clear_list(win):
    """把共享清单清空。

    **先清空再断言**：这份清单是八个榜共用、跨会话留下的，上一次跑脚本加的东西还在这里。
    不清空的话取的数是「上次那几只 + 这次这三只」，而脚本按这次这三只重算 —— 两边对不上，
    而画面是一版漂亮的三条线，看不出它多画了几只。
    """
    for _ in range(24):
        names = [name for _, name in chip_names(win)]

        if not names:
            return True

        button = remove_chip(win, names[0])

        if button is None:
            return False

        try:
            if not press(button, win):
                return False
        except Exception:  # noqa: BLE001
            return False

        time.sleep(0.6)

    return False


def tick(win, code, on, tries=3):
    """把一只勾上或勾掉。chip 是开关，一次 `Click` 就是翻面。

    **这是整个脚本里唯一真去点 chip 的地方。** 两只、三只、六只那几步都是一键预设走的
    `Include` —— 它们进来就已经是勾上的，`tick` 读回来是 1，一次也没点过。只有跨市场那只
    是用搜索框加进来的（`add_to_list` 不调 `Include`），加进来默认是关的，必须真点，于是
    也只有这一步会撞上 `press` 的那些退化路径。

    所以这里重试，并且把「点不到」与「点了没翻面」分开：前者是 `press` 报的失败（矩形为
    空、chip 被横向滚动的面板裁在外面），后者是真点到了而控件没反应。两者都重试三次再认
    输，因为这一下确实偶发失效，而静默放过它等于把后面「港股没进画」那三条断言变成对一
    个没发生过的操作的表扬。
    """
    for attempt in range(tries):
        control = chip(win, code)

        if control is None:
            return False

        if (chip_state(win, code) == 1) == on:
            return True

        if not press(control, win):
            time.sleep(1.2)
            continue

        time.sleep(1.0)

        if (chip_state(win, code) == 1) == on:
            return True

    return False


def ticked(win):
    """画面上被勾中的那几只在清单里的顺序 —— 也就是画面的顺序。"""
    return [code for code, _ in chip_names(win) if chip_state(win, code) == 1]


def pick_range(win, label):
    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")

    return winui.combo_pick(win, combo, label) if combo is not None else None


def add_to_list(win, code, name, tries=3):
    """在自选搜索框里填一个代码并提交，然后数一遍 chip。写法抄自 verify-holdodds。"""
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

        if any(n.strip() == name for _, n in chip_names(win)):
            return True

    return False


def read_status(win, status, pattern=None):
    """把「取数完成」那句话拆成 (几份, 多少个交易日, 起, 止)。

    `pattern` 是这一页的那一句。持仓页写「{n} 只标的 · {n} 个交易日」，定投页写
    「{n} 个计划 · {n} 个交易日」——而**单份时两页都不写前半截**（持仓页那句变成
    「已取 1211 个交易日（…），持有 1211 天」），所以那一组做成可选，一条正则管两种情形。
    """
    hit = (pattern or FETCHED).search(status)

    if hit is None:
        return None

    return {
        "tracks": int(hit.group(1)) if hit.group(1) else 1,
        "days": int(hit.group(2)),
        "start": hit.group(3),
        "end": hit.group(4),
        "status": status,
    }


def fetch(win, seconds=300, patterns=None):
    """按一次取数并读回状态行。

    `patterns` 是这一页「取数完成了」的那几个样子，默认持仓页那一套（见 `read_status`）。
    """
    done = patterns or [FETCHED]
    close_status(win)

    button = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if button is None:
        return None, "取数按钮不在"

    # 点不到要说出来：以前 `press` 在矩形为空时谎报成功，这里就变成「取数没反应」，
    # 而真正的病因是按钮被量成了 0×0。
    if not press(button, win):
        return None, "取数按钮点不到"

    status = status_until(win, done, seconds)

    if status is None:
        return None, status_text(win) or "（状态条空）"

    return read_status(win, status, done[0]), status


def press_preset(win, code, seconds=300, patterns=None):
    """点一个一键预设 —— 它自己就会取数（加入清单 + 勾上 + 取数，一次点击）。

    **`patterns` 一定要按页面给。** 状态行的措辞是每页自己的资源：持仓页说
    「{n} 只标的」、定投页说「{n} 个计划」，而单份时两页都只说「已取 N 个交易日（…）」。
    于是定投页借用持仓页那对正则时，**第一只是通的、第二只起永远等不到** —— `status_until`
    干等满 300 秒才返回，返回的是 `(None, 状态行)`：一个非空元组，**真值依旧为真**，所以
    调用处那句 `if press_preset(...)` 看着像过了。后果是每加一只白等五分钟，整趟拖到半个
    小时，而这半小时里任何一个别的脚本来动窗口，画面就不是这一趟摆出来的了。

    所以要么传 `patterns`，要么老实看返回值里的第一个元素（它是 `None` 就说明没解析出
    来，不是没取到数）。
    """
    done = patterns or [FETCHED, TOO_MANY]
    close_status(win)

    button = preset(win, code)

    if button is None:
        return None, "预设不在"

    if not press(button, win):
        return None, "预设点不到"

    status = status_until(win, done, seconds)

    if status is None:
        return None, status_text(win) or "（状态条空）"

    return read_status(win, status, done[0]), status


def scrub(win, progress):
    slider = winui.find(win, lambda c: c.AutomationId == "Scrub")

    if slider is None:
        return False

    slider.GetRangeValuePattern().SetValue(progress)
    time.sleep(1.8)

    return True


def motion(win, name):
    """切一下推进方式，返回它请求的那一项的名字（取不到下拉就是 None）。

    **返回值不是「切成了」**：ComboBox 在本应用里既没有 `SelectionPattern` 也没有
    `ValuePattern`，选中项根本读不回来，见 `winui.combo_pick`。所以这个函数只说明它点过
    哪一项，切换是否生效由调用方**看画面**判定。
    """
    combo = winui.find(win, lambda c: c.AutomationId == "MotionCombo")

    return None if combo is None else winui.combo_pick(win, combo, name)


def window_on(win):
    """窗口天数框可用吗 —— 推进方式读回来的唯一办法。

    ComboBox 的选中项读不回来（见 `motion`），而「窗口框亮不亮」是由 `ChosenMotion()` 直接
    算出来的同一个值：滚动才亮。所以这一页的推进方式是不是真的切过去了，看这个布尔值，
    不看下拉。
    """
    box = winui.find(win, lambda c: c.AutomationId == "WindowBox")

    return None if box is None else box.IsEnabled


def head_of(shot):
    """最靠右的那个末端白点的 x —— 曲线的头。

    白点是按 y 排的（见 `end_dots`），所以这里要自己取 x 最大的那个，不能拿 `[-1]`：
    几只挤在一起时最后那个点是画面最下面那只，而不是最靠右的那只。
    """
    if shot is None or not shot["dots"]:
        return None

    return max(d[0] for d in shot["dots"])


def main():
    for old in SHOTS:
        path = os.path.join(REPO, "artifacts", old)

        if os.path.exists(path):
            os.remove(path)

    win = winui.launch(winui.EXE)

    if win is None:
        check("应用起得来", False)
        return report()

    check("窗口最大化了（窄窗口会把 chip 挤出横向滚动的面板）", maxed(win))

    today = date.today()
    start = add_months(today, -36)

    # ---- 0) 源码：画布上量不出来的那几件事 -----------------------------------------
    print("源码")

    series = open(SERIES, encoding="utf-8").read()
    renderer = open(RENDERER, encoding="utf-8").read()
    page = open(PAGE, encoding="utf-8").read()
    xaml = open(XAML, encoding="utf-8").read()
    palette = open(PALETTE, encoding="utf-8").read()
    picker = open(PICKER, encoding="utf-8").read()
    picker_xaml = open(PICKER_XAML, encoding="utf-8").read()
    store = open(STORE, encoding="utf-8").read()

    check("上限是六只", "public const int MostTracks = 6;" in series)
    check("超过上限是拒绝，不是画前几只",
          "chosen.Count > PositionLoader.MostTracks" in page
          and "PositionTooMany" in page
          and "return;" in page.split("chosen.Count > PositionLoader.MostTracks")[1][:600])
    check("跨市场的标的被滤掉（金额是本市场的钱）", "_market.Accepts(e.Code)" in page)
    check("只剩别的市场时报「没有本市场的标的」", "PositionNoMarketPicks" in page)
    check("日期轴取的是并集（取交集会把十年悄悄截成三年）",
          "var union = new SortedSet<DateOnly>();" in series)
    check("晚上市的从自己第一天起，不在本金上拉平线",
          "value = _board.Capital + ((track.Value[at] - _board.Capital) * p);" in renderer)
    check("区间内没有数据的进 Skipped 而不是画平线", "skipped.Add(display);" in series)
    check("颜色按位置取（不按代码哈希）", "public static Color Track(int order)" in palette)
    check("曲线色里没有本金线的琥珀",
          "Emphasis,\n        Rgb(0x06, 0xB6, 0xD4)" in palette)
    check("两条以上不画填充（六层填充是一团泥）",
          "if (!_board.Comparing && lines.Count > 0)" in renderer)
    check("两条以上图例只剩本金",
          '_board.Comparing\n            ? new[] { (Palette.Moving, "PositionLegendCapital") }' in renderer)
    check("末端白点锚在自己那条线上（不是本金线上）",
          "var (lx, ly) = (line.Points[^1].X, line.Points[^1].Y - context.Px(4));" in renderer)
    check("胶囊标签两行：名字 + 金额", '(name + " ", Palette.Muted, nameFormat),' in renderer)
    check("标签彼此避让（按 y 排序往下推）",
          "var order = Enumerable.Range(0, boxes.Count).OrderBy(i => boxes[i].Y).ToArray();"
          in renderer)
    check("标签描边不是发丝线（压在曲线上要分得开）",
          "private const double LabelEdge = 3;" in renderer)

    # ---- 标签骑在曲线头右边 ---------------------------------------------------------
    #
    # 这一组全是**布局**断言，而布局是最容易悄悄回退的那一类：画面看着还是「三条线、
    # 三个胶囊」，只有把它们之间的距离量出来才知道胶囊是不是又压回曲线上去了。
    check("胶囊锚在自己曲线头的**右边**（左缘 = 头 + LabelGap）",
          "anchors[i].X + context.Px(LabelGap)" in renderer)
    check("右缘按**画面**右缘收，不是绘图区右缘（那条竖栏本来就在右边距里）",
          "context.Width - context.Px(LabelEdgePad) - width" in renderer)
    check("绘图区让出一列给胶囊（标题、卡片、进度条仍是整幅宽）",
          "Math.Max(1, context.ChartWidth - LabelColumn(session, context))" in renderer)
    check("那一列按**最终**金额量，所以每帧一样宽（不然曲线会横着滑）",
          "track.Name, track.Profit));" in renderer)
    check("日期也按让出去之后的宽度排（一处量、两处用）",
          renderer.count("DrawXLabels(session, context, t, bottom, plotW, introA,") == 2)
    check("两条以上大数字是领先那只的金额 + 名字",
          "PositionLeaderLine" in renderer and "plot.Values[leader] - _board.Capital" in renderer)
    check("单只时大数字仍是收益率",
          "var ret = _board.Capital > 0 ? ((plot.Values[leader] / _board.Capital) - 1) * 100 : 0;"
          in renderer)
    check("两条以上收尾是每只一张卡",
          "DrawTrackCards(session, context, a, left, gap, y, cardHeight, valueFormat);" in renderer)
    check("取数后把清单里的名字换成端点叫的",
          "Watchlist.Rename(track.Code, InstrumentNames.Display(track.Code, track.Name));" in page)
    check("一键预设是「加入清单 + 勾上 + 立刻取数」",
          "Watch.Include(code);" in page and "Fetch();" in page)
    check("页面用的是共享清单控件，不是又一个单标的搜索框",
          '<views:WatchlistPicker x:Name="Watch" Selectable="True" />' in xaml
          and "InstrumentSearch" not in xaml)
    check("预设按代码寻址，不按 14 种语言拼写的名字",
          'AutomationProperties.AutomationId="{x:Bind Code}"' in xaml)
    check("chip 也按代码寻址（脚本与读屏都要）",
          'AutomationProperties.AutomationId="{x:Bind Code}"' in picker_xaml)
    check("第一次勾选把「只画第一只」的规则变成显式集合",
          "if (!_touched)\n        {\n            _touched = true;" in picker)
    check("没交互过时只画第一只",
          "? [.. picks.Where(p => _on.Contains(p.Code))]\n                : [picks[0]];" in picker)
    check("清单存在盘上（重启还在）", 'StudioPreferences Store = new("Watchlist.")' in store)
    check("这一页的偏好里不再存标的代码/名字",
          'Save("Instrument' not in page and 'GetString("Instrument' not in page)

    # 推进方式：两种走法看的是同一份数据，所以它们必须是**渲染器的构造参数**而不是取数
    # 参数 —— 构造参数才在每次重画时被读到，见 memory 里那条「影响排名的开关写成属性会读
    # 成默认值」的教训。
    check("推进方式是渲染器的构造参数（不是取数参数）",
          "public PositionRenderer(PositionBoard board, AnimationPlan plan, PositionMotion motion, int window)"
          in renderer)
    check("两种推进方式：整段铺满 / 窗口滚动",
          "public enum PositionMotion" in series and "Grow = 0," in series and "Scroll = 1," in series)
    check("整段铺满就是「窗口和整段一样长」的同一套算术",
          "var count = _motion is PositionMotion.Scroll ? Math.Min(_window, n) : n;" in renderer)
    check("窗口右端跟着到达点走（滚动是连续滑，不是一天一跳）",
          "Math.Max(moving + eased[moving], count - 1)" in renderer)
    check("窗口左端 = 右端 − 窗口长度",
          "var first = _motion is PositionMotion.Scroll ? head - (count - 1) : 0;" in renderer)
    check("横轴把窗口铺满（不是把整段铺满）",
          "double Across(int i) => mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);" in renderer)
    check("窗口左端向上取整（曲线不能画到轴外面去）",
          "var left = Math.Max(0, (int)Math.Ceiling(first));" in renderer)
    check("纵轴只算一次，不随窗口重算（本金线不会跟着滑）",
          renderer.count("_scale = AnimationPlan.NiceScale(") == 1)
    check("日期标签按窗口取，但每颗钉在自己那一天上",
          "if (i < first || i > head)" in renderer)
    check("切换推进方式只重画、不重新取数",
          'SelectionChanged="OnLookChanged"' in xaml
          and "WindowBox.IsEnabled = ChosenMotion() is PositionMotion.Scroll;" in page)
    check("下拉与窗口框各自绑了资源键",
          'x:Uid="PositionMotionLabel"' in xaml and 'x:Uid="PositionWindowLabel"' in xaml)

    # ---- 1) 进页 -------------------------------------------------------------------
    print("\n真机")

    if not goto(win, "持仓收益"):
        check("导航里有「持仓收益」", False)
        return report()

    check("导航里有「持仓收益」", True)
    check("本金框在", winui.find(win, lambda c: c.AutomationId == "CapitalBox") is not None)
    check("区间下拉在", winui.find(win, lambda c: c.AutomationId == "RangeCombo") is not None)
    check("取数按钮在", winui.find(win, lambda c: c.AutomationId == "FetchButton") is not None)
    check("自选清单的搜索框在这一页（共享控件搬过来了）",
          winui.find(win, lambda c: c.AutomationId == "Search") is not None)
    check("一键预设那一排都在",
          all(preset(win, code) is not None for code, _ in PRESETS),
          "、".join(name for code, name in PRESETS if preset(win, code) is None) or "七只都在")

    # 偏好会持久化：区间上一次跑脚本可能留在别的档上，三档里最省事的那个显式选一遍。
    check("区间选到「近 3 年」", pick_range(win, "近 3 年") == "近 3 年",
          str(pick_range(win, "近 3 年")))
    check("清单先清空（这份清单跨会话共享）", clear_list(win))
    check("清空后清单是空的", chip_names(win) == [], str(chip_names(win)))

    # ---- 2) 一只 -------------------------------------------------------------------
    print("\n一只")

    data, status = press_preset(win, PRESETS[0][0])

    if data is None:
        check("点一键预设就取数", False, status[:120])
        return report()

    check("点一键预设就取数", True, data["status"][:70])
    check("取的是单只口径（没有「N 只标的」）", "只标的" not in data["status"])
    check("清单里只有这一只且被勾上", ticked(win) == [PRESETS[0][0]], str(ticked(win)))
    check("默认标题写着这一只",
          any(f"持仓收益：{PRESETS[0][1]}" in t for t in texts(win)),
          next((t for t in texts(win) if "持仓收益" in t), "（没有）"))

    union, tracks = expected(start, today, PRESETS[:1])

    check("交易日数与独立算的一致", data["days"] == len(union),
          f"页面 {data['days']} / 脚本 {len(union)}")
    check("区间与独立算的一致",
          data["start"] == union[0].isoformat() and data["end"] == union[-1].isoformat(),
          f"页面 {data['start']}–{data['end']} / 脚本 {union[0]}–{union[-1]}")

    one = measure(win, "verify-position-one.png")

    check("画布量得出（预览在）", one is not None)

    if one is not None:
        left, right, top, bottom = one["box"]
        ratio = (right - left + 1) / (bottom - top + 1)

        check("画面是 9:16（下缘算准了才对得上）",
              abs(ratio - 9 / 16) / (9 / 16) < 0.01,
              f"{right - left + 1}×{bottom - top + 1} 比 {ratio:.4f}（9:16 是 0.5625）")

        check("一只只有一个末端白点", len(one["dots"]) == 1, f"{len(one['dots'])} 个")
        check("本金线是一根横贯绘图区的直线", one["capital"][0] >= 100,
              f"最长 {one['capital'][0]} 像素 @y={one['capital'][1]}")
        check("单只也有曲线末端的胶囊标签（这是这次新加的）", one["labels"][0][0] == 1,
              f"标签 {one['labels'][0][0]} 只，最长那条边在 y={one['labels'][0][1]}"
              f"、从 x={one['labels'][0][2]} 起")

        # 「只有一条曲线」用标签数，不用像素数：抗锯齿会让红线的边渗出几十个落在别的色相
        # 窗口里的像素（大数字是 Emphasis 红，边上一圈就是粉的），而标签一只也伪造不出来。
        check("单只只画第一条曲线色（别的色一条标签也没有）",
              sum(row[0] for row in one["labels"]) == 1 and one["labels"][0][0] == 1,
              " / ".join(f"{i + 1}: {one['labels'][i][0]} 只" for i in range(6)))

        capital_y = one["capital"][1]
        profit = tracks[0]["profit"]

        check("白点在本金线的正确一侧（跟着收益的符号）",
              (one["dots"][0][1] < capital_y) == (profit > 0),
              f"点 y={one['dots'][0][1]:.0f} 本金线 y={capital_y} 收益 {profit:+,.0f}")

    # ---- 3) 跨市场的标的被滤掉 -----------------------------------------------------
    #
    # 就放在「一只」后面，因为清单那一排是**横向滚动**的：面板只放得下三只，第四只 chip
    # 的矩形是 0×0，点不动（见 press）。此刻清单里只有第一只，加进来的港股那只排第二，
    # 点得到；等七只都进来之后，最后几只已经滚出面板，这一步就做不成了。
    print("\n跨市场")

    if not add_to_list(win, FOREIGN[0], FOREIGN[1]):
        check("把港股那只加进清单", False, str(chip_names(win)))
    else:
        check("把港股那只加进清单", True, " / ".join(n for _, n in chip_names(win)))
        check("新进清单的那只默认是关的（chip 是开关）",
              chip_state(win, FOREIGN[0]) == 0, str(chip_state(win, FOREIGN[0])))
        check("把港股那只也勾上", tick(win, FOREIGN[0], True))
        check("清单里现在是一只 A 股 + 一只港股（第二只还在面板里）",
              len(chip_names(win)) == 2, " / ".join(n for _, n in chip_names(win)))

        data, status = fetch(win)

        if data is None:
            check("跨市场勾选后取数", False, status[:120])
        else:
            check("跨市场勾选后取数", True, data["status"][:70])
            check("港股那只没有进画（金额是本市场的钱）", data["tracks"] == 1,
                  data["status"][:80])

            filtered = measure(win, "verify-position-filtered.png", count=1)

            check("画面上还是一条曲线、一个标签、一个白点",
                  filtered is not None and len(filtered["dots"]) == 1
                  and filtered["labels"][0][0] == 1,
                  f"{len(filtered['dots']) if filtered else '—'} 个白点 / "
                  f"{filtered['labels'][0][0] if filtered else '—'} 个标签")

        removed = remove_chip(win, FOREIGN[1])

        if removed is not None:
            press(removed, win)
            time.sleep(0.9)

        check("把港股那只从清单里删回去",
              not any(code == FOREIGN[0] for code, _ in chip_names(win)),
              " / ".join(n for _, n in chip_names(win)))
        check("只剩第一只勾着（港股那只勾过，但它不在本市场）",
              ticked(win) == [PRESETS[0][0]], str(ticked(win)))

    # ---- 4) 两只 -------------------------------------------------------------------
    print("\n两只")

    data, status = press_preset(win, PRESETS[1][0])

    if data is None:
        check("加第二只并取数", False, status[:120])
        return report()

    check("加第二只并取数", True, data["status"][:70])
    check("报的是两只", data["tracks"] == 2, data["status"][:80])
    check("两只都勾着", ticked(win) == [PRESETS[0][0], PRESETS[1][0]], str(ticked(win)))
    check("默认标题是「A vs B」",
          any(f"{PRESETS[0][1]} vs {PRESETS[1][1]}" in t for t in texts(win)),
          next((t for t in texts(win) if " vs " in t), "（没有）"))

    union, tracks = expected(start, today, PRESETS[:2])

    check("两只的交易日数与独立算的一致", data["days"] == len(union),
          f"页面 {data['days']} / 脚本 {len(union)}")

    two = measure(win, "verify-position-two.png", count=2)

    check("画布量得出", two is not None)

    if two is not None:
        check("两只就是两个白点", len(two["dots"]) == 2, f"{len(two['dots'])} 个")
        check("两条曲线色都出现了", all(two["pixels"][i] > 200 for i in (0, 1)),
              " / ".join(f"{i + 1}: {two['pixels'][i]}" for i in (0, 1)))
        check("两条都有胶囊标签（不是只有尽头那一只）",
              all(two["labels"][i][0] == 1 for i in (0, 1)),
              " / ".join(f"{i + 1}: {two['labels'][i][0]} 只" for i in (0, 1)))

        # 两只：一正一负，各自必须落在本金线的正确一侧。锚错线 —— 比如锚到
        # min(自己的线, 本金线) —— 就会把亏损那一条抬到本金线上方。
        capital_y = two["capital"][1]

        check("两条曲线各自在本金线的正确一侧",
              all((two["ends"][i] < capital_y) == (tracks[i]["profit"] > 0) for i in (0, 1)),
              "、".join(f"{tracks[i]['name']} {tracks[i]['profit']:+,.0f} y={two['ends'][i]}"
                        f"（本金线 {capital_y}）" for i in (0, 1)))

    # ---- 5) 三只 -------------------------------------------------------------------
    print("\n三只")

    data, status = press_preset(win, PRESETS[2][0])

    if data is None:
        check("加第三只并取数", False, status[:120])
        return report()

    check("加第三只并取数", True, data["status"][:70])
    check("报的是三只", data["tracks"] == 3, data["status"][:80])
    check("三只都勾着", ticked(win) == [code for code, _ in PRESETS[:3]], str(ticked(win)))
    check("默认标题是「A 等 3 只」",
          any(f"{PRESETS[0][1]} 等 3 只" in t for t in texts(win)),
          next((t for t in texts(win) if "等 3 只" in t), "（没有）"))

    union, tracks = expected(start, today, PRESETS[:3])

    check("三只的交易日数与独立算的一致", data["days"] == len(union),
          f"页面 {data['days']} / 脚本 {len(union)}")
    check("脚本算出的三只末值互不相同（否则比的是同一个数）",
          len({round(t["value"]) for t in tracks}) == 3,
          "、".join(f"{t['name']} {t['value']:,.0f}" for t in tracks))

    three = measure(win, "verify-position-three.png", count=3)

    check("画布量得出", three is not None)

    if three is not None:
        check("三只就是三个白点", len(three["dots"]) == 3, f"{len(three['dots'])} 个")
        check("三条曲线色都出现了", all(three["pixels"][i] > 150 for i in (0, 1, 2)),
              " / ".join(f"{i + 1}: {three['pixels'][i]}" for i in (0, 1, 2)))
        check("三条都有胶囊标签", all(three["labels"][i][0] == 1 for i in (0, 1, 2)),
              " / ".join(f"{i + 1}: {three['labels'][i][0]} 只" for i in (0, 1, 2)))

        # 每一个白点骑在哪条曲线上，是**量出来的**：挨着它那些曲线色的像素。然后按颜色的
        # **位置**去对脚本算出来的那一只 —— 两者必须一一对上，画面最上面那个点就是最赚的
        # 那一只。哈希配色在这里就会错开。
        homes = {i: three["ends"][i] for i in (0, 1, 2)}
        capital_y = three["capital"][1]

        check("每个白点都找得到自己那条曲线",
              all(homes[i] is not None for i in (0, 1, 2)),
              " / ".join(f"{i + 1}: y={homes[i]}" for i in (0, 1, 2)))

        leader = max(range(3), key=lambda i: tracks[i]["value"])
        top = min((homes[i], i) for i in (0, 1, 2) if homes[i] is not None)

        check("最赚的那只画在最上面", top[1] == leader,
              f"脚本最赚 {tracks[leader]['name']}（第 {leader + 1} 条）/ "
              f"画面最上面是第 {top[1] + 1} 条（y={top[0]}）")

        check("符号都对（赚的在线上方、亏的在线下方）",
              all((homes[i] < capital_y) == (tracks[i]["profit"] > 0) for i in (0, 1, 2)),
              "、".join(f"{tracks[i]['name']} {tracks[i]['profit']:+,.0f} y={homes[i]}"
                        for i in (0, 1, 2)) + f"（本金线 y={capital_y}）")

        # 画面高度对得上钱：两个白点之间差多少像素，正比于那一对末值之差。反过来算「一
        # 像素多少钱」，**每一对都得一样** —— 这一条不依赖任何比例，只看画面自己。
        #
        # 只比**离得开**的那些对：白点的位置是整数像素，差 14 像素的一对，单像素量化就是
        # 7%。差不到 25 像素的对（差不到 3% 的钱）不比。
        pairs = [(a, b) for a in (0, 1, 2) for b in (0, 1, 2) if b > a]
        spans = {}

        for a, b in pairs:
            if homes[a] is None or homes[b] is None:
                continue

            dy = homes[b] - homes[a]
            dv = tracks[b]["value"] - tracks[a]["value"]

            if abs(dy) >= 25:
                spans[(a, b)] = dv / dy

        if len(spans) >= 2:
            rates = list(spans.values())
            spread = (max(rates) - min(rates)) / (sum(rates) / len(rates))

            check("每像素多少元，各对算出来一致（差 < 8%）", spread < 0.08,
                  "、".join(f"{tracks[a]['name']}→{tracks[b]['name']} {v:,.0f} 元/像素"
                            for (a, b), v in spans.items()) + f" 差 {spread:.1%}")
        else:
            check("至少有两对白点离得够开，能比每像素多少元", False,
                  f"只凑出 {len(spans)} 对")

    # ---- 6) 两种推进方式 -----------------------------------------------------------
    #
    # 这是「显示方式」而不是「参数」：切换只重画，不重新取数，所以它的全部差别正好落在
    # 像素上 —— 而画布上没有 UIA 节点，也就只能量像素：
    #
    #     整段铺满 0.5 处   曲线头跟着进度走，它在画面中段
    #     窗口滚动 0.5 处   窗口的右端就是头部，它停在绘图区右端
    #
    # 两条用**同一个进度**（0.5），所以「靠右了一大截」不依赖任何绝对位置。
    #
    # 「绘图区右端」不是画布右缘：绘图区右边让出了一条竖栏给末端胶囊（`LabelColumn`），
    # 满进度的曲线头就停在那条栏的左边界上，栏里放着胶囊。所以基准要**从画面上量**（满进度
    # 那一帧的头），不能拿画布的边框当基准 —— 拿边框当基准，一条本来是对的断言会报「还差
    # 一大截」，而那一截里大半是天生就有的留白。留白的**数目**会随竖栏宽度变（它又随名字
    # 与金额变），所以这里连数字都不写：写了就成了一条会被改一次忘一次的东西。
    # 推进方式是**落盘的**偏好（这一节的最后一条就是验它落盘），所以上一次跑完停在
    # 「窗口滚动」，这一次一开局就是滚动的 —— 不先复位，下面那一帧「整段铺满」量到的其实
    # 是滚动的样子，而「滚动」那一帧也量到同样的东西，两条断言一起错、还错得一模一样
    # （都是 1078），看不出是偏好没复位，只看见「两种走法没差别」。
    print("\n推进方式")

    check("推进方式下拉在", winui.find(win, lambda c: c.AutomationId == "MotionCombo") is not None)
    check("窗口天数框在", winui.find(win, lambda c: c.AutomationId == "WindowBox") is not None)

    motion(win, "整段铺满")

    check("复位成「整段铺满」后窗口框是灰的（窗口是滚动的参数）", window_on(win) is False,
          f"窗口框可用={window_on(win)}")

    grow = scroll = None

    if scrub(win, 0.5):
        grow = measure(win, "verify-position-grow.png", count=3)

    check("切成「窗口滚动」", motion(win, "窗口滚动") == "窗口滚动")
    check("滚动时窗口框可用", window_on(win) is True, f"窗口框可用={window_on(win)}")

    if scrub(win, 0.5):
        scroll = measure(win, "verify-position-scroll.png", count=3)

    if grow is None or scroll is None:
        check("两种推进方式都画得出", False, "取不到画面")
    else:
        left, right = grow["box"][0], grow["box"][1]
        width = right - left
        a, b = head_of(grow), head_of(scroll)

        # 绘图区右端：满进度那一帧的曲线头。同一批标的、同一条轴，两种走法都停在同一个
        # x 上，所以它是这一对比的天然基准。
        tip = head_of(three) if three is not None else None

        check("整段铺满：0.5 处曲线头还在画面中段",
              a is not None and a < left + (width * 0.66),
              f"头 x={a}，中段 {left + (width // 2)}，右缘 {right}")
        # 滚动的头部离右端最多差**一格**：窗口是 60 个交易日铺在绘图区上，新的一天从右端
        # 长出来、旧的往左挪，所以头在 [右端 - 一格, 右端] 之间来回。一格约 5.6 像素，加白点
        # 重心的一两个，取画面宽度的 4%（约 15 像素）当界 —— 而整段铺满在同一进度下要差
        # 一百多像素，这个界松一点也照样分得开。
        check("窗口滚动：0.5 处曲线头已经停在绘图区右端（窗口铺满了）",
              b is not None and tip is not None and tip - b <= width * 0.04,
              f"头 x={b}，绘图区右端 x={tip}（还差 {tip - b} 像素，画布宽 {width}）")
        check("同一个进度下滚动比整段铺满靠右一大截",
              a is not None and b is not None and b - a > width * 0.2,
              f"整段 {a} → 滚动 {b}，差 {b - a} 像素（画布宽 {width}）")
        check("滚动时三条曲线都还在窗口里（三个白点、三个标签）",
              len(scroll["dots"]) == 3 and all(scroll["labels"][i][0] == 1 for i in (0, 1, 2)),
              f"{len(scroll['dots'])} 个白点 / "
              + " ".join(str(scroll["labels"][i][0]) for i in (0, 1, 2)) + " 个标签")

    check("切回「整段铺满」", motion(win, "整段铺满") == "整段铺满")
    check("切回来之后窗口框又是灰的", window_on(win) is False, f"窗口框可用={window_on(win)}")

    # ---- 7) 标签跟着进度条走 -------------------------------------------------------
    print("\n拖动")

    early = late = None

    if scrub(win, 0.45):
        early = measure(win, "verify-position-early.png", count=3)

    if scrub(win, 0.90):
        late = measure(win, "verify-position-late.png", count=3)

    if early is not None and late is not None:
        check("两个进度下都还是三条曲线，三条都有标签",
              all(early["labels"][i][0] == 1 and late["labels"][i][0] == 1
                  for i in (0, 1, 2)),
              "0.45 " + str([early["labels"][i][0] for i in (0, 1, 2)])
              + " / 0.9 " + str([late["labels"][i][0] for i in (0, 1, 2)]))

        # 标签是**画在线的末端**的，所以进度一走，标签跟着线一起往右、上下也跟着变。两帧
        # 一比就知道它是不是真跟着 —— 不是比「最长段变了没有」，那会被「恰好一样长」放过。
        moved = []

        for i in (0, 1, 2):
            a, b = early["labels"][i], late["labels"][i]

            if a[1] is not None and b[1] is not None and (a[1] != b[1] or a[2] != b[2]):
                moved.append((i, a[1], a[2], b[1], b[2]))

        check("拖到 0.9 后三条标签都换了位置（标签跟着曲线走）", len(moved) == 3,
              "、".join(f"第{i + 1}条 y{a}→{c} x{b}→{d}" for i, a, b, c, d in moved))

        e = min(early["labels"][i][2] for i in (0, 1, 2) if early["labels"][i][2] is not None)
        l = min(late["labels"][i][2] for i in (0, 1, 2) if late["labels"][i][2] is not None)

        check("0.9 处标签比 0.45 处靠右得多（进度真的接进去了）", l - e > 60,
              f"0.45 标签左端 x={e} / 0.9 x={l}，差 {l - e} 像素")

        scrub(win, 1.0)

    # ---- 7b) 胶囊骑在曲线头**右边** -------------------------------------------------
    #
    # 这是这一页的胶囊唯一一次挪位置。以前它锚在曲线头的**左边**（右缘 = 头 − 12），于是
    # 压在自己那条线上；几只一起看时，几颗胶囊全叠在绘图区右端那一小片里，几乎盖住曲线的
    # 最后一段 —— 而画面看起来只是「标签挤了点」。
    #
    # 现在绘图区右侧让出一条竖栏（`PositionRenderer.LabelColumn`），曲线停在那条栏左边，
    # 胶囊骑在线头**右边**。两件事都能量：左缘在头的右边，右缘还在画面里。
    #
    # 为什么这一条不能只靠源码断言：源码里写对、画面里却压回去，是完全可能的
    # —— `LabelColumn` 量出来的宽度、`ChartMargins.Right` 与画布宽度三者任何一个算错，
    # 表达式都还是原来那一行。判决只在像素上。
    print("\n胶囊的位置")

    tip = measure(win, "verify-position-tip.png", count=3) if scrub(win, 1.0) else None

    if tip is None:
        check("满进度那一帧量得出", False, "取不到画面")
    else:
        right = tip["box"][1]
        ahead, inside = [], []

        for i in (0, 1, 2):
            # 变量别叫 `start`：`main` 里那个是整段区间的起点（一个日期），在这里被一个列号
            # 盖掉之后，后面 `expected(start, …)` 会拿日期当列号算 —— 报的是一句
            # 「`date` 和 `int` 不能比大小」，离现场很远。
            _, row, edge = tip["labels"][i]
            head = tip["dotx"].get(i)

            if row is None or edge is None or head is None:
                continue

            # 那一行上最长的那一段就是胶囊的上下边，它的长度约等于胶囊的宽（圆角那两截
            # 不在里面，所以只会偏短一点点 —— 这一条判的是「还在画面里」，宁松不紧）。
            width, _ = best_run(tip["frame"].of(TRACKS[i]), row)

            if edge > head + 4:
                ahead.append(i)

            if edge + width <= right:
                inside.append(i)

        check("满进度时三颗胶囊都在自己曲线头的右边（不再压曲线）", len(ahead) == 3,
              "、".join(f"第{i + 1}条 头 x={tip['dotx'].get(i)} → 胶囊 x={tip['labels'][i][2]}"
                       for i in (0, 1, 2)))
        check("三颗胶囊都没跑出画面（右边那条竖栏正是留给它们的）", len(inside) == 3,
              f"画面右缘 x={right}；"
              + "、".join(f"第{i + 1}条 左缘 {tip['labels'][i][2]}"
                         for i in (0, 1, 2)))

    # ---- 8) 上限：六只画得出来，第七只被拒 -----------------------------------------
    print("\n上限")

    for code, _ in PRESETS[3:6]:
        press_preset(win, code)
        time.sleep(0.4)
        close_status(win)

    check("六只都勾着", len(ticked(win)) == 6, str(ticked(win)))

    union, tracks = expected(start, today, PRESETS[:6])

    six = measure(win, "verify-position-six.png", count=6)

    check("画布量得出", six is not None)

    if six is not None:
        # **几个白点要算，不能写死。** A股这七只预设里，四只挤在 1.22～1.28 百万之间，轴上
        # 一共二十来个像素，两只差不到一个像素的两个点会叠成一个连通块。比例不用去猜轴刻
        # 度 —— 拿观测到的最高与最低那两个白点的距离除以它们末值之差，就是每像素多少元：
        #
        #     轴上 91 个像素 = 74.05 万元 → 一像素约 8,100 元
        #
        # 相邻两只差不到五个像素（约四万元）的，两个点必然叠在一起。点本身的直径是
        # `Px(6)` 的两倍，屏幕上四五个像素，所以五个像素就是「挨上」的界线。
        rates = [t["value"] for t in tracks]
        ys = [d[1] for d in six["dots"]]
        merged = 0

        if len(ys) >= 2 and max(rates) > min(rates) and max(ys) > min(ys):
            per_pixel = (max(rates) - min(rates)) / (max(ys) - min(ys))
            order = sorted(rates)
            merged = sum(1 for a, b in zip(order, order[1:]) if (b - a) / per_pixel < 5)

            check("六只画得出六个末端白点（挨在一起的两只算一个）",
                  len(six["dots"]) == 6 - merged,
                  f"{len(six['dots'])} 个（一像素约 {per_pixel:,.0f} 元，"
                  f"{merged} 对挨在一起，应有 {6 - merged} 个）")
        else:
            check("六只画得出六个末端白点（挨在一起的两只算一个）", False,
                  f"凑不出比例：末值 {len(set(rates))} 种 / 白点 {len(ys)} 个")

        # 标签那一条不受白点叠不叠的影响：六只各有各的胶囊，一只也不能少。**这才是「六只
        # 都画出来了」的硬证据** —— 少画一只的画面看起来完全正常，白点数还可能一模一样。
        check("六只六条曲线色都出现了", all(six["pixels"][i] > 150 for i in range(6)),
              " / ".join(f"{i + 1}: {six['pixels'][i]}" for i in range(6)))
        check("六只都有胶囊标签", all(six["labels"][i][0] == 1 for i in range(6)),
              " / ".join(f"{i + 1}: {six['labels'][i][0]} 只" for i in range(6)))

    # 第七只：一键预设自己就会发现超限 —— 加进清单、勾上、取数被拒。
    before = six["dots"] if six else []
    press_preset(win, PRESETS[6][0], seconds=40)
    time.sleep(1.0)

    check("第七只也勾上了", len(ticked(win)) == 7, str(ticked(win)))

    refusal = status_text(win)
    hit = TOO_MANY.search(refusal)

    check("勾到七只时拒绝取数", hit is not None, refusal.strip()[:70] or "（状态条空）")
    check("报的是「最多 6 只、现在勾了 7 只」",
          hit is not None and hit.group(1) == "6" and hit.group(2) == "7",
          f"{hit.group(1)} / {hit.group(2)}" if hit else "（没匹配上）")

    # 被拒之后画面不该变。**这一条比数白点硬**：多画一只的画面白点数可能一模一样（两只
    # 叠在一起），而标题是页面自己按那份持仓板写上去的 —— 板没重建，标题就还是「等 6 只」。
    check("被拒之后标题还是「等 6 只」（没有悄悄画前六只）",
          any("等 6 只" in t for t in texts(win)),
          next((t for t in texts(win) if "等" in t), "（没有）"))

    after = measure(win, "verify-position-limit.png", count=6)

    check("被拒之后白点数没变",
          after is not None and len(after["dots"]) == len(before),
          f"{len(before)} → {len(after['dots']) if after else '—'}")

    # ---- 9) 重启后清单还在 ----------------------------------------------------------
    print("\n重启")

    # 推进方式是这一页的偏好（`Position.Motion`），不是共享清单的一部分，所以它落不落盘
    # 要在重启里验一次。切上去，重启，看窗口框还是不是可用的 —— 那一个布尔值就说明
    # `ChosenMotion()` 读回来的是哪个。
    check("重启前把推进方式切成「窗口滚动」（验它落盘）", motion(win, "窗口滚动") == "窗口滚动")

    # **切完要等一会儿再杀进程。** 偏好写入是 400 毫秒去抖的（`StudioPreferences.Queue`
    # 把写操作排进一个 `DispatcherTimer`），立刻 `kill` 的话那一笔还在队列里。这里一直是靠
    # 下面那次 `chip_names`（整棵树的 UIA 遍历）把 400 毫秒拖过去才过的 —— 那是运气，
    # 不是断言。定投页那一趟没有这一步，于是踩到了。
    time.sleep(1.0)

    kept = [name for _, name in chip_names(win)]

    check("重启前清单里有七只（预设那七只）", len(kept) == 7, "、".join(kept))

    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    maxed(win)

    if goto(win, "持仓收益"):
        after = [name for _, name in chip_names(win)]

        check("重启后清单还在（存在盘上，不是内存里）", after == kept,
              "、".join(after) or "（空）")
        check("重启后勾选回到「只画第一只」（勾选是这一页的，不落盘）",
              ticked(win) == [PRESETS[0][0]], str(ticked(win)))
        check("重启后推进方式还是「窗口滚动」（偏好落盘了）", window_on(win) is True,
              f"窗口框可用={window_on(win)}")

        data, status = fetch(win)

        if data is None:
            check("重启后直接取数", False, status[:120])
        else:
            check("重启后直接取数", True, data["status"][:70])
            check("重启后画的是清单第一只（一笔一勾不跟着落盘）", data["tracks"] == 1,
                  data["status"][:80])

        # 落盘的那一个偏好用完就复位：这一趟为了验落盘把它停在「窗口滚动」上，不复位的话
        # 下一次跑是开局就在滚动里。开头那一句复位是同一件事的另一半 —— 两处都有，哪一处
        # 生效都行，缺了才要紧。
        motion(win, "整段铺满")

        check("收尾复位回「整段铺满」", window_on(win) is False, f"窗口框可用={window_on(win)}")

    return report()


if __name__ == "__main__":
    sys.exit(main())
