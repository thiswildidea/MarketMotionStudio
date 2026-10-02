# -*- coding: utf-8 -*-
r"""把「极端交易日」标的那个下拉的 resw 键从 14 份 Resources.resw 里删掉。

这一页的标的区改成了 K线 / 涨跌日历那一套：搜索框 + 一键预设 + 共享收藏。原来那个
下拉没有控件再读它了（`ExtremeDaysInstrument.Header` = 「标的」/ "Instrument"），
而一个键留着、控件却没了，就是下一轮读代码的人要花时间去排除的东西。

**删而不是换后缀**：那几个按钮不需要表头 —— 八个指数名摆在搜索框下面，是什么一眼
看得出。把 `.Header` 改成别的后缀只是让一个没人读的字符串换一个没人读的后缀。

**其余键的顺序原样保留**：14 份仍然逐字节同构，`verify-resw-uids.py` 比的是键集合，
删完从 733 变 732。

**幂等**：已经删过就报 0 条，不报错 —— 发版前重跑一次是常规动作。

用法：python tools\port-extremedays-presets.py [--apply]
"""
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 基名（不带后缀）：一个控件名下一个后缀都不该留。
KEY = "ExtremeDaysInstrument"

PATTERN = re.compile(rf'  <data name="{KEY}(\.\w+)?"[^>]*>.*?</data>\n', re.S)


def main():
    apply = "--apply" in sys.argv

    removed = 0

    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        hits = PATTERN.findall(text)

        if len(hits) > 1:
            print(f"{tag}: {len(hits)} entries under {KEY} — expected at most 1")

        if hits and apply:
            # 末尾换行与 BOM 照旧：resw 带 BOM，store-listing.md 恰恰不能带。
            path.write_bytes(PATTERN.sub("", text).encode("utf-8-sig"))

        removed += len(hits)

        state = "removed" if hits and apply else "would remove" if hits else "already gone"

        print(f"{tag}: {state} {len(hits)}")

    print(f"\n{removed} removal(s) over {len(LANGS)} languages")

    if not apply:
        print("dry run — pass --apply to write")

    return 0


if __name__ == "__main__":
    sys.exit(main())
