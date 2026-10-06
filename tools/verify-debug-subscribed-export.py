# -*- coding: utf-8 -*-
r"""真机确认：Debug 构建开着订阅模拟时，「导出」不再弹订阅对话框，而是直接把文件写出来。

为什么要有这一条：`PermitAsync` 的 `if (subscription.Subscribed) return true;` 是源码里读到的，
读得到不等于点得通 —— 而它出问题时的样子**是一条谁都不会怀疑的路上**：按钮照样按得下去，
只是又弹出那个「导出视频需要按月订阅」的框，看起来像订阅没生效。所以这里把它按下去，
然后盯着两件事：**订阅对话框有没有冒出来**，以及**输出文件夹里有没有多出一个 mp4**。

输出文件夹是上次选过的那个（`OutputFolder.RememberedPath`），从设置页那句路径读回来 ——
所以跑之前**至少导出过一次、或者去设置页选过一次文件夹**，否则第一次导出会弹保存选择器，
那个框不是订阅框、但脚本会把它当成「有别的框冒出来」。脚本会把这种情况说清楚。

前置：`python tools/simulate-subscription.py on`（没开的话应当弹订阅框，脚本会如实报出来）。

用法：python tools/verify-debug-subscribed-export.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import winui  # noqa: E402

SHOT_DIR = os.path.join(os.path.dirname(HERE), "artifacts")

NAV_TURNOVER = ["市场成交额", "Market turnover", "Umsatz", "売買代金", "거래대금"]
NAV_SETTINGS = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки",
                "Ajustes", "Paramètres", "Impostazioni", "Configurações", "Instellingen",
                "Ayarlar", "Pengaturan"]

# 订阅对话框认标题那一句（SubscriptionOfferTitle，14 语言里相同的那几个词）。
OFFER_TITLES = ["导出视频需要按月订阅", "Exporting a video requires a subscription",
                "需要订阅", "A subscription is required"]


def check(what, ok, note=""):
    print("  %s %s%s" % ("√" if ok else "×", what, ("  — %s" % note) if note else ""), flush=True)
    return ok


def by_id(window, automation_id):
    return winui.find(window, lambda c, a=automation_id: c.AutomationId == a)


def pick_nav(window, names):
    for _ in range(4):
        for name in names:
            item = winui.find(
                window,
                lambda c, n=name: c.ControlTypeName == "ListItemControl" and c.Name == n)

            if item is not None:
                return item

        time.sleep(1.5)

    return None


def remember_folder(window):
    """从设置页把上次选定的输出文件夹读回来。

    走设置页而不是读注册表：`OutputFolder.RememberedPath` 存在 LocalSettings 里，
    外面直接读 settings.dat 是二进制格式，而页面上那句路径就是同一个值。
    """
    item = pick_nav(window, NAV_SETTINGS)

    if item is None:
        return None

    try:
        item.GetSelectionItemPattern().Select()
    except Exception:  # noqa: BLE001
        item.Click(simulateMove=False, waitTime=0.4)

    deadline = time.time() + 20

    while time.time() < deadline:
        text = by_id(window, "OutputPathText")

        if text is not None and text.Name:
            return text.Name.strip()

        time.sleep(0.5)

    return None


def mp4s(folder):
    if not folder or not os.path.isdir(folder):
        return set()

    return {f for f in os.listdir(folder) if f.lower().endswith(".mp4")}


def main():
    sim = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Packages",
                       "8166Yxw.MarketMotionStudio_fzc58jprbah1t", "LocalState",
                       "simulate-subscription.txt")

    if not os.path.exists(sim):
        print("订阅模拟没开 —— 先跑 python tools/simulate-subscription.py on")
        return 2

    with open(sim, encoding="utf-8") as f:
        print("订阅模拟在（价钱显示为 %r）" % f.read().strip())

    window = winui.launch(winui.EXE)

    if window is None:
        print("应用没起来")
        return 1

    folder = remember_folder(window)
    print("输出文件夹 = %r" % folder)

    if not folder or not os.path.isdir(folder):
        print("读不到输出文件夹 —— 先去设置页「选择文件夹」选一个，或手动导出一次。")
        winui.kill(winui.EXE)
        return 2

    item = pick_nav(window, NAV_TURNOVER)

    if item is None:
        print("没找到「市场成交额」导航项")
        winui.kill(winui.EXE)
        return 1

    try:
        item.GetSelectionItemPattern().Select()
    except Exception:  # noqa: BLE001
        item.Click(simulateMove=False, waitTime=0.4)

    # 导出按钮在没取到数之前是禁用的；它自己亮起来就说明数据到了。
    button = None
    deadline = time.time() + 120

    while time.time() < deadline:
        button = by_id(window, "ExportButton")

        if button is not None and button.IsEnabled:
            break

        time.sleep(2)

    if button is None or not button.IsEnabled:
        print("导出按钮一直没亮（数据没到？）")
        winui.kill(winui.EXE)
        return 1

    print("导出按钮已亮，按下它")
    before = mp4s(folder)
    print("按下之前文件夹里有 %d 个 mp4" % len(before))

    button.SetFocus()
    button.Click(simulateMove=False, waitTime=0.5)

    # 订阅框是**立刻**弹的（PermitAsync 在编码之前），3 秒足够看清。
    time.sleep(3.0)
    offer = None

    for title in OFFER_TITLES:
        offer = winui.find(
            window,
            lambda c, t=title: c.Name == t and c.ControlTypeName != "ListItemControl")

        if offer is not None:
            break

    ok_dialog = check("按下导出后没有弹出订阅对话框", offer is None,
                      "冒出来的是 %r" % offer.Name if offer is not None else "")

    if offer is not None:
        try:
            offer.Click(simulateMove=False, waitTime=0.4)
        except Exception:  # noqa: BLE001
            pass

        winui.kill(winui.EXE)
        return 1

    print("没有订阅框，等文件写出来（最多 180 秒）")
    deadline = time.time() + 180
    written = set()

    while time.time() < deadline:
        written = mp4s(folder) - before

        if written:
            break

        time.sleep(4)

    ok_file = check("导出真的写出了 mp4", bool(written), "新文件：%s" % (sorted(written) or "无"))

    window.SetActive()
    window.SetTopmost(True)
    time.sleep(1.0)

    try:
        shot = os.path.join(SHOT_DIR, "verify-debug-subscribed-export.png")
        window.CaptureToImage(shot)
        print("截图：%s" % shot)
    except Exception as exc:  # noqa: BLE001
        print("截图失败：%s" % exc)

    window.SetTopmost(False)
    winui.kill(winui.EXE)
    return 0 if (ok_dialog and ok_file) else 1


if __name__ == "__main__":
    sys.exit(main())
