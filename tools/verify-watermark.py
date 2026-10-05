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
          "Resolve() => Enabled ? new Watermark(Text) : null" in settings)

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
    """把设置页那条反馈预览弄进视口，返回文本框的屏幕矩形。

    滚动容器是文本框的**直接父级**那个 `PaneControl` —— 这一页按 `ScrollViewerControl`
    一个都找不到（`verify-framebackdrop` 里的 `scroll_settings` 因此只是安静地什么都不做），
    所以这里从文本框往上问一句「你会滚吗」。

    45% 那个位置是量出来的：文本框落到 y 611..685，它下面那一条正好整条在窗口里。再多滚
    一点（60%）这一条就跑到卡片上方去了，又采不到。
    """
    box = vfb.require(window, "WatermarkText")
    scroller = vfb.pat(box.GetParentControl(), auto.PatternId.ScrollPattern)

    if scroller is not None:
        try:
            if scroller.VerticallyScrollable:
                scroller.SetScrollPercent(-1, 45)
                time.sleep(1.2)
        except Exception:  # noqa: BLE001 - a page that will not scroll is read where it is
            pass

    return box.BoundingRectangle


def strip_band(window, name):
    """设置页那条反馈预览的水印纹理比例，扫不到就是 None。

    它**不是 UIA 里的一个控件**：`WatermarkPreview` 是 `Grid` 的子类，而 Grid 在 UIA 里没有
    自己的节点（实测按 AutomationId 找它，一个都找不到）。所以位置从**它上面那个文本框**
    往下扫：卡片底色是浅灰、这一条是深色渐变，行均值一眼分得开。

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

    dark = [y for y in range(top, min(image.size[1], top + 220))
            if a[y, left:right].mean() < 100]

    if len(dark) < 20:
        return None

    return grain_array(a[dark[0]:dark[-1] + 1, left:right])


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

    # ---- 6) 收尾：不留痕迹
    vfb.goto_settings(window)
    settle(window, True, DEFAULT_TEXT)

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
