# -*- coding: utf-8 -*-
r"""把「定投计划」这一轮新加的 resw 键注入 14 份 Resources.resw。

这一轮给了定投页三样持仓页刚有的东西：**两种推进方式**、**曲线末端实时显示收益金额**、
**最多六只对比**。前两样只是画面上的走法与标签，第三样让这一页第一次有了「几份计划放在
一起比」的说法，于是副标题、状态行、大数字下面那一行、标题都要多一种形式。

**为什么不复用持仓页那批键。** 表面上两页说同一件事，但那批键说的是 `holdings`（一只持仓 =
一笔钱买进去之后不动），这一页说的是 `plans`（一份计划 = 按节奏一直在买）。别人的语言里
这两个词常常不是一个词（德语 Anlage / Plan，波兰语 instrumentów / planów），共用会逼着
14 种语言各自去猜。而且**一个 resw 键只有一个 port 脚本负责** —— 持仓那批归
`port-position-motion-resw.py`，这一批归这里。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-dca-motion-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 推进方式 -------------------------------------------------------------------
#
# 与持仓页同一对、同一个理由，单位也一样（交易日），所以这四个键的措辞照着那一页来。

LABEL = [
    "Motion", "Ablauf", "Animación", "Animation", "Animazione", "Animacja",
    "Animação", "Animace", "Animasyon", "Анимация", "進行", "진행 방식",
    "推進方式", "推进方式",
]

GROW = [
    "Grow across the span", "Über die ganze Spanne", "Crecer por todo el periodo",
    "Tracer tout l'intervalle", "Tutto l'intervallo", "Cały zakres naraz",
    "Todo o período", "Celé období", "Aralığın tamamı", "Весь диапазон",
    "全区間を描く", "전체 구간 그리기", "整段鋪滿", "整段铺满",
]

SCROLL = [
    "Scroll a window", "Fenster weiterbewegen", "Desplazar una ventana",
    "Fenêtre glissante", "Finestra scorrevole", "Przesuwne okno",
    "Janela deslizante", "Posuvné okno", "Kayan pencere", "Скользящее окно",
    "窓をスクロール", "창 이동", "視窗滾動", "窗口滚动",
]

WINDOW = [
    "Window (days)", "Fenster (Tage)", "Ventana (días)", "Fenêtre (jours)",
    "Finestra (giorni)", "Okno (dni)", "Janela (dias)", "Okno (dny)",
    "Pencere (gün)", "Окно (дней)", "表示日数", "창 크기(일)",
    "視窗天數", "窗口天数",
]

# ---- 多只时的说法 ---------------------------------------------------------------

# 标题：两份计划互相命名。
VS = [
    "{0} vs {1}", "{0} gegen {1}", "{0} frente a {1}", "{0} face à {1}",
    "{0} contro {1}", "{0} kontra {1}", "{0} contra {1}", "{0} versus {1}",
    "{0} ve {1}", "{0} против {1}", "{0} vs {1}", "{0} vs {1}",
    "{0} vs {1}", "{0} vs {1}",
]

# 标题：三份以上。
MANY = [
    "{0} and {1} more", "{0} und {1} weitere", "{0} y {1} más", "{0} et {1} autres",
    "{0} e altri {1}", "{0} i {1} więcej", "{0} e mais {1}", "{0} a další {1}",
    "{0} ve {1} tane daha", "{0} и ещё {1}", "{0} ほか {1} 件", "{0} 외 {1}개",
    "{0} 等 {1} 個", "{0} 等 {1} 个",
]

# 状态行：几份计划、多少个交易日、什么区间。买入次数在这里换成计划份数 —— 六份计划各有各的
# 期数，报其中一个是在替它们挑。
BOARD = [
    "{0} plans · {1} trading days ({2} to {3})",
    "{0} Pläne · {1} Handelstage ({2} bis {3})",
    "{0} planes · {1} días de bolsa ({2} a {3})",
    "{0} plans · {1} jours de bourse ({2} au {3})",
    "{0} piani · {1} giorni di borsa ({2} al {3})",
    "{0} planów · {1} dni sesji ({2} do {3})",
    "{0} planos · {1} dias de pregão ({2} a {3})",
    "{0} plánů · {1} obchodních dnů ({2} až {3})",
    "{0} plan · {1} işlem günü ({2} - {3})",
    "Планов: {0} · торговых дней {1} ({2} — {3})",
    "{0} 件のプラン · {1}営業日（{2}〜{3}）",
    "플랜 {0}개 · 거래일 {1}일({2}~{3})",
    "已取 {0} 個計劃 · {1} 個交易日（{2} 至 {3}）",
    "已取 {0} 个计划 · {1} 个交易日（{2} 至 {3}）",
]

# 勾太多：拒绝取数，不是静默少画。
TOO_MANY = [
    "At most {0} plans can be compared; {1} are switched on",
    "Höchstens {0} Pläne lassen sich vergleichen; {1} sind eingeschaltet",
    "Se pueden comparar como máximo {0} planes; hay {1} activados",
    "{0} plans au maximum ; {1} sont activés",
    "Si possono confrontare al massimo {0} piani; {1} sono attivi",
    "Porównać można najwyżej {0} planów; włączonych jest {1}",
    "É possível comparar no máximo {0} planos; há {1} ligados",
    "Porovnat lze nejvýše {0} plánů; zapnuto je {1}",
    "En fazla {0} plan karşılaştırılabilir; {1} tanesi açık",
    "Сравнить можно не более {0} планов; включено {1}",
    "同時に比較できるのは最大 {0} 件です。いま {1} 件が選ばれています",
    "동시에 비교할 수 있는 플랜은 최대 {0}개입니다. 지금 {1}개가 켜져 있습니다",
    "最多同時對比 {0} 個計劃，現在勾了 {1} 個",
    "最多同时对比 {0} 个计划，现在勾了 {1} 个",
]

# 勾上的都不是本市场的：一份也画不出来。
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

# 区间内没有数据的那些：报出名字，不画平线。整句带括号，因为它是接在状态行后面的半句。
SKIPPED = [
    "({0} had no price in the range and was left out)",
    "({0} hatten im Zeitraum keinen Kurs und blieben außen vor)",
    "({0} no tenían precio en el rango y quedaron fuera)",
    "({0} n'avaient pas de cours sur la période et ont été écartés)",
    "({0} non avevano prezzi nel periodo e sono stati esclusi)",
    "({0} nie miały kursu w przedziale i zostały pominięte)",
    "({0} não tinham preço no intervalo e ficaram de fora)",
    "({0} neměly v rozsahu žádný kurz a byly vynechány)",
    "({0} aralıkta fiyatı olmadığı için dışarıda bırakıldı)",
    "({0} не имели цены в диапазоне и были пропущены)",
    "（期間内に価格がなかった {0} は除外しました）",
    "(기간 안에 가격이 없던 {0}은 제외했습니다)",
    "（{0} 在區間內沒有數據，已跳過）",
    "（{0} 在区间内没有数据，已跳过）",
]

# 副标题多只版：节奏、金额、份数、起点。单只那句说的是「投进哪一只」，多只没法这么说。
SUBTITLE = [
    "{0} · {1} {2} each · {3} plans from {4}",
    "{0} · je {1} {2} · {3} Pläne ab {4}",
    "{0} · {1} {2} cada uno · {3} planes desde {4}",
    "{0} · {1} {2} chacun · {3} plans depuis le {4}",
    "{0} · {1} {2} ciascuno · {3} piani dal {4}",
    "{0} · po {1} {2} · {3} planów od {4}",
    "{0} · {1} {2} cada · {3} planos desde {4}",
    "{0} · po {1} {2} · {3} plánů od {4}",
    "{0} · her birine {1} {2} · {4} tarihinden {3} plan",
    "{0} · по {1} {2} · планов: {3}, с {4}",
    "{0} · 各 {1}{2} · {3} 件のプラン（{4} から）",
    "{0} · 각각 {1}{2} · {3}개 플랜, {4}부터",
    "{0} · 每次 {1} {2} · {3} 個計劃自 {4} 起",
    "{0} · 每次 {1} {2} · {3} 个计划自 {4} 起",
]

# 大数字下面那一行：多只时它说「这是谁的」。收益率而不是金额 —— 晚上市的投得少，
# 赚得少不代表计划更差，只有收益率能并排。
LEADER = [
    "{0} · return so far", "{0} · Rendite bisher", "{0} · rentabilidad hasta ahora",
    "{0} · rendement à ce jour", "{0} · rendimento finora", "{0} · zwrot do tej pory",
    "{0} · retorno até agora", "{0} · výnos zatím", "{0} · şimdiye kadarki getiri",
    "{0} · доходность на сейчас", "{0} · 現時点の運用利回り",
    "{0} · 현재까지 수익률", "{0} · 目前收益率", "{0} · 目前收益率",
]

ROWS = [
    ("DcaMotionLabel.Header", LABEL),
    ("DcaMotionGrow", GROW),
    ("DcaMotionScroll", SCROLL),
    ("DcaWindowLabel.Header", WINDOW),
    ("DcaVsTitle", VS),
    ("DcaCompareMany", MANY),
    ("DcaBoardFetched", BOARD),
    ("DcaTooMany", TOO_MANY),
    ("DcaNoMarketPicks", NO_MARKET),
    ("DcaSkipped", SKIPPED),
    ("DcaCompareSubtitle", SUBTITLE),
    ("DcaLeaderLine", LEADER),
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
