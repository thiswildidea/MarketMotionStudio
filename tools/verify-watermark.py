# -*- coding: utf-8 -*-
r"""验证「背景水印」：默认开启、可改文字、关掉就什么都不画，且导出与预览一致。

**判据用像素，不用界面文字。** 水印是画在背景上的一层极淡的白（alpha 26/255），界面上没有任何
一处会写「已加上水印」。能问的只有画面本身：把预览面按行取中位数当基线——每一行的底色是同一个
渐变值，横向标准差本来就是 0——再数比基线亮出去的像素占多少。开着这一层纹理在，关着它一格都
没有。

**改动前后比的是整幅画面，不是某一行。** 水印是斜向平铺的，量某一个坐标等于赌它正好落在那里。

**重启那一趟排在改动之前**（`verify-framebackdrop` 那一轮踩过）：先改再重启，记住的当然是刚改的
那个值，三项持久化断言会全红而产品是对的。

**收尾无条件复位**：开关回开、文字回默认。这是默认开启的设置，脚本把它留在「关」上，下一个验
别的东西的脚本就会对着没有水印的画面找水印。

辅助函数不复制：`verify-framebackdrop.py` 的 `find` / `require` / `invoke_click` /
`goto_settings` / `goto_first_page` / `wait_window` 直接按路径加载来用（文件名带连字符，只能
按路径加载）。复制出去的是一份迟早会对不上的副本。

用法：python tools\verify-watermark.py
用法（只看源码断言）：python -c "import importlib.util as u; ..."
"""
import importlib.util
import os
import statistics
import subprocess
import sys
import time

import numpy as np
import uiautomation as auto
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, "artifacts")
SRC = os.path.join(REPO, "src", "MarketMotionStudio")

sys.path.insert(0, HERE)

import winui  # noqa: E402

_spec = importlib.util.spec_from_file_location("vfb", os.path.join(HERE, "verify-framebackdrop.py"))
vfb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vfb)

DEFAULT_TEXT = "周期留白"

# 默认字体（`Ink.Family`），复位时用它。
DEFAULT_FONT = "Microsoft YaHei"

# 换过去的那一款。**一串候选，不是一款**：下拉在 UIA 里只暴露它当前可见的那一段（实测滚
# 动设置页之前 157 项、之后 151 项，Georgia 只在其中一种情况下露出来），所以只认一款的
# 脚本换个窗口位置就选不上。候选都选含中文的、与默认那款形状差得远的 —— 一款不含中文
# 字形的字体会把「周期留白」交给回退字体去画，画出来还是默认那副样子，画面就不变了。
OTHER_FONTS = ["KaiTi", "Georgia", "Impact"]

# 默认浓度 10%（水印那一层 alpha 26/255），以及浓度滑条的上界。
DEFAULT_STRENGTH = 10
MAX_STRENGTH = 40

# 水印是白 alpha 26 打在近黑的底上，抬起来约 21 一通道、三通道和约 63。所以只数「比所在行
# 中位数亮出 24~140」的像素 —— 上界是这一条最要紧的地方：画面上还有标题、进度条、卡片边框，
# 它们比水印亮得多（实测关掉时那些像素的中位亮度是 449，水印是 63 上下）。不设上界时关掉的
# 画面照样量出 1.16%，看上去像「关了还有水印」，而那 1.16% 全是一行标题和一个进度条。
GRAIN_LOW = 24
GRAIN_HIGH = 140

# 有/没有水印的分界，按上面那个带实测：开着 7.4%（改短的文字 4.6%），关着 0.11%。
GRAIN_ON = 0.010
GRAIN_OFF = 0.005

FAILED = []


def check(label, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + label + ("  — " + detail if detail else ""))

    if not ok:
        FAILED.append(label)


def read(name):
    return open(os.path.join(SRC, name), encoding="utf-8-sig").read()


# ---- 源码断言 -------------------------------------------------------------------
#
# 画面上看不出来的三件事只能在这里守：默认开、留空回落、以及「水印画在背景之后、内容之前」。

def source():
    context = read(os.path.join("Render", "FrameContext.cs"))
    backdrop = read(os.path.join("Render", "Backdrop.cs"))
    watermark = read(os.path.join("Render", "Watermark.cs"))
    settings = read("WatermarkSettings.cs")
    surface = read(os.path.join("Views", "PreviewSurface.cs"))
    page = read(os.path.join("Pages", "SettingsPage.xaml.cs"))
    markup = read(os.path.join("Pages", "SettingsPage.xaml"))
    ink = read(os.path.join("Render", "Ink.cs"))
    frame = read(os.path.join("Render", "FrameExporter.cs"))
    video = read(os.path.join("Render", "VideoExporter.cs"))

    print("源码：")

    check("水印随 FrameContext 走（渲染器不各自去读设置）",
          "Watermark? Watermark" in context)

    check("画在**背景之后、内容之前**——`Fill` 先铺背景再调水印",
          "FillBackdrop(session, context, fallback);" in backdrop
          and "context.Watermark?.Draw(session, context);" in backdrop)

    sites = context_sites()

    check("每一处构造 FrameContext 的地方都带上了水印",
          len(sites) == 3 and all("watermark" in near.lower() for _, near in sites),
          "{} 处：{}".format(len(sites), ", ".join(os.path.basename(p) for p, _ in sites)))

    check("封面与视频各**读一次**快照，不在帧循环里读",
          "var watermark = WatermarkSettings.Current;" in frame
          and "var watermark = WatermarkSettings.Current;" in video)

    check("预览订阅 Changed（设置页不持有预览的引用）",
          "WatermarkSettings.Changed += (_, _) => Redraw();" in surface)

    check("默认**开启**：键不存在时算开，不是算关",
          "Settings.Values[OnKey] is not bool on || on" in settings)

    check("默认那句话是「周期留白」",
          f'public const string DefaultText = "{DEFAULT_TEXT}";' in watermark)

    check("留空回落默认，而不是画一个空水印",
          'Settings.Values[TextKey] is string text && text.Trim().Length > 0' in settings)

    check("关掉时解析为 null（渲染器「没有」而不是「画一个空的」）",
          "Enabled ? new Watermark(Text, Family, Colour, Watermark.AlphaOf(Strength)) : null"
          in settings)

    print("源码（长什么样）：")

    check("画的时候用的是所选字体（`Ink.Format` 带上 family）",
          "Ink.Format(fontSize, family: Family)" in watermark)

    check("颜色是所选的颜色、浓度是所选的浓度（不是写死的白）",
          "Color.FromArgb(Alpha, Colour.R, Colour.G, Colour.B)" in watermark)

    # 这一层是按设备缓存的整层。键里少一样，换那样就只在预览上看不出来 —— 导出用的是
    # 另一份缓存，那一份还会是新的。所以这三样一个都不能少，而少了的那一格画面完全正常。
    check("缓存那一层把字体 / 颜色 / 浓度一起当键（否则改了不重画）",
          'string.Equals(entry.Family, Family, StringComparison.Ordinal)' in watermark
          and "entry.Colour.Equals(Colour)" in watermark
          and "entry.Alpha == Alpha" in watermark)

    check("浓度的上界不是 100（拉满仍然画在数据之下）",
          "public const int MaxOpacity = 40;" in watermark)

    check("取色器不给 alpha（那是浓度滑条的事）",
          'x:Name="WatermarkColour"' in markup and 'IsAlphaEnabled="False"' in markup)

    check("三项都落到设置里（下拉 / 取色器 / 滑条各写各的）",
          "WatermarkSettings.Family = font;" in page
          and "WatermarkSettings.Colour = args.NewColor;" in page
          and "WatermarkSettings.Strength = (int)Math.Round(e.NewValue);" in page)

    check("关掉时三个控件一起灰掉（不是只有输入框）",
          "WatermarkFontCombo.IsEnabled = on;" in page
          and "WatermarkColourButton.IsEnabled = on;" in page
          and "WatermarkStrengthSlider.IsEnabled = on;" in page)

    check("没存过时回落到默认字体与默认颜色",
          ": Watermark.DefaultFamily" in settings
          and "Watermark.DefaultColour" in settings)

    # 字体名里带逗号的，DirectWrite 会当成「两个字体」，画出来的就不是用户点的那一个。
    check("带逗号的字体名被拒（退回默认字体）",
          "family.Contains(',')" in ink)

    check("按设备缓存整层（每帧上百个字只画一次）",
          "ConditionalWeakTable<CanvasDevice, Entry> Painted" in watermark)

    check("Transform 一定还原（否则整张图会歪 45°）",
          "finally" in watermark and "session.Transform = saved;" in watermark)

    check("斜向 45°，且错开半格（否则平铺看着像网格）",
          "Radians = -Math.PI / 4" in watermark and "stagger" in watermark)


def context_sites():
    """Every `new FrameContext(` in the source, with the text just after it.

    The call reaches across several lines in the preview, so it has to be taken
    as a stretch of text rather than line by line — a line-based test passes
    there because the line carrying the watermark is the next one down, and that
    is exactly the site that would go unsigned if it were ever forgotten.
    """
    found = []

    for root, _, files in os.walk(SRC):
        for name in files:
            if not name.endswith(".cs"):
                continue

            path = os.path.join(root, name)
            text = open(path, encoding="utf-8-sig").read()
            at = text.find("new FrameContext(")

            while at >= 0:
                found.append((path, text[at:at + 160].replace("\n", " ")))
                at = text.find("new FrameContext(", at + 1)

    return found


# ---- 像素判据 -------------------------------------------------------------------

def canvas_array(path):
    """预览面那一块，作为 RGB 数组。"""
    im = Image.open(path).convert("RGB")
    box = winui.canvas_box(im)

    assert box is not None, path + ": 画面里没有画布（抓到的不是应用窗口？）"

    bottom = winui.frame_bottom(im, box)

    return np.asarray(im, dtype=np.int16)[box[2]:bottom, box[0]:box[1]]


def grain_array(a):
    """水印那种亮度的像素占多少。见 GRAIN_LOW。

    底色是纵向渐变：同一行同色，横向标准差本来就是 0，所以「行中位数」就是这一行的底色，
    任何偏离都是画上去的东西。但画上去的不止水印，所以只数水印这一段亮度。
    """
    sums = a.sum(axis=2)
    lifted = sums - np.median(sums, axis=1, keepdims=True)

    return float(((lifted > GRAIN_LOW) & (lifted < GRAIN_HIGH)).mean())


def grain(path):
    """窗口截图里那块预览面的纹理比例。"""
    return grain_array(canvas_array(path))


def diff_ratio(one, other):
    """两幅画面有多少比例的像素不同。"""
    a = canvas_array(one)
    b = canvas_array(other)

    height = min(a.shape[0], b.shape[0])
    width = min(a.shape[1], b.shape[1])

    return float((np.abs(a[:height, :width] - b[:height, :width]).max(axis=2) > 6).mean())


# ---- 真机 -----------------------------------------------------------------------

def restart():
    before = vfb.app_pids()
    subprocess.run(["taskkill", "/IM", "MarketMotionStudio.exe", "/F"],
                   capture_output=True)
    time.sleep(2)

    os.startfile(r"shell:AppsFolder\%s" % vfb.APPID)
    time.sleep(6)

    window = vfb.wait_window()
    assert window is not None, "重启后窗口未找到"

    after = vfb.app_pids()
    print("  重启：PID", before, "->", after)

    window.SetActive()
    window.MoveWindow(60, 60, 1500, 940)
    time.sleep(1.5)

    return window


def settle(window, on, text):
    """把水印设置摆到一个已知状态：开关 + 文字。"""
    toggle = vfb.require(window, "WatermarkToggle")
    pattern = vfb.pat(toggle, auto.PatternId.TogglePattern)

    assert pattern is not None, "开关不支持 TogglePattern"

    if on != (pattern.ToggleState == auto.ToggleState.On):
        pattern.Toggle()
        time.sleep(0.8)

    box = vfb.require(window, "WatermarkText")
    value = vfb.pat(box, auto.PatternId.ValuePattern)

    assert value is not None, "文本框不支持 ValuePattern"

    if value.Value != text:
        value.SetValue(text)
        time.sleep(0.8)


def state_of(window):
    toggle = vfb.require(window, "WatermarkToggle")
    pattern = vfb.pat(toggle, auto.PatternId.TogglePattern)
    box = vfb.require(window, "WatermarkText")
    value = vfb.pat(box, auto.PatternId.ValuePattern)

    assert value is not None, "文本框不支持 ValuePattern"

    return pattern.ToggleState == auto.ToggleState.On, value.Value


def shot(window, name):
    path = os.path.join(OUT, name)
    winui.capture(window, path)
    print("  shot:", name)

    return path


def show_strip(window):
    """把设置页那条反馈预览弄进视口，返回锚点（浓度滑条）的屏幕矩形。

    锚点是**预览条上面那一个控件**，现在它是浓度滑条 —— 这一轮在文本框与预览条之间插进了
    字体下拉与取色器，还拿文本框当锚点的话，往下那 220 像素采到的全是新控件：卡片与预览条
    底色不同，扫不到就说「没扫到那一条」，而预览条好端端画着。

    滚动容器是锚点的**直接父级**那个 `PaneControl` —— 这一页按 `ScrollViewerControl`
    一个都找不到（`verify-framebackdrop` 里的 `scroll_settings` 因此只是安静地什么都不做），
    所以这里从锚点往上问一句「你会滚吗」。

    滚动百分比**试出来**而不是写死：卡片每加一行控件，写死的那个数就把预览条推出窗口下沿，
    而推出去的表现同样是「没扫到那一条」。所以按「滑条整个在窗口里、下面还留得下预览条」
    依次试几个位置。
    """
    anchor = vfb.require(window, "WatermarkStrengthSlider")
    scroller = vfb.pat(anchor.GetParentControl(), auto.PatternId.ScrollPattern)

    frame = window.BoundingRectangle

    for percent in (45, 55, 65, 75):
        if scroller is not None:
            try:
                if scroller.VerticallyScrollable:
                    scroller.SetScrollPercent(-1, percent)
                    time.sleep(1.2)
            except Exception:  # noqa: BLE001 - a page that will not scroll is read where it is
                pass

        rect = anchor.BoundingRectangle

        if rect.top > frame.top and rect.bottom < frame.bottom - 120:
            break

    return anchor.BoundingRectangle


def strip_crop(window, name):
    """设置页那条反馈预览的像素，扫不到就是 None。

    它**不是 UIA 里的一个控件**：`WatermarkPreview` 是 `Grid` 的子类，而 Grid 在 UIA 里没有
    自己的节点（实测按 AutomationId 找它，一个都找不到）。所以位置从**它上面那个控件**往下
    扫：卡片底色是浅灰、这一条是深色渐变，行均值一眼分得开。

    偏移量不写死：截图坐标与 UIA 坐标差着窗口边框那几十像素，写死就采到卡片空白处，看上去
    像「这条根本没画」。
    """
    rect = show_strip(window)
    frame = window.BoundingRectangle
    image = Image.open(shot(window, name)).convert("RGB")
    a = np.asarray(image, dtype=np.int16)

    left = max(0, rect.left - frame.left)
    right = min(image.size[0], rect.right - frame.left)
    top = max(0, rect.bottom - frame.top)

    found = [y for y in range(top, min(image.size[1], top + 220))
             if a[y, left:right].mean() < 100]

    if len(found) < 20:
        return None

    # 只取**连着**的那一段。暗行不止预览条：截图比窗口矮几十行，往下扫会扫到窗口下沿
    # 之外的那一片，它同样是暗的。按 `首行..末行` 框进来，那一块亮度不均，关掉的画面
    # 就量出 0.59%（阈值 0.5%）—— 而预览条本身实测是 0.0000%。
    dark = [found[0]]

    for y in found[1:]:
        if y - dark[-1] > 2:
            break

        dark.append(y)

    # 上下各缩进几行再取：卡片那一圈边框和预览条自己的边也在这一段里。
    upper = dark[0] + 2
    lower = dark[-1] - 1

    if lower - upper < 20:
        return None

    return a[upper:lower, left:right]


def strip_band(window, name):
    """那条预览上的水印纹理比例，扫不到就是 None。见 `strip_crop`。"""
    crop = strip_crop(window, name)

    return None if crop is None else grain_array(crop)


def crop_diff(one, other):
    """两幅预览条有多少比例的像素不同。"""
    height = min(one.shape[0], other.shape[0])
    width = min(one.shape[1], other.shape[1])

    return float((np.abs(one[:height, :width] - other[:height, :width]).max(axis=2) > 6).mean())


def pick_font(window, name):
    """在字体下拉里选一款，返回有没有选上。

    下拉展开后到**根级窗口**找 ListItem（`verify-position` 那一轮量出来的）：这一页的下拉
    有几百项，展开后的列表不是组合框的子树。按名字找而不是按序号，因为选到哪一款决定了
    画面变多少 —— Georgia 与默认那款差得远，一眼看得出。
    """
    combo = vfb.require(window, "WatermarkFontCombo")

    combo.SetFocus()
    time.sleep(0.3)

    expand = vfb.pat(combo, auto.PatternId.ExpandCollapsePattern)

    if expand is None:
        print("      （下拉不支持 ExpandCollapsePattern）")
        return False

    for _ in range(3):
        if expand.ExpandCollapseState == auto.ExpandCollapseState.Expanded:
            break

        expand.Expand()
        time.sleep(1.2)

    # 展开之后按名字找。列表长（这一台机器上 129 个族），找名字而不是找序号：序号换一台
    # 机器就是另一款字体，而选到哪一款决定了画面变多少。
    items = vfb.find_all(
        lambda c: c.ControlTypeName == "ListItemControl", window)

    if not items:
        items = vfb.find_all(
            lambda c: c.ControlTypeName == "ListItemControl",
            auto.GetRootControl(), limit=12)

    seen = {c.Name for c in items}

    if name not in seen:
        print("      （下拉里 {} 项，没有 {}）".format(len(items), name))
        return False

    item = next(c for c in items if c.Name == name)

    select = vfb.pat(item, auto.PatternId.SelectionItemPattern)

    if select is None:
        return False

    select.Select()
    time.sleep(1.0)

    return True


def set_strength(window, percent):
    """把浓度滑条摆到某个位置。"""
    slider = vfb.require(window, "WatermarkStrengthSlider")
    value = vfb.pat(slider, auto.PatternId.RangeValuePattern)

    assert value is not None, "浓度滑条不支持 RangeValuePattern"

    value.SetValue(percent)
    time.sleep(0.8)


def device():
    print("真机：")

    pids = vfb.app_pids()

    if not pids:
        os.startfile(r"shell:AppsFolder\%s" % vfb.APPID)
        time.sleep(6)

    window = vfb.wait_window()
    assert window is not None, "窗口未找到"

    window.SetActive()
    window.MoveWindow(60, 60, 1500, 940)
    time.sleep(1.5)

    # ---- 1) 默认：先摆到「开 + 默认文字」，重启后还在 —— 验持久化
    vfb.goto_settings(window)
    settle(window, True, DEFAULT_TEXT)

    window = restart()

    vfb.goto_settings(window)
    on, text = state_of(window)

    check("开关与文字都记着（重启之后）", on and text == DEFAULT_TEXT,
          f"开={on} 文字={text!r}")

    # ---- 2) 开着：设置页那条反馈预览上先看得见，然后图表页的预览面上也有
    on_strip = strip_band(window, "verify-watermark-sample-on.png")

    check("设置页那条预览上也画着水印（改完当场看得见）",
          on_strip is not None and on_strip > GRAIN_ON,
          "纹理占 {:.3%}".format(on_strip) if on_strip is not None else "没扫到那一条")

    vfb.goto_first_page(window)
    base = shot(window, "verify-watermark-on.png")

    base_grain = grain(base)

    check("开着的画面上有水印纹理", base_grain > GRAIN_ON,
          "纹理占 {:.3%}".format(base_grain))

    # ---- 3) 关掉：一格纹理都不该有
    vfb.goto_settings(window)
    settle(window, False, DEFAULT_TEXT)

    off_strip = strip_band(window, "verify-watermark-sample-off.png")

    check("关掉后那条预览上也没有水印",
          off_strip is not None and off_strip < GRAIN_OFF,
          "纹理占 {:.4%}".format(off_strip) if off_strip is not None else "没扫到那一条")

    vfb.goto_first_page(window)
    off = shot(window, "verify-watermark-off.png")

    off_grain = grain(off)

    check("关掉的画面上一格水印都没有", off_grain < GRAIN_OFF,
          "纹理占 {:.4%}".format(off_grain))

    check("开着与关着是两幅不同的画面", diff_ratio(base, off) > 0.01,
          "差异 {:.2%}".format(diff_ratio(base, off)))

    # ---- 4) 改成自己的话：画面跟着变
    vfb.goto_settings(window)
    settle(window, True, "ABCD")
    vfb.goto_first_page(window)
    renamed = shot(window, "verify-watermark-renamed.png")

    check("改了文字画面就变了", diff_ratio(base, renamed) > 0.01,
          "与默认那句差 {:.2%}".format(diff_ratio(base, renamed)))

    check("改了文字水印仍然在", grain(renamed) > GRAIN_ON,
          "纹理占 {:.3%}".format(grain(renamed)))

    # ---- 5) 清空：回到默认那句话，不是「没有水印」
    vfb.goto_settings(window)
    settle(window, True, "")
    vfb.goto_first_page(window)
    blank = shot(window, "verify-watermark-blank.png")

    check("留空回到默认那句话（不是变成没水印）", diff_ratio(base, blank) < 0.002,
          "与默认那句差 {:.3%}".format(diff_ratio(base, blank)))

    # ---- 5b) 浓度：拉满之后整条预览更亮，拉回来又是原来那一条
    #
    # 不看 `grain_array`：那个判据数的是「比行底色亮出 24~140」的像素，浓度拉到 40% 时
    # 水印自己比 140 还亮，全落进上界之外 —— 拉满反倒量出 0，看上去像「拉满没画」。所以
    # 这里比的是**整条的亮度**，它是单调的：浓度越高，铺满画面的那一层越亮。
    vfb.goto_settings(window)
    settle(window, True, DEFAULT_TEXT)
    plain = strip_crop(window, "verify-watermark-plain.png")

    assert plain is not None, "没扫到那条预览"

    set_strength(window, MAX_STRENGTH)
    strong = strip_crop(window, "verify-watermark-strong.png")

    assert strong is not None, "浓度拉满后没扫到那条预览"

    check("浓度拉满，整条预览更亮",
          strong.mean() > plain.mean() + 2,
          "亮度 {:.1f} -> {:.1f}".format(plain.mean(), strong.mean()))

    check("浓度拉满与默认是两幅不同的画面", crop_diff(plain, strong) > 0.05,
          "差异 {:.2%}".format(crop_diff(plain, strong)))

    set_strength(window, DEFAULT_STRENGTH)
    settled = strip_crop(window, "verify-watermark-strength-back.png")

    assert settled is not None, "浓度拉回后没扫到那条预览"

    check("浓度拉回默认，预览条回到原样", crop_diff(plain, settled) < 0.01,
          "与默认浓度差 {:.3%}".format(crop_diff(plain, settled)))

    # ---- 5c) 字体：换一款预览条就变，重启之后还是那一款
    #
    # 字体是唯一一项「换了之后画面变、但界面上一个字都不会说」的：下拉里选了 Georgia，
    # UIA 读不出选中项的名字（`MarketCombo` 那类的 ValuePattern 是空的），所以判据只能是
    # 那一幅画面 —— 重启之后还是同一幅，就是记着。
    chosen = next((name for name in OTHER_FONTS if pick_font(window, name)), None)

    check("字体下拉里选得到另一款字体", chosen is not None, str(chosen))

    other = strip_crop(window, "verify-watermark-font.png")

    assert other is not None, "换字体后没扫到那条预览"

    check("换了字体，预览条就变了", crop_diff(plain, other) > 0.01,
          "与默认字体差 {:.2%}".format(crop_diff(plain, other)))

    window = restart()
    vfb.goto_settings(window)

    kept = strip_crop(window, "verify-watermark-font-kept.png")

    assert kept is not None, "重启后没扫到那条预览"

    check("换过的字体记着（重启后还是那一幅）", crop_diff(other, kept) < 0.01,
          "与重启前差 {:.3%}".format(crop_diff(other, kept)))

    pick_font(window, DEFAULT_FONT)
    restored = strip_crop(window, "verify-watermark-font-back.png")

    check("换回默认字体，预览条回到原样",
          restored is not None and crop_diff(plain, restored) < 0.01,
          "与默认字体差 {:.3%}".format(crop_diff(plain, restored) if restored is not None else -1))

    # ---- 6) 收尾：不留痕迹
    vfb.goto_settings(window)
    settle(window, True, DEFAULT_TEXT)
    set_strength(window, DEFAULT_STRENGTH)
    pick_font(window, DEFAULT_FONT)

    on, text = state_of(window)
    check("收尾复位：开 + 默认那句话", on and text == DEFAULT_TEXT,
          f"开={on} 文字={text!r}")


def main():
    source()
    print()
    device()

    print()
    print("FAILED:", len(FAILED))

    for label in FAILED:
        print("  ✗", label)

    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
