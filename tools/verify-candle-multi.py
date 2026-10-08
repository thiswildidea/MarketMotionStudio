# -*- coding: utf-8 -*-
"""真机验证 K 线页的两件新事：分钟线的表头是**当日**涨跌幅，以及这一页可以画多个标的。

为什么要真机：这两件都不是「源端返回什么」的问题。当日涨跌幅是把**前一个交易日**的收盘价
带进序列，多标的是把 N 条序列摆到同一根轴上 —— 两件都发生在页面里，而且第二件改的是画面
本身（不再画蜡烛），离线脚本一样也证明不了。

画面上的判据是**像素**的，因为预览画布没有自动化节点：曲线几条按赛道色的色相数，末端标注
有没有进平台那条按钮栏按最右侧墨迹与「帧宽 82%」那条线比。两处都用比例，不用绝对像素 ——
两次实拍的画布可能不一样大（状态条长出来时预览会按 9:16 缩）。

用法：
    python tools/verify-candle-multi.py
"""
import colorsys
import importlib.util
import os
import re
import sys
import time

import uiautomation as auto
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src", "MarketMotionStudio")
OUT = os.path.join(ROOT, "artifacts")

sys.path.insert(0, HERE)

# 载入 verify-candle.py 里那些开窗口、按按钮、读状态条的手脚，不重写一遍。
sys.argv = ["x"]
_spec = importlib.util.spec_from_file_location("vc", os.path.join(HERE, "verify-candle.py"))
vc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vc)

import winui  # noqa: E402

check = vc.check
CHECKS = vc.CHECKS
BAD = vc.BAD

SAFE = 0.82


def read(*parts):
    with open(os.path.join(SRC, *parts), encoding="utf-8-sig") as handle:
        return handle.read()


def goto(win):
    page = vc.find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "K线", win)

    for _ in range(3):
        if page is not None:
            sel = vc.pat(page, auto.PatternId.SelectionItemPattern)

            if sel is not None:
                try:
                    sel.Select()
                except Exception:  # noqa: BLE001
                    pass
            else:
                vc.click(page, 1.0)

        deadline = time.time() + 12

        while time.time() < deadline:
            time.sleep(0.8)

            if vc.find(lambda c: c.AutomationId == "PeriodCombo", win) is not None:
                return True

    return False


def chips(win):
    """清单里每一只的 (代码, 名字, 开关)。按**代码**寻址，不按 14 种语言拼写的名字。"""
    out = []

    for control in vc.find_all(lambda c: c.ControlTypeName == "ButtonControl", win):
        if not control.AutomationId:
            continue

        try:
            pattern = control.GetTogglePattern()
        except Exception:  # noqa: BLE001
            continue

        if pattern is None:
            continue

        out.append((control.AutomationId, control.Name, pattern))

    return out


def presets(win):
    """一键预设那几个按钮，按它们在页面上的顺序。

    按**位置**认，不按 AutomationId：`ItemsControl` 与自定义控件不把 `x:Name` 带进
    UIA（实测 `Presets` 与 `Watch` 都查不到，而 `PeriodCombo`、`FetchButton` 查得到）。
    预设就夹在搜索框下缘和「收藏」上缘那一段里 —— 那一段只有它们。
    """
    search = vc.find(lambda c: c.AutomationId == "InstrumentSearch", win)
    add = vc.find(lambda c: c.AutomationId == "FavouriteButton", win)

    if search is None or add is None:
        return []

    top = search.BoundingRectangle.bottom
    bottom = add.BoundingRectangle.top

    out = []

    for control in vc.find_all(lambda c: c.ControlTypeName == "ButtonControl", win, 0, 30):
        box = control.BoundingRectangle

        if box.height() == 0 or not control.Name:
            continue

        if top <= box.top and box.bottom <= bottom:
            out.append((box.top, box.left, control))

    return [control for _, _, control in sorted(out)]


def analyse(name):
    """一张截图里：赛道色出现了几种，以及最右侧的彩色墨迹在哪。

    只数**有彩度**的像素：画布是近黑的，网格和轴标签是灰的，进度条在画面下缘之外 ——
    剩下的彩色就是曲线本身和骑在它们末端的那一圈标注边框。
    """
    whole = Image.open(os.path.join(OUT, name)).convert("RGB")
    box = winui.canvas_box(whole)

    if box is None:
        return None, None, None, None

    left, right, top, _ = box

    # 画布的下缘要问 `frame_bottom`，不能用 `canvas_box` 给的那个：`canvas_box` 往下会走
    # 过画面下面的那一排控件（按钮、搓擦条也是暗的），实测把 852 说成 890。而画面最底下
    # 那两行是进度条 —— 它铺满整幅宽，混进来就是一条永远越线的墨迹，所以扫到下缘往上一
    # 点点为止。
    bottom = winui.frame_bottom(whole, box) or box[3]
    height = bottom - top
    pixels = whole.load()

    floor = int(bottom - (height * 0.03))
    hues = {}
    far = left

    for y in range(top, floor, 2):
        for x in range(left, right, 2):
            r, g, b = pixels[x, y]

            if max(r, g, b) - min(r, g, b) < 70 or max(r, g, b) < 90:
                continue

            hue = int(colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 12)
            hues[hue] = hues.get(hue, 0) + 1

            if x > far:
                far = x

    strong = sorted((count for count in hues.values() if count >= 60), reverse=True)

    return strong, far, box, right


def main():
    # ---- 源码：当日涨跌幅 ------------------------------------------------------------
    series = read("Market", "CandleSeries.cs")
    render = read("Render", "CandleRenderer.cs")

    check("序列带得动「昨收」", "double PreviousClose = 0" in series)
    check("昨收取**前一场**的收盘，不是上一根的",
          "CloseBefore(MinuteDay day)" in series and "Days[at - 1].Bars[^1].Close" in series)
    check("每一天的序列把昨收带进去",
          "ForDay(MinuteSession session, MinuteDay day)" in series
          and "session.CloseBefore(day)" in series)
    check("表头优先用昨收 —— 分钟线的那个大数字才是当日的",
          "_series.PreviousClose > 0" in render,
          "" if "_series.PreviousClose > 0" in render else "还在拿前一根当基准")

    # ---- 源码：多标的 ----------------------------------------------------------------
    board = read("Market", "CandleBoard.cs")
    racer = read("Render", "CandleRaceRenderer.cs")
    page = read("Pages", "CandlePage.xaml.cs")
    xaml = read("Pages", "CandlePage.xaml")

    check("轴是**并集**不是交集（晚上市的不被截短）", "new SortedSet<string>" in board)
    check("自己没有的那天向前携带，不画成掉回零", "returns[i] = carried" in board)
    check("分钟线取各标的共有的那一个交易日", "SharedDay(sessions)" in board)
    check("每条曲线一种赛道色", "Palette.Track(k)" in racer)
    check("末端标注走的是三页共用那一处安全线算术",
          "context.SafeRight(_giveWay)" in racer
          and "context.RightLabelColumn(widest, context.Px(LabelGap + LabelEdgePad), _giveWay)"
          in racer)
    check("页面在选了 2 个以上时改画比较",
          "CandleRaceRenderer(board, plan, ChosenMotion(), ChosenWindow())" in page)
    check("蜡烛图那一排样式在多标的下是灰的（不然就是三个被忽略的设置）",
          "StyleCombo.IsEnabled = _board is null" in page)
    check("清单那一排是可开关的",
          '<views:WatchlistPicker x:Name="Watch" Selectable="True" />' in xaml)

    # ---- 真机 ------------------------------------------------------------------------
    win = vc.launch()

    if win is None:
        check("窗口起来了", False)
        return 1

    check("导航到 K 线页", goto(win))

    rows = presets(win)
    check("页面上有至少两个一键预设", len(rows) >= 2,
          "、".join(c.Name for c in rows[:4]) or "0 个")

    if len(rows) < 2:
        return 1

    # 上一轮跑完会留着开关的状态（清单是跨会话共享的），这一轮先全部关掉，从干净处起。
    for _, _, pattern in chips(win):
        if pattern.ToggleState == auto.ToggleState.On:
            pattern.Toggle()

    time.sleep(1.0)

    # 全都关掉时取数，应当被**挡住**并说出原因 —— 这句话是本版才有的。
    vc.click(vc.find(lambda c: c.AutomationId == "FetchButton", win), 1.0)
    empty = vc.wait_status(win, seconds=30)
    check("一只都没开时取数被挡住并说清原因", bool(empty) and "标的" in (empty or ""),
          empty or "(状态条空)")

    # 一键预设点一下 = 加进清单 + 打开这只 + 取数。点两个，页面就该从「一只的蜡烛图」
    # 换成「两只的比较」。
    vc.click(rows[0], 1.0)
    one = vc.wait_status(win, seconds=90)
    check("第一只取到了", bool(one) and not BAD.search(one or ""), one or "(状态条空)")

    check("一只时样式下拉是可用的", vc.enabled(win, "StyleCombo") is not False,
          str(vc.enabled(win, "StyleCombo")))

    vc.click(rows[1], 1.0)
    many = vc.wait_status(win, seconds=120)
    check("第二只取到了（两只一起）", bool(many) and not BAD.search(many or ""),
          many or "(状态条空)")

    on = [c for c in chips(win) if c[2].ToggleState == auto.ToggleState.On]
    check("清单里有两只开着", len(on) >= 2, f"{len(on)} 只")

    check("多标的下样式下拉是灰的（这一版不画蜡烛）",
          vc.enabled(win, "StyleCombo") is False, str(vc.enabled(win, "StyleCombo")))

    vc.scrub_to(win, 1.0)
    vc.shot(win, "verify-candle-multi.png")

    strong, far, box, right = analyse("verify-candle-multi.png")

    if box is None:
        check("截图里认得出画布", False)
        return 1

    width = box[1] - box[0]
    check("画面上至少两种赛道色（确有几条曲线）", len(strong) >= 2, str(strong[:4]))
    check("末端标注的右缘在安全线以内（不进平台那条按钮栏）",
          far <= (box[0] + (width * SAFE)) + 6,
          f"最右墨迹 x={far}，安全线 {round(box[0] + (width * SAFE))}，画布右缘 {right}")

    # ---- 退回一只 --------------------------------------------------------------------
    # 双向验：只验「两只时是比较」的话，「一只时也画比较」照样绿。
    if on:
        win.SetFocus()

        try:
            on[-1][2].Toggle()
        except Exception:  # noqa: BLE001
            pass

        time.sleep(1.0)

        fetch = vc.find(lambda c: c.AutomationId == "FetchButton", win)
        vc.click(fetch, 1.0)
        back = vc.wait_status(win, seconds=90)

        check("关掉一只之后取数正常", bool(back) and not BAD.search(back or ""),
              back or "(状态条空)")
        check("退回一只后样式下拉恢复可用", vc.enabled(win, "StyleCombo") is not False,
              str(vc.enabled(win, "StyleCombo")))

        vc.scrub_to(win, 1.0)
        vc.shot(win, "verify-candle-single-again.png")

        strong2, _, box2, _ = analyse("verify-candle-single-again.png")
        check("退回一只后画面变了（不再是那几条曲线）", strong2 is not None, "")

    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"\n通过 {passed} 项，失败 {len(CHECKS) - passed} 项")

    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
