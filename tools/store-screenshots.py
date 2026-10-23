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
  python tools\store-screenshots.py --crypto    # 只截加密十一页（市场选第四格）

窗口**最大化后再抓**（商店要的是「应用全屏」的观感，不是缩在屏幕中间的窗口）；
画面一律停在动画的**最后一帧**。

产出：artifacts\store-screens\<语言>\<序号>-<页面>.png，逐行写 runlog.txt。
商店只要求截图 ≥1366×768；本屏 1920×1080，最大化后是 1920×1080（含标题栏）。
跑之前确认主题是浅色——旧图库是浅色主题，深浅混着上传不好看。
"""
import os
import re
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
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKETS = os.path.join(ROOT, "src", "MarketMotionStudio", "Market", "Markets.cs")

# 各页「一键预置」那一排用的是市场档案里的哪张清单（照 Pages/*.xaml.cs 填 Presets 的那一行）。
PRESET_PROPERTY = {
    "03-gain-calendar": "BroadIndices",
    "05-dca-plan": "DcaInstruments",
    "06-position": "PositionInstruments",
    "07-candle": "CandleInstruments",
}

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

# 加密货币那十一页只在市场切成加密货币时才在导航里 —— 选它时股票页整组 Remove，
# 反过来也一样。所以它们不可能和上面这批同一次跑出来，得单独一趟。
#
# 顺序照导航里的顺序（`CryptoPages`），文件名里的序号接着上面排。
#
# 第四项是币种策略：`crypto_set_coins` 把开关摆成「恰好这一组」。
#   * 矩阵、K 线一类单币页 —— 只留 BTC（跟 1.0.17 那批六页同一个口径）；
#   * 比较、涨跌、占比 —— 六个主流币一起上：占比页单币恒为 100%，比较页单币
#     只有一条线，都不是给人看的画面。六个正好是 CryptoPicker 的上限。
#   * 市值榜不给人挑（问 CoinGecko 的前十五名）—— None，页面上根本没有开关。
CRYPTO_PAGES = [
    ("NavCryptoCandle", "10-crypto-candle", None, ("BTC",)),
    ("NavCryptoDca", "11-crypto-dca", None, ("BTC",)),
    ("NavCryptoPosition", "12-crypto-position", None, ("BTC",)),
    ("NavCryptoCalendar", "13-crypto-calendar", None, ("BTC",)),
    ("NavCryptoCapHistory", "14-crypto-caphistory", None, ("BTC",)),
    ("NavCryptoMarketCap", "15-crypto-marketcap", None, None),
    ("NavCryptoMatrix", "16-crypto-monthly", None, ("BTC",)),
    ("NavCryptoCompare", "17-crypto-compare", None,
     ("BTC", "ETH", "SOL", "XRP", "DOGE", "ADA")),
    ("NavCryptoMovers", "18-crypto-movers", None,
     ("BTC", "ETH", "SOL", "XRP", "DOGE", "ADA")),
    ("NavCryptoDominance", "19-crypto-dominance", None,
     ("BTC", "ETH", "SOL", "XRP", "DOGE", "ADA")),
    ("NavCryptoAnnual", "20-crypto-annual", None, ("BTC",)),
]
# --crypto：只截加密十一页，市场选第四格（`MarketId.Crypto`）。
CRYPTO = "--crypto" in sys.argv

if CRYPTO:
    PAGES = CRYPTO_PAGES

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


def preset_codes(market_idx, page):
    """这一页在给定市场下，预置那一排的标的代码（源码里的顺序）。

    从 Markets.cs 读，不在这里抄一份：清单是会改的，抄一份就等于有了第二个事实源，
    改了那边这边还指着旧代码，点下去的是「没找到」而日志只说一句没点着。

    读不到就返回空表（例如 A股 的 BroadIndices 指向 MonthlySeries.BroadIndices，
    那张清单不在这个文件里）→ 点不成，退回原来的行为。
    """
    text = open(MARKETS, encoding="utf-8").read()
    lists = {name: re.findall(r'new\(\s*"([^"]+)"', body)
             for name, body in re.findall(
                 r"public static readonly RaceEntry\[\] (\w+)\s*=\s*\[(.*?)\];", text, re.S)}

    blocks = re.split(r"\n        new\(\n", text[text.index("MarketProfile[] Profiles"):])
    blocks = [b for b in blocks if "MarketId." in b]

    if market_idx >= len(blocks):
        return []

    wanted = re.search(PRESET_PROPERTY[page] + r":\s*(\w+),", blocks[market_idx])
    return lists.get(wanted.group(1), []) if wanted else []


def click_preset(win, name, market_idx=0, page=None):
    """点这一页「一键预置」那一排的第一个标的。

    **不能按 Presets 这个容器找** —— 它是 ItemsControl，只有 x:Name 没有 AutomationId，
    byid 找不到它，于是这个函数的头一个版本每一次都返回「没找到」，而日志里只字不提
    （2026-10-10：zh-Hant 的定投计划页连着两轮取数超时，就是因为这一路一直在空转）。

    按钮自己是有的：DataTemplate 把 AutomationId 绑成了标的代码（Pages/DcaPlanPage.xaml），
    而**代码与语言无关** —— 按钮上的字是本地化的名字，认名字等于给十四种语言各抄一遍。
    """
    codes = preset_codes(market_idx, page) if page in PRESET_PROPERTY else []

    if name != "FIRST" or not codes:
        return False

    first = codes[0]
    b = find(lambda c: c.ControlTypeName == "ButtonControl" and c.AutomationId == first, win)

    if b is None:
        return False

    return invoke_click(b)


def crypto_chips(win):
    """币种开关那一排（AutomationId = "Coin" + 代码，代码与语言无关）。

    `CoinCombo` 也以 Coin 开头（涨跌日历/市值历程两页挑单个币的下拉），拿它当开关去点
    会把下拉展开 —— 所以按「不是 Combo 结尾」把它挡掉。
    """
    out = []

    def walk(c, depth=0):
        if depth > 25:
            return
        try:
            aid = c.AutomationId or ""
        except Exception:
            aid = ""
        if aid.startswith("Coin") and not aid.endswith("Combo"):
            out.append(c)
        try:
            for ch in c.GetChildren():
                walk(ch, depth + 1)
        except Exception:
            pass

    walk(win)
    return out


def crypto_only_btc(win, timeout=25):
    """把币种开关摆成「只有 BTC」。

    **为什么不能只保证 BTC 是开的。** 三页都把「上次选的」存了下来，上一轮（或上一趟判据
    中途退出）可能留下两只。两只时 K 线与定投走的是**多标的**那一支：状态行说「2 个币种 ·
    N 天」，画面也不是截图要给人看的那个样子。与 verify-crypto 的 `only_coin` 同一个道理：
    **起点不假设**。

    **开关先读 `TogglePattern`。** 默认就勾着，盲点一次等于点掉，取数就报「请至少勾选一个
    币种」—— 看着像源坏了。
    """
    deadline = time.time() + timeout

    while time.time() < deadline:
        chips = crypto_chips(win)

        if not chips:
            return False  # 这一页没有币种开关（市值榜是问前 15 名，不给人挑）

        settled = True

        for chip in chips:
            want = chip.AutomationId == "CoinBTC"
            state = None

            try:
                pattern = chip.GetPattern(auto.PatternId.TogglePattern)

                if pattern is not None:
                    state = pattern.ToggleState
            except Exception:
                state = None

            if state is None:
                continue

            if (state == auto.ToggleState.On) != want:
                invoke_click(chip)
                settled = False

        if settled:
            return True

        time.sleep(0.5)

    return False


def crypto_set_coins(win, codes, timeout=25):
    """把币种开关摆成「恰好 codes 这一组」。

    `crypto_only_btc` 的一般化：矩阵页给单币，比较/涨跌/占比给六个主流币 —— 占比页单币
    恒为 100%，比较页单币只有一条线，都不是截图要给人看的画面。开关名 `Coin` + 代码
    （与语言无关），先读 `TogglePattern` 再动手，与 only_btc 同一个道理：**起点不假设**。
    """
    want_set = set(codes)
    deadline = time.time() + timeout

    while time.time() < deadline:
        chips = crypto_chips(win)

        if not chips:
            return False  # 这一页没有币种开关（市值榜不给人挑）

        settled = True

        for chip in chips:
            code = chip.AutomationId[len("Coin"):]
            want = code in want_set
            state = None

            try:
                pattern = chip.GetPattern(auto.PatternId.TogglePattern)

                if pattern is not None:
                    state = pattern.ToggleState
            except Exception:
                state = None

            if state is None:
                continue

            if (state == auto.ToggleState.On) != want:
                invoke_click(chip)
                settled = False

        if settled:
            return True

        time.sleep(0.5)

    return False


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


def picture_size(path):
    """图有多大 —— 抓完之后第一件要问的事。"""
    if Image is None:
        return None

    with Image.open(path) as im:
        return im.size


def frame_share(path):
    """整幅图里"很暗"的像素占多少。

    9:16 预览帧是一整块深色矩形，占满窗的一成多；而桌面上根本没有这么一块 —— 实测真图
    0.122~0.128，抓成整屏（别的应用在前台）的那张 **0.004**。这两种量差着三十倍，阈值取
    在中间任何地方都行。
    """
    if Image is None:
        return 1.0

    with Image.open(path) as im:
        grey = im.convert("L").resize((im.width // 2, im.height // 2))
        pixels = list(grey.getdata())

    return sum(1 for v in pixels if v < DARK) / len(pixels)


def visible_size(win):
    """窗口在屏幕上真正看得见的那块有多大。

    最大化时窗口矩形比屏幕还大 9 px 一圈（实测 1938x1038 @(-9,-9)），而抓到的正是可见的
    1920x1020 —— 所以断言要拿矩形与屏幕的交集去比，不能拿矩形自己比。
    """
    try:
        rect = win.BoundingRectangle

        try:
            screen_w, screen_h = auto.GetScreenSize()
        except Exception:
            screen_w, screen_h = 1920, 1080

        wide = min(rect.right, screen_w) - max(rect.left, 0)
        high = min(rect.bottom, screen_h) - max(rect.top, 0)

        # 窗口最小化 / 刚被重启还没画出来时，UIA 会老老实实交出一个 0x0 的矩形（2026-10-11
        # 在 tr 那一趟撞上，日志里「窗口可见那块是 0x0」）。它是**没读到**，不是「窗口就是
        # 这么大」—— 当成尺寸不合去比，只会把三次机会全耗在重试同一件事上。
        return (wide, high) if wide > 0 and high > 0 else None
    except Exception:
        return None


def focus_window(win, maximize=True):
    """把窗口抬回前台（必要时最大化）。

    **为什么非做不可。** 别的应用抢到前台、把窗口盖住之后，`CaptureToImage` 会落回整屏
    抓取 —— 拿到的是那个应用和桌面。2026-10-11 实测两次：ArcGIS 的设置窗在前台，zh-Hans
    的市值历程与市值榜两张图都成了它，而日志里「数据就绪 / 截图(终帧)」两行照常打印，
    墨色判据也照过（它只问"有没有内容"）。
    """
    pattern = pat(win, auto.PatternId.WindowPattern)

    if maximize and pattern is not None:
        try:
            if pattern.WindowVisualState != auto.WindowVisualState.Maximized:
                pattern.SetWindowVisualState(auto.WindowVisualState.Maximized)
                time.sleep(1.2)
        except Exception:
            pass

    try:
        win.SetFocus()
        time.sleep(1)
    except Exception:
        pass


# 「很暗」的门槛（亮度 0~255）：预览帧那块深色矩形远低于它，浅色界面远高于它。
DARK = 60

# 整幅图里暗像素低于这个占比 = 画面里没有预览帧（见 capture 的说明）。真图 0.12 上下。
FRAME_DARK = 0.05

# 尺寸判据的容差（px）。**不能用等号**：UIA 给的窗口矩形是含边框溢出那圈的，最大化时实测
# 1938x1029 @(-9,-9)，而抓到的正是屏幕上可见的 1920x1020 —— 差 9 px。整屏抓取则要差 60 px
# （1920x1080 对 1920x1020），容差取 24 才既放得过边框、又挡得住整屏。
SIZE_SLACK = 24


def capture(win, path, min_ink=0.01, attempts=3):
    """截图，并检查那一帧**就是这个应用**、而且不是白板；不对就等一会儿再抓。

    三条判据，各挡一种病：

      * 尺寸 —— 抓成整屏时是 1920x1080，而窗口只有 1920x1020；
      * 墨色 —— 抓在重绘中间态时几乎全白（0.006）；
      * 暗色 —— 画面里没有那块 9:16 的深色预览帧，说明窗口被别的东西盖着。

    只有第二条是原来就有的。前两条对应的是「图里的东西不是这一页」——它比白板更难发现，
    因为一眼看上去"有内容"。
    """
    want = visible_size(win)
    ratio = 0.0
    share = 0.0
    size = None

    for attempt in range(attempts):
        focus_window(win)

        # 抓图这一步会抛 COMError（`-2147220991 事件无法调用任何订户`）：窗口正在被销毁或
        # 重建时 UIA 拿不到矩形。它**不是**这一页坏了 —— 不接住，整趟 14 语言 × 6 页就断在
        # 这里，前面四十分钟白跑（2026-10-11 实测：tr 那一趟跑完第 1 张就崩了）。
        try:
            ok = win.CaptureToImage(path)
        except Exception as exc:
            say("    抓图抛异常（%s），等 3s 重抓" % str(exc)[:60])
            ok = False

        time.sleep(0.5)

        if not (ok and os.path.exists(path)):
            continue

        size = picture_size(path)
        ratio = ink_ratio(path)
        share = frame_share(path)

        if want is not None and any(abs(a - b) > SIZE_SLACK
                                    for a, b in zip(size, want)):
            say("    抓到的是 %s，窗口可见那块是 %s（差得超过 %d px）—— 整屏抓取，重来"
                % ("x".join(map(str, size)) if size else "?", "x".join(map(str, want)),
                   SIZE_SLACK))
            time.sleep(1.5)
            continue

        if ratio < min_ink:
            say("    截图几乎是空白（墨色 %.3f），等 2s 重抓" % ratio)
            time.sleep(2)
            continue

        if share < FRAME_DARK:
            say("    画面里没有那块预览帧（暗色 %.3f，真图 0.12 上下）—— 被别的窗口盖住了，重抓"
                % share)
            time.sleep(2)
            continue

        return True

    say("    !! 连抓 %d 次都不对（尺寸 %s，墨色 %.3f，暗色 %.3f）"
        % (attempts, "x".join(map(str, size)) if size else "?", ratio, share))
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
    # 加密那一趟：市场一律第四格（MarketId.Crypto），不管这一语言平时给股票页选的是哪个市场。
    if CRYPTO:
        market_idx = 3

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
    elif combo_select_index(mcombo, market_idx,
                            # 第四格是探测回来之后才补上的：每源最多问两次、每次一条二十秒的
                            # 绳子。按八秒等，会把「还在问」读成「取不到币价」。
                            timeout=(90 if CRYPTO else 8)):
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
    for entry in PAGES:
        nav_id, fname = entry[0], entry[1]
        preset = entry[2] if len(entry) > 2 else None
        coins = entry[3] if len(entry) > 3 else None
        say("  --- %s ---" % fname)
        nav = byid(win, nav_id)
        if nav is None:
            say("    %s 未找到（该市场无此页），跳过" % nav_id)
            continue
        invoke_click(nav)
        time.sleep(2)

        if CRYPTO:
            if coins:
                say("    币种摆成 %s：%s"
                    % ("+".join(coins),
                       "是" if crypto_set_coins(win, coins) else "这一页没有币种开关"))
            else:
                say("    这一页不挑币（榜单/下拉页），维持现状")
            time.sleep(1.0)

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
            if click_preset(win, preset, market_idx, fname):
                say("    已点预置标的 %r" % preset)
                time.sleep(1.5)
                fb = byid(win, "FetchButton")
            else:
                say("    预置标的 %r 未找到" % preset)

        if fb is None or not fb.IsEnabled:
            say("    获取按钮不可用，跳过该页")
            continue

        invoke_click(fb)
        ok = wait_play_enabled(win, 15)
        retried = False

        # 15 秒还没就绪，且这一页的取数**压根没开跑** —— 判据是 FetchButton 一直可用：
        # 真去取数时 RunAsync 头一件事就是把它置灰，而取数被拒（例如自选清单里没有当前
        # 市场的标的，DcaNoMarketPicks / PositionNoMarketPicks）是 ShowStatus 之后直接
        # return，按钮从头到尾没暗过。这是唯一一个与语言无关的信号：状态条上的字是本地化
        # 的，读它的文字等于给十四种语言各写一条断言。
        #
        # 这时点一下预置标的把它加进来再取一次。Watch.Include 只动这一页的勾选，不写清单
        # 本身，所以不会把这台机器的自选清单改掉。第一次就成了的语言走不到这里。
        if not ok and preset and mode == "preset":
            again = byid(win, "FetchButton")

            if again is not None and again.IsEnabled and click_preset(win, preset, market_idx, fname):
                retried = True
                say("    取数没开跑，点预置标的 %r 后重试" % preset)
                time.sleep(1.5)

                # 预置标的的点击自己就会发起取数（Include 之后直接 Fetch），按钮已经暗了就
                # 别再点第二下 —— 那会把它当成取消。
                again = byid(win, "FetchButton")
                if again is not None and again.IsEnabled:
                    invoke_click(again)

        if not ok:
            ok = wait_play_enabled(win)

        if ok:
            say("    数据就绪" if not retried else "    数据就绪（点预置标的后）")
        else:
            # 取数始终没成，就**别把这一屏留下来**。它看上去和真图一模一样 —— 画布、
            # 标题、状态条、参数面板都在，只是画布里是空的，状态条上多一行「两个源都
            # 没答」。三条抓图自检全过（尺寸对、有墨色、那块预览帧也在），因为病不在
            # 这里。2026-10-11 tr 那一趟撞上：Yahoo 与 CoinGecko 同时不通，五张图全都
            # 是这屏，而日志里只有一行「等待数据超时」，看图才看得出来。
            say("    !! 取数始终没成，这一张不留（网络恢复后重跑这一门语言）")
            stale = os.path.join(outdir, fname + ".png")

            if os.path.exists(stale):
                os.remove(stale)

            continue

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
