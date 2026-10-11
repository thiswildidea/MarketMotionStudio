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

# 换过去的那一款。**一串候选，不是一款**：下拉一次只建出**已经渲染出来的那些项**（实测
# 展开后 192 项，而这一台机器有 176 个族 —— 不是全部都在），所以只认一款的脚本换个窗口
# 位置就选不上。候选按「排得靠前」挑：实测 `KaiTi` 在头三十项里，`Arial` 在第一项。
#
# 还要**与默认那款形状差得远**，否则换了画面也不变，判据红掉而产品是对的：`Arial` 不含
# 中文字形，把「周期留白」交给回退字体去画 —— 画出来与 `Microsoft YaHei` 几乎一样，
# 反而更糟。所以中文名的候选（KaiTi / LiSu）才是首选，它们既是中文字体、字形又很不一样。
OTHER_FONTS = ["KaiTi", "LiSu", "Consolas", "Cascadia Code"]

# 默认浓度 10%（水印那一层 alpha 26/255），以及浓度滑条的上界。
DEFAULT_STRENGTH = 10
MAX_STRENGTH = 40

# 一处笔画边缘算不算数：横向与纵向的梯度**都要**落在这一段里。见 `grain_array`。
#
# 下界 6 是「看得出是个边缘」，上界 40 是「是水印那种淡笔画，不是图表的粗笔画」——
# 曲线、柱、胶囊比水印重得多，它们的边缘远在 40 之上；底色渐变又远在 6 之下。
GRADIENT_LOW = 6
GRADIENT_HIGH = 40

# 有/没有水印的分界，按上面那个带实测：开着 6.41%（改成 ABCD 2.81%），关着 0.52%。
# 差 12 倍，所以阈值放在两者中间偏低的地方，给压缩、缩放留出余量。
GRAIN_ON = 0.015
GRAIN_OFF = 0.012

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

    check("关掉时三处一起灰掉（不是只有输入框）：字体 / 颜色 / 浓度",
          "WatermarkFontCombo.IsEnabled = on;" in page
          and "WatermarkColourButton.IsEnabled = on;" in page
          and "WatermarkStrengthSlider.IsEnabled = on && WatermarkSettings.StrengthOptional;" in page)

    # 浓度那一处**多一个条件**，而且是设计要的：未付费时浓度恒为 `MaxOpacity`
    # （`WatermarkSettings.Strength` 的 getter 里那一支），所以它不该可改 —— 灰掉与
    # 「改了也没用」必须是同一件事。这条判据原来写的是三处都 `= on`，于是它守的是
    # 「订阅这件事不存在」，而不是「关掉时会灰」。两个条件各自写一句，改动任一支都能被看见。
    check("浓度那处的第二个条件是订阅（未付费时它不可改）",
          "public static bool StrengthOptional => PaidFor;" in settings
          and ": Watermark.MaxOpacity;" in settings)

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
    """水印那种纹理的像素占多少。

    **量的是「两个方向同时都有梯度」，不是「比行底色亮出多少」。** 后者这次被推翻了：
    `canvas_box` 修好之前它返回的是整幅窗口，行中位数被窗口的浅色面板抬到两百上下，
    画布自己那点深色全落在中位数**以下**，「亮出 24~140」的只剩一行标题 —— 关掉的画面
    量出 0.11%，看着像判据很干净，其实是**站错了地方**。框修对之后同一张图量出 16.7%，
    而那是图表的曲线、网格、轴标签；开着 19.9% 对关掉 16.7%，差 3pp，分不开。

    纹理的说法站得住：水印是**斜向 45° 的细笔画**，于是每一处笔画边缘在**横向和纵向
    同时**留下一个中等大小的梯度；而图表的前景是横平竖直的 —— 一条水平网格线只有纵向
    梯度，一根竖直轴只有横向梯度。两个方向一起问，水印单独浮出来。

    实测（1500×940 的窗口，默认浓度 10%）：

        默认那句话          6.41%
        改成 ABCD           2.81%
        留空（回落默认）    6.40%
        关掉                0.52%

    差 12 倍，阈值取 1.5% 分得干干净净；而「留空回到默认」这条也由同一对数守住
    （6.40 对 6.41）。改成 ABCD 会掉下来是因为笔画少了：水印**面积**在减，纹理跟着减 ——
    这正是判据该有的行为。
    """
    g = a.astype(np.float32).mean(axis=2)

    # 两个方向的梯度对齐到同一个网格（各自丢掉最后一行/列）。
    across = np.abs(np.diff(g, axis=1))[:-1, :]
    down = np.abs(np.diff(g, axis=0))[:, :-1]

    both = (
        (across > GRADIENT_LOW) & (across < GRADIENT_HIGH)
        & (down > GRADIENT_LOW) & (down < GRADIENT_HIGH)
    )

    return float(both.mean())


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
    """重启应用，交回窗口。

    **这里不等任何控件。** 重启回到的是**上次退出时那一页**，不一定是设置页 —— 实测
    重启后落在图表页（`Scrub` 在、`WatermarkToggle` 不在），所以在这里等水印卡片会
    一直等到超时。等页面 + 等控件是 `vfb.goto_settings` 那一头的事，见 `settle`。
    """
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


def until(window, automation_id, seconds=30):
    """等某个控件出现在树里，返回它；等不到返回 None。

    重启/切页之后界面是**逐步建**出来的，`vfb.require` 是「现在就找」，早一刻就是
    「未找到」。等的是那个控件本身，不是一段时间：设置页的卡片越多、越靠下，它出现
    得越晚，而卡片顺序正是会变的东西（市场那张这次从第五挪到了第一）。
    """
    deadline = time.time() + seconds

    while time.time() < deadline:
        found = vfb.find(lambda c: c.AutomationId == automation_id, window)

        if found is not None:
            return found

        time.sleep(0.5)

    return None


def settings(window):
    """切到设置页，并等水印那一张卡片也建好。

    加这一层是因为 `vfb.goto_settings` 只保证**导航切过去了**（点了导航项、睡两秒），
    不保证这一页的控件都建好了 —— 实测重启后紧接着 `require("WatermarkToggle")` 抛
    「未找到」，而同一趟里晚半秒就成了。水印卡片在设置页最靠下那几张之一，它能找到
    就说明整页都好了。
    """
    vfb.goto_settings(window)

    assert until(window, "WatermarkToggle") is not None, \
        "设置页切过去了，但 30 秒内没建出水印卡片"

    return window


def bring_into_view(window, control):
    """把控件滚进可视区，再返回它。

    **不滚就可能切不动那个开关。** 水印卡片在设置页很下面（市场、语言、主题、帧背景
    之后），窗口 940 高时 `WatermarkToggle` 停在屏外；对屏外的 WinUI `ToggleSwitch`
    调 `TogglePattern.Toggle()` **抛 `COMError -2147220992`**（控件看着找得到、
    `IsEnabled` 也读得出，就是按不动）。实测：不滚必抛，滚进来必成。

    用的是 UIA 自己的 `ScrollItemPattern`，不是去动 ScrollViewer 的百分比 —— 百分比
    要按卡片高度猜，而卡片顺序正是会变的东西（市场那张从第五挪到第一之后，原来猜的
    位置就全错了）。控件自己最清楚该滚到哪里。

    **`ScrollItemPattern` 得走 `GetPattern`**：`uiautomation` 那个包装类没给
    `GetScrollItemPattern()`（调它抛 `AttributeError`），只有 `GetPattern(PatternId)`。

    `AutomationId` 有名字的控件才走这条路；拿不到那个模式就原样返回，让调用方照旧去
    试 —— 免得把一个「本来就在屏上」的控件弄出别的毛病。
    """
    try:
        scroll = control.GetPattern(auto.PatternId.ScrollItemPattern)
        if scroll is not None:
            scroll.ScrollIntoView()
            time.sleep(0.6)
    except Exception:  # noqa: BLE001 - 已经在屏上、或不支持，都不是错误
        pass

    return control


def settle(window, on, text):
    """把水印设置摆到一个已知状态：开关 + 文字。"""
    toggle = bring_into_view(window, vfb.require(window, "WatermarkToggle"))
    pattern = vfb.pat(toggle, auto.PatternId.TogglePattern)

    assert pattern is not None, "开关不支持 TogglePattern"

    if on != (pattern.ToggleState == auto.ToggleState.On):
        pattern.Toggle()
        time.sleep(0.8)

    box = bring_into_view(window, vfb.require(window, "WatermarkText"))
    value = vfb.pat(box, auto.PatternId.ValuePattern)

    assert value is not None, "文本框不支持 ValuePattern"

    if value.Value != text:
        value.SetValue(text)
        time.sleep(0.8)


def state_of(window):
    """读回开关与文字。

    **两项都先滚进视口再读**，和 `settle` 一样：水印卡片在设置页很下面，重启之后页面回到
    顶部，`WatermarkToggle` 停在屏外。屏外的 WinUI 控件**连读都不稳** —— 找得到、但
    `require` 的深度遍历是走可视树的，控件一进一出可读性就变，实测重启那一趟直接
    `WatermarkToggle 未找到`。

    卡片的顺序是会变的东西：市场那张从第五挪到第一之后，水印又被往下推了一格 ——
    「重启后读一次」这一条正是最先被这种挪动打中的地方，所以这里不假设它在屏内。
    """
    toggle = bring_into_view(window, vfb.require(window, "WatermarkToggle"))
    pattern = vfb.pat(toggle, auto.PatternId.TogglePattern)
    box = bring_into_view(window, vfb.require(window, "WatermarkText"))
    value = vfb.pat(box, auto.PatternId.ValuePattern)

    assert pattern is not None, "开关不支持 TogglePattern"
    assert value is not None, "文本框不支持 ValuePattern"

    return pattern.ToggleState == auto.ToggleState.On, value.Value


def shot(window, name):
    """抓一张，**并且确认抓到的真是这个窗口当前的这一页**。

    `winui.capture` 返回布尔值就是干这个的：它把图读回来，看里面有没有一块画布
    （`looks_like_a_frame`），没有就再抬一次窗口重抓，`tries` 次都不行返回 False
    —— 而**文件照样写**。

    这一条原来把返回值丢了。「页面还停在别的页上」或者「窗口被什么盖住」的时候，
    抓回来的是上一页那张图，而后面所有像素判据都拿它当真：

    `goto_first_page` 点完导航就回来，**没有把窗口抬回前台** —— 页面确实翻过去了，
    但前台还是脚本自己的控制台，于是 `CaptureToImage` 抓到的一直是**上一张**。表现
    是「关掉水印」「改文字」「拉浓度」「换字体」四组断言全报 0.00% 差异，读数却一次
    比一次**旧**（关掉那张量到 16.25%，是几分钟前「开着」那幅的纹理）。那是「这条
    判据在量一张过期的图」，不是「应用画错了」。

    **`capture` 的返回值只在有画布的那几页上有意义**：设置页没有预览画布，
    `looks_like_a_frame` 必然为假，于是每一张设置页的图都被判成「抓错了」——所以
    这一条**只对图表页要那个返回值**，设置页那张交回路径。

    设置页那几张另有一个不依赖 `capture` 的守卫：`strip_crop` 是在**画面里认**那条预览的
    （设置页里唯一一条横跨卡片的深色带），认不出来返回 None 让断言红掉 —— 那是
    「这条判据自己的眼睛」，不多不少。**它现在不靠滑条坐标推算了**（推偏了不报错，只会
    安静地量到别的区域，见 `strip_crop` 的注释）。

    **`_chart_page` 只看导航，不看图。** 它问的是「这个窗口现在停在图表页吗」，而
    窗口被别的窗口盖住时这个问题的答案还是「是」——UIA 读的是窗口自己，不读谁在最
    上面。所以真正的判据只能是**这一张图里有没有那块画布**：`canvas_box` 修好之后
    它答得出 9:16，答不出就是这张图不是这一页（或窗口不在前台）。用图回答问题，
    而不是用一个与图无关的状态回答问题。
    """
    path = os.path.join(OUT, name)

    ok = winui.capture(window, path)

    if not ok and _chart_page(window):
        raise AssertionError(
            "%s: 抓到的不是这个窗口（多半停在别的页上、或窗口被盖住了）" % name
        )

    print("  shot:", name)

    return path


def _chart_page(window):
    """这个窗口现在停在**有预览画布**的那几页上吗。

    判据是「找得到那个画布控件」以外的**语言无关**信号：预览面在 UIA 里没有自己的
    节点（见 `strip_crop` 的注释），所以按统计条 `Scrub` 认 —— 图表页都有那条播放
    栏，设置页没有。`verify-watermark` 里别处也用过同一条。
    """
    try:
        return vfb.find(lambda c: c.AutomationId == "Scrub", window) is not None
    except Exception:  # noqa: BLE001
        return False


def show_strip(window):
    """把设置页那条反馈预览弄进视口，返回锚点（浓度滑条）的屏幕矩形。

    **滚动交给 `ScrollItemPattern.ScrollIntoView`，不再试百分比。** 原来按
    `SetScrollPercent(45/55/65/75)` 试四个位置、取第一个「滑条在窗口里、下面还留得下
    120 像素」的 —— 这一次它**停在了一个真错的位置上**：设置页又长了一截（市场那张卡片
    挪到了最顶），第四次试的 75% 让滑条落在 `(612, 308, 1012, 349)`，判据成立、跳出循环，
    可实测那一趟已经滚过页面底部，滑条与它下面那条预览都出了视口。`strip_crop` 于是从
    `y=349` 往下扫 220 行，扫到的是卡片下面的别的东西，量出 0.0000% —— 而这个读数与
    「水印没画」**一模一样**，是这一轮最难查的一条假线索。

    百分比本来就是猜的：卡片顺序、每张卡片几行控件都是会变的东西（水印卡片这一轮就从
    倒数第二挪下去了）。控件自己知道该滚到哪，问它。

    坐标**滚完再读一次**：`ScrollIntoView` 之后 `BoundingRectangle` 才是最终位置，
    滚之前读到的那个数正是上面那次事故的来源。

    **`ScrollIntoView` 只保证那个控件自己可见，不保证它下面的东西可见。** 实测：滚完
    浓度滑条进了视口（停在 y≈657），而**预览条在它下面、被窗口下沿切掉**（页面滚到
    58.8%，滑条下面还有预览条 + 一段说明文字）。这一页的缩放是 150%，差着九十来像素。

    所以这里是**两级**：先请控件自己滚（它对不可用的控件不生效，未订阅时浓度滑条是灰的
    —— 而那种时候设置页上本来就没有浓度可调，下面几条浓度判据也不该跑）；**再按画面
    确认预览条真的在**，不在就按几个百分比往下推（实测 65~80 都能让它完整可见）。

    「再按画面确认」是关键：推偏了**不会报错**，只会安静地量到别的区域，而那个读数与
    「水印没画」一模一样 —— 这一轮就是这样追了半天。所以每一步都拿画面回答「它在不在」。
    """
    anchor = vfb.require(window, "WatermarkStrengthSlider")

    try:
        scroll = anchor.GetPattern(auto.PatternId.ScrollItemPattern)

        if scroll is not None:
            scroll.ScrollIntoView()
            time.sleep(1.0)
    except Exception:  # noqa: BLE001 - 不支持就按当前位置读
        pass

    if _strip_is_visible(window):
        return anchor.BoundingRectangle

    control = vfb.require(window, "WatermarkToggle")
    scroller = vfb.pat(control.GetParentControl(), auto.PatternId.ScrollPattern)

    if scroller is not None and scroller.VerticallyScrollable:
        for percent in (65, 70, 75, 80):
            try:
                scroller.SetScrollPercent(-1, percent)
                time.sleep(1.0)
            except Exception:  # noqa: BLE001 - 滚不动就按当前位置读
                break

            if _strip_is_visible(window):
                break

    return anchor.BoundingRectangle


def _strip_is_visible(window):
    """画面上现在认得出那条预览吗。见 `strip_geometry`。

    **不走 `winui.capture`**：那个函数每次都抬窗口、重试最多四次、每次睡 0.6 秒 ——
    它是给「要留下来量的那张图」用的，而这里只是问一句「在不在」，一次要问好几遍。
    所以直接抓一张到临时文件（同一张图会被覆盖），读一读就删掉。
    """
    path = os.path.join(OUT, "_strip-probe.png")

    try:
        window.CaptureToImage(path)
        image = Image.open(path).convert("RGB")
    except Exception:  # noqa: BLE001 - 抓不到就是看不见
        return False

    return strip_geometry(np.asarray(image, dtype=np.int16)) is not None


def strip_geometry(a):
    """那条预览在数组里的行列范围，认不出就是 None。

    认法是画面自己的特征：**设置页里唯一一条横跨卡片的深色带**（卡片是浅灰 245 上下、
    预览条是接近黑的渐变）。先在行方向取最长连续段，再取它的列边界 —— 列边界也一起认，
    而不是照抄滑条的宽度，因为面板列范围里还夹着窗口左侧露出来的背景图片（它也是暗的）。

    **形状要一起验**：高 60~130 行（XAML 给的 72 乘上窗口的 150% 缩放，实测 86~89）、
    宽 ≥500 列（实测 795）。认错的样子必须与认对的样子分得开 —— 这一轮就是没分，从滑条
    坐标往下扫到一段别的东西，量出 0.0000%，而那个读数与「水印没画」一模一样。

    **「暗」的阈值不能卡太紧**：预览条的亮度跟着浓度走（10% 时均值 20 上下，拉满 40% 时
    高到 50 开外），而卡片是 245。120 在两头之间都留得下。
    """
    height, width = a.shape[:2]

    probe = a[:, width // 2:width - 20]
    rows = [y for y in range(height) if probe[y].mean() < 120]

    if not rows:
        return None

    best = (0, 0)
    start = prev = rows[0]

    for y in rows[1:]:
        if y - prev > 2:
            if prev - start > best[1] - best[0]:
                best = (start, prev)

            start = y

        prev = y

    if prev - start > best[1] - best[0]:
        best = (start, prev)

    top, bottom = best

    if not 60 <= bottom - top <= 130:
        return None

    middles = [a[y] for y in range(top + 8, bottom - 8, max(1, (bottom - top) // 8))]
    columns = [x for x in range(width) if all(row[x].mean() < 120 for row in middles)]

    if len(columns) < 500:
        return None

    # 上下各缩进两行：预览条自己的圆角边也在这一段里。
    return top + 2, bottom - 1, columns[0], columns[-1] + 1


def strip_crop(window, name):
    """设置页那条反馈预览的像素，扫不到就是 None。

    它**不是 UIA 里的一个控件**：`WatermarkPreview` 是 `Grid` 的子类，而 Grid 在 UIA 里没有
    自己的节点（实测按 AutomationId 找它，一个都找不到）。所以位置只能从**画面**里认，
    规则见 `strip_geometry` —— 那里也写着为什么不能从滑条的坐标往下推。

    这里只负责：先把它弄进视口（`show_strip`），拍一张，按 `strip_geometry` 裁下来。
    """
    show_strip(window)

    image = Image.open(shot(window, name)).convert("RGB")
    a = np.asarray(image, dtype=np.int16)
    geometry = strip_geometry(a)

    if geometry is None:
        return None

    top, bottom, left, right = geometry

    return a[top:bottom, left:right]


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

    # **先把它滚进视口，再展开。** 下拉在屏外时 `Expand()` 报成功而列表根本没出来 ——
    # 于是 `find_all` 拿到的还是页面上原有的项，`name in seen` 对**每一个**候选都为假，
    # 报出来的样子是「下拉里 176 项，没有 KaiTi」，而 KaiTi 就在第一屏。
    show_strip(window)

    combo.SetFocus()
    time.sleep(0.3)

    expand = vfb.pat(combo, auto.PatternId.ExpandCollapsePattern)

    if expand is None:
        print("      （下拉不支持 ExpandCollapsePattern）")
        return False

    for _ in range(4):
        if expand.ExpandCollapseState == auto.ExpandCollapseState.Expanded:
            break

        expand.Expand()
        time.sleep(1.2)

    # 展开之后按名字找。找名字而不是找序号：序号换一台机器就是另一款字体，而选到哪一款
    # 决定了画面变多少。
    #
    # **找到的只是已经渲染出来的那些项**：这一台机器上 176 个族，下拉不会一次全建出来。
    # 所以候选要给几款**排在前面的**（`KaiTi` 在头三十项里），而脚本要**逐个试**而不是
    # 认定某一款必须在 —— 找不着的那一款换一台机器就可能在前排。
    items = vfb.find_all(
        lambda c: c.ControlTypeName == "ListItemControl", window)

    if not items:
        items = vfb.find_all(
            lambda c: c.ControlTypeName == "ListItemControl",
            auto.GetRootControl(), limit=400)

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

    # ---- 0) 先把上一趟留下的东西清掉，再从已知状态开始
    #
    # **浓度与字体都是会持久化的偏好，而上一趟可能是失败退出的**（脚本在中间某步抛了，
    # 收尾那段就没跑到）。这一轮就是这样翻车的：上一趟停在浓度 40% 上，于是这趟的
    # `plain`（本该是默认 10%）拍到的其实是 40% —— 后面对比「拉满与默认」自然量出
    # 0.00% 差异，判据红掉而产品是对的。同一趟里 `font` 与 `font-back` 也撞上同一个坑。
    #
    # 所以**不假设起点**：浓度回默认、字体回默认、开关回开、文字回默认，四件事都显式
    # 做一遍。顺序上浓度与字体要**在开关打开之后**（关着的时候那几个控件是灰的，
    # 摆不动）。
    settings(window)
    settle(window, True, DEFAULT_TEXT)
    set_strength(window, DEFAULT_STRENGTH)
    pick_font(window, DEFAULT_FONT)

    # ---- 1) 默认：摆到「开 + 默认文字」，重启后还在 —— 验持久化
    window = restart()

    settings(window)
    on, text = state_of(window)

    check("开关与文字都记着（重启之后）", on and text == DEFAULT_TEXT,
          f"开={on} 文字={text!r}")

    # ---- 2) 开着：设置页那条反馈预览上先看得见，然后图表页的预览面上也有
    on_strip = strip_band(window, "verify-watermark-sample-on.png")

    check("设置页那条预览上也画着水印（改完当场看得见）",
          on_strip is not None and on_strip > GRAIN_ON,
          "纹理占 {:.3%}".format(on_strip) if on_strip is not None else "没扫到那一条")

    # **进图表页之前把浓度重设一次**，这是「不假设起点」的最后一环。
    #
    # 实测（1.0.15.0 Debug，装完之后第一次跑）：冷启动后**图表页第一次**被建起来时，
    # 画布上的水印层没有画上 —— 那一刻量到 0.067%，而同一趟里设置页那条预览是 4.7%、
    # 同一窗口尺寸下正常值是 6.09%。此后任何一次设置变更都会把它补回来，所以后面几步
    # （都经过 `settle`）都是好的，只有 base 这一张是裸的。判据要量的是「水印画没画」，
    # 不能让它取决于这一页是第几次被建起来 —— 碰一下浓度，与其余几步拉齐。
    set_strength(window, DEFAULT_STRENGTH)

    vfb.goto_first_page(window)

    base = shot(window, "verify-watermark-on.png")

    base_grain = grain(base)

    check("开着的画面上有水印纹理", base_grain > GRAIN_ON,
          "纹理占 {:.3%}".format(base_grain))

    # ---- 3) 关掉：一格纹理都不该有
    settings(window)
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
    settings(window)
    settle(window, True, "ABCD")
    vfb.goto_first_page(window)
    renamed = shot(window, "verify-watermark-renamed.png")

    check("改了文字画面就变了", diff_ratio(base, renamed) > 0.01,
          "与默认那句差 {:.2%}".format(diff_ratio(base, renamed)))

    check("改了文字水印仍然在", grain(renamed) > GRAIN_ON,
          "纹理占 {:.3%}".format(grain(renamed)))

    # ---- 5) 清空：回到默认那句话，不是「没有水印」
    settings(window)
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
    settings(window)
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
    settings(window)

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
    settings(window)
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
