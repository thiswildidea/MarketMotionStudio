#!/usr/bin/env python
"""Reads the candle page's restored defaults, and nothing else.

The walk in verify-candle.py changes the motion twice, so it cannot tell whether a
wrong default is the app's or the last run's. This one opens the page, reads the
three drop-downs and whether the window box is live, and leaves every value alone.

Run:  python tools/probe-candle-defaults.py
"""

import time

import uiautomation as auto

auto.uiautomation.SetGlobalSearchTimeout(5)


def find(control, condition):
    if control is None:
        return None
    try:
        if condition(control):
            return control
    except Exception:  # noqa: BLE001 - a control that vanished mid-walk
        return None
    for child in control.GetChildren():
        found = find(child, condition)
        if found is not None:
            return found
    return None


def value(combo):
    try:
        return combo.GetValuePattern().Value
    except Exception:  # noqa: BLE001
        picked = combo.GetSelectionPattern().GetSelection()
        return picked[0].Name if picked else None


def main():
    root = auto.GetRootControl()
    window = None
    for candidate in root.GetChildren():
        if find(candidate, lambda c: c.AutomationId == "Scrub") is not None:
            window = candidate
            break

    if window is None:
        print("no studio window")
        return 1

    window.SetActive()
    time.sleep(1.0)

    item = find(window, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "K线")
    if item is None:
        print("no K线 nav item")
        return 1

    item.GetSelectionItemPattern().Select()
    time.sleep(2.0)

    for name in ("PeriodCombo", "StyleCombo", "MotionCombo"):
        control = find(window, lambda c, n=name: c.AutomationId == n)
        print(f"  {name:12s} {value(control) if control else '(missing)'}")

    box = find(window, lambda c: c.AutomationId == "WindowBox")
    print(f"  WindowBox    enabled={box.IsEnabled if box else None} text={box.GetValuePattern().Value if box else None}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
