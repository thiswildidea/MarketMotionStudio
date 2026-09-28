# -*- coding: utf-8 -*-
"""Check that the manual renders its pictures, and where it thinks they are.

Opens Help, scrolls to the chapters that carry a picture and captures what the
page looks like. Also counts Image controls the accessibility tree exposes,
which is the only machine-readable sign that a picture made it into the layout
rather than falling through to the caption alone.
"""

import os
import subprocess
import time

import uiautomation as auto

EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"

# Wheel notches before each capture. The help page is one long scroll and the
# accessibility tree does not expose its scroller, so this drives it the way a
# reader does — and the pictures are what the capture is for anyway.
STOPS = [
    (8, "help-1-sector-race.png"),
    (6, "help-2-position.png"),
]


def find(condition, root, depth=0, limit=25):
    if depth > limit:
        return None

    try:
        if condition(root):
            return root
    except Exception:
        return None

    try:
        for child in root.GetChildren():
            hit = find(condition, child, depth + 1, limit)
            if hit is not None:
                return hit
    except Exception:
        pass

    return None


def pattern(control, pattern_id):
    try:
        return control.GetPattern(pattern_id)
    except Exception:
        return None


def click(control):
    for invoke in (auto.PatternId.InvokePattern, auto.PatternId.SelectionItemPattern):
        handle = pattern(control, invoke)

        if handle is None:
            continue

        try:
            handle.Invoke() if invoke == auto.PatternId.InvokePattern else handle.Select()
            time.sleep(0.5)
            return True
        except Exception:
            pass

    try:
        control.Click(simulateMove=False, waitTime=0.5)
        return True
    except Exception:
        return False


def pids():
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq " + EXE],
        capture_output=True,
    )
    text = result.stdout.decode("utf-8", "replace")

    return {
        int(row.split('","')[1].strip('"'))
        for row in text.splitlines()[1:]
        if EXE.lower() in row.lower()
    }


def window():
    for _ in range(15):
        for candidate in auto.GetRootControl().GetChildren():
            try:
                if candidate.ControlTypeName == "WindowControl" and candidate.ProcessId in pids():
                    return candidate
            except Exception:
                pass
        time.sleep(1)

    return None


def count_images(root):
    total = 0

    def walk(control, depth=0):
        nonlocal total

        if depth > 25:
            return

        try:
            if control.ControlTypeName == "ImageControl":
                total += 1
        except Exception:
            pass

        try:
            for child in control.GetChildren():
                walk(child, depth + 1)
        except Exception:
            pass

    walk(root)
    return total


def main():
    win = window()
    assert win, "no window"

    win.SetActive()
    win.MoveWindow(60, 60, 1500, 940)
    time.sleep(3)

    # Away and back: a page that is already showing is not rebuilt, and the help
    # page would keep the scroll position the last run left it at.
    for name in ("设置", "帮助"):
        item = None
        for _ in range(8):
            item = find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name, win)
            if item:
                break
            time.sleep(2)

        assert item, f"navigation item not found: {name}"
        assert click(item), f"could not open {name}"
        time.sleep(3)

    print("pictures in the accessibility tree:", count_images(win))

    middle = win.BoundingRectangle
    auto.SetCursorPos(
        (middle.left + middle.right) // 2,
        (middle.top + middle.bottom) // 2,
    )

    for notches, name in STOPS:
        auto.WheelDown(wheelTimes=notches, interval=0.05)
        time.sleep(1.5)

        path = os.path.join(OUT, name)
        win.CaptureToImage(path)
        print("  captured", name, "after", notches, "notches")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
