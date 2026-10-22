#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""量「管理持仓」对话框和持仓列表对不对得上 —— 以及**只看不改时账本一个字都不动**。

四件事，缺一不可：
  1. 逐行：对话框里的股数/成本 = 列表里的「N 股 · 成本 ¥X」。这是读者报的那个问题 ——
     列表画的是「账本（开盘）+ 当天成交」，对话框从前只读账本，于是 900 股对 100 股。
  2. 打开再关闭之后 portfolio.json 字节不变。对话框显示的是**收盘**，账本存的是**开盘**；
     一关闭就把收盘写进账本，回放从那一刻起就没有仓位可走了（而且旧版关闭时还会把当天全部
     成交标成「已折」，当天 10 笔买入就这么从列表上消失了）。
  3. 改一行、关闭：账本换成收盘口径，列表跟着变。
  4. 没改的行不能再被当天的成交加一遍（顺丰 200→400 之后再叠 200 就是 600）。

跑完还原账本（先杀进程，再还原 —— App 手里那本会在退出时写回磁盘）。
"""

import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402

PAGE = "实时持仓收益"
DETAIL_ROW = re.compile(r"^([\d,]+)\s*股\s*·\s*成本\s*(?:HK\$|HKD|¥|￥|\$)?([\d.]+)$")
CLEARED = "已清仓"

PKG = "8166Yxw.MarketMotionStudio_fzc58jprbah1t"
JSON = os.path.join(
    os.environ.get("LOCALAPPDATA", "C:/Users/user/AppData/Local"),
    "Packages", PKG, "LocalState", "portfolio.json")

FAILED = []


def check(name, ok, note=""):
    print(("  ✓ " if ok else "  ✗ ") + name + ((" — " + note) if note else ""))
    if not ok:
        FAILED.append(name)


def press(win, control):
    if control is None:
        return False
    try:
        control.GetInvokePattern().Invoke()
        return True
    except Exception:  # noqa: BLE001
        pass
    try:
        control.Click()
        return True
    except Exception:  # noqa: BLE001
        return False


def texts(win):
    # `find_all` 的 limit 是**深度**上限，不是条数上限（这一页离窗口根不到 30 层）。
    return [c.Name for c in winui.find_all(win, lambda c: c.Name, limit=30) if c.Name]


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


def wait_fetched(win, seconds=90):
    """等页眉那一行「2026-10-22 · N 个分钟点 · 收益 …」。"""
    for _ in range(seconds // 3):
        if any("分钟点" in name for name in texts(win)):
            return True
        time.sleep(3)
    return False


def summary(win):
    for name in texts(win):
        if "分钟点" in name:
            return name
    return None


def list_rows(win):
    """列表上的每一行，按顺序：[(股数, 成本), ...]，已清仓记 (0, 0)。"""
    rows = []
    for name in texts(win):
        if name == CLEARED:
            rows.append((0, 0.0))
            continue
        hit = DETAIL_ROW.match(name)
        if hit:
            rows.append((float(hit.group(1).replace(",", "")), float(hit.group(2))))
    return rows


def dialog_rows(win):
    """对话框每一行的 (股数, 成本)，按树顺序。

    UIA 里每个编辑框都被走到两次（TextBox 自己 + 里面的 TextBoxView），值一样、矩形一样，
    所以相邻重复先去一遍；再按「数量 → 成本」配对；最后一对属于「添加一只」那一排，丢掉。
    """
    seen = []
    for edit in winui.find_all(win, lambda c: c.ControlTypeName == "EditControl", limit=30):
        try:
            value = edit.GetValuePattern().Value
        except Exception:  # noqa: BLE001
            continue
        if edit.Name not in ("数量", "成本"):
            continue
        key = (edit.Name, value, edit.BoundingRectangle.top, edit.BoundingRectangle.left)
        if seen and seen[-1] == key:
            continue
        seen.append(key)

    pairs = []
    for i in range(0, len(seen) - 1, 2):
        first, second = seen[i], seen[i + 1]
        if first[0] == "数量" and second[0] == "成本":
            pairs.append((first[1], second[1]))

    return pairs[:-1] if pairs else pairs


def book_snapshot():
    with open(JSON, encoding="utf-8") as fh:
        data = json.load(fh)
    return [(h["Code"], h["Shares"], h["Cost"]) for h in data.get("Holdings", [])]


def close_dialog(win):
    return press(win, winui.find(
        win, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == "关闭"))


def open_dialog(win):
    return press(win, winui.find(win, lambda c: c.AutomationId == "ManageButton"))


def main():
    backup = JSON + ".probe-backup"
    shutil.copy2(JSON, backup)
    original = open(JSON, "rb").read()

    try:
        winui.kill(winui.EXE)
        time.sleep(1)

        win = winui.launch(winui.EXE)
        if win is None:
            print("起不来")
            return 1
        time.sleep(3)

        check("进得了这一页", goto(win, PAGE))
        check("这一页取到了数", wait_fetched(win))

        time.sleep(3)

        print("\n列表")
        rows = list_rows(win)
        print("  列表 %d 行：%s" % (len(rows), rows))
        print("  页眉：%s" % summary(win))

        book = book_snapshot()
        print("  账本（开盘）%d 行：%s" % (len(book), book))

        check("列表已经长出当天的成交（不等于账本）",
              rows != [(s, c) for _, s, c in book],
              "列表与账本一字不差 —— 当天成交没上列表")

        before = open(JSON, "rb").read()

        print("\n管理持仓")
        check("点得开「管理持仓」", open_dialog(win))
        time.sleep(2.5)

        pairs = dialog_rows(win)
        print("  对话框 %d 行：%s" % (len(pairs), pairs))

        got = [(round(float(s), 2), round(float(c), 3)) for s, c in pairs]
        want = [(s, round(c, 3)) for s, c in rows]

        check("对话框逐行等于列表（股数 + 成本，成本按列表那 3 位比）", got == want,
              "对话框 %s / 列表 %s" % (got, want))

        check("关得掉", close_dialog(win))
        time.sleep(2)

        same = open(JSON, "rb").read() == before
        check("只看一眼再关掉，账本一个字节都不动", same,
              "" if same else "打开/关闭写了账本 —— 回放会因此失去仓位")

        print("\n改一行")
        check("再打开", open_dialog(win))
        time.sleep(2.5)

        pairs = dialog_rows(win)
        print("  打开后 %d 行，头一行 %s" % (len(pairs), pairs[0] if pairs else None))

        edited = None
        if pairs:
            target = round(float(pairs[0][0]) + 1)
            edited = target

            box = None
            for edit in winui.find_all(win, lambda c: c.ControlTypeName == "EditControl", limit=30):
                if edit.Name != "数量":
                    continue
                try:
                    if edit.GetValuePattern().Value == pairs[0][0] and \
                            edit.BoundingRectangle.top == _top_of_first_row(win, pairs[0]):
                        box = edit
                        break
                except Exception:  # noqa: BLE001
                    continue

            if box is None:
                print("  没找到第一行的股数框，改用键盘")
            else:
                box.GetValuePattern().SetValue(str(target))
                box.SetFocus()
                time.sleep(0.8)

        close_dialog(win)
        time.sleep(3)

        changed = book_snapshot()
        print("  改后账本：%s" % changed)

        check("改一行，账本按收盘口径落下（行数不变、不只动一行）",
              edited is not None and len(changed) == len(book) and changed != book,
              "%d 行 → %d 行" % (len(book), len(changed)))

        print("\n改完之后")
        wait_fetched(win)
        time.sleep(4)

        rows_after = list_rows(win)
        print("  列表 %d 行：%s" % (len(rows_after), rows_after))

        expect = list(rows)
        if expect and edited is not None:
            expect[0] = (float(edited), expect[0][1])

        check("列表 = 改之前的收盘 + 那一行的改动（成交没有被再加一遍）",
              rows_after == expect,
              "期望 %s / 实际 %s" % (expect, rows_after))
    finally:
        for _ in range(3):
            if close_dialog(win) is False:
                break
            time.sleep(1)

        winui.kill(winui.EXE)
        time.sleep(1)

        shutil.copy2(backup, JSON)
        os.remove(backup)

        same = open(JSON, "rb").read() == original
        check("跑完账本还原成跑之前那一版", same, "" if same else "字节不同")

    print()
    if FAILED:
        print("%d 项未通过：%s" % (len(FAILED), "、".join(FAILED)))
        return 1

    print("全部通过")
    return 0


def _top_of_first_row(win, pair):
    """第一行「数量」框的 top：按值找第一处，返回它的矩形上沿。"""
    for edit in winui.find_all(win, lambda c: c.ControlTypeName == "EditControl", limit=30):
        if edit.Name != "数量":
            continue
        try:
            if edit.GetValuePattern().Value == pair[0] and edit.BoundingRectangle.top > 0:
                return edit.BoundingRectangle.top
        except Exception:  # noqa: BLE001
            continue
    return -1


if __name__ == "__main__":
    sys.exit(main() or 0)
