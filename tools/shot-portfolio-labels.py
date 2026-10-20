#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""持仓收益页「买入 / 卖出点」文字标签截图：把流水重戳成今天，进页、拖到刚过 09:35–09:40
成交的那一帧，让红/绿两种标签都还浮在曲线上，抓全窗口。

仅用于给开发者看效果，不改任何代码。portfolio.json 的原样还原由脚本自己负责（finally）。

- 锁屏：窗口缩到 1720x1000，使 shot() 的尺寸校验能区分锁屏（1920x1080）。
- 只在会话已解锁时才能抓到；否则 shot() 返回 False，脚本如实报 grabbed lock screen。
"""

import ctypes
import ctypes.wintypes
import json
import os
import re
import sys
import threading
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

PAGE = "实时持仓收益"
DETAIL = re.compile(r"^(?:[\d,]+\s*股\s*·\s*成本\s*[¥HK$]|已清仓)")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")
CLOCK = re.compile(r"^\d{2}:\d{2}$")

PKG = "8166Yxw.MarketMotionStudio_fzc58jprbah1t"
JSON = os.path.join(
    os.environ.get("LOCALAPPDATA", "C:/Users/user/AppData/Local"),
    "Packages", PKG, "LocalState", "portfolio.json")
TODAY = "2026-10-20"  # 与 App 的 DateTime.Today 对齐，Assemble 只收同一天的流水


def keep_alive(stop):
    u = ctypes.windll.user32
    while not stop.is_set():
        try:
            pt = ctypes.wintypes.POINT()
            u.GetCursorPos(ctypes.byref(pt))
            u.SetCursorPos(pt.x + 1, pt.y)
            u.SetCursorPos(pt.x, pt.y)
        except Exception:  # noqa: BLE001
            pass
        stop.wait(12)


def texts(win):
    return [c.Name for c in winui.find_all(win, lambda c: c.Name, limit=60) if c.Name]


def status(win):
    for n in texts(win):
        if "收益" in n and "分钟点" in n:
            return n
    return None


def clock_now(win):
    for n in texts(win):
        if CLOCK.match(n):
            return n
    return None


def to_minute(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)
    if item is None:
        return False
    for _ in range(6):
        try:
            item.GetScrollItemPattern().ScrollIntoView()
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.5)
        if item.BoundingRectangle.width() > 0:
            break
    for _ in range(4):
        try:
            item.GetSelectionItemPattern().Select()
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2.5)
        try:
            if item.GetSelectionItemPattern().IsSelected:
                return True
        except Exception:  # noqa: BLE001
            pass
    return False


def resize(win, w=1720, h=1000):
    try:
        hwnd = win.NativeWindowHandle
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 80, 40, w, h, 0x0004)
        time.sleep(1.0)
    except Exception:  # noqa: BLE001
        pass


def restamp(json_path):
    with open(json_path, encoding="utf-8") as fh:
        data = json.load(fh)
    n = 0
    for t in data.get("Trades", []):
        if t.get("Day") != TODAY:
            t["Day"] = TODAY
            n += 1
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return n


def main():
    stop = threading.Event()
    threading.Thread(target=keep_alive, args=(stop,), daemon=True).start()

    stamp = restamp(JSON)
    print("restamped", stamp, "trades ->", TODAY)

    try:
        winui.kill(winui.EXE)
        win = winui.launch(winui.EXE)
        if win is None:
            stop.set()
            print("起不来")
            return 1

        time.sleep(2)
        resize(win)

        if not goto(win, PAGE):
            stop.set()
            print("进不了页")
            return 1

        for _ in range(60):
            if status(win):
                break
            time.sleep(2)

        # 费率框恢复 A 股默认口径，覆盖探针遗留的 0。
        for name, value in (("FeeCommission", "2.5"), ("FeeMinimum", "5"),
                            ("FeeStamp", "5"), ("FeeTransfer", "0.1")):
            box = winui.find(win, lambda c: c.AutomationId == name)
            if box is None:
                continue
            inner = winui.find(box, lambda c: c.ControlTypeName == "EditControl")
            target = inner if inner is not None else box
            try:
                target.GetValuePattern().SetValue(value)
                target.SetFocus()
                auto.SendKeys("{Tab}")
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.4)

        time.sleep(2)

        # 时钟画在视频画布上，UIA 读不到；持仓列表又因账本换过而不作数。于是按动画节奏直接
        # 算：60s 视频、Intro 2400ms、FinaleStart 54000ms，ramped=(t-2400)/51600，
        # shown=floor(ramped*(N-1))。前 10 分钟是 samples[0..]，samples[i].Minute=570+i。
        # minute 584 处刚过 09:35/09:36/09:40 三笔卖出，标签还亮着（买入稍淡）。
        # 多抓几帧备选，再挑最好的那张。
        scrub = winui.find(win, lambda c: c.AutomationId == "Scrub")
        os.makedirs(OUT, exist_ok=True)
        picks = []
        if scrub is not None:
            for v in (0.575, 0.588, 0.600, 0.615):
                try:
                    scrub.GetRangeValuePattern().SetValue(v)
                except Exception:  # noqa: BLE001
                    pass
                time.sleep(1.0)
                path = os.path.join(OUT, "probe-portfolio-labels-%.3f.png" % v)
                ok = winui.shot(win, path)
                picks.append((v, path, ok))
                print("v=%.3f -> %s %s" % (v, os.path.basename(path),
                                           "(verified)" if ok else "(锁屏/尺寸不符)"))
        else:
            print("没找到 scrub 控件")

        print("状态:", status(win))
        for line in texts(win):
            if DETAIL.match(line):
                print("  ", line)

        path = os.path.join(OUT, "probe-portfolio-labels.png")
        ok = winui.shot(win, path)
        print("saved:", path, "(verified)" if ok else "(WARNING: 抓到锁屏/尺寸不符)")

        stop.set()
        winui.kill(winui.EXE)
        return 0 if ok else 2
    finally:
        # 无论如何还原账本原样（流水日戳回到 2026-10-19）。
        try:
            with open(JSON, encoding="utf-8") as fh:
                data = json.load(fh)
            changed = False
            for t in data.get("Trades", []):
                if t.get("Day") == TODAY:
                    t["Day"] = "2026-10-19"
                    changed = True
            if changed:
                with open(JSON, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, ensure_ascii=False, indent=2)
                print("restored journal -> 2026-10-19")
        except Exception as exc:  # noqa: BLE001
            print("还原失败:", exc)


if __name__ == "__main__":
    raise SystemExit(main())
