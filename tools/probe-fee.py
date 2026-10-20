"""费率：默认（A 股口径）下的成本与收益，再把四个数归零对照一遍。

只回答一件事：券商 App 上那个摊薄成本（超图 6.544 / 中望 14.444）能不能对上，对上了之后
当日收益少掉多少。
"""

import os
import re
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

PAGE = "实时持仓收益"
DETAIL = re.compile(r"^(?:[\d,]+\s*股\s*·\s*成本\s*[¥HK$]|已清仓)")

BOXES = ["FeeCommission", "FeeMinimum", "FeeStamp", "FeeTransfer"]


def texts(win):
    return [c.Name for c in winui.find_all(win, lambda c: c.Name, limit=30) if c.Name]


def rows(win):
    return [name for name in texts(win) if DETAIL.match(name)]


def summary(win):
    for name in texts(win):
        if "收益" in name and "分钟点" in name:
            return name

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

    return winui.invoke_click(item)


def set_fee(win, name, text):
    box = winui.find(win, lambda c: c.AutomationId == name)

    if box is None:
        print("   找不到 %s" % name)
        return False

    inner = winui.find(box, lambda c: c.ControlTypeName == "EditControl")

    if inner is not None:
        inner.GetValuePattern().SetValue(text)
        inner.SendKey(auto.Keys.VK_TAB)
    else:
        box.GetValuePattern().SetValue(text)

    time.sleep(0.4)

    return True


def show(tag, win):
    print("\n%s" % tag)
    print("   %s" % (summary(win) or "（没有状态行）"))

    for line in rows(win)[:3]:
        print("   %s" % line)


def main():
    winui.kill(winui.EXE)

    win = winui.launch(winui.EXE)

    if win is None:
        print("起不来")
        return 1

    win.SetActive()
    time.sleep(1)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass

    if not goto(win, PAGE):
        print("进不了页")
        return 1

    for _ in range(40):
        if summary(win):
            break

        time.sleep(2)

    scrub = winui.find(win, lambda c: c.AutomationId == "Scrub")

    if scrub is not None:
        scrub.GetRangeValuePattern().SetValue(1.0)
        time.sleep(2)

    show("默认费率（万 2.5 / 最低 5 / 千 0.5 / 万 0.1）", win)

    for name in BOXES:
        set_fee(win, name, "0")

    time.sleep(6)

    for _ in range(30):
        if summary(win):
            break

        time.sleep(2)

    if scrub is not None:
        scrub.GetRangeValuePattern().SetValue(1.0)
        time.sleep(2)

    show("四项归零（不计手续费）", win)

    winui.kill(winui.EXE)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
