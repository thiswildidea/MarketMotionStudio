# -*- coding: utf-8 -*-
"""冒烟验证「动画背景」：设置页改类型/取色/浓度 → 回图表页看 9:16 预览是否跟着变。

覆盖三条路径：图片（含浓度）、颜色（含取色器 hex 输入）、默认值还原。
复用 verify-background.py 的辅助（按 PID 找窗口、Invoke 点击）。
用法：python tools/verify-framebackdrop.py
"""
import os
import subprocess
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"
SETTINGS_NAMES = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки"]

# 组合框里的顺序：0 默认 / 1 颜色 / 2 图片
KIND_DEFAULT, KIND_COLOUR, KIND_PICTURE = 0, 1, 2


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


def combo_select(combo, index):
    """展开下拉并按下标点选一项。返回被选中的名字。"""
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


def set_slider(slider, value):
    p = pat(slider, auto.PatternId.RangeValuePattern)
    assert p is not None, "滑条不支持 RangeValue"
    p.SetValue(value)
    time.sleep(0.6)


def app_pids():
    p = subprocess.run(["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq " + EXE],
                       capture_output=True)
    pids = set()
    for line in p.stdout.decode("utf-8", "replace").splitlines()[1:]:
        parts = [x.strip('"') for x in line.split('","')]
        if len(parts) >= 2 and parts[0].lower() == EXE.lower():
            pids.add(int(parts[1]))
    return pids


def wait_window(timeout=40):
    deadline = time.time() + timeout
    while time.time() < deadline:
        pids = app_pids()
        if pids:
            for w in auto.GetRootControl().GetChildren():
                try:
                    if w.ControlTypeName == "WindowControl" and w.ProcessId in pids:
                        return w
                except Exception:
                    pass
        time.sleep(1)
    return None


def shot(win, name):
    win.CaptureToImage(os.path.join(OUT, name))
    print("shot:", name)


def goto_settings(win):
    nav = None
    for name in SETTINGS_NAMES:
        nav = find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name, win)
        if nav is not None:
            break
    assert nav is not None, "设置导航项未找到"
    invoke_click(nav)
    time.sleep(2)


def goto_first_page(win):
    """回到第一个图表页（市场成交额）。"""
    items = find_all(lambda c: c.ControlTypeName == "ListItemControl", win, limit=8)
    assert items, "导航项未找到"
    invoke_click(items[0])
    time.sleep(2)


def scroll_settings(win, percent):
    sv = find(lambda c: c.ControlTypeName == "ScrollViewerControl", win)
    p = pat(sv, auto.PatternId.ScrollPattern)
    if p is not None:
        p.SetScrollPercent(-1, percent)
    time.sleep(1.2)


def require(win, automation_id):
    ctrl = find(lambda c: c.AutomationId == automation_id, win)
    assert ctrl is not None, automation_id + " 未找到"
    return ctrl


def set_colour(win, button_id, hex_value):
    """打开某个取色器下拉，在十六进制框里写入颜色。"""
    button = require(win, button_id)
    invoke_click(button)
    time.sleep(1.2)

    # 取色器内部的 AutomationId 是 WinUI 模板给的（HexTextBox），不是我们起的名字。
    edit = find(lambda c: c.AutomationId == "HexTextBox", win, limit=25)

    assert edit is not None, "取色器的十六进制输入框未找到"

    was = pat(edit, auto.PatternId.ValuePattern)
    print("hex box was", was.Value if was is not None else "?")

    value = pat(edit, auto.PatternId.ValuePattern)
    assert value is not None, "十六进制输入框不支持 ValuePattern"
    value.SetValue(hex_value)
    auto.SendKeys("{Enter}")
    time.sleep(0.8)

    auto.SendKeys("{Escape}")
    time.sleep(0.8)


def main():
    pids = app_pids()
    if not pids:
        os.startfile(r"shell:AppsFolder\%s" % APPID)
        time.sleep(6)

    win = wait_window()
    assert win is not None, "窗口未找到"
    win.SetActive()
    win.MoveWindow(60, 60, 1500, 940)
    time.sleep(1.5)
    print("window:", win.Name)

    # ---- 1) 图片：选一张，看预览
    goto_settings(win)
    scroll_settings(win, 45)

    kind = require(win, "FrameBackdropCombo")
    print("kind ->", combo_select(kind, KIND_PICTURE))
    time.sleep(1.5)
    shot(win, "fb-verify-1-picture-settings.png")

    gallery = require(win, "FramePictureGallery")
    items = gallery.GetChildren()
    print("frame gallery items:", len(items))
    assert items, "动画背景画廊为空"
    invoke_click(items[0])
    time.sleep(2)
    shot(win, "fb-verify-2-picture-chosen.png")

    goto_first_page(win)
    shot(win, "fb-verify-3-preview-picture.png")

    # ---- 2) 浓度滑条：拉到最低，图片应该明显更亮
    goto_settings(win)
    scroll_settings(win, 45)
    set_slider(require(win, "FrameDimSlider"), 20)
    goto_first_page(win)
    shot(win, "fb-verify-4-preview-dim-20.png")

    # ---- 3) 颜色：给顶部一个紫色，看预览上端是否变紫
    goto_settings(win)
    scroll_settings(win, 45)
    set_slider(require(win, "FrameDimSlider"), 60)
    kind = require(win, "FrameBackdropCombo")
    print("kind ->", combo_select(kind, KIND_COLOUR))
    time.sleep(1.2)
    set_colour(win, "TopColourButton", "#7A1FA2")
    shot(win, "fb-verify-5-colour-settings.png")

    goto_first_page(win)
    shot(win, "fb-verify-6-preview-colour.png")

    # ---- 4) 还原，收尾不留痕迹：颜色回设计值，类型回「默认」
    goto_settings(win)
    scroll_settings(win, 45)
    set_colour(win, "TopColourButton", "#0C1428")
    set_colour(win, "BottomColourButton", "#060911")

    kind = require(win, "FrameBackdropCombo")
    print("kind ->", combo_select(kind, KIND_DEFAULT))
    time.sleep(1.2)
    goto_first_page(win)
    shot(win, "fb-verify-7-preview-default.png")

    print("OK")


if __name__ == "__main__":
    main()
