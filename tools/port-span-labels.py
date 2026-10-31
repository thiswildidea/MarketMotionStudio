#!/usr/bin/env python3
"""Adds the span-worded labels to all fourteen resource files.

When the picture is a run of days rather than one session, three sentences have to say so:

  * the returns page's read-out counts **trading days**, not minutes;
  * the double-screen page's counts them too;
  * the book's own heading is no longer "the day's profit" but the span's.

The day-worded keys stay as they are and stay in use: 当日 still draws minutes and still
reads "分钟点", which is what it is.

Idempotent: a file already carrying `BoardPnlLabelSpan` is left alone. resw keeps its BOM
and LF endings.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

ZH = {
    "PortfolioSpanTrimmed": "（起点已对齐初始持仓基准日 {0}）",
    "PortfolioSpanShallow": "（分时数据只有最近 5 个交易日，起点 {0}）",
    "PortfolioPnlFetchedDays": "{0} · {1} 个交易日 · 收益 {2}",
    "BoardFetchedDays": "取到 {0} / {1} 个指数 · {2} 个交易日 · 组合 {3}",
    "BoardPnlLabelSpan": "持仓区间盈亏",
}

T = {
    "en-US": {
        "PortfolioSpanShallow": "(minute data only reaches back five sessions; from {0})",
        "PortfolioSpanTrimmed": "(opened at the snapshot's own day, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} trading days · {2} made",
        "BoardFetchedDays": "{0} of {1} indexes · {2} trading days · book {3}",
        "BoardPnlLabelSpan": "The book's span",
    },
    "zh-Hant": {
        "PortfolioSpanShallow": "（分時資料只有最近 5 個交易日，起點 {0}）",
        "PortfolioSpanTrimmed": "（起點已對齊初始持倉基準日 {0}）",
        "PortfolioPnlFetchedDays": "{0} · {1} 個交易日 · 收益 {2}",
        "BoardFetchedDays": "取到 {0} / {1} 個指數 · {2} 個交易日 · 組合 {3}",
        "BoardPnlLabelSpan": "持倉區間盈虧",
    },
    "cs": {
        "PortfolioSpanShallow": "(minutová data sahají jen pět seancí zpět; od {0})",
        "PortfolioSpanTrimmed": "(počátek zarovnán na den počáteční pozice, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} obchodních dnů · výnos {2}",
        "BoardFetchedDays": "{0} z {1} indexů · {2} obchodních dnů · portfolio {3}",
        "BoardPnlLabelSpan": "Výsledek portfolia za období",
    },
    "de": {
        "PortfolioSpanShallow": "(Minutendaten reichen nur fünf Sitzungen zurück; ab {0})",
        "PortfolioSpanTrimmed": "(Beginn am Tag der Anfangsposition, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} Handelstage · Ertrag {2}",
        "BoardFetchedDays": "{0} von {1} Indizes · {2} Handelstage · Buch {3}",
        "BoardPnlLabelSpan": "Buch im Zeitraum",
    },
    "es": {
        "PortfolioSpanShallow": "(los datos por minuto solo llegan cinco sesiones atrás; desde {0})",
        "PortfolioSpanTrimmed": "(inicio alineado al día de la posición inicial, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} sesiones · resultado {2}",
        "BoardFetchedDays": "{0} de {1} índices · {2} sesiones · cartera {3}",
        "BoardPnlLabelSpan": "Cartera en el periodo",
    },
    "fr": {
        "PortfolioSpanShallow": "(les données minute ne remontent que cinq séances ; à partir du {0})",
        "PortfolioSpanTrimmed": "(début aligné sur le jour de la position initiale, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} séances · résultat {2}",
        "BoardFetchedDays": "{0} sur {1} indices · {2} séances · portefeuille {3}",
        "BoardPnlLabelSpan": "Portefeuille sur la période",
    },
    "it": {
        "PortfolioSpanShallow": "(i dati al minuto arrivano solo a cinque sedute; dal {0})",
        "PortfolioSpanTrimmed": "(inizio allineato al giorno della posizione iniziale, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} sedute · risultato {2}",
        "BoardFetchedDays": "{0} su {1} indici · {2} sedute · portafoglio {3}",
        "BoardPnlLabelSpan": "Portafoglio nel periodo",
    },
    "ja": {
        "PortfolioSpanShallow": "（分足データは直近 5 営業日分のみ。{0} から）",
        "PortfolioSpanTrimmed": "（起点を初期保有の基準日 {0} に合わせました）",
        "PortfolioPnlFetchedDays": "{0} · {1} 営業日 · 損益 {2}",
        "BoardFetchedDays": "{0} / {1} 指数 · {2} 営業日 · ポートフォリオ {3}",
        "BoardPnlLabelSpan": "保有期間の損益",
    },
    "ko": {
        "PortfolioSpanShallow": "(분봉 데이터는 최근 5거래일까지만 제공됩니다. {0}부터)",
        "PortfolioSpanTrimmed": "(시작점을 초기 보유 기준일 {0}에 맞춤)",
        "PortfolioPnlFetchedDays": "{0} · {1} 거래일 · 수익 {2}",
        "BoardFetchedDays": "{0} / {1} 지수 · {2} 거래일 · 포트폴리오 {3}",
        "BoardPnlLabelSpan": "보유 기간 손익",
    },
    "pl": {
        "PortfolioSpanShallow": "(dane minutowe sięgają tylko pięć sesji wstecz; od {0})",
        "PortfolioSpanTrimmed": "(początek wyrównany do dnia pozycji początkowej, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} sesji · wynik {2}",
        "BoardFetchedDays": "{0} z {1} indeksów · {2} sesji · portfel {3}",
        "BoardPnlLabelSpan": "Wynik portfela w okresie",
    },
    "pt-BR": {
        "PortfolioSpanShallow": "(os dados por minuto só chegam a cinco pregões; desde {0})",
        "PortfolioSpanTrimmed": "(início alinhado ao dia da posição inicial, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} pregões · resultado {2}",
        "BoardFetchedDays": "{0} de {1} índices · {2} pregões · carteira {3}",
        "BoardPnlLabelSpan": "Carteira no período",
    },
    "ru": {
        "PortfolioSpanShallow": "(минутные данные есть только за пять последних сессий; с {0})",
        "PortfolioSpanTrimmed": "(начало выровнено по дню начальной позиции, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} торговых дней · результат {2}",
        "BoardFetchedDays": "{0} из {1} индексов · {2} торговых дней · портфель {3}",
        "BoardPnlLabelSpan": "Портфель за период",
    },
    "tr": {
        "PortfolioSpanShallow": "(dakika verisi yalnızca son beş seanı kapsar; {0} itibarıyla)",
        "PortfolioSpanTrimmed": "(başlangıç ilk pozisyon gününe hizalandı, {0})",
        "PortfolioPnlFetchedDays": "{0} · {1} işlem günü · getiri {2}",
        "BoardFetchedDays": "{0} / {1} endeks · {2} işlem günü · portföy {3}",
        "BoardPnlLabelSpan": "Dönem portföyü",
    },
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    changed = 0

    for lang, table in [("zh-Hans", ZH), *T.items()]:
        resw = STRINGS / lang / "Resources.resw"

        if not resw.exists():
            print(f"{lang}: MISSING FILE")
            continue

        raw = resw.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")

        missing = {k: v for k, v in table.items() if f'name="{k}"' not in text}

        if not missing:
            print(f"{lang}: already present")
            continue

        block = "".join(f'  <data name="{k}"><value>{esc(v)}</value></data>\n' for k, v in missing.items())

        trimmed = text.rstrip()
        assert trimmed.endswith("</root>"), lang
        text = trimmed[: -len("</root>")].rstrip("\n") + "\n" + block + "</root>\n"

        resw.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + text.encode("utf-8"))
        changed += 1
        print(f"{lang}: added {len(missing)} keys")

    print(f"changed {changed} files")


if __name__ == "__main__":
    main()
