#!/usr/bin/env python3
"""Imports the reader's own 30 October workbook, then imports it a second time.

Two things to prove end to end, with the files where the reader keeps them:

  * the day's workbook goes through 导入表格 → 解析 → 导入, lands on the day the picker holds,
    and the filed table grows by exactly its rows;
  * the same workbook a second time adds nothing, and says so **before** the button is pressed.

The picker is driven the only way this machine allows: `WM_SETTEXT` into its filename box, then
a mouse click on 打开(O). A path that does not exist leaves the dialog open and the import
silently doing nothing — which is what a stray space in the filename looks like.
"""

import ctypes
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

spec = importlib.util.spec_from_file_location("probe", os.path.join(HERE, "verify-import-picker.py"))
PARTS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PARTS)

import winui  # noqa: E402

XLSX = r"C:\Users\user\Desktop\成交记录\2026-10-30今日委托记录-成交.xlsx"


def open_dialog():
    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(2)

    page = winui.find(
        win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "实时持仓收益")

    if page is not None:
        winui.invoke_click(page)
        time.sleep(2.5)

    for _ in range(3):
        if PARTS.aid(win, "HistoryNote") is not None:
            return win

        button = PARTS.aid(win, "ImportButton")

        if button is not None:
            winui.invoke_click(button)
            time.sleep(3)

        win = winui.app_window("MarketMotionStudio.exe", wait_seconds=20)

    return win


def pick_and_read(win):
    winui.invoke_click(PARTS.aid(win, "SheetButton"))
    time.sleep(3.5)

    box = PARTS.desktop_find(
        lambda c: c.ControlTypeName == "EditControl" and c.AutomationId == "1148")

    if box is None:
        print("   文件框未出现")
        return None

    PARTS.U32.SendMessageW(box.NativeWindowHandle, PARTS.WM_SETTEXT, 0, ctypes.c_wchar_p(XLSX))
    time.sleep(1.2)

    open_button = PARTS.desktop_find(
        lambda c: c.ControlTypeName == "SplitButtonControl" and c.AutomationId == "1")

    r = open_button.BoundingRectangle
    PARTS.click_at((r.left + r.right) / 2, (r.top + r.bottom) / 2)
    time.sleep(5)

    return winui.app_window("MarketMotionStudio.exe", wait_seconds=20)


def main():
    if not os.path.exists(XLSX):
        print("目标文件不存在:", XLSX)
        return 1

    win = open_dialog()
    print("1) 导入前档案:", repr(PARTS.aid(win, "HistoryNote").Name))

    win = pick_and_read(win)

    if win is None:
        return 1

    print("   解析提示 :", repr(PARTS.aid(win, "Note").Name))
    print("   粘贴框   :", repr(PARTS.aid(win, "Raw").GetValuePattern().Value.split("\n")[0]))
    print("   导入可用 :", PARTS.aid(win, "ApplyButton").IsEnabled)

    winui.invoke_click(PARTS.aid(win, "ApplyButton"))
    time.sleep(4)

    win = winui.app_window("MarketMotionStudio.exe", wait_seconds=20)
    print("2) 导入后提示:", repr(PARTS.aid(win, "Note").Name))
    print("   导入后档案:", repr(PARTS.aid(win, "HistoryNote").Name))

    # 第二次：同一份文件，应整份被判重复
    print("\n3) 再导入一次同一份")
    win = pick_and_read(win)

    if win is None:
        return 1

    print("   解析提示 :", repr(PARTS.aid(win, "Note").Name))
    print("   档案(未变):", repr(PARTS.aid(win, "HistoryNote").Name))

    out = r"D:\software\MarketMotionStudio\.workbuddy\shot-real.png"
    winui.capture(win, out)
    print("\n截图:", out)

    return 0


if __name__ == "__main__":
    sys.exit(main())
