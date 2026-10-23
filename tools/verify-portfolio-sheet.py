#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""量「管理持仓」的列表导入/导出，以及检索建议里那串记录转储。

五件事：

  1. **建议列表写的是名字，不是 `StockChoice { Stock = … }`。** 读者看到的「乱码」就是
     这条：`AutoSuggestBox` 的列表走 `ToString`，而 record 的 `ToString` 是字段转储。
  2. **导出文件是规范的 CSV**：UTF-8 带 BOM（Excel 双击不乱码）、固定表头
     `code,name,shares,cost`、CRLF、行数与对话框一致、数值逐行相同。
  3. **坏文件什么都不改**，并把行号和理由说出来（列数 / 代码 / 数量 / 成本 / 重复）。
  4. **好文件整表替换**：对话框的行立刻变成文件里的行。
  5. **关闭之后页面列表刷新**，账本也换成文件里的那些行 —— 这是「操作后列表数据需正确刷新」。

跑完还原账本（先杀进程再还原：应用手里那本会在退出时写回磁盘）。
"""

import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import winui  # noqa: E402
import importlib  # noqa: E402

dlg = importlib.import_module("verify-portfolio-dialog")

TMP = os.path.join(os.environ.get("TEMP", "C:/Users/user/AppData/Local/Temp"), "holdings-sheet")
FAILED = []
TOTAL = [0]


def check(name, ok, note=""):
    TOTAL[0] += 1
    print(("  ✓ " if ok else "  ✗ ") + name + ((" — " + note) if note else ""))
    if not ok:
        FAILED.append(name)


def picker(win, seconds=12):
    for _ in range(seconds * 4):
        box = next((c for c in winui.find_all(win, lambda c: c.ClassName == "#32770", limit=8)), None)
        if box is not None:
            return box
        time.sleep(0.25)
    return None


def pick(win, path, button="1"):
    """把路径填进文件对话框并按下保存/打开（都是 `1001` 与 `1`）。"""
    box = picker(win)

    if box is None:
        return False

    # 两个对话框的文件名框不是同一个 id：「另存为」是 `1001`，「打开」是 `1148`。
    edit = winui.find(
        box,
        lambda c: c.ControlTypeName == "EditControl" and c.AutomationId in ("1001", "1148"))

    target = winui.find(box, lambda c: c.ControlTypeName == "ButtonControl" and c.AutomationId == button)

    if edit is None:
        return False

    edit.GetValuePattern().SetValue(path)
    time.sleep(0.6)

    if target is not None:
        target.GetInvokePattern().Invoke()
    else:
        # 主按钮没露出来时，回车是同一个动作。
        edit.SendKeys("{Enter}")

    time.sleep(2.5)

    # 对话框还开着就说明没提交（路径被当成新名字之类）。
    return picker(win, seconds=2) is None


def say(win):
    """对话框底下那行说明（`Message` 的 Name 就是它的文字）。"""
    for control in winui.find_all(win, lambda c: c.AutomationId == "Message", limit=12):
        if control.Name:
            return control.Name

    return ""


def suggestions(win, text):
    """在代码框里打一串字，读回建议列表里的名字。"""
    box = None

    for edit in winui.find_all(win, lambda c: c.ControlTypeName == "EditControl", limit=40):
        r = edit.BoundingRectangle
        if "代码" in (edit.Name or "") and r.left > 0 and r.top > 0:
            box = edit
            break

    if box is None:
        return []

    box.GetValuePattern().SetValue(text)
    time.sleep(3)

    names = [c.Name for c in winui.find_all(win, lambda c: c.ControlTypeName == "ListItemControl", limit=12)
             if c.Name]

    # UIA 里整棵建议列表会被走两遍。
    return list(dict.fromkeys(names))


def write(path, rows, encoding="utf-8-sig", header="code,name,shares,cost"):
    with open(path, "w", encoding=encoding, newline="") as handle:
        handle.write("\r\n".join([header] + rows) + "\r\n")


def main():
    if not os.path.isdir(TMP):
        os.makedirs(TMP)

    good = os.path.join(TMP, "good.csv")
    bad = os.path.join(TMP, "bad.csv")
    exported = os.path.join(TMP, "exported.csv")

    for path in (good, bad, exported):
        if os.path.exists(path):
            os.remove(path)

    write(good, [
        "sz002352,顺丰控股,100,29.948",
        "sh600519,贵州茅台,5,1500.5",
        "hk00700,腾讯控股,200,300.25",
    ])

    write(bad, [
        "600519,贵州茅台",            # 2: 列数
        "abc,坏代码,100,1.0",         # 3: 代码
        "601398,工商银行,0,5.2",      # 4: 数量
        "601398,工商银行,100,abc",    # 5: 成本
    ])

    backup = dlg.JSON + ".sheet-backup"
    shutil.copy2(dlg.JSON, backup)

    try:
        winui.kill(winui.EXE)
        time.sleep(1.5)

        win = winui.launch(winui.EXE)

        if win is None:
            print("起不来")
            return 1

        time.sleep(3)

        check("进得了这一页", dlg.goto(win, dlg.PAGE))
        check("这一页取到了数", dlg.wait_fetched(win))
        time.sleep(2)

        page_rows = dlg.list_rows(win)
        print("  页面上 %d 行：%s" % (len(page_rows), page_rows[:4]))

        check("点得开「管理持仓」", dlg.open_dialog(win))
        time.sleep(2.5)

        print("\n检索建议")
        items = suggestions(win, "顺丰")
        print("  建议：%s" % items[:4])

        check("建议列表写的是「名字 · 代码」",
              any("顺丰控股 · SZ002352" in name for name in items),
              repr(items[:4]))
        check("建议列表里没有 record 转储（StockChoice { … }）",
              not any("StockChoice" in name or "StockRef" in name for name in items),
              repr([n for n in items if "StockChoice" in n or "StockRef" in n][:2]))

        # 清掉刚才那串字，免得上一条建议影响后面的行数。
        for edit in winui.find_all(win, lambda c: c.ControlTypeName == "EditControl", limit=40):
            r = edit.BoundingRectangle
            if "代码" in (edit.Name or "") and r.left > 0 and r.top > 0:
                edit.GetValuePattern().SetValue("")
                break

        time.sleep(0.8)

        print("\n导出")
        rows = dlg.dialog_rows(win)
        print("  对话框 %d 行：%s" % (len(rows), rows[:4]))

        buttons = {c.AutomationId: c.Name
                   for c in winui.find_all(win, lambda c: c.ControlTypeName == "ButtonControl", limit=40)}

        check("两枚按钮都在（导入列表 / 导出列表）",
              buttons.get("SheetImportButton") == "导入列表" and buttons.get("SheetExportButton") == "导出列表",
              "%r / %r" % (buttons.get("SheetImportButton"), buttons.get("SheetExportButton")))

        check("导出选择器打开了", dlg.press(win, winui.find(win, lambda c: c.AutomationId == "SheetExportButton")))
        check("选了个路径并保存", pick(win, exported))

        if os.path.exists(exported):
            raw = open(exported, "rb").read()
            text = raw.decode("utf-8-sig")
            lines = text.replace("\r\n", "\n").strip("\n").split("\n")

            print("  文件 %d 行，开头 %r" % (len(lines), lines[0]))

            check("文件以 UTF-8 BOM 开头（Excel 双击不乱码）", raw.startswith(b"\xef\xbb\xbf"))
            check("表头是 code,name,shares,cost", lines[0] == "code,name,shares,cost", lines[0])
            # 最后一行后面没有换行（Write 只在每行前面缀 CRLF），所以是「行数 − 1」。
            check("换行是 CRLF（没有裸 LF）",
                  raw.count(b"\r\n") == len(lines) - 1
                  and raw.replace(b"\r\n", b"").count(b"\n") == 0,
                  "%d 个 CRLF / %d 行 / 裸 LF %d"
                  % (raw.count(b"\r\n"), len(lines), raw.replace(b"\r\n", b"").count(b"\n")))
            check("行数 = 对话框行数 + 表头", len(lines) - 1 == len(rows), "%d vs %d" % (len(lines) - 1, len(rows)))

            parsed = []
            for line in lines[1:]:
                parts = line.split(",")
                parsed.append((float(parts[2]), float(parts[3])))

            # 对话框那一侧是输入框里的**文本**，按数值比。
            want = [(float(shares), float(cost)) for shares, cost in rows]

            same = len(parsed) == len(want) and all(
                abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-4 for a, b in zip(parsed, want))

            check("逐行数值与对话框一致", same, "%s vs %s" % (parsed[:3], want[:3]))
        else:
            check("文件写出来了", False, exported)

        print("\n导入一个坏文件")

        before = dlg.dialog_rows(win)
        check("导入选择器打开了", dlg.press(win, winui.find(win, lambda c: c.AutomationId == "SheetImportButton")))
        check("选了个坏文件并打开", pick(win, bad))
        time.sleep(1.5)

        message = say(win)
        print("  说明：%r" % message)

        check("说出了行号与理由", "第 2 行" in message and "列数" in message, message)
        check("坏文件一行都没进列表", dlg.dialog_rows(win) == before,
              "%d → %d 行" % (len(before), len(dlg.dialog_rows(win))))

        print("\n导入一个好文件")

        check("再打开选择器", dlg.press(win, winui.find(win, lambda c: c.AutomationId == "SheetImportButton")))
        check("选了个好文件并打开", pick(win, good))
        time.sleep(1.5)

        message = say(win)
        print("  说明：%r" % message)
        print("  列表：%s" % dlg.dialog_rows(win))

        check("说清导入了 3 行", "已导入 3 行" in message, message)
        after = [(float(shares), float(cost)) for shares, cost in dlg.dialog_rows(win)]

        check("对话框的行换成了文件里的三行",
              after == [(100.0, 29.948), (5.0, 1500.5), (200.0, 300.25)],
              str(after))

        print("\n关闭之后")
        check("关得掉", dlg.close_dialog(win))
        time.sleep(4)

        refreshed = dlg.list_rows(win)
        print("  页面 %d 行：%s" % (len(refreshed), refreshed))

        check("页面列表跟着刷新成文件里的三行",
              [(round(s, 4), round(c, 4)) for s, c in refreshed]
              == [(100.0, 29.948), (5.0, 1500.5), (200.0, 300.25)],
              str(refreshed))

        book = dlg.book_snapshot()
        print("  账本：%s" % book)

        check("账本也换成了文件里的三行",
              sorted(code for code, _, _ in book) == sorted(["sz002352", "sh600519", "hk00700"]),
              str(book))
        landed = {code: (round(shares, 4), round(cost, 4)) for code, shares, cost in book}

        check("股数与成本按文件落下",
              landed.get("sz002352") == (100.0, 29.948)
              and landed.get("sh600519") == (5.0, 1500.5)
              and landed.get("hk00700") == (200.0, 300.25),
              str(landed))

        print("\n%d 项通过 / %d 项失败（共 %d 项）" % (TOTAL[0] - len(FAILED), len(FAILED), TOTAL[0]))
        return 0 if not FAILED else 1
    finally:
        winui.kill(winui.EXE)
        time.sleep(1.5)
        shutil.copy2(backup, dlg.JSON)
        os.remove(backup)
        print("账本已还原")


if __name__ == "__main__":
    sys.exit(main())
