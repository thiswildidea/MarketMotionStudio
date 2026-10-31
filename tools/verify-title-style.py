#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把两层标题样式量出来，而不是靠看——新链路版。

页面右栏只剩一枚标题徽章和一个齿轮；齿轮弹出两个浮动窗口（主标题 / 副标题），旋转是
窗口里的滑杆。量法同一窗口、同一份数据，只动一个旋钮，量预览画布标题带/副标题带像素：

    主标题窗口 旋转 8°   → 标题带像素相对基线大幅变化（转动了）
    副标题窗口 填两行    → 副标题带从空变亮（行出现了）
    主标题窗口 旋转 -8°  → 标题带再次变化（本地的选择活着）
    清掉本地旋转 + 全局字号 90 → 标题再变（未配置项回退全局）
    重启                → 副标题仍在（本地配置落了盘）
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
MAIN_TITLE = "实时持仓收益"

SUBTITLE_TEXT = "午后开盘赚四千\n收盘倒亏两千五"

results = []


def check(name, ok, detail):
    results.append((name, ok, detail))
    print(("PASS" if ok else "FAIL"), name, "--", detail)


def goto(win, title):
    """精确名匹配 + 需要时滚动导航——「持仓收益」是「实时持仓收益」的子串，
    子串匹配会点错页。"""
    for _ in range(12):
        items = winui.find_all(win, lambda c: c.ControlTypeName == "ListItemControl", limit=60)
        exact = [i for i in items if (i.Name or "") == title]

        if exact:
            winui.invoke_click(exact[0])
            time.sleep(1.5)

            return True

        sv = winui.find(
            win, lambda c: getattr(c, "AutomationId", "") == "MenuItemsScrollViewer")

        if sv is None:
            break

        try:
            sv.GetPattern(winui.auto.PatternId.ScrollPattern).Scroll(
                winui.auto.ScrollAmount.NoAmount, winui.auto.ScrollAmount.SmallIncrement)
        except Exception:  # noqa: BLE001
            break

        time.sleep(0.4)

    return False


def by_id(win, automation_id, limit=80):
    return winui.find(
        win, lambda c: getattr(c, "AutomationId", "") == automation_id, limit=limit)


def ready(win):
    """页面取到数据（导出可用）才算就绪。"""
    for _ in range(60):
        export = by_id(win, "ExportButton")

        if export is not None and export.IsEnabled:
            return True

        time.sleep(1)

    return False


def shot(win, name):
    path = os.path.join(ART, name)
    winui.shot(win, path)

    return path


def bands(path):
    """画布内标题带与副标题带的亮像素数与像素阵。"""
    img = Image.open(path).convert("RGB")
    box = winui.canvas_box(img)

    if box is None:
        return None

    left, right, top, bottom = box
    height = bottom - top
    arr = np.asarray(img, dtype=np.int16)

    title = arr[top:top + int(height * 0.16), left:right]
    sub = arr[top + int(height * 0.16):top + int(height * 0.30), left:right]

    def bright(a):
        return int(((a.sum(axis=2) > 330)).sum())

    return {
        "title": title,
        "sub": sub,
        "title_bright": bright(title),
        "sub_bright": bright(sub),
    }


def diff(a, b):
    if a is None or b is None:
        return 0.0

    h = min(a.shape[0], b.shape[0])
    w = min(a.shape[1], b.shape[1])

    if h == 0 or w == 0:
        return 0.0

    d = np.abs(a[:h, :w].astype(int) - b[:h, :w].astype(int)).max(axis=2)

    return float((d > 40).mean())


def open_dialog(win, item_id, seconds=4):
    """点齿轮，点弹出菜单里的那一项，等浮动窗口出现（认主按钮「确定」）。"""
    gear = by_id(win, "TitleGear")

    if gear is None:
        return False

    winui.invoke_click(gear)
    time.sleep(0.8)

    item = by_id(win, item_id)

    if item is None:
        return False

    winui.invoke_click(item)

    for _ in range(seconds * 4):
        if by_id(win, "RotationSlider") is not None or by_id(win, "ShowCheck") is not None:
            time.sleep(0.5)

            return True

        time.sleep(0.25)

    return False


def primary_ok(win):
    """点浮动窗口的主按钮（确定）。ContentDialog 的按钮是普通 Button，按文本认。"""
    def is_primary(c):
        return c.ControlTypeName == "ButtonControl" and (c.Name or "") in ("确定", "OK")

    button = winui.find(win, is_primary, limit=80)

    if button is None:
        return False

    winui.invoke_click(button)
    time.sleep(1.5)

    return True


def set_rotation(win, degrees):
    """主标题窗口里把旋转滑杆拖到目标角度。RangeValue 就是滑杆的拖拽结果。
    先取消「跟随全局」——上一轮收拾留下的勾选会让滑杆 disabled。"""
    slider = by_id(win, "RotationSlider")
    follow = by_id(win, "RotationFollow")

    if slider is None:
        return False

    if follow is not None:
        try:
            state = follow.GetPattern(winui.auto.PatternId.TogglePattern).ToggleState

            if state == winui.auto.ToggleState.On:
                follow.GetPattern(winui.auto.PatternId.TogglePattern).Toggle()
                time.sleep(0.4)
        except Exception:  # noqa: BLE001
            pass

    slider.GetPattern(winui.auto.PatternId.RangeValuePattern).SetValue(float(degrees))
    time.sleep(0.6)

    return primary_ok(win)


def set_subtitle(win, text):
    """副标题窗口里填文本、确保显示开着，确认。"""
    box = by_id(win, "SubTextBox")
    toggle = by_id(win, "ShowCheck")

    if box is None or toggle is None:
        return False

    try:
        state = toggle.GetPattern(winui.auto.PatternId.TogglePattern).ToggleState

        if state != winui.auto.ToggleState.On:
            toggle.GetPattern(winui.auto.PatternId.TogglePattern).Toggle()
            time.sleep(0.4)
    except Exception:  # noqa: BLE001
        pass

    box.GetValuePattern().SetValue(text)
    time.sleep(0.6)

    return primary_ok(win)


def clear_local_rotation(win):
    """主标题窗口里把旋转交还全局（勾上「跟随全局」）。"""
    slider = by_id(win, "RotationSlider")
    follow = by_id(win, "RotationFollow")

    if slider is None or follow is None:
        return False

    try:
        state = follow.GetPattern(winui.auto.PatternId.TogglePattern).ToggleState

        if state != winui.auto.ToggleState.On:
            follow.GetPattern(winui.auto.PatternId.TogglePattern).Toggle()
            time.sleep(0.4)
    except Exception:  # noqa: BLE001
        return False

    return primary_ok(win)


def zero_local_rotation(win):
    """主标题窗口里把滑杆拖回 0（取消「跟随全局」再拖）。"""
    slider = by_id(win, "RotationSlider")
    follow = by_id(win, "RotationFollow")

    if slider is None or follow is None:
        return False

    try:
        state = follow.GetPattern(winui.auto.PatternId.TogglePattern).ToggleState

        if state == winui.auto.ToggleState.On:
            follow.GetPattern(winui.auto.PatternId.TogglePattern).Toggle()
            time.sleep(0.4)
    except Exception:  # noqa: BLE001
        pass

    slider.GetPattern(winui.auto.PatternId.RangeValuePattern).SetValue(0.0)
    time.sleep(0.6)

    return primary_ok(win)


def main():
    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(3)
    win = winui.app_window("MarketMotionStudio.exe")
    assert goto(win, MAIN_TITLE), "进不去实时持仓收益页"
    assert ready(win), "页面没有取到数据（导出按钮一直不可用）"

    time.sleep(2)

    # -1. 标题得是可见的：隐藏标题开关若开着，主副标题都被藏掉，旋转/副标题全量不出来。
    #     开关在徽章正下方，先确保它「关」（显示）。
    toggle = by_id(win, "HideTitleToggle")

    if toggle is not None:
        tp = winui.auto.PatternId.TogglePattern

        if toggle.GetPattern(tp).ToggleState == winui.auto.ToggleState.On:
            toggle.GetPattern(tp).Toggle()
            time.sleep(2)

    # 0. 基线必须是无副标题的：上一轮留下的演示副标题先清掉，否则副标题带
    #    一开始就是亮的，「从空变亮」量不出来。
    assert open_dialog(win, "EditSubtitle"), "副标题浮动窗口没打开（清基线）"
    assert set_subtitle(win, ""), "副标题清不掉"
    time.sleep(2)

    # 0.5 旋转也归零：上一轮留下的本地旋转会让「8° 变化」量不出来（基线已经转了）。
    assert open_dialog(win, "EditMainTitle"), "主标题窗口没打开（归零旋转）"
    assert zero_local_rotation(win), "旋转归零失败"
    time.sleep(2)

    base = bands(shot(win, "title-a-base.png"))
    check("基线可读", base is not None, f"标题带亮像素 {base and base['title_bright']}")

    # 1. 主标题窗口里旋转 8°：标题带像素必须动。
    assert open_dialog(win, "EditMainTitle"), "主标题浮动窗口没打开"
    assert set_rotation(win, 8), "旋转滑杆拖不动"
    time.sleep(2)
    rot = bands(shot(win, "title-b-rot8.png"))
    moved = diff(base["title"], rot["title"])
    check("主标题旋转生效（滑杆 8°）", moved > 0.02, f"标题带变化率 {moved:.3f}")

    # 2. 副标题窗口里填两行：副标题带明显变亮——基线里那条琥珀色日期行也在带内，
    #    所以量相对倍数而不是绝对阈值。
    assert open_dialog(win, "EditSubtitle"), "副标题浮动窗口没打开"
    assert set_subtitle(win, SUBTITLE_TEXT), "副标题文本写不进去"
    time.sleep(2)
    sub = bands(shot(win, "title-c-sub.png"))
    check(
        "副标题出现",
        sub["sub_bright"] > base["sub_bright"] * 1.5,
        f"副标题带亮像素 {base['sub_bright']} → {sub['sub_bright']}")

    # 3. 本地选择仍活着：再开主标题窗口改到 -8°，标题带必须再动一次。
    assert open_dialog(win, "EditMainTitle"), "主标题浮动窗口开不了第二次"
    assert set_rotation(win, -8), "旋转改不到 -8°"
    time.sleep(2)
    rot2 = bands(shot(win, "title-d-rotm8.png"))
    moved2 = diff(sub["title"], rot2["title"])
    check("本地覆盖再改仍生效", moved2 > 0.02, f"标题带变化率 {moved2:.3f}")

    # 4. 未配置的项回退全局：把本地旋转交还全局（跟随全局），设置页只设字号 90。
    assert open_dialog(win, "EditMainTitle"), "第三次开不了主标题窗口"
    assert clear_local_rotation(win), "交不还全局"
    time.sleep(1.5)

    assert goto(win, "设置"), "进不去设置页"
    size = by_id(win, "TitleSizeSlider", limit=120)
    sizeDefault = by_id(win, "TitleSizeDefault", limit=120)
    tp = winui.auto.PatternId.TogglePattern

    if sizeDefault.GetPattern(tp).ToggleState == winui.auto.ToggleState.On:
        sizeDefault.GetPattern(tp).Toggle()
        time.sleep(0.5)

    size.GetPattern(winui.auto.PatternId.RangeValuePattern).SetValue(90.0)
    time.sleep(1.5)

    assert goto(win, MAIN_TITLE), "回不去实时持仓收益页"
    time.sleep(3)
    big = bands(shot(win, "title-e-global90.png"))
    grew = diff(rot2["title"], big["title"])
    check("未配置项回退全局（全局字号 90 生效）", grew > 0.02, f"标题带变化率 {grew:.3f}")

    # 收拾全局字号，别让它默默影响后面的日子。
    assert goto(win, "设置"), "进不去设置页"
    sizeDefault = by_id(win, "TitleSizeDefault", limit=120)

    if sizeDefault.GetPattern(tp).ToggleState != winui.auto.ToggleState.On:
        sizeDefault.GetPattern(tp).Toggle()
        time.sleep(0.5)

    # 5. 本地配置落盘：重启后副标题仍在。
    winui.kill("MarketMotionStudio.exe")
    time.sleep(3)
    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(3)
    win = winui.app_window("MarketMotionStudio.exe")
    assert goto(win, MAIN_TITLE), "重启后进不去页面"
    assert ready(win), "重启后页面没有取到数据"
    time.sleep(2)
    again = bands(shot(win, "title-f-restart.png"))
    check(
        "重启后副标题保持",
        again["sub_bright"] > rot2["sub_bright"] * 0.6 and again["sub_bright"] > 800,
        f"副标题带亮像素 {again['sub_bright']}（重启前 {rot2['sub_bright']}）")

    # 收拾：旋转先交还全局再拖回 0，副标题留作演示。
    assert open_dialog(win, "EditMainTitle"), "收拾时开不了主标题窗口"
    assert zero_local_rotation(win), "旋转归零失败"

    # 6. 隐藏标题开关同控主副：开着时主+副一起藏，副标题带亮像素塌到近 0。
    toggle = by_id(win, "HideTitleToggle")

    if toggle is not None:
        tp = winui.auto.PatternId.TogglePattern

        # 确保「开」（隐藏）
        if toggle.GetPattern(tp).ToggleState != winui.auto.ToggleState.On:
            toggle.GetPattern(tp).Toggle()
            time.sleep(2)

        hidden = bands(shot(win, "title-g-hide.png"))
        # 副标题带是主判据：副标题藏掉后它塌到日期行的固有琥珀色（约 449），
        # 相对显示时（2000+）砍掉近八成。标题带不能这么量——标题让位后日期/
        # 时钟上移，反而更亮，所以只拿副标题带说事。
        check(
            "隐藏标题同控主副",
            hidden is not None
            and hidden["sub_bright"] < again["sub_bright"] * 0.5,
            f"隐藏后 副标题带 {hidden and hidden['sub_bright']} / 标题带 "
            f"{hidden and hidden['title_bright']}（显示时 {again['sub_bright']} / {again['title_bright']}）")

        # 复位：关掉（显示），别把隐藏状态留给下次。
        if toggle.GetPattern(tp).ToggleState == winui.auto.ToggleState.On:
            toggle.GetPattern(tp).Toggle()
            time.sleep(2)

    failed = [name for name, ok, _ in results if not ok]

    print()
    print(f"{len(results) - len(failed)}/{len(results)} PASS")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
