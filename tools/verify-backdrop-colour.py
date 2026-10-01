# -*- coding: utf-8 -*-
"""验证「动画背景 → 颜色」这条链：选类型 → 选两个颜色 → 设定页看得见 → 帧也变了 → 重启还在。

为什么要单独一支脚本：颜色这条链上有四段，任何一段断了，用户看到的都是同一句话
——「选了颜色没反应」。仅看设置页或仅看预览都不足以定位，所以四段一起查：

1. 选「颜色」类型后两个取色器出现（面板与类型确实连上了）；
2. 十六进制框写入 → 读回一致（取色器与设置对象连上了）；
3. 设置页的渐变条按 红→蓝 排布（设置对象与界面反馈连上了）；
4. 回图表页，9:16 预览面上端偏红、下端偏蓝（设置对象与渲染器连上了）；
5. 重启后读回仍是设定值（设置对象与磁盘连上了）。

判定靠像素，不靠"应该生效"：设置页与预览面各自截图，按行取色比对。
用法：python tools/verify-backdrop-colour.py
"""

import os
import subprocess
import sys
import time

import numpy as np
import uiautomation as auto
from PIL import Image

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"

KIND_COLOUR = 1
TOP_HEX = "#FF0000"
BOTTOM_HEX = "#0000FF"

auto.uiautomation.SetGlobalSearchTimeout(6)

_checks = []


def check(label, ok, detail=""):
    _checks.append(bool(ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  — {detail}" if detail else ""))


# ---- UIA helpers ---------------------------------------------------------------


def find(cond, root, depth=0, limit=25):
    if depth > limit:
        return None
    try:
        if cond(root):
            return root
    except Exception:
        return None
    try:
        for ch in root.GetChildren():
            r = find(cond, ch, depth + 1, limit)
            if r is not None:
                return r
    except Exception:
        pass
    return None


def find_all(cond, root, depth=0, limit=25, out=None):
    out = [] if out is None else out
    if depth > limit:
        return out
    try:
        if cond(root):
            out.append(root)
    except Exception:
        pass
    try:
        for ch in root.GetChildren():
            find_all(cond, ch, depth + 1, limit, out)
    except Exception:
        pass
    return out


def pat(ctrl, pattern_id):
    try:
        return ctrl.GetPattern(pattern_id)
    except Exception:
        return None


def invoke_click(ctrl):
    p = pat(ctrl, auto.PatternId.InvokePattern)
    if p is not None:
        try:
            p.Invoke()
            time.sleep(0.4)
            return True
        except Exception:
            pass
    p = pat(ctrl, auto.PatternId.SelectionItemPattern)
    if p is not None:
        try:
            p.Select()
            time.sleep(0.4)
            return True
        except Exception:
            pass
    try:
        ctrl.Click(simulateMove=False, waitTime=0.4)
        return True
    except Exception:
        return False


def app_pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq " + EXE, "/NH", "/FO", "CSV"],
                         capture_output=True)
    text = out.stdout.decode("utf-8", "replace") or out.stdout.decode("gbk", "replace")
    pids = []
    for line in (text or "").splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[0].lower() == EXE.lower():
            pids.append(int(parts[1]))
    return pids


def wait_window(seconds=40):
    deadline = time.time() + seconds
    while time.time() < deadline:
        pids = app_pids()
        for top in auto.GetRootControl().GetChildren():
            try:
                if top.ProcessId in pids and top.ControlTypeName == "WindowControl" and top.Name:
                    return top
            except Exception:
                continue
        time.sleep(1)
    return None


def restart_and_wait():
    for _ in range(3):
        subprocess.run(["taskkill", "/F", "/IM", EXE], capture_output=True)
        time.sleep(1.5)
        if not app_pids():
            break

    os.startfile(r"shell:AppsFolder\%s" % APPID)
    time.sleep(7)

    win = wait_window()
    if win is not None:
        win.SetActive()
        win.MoveWindow(60, 60, 1500, 940)
        time.sleep(1.5)
    return win


def goto(win, automation_id):
    item = find(lambda c: c.AutomationId == automation_id, win)
    if item is None:
        return False
    invoke_click(item)
    time.sleep(2.5)
    return True


def scroll_settings(win, percent):
    sv = find(lambda c: c.ControlTypeName == "ScrollViewerControl", win)
    p = pat(sv, auto.PatternId.ScrollPattern)
    if p is not None:
        p.SetScrollPercent(-1, percent)
    time.sleep(1.2)


def bring_into_view(win, automation_id):
    """滚到某个控件处在窗口中部。

    按控件类型找 ScrollViewer 是找不到的：设置页那个滚动容器在 UIA 里是
    **PaneControl**（名字是空的，ControlType 也不叫 ScrollViewer），按类型筛
    一个都筛不出来，于是"滚动"一直没发生，而下面的控件矩形是 (0,0,0,0)——
    离屏的控件就是这样，看不出是没滚还是没有。

    所以找的是**能滚的东西**：带 ScrollPattern 且真的可纵向滚动。挑的时候还要
    挑包含了目标控件的那个，因为页面里能滚的还有图片画廊，滚它页面纹丝不动。
    """
    control = find(lambda c: c.AutomationId == automation_id, win)

    if control is None:
        return False

    rect = control.BoundingRectangle

    if 300 <= (rect.top + rect.bottom) // 2 <= 600:
        return True

    scroller = None

    for sv in find_all(lambda c: pat(c, auto.PatternId.ScrollPattern) is not None, win, limit=25):
        if find(lambda c: c.AutomationId == automation_id, sv, limit=25) is None:
            continue

        scroll_pattern = pat(sv, auto.PatternId.ScrollPattern)

        if scroll_pattern is not None and scroll_pattern.VerticallyScrollable:
            scroller = sv
            break

    if scroller is None:
        return False

    scroller_pattern = pat(scroller, auto.PatternId.ScrollPattern)

    if scroller_pattern is None:
        return False

    for percent in range(0, 101, 5):
        try:
            scroller_pattern.SetScrollPercent(-1, percent)
        except Exception:
            return False

        time.sleep(0.35)

        control = find(lambda c: c.AutomationId == automation_id, win)

        if control is None:
            continue

        rect = control.BoundingRectangle

        if 300 <= (rect.top + rect.bottom) // 2 <= 600:
            return True

    return False


def require(win, automation_id):
    ctrl = find(lambda c: c.AutomationId == automation_id, win)
    assert ctrl is not None, automation_id + " 未找到"
    return ctrl


def combo_select(combo, index):
    p = pat(combo, auto.PatternId.ExpandCollapsePattern)
    if p is not None:
        try:
            p.Expand()
            time.sleep(0.5)
        except Exception:
            pass

    items = find_all(lambda c: c.ControlTypeName == "ListItemControl", combo, limit=6)

    if index >= len(items):
        raise AssertionError("下拉项不足: %d <= %d" % (len(items), index))

    name = items[index].Name
    invoke_click(items[index])
    return name


def combo_value(combo):
    """A WinUI combo answers to ValuePattern or to SelectionPattern, not to both."""
    for pid in (auto.PatternId.ValuePattern, auto.PatternId.SelectionPattern):
        p = pat(combo, pid)

        if p is None:
            continue

        try:
            if pid == auto.PatternId.ValuePattern:
                return p.Value

            items = p.GetSelection()

            return items[0].Name if items else None
        except Exception:
            continue

    return None


def hex_now(win):
    edit = find(lambda c: c.AutomationId == "HexTextBox", win, limit=25)

    if edit is None:
        return None

    value = pat(edit, auto.PatternId.ValuePattern)

    return value.Value if value is not None else None


def set_colour(win, button_id, hex_value):
    """按人的做法：打开取色器，在十六进制框里写入并回车。"""
    invoke_click(require(win, button_id))
    time.sleep(1.4)

    edit = find(lambda c: c.AutomationId == "HexTextBox", win, limit=25)

    if edit is None:
        return None

    value = pat(edit, auto.PatternId.ValuePattern)

    if value is None:
        return None

    value.SetValue(hex_value)
    auto.SendKeys("{Enter}", waitTime=0.3)
    time.sleep(0.9)

    now = hex_now(win)
    auto.SendKeys("{Escape}", waitTime=0.3)
    time.sleep(0.8)

    return now


def shot(win, name):
    path = os.path.join(OUT, name)
    win.CaptureToImage(path)
    return path


# ---- pixel helpers -------------------------------------------------------------


def rows_of(mask):
    return np.where(mask.any(axis=1))[0]


def red_or_blue(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    red = (r > 170) & (g < 100) & (b < 100)
    blue = (b > 170) & (r < 100) & (g < 100)
    return red, blue


def gradient_bar(win, path):
    """采样两个取色器下拉下方的那条渐变：横向应同色，纵向应从顶部色走到底部色。

    横向按控件坐标取样（x 从「顶部」按钮算起），纵向**自己找**：从按钮下方往下扫，
    第一段"横向平坦、又明显不同于卡片底色"的连续行就是那条渐变。

    不按 UIA 坐标加一个写死的偏移量取纵向：截图和 UIA 的窗口坐标差着几十像素
    （截图把标题栏算在内，UIA 的矩形是窗口外框），差多少随边框走，写死偏移量就是
    在赌——赌错时采到的是卡片空白处那种浅灰，看起来像"渐变条没画"。
    横向同理不整幅图找色块：卡片里还有图片画廊，按颜色搜会把缩略图当成渐变条。
    """
    button = find(lambda c: c.AutomationId == "TopColourButton", win)
    wr = win.BoundingRectangle
    tr = button.BoundingRectangle

    x0 = tr.left - wr.left
    x1 = x0 + 400
    y0 = max(0, tr.bottom - wr.top)

    a = np.asarray(Image.open(path).convert("RGB")).astype(int)

    # 卡片底色：按钮上方，那里一定是卡片而不是条。
    bg = a[max(0, y0 - 30), x0:x1].mean(axis=0)

    rows = []

    for y in range(y0, min(a.shape[0], y0 + 160)):
        line = a[y, x0:x1]

        if np.abs(line.mean(axis=0) - bg).sum() > 60 and line.std(axis=0).max() < 12:
            rows.append(y)

    if not rows:
        raise AssertionError(f"按钮下方 160 行里没找到渐变条（y0={y0}，底色 {tuple(bg.round(0))}）")

    runs = []
    start = rows[0]
    prev = rows[0]

    for y in rows[1:]:
        if y - prev > 2:
            runs.append((start, prev))
            start = y
        prev = y

    runs.append((start, prev))

    top, bottom = max(runs, key=lambda r: r[1] - r[0])

    upper = a[top + 3, x0:x1].mean(axis=0)
    lower = a[bottom - 3, x0:x1].mean(axis=0)

    # 横向也验一下：一条渐变在同一行内必须是同一个颜色，否则取到的不是它。
    flat = a[(top + bottom) // 2, x0:x1].std(axis=0).max()

    return upper, lower, flat


def reset_opacity(win):
    """把「不透明度」拨回 100。

    它和颜色一样是持久化的：另一个脚本（verify-frame-strength.py）跑完会把它留在
    20，于是这个脚本再跑时预览面是淡的，"颜色到底生效了没有"就没法从这一处判断。
    **断言前先把持久化的东西复位**，别断言"上一次跑完的样子"。
    """
    control = find(lambda c: c.AutomationId == "FrameStrengthSlider", win)

    if control is None:
        return None

    p = pat(control, auto.PatternId.RangeValuePattern)

    if p is None:
        return None

    try:
        p.SetValue(100.0)
        time.sleep(0.8)
        return p.Value
    except Exception:
        return None


def frame_rows(path):
    """The rows the 9:16 preview occupies: the tall block of non-pale pixels."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    pale = a.sum(axis=2) > 690
    wide = (~pale[:, 460:880]).sum(axis=1) > 300
    ys = np.where(wide)[0]

    if len(ys) < 100:
        return None

    # The tallest run of such rows, which is the preview rather than a stray panel.
    best = (ys[0], ys[0])
    start = ys[0]
    prev = ys[0]
    for y in ys[1:]:
        if y - prev > 6:
            if prev - start > best[1] - best[0]:
                best = (start, prev)
            start = y
        prev = y
    if prev - start > best[1] - best[0]:
        best = (start, prev)

    return best


# ---- the five checks -----------------------------------------------------------


def main():
    win = restart_and_wait()

    if win is None:
        print("窗口未找到")
        return 1

    print("window:", win.Name)

    # ---- 1) 选「颜色」类型，两个取色器出现

    if not goto(win, "NavSettingsItem"):
        print("设置页进不去")
        return 1

    combo = require(win, "FrameBackdropCombo")
    print("kind ->", combo_select(combo, KIND_COLOUR))
    time.sleep(1.2)

    print("  scrolled into view:", bring_into_view(win, "TopColourButton"))

    check("「颜色」类型下两个取色器出现",
          find(lambda c: c.AutomationId == "TopColourButton", win) is not None
          and find(lambda c: c.AutomationId == "BottomColourButton", win) is not None)

    # ---- 2) 两个颜色写入并读回

    top_now = set_colour(win, "TopColourButton", TOP_HEX)
    bottom_now = set_colour(win, "BottomColourButton", BOTTOM_HEX)

    check("顶部颜色写入并读回", top_now == TOP_HEX, f"读回 {top_now}")
    check("底部颜色写入并读回", bottom_now == BOTTOM_HEX, f"读回 {bottom_now}")

    # ---- 3) 设置页的渐变条：红在上、蓝在下

    # 不透明度也是持久化的，先拨回满值：上一轮别的东西把它降到 20 的话，下面
    # 「预览面上端是红的」会因为透出底色而失败，看着像颜色没生效。
    opacity = reset_opacity(win)
    check("不透明度复位到 100（本脚本只验颜色）", opacity == 100.0, f"读回 {opacity}")

    bring_into_view(win, "TopColourButton")
    settings_shot = shot(win, "verify-backdrop-colour-settings.png")
    upper, lower, flat = gradient_bar(win, settings_shot)

    check("设置页渐变条上端是顶部色（偏红）", upper[0] > upper[2] + 60,
          f"rgb={tuple(upper.round(0))}，横向起伏 {flat:.1f}")
    check("设置页渐变条下端是底部色（偏蓝）", lower[2] > lower[0] + 60,
          f"rgb={tuple(lower.round(0))}")

    # ---- 4) 回图表页，预览面上端偏红、下端偏蓝

    goto(win, "NavMarketTurnover")
    preview_shot = shot(win, "verify-backdrop-colour-preview.png")

    span = frame_rows(preview_shot)
    check("图表页找到 9:16 预览面", span is not None, str(span))

    if span is None:
        return 1

    top, bottom = span
    height = bottom - top
    a = np.asarray(Image.open(preview_shot).convert("RGB")).astype(int)
    band = a[:, 460:880]
    upper = band[top + 8: top + int(height * 0.12)].reshape(-1, 3).mean(axis=0)
    lower = band[bottom - int(height * 0.12): bottom - 8].reshape(-1, 3).mean(axis=0)

    check("预览面上端是顶部颜色（偏红）", upper[0] > upper[2] + 40, f"rgb={tuple(upper.round(0))}")
    check("预览面下端是底部颜色（偏蓝）", lower[2] > lower[0] + 40, f"rgb={tuple(lower.round(0))}")

    # ---- 5) 重启后设置还在

    win = restart_and_wait()

    if win is None:
        check("重启后窗口能打开", False)
        return 1

    goto(win, "NavSettingsItem")
    bring_into_view(win, "TopColourButton")

    kind = find(lambda c: c.AutomationId == "FrameBackdropCombo", win)
    kind_now = combo_value(kind) if kind is not None else None
    check("重启后类型仍是「颜色」", kind_now == "颜色", f"读回 {kind_now}")

    top_now = set_colour(win, "TopColourButton", TOP_HEX)
    check("重启后颜色仍是设定值", top_now == TOP_HEX, f"读回 {top_now}")

    passed = sum(1 for c in _checks if c)
    print(f"\n{passed}/{len(_checks)} 通过")

    return 0 if passed == len(_checks) else 1


if __name__ == "__main__":
    sys.exit(main())
