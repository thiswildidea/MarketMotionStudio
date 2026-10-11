# -*- coding: utf-8 -*-
r"""把加密 K 线**分钟档**需要的五个键注入 14 份 Resources.resw。

**为什么是五个而不是复用现有的。**

- `CryptoMinuteDay.Header`：日期选择器自己的标题。不能借 `StudioRangeFrom`（那是「起始日期」，
  而这里没有区间，只有一天）。
- `CryptoMinuteReach`：分钟档能往回选多少天。这个数字**每档不同**（1 分钟 8 天、5/15 分钟 60 天），
  所以是带 `{0}` 的句型，由页面按当前周期填。
- `CryptoMinuteSourceNone`：备源（CoinGecko）没有分钟线时三档上的提示。照股票页
  `CandleMinuteMarketNone` 的做法：列出来、置灰、说为什么，而不是从列表里消失。
- `CryptoCandleMinuteFetched`：取数成功那句。复用 `CryptoCandleFetched` 会说出
  「1 分钟 K 线 1440 根（2026-10-11 至 2026-10-11）」—— 区间只有一天时「至」是个谎，
  它暗示有一段。
- `CryptoMinuteNone`：那一天取不到。不能复用 `CandleMinuteNone`，那句的后半句是
  「只有沪深两市有」，对币种不成立。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

`CryptoCandleMinuteFetched` 的占位符是 **{0}=根数、{1}=周期名、{2}=日期**，但**语序各语言自己定**
（中文是「{1} K 线 {0} 根（{2}）」）—— 这也是为什么这几个键不能共用一串英文格式。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-crypto-minute-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 1. 日期选择器的标题 ---------------------------------------------------------

DAY = [
    "Day",          # en-US
    "Tag",          # de
    "Día",          # es
    "Jour",         # fr
    "Giorno",       # it
    "Dzień",        # pl
    "Dia",          # pt-BR
    "Den",          # cs
    "Gün",          # tr
    "День",         # ru
    "日付",          # ja
    "날짜",          # ko
    "日期",          # zh-Hant
    "日期",          # zh-Hans
]

# ---- 2. 能往回选多少天 ------------------------------------------------------------

REACH = [
    "Only the last {0} days are available.",              # en-US
    "Nur die letzten {0} Tage sind verfügbar.",           # de
    "Solo están disponibles los últimos {0} días.",       # es
    "Seuls les {0} derniers jours sont disponibles.",     # fr
    "Sono disponibili solo gli ultimi {0} giorni.",       # it
    "Dostępne są tylko ostatnie {0} dni.",                # pl
    "Apenas os últimos {0} dias estão disponíveis.",      # pt-BR
    "K dispozici jsou pouze poslední {0} dny.",           # cs
    "Yalnızca son {0} gün kullanılabilir.",               # tr
    "Доступны только последние {0} дней.",                # ru
    "選択できるのは直近 {0} 日間だけです。",                  # ja
    "지난 {0}일만 선택할 수 있습니다.",                       # ko
    "只能選最近 {0} 天。",                                  # zh-Hant
    "只能选最近 {0} 天。",                                  # zh-Hans
]

# ---- 3. 备源没有分钟线时的提示 -----------------------------------------------------

SOURCE_NONE = [
    "The source in force carries no intraday series.",    # en-US
    "Die Quelle liefert keine Intraday-Serie.",           # de
    "La fuente activa no ofrece series intradía.",        # es
    "La source active n'a pas de série intrajournalière.",  # fr
    "La fonte attiva non ha serie intraday.",             # it
    "Aktywne źródło nie ma serii intraday.",              # pl
    "A fonte ativa não tem série intradiária.",           # pt-BR
    "Aktivní zdroj nemá intradenní řadu.",                # cs
    "Etkin kaynakta gün içi seri yok.",                   # tr
    "У активного источника нет внутридневных данных.",     # ru
    "現在のデータ源には日中のデータがありません。",              # ja
    "현재 데이터 소스에는 일중 데이터가 없습니다.",              # ko
    "目前這個來源沒有分鐘線。",                                # zh-Hant
    "目前这个来源没有分钟线。",                                # zh-Hans
]

# ---- 4. 取数成功那句：{0}=根数 {1}=周期名 {2}=日期 ---------------------------------

FETCHED = [
    "{0} {1} candles on {2}",              # en-US
    "{0} {1}-Kerzen am {2}",               # de
    "{0} velas de {1} el {2}",             # es
    "{0} chandeliers {1} le {2}",          # fr
    "{0} candele {1} il {2}",              # it
    "{0} świec {1} dnia {2}",              # pl
    "{0} candles de {1} em {2}",           # pt-BR
    "{0} svíček {1} dne {2}",              # cs
    "{2} tarihinde {0} adet {1} mum",      # tr
    "{0} свечей {1} за {2}",               # ru
    "{2} の {1} ローソク足 {0} 本",           # ja
    "{2} {1} 캔들 {0}개",                   # ko
    "{1} K 線 {0} 根（{2}）",                # zh-Hant
    "{1} K 线 {0} 根（{2}）",                # zh-Hans
]

# ---- 5. 那一天取不到 -------------------------------------------------------------

NONE = [
    "No candles came back for that day.",               # en-US
    "Für diesen Tag kamen keine Kerzen zurück.",        # de
    "No se recibieron velas para ese día.",             # es
    "Aucun chandelier n'est revenu pour ce jour.",      # fr
    "Nessuna candela è arrivata per quel giorno.",      # it
    "Dla tego dnia nie wróciły żadne świece.",          # pl
    "Nenhum candle retornou para esse dia.",            # pt-BR
    "Pro tento den se nevrátila žádná svíčka.",         # cs
    "O gün için mum verisi gelmedi.",                   # tr
    "За этот день свечи не вернулись.",                  # ru
    "その日のローソク足は返りませんでした。",                  # ja
    "그날의 캔들이 돌아오지 않았습니다.",                     # ko
    "這一天沒有取到分鐘線。",                                # zh-Hant
    "这一天没有取到分钟线。",                                # zh-Hans
]

ROWS = [
    ("CryptoMinuteDay.Header", DAY),
    ("CryptoMinuteReach", REACH),
    ("CryptoMinuteSourceNone", SOURCE_NONE),
    ("CryptoCandleMinuteFetched", FETCHED),
    ("CryptoMinuteNone", NONE),
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
