# -*- coding: utf-8 -*-
"""真机验证 K 线页的两件事：自定义数据区间，和上边距滑块的下限。

两件都是「界面里看不见的东西」——一个是折叠面板，一个是滑块量程的下半段——
截图只能证明当前这一屏长什么样，证明不了选到「自定义」之后会不会冒出两个日期框，
也证明不了 40 真的落进了 Minimum 而不是落在代码里没人用。

日期本身不由 UIA 驱动：WinUI 的 DatePicker 只把 FlyoutButton 和三个数字文本块
暴露出来，没有可设值的模式（见 tools/ 里已删掉的 probe-datepicker.py 的结论）。
所以这里验证的是「面板出现 + 默认区间取得回数据」，越界与倒序的拒绝由
CandleLoader 自己判定，另有离线用例覆盖。

用法：python tools/verify-candle-range.py
"""
import os
import re
import sys
import time

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

FAIL = re.compile(r"失败|错误|无法|不可用|异常|不属于|过长|failed|error")

CHECKS = []


def check(name, ok, note=""):
    CHECKS.append((name, ok, note))
    print(f"{'✓' if ok else '✗'} {name}" + (f" — {note}" if note else ""))


def texts(root, depth=0, limit=25, out=None):
    out = [] if out is None else out

    if root is None or depth > limit:
        return out

    try:
        if root.Name:
            out.append(root.Name)
    except Exception:  # noqa: BLE001
        pass

    try:
        for child in root.GetChildren():
            texts(child, depth + 1, limit, out)
    except Exception:  # noqa: BLE001
        pass

    return out


def status_text(win):
    """What the page's own status bar is saying, or None while it is closed.

    Read from the bar itself rather than by diffing the window's text before and
    after: fetching the same span twice produces the same sentence, and a diff
    reports the second fetch as having produced nothing at all. It reported a
    working fetch as a failure for exactly that reason.
    """
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return None

    # The bar's text nodes are the severity icon, the icon's own accessible name,
    # and the message. Taking the first one returns a private-use glyph, which
    # renders as nothing and matches nothing — so the message is picked by shape:
    # the longest node that is not the icon or its description.
    parts = [
        t for t in texts(bar)
        if t != bar.Name and len(t) < 200 and not is_glyph(t) and "图标" not in t
    ]

    return max(parts, key=len) if parts else None


def is_glyph(text):
    """Whether a string is a Segoe Fluent icon character rather than words."""
    return all(ord(ch) >= 0xE000 for ch in text)


def close_status(win):
    """Dismisses the status bar, so the next message is unambiguously a new one.

    Two ranges of the same length produce the same sentence — "241 根日K（... 至 ...）"
    for both — so waiting for the message to *change* waits forever when the second
    fetch succeeds with the same numbers as the first. It did exactly that: a
    working custom-range fetch was reported as a failure twice.
    """
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return

    closer = winui.find(
        bar, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "关闭")

    if closer is not None:
        try:
            closer.GetInvokePattern().Invoke()
            time.sleep(0.8)
        except Exception:  # noqa: BLE001
            pass


def wait_status(win, seconds=90):
    """The status bar's message, once there is one."""
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(1.5)
        text = status_text(win)

        if text and ("根" in text or FAIL.search(text)):
            return text

    return None


def open_popup_items(win):
    """The items of whatever combo is open, which live in the root window's popup.

    Filtered by process, not just by control type: a combo's popup is a separate
    top-level window, and the desktop has other applications on it whose own list
    rows answer to the same walk. Without the filter this returns the items of
    whatever else happens to be open — it once returned another app's menus, and
    a name test against that is a name test against nothing.
    """
    found = []

    for top in auto.GetRootControl().GetChildren():
        if top.ProcessId != win.ProcessId:
            continue

        found += winui.find_all(
            top,
            lambda c: c.ControlTypeName == "ListItemControl" and c.Name)

    return found


def combo_pick(win, combo, index, name=None):
    """Opens a combo by its own control and picks the item at `index`."""
    combo.GetExpandCollapsePattern().Expand()
    time.sleep(1.0)

    items = open_popup_items(win)

    if name is not None:
        items = [i for i in items if i.Name == name]

    if not items:
        combo.GetExpandCollapsePattern().Collapse()
        return None

    picked = items[index]
    picked.GetSelectionItemPattern().Select()
    time.sleep(1.2)

    return picked.Name


def main():
    win = winui.app_window(winui.EXE, wait_seconds=20)

    if win is None:
        print("no studio window")
        return 1

    win.SetActive()
    time.sleep(1.0)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass

    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "K线")

    if item is None:
        print("no K线 nav item")
        return 1

    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)

    # ---- 1. 区间下拉里有「自定义」

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    check("RangeCombo 在", combo is not None)

    if combo is None:
        return report()

    combo.GetExpandCollapsePattern().Expand()
    time.sleep(1.0)
    labels = [i.Name for i in open_popup_items(win)]
    combo.GetExpandCollapsePattern().Collapse()
    time.sleep(0.8)

    check("区间下拉含「自定义」", "自定义" in labels, " / ".join(labels))

    # ---- 2. 日期框跟着区间出现和消失
    #
    # A collapsed panel's children are not in the tree at all, so "absent" is what
    # "hidden" looks like from here. The page restores whatever span it was left on,
    # so the check starts by moving off 自定义: asserting on the state it happens to
    # open in is asserting on the previous run.

    settled = combo_pick(win, combo, 0, name="近 12 个月")
    check("切回「近 12 个月」", settled == "近 12 个月", str(settled))

    from_box = winui.find(win, lambda c: c.AutomationId == "FromDate")
    check("非自定义区间下没有日期框", from_box is None, f"FromDate={'有' if from_box else '无'}")

    picked = combo_pick(win, combo, 0, name="自定义")
    check("选到「自定义」", picked == "自定义", str(picked))

    from_box = winui.find(win, lambda c: c.AutomationId == "FromDate")
    to_box = winui.find(win, lambda c: c.AutomationId == "ToDate")

    shown = bool(from_box) and bool(to_box) and not from_box.IsOffscreen and not to_box.IsOffscreen
    check("两个日期框露出来了", shown,
          f"FromDate offscreen={from_box.IsOffscreen if from_box else '?'} "
          f"ToDate offscreen={to_box.IsOffscreen if to_box else '?'}")

    # The DatePicker's whole day is one text node, "‎2025‎年‎10月‎1‎日" — there are no
    # separate fields to read, so the shape of that string is the assertion.
    for label, box in (("起始", from_box), ("结束", to_box)):
        if box is None:
            continue

        parts = texts(box)
        dated = next((p for p in parts if "年" in p and "日" in p), None)

        check(f"{label}日期已填", dated is not None, dated or " ".join(parts[:4]))

    # ---- 3. 用默认区间取一次数

    close_status(win)
    fetch = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if fetch is not None:
        fetch.GetInvokePattern().Invoke()
        status = wait_status(win)

        if status is None:
            print("   状态条现在是:", status_text(win))

        check("自定义区间取数成功",
              bool(status) and not FAIL.search(status), str(status))
    else:
        check("自定义区间取数成功", False, "FetchButton 不见了")

    # ---- 4. 上边距滑块：默认 230、下限 40

    slider = winui.find(win, lambda c: c.AutomationId == "MarginTopSlider")

    if slider is None:
        # 视频设置面板在右栏折叠着，展开它
        expander = winui.find(win, lambda c: c.AutomationId == "VideoSettings")

        if expander is not None:
            try:
                expander.GetExpandCollapsePattern().Expand()
                time.sleep(1.2)
            except Exception:  # noqa: BLE001
                pass

        slider = winui.find(win, lambda c: c.AutomationId == "MarginTopSlider")

    check("MarginTopSlider 在", slider is not None)

    if slider is not None:
        rng = slider.GetRangeValuePattern()
        check("上边距下限是 40", int(rng.Minimum) == 40, f"min={rng.Minimum} max={rng.Maximum}")
        check("上边距默认落在 230", int(rng.Value) == 230, f"value={rng.Value}")

        # 把滑块拉到下限，确认它真的动得了（旧写法下限也是 230，拉不动）
        rng.SetValue(40)
        time.sleep(1.0)
        check("上边距能拉到 40", int(slider.GetRangeValuePattern().Value) == 40,
              f"value={slider.GetRangeValuePattern().Value}")

        slider.GetRangeValuePattern().SetValue(230)
        time.sleep(0.8)

    return report()


def report():
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print()
    print(f"{passed}/{len(CHECKS)} 通过")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
