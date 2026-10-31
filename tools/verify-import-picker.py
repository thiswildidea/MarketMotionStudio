#!/usr/bin/env python3
"""Drives the whole-record import with the reader's own files.

The file picker is a system dialog in another process: `ValuePattern.SetValue` on its filename
box fails with CO_E_NOTINITIALIZED, and `SendKeys` never reaches it because the focus stays with
the app's window. What does work is `WM_SETTEXT` on the box (it is a real Win32 edit control,
`NativeWindowHandle` is a real handle) followed by a **mouse click** on 打开(O) — that button is a
`SplitButtonControl` whose `InvokePattern` is a no-op.

Everything is re-read from the UIA tree on each step: an element cached across a dialog closing
comes back as a COM error rather than as "gone".
"""

import ctypes
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui  # noqa: E402
import uiautomation as auto  # noqa: E402

U32 = ctypes.windll.user32
WM_SETTEXT = 0x000C


def walk(control, depth=0, out=None):
    out = out if out is not None else []

    if depth > 14:
        return out

    for kid in control.GetChildren():
        out.append(kid)
        walk(kid, depth + 1, out)

    return out


def desktop_find(pred):
    for top in auto.GetRootControl().GetChildren():
        for c in walk(top):
            try:
                if pred(c):
                    return c
            except Exception:  # noqa: BLE001
                pass

    return None


def aid(win, name):
    return winui.find(win, lambda c, n=name: c.AutomationId == n)


def click_at(x, y):
    U32.SetCursorPos(int(x), int(y))
    time.sleep(0.3)
    U32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.08)
    U32.mouse_event(0x0004, 0, 0, 0, 0)


def pick_file(path, settle=3.5):
    """Puts `path` into the picker and confirms it. False when no picker is up."""
    box = desktop_find(
        lambda c: c.ControlTypeName == "EditControl" and c.AutomationId == "1148")

    if box is None:
        print("   [picker] 文件框未出现")
        return False

    handle = box.NativeWindowHandle
    U32.SendMessageW(handle, WM_SETTEXT, 0, ctypes.c_wchar_p(path))
    time.sleep(1.2)

    button = desktop_find(
        lambda c: c.ControlTypeName == "SplitButtonControl" and c.AutomationId == "1")

    if button is None:
        print("   [picker] 打开(O) 未找到")
        return False

    r = button.BoundingRectangle
    click_at((r.left + r.right) / 2, (r.top + r.bottom) / 2)
    time.sleep(settle)

    return True


def report(win, label):
    note = aid(win, "Note")
    button = aid(win, "ArchiveImportButton")
    history = aid(win, "HistoryNote")

    print(f"{label}")
    print(f"   提示 : {note.Name if note else None!r}")
    print(f"   按钮 : {button.Name if button else None!r}")
    print(f"   档案 : {history.Name if history else None!r}")


def main():
    csv = r"C:\Users\user\Desktop\成交记录\trades.csv"
    xlsx = r"C:\Users\user\Desktop\成交记录\2026-10-30 今日委托记录-成交.xlsx"

    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(2)

    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "实时持仓收益")

    if item:
        winui.invoke_click(item)
        time.sleep(2.5)

    winui.invoke_click(aid(win, "ImportButton"))
    time.sleep(3)

    report(win, "初始")

    # ---- 全量导入：21 日到 29 日的记录 ----
    print("\n== 全量导入 trades.csv ==")
    winui.invoke_click(aid(win, "ArchiveImportButton"))
    time.sleep(3.5)

    if not pick_file(csv):
        return 1

    win = winui.app_window("MarketMotionStudio.exe", wait_seconds=20)
    report(win, "选中文件后（应只提示，不改档案）")

    winui.invoke_click(aid(win, "ArchiveImportButton"))
    time.sleep(4)

    win = winui.app_window("MarketMotionStudio.exe", wait_seconds=20)
    report(win, "确认后")

    return 0


if __name__ == "__main__":
    sys.exit(main())
