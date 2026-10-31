#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把午休开关量出来，而不是靠猜。

读者报的是：在「持仓·大盘 双屏」页，开关**没勾**时曲线上却留着午休那一段，
**勾上**反而没了——正好反了。要么是开关接反了，要么是它根本没挪动画面。
两件事用同一个量法就能分开：同一张图、同一份数据，只动开关，量午休在曲线上
留下的那段平线。

量法：取预览画布里收益曲线的上沿，逐列记高度。午休**在轴上**时，因为那一个半小时
没有成交价变动，曲线必然是一长串同高的列；**不在轴上**时它被压成一条缝，
这种长平段根本不会出现。于是：

    勾上 → 出现一段很长的同高列
    不勾 → 没有这种长段

两个页面都跑：它们画的是同一本账，一个钟头不能有两套规矩，就像一天不能有两个起点。
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))

import numpy as np
from PIL import Image

import winui

ART = os.path.join(HERE, "artifacts")
PAGES = [("持仓·大盘 双屏", "board"), ("实时持仓收益", "plain")]


def goto(win, title):
    for item in winui.find_all(win, lambda c: c.ControlTypeName == "ListItemControl", limit=40):
        try:
            name = item.Name or ""
        except Exception:  # noqa: BLE001
            continue

        if title in name or name in title:
            winui.invoke_click(item)
            return True

    return False


def lunch_box(win):
    return winui.find(win, lambda c: c.ControlTypeName == "CheckBoxControl"
                      and "午" in (c.Name or ""))


def top_edge(path):
    """画布内每列曲线的高度（画布内行号）。"""
    img = Image.open(path).convert("RGB")
    box = winui.canvas_box(img)

    if box is None:
        return np.array([]), 0

    left, right, top, bottom = box
    small = np.asarray(img, dtype=np.int16)[top:bottom, left:right]

    r, g, b = small[:, :, 0].astype(int), small[:, :, 1].astype(int), small[:, :, 2].astype(int)
    red = (r > 150) & (r - g > 50) & (r - b > 50)
    green = (g > 120) & (g - r > 40) & (g - b > 40)
    mask = red | green

    heights = []
    for x in range(mask.shape[1]):
        rows = np.flatnonzero(mask[:, x])
        heights.append(float(rows.min()) if rows.size else float("nan"))

    return np.array(heights), int(mask.sum())


def widest_flat(heights, tol=1.2):
    """曲线连续保持同一高度的最宽列数与位置。"""
    xs = np.flatnonzero(np.isfinite(heights))

    if xs.size == 0:
        return 0, 0, 0

    best, run, end = 0, 1, xs[0]

    for i in range(1, xs.size):
        left, here = xs[i - 1], xs[i]

        if here == left + 1 and abs(heights[here] - heights[left]) <= tol:
            run += 1

            if run > best:
                best, end = run, here
        else:
            run = 1

    return best, end - best + 1, end


def look(win, tag, want):
    box = lunch_box(win)

    if box is None:
        return None

    pattern = box.GetTogglePattern()

    if pattern.ToggleState != want:
        pattern.Toggle()
        time.sleep(10)

    time.sleep(5)

    path = os.path.join(ART, f"lunch-{tag}-{'on' if want else 'off'}.png")
    winui.shot(win, path)

    heights, lit = top_edge(path)

    return widest_flat(heights), lit, path


def main():
    os.makedirs(ART, exist_ok=True)

    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(4)

    # 窗口太小的话，预览画布按比缩放，量出来的列数不可比。
    try:
        import uiautomation as auto

        win.ShowWindow(auto.WindowVisualState.Maximized)
        time.sleep(2)
    except Exception:  # noqa: BLE001
        pass

    failures = []

    for title, tag in PAGES:
        if not goto(win, title):
            failures.append("找不到导航项 " + title)
            continue

        time.sleep(6)

        combo = winui.find(win, lambda c: c.AutomationId == "ScopeCombo")

        if combo is None:
            failures.append(title + ": 找不到 持仓范围 下拉框")
            continue

        for attempt in range(3):
            try:
                winui.combo_pick(win, combo, "A股+港股通")
                break
            except Exception:  # noqa: BLE001 - UIA 偶发 COM 错误，重开一次弹层即可
                time.sleep(2)

        time.sleep(16)

        off = look(win, tag, want=0)
        on = look(win, tag, want=1)

        if off is None or on is None:
            failures.append(title + ": 找不到 午休 复选框")
            continue

        print("")
        print("=== " + title + " ===")
        print("  未选中：最长平段 %dpx  (列 %d..%d)  曲线像素 %d" % (off[0][0], off[0][1], off[0][2], off[1]))
        print("  选中　：最长平段 %dpx  (列 %d..%d)  曲线像素 %d" % (on[0][0], on[0][1], on[0][2], on[1]))

        ok = off[1] > 0 and on[1] > 0 and on[0][0] > off[0][0] + 20
        print("  " + ("PASS" if ok else "FAIL") + " 只有勾上，轴上才留午休那一段")

        if not ok:
            failures.append(title + ": 午休开关没按预期改变画面")

        # 收尾：把开关留在未选中、把账本留在 A股。
        try:
            winui.combo_pick(win, combo, "A股")
        except Exception:  # noqa: BLE001
            pass

        time.sleep(8)

    print("")
    print("判定:", "全部通过" if not failures else "未通过")

    for line in failures:
        print("  -", line)

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
