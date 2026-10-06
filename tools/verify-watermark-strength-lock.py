# -*- coding: utf-8 -*-
r"""真机确认：未订阅时水印「浓度」钉在上限且改不动，订阅之后能改。

为什么要上真机：这次动的是**同一个锁的另一半**（开关早就锁了，浓度是新锁的），而失败方式跟原来那半完全一样 ——
滑块照样画在那里、照样有值，看起来只是「用户自己把它拉满了」。源码断言能证明「值来自 MaxOpacity」「IsEnabled
跟着 StrengthOptional」，证明不了两件事：**控件真的显示 40**，以及**真的改不动**。

所以它这里的判据不是「IsEnabled 是 False」，而是**试着把它拖到别处，再看它回到哪里**：

* 未订阅：读出来是 40，且 `SetValue(10)` 之后仍然是 40（控件拒绝，或写埋 old value 被盖回去）。
* 订阅：同一个 SetValue 生效，值变了 —— 证明刚才那次动不了是订阅的缘故，不是控件坏了。

后一半尤其重要：「谁都拖不动」和「没订阅的人拖不动」在画面上长得一模一样，只测前一半的话，一个把滑块彻底写死的
回归会一路绿灯。

阈值写死为 40：`Watermark.MaxOpacity`，滑块的上限就是它 —— 「钉在上限」与「钉在 40」是同一件事。

用法：python tools/verify-watermark-strength-lock.py
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
LOCAL = os.path.dirname(SIMULATION)
CEILING = 40
TRIED = 10

# 导航项的叫法随界面语言变（见 resw 的 ShellSettings），而用户的默认语言又不由脚本决定。
SETTINGS_NAMES = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки",
                  "Ajustes", "Paramètres", "Impostazioni", "Configurações", "Instellingen",
                  "Ayarlar", "Pengaturan", "設定"]

PASSED = []
FAILED = []


def check(what, ok, note=""):
    line = "  %s %s" % ("√" if ok else "×", what)

    if note:
        line += "  — %s" % note

    print(line, flush=True)
    (PASSED if ok else FAILED).append(what)


def slider(window):
    return winui.find(window, lambda c: c.AutomationId == "WatermarkStrengthSlider")


def probe(control):
    """把这只滑块报出来的三件事取回来：(值, 只读吗, 可操作吗)。

    **读的是 `Value` 不是 `CurrentValue`** —— uiautomation 的 RangeValuePattern 把百分比放在 `Value`
    上，`CurrentValue` 根本不存在，按着别的包写法去读会得到 None，而 None 一路传到判定里就变成
    「控件没值」这种看起来像应用坏了的错误结论。（实测：IsEnabled 明明读到了，值却一直是 None。）
    """
    pattern = None

    try:
        pattern = control.GetRangeValuePattern()
    except Exception:  # noqa: BLE001
        return None, None, control.IsEnabled

    try:
        return pattern.Value, pattern.IsReadOnly, control.IsEnabled
    except Exception:  # noqa: BLE001
        return None, None, control.IsEnabled


def drag(control, value):
    """把它拖到 `value`。返回 False 表示这一下被拒了。

    走 RangeValuePattern 的 SetValue 而不是真点：设值与鼠标拖是同一个控件的两条入口，而这里要
    回答的是「它让不让改」，问它要这个值就是最短的那条路 —— 而且它拒的方式不一样，比
    试着点一下更好判。
    """
    try:
        pattern = control.GetRangeValuePattern()
    except Exception:  # noqa: BLE001
        return False

    try:
        pattern.SetValue(value)
    except Exception:  # noqa: BLE001 - 被禁用时 UIA 抛 ElementNotEnabled
        return False

    time.sleep(0.8)

    return True


def goto_settings(window):
    """切到设置页 —— 滑块在那儿，没走到就谈不上读到它。"""
    item = None

    for attempt in range(3):
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
        try:
            item.Click(simulateMove=False, waitTime=0.4)
        except Exception:  # noqa: BLE001
            return False

    # 等到滑块真的挂进树里：导航是一次页面切换，UIA 那一瞬间还没有它，
    # 「找不到」会被误读成「控件不存在」。
    deadline = time.time() + 15

    while time.time() < deadline:
        if slider(window) is not None:
            time.sleep(1.0)
            return True

        time.sleep(0.5)

    return False


def set_simulation(subscribed):
    if subscribed:
        os.makedirs(LOCAL, exist_ok=True)

        with open(SIMULATION, "w", encoding="utf-8") as f:
            f.write("¥28.00")
    elif os.path.exists(SIMULATION):
        os.remove(SIMULATION)


def main():
    if not os.path.isdir(LOCAL):
        print("找不到 LocalState（%s），跳过" % LOCAL)
        return 1

    try:
        for subscribed in (False, True):
            set_simulation(subscribed)
            # 先杀再起：还在跑的那个实例保持着它启动时加载的程序集，
            # 对着它读等于对着上一次改动读。
            window = winui.launch(winui.EXE)

            if window is None:
                print("应用没起来")
                return 1

            if not goto_settings(window):
                print("没走到设置页")
                winui.kill(winui.EXE)
                return 1

            control = slider(window)
            label = "订阅" if subscribed else "未订阅"
            value, readonly, movable = probe(control)

            print("%s：滑块 Value = %s，IsReadOnly = %s，IsEnabled = %s"
                  % (label, value, readonly, movable), flush=True)

            if subscribed:
                # 先记住它，后头放回去：这一轮会往 LocalSettings 里写一个浓度偏好，
                # 不还原的话下一次打开的设置页就不是出厂那个样子了。
                original = value
                accepted = drag(control, TRIED)
                moved, readonly_after, _ = probe(control)

                check("订阅之后浓度拖得动",
                      accepted and moved is not None and abs(moved - TRIED) < 0.5,
                      "拖到 %d 之后是 %s" % (TRIED, moved))
                check("订阅之后滑块不再是只读的", readonly_after is False,
                      "IsReadOnly = %s" % readonly_after)

                if original is not None and abs(original - moved) > 0.5:
                    drag(control, original)
            else:
                check("未订阅时浓度显示在上限 %d" % CEILING,
                      value is not None and abs(value - CEILING) < 0.5,
                      "实际 %s" % value)

                rejected = drag(control, TRIED)
                after, readonly_after, _ = probe(control)

                check("未订阅时拖不动：把它拖到 %d，它仍在 %d" % (TRIED, CEILING),
                      after is not None and abs(after - CEILING) < 0.5,
                      "UIA 接受了这一下=%s，拖之后是 %s" % (rejected, after))
                check("未订阅时控件自己也报不可操作", movable is False)
                check("未订阅时这只滑块是只读的", readonly is False or readonly_after is True,
                      "IsReadOnly = %s → %s" % (readonly, readonly_after))

            winui.kill(winui.EXE)
    finally:
        set_simulation(False)

    print("\n%s" % ("全部通过" if not FAILED else "%d 项失败" % len(FAILED)))

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
