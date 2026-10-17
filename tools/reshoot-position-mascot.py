#!/usr/bin/env python3
"""接管**已在运行**的持仓收益页（数据已取好）：把「显示牛熊图标」扳到开，
推进到结尾，重新截图。不重启、不重新取数 —— 只为把那一张图拿对。

主驱动 `drive-position-mascot.py` 里那次失败的原因：`press()` 走 InvokePattern，
在 WinUI 复选框上不翻面。这里改用 TogglePattern.Toggle() 并读回确认。
"""
import os
import sys
import time

import winui


def toggle_of(control):
    try:
        return control.GetTogglePattern()
    except Exception:  # noqa: BLE001
        return None


def set_toggle(win, automation_id, on, tries=8):
    control = winui.find(win, lambda c: c.AutomationId == automation_id)
    if control is None:
        print("  [set_toggle] control not found:", automation_id)
        return False
    wanted = 1 if on else 0
    for i in range(tries):
        pat = toggle_of(control)
        state = None if pat is None else pat.ToggleState
        print(f"  [set_toggle] try {i}: state={state} want={wanted}")
        if pat is not None and state == wanted:
            return True
        if pat is not None:
            pat.Toggle()
        time.sleep(0.7)
        control = winui.find(win, lambda c: c.AutomationId == automation_id)
        if control is None:
            return False
    pat = toggle_of(control)
    return pat is not None and pat.ToggleState == wanted


def main():
    winui.keep_awake()
    win = winui.app_window("MarketMotionStudio.exe", wait_seconds=10)
    if win is None:
        print("NO_RUNNING_APP")
        sys.exit(2)
    win.SetActive()
    time.sleep(0.8)

    if not set_toggle(win, "MascotCheck", True):
        print("MASCOT_TOGGLE_FAIL")
        sys.exit(3)
    print("MASCOT_ON")

    slider = winui.find(win, lambda c: c.AutomationId == "Scrub")
    if slider is None:
        print("NO_SCRUB")
        sys.exit(4)
    slider.GetRangeValuePattern().SetValue(1.0)
    time.sleep(1.8)
    print("SCRUBBED to 1.0")

    out = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                       "artifacts", "position-mascot-end.png"))
    ok = winui.capture(win, out, tries=6)
    print("CAPTURE_OK:", ok)
    print("OUT:", out)


if __name__ == "__main__":
    main()
