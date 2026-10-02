#!/usr/bin/env python
"""把商店截图写进 listing CSV 的 DesktopScreenshot1..30 列（14 语言）。

为什么是第二个脚本：`port-listing-csv.py` 只写三段文案，它一开始就写着不碰资产。
截图是另一回事——它得先**把图片搬到 CSV 旁边**。这一列的官方说明是「相对路径(或指向
合作伙伴中心文件的 URL)」，相对路径是相对 CSV 自己所在的目录，所以图片必须和
`docs\\listingData-*.csv` 放在同一个包里上传；原来那五列是上一次上传后回来的
`listingassets` URL，那是商店里的旧图，不是磁盘上的文件。

来源 `artifacts\\store-screens\\<语言>\\`（`tools\\store-screenshots.py` 的产物，被
gitignore），落点 `docs\\store-screens\\<语言>\\`。**目录名用 CSV 列名的小写**
（en-us / zh-hans / pt-br），因为那一列就是按它认语言的，而源目录沿用的是
`store-screenshots.py` 里的 tag（en-US / zh-Hans）。

每语言填几列由磁盘上的文件数决定：市场成交额页只在 A股 市场存在，所以 zh-hans 八张、
其余十三种各七张。填不满的 `DesktopScreenshotN` 一律清空——留着上一次的旧 URL 会让
商店把旧图排在新图后面。`DesktopScreenshotCaption*` 不动（一直是空的）。

**路径必须带上导入文件夹的名字。** Partner Center 导入资产只有两条路：「导入 .csv」
（此时这一列只能填已经上传过的 `listingassets` URL）和「导入文件夹」（文件夹里一个 CSV
加若干图片）。走第二条时，官方文档的例子是 `my_folder/images/screenshot1.png` —— 路径
**从根文件夹名开始**，不是从 CSV 所在目录开始。写 `store-screens/pl/02-sector-race.png`
会被整条拒掉（「您提供的值无效」，99 格全拒），而日志上只说是值不对，不说差在哪。
这里的根文件夹就是 CSV 所在的 `docs`，导入时选它。

幂等：跑第二遍 0 改动。BOM 与 CRLF 保持原样（Partner Center 导出来的就是这个样子）。
"""

import csv
import filecmp
import io
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(
    REPO, "docs", "listingData-9NGDNH0CCW7L-1152921505702020674.csv")
SOURCE = os.path.join(REPO, "artifacts", "store-screens")
TARGET = os.path.join(REPO, "docs", "store-screens")

# CSV 里 DesktopScreenshot 一共给到 30。
MOST_SHOTS = 30

# 导入时选的那个文件夹的名字，路径必须含它（见文件头的说明）。取 CSV 所在目录的
# 目录名，而不是写死一个字符串：导入时选的就是这一个文件夹，两边改一个名字就得一起改。
ROOT = os.path.basename(os.path.dirname(CSV_PATH))

# 前四列不是语言：Field / ID / Type / default。
FIRST_LANGUAGE_COLUMN = 4


def language_columns(header):
    """CSV 的语言列：第 5 列起，到表尾。"""
    return [(index, name.lower())
            for index, name in enumerate(header) if index >= FIRST_LANGUAGE_COLUMN]


def source_dirs():
    """源目录按小写名索引——CSV 的列是 en-us，磁盘上是 en-US。"""
    found = {}

    for name in os.listdir(SOURCE):
        path = os.path.join(SOURCE, name)

        if os.path.isdir(path):
            found[name.lower()] = path

    return found


def copy_shots(code, src):
    """把该语言的截图搬到 docs 下，返回排序后的文件名。

    已存在且逐字节相同的文件不动——重跑一遍不该改写 99 个 PNG 的时间戳。
    """
    dst = os.path.join(TARGET, code)
    os.makedirs(dst, exist_ok=True)

    names = sorted(n for n in os.listdir(src) if n.lower().endswith(".png"))

    for name in names:
        s = os.path.join(src, name)
        d = os.path.join(dst, name)

        if os.path.exists(d) and filecmp.cmp(s, d, shallow=False):
            continue

        shutil.copy2(s, d)

    return names


def main():
    raw = io.open(CSV_PATH, "rb").read()
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig").replace("\r\n", "\n"))))
    header = rows[0]
    columns = language_columns(header)
    sources = source_dirs()

    missing = [code for _, code in columns if code not in sources]

    if missing:
        print("没有这些语言的截图目录：%s" % ", ".join(missing))
        return 1

    # 每语言要填的那一串相对路径，先备好。
    wanted = {}

    for _, code in columns:
        names = copy_shots(code, sources[code])
        wanted[code] = ["%s/store-screens/%s/%s" % (ROOT, code, n) for n in names]

    changed = 0
    report = []

    for row in rows[1:]:
        match = re.match(r"^DesktopScreenshot(\d+)$", row[0])

        if match is None:
            continue

        index = int(match.group(1)) - 1

        for column, code in columns:
            shots = wanted[code]
            value = shots[index] if index < len(shots) else ""

            if row[column] != value:
                row[column] = value
                changed += 1

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerows(rows)

    payload = "\ufeff" if raw[:3] == b"\xef\xbb\xbf" else ""
    io.open(CSV_PATH, "w", encoding="utf-8", newline="").write(payload + buffer.getvalue())

    print("写了 %d 格 → %s\n" % (changed, os.path.basename(CSV_PATH)))

    for column, code in columns:
        shots = wanted[code]
        # 路径从仓库根起算：它已经含了导入文件夹的名字。
        absent = [p for p in shots
                  if not os.path.exists(os.path.join(REPO, *p.split("/")))]
        report.append(len(absent))

        print("  %-8s %2d 张%s" % (
            code, len(shots),
            "" if not absent else "  × 磁盘上缺 %d 个" % len(absent)))

    bad = sum(report)
    print("\n%s" % ("截图与磁盘一致" if bad == 0 else "%d 个文件对不上" % bad))

    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
