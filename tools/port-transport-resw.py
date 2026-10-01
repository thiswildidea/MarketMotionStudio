# -*- coding: utf-8 -*-
"""把播放进度条的位置文案从「秒数」改成「时钟」。

播放条上的位置过去写成 "0.0 / 75 秒"：一个数加一个出现在句尾的单位。现在两侧都是
m:ss（"0:00 / 1:15"），单位就没有东西可修饰了——钟点本身就是单位，写第二遍是重复。
于是 14 份资源里 StudioScrubPosition 的值统一成 `{0} / {1}`，两个参数各是一段时钟。

值在 14 种语言里完全相同，这是对的：这不是翻译，是一段没有词的格式串。留着这个键
（而不是把格式写死在代码里）是因为「位置 / 总长」的排布仍可能有语言想调整。

脚本只动这一个键，别的行一个字节都不碰。resw 是 UTF-8 **BOM** + LF，所以走
read_bytes/decode('utf-8-sig')/write_bytes，不用文本模式——文本模式会把换行归一化，
git 上就显示成整个文件被重写。

用法：
    python tools/port-transport-resw.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1] / "src" / "MarketMotionStudio" / "Strings"
KEY = "StudioScrubPosition"
WANTED = 14

# 只匹配这一个 data 元素的值，且允许值本身跨行（xml:space="preserve" 那种写法）。
ELEMENT = re.compile(r'(<data name="' + KEY + r'">)\s*<value>.*?</value>', re.S)
REPLACEMENT = r"\g<1><value>{0} / {1}</value>"


def main() -> int:
    files = sorted(ROOT.glob("*/Resources.resw"))

    if len(files) != WANTED:
        print(f"!! 找到 {len(files)} 份资源，应当是 {WANTED} 份")
        return 1

    counts = {}
    changed = 0

    for path in files:
        raw = path.read_bytes()
        had_bom = raw[:3] == b"\xef\xbb\xbf"
        text = raw.decode("utf-8-sig")

        counts[path.parent.name] = text.count(f'name="{KEY}"')

        new_text, hits = ELEMENT.subn(REPLACEMENT, text)

        if hits != 1:
            print(f"!! {path.parent.name}: 命中 {hits} 处 {KEY}，预期 1 处")
            return 1

        if new_text == text:
            print(f"{path.parent.name:<8} 已是时钟格式")
            continue

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + new_text.encode("utf-8"))
        changed += 1
        print(f"{path.parent.name:<8} 已改写")

    # 「14 份键与顺序必须相同」——这里只检查数量，顺序由脚本不重排来保证。
    if len(set(counts.values())) != 1:
        print(f"!! 各语言键数不一致：{counts}")
        return 1

    print(f"\n{changed} 份改写，{WANTED - changed} 份原本就对；每份键数 {set(counts.values()).pop()}")

    if KEY not in "\n".join(
        p.read_bytes().decode("utf-8-sig") for p in files
    ):
        print(f"!! {KEY} 在改写后消失")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
