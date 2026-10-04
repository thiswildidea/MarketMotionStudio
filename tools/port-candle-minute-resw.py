# -*- coding: utf-8 -*-
r"""把「K 线页加 1/5/15 分钟三档 + 挑一个交易日」要用的 resw 键注入 14 份 Resources.resw。

分钟 K 线走的是一个新端点（`ifzq.gtimg.cn/.../kline/mkline`），三件事决定了这些文案怎么写：

* **只有沪深两市有。** 港股、美股、北证 50 一律返回空的 `data`，所以拒因文案必须说出
  「只有沪深两市」，而不是笼统的「取不到」——前者读者能自己判断要不要换个标的，后者不能。
* **不能任意指定日期。** 端点不接受日期区间（传了就只回 qt/prec，没有 K 线块），只给
  「最近 N 根」。所以交易日下拉是**从取回来的日子里挑**，不是日历。说明文案要把这一点写在
  控件下面，否则读者会以为能挑到去年某一天。
* **只列完整的交易日。** 最近那天可能还在盘中、最早那天可能被 800 根截断，两者都不是一天。
  `CandleMinuteNoWhole` 就是这一种。

复用的键（不新造）：进度行用 `TurnoverIntradayFetching`、午休那条线上的小字用
`TurnoverIntradayNoon`——都是同一件事，14 种译法就是 14 次译错的机会。

resw 是 UTF-8 **带 BOM** + LF。删键按「基础名 + 可选后缀」匹配——文件里两种条目格式并存，
写成 `">` 结尾会漏掉带 `xml:space="preserve"` 的那一种（PRI278 的根因）。

幂等：先删同名键再追加，跑几遍结果一样。

用法：python tools\port-candle-minute-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 每条文案写满 14 列，列序与 LANGS 完全一致：
# en-US, de, es, fr, it, pl, pt-BR, cs, tr, ru, ja, ko, zh-Hant, zh-Hans

PAGE = [
    # ---- 周期下拉多出来的三档 -----------------------------------------------------
    ("CandlePeriodMinute1", [
        "1 minute", "1 Minute", "1 minuto", "1 minute", "1 minuto", "1 minuta",
        "1 minuto", "1 minuta", "1 dakika", "1 минута", "1 分", "1분",
        "1 分鐘", "1 分钟"]),

    ("CandlePeriodMinute5", [
        "5 minutes", "5 Minuten", "5 minutos", "5 minutes", "5 minuti", "5 minut",
        "5 minutos", "5 minut", "5 dakika", "5 минут", "5 分", "5분",
        "5 分鐘", "5 分钟"]),

    ("CandlePeriodMinute15", [
        "15 minutes", "15 Minuten", "15 minutos", "15 minutes", "15 minuti", "15 minut",
        "15 minutos", "15 minut", "15 dakika", "15 минут", "15 分", "15분",
        "15 分鐘", "15 分钟"]),

    # ---- 交易日下拉 ---------------------------------------------------------------
    ("CandleDayLabel.Header", [
        "Trading day", "Handelstag", "Día de negociación", "Jour de bourse",
        "Giornata di borsa", "Dzień sesji", "Dia de negociação", "Obchodní den",
        "İşlem günü", "Торговый день", "取引日", "거래일", "交易日", "交易日"]),

    # 下拉下面那行说明。必须说清「只能挑源端还留着的这几天」：不给这句，下拉看起来
    # 就是个能随便选日期的控件，而事实不是。
    ("CandleMinuteNote.Text", [
        "The source keeps minute candles for the last few sessions only — these are the "
        "days it still has.",

        "Die Quelle hält Minutenkerzen nur für die letzten Sitzungen — dies sind die Tage, "
        "die sie noch hat.",

        "La fuente conserva velas por minuto solo para las últimas sesiones — estos son "
        "los días que aún tiene.",

        "La source ne conserve les bougies par minute que pour les dernières séances — "
        "voici les jours qu'elle a encore.",

        "La fonte conserva le candele al minuto solo per le ultime sedute — questi sono i "
        "giorni che ha ancora.",

        "Źródło trzyma świece minutowe tylko dla ostatnich sesji — to są dni, które "
        "jeszcze ma.",

        "A fonte mantém candles de minuto apenas para as últimas sessões — estes são os "
        "dias que ainda tem.",

        "Zdroj uchovává minutové svíčky jen pro poslední seance — toto jsou dny, které "
        "ještě má.",

        "Kaynak dakika mumlarını yalnızca son birkaç seans için tutuyor — bunlar elinde "
        "kalan günler.",

        "Источник хранит минутные свечи только за последние несколько сессий — это дни, "
        "которые у него ещё есть.",

        "ソースが分足を保持しているのは直近数セッションだけです。ここに並ぶのは、"
        "いま残っている日です。",

        "소스는 최근 몇 세션의 분봉만 보관합니다. 아래에 있는 날짜가 현재 남아 있는 날입니다.",

        "來源只保留最近幾個交易日的分鐘 K 線——這裡列出的是它現在還留著的日子。",

        "来源只保留最近几个交易日的分钟 K 线——这里列出的是它现在还留着的日子。"]),

    # ---- 状态行 -------------------------------------------------------------------
    # {0}=名字，{1}=日期，{2}=根数，{3}=还能挑的完整交易日数。
    ("CandleMinuteFetched", [
        "{0} on {1} · {2} candles · {3} whole sessions to choose from",
        "{0} am {1} · {2} Kerzen · {3} vollständige Sitzungen zur Auswahl",
        "{0} el {1} · {2} velas · {3} sesiones completas para elegir",
        "{0} le {1} · {2} bougies · {3} séances complètes au choix",
        "{0} il {1} · {2} candele · {3} sedute complete tra cui scegliere",
        "{0} {1} · {2} świec · {3} pełne sesje do wyboru",
        "{0} em {1} · {2} candles · {3} sessões completas para escolher",
        "{0} {1} · {2} svíček · {3} celé seance na výběr",
        "{0} · {1} · {2} mum · seçilebilir {3} tam seans",
        "{0} {1} · {2} свечей · полных сессий на выбор: {3}",
        "{0} {1} · {2} 本 · 選べる完全なセッション {3} 日分",
        "{0} {1} · {2}개 봉 · 선택 가능한 온전한 세션 {3}개",
        "{0} · {1} · {2} 根 · 還有 {3} 個完整交易日可選",
        "{0} · {1} · {2} 根 · 还有 {3} 个完整交易日可选"]),

    # 源端没有这个标的的分钟 K 线。{0}=名字，{1}=代码。
    # 必须点名「只有沪深两市」：北证 50 是 A 股但没有分钟数据，说「没有数据」读者会以为
    # 是网络问题，说「只有沪深」他立刻知道换只股票就行。
    ("CandleMinuteNone", [
        "The source keeps no minute candles for {0} ({1}) — only Shanghai and Shenzhen "
        "have them.",

        "Die Quelle hat keine Minutenkerzen für {0} ({1}) — nur Shanghai und Shenzhen "
        "führen sie.",

        "La fuente no tiene velas por minuto de {0} ({1}) — solo las tienen Shanghái y "
        "Shenzhen.",

        "La source n'a pas de bougies par minute pour {0} ({1}) — seules Shanghai et "
        "Shenzhen en ont.",

        "La fonte non ha candele al minuto per {0} ({1}) — le hanno solo Shanghai e "
        "Shenzhen.",

        "Źródło nie ma świec minutowych dla {0} ({1}) — mają je tylko Szanghaj i Shenzhen.",

        "A fonte não tem candles de minuto para {0} ({1}) — apenas Xangai e Shenzhen os "
        "têm.",

        "Zdroj nemá minutové svíčky pro {0} ({1}) — mají je jen Šanghaj a Šen-čen.",

        "Kaynakta {0} ({1}) için dakika mumu yok — yalnızca Şanghay ve Shenzhen'de var.",

        "У источника нет минутных свечей для {0} ({1}) — они есть только для Шанхая и "
        "Шэньчжэня.",

        "ソースに {0}（{1}）の分足はありません。分足があるのは上海と深圳だけです。",

        "소스에 {0}({1})의 분봉이 없습니다. 분봉이 있는 곳은 상하이와 선전뿐입니다.",

        "來源沒有 {0}（{1}）的分鐘 K 線——只有滬深兩市有。",

        "来源没有 {0}（{1}）的分钟 K 线——只有沪深两市有。"]),

    # 取回来了，但没有一天是完整的。
    ("CandleMinuteNoWhole", [
        "None of the sessions that came back is a whole day — the latest one may still be "
        "trading.",

        "Keine der zurückgegebenen Sitzungen ist ein ganzer Tag — die letzte läuft "
        "vielleicht noch.",

        "Ninguna de las sesiones devueltas es un día completo — la última puede seguir "
        "cotizando.",

        "Aucune des séances renvoyées n'est une journée complète — la dernière est "
        "peut-être en cours.",

        "Nessuna delle sedute ricevute è una giornata intera — l'ultima potrebbe essere "
        "ancora in corso.",

        "Żadna z otrzymanych sesji nie jest pełnym dniem — ostatnia może jeszcze trwać.",

        "Nenhuma das sessões recebidas é um dia inteiro — a última pode ainda estar em "
        "andamento.",

        "Žádná z vrácených seancí není celý den — ta poslední možná ještě probíhá.",

        "Dönen seansların hiçbiri tam bir gün değil — sonuncusu hâlâ işlem görüyor "
        "olabilir.",

        "Ни одна из полученных сессий не является полным днём — последняя, возможно, "
        "ещё идёт.",

        "返ってきたセッションに 1 日分としてそろっているものがありません。"
        "最新の日はまだ取引中の可能性があります。",

        "받아온 세션 중 하루치가 온전한 것이 없습니다. 마지막 날은 아직 거래 중일 수 있습니다.",

        "取回來的幾天都不是完整的交易日——最新那天可能還在盤中。",

        "取回来的几天都不是完整的交易日——最新那天可能还在盘中。"]),

    # 港股/美股下那三档是灰的，这是灰的原因（鼠标悬停）。
    ("CandleMinuteMarketNone", [
        "This market has no minute candles — the source keeps them for Shanghai and "
        "Shenzhen only.",

        "Dieser Markt hat keine Minutenkerzen — die Quelle führt sie nur für Shanghai und "
        "Shenzhen.",

        "Este mercado no tiene velas por minuto — la fuente solo las tiene para Shanghái y "
        "Shenzhen.",

        "Ce marché n'a pas de bougies par minute — la source ne les conserve que pour "
        "Shanghai et Shenzhen.",

        "Questo mercato non ha candele al minuto — la fonte le conserva solo per Shanghai "
        "e Shenzhen.",

        "Ten rynek nie ma świec minutowych — źródło ma je tylko dla Szanghaju i Shenzhen.",

        "Este mercado não tem candles de minuto — a fonte os mantém apenas para Xangai e "
        "Shenzhen.",

        "Tento trh nemá minutové svíčky — zdroj je uchovává jen pro Šanghaj a Šen-čen.",

        "Bu piyasada dakika mumu yok — kaynak bunları yalnızca Şanghay ve Shenzhen için "
        "tutuyor.",

        "У этого рынка нет минутных свечей — источник хранит их только для Шанхая и "
        "Шэньчжэня.",

        "この市場に分足はありません。ソースが分足を保持しているのは上海と深圳だけです。",

        "이 시장에는 분봉이 없습니다. 소스가 분봉을 보관하는 곳은 상하이와 선전뿐입니다.",

        "這個市場沒有分鐘 K 線——來源只為滬深兩市保留。",

        "这个市场没有分钟 K 线——来源只为沪深两市保留。"]),
]


def entry(key, value):
    """One <data> line, escaped.

    A bare `&` is not legal XML, and MakePri reports it as `PRI224: root node not found`,
    naming the root element rather than the value that broke it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        at = LANGS.index(tag)
        lines = []

        for key, values in PAGE:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values"
            lines.append(entry(key, values[at]))

        # Idempotent: drop a key of the same name wherever it already sits, then append.
        # `[^>]*` after the name because this file holds two entry shapes — the single-line
        # `<data name="K">` a machine wrote and the hand-edited
        # `<data name="K" xml:space="preserve">` — and a pattern that insists on `">` matches
        # only the first, which is how a file once ended up holding both `K` and `K.Text`
        # (PRI278: key defined as both a resource and a scope).
        for key, _ in PAGE:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at_root = text.rfind("</root>")
        assert at_root > 0, f"{tag}: no </root>"

        text = text[:at_root] + "".join(lines) + text[at_root:]

        # Bytes, not text: read_text/write_text would normalise the line endings and git
        # would see the whole file rewritten. utf-8-sig because a resw without its BOM is
        # read as UTF-16 by MakePri.
        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
