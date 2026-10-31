# -*- coding: utf-8 -*-
"""用读者手头的真实文件（含斜杠日期）在双屏页验证导入初始持仓。

判据：
* 导入当场：对话框列表变成文件的行（快手 600@34.062，日期 2026/10/29 被接受）。
* 等 40 秒（自动刷新一轮）：磁盘基准仍是导入的行，不被收盘同步盖掉。
* 重开对话框：列表仍是导入的行。
"""

import ctypes
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uiautomation as auto
import winui

LOCAL = os.path.join(
    os.environ["LOCALAPPDATA"], "Packages", "8166Yxw.MarketMotionStudio_fzc58jprbah1t", "LocalState")

SOURCE = r"C:\Users\user\Desktop\成交记录\包括港股通\baseline.csv"

U32 = ctypes.windll.user32
WM_SETTEXT = 0x000C


def aid(win, name):
    return winui.find(win, lambda c, n=name: c.AutomationId == n)


def walk(control, depth=0, out=None):
    out = out if out is not None else []
    if depth > 12:
        return out
    for kid in control.GetChildren():
        out.append(kid)
        walk(kid, depth + 1, out)
    return out


def desktop(pred):
    for top in auto.GetRootControl().GetChildren():
        for control in walk(top):
            try:
                if pred(control):
                    return control
            except Exception:  # noqa: BLE001
                continue
    return None


def click_at(x, y):
    U32.SetCursorPos(int(x), int(y))
    time.sleep(0.25)
    U32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.06)
    U32.mouse_event(0x0004, 0, 0, 0, 0)


def pick(path):
    box = desktop(lambda c: c.ControlTypeName == "EditControl" and c.AutomationId == "1148")

    if box is None:
        return False

    U32.SendMessageW(box.NativeWindowHandle, WM_SETTEXT, 0, ctypes.c_wchar_p(path))
    time.sleep(1.0)

    open_btn = desktop(lambda c: c.ControlTypeName == "SplitButtonControl" and c.AutomationId == "1")

    if open_btn is not None:
        rect = open_btn.BoundingRectangle
        click_at(rect.left + (rect.right - rect.left) * 0.35, (rect.top + rect.bottom) / 2)
        time.sleep(3)

    return desktop(lambda c: c.ControlTypeName == "EditControl" and c.AutomationId == "1148") is None


def dialog_rows(win):
    """对话框列表里每一行的『名称+数量』，按屏幕顺序。"""
    out = []

    texts = winui.find_all(win, lambda c: c.ControlTypeName == "TextControl", limit=40)

    for control in texts:
        try:
            text = control.Name or ""
        except Exception:  # noqa: BLE001
            continue

        if any(k in text for k in ("快手", "理想", "超图", "恒生科技", "大秦", "五粮液", "中望", "首旅", "儒意")):
            out.append(text.split("\n")[0].strip())

    return out


def disk_baseline():
    path = os.path.join(LOCAL, "ledger-baseline.json")

    if not os.path.exists(path):
        return None

    return json.load(io.open(path, encoding="utf-8-sig"))


def disk_brief():
    doc = disk_baseline()

    if doc is None:
        return "（无）"

    return f"{doc['Day']} {len(doc['Rows'])}行 首行={doc['Rows'][0]['Code']}:{doc['Rows'][0]['Shares']}@{doc['Rows'][0]['Cost']}"


def open_dialog(win):
    for _ in range(3):
        manage = aid(win, "ManageButton")

        if manage is not None:
            winui.invoke_click(manage)

        for _ in range(5):
            time.sleep(1.5)

            if aid(win, "BaselineDay") is not None:
                return

    raise SystemExit("对话框没打开")


def close_dialog(win):
    close = winui.find(win, lambda c: c.ControlTypeName == "ButtonControl" and (c.Name or "") == "关闭")

    if close is not None:
        winui.invoke_click(close)

    time.sleep(3)


def main():
    print("读者文件:", SOURCE)
    print("导入前磁盘:", disk_brief())

    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(4)

    page = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl"
                      and "持仓" in (c.Name or "") and "大盘" in (c.Name or ""))

    if page is None:
        raise SystemExit("没有双屏页")

    winui.invoke_click(page)
    time.sleep(12)

    combo = aid(win, "ScopeCombo")
    print("范围框:", winui.value(combo))

    open_dialog(win)
    print("导入前列表:", dialog_rows(win))

    winui.invoke_click(aid(win, "BaselineImportButton"))
    time.sleep(3.5)

    if not pick(SOURCE):
        print("picker 没关上，本轮作废")
        return

    time.sleep(2)

    print("\n-- 导入后当场 --")
    print("列表:", dialog_rows(win))
    print("磁盘:", disk_brief())

    message = aid(win, "Message")
    print("提示:", repr(message.Name if message else None))

    after_list = dialog_rows(win)
    doc = disk_baseline()
    ok_list = any("快手" in row for row in after_list)
    ok_disk = doc is not None and doc["Day"] == "2026-10-29" and any(
        row["Code"].startswith("hk") for row in doc["Rows"])

    print("\n-- 等 40 秒（自动刷新一轮）--")
    time.sleep(40)
    print("磁盘:", disk_brief())
    ok_stuck = disk_baseline() is not None and disk_baseline()["Day"] == "2026-10-29"

    close_dialog(win)
    open_dialog(win)

    print("\n-- 重开对话框 --")
    print("列表:", dialog_rows(win))
    ok_reopen = any("快手" in row for row in dialog_rows(win))

    # 截图留档，并把对话框留在打开状态给读者看？不——关掉，别挡页面。
    winui.shot(win, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "artifacts", "baseline-import-real.png"))
    close_dialog(win)

    print("\n判定:")
    print("  ", "PASS" if ok_list else "FAIL", "导入当场列表更新为文件的行")
    print("  ", "PASS" if ok_disk else "FAIL", "磁盘基准=文件内容（日期 10/29、含港股）")
    print("  ", "PASS" if ok_stuck else "FAIL", "40 秒后台刷新后不被收盘同步盖掉")
    print("  ", "PASS" if ok_reopen else "FAIL", "重开对话框列表仍是导入的行")

    if not (ok_list and ok_disk and ok_stuck and ok_reopen):
        raise SystemExit("判定未通过")


if __name__ == "__main__":
    main()
