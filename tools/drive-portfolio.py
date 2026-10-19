# -*- coding: utf-8 -*-
"""端到端驱动「实时持仓收益」页：抓取 → 封面 → 导出。

假设应用已经部署（Add-AppxPackage -Register）。它启动应用、切到持仓收益页，
点取数，再点封面与导出，把每一步的结果写进 artifacts/drive-portfolio.txt，
并读取应用自己的 crash.log 看运行期间有没有报错。

判据：
- 抓取成功：SummaryText 变了（或 UpdatedText 的时间戳变了），且状态栏没有坏词。
- 抓取失败：状态栏出现 失败/错误/超时…，或两分钟内什么都没变。
- 封面成功：状态栏出现「保存 / saved」。
- 导出成功：状态栏出现「导出 / exported」。
- 取消（取消选择文件夹）单独算，算测试环境问题不算代码失败。

需要 uiautomation，用项目 venv 的 python 跑。
"""
import os
import re
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402  - 启动/查找/点击都走这里

EXE = "MarketMotionStudio.exe"
APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
NAV = "实时持仓收益"
LOG = r"D:\software\MarketMotionStudio\artifacts\drive-portfolio.txt"
CRASH = r"C:\Users\user\AppData\Local\Packages\8166Yxw.MarketMotionStudio_fzc58jprbah1t\LocalState\crash.log"

BAD = re.compile(r"失败|错误|无法|不可用|不属于|超时|过长|异常|failed|error|exception", re.I)
CANCEL = re.compile(r"取消|cancelled|cancel", re.I)

PRIVATE = re.compile(r"[\ue000-\uf8ff]")


def say(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")


def by_aid(aid):
    def cond(c):
        try:
            return c.AutomationId == aid
        except Exception:  # noqa: BLE001
            return False
    return cond


def text_of(win, aid):
    c = winui.find(win, by_aid(aid))
    try:
        return c.Name if c is not None else None
    except Exception:  # noqa: BLE001
        return None


def status_text(win):
    bar = winui.find(win, by_aid("Status"))
    if bar is None:
        return None
    nodes = []
    winui.find_all(bar, lambda c: c.ControlTypeName == "TextControl" and bool(getattr(c, "Name", None)), out=nodes)
    texts = [n.Name for n in nodes if n.Name and not PRIVATE.search(n.Name)]
    return max(texts, key=len) if texts else None


def click_aid(win, aid):
    c = winui.find(win, by_aid(aid))
    if c is None:
        return None
    ok = winui.invoke_click(c)
    return c if ok else None


def main():
    open(LOG, "w", encoding="utf-8").close()
    try:
        with open(CRASH, "rb") as f:
            offset = f.seek(0, os.SEEK_END)
    except Exception:
        offset = 0
    say("crash.log offset before run: %d" % offset)

    win = winui.launch(EXE, appid=APPID)
    assert win is not None, "应用窗口未找到"
    say("window: handle=%s" % win.NativeWindowHandle)

    # --- 切到持仓收益页 -------------------------------------------------------
    nav = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == NAV)
    if nav is None:
        say("NAV ITEM NOT FOUND: %s" % NAV)
        for it in winui.find_all(win, lambda c: c.ControlTypeName == "ListItemControl" and bool(getattr(c, "Name", None))):
            say("  nav item: %r" % getattr(it, "Name", None))
        raise SystemExit(1)
    winui.invoke_click(nav)
    say("navigated to %s" % NAV)
    time.sleep(2.5)

    # --- 抓取 -----------------------------------------------------------------
    before_summary = text_of(win, "SummaryText")
    before_updated = text_of(win, "UpdatedText")
    say("before fetch: summary=%r updated=%r" % (before_summary, before_updated))

    fb = click_aid(win, "FetchButton")
    if fb is None:
        say("FETCH BUTTON NOT FOUND / NOT CLICKED")
    else:
        say("clicked FetchButton")
        summary = status = None
        deadline = time.time() + 120
        while time.time() < deadline:
            time.sleep(2)
            s = text_of(win, "SummaryText")
            u = text_of(win, "UpdatedText")
            st = status_text(win)
            if (s and s != before_summary) or (u and u != before_updated):
                summary = s
                break
            if st and BAD.search(st):
                status = st
                break
        if summary is not None:
            say("FETCH OK: %s" % summary)
        else:
            say("FETCH RESULT: %s" % (status or "(no change within 120s)"))

    # --- 把视频时长拉到最短，导出更快 -----------------------------------------
    dur = winui.find(win, by_aid("DurationSlider"))
    if dur is not None:
        try:
            pat = dur.GetPattern(auto.PatternId.RangeValuePattern)
            pat.SetValue(pat.Minimum)
            say("duration set to minimum=%s" % pat.Minimum)
        except Exception as e:  # noqa: BLE001
            say("duration set failed: %r" % e)
    time.sleep(1)

    # --- 封面 -----------------------------------------------------------------
    cb = click_aid(win, "CoverButton")
    if cb is None:
        say("COVER BUTTON NOT FOUND / NOT CLICKED")
    else:
        say("clicked CoverButton")
        cover = None
        deadline = time.time() + 60
        while time.time() < deadline:
            time.sleep(2)
            st = status_text(win)
            if st:
                if "保存" in st or "saved" in st.lower():
                    cover = st
                    break
                if CANCEL.search(st):
                    cover = "(picker cancelled) " + st
                    break
                if BAD.search(st):
                    cover = st
                    break
        say("COVER: %s" % (cover or "(no status within 60s — possibly a folder picker)"))

    # --- 导出 -----------------------------------------------------------------
    eb = click_aid(win, "ExportButton")
    if eb is None:
        say("EXPORT BUTTON NOT FOUND / NOT CLICKED")
    else:
        say("clicked ExportButton")
        exp = None
        deadline = time.time() + 180
        while time.time() < deadline:
            time.sleep(3)
            st = status_text(win)
            if st:
                if "导出" in st or "exported" in st.lower():
                    exp = st
                    break
                if CANCEL.search(st):
                    exp = "(picker cancelled) " + st
                    break
                if BAD.search(st):
                    exp = st
                    break
        say("EXPORT: %s" % (exp or "(no status within 180s — possibly a folder picker)"))

    say("--- crash.log written during this run ---")
    try:
        with open(CRASH, "rb") as f:
            f.seek(offset)
            say(f.read().decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001
        say("(unreadable: %r)" % e)
    say("--- end ---")


if __name__ == "__main__":
    main()
