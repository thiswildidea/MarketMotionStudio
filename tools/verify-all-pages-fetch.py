# -*- coding: utf-8 -*-
"""逐个页面点一次「取数」，确认改了复权口径之后没有哪一页取不到数。

改的是所有页面的价格序列：默认复权从 qfq 换成各市场自己的复权端点（港 hkfqkline+hfq、
美 usfqkline+qfq、A newfqkline+hfq），美股复权序列没有成交额所以还要回通用端点补一次，
月线也跟着换了端点。离线脚本能证明源端返回什么，证明不了页面还跑得起来——这个脚本跑
真实 UI，每个页面点一次取数，把状态条读出来。

用法：
    python tools/verify-all-pages-fetch.py            # A股，茅台
    python tools/verify-all-pages-fetch.py 00700      # 港股
    python tools/verify-all-pages-fetch.py AAPL       # 美股

成交量换手率页没有默认标的（搜索框空着就是没有标的），所以只有那一页需要先填一个代码
再点取数。给的代码按当前市场选——A股 600519、港股 00700、美股 AAPL。
"""
import os
import subprocess
import re
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402  - the shared window/control plumbing lives beside this file

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"

PRIVATE = re.compile(r"[\ue000-\uf8ff]")
# "不属于" is in here because a page that remembers another market's instrument
# answers "该代码不属于当前市场" — a fetch that never ran, which has to look like
# the failure it is rather than like a status line with no bad words in it.
BAD = re.compile(r"失败|错误|无法|不可用|不属于|failed|error")


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


def kill_app():
    subprocess.run(["taskkill", "/IM", EXE, "/F"], capture_output=True)
    time.sleep(2)


def launch():
    kill_app()
    os.startfile(r"shell:AppsFolder\%s" % APPID)
    win = winui.app_window(EXE, wait_seconds=45)
    time.sleep(3)
    return win


def chosen_text(win):
    """What the volume page says it has picked.

    Never empty: before anything is picked it carries the "nothing chosen" line,
    so the way to tell is a change, not a presence.
    """
    box = find(lambda c: c.AutomationId == "ChosenText", win)
    return box.Name.strip() if box is not None and box.Name else ""


def search_text(win):
    """What is typed in the volume page's box, or None if it is not this page."""
    box = find(lambda c: c.AutomationId == "StockSearch", win)

    if box is None:
        return None

    edit = find(lambda c: c.AutomationId == "TextBox", box, limit=6)

    if edit is None:
        return None

    try:
        return edit.GetValuePattern().Value.strip()
    except Exception:  # noqa: BLE001
        return ""


def pick_instrument(win, code):
    """Fill the volume page's search box and submit it.

    Only that page needs this: every other one opens with its own instrument and
    answers a click on 取数 straight away. This one has to be told which stock,
    and an empty box is no stock at all — the page answers "无法识别这个代码" and
    the sweep reports a failure that has nothing to do with the fetch under test.

    Overwrites whatever is there rather than filling only an empty box. The page
    remembers the last instrument it fetched, so after a run against another
    market the box opens holding that market's code — and clicking 取数 then
    reports "不属于当前市场", which is true and says nothing about this market.

    The code goes in through the clipboard rather than keystrokes: Chinese will
    not type into an AutoSuggestBox, and although a code is only digits, using
    the same route for both is cheaper than remembering which needs which.

    The keystrokes go to the inner edit, not to `StockSearch` itself — that one
    is a GroupControl wrapping the edit, and it is the edit that holds the text.
    """
    box = find(lambda c: c.AutomationId == "StockSearch", win)
    edit = None if box is None else find(lambda c: c.AutomationId == "TextBox", box, limit=6)

    if edit is None:
        return False

    edit.SetFocus()
    time.sleep(0.3)
    edit.SendKeys("{Ctrl}a", waitTime=0.3)
    auto.SetClipboardText(code)
    edit.SendKeys("{Ctrl}v", waitTime=0.5)

    deadline = time.time() + 5
    while time.time() < deadline:
        if search_text(win) == code:
            break
        time.sleep(0.3)
    else:
        return False

    # Enter, not a click on a suggestion: the box resolves a bare code itself, and
    # the drop-down is a separate top-level window that has to be found by luck.
    edit.SendKeys("{Enter}", waitTime=0.5)

    # Submitted, not proven. Whether the code belongs to this market is the fetch's
    # own answer to report, and waiting on that here would only hide it.
    time.sleep(2.0)
    return True


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
    code = sys.argv[1] if len(sys.argv) > 1 else "600519"

    win = launch()
    assert win is not None, "窗口未找到"

    seen = []
    for name in [it.Name for it in nav_items(win)]:
        seen.append(name)

    print("导航项：", " / ".join(seen))
    print("标的：", code)
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

        # Only the volume page has a box to fill, and it has to be overwritten
        # rather than topped up — see pick_instrument. `ChosenText` is the tell:
        # two other pages carry a `StockSearch` too, both inside a panel that is
        # collapsed until a custom mode is picked, and filling one of those would
        # quietly change which instrument the sweep is testing.
        if find(lambda c: c.AutomationId == "ChosenText", win) is not None \
                and search_text(win) is not None:
            if not pick_instrument(win, code):
                print(f"{name:<12} ✗ 没能选上标的 {code}")
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
