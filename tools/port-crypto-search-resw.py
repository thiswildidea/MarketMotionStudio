# -*- coding: utf-8 -*-
r"""把加密三页那口**检索框**的两句文案注入 14 份 Resources.resw。

两个键，都不是可有可无的：

- `CryptoSearch.PlaceholderText` —— 框里那句灰字。没有它，框是一个空白的矩形，
  除了一根光标什么也不说，而三页的框长得一样、和下面的周期框也长得一样。
- `CryptoSearchNone.Text` —— 敲进去一个谁都不匹配的词时说的话。**没有它，界面是一片
  空白**：按钮全被收起来了，「已选 3 个，最多 6 个」还挂在那儿，读起来像这一块坏了
  而不是像「这个词没找到」。空结果是一个答案，答案要说出来。

**匹配用的是当前语言下的币种名**（`CryptoAsset.Display` → `INST*` 键），所以那句灰字
也得跟着语言走：中文界面的框写着「检索币种」，里面敲「比特」；英文界面写着「Search
coins」，里面敲 "bitcoin"。两边对不上就等于没有这口框。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-crypto-search-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 框里的灰字 -------------------------------------------------------------------

SEARCH_HINT = [
    "Search coins",             # en-US
    "Coins suchen",             # de
    "Buscar monedas",           # es
    "Rechercher une crypto",    # fr
    "Cerca monete",             # it
    "Szukaj kryptowalut",       # pl
    "Pesquisar moedas",         # pt-BR
    "Hledat mince",             # cs
    "Kripto ara",               # tr
    "Поиск криптовалют",        # ru
    "コインを検索",              # ja
    "코인 검색",                 # ko
    "搜尋幣種",                  # zh-Hant
    "检索币种",                  # zh-Hans
]

# ---- 谁都不匹配时说的一句 ---------------------------------------------------------
#
# 「这个词没找到」而不是「没有数据」：币是有的，是这一行被这个词收起来了。

SEARCH_NONE = [
    "No coin matches that.",                    # en-US
    "Keine Coin passt dazu.",                   # de
    "Ninguna moneda coincide.",                 # es
    "Aucune crypto ne correspond.",             # fr
    "Nessuna moneta corrisponde.",              # it
    "Żadna kryptowaluta nie pasuje.",           # pl
    "Nenhuma moeda corresponde.",               # pt-BR
    "Žádná mince neodpovídá.",                  # cs
    "Eşleşen kripto yok.",                      # tr
    "Ни одна криптовалюта не подходит.",        # ru
    "一致するコインがありません。",               # ja
    "일치하는 코인이 없습니다.",                  # ko
    "沒有符合的幣種。",                          # zh-Hant
    "没有匹配的币种。",                          # zh-Hans
]

ROWS = [
    ("CryptoSearch.PlaceholderText", SEARCH_HINT),
    ("CryptoSearchNone.Text", SEARCH_NONE),
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
