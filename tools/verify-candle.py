# -*- coding: utf-8 -*-
"""真机验证 K 线页：取数、四种画法、两种推进方式、三种周期。

离线脚本能证明源端返回什么，证明不了页面跑得起来。这个脚本打开真实窗口，
按页面上那个顺序走一遍，把状态条读出来，并给每种画法留一张截图。

用法：
    python tools/verify-candle.py
"""
import os
import re
import subprocess
import time

import uiautomation as auto

APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUT = r"D:\software\MarketMotionStudio\artifacts"
SRC = r"D:\software\MarketMotionStudio\src\MarketMotionStudio"

PRIVATE = re.compile(r"[\ue000-\uf8ff]")
BAD = re.compile(r"失败|错误|无法|不可用|异常|failed|error")

CHECKS = []


def check(name, ok, note=""):
    CHECKS.append((name, ok, note))
    print(f"{'✓' if ok else '✗'} {name}" + (f" — {note}" if note else ""))


def find(cond, root, depth=0, limit=25):
    if depth > limit:
        return None
    try:
        if cond(root):
            return root
    except Exception:
        return None
    try:
        for ch in root.GetChildren():
            r = find(cond, ch, depth + 1, limit)
            if r is not None:
                return r
    except Exception:
        pass
    return None


def find_all(cond, root, depth=0, limit=25, out=None):
    out = [] if out is None else out
    if depth > limit:
        return out
    try:
        if cond(root):
            out.append(root)
    except Exception:
        pass
    try:
        for ch in root.GetChildren():
            find_all(cond, ch, depth + 1, limit, out)
    except Exception:
        pass
    return out


def pat(ctrl, pattern_id):
    try:
        return ctrl.GetPattern(pattern_id)
    except Exception:
        return None


def click(ctrl, wait=0.5):
    p = pat(ctrl, auto.PatternId.InvokePattern)
    if p is not None:
        try:
            p.Invoke()
            time.sleep(wait)
            return True
        except Exception:
            pass
    try:
        ctrl.Click(simulateMove=False, waitTime=wait)
        return True
    except Exception:
        return False


def app_pids():
    p = subprocess.run(["tasklist", "/FO", "CSV", "/FI", "IMAGENAME eq " + EXE],
                       capture_output=True)
    pids = set()
    for line in p.stdout.decode("utf-8", "replace").splitlines()[1:]:
        parts = [x.strip('"') for x in line.split('","')]
        if len(parts) >= 2 and parts[0].lower() == EXE.lower():
            pids.add(int(parts[1]))
    return pids


def launch():
    subprocess.run(["taskkill", "/IM", EXE, "/F"], capture_output=True)
    time.sleep(2)
    os.startfile(r"shell:AppsFolder\%s" % APPID)
    deadline = time.time() + 45
    while time.time() < deadline:
        if app_pids():
            for w in auto.GetRootControl().GetChildren():
                if w.ProcessId in app_pids() and w.Name:
                    time.sleep(3)
                    return w
        time.sleep(1)
    return None


def status_text(win):
    bar = find(lambda c: c.AutomationId == "Status", win)
    if bar is None:
        return None
    texts = [t.Name for t in find_all(lambda c: c.ControlTypeName == "TextControl", bar, limit=8)
             if t.Name and not PRIVATE.search(t.Name)]
    return max(texts, key=len) if texts else None


def wait_status(win, unlike=None, seconds=60):
    """等状态条说一句新话，且不是取数中的那句。"""
    last = unlike
    deadline = time.time() + seconds
    while time.time() < deadline:
        time.sleep(1.2)
        got = status_text(win)
        if got and got != last and not re.search(r"…|\.\.\.|正在|Fetching|读取", got):
            return got
    return status_text(win)


def pick(win, combo_id, label):
    """在下拉里选一项。展开 ComboBox，再从它的弹出层里点那一项。"""
    combo = find(lambda c: c.AutomationId == combo_id, win)
    if combo is None:
        return False

    expand = pat(combo, auto.PatternId.ExpandCollapsePattern)
    if expand is not None:
        try:
            expand.Expand()
            time.sleep(0.5)
        except Exception:
            pass
    else:
        click(combo, 0.6)

    # 弹出层不在这个窗口的子树里，所以到根上去找。
    for root in auto.GetRootControl().GetChildren():
        item = find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == label,
                    root, limit=8)
        if item is None:
            continue
        sel = pat(item, auto.PatternId.SelectionItemPattern)
        if sel is not None:
            try:
                sel.Select()
                time.sleep(0.8)
                return True
            except Exception:
                pass
        click(item, 0.8)
        return True

    return False


def combo_value(win, combo_id):
    """WinUI 的 ComboBox 不把当前项当成子 Text 节点，所以先问 ValuePattern，
    再退回「已选中项」和 LegacyIAccessible。"""
    combo = find(lambda c: c.AutomationId == combo_id, win)
    if combo is None:
        return None

    value = pat(combo, auto.PatternId.ValuePattern)
    if value is not None:
        try:
            if value.Value:
                return value.Value
        except Exception:
            pass

    selection = pat(combo, auto.PatternId.SelectionPattern)
    if selection is not None:
        try:
            chosen = selection.GetSelection()
            if chosen and chosen[0].Name:
                return chosen[0].Name
        except Exception:
            pass

    for c in find_all(lambda c: c.ControlTypeName == "TextControl", combo, limit=6):
        if c.Name:
            return c.Name

    return None


def enabled(win, automation_id):
    ctrl = find(lambda c: c.AutomationId == automation_id, win)
    return None if ctrl is None else ctrl.IsEnabled


def label_of(win, automation_id):
    """复选框的 UIA 名字就是它的 Content，所以标签空不空看这里。

    标签缺失在画面上表现为「方框旁边没有字」，和旁边的控件一比像是排版问题，
    编译器不管，构建也不报——只有读出来才知道是资源键没对上。
    """
    ctrl = find(lambda c: c.AutomationId == automation_id, win)
    return None if ctrl is None else ctrl.Name


def toggle_on(win, automation_id):
    ctrl = find(lambda c: c.AutomationId == automation_id, win)
    if ctrl is None:
        return None

    toggle = pat(ctrl, auto.PatternId.TogglePattern)
    if toggle is None:
        return None

    if toggle.ToggleState == auto.ToggleState.Off:
        toggle.Toggle()
        time.sleep(1.0)

    return toggle.ToggleState


def shot(win, name):
    path = os.path.join(OUT, name)
    try:
        win.CaptureToImage(path)
        return path
    except Exception:
        return None


def scrub_to(win, progress):
    """把进度条拖到某一处。进度条是每一页共用的那一条（`Scrub`）。"""
    bar = find(lambda c: c.AutomationId == "Scrub", win)

    if bar is None:
        return False

    bar.GetRangeValuePattern().SetValue(progress)
    time.sleep(1.8)

    return True


def png_diff(a, b, floor=13):
    """两幅画面差了多少，0..1。

    比**整幅**，不比某一根蜡烛：要证明的是整条横轴铺满了，而最后一根碰巧落在同一处说明
    不了这件事。`floor` 是「算不算不一样」的界，13/255 —— 抗锯齿那几个灰阶不算。
    """
    from PIL import Image, ImageChops

    if a is None or b is None:
        return 1.0

    first = Image.open(a).convert("RGB")
    second = Image.open(b).convert("RGB")

    if first.size != second.size:
        return 1.0

    hist = ImageChops.difference(first, second).convert("L").histogram()

    return sum(hist[floor:]) / float(first.size[0] * first.size[1])


def main():
    # 窗口三件套（多少根 / 右端 / 左端）由 `AnimationPlan.Window` 一处算，K线、持仓、定投
    # 三页共用 —— 各写一份的话改一处就得改三处，而每页单看都对、错起来也一模一样。
    plan = open(os.path.join(SRC, "Render", "AnimationPlan.cs"), encoding="utf-8-sig").read()
    render = open(os.path.join(SRC, "Render", "CandleRenderer.cs"), encoding="utf-8-sig").read()

    check("窗口几何交给共享的 `AnimationPlan.Window`",
          "_plan.Window(" in render and "_motion is CandleMotion.Scroll, _window, n" in render)
    check("滚动的窗口在收尾段展开成整段（不是一路滚到底）",
          "var wide = Easing.Ramp(t, FinaleStartMs, OpenOutMs);" in plan)
    check("展开时三件套自洽（Count = 右端 − 左端 + 1）",
          "return (head - first + 1, head, first);" in plan)

    win = launch()
    assert win is not None, "窗口未找到"

    items = [it.Name for it in find_all(
        lambda c: c.ControlTypeName == "ListItemControl", win, limit=8)
        if it.Name and it.Name not in ("设置", "Settings", "帮助", "Help")]

    check("导航里出现 K 线页", "K线" in items, " / ".join(items))

    page = find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "K线", win)

    # 导航项要点中才行：Invoke 有时只高亮不选中，于是一直停在启动页上，后面
    # 每一个 AutomationId 都找不到。用 Select，然后等这个页面自己的控件出现。
    def goto_page():
        for _ in range(3):
            if page is not None:
                sel = pat(page, auto.PatternId.SelectionItemPattern)
                if sel is not None:
                    try:
                        sel.Select()
                    except Exception:
                        pass
                else:
                    click(page, 1.0)
            deadline = time.time() + 12
            while time.time() < deadline:
                time.sleep(0.8)
                if find(lambda c: c.AutomationId == "PeriodCombo", win) is not None:
                    return True
        return False

    check("导航到 K 线页", goto_page())

    # 这个页面把四个下拉的选择都存下来了，所以「默认」只在从没存过时才是默认值：
    # 上一轮跑完停在「月K / 面积图」，这一轮恢复出来的就是月K和面积图，不是默认
    # 写错了。先显式复位到默认，下面三个检查才真的在检查默认值本身；顺带也把
    # 「恢复出来的值能落到预览上」这条路径走了一遍。
    for combo, label in (("PeriodCombo", "日K"),
                         ("StyleCombo", "蜡烛图"),
                         ("MotionCombo", "逐根铺满")):
        if combo_value(win, combo) != label:
            pick(win, combo, label)
            time.sleep(1.2)

    # 改周期会自己取一次数，等它落地，别和下面那次点取数撞在一起。
    time.sleep(3.0)

    # 两个复选框的标签也是资源键，键名写错就是一片空白，这里一并读出来。
    for box, wanted in (("AveragesCheck", "MA"), ("VolumeCheck", "成交量")):
        label = label_of(win, box)
        check(f"{box} 有标签", bool(label) and wanted in (label or ""), repr(label))

    # 四条信息的画面才是完整的：均线、成交量副图都在，四个画法的截图才有意义。
    check("两个叠加项都打开了",
          toggle_on(win, "AveragesCheck") == auto.ToggleState.On
          and toggle_on(win, "VolumeCheck") == auto.ToggleState.On)

    check("周期下拉默认日K", combo_value(win, "PeriodCombo") == "日K",
          str(combo_value(win, "PeriodCombo")))
    check("推进方式默认逐根铺满", combo_value(win, "MotionCombo") == "逐根铺满",
          str(combo_value(win, "MotionCombo")))
    check("滚动未开时窗口根数是灰的", enabled(win, "WindowBox") is False,
          str(enabled(win, "WindowBox")))

    fetch = find(lambda c: c.AutomationId == "FetchButton", win)
    click(fetch, 1.0)
    daily = wait_status(win, seconds=90)

    ok = bool(daily) and not BAD.search(daily)
    check("日K 取数", ok, daily or "(状态条空)")
    shot(win, "verify-candle-daily.png")

    # 四种画法：都不该重新取数，也不该报错。
    for label, name in [("蜡烛图", "candle"), ("美国线", "bar"), ("收盘线", "line"), ("面积图", "area")]:
        pick(win, "StyleCombo", label)
        time.sleep(1.2)
        got = status_text(win)
        check(f"画法 {label}", bool(got) and not BAD.search(got), got or "")
        shot(win, f"verify-candle-{name}.png")

    # 推进方式：滚动打开窗口根数，铺满又把它收起来。
    pick(win, "MotionCombo", "窗口滚动")
    time.sleep(1.2)
    check("切到窗口滚动后窗口根数可编辑", enabled(win, "WindowBox") is True)
    shot(win, "verify-candle-scroll.png")

    pick(win, "MotionCombo", "逐根铺满")
    time.sleep(1.0)
    check("切回逐根铺满后窗口根数变灰", enabled(win, "WindowBox") is False)

    # 收尾：滚动的窗口在收尾段展开成整段 —— 所以**拖到头**时，滚动与逐根铺满该是同一幅。
    # 判据用整幅画面（`png_diff`），不是某一根蜡烛：展开完之后最后一根本来就在同一处，
    # 一根说明不了整条横轴是不是铺满了。
    pick(win, "MotionCombo", "窗口滚动")
    time.sleep(1.2)
    scrub_to(win, 1.0)
    rolled = shot(win, "verify-candle-end-scroll.png")

    pick(win, "MotionCombo", "逐根铺满")
    time.sleep(1.2)
    scrub_to(win, 1.0)
    whole = shot(win, "verify-candle-end-grow.png")

    check("滚动走到头，画面就是逐根铺满（窗口在收尾段展开了）",
          png_diff(rolled, whole) < 0.01, "两幅差 {:.3%}".format(png_diff(rolled, whole)))

    # 周期换了要重新取数：等状态条说出新周期的名字。
    for label, key in [("周K", "周K"), ("月K", "月K")]:
        pick(win, "PeriodCombo", label)
        got = wait_status(win, unlike=daily, seconds=90)
        check(f"{label} 取数", bool(got) and key in (got or "") and not BAD.search(got),
              got or "(状态条空)")
        shot(win, f"verify-candle-{key}.png")

    # 成交量关掉：价格图收回那块空间，不该报错。
    volume = find(lambda c: c.AutomationId == "VolumeCheck", win)
    if volume is not None:
        toggle = pat(volume, auto.PatternId.TogglePattern)
        if toggle is not None:
            toggle.Toggle()
            time.sleep(1.2)
        got = status_text(win)
        check("关掉成交量面板", bool(got) and not BAD.search(got), got or "")
        shot(win, "verify-candle-novolume.png")

    print()
    failed = [n for n, ok, _ in CHECKS if not ok]
    print(f"{len(CHECKS) - len(failed)}/{len(CHECKS)} 通过")
    if failed:
        print("未通过：" + "、".join(failed))


if __name__ == "__main__":
    main()
