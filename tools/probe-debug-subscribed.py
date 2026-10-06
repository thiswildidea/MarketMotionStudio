# -*- coding: utf-8 -*-
r"""一次性：把 Debug 构建切成「已订阅」，上真机看看解锁后各控件长什么样。

不是断言脚本，是**把状态拍下来给人看**：订阅卡片那句话、水印开关与浓度滑块的
IsEnabled、订阅/管理两个按钮。量完即删。

用法：python tools/probe-debug-subscribed.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import winui  # noqa: E402

SIMULATION = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Packages", "8166Yxw.MarketMotionStudio_fzc58jprbah1t", "LocalState",
    "simulate-subscription.txt")

SHOT = os.path.join(os.path.dirname(HERE), "artifacts", "probe-subscribed-settings.png")

SETTINGS_NAMES = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки",
                  "Ajustes", "Paramètres", "Impostazioni", "Configurações", "Instellingen",
                  "Ayarlar", "Pengaturan", "設定"]


def by_id(window, automation_id):
    return winui.find(window, lambda c, a=automation_id: c.AutomationId == a)


def goto_settings(window):
    item = None

    for _ in range(3):
        for name in SETTINGS_NAMES:
            item = winui.find(
                window,
                lambda c, n=name: c.ControlTypeName == "ListItemControl" and c.Name == n)

            if item is not None:
                break

        if item is not None:
            break

        time.sleep(1.5)

    if item is None:
        return False

    try:
        item.GetSelectionItemPattern().Select()
    except Exception:  # noqa: BLE001
        item.Click(simulateMove=False, waitTime=0.4)

    deadline = time.time() + 15

    while time.time() < deadline:
        if by_id(window, "WatermarkStrengthSlider") is not None:
            time.sleep(1.0)
            return True

        time.sleep(0.5)

    return False


def report(window, automation_id, extra=""):
    control = by_id(window, automation_id)

    if control is None:
        print("  %-24s 不在树里" % automation_id)
        return None

    value = None

    try:
        value = control.GetRangeValuePattern().Value
    except Exception:  # noqa: BLE001
        pass

    line = "  %-24s IsEnabled=%s" % (automation_id, control.IsEnabled)

    if value is not None:
        line += "  Value=%s" % value

    if control.Name:
        line += "  Name=%r" % control.Name

    if extra:
        line += "  %s" % extra

    print(line)
    return control


def main():
    if not os.path.exists(SIMULATION):
        print("模拟文件不在：%s" % SIMULATION)
        return 1

    with open(SIMULATION, encoding="utf-8") as f:
        print("模拟文件存在，内容 = %r → 它会被当成价钱显示" % f.read().strip())

    window = winui.launch(winui.EXE)

    if window is None:
        print("应用没起来")
        return 1

    if not goto_settings(window):
        print("没走到设置页")
        return 1

    print("设置页控件：")
    for automation_id in ("SubscriptionState", "SubscribeButton", "ManageButton",
                          "WatermarkToggle", "WatermarkLockedNote", "WatermarkText",
                          "WatermarkFontCombo", "WatermarkStrengthSlider"):
        report(window, automation_id)

    # 这里不用 `winui.capture`：它写完图还要回读一遍、断言「画面里有一块画布」，
    # 而**设置页没有画布** —— 它对这样的页面永远是 False，图却照样写了出来。
    # 拿它判成败会把「判据不适用」读成「没截到」。
    window.SetActive()
    window.SetTopmost(True)
    os.makedirs(os.path.dirname(SHOT), exist_ok=True)
    time.sleep(1.0)

    try:
        window.CaptureToImage(SHOT)
        print("\n截图：%s（%d 字节）" % (SHOT, os.path.getsize(SHOT)))
    except Exception as exc:  # noqa: BLE001
        print("\n截图失败：%s" % exc)

    window.SetTopmost(False)

    winui.kill(winui.EXE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
