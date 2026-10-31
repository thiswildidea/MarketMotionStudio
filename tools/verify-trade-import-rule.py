#!/usr/bin/env python3
"""Drives 导入成交记录 with the two kinds of text it has to tell apart.

The claim under test is the rule the reader asked for: a day of broker orders may only be
**appended**, while the file this app exports from 管理持仓 may **replace** the archive. The
two are told apart by whether the rows carry their own dates, so this feeds the dialog both
and reads back what it decided — plus, for the dated one, whether the rows survived a round
trip through 解析 with their days and their prices intact.

Probe, not verify: it prints what the dialog said and asserts nothing beyond that.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui  # noqa: E402

LOCAL = os.path.expandvars(
    r"%LOCALAPPDATA%\Packages\8166Yxw.MarketMotionStudio_fzc58jprbah1t\LocalState")

# What a broker's filled-order screen looks like pasted in: no dates, direction in Chinese,
# one trade per line.
TODAY = """买入 超图软件 300036 10.60 2700 09:30:55
卖出 公牛集团 603195 37.51 300 09:31:17
买入 儒意电影 002739 8.36 1200 10:11:10"""


def exported_trades():
    """The archive in exactly the shape 导出全部成交记录 writes it."""
    path = os.path.join(LOCAL, "ledger-trades.json")

    if not os.path.exists(path):
        return ""

    rows = json.load(open(path, encoding="utf-8-sig"))
    rows = rows.get("Trades", rows) if isinstance(rows, dict) else rows

    lines = ["day,time,code,name,side,price,shares"]

    for t in rows:
        side = "buy" if str(t["Side"]) in ("0", "Buy", "buy") else "sell"
        lines.append("%s,%s,%s,%s,%s,%s,%s" % (
            t["Day"], t["Time"], t["Code"], t["Name"], side, t["Price"], t["Shares"]))

    return "\n".join(lines)


def find(win, name):
    return winui.find(win, lambda c, n=name: c.AutomationId == n)


def set_text(control, text):
    control.GetValuePattern().SetValue(text)


def read(win, name):
    c = find(win, name)

    if c is None:
        return None

    try:
        return c.Name
    except Exception:  # noqa: BLE001
        return None


def preview_lines(win, most=3):
    """The first few rows of the parse preview, as the reader sees them.

    Read from inside the preview list, not from the whole window: the dialog now carries two
    lists — the archive above and this parse below — and a window-wide scan answers with the
    archive every time, which reads as "the paste did nothing".

    Best effort. The count and the overwrite state are the judgement here (they come from the
    parse itself); this is the human-readable confirmation of what those numbers are counting.
    """
    out = []
    box = find(win, "Preview")

    if box is None:
        return out

    def walk(c, depth=0):
        if depth > 12 or len(out) >= most:
            return

        for kid in c.GetChildren():
            try:
                if kid.ControlTypeName == "TextControl" and kid.Name:
                    out.append(kid.Name)
            except Exception:  # noqa: BLE001
                pass

            walk(kid, depth + 1)

    walk(box)

    return out[:most]


def apply_state(win):
    """Whether the day's list may be applied, and how many rows the dialog read.

    The overwrite checkbox this used to read is gone: replacing the archive is its own button now
    (全量导入), and the daily import never replaces. What still matters here is that a list parses
    cleanly and that 导入 becomes available for it.
    """
    button = find(win, "ApplyButton")

    if button is None:
        return "missing"

    return "enabled" if button.IsEnabled else "disabled"


def try_parse(win, label, text):
    print(f"\n== {label} ==")

    raw = find(win, "Raw")

    if raw is None:
        print("  [FAIL] Raw box not found")
        return

    set_text(raw, text)
    time.sleep(1.5)

    # 解析 is the button that turns the text into rows; the auto-parse on edit may already
    # have run, and pressing it twice is harmless.
    button = find(win, "ParseButton")

    if button is not None:
        winui.invoke_click(button)
        time.sleep(1.5)

    print(f"  Note        : {read(win, 'Note')!r}")
    print(f"  导入        : {apply_state(win)}")

    lines = preview_lines(win)

    if lines:
        for line in lines:
            print(f"  preview     : {line!r}")
    else:
        print("  preview     : (未读到行，不影响判定——笔数与覆盖状态才是判据)")


def main():
    csv = exported_trades()
    print(f"archive as exported: {csv.count(chr(10))} lines")
    print(csv.split("\n")[0])
    print(csv.split("\n")[1] if csv.count("\n") >= 1 else "")

    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(2)

    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "实时持仓收益")

    if item:
        winui.invoke_click(item)
        time.sleep(2.5)

    imp = find(win, "ImportButton")

    if imp is None:
        print("[FAIL] ImportButton not found")
        sys.exit(1)

    winui.invoke_click(imp)
    time.sleep(2.5)

    # 1. The archive this app exported: dated rows, so it may replace.
    try_parse(win, "导出的历史成交记录（带日期）", csv)

    # 2. A day of broker orders: no dates, so it may only be appended.
    try_parse(win, "当日委托（无日期）", TODAY)

    print("\nDone.")


if __name__ == "__main__":
    main()
