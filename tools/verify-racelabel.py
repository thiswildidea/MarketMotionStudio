# -*- coding: utf-8 -*-
"""真机验证条形榜的**行内文字大小**。

这不是审美，是一条会把画面说错的规则。行文字原先按**行距**算：

    nameSize = min(30, (rowH / Scale) * 0.34)

于是行数越多字越小。市值榜、极端交易日、AH 溢价三块都是十五行，算出来 27 基线像素，
**够不到那个 30 的上限** —— 应用里每一块榜都长在上限上，只有行数最多、最需要空间的
这几块没有。预览画布按 0.34 缩放（用首末两行在窗口里的 y 反解出来的），27 基线像素
落在屏幕上就是 9 像素高的字，汉字在 9 像素上没有笔画可放，读出来是一团灰。

现在按**它自己那条条形**算：

    nameSize = min(36, (barH / Scale) * 0.72)

行距管的是两行隔多远，条形管的是每行多高 —— 文字是画在条形上、或紧贴条形画的。把它
挂在行距上，等于让一条画得细的条形和一条两倍高的条形报同一个字号。

**第二条规则：名字能用的是画面左边到绘图区，不只是那条栏。** 名字是右对齐画在条形
起点左边的，所以它们末端对齐、各自往左伸手，而条形榜的这个渲染器左边没有 Y 轴 ——
那条边距是空的。原先只给 176−24=152，而港股榜最长的名字（中国石油化工股份）是八个
字、在 32.7 字号下约 261 基线像素，于是**整列被压到 19** —— 连 腾讯 和 美团 一起 ——
只为让一个名字留在一条它本来不必留在里面的带子里。三条规则合起来：

    市场     旧      新
    A股      24.1    32.7
    美股     24.1    32.7
    港股     15.8    32.7      ← 整列被最长名字压掉的那一条

**为什么必须上真机量。** 字号不是控件属性，是渲染器算出来的一个数；预览画布在 UIA
树里没有节点（画布上的字只能靠像素）。能拿到它的只有像素：条形的色块高度（鲜艳像素
的行段）、行距（行段中心的间距）、名字的字高（左栏里又亮又不鲜艳的像素）。

判据是**比值**，不是像素数：截图大小随窗口变，比值不随。旧规则下 字高/行距 ≈ 0.275、
字高/条形 ≈ 0.43；新规则下 0.373 / 0.583（字高量的是墨迹，汉字墨迹约占字号的 0.8）。

用法：python tools/verify-racelabel.py
"""
import importlib.util
import os
import re
import sys
import time
from pathlib import Path

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

REPO = Path(__file__).resolve().parent.parent
RENDERER = REPO / "src/MarketMotionStudio/Render/SectorRaceRenderer.cs"
BARRACE = REPO / "src/MarketMotionStudio/Render/BarRaceRenderer.cs"
UNDERWATER = REPO / "src/MarketMotionStudio/Render/UnderwaterRenderer.cs"
INK = REPO / "src/MarketMotionStudio/Render/Ink.cs"

PASSED = []
FAILED = []


def check(name, ok, note=""):
    (PASSED if ok else FAILED).append(name)
    print(("  √ " if ok else "  × ") + name + (f" — {note}" if note else ""))


def report():
    print(f"\n{len(PASSED)}/{len(PASSED) + len(FAILED)} 通过")

    return 0 if not FAILED else 1


def read(path):
    return path.read_text(encoding="utf-8")


# ---- 源码级：规则本身 -------------------------------------------------------------

def source_checks():
    renderer = read(RENDERER)
    ink = read(INK)

    check("字号挂在条形上，不再挂在行距上",
          "var nameSize = Math.Min(LabelCap, (barH / context.Scale) * LabelOfBar);" in renderer,
          "渲染器里那一行")

    # 旧规则必须真的走了：留着它，新规则会被下一次改动悄悄绕过。
    check("旧的「行距 × 0.34」已经不在了", "* 0.34" not in renderer)

    check("上限从 30 提到 36", "private const double LabelCap = 36;" in renderer)
    check("字号占条形的比例是 0.72", "private const double LabelOfBar = 0.72;" in renderer)

    # 字号要在进循环**之前**算一次：一面榜上每行一个字号，读起来像勒索信而不是清单。
    loop = renderer.find("foreach (var k in order)")
    check("字号在进循环之前算一次（不是逐行算）",
          loop > 0 and 0 < renderer.find("var nameSize =") < loop
          and "nameSize" not in renderer[loop:])

    # 名字栏按最长名字定宽。150 是「能源 / 材料」时代的宽度。
    check("名字栏宽到装得下最长的那家", "private const double GutterLeft = 176;" in renderer)

    # 第二条规则：名字能用的宽度是**画面左边到绘图区**，不是那条 176 的栏。
    check("名字能用的是画面左边到绘图区，不只是那条栏",
          "var room = x0 - context.Px(NameRightGap) - context.Px(NameEdgeInset);" in renderer)
    check("旧的那条「栏宽减 24」不在了（减的是 Margins.Left，而那条边距是空的）",
          "GutterTextInset" not in renderer)

    # 画与量必须是同一个数，否则「量出来的宽度」和「画出来的位置」会各自漂移。
    check("绘制与测量共用同一个右边距",
          "x0 - context.Px(NameRightGap)" in renderer
          and "private const double NameRightGap = 14;" in renderer)
    check("最长名字离画面左边缘还留着一点", "private const double NameEdgeInset = 16;" in renderer)

    check("条内标注的墨色按条形自己的颜色挑", "Ink.OnTopOf(colour)" in renderer)
    check("涨跌着色的榜不跟着换墨色（颜色就是意思）",
          "ColourBySign" in renderer and "insideInk" in renderer)
    check("浅色条配深色字，阈值是 WCAG 亮度 0.30", "luminance > 0.30 ? LabelOnLight" in ink)

    # 名字一律亮白：淡蓝 #C9D8F5 在预览的三分之一缩放下读成灰。冠军行另有光晕，不靠墨色。
    check("名字一律亮白，冠军只靠光晕",
          "var nameColour = Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF);" in renderer)
    check("旧的淡蓝名字已经不在（#C9D8F5）", "0xC9, 0xD8, 0xF5" not in renderer)

    # 成交额页是时间轴柱状图，没有行名字；那边对应的字是贴在柱子上的极值标注。
    bar_race = read(BARRACE)
    check("成交额页的极值标注也是亮白（颜色留在外框上）",
          "strong,\n            Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF), a);" in bar_race)

    # 回撤与修复页是同一个名字栏，而且是旧规则的原样副本：它的行数由自选清单决定（3 到 16），
    # 三条规则在这一页更该生效。
    under = read(UNDERWATER)
    check("回撤与修复页的字号也挂在行自己的带子上",
          "var nameSize = Math.Min(LabelCap, (band / context.Scale) * LabelOfBand);" in under)
    check("回撤与修复页旧的「行距 × 0.34」不在了", "* 0.34" not in under)
    check("回撤与修复页的名字能用画面左边到绘图区",
          "var room = x0 - context.Px(NameRightGap) - context.Px(NameEdgeInset);" in under)
    check("回撤与修复页的名字也是亮白", "0xC9, 0xD8, 0xF5" not in under
          and "Color.FromArgb(0xFF, 0xFF, 0xFF, 0xFF), intro);" in under)


# ---- 像素：把画面上的字量出来 ------------------------------------------------------

def shot(win, name):
    path = os.path.join(REPO, "artifacts", name)

    # 先把窗口提到最前再截：截图截的是**屏幕上看得见的东西**，而姊妹工程是同一套外壳、
    # 同一个窗口标题，它开着就会盖在预览上，量出来的「字高」是另一个应用的字。
    try:
        win.SetActive()
        time.sleep(0.4)
        win.SetTopmost(True)
        time.sleep(0.8)
    except Exception:  # noqa: BLE001
        pass

    win.CaptureToImage(path)

    try:
        win.SetTopmost(False)
    except Exception:  # noqa: BLE001
        pass

    return path


def bar_bands(image):
    """画面里每一条条形占的行区间。

    条形是**鲜艳**的（饱和度高的色块），而这个应用的窗口本身是灰的、导航图标是灰的、
    状态条是浅绿的。所以先按列数鲜艳像素，取最密的那个列区间 —— 条形都从同一个起点长
    出来，那里是竖着穿过所有条形的位置 —— 再在该区间里按行数，找连续的行段。

    然后过两遍筛：
    - **按中位高度**：播放进度条也是鲜艳的，但它只有几像素高。
    - **按行距连成链**：表头底下有一小段鲜艳的装饰，它和第一行之间隔着半屏；只留间距
      一致的那条最长的链，才不会把它当成一行。
    """
    width, height = image.size
    pixels = image.load()

    def vivid(x, y):
        r, g, b = pixels[x, y]

        return max(r, g, b) - min(r, g, b) > 60 and max(r, g, b) > 90

    columns = [sum(1 for y in range(0, height, 3) if vivid(x, y)) for x in range(width)]
    widest = max(columns)

    if widest <= 4:
        return None, []

    band = [x for x, count in enumerate(columns) if count > widest * 0.5]

    if not band:
        return None, []

    left, right = band[0], band[-1]
    across = [sum(1 for x in range(left, right + 1, 3) if vivid(x, y)) for y in range(height)]

    bands = []
    current = None

    for y, count in enumerate(across):
        if count >= 2:
            if current is None:
                current = [y, y]
            elif y - current[1] <= 2:
                current[1] = y
            else:
                bands.append(tuple(current))
                current = [y, y]
        elif current is not None and y - current[1] > 2:
            bands.append(tuple(current))
            current = None

    if current is not None:
        bands.append(tuple(current))

    if len(bands) < 5:
        return (left, right), bands

    heights = sorted(b[1] - b[0] + 1 for b in bands)
    median = heights[len(heights) // 2]
    bands = [b for b in bands if median * 0.65 <= b[1] - b[0] + 1 <= median * 1.35]

    return (left, right), longest_run(bands)


def glyph_pixels(pixels, left, y0, y1, reach=96):
    """条形左边那一栏里的名字：紧贴着条形、又亮又不鲜艳的一串像素。

    窗口**必须从条形往左数起**，不能用画面的百分比：预览画布只占窗口的一小半，而窗口
    右边还坐着整个设置面板，按百分比开窗会把面板上的亮像素（滑块、按钮、数字框）当成
    字读进来 —— 读到的「字高」就等于条形高，两条比值全成 1.000。

    墨迹是实心的：名字的墨色变了，但每一扫描行的最亮值仍然恒定 —— 亮白是 255，旧淡蓝
    #C9D8F5 是 201。所以既能量高度，也能一眼看出是哪一种墨色。返回 (行, 最右, 最亮值)。
    """
    rows = []
    right = 0
    top = 0

    for y in range(y0, y1):
        n = 0
        gap = 0
        x = left - 2

        while x >= 0 and left - x <= reach:
            r, g, b = pixels[x, y]

            if min(r, g, b) > 120 and max(r, g, b) - min(r, g, b) < 70:
                n += 1
                gap = 0
                top = max(top, min(r, g, b))
                right = max(right, x)
            elif n and gap > 4:
                break
            else:
                gap += 1

            x -= 1

        if n >= 2:
            rows.append(y)

    return rows, right, top


def value_pixels(pixels, left, right, y0, y1, pad=24, reach=70):
    """条形右端那一串数值的墨迹行。

    数值用的是**没有压过**的字号（valueFormat 直接吃 nameSize），名字用的是压进可用宽度
    之后的字号。所以这两个墨迹高的比，就是「整列被压掉了多少」。

    只扫右端 70 像素、并且跳过条形最左那 24 像素：条形是一道从 alpha 0.55 开始的渐变，
    它**暗的一端在左**，一路扫过去会把那截暗色块当作墨迹，于是「字高」等于条形高 ——
    这正是第一版量出「数值 16px」的原因（条形本身才 16px）。
    """
    rows = []
    floor = max(left + pad, right - reach)

    for y in range(y0, y1):
        n = 0
        x = right

        while x >= floor:
            r, g, b = pixels[x, y]

            # 墨色要么是很亮的白（压在深色条上），要么是很暗的深蓝（压在浅色条上）。
            if (min(r, g, b) > 200 and max(r, g, b) - min(r, g, b) < 40) or max(r, g, b) < 60:
                n += 1

            x -= 1

        if n >= 2:
            rows.append(y)

    if not rows:
        return 0

    span = rows[-1] - rows[0] + 1

    # 一条条的整段都被当成字，说明读到的是条形自己，不是字。
    return 0 if span >= (y1 - y0) else span


def longest_run(bands, slack=0.35):
    """一串带子里间距一致、且最长的那一段。

    一根灰条就能把整串切开：灰不满足「鲜艳」，灰条那一行在按条形数出来的带子里就是一处
    断口。所以名字要在**整幅画面**上扫，再按间距取最长的一段 —— 若把扫描区间交给条形定，
    灰条后面的那些行照样扫不到（港股榜十五行，扫出来八行）。
    """
    if len(bands) < 3:
        return bands

    centers = [(b[0] + b[1]) // 2 for b in bands]
    gaps = [centers[i + 1] - centers[i] for i in range(len(centers) - 1)]
    pitch = sorted(gaps)[len(gaps) // 2]

    best = run = [bands[0]]

    for i, gap in enumerate(gaps):
        if pitch * (1 - slack) <= gap <= pitch * (1 + slack):
            run.append(bands[i + 1])
        else:
            if len(run) > len(best):
                best = run
            run = [bands[i + 1]]

    return run if len(run) >= len(best) else best


def name_rows(pixels, left, y0, y1, reach=96):
    """按**名字**数行，不按条形数行。

    调色板里有一半是灰的，而灰不满足「鲜艳」——按条形数行会漏掉灰条那几行（A 股榜十五行
    数出来十三行，港股榜数出来八行）。名字是亮白的、每行都有一条、且紧贴着条形的左端，所以
    在条形占的那段纵向区间里按名字数，数出来的才是这块榜到底画了几行。

    reach 的上限是**画布的左缘**，不是「往左多少像素」：窗口左边坐着设置面板，探出去就会
    读到面板上一条竖着的亮带，于是每一行都有 24 个「墨迹像素」、十五行连成一段。
    """
    rows = []
    cur = None

    for y in range(max(0, y0), y1 + 1):
        n = 0
        x = left - 2

        while x >= 0 and left - x <= reach:
            r, g, b = pixels[x, y]

            if min(r, g, b) > 120 and max(r, g, b) - min(r, g, b) < 70:
                n += 1

            x -= 1

        if n >= 2:
            cur = [y, y] if cur is None else [cur[0], y]
        elif cur is not None and y - cur[1] > 3:
            rows.append(tuple(cur))
            cur = None

    if cur is not None:
        rows.append(tuple(cur))

    return [r for r in rows if r[1] - r[0] >= 2]


def measure(win, name):
    from PIL import Image

    path = shot(win, name)
    image = Image.open(path).convert("RGB")
    pixels = image.load()

    (left, right), bands = bar_bands(image)

    if not bands or len(bands) < 5:
        return None, f"没找到条形（{len(bands) if bands else 0} 段）"

    heights = sorted(b[1] - b[0] + 1 for b in bands)
    centers = [(b[0] + b[1]) // 2 for b in bands]
    gaps = sorted(centers[i + 1] - centers[i] for i in range(len(centers) - 1))

    bar = heights[len(heights) // 2]
    row = gaps[len(gaps) // 2]

    # 名字在条形左边那一栏，右对齐贴着条形。窗口上下各放 4 像素：墨迹是垂直居中的，
    # 但取整会让它探出条形一两个像素；4 小于行距与条形之差的一半，探不到邻行。
    glyphs = []
    values = []
    text_right = 0
    text_top = 0

    for band in bands:
        rows, right_edge, top = glyph_pixels(pixels, left, band[0] - 4, band[1] + 5)

        if rows:
            glyphs.append(rows[-1] - rows[0] + 1)
            text_right = max(text_right, right_edge)
            text_top = max(text_top, top)

        y = (band[0] + band[1]) // 2
        x = right

        while x >= left and not (max(pixels[x, y]) - min(pixels[x, y]) > 60
                                 and max(pixels[x, y]) > 90):
            x -= 1

        value = value_pixels(pixels, left, x, band[0], band[1] + 1)

        # 短条的数值画在条形外面，量不到就算了 —— 它不是这条断言要看的东西。
        if value:
            values.append(value)

    if not glyphs:
        return None, "名字那一栏一个亮的字都没读到"

    glyphs.sort()
    values.sort()

    named = longest_run(name_rows(pixels, left, 0, image.size[1] - 1))

    return {
        "path": path,
        "rows": len(named) if named else len(bands),
        "bar_rows": len(bands),
        "bar": bar,
        "row": row,
        "text": glyphs[len(glyphs) // 2],
        "text_rows": glyphs,
        "ink": text_top,
        "value": values[len(values) // 2] if values else 0,
        "values": values,
        "gap": left - text_right,
    }, ""


# ---- 真机：跑起来量 ---------------------------------------------------------------

def texts(root, depth=0, limit=25, out=None):
    out = [] if out is None else out

    if depth > limit:
        return out

    for child in root.GetChildren():
        if child.Name:
            out.append(child.Name)

        texts(child, depth + 1, limit, out)

    return out


def board(win, shot_name):
    """切到市值榜、取数、拖到最后一帧，量一次。返回量到的数。"""
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "市值榜")

    if item is None:
        return None, "导航里没有「市值榜」"

    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)

    button = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if button is None:
        return None, "没有取数按钮"

    button.GetInvokePattern().Invoke()

    # 取数要问一次榜单再加每只标的的月线，慢慢等；状态行的消息有两个空串节点要跳过。
    said = ""
    deadline = time.time() + 600

    while time.time() < deadline:
        status = winui.find(win, lambda c: c.AutomationId == "Status")

        if status is not None:
            parts = [t for t in texts(status) if t.strip()]

            if len(parts) >= 3:
                said = " ".join(parts[2:])

                if "期" in said or re.search(r"失败|错误|无法|异常", said):
                    break

        time.sleep(3)

    if "期" not in said:
        return None, f"取数没回来：{said[:60]}"

    # 拖到最后一帧：动画开头只有表头，条形是长出来的。进度条的值域是 0–1。
    slider = winui.find(win, lambda c: c.AutomationId == "Scrub")

    if slider is not None:
        slider.GetRangeValuePattern().SetValue(1.0)
        time.sleep(2.0)

    got, why = measure(win, shot_name)

    return (got, said) if got else (None, why)


def load_set_market():
    spec = importlib.util.spec_from_file_location("set_market", REPO / "tools" / "set-market.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


MARKETS = ("A股", "港股", "美股")

# 截图文件名用拉丁字母：中文文件名在几个 shell 之间转手会变成乱码。
MARKET_FILES = {"A股": "cn", "港股": "hk", "美股": "us"}


def current_market(win):
    """Which market the app is set to, read off the settings page's combo.

    `set_market.market_value` reads the ComboBox's Value pattern, which is empty on this control,
    so it answers `None` — and `None` is indistinguishable from "there is no preference to put
    back", which is how a run that switched to 港股 left the app sitting on it. The selection is
    on the popup's items, so the popup has to be opened and the items walked.
    """
    settings = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "设置")

    if settings is None:
        return None

    settings.GetSelectionItemPattern().Select()
    time.sleep(2.0)

    combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo")

    if combo is None:
        return None

    combo.GetExpandCollapsePattern().Expand()
    time.sleep(1.2)

    found = None

    for root in auto.GetRootControl().GetChildren():
        for name in MARKETS:
            item = winui.find(root, lambda c, n=name: (  # noqa: B023 - n is bound per call
                c.ControlTypeName == "ListItemControl" and c.Name == n), limit=8)

            if item is not None and item.GetSelectionItemPattern().IsSelected:
                found = name
                break

        if found:
            break

    try:
        combo.GetExpandCollapsePattern().Collapse()
    except Exception:  # noqa: BLE001
        pass

    return found


def switch_market(wanted):
    """换市场并重启：市场是一个启动时才读的持久偏好。"""
    helper = load_set_market()
    win = helper.window()

    if win is None:
        win = helper.launch()

    if win is None:
        return None

    win.SetActive()
    time.sleep(1.0)

    settings = helper.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "设置")

    if settings is None:
        return None

    settings.GetSelectionItemPattern().Select()
    time.sleep(2.0)

    combo = helper.find(win, lambda c: c.AutomationId == "MarketCombo")

    if combo is None:
        return None

    combo.GetExpandCollapsePattern().Expand()
    time.sleep(1.2)

    picked = None

    for root in auto.GetRootControl().GetChildren():
        picked = helper.find(root, lambda c: c.ControlTypeName == "ListItemControl"
                             and c.Name == wanted, limit=8)
        if picked is not None:
            break

    if picked is None:
        return None

    picked.GetSelectionItemPattern().Select()
    time.sleep(1.5)

    helper.kill()

    return helper.launch()


def live_checks():
    # 姊妹工程先关掉：两个应用同壳同名，它的窗口会盖在预览画布上，而截图截的是屏幕上
    # 看得见的东西。
    winui.kill("WorldMotionStudio.exe")

    win = winui.launch(winui.EXE)

    if win is None:
        check("应用起得来", False, "没有窗口")
        return None, 0

    check("应用起得来", True)

    win.SetActive()
    time.sleep(1.5)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass

    original = current_market(win)

    if original is None:
        check("读得到当前市场（跑完要还原）", False, "读不到，跑完可能把市场留在港股")
    else:
        check("读得到当前市场（跑完要还原）", True, original)

    got, said = board(win, "verify-racelabel.png")

    if got is None:
        check("量到了画面上的字", False, said[:70])
        return original, 0

    check("取数回来了", True, said[:70])
    check("量到了画面上的字", True,
          f"{got['rows']} 行 · 条形 {got['bar']}px · 行距 {got['row']}px · "
          f"字高 {got['text']}px · 条内数值 {got['value']}px")

    check("市值榜画满十五行", got["rows"] == 15,
          f"{got['rows']} 行（按名字数；鲜艳条形只有 {got['bar_rows']} 段）")

    # 名字的墨色：亮白的最亮值是 255，旧淡蓝 #C9D8F5 是 201 —— 一眼能分开。
    check("名字是亮白，不是旧的淡蓝", got["ink"] >= 240,
          f"墨色最亮值 {got['ink']}（白 255 / 旧淡蓝 201）")

    ratio_row = got["text"] / got["row"]
    ratio_bar = got["text"] / got["bar"]

    # 字高量的是字的**墨迹**高，不是字号：汉字墨迹约占字号的 0.8。旧规则（字号 = 行距
    # × 0.34）落到这里约 0.275，新规则（字号 = 条形 × 0.72）约 0.373。
    check("字高/行距 ≥ 0.34（旧规则约 0.275）", ratio_row >= 0.34, f"{ratio_row:.3f}")

    # 字号是条形的 0.72，墨迹就是条形的约 0.58；旧规则约 0.43。
    check("字高/条形在 0.50–0.85 之间（旧规则约 0.43）",
          0.50 <= ratio_bar <= 0.85, f"{ratio_bar:.3f}")

    # 名字用的是压进可用宽度之后的字号，条内数值用的是没压过的。两者一样高，就说明
    # 最长的名字没有把整列拖小。
    if got["value"]:
        check("名字没有被最长的那个名字压小", got["text"] >= got["value"] - 1,
              f"名字 {got['text']}px · 数值 {got['value']}px")
    else:
        check("名字没有被最长的那个名字压小", False, "没量到条内数值")

    # 名字栏加宽是为了让大字装得下；装不下的表现为名字贴到条形上，而这一条在截图里
    # 看得见却没有断言看着：文字与色块之间那道缝就是判据。
    check("名字没有贴到条形上", got["gap"] >= 3, f"缝 {got['gap']}px")

    return original, got["text"]


def other_checks(other, first_text, first_market):
    """再量一个市场：这次改动里「名字能用画面左边到绘图区」这条，只有跨市场才量得出差别。

    港股榜最长的是八个字（中国石油化工股份），美股榜最长的是五个（埃克森美孚），A 股榜最长
    的是四个。旧规则把整列压到 176−24=152 能装下的尺寸，于是港股榜的字只有 A 股榜的六成；
    现在三个市场都该是同一个字号。

    哪个市场当「另一个」取决于进来时是哪个 —— 如果进来就是港股，就去量美股，否则去量港股。
    """
    win = switch_market(other)

    if win is None:
        check(f"切到{other}榜", False, "没切过去")
        return

    got, said = board(win, f"verify-racelabel-{MARKET_FILES[other]}.png")

    if got is None:
        check(f"{other}榜量到了画面上的字", False, said[:70])
        return

    check(f"{other}榜量到了画面上的字", True,
          f"{got['rows']} 行 · 条形 {got['bar']}px · 行距 {got['row']}px · 字高 {got['text']}px")

    check(f"{other}榜的字和{first_market}榜一样大（最长的名字不再拖小整列）",
          abs(got["text"] - first_text) <= 1,
          f"{other} {got['text']}px · {first_market} {first_text}px")


def main():
    source_checks()
    original, first_text = live_checks()

    if first_text:
        other_checks("美股" if original == "港股" else "港股", first_text, original or "起始市场")

    # 脚本动了哪个偏好，最后要改回原样：市场是一个启动时才读的持久偏好。无条件还原 ——
    # 只要最后一次测量不是原市场，应用就停在别处，「是港股就不还原」正好漏掉这一种。
    if original:
        switch_market(original)
        check("市场还原回 " + original, True)

    print("\n看画面：artifacts/ · verify-racelabel-*.png")

    return report()


if __name__ == "__main__":
    sys.exit(main())
