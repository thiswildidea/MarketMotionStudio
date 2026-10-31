"""Drives 管理持仓 to prove it is now an editor of the initial position.

Four things are checked, in the order a reader would meet them:

1. it opens on the baseline (not on the closing figures the page is drawing);
2. a retyped share count lands in `ledger-baseline.json`;
3. closing rebases the book — `portfolio.json` becomes that snapshot, and the archive's fills
   are put back in the journal so they walk it forward again;
4. reopening shows the edited number, not a recomputed closing figure.

Run it with the app closed; it launches its own copy.
"""

import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui

LOCAL = os.path.join(
    os.environ["LOCALAPPDATA"], "Packages", "8166Yxw.MarketMotionStudio_fzc58jprbah1t", "LocalState")

DIALOG_PAGE = "实时持仓收益"


def aid(win, name):
    return winui.find(win, lambda c, n=name: c.AutomationId == n)


def read_json(name):
    path = os.path.join(LOCAL, name)
    if not os.path.exists(path):
        return None
    return json.load(io.open(path, encoding="utf-8-sig"))


def rows_of(book):
    if isinstance(book, dict):
        for key in ("Rows", "Holdings", "Trades"):
            if key in book:
                return book[key]
        return []
    return book


def open_dialog():
    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(2.5)

    page = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == DIALOG_PAGE)
    if page is not None:
        winui.invoke_click(page)
        time.sleep(2.5)

    manage = aid(win, "ManageButton")
    if manage is None:
        raise SystemExit("ManageButton 不在页面上")

    winui.invoke_click(manage)
    time.sleep(3)

    return win


def row_boxes(win):
    """Every row's 数量/成本 box, in list order (the form's own boxes come last)."""
    boxes = winui.find_all(
        win,
        lambda c: c.ControlTypeName == "EditControl",
        limit=40,
    )

    out = []

    for box in boxes:
        try:
            name = box.Name or ""
            value = box.GetValuePattern().Value
        except Exception:  # noqa: BLE001
            continue

        if name in ("数量", "成本") and value:
            out.append((name, value, box))

    return out


def main():
    baseline = read_json("ledger-baseline.json")
    print("磁盘 基准:", baseline["Day"], "行数", len(rows_of(baseline)))
    print("  首行:", rows_of(baseline)[0]["Name"], rows_of(baseline)[0]["Shares"], rows_of(baseline)[0]["Cost"])

    win = open_dialog()

    if aid(win, "HistoryNote") is not None:
        raise SystemExit("开出来的不是持仓对话框")

    boxes = row_boxes(win)
    print(f"\n[1] 对话框里有 {len(boxes)} 个行输入框")
    for name, value, _ in boxes[:4]:
        print(f"    {name} = {value}")

    if not boxes:
        raise SystemExit("没读到行输入框")

    first_shares = boxes[0][1]
    print("    首行数量 =", first_shares,
          "→", "与基准一致" if first_shares.replace(",", "") == f"{rows_of(baseline)[0]['Shares']:.0f}" else "与基准不一致")

    # ---- 改一个数 ----
    target = "3100"
    shares_box = boxes[0][2]
    shares_box.GetValuePattern().SetValue(target)
    time.sleep(0.6)

    # 焦点离开才会提交：点一下对话框标题区
    close = winui.find(win, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "关闭")
    if close is None:
        raise SystemExit("找不到关闭按钮")

    winui.invoke_click(close)
    time.sleep(4)

    print("\n[2] 关闭后读磁盘")
    after = read_json("ledger-baseline.json")
    head = rows_of(after)[0]
    print(f"    基准首行: {head['Name']} {head['Shares']:.0f} 股 @ {head['Cost']:.4f}")
    print("    写入成功" if abs(head["Shares"] - 3100) < 0.5 else "    **没写进基准**")

    book = read_json("portfolio.json")
    book_rows = rows_of(book)
    first = book_rows[0] if book_rows else {}
    print(f"[3] 账本首行: {first.get('Name')} {first.get('Shares')} 股 · 共 {len(book_rows)} 行")
    print("    已按新起点重设" if abs((first.get("Shares") or 0) - 3100) < 0.5 else "    **账本没跟着重设**")

    # ---- 重开，看是否保持 ----
    win = open_dialog()
    boxes = row_boxes(win)
    print("\n[4] 重新打开后首行数量 =", boxes[0][1] if boxes else "（读不到）")
    print("    保持不变" if boxes and boxes[0][1].replace(",", "") == target else "    **重开后变了**")


if __name__ == "__main__":
    main()
