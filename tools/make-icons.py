# -*- coding: utf-8 -*-
"""画出导航栏那十六个页面的图标，并生成 `Themes/Icons.xaml`。

为什么要有这个脚本
------------------
导航原先用的是 `Segoe Fluent Icons` 里的字形，而字形是**有限的一袋**：十六页里有三对
页面被分到了同一个字形 —— K线与行业板块竞速（`E9E9`）、成交量换手率与持有胜率
（`E9D2`）、成交额与持仓收益（`E9D9`）。一个字形说不了两个页面，于是"图标不代表
页面意思"不是审美问题，是**重号**问题。

为什么是脚本而不是手写路径
--------------------------
每个图标都是**描边骨架**（线、圆环、折线、箭头），不是手写的填充轮廓 —— 描边要变成
`PathIcon` 能用的填充几何，得先把每条线沿两侧外扩、在拐角与端点补圆头，再求并集。
手算这个等于手算偏置曲线，必然出错。这里交给 shapely：`buffer(w/2, round, round)` 就是
"沿这条线刷一层半笔宽"，`unary_union` 就是"把重叠的几笔合成一个形状"。

于是绘图写法可以保持成它本来的样子：`line(...)`、`ring(...)`、`arrow(...)`，坐标就是
20×20 网格上的坐标。

两条不能忘的规矩
----------------
1. **每幅图都装在一个共同的方框里。** `PathIcon` 用的是 `Viewbox Stretch="Uniform"`，
   它把几何的**包围盒**缩放去填满图标格 —— 也就是说，一幅宽扁的图会被缩小，一幅
   瘦高的图会被放大，两个图标并排就不再是一个字号。所以每幅图都额外带两个
   **定位点**（`(2,2)` 与 `(18,18)` 上各一个 0.03 单位的方点），把包围盒钉死成
   `[2,18]²`。0.03 单位在 16px 上不到百分之三像素，看不见，但足以让包围盒存在。
   于是"设计区域是 16×16，居中，四周留 2 单位"成了每幅图共享的事实。
2. **几何一律只用 `M`/`L`/`Z`。** 圆、弧、圆角都在这里被离散成折线 —— 曲线命令
   （`A`/`C`）在 XAML 的路径小语言里能用，但没有必要，而且折线在 16px 下与曲线
   无从分辨。

用法
----
    python tools/make-icons.py            # 生成 XAML + SVG + 预览图
    python tools/make-icons.py --check    # 只校验（不许改包围盒、不许重号）

产物
----
- `src/MarketMotionStudio/Themes/Icons.xaml` —— 16 条 `PathGeometry`
- `artifacts/icons/*.svg` —— 每幅一张，供帮助文档或别处引用
- `artifacts/icons/sheet-light.png` / `sheet-dark.png` —— 16/24/48px 三档总览
- `artifacts/icons/nav-light.png` / `nav-dark.png` —— 按导航顺序排的模拟列表
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

REPO = Path(__file__).resolve().parent.parent
XAML = REPO / "src/MarketMotionStudio/Themes/Icons.xaml"
SVGS = REPO / "artifacts/icons"

GRID = 20.0          # 设计网格
BOX0, BOX1 = 2.0, 18.0   # 共同方框（定位点所在）
STROKE = 1.6         # 主笔宽，与 Segoe Fluent 的线性字形相当
# 定位点的边长。0.12 而不是更小：路径数据按一位小数落盘，比 0.05 小的东西会被
# 四舍五入抹成一个点（第一版就是 0.03，于是十六幅图的包围盒一个都没被钉住 ——
# 而"没钉住"在截图里看不出来，因为图标照样画得出来）。0.12 单位在 16px 上不到
# 百分之一个像素。
MARK = 0.12
QUAD = 6             # 圆被离散成每象限几段


# ---------------------------------------------------------------- 画笔

def stroke(points, w=STROKE):
    return LineString([(float(x), float(y)) for x, y in points]).buffer(
        w / 2.0, quad_segs=QUAD, cap_style="round", join_style="round")


def line(x0, y0, x1, y1, w=STROKE):
    return stroke([(x0, y0), (x1, y1)], w)


def polyline(points, w=STROKE):
    return stroke(points, w)


def ring(cx, cy, r, w=STROKE):
    """圆环：外圆减内圆。"""
    return Point(cx, cy).buffer(r, quad_segs=QUAD * 2).difference(
        Point(cx, cy).buffer(r - w, quad_segs=QUAD * 2))


def dot(cx, cy, r):
    return Point(cx, cy).buffer(r, quad_segs=QUAD * 2)


def box(x0, y0, x1, y1, w=STROKE, r=0.0):
    """描边的矩形；r > 0 时四角带圆角。"""
    rect = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    if r > 0:
        rect = rect.buffer(-r, join_style="round").buffer(r, join_style="round")

    return rect.exterior.buffer(w / 2.0, quad_segs=QUAD*2, cap_style="round", join_style="round")


def square(cx, cy, side, r=0.3):
    """实心小方（收益矩阵用），四角略圆。"""
    h = side / 2.0
    return Polygon([(cx - h, cy - h), (cx + h, cy - h),
                    (cx + h, cy + h), (cx - h, cy + h)]).buffer(
        r, quad_segs=QUAD, join_style="round")


def at(cx, cy, deg, r):
    """数学角度的落点：0°是右，90°是上（屏幕坐标 y 向下）。"""
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy - r * math.sin(a))


def arc(cx, cy, r, a0, a1, w=STROKE):
    """弧，从 a0 扫到 a1（可为负、可跨 0），按方向采点。"""
    n = max(6, int(abs(a1 - a0) / 6) + 4)
    pts = [at(cx, cy, a0 + (a1 - a0) * i / n, r) for i in range(n + 1)]
    return stroke(pts, w)


def head(tip, deg, length=2.2, spread=30.0, w=STROKE):
    """箭头：两笔从箭尖往回斜挑。deg 是箭尖指向（数学角度）。"""
    return unary_union([
        stroke([tip, at(tip[0], tip[1], deg + 180 + s, length)], w)
        for s in (-spread, spread)])


def arc_arrow(cx, cy, r, a0, a1, w=STROKE, length=2.0, spread=34.0):
    """一段弧，末端带一个顺着弧走的箭头（箭尖落在弧的端点上）。"""
    end = at(cx, cy, a1, r)
    back = at(cx, cy, a1 - math.copysign(2.0, a1 - a0), r)
    deg = math.degrees(math.atan2(-(end[1] - back[1]), end[0] - back[0]))

    return unary_union([arc(cx, cy, r, a0, a1, w),
                        head(end, deg, length, spread, w)])


def arrow(x0, y0, x1, y1, length=2.2, spread=30.0, w=STROKE, tail=True):
    """带箭头的直线。"""
    deg = math.degrees(math.atan2(-(y1 - y0), x1 - x0))
    parts = [head((x1, y1), deg, length, spread, w)]

    if tail:
        parts.append(line(x0, y0, x1, y1, w))

    return unary_union(parts)


# ---------------------------------------------------------------- 十六幅图
#
# 每一幅都写清它替的是哪一页、为什么是这个形状。形状本身是给 16px 看的：
# 细节超过三处就会糊成一团，所以宁可少画。

def icon_turnover():
    """成交额：四根高低不齐的柱子 —— 全市场一天的成交，以金额计。

    不画基线、不画箭头，只靠四根柱子的**参差**说"很多标的、合起来一天"。
    这是唯一一副纯柱状图（成交量换手率那幅上面还压着一个环），所以不会混。
    """
    tops = [11.2, 6.8, 12.6, 4.6]
    return [stroke([(x, t), (x, 17.0)], 1.9)
            for x, t in zip((4.9, 8.3, 11.7, 15.1), tops)]


def icon_candle():
    """K线：两根蜡烛，一高一矮，影线穿过实体。

    蜡烛的实体画成**空心**矩形、影线细一点，形状本身就与"柱子"分得开：
    柱子的两端是圆的，蜡烛的两端是尖的（影线）。
    """
    return [
        line(6.3, 3.4, 6.3, 16.6),
        box(4.7, 6.6, 7.9, 13.4),
        line(13.7, 5.8, 13.7, 15.2),
        box(12.1, 8.8, 15.3, 12.2),
    ]


def icon_volume():
    """成交量换手率：两根柱子，上面扣一个带箭头的环。

    环是"换手"（份额在转手），柱子是"量"。它与成交额那幅的区别就在这个环 ——
    两页在导航里挨得不远，这是有意让它们长得不一样。

    环画得比"好看"该有的尺寸更大：16px 上环的洞只有 1px 时，环与箭头会糊成
    一个斑点，而一个斑点什么也不说。
    """
    parts = [stroke([(x, t), (x, 17.0)], 1.9)
             for x, t in zip((5.3, 9.9, 14.5), (13.2, 11.4, 9.8))]

    # 环：缺口留在正上方，箭尖落在缺口的右端，顺着弧走进缺口。
    parts.append(arc_arrow(10.0, 7.2, 3.6, -250.0, 50.0, length=2.4, spread=38.0))

    return parts


def icon_sector_race():
    """行业板块竞速：一块仪表，指针偏右。

    "竞速"这一层意思用速度表说，比再画一组横条好 —— 横条在这套图标里已经
    被成交额与市值榜占了，多一副就又开始重号。
    """
    cx, cy, r = 10.0, 14.4, 6.8
    return [
        arc(cx, cy, r, 180.0, 0.0),
        line(cx, cy, at(cx, cy, 52.0, 3.9)[0], at(cx, cy, 52.0, 3.9)[1]),
        dot(cx, cy, 1.0),
    ]


def icon_market_cap():
    """市值榜：领奖台 —— 三块高低不同的台子站在一条基线上。

    基线是它与成交额那幅的分别：成交额是四根柱子悬着，市值榜是"名次"落在
    地上。台子的宽窄一致、高低不同，就是"榜"。
    """
    return [
        line(3.2, 17.0, 16.8, 17.0),
        box(3.4, 12.4, 6.6, 17.0),
        box(8.4, 9.0, 11.6, 17.0),
        box(13.4, 13.6, 16.6, 17.0),
    ]


def icon_ah_premium():
    """AH 溢价：两个同大的圆环，上面一个双向箭头。

    两个环 = 同一家公司的两个上市地；双向箭头 = 两者之间的价差。这是页面上
    唯一需要第二个市场才有意义的东西，所以图上也正好是"两样东西在比"。
    """
    return [
        ring(6.3, 11.4, 3.3),
        ring(13.7, 11.4, 3.3),
        arrow(6.6, 5.0, 13.4, 5.0, length=2.1, spread=28),
    ]


def icon_extreme_days():
    """极端交易日：一道闪电。

    那一页的行是"某一天涨跌多少"，榜首是二十年里最猛的一天 —— 一根尖的，
    不是一根高的。实心闪电也是这套线性图标里唯一的实心块面，一眼就认得。
    """
    return [Polygon([(12.0, 2.8), (5.8, 10.9), (9.8, 10.9),
                     (8.0, 17.2), (14.2, 9.1), (10.2, 9.1)])]


def icon_fx_corridor():
    """汇率走廊：上下两条平行线夹着一个点。

    这一页的行**是范围不是量**：两端是区间最低与最高，游标是现价。两条线加
    一个点就是这句话本身，别处没有第二幅这样画的。
    """
    return [
        line(3.0, 6.2, 17.0, 6.2),
        line(3.0, 13.8, 17.0, 13.8),
        dot(11.2, 10.0, 1.6),
    ]


def icon_index_race():
    """指数长跑：一条中途有回撤、整体向上的折线，箭头落在末端。

    行是"从自己第一个月起的累计涨幅"，所以是线不是柱；箭头表示长跑的方向。
    中途那个小回落是故意留的 —— 一条笔直上升的线看着像示意，不像指数。
    """
    return [arrow(3.0, 16.0, 16.4, 4.4, length=2.6, spread=30,
                  tail=False),
            polyline([(3.0, 16.0), (6.4, 12.4), (9.0, 14.2),
                      (12.8, 7.8), (16.4, 4.4)])]


def icon_asset_race():
    """大类资产：一块三等分的饼。

    饼 = 资产配置。三条半径的角度特意避开 90°/210°/330° —— 那个朝向在 16px 上
    读出来是奔驰标，而这里要说的是"分成几类"，不是某个牌子。与持有胜率那幅
    （同心环 + 心）也分得开：那幅是从外往里的圈，这幅是从圆心往外切。
    """
    cx, cy, r = 10.0, 10.0, 6.2
    parts = [ring(cx, cy, r)]

    for deg in (15.0, 135.0, 255.0):
        parts.append(line(cx, cy, at(cx, cy, deg, r)[0], at(cx, cy, deg, r)[1]))

    return parts


def icon_drawdown():
    """回撤与修复：一条水位线，线下一块凹下去的面积。

    这一页的行**就是**这么画的：从 0 轴往下扎的填充曲线。所以图标也照这个样子
    来，而不是画一条折线 —— 折线版本先是被画成"下探再拉起"，而那个形状在 16px
    上就是一个对勾，对勾说的是"成功"，正好把页面的意思说反了。
    """
    level = 6.6
    curve = [(3.0, level), (5.8, 9.8), (8.2, 14.6), (10.6, 15.8),
             (13.0, 13.0), (15.0, 9.4), (17.0, level)]

    return [line(3.0, level, 17.0, level), Polygon(curve)]


def icon_hold_odds():
    """持有胜率：靶心。

    胜率是"打中没打中"，靶心是它最短的说法。三圈（外圈、内圈、心）在 16px 上
    仍然分得清，是因为它们足够大：外圈直径接近设计区的四分之三。
    """
    return [ring(10.0, 10.0, 6.0), ring(10.0, 10.0, 3.3), dot(10.0, 10.0, 1.2)]


def icon_matrix():
    """收益矩阵：九个实心小方。

    矩阵就是格子。实心而不是描边：16px 上描边的小方格之间的缝只有半个像素，
    九个连成一片糊。九个小方之间的缝有一点四个单位，看得见。
    """
    parts = []

    for row in range(3):
        for col in range(3):
            parts.append(square(4.25 + col * 4.4 + 1.35, 4.25 + row * 4.4 + 1.35, 2.7))

    return parts


def icon_gain_calendar():
    """涨跌日历：一个日历，里面一支向上的箭、一支向下的箭。

    日历就是日历 —— 那一页的行是"某一天的涨跌"，横轴是月份，日历是最短的
    说法。里面的上下箭头是它与定投计划（日历里一个加号）的分别。
    """
    parts = [
        box(3.2, 4.8, 16.8, 17.0, r=1.4),
        line(3.2, 8.4, 16.8, 8.4),
        line(6.6, 3.2, 6.6, 5.6),
        line(13.4, 3.2, 13.4, 5.6),
    ]
    parts.append(arrow(7.6, 15.2, 7.6, 11.0, length=1.9, spread=30))
    parts.append(arrow(12.4, 11.0, 12.4, 15.2, length=1.9, spread=30))

    return parts


def icon_dca_plan():
    """定投计划：三级台阶。

    定投的意思是"每隔一段固定时间买入固定金额"，所以形状要说的是**等距的几段**，
    不是"钱"。台阶正好：每一级是一次买入，级与级之间的高度是它换来的东西，整段
    是往上走的。

    它本来与涨跌日历共用日历外形（里面一个加号），后来换掉了：两页在导航里相邻，
    两个轮廓一样的日历摆在一起，就还是重号那个毛病 —— 靠里面的记号分，等于要求
    人凑近看。台阶的轮廓在整套里是唯一的。
    """
    return [polyline([(3.4, 16.6), (7.0, 16.6), (7.0, 12.9), (10.5, 12.9),
                      (10.5, 9.2), (14.0, 9.2), (14.0, 5.6), (16.8, 5.6)])]


def icon_position():
    """持仓收益：一只钱夹，里面一支向上的箭。

    钱夹是"持有"，箭头是"收益"。夹扣画在右半边，箭头因此只能待在左半边 ——
    这一点不对称正好让"钱夹"读得出来，否则一个矩形加一支箭头就是"上传"。
    """
    return [
        box(3.4, 7.6, 16.6, 16.8, r=1.4),
        box(12.4, 10.6, 16.6, 13.8, r=0.8),
        arrow(7.4, 15.0, 7.4, 10.6, length=1.9, spread=30),
    ]


# 名字/标签只用于预览图；key 与 MainWindow.xaml 里的 Tag 一一对应。
ICONS = [
    ("Turnover", "成交额", icon_turnover),
    ("Candle", "K线", icon_candle),
    ("Volume", "成交量换手率", icon_volume),
    ("SectorRace", "行业板块竞速", icon_sector_race),
    ("MarketCap", "市值榜", icon_market_cap),
    ("AhPremium", "AH 溢价", icon_ah_premium),
    ("ExtremeDays", "极端交易日", icon_extreme_days),
    ("FxCorridor", "汇率走廊", icon_fx_corridor),
    ("IndexRace", "指数长跑", icon_index_race),
    ("AssetRace", "大类资产", icon_asset_race),
    ("Drawdown", "回撤与修复", icon_drawdown),
    ("HoldOdds", "持有胜率", icon_hold_odds),
    ("Matrix", "收益矩阵", icon_matrix),
    ("GainCalendar", "涨跌日历", icon_gain_calendar),
    ("DcaPlan", "定投计划", icon_dca_plan),
    ("Position", "持仓收益", icon_position),
]

# 允许长得一样的成对图标。现在是空的：整套图标存在的理由就是原先有三对页面共用
# 同一个字形，所以任何两条路径完全一致都应该是一次构建失败。
ALLOWED_TWINS = set()


# ---------------------------------------------------------------- 装配

def build(name, draw):
    """画出几何、钉死方框、返回（并集, 轮廓环列表）。"""
    parts = [g for g in draw() if g is not None and not g.is_empty]
    assert parts, name

    shape = unary_union(parts)

    drawn = shape.bounds
    assert drawn[0] >= BOX0 - 1e-6 and drawn[1] >= BOX0 - 1e-6, \
        f"{name}: 画到了方框外 {drawn}"
    assert drawn[2] <= BOX1 + 1e-6 and drawn[3] <= BOX1 + 1e-6, \
        f"{name}: 画到了方框外 {drawn}"

    # 两个定位点：按包围盒缩放的东西（PathIcon 就是）没有它们，每幅图都会
    # 被拉成同样大小，宽扁的会被撑高、瘦高的会被压扁。
    marks = [Polygon([(BOX0, BOX0), (BOX0 + MARK, BOX0),
                      (BOX0 + MARK, BOX0 + MARK), (BOX0, BOX0 + MARK)]),
             Polygon([(BOX1 - MARK, BOX1 - MARK), (BOX1, BOX1 - MARK),
                      (BOX1, BOX1), (BOX1 - MARK, BOX1)])]

    shape = unary_union([shape] + marks)

    return shape


def rings(shape):
    """并集拆成外环 + 洞；外环逆时针、洞顺时针，非零填充才挖得出洞。"""
    polys = shape.geoms if shape.geom_type == "MultiPolygon" else [shape]
    out = []

    for poly in polys:
        fixed = orient(poly, sign=1.0)
        out.append(list(fixed.exterior.coords))
        out.extend(list(inner.coords) for inner in fixed.interiors)

    return out


def path_data(shape):
    """折线路径。只用 M/L/Z —— 曲线在这里没有意义，16px 看不出来。"""
    chunks = []

    for ring in rings(shape):
        pts = [(round(x, 1), round(y, 1)) for x, y in ring]

        # 合并重复点（四舍五入会造出来）
        clean = [pts[0]]

        for p in pts[1:]:
            if p != clean[-1]:
                clean.append(p)

        if clean[0] == clean[-1]:
            clean.pop()

        if len(clean) < 3:
            continue

        chunks.append("M" + "L".join(f"{x:g},{y:g}" for x, y in clean) + "Z")

    return "".join(chunks)


def svg(shape, size=20):
    """同一幅几何另存一份 SVG：帮助文档与他人复用都方便，且与 XAML 同源。"""
    body = []

    for ring in rings(shape):
        pts = " ".join(f"{x:g},{y:g}" for x, y in ring)
        body.append(f'    <path d="M{pts}Z" fill="currentColor" fill-rule="nonzero"/>')

    return ('<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {size:g} {size:g}" width="24" height="24" color="#1a1a1a">\n'
            + "\n".join(body) + "\n</svg>\n")


# ---------------------------------------------------------------- 预览

def font(size, cjk=True):
    for name in (("msyh.ttc", "segoeui.ttf") if cjk else ("segoeui.ttf",)):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except OSError:
            continue

    return ImageFont.load_default()


def render(shape, px, ink, bg, ss=8):
    """把一幅图按 px × px 画出来（超采样后缩小，边缘才有抗锯齿）。

    PIL 的多边形填充没有奇偶规则，洞不是自动挖的：每个外环铺 ink，它自己的洞
    再按背景色盖回去。多边形之间按面积从大到小走 —— 一个环的洞可能正落在另一个
    小件上（靶心的心就落在内圈里），顺序错了就会把它擦掉。
    """
    n = px * ss
    img = Image.new("RGB", (n, n), bg)
    draw = ImageDraw.Draw(img)
    k = n / GRID
    polys = shape.geoms if shape.geom_type == "MultiPolygon" else [shape]

    for poly in sorted(polys, key=lambda p: -p.area):
        draw.polygon([(x * k, y * k) for x, y in poly.exterior.coords], fill=ink)

        for inner in poly.interiors:
            draw.polygon([(x * k, y * k) for x, y in inner.coords], fill=bg)

    return img.resize((px, px), Image.LANCZOS)


def sheet(shapes, path, ink, bg):
    cols = 4
    rows = (len(shapes) + cols - 1) // cols
    cell_w, cell_h = 200, 96
    img = Image.new("RGB", (cell_w * cols, cell_h * rows), bg)
    draw = ImageDraw.Draw(img)
    label = font(13, cjk=False)

    for i, (name, _, shape) in enumerate(shapes):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h
        x = cx + 12

        for px in (16, 24, 48):
            icon = render(shape, px, ink, bg)
            img.paste(icon, (x, cy + 24))
            x += px + 14

        draw.text((cx + 12, cy + 10), name, fill=ink, font=label)

    img.save(path)
    return path


def nav_mock(icons, path, ink, bg, hi=None):
    """按导航顺序排一份模拟列表：图标 16px、行高 40、左边距 12。"""
    row = 40
    img = Image.new("RGB", (300, row * len(icons) + 8), bg)
    draw = ImageDraw.Draw(img)
    label = font(15)

    for i, (_, text, shape) in enumerate(icons):
        y = 4 + i * row

        if hi is not None and i == hi:
            draw.rectangle([0, y, 300, y + row - 2], fill=(0, 90, 158) if bg[0] < 128 else (229, 241, 251))

        icon = render(shape, 16, ink, bg)
        img.paste(icon, (14, y + (row - 16) // 2 - 1))
        draw.text((48, y + (row - 18) // 2 - 1), text, fill=ink, font=label)

    img.save(path)
    return path


# ---------------------------------------------------------------- 输出

def write_xaml(shapes, path):
    blocks = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<!--",
        "    导航栏那十六个页面的图标。**生成物**，不要手改：",
        "    改 tools/make-icons.py 再跑一次（python tools/make-icons.py）。",
        "",
        "    每条都是一幅填充几何（路径数据，只用了 M/L/Z），由描边骨架外扩求并",
        "    而来 —— PathIcon 只吃填充，而描边（线、圆环、折线）是这些图标本来的",
        "    写法。",
        "",
        "    **为什么是字符串而不是 PathGeometry。** 两种写法都想试过：WinUI 的",
        "    XAML 编译器不接受把路径小语言写在 `PathGeometry.Figures` 上",
        "    （WMC0055，`Cannot assign text value ... into property 'Figures' of",
        "    type 'PathFigureCollection'`），尽管同一段小语言写在 `PathIcon.Data`",
        "    上完全合法。所以这里存字符串，`MainWindow.xaml` 里由 `Data` 属性自己",
        "    转换。",
        "",
        "    每一幅都带着两个 0.03 单位的定位点，落在 (2,2) 与 (18,18)。PathIcon 用",
        "    Viewbox 的等比缩放去填满图标格，量的是几何的包围盒 —— 没有这两个点，",
        "    宽扁的图会被撑高、瘦高的图会被压扁，并排就不再是一个字号。有了它们，",
        "    每幅图共享同一个 20×20 的方框，设计区是中间的 16×16。",
        "-->",
        '<ResourceDictionary',
        '    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"',
        '    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">',
        "",
    ]

    for key, label, _ in ICONS:
        shape = shapes[key]
        blocks.append(f"    <!-- {label} -->")
        blocks.append(f'    <x:String x:Key="Icon{key}" xml:space="preserve">{path_data(shape)}</x:String>')
        blocks.append("")

    blocks.append("</ResourceDictionary>")
    path.write_text("\n".join(blocks), encoding="utf-8")

    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验，不写文件")
    args = ap.parse_args()

    shapes = {}

    for key, label, draw in ICONS:
        shapes[key] = build(key, draw)

    # 重号检查：这套图标存在的理由，就是原先有三对页面共用同一个字形。
    seen = {}

    for key, _, _ in ICONS:
        data = path_data(shapes[key])

        for other, other_data in seen.items():
            if data == other_data and frozenset((key, other)) not in ALLOWED_TWINS:
                print(f"✗ {key} 与 {other} 是同一条路径 —— 又重号了")
                return 1

        seen[key] = data

    print(f"{len(shapes)} 幅图，包围盒与重号都干净")

    if args.check:
        return 0

    SVGS.mkdir(parents=True, exist_ok=True)

    for key, _, _ in ICONS:
        (SVGS / f"{key}.svg").write_text(svg(shapes[key]), encoding="utf-8")

    ordered = [(key, label, shapes[key]) for key, label, _ in ICONS]
    sheet(ordered, SVGS / "sheet-light.png", (23, 23, 23), (243, 243, 243))
    sheet(ordered, SVGS / "sheet-dark.png", (243, 243, 243), (32, 32, 32))
    nav_mock([(k, l, s) for k, l, s in ordered], SVGS / "nav-light.png",
             (23, 23, 23), (243, 243, 243), hi=4)
    nav_mock([(k, l, s) for k, l, s in ordered], SVGS / "nav-dark.png",
             (243, 243, 243), (32, 32, 32), hi=4)

    XAML.parent.mkdir(parents=True, exist_ok=True)
    write_xaml(shapes, XAML)

    print(f"写好了 {XAML.relative_to(REPO)}")
    print(f"预览在 {(SVGS / 'sheet-light.png').relative_to(REPO)} 等四张")

    return 0


if __name__ == "__main__":
    sys.exit(main())
