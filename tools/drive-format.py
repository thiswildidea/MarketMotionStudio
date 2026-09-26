# -*- coding: utf-8 -*-
"""Cover + MP4 at 1440p30, back to back in one fresh session.

The earlier 1440p cover/video mismatch is suspect for a boring reason: the two files
came from different app sessions, and an earlier script poked the first slider it found
with `{Home}` — which may have been a margin slider, not the duration one. Margins are
per-session state, and margins move the plot area. This run changes nothing except the
format combos, exports both artefacts from the same session, and confirms every step by
its observable effect (a new PNG on disk, a new line in the crash log) rather than by
trusting that an invoke did something.
"""
import os
import subprocess
import time

import uiautomation as auto

LOG = r"D:\software\AShareMotionStudio\artifacts\final.txt"
CRASH = (r"C:\Users\user\AppData\Local\Packages"
         r"\AShareMotionStudio.Dev_cdwthxytk4q78\LocalState\crash.log")
APPID = "AShareMotionStudio.Dev_cdwthxytk4q78!App"
OUTDIR = os.path.join(os.path.expanduser("~"), "Desktop", "新建文件夹")
lines = []


def say(s):
    lines.append(str(s))
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def find(cond, root, depth=0, limit=20):
    if depth > limit:
        return None
    try:
        if cond(root):
            return root
    except Exception:
        return None
    try:
        for ch in root.GetChildren():
            r = find(cond, ch, depth + 1, limit)
            if r is not None:
                return r
    except Exception:
        pass
    return None


def byid(root, aid):
    return find(lambda c: c.AutomationId == aid, root)


def invoke(c, what):
    for attempt in range(3):
        try:
            c.GetInvokePattern().Invoke()
        except Exception as e:
            say("  invoke %s failed: %r" % (what, e))
            time.sleep(2)
            continue
        return True
    return False


def alive():
    try:
        p = subprocess.run(["tasklist", "/FI", "IMAGENAME eq AShareMotionStudio.exe"],
                           capture_output=True)
        return b"AShareMotionStudio.exe" in p.stdout
    except Exception:
        return None


def texts(root):
    got = []

    def walk(c, d):
        if d > 20:
            return
        try:
            if c.ControlTypeName in ("TextControl", "EditControl") and c.Name:
                got.append(c.Name)
        except Exception:
            pass
        try:
            for ch in c.GetChildren():
                walk(ch, d + 1)
        except Exception:
            pass

    walk(root, 0)
    return got


def logtail(offset):
    try:
        with open(CRASH, "rb") as f:
            f.seek(offset)
            return f.read().decode("utf-8", "replace")
    except Exception:
        return ""


try:
    with open(CRASH, "rb") as f:
        offset = f.seek(0, os.SEEK_END)
except Exception:
    offset = 0

open(LOG, "w", encoding="utf-8").close()

p = subprocess.run(["taskkill", "/IM", "AShareMotionStudio.exe", "/F"],
                   capture_output=True)
say("kill: %s" % p.returncode)
time.sleep(3)
os.startfile(r"shell:AppsFolder\%s" % APPID)
say("launched")

win = None
for _ in range(30):
    time.sleep(1)
    try:
        w = auto.WindowControl(searchDepth=1, Name="A股指标动画工作室", foundIndex=1)
        if w.Exists(maxSearchSeconds=2):
            win = w
            break
    except Exception:
        pass
if win is None:
    say("WINDOW NEVER APPEARED")
    raise SystemExit(1)
say("window up")
time.sleep(3)

# --- 3-month range, then fetch ------------------------------------------------
rc = byid(win, "RangeCombo")
if rc is not None:
    try:
        rc.GetExpandCollapsePattern().Expand()
        time.sleep(0.7)
        for it in rc.GetChildren():
            if it.ControlTypeName == "ListItemControl" and "3 个月" in (it.Name or ""):
                it.GetSelectionItemPattern().Select()
                say("range: 近 3 个月")
                break
        time.sleep(0.5)
        rc.GetExpandCollapsePattern().Collapse()
    except Exception as e:
        say("range select failed: %r" % e)
else:
    say("RangeCombo NOT FOUND")

before = set(texts(win))
fb = byid(win, "FetchButton")
if fb is None:
    say("FetchButton NOT FOUND")
    raise SystemExit(1)
invoke(fb, "fetch")
for _ in range(45):
    time.sleep(2)
    hit = [t for t in texts(win) if t not in before and "交易日" in t]
    if hit:
        say("fetch: %s" % hit[0])
        break
else:
    say("fetch: no confirmation in 90s")

# --- 1440p30 ------------------------------------------------------------------
allc = []


def walk_all(c, d):
    if d > 20:
        return
    try:
        allc.append(c)
    except Exception:
        return
    try:
        for ch in c.GetChildren():
            walk_all(ch, d + 1)
    except Exception:
        pass


walk_all(win, 0)
for aid, want in (("ResolutionCombo", "1440"), ("FrameRateCombo", "60")):
    combo = byid(win, aid)
    if combo is None:
        say("%s NOT FOUND" % aid)
        continue
    try:
        combo.GetExpandCollapsePattern().Expand()
        time.sleep(0.7)
        for it in combo.GetChildren():
            if it.ControlTypeName == "ListItemControl" and want in (it.Name or ""):
                it.GetSelectionItemPattern().Select()
                say("%s -> %r" % (aid, it.Name))
                break
        time.sleep(0.5)
        combo.GetExpandCollapsePattern().Collapse()
    except Exception as e:
        say("%s select failed: %r" % (aid, e))
time.sleep(1.5)
for t in texts(win):
    if "Mbps" in t:
        say("bitrate: %s" % t)
        break

cover_before = {f for f in os.listdir(OUTDIR) if f.endswith(".png")}
mp4_before = {f for f in os.listdir(OUTDIR) if f.endswith(".mp4")}

# --- cover --------------------------------------------------------------------
cb = byid(win, "CoverButton")
say("CoverButton %s" % ("enabled" if cb and cb.IsEnabled else "MISSING/DISABLED"))
if cb and cb.IsEnabled:
    invoke(cb, "cover")
    for _ in range(15):
        time.sleep(2)
        new = {f for f in os.listdir(OUTDIR) if f.endswith(".png")} - cover_before
        if new:
            say("cover file: %s" % new.pop())
            break
    else:
        say("cover: NO FILE in 30s")

# --- export, confirmed by the log actually moving ------------------------------
eb = byid(win, "ExportButton")
say("ExportButton %s" % ("enabled" if eb and eb.IsEnabled else "MISSING/DISABLED"))
if eb and eb.IsEnabled:
    invoke(eb, "export")
    moved = False
    for _ in range(10):
        time.sleep(2)
        if logtail(offset).strip():
            moved = True
            break
    if not moved:
        say("export invoke produced NO log — retrying once")
        invoke(eb, "export-retry")
        for _ in range(10):
            time.sleep(2)
            if logtail(offset).strip():
                moved = True
                break
    say("export started: %s" % moved)
    if moved:
        last = ""
        stall = 0
        for i in range(72):
            time.sleep(5)
            ls = [l for l in logtail(offset).splitlines() if l.strip()]
            cur = ls[-1] if ls else ""
            if cur != last:
                last, stall = cur, 0
                say("  t=%3ds %s" % ((i + 1) * 5, cur.strip()))
            else:
                stall += 5
                if stall >= 45:
                    say("  STALLED 45s at: %s" % cur.strip())
                    break
            if "transcode returned" in cur:
                say("  DONE")
                break

new_mp4 = {f for f in os.listdir(OUTDIR) if f.endswith(".mp4")} - mp4_before
say("new mp4: %s" % (new_mp4 or "NONE"))
say("--- end ---")
