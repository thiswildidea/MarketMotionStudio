#!/usr/bin/env python3
"""Adds the range picker's strings to all fourteen resource files.

The shared span control (需求一：全局时间范围) reads ten keys: its own header, the five
answers on its menu, the two custom days' headers, and the two ways the frame says what
span it is actually drawing.

Translated from the same Chinese every time rather than written fresh per language, so a
control that means one thing says one thing in all fourteen.

Idempotent: a file already carrying `RangeSpanToday` is left alone. resw keeps its BOM and
LF endings.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STRINGS = ROOT / "src" / "MarketMotionStudio" / "Strings"

ZH = {
    "PortfolioSpanNoBaseline": "这段时间的收益画不出来：{0}",
    "PortfolioSpanIncomplete": "自定义范围还没有选齐起止日期。",
    "RangeSpanHeader": "时间范围",
    "RangeSpanToday": "当日",
    "RangeSpanWeek": "近一周",
    "RangeSpanMonth": "近一月",
    "RangeSpanYear": "近一年",
    "RangeSpanCustom": "自定义",
    "RangeSpanFrom": "起始日期",
    "RangeSpanTo": "结束日期",
    "SpanRange": "{0}–{1}",
    "SpanRangeUnset": "未设定",
}

T = {
    "en-US": {
        "PortfolioSpanNoBaseline": "This span cannot be drawn: {0}",
        "PortfolioSpanIncomplete": "Pick both ends of the custom range first.",
        "RangeSpanHeader": "Range",
        "RangeSpanToday": "Today",
        "RangeSpanWeek": "Past week",
        "RangeSpanMonth": "Past month",
        "RangeSpanYear": "Past year",
        "RangeSpanCustom": "Custom",
        "RangeSpanFrom": "From",
        "RangeSpanTo": "To",
        "SpanRange": "{0} – {1}",
        "SpanRangeUnset": "not set",
    },
    "zh-Hant": {
        "PortfolioSpanNoBaseline": "這段時間的收益畫不出來：{0}",
        "PortfolioSpanIncomplete": "自訂範圍還沒有選齊起訖日期。",
        "RangeSpanHeader": "時間範圍",
        "RangeSpanToday": "當日",
        "RangeSpanWeek": "近一週",
        "RangeSpanMonth": "近一月",
        "RangeSpanYear": "近一年",
        "RangeSpanCustom": "自訂",
        "RangeSpanFrom": "起始日期",
        "RangeSpanTo": "結束日期",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "未設定",
    },
    "cs": {
        "PortfolioSpanNoBaseline": "Toto období nelze vykreslit: {0}",
        "PortfolioSpanIncomplete": "Nejprve vyberte oba konce vlastního období.",
        "RangeSpanHeader": "Období",
        "RangeSpanToday": "Dnes",
        "RangeSpanWeek": "Poslední týden",
        "RangeSpanMonth": "Poslední měsíc",
        "RangeSpanYear": "Poslední rok",
        "RangeSpanCustom": "Vlastní",
        "RangeSpanFrom": "Od",
        "RangeSpanTo": "Do",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "není nastaveno",
    },
    "de": {
        "PortfolioSpanNoBaseline": "Dieser Zeitraum kann nicht gezeichnet werden: {0}",
        "PortfolioSpanIncomplete": "Bitte zuerst Anfang und Ende des eigenen Zeitraums wählen.",
        "RangeSpanHeader": "Zeitraum",
        "RangeSpanToday": "Heute",
        "RangeSpanWeek": "Letzte Woche",
        "RangeSpanMonth": "Letzter Monat",
        "RangeSpanYear": "Letztes Jahr",
        "RangeSpanCustom": "Eigener Zeitraum",
        "RangeSpanFrom": "Von",
        "RangeSpanTo": "Bis",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "nicht festgelegt",
    },
    "es": {
        "PortfolioSpanNoBaseline": "No se puede dibujar este intervalo: {0}",
        "PortfolioSpanIncomplete": "Primero elige los dos extremos del intervalo personalizado.",
        "RangeSpanHeader": "Intervalo",
        "RangeSpanToday": "Hoy",
        "RangeSpanWeek": "Última semana",
        "RangeSpanMonth": "Último mes",
        "RangeSpanYear": "Último año",
        "RangeSpanCustom": "Personalizado",
        "RangeSpanFrom": "Desde",
        "RangeSpanTo": "Hasta",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "sin definir",
    },
    "fr": {
        "PortfolioSpanNoBaseline": "Cette période ne peut pas être tracée : {0}",
        "PortfolioSpanIncomplete": "Choisissez d'abord les deux bornes de la période personnalisée.",
        "RangeSpanHeader": "Période",
        "RangeSpanToday": "Aujourd'hui",
        "RangeSpanWeek": "Sept derniers jours",
        "RangeSpanMonth": "Trente derniers jours",
        "RangeSpanYear": "Douze derniers mois",
        "RangeSpanCustom": "Personnalisée",
        "RangeSpanFrom": "Du",
        "RangeSpanTo": "Au",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "non définie",
    },
    "it": {
        "PortfolioSpanNoBaseline": "Questo intervallo non può essere disegnato: {0}",
        "PortfolioSpanIncomplete": "Scegli prima entrambi gli estremi dell'intervallo personalizzato.",
        "RangeSpanHeader": "Intervallo",
        "RangeSpanToday": "Oggi",
        "RangeSpanWeek": "Ultima settimana",
        "RangeSpanMonth": "Ultimo mese",
        "RangeSpanYear": "Ultimo anno",
        "RangeSpanCustom": "Personalizzato",
        "RangeSpanFrom": "Da",
        "RangeSpanTo": "A",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "non impostato",
    },
    "ja": {
        "PortfolioSpanNoBaseline": "この期間は描画できません：{0}",
        "PortfolioSpanIncomplete": "カスタム期間の開始日と終了日を選んでください。",
        "RangeSpanHeader": "期間",
        "RangeSpanToday": "当日",
        "RangeSpanWeek": "直近1週間",
        "RangeSpanMonth": "直近1か月",
        "RangeSpanYear": "直近1年",
        "RangeSpanCustom": "カスタム",
        "RangeSpanFrom": "開始日",
        "RangeSpanTo": "終了日",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "未設定",
    },
    "ko": {
        "PortfolioSpanNoBaseline": "이 기간은 그릴 수 없습니다: {0}",
        "PortfolioSpanIncomplete": "사용자 지정 기간의 시작일과 종료일을 먼저 선택하세요.",
        "RangeSpanHeader": "기간",
        "RangeSpanToday": "당일",
        "RangeSpanWeek": "최근 1주",
        "RangeSpanMonth": "최근 1개월",
        "RangeSpanYear": "최근 1년",
        "RangeSpanCustom": "사용자 지정",
        "RangeSpanFrom": "시작일",
        "RangeSpanTo": "종료일",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "미설정",
    },
    "pl": {
        "PortfolioSpanNoBaseline": "Tego zakresu nie można narysować: {0}",
        "PortfolioSpanIncomplete": "Najpierw wybierz obie daty zakresu własnego.",
        "RangeSpanHeader": "Zakres",
        "RangeSpanToday": "Dziś",
        "RangeSpanWeek": "Ostatni tydzień",
        "RangeSpanMonth": "Ostatni miesiąc",
        "RangeSpanYear": "Ostatni rok",
        "RangeSpanCustom": "Własny",
        "RangeSpanFrom": "Od",
        "RangeSpanTo": "Do",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "nie ustawiono",
    },
    "pt-BR": {
        "PortfolioSpanNoBaseline": "Não é possível desenhar este período: {0}",
        "PortfolioSpanIncomplete": "Escolha primeiro as duas datas do período personalizado.",
        "RangeSpanHeader": "Período",
        "RangeSpanToday": "Hoje",
        "RangeSpanWeek": "Última semana",
        "RangeSpanMonth": "Último mês",
        "RangeSpanYear": "Último ano",
        "RangeSpanCustom": "Personalizado",
        "RangeSpanFrom": "De",
        "RangeSpanTo": "Até",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "não definido",
    },
    "ru": {
        "PortfolioSpanNoBaseline": "Этот период нельзя построить: {0}",
        "PortfolioSpanIncomplete": "Сначала выберите обе границы своего периода.",
        "RangeSpanHeader": "Период",
        "RangeSpanToday": "Сегодня",
        "RangeSpanWeek": "За неделю",
        "RangeSpanMonth": "За месяц",
        "RangeSpanYear": "За год",
        "RangeSpanCustom": "Свой период",
        "RangeSpanFrom": "С",
        "RangeSpanTo": "По",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "не задан",
    },
    "tr": {
        "PortfolioSpanNoBaseline": "Bu aralık çizilemiyor: {0}",
        "PortfolioSpanIncomplete": "Önce özel aralığın iki ucunu seçin.",
        "RangeSpanHeader": "Aralık",
        "RangeSpanToday": "Bugün",
        "RangeSpanWeek": "Son hafta",
        "RangeSpanMonth": "Son ay",
        "RangeSpanYear": "Son yıl",
        "RangeSpanCustom": "Özel",
        "RangeSpanFrom": "Başlangıç",
        "RangeSpanTo": "Bitiş",
        "SpanRange": "{0}–{1}",
        "SpanRangeUnset": "ayarlanmadı",
    },
}


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    changed = 0

    for lang, table in [("zh-Hans", ZH), *T.items()]:
        path = STRINGS / lang / "Resources.resw"

        if not path.exists():
            print(f"{lang}: MISSING FILE")
            continue

        resw = path
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
