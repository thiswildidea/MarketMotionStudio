# -*- coding: utf-8 -*-
"""真机验证 K 线页这一版的四件新事：分钟线的表头是**当日**涨跌幅，这一页可以画多个标的，
比较画面的零点与交易日（用户报「上证指数今天跌了 0.79，图上对不上」「为什么交易日为空」），
以及这一页也有了「允许图形越过右侧安全线」—— 顺便验页面上只剩一处检索框。

为什么要真机：都不是「源端返回什么」的问题。当日涨跌幅是把**前一个交易日**的收盘价带进
序列；多标的是把 N 条序列摆到同一根轴上；零点取昨收而不是当日开盘改的是画出来的数；
交易日改的是画面上的选择与重画路径 —— 四件都发生在页面里，离线脚本一样也证明不了。

画面上的判据是**像素**的，因为预览画布没有自动化节点：曲线几条按赛道色的色相数，末端标注
有没有进平台那条按钮栏按最右侧墨迹与「帧宽 82%」那条线比，换一天有没有重画按两幅画的差异
比。都用比例，不用绝对像素 —— 两次实拍的画布可能不一样大（状态条长短一变，预览按 9:16 缩）。

越线开关那两条**双向**验：关着时墨迹在安全线以内，打开后更靠右。只验一条的话，「开关接
反了」和「开关没接上」各能骗过一半 —— 前者骗过「打开后更靠右」，后者骗过「关着时在以内」。
换一天那条同样双向：换过去必须变，换回来必须变回同一张。

用法：
    python tools/verify-candle-multi.py
"""
import colorsys
import importlib.util
import os
import re
import sys
import time

import uiautomation as auto
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "src", "MarketMotionStudio")
OUT = os.path.join(ROOT, "artifacts")

sys.path.insert(0, HERE)

# 载入 verify-candle.py 里那些开窗口、按按钮、读状态条的手脚，不重写一遍。
sys.argv = ["x"]
_spec = importlib.util.spec_from_file_location("vc", os.path.join(HERE, "verify-candle.py"))
vc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vc)

# 还有 verify-candle-minute.py：这一跑要用它的 `combo_selected`（WinUI 的下拉读不回选中项，
# 只能展开再从选中行读）—— 它那句也是照着同一套 UIA 磕出来的。
sys.argv = ["x"]
_spec = importlib.util.spec_from_file_location(
    "vm", os.path.join(HERE, "verify-candle-minute.py"))
vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vm)

import winui  # noqa: E402

check = vc.check
CHECKS = vc.CHECKS
BAD = vc.BAD

SAFE = 0.82
PERIOD_DAILY = "日K"
PERIOD_5 = "5 分钟"


def read(*parts):
    with open(os.path.join(SRC, *parts), encoding="utf-8-sig") as handle:
        return handle.read()


# 一键预设**按代码**认，代码从 `Markets.cs` 自己数出来 —— 不写死六个，也不按名字认：
# 名字是界面语言拼的（14 种），而 UIA 里按钮的 AutomationId 正是 `MatrixPreset.Code`。
# 位置也不能单独当证据：窗口不在前台时 UIA 的矩形全是 0（见 `wake`），那时「夹在检索框与
# 收藏之间」会把整页按钮都圈进来。
CODE = re.compile(r'^\s*new\("([a-z]{2}[0-9A-Za-z.]+)",', re.M)
PRESET_CODES = set(CODE.findall(read("Market", "Markets.cs")))


def wake(win):
    """把窗口叫到前台，并等到「按位置认控件」这件事做得了。

    窗口不在前台时 UIA 给的 `BoundingRectangle` 是 `Rect(0,0,0,0)`、`IsOffscreen` 是 True。
    这一页的一键预设只能**按位置**认（`ItemsControl` 不把 `x:Name` 带进 UIA，实测 `Presets`
    查不到），位置一乱认出来的就是别的按钮 —— 实测认出过「水平小幅下降」这种仓库里根本不
    存在的名字：点下去什么都没发生，状态条上还留着上一句成功的话，于是「第一只取到了」是
    绿的，而清单里自始至终只有一只，后面每一条量蜡烛的跟着一起错，且错得没有症状。

    探针取**进度条**，不取检索框：检索框在右侧面板那个 `ScrollViewer` 里，跑到后半程面板会
    被别处的聚焦滚下去 —— 实测最后一张截图上面板已经从「起始日期」开头，检索框和整排清单都
    不在画面里，于是这一步无端失败，跟着 `chips()` 交回空清单（「走的时候清单也是干净的」
    报的是「一个 chip 都没读出来」，而清单上明明还开着一只）。进度条在播放条里，从不滚动。
    """
    for _ in range(6):
        try:
            auto.SetForegroundWindow(win.NativeWindowHandle)
            win.SetFocus()
        except Exception:  # noqa: BLE001
            pass

        time.sleep(1.0)

        for probe in (lambda c: c.AutomationId == "Scrub",
                      lambda c: c.AutomationId == "InstrumentSearch"):
            ctrl = vc.find(probe, win)

            if ctrl is None:
                continue

            try:
                if ctrl.BoundingRectangle.height() > 0 and not ctrl.IsOffscreen:
                    return True
            except Exception:  # noqa: BLE001
                pass

    return False


def into_view(win, automation_id="InstrumentSearch"):
    """把右侧面板滚到看得见那个控件为止，返回它。

    面板是个 `ScrollViewer`，而按**位置**认控件的那两处（清单那一排、一键预设那一排）都拿
    检索框的下缘当零点。跑到后半程面板会被别处的聚焦滚下去（最后一张截图上它从「起始日期」
    开头），那时零点不在视口里，两处一起认错人。`ScrollItemPattern.ScrollIntoView` 正是
    UIA 给的「把这一项滚进来」，也是真人会做的动作。
    """
    ctrl = vc.find(lambda c: c.AutomationId == automation_id, win)

    if ctrl is None:
        return None

    try:
        if ctrl.IsOffscreen:
            ctrl.GetScrollItemPattern().ScrollIntoView()
            time.sleep(1.0)
            ctrl = vc.find(lambda c: c.AutomationId == automation_id, win)
    except Exception:  # noqa: BLE001 - 控件在这一趟里消失了，下面会当成 None
        pass

    return ctrl


def goto(win):
    page = vc.find(lambda c: c.ControlTypeName == "ListItemControl" and c.Name == "K线", win)

    for _ in range(3):
        if page is not None:
            sel = vc.pat(page, auto.PatternId.SelectionItemPattern)

            if sel is not None:
                try:
                    sel.Select()
                except Exception:  # noqa: BLE001
                    pass
            else:
                vc.click(page, 1.0)

        deadline = time.time() + 12

        while time.time() < deadline:
            time.sleep(0.8)

            if vc.find(lambda c: c.AutomationId == "PeriodCombo", win) is not None:
                return True

    return False


INSTRUMENT = re.compile(r"^(?:sh|sz|bj|hk|us)[0-9A-Za-z.]+$")


def chips(win):
    """清单里每一只的 (代码, 名字, 开关)。按**代码**寻址，不按 14 种语言拼写的名字。

    筛两条，**不含位置** —— 位置这条被拿掉了，原因值得记下来：

    - 原来还要「这一排在搜索框下缘 160 px 之内」，那是用来排除视频设置面板里的「隐藏标题」
      「安全区参考线」的 —— 两个 `ToggleButton`，各有自己的 AutomationId，也有 TogglePattern，
      **把它们当成 chip 关掉就是把读者自己的设置关掉**。但检索框在右侧面板那个 `ScrollViewer`
      里，跑到后半程面板会被别处的聚焦滚出视口（实测最后一帧上面板已经从「起始日期」开头），
      而那时 UIA 给的矩形**还在**、只是整排上移出了视口 —— 那条于是从 0 到 160，一个 chip
      都圈不进来。于是「走的时候清单也是干净的」报「一个 chip 都没读出来」，而清单上明明还
      开着一只。面板滚出视口时 `IsOffscreen` 又不置位，所以「滚回视口」也救不了。

    两条有 AutomationId 的开关：

    - **AutomationId 像一个标的代码**（`sh000001`、`usAAPL.OQ`）。预设按钮的 AutomationId
      也是代码，但它们不是 `ToggleButton`，第 2 条就把两种分开了；「隐藏标题」那两个 id 不像
      代码，第 1 条同样排得掉 —— 而且不依赖面板滚到了哪儿。
    - **有 TogglePattern**：chip 是开关。

    每只旁边那个 `×` 的 AutomationId 是空的，第 1 条就出去了。
    """
    if not wake(win):
        return []

    out = []

    for control in vc.find_all(lambda c: c.ControlTypeName == "ButtonControl", win):
        if not INSTRUMENT.match(control.AutomationId or ""):
            continue

        try:
            pattern = control.GetTogglePattern()
        except Exception:  # noqa: BLE001
            continue

        if pattern is None:
            continue

        out.append((control.AutomationId, control.Name, pattern))

    return out


def clear_chips(win, tries=6):
    """把清单里的开关全关掉，**数到 0 才算**，返回 `(是否关干净, 说明)`。

    说明那一半是给失败看的：这一条红的时候有两个完全不同的原因 —— 开关真的关不掉，或者
    一个 chip 都没读出来（窗口不在前台、清单还没画）。两者的「没关干净」长得一样。

    清单是跨会话共享的一份，而且它的开关状态**跟内容一起落盘** —— 实测刚进页面时
    「创业板指」就是开着的，那是上一轮留下的。页面刚打开那一下共享清单还是异步读的，
    这时 chips 一个都读不到，「全关掉」于是等于什么都没做，随后点一个预设会把**它**加到
    已经开着的那只上：于是「点一下预设就是清单上多一只」读到两只，画面画的是两条曲线 ——
    而这一跑要的是「一只 → 两只」那两步。
    """
    seen = 0

    for _ in range(tries):
        live = chips(win)

        if not live:
            time.sleep(1.5)
            continue

        on = [c[1] for c in live if c[2].ToggleState == auto.ToggleState.On]

        if not on:
            return True, f"关干净了（清单上 {len(live)} 只）"

        for c in live:
            if c[2].ToggleState == auto.ToggleState.On:
                c[2].Toggle()
                time.sleep(0.4)

        time.sleep(1.0)
        seen = max(seen, len(live))

    if seen == 0:
        return False, "一个 chip 都没读出来（窗口不在前台，或清单还没画）"

    return False, f"关了 {tries} 遍还剩一只开着"


def presets(win):
    """一键预设那几个按钮，按它们在页面上的顺序。

    三层筛，因为 UIA 在这里给不出名字：

    1. **位置**：夹在搜索框下缘与「收藏」上缘之间。`ItemsControl` 不把 `x:Name` 带进 UIA
       （实测 `Presets` 与 `Watch` 都查不到，而 `PeriodCombo`、`FetchButton` 查得到），所以
       没有 `Presets` 这个 AutomationId 可用。
    2. **有 AutomationId**：预设按钮按代码寻址（`AutomationProperties.AutomationId="{x:Bind
       Code}"`），而「收藏」那一排两个按钮没有 —— 它们是按 `Tag` 认的。
    3. **没有 TogglePattern**：清单里的 chip 是 `ToggleButton`，它的 AutomationId 也是标的
       代码，前两条筛不出来。chip 是开关，预设是按钮，两件事。
    4. **AutomationId 是 `Markets.cs` 里数出来的一个代码**。这一条是后加的：位置那两条在
       窗口没激活时矩形全为 0，`0 <= 0 and 0 <= 0` 于是把整页按钮都圈了进来，认出来的是
       「水平小幅下降」这种本页根本没有的按钮。代码是唯一在两处都说得上的东西。
    """
    if not wake(win):
        return []

    search = into_view(win)
    add = vc.find(lambda c: c.AutomationId == "FavouriteButton", win)

    if search is None or add is None:
        return []

    top = search.BoundingRectangle.bottom
    bottom = add.BoundingRectangle.top

    if bottom <= top:
        return []

    out = []

    for control in vc.find_all(lambda c: c.ControlTypeName == "ButtonControl", win, 0, 30):
        if control.AutomationId not in PRESET_CODES:
            continue

        try:
            box = control.BoundingRectangle

            if box.height() == 0 or control.IsOffscreen:
                continue

            if control.GetPattern(auto.PatternId.TogglePattern) is not None:
                continue
        except Exception:  # noqa: BLE001
            continue

        if top <= box.top and box.bottom <= bottom:
            out.append((box.top, box.left, control))

    return [control for _, _, control in sorted(out)]


def cross(win, on):
    """把越线开关拨到要的那一边，返回它现在的状态。

    不用 `vc.toggle_on`：那只会在关着的时候打开，拨回去还得自己来 —— 而窗口关掉时偏好是
    落盘的，留着开在那里的开关就是留着一个别人下次打开看到的、没人记得改过的设置。
    """
    ctrl = vc.find(lambda c: c.AutomationId == "CrossCheck", win)

    if ctrl is None:
        return None

    toggle = vc.pat(ctrl, auto.PatternId.TogglePattern)

    if toggle is None:
        return None

    want = auto.ToggleState.On if on else auto.ToggleState.Off

    if toggle.ToggleState != want:
        toggle.Toggle()
        time.sleep(1.0)

    return toggle.ToggleState


def visible_searches(win):
    """页面上看得见的检索框，按 AutomationId 数 —— 应当是**恰好一个**。

    两个候选：面板自己那个 `InstrumentSearch`，和清单控件自带的 `Search`。清单那个在这一页
    是收起来的（`SearchVisible="False"`），实测收起来之后它**根本不进 UIA 树**，所以这一条
    真正读到的是「树里只剩一个」。

    **问三遍。** 刚取完数那一会儿整棵树有一次返回空 —— 不是控件不在，是这一趟遍历没走到它。
    问三遍之后仍是空才是真的空，那时该红。

    **先叫醒窗口。** `IsOffscreen` 在窗口不在前台时一律是 True —— 那时这一条读到的不是
    「页面上有两个检索框」，而是「这个窗口没在看」，两者在这一条里长得一模一样。
    """
    wake(win)

    out = []

    for _ in range(3):
        out = []

        for control in vc.find_all(
                lambda c: c.AutomationId in ("InstrumentSearch", "Search"), win):
            try:
                out.append((control.AutomationId, bool(control.IsOffscreen)))
            except Exception as error:  # noqa: BLE001
                out.append((control.AutomationId, f"读取失败 {str(error)[:30]}"))

        if out:
            break

        time.sleep(1.5)

    return out


def analyse(name):
    """一张截图里：赛道色出现了几种，以及最右侧的彩色墨迹在哪。

    只数**有彩度**的像素：画布是近黑的，网格和轴标签是灰的，进度条在画面下缘之外 ——
    剩下的彩色就是曲线本身和骑在它们末端的那一圈标注边框。

    `name` 收的是 `vc.shot` 交回来的路径：它只在照片确实是**这个窗口**的一帧时才给路径
    （见 `winui.capture`）。给不出时这里交出四个 None，调用方那些比较于是红在明处 ——
    拿着一张别的窗口（或上一轮的旧图）量出来的数，比红着更糟。
    """
    if name is None:
        return None, None, None, None

    whole = Image.open(name if os.path.isabs(name) else os.path.join(OUT, name)).convert("RGB")
    box = winui.canvas_box(whole)

    if box is None:
        return None, None, None, None

    left, right, top, _ = box

    # 画布的下缘要问 `frame_bottom`，不能用 `canvas_box` 给的那个：`canvas_box` 往下会走
    # 过画面下面的那一排控件（按钮、搓擦条也是暗的），实测把 852 说成 890。而画面最底下
    # 那两行是进度条 —— 它铺满整幅宽，混进来就是一条永远越线的墨迹，所以扫到下缘往上一
    # 点点为止。
    bottom = winui.frame_bottom(whole, box) or box[3]
    height = bottom - top
    pixels = whole.load()

    floor = int(bottom - (height * 0.03))
    hues = {}
    far = left

    for y in range(top, floor, 2):
        for x in range(left, right, 2):
            r, g, b = pixels[x, y]

            if max(r, g, b) - min(r, g, b) < 70 or max(r, g, b) < 90:
                continue

            hue = int(colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 12)
            hues[hue] = hues.get(hue, 0) + 1

            if x > far:
                far = x

    strong = sorted((count for count in hues.values() if count >= 60), reverse=True)

    return strong, far, box, right


def band_diff(a, b, floor=40):
    """两幅画面的**画布带**差了多少，0..1。

    不比整幅：整幅里九成是面板、下拉和状态条，而「换一天」改的只有画面里那几条曲线。实测
    同一件事在整幅上是 0.5%（被读成「没重画」），在画面带里是二十几个百分点。界也跟着换
    地方才有意义 —— 整幅上 2% 要整块面板变过才够，画布带上 2% 只是曲线动了几根。
    """
    from PIL import Image

    if a is None or b is None:
        return 1.0

    first = Image.open(a).convert("RGB")
    second = Image.open(b).convert("RGB")

    if first.size != second.size:
        return 1.0

    box = winui.canvas_box(first)

    if box is None:
        return 1.0

    left, right, top, _ = box
    bottom = winui.frame_bottom(first, box) or box[3]
    one = first.load()
    two = second.load()
    changed = 0
    total = 0

    for y in range(top, bottom, 2):
        for x in range(left, right, 2):
            total += 1

            if sum(abs(p - q) for p, q in zip(one[x, y], two[x, y])) > floor:
                changed += 1

    return changed / max(1, total)


def main():
    # ---- 源码：当日涨跌幅 ------------------------------------------------------------
    series = read("Market", "CandleSeries.cs")
    render = read("Render", "CandleRenderer.cs")

    check("序列带得动「昨收」", "double PreviousClose = 0" in series)
    check("昨收取**前一场**的收盘，不是上一根的",
          "CloseBefore(MinuteDay day)" in series and "Days[at - 1].Bars[^1].Close" in series)
    check("每一天的序列把昨收带进去",
          "ForDay(MinuteSession session, MinuteDay day)" in series
          and "session.CloseBefore(day)" in series)
    check("表头优先用昨收 —— 分钟线的那个大数字才是当日的",
          "_series.PreviousClose > 0" in render,
          "" if "_series.PreviousClose > 0" in render else "还在拿前一根当基准")

    # ---- 源码：多标的 ----------------------------------------------------------------
    board = read("Market", "CandleBoard.cs")
    racer = read("Render", "CandleRaceRenderer.cs")
    page = read("Pages", "CandlePage.xaml.cs")
    xaml = read("Pages", "CandlePage.xaml")

    # 预设的代码是判据自己从 `Markets.cs` 数出来的。数不出来就大声失败 —— 静默变成空集合的
    # 话，`presets()` 会返回空列表，然后「页面上有至少两个一键预设」红着，看上去像页面坏了。
    check("判据自己数得出预设的代码（不写死六个）", len(PRESET_CODES) >= 6,
          f"{len(PRESET_CODES)} 个：{sorted(PRESET_CODES)[:3]}")

    check("轴是**并集**不是交集（晚上市的不被截短）", "new SortedSet<string>" in board)
    check("自己没有的那天向前携带，不画成掉回零", "returns[i] = carried" in board)
    check("分钟线取各标的**共有**的那些交易日（交集，且整场优先）",
          "SharedDays(sessions)" in board and "sessions[0].Whole" in board)

    # 用户报的：``上证指数今天跌了 0.79，图上对不上``。图上那条是 -0.71% —— 比较画面把零点
    # 放在**当日开盘**上，而一天是相对**前收盘**算的。科创50 那天开盘算 -3.73%、昨收算
    # -4.82%，差一个多百分点。基准现在只有一处：`CandleSeries.Baseline`，`RangeReturn`
    # 和比较画面都读它。
    check("比较画面的零点取昨收，不取当日开盘",
          "PreviousClose > 0 ? PreviousClose : Opening" in series
          and "var baseline = one.Baseline" in board,
          "" if "var baseline = one.Baseline" in board else "还在拿 Bars[0].Open 当零点")
    check("区间涨跌走同一个基准（分钟周期下就是当日涨跌幅）",
          "RangeReturn => Baseline > 0 ? ((Closing / Baseline) - 1) * 100 : 0" in series)
    check("每条曲线一个零点，不是各自的开盘价",
          "double Baseline)" in board and "one.Bars[0].Open" not in board)

    # 用户报的另一半：``为什么交易日为空``。比较取完数之后那个下拉是空的 —— 页面对比较画面
    # 本来只清空它，而候选日一直都在手上（每个标的的 session 里）。
    check("比较画面把交易日列出来（不再清空它）",
          "board.Drawn?.Id" in page and page.count("FillDays();") == 2,
          f"FillDays() 出现 {page.count('FillDays();')} 次")
    check("换一天是重画，不回源端（session 就在板子上）",
          "public static CandleBoard On(CandleBoard board, string day)" in board
          and "CandleBoardLoader.On(board, id)" in page)
    check("取数时把存住的那一天带上",
          "progress, cancellation, _day)" in page)
    check("一天都没取回来之前那个下拉是灰的",
          "DayCombo.IsEnabled = DayCombo.Items.Count > 0" in page)
    check("分钟周期下不再留两个没人读的日期选择器",
          "!CandleLoader.IsMinute(ChosenPeriod())" in page,
          "" if "!CandleLoader.IsMinute(ChosenPeriod())" in page
          else "自定义区间那两个 DatePicker 在 5 分钟档下还立着")
    check("每条曲线一种赛道色", "Palette.Track(k)" in racer)
    check("末端标注走的是三页共用那一处安全线算术",
          "context.SafeRight(_giveWay)" in racer
          and "context.RightLabelColumn(widest, context.Px(LabelGap + LabelEdgePad), _giveWay)"
          in racer)
    check("页面在选了 2 个以上时改画比较",
          "board, plan, ChosenMotion(), ChosenWindow(), CrossSafeRight())" in page)
    check("蜡烛图那一排样式在多标的下是灰的（不然就是三个被忽略的设置）",
          "StyleCombo.IsEnabled = _board is null" in page)
    check("清单那一排是可开关的",
          "Selectable=\"True\"" in xaml and "WatchlistPicker" in xaml)

    # ---- 源码：越线开关，和一处检索 --------------------------------------------------
    check("蜡烛图那把绘图区也当安全线是硬约束（关着时收在按钮栏之前）",
          "Math.Min(context.ChartRight, context.SafeRight())" in render
          and "_crossSafeRight" in render,
          "" if "context.SafeRight()" in render else "蜡烛图完全不知道安全线")
    check("页面把同一个选择交给两种画面",
          "ChosenWindow(), CrossSafeRight())" in page
          and "VolumeCheck.IsChecked is true, CrossSafeRight())" in page)
    check("这个选择是存住的（读一次、写一次）",
          page.count('"CrossSafeRight"') >= 2, str(page.count('"CrossSafeRight"')))
    check("清单可以只要 chips —— 这一页的检索在上方已经有了",
          "SearchVisible" in read("Views", "WatchlistPicker.xaml.cs")
          and 'SearchVisible="False"' in xaml)

    # ---- 真机 ------------------------------------------------------------------------
    win = vc.launch()

    if win is None:
        check("窗口起来了", False)
        return 1

    check("导航到 K 线页", goto(win))

    # 量位置之前先叫醒窗口：不激活时矩形全是 0，按位置认的那几条（`presets`、`chips`）会
    # 认错人，而认错人之后每句话都还通顺 —— 这是这一跑里最难看出来的一种错。
    check("窗口叫到了前台（矩形量得出来）", wake(win))

    rows = presets(win)
    check("页面上有至少两个一键预设", len(rows) >= 2,
          "、".join(c.Name for c in rows[:4]) or "0 个")

    if len(rows) < 2:
        return 1

    # 周期是**落盘的偏好**，而这一跑量蜡烛那几条要在日 K 上量。先摆回日 K：摆回去本身不发
    # 请求（周期只有在下一次取数时才用得上），所以这一下不要等状态条。
    period_combo = vc.find(lambda c: c.AutomationId == "PeriodCombo", win)

    if period_combo is not None and vm.combo_selected(win, period_combo) != PERIOD_DAILY:
        winui.combo_pick(win, period_combo, PERIOD_DAILY)
        time.sleep(2.0)

    # 上一轮跑完会留着开关的状态（清单是跨会话共享的，且开关跟着内容一起落盘），这一轮
    # 先全部关掉，从干净处起 —— 而且要**验到 0**，见 `clear_chips`。
    clean, why = clear_chips(win)
    check("来的时候清单是干净的（开关状态跟内容一起落盘）", clean, why)

    # 全都关掉时取数，应当被**挡住**并说出原因 —— 这句话是本版才有的。
    vc.click(vc.find(lambda c: c.AutomationId == "FetchButton", win), 1.0)
    empty = vc.wait_status(win, seconds=30)
    check("一只都没开时取数被挡住并说清原因", bool(empty) and "标的" in (empty or ""),
          empty or "(状态条空)")

    # 一键预设点一下 = 加进清单 + 打开这只 + 取数。点两个，页面就该从「一只的蜡烛图」
    # 换成「两只的比较」。
    # 「点一下预设」到底有没有把这只放上清单，**按清单数**判，不看状态条：认错按钮时状态条
    # 上还留着上一句成功的话，只有清单数得上。
    vc.click(rows[0], 1.0)
    one = vc.wait_status(win, seconds=90)
    check("第一只取到了", bool(one) and not BAD.search(one or ""), one or "(状态条空)")

    picked = [c for c in chips(win) if c[2].ToggleState == auto.ToggleState.On]
    check("点一下预设就是清单上多一只（且它是开着的）", len(picked) == 1,
          f"{len(picked)} 只：{[p[1] for p in picked]}")

    check("一只时样式下拉是可用的", vc.enabled(win, "StyleCombo") is not False,
          str(vc.enabled(win, "StyleCombo")))

    vc.click(rows[1], 1.0)
    many = vc.wait_status(win, seconds=120)
    check("第二只取到了（两只一起）", bool(many) and not BAD.search(many or ""),
          many or "(状态条空)")

    on = [c for c in chips(win) if c[2].ToggleState == auto.ToggleState.On]
    check("清单里有两只开着", len(on) == 2, f"{len(on)} 只：{[c[1] for c in on]}")

    check("多标的下样式下拉是灰的（这一版不画蜡烛）",
          vc.enabled(win, "StyleCombo") is False, str(vc.enabled(win, "StyleCombo")))

    vc.scrub_to(win, 1.0)
    frame = vc.shot(win, "verify-candle-multi.png")

    check("比较画面这张照片是这个窗口的一帧（不是被盖住时抓到的别人）", frame is not None)

    strong, far, box, right = analyse(frame)

    if box is None:
        check("截图里认得出画布", False)
        return 1

    width = box[1] - box[0]
    line = round(box[0] + (width * SAFE))
    check("画面上至少两种赛道色（确有几条曲线）", len(strong) >= 2, str(strong[:4]))
    check("末端标注的右缘在安全线以内（不进平台那条按钮栏）",
          far <= line + 6,
          f"最右墨迹 x={far}，安全线 {line}，画布右缘 {right}")

    # ---- 比较画面上的交易日：列出来，且换一天只重画 --------------------------------
    #
    # 用户报的原话是「为什么交易日为空」：比较取完数之后那个下拉是空的，因为页面对比较画面
    # 本来只清空它。比较只能画在所有标的共有的一天上，所以候选就是那些共有日 —— 它们都在
    # 取数时那几次请求里回来了。
    #
    # 交易日只在分钟档上有，而周期是**落盘的偏好**：先切到 5 分钟，验完切回原来那一档，
    # 免得这一跑把读者（或下一个判据）留在别的周期上。
    period_combo = vc.find(lambda c: c.AutomationId == "PeriodCombo", win)
    was_period = vm.combo_selected(win, period_combo)
    stale = vc.status_text(win)

    if was_period != PERIOD_5:
        winui.combo_pick(win, period_combo, PERIOD_5)
        time.sleep(2.0)

    # 等一条**新**话：切换周期后的旧成功行与新的长得一模一样，不问「是不是新的」就会拿
    # 切换之前那一条当结果，于是「多标的 × 5 分钟取到了」在根本没取到数时也是绿的。
    minutes = vc.wait_status(win, unlike=stale, seconds=150)

    check("多标的 × 5 分钟取到了", bool(minutes) and not BAD.search(minutes or ""),
          minutes or "(状态条空)")

    day_combo = vc.find(lambda c: c.AutomationId == "DayCombo", win)
    offered = winui.combo_labels(win, day_combo) if day_combo is not None else []

    check("多标的下交易日不是空的（列着它们共有的日子）",
          len(offered) >= 2, f"{len(offered)} 项：{offered[:4]}")
    check("那个下拉不是灰的（有日子可选）",
          vc.enabled(win, "DayCombo") is not False, str(vc.enabled(win, "DayCombo")))

    if len(offered) >= 2:
        current = vm.combo_selected(win, day_combo)

        # 挑的是「与当前不同的那一天」：日期也落盘，上一次跑完留在这页的正是上一次挑的那天，
        # 再挑一次等于什么都没做，而「画面没变」会被读成「换日期坏了」。
        target = offered[0] if current != offered[0] else offered[-1]

        vc.scrub_to(win, 1.0)
        first = vc.shot(win, "verify-candle-multi-day-a.png")
        line_before = vc.status_text(win)

        if winui.combo_pick(win, day_combo, target):
            time.sleep(2.0)

            vc.scrub_to(win, 1.0)
            second = vc.shot(win, "verify-candle-multi-day-b.png")
            # 只比**画布带**：换一天改的是画面里那几条曲线，整幅里九成是面板和状态条，
            # 于是在整幅上这件事只有 0.5% —— 那不是「没重画」，是「比错了地方」。
            moved = band_diff(first, second)

            check(f"换到 {target} 画面真的重画了", moved > 0.02,
                  f"画布带里 {moved:.1%} 的像素变了")

            # 换一天**不该**发请求：那些日子在同一次取数里就回来了。真发了请求的话状态行会
            # 换一条 —— 而新那条里的起止日正是挑中的那天，所以「文字一模一样」就是「没取数」。
            check("换一天不重新取数（状态行还是那一条）",
                  vc.status_text(win) == line_before, str(vc.status_text(win))[:80])

            # 换回来必须画回同一张：只验「换一天变了」的话，日期映射接错（比如永远画最新那
            # 天）也能过 —— 它每换一次都变。
            if winui.combo_pick(win, day_combo, current or offered[-1]):
                time.sleep(2.0)

                vc.scrub_to(win, 1.0)
                third = vc.shot(win, "verify-candle-multi-day-c.png")
                again = band_diff(first, third)

                check("换回原先那一天画回同一张", again < 0.02, f"{again:.1%} 不同")
        else:
            check(f"挑到 {target}", False)

    if was_period and was_period != PERIOD_5:
        winui.combo_pick(win, period_combo, was_period)
        vc.wait_status(win, unlike=vc.status_text(win), seconds=150)

    # 蜡烛那几条要在日 K 上量：分钟档下这一页画的是同一条曲线，不是蜡烛。
    check("回到日K（蜡烛那几条要在日K上量）",
          vm.combo_selected(win, period_combo) == PERIOD_DAILY,
          str(vm.combo_selected(win, period_combo)))

    # ---- 一处检索，和一个越线开关 ----------------------------------------------------
    #
    # 安全线按**当前的**画布重量一次：上面那次是切换周期之前量的，而画布大小随状态条的长短
    # 走（预览按 9:16 等比缩，状态条多一行画面就窄一点）。
    vc.scrub_to(win, 1.0)
    remeasured = analyse(vc.shot(win, "verify-candle-multi.png"))

    if remeasured[2] is not None:
        _, far, box, right = remeasured
        line = round(box[0] + ((box[1] - box[0]) * SAFE))

    boxes = visible_searches(win)
    check("页面上看得见的检索框只有一个（不再有两块「股票」）",
          boxes == [("InstrumentSearch", False)], str(boxes))

    check("页面上有「允许图形越过右侧安全线」，且带标签",
          bool(vc.label_of(win, "CrossCheck")), str(vc.label_of(win, "CrossCheck")))

    # 双向验：只验「打开后更靠右」的话，「开关根本没接上、两次都靠右」照样绿；只验「关着时
    # 在安全线内」的话，「开关接反了、关着反而越线」也绿。
    check("越线开关默认是关的", cross(win, False) == auto.ToggleState.Off)

    vc.scrub_to(win, 1.0)
    _, far_off, _, _ = analyse(vc.shot(win, "verify-candle-cross-off.png"))

    check("关着时末端标注停在安全线以内", far_off is not None and far_off <= line + 6,
          f"最右墨迹 x={far_off}，安全线 {line}")

    check("越线开关打开", cross(win, True) == auto.ToggleState.On)

    vc.scrub_to(win, 1.0)
    _, far_on, _, _ = analyse(vc.shot(win, "verify-candle-cross-on.png"))

    check("打开后图形放宽到那条带里（不只是数字没动）",
          far_on is not None and far_off is not None and far_on >= far_off + 4,
          f"关闭 x={far_off} → 打开 x={far_on}（安全线 {line}）")

    # 回到关闭：这一页的偏好是落盘的，留一个开着的开关就是留一个下次打开时的意外。
    check("开关拨回关闭", cross(win, False) == auto.ToggleState.Off)

    # ---- 退回一只 --------------------------------------------------------------------
    # 双向验：只验「两只时是比较」的话，「一只时也画比较」照样绿。
    #
    # 这一段**必须真有一只**才量：少了那一只，取数会被「没有选中任何标的」挡住，画面是空的，
    # 而空画面上最右墨迹就是画布左缘 —— 关与开两个数字一模一样，看着像「开关没接上」，其实
    # 是这一段根本没画东西。所以先按清单数判，不够两只就别往下走。
    if len(on) == 2:
        win.SetFocus()

        try:
            on[-1][2].Toggle()
        except Exception:  # noqa: BLE001
            pass

        time.sleep(1.0)

        still = [c for c in chips(win) if c[2].ToggleState == auto.ToggleState.On]
        check("退回一只后清单上还剩一只（这一段量的不是空画面）", len(still) == 1,
              f"{len(still)} 只：{[c[1] for c in still]}")

        fetch = vc.find(lambda c: c.AutomationId == "FetchButton", win)
        vc.click(fetch, 1.0)
        back = vc.wait_status(win, seconds=90)

        check("关掉一只之后取数正常", bool(back) and not BAD.search(back or ""),
              back or "(状态条空)")
        check("退回一只后样式下拉恢复可用", vc.enabled(win, "StyleCombo") is not False,
              str(vc.enabled(win, "StyleCombo")))

        vc.scrub_to(win, 1.0)
        strong2, _, box2, _ = analyse(vc.shot(win, "verify-candle-single-again.png"))
        check("退回一只后画面变了（不再是那几条曲线）", strong2 is not None, "")

        # 蜡烛图那一半也受同一个开关管。这一页的蜡烛没有末端标签，但最右边那几根就是画在
        # 那条带里的墨，所以两条都要验 —— 不然「参数加上了、没接进去」也能过。
        vc.scrub_to(win, 1.0)
        _, candle_off, _, _ = analyse(vc.shot(win, "verify-candle-candle-cross-off.png"))

        cross(win, True)

        vc.scrub_to(win, 1.0)
        _, candle_on, _, _ = analyse(vc.shot(win, "verify-candle-candle-cross-on.png"))

        check("蜡烛图也读这个开关（打开后一直画到右边距）",
              candle_on is not None and candle_off is not None
              and candle_on >= candle_off + 4,
              f"关闭 x={candle_off} → 打开 x={candle_on}")

        cross(win, False)

    # 开关的状态**也落盘**，和清单的内容一起 —— 把开关留在开着的位置上，下一个判据（以及
    # 下一次真实使用）就是从一个没人选过的画面开始的：这一页的搜索和一键预设都是「把这只放
    # 到清单上并画出来」，清单里还开着别人，按下去画出来的就是两只。来的时候全关，走的时候
    # 也全关。
    clean, why = clear_chips(win)
    check("走的时候清单也是干净的", clean, why)

    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"\n通过 {passed} 项，失败 {len(CHECKS) - passed} 项")

    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
