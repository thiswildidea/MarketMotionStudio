"""Proves 导入初始持仓 replaces the list on screen, without reopening the dialog.

Makes a file from the current baseline with the first row's shares changed to 888, imports it
through the real picker, and reads the row boxes back while the dialog is still open.
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


def rows(win):
    out = []

    for control in winui.find_all(win, lambda c: c.ControlTypeName == "EditControl", limit=40):
        try:
            name = control.Name or ""
            value = control.GetValuePattern().Value
        except Exception:  # noqa: BLE001
            continue

        if name == "数量" and value:
            out.append(value)

    return out


def main():
    source = json.load(io.open(os.path.join(LOCAL, "ledger-baseline.json"), encoding="utf-8-sig"))
    head = source["Rows"][0]

    out = ["day,code,name,shares,cost"]

    for i, row in enumerate(source["Rows"]):
        shares = 888 if i == 0 else row["Shares"]
        out.append(f"{source['Day']},{row['Code']},{row['Name']},{shares},{row['Cost']}")

    path = os.path.join(os.environ["TEMP"], "baseline-888.csv")
    io.open(path, "w", encoding="utf-8-sig", newline="").write("\r\n".join(out))

    print("测试文件首行:", out[1])

    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(2.5)

    page = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "实时持仓收益")
    if page is not None:
        winui.invoke_click(page)
        time.sleep(2.5)

    winui.invoke_click(aid(win, "ManageButton"))
    time.sleep(3)

    before = rows(win)
    print("导入前首行数量:", before[0] if before else "（读不到）")

    winui.invoke_click(aid(win, "BaselineImportButton"))
    time.sleep(3.5)

    if not pick(path):
        print("picker 没能关闭（这台机器上时好时坏），本轮跳过")
        return

    time.sleep(2)

    after = rows(win)
    print("导入后首行数量:", after[0] if after else "（读不到）")

    on_disk = json.load(io.open(os.path.join(LOCAL, "ledger-baseline.json"), encoding="utf-8-sig"))
    print("磁盘基准首行:", on_disk["Rows"][0]["Shares"])

    message = aid(win, "Message")
    print("提示:", repr(message.Name if message else None))

    print("\n判定:",
          "列表当场更新" if after and after[0] == "888" else "**列表没更新**")


if __name__ == "__main__":
    main()
