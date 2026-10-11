# -*- coding: utf-8 -*-
r"""把「加密货币」这个**市场名**注入 14 份 Resources.resw。

**为什么市场这一档也要单独一个键。** 加密货币原来只是导航里并列的三项，市场下拉里没有它。
现在它是一个可选的市场（`MarketId.Crypto`），于是需要和「A股 / 港股 / 美股」并列的一个名字 ——
那三个各有自己的键（`MarketAShare` / `MarketHongKong` / `MarketUnitedStates`），这一个不能借用
任何页面标题的措辞：下拉里那一格是**市场的名字**，不是某一页的名字。

**措辞跟着既有的加密键走**，不另起一套：日文用「暗号資産」（`NavCryptoCandle` 已是这个字），
韩文用「암호화폐」（与 `CryptoDisclaimer` 一致），俄文用「Криптовалюты」，中文两份用
「加密貨幣 / 加密货币」。德语取全称 `Kryptowährungen` 而不是 `Krypto` —— 下拉里另外三项
（Aktien / Hongkong / US）也都是全称，缩写在这里会显得像另一个类别。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-crypto-market-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 市场名 ---------------------------------------------------------------------
#
# 「支持加密货币的地区才会出现这一项」这条规则本身**不在这里说**：看不到这一格的人正是
# 需要知道为什么的人，而这句说明只有看得到的人才会读。规则写在帮助手册的「选择市场」一章。

MARKET_CRYPTO = [
    "Cryptocurrency",     # en-US
    "Kryptowährungen",    # de
    "Criptomonedas",      # es
    "Cryptomonnaies",     # fr
    "Criptovalute",       # it
    "Kryptowaluty",       # pl
    "Criptomoedas",       # pt-BR
    "Kryptoměny",         # cs
    "Kripto",             # tr
    "Криптовалюты",       # ru
    "暗号資産",            # ja
    "암호화폐",            # ko
    "加密貨幣",            # zh-Hant
    "加密货币",            # zh-Hans
]

ROWS = [
    ("MarketCrypto", MARKET_CRYPTO),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project
    file rather than the string that caused it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        lines = []

        for key, values in ROWS:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in ROWS:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at = text.rfind("</root>")
        assert at > 0, f"{tag}: no </root>"

        text = text[:at] + "".join(lines) + text[at:]

        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
