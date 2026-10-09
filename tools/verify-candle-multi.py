# -*- coding: utf-8 -*-
"""真机验证 K 线页这一版的四件新事：分钟线的表头是**当日**涨跌幅，这一页可以画多个标的，
比较画面的零点与交易日（用户报「上证指数今天跌了 0.79，图上对不上」「为什么交易日为空」），
以及这一页也有了「允许图形越过右侧安全线」—— 顺便验页面上只剩一处检索框。

再往下一版：多标的的两种排布。**合图**是几条百分比曲线共用一根轴，**分图**是一只一格、
各有各的纵轴、上下排列，最多三只；两种排布的最下方都收在一排卡片上，每只一张，大数字是
涨幅%、小字是涨跌额。分图超过三只时只画前三只，其余的在状态行里点名。

再一件（用户报「导出 MP4 没响应」）：**比较画面的导出**。这一页是唯一一个「两个数据源画两张
画」的页面，而两个导出处理器的守卫只问了序列 —— 比较画面故意把序列清空、留着板子，于是每
一次按下都从第一行静默返回。这一跑把它按下去，等日志里长出 `encode: enter`（`EncodeAsync`
的第一句），再按取消收尾。

为什么要真机：都不是「源端返回什么」的问题。当日涨跌幅是把**前一个交易日**的收盘价带进
序列；多标的是把 N 条序列摆到同一根轴上；零点取昨收而不是当日开盘改的是画出来的数；
交易日改的是画面上的选择与重画路径；排布是下拉接上了没有、切过去有没有重画；导出是那条
路走不走得到编码器 —— 都发生在页面里，离线脚本一样也证明不了。

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

# 收尾那排卡片所在的横带，画面高度的比例。绘图区在它上面结束（曲线与末端标签都夹在
# 绘图区里），进度条在它下面（恒被 `band_hues` 排除）。页边距那四个偏好怎么调，卡片都
# 落在这条带里 —— 所以这里可以按比例写，而不必去问「卡片到底在第几行」。
CARD_LO = 0.70
CARD_HI = 0.97


def package_state_file(name):
    """应用 LocalState 里的一个文件，包名不写死。

    这台机器上只有一个带 `MarketMotionStudio` 的包文件夹，找出来就是了 —— 把 `8166Yxw....`
    那一串写进脚本，等于把某一次安装当成了事实。
    """
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Packages")

    if not os.path.isdir(base):
        return None

    for entry in os.listdir(base):
        if "MarketMotionStudio" not in entry:
            continue

        path = os.path.join(base, entry, "LocalState", name)

        if os.path.exists(path):
            return path

    return None


LOG = package_state_file("crash.log")


def log_size():
    """应用自己那份诊断日志现在有多长。

    按**偏移量**等新行，而不是按内容找：这一跑里 `encode: enter` 之前出现过多少次都不算数，
    算数的是**按下去之后**多出来的那一行。
    """
    try:
        return os.path.getsize(LOG)
    except (OSError, TypeError):
        return 0


def wait_log(offset, needle, seconds):
    """等日志从 `offset` 之后长出含 `needle` 的一行，返回是否等到。"""
    deadline = time.time() + seconds

    while time.time() < deadline:
        try:
            with open(LOG, "rb") as handle:
                handle.seek(offset)
                grown = handle.read().decode("utf-8", "replace")
        except (OSError, TypeError):
            grown = ""

        if needle in grown:
            return True

        time.sleep(1.0)

    return False


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
    检索框的下缘当零点。跑到后半程面板会被别处的聚焦滚下去，那时零点不在视口里，两处一起
    认错人。`ScrollItemPattern.ScrollIntoView` 正是 UIA 给的「把这一项滚进来」，也是真人会
    做的动作。

    **这一段是补过的，而且原来那句从来没有生效过。** 原来写的是
    `ctrl.GetScrollItemPattern()`，而这一页的检索框在 uiautomation 里是个 `GroupControl`，
    它**没有**这个便捷方法 —— 实测恒抛 `AttributeError: 'GroupControl' object has no
    attribute 'GetScrollItemPattern'`，被那句 `except` 吞掉。于是「滚回视口」这件事一次都
    没发生过，而它看起来是发生了：函数照常返回控件，调用方接着按位置量。改用
    `GetPattern(PatternId.ScrollItemPattern)`（这个在每一类 Control 上都有），拿不到或者
    调用失败就退到容器自己那条路（见 `panel_top`）。
    """
    ctrl = vc.find(lambda c: c.AutomationId == automation_id, win)

    if ctrl is None:
        return None

    try:
        if not ctrl.IsOffscreen:
            return ctrl
    except Exception:  # noqa: BLE001 - 读不到就当作要滚
        pass

    pattern = vc.pat(ctrl, auto.PatternId.ScrollItemPattern)
    scrolled = False

    if pattern is not None:
        try:
            pattern.ScrollIntoView()
            scrolled = True
        except Exception:  # noqa: BLE001 - 有的容器给了模式但调用会失败
            scrolled = False

    if not scrolled:
        panel_top(win)

    time.sleep(1.0)

    return vc.find(lambda c: c.AutomationId == automation_id, win)


def panel_top(win):
    """把右侧面板滚回顶部，返回那个容器是否真的动了。

    `into_view` 那条路不够用（见它上面那段），所以这里走**容器自己**的滚动条位置。

    容器的认法只能靠 `ClassName`：面板那个 `ScrollViewer` 在 UIA 里是 `PaneControl`，
    **不是** `ScrollViewerControl`（实测按名字找不到任何 `ScrollViewerControl`，而
    `ClassName == "ScrollViewer"` 有八个）。再要求它把检索框装在里面，才不会被清单那个
    自己的滚动条认成面板。

    为什么非滚回来不可：与检索框交互（展开下拉、选一行）本身就会把面板滚下去 —— 实测
    滚到 28.09%，检索框的矩形变成 `(0,0,0,0)`、`IsOffscreen` True。而按**位置**认控件的
    那两处（清单那一排、一键预设那一排）都以检索框的下缘当零点：零点不在视口里，两处一起
    认错人。实测「一键预设」读到 **0 个**（页面上明明有四个），而状态条上还留着上一句成功
    的话 —— 认错人之后每句话都还通顺。
    """
    def holds_the_search(box):
        return vc.find(lambda c: c.AutomationId == "InstrumentSearch", box, limit=8) is not None

    found = False

    for box in vc.find_all(lambda c: c.ClassName == "ScrollViewer", win):
        if not holds_the_search(box):
            continue

        pattern = vc.pat(box, auto.PatternId.ScrollPattern)

        try:
            if pattern is not None and pattern.VerticallyScrollable:
                pattern.SetScrollPercent(auto.ScrollPattern.NoScrollValue, 0)
                found = True
        except Exception:  # noqa: BLE001 - 容器可能在这一趟里消失
            continue

    if found:
        time.sleep(1.0)

    return found


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


def drop_chip(win, code, name):
    """把一只从**共享清单**上摘掉（chip 右边那个 ×），返回是否摘掉。

    认那个 × 只能在**开关的父节点里**找：它自己的 `AutomationId` 是空的（`WatchlistPicker.xaml`
    里两套模板都一样），而按名字找会碰到页面上别处同名的按钮 —— 检索建议里就有同一个名字。
    父节点里那个 `ButtonControl` 是唯一的，所以这一条不含猜测。

    为什么需要它：这一段要凑够四只，而共享清单是**用户自己的数据**。一键预设点一下就「把这只
    放到清单上并画出来」，不在这份清单上的预设按下去就会永久留上去 —— 用完了要放回原样。
    """
    toggle = vc.find(lambda c: c.AutomationId == code, win)

    if toggle is None:
        return False

    try:
        parent = toggle.GetParentControl()
    except Exception:  # noqa: BLE001 - 取不到父节点，下面按窗口找
        parent = None

    for box in (parent, win):
        if box is None:
            continue

        # `vc.find` 的第三个位置参数是 **depth**（第四个才是 limit），所以这里把它写全：
        # 在父节点里只搜三层，免得一路搜到页面上别处同名的按钮去。
        button = vc.find(
            lambda c: c.ControlTypeName == "ButtonControl"
            and not c.AutomationId
            and (box is parent or c.Name == name),
            box, 0, 6 if box is parent else 12)

        if button is not None:
            return vc.click(button, 1.5)

    return False


def clear_chips(win, tries=8):
    """把清单里的开关全关掉，**连着两次数到 0 才算**，返回 `(是否关干净, 说明)`。

    「连着两次」是补上去的，原因和这一段的其它几处一样：清单是**异步读**进来的。实测
    第一遍读到 8 只、全关掉、报「关干净了」，随后页面自己把存住的那一只又点亮了回来 ——
    于是「点一下预设就是清单上多一只」读到 **2 只**（多出来的那只不是点出来的），而它的
    下一句「一只时样式下拉是可用的」跟着红：那会儿画的已经是两只的比较了。两句话都通顺，
    只有数不对，而数不对已经被下一句掩盖成「下拉坏了」。

    所以干净的判据不是「这一眼看到 0」，是「隔一秒再看还是 0」。

    说明那一半是给失败看的：这一条红的时候有两个完全不同的原因 —— 开关真的关不掉，或者
    一个 chip 都没读出来（窗口不在前台、清单还没画）。两者的「没关干净」长得一样。

    清单是跨会话共享的一份，而且它的开关状态**跟内容一起落盘** —— 实测刚进页面时
    「创业板指」就是开着的，那是上一轮留下的。页面刚打开那一下共享清单还是异步读的，
    这时 chips 一个都读不到，「全关掉」于是等于什么都没做，随后点一个预设会把**它**加到
    已经开着的那只上：于是「点一下预设就是清单上多一只」读到两只，画面画的是两条曲线 ——
    而这一跑要的是「一只 → 两只」那两步。
    """
    seen = 0
    clean = 0

    for _ in range(tries):
        live = chips(win)

        if not live:
            clean = 0
            time.sleep(1.5)
            continue

        on = [c[1] for c in live if c[2].ToggleState == auto.ToggleState.On]

        if not on:
            clean += 1

            if clean >= 2:
                return True, f"关干净了（清单上 {len(live)} 只，隔一秒还是 0）"

            time.sleep(2.0)
            continue

        clean = 0

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


def band_hues(name, lo=0.0, hi=1.0, step=2, least=60):
    """画面里**某一条横带**上出现了几种赛道色。

    与 `analyse` 同一次取样，交出的是色相桶而不是个数：问「这帧是几只的」要的是种类，
    而两种颜色各画了三百个像素，在「个数」那一半上长得一模一样。

    `lo` / `hi` 是画面高度的比例（0 是顶、1 是底），所以画布大小变了也不用改数 —— 两次
    实拍的画布可能不一样大。最下面 3% 恒被排除在外：那一条是进度条，它铺满整幅宽，混进
    来就是一条永远在那儿的墨迹（见 `analyse`）。

    取**色相**而不是 RGB：画布是近黑的、描边与大字都按浓度淡入淡出，同一条赛道色在收尾
    那一段里每个像素都不相等，而色相不变。
    """
    if name is None:
        return None

    whole = Image.open(name if os.path.isabs(name) else os.path.join(OUT, name)).convert("RGB")
    box = winui.canvas_box(whole)

    if box is None:
        return None

    left, right, top, _ = box
    bottom = winui.frame_bottom(whole, box) or box[3]
    height = bottom - top
    pixels = whole.load()

    y0 = max(top, int(top + (height * lo)))
    y1 = min(int(top + (height * hi)), int(bottom - (height * 0.03)))
    hues = {}

    for y in range(y0, y1, step):
        for x in range(left, right, step):
            r, g, b = pixels[x, y]

            if max(r, g, b) - min(r, g, b) < 70 or max(r, g, b) < 90:
                continue

            hue = int(colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 12)
            hues[hue] = hues.get(hue, 0) + 1

    return frozenset(hue for hue, count in hues.items() if count >= least)


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


def amber(r, g, b):
    """`Palette.Moving` 那个琥珀 —— 单标的表头日期也是这个色。"""
    return r > 170 and 110 < g < 225 and b < 120 and (r - b) > 90


def cool(r, g, b):
    """`Palette.Muted` 那种偏蓝的灰：副标题、轴标签、网格都是它。"""
    return (b - r) > 25 and 90 < max(r, g, b) < 235


def header_bands(name, lo=0.10, hi=0.33):
    """画面上半段里每一条墨迹带：起、止、高几个像素、墨迹几个、其中琥珀几个、偏冷几个、列剖面。

    比例都是画面高度的比例 —— 两次实拍的画布可能不一样大（状态条一长，预览就按 9:16 缩），
    按像素写就会红在一个没坏的画面上。而**列剖面**是这一处的新东西：比「两条带是不是同一幅
    墨」要的是逐列的墨，不是总数 —— 同一个钟点的墨迹总数在两次实拍之间可以一模一样（`15:00`
    与 `11:00` 就是一例），差的是哪一列有墨。

    `hi` 停在绘图区（`PlotTopFraction` 0.34）之上：再往下扫，轴与曲线连成的墨会把这一块并进去。

    画布那块矩形问 `winui.canvas_box`，下缘用**它自己给的那个**。它现在的下缘是由宽度按 9:16
    反推出来的（见那里的注释），而 `frame_bottom` 那趟往下走会跨过画布下面那排控件、走到页面
    上（实测把 851 说成 924，低 73 像素）—— 认错下缘等于把比例的分母换掉，两条带的位置会
    一起错一成。
    """
    if name is None:
        return None, None

    whole = Image.open(name if os.path.isabs(name) else os.path.join(OUT, name)).convert("RGB")
    box = winui.canvas_box(whole)

    if box is None:
        return None, None

    left, right, top, bottom = box
    height = bottom - top
    pixels = whole.load()
    rows = []

    for y in range(int(top + (height * lo)), int(top + (height * hi))):
        ink = gold = blue = 0
        across = []

        for x in range(left + 2, right - 2):
            r, g, b = pixels[x, y]

            # 一行里两个以上亮像素才算墨：抗锯齿的边缘是一个一个的孤立点。
            if max(r, g, b) < 110:
                across.append(0)

                continue

            ink += 1
            across.append(1)

            if amber(r, g, b):
                gold += 1

            if cool(r, g, b):
                blue += 1

        rows.append((y, ink, gold, blue, across))

    out = []
    run = None

    for y, ink, gold, blue, across in rows:
        if ink >= 2:
            if run is None:
                run = [y, y, 0, 0, 0, []]

            run[1] = y
            run[2] += ink
            run[3] += gold
            run[4] += blue
            run[5].append(across)
        elif run is not None:
            out.append(tuple(run))
            run = None

    if run is not None:
        out.append(tuple(run))

    width = max(1, right - left)
    step = width / 48
    bands = []

    for begin, end, ink, gold, blue, across in out:
        if ink < 12:
            continue

        profile = [0] * 48

        for row in across:
            for i in range(48):
                profile[i] += sum(row[int(i * step):int((i + 1) * step)])

        bands.append({
            "lo": (begin - top) / height,
            "hi": (end - top) / height,
            "tall": end - begin + 1,
            "ink": ink,
            "gold": gold,
            "blue": blue,
            "profile": profile,
        })

    return bands, box


def spread(one, two):
    """两条带的墨差多少，0..1：48 格列剖面逐格差的绝对值之和 ÷ 两幅的墨迹总数。

    与 `band_diff` 不同，它比的是**同一条带自己**在两个进度下的墨，所以别处变了不算 —— 这一条
    要问的正是「那一行变了没有」，而整幅或整条画布带在别的地方也在变（曲线、轴、卡片都跟着
    进度动），拿它们当尺子量不出「这一行」。
    """
    return (sum(abs(p - q) for p, q in zip(one["profile"], two["profile"]))
            / max(1, one["ink"] + two["ink"]))


def main():
    # ---- 源码：当日涨跌幅 ------------------------------------------------------------
    series = read("Market", "CandleSeries.cs")
    render = read("Render", "CandleRenderer.cs")
    frame_ctx = read("Render", "FrameContext.cs")
    intraday = read("Render", "IntradayRenderer.cs")
    turnover = read("Render", "TurnoverRenderer.cs")

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
    split = read("Render", "CandleSplitRenderer.cs")
    line = read("Render", "CandleLine.cs")
    cards = read("Render", "TrackCards.cs")
    position = read("Render", "PositionRenderer.cs")
    dca = read("Render", "DcaRenderer.cs")
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
    check("页面在选了 2 个以上时改画比较",
          "drawn, plan, ChosenMotion(), ChosenWindow(), CrossSafeRight())" in page)
    check("蜡烛图那一排样式在多标的下是灰的（不然就是三个被忽略的设置）",
          "StyleCombo.IsEnabled = _board is null" in page)
    check("清单那一排是可开关的",
          "Selectable=\"True\"" in xaml and "WatchlistPicker" in xaml)

    # ---- 源码：分图（每只一张图，上下排列，最多三只） ------------------------------
    #
    # 这一版的两半：**合图**是一张轴上几条百分比曲线，**分图**是一只一格、各有各的纵轴。
    # 分图上限三只不是调色板的限制（那是 `MostTracks = 6`），是格子的高度 —— 三格时一格
    # 约帧高的九分之一，第四格就剩不到一百像素的绘图区。
    check("分图最多三格（第四格就没有绘图区了）",
          "public const int MostPanels = 3;" in board)
    check("分图时把板子重建到前三只 —— 从轴上也掉，不只是不画",
          "CandleBoardLoader.Only(board, CandleBoardLoader.MostPanels)" in page
          and "[.. series.Take(count)], board.Period, board.Skipped, board.Sessions, board.Drawn);"
          in board)
    check("板子带着它那几份序列（所以重画不用再取一遍）",
          "IReadOnlyList<CandleSeries>? Series = null" in board
          and "sessions, drawn, series);" in board)

    # 两种排布画的是同一套家具。安全线那套算术只有一处（`CandleLine`）：两份各自写着
    # 「每句都通顺、合起来就是两种答案」是最难看出来的一种错。
    check("末端标注走的是三页共用那一处安全线算术",
          "context.SafeRight(giveWay)" in line
          and "widest, context.Px(LabelGap + LabelEdgePad), giveWay);" in line)
    check("合图里不再留着它自己的第二份（搬走之后没有留下来的那一份）",
          "RightLabelColumn" not in racer and "SafeRight(" not in racer
          and "LabelGap" not in racer)
    check("两种排布画的是同一套家具：轴、曲线、末端标签、标题",
          all(("CandleLine." + what + "(") in racer and ("CandleLine." + what + "(") in split
              for what in ("Axis", "Curve", "EndLabel", "Header")))
    check("日期行只画一次，画在最下面那格底下（x 轴是整帧的，不是一格的）",
          split.count("CandleLine.XLabels(") == 1
          and "XLabels" not in split.split("private void DrawPanel(")[1]
              .split("private static (double Lo")[0])
    check("一个标签列给整帧（三格同宽，同一个 x 才对得上）",
          split.count("CandleLine.LabelColumn(") == 1
          and split.index("CandleLine.LabelColumn(")
          < split.index("for (var k = 0; k < tracks.Count; k++)"))
    check("分图里的标签夹在自己那一格内（不许掉到下一格上）",
          "panelTop, panelBottom, introA, _giveWay);" in split)

    # ---- 源码：收尾那排卡片 ----------------------------------------------------------
    #
    # 用户要的「最下方显示多标的涨幅」：两种排布都收在同一排上，每只一张，大数字是涨幅%，
    # 小字是涨跌额。这一排是从持仓页那排抽出来共用的，所以持仓页与定投页也走同一处。
    check("两种排布都收在同一排卡片上",
          "TrackCards.Draw(session, context, cards, a, _giveWay);" in racer
          and "TrackCards.Draw(session, context, cards, a, _giveWay);" in split)
    check("卡片的大数字是涨幅%、小字是涨跌额",
          "CandleLine.Percent(track.Final)" in racer
          and "Amount(track.Baseline * track.Final / 100)" in racer
          and "CandleLine.Percent(track.Final)" in split
          and "Amount(track.Baseline * track.Final / 100)" in split)
    check("卡片行只有一处：持仓页与定投页也用这同一行",
          "TrackCards.Card(" in position and "TrackCards.Card(" in dca
          and "TrackCards.Draw(session, context, cards, a, _giveWay);" in position
          and "TrackCards.Draw(session, context, cards, a, _giveWay);" in dca)

    # 那排卡片也得让开右侧那条按钮栏。这一条是**真机先红出来的**：加了卡片之后「最右墨迹
    # 在安全线以内」那条从绿变红 —— 卡片按整幅绘图区宽铺，右缘落在按钮栏里 44 px（帧宽
    # 18% 是 194，右页边距只有 150）。而它是**内容**：一个数字被头像压住，比曲线越线更糟。
    # 算术在 `FrameContext` 一处（`CardRowRight`），六处都调它：K 线两种排布共用那排收尾卡，
    # 加上五页的四张统计卡。判据里问的是「有没有第二份算术」，不是「某一页有没有让」——
    # 一份一份地问，第五页就会有一份自己的。
    check("卡片行也让开那条按钮栏（算术只在一处，六处都调它）",
          "context.CardRowRight(giveWay)" in cards
          and "public double CardRowRight(double giveWay = 1) => "
              "Math.Min(ChartRight, SafeRight(giveWay));" in frame_ctx
          and all("context.CardRowRight() - left" in src
                  for src in (render, dca, position, intraday, turnover)))
    check("这一页两种画面收在同一处家具上（与单标的那张图同一个总数）",
          "public const double CreditGap = TrackCards.CreditGap;" in racer
          and "public const double CreditGap = TrackCards.CreditGap;" in split
          and "public const double CreditGap = 430;" in render
          and "AboveCredit = 192" in cards and "DateRowRoom = 238" in cards)

    # ---- 源码：头部那两行时间（用户报「多标的时候没有时间」） ------------------------
    #
    # 单标的的画面在表头就写着那根 K 线的日期（`CandleRenderer.DateRow`，琥珀色 34 px），比较
    # 画面只写了代码与周期，把「哪一段」整个交给了脚下那条日期轴。而那条轴是**刻度**，不是一句
    # 话：它跟着窗口走，收尾展开时才铺满整段，而且一个被问「这是哪天」的人不会去读轴。
    #
    # 用户随后又报了两件事（2026-10-09）：「9:30 - 15:00 太小」与「要时时刻刻的钟点，而不是
    # 9:30 - 15:00」。于是第二行从**区间**改成**画面画到的那一刻** —— 窗口的右缘，也就是每条
    # 曲线领头处所在的那一列 —— 并按画面大字的字号（128）画。区间那句话的毛病是它说的不是画面：
    # 下午走了四分之三的那一帧与整段的末帧写着同一句话，而观众跟着看的正是「走到哪儿了」。
    #
    # 分岔只在一处（`board.Intraday`）：分钟线写那一刻的钟点，日/周/月线写区间的末一天 ——
    # 后者的「最新时刻」本来就是一个日期，所以还是同一条规则。两种排布共用一处画
    # （`CandleLine.Header`）—— 一份一份地问，第二份就会有自己的答案。
    check("多标的头部有日期与大字两行（一处画，两种排布共用）",
          "public const double DateRow = 0.235;" in line
          and "public const double MomentRow = 0.305;" in line
          and "public const double MomentSize = 128;" in line
          and "TimeBlock(session, context, board, titleLines, moment, a);" in line
          and line.count("private static void TimeBlock(") == 1)
    check("第二行是**画面画到的那一刻**，不是一整段区间（分岔只在一处）",
          "board.Intraday" in line
          and "board.Stamps[at]" in line
          and "CandleLoader.Iso(board.End)" in line
          and 'board.Stamps[0] + " - " + board.Stamps[^1]' not in line)
    check("那个「一刻」就是窗口的右缘（头部与曲线领头处说的是同一件事）",
          "double t, double moment)" in line
          and racer.count("Math.Max(0, head));") == 1
          and split.count("Math.Max(0, head));") == 1)
    check("空板子不画这两行（头部在两种排布决定画不画之前就画了）",
          "if (board.Count <= 0)" in line)

    # 两行都得落在绘图区**上面**，否则标题压着曲线。行数是从源文件里读出来的再比，不是把
    # 0.235 / 0.305 抄一遍 —— 抄一遍的话，谁把某一行挪到绘图区里，这条还绿着。
    rows_of = lambda src, key: float(  # noqa: E731 - 一处算术，不要两份
        re.search(key + r" = ([0-9.]+);", src).group(1))

    check("两行都在绘图区之上（标题不压着曲线）",
          rows_of(line, "DateRow") < rows_of(line, "MomentRow")
          and rows_of(line, "MomentRow") < rows_of(racer, "PlotTopFraction")
          and rows_of(line, "MomentRow") < rows_of(split, "PlotTopFraction"),
          f"日期 {rows_of(line, 'DateRow')} / 大字 {rows_of(line, 'MomentRow')}"
          f" / 绘图区 {rows_of(racer, 'PlotTopFraction')}")

    # 两行现在**不是**一个 pitch 的距离，而这一点是要验的：第二行是大字（128），而一行字占了
    # 行距就装不下它的墨 —— 照抄一个 pitch（0.035 ≈ 67 px）的话，那行字会画进上面那行日期里，
    # 而画面看着像「日期重影」。所以问的是「间距够不够那行字自己的高度」，不是「是不是 0.035」。
    check("两行的间距够那行大字的墨（不是照抄一个行距）",
          "public const double HeaderRowPitch = 0.035;" in frame_ctx
          and (rows_of(line, "MomentRow") - rows_of(line, "DateRow")) * 1920
          > rows_of(line, "MomentSize") * 0.72,
          f"间距 {(rows_of(line, 'MomentRow') - rows_of(line, 'DateRow')) * 1920:.0f} px，"
          f"那行字高 {rows_of(line, 'MomentSize') * 0.72:.0f} px")

    # 字号本身：那一行得是这一块的头号 —— 比日期大一倍以上、加粗。用户说的原话是「和持仓收益
    # 百分比大小」，而持仓页那个数字是 128 加粗；这条不问 128 抄对没有（那有上面一条），问的
    # 是「它有没有大到成为这块的头号」。
    check("那行大字是这一块的头号（比日期大一倍以上，且加粗）",
          rows_of(line, "MomentSize") >= rows_of(line, "DateSize") * 2
          and "Ink.Format(context.Px(MomentSize), bold: true)" in line,
          f"{rows_of(line, 'MomentSize')} 对日期 {rows_of(line, 'DateSize')}")

    # ---- 源码：这个选择在页面上 ------------------------------------------------------
    check("排布下拉是比较画面自己的设置（一只时是灰的，与「画法」那条相反）",
          "SplitCombo.IsEnabled = _board is not null;" in page
          and "StyleCombo.IsEnabled = _board is null" in page)
    check("分图时才解释「最多 3 只」（合图没有这回事）",
          "SplitNote.Visibility = _board is not null && ChosenSplit() is CandleSplit.Apart"
          in page)
    check("这个选择是存住的（读一次、写一次）",
          page.count('"Split"') >= 2, str(page.count('"Split"')))
    check("第 4 只起在状态行里点名，不是悄悄不画",
          "CandleSplitTrimmed" in page
          and "board.Tracks.Skip(CandleBoardLoader.MostPanels)" in page)
    check("切排布不重新取数（下拉只改画法）",
          re.search(
              r"OnLookChanged\(object sender, object e\)\s*\{\s*if \(!_ready\)\s*\{\s*return;\s*\}"
              r"\s*ApplyPreviewSettings\(\);\s*SavePreferences\(\);", page) is not None,
          "" if "void OnLookChanged" in page else "OnLookChanged 不见了")

    # ---- 源码：导出的守卫（用户报「导出 MP4 没响应」） --------------------------------
    #
    # 这一条是用户那一句报出来的，而它出问题时的样子**一点声响都没有**：按钮是亮的
    # （`ExportButton.IsEnabled = _fetched is not null || _board is not null` 把两条来源都算
    # 上了），画面好好地画着，按下去既不弹框、也不写状态行、也不报错、也不写文件，日志里
    # 干干净净 —— 因为那两个导出处理器的守卫只问了**序列**，而比较画面**故意把序列清空**
    # （留着板子），于是每一次按下都从第一行静默返回。
    #
    # 这一页是唯一一个「两个数据源画两张画」的页面：另外十六页各只有一处来源、各问一处，
    # 照抄它们的写法正是这个缺陷的来源。所以判据问的是「守卫是不是只有一处」，不是
    # 「这个处理器里改没改」—— 一处一处地问，第二个处理器就会有一份自己的答案。
    #
    # 而**先例本来就在**：成交额页（唯一另一个有两种视图的页面）的守卫问的是 `SeriesRange()`
    # —— 那正是「两处来源，取在的那一处」。所以这一页是照抄错了对象，不是没东西可抄。
    # 那一条别的页面的原文这里**不钉**：钉住它，等于让它以后被一次合法的重构判红。
    check("导出的守卫问的是一处，而不是只问序列",
          page.count("FrameSpan is not { } span") == 2
          and "_fetched is not { } fetched || App.Window" not in page)
    check("那一处同时读两条来源（比较画面把序列清空了，板子在）",
          "private (DateOnly Start, DateOnly End)? FrameSpan =>" in page
          and "board.Start, board.End" in page
          and "fetched.Start, fetched.End" in page)
    check("视频与封面两个文件名都从那一处取日期",
          page.count("span.Start, span.End, format)") == 2)
    check("按钮的可用性问的是同一件事（两条来源都算，所以守卫也得两条都收）",
          "var ready = _fetched is not null || _board is not null;" in page
          and "ExportButton.IsEnabled = ready;" in page
          and "CoverButton.IsEnabled = ready;" in page)

    resw = sorted(
        d for d in os.listdir(os.path.join(SRC, "Strings"))
        if os.path.isfile(os.path.join(SRC, "Strings", d, "Resources.resw")))
    keys = ("CandleSplitLabel.Header", "CandleSplitTogether", "CandleSplitApart",
            "CandleSplitNote.Text", "CandleSplitTrimmed")
    missing = [f"{d}/{k}" for d in resw for k in keys
               if f'<data name="{k}"' not in read("Strings", d, "Resources.resw")]

    check("14 种语言都有分图那五条（下拉的标签、两项、说明、点名）",
          len(resw) == 14 and not missing,
          f"{len(resw)} 种语言；缺 {missing[:4]}" if missing else f"{len(resw)} 种语言")

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

    # 推进方式是**落盘的偏好**，而末帧的形状由它决定：窗口滚动的最后一段会展开成完整区间，
    # 让位量跟着同一个斜坡走到 0，末端标注因此跑到画面右缘 —— **与打开越线开关同一个位置**
    # （x=1129 对安全线 1065）。这一条问的是「关着时收在安全线以内」，所以先拨回逐根铺满：
    # 前面跑的那几份判据会把偏好留在滚动上，而落盘的偏好是跨会话的，默认值只在「从没跑过
    # 别的判据」时才成立。
    #
    # 放在 `panel_top` **之前**：挑下拉要与面板交互，交互会把面板滚下去，而按位置认控件的
    # 那两处（`chips`、`presets`）都以检索框下缘当零点 —— 实测放在取数之后那一处，预设会读
    # 到 0 个，而两幅「应当一模一样」的画差出 4.5%。先摆偏好，再定面板的起点。
    check("推进方式拨回逐根铺满（末帧的形状由它决定）",
          winui.combo_pick(win, vc.find(lambda c: c.AutomationId == "MotionCombo", win),
                           "逐根铺满") is not None)

    # 越线开关同样先拨回关，而且理由更硬：它是这一跑里**唯一能把墨迹推出安全线**的东西
    # （打开时末端标注跑到画面右缘，x=1129 对安全线 1065），而下面那两条「末端标注在安全线
    # 以内」问的正是关着的样子。实测红过一次：上一跑到一半被锁屏掐断，开关留在开上，而落盘的
    # 偏好是跨会话的 —— 于是这两条量到 1129，而同一份脚本后面复位过的那一处量到 1065。**默认
    # 值只在「从没跑过别的判据」时才成立**，与推进方式是同一件事。
    #
    # 放在 `panel_top` **之前**，也是同一个理由：拨开关要与面板交互，交互会把面板滚下去。
    check("越线开关先拨回关（末端标注那两条问的是关着的样子）",
          cross(win, False) == auto.ToggleState.Off)

    # 面板的起点也定死：清单与一键预设都是**虚拟化**的一排，滚到哪儿决定了哪几项被实例化，
    # 而按位置认控件的那两处又都以检索框下缘当零点。从同一个地方起，这一跑的每一步才和
    # 上一次可比。
    panel_top(win)

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

    # ---- 头部那两行：日期不动，大字钟点跟着画面走（真机） ------------------------------
    #
    # 用户在两句报里说了三件事：「多标的时候图表和标题没有时间」、「9:30 - 15:00 太小」、
    # 「要时时刻刻的钟点，而不是 9:30 - 15:00」。所以这一条问的是三件事，而不是「第 0.235 行
    # 有没有字」：
    #
    #   1. 日期下面那一行是这块里**最高**的一条墨（字号就是在这件事上看得见的）；
    #   2. 日期那一行**不随进度变** —— 它是「这是哪一天」，一个事实；
    #   3. 大字那一行**随进度变** —— 它是「走到哪儿了」。
    #
    # 第 2 条是第 3 条的**对照**，而且是一个硬的对照：两幅真的不同的画面之间，日期那一行的墨
    # 实测一格不差（0.0000），因为两幅画的都是同一天。只验第 3 条的话，「两幅画面本来就处处
    # 不同」也能让它绿；只验「有两条带」的话，把钟点写死在 15:00 也照样绿。
    #
    # 三个进度而不是两个：第二行要跟着走，那它在**每一对**之间都该变。
    #
    # 认颜色、认高矮，不认字：预览画布没有自动化节点。日期是唯一琥珀色的那条，大字是它下面墨
    # 最多的那条。比的是**同一条带自己**在不同进度下的列剖面（`spread`），不是整幅差 —— 曲线、
    # 轴、卡片都在跟着进度动，用它们当尺子量不出「这一行」变了没有。
    # 三个进度而不是两个，而且**三个值互不相同**：同一个值再设一次不触发控件的变更，于是
    # `Playback.Seek` 不会被调到（它才是那句把画面钉住的话），抓回来的可能是上一次那一幅。
    # 实测过：同一个 0.35 连拍两次，第二张是另一幅画面。
    shots = []

    for tag, at in (("end", 1.0), ("mid", 0.6), ("early", 0.3)):
        vc.scrub_to(win, at)
        bands, box = header_bands(vc.shot(win, f"verify-candle-multi-moment-{tag}.png"))
        shots.append((at, bands, box))

    check("三个进度都认得出画布（量那两行得先有画布）",
          all(bands is not None for _, bands, _ in shots))

    if all(bands is not None for _, bands, _ in shots):
        # 三次实拍的画布得一样大：列剖面按画布宽分 48 格，宽度一换，两次的格子里装的就是不同的
        # 东西，比出来的差是取样差不是画面差。
        check("三次实拍的画布一样大（列剖面比的是同一块地方）",
              len({box for _, _, box in shots}) == 1,
              str([box for _, _, box in shots]))

        def parts(bands):
            sub = next((b for b in bands if b["blue"] >= 40), None)
            day = next((b for b in bands if b["gold"] >= 40
                        and (sub is None or b["lo"] > sub["hi"])), None)
            below = [b for b in bands if day is not None and b["lo"] > day["hi"]]
            big = max(below, key=lambda b: b["tall"]) if below else None

            return day, big

        seen = [parts(bands) for _, bands, _ in shots]

        check("副标题下面有日期那一行（琥珀色，画面上只有它是这个色）",
              all(day is not None for day, _ in seen),
              "、".join(f"{b['lo']:.3f}..{b['hi']:.3f} 琥珀 {b['gold']}"
                        for b in shots[0][1]) or "一条墨迹带都没有")

        check("日期下面那一行是这块里最高的一条墨（比日期高一倍以上）",
              all(day is not None and big is not None and big["tall"] >= day["tall"] * 2
                  for day, big in seen),
              "、".join(f"{b['lo']:.3f}..{b['hi']:.3f} 高 {b['tall']} px"
                        for b in shots[0][1]))

        # 两个差都先算出来再断言：`check` 的第三个参数是**当场求值**的实参，写进那一行里
        # 会在「根本认不出那两行」的那一跑上先把 `spread(None, …)` 抛出来。
        kept = (spread(seen[0][0], seen[1][0]), spread(seen[0][0], seen[2][0])) \
            if all(day is not None for day, _ in seen) else None
        moved = (spread(seen[0][1], seen[1][1]), spread(seen[0][1], seen[2][1])) \
            if all(big is not None for _, big in seen) else None

        check("日期那一行不随进度变（它是「这是哪一天」，不是「走到哪儿了」）",
              kept is not None and max(kept) < 0.01,
              "认不出日期那一条" if kept is None else "、".join(f"差 {d:.4f}" for d in kept))
        check("大字那一行随进度变（那个钟点跟着画面走，不是写死的区间）",
              moved is not None and min(moved) > 0.03,
              "认不出大字那一条" if moved is None else "、".join(f"差 {d:.4f}" for d in moved))

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

        restored = vc.wait_status(win, unlike=vc.status_text(win), seconds=150)

        # 这一次取数**必须**成：下面分图那一段拿「比较画面在不在」当探针，而一次失败的
        # 取数会把板子留成空的 —— 于是排布下拉是灰的、`combo_labels` 读到 **0 项**，读成
        # 「下拉里没有分图这一项」，其实是这一次根本没取到。实测就这样红过一跑，而那条红
        # 报的是一个没坏的控件。
        if not restored or BAD.search(restored):
            stale = vc.status_text(win)
            vc.click(vc.find(lambda c: c.AutomationId == "FetchButton", win), 1.0)

            retry = vc.wait_status(win, unlike=stale, seconds=180)

            check("切回原来的周期之后取数正常（第一次没成，补了一次）",
                  bool(retry) and not BAD.search(retry or ""), retry or "(状态条空)")

    # 蜡烛那几条要在日 K 上量：分钟档下这一页画的是同一条曲线，不是蜡烛。
    check("回到日K（蜡烛那几条要在日K上量）",
          vm.combo_selected(win, period_combo) == PERIOD_DAILY,
          str(vm.combo_selected(win, period_combo)))

    # ---- 分图：一个下拉，两种排布，和收尾那排卡片 ------------------------------------
    #
    # 用户要的三件事都在这一段：一个下拉在「同一张图」与「每只一张图」之间切；分图上下排列；
    # 两种排布的最下方都有一排卡片，每只一张，大数字是涨幅%、小字是涨跌额。
    #
    # 全是像素判据（预览画布没有自动化节点）：切过去有没有重画按两幅画的差异比；收尾那排
    # 卡片按「绘图区以下那条带里有没有赛道色」比 —— 那条带在收尾之前是空的，卡片是唯一会
    # 画进去的东西，所以这两个数一进一出就把「卡片在收尾时出现了」量出来了，不必知道卡片
    # 落在第几行（行位置随页边距的偏好走，写死就会红在一个没坏的画面上）。
    # 这一段量的是「比较画面」上的东西，所以先在页面自己身上确认比较画面在手上 —— 探针就是
    # 那个排布下拉：它是比较画面自己的设置，一只的图它是灰的。灰着就别往下量了，先补一次
    # 取数（周期来回是下一次取数才生效的，页面手上那块板子可能是旧周期的、也可能是空的）。
    if vc.enabled(win, "SplitCombo") is not True:
        stale = vc.status_text(win)
        vc.click(vc.find(lambda c: c.AutomationId == "FetchButton", win), 1.0)
        vc.wait_status(win, unlike=stale, seconds=180)

    # 这里**故意不** `into_view("SplitCombo")`：把面板滚到那个下拉会让它自己的滚动条出现
    # 或消失，右侧面板的宽度跟着变一点，预览按剩余宽度等比缩 —— 于是同一张画面前后两次
    # 量出来的画布不一样大，两幅「应当一模一样」的画差出四五个百分点。挑下拉靠的是
    # ExpandCollapse，不需要它进视口。
    split_combo = vc.find(lambda c: c.AutomationId == "SplitCombo", win)
    labels = winui.combo_labels(win, split_combo) if split_combo is not None else []

    check("页面上多了「分图显示」这个下拉，正好两项",
          len(labels) == 2, "、".join(labels) or "0 项")
    check("比较时排布下拉是能选的（它属于比较，不属于蜡烛图）",
          vc.enabled(win, "SplitCombo") is not False, str(vc.enabled(win, "SplitCombo")))
    check("合图时不解释分图（那条说明是收起来的）",
          vc.find(lambda c: c.AutomationId == "SplitNote", win) is None)

    vc.scrub_to(win, 1.0)
    together = vc.shot(win, "verify-candle-split-together.png")
    together_status = vc.status_text(win)

    if len(labels) != 2:
        check("排布下拉里挑得出两项", False, "、".join(labels))
    elif winui.combo_pick(win, split_combo, labels[1]) is None:
        check(f"挑到「{labels[1]}」", False)
    else:
        time.sleep(2.0)

        # 切排布不该发请求：那几份序列都在手上，换的是画法。真发了请求的话状态行会换一条。
        check("切排布不重新取数（状态行还是那一条）",
              vc.status_text(win) == together_status, str(vc.status_text(win))[:80])

        vc.scrub_to(win, 0.5)
        mid = vc.shot(win, "verify-candle-split-apart-mid.png")
        vc.scrub_to(win, 1.0)
        apart = vc.shot(win, "verify-candle-split-apart.png")

        moved = band_diff(together, apart)

        check(f"切到「{labels[1]}」画面真的重画了（不是只换了个标签）",
              moved > 0.02, f"画布带里 {moved:.1%} 的像素变了")

        strong_apart, far_apart, box_apart, right_apart = analyse(apart)

        if box_apart is None:
            check("分图那张照片里认得出画布", False)
        else:
            line_apart = round(box_apart[0] + ((box_apart[1] - box_apart[0]) * SAFE))

            check("分图画面上仍有两条赛道色（一格一条曲线）",
                  len(strong_apart) >= 2, str(strong_apart[:4]))
            check("分图的末端标注也在安全线以内（不进平台那条按钮栏）",
                  far_apart <= line_apart + 6,
                  f"最右墨迹 x={far_apart}，安全线 {line_apart}，画布右缘 {right_apart}")

        before = band_hues(mid, CARD_LO, CARD_HI, step=1)
        after = band_hues(apart, CARD_LO, CARD_HI, step=1)

        check("收尾之前，绘图区以下那条带是空的（曲线都还在绘图区里）",
              before is not None and len(before) == 0,
              f"{len(before) if before is not None else '读不出来'} 种色相")
        check("收尾时最下方出现那排卡片，每只一种赛道色",
              after is not None and len(after) >= 2,
              f"{len(after) if after is not None else '读不出来'} 种色相")
        check("分图时那条说明出来了（最多 3 只这件事被说出口）",
              vc.find(lambda c: c.AutomationId == "SplitNote", win) is not None)

        # 双向验：只验「切过去变了」的话，「下拉没接上、而画面本来就在动」也过得去。
        if winui.combo_pick(win, split_combo, labels[0]) is None:
            check(f"切回「{labels[0]}」", False)
        else:
            time.sleep(2.0)

            vc.scrub_to(win, 1.0)
            back = vc.shot(win, "verify-candle-split-back.png")
            again = band_diff(together, back)

            check("切回「同一张图」画回同一张", again < 0.02, f"{again:.1%} 不同")
            check("合图时那条说明又收起来了",
                  vc.find(lambda c: c.AutomationId == "SplitNote", win) is None)

    # ---- 一处检索，和一个越线开关 ----------------------------------------------------
    #
    # 安全线按**当前的**画布重量一次：上面那次是切换周期之前量的，而画布大小随状态条的长短
    # 走（预览按 9:16 等比缩，状态条多一行画面就窄一点）。
    vc.scrub_to(win, 1.0)
    remeasured = analyse(vc.shot(win, "verify-candle-multi.png"))

    if remeasured[2] is not None:
        _, far, box, right = remeasured
        line = round(box[0] + ((box[1] - box[0]) * SAFE))

    # 与检索框交互（展开排布下拉、选一行）会把面板滚下去，而 `into_view` 滚不回来（见
    # `panel_top`）。这一条量的是「页面上只有一个检索框」，不该由面板滚到哪儿决定。
    panel_top(win)

    boxes = visible_searches(win)
    check("页面上看得见的检索框只有一个（不再有两块「股票」）",
          boxes == [("InstrumentSearch", False)], str(boxes))

    check("页面上有「允许图形越过右侧安全线」，且带标签",
          bool(vc.label_of(win, "CrossCheck")), str(vc.label_of(win, "CrossCheck")))

    # 双向验：只验「打开后更靠右」的话，「开关根本没接上、两次都靠右」照样绿；只验「关着时
    # 在安全线内」的话，「开关接反了、关着反而越线」也绿。
    # 这一条**不叫「默认是关的」**：它先把开关拨到关再读回来，问的是「拨得回去」，而默认值早
    # 在上面复位那一步就被改过了 —— 那样的名字会在「默认值其实是开」时照样绿，而这句话本身
    # 是假的。默认值要验，得在跑过任何判据之前量。
    check("越线开关拨回关（下面两条像素都在这个前提下量）",
          cross(win, False) == auto.ToggleState.Off)

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
        # 与上一条**相反**，这就是「排布是比较画面自己的设置」那句话在真机上的那一面：
        # 一只的图没有「分不分」这回事。两条一起才说明这个开关是按画面接的，不是按有没有板子。
        check("退回一只后排布下拉变灰了（一只的图没有分不分这回事）",
              vc.enabled(win, "SplitCombo") is False, str(vc.enabled(win, "SplitCombo")))

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

    # ---- 分图只画前三只：第四只在状态行里被点名 --------------------------------------
    #
    # 上限三只是这一版定的，而「只画前 3 只」有两种做法：悄悄不画，或者把没画的那几只说出
    # 来。悄悄不画的话，读者要数一遍面板才发现清单上少了一只 —— 所以页面在点名。这一段要
    # 真的凑够四只才量得出来：只有三只时根本没有「被略过的」这件事。
    #
    # 画面上的判据是**「四只的那一张」与「把第 4 只关掉之后那一张」一模一样**。
    #
    # 这个对照的选法磕了两次，两次都值得记下来：
    #
    # - 先是「整帧只有三种赛道色」。实测不成立：分图的曲线是淡着画的，一条线在预览这个
    #   尺寸下几乎没有纯色像素，全是与近黑底的混色 —— 同一支紫（#A855F7，色相 271）混暗
    #   之后色相落到 268–270，跨过了 12 等分那条边界，于是**一支线数出两种色**。「第四只
    #   真画了」和「一支线被数成两种」在「几种色」这个数上是同一个数。
    # - 再是「另一组三只当对照」。实测差 3.8%，而差的不是多画了一只 —— **第三只本来就
    #   不是同一只**：清单的顺序就是看板的顺序，而这里点进来的次序按的是一键预设那一排
    #   的位置，两者不一样。于是对照里第 3 格是茅台、正式那张第 3 格是平安。
    #
    # 所以对照只能由**页面自己说的那一只**来定：状态行点名了「未画：X」，就把 X 关掉。
    # 剩下的正好是前 3 只，两张该逐像素一样。不一样才是「多画了一只」。
    check("面板能滚回顶部（不然下面按位置认控件的那两条会一起认错人）", panel_top(win))

    rows = presets(win)
    split_combo = vc.find(lambda c: c.AutomationId == "SplitCombo", win)

    # 顺序不能反过来：**一只时排布下拉是灰的**（它是比较画面自己的设置），所以先要点到两只
    # 才有板子、才能切分图；而点名只在分图下发生，所以第四只要在切过去之后再点。上一次跑
    # 就是在这里红的 —— 上一次这一段直接从一只起手去挑分图，`combo_pick` 返回 None，读成
    # 「下拉里没有那一项」，其实是那一项就在那儿、只是这一个下拉整个是灰的。
    #
    # 点的也必须是**此刻关着**的那几只：上一段留下的那一只正开着，而点一个已经开着的预设
    # 不会让清单多出第二只 —— 于是「凑到两只」这件事会悄悄不成立。
    live = chips(win)
    on = {c[0] for c in live if c[2].ToggleState == auto.ToggleState.On}

    # 清单是**异步读进来**的（`clear_chips` 那一节的教训），所以「本来就有哪些」连读两次取
    # 并集 —— 这个集合只用来决定「哪几只是**这一跑带进来的**、走的时候要摘掉」，只可能让
    # 摘的动作更保守：读漏了就会把读者自己的一只当成带进来的。
    before = {c[0] for c in live}
    time.sleep(1.5)
    before |= {c[0] for c in chips(win)}

    # 点的是**此刻没开着**的预设，只筛这一条。原来还多筛了一条「它已经在清单上」，那一条既是
    # 多余的、又把这一段挂在了**用户自己的清单里恰好有几只预设**上：一键预设本来就是「把这只
    # 放到清单上并画出来」，不在清单上的按一下照样上去。共享清单是用户数据、会变 —— 实测这份
    # 清单里只有两只是预设里的（上证指数、创业板指），于是「关着的预设」只剩 1 个，整段直接
    # 跳过：红的是「凑够四只」这句话，而页面是好的。
    todo = [row for row in rows if row.AutomationId not in on]

    # 还差几只到四只；`head` 是「先凑到两只」那一只 —— 一只时排布下拉是灰的（它属于比较画面），
    # 而「第 4 只被点名」只发生在分图下，所以顺序是：凑到两只 → 切分图 → 再点剩下的。
    need = max(0, 4 - len(on))
    head = todo[:1] if len(on) < 2 else []
    tail = todo[len(head):need]
    clicked = list(head) + list(tail)

    if len(rows) < 4:
        check("页面上至少有四个一键预设（这一段要凑够四只）", False, f"{len(rows)} 个")
    elif len(labels) != 2 or split_combo is None:
        check("排布下拉还在，且挑得出两项", False, "、".join(labels))
    elif need > len(todo):
        check("清单与预设加起来凑得出四只（这一段量的真是「超过三只」）", False,
              f"清单上 {len(on)} 只开着，预设里没开着的只有 {len(todo)} 个")
    else:
        stale = vc.status_text(win)

        for row in head:
            vc.click(row, 1.0)
            got = vc.wait_status(win, unlike=stale, seconds=180)
            stale = got or stale

            if not got or BAD.search(got):
                check(f"加上「{row.Name}」之后取数正常", False, got or "(状态条空)")
                break

        on2 = [c for c in chips(win) if c[2].ToggleState == auto.ToggleState.On]
        check("先凑到两只（一只时排布下拉是灰的）", len(on2) == 2,
              f"{len(on2)} 只：{[c[1] for c in on2]}")
        check("两只时排布下拉恢复可用", vc.enabled(win, "SplitCombo") is not False,
              str(vc.enabled(win, "SplitCombo")))

        if winui.combo_pick(win, split_combo, labels[1]) is None:
            check("切到分图（点名只在分图下发生）", False)
        else:
            for row in tail:
                vc.click(row, 1.0)
                got = vc.wait_status(win, unlike=stale, seconds=180)
                stale = got or stale

                if not got or BAD.search(got):
                    check(f"加上「{row.Name}」之后取数正常", False, got or "(状态条空)")
                    break

            # 清单上本来就已经开着四只时没有第四只可点，而「点名」是**取数时**由页面说的（图
            # 片那一栏选的还是合图）。切到分图之后重取一次，让它把没画的那一只说出来 —— 不然
            # 这一条会红在一个「页面根本没机会说话」的地方。
            if not tail:
                vc.click(vc.find(lambda c: c.AutomationId == "FetchButton", win), 1.0)
                stale = vc.wait_status(win, unlike=stale, seconds=180) or stale

        on4 = [c for c in chips(win) if c[2].ToggleState == auto.ToggleState.On]

        check("清单上有四只开着（这一段量的真是「超过三只」）",
              len(on4) == 4, f"{len(on4)} 只：{[c[1] for c in on4]}")

        if len(on4) == 4:
            said = vc.status_text(win) or ""

            # 关哪一只**由状态行决定**，不由清单顺序决定：名字出现在那句话里的那一只就是
            # 页面自己说没画的那一只。清单的先后和看板的先后是两件事，这一段的两次红都是
            # 踩在这上面。
            dropped = next((c for c in on4 if c[1] in said), on4[-1])

            check("第 4 只在状态行里被点名（不是悄悄不画）",
                  dropped[1] in said, f"第 4 只「{dropped[1]}」，状态行：{said[:90]}")

            vc.scrub_to(win, 1.0)
            four = vc.shot(win, "verify-candle-split-four.png")

            win.SetFocus()

            try:
                dropped[2].Toggle()
            except Exception:  # noqa: BLE001 - 拨不动的话下面按清单数判
                pass

            time.sleep(1.0)

            left3 = [c for c in chips(win) if c[2].ToggleState == auto.ToggleState.On]
            vc.click(vc.find(lambda c: c.AutomationId == "FetchButton", win), 1.0)
            back = vc.wait_status(win, unlike=said, seconds=180)

            if not left3 or len(left3) != 3:
                check("把被点名的那一只关掉之后清单上正好剩三只", False,
                      f"{len(left3)} 只：{[c[1] for c in left3]}")
            elif not back or BAD.search(back):
                check("关掉它之后取数正常", False, back or "(状态条空)")
            else:
                vc.scrub_to(win, 1.0)
                three = vc.shot(win, "verify-candle-split-three.png")
                same = band_diff(four, three)

                check("只画前 3 只：把关掉第 4 只之后的画面与它比，逐像素一样",
                      same < 0.02, f"{same:.1%} 不同")

        # ---- 真机：比较画面的导出，按下去必须真的动起来 ---------------------------------
        #
        # 量的就是用户报的那一件事。`encode: enter` 是 `VideoExporter.EncodeAsync` 的第一句，
        # 出现它说明整条路走到了编码器 —— 而在这一版之前，比较画面上**从来没有出现过这一行**
        # （导出按钮按得下去，什么都不发生，日志里干干净净）。
        #
        # 只问「状态行有没有说话」是不够的：不说不动是缺陷，动错了也是另一种缺陷，这里能分
        # 开的正是前者 —— 而前者就是用户报的那一种。
        #
        # 收尾**按取消**：取消会把半成品删掉（`EncodeAsync` 的 catch 里 delete），所以不会在
        # 读者的输出文件夹里留下垃圾文件。
        split_box = vc.find(lambda c: c.AutomationId == "SplitCombo", win)

        check("这一段量的是比较画面（单标的的导出一直是好的，量它等于没量）",
              split_box is not None and split_box.IsEnabled,
              "SplitCombo 不在或不可用 —— 此刻画的不是比较画面")

        export = vc.find(lambda c: c.AutomationId == "ExportButton", win)

        if export is None or not export.IsEnabled:
            check("比较画面的导出按钮是亮的（它是 `ready`，两条来源都算）", False,
                  "没找到按钮" if export is None else "IsEnabled=False")
        else:
            offset = log_size()
            said = vc.status_text(win)

            vc.click(export, 1.0)

            entered = wait_log(offset, "encode: enter", seconds=45)

            check("按下导出后编码真的开始了（比较画面的导出不再是静默返回）",
                  entered,
                  "" if entered else
                  "45 秒内日志里没有 encode: enter；状态行："
                  f"{(vc.status_text(win) or '（空）')[:80]}")

            if entered:
                during = vc.status_text(win) or ""

                check("导出期间状态行在报进度", during != (said or "") or "%" in during,
                      during[:90])

                cancel = vc.find(lambda c: c.AutomationId == "CancelButton", win)

                if cancel is not None and cancel.IsEnabled:
                    vc.click(cancel, 1.0)
                else:
                    check("导出的取消按钮是亮的（导出期间它能停）",
                          cancel is not None and cancel.IsEnabled,
                          "没找到按钮" if cancel is None else "IsEnabled=False")

                time.sleep(4.0)

                after = vc.status_text(win) or ""

                check("取消之后状态行换了话（不是停在那儿不动）", after != during, after[:90])

        # 排布也是落盘的偏好：走的时候摆回「同一张图」，别把下一个判据（和下一次真实使用）
        # 留在没人选过的那一半上。
        winui.combo_pick(win, split_combo, labels[0])

    # 开关的状态**也落盘**，和清单的内容一起 —— 把开关留在开着的位置上，下一个判据（以及
    # 下一次真实使用）就是从一个没人选过的画面开始的：这一页的搜索和一键预设都是「把这只放
    # 到清单上并画出来」，清单里还开着别人，按下去画出来的就是两只。来的时候全关，走的时候
    # 也全关。
    clean, why = clear_chips(win)
    check("走的时候清单也是干净的", clean, why)

    # 而这一段点进去的预设，落在的是**共享清单**上（一键预设点一下就是「放到清单上并画出来」），
    # 用完了要摘掉：共享清单是读者自己的数据，判据不该给它留下东西。摘的只有**这一跑带进来的
    # 那几只**（`before` 是这一段开始时的清单），读者原本就在清单上的预设一只都不碰。
    ours = [row for row in clicked if row.AutomationId not in before]

    if ours:
        for row in ours:
            drop_chip(win, row.AutomationId, row.Name)

        time.sleep(1.0)

        still = {c[0] for c in chips(win)}

        check("这一跑带进清单的预设又摘掉了（共享清单是读者自己的）",
              not any(row.AutomationId in still for row in ours),
              f"带进 {[r.Name for r in ours]}，还留着 "
              f"{[r.Name for r in ours if r.AutomationId in still]}")

    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"\n通过 {passed} 项，失败 {len(CHECKS) - passed} 项")

    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
