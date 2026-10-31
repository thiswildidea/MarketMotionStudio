#!/usr/bin/env python3
"""Drives the two portfolio pages across the span picker and reads what they drew.

Answers, with the app actually running:

  1.  当日 still answers in minutes (the old path must not have moved);
  2.  近一周 / 近一月 reach the returns engine and draw a span — or say why they
      cannot, in the line under the switch rather than in silence;
  3.  both pages read the same span from the same control.

Probe, not verify: a run the reader can watch and a transcript they can re-read, and
nothing is asserted beyond what was printed.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui  # noqa: E402

LOCAL = os.path.expandvars(
    r"%LOCALAPPDATA%\Packages\8166Yxw.MarketMotionStudio_fzc58jprbah1t\LocalState")


def ledger_day():
    """What the snapshot the app seeded calls its first day."""
    path = os.path.join(LOCAL, "ledger-baseline.json")

    if not os.path.exists(path):
        return None

    return json.load(open(path, encoding="utf-8-sig")).get("Day")


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

    if item is None:
        return False

    for _ in range(6):
        try:
            item.GetScrollItemPattern().ScrollIntoView()
        except Exception:  # noqa: BLE001
            pass

        time.sleep(0.4)

        try:
            if item.BoundingRectangle.width() > 0:
                break
        except Exception:  # noqa: BLE001
            pass

    winui.invoke_click(item)
    time.sleep(2.0)

    return True


def pick_span(win, label):
    """Set the shared range picker to one of its menu entries, by its text."""
    combo = winui.find(win, lambda c: c.AutomationId == "SpanPickerMenu")

    if combo is None:
        print("  [FAIL] range picker menu not found on the page")
        return False

    return winui.combo_pick(win, combo, label)


def read_out(win, what):
    """One of the page's two text lines, read out of the UIA tree."""
    control = winui.find(win, lambda c: c.AutomationId == what)

    if control is None:
        return None

    try:
        return control.Name
    except Exception:  # noqa: BLE001
        return None


def status_open(win):
    """Whether the page's info bar is open, and what it says if it is."""
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return None

    try:
        return bar.Name if bar.IsOffscreen is False else None
    except Exception:  # noqa: BLE001
        return None


def snapshot(win, page, span, seconds=45):
    """Pick a span, wait out the fetch, and print every line the page says about it."""
    print(f"\n== {page} / {span} ==")

    if not pick_span(win, span):
        return

    # The fetch is a read of a span's closes plus, inside the week, its minutes: slow
    # enough that a fixed short sleep guesses wrong. Wait on the summary line changing
    # to carry a number of samples.
    deadline = time.time() + seconds
    last = ""

    while time.time() < deadline:
        summary = read_out(win, "SummaryText") or ""

        if summary and summary != last and any(ch.isdigit() for ch in summary):
            last = summary

        if last:
            break

        time.sleep(2)

    time.sleep(3)

    summary = read_out(win, "SummaryText")
    updated = read_out(win, "UpdatedText")
    bar = status_open(win)

    print(f"  SummaryText : {summary!r}")
    print(f"  UpdatedText : {updated!r}")
    print(f"  Status bar  : {bar!r}")


def main():
    print(f"ledger baseline day: {ledger_day()}")

    win = winui.launch("MarketMotionStudio.exe")

    print(f"window: {win.Name!r}")

    # The intraday page first: it owns the switch the spans answer through.
    if not goto(win, "实时持仓收益"):
        print("[FAIL] cannot reach 实时持仓收益")
        sys.exit(1)

    snapshot(win, "实时持仓收益", "当日")
    snapshot(win, "实时持仓收益", "近一周")
    snapshot(win, "实时持仓收益", "近一月")

    if goto(win, "持仓·大盘 双屏"):
        snapshot(win, "双屏", "近一周")
        snapshot(win, "双屏", "近一月")
    else:
        print("[note] 持仓·大盘 双屏 not offered under this market")

    # 自定义: the two day pickers only exist for this one entry, and a span it cannot fill in
    # must leave the picture alone rather than read from the beginning of time.
    print("\n== 实时持仓收益 / 自定义 ==")

    if goto(win, "实时持仓收益") and pick_span(win, "自定义"):
        time.sleep(1.5)

        for name in ("SpanPickerFrom", "SpanPickerTo"):
            picker = winui.find(win, lambda c, n=name: c.AutomationId == n)
            state = "missing"

            if picker is not None:
                try:
                    state = "visible" if not picker.IsOffscreen else "present-but-hidden"
                except Exception:  # noqa: BLE001
                    state = "present"

            print(f"  {name}: {state}")

        print(f"  SummaryText : {read_out(win, 'SummaryText')!r}")
        print(f"  Status bar  : {status_open(win)!r}")

    print("\nledger after the run:")
    for name in ("ledger-baseline.json", "ledger-trades.json"):
        path = os.path.join(LOCAL, name)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  {name}: {size} bytes")

    print("\nDone. The app is left running for the reader to look at.")


if __name__ == "__main__":
    main()
