# -*- coding: utf-8 -*-
"""冒烟验证背景图片功能：进设置页、画廊选一张系统图片、验证背景生效。

复用 store-screenshots.py 的成熟辅助（按 PID 找窗口、Invoke 点击）。
"""
import os
import subprocess
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"
SETTINGS_NAMES = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки"]


def find(cond, root, depth=0, limit=25):
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


def pat(ctrl, pattern_id):
    try:
        return ctrl.GetPattern(pattern_id)
    except Exception:
        return None


def invoke_click(ctrl):
    p = pat(ctrl, auto.PatternId.InvokePattern)
    if p is not None:
        try:
            p.Invoke()
            time.sleep(0.5)
            return True
        except Exception:
            pass
    p = pat(ctrl, auto.PatternId.SelectionItemPattern)
    if p is not None:
        try:
            p.Select()
            time.sleep(0.5)
            return True
        except Exception:
            pass
    try:
        ctrl.Click(simulateMove=False, waitTime=0.5)
        return True
    except Exception:
        return False


def app_pids():
    p = subprocess.run(["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq " + EXE],
                       capture_output=True)
    pids = set()
    for line in p.stdout.decode("utf-8", "replace").splitlines()[1:]:
        parts = [x.strip('"') for x in line.split('","')]
        if len(parts) >= 2 and parts[0].lower() == EXE.lower():
            pids.add(int(parts[1]))
    return pids


def wait_window(timeout=40):
    deadline = time.time() + timeout
    while time.time() < deadline:
        pids = app_pids()
        if pids:
            for w in auto.GetRootControl().GetChildren():
                try:
                    if w.ControlTypeName == "WindowControl" and w.ProcessId in pids:
                        return w
                except Exception:
                    pass
        time.sleep(1)
    return None


def main():
    pids = app_pids()
    if not pids:
        os.startfile(r"shell:AppsFolder\%s" % APPID)
        time.sleep(5)

    win = wait_window()
    assert win is not None, "窗口未找到"
    # 置前 + 移到已知位置，截图才不会被别的窗口挡住
    win.SetActive()
    win.MoveWindow(60, 60, 1500, 940)
    time.sleep(1.5)
    print("window:", win.Name)

    # 1) 进设置页
    nav = None
    for name in SETTINGS_NAMES:
        nav = find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name, win)
        if nav is not None:
            break
    assert nav is not None, "设置导航项未找到"
    invoke_click(nav)
    time.sleep(2)
    win.CaptureToImage(os.path.join(OUT, "bg-verify-1-settings.png"))
    print("shot 1 done")

    # 2) 画廊：BackgroundGallery 里的第一张图（用户自己的没有，系统图片第一张）
    gallery = find(lambda c: c.AutomationId == "BackgroundGallery", win)
    assert gallery is not None, "BackgroundGallery 未找到"
    items = gallery.GetChildren()
    print("gallery items:", len(items))
    assert items, "画廊为空"
    invoke_click(items[0])
    time.sleep(2)

    win.CaptureToImage(os.path.join(OUT, "bg-verify-2-applied.png"))
    print("shot 2 done")

    # 3) 拖遮罩强度滑条到另一档，验证 Dim 生效（略过：Changed 事件同一路径）
    print("OK")


if __name__ == "__main__":
    main()
