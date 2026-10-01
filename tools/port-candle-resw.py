"""Adds the candle page's strings to all fourteen resource files.

Idempotent: a key already present has its value replaced in place, so running this
twice changes nothing the second time. Written with `read_bytes` / `write_bytes`
because these files are UTF-8 **with a BOM** and LF endings — `write_text` would
strip the BOM and normalise the endings, and git would then show all fourteen files
as rewritten.

Run:  <venv python> tools/port-candle-resw.py
"""

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

TAGS = [
    "en-US", "de", "es", "fr", "it", "pl", "pt-BR",
    "cs", "tr", "ru", "ja", "ko", "zh-Hans", "zh-Hant",
]

# Key order is shared by every file; the script inserts them in this order.
KEYS = [
    "NavCandle.Content",
    "CandlePageTitle.Text",
    "CandlePageSubtitle.Text",
    "CandleSubtitleLine",
    "CandleDefaultTitle",
    "CandlePeriodLabel.Header",
    "CandlePeriodDaily",
    "CandlePeriodWeekly",
    "CandlePeriodMonthly",
    "CandleStyleLabel.Header",
    "CandleStyleCandles",
    "CandleStyleBars",
    "CandleStyleLine",
    "CandleStyleArea",
    "CandleMotionLabel.Header",
    "CandleMotionGrow",
    "CandleMotionScroll",
    "CandleWindowLabel.Header",
    "CandleShowAverages.Content",
    "CandleOpen",
    "CandleClose",
    "CandleMoveLabel",
    "CandleCardRange",
    "CandleCardAmplitude",
    "CandleLegendClose",
    "CandleFetched",
]

VALUES = {
    "en-US": {
        "NavCandle.Content": "Candles",
        "CandlePageTitle.Text": "Candles",
        "CandlePageSubtitle.Text":
            "One instrument's candles: daily, weekly or monthly, drawn four ways, "
            "with its averages and its volume underneath.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Period",
        "CandlePeriodDaily": "Daily",
        "CandlePeriodWeekly": "Weekly",
        "CandlePeriodMonthly": "Monthly",
        "CandleStyleLabel.Header": "Style",
        "CandleStyleCandles": "Candles",
        "CandleStyleBars": "OHLC bars",
        "CandleStyleLine": "Closing line",
        "CandleStyleArea": "Closing area",
        "CandleMotionLabel.Header": "Motion",
        "CandleMotionGrow": "Grow across the range",
        "CandleMotionScroll": "Scroll a window",
        "CandleWindowLabel.Header": "Window (candles)",
        "CandleShowAverages.Content": "Moving averages MA5/10/20",
        "CandleOpen": "Open",
        "CandleClose": "Close",
        "CandleMoveLabel": "Change",
        "CandleCardRange": "Range return",
        "CandleCardAmplitude": "Amplitude",
        "CandleLegendClose": "Close",
        "CandleFetched": "{0} {1} candles ({2} to {3})",
    },
    "de": {
        "NavCandle.Content": "Kerzen",
        "CandlePageTitle.Text": "Kerzenchart",
        "CandlePageSubtitle.Text":
            "Die Kerzen eines Instruments: täglich, wöchentlich oder monatlich, auf vier "
            "Arten gezeichnet, mit Durchschnitten und Volumen darunter.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Intervall",
        "CandlePeriodDaily": "Täglich",
        "CandlePeriodWeekly": "Wöchentlich",
        "CandlePeriodMonthly": "Monatlich",
        "CandleStyleLabel.Header": "Darstellung",
        "CandleStyleCandles": "Kerzen",
        "CandleStyleBars": "OHLC-Balken",
        "CandleStyleLine": "Schlusskurslinie",
        "CandleStyleArea": "Schlusskursfläche",
        "CandleMotionLabel.Header": "Ablauf",
        "CandleMotionGrow": "Über den ganzen Zeitraum",
        "CandleMotionScroll": "Fenster weiterbewegen",
        "CandleWindowLabel.Header": "Fenster (Kerzen)",
        "CandleShowAverages.Content": "Gleitende Durchschnitte MA5/10/20",
        "CandleOpen": "Eröffnung",
        "CandleClose": "Schluss",
        "CandleMoveLabel": "Veränderung",
        "CandleCardRange": "Rendite im Zeitraum",
        "CandleCardAmplitude": "Spanne",
        "CandleLegendClose": "Schlusskurs",
        "CandleFetched": "{0} {1} ({2} bis {3})",
    },
    "es": {
        "NavCandle.Content": "Velas",
        "CandlePageTitle.Text": "Velas",
        "CandlePageSubtitle.Text":
            "Las velas de un instrumento: diarias, semanales o mensuales, dibujadas de "
            "cuatro formas, con sus medias y su volumen debajo.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Intervalo",
        "CandlePeriodDaily": "Diarias",
        "CandlePeriodWeekly": "Semanales",
        "CandlePeriodMonthly": "Mensuales",
        "CandleStyleLabel.Header": "Tipo de dibujo",
        "CandleStyleCandles": "Velas",
        "CandleStyleBars": "Barras OHLC",
        "CandleStyleLine": "Línea de cierre",
        "CandleStyleArea": "Área de cierre",
        "CandleMotionLabel.Header": "Animación",
        "CandleMotionGrow": "Crecer por todo el periodo",
        "CandleMotionScroll": "Desplazar una ventana",
        "CandleWindowLabel.Header": "Ventana (velas)",
        "CandleShowAverages.Content": "Medias móviles MA5/10/20",
        "CandleOpen": "Apertura",
        "CandleClose": "Cierre",
        "CandleMoveLabel": "Variación",
        "CandleCardRange": "Rentabilidad del periodo",
        "CandleCardAmplitude": "Amplitud",
        "CandleLegendClose": "Cierre",
        "CandleFetched": "{0} {1} ({2} a {3})",
    },
    "fr": {
        "NavCandle.Content": "Chandeliers",
        "CandlePageTitle.Text": "Chandeliers",
        "CandlePageSubtitle.Text":
            "Les chandeliers d'un instrument : quotidiens, hebdomadaires ou mensuels, "
            "dessinés de quatre façons, avec ses moyennes et son volume en dessous.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Granularité",
        "CandlePeriodDaily": "Quotidien",
        "CandlePeriodWeekly": "Hebdomadaire",
        "CandlePeriodMonthly": "Mensuel",
        "CandleStyleLabel.Header": "Type de tracé",
        "CandleStyleCandles": "Chandeliers",
        "CandleStyleBars": "Barres OHLC",
        "CandleStyleLine": "Ligne de clôture",
        "CandleStyleArea": "Aire de clôture",
        "CandleMotionLabel.Header": "Animation",
        "CandleMotionGrow": "Tracer tout l'intervalle",
        "CandleMotionScroll": "Fenêtre glissante",
        "CandleWindowLabel.Header": "Fenêtre (chandeliers)",
        "CandleShowAverages.Content": "Moyennes mobiles MA5/10/20",
        "CandleOpen": "Ouverture",
        "CandleClose": "Clôture",
        "CandleMoveLabel": "Variation",
        "CandleCardRange": "Rendement de la période",
        "CandleCardAmplitude": "Amplitude",
        "CandleLegendClose": "Clôture",
        "CandleFetched": "{0} {1} ({2} à {3})",
    },
    "it": {
        "NavCandle.Content": "Candele",
        "CandlePageTitle.Text": "Candele",
        "CandlePageSubtitle.Text":
            "Le candele di uno strumento: giornaliere, settimanali o mensili, disegnate in "
            "quattro modi, con le medie e il volume sotto.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Intervallo",
        "CandlePeriodDaily": "Giornaliere",
        "CandlePeriodWeekly": "Settimanali",
        "CandlePeriodMonthly": "Mensili",
        "CandleStyleLabel.Header": "Tipo di disegno",
        "CandleStyleCandles": "Candele",
        "CandleStyleBars": "Barre OHLC",
        "CandleStyleLine": "Linea di chiusura",
        "CandleStyleArea": "Area di chiusura",
        "CandleMotionLabel.Header": "Animazione",
        "CandleMotionGrow": "Tutto l'intervallo",
        "CandleMotionScroll": "Finestra scorrevole",
        "CandleWindowLabel.Header": "Finestra (candele)",
        "CandleShowAverages.Content": "Medie mobili MA5/10/20",
        "CandleOpen": "Apertura",
        "CandleClose": "Chiusura",
        "CandleMoveLabel": "Variazione",
        "CandleCardRange": "Rendimento del periodo",
        "CandleCardAmplitude": "Ampiezza",
        "CandleLegendClose": "Chiusura",
        "CandleFetched": "{0} {1} ({2} – {3})",
    },
    "pl": {
        "NavCandle.Content": "Świece",
        "CandlePageTitle.Text": "Wykres świecowy",
        "CandlePageSubtitle.Text":
            "Świece jednego instrumentu: dzienne, tygodniowe lub miesięczne, rysowane na "
            "cztery sposoby, ze średnimi i wolumenem poniżej.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Interwał",
        "CandlePeriodDaily": "Dzienne",
        "CandlePeriodWeekly": "Tygodniowe",
        "CandlePeriodMonthly": "Miesięczne",
        "CandleStyleLabel.Header": "Rodzaj wykresu",
        "CandleStyleCandles": "Świece",
        "CandleStyleBars": "Słupki OHLC",
        "CandleStyleLine": "Linia zamknięcia",
        "CandleStyleArea": "Obszar zamknięcia",
        "CandleMotionLabel.Header": "Animacja",
        "CandleMotionGrow": "Cały zakres naraz",
        "CandleMotionScroll": "Przesuwne okno",
        "CandleWindowLabel.Header": "Okno (świece)",
        "CandleShowAverages.Content": "Średnie kroczące MA5/10/20",
        "CandleOpen": "Otwarcie",
        "CandleClose": "Zamknięcie",
        "CandleMoveLabel": "Zmiana",
        "CandleCardRange": "Zwrot w okresie",
        "CandleCardAmplitude": "Amplituda",
        "CandleLegendClose": "Zamknięcie",
        "CandleFetched": "{0} {1} ({2} – {3})",
    },
    "pt-BR": {
        "NavCandle.Content": "Candlestick",
        "CandlePageTitle.Text": "Candlestick",
        "CandlePageSubtitle.Text":
            "Os candles de um instrumento: diários, semanais ou mensais, desenhados de "
            "quatro formas, com médias e volume abaixo.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Intervalo",
        "CandlePeriodDaily": "Diários",
        "CandlePeriodWeekly": "Semanais",
        "CandlePeriodMonthly": "Mensais",
        "CandleStyleLabel.Header": "Tipo de desenho",
        "CandleStyleCandles": "Candles",
        "CandleStyleBars": "Barras OHLC",
        "CandleStyleLine": "Linha de fechamento",
        "CandleStyleArea": "Área de fechamento",
        "CandleMotionLabel.Header": "Animação",
        "CandleMotionGrow": "Todo o período",
        "CandleMotionScroll": "Janela deslizante",
        "CandleWindowLabel.Header": "Janela (candles)",
        "CandleShowAverages.Content": "Médias móveis MA5/10/20",
        "CandleOpen": "Abertura",
        "CandleClose": "Fechamento",
        "CandleMoveLabel": "Variação",
        "CandleCardRange": "Retorno do período",
        "CandleCardAmplitude": "Amplitude",
        "CandleLegendClose": "Fechamento",
        "CandleFetched": "{0} {1} ({2} a {3})",
    },
    "cs": {
        "NavCandle.Content": "Svíčky",
        "CandlePageTitle.Text": "Svíčkový graf",
        "CandlePageSubtitle.Text":
            "Svíčky jednoho nástroje: denní, týdenní nebo měsíční, kreslené čtyřmi způsoby, "
            "s průměry a objemem pod nimi.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Interval",
        "CandlePeriodDaily": "Denní",
        "CandlePeriodWeekly": "Týdenní",
        "CandlePeriodMonthly": "Měsíční",
        "CandleStyleLabel.Header": "Způsob zobrazení",
        "CandleStyleCandles": "Svíčky",
        "CandleStyleBars": "OHLC sloupce",
        "CandleStyleLine": "Čára závěru",
        "CandleStyleArea": "Plocha závěru",
        "CandleMotionLabel.Header": "Animace",
        "CandleMotionGrow": "Celé období",
        "CandleMotionScroll": "Posuvné okno",
        "CandleWindowLabel.Header": "Okno (svíčky)",
        "CandleShowAverages.Content": "Klouzavé průměry MA5/10/20",
        "CandleOpen": "Otevření",
        "CandleClose": "Závěr",
        "CandleMoveLabel": "Změna",
        "CandleCardRange": "Výnos za období",
        "CandleCardAmplitude": "Rozpětí",
        "CandleLegendClose": "Závěr",
        "CandleFetched": "{0} {1} ({2} – {3})",
    },
    "tr": {
        "NavCandle.Content": "Mumlar",
        "CandlePageTitle.Text": "Mum grafiği",
        "CandlePageSubtitle.Text":
            "Bir enstrümanın mumları: günlük, haftalık veya aylık, dört farklı şekilde "
            "çizilir; altında ortalamaları ve hacmi.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Aralık",
        "CandlePeriodDaily": "Günlük",
        "CandlePeriodWeekly": "Haftalık",
        "CandlePeriodMonthly": "Aylık",
        "CandleStyleLabel.Header": "Çizim türü",
        "CandleStyleCandles": "Mumlar",
        "CandleStyleBars": "OHLC çubukları",
        "CandleStyleLine": "Kapanış çizgisi",
        "CandleStyleArea": "Kapanış alanı",
        "CandleMotionLabel.Header": "Animasyon",
        "CandleMotionGrow": "Aralığın tamamı",
        "CandleMotionScroll": "Kayan pencere",
        "CandleWindowLabel.Header": "Pencere (mum)",
        "CandleShowAverages.Content": "Hareketli ortalamalar MA5/10/20",
        "CandleOpen": "Açılış",
        "CandleClose": "Kapanış",
        "CandleMoveLabel": "Değişim",
        "CandleCardRange": "Dönem getirisi",
        "CandleCardAmplitude": "Genlik",
        "CandleLegendClose": "Kapanış",
        "CandleFetched": "{0} {1} ({2} - {3})",
    },
    "ru": {
        "NavCandle.Content": "Свечи",
        "CandlePageTitle.Text": "Свечной график",
        "CandlePageSubtitle.Text":
            "Свечи одного инструмента: дневные, недельные или месячные, в четырёх видах, "
            "со скользящими средними и объёмом ниже.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "Интервал",
        "CandlePeriodDaily": "Дневные",
        "CandlePeriodWeekly": "Недельные",
        "CandlePeriodMonthly": "Месячные",
        "CandleStyleLabel.Header": "Вид графика",
        "CandleStyleCandles": "Свечи",
        "CandleStyleBars": "Бары OHLC",
        "CandleStyleLine": "Линия закрытия",
        "CandleStyleArea": "Область закрытия",
        "CandleMotionLabel.Header": "Анимация",
        "CandleMotionGrow": "Весь диапазон",
        "CandleMotionScroll": "Скользящее окно",
        "CandleWindowLabel.Header": "Окно (свечи)",
        "CandleShowAverages.Content": "Скользящие средние MA5/10/20",
        "CandleOpen": "Открытие",
        "CandleClose": "Закрытие",
        "CandleMoveLabel": "Изменение",
        "CandleCardRange": "Доходность за период",
        "CandleCardAmplitude": "Амплитуда",
        "CandleLegendClose": "Закрытие",
        "CandleFetched": "{0} {1} ({2} — {3})",
    },
    "ja": {
        "NavCandle.Content": "ローソク足",
        "CandlePageTitle.Text": "ローソク足",
        "CandlePageSubtitle.Text":
            "1つの銘柄のローソク足。日足・週足・月足から選び、4つの描き方で表示します。下段に移動平均と出来高。",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "期間",
        "CandlePeriodDaily": "日足",
        "CandlePeriodWeekly": "週足",
        "CandlePeriodMonthly": "月足",
        "CandleStyleLabel.Header": "描き方",
        "CandleStyleCandles": "ローソク足",
        "CandleStyleBars": "OHLCバー",
        "CandleStyleLine": "終値ライン",
        "CandleStyleArea": "終値エリア",
        "CandleMotionLabel.Header": "進行",
        "CandleMotionGrow": "全区間を描く",
        "CandleMotionScroll": "窓をスクロール",
        "CandleWindowLabel.Header": "表示本数",
        "CandleShowAverages.Content": "移動平均 MA5/10/20",
        "CandleOpen": "始値",
        "CandleClose": "終値",
        "CandleMoveLabel": "騰落率",
        "CandleCardRange": "期間騰落率",
        "CandleCardAmplitude": "振幅",
        "CandleLegendClose": "終値",
        "CandleFetched": "{0}本の{1}（{2}〜{3}）",
    },
    "ko": {
        "NavCandle.Content": "캔들",
        "CandlePageTitle.Text": "캔들 차트",
        "CandlePageSubtitle.Text":
            "한 종목의 캔들입니다. 일·주·월 중에서 고르고 네 가지 방식으로 그립니다. 아래에 이동평균과 거래량.",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "주기",
        "CandlePeriodDaily": "일봉",
        "CandlePeriodWeekly": "주봉",
        "CandlePeriodMonthly": "월봉",
        "CandleStyleLabel.Header": "표시 방식",
        "CandleStyleCandles": "캔들",
        "CandleStyleBars": "OHLC 바",
        "CandleStyleLine": "종가 선",
        "CandleStyleArea": "종가 영역",
        "CandleMotionLabel.Header": "진행 방식",
        "CandleMotionGrow": "전체 구간 그리기",
        "CandleMotionScroll": "창 이동",
        "CandleWindowLabel.Header": "창 크기(캔들)",
        "CandleShowAverages.Content": "이동평균 MA5/10/20",
        "CandleOpen": "시가",
        "CandleClose": "종가",
        "CandleMoveLabel": "등락률",
        "CandleCardRange": "구간 수익률",
        "CandleCardAmplitude": "진폭",
        "CandleLegendClose": "종가",
        "CandleFetched": "{0}개 {1} ({2} ~ {3})",
    },
    "zh-Hans": {
        "NavCandle.Content": "K线",
        "CandlePageTitle.Text": "K线走势",
        "CandlePageSubtitle.Text":
            "一只标的的 K 线：日K、周K、月K 三种周期，四种画法，下方带均线与成交量。",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "周期",
        "CandlePeriodDaily": "日K",
        "CandlePeriodWeekly": "周K",
        "CandlePeriodMonthly": "月K",
        "CandleStyleLabel.Header": "画法",
        "CandleStyleCandles": "蜡烛图",
        "CandleStyleBars": "美国线",
        "CandleStyleLine": "收盘线",
        "CandleStyleArea": "面积图",
        "CandleMotionLabel.Header": "推进方式",
        "CandleMotionGrow": "逐根铺满",
        "CandleMotionScroll": "窗口滚动",
        "CandleWindowLabel.Header": "窗口根数",
        "CandleShowAverages.Content": "均线 MA5/10/20",
        "CandleOpen": "开",
        "CandleClose": "收",
        "CandleMoveLabel": "涨跌",
        "CandleCardRange": "区间涨跌",
        "CandleCardAmplitude": "振幅",
        "CandleLegendClose": "收盘价",
        "CandleFetched": "{0} 根{1}（{2} 至 {3}）",
    },
    "zh-Hant": {
        "NavCandle.Content": "K線",
        "CandlePageTitle.Text": "K線走勢",
        "CandlePageSubtitle.Text":
            "一檔標的的 K 線：日K、週K、月K 三種週期，四種畫法，下方帶均線與成交量。",
        "CandleSubtitleLine": "{0} · {1}",
        "CandleDefaultTitle": "{0} · {1}",
        "CandlePeriodLabel.Header": "週期",
        "CandlePeriodDaily": "日K",
        "CandlePeriodWeekly": "週K",
        "CandlePeriodMonthly": "月K",
        "CandleStyleLabel.Header": "畫法",
        "CandleStyleCandles": "蠟燭圖",
        "CandleStyleBars": "美國線",
        "CandleStyleLine": "收盤線",
        "CandleStyleArea": "面積圖",
        "CandleMotionLabel.Header": "推進方式",
        "CandleMotionGrow": "逐根鋪滿",
        "CandleMotionScroll": "視窗滾動",
        "CandleWindowLabel.Header": "視窗根數",
        "CandleShowAverages.Content": "均線 MA5/10/20",
        "CandleOpen": "開",
        "CandleClose": "收",
        "CandleMoveLabel": "漲跌",
        "CandleCardRange": "區間漲跌",
        "CandleCardAmplitude": "振幅",
        "CandleLegendClose": "收盤價",
        "CandleFetched": "{0} 根{1}（{2} 至 {3}）",
    },
}


def escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> int:
    before = {}

    for tag in TAGS:
        path = ROOT / tag / "Resources.resw"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        text = path.read_bytes().decode("utf-8-sig")
        before[tag] = hashlib.sha256(text.encode("utf-8")).hexdigest()

        for key in KEYS:
            value = escape(VALUES[tag][key])
            entry = f'  <data name="{key}"><value>{value}</value></data>'
            pattern = re.compile(
                r'  <data name="' + re.escape(key) + r'">.*?</data>', re.S)

            if pattern.search(text):
                text = pattern.sub(entry, text, count=1)
            else:
                text = text.replace("</root>", entry + "\n</root>", 1)

        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

    # Every file has to carry the same keys in the same order, or a build that
    # resolves one language will not resolve another.
    orders = {}

    for tag in TAGS:
        text = (ROOT / tag / "Resources.resw").read_bytes().decode("utf-8-sig")
        orders[tag] = tuple(re.findall(r'<data name="([^"]+)"', text))

    distinct = {hashlib.sha256("\n".join(order).encode("utf-8")).hexdigest() for order in orders.values()}

    if len(distinct) != 1:
        print("key order differs between languages")
        return 1

    for tag in TAGS:
        text = (ROOT / tag / "Resources.resw").read_bytes().decode("utf-8-sig")
        after = hashlib.sha256(text.encode("utf-8")).hexdigest()
        print(f"{tag:9} {len(orders[tag]):4} keys  {'changed' if after != before[tag] else 'unchanged'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
