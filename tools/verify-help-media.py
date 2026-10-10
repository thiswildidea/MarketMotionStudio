# -*- coding: utf-8 -*-
"""帮助配图：干净不干净、是不是这一页、十四种语言是不是同一套。

三件事都可能错，而且都不会报错，所以都得量：

  1. **混进了别的东西。** 抓图那一刻屏幕上弹了条通知，就跟着进图了。它不影响任何
     判据（图还是"拍到了"），所以没人会发现 —— 上一批图就是这么发的。Windows 的通知
     贴在右下角，所以查右下角那一块：窗口是浅色的，通知是一块深色的圆角矩形，量那一
     块里有多少**暗像素**就能分开（实测真图最多 969，一条通知要占两万以上）。

  2. **拍错了页。** 文件名对、图不对（position.png 里其实是行业板块竞速）。
     查的是**版式**：同一个页面在十四种语言下，9:16 预览帧一定落在同一个位置；
     换一页就换了位置。跨语言比同一页的帧框，比跨页比更容易说清楚 —— 帧的大小
     是固定的，跨页差别也不小，但"十四种语言必须严丝合缝"是一条没有例外的断言。

  3. **十四种语言拍成了同一张。** 切语言没生效，或者复制粘贴。同一语言下，五张
     图不能有两张一模一样。

尺寸和裁剪框都从 tools/help-media.py 读，不写死：那边改了裁剪，这里跟着算。

用法：
  python tools/verify-help-media.py
  python tools/verify-help-media.py --self-test   # 只跑"通知检测两个方向都判得对不对"
"""

import hashlib
import importlib.util
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELP = os.path.join(ROOT, "src", "MarketMotionStudio", "Assets", "Help")

# 通知所在的地方，按图的比例（不是像素）：Windows 的通知贴在右下角。
TOAST_ZONE = (0.70, 0.80)

# 判据是「右下角有没有一大块暗底」，不是「有没有绿色的像素」。
#
# 头一版数的是通知图标那种绿（r<60 且 g>160 且 b>120 且 g>b），而它把**应用自己的**一个
# 14×14 青绿色小图标（众数 (12,200,163)，约 119 px）当成了通知 —— 那个图标是内容的一部分，
# 本来就该出现在手册配图上。于是「干净样本」和「污染样本」都报 119，对照等于没有（2026-10-10）。
#
# 改成数暗像素：窗口是浅色的（卡片 250,249,248、导航栏 245,242,240），通知条是一块深色的
# 圆角矩形。这一块区域里散落着的是文字笔画 —— 实测 70 张新图最多 969 个暗像素（占区域
# 0.8%），而一条 356×90 的通知要占掉两万以上。这两种量差着二十倍，阈值取在中间任何地方都行。
DARK = 80          # 亮度低于这个数算「暗」
TOAST_DARK = 4000  # 右下角暗像素超过这个数 = 有一块通知


def toasted(image):
    """右下角暗像素的个数。多于一整块通知，少于散落的文字笔画。"""
    width, height = image.size
    pixels = image.load()
    hits = 0

    for y in range(int(height * TOAST_ZONE[1]), height):
        for x in range(int(width * TOAST_ZONE[0]), width):
            r, g, b = pixels[x, y]

            if (r * 299 + g * 587 + b * 114) // 1000 < DARK:
                hits += 1

    return hits


def has_toast(image):
    return toasted(image) > TOAST_DARK


def module(path):
    """按路径加载，不复制别人脚本里的常量。"""
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    loaded = importlib.util.module_from_spec(spec)
    saved, sys.argv = sys.argv, [name]

    try:
        spec.loader.exec_module(loaded)
    finally:
        sys.argv = saved

    return loaded


def expected_size(pipeline):
    """裁剪框按 TARGET_WIDTH 缩放之后应当是多大 —— 与 help-media.py 同一条算式。"""
    left, top, right, bottom = pipeline.CROP
    width = right - left
    height = bottom - top
    scale = min(1.0, pipeline.TARGET_WIDTH / width)

    return round(width * scale), round(height * scale)


def runs(values):
    """把一串下标压成连续段 [(起, 止), ...]。"""
    out = []

    for v in values:
        if out and v == out[-1][1] + 1:
            out[-1][1] = v
        else:
            out.append([v, v])

    return [tuple(r) for r in out]


def longest_run(values, gap=0):
    """最长的一段连续下标。gap：中间断开不超过这么多，还算同一段。

    帧里会横着一条浅色的带子（定投页 y≈214、持仓页 y≈237，六七个像素高，是一条
    数值卡或图例），带子那几行暗像素掉到 120 以下，帧就被切成两截 —— 而**长的那一截
    恰好是下半截**，于是量出来的是一个 353×511 的"帧"，比例根本不是 9:16（2026-10-10）。
    """
    merged = []

    for start, end in runs(values):
        if merged and start - merged[-1][1] - 1 <= gap:
            merged[-1][1] = end
        else:
            merged.append([start, end])

    best = None

    for start, end in merged:
        if best is None or end - start > best[1] - best[0]:
            best = (start, end)

    return best


def frame_box(image):
    """9:16 预览帧的外框。

    逐行/逐列数"很暗"的像素：帧是一整块深色矩形，一行里有几百个暗像素；页面
    标题那些字也是黑的，但一行里只有几十个。于是"暗像素超过阈值"的行列围出来
    的就是帧，不受字和面板影响。

    **取最长的一段连续行列，不是取第一和最后一个。** 裁剪框放到 1920x1020 之后，
    画面里多出几条横贯的深色分隔线（单行，1~2 px）；按首尾取会把它们当成帧的下边
    缘，十四种语言里有一半报出 725 之外的高度（2026-10-10）。

    围出来的框还要自己量一遍是不是 9:16 —— 差得远就当没找着，由调用方大声报出来。
    不然框认歪了也会返回一个"看起来像"的框，跨语言比对就变成了比错误。
    """
    width, height = image.size
    pixels = image.load()
    dark = 60
    span = 120

    def row_count(y):
        return sum(1 for x in range(width)
                   if sum(pixels[x, y]) / 3 < dark)

    def column_count(x):
        return sum(1 for y in range(height)
                   if sum(pixels[x, y]) / 3 < dark)

    rows = longest_run([y for y in range(height) if row_count(y) > span], gap=10)
    columns = longest_run([x for x in range(width) if column_count(x) > span], gap=10)

    if rows is None or columns is None:
        return None

    box = (columns[0], rows[0], columns[-1], rows[-1])
    wide = box[2] - box[0] + 1
    tall = box[3] - box[1] + 1

    if wide <= 0 or abs(tall / wide - 16 / 9) > 0.03:
        return None

    return box


def main():
    publish = module(os.path.join(ROOT, "tools", "publish-help-to-support.py"))
    pipeline = module(os.path.join(ROOT, "tools", "help-media.py"))
    size = expected_size(pipeline)
    languages = publish.languages()

    passed = 0
    failed = []

    def check(ok, what):
        nonlocal passed
        if ok:
            passed += 1
        else:
            failed.append(what)

    # 文档点名了哪些图 —— 图集以文档为准，不是以文件夹里有什么为准。
    wanted = []
    for _, name in languages:
        for reference in publish.pictures(os.path.join(HELP, name)):
            if reference not in wanted:
                wanted.append(reference)

    print("语言 %d 种，文档点名的图 %d 张，期望尺寸 %dx%d"
          % (len(languages), len(wanted), size[0], size[1]))

    by_page = {}
    digest = {}

    for language, name in languages:
        for reference in publish.pictures(os.path.join(HELP, name)):
            found, relative = publish.picture_file(HELP, language, reference)

            check(found is not None, "%s 引用的 %s 找不到" % (name, reference))
            if found is None:
                continue

            with Image.open(found) as opened:
                image = opened.convert("RGB")

            check(image.size == size, "%s 是 %dx%d，期望 %dx%d"
                  % (relative, image.size[0], image.size[1], size[0], size[1]))

            hits = toasted(image)
            check(not has_toast(image),
                  "%s 右下角有 %d 个暗像素，多过一整块通知的 %d（通知混进来了）"
                  % (relative, hits, TOAST_DARK))

            box = frame_box(image)
            check(box is not None, "%s 找不到 9:16 预览帧" % relative)

            if box is not None:
                by_page.setdefault(reference, {})[language] = box

            with open(found, "rb") as handle:
                digest.setdefault(language, {})[reference] = hashlib.sha256(handle.read()).hexdigest()

    # 同一页：十四种语言的帧框要一致
    for reference, boxes in sorted(by_page.items()):
        first = None
        for language, box in sorted(boxes.items()):
            if first is None:
                first = (language, box)
                continue

            offset = max(abs(a - b) for a, b in zip(first[1], box))

            # 容差按帧自己的宽度算百分比，不写一个固定像素：预览帧是「剩下多少地方就
            # 多大」，参数面板里的字在有的语言里长一些，面板挤宽了预览就小一圈。实测
            # 月度矩阵页差到 21 px（353 对 341，6%）—— 那是版式，不是拍错。窗口放大
            # 到 1920 之后才显出来：小窗口时预览是被高度卡住的，十四种语言一样大。
            allowed = round((first[1][2] - first[1][0] + 1) * 0.08)
            check(offset <= allowed, "%s 的预览帧：%s 在 %s，%s 在 %s，差 %d px（容差 %d）"
                  % (reference, first[0], first[1], language, box, offset, allowed))

    # 同一语言：五张图不能有重样的
    for language, shots in sorted(digest.items()):
        seen = {}
        for reference, sha in sorted(shots.items()):
            check(sha not in seen, "%s 的 %s 与 %s 一模一样"
                  % (language, reference, seen.get(sha, "?")))
            seen[sha] = reference

    if by_page:
        sample = by_page[wanted[0]]
        print("帧框（%s，取一种语言）：%s" % (wanted[0], sorted(sample.items())[0][1]))
        print("帧框宽度跨语言最大差：%s"
              % max(max(abs(a - b) for a, b in zip(
                  list(boxes.values())[0], box)) for boxes in by_page.values()))

    print("%d 项通过，%d 项失败" % (passed, len(failed)))

    for what in failed:
        print("  ! %s" % what)

    return 1 if failed else 0


def self_test():
    """双向对照：真图要判干净，**合成**的一条通知要判得出来。

    头一版是「把旧图上那条通知搬到现在这张图里」—— 而那个旧样本其实也是干净的：右下角
    那 119 个绿像素是应用自己的 14×14 图标（见文件头）。拿一张干净图当「带通知」的样本，
    等于拿它证明检测器会说"干净"，两头都过不了真。

    所以通知改成**合成**的：一块深色圆角矩形，尺寸照 Windows 的通知来（356×90，贴在
    右下角）。两头就都是确定的 —— 真图必须判干净，合成的那张必须判有通知，任何一头反了
    都说明判据写错了。
    """
    clean = os.path.join(HELP, "media", "zh-Hans", "sector-race.png")

    if not os.path.isfile(clean):
        print("没有对照用的真图：%s（先跑 help-media.py 生成配图）" % clean)
        return 1

    with Image.open(clean) as opened:
        good = opened.convert("RGB")

    width, height = good.size
    left, top = width - 380, height - 110

    pasted = good.copy()
    ImageDraw.Draw(pasted).rounded_rectangle(
        [left, top, left + 356, top + 90], radius=8, fill=(32, 32, 32))

    hits_good = toasted(good)
    hits_bad = toasted(pasted)

    print("真图：%d 个暗像素（阈值 %d）" % (hits_good, TOAST_DARK))
    print("合成一条通知贴上去：%d 个暗像素" % hits_bad)

    ok = hits_good <= TOAST_DARK and hits_bad > TOAST_DARK
    print("对照%s" % ("通过" if ok else "失败 —— 这个检测器认不出通知"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())

    sys.exit(main())
