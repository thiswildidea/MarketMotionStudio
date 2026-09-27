# -*- coding: utf-8 -*-
r"""生成 Microsoft Store 商品页截图：简体中文 / 繁體中文 / English 三语言。

思路：应用内置语言设置（设置页 LanguageCombo，重启生效）。脚本对每种语言
「切语言 → 杀进程重启 → 逐页导航 → 选标的 → 获取数据 → 拖到中途帧 → 截图」，
全部用 AutomationId 定位（x:Name 即 AutomationId），因此不依赖当前界面语言。

运行前提（缺一不可）：
  1. 应用已注册（Release 或 Debug 松散布局均可）：
     Add-AppxPackage -Register <布局目录>\AppxManifest.xml
  2. 包族名与 APPID 一致 —— 重新注册后若包族哈希变化，先改下面的 APPID；
  3. python 环境装有 uiautomation（2.0.x，用 GetPattern(PatternId.X)）。

用法：
  python tools\store-screenshots.py            # 三语言全量
  python tools\store-screenshots.py --smoke    # 只跑 zh-Hans + 市场成交额一页

产出：artifacts\store-screens\<语言>\<序号>-<页面>.png，逐行写 runlog.txt。
截图尺寸要求 ≥1366×768，脚本会先把窗口 MoveWindow 到安全大小再抓。
"""
import os
import subprocess
import sys
import time

import uiautomation as auto

# ---- 常量 -----------------------------------------------------------------------
APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUTROOT = r"D:\software\MarketMotionStudio\artifacts\store-screens"
LOG = os.path.join(OUTROOT, "runlog.txt")
SMOKE = "--smoke" in sys.argv

# (语言 tag, 重启后的窗口标题, 语言下拉条目文本, 设置导航项的本地化名称)
# 注：页脚导航项（帮助/设置）的 AutomationId 为空，只能按本地化名称找，
# 且找的时候要用「当前界面语言」的名称（上一轮的语言），不是目标语言的。
LANGS = [
    ("zh-Hans", "行情指标动画工作室", "简体中文", "设置"),
    ("zh-Hant", "行情指標動畫工作室", "繁體中文", "設定"),
    ("en-US", "Market Motion Studio", "English", "Settings"),
]

# (导航项 AutomationId, 输出文件名, 预置标的按钮名；None=直接获取，FIRST=点第一个预置)
PAGES = [
    ("NavMarketTurnover", "01-market-turnover", None),
    ("NavSectorRace", "02-sector-race", None),
    ("NavGainCalendar", "03-gain-calendar", "FIRST"),
    ("NavMatrix", "04-monthly-matrix", None),
    ("NavDcaPlan", "05-dca-plan", "FIRST"),
    ("NavPosition", "06-position", "中国平安"),
]

if SMOKE:
    LANGS = LANGS[:1]
    PAGES = PAGES[:1]

LINES = []


def say(s):
    LINES.append(str(s))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")


# ---- 基础操作 -------------------------------------------------------------------
def kill_app():
    subprocess.run(["taskkill", "/IM", EXE, "/F"], capture_output=True)
    time.sleep(3)


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
    os.startfile(r"shell:AppsFolder\%s" % APPID)


def wait_window(timeout=60):
    """按进程找主窗口——标题随语言变，不能按名字找。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        pids = app_pids()
        if pids:
            for w in auto.GetRootControl().GetChildren():
                try:
                    if w.ControlTypeName == "WindowControl" and w.ProcessId in pids:
                        return w
                except Exception:
                    pass
        time.sleep(1)
    return None


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


def byid(root, aid):
    return find(lambda c: c.AutomationId == aid, root)


def pat(ctrl, pattern_id):
    try:
        return ctrl.GetPattern(pattern_id)
    except Exception:
        return None


def invoke_click(ctrl):
    """优先 Invoke（不依赖鼠标位置），失败再 SelectionItem，最后真实点击。"""
    p = pat(ctrl, auto.PatternId.InvokePattern)
    if p is not None:
        try:
            p.Invoke()
            time.sleep(0.5)
            return True
        except Exception:
            pass
    p = pat(ctrl, auto.PatternId.SelectionItemPattern)
    if p is not None:
        try:
            p.Select()
            time.sleep(0.5)
            return True
        except Exception:
            pass
    try:
        ctrl.Click(simulateMove=False, waitTime=0.5)
        return True
    except Exception:
        return False


def find_settings_nav(win, settings_name):
    """设置项在页脚，AutomationId 为空，按名称找。

    先试 AutomationId（万一将来补上），再试当前语言的名称，最后兜底
    尝试全部语言的设置项名称——初始语言未知时也能找到入口。
    """
    nav = byid(win, "NavSettings")
    if nav is not None:
        return nav
    nav = find(lambda c: c.ControlTypeName == "ListItemControl"
               and c.Name == settings_name, win)
    if nav is not None:
        return nav
    for fallback in ("设置", "設定", "Settings"):
        nav = find(lambda c: c.ControlTypeName == "ListItemControl"
                   and c.Name == fallback, win)
        if nav is not None:
            say("  （设置项按兜底名称 %r 找到）" % fallback)
            return nav
    return None


def combo_select(combo, item_name, timeout=8):
    """展开下拉，按条目文本选择（语言条目是原生语言名，不随界面语言变）。"""
    p = pat(combo, auto.PatternId.ExpandCollapsePattern)
    if p is None:
        return False
    try:
        p.Expand()
    except Exception:
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        for it in combo.GetChildren():
            if it.ControlTypeName == "ListItemControl" and it.Name == item_name:
                sp = pat(it, auto.PatternId.SelectionItemPattern)
                if sp is not None:
                    sp.Select()
                    time.sleep(0.5)
                    try:
                        p.Collapse()
                    except Exception:
                        pass
                    return True
        time.sleep(0.5)
    try:
        p.Collapse()
    except Exception:
        pass
    return False


def click_preset(win, name):
    """点 Presets（ItemsControl）里的标的按钮。name=FIRST 表示第一个。"""
    presets = byid(win, "Presets")
    if presets is None:
        return False
    if name == "FIRST":
        b = find(lambda c: c.ControlTypeName == "ButtonControl", presets)
    else:
        b = find(lambda c: c.ControlTypeName == "ButtonControl" and c.Name == name,
                 presets)
    if b is None:
        return False
    return invoke_click(b)


def wait_play_enabled(win, timeout=240):
    """获取数据的完成信号：播放按钮从禁用变可用（语言无关）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        pb = byid(win, "PlayButton")
        if pb is not None and pb.IsEnabled:
            return True
        time.sleep(2)
    return False


def scrub_mid(win, ratio=0.55):
    """把进度条拖到中途，让截图停在动画中段而不是终帧。"""
    sc = byid(win, "Scrub")
    if sc is None:
        return False
    p = pat(sc, auto.PatternId.RangeValuePattern)
    if p is None:
        return False
    try:
        lo, hi = p.Minimum, p.Maximum
        p.SetValue(lo + (hi - lo) * ratio)
        time.sleep(0.8)
        return True
    except Exception:
        return False


def ensure_window_size(win):
    """Store 要求截图 ≥1366×768；把窗口放到安全大小（物理像素）。"""
    try:
        sw, sh = auto.GetScreenSize()
    except Exception:
        sw, sh = 1920, 1080
    w = min(1720, sw - 80)
    h = min(1000, sh - 60)
    if w < 1366 or h < 768:
        say("  !! 屏幕太小（%dx%d），截图可能不满足商店最小尺寸" % (sw, sh))
    try:
        win.MoveWindow(30, 20, w, h)
        time.sleep(1)
    except Exception as e:
        say("  MoveWindow failed: %r" % e)


def capture(win, path):
    try:
        win.SetFocus()
        time.sleep(1)
    except Exception:
        pass
    ok = win.CaptureToImage(path)
    time.sleep(0.5)
    return ok and os.path.exists(path)


# ---- 主流程 ---------------------------------------------------------------------
os.makedirs(OUTROOT, exist_ok=True)
open(LOG, "w", encoding="utf-8").close()

try:
    auto.SetProcessDpiAwareness(auto.ProcessDpiAwareness.PerMonitorDpiAware)
except Exception:
    try:
        auto.SetProcessDpiAwareness(2)
    except Exception:
        pass

for tag, title, combo_label, settings_name in LANGS:
    say("===== %s =====" % tag)
    kill_app()
    launch()
    win = wait_window()
    if win is None:
        say("  首次启动：窗口未出现，跳过该语言")
        continue
    time.sleep(2)
    ensure_window_size(win)

    # --- 切语言：设置页选语言 → 重启生效 ---
    nav = find_settings_nav(win, settings_name)
    if nav is None:
        say("  设置导航项未找到（%r），跳过该语言" % settings_name)
        continue
    invoke_click(nav)
    time.sleep(2)
    combo = byid(win, "LanguageCombo")
    if combo is None:
        say("  LanguageCombo 未找到，跳过该语言")
        continue
    if not combo_select(combo, combo_label):
        say("  未能选中语言条目 %r" % combo_label)
        continue
    say("  已选语言 %r，重启生效" % combo_label)

    kill_app()
    launch()
    win = wait_window()
    if win is None:
        say("  重启后窗口未出现，跳过该语言")
        continue
    say("  重启后窗口标题: %r（期望 %r）%s" %
        (win.Name, title, "OK" if win.Name == title else "!! 不一致"))
    time.sleep(2)
    ensure_window_size(win)

    outdir = os.path.join(OUTROOT, tag)
    os.makedirs(outdir, exist_ok=True)

    # --- 逐页：导航 → 选标的 → 获取 → 拖进度 → 截图 ---
    for nav_id, fname, preset in PAGES:
        say("  --- %s ---" % fname)
        nav = byid(win, nav_id)
        if nav is None:
            say("    %s 未找到" % nav_id)
            continue
        invoke_click(nav)
        time.sleep(2)

        fb = byid(win, "FetchButton")
        if fb is None:
            say("    FetchButton 未找到")
            continue

        if preset and not fb.IsEnabled:
            if click_preset(win, preset):
                say("    已点预置标的 %r" % preset)
                time.sleep(1.5)
                fb = byid(win, "FetchButton")
            else:
                say("    预置标的 %r 未找到" % preset)

        if fb is None or not fb.IsEnabled:
            say("    获取按钮不可用，跳过该页")
            continue

        invoke_click(fb)
        if wait_play_enabled(win):
            say("    数据就绪")
        else:
            say("    等待数据超时（240s），仍尝试截图")

        scrub_mid(win)
        path = os.path.join(outdir, fname + ".png")
        if capture(win, path):
            say("    截图: %s" % path)
        else:
            say("    截图失败: %s" % path)

say("ALL DONE")
