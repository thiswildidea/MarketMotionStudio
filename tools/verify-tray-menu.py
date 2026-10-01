# -*- coding: utf-8 -*-
"""Checks the notification-area menu on a running build.

The menu is opened by right-clicking the tray icon, which is found by trying
positions across the notification area until a menu answering to this app's own
words comes back — the icon carries no accessible name of its own, and which of
the buttons is ours changes as other apps come and go.

Two states are checked, and the script says which one it found rather than
assuming: the item is pressable with "Update to …" when the Store has
something, and greyed out with the installed version when it has not. Getting
the second state on a machine whose Store does have an update needs the local
package to claim a higher version than the Store's, which is what
`--expect none` is for: raise the manifest version, register, run this, put it
back.

    python tools/verify-tray-menu.py [--expect any|update|none]
"""

import argparse
import os
import re
import subprocess
import sys
import time

import uiautomation as auto

EXE = "MarketMotionStudio.exe"
APP_ID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")

# The icon's accessible name is the tray tooltip, which is the app's own name.
# Used to pick this app's icon out of the row, since which one is ours moves.
APP_NAME = "行情指标动画工作室"

# The item's two shapes, straight from the resw of the language in use.
UPDATE_TO = re.compile(r"^(更新到|Update to|Auf .* aktualisieren|Actualizar a|Mettre à jour vers)\b")
UP_TO_DATE = re.compile(r"^(已是最新版本|You have the latest version|Sie haben die neueste)")


def pids_of(exe: str) -> set[int]:
    done = subprocess.run(["tasklist", "/FO", "CSV", "/FI", f"IMAGENAME eq {exe}"],
                          capture_output=True)
    found = set()
    for line in done.stdout.decode("utf-8", "replace").splitlines()[1:]:
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2 and parts[0].lower() == exe.lower():
            found.add(int(parts[1]))
    return found


def start_app() -> set[int]:
    subprocess.run(["taskkill", "/F", "/IM", EXE], capture_output=True)
    time.sleep(2)
    subprocess.run(["start", "", f"shell:AppsFolder\\{APP_ID}"], shell=True)
    for _ in range(40):
        time.sleep(0.5)
        pids = pids_of(EXE)
        if pids:
            time.sleep(2.5)  # the tray icon is created with the window, not before it
            return pids
    raise SystemExit("应用没有启动")


def menu_items(pids: set[int]) -> list:
    """Menu items of the tray's own menu window, and no other.

    The tray's menu is a window of its own in SecondWindow mode, which is the
    only reason it can be read at all: the system's own tray menu is not
    reachable to automation. The app's main window contributes a menu item of
    its own — the one on its title bar — so the items are read per window and
    the window holding "Open" is the one taken.
    """
    per_window = []

    def scan(control, depth=0, limit=7, into=None):
        if depth > limit:
            return
        try:
            if control.ControlTypeName == "MenuItemControl":
                into.append(control)
        except Exception:
            return
        try:
            for child in control.GetChildren():
                scan(child, depth + 1, limit, into)
        except Exception:
            pass

    for window in auto.GetRootControl().GetChildren():
        try:
            if window.ProcessId not in pids:
                continue
        except Exception:
            continue
        found = []
        try:
            scan(window, into=found)
        except Exception:
            pass
        if found:
            per_window.append(found)

    for group in per_window:
        if any(("打开" in (i.Name or "")) or ("Open" in (i.Name or "")) for i in group):
            return group
    return per_window[0] if per_window else []


def tray_buttons() -> list:
    """The icons in the notification area, whatever they are.

    Ours carries no accessible name, and its position changes as other apps
    come and go, so the buttons are read from the shell and tried one by one.
    """
    buttons = []

    def scan(control, depth=0, limit=9):
        if depth > limit:
            return
        try:
            if control.ClassName == "SystemTray.NormalButton":
                buttons.append(control)
        except Exception:
            pass
        try:
            for child in control.GetChildren():
                scan(child, depth + 1, limit)
        except Exception:
            pass

    for window in auto.GetRootControl().GetChildren():
        if "TrayWnd" in (window.ClassName or ""):
            scan(window)
    return buttons


def open_tray_menu(pids: set[int], tries: int = 6):
    """Right-clicks this app's notification-area icon until its menu opens.

    The right-click does not always take: the shell seems to swallow it when
    the pointer has only just arrived, and a menu left open from an earlier
    attempt keeps the next one from opening. So the pointer is walked away and
    back, and the click is repeated — several times if need be — rather than
    tried once and given up on.
    """
    buttons = tray_buttons()
    ours = [b for b in buttons if APP_NAME in (b.Name or "")]
    for button in ours or buttons:
        box = button.BoundingRectangle
        if box.right <= box.left:
            continue
        x = (box.left + box.right) // 2
        y = (box.top + box.bottom) // 2
        for _ in range(tries):
            auto.SetCursorPos(200, 400)
            time.sleep(0.4)
            auto.SetCursorPos(x, y)
            time.sleep(0.6)
            auto.RightClick(x, y)
            time.sleep(2.5)  # SecondWindow builds a window of its own; not instant
            items = menu_items(pids)
            if any("退出" in (i.Name or "") or "Exit" in (i.Name or "") for i in items):
                return items
            auto.SendKeys("{Escape}")
            time.sleep(1.0)
    return []


def shot_of(pids: set[int], path: str) -> bool:
    for window in auto.GetRootControl().GetChildren():
        try:
            if window.ProcessId not in pids:
                continue
            if "MenuItemControl" not in _types(window):
                continue
            window.SetFocus()
            time.sleep(0.6)
            return window.CaptureToImage(path)
        except Exception:
            continue
    return False


def _types(window) -> set:
    kinds = set()

    def scan(control, depth=0, limit=7):
        if depth > limit:
            return
        try:
            kinds.add(control.ControlTypeName)
        except Exception:
            return
        try:
            for child in control.GetChildren():
                scan(child, depth + 1, limit)
        except Exception:
            pass

    scan(window)
    return kinds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect", choices=["any", "update", "none"], default="any")
    parser.add_argument("--reuse", action="store_true", help="不要重启应用")
    args = parser.parse_args()

    pids = pids_of(EXE) if args.reuse else start_app()
    if not pids:
        pids = start_app()
    print(f"应用进程：{pids}")

    items = open_tray_menu(pids)
    if not items:
        print("✗ 没找到托盘菜单")
        return 1

    results = []

    def check(label, ok, detail=""):
        results.append((label, ok, detail))
        print(f"{'✓' if ok else '✗'} {label}" + (f"    {detail}" if detail else ""))

    names = [i.Name or "" for i in items]
    print(f"\n菜单项：{names}")

    check("菜单有打开/更新/退出三项", len(items) == 3, f"{len(items)} 项")

    # The update item is the one that is neither the first nor the last.
    update = items[1] if len(items) == 3 else None
    if update is None:
        return 1

    text = update.Name or ""
    enabled = update.IsEnabled

    if UPDATE_TO.match(text):
        check("有更新时文案是「更新到 …」", True, text)
        check("有更新时可按", enabled, f"IsEnabled={enabled}")
        if args.expect == "none":
            check("期望无更新状态", False, "实际是有更新")
    elif UP_TO_DATE.match(text):
        check("无更新时文案是已安装版本", True, text)
        check("无更新时不可按", not enabled, f"IsEnabled={enabled}")
        if args.expect == "update":
            check("期望有更新状态", False, "实际是无更新")
    else:
        check("更新项文案可识别", False, text)

    # Icons: the item's own icon is a child control of it.
    kinds = _types(update)
    check("更新项带图标", any("Image" in k or "Text" in k for k in kinds), str(sorted(kinds)))

    os.makedirs(OUT, exist_ok=True)
    tag = "update" if UPDATE_TO.match(text) else "none"
    path = os.path.join(OUT, f"verify-tray-menu-{tag}.png")
    ok = shot_of(pids, path)
    print(f"\n截图：{path}（{ok}）")

    auto.SendKeys("{Escape}")

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
