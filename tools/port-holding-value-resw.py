# -*- coding: utf-8 -*-
r"""把持仓收益页那行「市值 ¥…」改成「持仓市值 ¥…」，14 种语言一起改。

2026-10-23。那条线说的是**手里这些股此刻值多少钱**，不是账户总资产 —— 只写「市值」，
读者很容易读成「我以前写的是价值」。改的只是 `PortfolioPnlValueLine` 这一个键，不新增、
不删除：同一个画面里收尾卡片用的 `PortfolioPnlStatValue` 早就是「持仓市值」，两处说法
本该一致。

幂等：已经是目标值的文件跳过。resw 是 **LF 带 BOM**，照原样写回。
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

KEY = "PortfolioPnlValueLine"

# 占位符 `{0}` 一个不能少：少了它，`Strings.Format` 会把金额丢掉，而画面上只是少了个数，
# 不会报错。
LINE = {
    "zh-Hans": "持仓市值 {0}",
    "zh-Hant": "持倉市值 {0}",
    "en-US": "position value {0}",
    "ja": "保有評価額 {0}",
    "ko": "보유 평가액 {0}",
    "de": "Positionswert {0}",
    "fr": "valeur des positions {0}",
    "it": "valore posizioni {0}",
    "es": "valor de la posición {0}",
    "pt-BR": "valor da posição {0}",
    "pl": "wartość pozycji {0}",
    "cs": "hodnota pozic {0}",
    "ru": "стоимость позиций {0}",
    "tr": "pozisyon değeri {0}",
}


def main():
    for tag in lt.LANGS:
        path = lt.STRINGS / tag / "Resources.resw"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        pattern = re.compile(r'(<data name="%s"><value>)(.*?)(</value></data>)' % KEY)
        found = pattern.search(body)

        assert found, f"{tag}: 没有 {KEY}"

        if found.group(2) == LINE[tag]:
            print(f"{tag:9} already there")
            continue

        body = pattern.sub(lambda m: m.group(1) + LINE[tag] + m.group(3), body, count=1)

        if crlf:
            body = body.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + body.encode("utf-8"))

        print(f"{tag:9} {found.group(2)}  →  {LINE[tag]}")


if __name__ == "__main__":
    main()
