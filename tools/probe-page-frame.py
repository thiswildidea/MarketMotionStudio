#!/usr/bin/env python
"""Maximises the window, opens one page, fetches, and captures the frame.

Built for the pages whose header line is drawn as a row of runs, where a change to
the spacing between them is invisible in a narrow window and can push the line past
the frame's edges in a long language.

Usage:  python tools/probe-page-frame.py 行业板块竞速 sector-race
"""

import os
import subprocess
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")
EXE = "MarketMotionStudio.exe"
APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else "行业板块竞速"
    name = sys.argv[2] if len(sys.argv) > 2 else "page"

    # Restarted rather than adopted. A window closed to the tray is still in the UIA
    # tree with every control intact, so navigation and the fetch button both work
    # against it — while CaptureToImage reads the screen rectangle it claims, which
    # by then is showing whatever else is on the desktop. The sibling project shares
    # this desktop, and the first run of this script saved a picture of it.
    subprocess.run(["taskkill", "/F", "/IM", EXE], capture_output=True, check=False)
    time.sleep(2.0)
    os.startfile("shell:AppsFolder\\%s" % APPID)

    window = winui.app_window(EXE, wait_seconds=45)

    if window is None:
        print("the app did not come up")
        return 1

    window.SetActive()
    time.sleep(2.0)

    size = window.GetWindowPattern()

    if size is not None:
        try:
            size.SetWindowVisualState(auto.WindowVisualState.Maximized)
            time.sleep(2.0)
        except Exception:  # noqa: BLE001
            pass

    # Selected, then confirmed to have stayed. The app is still settling when the window
    # first answers — it comes up on the page it was last left on, and that restore lands
    # after this selection often enough to matter: the run then fetched and photographed
    # the *previous* page while reporting success. Selecting the same item again after the
    # restore is harmless, and `IsSelected` is what tells the two apart.
    for attempt in range(4):
        item = winui.find(window, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == page)

        if item is None:
            print(f"no {page} nav item — the window is not where the page list is")
            return 1

        item.GetSelectionItemPattern().Select()
        time.sleep(3.0)

        try:
            if item.GetSelectionItemPattern().IsSelected:
                break
        except Exception:  # noqa: BLE001 - a re-laid-out item goes stale; try again
            pass
    else:
        print(f"{page}: the nav item would not stay selected")
        return 1

    fetch = winui.find(window, lambda c: c.AutomationId == "FetchButton")

    if fetch is not None:
        fetch.GetInvokePattern().Invoke()
        time.sleep(18.0)

    status = winui.find(window, lambda c: c.AutomationId == "Status")
    print("status:", status.Name if status else None)

    path = os.path.join(OUT, f"probe-page-{name}.png")

    # Pinned for the moment of the grab: restarting the app puts it in front, but the
    # sibling project's window can come back over it in the eighteen seconds the fetch
    # takes. See the same note in probe-candle-frame.py.
    try:
        window.SetTopmost(True)
        time.sleep(0.8)
        window.CaptureToImage(path)
        window.SetTopmost(False)
    except Exception as exc:  # noqa: BLE001
        print("could not pin to top:", exc)
        window.CaptureToImage(path)

    print("saved:", path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
