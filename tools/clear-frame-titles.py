# -*- coding: utf-8 -*-
r"""清掉各页被手动输入过的「标题文字」，让画面标题回到该页的默认（分语言的）文案。

为什么要清：商店截图要把 14 种语言的界面都拍一遍，而「标题文字」是**全局持久偏好**
（`StudioPreferences` 存 `ApplicationData.Current.LocalSettings`，与界面语言无关）。
某页只要被手输过一次，那一段中文就会跟着出现在英语、日语、俄语的商店图里；市值榜页
留下的那句还写着「美股市值」，而截图时市场是 A股。这些都不是应用的问题，是截图前
必须扫干净的状态。

用法：
  python tools\clear-frame-titles.py            # 只看：逐页读出标题框内容
  python tools\clear-frame-titles.py --clear    # 清空非空的（Ctrl+A 再 Delete）
  python tools\clear-frame-titles.py --clear --pages=NavMarketCap

不传 --clear 时只读不改。清空走键盘（程序化 SetValue 不触发 TextChanged，也就不会
保存），窗口要先拿到前台——键盘只发给前台窗口。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uiautomation as auto  # noqa: E402
import winui  # noqa: E402

CLEAR = "--clear" in sys.argv

# 全部页面，按导航顺序（AutomationId = x:Name）。
PAGES = [
    "NavMarketTurnover", "NavCandle", "NavStockVolume", "NavSectorRace",
    "NavMarketCap", "NavAhPremium", "NavExtremeDays", "NavFxCorridor",
    "NavIndexRace", "NavAssetRace", "NavDrawdown", "NavHoldOdds",
    "NavMatrix", "NavGainCalendar", "NavDcaPlan", "NavPosition",
]

_pages_arg = next((a.split("=", 1)[1].split(",")
                   for a in sys.argv[1:] if a.startswith("--pages=")), None)

if _pages_arg:
    PAGES = [p for p in PAGES if p in _pages_arg]


def select(win, nav_id):
    """导航项是 ListItem，选中它而不是 Invoke。"""
    nav = winui.find(win, lambda c: c.AutomationId == nav_id)

    if nav is None:
        return False

    try:
        nav.GetSelectionItemPattern().Select()
        return True
    except Exception:  # noqa: BLE001 - the item can go stale mid-click
        pass

    try:
        nav.GetInvokePattern().Invoke()
        return True
    except Exception:  # noqa: BLE001
        return False


def main():
    win = winui.launch(winui.EXE, wait_seconds=45)

    if win is None:
        print("窗口没起来")
        return 1

    time.sleep(2)

    changed = []

    for nav_id in PAGES:
        if not select(win, nav_id):
            print("%-18s 导航项未找到（该市场可能没有这一页）" % nav_id)
            continue

        time.sleep(1.5)

        box = winui.find(win, lambda c: c.AutomationId == "TitleBox")

        if box is None:
            print("%-18s 没有标题框" % nav_id)
            continue

        try:
            current = box.GetValuePattern().Value or ""
        except Exception:  # noqa: BLE001
            current = ""

        if not current.strip():
            print("%-18s 空" % nav_id)
            continue

        if not CLEAR:
            print("%-18s 有内容 %r（未清，加 --clear 才动）" % (nav_id, current))
            continue

        win.SetActive()
        time.sleep(0.6)
        box.SetFocus()
        time.sleep(0.4)
        auto.SendKeys("{Ctrl}a{Delete}", waitTime=0.3)
        time.sleep(1.8)  # 保存是 400ms 防抖，等它落盘

        try:
            after = box.GetValuePattern().Value or ""
        except Exception:  # noqa: BLE001
            after = None

        print("%-18s 清空 %r -> %r" % (nav_id, current, after))
        changed.append(nav_id)

    winui.kill(winui.EXE)
    print("已清 %d 页" % len(changed) if CLEAR else "（只读巡检）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
