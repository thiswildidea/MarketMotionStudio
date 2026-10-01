# -*- coding: utf-8 -*-
"""验证「动画背景 → 颜色 → 不透明度」这条链。

不透明度是颜色的第四个参数，它断掉时用户看到的话和颜色断掉时一样——「改了没反应」。
所以这里查的是**两个方向**而不是一个：

1. 颜色类型下「不透明度」滑条确实在（面板与类型连上了）；
2. 滑条能设到 20，读回是 20（控件与设置对象连上了）；
3. 100% 时设置页渐变条上端就是所选的红（满值＝原来没有这个滑条时的表现）；
4. 降到 20% 后同一处明显变淡，但仍带红（设置对象与界面反馈连上了，且淡的是
   "透出底色"而不是"变成别的颜色"）；
5. 图表页的预览面同样变淡（设置对象与渲染器连上了——预览与导出同一渲染器，
   这一处就是文件里那一处）；
6. 重启后读回仍是 20（设置对象与磁盘连上了）；
7. 换成图片类型后这个滑条不在（它只管颜色，不该出现在图片下）。

判定靠像素，不靠"应该生效"。
用法：python tools/verify-frame-strength.py
"""

import importlib.util
import os
import sys
import time

import numpy as np
import uiautomation as auto
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "vbc", os.path.join(HERE, "verify-backdrop-colour.py"))
vbc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vbc)

TOP_HEX = "#FF0000"
BOTTOM_HEX = "#0000FF"
FULL = 100
FAINT = 20


def slider(win):
    return vbc.find(lambda c: c.AutomationId == "FrameStrengthSlider", win)


def slider_value(win):
    """读滑条的当前值。

    Slider 走 RangeValue，值在 `Value` 上（不是 `CurrentValue`），最小/最大也在
    同一个 pattern 上——顺手把它们打印出来，因为范围本身就是这次要验的东西之一。
    """
    control = slider(win)

    if control is None:
        return None

    p = vbc.pat(control, auto.PatternId.RangeValuePattern)

    if p is None:
        return None

    try:
        return p.Value
    except Exception:
        return None


def slider_range(win):
    p = vbc.pat(slider(win), auto.PatternId.RangeValuePattern)

    if p is None:
        return None

    try:
        return p.Minimum, p.Maximum
    except Exception:
        return None


def set_slider(win, wanted):
    """按人的做法：把滑条设成某个值。

    RangeValue.SetValue 优先；不支持时退到点一下再按方向键，因为键盘才是用户
    真正会用的那条路。
    """
    control = slider(win)

    if control is None:
        return None

    p = vbc.pat(control, auto.PatternId.RangeValuePattern)

    if p is not None:
        try:
            p.SetValue(float(wanted))
            time.sleep(1.2)
            return slider_value(win)
        except Exception:
            pass

    vbc.invoke_click(control)
    auto.SendKeys("{Home}", waitTime=0.4)

    step = 5
    for _ in range(int((wanted - 20) / step)):
        auto.SendKeys("{Right}", waitTime=0.12)

    time.sleep(1.2)

    return slider_value(win)


def bar_colours(win, path):
    """设置页渐变条上端与下端的颜色。

    定位那一段在 `verify-backdrop-colour.py` 里，两个脚本共用一份：它要处理的
    不是"渐变条在按钮下方多少像素"，而是"截图和 UIA 的坐标差多少"——那个差值
    随窗口边框走，两边各写一份就会一边对一边错。
    """
    upper, lower, _ = vbc.gradient_bar(win, path)

    return upper, lower


def preview_top(win, path):
    """预览面上端那一条的颜色。"""
    span = vbc.frame_rows(path)

    if span is None:
        return None

    top, bottom = span
    height = bottom - top

    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    band = a[:, 460:880]

    return band[top + 8: top + int(height * 0.12)].reshape(-1, 3).mean(axis=0)


def main():
    win = vbc.restart_and_wait()

    if win is None:
        print("窗口未找到")
        return 1

    print("window:", win.Name)

    if not vbc.goto(win, "NavSettingsItem"):
        print("设置页进不去")
        return 1

    combo = vbc.require(win, "FrameBackdropCombo")
    print("kind ->", vbc.combo_select(combo, 1))
    time.sleep(1.2)

    vbc.check("设置页能滚到动画背景卡片", vbc.bring_into_view(win, "TopColourButton"))

    # ---- 1) 滑条在

    vbc.check("颜色类型下「不透明度」滑条出现", slider(win) is not None)
    vbc.check("不透明度范围是 20–100", slider_range(win) == (20.0, 100.0), str(slider_range(win)))

    # ---- 2) 两个颜色就位

    top_now = vbc.set_colour(win, "TopColourButton", TOP_HEX)
    bottom_now = vbc.set_colour(win, "BottomColourButton", BOTTOM_HEX)

    vbc.check("顶部颜色写入并读回", top_now == TOP_HEX, f"读回 {top_now}")
    vbc.check("底部颜色写入并读回", bottom_now == BOTTOM_HEX, f"读回 {bottom_now}")

    # ---- 3) 100%：渐变条上端就是所选的红

    # 每次截图前都要重新滚回来：开取色器的浮层会把卡片顶走，采样点也就跟着走，
    # 采到的就变成卡片空白处那种浅灰，看起来像"渐变条没画"。
    vbc.bring_into_view(win, "TopColourButton")
    print("opacity ->", set_slider(win, FULL))
    vbc.check("不透明度能设到 100", slider_value(win) == FULL, f"读回 {slider_value(win)}")

    vbc.bring_into_view(win, "TopColourButton")
    full_shot = vbc.shot(win, "verify-frame-strength-full.png")
    full_upper, _ = bar_colours(win, full_shot)

    vbc.check("100% 时渐变条上端是所选的红色",
              full_upper[0] > 200 and full_upper[2] < 70,
              f"rgb={tuple(full_upper.round(0))}")

    # ---- 4) 预览面在 100% 时就是所选的红

    vbc.goto(win, "NavMarketTurnover")
    full_preview = vbc.shot(win, "verify-frame-strength-full-preview.png")
    full_frame = preview_top(win, full_preview)

    vbc.check("图表页找到 9:16 预览面", full_frame is not None,
              str(full_frame.round(0)) if full_frame is not None else "")

    if full_frame is None:
        return 1

    vbc.check("预览面 100% 时就是所选的红",
              full_frame[0] > 200 and full_frame[2] < 70,
              f"rgb={tuple(full_frame.round(0))}")

    # ---- 5) 20%：设置页与预览面一起变淡，但仍带红

    vbc.goto(win, "NavSettingsItem")
    vbc.bring_into_view(win, "TopColourButton")
    print("opacity ->", set_slider(win, FAINT))
    vbc.check("不透明度能设到 20", slider_value(win) == FAINT, f"读回 {slider_value(win)}")

    vbc.bring_into_view(win, "TopColourButton")
    faint_shot = vbc.shot(win, "verify-frame-strength-faint.png")
    faint_upper, _ = bar_colours(win, faint_shot)

    vbc.check("20% 时渐变条上端变淡",
              faint_upper[0] < full_upper[0] - 60,
              f"rgb={tuple(faint_upper.round(0))}，100% 时 {tuple(full_upper.round(0))}")
    vbc.check("20% 时仍带所选的红（是透出底色，不是换成别的颜色）",
              faint_upper[0] > faint_upper[2] + 20,
              f"rgb={tuple(faint_upper.round(0))}")

    vbc.goto(win, "NavMarketTurnover")
    faint_preview = vbc.shot(win, "verify-frame-strength-faint-preview.png")
    faint_frame = preview_top(win, faint_preview)

    vbc.check("预览面上端在 20% 时明显淡于 100%",
              faint_frame is not None and faint_frame[0] < full_frame[0] - 60,
              f"20% {tuple(faint_frame.round(0)) if faint_frame is not None else None} "
              f"/ 100% {tuple(full_frame.round(0))}")

    # ---- 6) 重启后还在（值停在 20，没有在上一趟被改回 100）

    win = vbc.restart_and_wait()

    if win is None:
        vbc.check("重启后窗口能打开", False)
        return 1

    vbc.goto(win, "NavSettingsItem")
    vbc.bring_into_view(win, "TopColourButton")

    vbc.check("重启后不透明度仍是 20", slider_value(win) == FAINT, f"读回 {slider_value(win)}")

    # ---- 7) 图片类型下不该有这个滑条

    combo = vbc.require(win, "FrameBackdropCombo")
    print("kind ->", vbc.combo_select(combo, 2))
    time.sleep(1.2)

    vbc.check("图片类型下没有不透明度滑条（它只管颜色）", slider(win) is None)

    passed = sum(1 for c in vbc._checks if c)
    print(f"\n{passed}/{len(vbc._checks)} 通过")

    return 0 if passed == len(vbc._checks) else 1


if __name__ == "__main__":
    sys.exit(main())
