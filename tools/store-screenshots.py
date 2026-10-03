# -*- coding: utf-8 -*-
r"""生成 Microsoft Store 商品页截图：全部 14 种语言。

思路：应用内置语言设置（设置页 LanguageCombo，重启生效）+ 市场设置
（MarketCombo，同样重启生效）。脚本对每种语言「切语言 + 切市场 → 杀进程
重启 → 逐页导航 → 选标的 → 获取数据 → 拖到终帧 → 截图」，全部用
AutomationId 定位（x:Name 即 AutomationId），因此不依赖当前界面语言。

各语言的市场与标的规定（2026-09-27）：
  简体中文   A股  预置标的（第一项=中国平安）
  繁體中文   港股  预置标的（第一项=腾讯控股）
  其余 12 种  美股  搜索 AAPL 选建议（展示搜索能力）

截图停在动画的**最后一帧**（进度条拖到最大），收尾卡/终态画面即商店图。

运行前提（缺一不可）：
  1. 应用已注册（Release 或 Debug 松散布局均可）：
     Add-AppxPackage -Register <布局目录>\AppxManifest.xml
  2. 包族名与 APPID 一致 —— 重新注册后若包族哈希变化，先改下面的 APPID；
  3. python 环境装有 uiautomation（2.0.x，用 GetPattern(PatternId.X)）。

用法：
  python tools\store-screenshots.py            # 14 语言全量
  python tools\store-screenshots.py --smoke    # 只跑 zh-Hans + 市场成交额一页
  python tools\store-screenshots.py --langs=en-US --pages=06-position
                                                # 只跑指定语言/页面（验证用）

窗口**最大化后再抓**（商店要的是「应用全屏」的观感，不是缩在屏幕中间的窗口）；
画面一律停在动画的**最后一帧**。

产出：artifacts\store-screens\<语言>\<序号>-<页面>.png，逐行写 runlog.txt。
商店只要求截图 ≥1366×768；本屏 1920×1080，最大化后是 1920×1080（含标题栏）。
跑之前确认主题是浅色——旧图库是浅色主题，深浅混着上传不好看。
"""
import os
import subprocess
import sys
import time

import uiautomation as auto

try:
    from PIL import Image
except ImportError:  # 没装 PIL 就不查空白，只管截图
    Image = None

# ---- 常量 -----------------------------------------------------------------------
APPID = "8166Yxw.MarketMotionStudio_fzc58jprbah1t!App"
EXE = "MarketMotionStudio.exe"
OUTROOT = r"D:\software\MarketMotionStudio\artifacts\store-screens"
LOG = os.path.join(OUTROOT, "runlog.txt")
SMOKE = "--smoke" in sys.argv

# 搜索模式下往 InstrumentSearch 里输入的查询串（美股，标普500 ETF）。
# 注意：腾讯美股数据未做拆股调整（AAPL 2014 年 7拆1 前后 645.57→102.25 断崖），
# 长区间截图必须挑无拆股的标的——SPY 近 13 年无拆股，收益曲线干净。
SEARCH_QUERY = "SPY"

# (语言 tag, 重启后的窗口标题, 语言下拉条目文本, 设置导航项名称(仅日志用),
#  市场索引 0=A股 1=港股 2=美股, 标的模式 preset=点预置 / search=搜索)
LANGS = [
    ("zh-Hans", "行情指标动画工作室", "简体中文", "设置", 0, "preset"),
    ("zh-Hant", "行情指標動畫工作室", "繁體中文", "設定", 1, "preset"),
    ("en-US", "Market Motion Studio", "English", "Settings", 2, "search"),
    ("ja", "Market Motion Studio", "日本語", "設定", 2, "search"),
    ("ko", "Market Motion Studio", "한국어", "설정", 2, "search"),
    ("de", "Market Motion Studio", "Deutsch", "Einstellungen", 2, "search"),
    ("es", "Market Motion Studio", "Español", "Configuración", 2, "search"),
    ("fr", "Market Motion Studio", "Français", "Paramètres", 2, "search"),
    ("it", "Market Motion Studio", "Italiano", "Impostazioni", 2, "search"),
    ("pl", "Market Motion Studio", "Polski", "Ustawienia", 2, "search"),
    ("pt-BR", "Market Motion Studio", "Português (Brasil)", "Configurações", 2, "search"),
    ("cs", "Market Motion Studio", "Čeština", "Nastavení", 2, "search"),
    ("tr", "Market Motion Studio", "Türkçe", "Ayarlar", 2, "search"),
    ("ru", "Market Motion Studio", "Русский", "Параметры", 2, "search"),
]

# 设置导航项的全部本地化名称。页脚项 AutomationId 为空只能按名称找，而找的
# 时刻界面还停留在上一轮语言，所以把 14 种全部列为兜底（set 去重）。
SETTINGS_NAMES = list(dict.fromkeys([
    "设置", "設定", "Settings", "Nastavení", "Einstellungen", "Configuración",
    "Paramètres", "Impostazioni", "Ustawienia", "Configurações", "Ayarlar",
    "Параметры", "설정",
]))

# (导航项 AutomationId, 输出文件名, 预置标的按钮名；FIRST=点第一个预置。
# 港股/美股市场下 NavMarketTurnover 不存在，脚本按「未找到」自然跳过。)
PAGES = [
    ("NavMarketTurnover", "01-market-turnover", None),
    ("NavSectorRace", "02-sector-race", None),
    ("NavGainCalendar", "03-gain-calendar", "FIRST"),
    ("NavMatrix", "04-monthly-matrix", None),
    ("NavDcaPlan", "05-dca-plan", "FIRST"),
    ("NavPosition", "06-position", "FIRST"),
    ("NavCandle", "07-candle", "FIRST"),
    ("NavMarketCap", "08-market-cap", None),
    # 债市固收是固定清单的榜，没有预置标的按钮 → 传 None，与板块竞速、市值榜一样。
    # 它是月线页、不受市场设置管辖，三个市场下都在，不会被当成「未找到」跳过，所以每语言
    # 都多出一张（历史上 zh-hans 八张、其余十三种各七张，差的那一张是只在 A股 存在的
    # 成交额页 —— 那一轮跑完市场被留在港股）。
    ("NavBondRace", "09-bond-race", None),
]

if SMOKE:
    LANGS = LANGS[:1]
    PAGES = PAGES[:1]

# --pages=01-market-turnover,06-position ：只重截指定页（语言仍全跑）
# --langs=zh-Hans,en-US ：只跑指定语言
_pages_arg = next((a.split("=", 1)[1].split(",")
                   for a in sys.argv[1:] if a.startswith("--pages=")), None)
if _pages_arg:
    PAGES = [p for p in PAGES if p[1] in _pages_arg]
_langs_arg = next((a.split("=", 1)[1].split(",")
                   for a in sys.argv[1:] if a.startswith("--langs=")), None)
if _langs_arg:
    LANGS = [l for l in LANGS if l[0] in _langs_arg]

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

    先试 AutomationId（万一将来补上），再试给定的名称，最后兜底尝试全部
    语言的设置项名称——启动语言未知时也能找到入口。
    """
    nav = byid(win, "NavSettings")
    if nav is not None:
        return nav
    nav = find(lambda c: c.ControlTypeName == "ListItemControl"
               and c.Name == settings_name, win)
    if nav is not None:
        return nav
    for fallback in SETTINGS_NAMES:
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


def combo_select_index(combo, index, timeout=8):
    """展开下拉，按序号选择第 index 项。

    市场下拉的条目文本是本地化的，但顺序固定等于 Markets.All
    （0=A股 1=港股 2=美股），按序号选就不依赖当前界面语言。
    """
    p = pat(combo, auto.PatternId.ExpandCollapsePattern)
    if p is None:
        return False
    try:
        p.Expand()
    except Exception:
        return False
    deadline = time.time() + timeout
    while time.time() < deadline:
        items = [c for c in combo.GetChildren()
                 if c.ControlTypeName == "ListItemControl"]
        if len(items) > index:
            sp = pat(items[index], auto.PatternId.SelectionItemPattern)
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


def collect_items(win):
    """窗口里全部 ListItemControl（导航项 + 可能出现的建议列表项）。"""
    items = []

    def walk(c, depth=0):
        if depth > 30:
            return
        try:
            if c.ControlTypeName == "ListItemControl":
                items.append(c)
        except Exception:
            pass
        try:
            for ch in c.GetChildren():
                walk(ch, depth + 1)
        except Exception:
            pass

    walk(win)
    return items


def item_key(c):
    r = c.BoundingRectangle
    return (c.Name, r.left, r.top)


def search_instrument(win, query, timeout=12, attempts=2):
    """Search `query`, then retry once from an empty box if nothing came back.

    Retried, because a suggestion list that never opened looks exactly like a query
    that has no matches — and the honest cause is usually that the previous page's
    fetch was still running when the keys went in. The retry clears the box first:
    typing into it again appends, and "SPYSPY" finds nothing either.
    """
    for attempt in range(attempts):
        if _search_once(win, query, timeout):
            return True

        if attempt + 1 < attempts:
            say("    第 %d 次没出建议，清空重来" % (attempt + 1))

    return False


def _search_once(win, query, timeout=12):
    """往 InstrumentSearch 键入查询串，从弹出的建议列表里点第一项。

    程序化 SetValue 不触发 UserInput 的 TextChanged（建议列表不弹），必须
    真键盘输入。建议项通过「输入前后 ListItemControl 快照的差集」识别——
    导航项在两侧都在，新增的就是建议列表。
    """
    box = byid(win, "InstrumentSearch")
    if box is None:
        say("    InstrumentSearch 未找到")
        return False
    before = {item_key(c) for c in collect_items(win)}

    # 焦点落到 AutoSuggestBox 内部的 Edit 上再敲键盘
    edit = find(lambda c: c.ControlTypeName == "EditControl", box) or box
    try:
        edit.SetFocus()
        time.sleep(0.4)
        # 先清空：重试时框里还留着上一次的串，再敲一遍就是 "SPYSPY"。
        auto.SendKeys("{Ctrl}a{Delete}", waitTime=0.3)
        time.sleep(0.3)
        auto.SendKeys(query, interval=0.06)
    except Exception as e:
        say("    SendKeys 失败: %r" % e)
        return False

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(1.0)
        new = [c for c in collect_items(win) if item_key(c) not in before]
        if new:
            say("    建议列表出现（%d 项），首项 %r" % (len(new), new[0].Name))
            return invoke_click(new[0])
    say("    等待建议列表超时（%ds）" % timeout)
    return False


def wait_play_enabled(win, timeout=240):
    """获取数据的完成信号：播放按钮从禁用变可用（语言无关）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        pb = byid(win, "PlayButton")
        if pb is not None and pb.IsEnabled:
            return True
        time.sleep(2)
    return False


def scrub(win, ratio=1.0):
    """把进度条拖到指定比例；默认 1.0 = 动画最后一帧（含收尾卡）。"""
    sc = byid(win, "Scrub")
    if sc is None:
        return False
    p = pat(sc, auto.PatternId.RangeValuePattern)
    if p is None:
        return False
    try:
        lo, hi = p.Minimum, p.Maximum
        p.SetValue(lo + (hi - lo) * ratio)
        time.sleep(1.0)
        return True
    except Exception:
        return False


def maximize_window(win):
    """把窗口最大化——商店截图要的是「应用全屏」的观感，不是缩在角落的窗口。

    uiautomation 的 Control 没有 Maximize()，走 WindowPattern；WinUI 3 的窗口
    有时不给这个 pattern，再退回 ShowWindow(SW_MAXIMIZE)。两条路都失败才
    退回按尺寸摆放（≥1366×768 是商店硬下限）。
    """
    wp = pat(win, auto.PatternId.WindowPattern)
    if wp is not None:
        try:
            wp.SetWindowVisualState(auto.WindowVisualState.Maximized)
            time.sleep(1.2)
            return
        except Exception as e:
            say("  WindowPattern 最大化失败: %r" % e)

    try:
        import ctypes

        hwnd = win.NativeWindowHandle
        if hwnd and ctypes.windll.user32.ShowWindow(hwnd, 3):  # SW_MAXIMIZE
            time.sleep(1.2)
            return
    except Exception as e:
        say("  ShowWindow 最大化失败: %r" % e)

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


def log_window_rect(win, when):
    """记下窗口矩形，好确认截图真的是全屏尺寸而不是上一次的大小。"""
    try:
        r = win.BoundingRectangle
        say("  窗口%s: %dx%d @(%d,%d)" % (when, r.width(), r.height(), r.left, r.top))
    except Exception:
        pass


def ink_ratio(path):
    """画面上「有墨」的像素占比——用来认出一帧空白图。

    为什么需要：取数完成的信号是播放按钮变可用，而预览的重绘在它之后才发生。
    抓到中间态的画面是**浅色背景 + 几乎没有别的东西**，而日志对此一无所知：
    「数据就绪」和「截图成功」两行照常打印，九十九张里唯独一张白板。有内容的图
    暗像素占 13% 上下，空白的那张 0.6%。
    """
    if Image is None:
        return 1.0

    with Image.open(path) as im:
        raw = im.convert("RGB").resize((im.width // 4, im.height // 4)).tobytes()

    dark = sum(1 for i in range(0, len(raw), 3)
               if (raw[i] + raw[i + 1] + raw[i + 2]) / 3 < 128)
    return dark / (len(raw) / 3)


def capture(win, path, min_ink=0.01, attempts=3):
    """截图，并检查那一帧不是白板；是就等一会儿再抓。"""
    ratio = 0.0

    for attempt in range(attempts):
        try:
            win.SetFocus()
            time.sleep(1)
        except Exception:
            pass

        ok = win.CaptureToImage(path)
        time.sleep(0.5)

        if not (ok and os.path.exists(path)):
            continue

        ratio = ink_ratio(path)

        if ratio >= min_ink:
            return True

        say("    截图几乎是空白（墨色 %.3f），等 2s 重抓" % ratio)
        time.sleep(2)

    say("    !! 连抓 %d 次都近乎空白（墨色 %.3f）" % (attempts, ratio))
    return os.path.exists(path)


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

for tag, title, combo_label, settings_name, market_idx, mode in LANGS:
    say("===== %s（市场=%d 模式=%s）=====" % (tag, market_idx, mode))
    kill_app()
    launch()
    win = wait_window()
    if win is None:
        say("  首次启动：窗口未出现，跳过该语言")
        continue
    time.sleep(2)
    maximize_window(win)
    log_window_rect(win, "启动后")

    # --- 切语言 + 切市场：设置页两项都选好 → 一次重启同时生效 ---
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
    say("  已选语言 %r" % combo_label)
    mcombo = byid(win, "MarketCombo")
    if mcombo is None:
        say("  MarketCombo 未找到（市场维持原值）")
    elif combo_select_index(mcombo, market_idx):
        say("  已选市场索引 %d" % market_idx)
    else:
        say("  未能选中市场索引 %d（市场维持原值）" % market_idx)

    kill_app()
    launch()
    win = wait_window()
    if win is None:
        say("  重启后窗口未出现，跳过该语言")
        continue
    say("  重启后窗口标题: %r（期望 %r）%s" %
        (win.Name, title, "OK" if win.Name == title else "!! 不一致"))
    time.sleep(2)
    maximize_window(win)
    log_window_rect(win, "重启后")

    outdir = os.path.join(OUTROOT, tag)
    os.makedirs(outdir, exist_ok=True)

    # --- 逐页：导航 → 选标的 → 获取 → 拖到终帧 → 截图 ---
    for nav_id, fname, preset in PAGES:
        say("  --- %s ---" % fname)
        nav = byid(win, nav_id)
        if nav is None:
            say("    %s 未找到（该市场无此页），跳过" % nav_id)
            continue
        invoke_click(nav)
        time.sleep(2)

        fb = byid(win, "FetchButton")
        if fb is None:
            say("    FetchButton 未找到")
            continue

        # search 模式：有搜索框的页面一律搜索选定（FetchButton 即使因默认
        # 标的可用也照样搜，截图要展示的是搜索动作的结果）。
        if mode == "search" and byid(win, "InstrumentSearch") is not None:
            if search_instrument(win, SEARCH_QUERY):
                say("    已搜索选定 %r" % SEARCH_QUERY)
                time.sleep(1.0)
                fb = byid(win, "FetchButton")
            else:
                say("    搜索失败，退回默认标的")

        if fb is not None and not fb.IsEnabled and mode == "preset" and preset:
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

        scrub(win, 1.0)
        path = os.path.join(outdir, fname + ".png")
        if capture(win, path):
            say("    截图(终帧): %s" % path)
        else:
            say("    截图失败: %s" % path)

# ---- 收尾：恢复简体中文 + A股，别把机器留在俄语/美股状态 --------------------------
say("===== 收尾：恢复 zh-Hans + A股 =====")
kill_app()
launch()
win = wait_window()
if win is not None:
    nav = find_settings_nav(win, "设置")
    if nav is not None:
        invoke_click(nav)
        time.sleep(2)
        combo = byid(win, "LanguageCombo")
        if combo is not None:
            combo_select(combo, "简体中文")
        mcombo = byid(win, "MarketCombo")
        if mcombo is not None:
            combo_select_index(mcombo, 0)
kill_app()

say("ALL DONE")
