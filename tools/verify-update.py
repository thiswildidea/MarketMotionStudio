# -*- coding: utf-8 -*-
r"""冒烟验证：导航栏「设置」旁的商店更新按钮。

走的是 StoreUpdates 的 Debug 模拟路径（LocalState\simulate-store-update.txt
里写一个版本号，Debug 版就当商店有那个版本），所以整条链路——按钮出现、
点击、进度计数、装完消失——在一台没有真实商店更新的开发机上也能走完。

用法：
    python -c "open(r'<LocalState>\\simulate-store-update.txt','w').write('9.9.9')"
    python tools\verify-update.py
"""
import os
import subprocess
import sys
import time

import uiautomation as auto

EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"
VERSION = "9.9.9"


def find(cond, root, depth=0, limit=25):
    if depth > limit:
        return None
    try:
        if cond(root):
            return root
    except Exception:
        return None
    try:
        for child in root.GetChildren():
            hit = find(cond, child, depth + 1, limit)
            if hit is not None:
                return hit
    except Exception:
        pass
    return None


def pattern(control, pid):
    try:
        return control.GetPattern(pid)
    except Exception:
        return None


def invoke(control):
    p = pattern(control, auto.PatternId.InvokePattern)
    if p is not None:
        try:
            p.Invoke()
            return True
        except Exception:
            pass
    try:
        control.Click(simulateMove=False, waitTime=0.4)
        return True
    except Exception:
        return False


def pids():
    out = subprocess.run(["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq " + EXE], capture_output=True)
    text = out.stdout.decode("utf-8", "replace")
    found = set()
    for line in text.splitlines()[1:]:
        if EXE.lower() in line.lower():
            found.add(int(line.split('","')[1].strip('"')))
    return found


def window():
    for _ in range(10):
        for w in auto.GetRootControl().GetChildren():
            try:
                if w.ControlTypeName == "WindowControl" and w.ProcessId in pids():
                    return w
            except Exception:
                pass
        time.sleep(1)
    return None


def shot(win, name):
    path = os.path.join(OUT, name)
    win.CaptureToImage(path)
    print("  截图:", name)


def update_button(win):
    # 按钮的无障碍名 = 悬停提示 = 「…有新版本 9.9.9。…」
    return find(
        lambda c: c.ControlTypeName == "ButtonControl" and VERSION in (c.Name or ""),
        win,
    )


def state(win):
    """当前设置项那一行是什么样：按钮在不在、写着什么。"""
    btn = find(lambda c: c.ControlTypeName == "ButtonControl" and "更新" in (c.Name or ""), win)
    btn2 = update_button(win)
    any_btn = btn or btn2
    if any_btn is None:
        return "无更新按钮"
    caption = find(
        lambda c: c.ControlTypeName == "TextControl" and (c.Name or "").startswith("正在更新"),
        any_btn,
    )
    return f"按钮在（{any_btn.Name[:24]}…）" + (f" / 标题 {caption.Name}" if caption else "")


def main():
    win = window()
    if win is None:
        print("找不到应用窗口——先启动应用")
        return 1

    win.SetActive()
    win.MoveWindow(60, 60, 1500, 940)
    time.sleep(3)

    print("1) 检查完成后的状态")
    btn = None
    for _ in range(10):
        btn = update_button(win)
        if btn is not None:
            break
        time.sleep(1)
    if btn is None:
        print("  ✗ 更新按钮没有出现——模拟文件读到了吗？")
        shot(win, "upd-verify-1-missing.png")
        return 1
    print("  ✓", state(win))
    shot(win, "upd-verify-1-present.png")

    print("2) 点更新，看进度计数")
    caption_seen = False
    if not invoke(btn):
        print("  ✗ 点击失败")
        return 1
    deadline = time.time() + 2.2
    while time.time() < deadline:
        caption = find(
            lambda c: c.ControlTypeName == "TextControl" and (c.Name or "").startswith("正在更新"),
            win,
        )
        if caption is not None:
            caption_seen = True
            print("  ✓ 进度:", caption.Name)
            shot(win, "upd-verify-2-progress.png")
            break
        time.sleep(0.15)
    if not caption_seen:
        print("  ! 没抓到进度帧（模拟安装 3 秒，可能已过去）")

    print("3) 等安装结束，按钮应当消失")
    gone = False
    for _ in range(30):
        if update_button(win) is None:
            gone = True
            break
        time.sleep(0.5)
    print("  ✓ 按钮已消失" if gone else "  ✗ 按钮仍在")
    time.sleep(0.5)
    shot(win, "upd-verify-3-done.png")

    return 0


if __name__ == "__main__":
    sys.exit(main())
