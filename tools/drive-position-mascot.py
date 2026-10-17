#!/usr/bin/env python3
"""真机驱动：打开「持仓收益」页 -> 勾选「显示牛熊图标」 -> 取一只标的 ->
推进到结尾（progress=1）-> 截图，证明牛熊徽标跟着曲线走到终点。

不依赖任何别的脚本的 __main__，所有 UIA 辅助都就地实现，抄自 verify-position.py 的
已验证写法（toggle_of / press / chip / clear_list / add_to_list / tick / goto /
scrub / capture）。
"""
import os
import re
import sys
import time

import uiautomation as auto
import winui

SRC_CODE = os.environ.get("MM_CODE", "sh600519")          # 单一标的：牛熊图标只在单只时画
SRC_NAME = os.environ.get("MM_NAME", "贵州茅台")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                   "artifacts", "position-mascot-end.png"))


def texts(root):
    return [c.Name for c in winui.find_all(root, lambda c: c.Name, limit=4000) if c.Name]


def status_text(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status")
    return " ".join(texts(bar)) if bar is not None else ""


def close_status(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status")
    if bar is None:
        return
    closer = winui.find(bar, lambda c: c.ControlTypeName == "ButtonControl"
                        and c.Name == "关闭")
    if closer is not None:
        try:
            press(closer, win)
            time.sleep(0.7)
        except Exception:  # noqa: BLE001
            pass


def status_until(win, patterns, seconds=360):
    deadline = time.time() + seconds
    while time.time() < deadline:
        time.sleep(1.5)
        text = status_text(win)
        if not text:
            continue
        if any(p.search(text) for p in patterns):
            return text
    return None


def toggle_of(control):
    try:
        return control.GetTogglePattern()
    except Exception:  # noqa: BLE001
        return None


def press(control, win=None):
    """按一下控件，真的按到才返回 True（矩形为空时静默跳过，这里如实报失败）。"""
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
    return winui.find(win, lambda c: c.AutomationId == code
                      and toggle_of(c) is not None)


def chip_state(win, code):
    found = chip(win, code)
    if found is None:
        return None
    pattern = toggle_of(found)
    return pattern.ToggleState if pattern is not None else None


def chip_names(win):
    out = []
    for control in winui.find_all(win, lambda c: c.ControlTypeName == "ButtonControl"):
        if toggle_of(control) is None or not control.AutomationId:
            continue
        if re.fullmatch(r"(sh|sz|bj|hk|us)[A-Za-z0-9.]+", control.AutomationId):
            out.append((control.AutomationId, control.Name))
    return out


def remove_chip(win, name):
    for control in winui.find_all(win,
                                 lambda c: c.ControlTypeName == "ButtonControl"
                                 and c.Name == name):
        kids = [t.Name for t in winui.find_all(
            control, lambda c: c.ControlTypeName == "TextControl", limit=4)]
        if any(k.strip() in ("×", "✕") for k in kids):
            return control
    return None


def clear_list(win):
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


def add_to_list(win, code, tries=3):
    """在自选搜索框里填代码并提交；返回时只要 chip 在场就算成功（名字以应用解析的为准）。"""
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
        if chip(win, code) is not None:
            return True
    return False


def tick(win, code, on, tries=3):
    for _ in range(tries):
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


def set_toggle(win, automation_id, on, tries=6):
    """把某个复选框扳到 `on` 并**读回确认**。

    `press()` 优先走 InvokePattern，而 WinUI 的复选框上 Invoke **不一定翻面**（这次真机上
    就这么静默失败了：截图里那个框还是空的）。TogglePattern.Toggle() 才是翻面的正路，
    所以这里用 Toggle 并每次读回 ToggleState，扳不动就重试，最后返回是否真的到了想要的状态。
    """
    control = winui.find(win, lambda c: c.AutomationId == automation_id)
    if control is None:
        return False
    wanted = 1 if on else 0
    for _ in range(tries):
        pat = toggle_of(control)
        if pat is not None and pat.ToggleState == wanted:
            return True
        if pat is not None:
            try:
                pat.Toggle()
            except Exception:  # noqa: BLE001
                press(control, win)
        else:
            press(control, win)
        time.sleep(0.7)
        control = winui.find(win, lambda c: c.AutomationId == automation_id)
        if control is None:
            return False
    pat = toggle_of(control)
    return pat is not None and pat.ToggleState == wanted


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl"
                      and c.Name == name)
    if item is None:
        return False
    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)
    return True


def scrub(win, progress):
    slider = winui.find(win, lambda c: c.AutomationId == "Scrub")
    if slider is None:
        return False
    slider.GetRangeValuePattern().SetValue(progress)
    time.sleep(1.8)
    return True


def maxed(win):
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


def fetch(win, seconds=360):
    done = [re.compile(r"已取")]
    close_status(win)
    button = winui.find(win, lambda c: c.AutomationId == "FetchButton")
    if button is None:
        return None, "取数按钮不在"
    if not press(button, win):
        return None, "取数按钮点不到"
    status = status_until(win, done, seconds)
    if status is None:
        return None, status_text(win) or "（状态条空）"
    return status, None


def main():
    winui.keep_awake()
    win = winui.launch("MarketMotionStudio.exe")
    if win is None:
        print("LAUNCH_FAIL")
        sys.exit(2)

    maxed(win)

    if not goto(win, "持仓收益"):
        print("NAV_FAIL")
        sys.exit(3)

    # 单一标的（牛熊图标只在非比较时绘制）
    clear_list(win)
    if not add_to_list(win, SRC_CODE):
        print("ADD_FAIL")
        sys.exit(4)
    if not tick(win, SRC_CODE, True):
        print("TICK_FAIL")
        sys.exit(5)

    # 勾选牛熊图标（TogglePattern 翻面 + 读回确认）
    if not set_toggle(win, "MascotCheck", True):
        print("MASCOT_TOGGLE_FAIL")
        sys.exit(6)
    print("MASCOT_ON: ok")

    # 取数（网络，单只约几分钟）
    status, err = fetch(win, seconds=420)
    print("FETCH:", status)
    if not status:
        print("FETCH_FAIL:", err)
        sys.exit(7)

    # 推进到结尾
    if not scrub(win, 1.0):
        print("SCRUB_FAIL")
        sys.exit(8)

    ok = winui.capture(win, OUT, tries=6)
    print("CAPTURE_OK:", ok)
    print("OUT:", OUT)
    if not ok:
        sys.exit(9)
    print("DONE")


if __name__ == "__main__":
    main()
