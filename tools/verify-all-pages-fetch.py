# -*- coding: utf-8 -*-
"""逐个页面点一次「取数」，确认改了复权口径之后没有哪一页取不到数。

改的是所有页面的价格序列：默认复权从 qfq 换成各市场自己的复权端点（港 hkfqkline+hfq、
美 usfqkline+qfq、A newfqkline+hfq），美股复权序列没有成交额所以还要回通用端点补一次，
月线也跟着换了端点。离线脚本能证明源端返回什么，证明不了页面还跑得起来——这个脚本跑
真实 UI，每个页面点一次取数，把状态条读出来。

用法：
    python tools/verify-all-pages-fetch.py
"""
import os
import re
import subprocess
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"

PRIVATE = re.compile(r"[\ue000-\uf8ff]")
BAD = re.compile(r"失败|错误|无法|不可用|failed|error")


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
            time.sleep(0.4)
            return True
        except Exception:
            pass
    p = pat(ctrl, auto.PatternId.SelectionItemPattern)
    if p is not None:
        try:
            p.Select()
            time.sleep(0.4)
            return True
        except Exception:
            pass
    try:
        ctrl.Click(simulateMove=False, waitTime=0.4)
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


def kill_app():
    subprocess.run(["taskkill", "/IM", EXE, "/F"], capture_output=True)
    time.sleep(2)


def launch():
    kill_app()
    os.startfile(r"shell:AppsFolder\%s" % APPID)
    deadline = time.time() + 45
    while time.time() < deadline:
        if app_pids():
            for w in auto.GetRootControl().GetChildren():
                if w.ProcessId in app_pids() and w.Name:
                    time.sleep(3)
                    return w
        time.sleep(1)
    return None


def status_text(win):
    bar = find(lambda c: c.AutomationId == "Status", win)
    if bar is None:
        return None
    texts = [t.Name for t in find_all(lambda c: c.ControlTypeName == "TextControl", bar, limit=8)
             if t.Name and not PRIVATE.search(t.Name)]
    return max(texts, key=len) if texts else None


def nav_items(win):
    return [it for it in find_all(lambda c: c.ControlTypeName == "ListItemControl", win, limit=8)
            if it.Name and it.Name not in ("设置", "Settings")]


def main():
    win = launch()
    assert win is not None, "窗口未找到"

    seen = []
    for name in [it.Name for it in nav_items(win)]:
        seen.append(name)

    print("导航项：", " / ".join(seen))
    print()

    for name in seen:
        item = find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name, win)
        if item is None:
            continue
        invoke_click(item)
        time.sleep(1.5)

        fetch = find(lambda c: c.AutomationId == "FetchButton", win)
        if fetch is None:
            print(f"{name:<12} （无取数按钮，跳过）")
            continue

        invoke_click(fetch)

        text = None
        deadline = time.time() + 45
        while time.time() < deadline:
            time.sleep(1.5)
            got = status_text(win)
            if got and got != text:
                text = got
                if not re.search(r"…|\.\.\.|正在|Fetching|读取", got):
                    break

        bad = bool(text and BAD.search(text))
        print(f"{name:<12} {'✗' if bad else '✓'} {text}")


if __name__ == "__main__":
    main()
