# -*- coding: utf-8 -*-
"""冒烟验证「定投计划」与「持仓收益」的取数——两个共用 HistoryWalk 分页回溯的页面。

要回答的核心问题：**区间起点落在休市日时，取数还能不能成。**
分页回溯的最后一步会请求 [区间起点, 已持有最早一根的前一天] 这一小段窗口；起点若正好
落在周末或假期（例如「近 5 年」从 2021-10-01 起，后面就是国庆长假），这段窗口里一根
bar 都没有——源端按窗口裁剪后返回空。`TencentKline.FetchStockBarsAsync` 曾把「窗口里
没有 bar」当成错误抛出来（"no daily bars in that range."），于是整条回溯在已经把多年
数据拿到手之后倒在了最后一步；现在它把空窗口当答案返回，回溯照设计停下。

顺带验证持仓页（同一个 walk）与长区间（13 年，5 次分页请求）。

用法：
    python tools/verify-dca-plan.py
"""
import os
import re
import subprocess
import sys
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"

PRIVATE = re.compile(r"[\ue000-\uf8ff]")
OK = re.compile(r"个交易日|trading days")
BAD = re.compile(r"失败|failed")


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
            time.sleep(0.6)
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


def launch():
    subprocess.run(["taskkill", "/IM", EXE, "/F"], capture_output=True)
    time.sleep(2)
    os.startfile(r"shell:AppsFolder\%s" % APPID)
    deadline = time.time() + 45
    while time.time() < deadline:
        pids = app_pids()
        if pids:
            for w in auto.GetRootControl().GetChildren():
                try:
                    if w.ControlTypeName == "WindowControl" and w.ProcessId in pids:
                        w.SetActive()
                        w.MoveWindow(60, 60, 1500, 940)
                        time.sleep(2)
                        return w
                except Exception:
                    pass
        time.sleep(1)
    return None


def status_text(win):
    """状态条里的消息文本。InfoBar 前面有个图标字形的 TextControl，要滤掉。"""
    bar = find(lambda c: c.AutomationId == "Status", win)
    if bar is None:
        return None
    texts = [t.Name for t in find_all(lambda c: c.ControlTypeName == "TextControl", bar, limit=8)
             if t.Name and not PRIVATE.search(t.Name)]
    return max(texts, key=len) if texts else None


def goto_page(win, automation_id, tries=12):
    for _ in range(tries):
        for it in find_all(lambda c: c.ControlTypeName == "ListItemControl", win, limit=8):
            invoke_click(it)
            time.sleep(1.2)
            if find(lambda c: c.AutomationId == automation_id, win) is not None:
                return True
        time.sleep(0.5)
    return False


def combo_pick(combo, index):
    p = pat(combo, auto.PatternId.ExpandCollapsePattern)
    if p is not None:
        try:
            p.Expand()
        except Exception:
            pass
    time.sleep(0.9)
    items = find_all(lambda c: c.ControlTypeName == "ListItemControl", combo, limit=6)
    if index >= len(items):
        raise AssertionError("下拉项不足: %d <= %d" % (len(items), index))
    name = items[index].Name
    sel = pat(items[index], auto.PatternId.SelectionItemPattern)
    if sel is not None:
        try:
            sel.Select()
        except Exception:
            pass
    else:
        items[index].Click(simulateMove=False, waitTime=0.5)
    time.sleep(0.9)
    auto.SendKeys("{Esc}")
    time.sleep(0.4)
    return name


def fetch_and_wait(win, seconds=240):
    """点「获取」，等一条终态消息（成功或失败），返回它。"""
    fetch = find(lambda c: c.AutomationId == "FetchButton", win)
    assert fetch is not None, "取数按钮未找到"
    invoke_click(fetch)

    deadline = time.time() + seconds
    while time.time() < deadline:
        text = status_text(win)
        if text and (OK.search(text) or BAD.search(text)):
            return text
        time.sleep(1.5)
    return None


def screenshot(win, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    try:
        from PIL import ImageGrab
        r = win.BoundingRectangle
        ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save(path)
        return path
    except Exception as ex:
        print("  (截图失败:", ex, ")")
        return None


FAILURES = []


def check(label, text):
    ok = bool(text) and bool(OK.search(text)) and not BAD.search(text)
    print("  %s %s -> %s" % ("PASS" if ok else "FAIL", label, text))
    if not ok:
        FAILURES.append(label)
    return ok


def main():
    win = launch()
    assert win is not None, "窗口未找到"

    # ---- 定投计划 -------------------------------------------------------------
    assert goto_page(win, "AmountBox"), "定投计划页未打开"
    print("定投计划页已打开")

    combo = find(lambda c: c.AutomationId == "RangeCombo", win)
    assert combo is not None, "区间下拉未找到"

    # 「近 5 年」：2026-10-01 往回五年 = 2021-10-01，国庆长假第一天，正是原来的翻车点。
    picked = combo_pick(combo, 1)
    print("区间:", picked)
    check("定投 近5年（起点 2021-10-01 假期）", fetch_and_wait(win))

    # 一键标的：换一个标的，顺带看画面标题跟不跟得上（截图留证）。
    preset = find(lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "黄金ETF", win)
    if preset is not None:
        invoke_click(preset)
        print("已点一键标的: 黄金ETF")
        check("定投 黄金ETF", fetch_and_wait(win))
        path = screenshot(win, "verify-dca-plan.png")
        if path:
            print("  截图:", path)
    else:
        print("  (未找到「黄金ETF」一键标的，跳过)")

    # 长区间：13 年，五次分页回溯，最后一次同样是「窗口里没有 bar」。
    picked = combo_pick(combo, 3)
    print("区间:", picked)
    check("定投 近13年（5 次分页）", fetch_and_wait(win))

    # ---- 持仓收益（同一个 HistoryWalk） ---------------------------------------
    assert goto_page(win, "CapitalBox"), "持仓收益页未打开"
    print("持仓收益页已打开")
    check("持仓 默认区间", fetch_and_wait(win))

    print()
    if FAILURES:
        print("FAIL:", ", ".join(FAILURES))
        sys.exit(2)
    print("全部通过")


if __name__ == "__main__":
    main()
