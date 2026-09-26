# -*- coding: utf-8 -*-
"""Drives the running app end to end: launch, fetch, export — and reports what happened.

This is the harness that proved export works. It needs `uiautomation` and the app to be
registered already:

    <python> -m pip install uiautomation
    cd src\\AShareMotionStudio\\bin\\x64\\Debug\\net10.0-windows10.0.26100.0
    Add-AppxPackage -Register .\\AppxManifest.xml

Then: `<python> tools\\drive-studio.py`, and read `artifacts\\drive4.txt` afterwards.
It writes to that file as it goes, so a failure part-way still leaves what was learned.

Two things it settles. Whether the three buttons that need a series are disabled before a
fetch and enabled after — a change to `MarketTurnoverPage` — and how far the encoder gets,
which it reads out of the app's own crash log rather than off the screen. `CrashLog.Note`
appends and flushes line by line, so the last line written before it stops is the answer;
a closed InfoBar is not, because it looks the same whether the code hung or never ran.

Note the window is found by title, which means **this only finds a Chinese-language
instance**. Change `Name=` below if the app is pinned to another language.
"""
import io, os, time, subprocess
import uiautomation as auto

LOG = r"D:\software\AShareMotionStudio\artifacts\drive4.txt"
CRASH = r"C:\Users\user\AppData\Local\Packages\AShareMotionStudio.Dev_cdwthxytk4q78\LocalState\crash.log"
APPID = "AShareMotionStudio.Dev_cdwthxytk4q78!App"

def say(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

def crash_since(offset):
    try:
        with open(CRASH, "rb") as f:
            f.seek(offset)
            return f.read().decode("utf-8", "replace")
    except Exception as e:
        return "(unreadable: %r)" % e

def find(cond, root, depth=0, limit=18):
    if depth > limit:
        return None
    try:
        if cond(root):
            return root
    except Exception:
        return None
    for ch in root.GetChildren():
        r = find(cond, ch, depth + 1, limit)
        if r is not None:
            return r
    return None

def btn(root, name):
    return find(lambda c: c.ControlTypeName == "ButtonControl" and c.Name == name, root)

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
        if d > 18:
            return
        try:
            if c.ControlTypeName in ("TextControl", "EditControl") and c.Name:
                got.append(c.Name)
        except Exception:
            return
        for ch in c.GetChildren():
            walk(ch, d + 1)
    walk(root, 0)
    return got

open(LOG, "w", encoding="utf-8").close()

try:
    with open(CRASH, "rb") as f:
        offset = f.seek(0, os.SEEK_END)
except Exception:
    offset = 0
say("crash.log offset before run: %d" % offset)

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

say("window handle=%s" % win.NativeWindowHandle)

# --- before fetch: the change under test ------------------------------------
for n in ("播放", "导出 MP4", "导出封面 PNG", "获取数据"):
    b = btn(win, n)
    say("before fetch: %-14s enabled=%s" % (n, (b.IsEnabled if b else "NOT FOUND")))

# --- fetch -------------------------------------------------------------------
before = set(texts(win))
b = btn(win, "获取数据")
if b and b.IsEnabled:
    b.Click()
    say("clicked 获取数据")
    status = None
    for _ in range(60):
        time.sleep(2)
        for t in texts(win):
            if t not in before and ("交易日" in t or "失败" in t or "错误" in t or "超时" in t or "过长" in t):
                status = t
                break
        if status:
            break
    say("fetch status: %s" % (status or "(none within 120s)"))
else:
    say("fetch button not clickable")

for n in ("播放", "导出 MP4", "导出封面 PNG"):
    x = btn(win, n)
    say("after fetch:  %-14s enabled=%s" % (n, (x.IsEnabled if x else "NOT FOUND")))

# --- shortest video, so a hang is cheap --------------------------------------
sliders = []
def collect(c, d):
    if d > 18:
        return
    try:
        if c.ControlTypeName == "SliderControl":
            sliders.append(c)
    except Exception:
        return
    for ch in c.GetChildren():
        collect(ch, d + 1)
collect(win, 0)
if sliders:
    try:
        sliders[0].SetFocus()
        auto.SendKeys("{Home}")
        time.sleep(1)
        for t in texts(win):
            if "视频时长" in t:
                say("duration set to minimum: %s" % t)
    except Exception as e:
        say("slider Home failed: %r" % e)

# --- export ------------------------------------------------------------------
b = btn(win, "导出 MP4")
say("export button enabled=%s" % (b.IsEnabled if b else "NOT FOUND"))
if b and b.IsEnabled:
    b.Click()
    say("clicked 导出 MP4")
    for i in range(36):
        time.sleep(5)
        a = alive()
        say("  t=%3ds alive=%s" % ((i + 1) * 5, a))
        if a is False:
            say("  PROCESS EXITED at ~%ds" % ((i + 1) * 5))
            break
else:
    say("export not clickable")

say("--- crash.log written during this run ---")
say(crash_since(offset))
say("--- end ---")
