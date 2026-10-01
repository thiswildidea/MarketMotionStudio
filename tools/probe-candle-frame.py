#!/usr/bin/env python
"""最大化窗口后打开 K 线页并截图，把预览面放大到能看清为止。

窗口窄的时候预览面只有两百多像素宽，一个 720 宽的帧被缩到三分之一，25px 的字
落成 8px 的糊点——那个尺寸下「字挤在一起」和「字挨在一起」看上去一样。把窗口
最大化，预览面跟着长高，帧的缩放比就上来了，表头那几行才判断得了。

用法：python tools/probe-candle-frame.py
"""

import os
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")

auto.uiautomation.SetGlobalSearchTimeout(5)


def find(control, condition):
    if control is None:
        return None
    try:
        if condition(control):
            return control
    except Exception:  # noqa: BLE001
        return None
    for child in control.GetChildren():
        found = find(child, condition)
        if found is not None:
            return found
    return None


def main():
    window = winui.app_window(winui.EXE)

    if window is None:
        print("no studio window")
        return 1

    window.SetActive()
    time.sleep(1.0)

    size = window.GetWindowPattern()
    if size is not None:
        try:
            size.SetWindowVisualState(auto.WindowVisualState.Maximized)
            time.sleep(2.0)
        except Exception as exc:  # noqa: BLE001
            print("could not maximise:", exc)

    item = find(window, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "K线")
    if item is None:
        print("no K线 nav item")
        return 1

    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)

    # 两个复选框都打开，才看得到均线图例、成交量副图，以及价格图因为让出空间而
    # 缩上去之后的样子。
    for name in ("AveragesCheck", "VolumeCheck"):
        box = find(window, lambda c, n=name: c.AutomationId == n)
        if box is None:
            print(f"{name}: missing")
            continue
        state = box.GetTogglePattern().ToggleState
        print(f"  {name:14s} {state}  label={box.Name!r}")
        if state == auto.ToggleState.Off:
            box.GetTogglePattern().Toggle()
            time.sleep(1.0)

    fetch = find(window, lambda c: c.AutomationId == "FetchButton")
    if fetch is not None:
        fetch.GetInvokePattern().Invoke()
        time.sleep(12.0)

    rect = window.BoundingRectangle
    print("window:", rect.width(), "x", rect.height())

    preview = find(window, lambda c: c.AutomationId == "Preview")
    if preview is not None:
        bounds = preview.BoundingRectangle
        print("preview:", bounds.width(), "x", bounds.height())

    path = os.path.join(OUT, "probe-candle-frame.png")

    # Pinned to the top for the moment of the grab, and only for that moment: the
    # capture is a screen copy of the window's rectangle, so anything overlapping it
    # lands in the picture. The sibling app (WorldMotionStudio) is open often enough
    # that an unpinned capture comes back showing *its* settings page, with the frame
    # behind it at half width — which reads as "the preview has gone wrong" rather
    # than as "something is in front of it".
    try:
        window.SetTopmost(True)
        time.sleep(0.8)
        window.CaptureToImage(path)
        window.SetTopmost(False)
    except Exception as exc:  # noqa: BLE001
        print("could not pin to top:", exc)
        window.CaptureToImage(path)

    print("saved:", path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
