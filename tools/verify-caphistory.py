# -*- coding: utf-8 -*-
r"""真机跑一遍「市值历程」这一页。

这一页的数值是**算出来的**，不是行情源给的，所以只验「页面在、控件在」等于没验：
京东方那种股本台阶、茅台那种从不算错的末值，才是这一页站得住的证据。于是这里验三件事：

1. 导航项在，页面上该有的控件都在；
2. 取数回报的期数落在预期的量级（默认两年 ≈ 480 个交易日）—— 这一条才证明取的是
   两年而不是一个月；
3. 期末流通市值与快照对得上（茅台 2026-10-06：算出 15,724，快照 15,734）—— 数量级差
   一位就说明股本的手/股换算错了，而那个错误在画面上只表现为「线看着有点低」。

第四件是**这条线长大时会不会动**。这一笔画的是曲线，而曲线最右端那几个点共用同一套
节奏：柱子可以从轴上长出来——它占的那一格本身就是标记，半根柱子还是柱子；曲线不行。
曾经的写法把「还没长完的点」按自己的进度乘一下就加进点列，于是刚出生的点贴在底边、
它左边那个已完成的点却在全高，线在两个点之间从全高摔到轴上：面板右边一道竖直落线，
底下再拖一段贴边的横线，一眼看去像数据掉了个坑。（同一份写法在 `StockDualRenderer`
的成交率面板上也在；`DcaRenderer` / `PositionRenderer` 不是——它们从相邻那天插值过去，
跨度只有一天的涨跌。）

这一条**只有播放途中才现形**：末帧是全对的，跑完再截图等于没验。所以这里不用碰运气抢
拍，而是把搓擦条定到两个不同的进度上各取一帧（`Seek` 会先停住播放再把画面放到那个位
置），然后要求**早那一帧已经画出的每一列，在晚那一帧里还在同一行**——长大的线不应该
移动已经画过的点。

这条判决里没有一个要猜的数：它不问「落线有多长」，只问「同一个 x 上的描线有没有换过
行」，所以早年的深谷贴着轴也照样判得过来，不需要给「算不算动了」拍一个像素阈值。

第五件是**曲线末端那颗胶囊**——名字加当下的数，骑在线头上，画在曲线自己的颜色里。于是它在像素上
就是「又一段同色的东西」，而它偏偏是跟着线头走的，正是上面那条「早先画出的点没有挪动过」会误判
成曲线坏了的东西。所以上面只在**曲线自己那一段**里数：曲线永远起于绘图区左缘、胶囊永远在其右，
取最左那一段就摘干净了。反过来也用得上——胶囊的下边是一条长长的水平线，而一条曲线在几百列里绝不
可能平，「平不平」就是认出胶囊的判据（`flat_share`）；单只那两块面板、多标的每条线，各要有一颗。

对账要对**快照的流通市值**（`qt.gtimg.cn` 的第 44 个字段），不是总市值（第 45 个）：这一页
还原的是流通股本。茅台两个字段都是 15,734，所以在这里对哪一个都一样；换成工商银行就会差
32%（22,324 / 29,510，它的 H 股与限售股不在流通股本里），拿总市值对账会得出「算法错了」
的结论，而错的其实是参照值。

只在应用里跑不算验证完：导出那一条链路（封面 / MP4）另有自己的历史，没跑就说「未导出」。

标的现在是**八个页面共用那份自选清单**多选的，多标的时只留市值一块面板、每条线在末端标出
名字，纵轴多一个「归一到 100」的读法。这三件也都是画面看着合理就算过了的事，所以各自送到能
量出来的地方去验：

- 只留一块面板 —— 单只那帧拿来做反面参照（市值与股价两条线隔着一块面板的空隙，行区间重
  叠为负），多标的那一帧要求两条线共用同一个行区间。只看后者，会把「这几只刚好画得近」
  当成「股价那块让出去了」。
- 并集日期轴 —— 先单取上市最晚那一只记下它自己的起点与天数，再两只一起取，要求起点更早、
  总数更多。取交集的话两只一起那一次会砍到晚那一只上市以来的时间。
- 刻度开关 —— 绝对值下两条线各自起在自己那个大小上（两家差好几倍，差出几十行），归一后都
  从 100 起于同一行。只验「归一后挨在一起」不够，两条线本来就可能凑巧同高。

最后顺手验「第七家是拒绝而不是悄悄画六条」：悄悄画六条是最像成功的一种失败 —— 画面是完全合
理的六条线，没人会想到清单上还留着第七家，所以这一条单独成一节。

用法：python tools\verify-caphistory.py
"""
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import uiautomation as auto

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import winui  # noqa: E402

auto.uiautomation.SetGlobalSearchTimeout(5)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts")

STRINGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "src", "MarketMotionStudio", "Strings")

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "MarketMotionStudio")

PAGE_XAML = os.path.join(SRC, "Pages", "CapHistoryPage.xaml")
PAGE_CODE = os.path.join(SRC, "Pages", "CapHistoryPage.xaml.cs")
RENDER = os.path.join(SRC, "Render", "CapHistoryRenderer.cs")

PASSED = []
FAILED = []

# `Palette.Tracks`：一条线一个颜色，按它在这幅画面上的位置取，不是按代码散列 —— 所以这几个
# 十六进制值对着 `Render/Palette.cs` 就能复核。这里判的是**色相**而不是那个数本身：抗锯齿与
# 半透明的叠加会把 RGB 挪动几十，而色相挪不动。
IS_TRACK_0 = lambda r, g, b: r >= 130 and (r - g) >= 55 and abs(g - b) <= 45        # #FF6B6B
IS_TRACK_1 = lambda r, g, b: b >= 120 and g >= 110 and (g - r) >= 60 and (b - r) >= 60  # #06B6D4

# 行区间重叠不再当作「一块面板」的判据（阈值会随选中的两家漂），改作两帧相对地看 —— 见
# `share_panel` 的注释，以及它在 `main` 里与单只那一帧配成的那一对。

# 胶囊左右两端是圆角，那几列不「平」，所以不在 `flat_runs` 认出胶囊的那一段里（量出来：胶囊
# 76 列宽、平段 68 列，两端各让掉 4 列）。用平段当胶囊时得往左多让出这么些列，否则圆角那几列
# 会从侧门回到曲线那一档 —— 胶囊离曲线只有 5 列，而 `line_bands` 关的是 8 列的缝。
CAPSULE_RIM = 8

# 一条平段要平到多少列才算一颗胶囊。见 `flat_runs`：胶囊 59–82 列，曲线最平只到 23 列。
CAPSULE_FLAT = 40

# 三家标的，各归一件事：
#
#   MAOTAI   单只那一段用它。选它的理由是它的流通市值与总市值恰好相等，所以对账那条断言
#            不必替这两种口径的差别操心。
#   LATE / EARLY
#            多标的那一段用它俩证「日期轴是并集」，也用它俩证「两种刻度的确换了刻度」。后一件
#            要求两家在各自的起点上大小差得远：中国移动 2022-01 上市时八百多亿，招商银行在
#            2016 年就已经三千多亿。换宁德时代不行 —— 它 2018 年上市时与中国移动几乎一样大，
#            绝对值那一帧两条线起在同一行，「归一后从同一行起」就失去了自己的对照组。
MAOTAI = ("sh600519", "贵州茅台")
LATE = ("sh600941", "中国移动")
EARLY = ("sh600036", "招商银行")

# 一键预设那一排（A 股）：7 只，正好够把清单顶到 `MostTracks + 1`。
A_PRESETS = [("sh601318", "中国平安"), ("sh600519", "贵州茅台"), ("sh600036", "招商银行"),
             ("sh600900", "长江电力"), ("sz000858", "五粮液"), ("sh510300", "沪深300ETF"),
             ("sh000001", "上证指数")]

MOST_TRACKS = 6

# 数据区间的显示字（resw 里 StudioRange* 那几个键在中文界面下的值）。写成一个常量而不是在三
# 处各拍一遍同一个中文字：下拉里答的就是这几个字，拍错一个字会让「选到了某一档」悄悄变成「哪
# 档都没选」—— combo 的选中项读不回来，所以选没选上只能看 `pick_range` 的返回值。
RANGE_2Y = "近 2 年"
RANGE_10Y = "10 年"
RANGE_12M = "近 12 个月"

# 状态行说的话全在 resw 里，这里只留**判认它的开头**：整句刻在这儿，改一个字就红给人看而不
# 是悄悄放过。之所以用开头而不是全句，是因为句子带着家数与日期。
HEADS_TOO_MANY = ["最多同时比较"]
HEADS_NO_PICKS = ["清单里没有一家公司属于"]
HEADS_FETCHED = ["已取到"]

# 市值刻度的两个档位与它旁边的两个按钮都在 resw 里；这里写的是中文界面下的显示字。
ABSOLUTE = "实际数值"
NORMALIZED = "归一到 100"


def check(name, ok, note=""):
    (PASSED if ok else FAILED).append((name, note))

    print(("  √ %s" if ok else "  × %s") % name + (("  — %s" % note) if note and not ok else ""))


SETTINGS_NAMES = ["设置", "設定", "Settings", "Einstellungen", "Ajustes", "Paramètres",
                  "Impostazioni", "Ustawienia", "Configurações", "Nastavení", "Ayarlar",
                  "Настройки", "設定", "设置"]


def open_settings(win):
    for name in SETTINGS_NAMES:
        item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

        if item is None:
            continue

        try:
            item.GetSelectionItemPattern().Select()
        except Exception:  # noqa: BLE001 - a stale row only means the next name may fit
            pass

        time.sleep(2.0)

        return True

    return False


def market_to(win, index):
    """Puts the app on the market at `index` in the settings list, restarting if it moved.

    All three markets are served, so the market is no longer a precondition to get out of
    the way — it is part of what is being checked, and a run has to *set* it rather than
    inherit it. The preference is remembered, so without this every assertion below is
    about whichever market the last script to run happened to leave behind.

    By position rather than by name, so the script does not have to know what a market
    is called in whichever language the app is currently in.
    """
    if not open_settings(win):
        print("· 设置页没找到，市场保持原样")
        return win

    combo = winui.find(win, lambda c: c.AutomationId == "MarketCombo")

    if combo is None:
        print("· 市场下拉没找到，市场保持原样")
        return win

    labels = winui.combo_labels(win, combo)

    if not labels or index >= len(labels):
        print("· 读不出市场下拉的内容，市场保持原样")
        return win

    current = winui.value(combo)

    if current == labels[index]:
        return win

    picked = winui.combo_pick(win, combo, labels[index])
    print(f"· 市场从 {current} 切到 {picked}（改市场要重启）")

    time.sleep(1.5)

    winui.kill(winui.EXE)
    time.sleep(2.0)

    win = winui.launch(winui.EXE)

    if win is None:
        return None

    time.sleep(3)

    return winui.app_window(winui.EXE, wait_seconds=30)


def ensure_ashare(win):
    """The mainland, where the numbers this script checks were measured."""
    return market_to(win, 0)


def goto(win, name):
    item = winui.find(win, lambda c: c.ControlTypeName == "ListItemControl" and c.Name == name)

    if item is None:
        return False

    item.GetSelectionItemPattern().Select()
    time.sleep(2.5)

    return True


def first(win, automation_id):
    return winui.find(win, lambda c: c.AutomationId == automation_id)


# ---- 共享自选清单 ------------------------------------------------------------------
#
# 这一页原先是「填一个代码，取一只」；现在它跟持仓页一样，**画面上是清单里的哪几只由
# chip 决定**。下面这几个写法抄自 `verify-position.py` —— 同一份清单由八个页面共用，
# 它的脾气（chip 没有 InvokePattern、横向滚动会把外面的 chip 量成 0×0、加进来默认是关的）
# 不会因为换了一页就变，所以与其再试一遍，不如照抄那天已经踩完的结论。

def toggle_of(control):
    try:
        return control.GetTogglePattern()
    except Exception:  # noqa: BLE001
        return None


def press(control, win=None):
    """按一下一个控件，并在**真的按到了**时才返回 True。

    Invoke → 真点 → 键盘，三级退化，每一级都踩过：chip 没有 `InvokePattern`；而 `Click`
    在矩形为空时静默跳过那一下却照常返回 True（横向滚动那一排里，面板外的 chip 正是 0×0）。
    所以真点之前先量矩形，量不到就报失败而不是报成功。
    """
    if win is not None:
        try:
            win.SetActive()
            time.sleep(0.25)
        except Exception:  # noqa: BLE001
            pass

    try:
        control.GetInvokePattern().Invoke()
        return True
    except Exception:  # noqa: BLE001
        pass

    try:
        box = control.BoundingRectangle

        if box.width() <= 0 or box.height() <= 0:
            return False
    except Exception:  # noqa: BLE001
        return False

    try:
        control.Click(simulateMove=False)
        return True
    except Exception:  # noqa: BLE001
        pass

    try:
        control.SetFocus()
        time.sleep(0.3)
        control.SendKeys("{Space}", waitTime=0.3)
        return True
    except Exception:  # noqa: BLE001
        return False


def press_id(win, automation_id, tries=3):
    """按自动化 Id 找到的那个按钮（页面自己的那几个按钮都还有 Id）。"""
    for _ in range(tries):
        control = first(win, automation_id)

        if control is None:
            time.sleep(1.5)
            continue

        try:
            rect = control.BoundingRectangle

            if rect is not None and rect.width() > 0 and rect.height() > 0:
                win.SetActive()
                control.Click(simulateMove=False, waitTime=0.5)
                return True

            control.GetInvokePattern().Invoke()
            return True
        except Exception:  # noqa: BLE001
            time.sleep(1.5)

    return False


def chip(win, code):
    """清单里某一只的名字开关，按**代码**寻址 —— chip 带着 AutomationId="{x:Bind Code}"，
    而同一个代码在下面那一排一键预设上还出现一次，靠 TogglePattern 把两者分开。"""
    return winui.find(win, lambda c: c.AutomationId == code and toggle_of(c) is not None)


def chip_state(win, code):
    found = chip(win, code)

    if found is None:
        return None

    pattern = toggle_of(found)

    return pattern.ToggleState if pattern is not None else None


def chip_names(win):
    """清单里每一只的 (代码, 名字)，按清单自己的顺序。"""
    out = []

    for control in winui.find_all(win, lambda c: c.ControlTypeName == "ButtonControl"):
        if toggle_of(control) is None or not control.AutomationId:
            continue

        if re.fullmatch(r"(sh|sz|bj|hk|us)[A-Za-z0-9.]+", control.AutomationId):
            out.append((control.AutomationId, control.Name))

    return out


def remove_chip(win, name):
    """chip 右半边那个 ×：两个按钮同名，靠子文本里的 × 分开。"""
    for control in winui.find_all(
            win, lambda c: c.ControlTypeName == "ButtonControl" and c.Name == name):
        kids = [t.Name for t in winui.find_all(
            control, lambda c: c.ControlTypeName == "TextControl", limit=4)]

        if any(k.strip() in ("×", "✕") for k in kids):
            return control

    return None


def clear_list(win):
    """把共享清单清空 —— **断言之前必须清空**。

    这份清单是八个页面共用、跨会话留下的。不清空就是从「上次那几只 + 这次这两只」取数，
    而脚本按这一次这两只在算，两边对不上，画面却是一版漂亮的两条线。
    """
    for _ in range(24):
        names = [name for _, name in chip_names(win)]

        if not names:
            return True

        button = remove_chip(win, names[0])

        if button is None or not press(button, win):
            return False

        time.sleep(0.6)

    return False


def tick(win, code, on, tries=3):
    """把一只勾上或勾掉，并**读回来确认翻面了**。"""
    for _ in range(tries):
        control = chip(win, code)

        if control is None:
            return False

        if (chip_state(win, code) == 1) == on:
            return True

        if not press(control, win):
            time.sleep(1.2)
            continue

        time.sleep(1.0)

        if (chip_state(win, code) == 1) == on:
            return True

    return False


def ticked(win):
    """画面上被勾中的那几只，按清单的顺序 —— 也就是画面的顺序。"""
    return [code for code, _ in chip_names(win) if chip_state(win, code) == 1]


def preset(win, code):
    """下面那一排一键预设里的某一只。

    与清单里的 chip 同一个 AutomationId，**靠没有 TogglePattern 把自己那一侧分开**：chip 是
    开关，预设是一次性按钮。
    """
    return winui.find(win, lambda c: c.AutomationId == code and toggle_of(c) is None)


def grow_ticks(win, want):
    """Presses one-tap presets until `want` picks are switched on; returns how many are.

    **Presets rather than chips, and not out of convenience.** The chip row scrolls
    sideways, so a chip past the fourth measures 0×0 and `press` reports the miss —
    every instrument after that point is unreachable by clicking it, and the failure is
    silent. The one-tap row is laid out differently, lists the market's own seven, and
    each press both puts the instrument on the shared list and switches it on.

    Its press also *fetches* (`OnPresetClick`), which is why the caller narrows the range
    first: every intermediate answer here is a real walk nobody asked for.
    """
    reached = len(ticked(win))

    for code, name in A_PRESETS:
        if reached >= want:
            break

        button = preset(win, code)

        if button is None or not press(button, win):
            continue

        # The fetch that press started has to finish before the next one is pressed: two
        # overlapping runs share one button and one status bar, and the answer read at
        # the end would then be whichever of them reported last.
        wait_status(win)
        reached = len(ticked(win))

        print("  · %s 之后勾着 %d 家" % (name, reached))

    return reached


def add_to_list(win, code, tries=3):
    """在清单自己的搜索框里填一个代码并提交，然后数一遍 chip。

    **按代码确认，不按名字确认。**加进来那一刻 chip 上的名字还是代码 —— 名字要等取数那一趟把
    交易所叫它的那个名字带回来才会改（`Watchlist.Rename`），而这里紧接着还要按下一次取数才
    轮得到它，而这一趟取数本身不需要那个名字。

    这里刻意不点下面那一排一键预设：预设每被按一下都会顺手去取一趟数（见 `OnPresetClick`），
    而把标的塞到清单里这一步只想问「它们在不在」，没必要为它付这一次网络。
    """
    for _ in range(tries):
        box = winui.find(win, lambda c: c.AutomationId == "Search")
        edit = None if box is None else winui.find(
            box, lambda c: c.AutomationId == "TextBox", limit=6)

        if edit is None:
            return False

        try:
            win.SetActive()
        except Exception:  # noqa: BLE001
            pass

        edit.SetFocus()
        time.sleep(0.3)
        edit.SendKeys("{Esc}", waitTime=0.3)
        edit.SendKeys("{Ctrl}a", waitTime=0.3)
        auto.SetClipboardText(code)
        edit.SendKeys("{Ctrl}v", waitTime=0.5)
        time.sleep(1.2)
        edit.SendKeys("{Enter}", waitTime=0.5)
        time.sleep(2.0)

        if code in [found for found, _ in chip_names(win)]:
            return True

    return False


def add_ticked(win, code):
    """Adds one pick to the list and switches it on. Returns how many are switched on."""
    if not add_to_list(win, code):
        return -1

    if not tick(win, code, True):
        return -1

    return len(ticked(win))


def texts(win):
    found = []
    winui.find_all(win, lambda c: c.ControlTypeName == "TextControl" and c.Name, out=found)

    return [c.Name for c in found]


def resw_notes():
    """口径说明在十四种语言里的文本，从 resw 文件读。

    The note is a plain TextBlock: like every other explanatory line in this app it carries
    an x:Uid and no x:Name, so there is no AutomationId to ask for and looking for one
    reports "the note is missing" about a line that is on screen in all fourteen. Matching
    on text instead means the check still holds after the interface language is switched.
    """
    out = []

    for path in sorted(os.listdir(STRINGS)):
        resw = os.path.join(STRINGS, path, "Resources.resw")

        if not os.path.exists(resw):
            continue

        for entry in ET.parse(resw).getroot().findall("data"):
            if entry.get("name") == "CapHistoryNote.Text":
                value = (entry.find("value").text or "").strip()

                if value:
                    out.append(value)

    return out


def note_shown(win):
    shown = texts(win)

    for note in resw_notes():
        head = note[:10]

        if any(head in t for t in shown):
            return True

    return False


def status_text(win):
    """The InfoBar's message, which is not the first text in it.

    An InfoBar carries its severity glyph as a text control too, and that one comes
    first — so asking for "the text" returns a single private-use character and the
    fetch looks like it said nothing at all. The message is the longest of them, and
    while it is still working the message is the one being replaced every second or so.
    """
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    if bar is None:
        return None

    found = []
    winui.find_all(bar, lambda c: c.ControlTypeName == "TextControl" and c.Name, out=found)

    if not found:
        return None

    return max((c.Name for c in found), key=len)


def pick_range(win, label):
    combo = first(win, "RangeCombo")

    return winui.combo_pick(win, combo, label) if combo is not None else None


def pick_axis(win, label):
    """市值刻度那两种读法之一（实际数值 / 归一到 100）。"""
    combo = first(win, "AxisCombo")

    return winui.combo_pick(win, combo, label) if combo is not None else None


def wait_status(win, seconds=420):
    """Waits for the fetch to be over, and returns the last thing the page said.

    **Waits on the button, not on the words.** The old version waited for the status
    text to contain one of a handful of Chinese words, which silently cannot work for
    the refusals added since: "最多同时比较 6 家公司" and "清单里没有一家公司属于 X 市场"
    contain none of them, so asking for either of those answers used to sit there for
    its full timeout and then report "the fetch said nothing" — which reads as a hung
    request rather than as a page that answered immediately. `RunAsync` disables the
    button while a walk is in flight and enables it when the walk is done, which is
    true in all fourteen languages and for every answer including the ones that were
    refused before a request was made.

    The button going straight from enabled to enabled (a refusal) still counts, because
    a refusal *is* the answer; what must not happen is mistaking an in-flight progress
    line for the closing one, which is why the text is read after the button is back.
    """
    time.sleep(2.5)

    end = time.time() + seconds
    last = None

    while time.time() < end:
        text = status_text(win)

        if text:
            last = text

        button = first(win, "FetchButton")

        if button is not None and button.IsEnabled and text:
            return text

        time.sleep(2)

    return last


def fetch_now(win):
    """Presses Fetch and waits for it to finish. Returns what the page said."""
    if not press_id(win, "FetchButton"):
        return None

    return wait_status(win)


def shot(win, name):
    path = os.path.join(OUT, name)

    try:
        win.SetTopmost(True)
        time.sleep(0.6)
    except Exception:  # noqa: BLE001
        pass

    win.CaptureToImage(path)

    try:
        win.SetTopmost(False)
    except Exception:  # noqa: BLE001
        pass

    return path


def seek_to(win, value):
    """Puts the preview on one moment of the animation, and holds it there.

    `Playback.Seek` stops playback and asks for that frame, so the picture is a pure
    function of this number — unlike anything caught by waiting for a clock, which is
    at the mercy of how long the capture itself took.
    """
    slider = first(win, "Scrub")

    if slider is None:
        return None

    try:
        pattern = slider.GetRangeValuePattern()
        pattern.SetValue(value)
        time.sleep(0.9)

        return pattern.Value
    except Exception:  # noqa: BLE001
        return None


def frame_at(win, name, value):
    """One moment of the animation, as a picture this script will trust.

    `winui.capture` is the one that checks the file came back looking like this window:
    `CaptureToImage` takes whatever is on top, and a reading taken from the wrong
    picture is confidently wrong in ways that look like drawing bugs.
    """
    at = seek_to(win, value)

    if at is None or abs(at - value) > 0.002:
        return None, None

    path = os.path.join(OUT, name)

    if not winui.capture(win, path):
        return None, None

    return path, at


def curve_rows(path, want=None):
    """The rows of one drawn line, whichever colour it is.

    `want` is a colour test, and what comes back is one row per column: **the lowest**
    row that answered. Nothing here assumes where a panel starts, and taking the lowest
    is what keeps the header's figures out — everything drawn above the curve in its own
    columns (the run of colour in the header's count, the big running figure) loses to
    the stroke below it.

    Colour first, not position. The curve is a `Palette.Track` colour and nothing else
    in the frame is that colour; the grid is grey-blue, the footer is near-white, and the
    progress bar along the canvas's last row runs indigo through pink. The area fill
    under the curve is the same hue but never stronger than 0.45 alpha, which lands it
    below the brightness this asks for — and it has to be kept out, because it fills down
    to the baseline and would otherwise answer "the bottom of the panel" in every column.

    Columns the line has not reached yet still answer with something of their own; the
    caller sorts that out by looking for the columns that form the line.
    """
    from PIL import Image

    picture = Image.open(path).convert("RGB")
    box = winui.canvas_box(picture)

    if not winui.looks_like_a_frame(picture, box):
        return None, None

    left, right, top, _ = box
    last = winui.frame_bottom(picture, box)
    pixels = picture.load()

    test = want if want is not None else IS_TRACK_0
    found = {}

    for x in range(left, right + 1):
        for y in range(last, top, -1):
            if test(*pixels[x, y]):
                found[x] = y
                break

    return found, (left, right, top, last)


def line_bands(rows, box, gap=8, fewest=40):
    """The stretches of neighbouring columns one colour occupies, small gaps closed.

    A gap of one column inside a curve is not two curves. Something drawn over it — a
    label riding ahead of its line, a neighbouring line crossing — takes that column away
    from the colour test, and taking the longer of the two remaining halves then answers
    at the wrong end of the line: the comparison's rebased frame lost its first
    thirty-three columns to exactly one column like this, and reported 中国移动 starting
    413 rows above where it does start.

    `fewest` then drops what is left over. A glyph is a few dozen columns at most and
    stops at every letter — that is what keeps the header's count and the running figure,
    drawn in the same colour, from being read as the line.
    """
    present = sorted(rows)
    bands = []
    run = []

    for x in present:
        if run and x - run[-1] > gap:
            bands.append(run)
            run = []

        run.append(x)

    if run:
        bands.append(run)

    return [b for b in bands if len(b) >= fewest]


def line_span(rows, box, jump=None):
    """One line's own columns and the rows it was drawn across.

    Only one band is taken, and it is the **leftmost**: see `line_bands` for why it is
    a band rather than whatever happened to answer in each column, and for why its gaps
    have already been closed.

    Leftmost rather than longest, because a capsule is drawn in its own line's colour
    and rides ahead of the curve's end — so it answers the same colour test, in columns
    of its own, and a curve that has only partly grown can be *shorter* than it. Taking
    the longest then measures the capsule and calls it the line: three tenths of the way
    through the animation the two are within a few dozen columns of each other, which is
    not a margin anyone can see. The line always begins at the plot's left edge, and the
    capsule never does.

    Leftmost is no longer enough on its own, though, and the reason is in `flat_runs`:
    the capsule is five columns from the line's last point, so `line_bands` — which
    closes eight — welds the two into one band and "leftmost" then measures the capsule
    as part of the line. So the capsule is taken out *first*, by its flat run and not by
    any distance, and `CAPSULE_RIM` is given back on the left to cover the rounded cap
    whose columns are not flat and so are not part of the run that found it.
    """
    kept = rows
    capsule = capsule_of(rows, box)

    if capsule is not None:
        kept = {x: y for x, y in rows.items() if x < capsule[0] - CAPSULE_RIM}

    bands = line_bands(kept, box)

    if not bands:
        return None

    band = min(bands, key=lambda b: b[0])
    said = {x: rows[x] for x in band}
    rows_of = list(said.values())

    return {"columns": band, "top": min(rows_of), "bottom": max(rows_of), "at": said}


def flat_runs(rows, fewest):
    """Every unbroken sideways run of columns at one row, the long enough ones only.

    A capsule's bottom edge is a horizontal stroke, and it is the lowest thing of the
    line's colour in every one of its columns — so the row `curve_rows` reports is the
    same all the way across, apart from the two rounded caps. A curve is never that flat
    over hundreds of columns: it is a decade of daily figures against one axis.

    This is what tells the capsule apart from the curve, which is the whole difficulty —
    they are the same colour by design, and the capsule is deliberately drawn *in front
    of* the line it names. **Distance cannot do it, and that was measured rather than
    guessed**: a capsule sits five columns past its line's last point, and the curve's
    own segments are five columns apart from each other too, so `line_bands` closes the
    one gap exactly as readily as the other and hands back a single band three hundred
    columns wide with the capsule fused onto its right-hand end. What separates them is
    shape, and shape has to be asked as an **absolute** length: as a share of that fused
    band the capsule's flat run came out at 0.21, i.e. as "not flat at all".

    Measured on this page's own frames: a capsule's flat run is **59 to 82 columns** —
    the price panel's is the wide one, because its figure carries thousands — and the
    flattest stretch any of these curves manages is **23**. `CAPSULE_FLAT` is chosen to
    sit in that gap, and both numbers are written down here so it can be re-picked
    without re-deriving them.
    """
    runs = []
    run = []
    previous = None

    for x in sorted(rows):
        level = previous is not None and abs(rows[x] - previous) <= 1

        if run and x - run[-1] == 1 and level:
            run.append(x)
        else:
            if len(run) >= fewest:
                runs.append(run)

            run = [x]

        previous = rows[x]

    if len(run) >= fewest:
        runs.append(run)

    return runs


def capsule_of(rows, box, fewest=CAPSULE_FLAT):
    """The columns of this colour that are a capsule rather than the curve, if there are.

    Of the flat runs long enough to be one, the **rightmost** is taken: a capsule rides
    ahead of its own line's leading end, so it is the last thing of this colour in the
    frame, and a curve that happens to run level for a while further left cannot outrank
    it. Length is the only thing asked of it — see `flat_runs` for why, and for the two
    measured numbers the threshold comes from.
    """
    runs = flat_runs(rows, fewest)

    return runs[-1] if runs else None


def capsule_note(rows, box):
    """What the flat runs looked like, for the note under a check that found no capsule."""
    widest = max((len(r) for r in flat_runs(rows, 1)), default=0)

    return "最长的一段平的是 %d 列，而胶囊要 %d 列" % (widest, CAPSULE_FLAT)


def curve_columns(rows, box, jump, within=None):
    """Which of those columns are the curve: its longest unbroken sideways run.

    The columns with a row in them are not all curve — the header's count is drawn in
    the same colour, and so is the running figure — so the curve is recognised by being
    a *chain*: hundreds of neighbouring columns in a row, where a glyph is at most a few
    dozen before the letters break it. `jump` is deliberately enormous (nearly half the
    canvas), because it must hold the broken curve too: with one point per day drawn at
    its own partial height a chain that only tolerated gentle slopes would stop at the
    first crack, exclude the very columns that are wrong, and pass on a frame with a
    vertical drop down its right-hand edge.

    `within` narrows the search to one band. The capsule is the reason: it is the same
    colour as its own curve and sits to the right of it, so an unrestricted search over
    a partly grown frame can come back with the capsule's columns and call them the
    line. The caller hands in the band `line_span` would have taken.
    """
    left, right = (within[0], within[-1]) if within else (box[0], box[1])
    longest = []
    run = []
    previous = None

    for x in range(left, right + 1):
        y = rows.get(x)
        broken = previous is not None and y is not None and abs(y - previous) > jump

        if y is None or broken:
            if len(run) > len(longest):
                longest = run

            run = [] if y is None else [x]
        elif not run:
            run = [x]
        else:
            run.append(x)

        previous = y

    return longest if len(longest) > len(run) else run


def compare_curve(early, late, columns, tail=3):
    """Every column the earlier frame had drawn must sit where the later one has it.

    The tolerance is one pixel, which is the anti-aliasing asking nothing of a decision
    that is otherwise exact: the same points, placed by the same arithmetic, have no
    reason to land on two rows.

    The last few columns are left out, and they are left out because they are not the
    same question. The line's leading point is where the next segment is still being
    welded on, so the stroke there is the stroke *as far as it goes*; once the point
    past it exists, that same column is carrying the line down through it and reaches a
    couple of rows deeper. Measured on this page: one column, x=875, answered row 406
    in the early frame (the line stops there) and row 408 in the later one (the line
    runs on through) — which is a line ending here against a line passing through, not
    one point drawn in two places. Three columns is one point's worth of stroke at this
    page's step, plus a pixel of doubt either side of it.
    """
    moved = []

    for x in columns[: max(len(columns) - tail, 0)]:
        before = early.get(x)
        after = late.get(x)

        if before is None or after is None or abs(before - after) > 1:
            moved.append((x, before, after))

    return moved


def share_panel(path):
    """Do the two line colours live in one panel, or in two?

    **This measures the two lines, not the layout — and that is why it is backed by a
    source check and read together with the single frame.** With one instrument the value
    line is drawn in the upper panel and the price line in the lower one, strictly above
    it and never interleaved; comparing, every line is drawn in the same rectangle. What
    distinguishes them here is how the two coloured lines' row ranges relate: two panels
    put them in two bands that cannot touch, one panel lets them overlap.

    The catch is that "one panel" does not *guarantee* an overlap: two companies whose
    values never come near each other keep to two bands even inside one tall panel, and
    would measure negative while being perfectly correct. So this number is only read
    **relative to the single frame's**, which is what `main` does, and the layout claim
    itself is asserted in `source_checks`, where it is laid out rather than drawn.
    """
    red, box = curve_rows(path, IS_TRACK_0)
    cyan, _ = curve_rows(path, IS_TRACK_1)

    if red is None or cyan is None:
        return None

    top_line = line_span(red, box)
    under = line_span(cyan, box)

    if top_line is None or under is None:
        return None

    together = min(top_line["bottom"], under["bottom"]) - max(top_line["top"], under["top"])
    flatter = min(top_line["bottom"] - top_line["top"], under["bottom"] - under["top"])

    return together / max(flatter, 1), top_line, under


def starts_apart(path):
    """How many rows apart the two lines begin, in rows.

    Under either reading each line begins at *its own* first day, so the rows compared
    are two different columns — which is fine, because what is being asked is whether
    the first figure each line starts from **has the same value**: rebasing sets them
    all to 100, and the axis then puts them at one row. Absolute leaves each at the
    company's own size, which for the pair this script picks is a several-fold gap.

    Taken from each line's **leftmost band** rather than from the longest one, because a
    line's first columns are exactly where something else is most likely to be drawn
    over it — and that is the end whose row decides this answer. See `line_bands`.
    """
    red, box = curve_rows(path, IS_TRACK_0)
    cyan, _ = curve_rows(path, IS_TRACK_1)

    if red is None or cyan is None:
        return None

    heads = []

    for rows in (red, cyan):
        bands = line_bands(rows, box)

        if not bands:
            return None

        heads.append(rows[min(bands, key=lambda b: b[0])[0]])

    return abs(heads[0] - heads[1])


def source_checks():
    """The things about this page that only the source can say.

    None of these are checkable from the running app: the preview canvas has no UIA
    nodes at all, so anything the frame's *labels* claim can only be verified at the
    line that writes them. Each one is a call shape rather than a name, and every one
    that could pass by absence has a positive twin next to it.
    """
    xaml = open(PAGE_XAML, encoding="utf-8").read()
    code = open(PAGE_CODE, encoding="utf-8").read()
    draw = open(RENDER, encoding="utf-8").read()

    # 这一页取标的的方式换了：不再是自己那个搜索框，而是八个页面共用的那份自选清单。
    check("页面用的是共享自选清单，且允许勾选",
          '<views:WatchlistPicker x:Name="Watch" Selectable="True" />' in xaml,
          "XAML 里找不到 WatchlistPicker")
    check("页面上不再有单标的那个搜索框", 'x:Name="InstrumentSearch"' not in xaml)

    # 一键预设要能靠代码寻址：脚本 else 与读屏都拿名字，名字在 14 种语言里拼写不同。
    check("预设按代码寻址", 'AutomationProperties.AutomationId="{x:Bind Code}"' in xaml)

    # 刻度必须是**构造参数**。写成属性会读成默认的「实际数值」，而周围的控件全绿。
    check("渲染器在构造时就拿到了刻度",
          "public CapHistoryRenderer(CapBoard board, AnimationPlan plan, "
          "CapAxis axis = CapAxis.Absolute)" in draw)
    check("页面把选中的刻度真的传了进去",
          "new CapHistoryRenderer(board, plan, ChosenAxis())" in code,
          "代码里找不到 ChosenAxis() 那次构造")

    # 多标的时只留市值一个面板。画面上两种样子都像一张画好的图，量出任一种「就是这样」的像素
    # 都得靠数据配合（见 `share_panel` 的注释），所以这一事实落在源码上：Draw 走哪条分支、加
    # 载器有没有去算股价、以及**那条分支自己有没有再叠一块面板**。
    check("多标的时走的是单独的画法",
          "_comparing\n            ? DrawComparison(session, context, t, column)" in draw,
          "Draw 里找不到那条分支")
    check("多标的时不算股价那条线", "_prices = _comparing ? [] : Display(board, axis, price: true);"
          in draw)

    # 最里面的那一条：`DrawComparison` 一旦回头去调单盯面板那套（PanelArea 切开上下两块、
    # DrawPanel 按 isPrice 取数），多标的就又有了股价那块面板 —— 而上面两条还是绿的。
    body = re.search(
        r"private int DrawComparison\(.*?\n    \}", draw, re.S)

    check("多标的那条分支自己没有再去切上下两块面板",
          body is not None and "PanelArea(" not in body.group(0)
          and "DrawPanel(" not in body.group(0),
          "DrawComparison 里出现了 PanelArea / DrawPanel")

    # ---- 末端胶囊 ------------------------------------------------------------------
    #
    # 胶囊画在曲线自己的颜色里、又骑在曲线右边，所以它在像素上就是「又一段同色的东西」，上面的
    # 像素判据只能靠「平不平」把它和曲线分开（见 `flat_share`）。下面这几条说的是像素说不出的
    # 那部分，其中要紧的是**胶囊上的数是当下那一刻的数**。
    check("渲染器有胶囊那一支画法", "private void DrawCapsules(" in draw)
    check("胶囊是圆角的：先填底、再描自己那条线的颜色",
          "session.FillRoundedRectangle(box, radius, radius, "
          "Ink.Fade(Palette.CardFill, 0.92 * opacity));" in draw and
          "Ink.Fade(end.Colour, 0.95 * opacity), (float)context.Px(LabelEdge));" in draw)

    # 描边不能是发丝线：它压在自己那条线的颜色上，描边是唯一把两者分开的东西（这条理由是从持仓
    # 页照抄的，那里先踩过一次）。
    check("描边是三像素", "private const double LabelEdge = 3;" in draw)

    # 「实时」两个字就落在这儿：胶囊报的是曲线走到那一刻的值，不是序列末端的那个值。写死末值，
    # 画面上是「一个从头到尾不动的数」，而**末帧是全对的** —— 这正是只有源码能验的那一类。
    check("胶囊报的是当下那一刻的值，不是序列末值",
          "var reached = values[last];" in draw and
          "Format(values[track.Last], false)" not in draw,
          "找不着 reached，或者还在拿 track.Last 当实时值")

    # 让位：两块面板与多标的共用同一列，并且**一帧只量一次**。量两次（每块面板各量一次）会让上下
    # 两块面板的绘图区不一样宽，而这两块是共用一条时间轴的 —— 市值与股价就对不上日子了。
    check("绘图区让出的那一列一帧只量一次",
          draw.count("LabelColumn(session, context)") == 1,
          "量了 %d 次" % draw.count("LabelColumn(session, context)"))
    check("两块面板与日期行共用同一列",
          draw.count("Math.Max(1, context.ChartWidth - column)") >= 2)

    # 右缘收在哪：曾经两页（定投、持仓）都把它收到**画面**右缘，理由写的是「那条竖栏本来就在
    # 右边距里」——而那是错的，安全区右边那条栏是帧宽 18%（1080 下 194 像素），比右边距默认
    # 150 还宽，胶囊于是落在帧宽 98%、正好在平台头像与评论按钮底下。三页现在共用一处算术。
    check("右缘收在**安全线**上，不是画面右缘（右边 18% 是平台自己的按钮栏）",
          "context.SafeRight - context.Px(LabelEdgePad) - width" in draw,
          "还在按画面右缘收")
    check("让出的那一列把按钮栏算进去了，且三页共用同一处算术（不再各抄一份）",
          "context.RightLabelColumn(widest, context.Px(LabelGap + LabelEdgePad))" in draw,
          "还在各抄一份 need = widest + … - Margins.Right")

    # 单只也要挂：`DrawPanel` 里没有那一次调用，「单只没有标注」这个老样子会一直留着而 UIA 全绿。
    panel = re.search(r"private int DrawPanel\(.*?\n    \}", draw, re.S)

    check("单只那块面板也画了末端胶囊",
          panel is not None and "DrawCapsules(" in panel.group(0),
          "DrawPanel 里没有 DrawCapsules")

    # 拒绝而不是悄悄截断。
    check("过数是从头拒的，不在加载器里截断",
          "if (chosen.Count > CapLoader.MostTracks)" in code and
          "Strings.Format(\n                \"CapHistoryTooMany\"" in code)


def main():
    winui.kill(winui.EXE)
    time.sleep(2)

    if not winui.launch(winui.EXE, wait_seconds=60):
        print("应用没起来")
        return 1

    win = winui.app_window(winui.EXE, wait_seconds=30)

    if win is None:
        print("找不到窗口")
        return 1

    time.sleep(2)

    win = ensure_ashare(win)

    if win is None:
        print("切市场之后应用没起来")
        return 1

    os.makedirs(OUT, exist_ok=True)

    print("源码：")
    source_checks()

    print("导航：")
    check("导航里有「市值历程」", goto(win, "市值历程"))

    print("控件：")
    check("自选清单的搜索框在", first(win, "Search") is not None)
    check("区间下拉在", first(win, "RangeCombo") is not None)
    check("刻度下拉在", first(win, "AxisCombo") is not None)
    check("取数按钮在", first(win, "FetchButton") is not None)
    check("口径说明在", note_shown(win))

    # ---- 1) 一只公司 --------------------------------------------------------------
    #
    # 单位、对数、 Probe 那些老断言照旧，只是标的从页面自己那个搜索框换成了八个页面共用的自选
    # 清单 —— 取数的入口换了，要验的数一个没变。
    print("一只：")

    # **断言之前先清空。** 这份清单八个页面共用、跨会话留下；不清空，这一帧是「上次剩的几只 +
    # 这一只」，而下面每一条都只按这一只在算 —— 画面是一版漂亮的图，看不出它多画了几条线。
    check("共享清单清空了", clear_list(win) and chip_names(win) == [],
          " / ".join(name for _, name in chip_names(win)))

    # **加不进清单，先看机器有没有人在用。** 搜索框是 `AutoSuggestBox`：代码是靠键盘打进
    # 去的，而要敲得进去，这个窗口得是前台窗口。锁屏、切走、没有交互桌面的时候，键全部落
    # 空 —— 而这里的三条会一起红，红的形状和「清单坏了」一模一样：清了、加了、还是空的。
    # 所以在按下第一下之前先把这件事说清楚，省得再花一轮去怀疑那个框。
    added = add_to_list(win, MAOTAI[0])

    check("机器上有可以输入的桌面（没锁屏、窗口在前台）", added,
          "搜索框是靠键盘填的：锁屏或窗口不在前台时键进不去，下面几条会一起红。"
          "先跑 tools\\verify-caphistory-shape.py，它不碰应用")
    check("茅台加进清单了", added)
    check("勾上了（加进来默认是关的）", tick(win, MAOTAI[0], True))
    check("画面上正好一家公司", len(ticked(win)) == 1, " / ".join(ticked(win)))

    # 区间先显式选两年，再去断言天数：偏好是持久化的，重装之后默认档位不一定是两年，而「取到
    # 多少天」正是要验的东西 —— 让它跟着默认值漂，等于每次重装换一个断言。
    picked = pick_range(win, RANGE_2Y)

    check("区间选到「%s」" % RANGE_2Y, picked == RANGE_2Y, str(picked))

    time.sleep(1.5)

    said = fetch_now(win)

    print("  状态行：%s" % said)

    check("取数有回话", said is not None, "状态行一直是空的")

    if said is None:
        return 1

    days = re.search(r"(\d+)\s*个交易日", said)
    value = re.search(r"期末市值\s*([\d,]+)", said)

    check("状态行报了期数与末值", days is not None and value is not None, said)

    # 单只与多只说的不是同一句话（多只那句报的是「几家」而不是期末市值），所以「带着期末市值」
    # 这一条本身就是在说：这一帧走的是单只那条路。
    check("单只那一句带着期末市值", value is not None, said)

    if days:
        count = int(days.group(1))

        # 上面选了「近 2 年」。两年是四百八十个交易日上下；一个月是二十，差一个数量级 —— 而画
        # 面上两者都只表现为「一条曲线」，看不出来。
        check("期数落在两年的量级（300–600）", 300 <= count <= 600, "%d 天" % count)

    if value:
        cap = float(value.group(1).replace(",", ""))

        # 茅台 2026 年秋的**流通**市值在 1.5 万亿量级（快照 15,734）。差一位就是手/股换算反了，
        # 而这个错在画面上只是「线偏低」—— 京东方那种股本台阶对不上也是同一个错。别拿快照的总
        # 市值当参照：茅台两者相等是巧合，工行会差三成。
        check("期末流通市值落在 1.5 万亿量级", 10_000 <= cap <= 30_000, "%.0f 亿" % cap)

    print("画面：")
    check("导出按钮亮了", (lambda b: b is not None and b.IsEnabled)(first(win, "ExportButton")))

    # 单只的时候是**两块面板**：市值在上、股价在下。这里先把两块的样子量下来，多标的那段要拿
    # 它当反面参照 —— 「少了一块面板」在一张图上量不出来，而「两条线还各占一段行区间」量得出
    # 来。
    single_path, single_at = frame_at(win, "caphistory-single.png", 1.0)

    check("单只的完成帧取到了", single_path is not None, "frame_at 返回 %s" % single_at)

    single_panel = share_panel(single_path) if single_path else None

    check("单只是市值与股价两块面板（两条线各占一段行区间）",
          single_panel is not None and single_panel[0] < 0,
          "重叠 %.2f" % single_panel[0] if single_panel else "认不出两条线")

    # 单只的时候曲线末端也要挂胶囊 —— 这一次加的就是它。判据是：除了曲线自己那一大段，同色里
    # 还有一段**平的**（胶囊的下边），而曲线绝不可能是平的。两块面板各自都要有，因为单只画的
    # 是市值与股价两条线。
    if single_path is not None:
        for word, test in (("市值", IS_TRACK_0), ("股价", IS_TRACK_1)):
            rows, one_box = curve_rows(single_path, test)
            cap = capsule_of(rows, one_box) if rows else None
            span = line_span(rows, one_box) if rows else None

            check("单只那一帧 %s 那块面板的线头上有胶囊" % word, cap is not None,
                  capsule_note(rows, one_box) if rows else "认不出这一色")

            # 光有一条平段还不够：它得在**曲线前面**，也就是骑在正在生长的那个头上。曲
            # 线自己后面画的一段平路也平，但那种平路在左、不在头前。
            check("单只那一帧 %s 的胶囊骑在曲线前面" % word,
                  cap is not None and span is not None and cap[0] > span["columns"][-1],
                  "胶囊起于 %s，曲线止于 %s" % (
                      None if cap is None else cap[0],
                      None if span is None else span["columns"][-1]))

    # ---- 2) 长大时会不会动（这一条只有播放途中才现形，末帧是全对的） --------------
    print("生长：")

    early_path, early_at = frame_at(win, "caphistory-growth-early.png", 0.30)
    late_path, late_at = frame_at(win, "caphistory-growth-late.png", 0.50)

    check("搓擦条把画面定住了", early_path is not None and late_path is not None,
          "取帧失败：%s / %s" % (early_at, late_at))

    if early_path is not None and late_path is not None:
        early, box = curve_rows(early_path)
        late, _ = curve_rows(late_path)

        # 允许一口气跨掉半个画面仍然算同一条线：它会跨得这么狠，恰恰是坏掉的那一帧的样子。
        jump = round((box[3] - box[2]) * 0.45)

        # 只在这条曲线自己那一段里数。胶囊与曲线同色、又骑在曲线右边，不在段里先摘出去，数出
        # 来的「曲线」可能是胶囊 —— 而胶囊本来就是跟着走的，于是「早先画出的点没有挪动过」会因
        # 为它挪了而红，红得像是曲线坏了。
        head_early = line_span(early, box)
        head_late = line_span(late, box)

        first_run = curve_columns(
            early, box, jump, head_early["columns"] if head_early else None)
        second_run = curve_columns(
            late, box, jump, head_late["columns"] if head_late else None)

        # 下限按画面的比例算，不按列数写死：绘图区为了把胶囊让到安全线左边，比过去窄了四分之
        # 一（`FrameContext.RightLabelColumn`），于是同一个进度画出来的链就是短了 —— 一条按旧宽
        # 度标定出来的 60 列会红在一帧完全正常的画面上。这条判据只负责证明「像素认出来的是一条
        # 线、不是一个字」，真正的那条回归（早帧的列后来有没有挪位）在下面，靠的是比较而不是
        # 长度。认出的是胶囊而不是曲线的可能性由 `line_span` 先摘掉胶囊、再由 `within` 收窄来挡。
        floor = round((box[1] - box[0]) * 0.10)

        check("认得出这条曲线", len(first_run) >= floor,
              "只连出 %d 列，一条线至少要横跨画面的 %d 列" % (len(first_run), floor))

        # 正向断言，且必须先于「没有挪动」那一条成立：搓擦条万一没生效，两帧会一模一样，而一
        # 模一样的两帧当然「一个点也没动」—— 那是一次通过，不是一个证明。
        check("两个进度画到了不一样的长度", len(second_run) > len(first_run),
              "%d → %d 列" % (len(first_run), len(second_run)))

        moved = compare_curve(early, late, first_run)

        check("早先画出的点后来没有挪动过", not moved,
              "%d 列挪了位，头三列 %s" % (len(moved), moved[:3]))

        # 播放途中抽的帧，抽完要把进度放回末尾：让动画停在半中腰，下一个进来的脚本截到的就不
        # 是这一页的完成画面了。
        seek_to(win, 1.0)

    # ---- 3) 多标的：日期轴是并集，画面只留市值一块面板 ----------------------------
    #
    # 这两件事一句话都能说清，但单看画面都数不出来 —— 天数写在状态栏里还算好办，「少了一块面
    # 板」在一张图上根本不可见。所以各自送到能量出来的地方去验：
    #
    #   - 并集：先单独取那只**上市最晚**的公司，记住它自己从哪一天起、一共多少天；再把两只一
    #     起取，要求起点更早、总数更多。若取的是交集，两只一起那一次会砍到晚那只上市以来的时
    #     间 —— 正好是这两条会红的地方。
    #   - 一块面板：看两条线是不是共用同一个行区间。见 share_panel。
    print("多标的：")

    check("换标的之前把清单清干净", clear_list(win))
    check("中国移动加进清单了", add_to_list(win, LATE[0]))
    check("勾上了", tick(win, LATE[0], True))
    check("画面上正好一家", len(ticked(win)) == 1, " / ".join(ticked(win)))

    # 十年：两家上市时间差四年，只有把区间拉回到 2018 年之前，晚那一只自己的起点才会晚于两家
    # 的并集起点。取两年时两只都从区间头起，证不出差别。
    picked = pick_range(win, RANGE_10Y)

    check("区间选到「%s」" % RANGE_10Y, picked == RANGE_10Y, str(picked))

    time.sleep(1.5)

    late_said = fetch_now(win)

    print("  晚那只单取：%s" % late_said)

    one_days = re.search(r"(\d+)\s*个交易日", late_said or "")
    one_from = re.search(r"(\d{4}-\d{2}-\d{2})", late_said or "")

    check("晚上市那只自己也取到了", one_days is not None and one_from is not None, str(late_said))

    check("把招商银行也加进来并勾上", add_ticked(win, EARLY[0]) == 2,
          " / ".join(ticked(win)))

    both_said = fetch_now(win)

    print("  两只一起：%s" % both_said)

    tracks = re.search(r"(\d+)\s*家公司", both_said or "")
    many_days = re.search(r"(\d+)\s*个交易日", both_said or "")
    many_from = re.search(r"(\d{4}-\d{2}-\d{2})", both_said or "")

    check("状态行报了家数、天数与起点",
          tracks is not None and many_days is not None and many_from is not None, str(both_said))

    if tracks:
        check("报的家数和勾着的个数一致",
              int(tracks.group(1)) == len(ticked(win)),
              "报 %s 家 / 勾着 %d 家" % (tracks.group(1), len(ticked(win))))

    if many_days and one_days:
        # 并集：两只一起的那一次要**比晚那一只自己更长**。取的是交集的话正好反过来 —— 砍掉晚
        # 那一只上市之前的整段。
        check("日期轴取的是并集而不是交集",
              int(many_days.group(1)) > int(one_days.group(1)),
              "两只 %s 天 / 晚那只自己 %s 天" % (many_days.group(1), one_days.group(1)))

    if many_from and one_from:
        # 同一件事的另一种说法，且不依赖天数：并集的起点要早于晚那一只自己的起点。
        check("并集的起点早于晚上市那只自己的起点",
              many_from.group(1) < one_from.group(1),
              "并集起于 %s / 晚那一只起于 %s" % (many_from.group(1), one_from.group(1)))

    # 多标的那一句不带期末市值（几家几 EUR 没处写），所以「没有报期末市值」与「报了几家」是同
    # 一件事的两面 —— 顺手验掉，它证明这一帧走的是多只那条路。
    check("多只那一句改报家数，不再是期末市值",
          re.search(r"期末市值", both_said or "") is None, str(both_said))

    both_path, both_at = frame_at(win, "caphistory-compare.png", 1.0)

    check("多标的的完成帧取到了", both_path is not None, "frame_at 返回 %s" % both_at)

    # 几条线就几颗胶囊，各自挂在自己那条线头上 —— 少一颗就是少一条线的名字，而画面上只是「右边
    # 少了一个牌子」，看着完全合理。
    if both_path is not None:
        for i, test in ((1, IS_TRACK_0), (2, IS_TRACK_1)):
            rows, two_box = curve_rows(both_path, test)
            cap = capsule_of(rows, two_box) if rows else None
            span = line_span(rows, two_box) if rows else None

            check("多标的第 %d 条线带着自己的末端胶囊" % i, cap is not None,
                  capsule_note(rows, two_box) if rows else "认不出这一色")

            # 每条线的胶囊挂在自己那条线上，也是它唯一能说「哪条是哪家」的地方。见单只
            # 那一段里同一条的理由。
            check("多标的第 %d 条的胶囊骑在曲线前面" % i,
                  cap is not None and span is not None and cap[0] > span["columns"][-1],
                  "胶囊起于 %s，曲线止于 %s" % (
                      None if cap is None else cap[0],
                      None if span is None else span["columns"][-1]))

    if both_path is not None and single_panel is not None:
        both_panel = share_panel(both_path)

        check("两条线都在（几条几色，缺一条就该去找加载器）", both_panel is not None,
              "认不出两条线")

        if both_panel is not None:
            # 一块面板的直接后果是**市值那条线能画到下半去了**：单只时它被关在上面那一半里，
            # 最深只到上面板的底边；多标的时整个绘图区都归它，最矮的那家公司一路压到面板底部。所
            # 以拿那一行的下一百行当界碑，两个数都打在失败信息里。
            #
            # 无懈可击的那一版说法在 `source_checks` 里（`DrawComparison` 不得再碰 PanelArea /
            # DrawPanel），那里才排除「又叠回了股价面板」；这只是同一件事跑起来之后的证词。
            lowest = max(both_panel[1]["bottom"], both_panel[2]["bottom"])
            confined = single_panel[1]["bottom"]

            check("多标的时市值线画到了单只那一帧上面板之外",
                  lowest > confined + 100,
                  "最低画到第 %d 行，单只那一帧市值线最深到第 %d 行" % (lowest, confined))

    # ---- 4) 两种刻度：归一以后每条线从同一个数起，于是起在同一行 ------------------
    print("刻度：")

    absolute_apart = starts_apart(both_path) if both_path else None

    picked_axis = pick_axis(win, NORMALIZED)

    check("刻度选到「%s」" % NORMALIZED, picked_axis == NORMALIZED, str(picked_axis))

    time.sleep(3.0)

    rebased_path, rebased_at = frame_at(win, "caphistory-rebased.png", 1.0)

    check("归一那一帧取到了", rebased_path is not None, "frame_at 返回 %s" % rebased_at)

    if rebased_path is not None and absolute_apart is not None:
        rebased_apart = starts_apart(rebased_path)

        # 双向：绝对值下两条线各自起在自己公司的大小上（这两家差好几倍，差出几十行），归一后都
        # 从 100 起于同一行。只验「归一后挨在一起」不够 —— 两条线本来就可能凑巧同高。
        check("绝对值下两条线的起点隔得很开", absolute_apart >= 15, "%d 行" % absolute_apart)
        check("归一到 100 以后两条线从同一行起",
              rebased_apart is not None and rebased_apart <= 8,
              "%d 行" % rebased_apart if rebased_apart is not None else "认不出")

    # 改回默认：偏好是存盘的，这一档漂到下个脚本进来的那一帧里，而别的脚本并不知道自己看到的
    # 是哪一档。**动了哪个偏好最后无条件改回**。
    pick_axis(win, ABSOLUTE)
    time.sleep(2.0)

    # ---- 5) 第七家：拒绝，不是悄悄略过 --------------------------------------------
    #
    # 用一键预设往上顶：chip 那一排是横向滚动的，第四只之后的 chip 量出来是 0×0，点不到（见
    # press）。预设一次按下既进清单又勾上，代价是它顺手发一次取数 —— 所以先把区间收到一年，
    # 让每一次配角的请求都只走一两趟。
    print("拒绝：")

    check("换标的之前把清单清干净", clear_list(win))

    picked = pick_range(win, RANGE_12M)

    check("区间选到「%s」" % RANGE_12M, picked == RANGE_12M, str(picked))

    time.sleep(1.5)

    reached = grow_ticks(win, want=MOST_TRACKS + 1)

    check("勾到了第七家", reached >= MOST_TRACKS + 1, "只顶到 %d 家" % reached)

    check("清单上正好七家", len(chip_names(win)) == MOST_TRACKS + 1,
          " / ".join(code for code, _ in chip_names(win)))

    refused = fetch_now(win)

    print("  第七家：%s" % refused)

    check("第七家是拒绝而不是悄悄画六条",
          refused is not None and any(head in refused for head in HEADS_TOO_MANY), str(refused))

    # 拒绝就该**没有数**：这一条把「说了拒绝」和「真的没去取」分开 —— 拒绝的话写在状态栏上、画
    # 面却照旧画着上一次那几只，是最像成功的一种失败。成功那句以「已取到」开头，它没有。
    check("被拒绝之后状态栏没有报数",
          refused is not None and not any(head in refused for head in HEADS_FETCHED), str(refused))

    # ---- 6) 纽约：三个市场里唯一会暴露单位错误的一段，外加「跨市场标的被滤掉」 ------
    print("美股：")

    win = market_to(win, 2)

    if win is None:
        print("切到美股之后应用没起来")
        return 1

    check("导航里还有「市值历程」", goto(win, "市值历程"))

    # 清单是跨市场持久的：切过来的时候上面那七只 A 股还在清单里。这一页只画本市场认得的代码，
    # 所以此刻按取数，该得到的是「没有一家属于这个市场」，而不是一次白跑的网络。
    picked = pick_range(win, RANGE_2Y)

    check("美股那边的区间也能选", picked == RANGE_2Y, str(picked))

    time.sleep(1.5)

    before_picks = fetch_now(win)

    print("  还没选美股时：%s" % before_picks)

    check("清单里没有美股时报的是「没有属于这个市场的」",
          before_picks is not None and any(head in before_picks for head in HEADS_NO_PICKS),
          str(before_picks))

    # 美股那份一键预设里的第一个就是苹果，一按既进清单又勾上 —— 它自己会发一次取数，所以这里
    # 不等一个不存在的按钮，直接等那一趟走完。
    apple = preset(win, "usAAPL.OQ")

    check("预设里有苹果", apple is not None)

    if apple is not None and press(apple, win):
        us_said = wait_status(win)

        print("  苹果：%s" % us_said)

        check("取到了苹果", us_said is not None and any(head in us_said for head in HEADS_FETCHED),
              str(us_said))

        us_days = re.search(r"(\d+)\s*个交易日", us_said or "")
        us_value = re.search(r"期末市值\s*([\d,]+)", us_said or "")

        check("美股期数落在两年的量级（300–600）",
              us_days is not None and 300 <= int(us_days.group(1)) <= 600,
              us_days.group(1) if us_days else str(us_said))

        if us_value:
            cap = float(us_value.group(1).replace(",", ""))

            # 苹果 2026 年秋的总市值在四万八千亿美元量级（快照 48,691）。这一栏在纽约是总市值：
            # 它的换手率是全部股本的比例，内部人持股也在分母里。差一百倍就是量被当成手，而美股
            # 没有手。
            check("美股末值落在 4.8 万亿美元量级", 30_000 <= cap <= 80_000, "%.0f 亿" % cap)

        # 清单上剩下的那几只 A 股没进画：这一帧只有苹果一只，所以那句话里不带「几家」。
        #
        # **拿清单上的只数当证据，不拿 chip 的勾选。** 切市场要重启，重启之后 `_touched` 归
        # 零，chip 的勾选重新变成「只画清单第一只」那条规则的一面 —— 于是这里勾着的是「清单
        # 第一只 + 苹果」，与清单上有几只无关。而清单本身是存盘的，八只还在上头，只是画不出
        # 来：这正是一件事。
        check("清单上剩下的 A 股没有被画进来",
              us_said is not None and "家公司" not in us_said and len(chip_names(win)) >= 8,
              "清单上 %d 只：%s" % (len(chip_names(win)), us_said or ""))

    check("美股导出按钮亮了", (lambda b: b is not None and b.IsEnabled)(first(win, "ExportButton")))

    # 收尾：这份清单八个页面共用，留在上面的七只 A 股与这一只苹果会成为下一个脚本进来的那一
    # 帧。不是为了干净 —— 而是下一个脚本如果先清空，它会替这次遗漏买单而不报错。
    win = ensure_ashare(win)

    if win is not None:
        goto(win, "市值历程")
        clear_list(win)

    shot(win, "verify-caphistory.png")

    return 0


def report():
    print()

    if FAILED:
        print("失败 %d 项：" % len(FAILED))

        for name, note in FAILED:
            print("  × %s  %s" % (name, note))

    print("通过 %d 项，失败 %d 项" % (len(PASSED), len(FAILED)))

    return 1 if FAILED else 0


if __name__ == "__main__":
    try:
        code = main()

        # **像素那一半有一支离线的孪生。** 曲线上那颗胶囊与曲线同色，所以只能靠形状认；
        # 那一半判据不碰应用，也就能随时复核 —— 而在锁屏或没人操作的机器上跑真机这一段，
        # 红的是键盘进不去，不是判据。最后提一句，省得有人两手空空地回去改判据。
        print()
        print("· 胶囊的像素判据还有一支离线的：tools\\verify-caphistory-shape.py")
    finally:
        # `report` alone would hide an early return: a run that bailed out before any
        # check ran has nothing in FAILED, and would be reported as a pass.
        sys.exit(report() or code)
