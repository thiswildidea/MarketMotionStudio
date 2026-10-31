# -*- coding: utf-8 -*-
"""两本账的基准行为：A股 静态可选，港股通 锁定最后交易日、随动画收盘更新。

读的是运行中的应用和落盘的账本文件，不是代码：

* A股：ledger-baseline-ashare.json 不因动画改变，对话框日期可选。
* 港股通：播放到最后一帧后 ledger-baseline.json 变成会话日的收盘持仓
  （含港股、摊薄成本），管理持仓对话框的日期选择器不可改。
* 两种模式都保留了导出/导入（按钮存在即可点）。
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui

STATE = os.path.expandvars(
    r"%LOCALAPPDATA%\Packages\8166Yxw.MarketMotionStudio_fzc58jprbah1t\LocalState")

PAGE = "实时持仓收益"


def aid(win, name):
    return winui.find(win, lambda c, n=name: c.AutomationId == n)


def read_json(name):
    path = os.path.join(STATE, name)

    if not os.path.exists(path):
        return None

    with open(path, encoding="utf-8") as file:
        return json.load(file)


def baseline_brief(doc):
    if doc is None:
        return "（无文件）"

    rows = ", ".join(
        f"{row['Code']}:{row['Shares']}@{row['Cost']}" for row in doc["Rows"][:4])

    return f"{doc['Day']} {len(doc['Rows'])}行 [{rows}…]"


def pick_scope(win, label):
    combo = aid(win, "ScopeCombo")

    if combo is None:
        raise SystemExit("页面上没有范围切换控件")

    print(f"\n切到 {label}: {winui.combo_pick(win, combo, label)}")
    time.sleep(15)


def open_dialog(win):
    """打开管理持仓对话框，等到选择器真的出现——上一次关闭的淡出动画会让
    紧跟其后的第二次打开看起来没生效（实测：港股通关掉立刻切A股再开，找不到控件）。"""
    for _ in range(3):
        manage = aid(win, "ManageButton")

        if manage is not None:
            winui.invoke_click(manage)

        for _ in range(5):
            time.sleep(1.5)

            if aid(win, "BaselineDay") is not None:
                return

    raise SystemExit("管理持仓对话框没有打开（找不到基准日期选择器）")


def close_dialog(win):
    close = winui.find(win, lambda c: c.ControlTypeName == "ButtonControl"
                       and (c.Name or "") == "关闭")

    if close is not None:
        winui.invoke_click(close)

    time.sleep(2)


def dialog_state(win, label):
    picker = aid(win, "BaselineDay")

    if picker is None:
        raise SystemExit("对话框里没有基准日期选择器")

    enabled = picker.IsEnabled
    print(f"  {label}: 基准日期可选 = {enabled}, 显示 = {picker.Name!r}")

    # 导入/导出两颗按钮在两种模式下都要在。
    export = winui.find(win, lambda c: c.ControlTypeName == "ButtonControl"
                        and "导出初始持仓" in (c.Name or ""))
    imports = winui.find(win, lambda c: c.ControlTypeName == "ButtonControl"
                         and "导入初始持仓" in (c.Name or ""))

    print(f"  {label}: 导出按钮 = {export is not None}, 导入按钮 = {imports is not None}")

    return enabled, export is not None and imports is not None


def main():
    kong_before = read_json("ledger-baseline.json")
    plain_before = read_json("ledger-baseline-ashare.json")

    print("起 beforehand:")
    print("  含港股基准:", baseline_brief(kong_before))
    print("  A股基准  :", baseline_brief(plain_before))

    win = winui.launch("MarketMotionStudio.exe")
    time.sleep(3)

    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl"
                      and c.Name == PAGE)

    if item is None:
        raise SystemExit("导航里没有 实时持仓收益")

    winui.invoke_click(item)
    time.sleep(12)

    # ---- 港股通：播放到收盘 → 基准更新为会话日收盘 ----
    pick_scope(win, "A股+港股通")

    kong_after_switch = read_json("ledger-baseline.json")
    same_switch = baseline_brief(kong_after_switch) == baseline_brief(kong_before)
    print("  切换后（播放前）基准未动:", same_switch)

    play = aid(win, "PlayButton")

    if play is None:
        raise SystemExit("页面上没有播放键")

    winui.invoke_click(play)
    print("  按下播放，等动画走完…")
    time.sleep(18)

    kong_after_play = read_json("ledger-baseline.json")
    print("  播放结束后含港股基准:", baseline_brief(kong_after_play))

    ok_updated = (
        kong_after_play is not None
        and kong_after_play["Day"] >= "2026-10-30"
        and any(row["Code"].startswith("hk") for row in kong_after_play["Rows"]))
    ok_parked = same_switch

    # ---- 港股通对话框：日期锁定、导入导出都在 ----
    open_dialog(win)
    kong_enabled, kong_buttons = dialog_state(win, "港股通")
    winui.shot(win, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "artifacts", "baseline-kong-dialog.png"))
    close_dialog(win)

    # ---- A股：基准不动、日期可选 ----
    pick_scope(win, "A股")

    plain_after = read_json("ledger-baseline-ashare.json")
    ok_plain = baseline_brief(plain_after) == baseline_brief(plain_before)
    print("  A股基准未因切换/动画改变:", ok_plain, baseline_brief(plain_after))

    open_dialog(win)
    plain_enabled, plain_buttons = dialog_state(win, "A股")
    close_dialog(win)

    print("\n判定:")
    print("  ", "PASS" if ok_parked else "FAIL", "港股通：切换后、播放前基准不写")
    print("  ", "PASS" if ok_updated else "FAIL", "港股通：动画结束基准更新为最后交易日收盘（含港股）")
    print("  ", "PASS" if not kong_enabled else "FAIL", "港股通：基准日期锁定不可改")
    print("  ", "PASS" if ok_plain else "FAIL", "A股：基准始终不变")
    print("  ", "PASS" if plain_enabled else "FAIL", "A股：基准日期可选")
    print("  ", "PASS" if kong_buttons and plain_buttons else "FAIL", "两种模式都有导出/导入初始持仓")

    failed = not (ok_parked and ok_updated and not kong_enabled
                  and ok_plain and plain_enabled and kong_buttons and plain_buttons)

    if failed:
        raise SystemExit("判定未通过")


if __name__ == "__main__":
    main()
