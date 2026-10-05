# -*- coding: utf-8 -*-
r"""把「持仓收益」多标的对比的 resw 键注入 14 份 Resources.resw。

这一页原来只画一只：搜索框选一个代码、收藏行记一个标的。现在它画的是读者自己那份
**共享自选清单**里勾中的几只——与本项目五个榜单同一份清单——所以页面上多了两件事
需要文字：

* **标题与副标题**。一只时仍是「持仓收益：中国平安」；两只时是「中国平安 vs 贵州茅台」
  （与用户给的参考图一致）；三只及以上是「中国平安 等 3 只」。副标题不能再写「买入
  ××元的××」，因为买入日是按各标的自己的首个交易日算的。
* **画面上的字**。每只曲线末端跟着一个胶囊标签（名字 + 收益金额），中间那个大数字在
  多只时改成**领先那只**的收益金额，下面的说明行随之换成那只的名字。
* **三条状态/报错**。超过上限（6 只）、自选里没有本市场的标的、以及区间内没有数据的
  标的被跳过——最后这条要**点名**，因为画面因此少一条线。

**复用既有的键，不另造**：`PositionFetched`（一只时的取数回报）、`PositionDefaultTitle`
（一只时的标题）、`DcaWanUnit` / `DcaCurrency*` / `DcaReturnLabel` / `DcaCardProfit` /
`PositionCard*` / `PositionLegendCapital` / `PositionSubtitleLine` / `PositionRangeLine`
全部照旧读，本脚本只写下面这 8 个新键。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。
第一列必须是英文——`port-ahpremium-resw.py` 里 `AhPremiumFetched` 就是在这里栽过：
第一列写成了中文，英文界面于是显示一整行中文状态。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-position-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 两只时的标题。参考图（长江电力 vs 工商银行）就是这个形状，所以中文也保留 vs。
VS = [
    "{0} vs {1}", "{0} gegen {1}", "{0} frente a {1}", "{0} face à {1}",
    "{0} contro {1}", "{0} kontra {1}", "{0} contra {1}", "{0} versus {1}",
    "{0} ve {1}", "{0} против {1}", "{0} vs {1}", "{0} vs {1}",
    "{0} vs {1}", "{0} vs {1}",
]

# 三只及以上：只报第一只的名字与总数。依次列六只名字会把标题撑成一整行。
MANY = [
    "{0} and {1} more", "{0} und {1} weitere", "{0} y {1} más", "{0} et {1} autres",
    "{0} e altri {1}", "{0} i {1} więcej", "{0} e mais {1}", "{0} a další {1}",
    "{0} ve {1} tane daha", "{0} и ещё {1}", "{0} ほか {1} 銘柄", "{0} 외 {1}개",
    "{0} 等 {1} 隻", "{0} 等 {1} 只",
]

# 副标题：{0} 金额、{1} 币种、{2} 区间起点。
#
# 不能沿用一只时那句「{0}买入{1}{2}的{3}」：每只是**各自**首个交易日买入的，写一个
# 买入日就是给一个不存在的日子。所以改成「各投入 …… 自 …… 起」，说清是同一笔金额、
# 落在各区间的起点上。
SUBTITLE = [
    "{0}{1} into each, from {2} · adjusted closes · dividends reinvested",
    "{0}{1} je Anlage, ab {2} · bereinigte Schlusskurse · Dividenden wieder angelegt",
    "{0}{1} en cada una, desde {2} · cierres ajustados · dividendos reinvertidos",
    "{0}{1} sur chacune, depuis le {2} · clôtures ajustées · dividendes réinvestis",
    "{0}{1} su ciascuna, dal {2} · chiusure rettificate · dividendi reinvestiti",
    "{0}{1} na każdą, od {2} · skorygowane zamknięcia · dywidendy reinwestowane",
    "{0}{1} em cada uma, desde {2} · fechamentos ajustados · dividendos reinvestidos",
    "{0}{1} do každé, od {2} · očištěné závěry · dividendy reinvestovány",
    "Her birine {0}{1}, {2} tarihinden · düzeltilmiş kapanışlar · temettüler yeniden yatırılır",
    "{0}{1} на каждую, с {2} · скорректированные закрытия · дивиденды реинвестируются",
    "各 {0}{1}、{2} から · 後復権終値 · 配当は再投資で計上",
    "각각 {0}{1}, {2}부터 · 후복권 종가 · 배당은 재투자로 반영",
    "各投入 {0}{1}，自 {2} 起 · 後復權收盤價 · 分紅按再投計入",
    "各投入 {0}{1}，自 {2} 起 · 后复权收盘价 · 分红按再投计入",
]

# 大数字下面那行：多只时是领先那只的名字。一只时仍是 DcaReturnLabel（「收益率」）。
LEADER = [
    "{0} · profit so far", "{0} · Gewinn bisher", "{0} · ganancia hasta ahora",
    "{0} · gain à ce jour", "{0} · guadagno finora", "{0} · zysk do tej pory",
    "{0} · lucro até agora", "{0} · zisk zatím", "{0} · şimdiye kadarki kâr",
    "{0} · прибыль на сейчас", "{0} · 現時点の累計収益", "{0} · 현재까지 누적 수익",
    "{0} · 累計收益", "{0} · 累计收益",
]

# 多只时的取数回报。
BOARD_FETCHED = [
    "{0} holdings over {1} trading days ({2} to {3})",
    "{0} Anlagen über {1} Handelstage ({2} bis {3})",
    "{0} valores en {1} días de negociación ({2} a {3})",
    "{0} supports sur {1} jours de bourse ({2} à {3})",
    "{0} strumenti su {1} giornate di borsa ({2}–{3})",
    "{0} instrumentów w {1} dniach sesyjnych ({2} – {3})",
    "{0} ativos em {1} dias de negociação ({2} a {3})",
    "{0} nástrojů za {1} obchodních dnů ({2} – {3})",
    "{0} varlık, {1} işlem günü ({2} – {3})",
    "{0} инструментов за {1} торговых дней ({2} – {3})",
    "{0} 銘柄・{1} 営業日（{2} 〜 {3}）",
    "{0}개 종목 · {1}거래일({2} ~ {3})",
    "已取 {0} 隻標的 · {1} 個交易日（{2} 至 {3}）",
    "已取 {0} 只标的 · {1} 个交易日（{2} 至 {3}）",
]

# 被跳过的标的：点名，不计数。画面因此少一条线，读者要知道是哪一只。
SKIPPED = [
    "{0} had no price in the range and was left out: {1}",
    "{0} hatten im Zeitraum keinen Kurs und blieben außen vor: {1}",
    "{0} no tenían precio en el rango y quedaron fuera: {1}",
    "{0} n'avaient pas de cours sur la période et ont été écartés : {1}",
    "{0} non avevano prezzi nel periodo e sono stati esclusi: {1}",
    "{0} nie miały kursu w przedziale i zostały pominięte: {1}",
    "{0} não tinham preço no intervalo e ficaram de fora: {1}",
    "{0} neměly v rozsahu žádný kurz a byly vynechány: {1}",
    "{0} aralıkta fiyatı olmadığı için dışarıda bırakıldı: {1}",
    "{0} не имели цены в диапазоне и были пропущены: {1}",
    "期間内に価格がなかった {0} 銘柄は除外しました：{1}",
    "기간 안에 가격이 없던 {0}개는 제외했습니다: {1}",
    "區間內沒有數據的 {0} 隻已跳過：{1}",
    "区间内没有数据的 {0} 只已跳过：{1}",
]

# 超过上限。**拒绝而不是截断**：六条线还能算对比，九条线是条形码，而少画三只的
# 画面看起来完全正常。
TOO_MANY = [
    "At most {0} holdings can be compared; {1} are switched on",
    "Höchstens {0} Anlagen lassen sich vergleichen; {1} sind eingeschaltet",
    "Se pueden comparar como máximo {0} valores; hay {1} activados",
    "{0} supports au maximum ; {1} sont activés",
    "Si possono confrontare al massimo {0} strumenti; {1} sono attivi",
    "Porównać można najwyżej {0} instrumentów; włączonych jest {1}",
    "É possível comparar no máximo {0} ativos; há {1} ligados",
    "Porovnat lze nejvýše {0} nástrojů; zapnuto je {1}",
    "En fazla {0} varlık karşılaştırılabilir; {1} tanesi açık",
    "Сравнить можно не более {0} инструментов; включено {1}",
    "同時に比較できるのは最大 {0} 銘柄です。いま {1} 銘柄が選ばれています",
    "동시에 비교할 수 있는 종목은 최대 {0}개입니다. 지금 {1}개가 켜져 있습니다",
    "最多同時對比 {0} 隻，現在勾了 {1} 隻",
    "最多同时对比 {0} 只，现在勾了 {1} 只",
]

# 勾中的标的都不属于当前市场。共享清单是跨市场的（五个榜单要三个市场同轴），
# 而这一页的金额是本市场货币，所以那些不能画。
NO_MARKET = [
    "None of your list is on the {0} market",
    "Nichts auf Ihrer Liste gehört zum Markt {0}",
    "Ningún valor de tu lista pertenece al mercado {0}",
    "Aucun support de votre liste n'appartient au marché {0}",
    "Nessuno strumento della tua lista appartiene al mercato {0}",
    "Żaden instrument z listy nie należy do rynku {0}",
    "Nenhum ativo da sua lista pertence ao mercado {0}",
    "Žádný nástroj ze seznamu nepatří na trh {0}",
    "Listenizdeki hiçbir varlık {0} piyasasına ait değil",
    "Ни одного инструмента из списка нет на рынке {0}",
    "マイリストに{0}市場の銘柄がありません",
    "내 목록에 {0} 시장 종목이 없습니다",
    "自選清單裡沒有{0}的標的",
    "自选清单里没有{0}的标的",
]

ROWS = [
    ("PositionVsTitle", VS),
    ("PositionCompareMany", MANY),
    ("PositionCompareSubtitle", SUBTITLE),
    ("PositionLeaderLine", LEADER),
    ("PositionBoardFetched", BOARD_FETCHED),
    ("PositionSkipped", SKIPPED),
    ("PositionTooMany", TOO_MANY),
    ("PositionNoMarketPicks", NO_MARKET),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project file
    rather than the string that caused it.
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
