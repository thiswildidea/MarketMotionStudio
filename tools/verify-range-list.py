"""Reads the page's list at the start of a span and again at its end.

The range is switched through the same combo the reader uses, and the switch is confirmed off the
summary line ("... 个交易日 ...") rather than off the combo — a ComboBox here exposes no selection
that can be read back.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui

PAGE = "实时持仓收益"


def aid(win, name):
    return winui.find(win, lambda c, n=name: c.AutomationId == n)


def summary(win):
    control = aid(win, "SummaryText")
    try:
        return control.Name if control is not None else ""
    except Exception:  # noqa: BLE001
        return ""


def lines(win, most=3):
    out = []

    for control in winui.find_all(win, lambda c: c.ControlTypeName == "TextControl", limit=80):
        try:
            text = control.Name or ""
        except Exception:  # noqa: BLE001
            continue

        if "股 · 成本" in text or "已清仓" in text:
            out.append(text)

        if len(out) >= most:
            break

    return out


def switch(win, label, tries=3):
    """Picks `label` from the range combo, confirming it off the summary line."""
    for attempt in range(1, tries + 1):
        combo = aid(win, "SpanPickerMenu")

        if combo is None:
            return False

        try:
            combo.GetExpandCollapsePattern().Collapse()
        except Exception:  # noqa: BLE001
            pass

        time.sleep(0.5)

        picked = winui.combo_pick(win, combo, label)
        print(f"  第{attempt}次选择 {label}: {picked}")

        deadline = time.time() + 75

        while time.time() < deadline:
            text = summary(win)

            if "个交易日" in text or "分时数据" in text:
                print("  汇总:", text)
                return True

            time.sleep(2)

    print("  汇总仍是:", summary(win))
    return False


def main():
    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(3)

    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == PAGE)

    if item is None:
        raise SystemExit("页面上没有 实时持仓收益")

    winui.invoke_click(item)
    time.sleep(3)

    print("[0] 打开:", summary(win))
    print("    列表:", lines(win, 2))

    print("\n[1] 切到 近一周")
    if not switch(win, "近一周"):
        raise SystemExit("范围没切过去")

    time.sleep(2)
    at_start = lines(win, 4)
    print("  起点列表:")
    for line in at_start:
        print("     ", line)

    scrub = aid(win, "Scrub")
    play = aid(win, "PlayButton")

    if play is None:
        raise SystemExit("没有播放按钮")

    print("\n[2] 按播放，边播边读列表")
    winui.invoke_click(play)

    seen = []
    for i in range(8):
        time.sleep(1.2)
        row = lines(win, 1)
        text = aid(win, "ScrubText")
        at = text.Name if text is not None else "?"
        print(f"   {i + 1}s {at:<12} {row[0] if row else '—'}")
        seen.append(tuple(row))

    winui.invoke_click(play)

    distinct = len(set(seen))
    print("\n判定:", f"播放过程中列表出现 {distinct} 种取值" if distinct > 1 else "**播放时列表不变**")


if __name__ == "__main__":
    main()
