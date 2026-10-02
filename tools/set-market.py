#!/usr/bin/env python
"""Switches the app's market and restarts it, then reads the choice back.

The market is a stored setting the pages read at startup — the settings page says
so itself — so anything verified per market needs the app restarted in between.
Reading the value back after the restart is the point: a hard kill is not a graceful
exit, and a setting that did not make it to disk looks exactly like a verification
that silently ran against the previous market.

Usage:  python tools/set-market.py 港股
        python tools/set-market.py A股
"""

import os
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"

auto.uiautomation.SetGlobalSearchTimeout(5)


def find(control, condition, depth=0, limit=25):
    if control is None or depth > limit:
        return None
    try:
        if condition(control):
            return control
    except Exception:  # noqa: BLE001
        return None
    for child in control.GetChildren():
        found = find(child, condition, depth + 1, limit)
        if found is not None:
            return found
    return None


def window():
    """The app's top-level window, found by process.

    Not by an AutomationId inside it: every page carries the playback bar except the
    manual, so a window left showing help has none of the controls that identify it —
    and the script reported "no studio window" for an app that was running and
    visible, then went on to verify the market it had failed to change.

    Owned by `winui`, not copied here. The copy that used to be here read `tasklist`
    with `text=True`, which decodes as UTF-8 and raises **inside subprocess's reader
    thread** — so it did not fail loudly, it returned `stdout = None` and blew up on
    `.splitlines()`. `tasklist` writes its "no tasks match" line in the system code
    page, so that landed exactly when the app was *not* running: the one case this
    function exists to answer "no processes" to.
    """
    return winui.app_window(EXE)


def kill():
    winui.kill(EXE)


def launch():
    return winui.launch(EXE, APPID)


def market_value(win):
    box = find(win, lambda c: c.AutomationId == "MarketCombo")
    if box is None:
        return None

    try:
        if box.GetValuePattern().Value:
            return box.GetValuePattern().Value
    except Exception:  # noqa: BLE001
        pass

    try:
        picked = box.GetSelectionPattern().GetSelection()
        return picked[0].Name if picked else None
    except Exception:  # noqa: BLE001
        return None


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else "A股"

    win = window() or launch()

    if win is None:
        print("no studio window")
        return 1

    win.SetActive()
    time.sleep(1.0)

    settings = find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "设置")
    if settings is None:
        print("no 设置 nav item")
        return 1

    settings.GetSelectionItemPattern().Select()
    time.sleep(2.0)

    combo = find(win, lambda c: c.AutomationId == "MarketCombo")
    if combo is None:
        print("no MarketCombo")
        return 1

    opened = combo.GetExpandCollapsePattern()
    if opened is not None:
        opened.Expand()
        time.sleep(1.2)

    item = None
    for root in auto.GetRootControl().GetChildren():
        item = find(root, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == wanted, limit=8)
        if item is not None:
            break

    if item is None:
        print(f"no {wanted} in the market list")
        return 1

    item.GetSelectionItemPattern().Select()
    time.sleep(1.5)

    print(f"set to {wanted}; restarting")

    kill()
    win = launch()

    if win is None:
        print("did not come back up")
        return 1

    win.SetActive()
    time.sleep(1.0)

    settings = find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "设置")
    if settings is not None:
        settings.GetSelectionItemPattern().Select()
        time.sleep(2.0)

    got = market_value(win)
    print(f"after restart: {got!r}")

    return 0 if got == wanted else 1


if __name__ == "__main__":
    sys.exit(main())
