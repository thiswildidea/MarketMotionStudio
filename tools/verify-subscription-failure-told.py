# -*- coding: utf-8 -*-
r"""真机确认：导出框里点「订阅」，买不成时**有话说**。

为什么要有这一条：买不成这条路以前是**完全安静**的 —— `SubscribeAsync` 返回
`Unavailable` 时连商店自己的对话框都不开（`_offer` 是 null 就直接返回），`PermitAsync`
拿到 false 就结束，于是「点了一下订阅」和「什么都没点」在画面上无法区分。这正是商店版
报回来的样子：*点击订阅没反应*。现在三个答案都要说话，`Unavailable` / `Failed` 各有一句，
写在这里的判据就是「第二个框真的冒出来了」。

本地 Debug 关掉模拟之后走的**正是商店那条路**：本机也没人给得出加载项，`LookupAsync`
一样是 `among 0` → `Unavailable`。所以这里量到的行为就是新机器上量到的行为。

判据三条：
  1. 导出框按下去，订阅框出来（否则后面全是空转）；
  2. 点「订阅」之后，弹「订阅没能完成」，正文是 `SettingsSubscriptionUnavailable` 那句；
  3. 文件夹里没有多出 mp4 —— 说了话不等于放行。

顺带盯一件只有这里抓得住的事：**第二个框是紧接着第一个框开的**。WinUI 的
`ContentDialog.ShowAsync()` 在前一个还没退干净时会抛异常，而这条路上商店框根本没出现，
两个框是背靠背的 —— 抛了就不是「没反应」，是**崩**。所以末尾再确认进程还活着。

前置：`python tools/simulate-subscription.py off`，并且至少导出过一次（输出文件夹已选），
否则第一次导出会弹保存选择器，脚本会把它当成「冒出来的不是订阅框」如实报出来。

用法：python tools/verify-subscription-failure-told.py
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import winui  # noqa: E402

SHOT_DIR = os.path.join(os.path.dirname(HERE), "artifacts")
CRASH_LOG = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Packages",
                         "8166Yxw.MarketMotionStudio_fzc58jprbah1t", "LocalState",
                         "crash.log")

NAV_TURNOVER = ["市场成交额", "Market turnover", "Umsatz", "売買代金", "거래대금"]
NAV_SETTINGS = ["设置", "Settings", "設定", "Einstellungen", "설정", "Настройки",
                "Ajustes", "Paramètres", "Impostazioni", "Configurações", "Instellingen",
                "Ayarlar", "Pengaturan"]

# 三个框的标题 / 按钮都是 14 语言里同一句，这里给中文 + 英文，够认出来就行。
OFFER_TITLE = "导出视频需要订阅"
FAILED_TITLE = "订阅没能完成"
FAILED_BODY = "无法联系到订阅"
SUBSCRIBE_BUTTON = "订阅"
CANCEL_BUTTON = "取消"


def check(what, ok, note=""):
    print("  %s %s%s" % ("√" if ok else "×", what, ("  — %s" % note) if note else ""), flush=True)
    return ok


def by_id(window, automation_id):
    return winui.find(window, lambda c, a=automation_id: c.AutomationId == a)


def named(window, name, control_type=None):
    return winui.find(
        window,
        lambda c, n=name, t=control_type: c.Name == n
        and (t is None or c.ControlTypeName == t))


def wait_named(window, name, seconds, control_type=None):
    deadline = time.time() + seconds

    while time.time() < deadline:
        found = named(window, name, control_type)

        if found is not None:
            return found

        time.sleep(0.4)

    return None


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


def press(window, control, note):
    """按一下，矩形为空就当没按 —— 静默跳过这一下是这里最容易读成谎话的事。"""
    if control is None:
        return False

    try:
        rect = control.BoundingRectangle
    except Exception:  # noqa: BLE001
        rect = None

    if rect is not None and rect.width() > 0 and rect.height() > 0:
        window.SetActive()
        control.Click(simulateMove=False, waitTime=0.5)
        return True

    # 矩形是空的（横滚面板外的按钮就是这样），但它是个**真按钮** ——
    # InvokePattern 不靠坐标，这一下按得下去，也真的按到了。
    try:
        control.GetInvokePattern().Invoke()
        print("  · %s 矩形是空的，走 InvokePattern 按下" % note)
        return True
    except Exception:  # noqa: BLE001
        pass

    print("  × %s 按不下去（矩形空，也没有 InvokePattern）" % note)
    return False


def remember_folder(window):
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


def crash_tail():
    try:
        with open(CRASH_LOG, encoding="utf-8", errors="replace") as f:
            lines = [ln.rstrip() for ln in f if ln.strip()]
    except OSError:
        return []

    return lines[-6:]


def maxed(win):
    win.SetActive()
    time.sleep(1.5)

    try:
        win.GetWindowPattern().SetWindowVisualState(winui.auto.WindowVisualState.Maximized)
        time.sleep(1.5)
    except Exception:  # noqa: BLE001
        pass


def main():
    sim = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Packages",
                       "8166Yxw.MarketMotionStudio_fzc58jprbah1t", "LocalState",
                       "simulate-subscription.txt")

    if os.path.exists(sim):
        print("订阅模拟还开着 —— 那样根本不会弹订阅框。先跑 python tools/simulate-subscription.py off")
        return 2

    print("订阅模拟已关（走的就是商店那条 Unavailable 路）")

    window = winui.launch(winui.EXE)

    if window is None:
        print("应用没起来")
        return 1

    maxed(window)

    folder = remember_folder(window)
    knows_folder = bool(folder) and os.path.isdir(folder)
    print("输出文件夹 = %r%s" % (folder, "" if knows_folder else "（未设置 —— 见下）"))

    item = pick_nav(window, NAV_TURNOVER)

    if item is None:
        print("没找到「市场成交额」导航项")
        winui.kill(winui.EXE)
        return 1

    try:
        item.GetSelectionItemPattern().Select()
    except Exception:  # noqa: BLE001
        item.Click(simulateMove=False, waitTime=0.4)

    # 这一页不会自己取数（重注册清过 LocalState，连上次的参数都没了），
    # 得先按「获取数据」—— 导出按钮在没取到数之前是禁用的，而且矩形是 0x0。
    fetch = by_id(window, "FetchButton")

    if fetch is not None and fetch.IsEnabled:
        print("按「获取数据」")
        press(window, fetch, "获取数据按钮")

    button = None
    deadline = time.time() + 180

    while time.time() < deadline:
        button = by_id(window, "ExportButton")

        if button is not None and button.IsEnabled:
            break

        time.sleep(2)

    if button is None or not button.IsEnabled:
        print("导出按钮一直没亮（数据没到？）")
        winui.kill(winui.EXE)
        return 1

    before = mp4s(folder)
    print("按下导出（文件夹里原有 %d 个 mp4）" % len(before))
    press(window, button, "导出按钮")

    offer = wait_named(window, OFFER_TITLE, 8)

    if offer is None:
        offer = wait_named(window, "Exporting a video requires a subscription", 3)

    ok_offer = check("按下导出后弹出了订阅框", offer is not None,
                     "标题 %r" % (offer.Name if offer is not None else "没等到"))

    if offer is None:
        winui.kill(winui.EXE)
        return 1

    subscribe = wait_named(window, SUBSCRIBE_BUTTON, 5, "ButtonControl")

    if subscribe is None:
        subscribe = wait_named(window, "Subscribe", 3, "ButtonControl")

    if not check("订阅框里有「订阅」按钮", subscribe is not None):
        winui.kill(winui.EXE)
        return 1

    print("点「订阅」")
    press(window, subscribe, "订阅按钮")

    # 背靠背第二个框：给足 12 秒，LookupAsync 要问一次商店。
    failed = wait_named(window, FAILED_TITLE, 12)

    if failed is None:
        failed = wait_named(window, "The subscription did not go through", 3)

    ok_told = check("买不成时弹出了「订阅没能完成」", failed is not None,
                    "标题 %r" % (failed.Name if failed is not None else "没等到"))

    body = wait_named(window, FAILED_BODY, 3) if failed is not None else None

    if body is None and failed is not None:
        # 正文是整句，Name 里带的是完整那句话；认前缀。
        body = winui.find(window, lambda c: FAILED_BODY in (c.Name or ""))

    ok_body = check("框里说的是「联系不到订阅」那句", body is not None,
                    (body.Name[:40] + "…") if body is not None else "没读到正文")

    time.sleep(1.0)
    window.SetActive()
    window.SetTopmost(True)
    time.sleep(1.0)

    try:
        shot = os.path.join(SHOT_DIR, "verify-subscription-failure-told.png")
        window.CaptureToImage(shot)
        print("截图：%s" % shot)
    except Exception as exc:  # noqa: BLE001
        print("截图失败：%s" % exc)

    window.SetTopmost(False)

    cancel = wait_named(window, CANCEL_BUTTON, 4, "ButtonControl")

    if cancel is not None:
        press(window, cancel, "取消按钮")

    time.sleep(2.0)

    written = mp4s(folder) - before

    if knows_folder:
        ok_no_file = check("说了话但没放行：没有多出 mp4", not written,
                           "多出来：%s" % (sorted(written) or "无"))
    else:
        # 文件夹没设过，这条自动成立 —— 而它是真的：闸口在选文件夹之前，
        # 连保存选择器都没轮到，更不可能有文件。
        ok_no_file = check("说了话但没放行：没有多出 mp4", not written,
                           "文件夹未设置，这条自动成立（闸口在选文件夹之前）")

    alive = bool(winui.pids(winui.EXE))
    ok_alive = check("背靠背开第二个框没有把应用带崩", alive,
                     "进程还在" if alive else "进程没了 —— 看 crash.log")

    print("crash.log 末尾：")

    for line in crash_tail():
        print("    %s" % line)

    winui.kill(winui.EXE)
    return 0 if (ok_offer and ok_told and ok_body and ok_no_file and ok_alive) else 1


if __name__ == "__main__":
    sys.exit(main())
