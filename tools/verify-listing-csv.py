#!/usr/bin/env python
"""只读校验：Partner Center 的 listing CSV 与 docs/store-listing.md 是否一致。

这个 CSV 是要**上传**的，而它有两个容易静默出错的地方，都是这个脚本要盯的：

1. **列错位** —— 中文写进繁中列、日文写进韩文列，肉眼扫一眼「都是方块字」看不出来。
   判据是各语言列的第一句：简中是「把行情指标变成」，繁中是「把行情指標變成」。
2. **旧文案残留** —— 曾经 zh-hans 的功能条还写着「八种图表」，而 md 里早就是十六种了：
   因为 md 的中文标题用的是**全角括号**，而抽取语言代码的正则只认半角，整节被跳过。
   所以这里是**逐字比对**每一格，不是「看着像就行」。

不动 Title 与 `OverrideLogosForWin10`：那是资产不是字，改了就找不回来。截图列原本也
在「不动」之列（值是上一次上传后回来的 `listingassets` URL），现在它由
`tools/port-listing-csv-screens.py` 改写成相对路径，所以这里改判另一件事：**每一格指向
的 PNG 是不是真躺在磁盘上**——相对路径写错一个字母，上传时才知道，而那时已经晚了。
"""

import csv
import importlib.util
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(
    REPO, "docs", "listingData-9NGDNH0CCW7L-1152921505702020674.csv")
PORT = os.path.join(REPO, "tools", "port-listing-csv.py")

LIMIT_DESCRIPTION = 10000
LIMIT_RELEASE_NOTES = 1500
LIMIT_FEATURE = 200
MOST_FEATURES = 20

# 各语言列的第一句：判列有没有错位的锚。
FIRST_WORDS = {
    "zh-hans": "把行情指标变成",
    "zh-hant": "把行情指標變成",
    "ja": "相場指標を",
    "ko": "시장 지표를",
    "en-us": "Turn stock-market",
}

PASSED = 0
FAILED = 0


def check(label, ok, detail=""):
    global PASSED, FAILED

    if ok:
        PASSED += 1
        print("  √ %s%s" % (label, (" — " + detail) if detail else ""))
    else:
        FAILED += 1
        print("  × %s%s" % (label, (" — " + detail) if detail else ""))


def load_port():
    spec = importlib.util.spec_from_file_location("port_listing_csv", PORT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def main():
    port = load_port()
    listing = port.read_markdown()

    raw = io.open(CSV_PATH, "rb").read()
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig").replace("\r\n", "\n"))))
    header = rows[0]
    columns = {name.lower(): index for index, name in enumerate(header)}

    print("文件属性")
    check("保住了 BOM（Partner Center 导出的就是带 BOM 的）", raw[:3] == b"\xef\xbb\xbf")
    check("行尾是 CRLF", raw.count(b"\r\n") == len(rows))
    check("表头 18 列、共 454 行", len(header) == 18 and len(rows) == 454,
          "%d 列 · %d 行" % (len(header), len(rows)))
    check("14 个语言列都在", len([n for n in header[4:] if n.strip()]) == 14)

    print("\n列没有错位（各语言列的第一句）")

    for code, word in FIRST_WORDS.items():
        row = [r for r in rows[1:] if r[0] == "Description"][0]
        check("%s 列是%s" % (code, code.split("-")[0]),
              row[columns[code]].startswith(word), row[columns[code]][:24])

    print("\n三段文案与 md 逐字一致")

    for code in sorted(listing):
        text = listing[code]
        column = columns[code]
        description = [r for r in rows[1:] if r[0] == "Description"][0][column]
        release = [r for r in rows[1:] if r[0] == "ReleaseNotes"][0][column]
        written = []

        for index in range(MOST_FEATURES):
            row = [r for r in rows[1:] if r[0] == "Feature%d" % (index + 1)]

            if row and row[0][column]:
                written.append(row[0][column])

        expected = []

        for feature in text["features"]:
            expected.extend(port.split_feature(feature))

        ok = (description == text["description"]
              and release == text["release"]
              and written == expected)

        check("%s 说明 / 新增 / 功能 %d 条" % (code, len(expected)), ok,
              "" if ok else "说明%s 新增%s 功能%s" % (
                  "同" if description == text["description"] else "异",
                  "同" if release == text["release"] else "异",
                  "同" if written == expected else "异"))

    print("\nPartner Center 的上限")

    for code in sorted(listing):
        column = columns[code]
        text = listing[code]
        written = []

        for index in range(MOST_FEATURES):
            row = [r for r in rows[1:] if r[0] == "Feature%d" % (index + 1)]

            if row and row[0][column]:
                written.append(row[0][column])

        longest = max(len(f) for f in written) if written else 0

        check("%s 说明 %d ≤ %d · 新增 %d ≤ %d · 功能 %d 条 ≤ %d，最长 %d ≤ %d" % (
            code, len(text["description"]), LIMIT_DESCRIPTION,
            len(text["release"]), LIMIT_RELEASE_NOTES,
            len(written), MOST_FEATURES, longest, LIMIT_FEATURE),
            len(text["description"]) <= LIMIT_DESCRIPTION
            and len(text["release"]) <= LIMIT_RELEASE_NOTES
            and len(written) <= MOST_FEATURES
            and longest <= LIMIT_FEATURE)

    print("\n资产没有被字动过")

    title = [r for r in rows[1:] if r[0] == "Title"][0]
    check("14 列的 Title 都还是 MarketMotionStudio",
          all(title[columns[code]] == "MarketMotionStudio" for code in listing))

    # 截图列现在是相对路径（相对 CSV 所在的 docs\），每一格都得能在磁盘上找到。
    shot_rows = [r for r in rows[1:] if re.match(r"^DesktopScreenshot\d+$", r[0])]
    counts = {}
    on_disk = True

    for code in listing:
        column = columns[code]
        paths = [r[column] for r in shot_rows if r[column]]
        counts[code] = len(paths)
        on_disk = on_disk and bool(paths) and all(
            os.path.exists(os.path.join(REPO, "docs", *p.split("/"))) for p in paths)

    check("14 列的截图都指向磁盘上真实存在的 PNG", on_disk,
          " ".join("%s %d" % (c, counts[c]) for c in sorted(counts)))

    check("zh-hans 八张、其余各七张（市场成交额页只在 A股 市场有）",
          counts.get("zh-hans") == 8
          and all(counts.get(c) == 7 for c in listing if c != "zh-hans"),
          "zh-hans %d" % counts.get("zh-hans", 0))

    check("没有残留的旧 listingassets URL",
          not any(r[columns[code]].startswith("http")
                  for r in shot_rows for code in listing),
          "%d 格" % sum(1 for r in shot_rows for code in listing
                        if r[columns[code]].startswith("http")))

    logo = [r for r in rows[1:] if r[0] == "OverrideLogosForWin10"][0]
    check("OverrideLogosForWin10 还是 False",
          all(logo[columns[code]] == "False" for code in listing))

    print("\n%d/%d 通过" % (PASSED, PASSED + FAILED))

    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
