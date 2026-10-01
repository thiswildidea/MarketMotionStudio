# -*- coding: utf-8 -*-
"""冒烟验证「行业板块竞速」的板块名本地化与列表归属。

要回答两件事：
  1. 下拉里列出的竞速列表，是不是当前市场的那一份；
  2. 从内置列表跑出来的板块名，是不是跟着界面语言走。

做法：可选先把界面语言切成别的（语言只在重启后生效）→ 进竞速页 → 读出 roster
下拉的全部选项 → 选中内置列表的第一项 → 取数 → 读状态条里那句「领先 X / leading X」，
检查那个名字的语言与界面语言是否一致。

用法：
    python tools/verify-sectornames.py               # 按当前语言验证
    python tools/verify-sectornames.py --lang en-US  # 先切英文（重启后）再验证
    python tools/verify-sectornames.py --lang ""     # 先恢复「跟随系统」再验证
"""
import argparse
import os
import re
import subprocess
import sys
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"

SETTINGS_NAMES = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки"]

# SettingsPage 的语言下拉顺序，见 Pages/SettingsPage.xaml.cs。
LANGUAGES = ["", "en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
             "ja", "ko", "zh-Hans", "zh-Hant"]

CJK = re.compile(r"[\u4e00-\u9fff]")
PRIVATE = re.compile(r"[\ue000-\uf8ff]")
DONE = re.compile(r"trading days|个交易日")


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


def kill_app():
    subprocess.run(["taskkill", "/IM", EXE, "/F"], capture_output=True)
    time.sleep(2)


def launch(maximized=True):
    kill_app()
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


def combo_items(combo, tries=3):
    """展开下拉，返回选项文本列表。弹窗第一遍常扫不到，要重试。"""
    for _ in range(tries):
        p = pat(combo, auto.PatternId.ExpandCollapsePattern)
        if p is not None:
            try:
                p.Expand()
            except Exception:
                pass
        time.sleep(0.8)
        items = find_all(lambda c: c.ControlTypeName == "ListItemControl" and c.Name, combo, limit=6)
        if items:
            return [i.Name for i in items]
        auto.SendKeys("{Esc}")
        time.sleep(0.4)
    return []


def combo_pick(combo, index):
    """选中第 index 项，返回它的文本。展开再点，收起来再走。"""
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


def status_text(win):
    """状态条里的消息文本。InfoBar 前面有个图标字形的 TextControl，要滤掉。"""
    bar = find(lambda c: c.AutomationId == "Status", win)
    if bar is None:
        return None
    texts = [t.Name for t in find_all(lambda c: c.ControlTypeName == "TextControl", bar, limit=8)
             if t.Name and not PRIVATE.search(t.Name)]
    return max(texts, key=len) if texts else None


def goto_settings(win):
    for name in SETTINGS_NAMES:
        nav = find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name, win)
        if nav is not None:
            invoke_click(nav)
            time.sleep(2)
            return True
    return False


def goto_page_with_control(win, automation_id):
    """导航里逐个试，直到带这个 AutomationId 的控件出现。"""
    for _ in range(12):
        for it in find_all(lambda c: c.ControlTypeName == "ListItemControl", win, limit=8):
            invoke_click(it)
            time.sleep(1.2)
            if find(lambda c: c.AutomationId == automation_id, win) is not None:
                return True
        time.sleep(0.5)
    return False


def set_language(tag):
    """把界面语言切成 tag（空串 = 跟随系统）。切完要重启才生效。"""
    win = launch()
    assert win is not None, "窗口未找到"
    assert goto_settings(win), "设置页未打开"

    combo = find(lambda c: c.AutomationId == "LanguageCombo", win)
    assert combo is not None, "语言下拉未找到"

    index = LANGUAGES.index(tag)
    picked = combo_pick(combo, index)
    print("语言已切到:", picked if picked else "(跟随系统)")
    time.sleep(1.5)


MARKETS = {"a": 0, "hk": 1, "us": 2}


def set_market(tag):
    """把市场切成 a / hk / us。与语言一样，只存不应用，要重启。"""
    win = launch()
    assert win is not None, "窗口未找到"
    assert goto_settings(win), "设置页未打开"

    combo = find(lambda c: c.AutomationId == "MarketCombo", win)
    assert combo is not None, "市场下拉未找到"

    picked = combo_pick(combo, MARKETS[tag.lower()])
    print("市场已切到:", picked)
    time.sleep(1.5)


def verify(roster_index=0, expect_roster=None, do_fetch=True):
    win = launch()
    assert win is not None, "窗口未找到"

    assert goto_page_with_control(win, "RosterCombo"), "竞速页未打开"
    print("竞速页已打开")

    roster = find(lambda c: c.AutomationId == "RosterCombo", win)
    lists = combo_items(roster)
    print("下拉里的竞速列表:", lists)
    assert lists, "下拉里没有选项"

    restored = current_selection(roster, expand=True)
    print("恢复后的选中项:", restored)
    if expect_roster is not None:
        got = restored
        if got != expect_roster:
            print("FAIL 恢复的选中项不是预期的: 期望 %r 实得 %r" % (expect_roster, got))
            sys.exit(2)

    english = not CJK.search(" ".join(lists))
    print("界面语言判定:", "英文" if english else "中文")

    picked = combo_pick(roster, roster_index)
    print("选中的列表:", picked)
    time.sleep(1.0)

    if not do_fetch:
        print("(不取数)")
        return

    fetch = find(lambda c: c.AutomationId == "FetchButton", win)
    assert fetch is not None, "取数按钮未找到"
    invoke_click(fetch)
    print("已请求取数，等待状态条…")

    text = None
    deadline = time.time() + 240
    while time.time() < deadline:
        candidate = status_text(win)
        if candidate and DONE.search(candidate):
            text = candidate
            break
        time.sleep(2)

    assert text, "状态条始终没出取数结果"
    print("状态条:", text)

    names = re.findall(r"(?:leading|领先|領先)\s*([^ ]+)", text)
    assert names, "状态条里没找到领先板块的名字: " + text

    bad = [n for n in names if bool(CJK.search(n)) == english]
    if bad:
        print("FAIL 板块名与界面语言不一致:", bad)
        sys.exit(1)

    win.CaptureToImage(os.path.join(OUT, "sectornames-check.png"))
    print("OK 板块名跟随界面语言:", names)


def current_selection(combo, expand=False):
    """当前选中项的文本。

    收起状态下 ComboBox 里只剩一个显示当前值的文本控件，读到的到底是它还是列表
    首项并不确定；展开着读 SelectionItemPattern 才是准的，所以问这种问题时先展开。
    """
    if expand:
        p = pat(combo, auto.PatternId.ExpandCollapsePattern)
        if p is not None:
            try:
                p.Expand()
            except Exception:
                pass
        time.sleep(0.9)

    for it in find_all(lambda c: c.ControlTypeName == "ListItemControl", combo, limit=6):
        p = pat(it, auto.PatternId.SelectionItemPattern)
        try:
            if p is not None and p.IsSelected:
                auto.SendKeys("{Esc}")
                time.sleep(0.3)
                return it.Name
        except Exception:
            pass

    auto.SendKeys("{Esc}")
    time.sleep(0.3)

    for t in find_all(lambda c: c.ControlTypeName == "TextControl", combo, limit=8):
        if t.Name:
            return t.Name
    return combo.Name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default=None,
                        help="先把界面语言切成这个标签再验证；空串表示跟随系统")
    parser.add_argument("--market", default=None, help="先把市场切成 a / hk / us 再验证")
    parser.add_argument("--roster", type=int, default=0, help="取数前选中第几个竞速列表")
    parser.add_argument("--no-fetch", action="store_true", help="只读下拉与恢复值，不取数")
    parser.add_argument("--expect-roster", default=None,
                        help="断言页面恢复出来的选中项文本（用来看跨市场的偏好错位）")
    args = parser.parse_args()

    if args.lang is not None:
        set_language(args.lang)

    if args.market is not None:
        set_market(args.market)

    verify(args.roster, args.expect_roster, do_fetch=not args.no_fetch)


if __name__ == "__main__":
    main()
