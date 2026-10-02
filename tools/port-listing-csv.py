#!/usr/bin/env python
"""把 docs/store-listing.md 的 14 语言文案写进 Partner Center 导出的 listing CSV。

为什么要有这个脚本：商店文案的**权威源是 `docs/store-listing.md`**（14 语言 × 3 段），
而 Partner Center 只认它自己导出/导入的 CSV。两边一旦靠手抄，就会出现现在这个文件里的
样子——中文列的功能条目没有 `- ` 前缀而英文列有（早年在网页里手填留下的），八种图表的
旧文案还挂在上面，而 md 里早就是十六种了。

**只写三块**：`Description`(ID 2)、`ReleaseNotes`(ID 3)、`Feature1..20`(ID 700+)。
Title（应用名是预留名，不该改）与 `OverrideLogosForWin10` 一律不动 —— 这个脚本改的是
字，不是资产。截图列（`DesktopScreenshot1..30`）也曾经属于「不动」，在值是上一次上传
回来的一串 `listingassets` URL 的时候；现在归 `tools/port-listing-csv-screens.py` 管，
它把图片搬到 `docs\store-screens\` 下并写入相对路径。**两个脚本各管一块，不交叉。**

Partner Center 的上限（learn.microsoft.com 官方答复，写在这里是因为改文案时必踩）：
Description **10,000** 字符、What's new **1,500**、Product features **20 条 × 200 字符**。
前两条 md 里本来就够，第三条不够：十一个语言里那条「十六种图表」的清单有 208–300 字符。
**清单不能删**（那是这个应用是什么），所以按分隔符拆成几条，用 `(1/2)` 标注——
数字和斜杠不需要翻译，而要一条「还有更多图表」的引导句就得在 14 份里各写一句。

幂等：跑第二遍应当 0 改动。BOM 与 CRLF 保持原样（Partner Center 导出的就是这个样子）。
"""

import csv
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKDOWN = os.path.join(REPO, "docs", "store-listing.md")
CSV_PATH = os.path.join(
    REPO, "docs", "listingData-9NGDNH0CCW7L-1152921505702020674.csv")

# Partner Center 的上限，超了导入会被拒。
LIMIT_DESCRIPTION = 10000
LIMIT_RELEASE_NOTES = 1500
LIMIT_FEATURE = 200
MOST_FEATURES = 20

# 拆条时给标注留的位置：` (1/2) ` 最多约 8 个字符。
SPLIT_MARGIN = 8


def read_markdown():
    """14 语言 × (说明, 新增功能, [功能条目])。

    语言代码从 `## English (en-US)` 这种标题的括号里取，正好就是 CSV 的列名小写。
    """
    text = io.open(MARKDOWN, encoding="utf-8").read().replace("\r\n", "\n")
    listing = {}

    for section in re.split(r"^## ", text, flags=re.M)[1:]:
        head = section.split("\n", 1)[0].strip()
        # 全角与半角都要认：中文、日文、繁中的标题是「简体中文（zh-Hans）」，
        # 全角括号——只写 `\(` 的话这三节会被静默跳过，而它们的列留在旧文案上
        # （zh-hans 的功能条还写着「八种图表」，而 md 里早就是十六种了）。
        code = re.search(r"[（(]([^）)]+)[）)]\s*$", head)

        if code is None:
            continue

        parts = re.split(r"^### ", section, flags=re.M)[1:]

        if len(parts) < 3:
            continue

        def body(index):
            chunk = parts[index].split("\n", 1)[1] if "\n" in parts[index] else ""

            # 段落里 markdown 的硬换行是两个空格结尾，CSV 里不需要那两个空格。
            return "\n".join(line.rstrip() for line in chunk.split("\n")).strip()

        features = [
            line.strip() for line in body(2).split("\n")
            # `---` 是 md 里的水平分隔线，不是一条功能。
            if line.strip() and not line.strip().startswith("---")
        ]

        listing[code.group(1).lower()] = {
            "description": body(0),
            "release": body(1),
            # 中文列（用户在网页里手填的）没有 `- ` 前缀，英文列有。统一去掉：
            # Partner Center 自己会把每条功能渲染成列表项，再挂一个横杠是两重符号。
            "features": [re.sub(r"^-\s+", "", f) for f in features],
        }

    return listing


def split_feature(text):
    """一条功能拆成几条，每条都在 200 字符以内。

    只在清单条上会用到（"Sixteen charts: turnover, volume, …"）。拆的是**名字**，
    前缀留着，标注用 `(1/2)` —— 数字与斜杠各语言通用，不必为它写 14 份译文。
    """
    if len(text) <= LIMIT_FEATURE:
        return [text]

    head = re.match(r"^(.*?[:：])\s*(.*)$", text, re.S)

    if head is None:
        return [text]

    prefix, rest = head.group(1), head.group(2)
    separator = "、" if "、" in rest else ", "
    names = [part.strip() for part in rest.split(separator) if part.strip()]

    if len(names) < 2:
        return [text]

    # 均分，不是贪心填满第一条：贪心会装出「14 个名字 / 2 个名字」这种头重脚轻的
    # 两条。从两条起试到每组都装得下为止。
    budget = LIMIT_FEATURE - SPLIT_MARGIN - len(prefix) - 1
    groups = [names]

    for count in range(2, len(names) + 1):
        size = -(-len(names) // count)
        cut = [names[i:i + size] for i in range(0, len(names), size)]

        if all(len(separator.join(g)) <= budget for g in cut):
            groups = cut
            break

    if len(groups) == 1:
        return [text]

    total = len(groups)

    return [
        "%s (%d/%d) %s" % (prefix, index + 1, total, separator.join(group))
        for index, group in enumerate(groups)
    ]


def main():
    listing = read_markdown()

    raw = io.open(CSV_PATH, "rb").read()
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig").replace("\r\n", "\n"))))
    header = rows[0]
    columns = {name.lower(): index for index, name in enumerate(header)}

    missing = [code for code in listing if code not in columns]

    if missing:
        print("CSV 里没有这些语言列：%s" % ", ".join(missing))
        return 1

    changed = 0
    # 一份功能清单会被 20 个 Feature 行各拆一次，用集合去重，报告才只有一行。
    split_report = set()

    for row in rows[1:]:
        field = row[0]

        for code, text in listing.items():
            column = columns[code]

            if field == "Description":
                value = text["description"]
            elif field == "ReleaseNotes":
                value = text["release"]
            elif re.match(r"^Feature\d+$", field):
                index = int(field[len("Feature"):]) - 1
                flat = []

                for feature in text["features"]:
                    pieces = split_feature(feature)

                    if len(pieces) > 1:
                        split_report.add((code, len(feature), len(pieces)))

                    flat.extend(pieces)

                value = flat[index] if index < len(flat) else ""
            else:
                continue

            if row[column] != value:
                row[column] = value
                changed += 1

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerows(rows)

    if raw[:3] == b"\xef\xbb\xbf":
        payload = "\ufeff"
    else:
        payload = ""

    io.open(CSV_PATH, "w", encoding="utf-8", newline="").write(
        payload + buffer.getvalue())

    print("写了 %d 格 → %s" % (changed, os.path.basename(CSV_PATH)))

    if split_report:
        print("\n超过 200 字符、按名字拆开的功能条：")

        for code, length, pieces in sorted(split_report):
            print("  %-8s %3d 字符 → %d 条" % (code, length, pieces))

    print("\n各语言字数（上限 说明 10000 / 新增 1500 / 功能 200×20）：")
    bad = 0

    for code in sorted(listing):
        text = listing[code]
        flat = []

        for feature in text["features"]:
            flat.extend(split_feature(feature))

        longest = max(len(f) for f in flat) if flat else 0
        over = []

        if len(text["description"]) > LIMIT_DESCRIPTION:
            over.append("说明 %d" % len(text["description"]))

        if len(text["release"]) > LIMIT_RELEASE_NOTES:
            over.append("新增 %d" % len(text["release"]))

        if len(flat) > MOST_FEATURES:
            over.append("功能 %d 条" % len(flat))

        if longest > LIMIT_FEATURE:
            over.append("功能最长 %d" % longest)

        bad += len(over)

        print("  %-8s 说明 %5d · 新增 %5d · 功能 %2d 条（最长 %3d）%s" % (
            code, len(text["description"]), len(text["release"]),
            len(flat), longest, ("  × " + "，".join(over)) if over else ""))

    print("\n%s" % ("全部在上限内" if bad == 0 else "%d 项超限" % bad))

    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
