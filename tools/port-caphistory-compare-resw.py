# -*- coding: utf-8 -*-
r"""把「市值历程」同时画几家公司的 resw 键注入 14 份 Resources.resw。

这一页改成多标的之后多出三样要说话的东西：

1. **刻度开关**（绝对值 / 归一到 100）。两种口径看的不是同一件事：绝对值回答「谁更大」，
   归一回答「谁涨得更快」——工商银行 2.3 万亿旁边放五粮液 2,731 亿，绝对值画面里后者是贴着
   底边的一条直线，看着像「这家公司什么都没发生」。
2. **多标的的标题**：「A 对 B」/「A 等 3 家」。
3. **多标的的状态行**：几家公司 × 多少个交易日，以及被略过的公司**点名**。

**一个 resw 键只有一个 port 脚本负责。** 这一页原有的那些键（面板名、单位、错误提示等等）
归 `port-caphistory-resw.py`，本脚本一个都不碰 —— 两边沾同一个键，先跑的那个留下的字会
被后跑的删掉，而删掉的一方完全不出声。所以 `CapHistoryPageSubtitle.Text` 那种「本来就有、
但现在说漏了多标的」的旧键，是回到它的 owner 脚本里改的，不在这里。

幂等：先删后插，跑几遍结果一样。resw 是 **UTF-8 带 BOM + LF**；删键按「基础名 + 可选后缀」
匹配，因为文件里单行 `<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">`
两种形态并存，写死 `">` 只匹配前一种，漏删会让 MakePri 以 PRI278 拒绝整份文件。

用法：python tools\port-caphistory-compare-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 下拉框标题。写「市值」而不写「纵轴」：这个开关改的是上面板那条线用什么单位读，股价面板
# 有自己的单位、与它无关 —— 写「纵轴」会让人以为两个面板一起变。
LABEL = [
    "Value axis", "Wertachse", "Eje del valor", "Axe des valeurs",
    "Asse del valore", "Oś wartości", "Eixo do valor", "Osa hodnoty",
    "Değer ekseni", "Ось значений", "目盛り", "값 축", "市值刻度", "市值刻度",
]

# 第一种：数字本身就是答案，回答「哪家公司更大」。默认项。
ABSOLUTE = [
    "As it stood", "Tatsächlicher Wert", "Valor real", "Valeur réelle",
    "Valore reale", "Wartość rzeczywista", "Valor real", "Skutečná hodnota",
    "Gerçek değer", "Фактическое значение", "実際の額", "실제 값",
    "實際數值", "实际数值",
]

# 第二种：各家按自己的首日折到 100，回答「谁的市值涨得更快」。
#
# 不写「百分比」：样子确实像涨跌幅，但这条线上的数是 **137** 而不是 **+37%**，而「用百分比
# 表示」会让「跌到 82」在不同语言里分别变成 −18%、18% 或 0.82 —— 那是十四个笔误等着发生。
# 写成「= 100 起点」，哪种语言都同一副写法。
NORMALIZED = [
    "Rebased to 100", "Auf 100 umbasiert", "Rebasado a 100", "Rebasé sur 100",
    "Ribasato a 100", "Przeliczone na 100", "Rebaseado em 100",
    "Přepočteno na 100", "100'e göre yeniden", "К 100 в начале",
    "100 基準", "100 기준", "歸一到 100", "归一到 100",
]

# 归一化时纵轴的单位写成「首日 = 100」而不是「亿元」：那时候画出来的数不是钱。
#
# 这一个键代替了 `CapHistoryCapUnit`（数量级 + 货币）的位置，但不能删 —— 前者是金额的
# 量级模板（亿在英文里没有，十四种写法），这一条是两个数字和一个等号，哪种语言都一样写。
REBASED_UNIT = [
    "first day = 100", "erster Tag = 100", "primer día = 100", "1er jour = 100",
    "primo giorno = 100", "pierwszy dzień = 100", "primeiro dia = 100",
    "první den = 100", "ilk gün = 100", "первый день = 100", "初日 = 100",
    "첫날 = 100", "首日 = 100", "首日 = 100",
]

# 刻度开关的说明。要回答的是多标的时**股价面板去哪了** —— 那是这一页原来的一半画面，
# 消失得没说一句。顺便交代归一什么时候才有用。
AXIS_NOTE = [
    "Comparing several companies gives the whole frame to market value — there is no "
    "price axis their prices share honestly — and each line is named at its end. "
    "Rebasing answers whose value grew faster once one is many times the other.",
    "Beim Vergleich mehrerer Unternehmen gehört der ganze Rahmen dem Marktwert — es gibt "
    "keine Preisachse, die ihre Kurse ehrlich teilen — und jede Linie ist am Ende "
    "beschriftet. Das Umbasieren beantwortet, wessen Wert schneller wuchs, wenn einer ein "
    "Vielfaches des anderen ist.",
    "Comparar varias empresas da todo el marco al valor de mercado — no hay un eje de "
    "precios que sus cotizaciones compartan con honestidad — y cada línea se nombra en su "
    "extremo. Rebasar responde quién creció más rápido cuando una es muchas veces la otra.",
    "Comparer plusieurs entreprises donne tout le cadre à la valeur de marché — il n'existe "
    "pas d'axe de prix que leurs cours partagent honnêtement — et chaque courbe est nommée "
    "à son extrémité. Le rebasement répond à la question de laquelle a le plus progressé "
    "quand l'une vaut plusieurs fois l'autre.",
    "Il confronto di più aziende lascia tutto il riquadro al valore di mercato — non c'è un "
    "asse dei prezzi che i loro prezzi condividano onestamente — e ogni linea è nominata "
    "alla sua estremità. Il ribasamento dice quale valore è cresciuto più in fretta quando "
    "uno è molte volte l'altro.",
    "Porównanie kilku spółek oddaje cały kadr wartości rynkowej — nie ma osi cen, którą ich "
    "kursy dzielą uczciwie — a każda linia jest podpisana na końcu. Przeliczenie na 100 "
    "mówi, czyja wartość rosła szybciej, gdy jedna jest wielokrotnością drugiej.",
    "Comparar várias empresas dá todo o quadro ao valor de mercado — não há eixo de preço "
    "que seus preços compartilhem honestamente — e cada linha é nomeada na ponta. Rebasear "
    "responde quem cresceu mais rápido quando uma é várias vezes a outra.",
    "Při porovnání více firem patří celý rám tržní hodnotě — neexistuje cenová osa, kterou "
    "by jejich ceny sdílely poctivě — a každá linie je pojmenována na konci. Přepočet říká, "
    "čí hodnota rostla rychleji, když je jedna násobkem druhé.",
    "Birden çok şirket karşılaştırıldığında çerçevenin tamamı piyasa değerine kalır — "
    "fiyatlarının dürüstçe paylaşacağı bir fiyat ekseni yoktur — ve her çizgi ucunda "
    "adlandırılır. Yeniden basma, biri diğerinin katları olduğunda kimin değeri daha hızlı "
    "büyüdü sorusunu yanıtlar.",
    "При сравнении нескольких компаний весь кадр отдаётся капитализации — нет оси цен, "
    "которую их цены делят честно, — и каждая линия подписана на конце. Пересчёт к 100 "
    "отвечает, чья капитализация росла быстрее, когда одна во много раз больше другой.",
    "複数社を比べると枠のすべてが時価総額に割かれます。株価を正直に共有できる価格軸が"
    "ないためで、各線は末端に名前が付きます。一方が他方の何倍もあるとき、100 基準は"
    "どちらが速く伸びたかを答えます。",
    "여러 기업을 비교하면 프레임 전체를 시가총액에 씁니다(주가를 정직하게 공유할 가격 축이 "
    "없으므로). 각 선은 끝에 이름이 붙습니다. 한쪽이 다른 쪽의 몇 배일 때 100 기준은 누가 "
    "더 빨리 컸는지를 답합니다.",
    "選了幾家公司時，整個畫面都留給市值：幾條股價曲線沒有一套共用的、誠實的刻度，所以"
    "每條線在自己的末端標出名字。若一家比另一家大好幾倍，歸一（首日 = 100）看的是誰漲得"
    "更快。",
    "选了几家公司时，整个画面都留给市值：几条股价曲线没有一套共用的、诚实的刻度，所以"
    "每条线在自己的末端标出名字。若一家比另一家大好几倍，归一（首日 = 100）看的是谁涨得"
    "更快。",
]

# 两家时的默认标题。
VS = [
    "{0} vs {1}", "{0} gegen {1}", "{0} frente a {1}", "{0} contre {1}",
    "{0} contro {1}", "{0} kontra {1}", "{0} x {1}", "{0} vs {1}",
    "{0} ve {1}", "{0} против {1}", "{0} 対 {1}", "{0} 대 {1}",
    "{0} 對 {1}", "{0} 对 {1}",
]

# 三家以上：{1} 是含第一家在内的**总数**（length），不是「另外几家」。
MANY = [
    "{0} and {1} more", "{0} und {1} weitere", "{0} y {1} más", "{0} et {1} autres",
    "{0} e altre {1}", "{0} i {1} więcej", "{0} e mais {1}", "{0} a dalších {1}",
    "{0} ve {1} tane daha", "{0} и ещё {1}", "{0} ほか {1} 社", "{0} 외 {1}개",
    "{0} 等 {1} 家", "{0} 等 {1} 家",
]

# 多标的取到之后的状态行。这一行不带币种 —— 亿没有英文，而带上错单位比不带更糟。
BOARD_FETCHED = [
    "{0} companies over {1} trading days ({2} to {3})",
    "{0} Unternehmen über {1} Handelstage ({2} bis {3})",
    "{0} empresas en {1} sesiones ({2} a {3})",
    "{0} entreprises sur {1} séances ({2} à {3})",
    "{0} aziende su {1} sedute ({2} - {3})",
    "{0} spółek przez {1} sesji ({2} - {3})",
    "{0} empresas em {1} pregões ({2} a {3})",
    "{0} firem za {1} obchodních dnů ({2} až {3})",
    "{0} şirket, {1} işlem günü ({2} - {3})",
    "{0} компаний за {1} торговых дней ({2} — {3})",
    "{0} 社、{1} 営業日（{2} から {3}）",
    "{0}개 기업, {1}거래일({2}~{3})",
    "已取到 {0} 家公司、{1} 個交易日，{2} 至 {3}",
    "已取到 {0} 家公司、{1} 个交易日，{2} 至 {3}",
]

# 有几家在区间里根本算不出市值（最常见的是指数：它没有换手率）。
#
# 点名而不是只报数：读者要动手改的是「哪一家」，而画面少一条线恰恰是看不出少谁的。
# {0} 是家数，{1} 是逗号分隔的名字。
SKIPPED = [
    "Had no value inside the range, left out ({0}): {1}",
    "Ohne Marktwert im Zeitraum, weggelassen ({0}): {1}",
    "Sin valor en el rango, omitidas ({0}): {1}",
    "Sans valeur sur la période, non tracées ({0}) : {1}",
    "Senza valore nell'intervallo, escluse ({0}): {1}",
    "Brak wartości w zakresie, pominięte ({0}): {1}",
    "Sem valor no intervalo, deixadas de fora ({0}): {1}",
    "Bez hodnoty v rozsahu, vynechány ({0}): {1}",
    "Aralıkta değeri yok, çıkarıldı ({0}): {1}",
    "Нет капитализации в диапазоне, пропущено ({0}): {1}",
    "期間内に値がなく除外（{0} 件）: {1}",
    "구간에 값이 없어 제외({0}개): {1}",
    "區間內沒有市值、已略過（{0} 家）：{1}",
    "区间内没有市值、已略过（{0} 家）：{1}",
]

# 拒绝而不是截断 —— 六家公司照样能画、少三家也不报错，但那张图画的是没人选过的清单。
TOO_MANY = [
    "At most {0} companies can be compared; {1} are switched on",
    "Höchstens {0} Unternehmen lassen sich vergleichen; {1} sind eingeschaltet",
    "Se pueden comparar como máximo {0} empresas; {1} están activadas",
    "On peut comparer au plus {0} entreprises ; {1} sont sélectionnées",
    "Si possono confrontare al massimo {0} aziende; {1} sono attive",
    "Można porównać najwyżej {0} spółek; włączone są {1}",
    "No máximo {0} empresas podem ser comparadas; {1} estão ativadas",
    "Lze porovnat nejvýše {0} firem; zapnuto je {1}",
    "En fazla {0} şirket karşılaştırılabilir; {1} tanesi açık",
    "Можно сравнить не более {0} компаний; включено {1}",
    "比較できるのは最大 {0} 社です（現在 {1} 社が選択中）",
    "최대 {0}개 기업만 비교할 수 있습니다. 현재 {1}개가 켜져 있습니다",
    "最多同時比較 {0} 家公司，目前選了 {1} 家",
    "最多同时比较 {0} 家公司，目前选了 {1} 家",
]

# 清单里没有一家属于当前市场。清单本身是跨市场的（好几个榜要三家放一条轴上），
# 而市值是单一市场的口径 —— 所以不是错误，是「这一页现在没得画」。
NO_MARKET_PICKS = [
    "None of your list is on the {0} market",
    "Keine Auswahl aus deiner Liste liegt am Markt {0}",
    "Ninguna selección de tu lista está en el mercado {0}",
    "Aucun élément de votre liste n'est sur le marché {0}",
    "Nessuna scelta della tua lista è nel mercato {0}",
    "Żaden wybór z twojej listy nie jest na rynku {0}",
    "Nenhuma escolha da sua lista está no mercado {0}",
    "Žádná položka z tvého seznamu není na trhu {0}",
    "Listenizdeki hiçbir seçim {0} piyasasında değil",
    "Ни одного выбора из вашего списка на рынке {0}",
    "リストの選択肢は {0} 市場にありません",
    "목록의 어떤 항목도 {0} 시장에 없습니다",
    "清單裡沒有一家公司屬於 {0} 市場",
    "清单里没有一家公司属于 {0} 市场",
]

ROWS = [
    ("CapHistoryAxisLabel.Header", LABEL),
    ("CapHistoryAxisAbsolute", ABSOLUTE),
    ("CapHistoryAxisNormalized", NORMALIZED),
    ("CapHistoryRebasedUnit", REBASED_UNIT),
    ("CapHistoryAxisNote.Text", AXIS_NOTE),
    ("CapHistoryVsTitle", VS),
    ("CapHistoryCompareMany", MANY),
    ("CapHistoryBoardFetched", BOARD_FETCHED),
    ("CapHistorySkipped", SKIPPED),
    ("CapHistoryTooMany", TOO_MANY),
    ("CapHistoryNoMarketPicks", NO_MARKET_PICKS),
]


def entry(key, value):
    """One resw row, XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224: root node not found`
    — naming the root element and the project file, and saying nothing about the text
    that caused it.
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

        for key, values in ROWS:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values"
            lines.append(entry(key, values[at]))

        # Idempotent: drop a key of the same base name wherever it already sits, then
        # append. The optional suffix is matched so that renaming a key from `X` to
        # `X.Text` does not leave the old one behind, and `[^>]*` follows the name
        # because this file holds two entry shapes.
        for key, _ in ROWS:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        mark = text.rfind("</root>")
        assert mark > 0, f"{tag}: no </root>"

        text = text[:mark] + "".join(lines) + text[mark:]

        # Bytes, not text: read_text/write_text would normalise the line endings and
        # git would see the whole file rewritten.
        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
