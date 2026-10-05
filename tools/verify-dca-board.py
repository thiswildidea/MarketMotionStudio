# -*- coding: utf-8 -*-
"""真机验证「定投计划」这一轮新加的三样：两种推进方式、末端实时收益金额、最多六只对比。

**为什么直接把 `verify-position.py` 当库用，而不是复制一份。** 两页共用同一套调色板
（`Palette.Tracks` 六条 + `Palette.Moving` 那根琥珀线）、同一个画布量法、同一批 chip 与
下拉的操作。这份函数曾经在三个脚本里各复制一份、然后同时失效过一次 —— 复制出去的是一份
迟早会对不上的副本，不是省事。

**定投与持仓在数据上的差别，脚本必须自己复刻：** 持仓是「一次买入之后不动」，定投是
「按节奏一直在买」。所以这里复刻的是每天的 `shares += amount / close`，而不是
`capital / close` 一份到底。

用法：
    python tools/verify-dca-board.py
"""
import importlib.util
import os
import sys
import time
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import winui  # noqa: E402

_spec = importlib.util.spec_from_file_location("vp", os.path.join(HERE, "verify-position.py"))
vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vp)

check = vp.check
report = vp.report

REPO = vp.REPO
PAGE = "定投计划"

# 定投页那一排一键预设（`Markets.ASharePlans`）。七只，上限是六 —— 第七只是用来试拒绝的。
PRESETS = [
    ("sh510300", "沪深300ETF"),
    ("sh510500", "中证500ETF"),
    ("sz159915", "创业板ETF"),
    ("sh518880", "黄金ETF"),
    ("sh513100", "纳指ETF"),
    ("sh000001", "上证指数"),
    ("sz399006", "创业板指"),
]

# 页面默认每期 100；脚本按同一个数复刻，不读框（框里的字读回来要绕一圈，而默认值没动过）。
AMOUNT = 100.0

SHOTS = ("verify-dca-one.png", "verify-dca-two.png", "verify-dca-three.png",
         "verify-dca-six.png", "verify-dca-grow.png", "verify-dca-scroll.png")

# 投入线（那根琥珀阶梯）用的就是 `Palette.Moving`，与持仓页的「本金线」同一个色。
CAPITAL = (0xFB, 0xBF, 0x24)


def spent_columns(shot):
    """投入线出现在画面的哪些列上，以及十等分里每段各有多少列。

    **不能照抄持仓页那句「本金线是一根横贯绘图区的直线」。** 那句在持仓页对：一笔买入之后
    再没动过，线是平的，一量就是上千像素的一整行。这一页每天都在买，线是一级一级往上的
    **阶梯**，最长的一段横线只有一两个像素 —— 实测 12 像素，而那是图例上的色块。照抄它会
    读出「投入线不见了」，画面上它却好好地横在那里。

    所以改量**列**：它盖住多少列，以及十段里是不是每段都有它。「覆盖了多少列」这种总量看不
    出「少了一截」（前半截被盖掉、后半截还在，总量照样过半），十等分才看得出来。

    **后三段不是它的地盘。** 有几份就有几个胶囊，都从绘图区右端往回排：六份时六个胶囊叠在
    一起，左端到 x≈995，把那条线连同六条曲线一起压住 —— 实测后三段只剩 [0, 5, 4] 列，哪一种
    画法都一样。所以「每段都有它」只量到标签之前。
    """
    xs = sorted({x for x, _ in shot["frame"].of(CAPITAL)})

    if not xs:
        return 0, [0] * 10

    span = xs[-1] - xs[0]
    buckets = [0] * 10

    for x in xs:
        buckets[min(9, (x - xs[0]) * 10 // max(1, span))] += 1

    return len(xs), buckets


# ---- 源码断言 -----------------------------------------------------------------------

def source():
    root = os.path.join(REPO, "src", "MarketMotionStudio")
    series = open(os.path.join(root, "Market", "DcaSeries.cs"), encoding="utf-8-sig").read()
    render = open(os.path.join(root, "Render", "DcaRenderer.cs"), encoding="utf-8-sig").read()
    page = open(os.path.join(root, "Pages", "DcaPlanPage.xaml.cs"), encoding="utf-8-sig").read()
    xaml = open(os.path.join(root, "Pages", "DcaPlanPage.xaml"), encoding="utf-8-sig").read()

    print("源码")

    # ---- 两种推进方式 ----
    check("定投也有自己的推进方式枚举（不复用持仓与 K 线的）",
          "public enum DcaMotion" in series)
    check("两种：整段铺满与窗口滚动",
          "Grow = 0" in series and "Scroll = 1" in series)
    check("走法是渲染器的**构造参数**（写成属性会读成默认值）",
          "public DcaRenderer(DcaBoard board, AnimationPlan plan, DcaMotion motion, int window)"
          in render)
    check("窗口至少两根（一根连不成线）", "_window = Math.Max(2, window)" in render)
    check("窗口三行算术：count / head / first",
          "var count = _motion is DcaMotion.Scroll ? Math.Min(_window, n) : n;" in render
          and "var head = _motion is DcaMotion.Scroll ? Math.Max(moving + eased[moving], count - 1) : moving;"
          in render
          and "var first = _motion is DcaMotion.Scroll ? head - (count - 1) : 0;" in render)
    check("横轴按窗口铺满（不是按整段）",
          "double Across(int i) => mx + (count > 1 ? plotW * (i - first) / (count - 1) : 0);" in render)
    check("窗口左边界向上取整（落在轴外会压住坐标数字）",
          "var left = Math.Max(0, (int)Math.Ceiling(first));" in render)
    check("日期标签按窗口取，但每颗钉在自己那一天上",
          "if (i < first || i > head)" in render)
    check("**纵轴只算一次** —— 两条线的距离就是结果，跟着窗口重算会让它变宽",
          render.count("_scale = AnimationPlan.NiceScale(") == 1)
    # `OnLookChanged` 里只有重画与落盘两行 —— 没有 `Fetch()`。改变一个显示方式不该重新
    # 去源端走一遍二十年。
    check("切换推进方式只重画、不重新取数",
          "private void OnLookChanged" in page
          and "ApplyPreviewSettings();\n        SavePreferences();" in page
          and "Fetch();" not in page.split("private void OnLookChanged")[1].split("private ")[0])
    check("窗口框只在滚动时可用",
          "WindowBox.IsEnabled = ChosenMotion() is DcaMotion.Scroll;" in page)
    check("推进方式落盘", '_prefs.Save("Motion", (int)ChosenMotion());' in page
          and '_prefs.Save("Window", ChosenWindow());' in page)
    check("下拉与窗口框各自绑了资源键",
          'x:Uid="DcaMotionLabel"' in xaml and 'x:Uid="DcaWindowLabel"' in xaml)

    # ---- 多只 ----
    check("上限是六份", "public const int MostTracks = 6;" in series)
    check("超过上限是拒绝，不是画前六份",
          "chosen.Count > DcaPlanner.MostTracks" in page and "DcaTooMany" in page)
    check("日期轴取并集（取交集会把十年悄悄截成三年）",
          "var union = new SortedSet<DateOnly>();" in series)
    check("每份从自己第一个交易日起（晚上市的不在别人的年份里画）",
          "int First," in series and "int Last," in series
          and "var begin = Math.Max(track.First, left);" in render)
    check("**投入线只画一条**：六份计划买的钱一样多、节奏一样，六条是同一条阶梯画六遍",
          "_board.Tracks[_board.Reference]" in render)
    check("共享的那条是**投得最多**的那份（画最少的会让别人看起来更赚）",
          "public int Reference" in series
          and "Tracks[i].FinalInvested > Tracks[at].FinalInvested" in series)
    check("多只不画填充（六层填充是一团泥）",
          "if (!_board.Comparing && lines.Count > 0 && paidLine.Count > 1)" in render)
    # 这一条守的是**绘制顺序**，不是画什么。六个计划按同一节奏投同一笔钱，所以前半段它们
    # 全都贴着投入线走：投入线画在它们下面，就被这六条盖掉前半截（实测只剩 99 列，前三分
    # 之一一列都没有），看上去像从画面中段凭空冒出来的一小段。所以多只时要画在**最后**。
    paid_call = "DrawPolyline(session, context, paidLine, Palette.Moving, style, introA);"
    loop_at = render.index("foreach (var line in lines)")
    over_at = render.index("if (_board.Comparing)")
    again_at = render.index(paid_call, loop_at)

    check("多只时那条共享的投入线画在**市值线之上**（压在下面会被六条盖没前半截）",
          render.count(paid_call) == 2
          and render.index(paid_call) < loop_at < over_at < again_at)
    check("多只时图例只剩投入线（每条市值线自己末端有标签）",
          "_board.Comparing\n            ? new[] { (Palette.Moving, \"DcaLegendInvested\") }" in render)
    check("大数字按**收益率**选领先的那份（晚上市的投得少，赚得少不等于更差）",
          "var ret = (plot.Values[i] / plot.Paid[i]) - 1;" in render)
    check("多只时收尾是每份一张卡",
          "DrawTrackCards(session, context, a, left, gap, y, cardHeight, valueFormat);" in render)

    # ---- 末端实时收益金额 ----
    check("末端胶囊两行：名字 + 金额",
          "(name + \" \", Palette.Muted, nameFormat)," in render
          and "(money, colour, valueFormat)," in render)
    check("胶囊锚在自己那条线的最后一列（不是投入线上）",
          "(line.Points[^1].X, line.Points[^1].Y - context.Px(4))" in render)
    check("胶囊彼此避让（按 y 排序往下推）",
          "centres[here] = centres[previous] + height + gap;" in render)
    check("**单只也画**（这是需求里那一半：一个的时候也要显示）",
          render.count("DrawLabels(session, context, lines, anchors, top, bottom, introA);") == 1
          and "if (!_board.Comparing" not in render.split("DrawLabels(session, context")[0][-200:])

    # ---- 填充的取色 ----
    #
    # 这一条是顺手记下来的：改之前那行是 `last.YValue <= last.YInvested ? Loss : Gain`，
    # 而 y 越小越高 —— 市值线在投入线**上面**是赚了，那一句给的是亏的颜色，与类注释
    # 「warm while the plan is ahead」正好相反。
    check("填充按**画面上的高低**取色：市值线在上面是赚",
          "var colour = value[span - 1].Y <= paid[span - 1].Y ? Gain : Loss;" in render)


# ---- 数据复刻 -----------------------------------------------------------------------

def plan(start, end, picks):
    """一份定投板的复刻：日期轴取并集，日频，每期固定金额。

    与 `DcaPlanner.LoadBoardAsync` 同一套动作 —— 每天 `shares += amount / close`，休市日
    **前值顺延**（份额还是那些份额，关着门的市场里买不进）。持仓页那份是「一次买入」，
    这一份是「一直在买」，两个函数不共用。
    """
    walks = {code: vp.closes(code, start, end) for code, _ in picks}
    union = sorted(set().union(*walks.values()))

    tracks = []

    for code, name in picks:
        own = walks[code]
        days = sorted(own)

        shares = 0.0
        invested = 0.0

        # 日频：每一天都买，第一天也买（周频与月频才要「这一周/这一月的第一个交易日」
        # 那个判断，而它会让区间第一天不买）。
        for day in days:
            shares += AMOUNT / own[day]
            invested += AMOUNT

        # 期末是**这一只自己的**最后一个交易日，不是并集轴最后一天 —— 它在那之后没有
        # 价格，画也画到那里为止。
        tracks.append({"code": code, "name": name,
                       "value": shares * own[days[-1]], "invested": invested})

    return union, tracks


def pick_freq(win, label):
    combo = winui.find(win, lambda c: c.AutomationId == "FreqCombo")

    return winui.combo_pick(win, combo, label) if combo is not None else None


# ---- 真机 ---------------------------------------------------------------------------

def main():
    for old in SHOTS:
        path = os.path.join(REPO, "artifacts", old)

        if os.path.exists(path):
            os.remove(path)

    win = winui.launch(winui.EXE)

    if win is None:
        check("应用起得来", False)
        return report()

    check("窗口最大化了（窄窗口会把 chip 挤出横向滚动的面板）", vp.maxed(win))

    if not vp.goto(win, PAGE):
        check(f"导航里有「{PAGE}」", False)
        return report()

    today = date.today()
    start = vp.add_months(today, -60)

    print(f"\n真机（{PAGE}，近 5 年，日频，每期 {AMOUNT:.0f}）")

    check("自选清单的 picker 在这一页（换掉了原来那个自己的搜索框）",
          winui.find(win, lambda c: c.AutomationId == "InstrumentSearch") is None)
    check("推进方式下拉在", winui.find(win, lambda c: c.AutomationId == "MotionCombo") is not None)
    check("窗口天数框在", winui.find(win, lambda c: c.AutomationId == "WindowBox") is not None)

    # 偏好会落盘，上一次跑成什么样这一趟就是什么样 —— 这三样必须先复位。
    check("区间选到「近 5 年」", vp.pick_range(win, "近 5 年") == "近 5 年")
    check("频率选到「每个交易日」", pick_freq(win, "每个交易日") == "每个交易日")

    amount = winui.find(win, lambda c: c.AutomationId == "AmountBox")
    check("金额框在", amount is not None)

    if amount is not None:
        try:
            amount.GetValuePattern().SetValue("100")
        except Exception:  # noqa: BLE001
            check("金额写成 100", False)
        else:
            check("金额写成 100", True)

    check("清单先清空（这份清单跨会话共享）", vp.clear_list(win) is True)
    check("清空后清单是空的", vp.chip_names(win) == [], str(vp.chip_names(win)))

    # ---- 一份 ----
    print("\n一份")

    check("点一键预设就取数", vp.press_preset(win, PRESETS[0][0]))
    check("清单里只有这一份且被勾上", vp.ticked(win) == [PRESETS[0][0]], str(vp.ticked(win)))

    one = vp.measure(win, "verify-dca-one.png", count=1)

    check("画布量得出", one is not None)

    if one is not None:
        check("一条市值线", one["pixels"][0] > 200, str(one["pixels"][0]))

        cols, buckets = spent_columns(one)

        # 一只时那个胶囊短，只压住末尾几十个像素，所以十段都要求有它。
        check("投入线横贯绘图区（十段里每段都有它）", min(buckets) >= 12,
              f"{cols} 列，十段 {buckets}")
        check("一个末端白点", len(one["dots"]) == 1, f"{len(one['dots'])} 个")
        check("**单只也有末端胶囊**（这是这次新加的那一半）",
              one["labels"][0][0] == 1, f"{one['labels'][0][0]} 只")

    # ---- 两份 ----
    print("\n两份")

    check("加第二份并取数", vp.press_preset(win, PRESETS[1][0]))
    check("两份都勾着", vp.ticked(win) == [PRESETS[0][0], PRESETS[1][0]], str(vp.ticked(win)))

    union, tracks = plan(start, today, PRESETS[:2])

    two = vp.measure(win, "verify-dca-two.png", count=2)

    check("画布量得出", two is not None)

    if two is not None:
        check("两条市值线都在", all(two["pixels"][i] > 200 for i in (0, 1)),
              " / ".join(f"{i + 1}: {two['pixels'][i]}" for i in (0, 1)))
        check("两个末端白点", len(two["dots"]) == 2, f"{len(two['dots'])} 个")
        check("两条都有末端胶囊", all(two["labels"][i][0] == 1 for i in (0, 1)),
              " / ".join(f"{i + 1}: {two['labels'][i][0]}" for i in (0, 1)))

        order = sorted(range(2), key=lambda i: -tracks[i]["value"])
        top = min((two["ends"][i], i) for i in (0, 1) if two["ends"][i] is not None)

        check("赚得多的那份画在上面", top[1] == order[0],
              f"脚本最多 {tracks[order[0]]['name']}（第 {order[0] + 1} 条）/ "
              f"画面最上面是第 {top[1] + 1} 条（y={top[0]}）")

    # ---- 六份 ----
    print("\n六份")

    for code, _ in PRESETS[2:6]:
        vp.press_preset(win, code)

    check("六份都勾着", len(vp.ticked(win)) == 6, str(vp.ticked(win)))

    _, six_tracks = plan(start, today, PRESETS[:6])

    six = vp.measure(win, "verify-dca-six.png", count=6)

    check("画布量得出", six is not None)

    if six is not None:
        check("六条市值线色都出现了",
              all(six["pixels"][i] > 200 for i in range(6)),
              " / ".join(f"{i + 1}: {six['pixels'][i]}" for i in range(6)))
        check("六份都有末端胶囊",
              all(six["labels"][i][0] == 1 for i in range(6)),
              " / ".join(f"{i + 1}: {six['labels'][i][0]}" for i in range(6)))

        # **共享的投入线还在，而且是完整的一条。** 六个计划都按同一个节奏投同一笔钱，
        # 所以前半段它们全都贴在投入线上走 —— 投入线画在它们**下面**的话，会被这六条
        # 盖掉前半截（实测只剩 99 列，前三分之一一列都没有），于是它看起来是从画面中段
        # 凭空冒出来的一小段。这一条守的就是绘制顺序。
        cols, buckets = spent_columns(six)

        check("六份时那条共享的投入线仍然贯穿画面（标签之前每段都有它）",
              min(buckets[:7]) >= 12, f"{cols} 列，十段 {buckets}")

        # **几个白点要算，不能写死。** 两份期末市值挨得很近时，两个点会叠成一个连通块。
        # 每像素多少钱从画面上量：最高与最低那两个白点的距离除以它们末值之差。
        ends = [(i, six["ends"][i]) for i in range(6) if six["ends"][i] is not None]

        check("每条线都找得到自己的白点", len(ends) == 6, f"{len(ends)}/6")

        if len(ends) == 6:
            low = min(ends, key=lambda p: p[1])
            high = max(ends, key=lambda p: p[1])
            spread = abs(six_tracks[low[0]]["value"] - six_tracks[high[0]]["value"])

            if spread > 0:
                rate = abs(high[1] - low[1]) / spread
                values = sorted((six_tracks[i]["value"], i) for i in range(6))
                merged = sum(
                    1 for a, b in zip(values, values[1:])
                    if (b[0] - a[0]) * rate < 5)

                check("白点数对得上（挨在一起的两份算一个）",
                      len(six["dots"]) == 6 - merged,
                      f"{len(six['dots'])} 个，应有 {6 - merged} 个"
                      f"（一像素约 {1 / rate:,.0f} 元，{merged} 对挨在一起）")
            else:
                check("六份期末市值互不相同（否则比的是同一个数）", False)

    # ---- 第七份：拒绝 ----
    print("\n上限")

    check("第七份也勾上了", vp.press_preset(win, PRESETS[6][0]) is not None
          and len(vp.ticked(win)) == 7, str(vp.ticked(win)))

    # `fetch` 给的是 **(读回来的数据, 状态行)** 两个值：拒绝取数时第一个是 `None`、状态行
    # 里是那句拒绝的话。写成 `"最多" in fetch(...)` 是在元组里找字符串 —— 永远为假，而报
    # 出来的明细正是一句「最多同时对比 6 个计划，现在勾了 7 个」，看上去像断言对了。
    data, said = vp.fetch(win)

    check("勾到七份时拒绝取数", data is None and "最多" in said, said[:80])

    # ---- 两种推进方式 ----
    #
    # 同持仓页那一对：整段铺满时曲线头跟着进度走，窗口滚动时窗口右端就是头、它停在绘图区
    # 右端。基准**从画面上量**（满进度那一帧的头），不能拿画布边框当 —— 右边那几十个像素
    # 是胶囊标签的地盘。
    print("\n推进方式")

    vp.motion(win, "整段铺满")

    check("复位成「整段铺满」后窗口框是灰的", vp.window_on(win) is False,
          f"窗口框可用={vp.window_on(win)}")

    grow = scroll = None

    if vp.scrub(win, 0.5):
        grow = vp.measure(win, "verify-dca-grow.png", count=6)

    check("切成「窗口滚动」", vp.motion(win, "窗口滚动") == "窗口滚动")
    check("滚动时窗口框可用", vp.window_on(win) is True, f"窗口框可用={vp.window_on(win)}")

    if vp.scrub(win, 0.5):
        scroll = vp.measure(win, "verify-dca-scroll.png", count=6)

    if grow is None or scroll is None:
        check("两种推进方式都画得出", False, "取不到画面")
    else:
        left, right = grow["box"][0], grow["box"][1]
        width = right - left
        a, b = vp.head_of(grow), vp.head_of(scroll)
        tip = vp.head_of(six) if six is not None else None

        check("整段铺满：0.5 处曲线头还在画面中段",
              a is not None and a < left + (width * 0.66),
              f"头 x={a}，中段 {left + (width // 2)}，右缘 {right}")
        check("窗口滚动：0.5 处曲线头已经停在绘图区右端",
              b is not None and tip is not None and tip - b <= width * 0.04,
              f"头 x={b}，绘图区右端 x={tip}（还差 {tip - b} 像素，画布宽 {width}）")
        check("同一个进度下滚动比整段铺满靠右一大截",
              a is not None and b is not None and b - a > width * 0.2,
              f"整段 {a} → 滚动 {b}，差 {b - a} 像素（画布宽 {width}）")

    check("切回「整段铺满」", vp.motion(win, "整段铺满") == "整段铺满")
    check("切回来之后窗口框又是灰的", vp.window_on(win) is False,
          f"窗口框可用={vp.window_on(win)}")

    # ---- 落盘 ----
    print("\n重启")

    check("重启前把推进方式切成「窗口滚动」（验它落盘）",
          vp.motion(win, "窗口滚动") == "窗口滚动")

    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    vp.maxed(win)

    if vp.goto(win, PAGE):
        check("重启后推进方式还是「窗口滚动」（偏好落盘了）", vp.window_on(win) is True,
              f"窗口框可用={vp.window_on(win)}")

        # 落盘的那一个偏好用完就复位，下一趟才不会开局就在滚动里。
        vp.motion(win, "整段铺满")

        check("收尾复位回「整段铺满」", vp.window_on(win) is False,
              f"窗口框可用={vp.window_on(win)}")

    return report()


if __name__ == "__main__":
    source()
    sys.exit(main())
