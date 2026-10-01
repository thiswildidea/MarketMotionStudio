# -*- coding: utf-8 -*-
"""Shared plumbing for the scripts that drive the running app through UIA.

The window is found by **process**, never by a control inside it. Two reasons, both
learned the hard way:

* The sibling project WorldMotionStudio is the same application shell and runs on
  the same desktop. It carries the same playback bar and the same Chinese control
  names, so "the first top-level window that has a Scrub" happily returns the wrong
  app — and a probe that reports on it is reporting on nothing.
* Every page carries the playback bar except the manual, so a window left showing
  help matches none of the controls that were being used to identify it. A script
  that then said "no studio window" was looking at an app that was running and
  visible, and went on to verify the market it had failed to change.
"""

import os
import subprocess
import time

import uiautomation as auto

auto.uiautomation.SetGlobalSearchTimeout(5)

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"


def console_text(raw):
    """Decode what a Windows console tool wrote.

    Not `text=True`: that decodes as UTF-8 and *raises inside subprocess's reader
    thread*, which leaves `stdout` as None rather than as an error. `tasklist` writes
    its "no tasks match" line in the system code page — GBK on this machine — so the
    failure lands exactly when the app is not running, which is when the call is
    supposed to answer "no processes" rather than blow up.
    """
    for encoding in ("utf-8", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", "replace")


def pids(image_name):
    result = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image_name}", "/NH", "/FO", "CSV"],
                            capture_output=True)
    out = console_text(result.stdout or b"")

    found = set()

    for line in out.splitlines():
        fields = [f.strip('"') for f in line.split('","')]

        if len(fields) > 1 and fields[1].isdigit():
            found.add(int(fields[1]))

    return found


def app_window(image_name, wait_seconds=0):
    deadline = time.time() + wait_seconds

    while True:
        running = pids(image_name)

        if running:
            for candidate in auto.GetRootControl().GetChildren():
                if candidate.ProcessId in running and candidate.Name:
                    return candidate

        if time.time() >= deadline:
            return None

        time.sleep(1)


def find(control, condition, depth=0, limit=25):
    if control is None or depth > limit:
        return None

    try:
        if condition(control):
            return control
    except Exception:  # noqa: BLE001 - a control that vanished mid-walk
        return None

    for child in control.GetChildren():
        hit = find(child, condition, depth + 1, limit)

        if hit is not None:
            return hit

    return None


def kill(image_name):
    subprocess.run(["taskkill", "/IM", image_name, "/F"], capture_output=True)
    time.sleep(2)


def launch(image_name, appid=APPID, wait_seconds=45):
    """Restarts the app and returns its window.

    Killed first, because a window already up is the last build's: the package is
    registered in place, and an instance that is running keeps the assembly it started
    with. Verifying against it is verifying the previous change.
    """
    kill(image_name)
    os.startfile(r"shell:AppsFolder\%s" % appid)

    window = app_window(image_name, wait_seconds=wait_seconds)
    time.sleep(3)

    return window


def find_all(control, condition, depth=0, limit=25, out=None):
    """Every control under `control` that matches, in tree order."""
    out = [] if out is None else out

    if control is None or depth > limit:
        return out

    try:
        if condition(control):
            out.append(control)
    except Exception:  # noqa: BLE001
        return out

    for child in control.GetChildren():
        find_all(child, condition, depth + 1, limit, out)

    return out


def popup_items(win):
    """Every list row the process is showing, the navigation pane's included.

    Filtered by process only — the desktop has other applications on it whose list
    rows answer to the same walk.

    The main window is deliberately *not* excluded, though its nav items come back
    in the same bag: in WinUI 3 a combo's items are part of the main window's own
    tree, not a pop-up window of their own. Excluding the window was tried and left
    nothing to select — every combo check failed at once. Callers tell the two apart
    by what the pop-up *added*; see `combo_labels`.
    """
    found = []

    for top in auto.GetRootControl().GetChildren():
        if top.ProcessId != win.ProcessId:
            continue

        found += find_all(top, lambda c: c.ControlTypeName == "ListItemControl" and c.Name)

    return found


def combo_items(win, combo, name=None, seconds=5, baseline=None):
    """Opens a combo and returns the rows that appeared.

    Waited for, because `Expand` returns before the pop-up's rows do — and an answer
    of "none" is then indistinguishable from a comma with nothing in it. A page that
    was working was reported as missing the very entry being looked for.

    `name` narrows it to one entry.

    `baseline`, when given, is the set of names the process was already showing with
    the box shut. It is what the wait is measured against, and that matters: the walk
    returns the navigation pane's rows whether or not the menu opened, so "any rows at
    all" is true the instant it starts. An expand that did nothing (see the retry note
    on `combo_pick`) then answered with eleven navigation items, and a caller comparing
    the menu's contents against a written-out list reported a working menu as having
    no 区间 entry and all eleven nav entries instead. Retried, for the same reason.
    """
    baseline = baseline or set()

    for attempt in range(3):
        try:
            combo.GetExpandCollapsePattern().Expand()
        except Exception:  # noqa: BLE001 - the box can go stale between pages
            time.sleep(1.0)
            continue

        deadline = time.time() + seconds

        while True:
            items = popup_items(win)

            if name is not None:
                items = [i for i in items if i.Name == name]

            if any(i.Name not in baseline for i in items) or time.time() >= deadline:
                return items

            time.sleep(0.4)

    return []


def combo_pick(win, combo, name):
    """Opens a combo and selects the entry called `name`. Returns its name, or None.

    Retried, because an expand issued while the previous collapse is still animating
    does nothing at all — the menu then looks empty, and the caller reads that as "this
    option does not exist" rather than as "the box was not open yet". Picking a second
    entry straight after listing the first is exactly that sequence: `combo_labels`
    ends by collapsing, and the expand that follows arrives too early. It cost a
    verification run that reported a working menu as a missing option.
    """
    for attempt in range(3):
        items = combo_items(win, combo, name=name)

        if items:
            try:
                items[0].GetSelectionItemPattern().Select()
            except Exception:  # noqa: BLE001 - the row can go stale mid-select
                time.sleep(1.2)
                continue

            time.sleep(1.2)

            return items[0].Name

        try:
            combo.GetExpandCollapsePattern().Collapse()
        except Exception:  # noqa: BLE001 - the popup may already be gone
            pass

        if attempt == 2:
            return None

        time.sleep(1.2)


def combo_labels(win, combo):
    """What a combo offers, without the navigation pane that the walk also sees.

    Deduplicated by name, in order. An open combo exposes the same rows twice — once
    inside the box's own tree and once in the popup — so a five-entry menu walks back
    as ten and an assertion like "three spans" fails on a combo that is perfectly
    correct. The list of *what it offers* is the same either way; this is the shape a
    caller can compare against.

    Empty means the menu never opened, and that is the honest answer: the walk sees the
    navigation pane's rows either way, so an "everything it found" fallback would hand
    the caller the navigation pane and it would report the option missing. There is no
    fallback here for that reason.
    """
    for attempt in range(3):
        before = {i.Name for i in popup_items(win)}
        items = combo_items(win, combo, baseline=before)

        labels = []
        seen = set()

        for item in items:
            if item.Name and item.Name not in before and item.Name not in seen:
                seen.add(item.Name)
                labels.append(item.Name)

        try:
            combo.GetExpandCollapsePattern().Collapse()
        except Exception:  # noqa: BLE001 - the popup may already be gone
            pass

        time.sleep(0.8)

        if labels:
            return labels

    return []


def value(combo):
    """A WinUI ComboBox's current item, which is not a child Text node."""
    if combo is None:
        return None

    try:
        if combo.GetValuePattern().Value:
            return combo.GetValuePattern().Value
    except Exception:  # noqa: BLE001
        pass

    try:
        picked = combo.GetSelectionPattern().GetSelection()
        return picked[0].Name if picked else None
    except Exception:  # noqa: BLE001
        return None
