# -*- coding: utf-8 -*-
"""把条形榜截图里的**墨迹剖面**打印出来 —— 用来校准 verify-racelabel.py 的阈值。

字号是渲染器算出来的一个数，UIA 读不到，只能量像素。但「亮像素」的阈值定在哪，
直接决定量出来的字高：定高了把字最上最下那一行切掉，定低了把背景当字。

这个脚本不判断对错，只把事实铺开：每一行在名字栏里的逐行亮度计数，以及不同阈值下
量出来的字高。阈值该怎么定，看完这张表就有答案。

用法：python tools/probe-racelabel-pixels.py [截图路径]
"""
import os
import sys
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent


def vivid(r, g, b):
    return max(r, g, b) - min(r, g, b) > 60 and max(r, g, b) > 90


def bar_bands(image):
    """与 verify-racelabel.py 同一套找法：最密的鲜艳列 → 该列区间里的连续行段。"""
    width, height = image.size
    pixels = image.load()

    columns = [sum(1 for y in range(0, height, 3) if vivid(*pixels[x, y])) for x in range(width)]
    widest = max(columns)

    if widest <= 4:
        return None, []

    band = [x for x, count in enumerate(columns) if count > widest * 0.5]
    left, right = band[0], band[-1]

    across = [sum(1 for x in range(left, right + 1, 3) if vivid(*pixels[x, y]))
              for y in range(height)]

    bands = []
    current = None

    for y, count in enumerate(across):
        if count >= 2:
            if current is None:
                current = [y, y]
            elif y - current[1] <= 2:
                current[1] = y
            else:
                bands.append(tuple(current))
                current = [y, y]
        elif current is not None and y - current[1] > 2:
            bands.append(tuple(current))
            current = None

    if current is not None:
        bands.append(tuple(current))

    if len(bands) >= 5:
        heights = sorted(b[1] - b[0] + 1 for b in bands)
        median = heights[len(heights) // 2]
        bands = [b for b in bands if median * 0.65 <= b[1] - b[0] + 1 <= median * 1.35]

    return (left, right), bands


def profile(pixels, left, y0, y1, reach=90):
    """名字栏里每一扫描行的「亮像素计数」与「最亮像素的最小通道值」。"""
    out = []

    for y in range(y0, y1):
        n = 0
        top = 0
        gap = 0
        x = left - 2

        while x >= 0 and left - x <= reach:
            r, g, b = pixels[x, y]
            low = min(r, g, b)

            if low > 60 and max(r, g, b) - low < 70:
                n += 1
                top = max(top, low)
                gap = 0
            elif n and gap > 4:
                break
            else:
                gap += 1

            x -= 1

        out.append((y, n, top))

    return out


def ink_height(rows, floor):
    hits = [y for y, n, top in rows if n >= 2 and top >= floor]

    if not hits:
        return 0

    return hits[-1] - hits[0] + 1


def value_ink(pixels, left, right, y0, y1):
    """条形右端那一串数值的墨迹行。

    数值用的是**没有被压过的**字号（valueFormat 直接吃 nameSize），而名字用的是压进
    名字栏之后的字号。所以这两个墨迹高的比，就是「整列被压掉了多少」：

        名字墨迹 ≈ 数值墨迹  → 整列没被压，名字栏够宽
        名字墨迹 < 数值墨迹  → 最长的名字把整列缩了，加宽栏宽才真的有用

    判读时注意两者都含 CJK（"55,746亿美元" 里的 亿美元），墨迹高可比；纯数字的
    cap height 只有字号的约 0.71，会比汉字矮。
    """
    rows = []

    # 只扫右端这 70 像素：数值是右对齐画在条形尾巴上的，而条形的**渐变更暗的一端在左**
    # （alpha 0.55 起），一路扫到左端会把那截暗色块当成墨迹，于是「字高」等于条形高。
    floor_x = max(left, right - 70)

    for y in range(y0, y1):
        n = 0
        x = right

        while x >= floor_x:
            r, g, b = pixels[x, y]

            # 墨色要么是很亮的白（压在深色条上），要么是很暗的深蓝（压在浅色条上），
            # 两种都跟条形自己的鲜艳颜色差得远。
            if (min(r, g, b) > 200 and max(r, g, b) - min(r, g, b) < 40) or max(r, g, b) < 70:
                n += 1

            x -= 1

        if n >= 2:
            rows.append(y)

    if not rows:
        return 0

    return rows[-1] - rows[0] + 1


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "artifacts", "verify-racelabel.png")
    image = Image.open(path).convert("RGB")
    pixels = image.load()
    width, height = image.size

    print(f"截图 {os.path.basename(path)} · {width}×{height}")

    (left, right), bands = bar_bands(image)

    if not bands:
        print("没找到条形")
        return 1

    heights = sorted(b[1] - b[0] + 1 for b in bands)
    centers = [(b[0] + b[1]) // 2 for b in bands]
    gaps = sorted(centers[i + 1] - centers[i] for i in range(len(centers) - 1))

    print(f"条形列区间 x={left}..{right} · {len(bands)} 段")
    print(f"  条形高 中位 {heights[len(heights) // 2]}px（范围 {heights[0]}–{heights[-1]}）")
    print(f"  行距   中位 {gaps[len(gaps) // 2]}px（范围 {gaps[0]}–{gaps[-1]}）")

    # 挑中间三行，把逐行剖面铺开看
    pick = bands[len(bands) // 2 - 1: len(bands) // 2 + 2]

    for y0, y1 in pick:
        rows = profile(pixels, left, y0 - 4, y1 + 5)
        print(f"\n行 y={y0}..{y1}（条形 {y1 - y0 + 1}px）名字栏逐行剖面：")
        print("    y   亮像素  最亮值")
        for y, n, top in rows:
            mark = "  ← 条形内" if y0 <= y <= y1 else ""
            print(f"  {y:5d}  {n:5d}  {top:5d}{mark}")

    # 条形的右端：最长那条条的尾巴，用来量条内数值的墨迹。
    span = []
    for b in bands:
        y = (b[0] + b[1]) // 2
        x = right
        while x >= left and not vivid(*pixels[x, y]):
            x -= 1
        span.append(x)

    print("\n名字墨迹 vs 条内数值墨迹（同一字号画出来的两种字）：")
    print("   行   名字   数值")

    for i, b in enumerate(bands):
        name = ink_height(profile(pixels, left, b[0] - 4, b[1] + 5), 120)
        value = value_ink(pixels, left, span[i], b[0], b[1] + 1)
        print(f"  {i:4d}  {name:5d}  {value:5d}")

    print("\n不同阈值下量出来的字高：")
    print("  阈值   各行字高                中位")

    for floor in (70, 80, 90, 100, 110, 120, 140):
        per = [ink_height(profile(pixels, left, b[0] - 4, b[1] + 5), floor) for b in bands]
        per = [p for p in per if p]
        per.sort()
        print(f"  {floor:4d}   {str(per):<28} {per[len(per) // 2] if per else 0}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
