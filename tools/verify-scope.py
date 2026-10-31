"""Checks that the book-scope switch really switches books, on both pages that carry it.

Four things have to hold, and each is read off the running app rather than off the code:

* 港股通 carries the Hong Kong rows, and the mainland book carries none of them.
* The span picker is offered under  mainland book and taken away under 港股通 — which is the
  scope that can only be asked about today.
* The Connect's two fee boxes appear and disappear with it.
* The double-screen page draws the same book as the per-stock one, the scope being shared.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui

PAGE = "实时持仓收益"


def aid(win, name):
    return winui.find(win, lambda c, n=name: c.AutomationId == n)


def rows(win):
    out = []

    for control in winui.find_all(win, lambda c: c.ControlTypeName == "TextControl", limit=40):
        try:
            text = control.Name or ""
        except Exception:  # noqa: BLE001
            continue

        if "股 · 成本" in text or "已清仓" in text:
            out.append(text.strip())

    return out


def kongish(win):
    """How many of the rows on screen are priced in Hong Kong dollars."""
    return sum(1 for line in rows(win) if "HK$" in line)


def present(win, name):
    """Whether the control is on the page at all — `Collapsed` takes it out of the tree."""
    return aid(win, name) is not None


def summary(win):
    control = aid(win, "SummaryText")

    try:
        return control.Name if control is not None else ""
    except Exception:  # noqa: BLE001
        return ""


def read(win, label):
    print(f"\n=== {label} ===")
    print("  范围框:", winui.value(aid(win, "ScopeCombo")))
    print("  汇总:", summary(win))
    print("  港股行:", kongish(win), "/", len(rows(win)))

    return {
        "kong": kongish(win),
        "picker": present(win, "SpanPickerMenu"),
        "fee": present(win, "FeeKongMinimum"),
    }


def pick(win, label):
    combo = aid(win, "ScopeCombo")

    if combo is None:
        raise SystemExit("页面上没有范围切换控件")

    print(f"\n切到 {label}: {winui.combo_pick(win, combo, label)}")
    time.sleep(14)


def main():
    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(3)

    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == PAGE)

    if item is None:
        raise SystemExit("页面上没有 实时持仓收益")

    winui.invoke_click(item)
    time.sleep(12)

    # Chosen explicitly rather than assumed: the scope is remembered between runs, so whatever
    # the last visit left is what the page opens on.
    pick(win, "A股")
    plain = read(win, "实时持仓收益 · A股")

    pick(win, "A股+港股通")
    kong = read(win, "实时持仓收益 · A股+港股通")

    # The double-screen page shares the scope, so it has to be on the same book as this one left
    # it — a switch made on one page is a switch made for both.
    board = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl"
                       and "持仓" in (c.Name or "") and "大盘" in (c.Name or ""))

    if board is None:
        raise SystemExit("导航里没有双屏页")

    print("\n切到:", board.Name)
    winui.invoke_click(board)
    time.sleep(14)

    both = read(win, "持仓·大盘 双屏 · 与上一页同一本账")

    ok_kong = kong["kong"] >= 2
    ok_plain = plain["kong"] == 0
    ok_picker = plain["picker"] and not kong["picker"]
    ok_fee = not plain["fee"] and kong["fee"]

    # The double-screen page is reached while 港股通 is still the chosen book, so it has to carry
    # the same two Hong Kong rows rather than the mainland six.
    ok_both = both["kong"] == kong["kong"] and both["fee"] == kong["fee"]

    print("\n判定:")
    print("  ", "PASS" if ok_kong else "FAIL", "港股通模式带上港股持仓行")
    print("  ", "PASS" if ok_plain else "FAIL", "A股模式不带任何港股行")
    print("  ", "PASS" if ok_picker else "FAIL", "时间范围只在 A股 下可选")
    print("  ", "PASS" if ok_fee else "FAIL", "港股通费率只在该模式下出现")
    print("  ", "PASS" if ok_both else "FAIL", "双屏页跟随同一本账")

    # Left on the mainland book, which is what the app opens on by default; the switch is
    # remembered, and a verification that walks away leaving 港股通 chosen would change what the
    # reader sees next time they open it.
    pick(win, "A股")

    if not (ok_kong and ok_plain and ok_picker and ok_fee and ok_both):
        raise SystemExit("判定未通过")


if __name__ == "__main__":
    main()
