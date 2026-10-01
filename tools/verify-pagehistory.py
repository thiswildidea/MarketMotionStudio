# -*- coding: utf-8 -*-
"""冒烟验证「页面导航」：标题栏的后退/前进按钮。

走一遍浏览器语义：首屏两个按钮都不可用 → 翻页后后退可用 → 后退后前进可用 →
另开新页后前进被清空 → 快捷键 Alt+Left 也能退。顺带确认按钮的无障碍名
（取的是资源里那个不带快捷键的词）。

用法：python tools/verify-pagehistory.py
"""
import os
import subprocess
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"


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


def find_all(cond, root, depth=0, limit=25, out=None):
    out = [] if out is None else out
    if depth > limit:
        return out
    try:
        if cond(root):
            out.append(root)
    except Exception:
        pass
    try:
        for ch in root.GetChildren():
            find_all(cond, ch, depth + 1, limit, out)
    except Exception:
        pass
    return out


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


def nav_items(win):
    """导航项：前若干个列表项，按导航里的顺序。"""
    items = find_all(lambda c: c.ControlTypeName == "ListItemControl", win, limit=8)
    return items


def selected_name(items):
    for item in items:
        p = pat(item, auto.PatternId.SelectionItemPattern)
        try:
            if p is not None and p.IsSelected:
                return item.Name
        except Exception:
            pass
    return None


def state(win, items):
    back = find(lambda c: c.AutomationId == "HistoryBackButton", win)
    forward = find(lambda c: c.AutomationId == "HistoryForwardButton", win)
    assert back is not None, "后退按钮未找到"
    assert forward is not None, "前进按钮未找到"
    return back, forward


def main():
    # 从头开始：历史是应用活着的时候攒的，接着上一次跑就会停在半路上，
    # 首屏那条断言也就无从谈起。
    if app_pids():
        subprocess.run(["taskkill", "/F", "/IM", EXE], capture_output=True)
        time.sleep(2)

    os.startfile(r"shell:AppsFolder\%s" % APPID)
    time.sleep(6)

    win = wait_window()
    assert win is not None, "窗口未找到"
    win.SetActive()
    win.MoveWindow(60, 60, 1400, 900)
    time.sleep(1.5)

    back, forward = state(win, None)
    print("names:", back.Name, "/", forward.Name)

    items = nav_items(win)
    assert len(items) >= 3, "导航项不足: %d" % len(items)
    print("nav:", [i.Name for i in items[:4]])

    # 首屏：没有去处，也没有来处。
    assert not back.IsEnabled, "首屏后退按钮应当不可用"
    assert not forward.IsEnabled, "首屏前进按钮应当不可用"
    print("start: on", selected_name(items), "back=off forward=off")

    first = selected_name(items)

    # 翻一页：后退可用。
    invoke_click(items[1])
    time.sleep(1.5)
    second = selected_name(items)
    assert second != first, "翻页后仍停在 %s" % first
    assert back.IsEnabled, "翻页后后退应当可用"
    assert not forward.IsEnabled, "翻页后前进仍应不可用"
    print("next: on", second, "back=on forward=off")

    # 后退：回到原页，前进出现。
    invoke_click(back)
    time.sleep(1.5)
    assert selected_name(items) == first, "后退后不在 %s，在 %s" % (first, selected_name(items))
    assert forward.IsEnabled, "后退后前进应当可用"
    print("back: on", selected_name(items), "forward=on")

    # 前进：回到第二页。
    invoke_click(forward)
    time.sleep(1.5)
    assert selected_name(items) == second, "前进后不在 %s" % second
    assert not forward.IsEnabled, "走到历史尽头后前进应当熄灭"
    print("forward: on", selected_name(items), "forward=off")

    # 另开新页：前方清空，像浏览器一样。
    invoke_click(items[2])
    time.sleep(1.5)
    third = selected_name(items)
    invoke_click(back)
    time.sleep(1.5)
    invoke_click(items[3])
    time.sleep(1.5)
    assert not forward.IsEnabled, "新开一页后前进应当清空"
    print("new page: on", selected_name(items), "forward=off")

    # Alt+Left 也要能退。窗口得先拿着焦点，按键才落在它身上；这一下对时序
    # 敏感，所以给几次机会。
    before = selected_name(items)
    win.SetActive()
    time.sleep(0.8)

    for _ in range(3):
        # 这个库按住修饰键的写法是 {Alt}(...)：括号里按完才松手。
        auto.SendKeys("{Alt}({Left})")
        time.sleep(1.5)

        if selected_name(items) != before:
            break

    after = selected_name(items)
    assert after != before, "Alt+Left 没有后退：仍在 %s" % before
    print("alt+left:", before, "->", after)

    win.CaptureToImage(os.path.join(OUT, "pagehistory-titlebar.png"))
    print("shot: pagehistory-titlebar.png")
    print("OK")


if __name__ == "__main__":
    main()
