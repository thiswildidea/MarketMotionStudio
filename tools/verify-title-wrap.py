# -*- coding: utf-8 -*-
r"""验证「所有页面的标题都支持换行」——手动回车断行、超宽自动折行、折出第二行时下面整体下移一行。

**判据是「头部那几条墨迹带 + 从源码常量算出来的位移」。** 画面上没有任何一处会写「标题折成了
两行」，能问的只有像素：市场成交额页的头部四行（标题 0.155 / 副标题 0.187 / 交易日 0.214 /
日期 0.2533）在预览里是四条亮带，折出第二行之后应当是**五条**，而且四条老带各下移
`TitleLineHeight × scale`、标题的第一行**一动不动**。这几条里最要紧的是「各下移同一个数」——
只数带数会把「第二行画出来了但下面没让位」判成通过，而那正是这次的错法：两行字叠在副标题上，
画面看着像字重了一点。

**再往下量一行，确认整摞都让了位**（而不只是紧挨着标题的那一行）：标题下面那个 128 像素的
总额数字。量它有两个坑，都踩过了：① 它的颜色 `(14,161,218)` 平均亮度只有 **131**，用头部小字
那个 140 的门槛会把它切成一条 41 像素高的带变成三个碎点（`INK_WIDE` 就是为这件事分开的）；
② 认它**不能按窗口里的位置** —— 同一个窗口里还坐着日期那一行（折行帧里它自己也被挪到了
0.275）和斜向水印，位置随帧而变。能分辨的是每一行的亮点数：水印 ≤12、日期 ≤30、大数字 80~90
且上下有 35 行 —— 所以取窗口里**峰值最大那一条**（`dominant`），并顺手断言它有 25~50 行高，
免得哪天量到的是柱子或日期那一行还浑然不觉。

**位移不写死**：`67.2 × 画布高 / 1920`，两个数都来自源码常量（`TitleLineHeight`、
`VideoFormat.BaselineHeight`），画布高从截图里量。写死 24 的话，预览换一个窗口大小就全红。

**输入走 ValuePattern，不走键盘。** 标题框现在允许回车，而 `SendKeys` 的粘贴路径在这台机器上
把文字搅成了一团（实测贴进去的是一段没见过的旧文本）；`SetValue` 写进去读回来是准的，而且
WinUI 的编辑框会把 `\n` 归一成 `\r` —— 这一条同时验证了 `TitleText` 里那次归一。

**收尾无条件把标题清空**：它是全局持久偏好，脚本留在上面，下一次拍商店图就会跟着冒出来
（`tools/clear-frame-titles.py` 那一整个脚本就是为这件事存在的）。

用法：python tools\verify-title-wrap.py
"""
import importlib.util
import os
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

# 文案注入脚本按路径加载：新说明、新手册条目的**唯一事实来源在它们那里**，
# 这里再抄一份就等于给自己留一份迟早对不上的副本。
_resw_spec = importlib.util.spec_from_file_location(
    "ptw_resw", os.path.join(HERE, "port-title-wrap-resw.py"))
ptw_resw = importlib.util.module_from_spec(_resw_spec)
_resw_spec.loader.exec_module(ptw_resw)

_help_spec = importlib.util.spec_from_file_location(
    "ptw_help", os.path.join(HERE, "port-title-wrap-help.py"))
ptw_help = importlib.util.module_from_spec(_help_spec)
_help_spec.loader.exec_module(ptw_help)

# 基线画幅高（`VideoFormat.BaselineHeight`）与两行标题的行距（`FrameContext.TitleLineHeight`）。
BASELINE_HEIGHT = 1920
TITLE_LINE_HEIGHT = 0.035 * BASELINE_HEIGHT

# 头部窗口：只量画布最上面这三成，避开绘图区里的柱子和 128 像素那个大数字。
HEAD_WINDOW = 0.30

# 一条带的判据：这一行横向有 ≥3 个亮点。标题是两三个字，副标题是一行说明，都远超 3。
BAND_MIN = 3
# 头部小字（细笔画，字号 62×0.3557 里的 8~9 像素那一档）用高门槛：低了会把画布底色和斜向水印
# 也算成墨。大数字另有一个门槛，见 INK_WIDE。
INK = 140
# 128 像素那个大数字本身是 `(14,161,218)`，平均亮度 131 —— 用 140 会把它切成碎点，
# 于是「总额那一行是单独一条带」永远红，而画面完全正常。
INK_WIDE = 120

# 一个标题的墨迹带高约 21 像素（62 字号的 CJK 在 0.3556 缩放下），下面几行是 8~9。
# 用它把「第二条是标题的第二行」和「副标题被人挪下来了」分开。
TITLE_BAND_MIN = 15

SHIFT_TOLERANCE = 2.5

FAILED = []
CHECKS = []
NOTES = []

# 每种情形一帧，存下来给人看。
SHOTS = []

# 每个情形都**显式写下标题**：标题框会恢复上一次会话留下的值（这台机器上就留着一段），
# 靠「什么都不设」当单行基准，量到的是上一轮那个标题，不是单行标题。
CASES = {
    # 短到一行放得下、且没有手动断行 —— 四条带。
    "single": "两市成交额",
    # 同样的字数，但中间敲了回车 —— 五条带，第一行不动。
    "manual": "两市成交额\n换个说法",
    # 没有换行符，靠宽度折 —— 也是五条带。
    "auto": "市场成交额的一行标题放不下的时候会自动折到第二行上去",
    # 清空 → 回该页的默认标题（一行），四条带回到原位。
    "cleared": "",
}

# 标题下面那一摞里再挑一行来量：运行中的总额（0.284 那个 128 像素的大数字，墨迹带 35 像素高）——
# 和副标题、日期走的是同一套行锚点，但离得远、字号又大，量它等于确认「整摞都动了」而不是只有紧挨着
# 标题的那一行动了。窗口要够宽才容得下折行帧里被挪下来的那一行（0.276 → 0.348），
# 上下界只要把日期那一行和绘图区（0.377）都圈进来即可 —— 认哪一条带不靠位置，靠 `dominant`。
TOTAL_WINDOW = (0.24, 0.37)
# 大数字那条带应有的高度（单行帧 188~222、折行帧 212~246 都是 35 行）。日期那一行是 9 行、
# 柱子是一根几十行但峰值低 —— 这个区间把「量到的确实是那个大数字」这句话钉住。
TOTAL_BAND = (25, 50)


def check(label, ok, detail=""):
    print(("  ✓ " if ok else "  ✗ ") + label + ("  — " + detail if detail else ""))

    CHECKS.append(label)

    if not ok:
        FAILED.append(label)


def note(text):
    print("    · " + text)
    NOTES.append(text)


def read(*parts):
    return open(os.path.join(SRC, *parts), encoding="utf-8-sig").read()


# ---- 源码断言 -------------------------------------------------------------------

# 画标题的十一处：十个渲染器 + 空数据时的底板。名字是文件里那句 `_title.Draw(` 的宿主。
TITLE_SITES = [
    "Render/TurnoverRenderer.cs",
    "Render/IntradayRenderer.cs",
    "Render/CandleRenderer.cs",
    "Render/DcaRenderer.cs",
    "Render/PositionRenderer.cs",
    "Render/SectorRaceRenderer.cs",
    "Render/UnderwaterRenderer.cs",
    "Render/FxCorridorRenderer.cs",
    "Render/StockDualRenderer.cs",
    "Render/MatrixRenderer.cs",
    "Render/StageRenderer.cs",
]

# 老写法：一行放不下就缩字号。折行上线后一处都不该再有。
OLD_TITLE = ['Ink.FitSize(session, title, context.Px', 'Ink.FitSize(session, Title, context.Px']


def source():
    context = read("Render", "FrameContext.cs")
    block = read("Render", "TitleBlock.cs")
    ink = read("Render", "Ink.cs")
    panel = read("Views", "VideoSettingsPanel.xaml")
    code = read("Views", "VideoSettingsPanel.xaml.cs")

    import pathlib

    all_render = {
        str(p.relative_to(SRC)).replace("\\", "/"): p.read_text(encoding="utf-8-sig")
        for p in pathlib.Path(SRC, "Render").glob("*.cs")
    }

    print("源码：")

    check("标题块排在字体那一层（一行、两行共用同一份测量与绘制）",
          "public readonly record struct Shape" in block
          and "shape.Size" in block)

    check("让位算术只有一处：三种情形（隐藏 / 一行 / 折行）",
          "public double TitleShift(int titleLines)" in context
          and "-Px(TitleRowHeight)" in context
          and "(titleLines - 1) * TitleLineHeight" in context)

    check("行距由行高比例乘出来，不是裸数",
          "TitleLineHeight = HeaderRowPitch * VideoFormat.BaselineHeight" in context)

    check("折行间距 = 头部行距（0.035）—— 折一行正好让出一条头部行",
          "HeaderRowPitch = 0.035" in context)

    check("行锚点收的是行数，不是「显示 / 隐藏」这个开关",
          "public double HeaderRow(double fraction, int titleLines)" in context)

    # 错法的形状是「把显示开关当行数交给行锚点」：`HeaderRow(0.187, ShowTitle)`、`ContentTop(ShowTitle)`。
    # 不能只搜 `, ShowTitle)` —— 开关本身还要合法地出现在三处：属性声明、`_title.For(..., ShowTitle)`
    # 和 `_title.Draw(..., _title.For(..., ShowTitle))`。所以逐行判形：出现开关、又不在这三处里，
    # 就是错的。
    stale = []

    for name, text in sorted(all_render.items()):
        for number, line in enumerate(text.splitlines(), 1):
            if "ShowTitle" not in line or "_title.For(" in line:
                continue

            if line.strip().startswith(("public bool ShowTitle", "///", "//")):
                continue

            stale.append("{}:{}".format(name, number))

    check("渲染器里没有一处再把「显示开关」当行数传给行锚点", not stale, ", ".join(stale) or "无")

    # 上面那条是「不许」，这条是「必需」：开关得真的流进标题块，隐藏标题才还有依据
    # （隐藏 = 行数 0，由 TitleBlock 一家算出来，而不是渲染器自己判断要不要画）。
    blind = [name for name in TITLE_SITES
             if "context, ShowTitle).Lines" not in all_render[name]]

    check("十一处的显示开关都真的流进了标题块（隐藏那一路还有依据）", not blind,
          ", ".join(blind) or "无")

    check("十一处标题都走同一个标题块",
          all("_title.Draw(" in all_render.get(name, "") for name in TITLE_SITES),
          "缺：{}".format(", ".join(name for name in TITLE_SITES
                                   if "_title.Draw(" not in all_render.get(name, ""))) or "无")

    left = sorted(name for name, text in all_render.items()
                  if any(old in text for old in OLD_TITLE))

    check("没有一处还在「缩字号到一行放得下」", not left, ", ".join(left) or "无")

    # 行数必须在读第一个行锚点之前算出来：折两行而没让位，就是两行字叠在副标题上。
    late = []

    for name in TITLE_SITES:
        text = all_render[name]
        at = text.find("public void Draw(CanvasDrawingSession session, FrameContext context)")
        head = text[at:at + 1400]

        if at < 0 or "_titleLines = _title.For(" not in head:
            late.append(name)

    check("十一处都在 Draw 的开头就把行数算出来（在第一个行锚点之前）",
          not late, ", ".join(late) or "无")

    check("测量与绘制用同一份解析结果（不是各自量一次）",
          "_title.Draw(session, context, title, _title.For(session, title, context, ShowTitle)" in all_render[
              "Render/TurnoverRenderer.cs"])

    check("画布上的字由 Ink 的同一处基线换算画出去",
          "public static void Draw(\n        CanvasDrawingSession session, CanvasTextLayout layout" in ink)

    check("标题框允许敲回车", 'AcceptsReturn="True"' in panel)

    check("标题框能看见第二行（多行输入、且不是一行高的框）",
          'TextWrapping="Wrap"' in panel and 'MinHeight="64"' in panel)

    check("换行符在「读标题」那一处归一成 \\n（编辑框给的是 \\r）",
          'Replace("\\r\\n", "\\n").Replace(\'\\r\', \'\\n\')' in code)

    # 14 语言的两处文案，直接对着注入脚本的表断 —— 表变了这里就跟着断，不会各走各的。
    missing = []

    for tag, want in ptw_resw.NOTE.items():
        text = read("Strings", tag, "Resources.resw")

        if "<data name=\"StudioTitleNote.Text\"><value>" + want not in text:
            missing.append(tag)

    check("14 语言的标题说明都换成了折行版", not missing, ", ".join(missing) or "无")

    stale = [tag for tag, want in ptw_resw.NOTE.items()
             if "缩放字号而不是被裁掉" in want]

    check("旧说法「缩小字号而不是被裁掉」14 语言里一句不剩", not stale, ", ".join(stale) or "无")

    missing = [tag for tag, want in ptw_help.ENTRY.items()
               if want not in open(os.path.join(REPO, "src", "MarketMotionStudio", "Assets",
                                                "Help", "help-{}.md".format(tag)),
                                   encoding="utf-8-sig").read()]

    check("14 份帮助手册都补了标题折行那一条", not missing, ", ".join(missing) or "无")


# ---- 真机 -----------------------------------------------------------------------

def texts(control, depth=0, limit=12, out=None):
    out = [] if out is None else out

    if control is None or depth > limit:
        return out

    try:
        name = control.Name

        if name and name.strip():
            out.append(name.strip())
    except Exception:  # noqa: BLE001
        pass

    try:
        for child in control.GetChildren():
            texts(child, depth + 1, limit, out)
    except Exception:  # noqa: BLE001
        pass

    return out


def status_text(win):
    bar = winui.find(win, lambda c: c.AutomationId == "Status")

    return " ".join(texts(bar)) if bar is not None else ""


def wait_status(win, seconds=300):
    deadline = time.time() + seconds

    while time.time() < deadline:
        time.sleep(2.0)
        text = status_text(win)

        if text:
            return text

    return None


def goto_page(win, nav_id):
    nav = winui.find(win, lambda c: c.AutomationId == nav_id)

    if nav is None:
        return False

    try:
        nav.GetSelectionItemPattern().Select()
        time.sleep(2.0)
        return True
    except Exception:  # noqa: BLE001
        return False


def fetch(win):
    button = winui.find(win, lambda c: c.AutomationId == "FetchButton")

    if button is None:
        return None

    try:
        button.GetInvokePattern().Invoke()
    except Exception:  # noqa: BLE001
        return None

    return wait_status(win)


def set_title(win, text):
    """写进标题框并读回来。返回 (编辑框里的值, 页面认的值)。

    编辑框会把 `\n` 变成 `\r`，所以两个都要看：一个证明输入真的进去了，
    另一个证明读标题那一处把 `\r` 归一回了 `\n`。
    """
    box = winui.find(win, lambda c: c.AutomationId == "TitleBox")

    if box is None:
        return None, None

    box.GetValuePattern().SetValue(text)
    time.sleep(1.6)

    raw = box.GetValuePattern().Value

    return raw, raw.strip().replace("\r\n", "\n").replace("\r", "\n")


def set_scrub(win, value):
    slider = winui.find(win, lambda c: c.AutomationId == "Scrub")

    if slider is None:
        return False

    slider.GetRangeValuePattern().SetValue(value)
    time.sleep(1.0)

    return True


def shot(win, name):
    path = os.path.join(OUT, name)

    return path if winui.capture(win, path) else None


def crop_of(path):
    whole = Image.open(path).convert("RGB")
    box = winui.canvas_box(whole)

    if box is None:
        return None

    bottom = winui.frame_bottom(whole, box)
    left, right, top, _ = box

    return whole.crop((left, top, right + 1, bottom + 1))


def bands(path, low=0.0, high=HEAD_WINDOW, ink=INK, least=BAND_MIN):
    """画布上 `[low, high)` 这一段里的墨迹带，一行为一条：(top, bottom, 峰值)，**画布坐标**。

    坐标一律是画布坐标系（加了 `low` 的偏移），不是窗口内的相对行号：两帧各自的窗口内偏移
    不同，拿相对行号相减会得出一个和位移毫无关系的数（而且看起来还挺像个位移）。
    """
    crop = crop_of(path)

    if crop is None:
        return None, None

    pixels = crop.load()
    width, height = crop.size
    first = int(height * low)
    rows = []

    for y in range(first, int(height * high)):
        lit = 0

        for x in range(width):
            r, g, b = pixels[x, y]

            if (r + g + b) / 3 > ink:
                lit += 1

        rows.append(lit)

    out = []
    start = None

    for index, lit in enumerate(rows):
        if lit >= least:
            if start is None:
                start = index
        elif start is not None:
            out.append((start + first, index - 1 + first,
                        max(rows[start:index])))
            start = None

    if start is not None:
        out.append((start + first, len(rows) - 1 + first, max(rows[start:])))

    return out, crop


def dominant(path, low, high):
    """窗口里**峰值最大**的那一条带 —— 标题下面那个 128 像素的大数字。

    不按位置认它：同一个窗口里还有日期那一行（折行帧里它自己也被挪下来了）和斜向水印，
    它们的位置随帧而变，而亮点数差一个数量级（水印 ≤12、日期 ≤30、大数字 80~90）。
    """
    found, crop = bands(path, low, high, ink=INK_WIDE, least=1)

    if not found:
        return None, crop

    return max(found, key=lambda band: band[2]), crop


def mean_difference(first, second):
    a = np.asarray(first, dtype=np.float32)
    b = np.asarray(second, dtype=np.float32)

    if a.shape != b.shape:
        return None

    return float(np.abs(a - b).mean())


def main():
    source()

    print("\n真机：")

    win = winui.launch(winui.EXE, wait_seconds=45)

    if win is None:
        check("窗口起来了", False)
        return 1

    try:
        time.sleep(2)

        check("切到市场成交额页", goto_page(win, "NavMarketTurnover"))

        message = fetch(win)

        check("取数成功（要一份真的数据才看得见标题下面那些行）",
              message is not None and "交易日" in message,
              (message or "（状态条空）")[:90])

        # 头部那四行是开场 1 秒内淡入的，进度 0 上一个字都没有 —— 拖到一半。
        check("拖到一半看静止的一帧", set_scrub(win, 0.5))

        seen = {}

        for name, text in CASES.items():
            raw, resolved = set_title(win, text)

            check("标题「{}」写进去了".format(name), resolved == text,
                  "{!r} -> {!r}".format(text, resolved))

            path = shot(win, "verify-title-wrap-{}.png".format(name))
            SHOTS.append(path)

            found, crop = bands(path)

            check("截到的是本窗口的一帧（{}）".format(name),
                  found is not None and crop is not None)

            if found is None:
                continue

            totals, _ = dominant(path, *TOTAL_WINDOW)

            seen[name] = (found, crop, totals)

            note("{}：头部 {} 条带 {}".format(name, len(found), found))
            note("{}：总额那一行 {}（峰值 {}{}）".format(
                name, totals[:2] if totals else None,
                totals[2] if totals else "-",
                "，高 {} 像素".format(totals[1] - totals[0] + 1) if totals else ""))

        if len(seen) < len(CASES):
            check("四种情形都量到了", False, "只量到 {}".format(sorted(seen)))
            return 1

        sizes = {name: state[1].size for name, state in seen.items()}

        check("四帧的画布一样大（量出来的位移才可比）",
              len(set(sizes.values())) == 1, str(sizes))

        (base, base_crop, base_total) = seen["single"]
        scale = base_crop.size[1] / BASELINE_HEIGHT
        shift = TITLE_LINE_HEIGHT * scale

        check("单行标题：头部四行就是四条带", len(base) == 4,
              "{} 条：{}".format(len(base), base))

        check("第一条带是标题（不是副标题那条八像素的）",
              base and base[0][1] - base[0][0] >= TITLE_BAND_MIN,
              "高 {} 像素".format(base[0][1] - base[0][0]) if base else "（没有带）")

        check("总额那一行量到的是大数字那条带（25~50 像素高，不是日期那条 9 像素的）",
              base_total is not None
              and TOTAL_BAND[0] <= base_total[1] - base_total[0] + 1 <= TOTAL_BAND[1],
              "{}".format(base_total))

        # 一行的位移：`67.2 × scale` 像素。画布高从截图量，两个常量在源码里。
        note("画布 {}×{}，scale={:.4f}，一行 = {:.1f} 像素".format(
            base_crop.size[0], base_crop.size[1], scale, shift))

        for name in ("manual", "auto"):
            got, _, total = seen[name]

            check("「{}」折出第二行".format(name), len(got) == 5,
                  "{} 条：{}".format(len(got), got))

            if len(got) != 5:
                continue

            check("「{}」标题的第一行没动（块往下长，不往上顶）".format(name),
                  abs(got[0][0] - base[0][0]) <= 1,
                  "{} vs {}".format(got[0][0], base[0][0]))

            check("「{}」第二条带是标题的第二行（厚度是标题那一档）".format(name),
                  got[1][1] - got[1][0] >= TITLE_BAND_MIN,
                  "高 {} 像素".format(got[1][1] - got[1][0]))

            offsets = [got[i + 1][0] - base[i][0] for i in range(4)]

            check("「{}」下面四行整体下移同一个数（= 一行标题）".format(name),
                  all(abs(offset - shift) <= SHIFT_TOLERANCE for offset in offsets),
                  "各 {}，期望 {:.1f}".format(offsets, shift))

            check("「{}」更靠下的那一行（总额）也下移同一个数".format(name),
                  total is not None and base_total is not None
                  and abs((total[0] - base_total[0]) - shift) <= SHIFT_TOLERANCE,
                  "{} vs {}，期望 {:.1f}".format(
                      total[:2] if total else None,
                      base_total[:2] if base_total else None, shift))

        got, _, total = seen["cleared"]

        check("清空标题后回到该页默认的一行，四条带回到原位",
              len(got) == 4 and all(abs(got[i][0] - base[i][0]) <= 1 for i in range(4)),
              "{}".format(got))

        check("清空后总额那一行也回到原位",
              total is not None and base_total is not None
              and abs(total[0] - base_total[0]) <= 1,
              "{} vs {}".format(total[:2] if total else None,
                                base_total[:2] if base_total else None))

        difference = mean_difference(
            np.asarray(seen["single"][1], dtype=np.float32),
            np.asarray(seen["manual"][1], dtype=np.float32))

        check("单行与折行是两张真的不一样的画面",
              difference is not None and difference > 2.0,
              "平均像素差 {:.2f}".format(difference) if difference is not None else "尺寸不同")

        return 0
    finally:
        # 标题是全局持久偏好：留在这里会跟着出现在下一次拍的所有商店图里。
        try:
            set_title(win, "")
            note("收尾：标题框已清空")
        except Exception as exc:  # noqa: BLE001
            note("收尾清标题失败：{}".format(exc))

        winui.kill(winui.EXE)


if __name__ == "__main__":
    code = main()

    print("\n展示图：{}".format(", ".join(os.path.basename(p) for p in SHOTS if p)))
    print("{}/{} 通过".format(len(CHECKS) - len(FAILED), len(CHECKS))
          if FAILED else "全部通过（{} 项）".format(len(CHECKS)))

    sys.exit(code or (1 if FAILED else 0))
