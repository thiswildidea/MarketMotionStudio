#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""持仓实时收益页截图：把 2026-10-19 的流水重戳成今天后，进页、等加载、拖到收盘、抓全窗口。

仅用于给开发者看效果，不改任何代码。portfolio.json 的原样还原由调用方负责。

锁屏问题：
- CaptureToImage 在锁屏时抓回的是锁屏本身；最大化窗口与锁屏同为全屏，`shot()` 的尺寸校验
  分不清，于是把锁屏当成应用窗口存下来。
- 两条对策：① 把窗口缩到非全屏（比 1920x1080 小一截），使尺寸校验能区分；② 跑一个后台线程
  每隔十几秒把鼠标挪一像素再挪回来，压住系统的空闲锁定计时器。
- 只有在会话已解锁的前提下才可能抓到。若仍判定失败，脚本会明确说 grabbed lock screen。
"""

import ctypes
import ctypes.wintypes
import os
import re
import sys
import threading
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

PAGE = "实时持仓收益"
DETAIL = re.compile(r"^(?:[\d,]+\s*股\s*·\s*成本\s*[¥HK$]|已清仓)")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")


def keep_alive(stop):
    """Tiny cursor jiggle: resets the OS idle timer without clicking anything."""
    u = ctypes.windll.user32
    while not stop.is_set():
        try:
            pt = ctypes.wintypes.POINT()
            u.GetCursorPos(ctypes.byref(pt))
            u.SetCursorPos(pt.x + 1, pt.y)
            u.SetCursorPos(pt.x, pt.y)
        except Exception:  # noqa: BLE001
            pass
        stop.wait(12)


def texts(win):
    return [c.Name for c in winui.find_all(win, lambda c: c.Name, limit=40) if c.Name]


def rows(win):
    return [n for n in texts(win) if DETAIL.match(n)]


def status(win):
    for n in texts(win):
        if "收益" in n and "分钟点" in n:
            return n
    return None


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)
    if item is None:
        return False
    for _ in range(6):
        try:
            item.GetScrollItemPattern().ScrollIntoView()
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.5)
        if item.BoundingRectangle.width() > 0:
            break
    for attempt in range(4):
        try:
            item.GetSelectionItemPattern().Select()
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2.5)
        try:
            if item.GetSelectionItemPattern().IsSelected:
                return True
        except Exception:  # noqa: BLE001
            pass
    return False


def resize(win, w=1720, h=1000):
    try:
        hwnd = win.NativeWindowHandle
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 80, 40, w, h, 0x0004)  # SWP_NOZORDER
        time.sleep(1.0)
    except Exception:  # noqa: BLE001
        pass


def main():
    stop = threading.Event()
    threading.Thread(target=keep_alive, args=(stop,), daemon=True).start()

    winui.kill(winui.EXE)
    win = winui.launch(winui.EXE)
    if win is None:
        stop.set()
        print("起不来")
        return 1

    time.sleep(2)
    resize(win)

    if not goto(win, PAGE):
        stop.set()
        print("进不了页")
        return 1

    for _ in range(60):
        if status(win):
            break
        time.sleep(2)

    # 费率框恢复 A 股默认口径（万2.5/最低5/千0.5/万0.1），覆盖探针遗留的 0。
    for name, value in (("FeeCommission", "2.5"), ("FeeMinimum", "5"),
                        ("FeeStamp", "5"), ("FeeTransfer", "0.1")):
        box = winui.find(win, lambda c: c.AutomationId == name)
        if box is None:
            continue
        inner = winui.find(box, lambda c: c.ControlTypeName == "EditControl")
        target = inner if inner is not None else box
        try:
            target.GetValuePattern().SetValue(value)
            target.SetFocus()
            auto.SendKeys("{Tab}")
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.5)

    time.sleep(3.5)

    scrub = winui.find(win, lambda c: c.AutomationId == "Scrub")
    if scrub is not None:
        try:
            scrub.GetRangeValuePattern().SetValue(1.0)
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2.5)

    print("状态:", status(win))
    for line in rows(win):
        print("  ", line)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "probe-portfolio-pnl.png")
    ok = winui.shot(win, path)
    print("saved:", path, "(verified)" if ok else "(WARNING: 抓到锁屏/尺寸不符)")

    stop.set()
    winui.kill(winui.EXE)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
