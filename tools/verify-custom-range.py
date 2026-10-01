# -*- coding: utf-8 -*-
"""真机验证定投页与持仓页的自定义区间。

这两个页面的区间原本只有 3 / 5 / 10 年和「最长」，加的两个日期框是折叠在
「自定义」后面的——截图证明不了选到它之后会不会冒出来，也证明不了那两个日期
真的喂给了取数：默认的自定义区间（近三年）和列表里的「近 3 年」是同一天，
光看「取数成功」分不出数据是哪个给的。

所以这里挑了两个**默认跨度不同**的页面来验：定投页默认近 5 年、持仓页默认
最长（约 13 年）。选到「自定义」后取一次数，回报的起始日必须落在日期框里那个
起始日附近——落在五年或十三年前就说明日期框是摆设。

日期本身不由 UIA 写入：WinUI 的 DatePicker 只把 FlyoutButton 和一整串日期文本
暴露出来，没有可设值的模式。能读不能写，正好够用——读出来的是默认值，而默认值
与列表里的任何一项都不同。

用法：python tools/verify-custom-range.py
"""
import os
import re
import sys
import time
from datetime import date, timedelta

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

FAIL = re.compile(r"失败|错误|无法|不可用|异常|不属于|过长|failed|error")
SPAN = re.compile(r"（(\d{4}-\d{2}-\d{2}) 至 (\d{4}-\d{2}-\d{2})）")
DATED = re.compile(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})")

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


def is_glyph(text):
    return all(ord(ch) >= 0xE000 for ch in text)


def status_text(win):
    """The page's own status bar, or None while it is closed.

    Picked by shape from the bar's text nodes — the longest one that is not the
    severity icon or the icon's own name — because taking the first returns a
    private-use glyph that renders as nothing and matches nothing.
    """
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return None

    parts = [
        t for t in texts(bar)
        if t != bar.Name and len(t) < 200 and not is_glyph(t) and "图标" not in t
    ]

    return max(parts, key=len) if parts else None


def close_status(win):
    """Dismisses the bar, so the next message is unambiguously a new one."""
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


def wait_status(win, seconds=120):
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(1.5)
        text = status_text(win)

        if text and (SPAN.search(text) or FAIL.search(text)):
            return text

    return None


# Combo pop-ups are driven from `winui` — the walk that finds a combo's rows also
# finds the navigation pane's, and telling them apart took two attempts to get
# right. See there.


def picker_date(win, automation_id):
    """The date a picker is showing, read from the one text node it exposes."""
    box = winui.find(win, lambda c: c.AutomationId == automation_id)

    if box is None:
        return None

    for part in texts(box):
        hit = DATED.search(part.replace("\u200e", ""))

        if hit:
            return date(int(hit.group(1)), int(hit.group(2)), int(hit.group(3)))

    return None


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

    if item is None:
        return False

    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)

    return True


def fetch_span(win):
    """Presses 获取数据 and returns the span the page says it fetched."""
    close_status(win)

    fetch = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if fetch is None:
        return None, "FetchButton 不见了"

    fetch.GetInvokePattern().Invoke()
    status = wait_status(win)

    if status is None:
        return None, status_text(win) or "（状态条空）"

    hit = SPAN.search(status)

    if hit is None:
        return None, status

    start = date.fromisoformat(hit.group(1))
    end = date.fromisoformat(hit.group(2))

    return (start, end), status


OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")


def shot(win, name):
    """The window, brought to the front first.

    The sibling project WorldMotionStudio is the same shell on the same desktop, and
    a capture taken while it overlaps the window is a picture of the wrong app.
    """
    path = os.path.join(OUT, name)

    try:
        win.SetTopmost(True)
        time.sleep(0.6)
    except Exception:  # noqa: BLE001
        pass

    win.CaptureToImage(path)

    try:
        win.SetTopmost(False)
    except Exception:  # noqa: BLE001
        pass

    return path


def at_page(win, name, wanted, other, picture=None):
    """Runs the whole custom-span story on one page. Returns the fetched span."""
    label = name

    if not goto(win, label):
        check(f"{label}：导航项在", False)
        return None

    combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
    check(f"{label}：区间下拉在", combo is not None)

    if combo is None:
        return None

    labels = winui.combo_labels(win, combo)
    check(f"{label}：区间含「自定义」", "自定义" in labels, " / ".join(labels))

    # Off 自定义 first: the page restores the span it was left on, so asserting
    # "the pickers are absent" without moving off it first is asserting on the
    # previous run's state.
    settled = winui.combo_pick(win, combo, other)
    check(f"{label}：能切回「{other}」", settled == other, str(settled))
    check(f"{label}：其他区间下没有日期框",
          winui.find(win, lambda c: c.AutomationId == "FromDate") is None)

    picked = winui.combo_pick(win, combo, "自定义")
    check(f"{label}：能选到「自定义」", picked == "自定义", str(picked))

    start = picker_date(win, "FromDate")
    end = picker_date(win, "ToDate")

    check(f"{label}：起始日期已填", start is not None, str(start))
    check(f"{label}：结束日期已填", end is not None, str(end))

    if start is None or end is None:
        return None

    # The default the pickers come up with: three years, so that choosing 自定义
    # for the first time asks for something rather than for today to today.
    check(f"{label}：默认起始日是三年前",
          abs((start - (date.today() - timedelta(days=3 * 365))).days) < 10,
          str(start))

    span, status = fetch_span(win)
    check(f"{label}：自定义区间取数成功", span is not None and not FAIL.search(status or ""),
          str(status))

    if span is None:
        return None

    got_start, got_end = span

    # The assertion that matters: the series begins at the date in the box, not at
    # what the page's own default span would have given. Seven days of slack covers
    # a start date landing on a weekend or inside a holiday week.
    check(f"{label}：取到的起点就是框里那个起始日",
          start - timedelta(days=1) <= got_start <= start + timedelta(days=10),
          f"框里 {start}，取到 {got_start}")

    check(f"{label}：取到的终点是今天附近",
          abs((got_end - date.today()).days) <= 10,
          f"框里 {end}，取到 {got_end}")

    # After the fetch, not before it: a picture of an empty preview proves the panel
    # appeared and nothing else.
    if picture:
        shot(win, picture)

    return got_start


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

    # The plan page opens on five years and the holding page on the longest span, so
    # a three-year result on either one can only have come from the two dates.
    at_page(win, "定投计划", "自定义", "近 5 年", "verify-custom-range-dca.png")
    at_page(win, "持仓收益", "自定义", "最长（约 13 年）", "verify-custom-range-position.png")

    # ---- 重启后还记得
    #
    # Before the regression below, which leaves the page on one of the counts: the
    # whole point of this check is that the span a person chose is the span that
    # comes back, and switching it first makes the check ask about a choice nobody
    # made. It did, and three checks failed on a page that remembered correctly.

    win = winui.launch(winui.EXE)

    if win is None:
        check("重启后窗口还在", False)
        return report()

    win.SetActive()
    time.sleep(1.0)

    try:
        win.GetWindowPattern().SetWindowVisualState(auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass

    if goto(win, "定投计划"):
        combo = winui.find(win, lambda c: c.AutomationId == "RangeCombo")
        check("重启后区间仍是「自定义」",
              combo is not None and winui.value(combo) == "自定义",
              str(winui.value(combo) if combo else None))

        box = winui.find(win, lambda c: c.AutomationId == "FromDate")
        check("重启后日期框直接是展开的", box is not None and not box.IsOffscreen)
        check("重启后起始日期还在", picker_date(win, "FromDate") is not None,
              str(picker_date(win, "FromDate")))

        # ---- 预设区间照旧
        #
        # The two ways of asking share one walk, so a custom span that works proves
        # nothing about the counts until one of them is fetched again. Five years is
        # two years further back than the custom default — far enough apart to tell
        # the two answers apart.
        if combo is not None and winui.combo_pick(win, combo, "近 5 年") == "近 5 年":
            check("切回预设后日期框收起",
                  winui.find(win, lambda c: c.AutomationId == "FromDate") is None)

            span, status = fetch_span(win)
            check("切回「近 5 年」后取数仍成功", span is not None, str(status))

            if span is not None:
                check("预设区间取到的起点约在五年前",
                      abs((span[0] - (date.today() - timedelta(days=5 * 365))).days) < 20,
                      str(span[0]))

    return report()


def report():
    failed = [name for name, ok, _ in CHECKS if not ok]

    print()
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} 通过")

    if failed:
        print("未通过：" + "；".join(failed))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
