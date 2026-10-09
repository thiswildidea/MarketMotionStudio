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

import ctypes
import os
import subprocess
import time

import uiautomation as auto

auto.uiautomation.SetGlobalSearchTimeout(5)

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"


def keep_awake():
    """Ask Windows not to blank the display while this script runs.

    A run spends minutes at a time in `sleep` between clicks, and an idle machine blanks
    the screen and locks. From then on `CaptureToImage` hands back the *lock screen* for
    every remaining shot — see `capture`, which says so rather than let the numbers from
    those shots be read as the app drawing something wrong.

    The request is per-thread and dies with this process; nothing is written to disk and
    no setting is changed. A lock imposed by policy is still a lock.
    """
    try:
        continuous, system, display = 0x80000000, 0x1, 0x2

        ctypes.windll.kernel32.SetThreadExecutionState(continuous | system | display)
    except Exception:  # noqa: BLE001 - an unrequested nap is not a failure
        pass


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

    Also wakes the display and asks it to stay awake — a run is minutes of clicking
    followed by minutes of `sleep`, and the screen blanking in the middle of one costs
    every screenshot after it (see `keep_awake`).
    """
    keep_awake()
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

    **The return value is "this entry was found and clicked", not "the box now reads
    that".** Nothing here can confirm the second half: a ComboBox exposes neither
    `SelectionPattern` nor `ValuePattern` in this app (`GetSelectionPattern()` raises,
    `GetValuePattern().Value` raises) and its own `Name` is the label above it, so the
    selection cannot be read back at all. Callers that need to know whether the switch
    took have to judge it off the picture — see the motion section in
    `verify-position.py`, where "did it switch back" is answered by where the curve's
    head sits, because that is the thing the switch is supposed to move.

    Retried, because an expand issued while the previous collapse is still animating
    does nothing at all — the menu then looks empty, and the caller reads that as "this
    option does not exist" rather than as "the box was not open yet". Picking a second
    entry straight after listing the first is exactly that sequence: `combo_labels`
    ends by collapsing, and the expand that follows arrives too early. It cost a
    verification run that reported a working menu as a missing option.

    **It collapses both before and after**, and that is not tidiness. `combo_items`
    expands every time, and an expand on an already-open box is a no-op — so the rows
    it hands back may be the ones in a pop-up that is on its way out. Selecting a row
    in a dying pop-up raises nothing and changes nothing, and the caller is told the
    name it asked for. That is exactly how a switch *back* to the first entry reported
    success while the box still read the second one: the run redrew, the assertion
    passed, and every picture after it was of the wrong motion — including the two the
    next section drew its conclusions from.
    """
    try:
        combo.GetExpandCollapsePattern().Collapse()
        time.sleep(0.4)
    except Exception:  # noqa: BLE001 - the box can go stale between pages
        pass

    for attempt in range(3):
        items = combo_items(win, combo, name=name)

        if items:
            try:
                items[0].GetSelectionItemPattern().Select()
            except Exception:  # noqa: BLE001 - the row can go stale mid-select
                time.sleep(1.2)
                continue

            time.sleep(1.2)

            try:
                combo.GetExpandCollapsePattern().Collapse()
            except Exception:  # noqa: BLE001 - the popup may already be gone
                pass

            time.sleep(0.4)

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


def canvas_box(whole):
    """The preview canvas inside a captured window, as (left, right, top, bottom).

    Shared, because three scripts had their own copy of this and all three copies were
    wrong in the same way at the same time.

    Not by a proportion of the window: the crop that used to be here ("the canvas is
    39%–62% across") counted one row on a frame, because the window layout is not a fixed
    fraction and the preview has no automation node to measure.

    And no longer by saturation, which is what stood in two of the three copies. Saturation
    was right about the chrome (grey has none) and wrong about the canvas: the canvas is
    near-black, and the only *vivid* things in a frame are the bars. A column-first
    saturation pass therefore answered "the bars" — the columns they cover are vivid top to
    bottom and beat every column that is mostly canvas — and returned a 32-pixel stripe
    holding no name column at all. Three row-count checks failed on frames that were
    perfectly drawn, while every check that compared numbers passed.

    What separates the two is **brightness**, and the field is found by walking out from the
    canvas's own centre: the chrome is near-white, the canvas is near-black, and the walk
    only stops when the light has run on for a stretch — which is what makes it immune to
    the light glyphs and gold dates *inside* the canvas, the thing a per-pixel threshold
    cannot survive.

    Returns None when the picture does not look like a captured canvas.

    *Which* way round the walk goes is decided by the picture, and that is newer than the rest
    of this function. It used to be one way only — out from the centre until the light ran
    on — on the stated fact that the chrome is near-white and the canvas near-black. That
    stopped being a fact the day the window began showing the desktop through itself: the
    chrome then measures about 190 instead of 250, which is **either side of the threshold
    depending on what is on the desktop and where**, so one side of the window answers and the
    other walks off the edge of the picture. The box comes back as the whole window — still
    inside it, so `looks_like_a_frame` still passes — and every measurement taken from it is
    confident nonsense: a safe line at 1645 against a canvas that ends at 1134, and a "the two
    frames differ" that reads 0.6% because nine tenths of what is being compared is chrome.

    So the canvas is also looked for the way round it was not: by its own near-black. The
    aspect is what tells the two answers apart, and it is safe to ask for because every size
    this app offers is 9:16 (`VideoFormat.Sizes` — 720×1280, 1080×1920, 1440×2560). The old
    walk stays the first answer so that nothing moves where it has always worked, and the
    near-black one takes over when the old one did not come back with a frame in it.
    """
    width, height = whole.size
    pixels = whole.load()

    def light(x, y):
        r, g, b = pixels[x, y]

        return (r + g + b) / 3 > 200

    def backdrop(x, y):
        r, g, b = pixels[x, y]

        return (r + g + b) / 3 < 70

    def chrome(x, y):
        """The canvas by way of what is around it — the walk the other one takes.

        Kept as its own predicate rather than as `not light` at the call, because the two walks
        mean the opposite thing by the pixel they are handed: this one stops on the chrome and
        `backdrop` stops on anything that is not the frame. Passing the same predicate to both
        and letting one of them invert it is how this function came to hand back no canvas at
        all for a frame whose middle is a curve.
        """
        return not light(x, y)

    # 5% of the height: no canvas is 50 pixels of unbroken light, and the chrome always is.
    edge = max(12, height // 20)

    def walk(x, y, dx, dy, inside):
        last = x if dx else y
        streak = 0

        while 0 <= x < width and 0 <= y < height:
            if inside(x, y):
                streak = 0
                last = x if dx else y
            else:
                streak += 1

                if streak >= edge:
                    break

            x += dx
            y += dy

        return last

    def walked(inside):
        if not inside(width // 2, height // 2):
            return None

        left = walk(width // 2, height // 2, -1, 0, inside)
        right = walk(width // 2, height // 2, 1, 0, inside)
        top = walk(width // 2, height // 2, 0, -1, inside)
        bottom = walk(width // 2, height // 2, 0, 1, inside)

        if right - left < 40 or bottom - top < 40:
            return None

        return left, right, top, bottom

    def bands():
        """The canvas as the one large near-black rectangle, counted rather than walked to.

        The walk above starts from a single pixel, and that pixel can be sitting on ink: a curve
        through the middle of the frame is not backdrop, and a walk that never starts hands back
        no canvas at all — which is exactly what happened on a frame whose curves cross the
        centre. Counting rows and columns asks the whole picture at once, so nothing depends on
        where one pixel happens to land.

        8% of the width: the canvas is about a fifth of a window, and the chrome carries dark
        controls of its own, so a higher bar finds nothing at all.

        **The height is derived from the width, not counted.** Counting downwards runs into the
        same thing the walk does: under the preview sits the page, and the row of controls there
        is dark again across exactly the same columns, so the count carries straight on past the
        canvas and hands back a box 130 pixels too tall. The other end is just as bad on a frame
        that ends on its cards, whose fill is light enough to drop those rows below the bar. The
        width is the one edge that is unambiguous — nothing else in the window is 383 dark pixels
        across — and 9:16 turns it into the height, which is a fact about the format rather than
        something to be measured again.
        """
        rows = [y for y in range(height)
                if sum(1 for x in range(width) if backdrop(x, y)) > 0.08 * width]

        if not rows:
            return None

        top = rows[0]
        bottom = rows[-1]
        left = right = None

        # Twice: the columns are counted over a band whose height came from the last guess, and
        # the guess is what they then correct. It settles in one step on every capture measured.
        for _ in range(2):
            mid0 = top + ((bottom - top) // 4)
            mid1 = bottom - ((bottom - top) // 4)
            tall = max(1, mid1 - mid0)
            across = [x for x in range(width)
                      if sum(1 for y in range(mid0, mid1) if backdrop(x, y)) > 0.6 * tall]

            if not across:
                return None

            left, right = across[0], across[-1]

            # Clamped, because a whole window can be dark enough to be counted as one row and
            # the width that comes out of it then asks for a canvas taller than the picture.
            bottom = min(top + int(round((right - left) / 0.5625)), height - 1)

        if bottom - top < 40 or right - left < 40:
            return None

        return left, right, top, bottom

    def upright(box):
        """Is this box shaped like a frame of this app?

        Two pixels of slack in the ratio: the canvas is rounded to whole pixels by the
        preview, and a 680-tall canvas is 383 or 382 across depending on where it landed.
        """
        left, right, top, bottom = box

        return abs(((right - left) / max(1, bottom - top)) - 0.5625) < 0.02

    found = walked(chrome)

    if found is not None and upright(found):
        return found

    # A frame drawn on a light backdrop has no near-black to count, and `bands` answers None
    # for it — which is why this is a second answer rather than a replacement.
    dark = bands()

    if dark is not None and upright(dark):
        return dark

    return found


def looks_like_a_frame(picture, box):
    """Is this box the canvas of a captured frame, rather than "some rectangle"?

    This is the test `capture` has always made, given a name: the canvas is **inset** —
    sidebar to its left, settings to its right, a playback bar under it — so a box the size
    of the whole picture is never a canvas. A few pixels of slack for the frame's own border.
    """
    return (box is not None
            and box[1] - box[0] < picture.size[0] - 8
            and box[3] - box[2] < picture.size[1] - 8)


def capture(win, path, tries=4):
    """Capture **this** window, and make sure that is what came back.

    `CaptureToImage` hands back whichever window is on top at that moment, and a script that
    runs for half an hour is not the only thing on the machine. One run of `verify-dca-board`
    wrote the whole editor into `verify-dca-six.png` — a 1920×1080 picture where the app is
    1920×1020 — and every measurement taken from it was confident nonsense: `canvas_box` fell
    back to "the entire picture", six tracks were counted as two, the labels were "not there",
    the plot's right edge came out at 1452, and seven assertions failed on a frame with
    nothing wrong with it. The failure reads as a data or drawing bug, and it is neither.

    So the picture is read back and checked against the one thing a captured app frame always
    has: **a canvas inside it**. `canvas_box` walks out from the frame's centre and returns
    the whole picture for anything else, so "the box is not the whole picture" is the test
    (`looks_like_a_frame`). Failing that, the window is raised again and the shot retaken.

    **Returns whether the picture is a frame of this window**; the file is written either way.
    A guard that threw would turn a wrong reading into a lost run, but a guard that only
    returned the path turned one into a *silent* wrong reading — and the second one is worse,
    because it arrives as a bug report about the app. The screen locking on its own is a
    property of the machine: on the retry after one such lock, `verify-dca-board` measured
    four lock-screen pictures in a row and reported eight failures — "the capsule column broke
    the drawing", "the scrolling motion does not scroll" — with the app drawing exactly what
    it should. The caller (`Frame`) now refuses to measure a picture that is not a frame and
    says so in the line that reports it.
    """
    from PIL import Image

    for attempt in range(tries):
        for call in (win.SetActive, lambda: win.SetTopmost(True)):
            try:
                call()
            except Exception:  # noqa: BLE001 - a window that went away is the retry's job
                pass

        # Raised first, then given the time to actually come up: the capture takes whatever
        # is on top *now*, and this sleep is the only thing between the two.
        time.sleep(0.6 + (0.5 * attempt))

        try:
            win.CaptureToImage(path)
            picture = Image.open(path).convert("RGB")
        except Exception:  # noqa: BLE001
            continue

        if looks_like_a_frame(picture, canvas_box(picture)):
            return True

    return False


def frame_bottom(whole, box=None, run=4, light=200, slack=8):
    """The canvas's last row — the bottom edge `canvas_box` gets wrong.

    `canvas_box` walks out from the canvas's centre and stops each walk at the first **long
    run** of light pixels, which is the right idea sideways and wrong downwards: below the
    preview sits the page, and the page is not uniformly light. The row of controls there —
    the accent-filled button, the scrubber — is dark again across exactly the same columns,
    so each dark band resets the streak and the walk steps over all of them. Measured on a
    170-pixel-tall preview: `canvas_box` answered 890 where the canvas ends at 852, a canvas
    0.5326 across where a 9:16 preview has to be 0.5625. `verify-position` then trimmed ten
    pixels off that as "the progress bar", which left the real bar (the frame's last two
    rows) *inside* the crop and the plot's right edge 50 pixels too far right.

    Read the other way round it needs no tolerance at all: rows *inside* the canvas are
    never light all the way across — the backdrop is near-black and a frame's light ink is
    thin — while every row of the page below it is. Four such rows in a row is the page, and
    the row above them is the canvas's last. The answer is exact: it lands within a pixel of
    the height the frame's own 9:16 says it should be, which is what lets a script assert
    the aspect ratio instead of assuming it.

    **And that is now the only thing it does**, because `canvas_box` stopped walking to the
    bottom: it takes the width — the one edge nothing else in the window is — and turns it into
    the height by the format's own 9:16, which is a fact rather than a measurement. So the row
    this walk finds is now one *page* below the canvas rather than a correction of it: with the
    row of dark controls sitting between the two, the walk steps over them and stops at the page
    under them (measured 924 against a canvas that ends at 851, 73 pixels too low). Answering
    with that would put the full-width progress bar back inside the crop this function exists to
    keep it out of, so it is only taken when the walk agrees with the box; otherwise the box
    stands. Kept rather than deleted because a caller still wants the *agreement* asked for: the
    box's bottom is a fact about the format, and the walk is the capture saying the same thing.

    Returns the row index of the canvas's last row, or `box[3]` when nothing light is found
    below the canvas.
    """
    if box is None:
        box = canvas_box(whole)

    if box is None:
        return None

    left, right, top, bottom = box
    pixels = whole.load()
    width = right - left + 1
    streak = 0

    for y in range((top + bottom) // 2, whole.size[1]):
        lit = 0

        for x in range(left, right + 1):
            r, g, b = pixels[x, y]

            if (r + g + b) / 3 > light:
                lit += 1

        if lit * 2 >= width:
            streak += 1

            if streak >= run:
                found = y - run

                return bottom if found > bottom + slack else found
        else:
            streak = 0

    return bottom
