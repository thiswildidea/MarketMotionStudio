# -*- coding: utf-8 -*-
r"""把「汇率走廊」这一页的 resw 键注入 14 份 Resources.resw。

第十二个页面的文案：导航名、标题、副标题、币种组下拉（标题 + 两项）、区间「最长」、
面板说明、口径说明、状态行、以及「区间太短」那条错误。

表头的两个量词不在这里：它们复用 `MarketCapUnitMonths`（个月）与 `AhPremiumUnitPairs`
（对）——两处都是同一个词、同一个意思，加两份新键只是给翻译多两条要维护的行。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`——
`port-ahpremium-resw.py` 里 `AhPremiumFetched` 就是在这里栽过：第一列写成了中文，
英文界面于是显示一整行中文状态。加键时先确认第一列是英文。

用法：python tools\port-fxcorridor-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 导航项、页面标题、以及无数据时舞台上的标题，共用一份：三处说的是同一件事。
NAV = [
    "Currency corridors", "Währungskorridore", "Corredores de divisas",
    "Couloirs de devises", "Corridoi valutari", "Korytarze walutowe",
    "Corredores de câmbio", "Měnové koridory", "Döviz koridorları",
    "Валютные коридоры", "為替コリドー", "환율 코리도",
    "匯率走廊", "汇率走廊",
]

PAGE = [
    # `.Content`, not `.Text`: a NavigationViewItem is a ContentControl, and the x:Uid loader
    # asks for the property the type actually has. Written as `.Text` the app does not start —
    # MainWindow's InitializeComponent throws, which is a crash on launch, not a blank label.
    ("NavFxCorridor.Content", NAV),

    ("FxCorridorPageTitle.Text", NAV),

    ("FxCorridorStageTitle", NAV),

    ("FxCorridorPageSubtitle.Text", [
        "Where each pair sits between the cheapest and the dearest it has been. Every pair is "
        "measured against its own range.",
        "Wo jedes Paar zwischen seinem billigsten und seinem teuersten Stand steht. Jedes Paar "
        "wird an der eigenen Spanne gemessen.",
        "Dónde está cada par entre lo más barato y lo más caro que ha estado. Cada par se mide "
        "contra su propio rango.",
        "Où se situe chaque paire entre le plus bas et le plus haut qu'elle a connus. Chaque "
        "paire est mesurée à sa propre fourchette.",
        "Dov'è ogni coppia tra il livello più basso e il più alto che ha avuto. Ogni coppia è "
        "misurata sul proprio intervallo.",
        "Gdzie każda para jest między najtańszym a najdroższym poziomem, na jakim była. Każda "
        "para jest mierzona własnym zakresem.",
        "Onde cada par está entre o mais barato e o mais caro que já esteve. Cada par é medido "
        "contra sua própria faixa.",
        "Kde se každý pár nachází mezi nejlevnější a nejdražší úrovní, na které byl. Každý pár "
        "se měří vlastním rozpětím.",
        "Her paritenin, gördüğü en ucuz ile en pahalı arasında nerede durduğu. Her parite kendi "
        "aralığına göre ölçülür.",
        "Где каждая пара находится между самым дешёвым и самым дорогим уровнем, на котором "
        "она бывала. Каждая пара измеряется по своему диапазону.",
        "各ペアがこれまでの最安値と最高値の間のどこにいるか。すべてのペアは自分のレンジで"
        "測ります。",
        "각 통화쌍이 지금까지의 최저와 최고 사이 어디에 있는지. 모든 쌍은 자기 구간으로 "
        "측정됩니다.",
        "每一組貨幣在自己最便宜與最貴之間走到哪裡。每一組都用自己的區間來量。",
        "每一组货币在自己最便宜与最贵之间走到哪里。每一组都用自己的区间来量。"]),

    ("FxCorridorList.Header", [
        "Pairs", "Paare", "Pares", "Paires", "Coppie", "Pary", "Pares", "Páry", "Pariteler",
        "Пары", "通貨ペア", "통화쌍", "貨幣組", "货币组"]),

    ("FxCorridorListCny", [
        "Renminbi pairs", "Renminbi-Paare", "Pares del renminbi", "Paires du renminbi",
        "Coppie del renminbi", "Pary renminbi", "Pares do renminbi", "Páry renminbi",
        "Renminbi pariteleri", "Пары с юанем", "人民元のペア", "위안화 쌍",
        "人民幣匯率", "人民币汇率"]),

    ("FxCorridorListCrosses", [
        "Major crosses", "Wichtige Crosses", "Cruces principales", "Principaux cross",
        "Cross principali", "Główne crossy", "Principais cruzamentos", "Hlavní crosy",
        "Ana çaprazlar", "Основные кроссы", "主要クロス", "주요 크로스",
        "主要交叉盤", "主要交叉盘"]),

    ("FxCorridorRangeMax", [
        "Longest", "Längster", "Más largo", "Le plus long", "Il più lungo", "Najdłuższy",
        "Mais longo", "Nejdelší", "En uzun", "Самый длинный", "最長", "가장 긴",
        "最長", "最长"]),

    # No placeholder in it: the list is whatever the chosen group holds, and a card that counts
    # rows before the fetch has run is a card that has to be rewritten on every fetch — and one
    # read with `Strings.Get` shows a literal "{0}", which two pages here have already done.
    # A TextBlock's x:Uid asks for `.Text`, so the key carries it even though nothing in code
    # reads it — a bare key here is a blank card and a verify failure, not a fallback.
    ("FxCorridorNote.Text", [
        "One row per pair. The row is the corridor — the floor and the ceiling the pair has "
        "traded between — and the marker is where the rate is now. Both are printed under each "
        "row, because a narrow corridor and a wide one look alike on the frame.",
        "Eine Zeile je Paar. Die Zeile ist der Korridor — der tiefste und der höchste Kurs, "
        "zwischen denen das Paar gehandelt hat — und die Markierung ist der Kurs von heute. "
        "Beide stehen unter jeder Zeile, weil ein enger und ein weiter Korridor im Bild gleich "
        "aussehen.",
        "Una fila por par. La fila es el corredor — el suelo y el techo entre los que ha "
        "cotizado — y la marca es dónde está la cotización ahora. Ambos se imprimen bajo cada "
        "fila, porque un corredor estrecho y uno ancho se ven igual en el fotograma.",
        "Une ligne par paire. La ligne est le couloir — le plancher et le plafond entre "
        "lesquels la paire a coté — et le repère est le cours actuel. Les deux sont imprimés "
        "sous chaque ligne, car un couloir étroit et un couloir large se ressemblent à l'image.",
        "Una riga per coppia. La riga è il corridoio — il pavimento e il soffitto fra cui la "
        "coppia ha quotato — e l'indicatore è dove sta il cambio ora. Entrambi sono scritti "
        "sotto ogni riga, perché un corridoio stretto e uno largo si vedono allo stesso modo.",
        "Jeden wiersz na parę. Wiersz to korytarz — najniższy i najwyższy kurs, między którymi "
        "para się poruszała — a znacznik to kurs teraz. Oba są wypisane pod każdym wierszem, "
        "bo wąski i szeroki korytarz wyglądają na obrazie tak samo.",
        "Uma linha por par. A linha é o corredor — o piso e o teto entre os quais o par negociou "
        "— e o marcador é onde está a cotação agora. Os dois aparecem sob cada linha, porque um "
        "corredor estreito e um largo se parecem no quadro.",
        "Jeden řádek na pár. Řádek je koridor — nejnižší a nejvyšší kurz, mezi kterými se pár "
        "obchodoval — a značka je, kde je kurz teď. Obě hodnoty jsou pod každým řádkem, protože "
        "úzký a široký koridor vypadají na obrázku stejně.",
        "Her parite için bir satır. Satır koridorun kendisidir — paritenin arasında işlem "
        "gördüğü taban ve tavan — işaret ise kurun şu anki yeri. İkisi de her satırın altında "
        "yazılır, çünkü dar bir koridorla geniş bir koridor görüntüde aynı görünür.",
        "Одна строка на пару. Строка — это коридор: минимум и максимум, между которыми пара "
        "торговалась, а маркер — где курс сейчас. Оба значения напечатаны под строкой, потому "
        "что узкий и широкий коридор выглядят на кадре одинаково.",
        "通貨ペアごとに1行。行そのものがコリドー（そのペアが動いた下限と上限）で、マーカーは"
        "現在のレートです。下限と上限は各行の下に印刷されます。細いコリドーと広いコリドーは"
        "画面上では見分けがつかないからです。",
        "통화쌍마다 한 줄. 줄 자체가 그 쌍이 오간 하한과 상한인 코리도이고, 표식은 현재 "
        "환율입니다. 하한과 상한은 각 줄 아래에 적힙니다. 좁은 코리도와 넓은 코리도는 화면에서 "
        "구분되지 않기 때문입니다.",
        "每一組貨幣一行。那一行的本身就是走廊——這組貨幣走過的下限與上限——游標是現在的匯率。"
        "下限與上限印在每一行的下方，因為窄的走廊和寬的走廊在畫面上看起來是一樣的。",
        "每一组货币一行。那一行的本身就是走廊——这组货币走过的下限与上限——游标是现在的汇率。"
        "下限与上限印在每一行的下方，因为窄的走廊和宽的走廊在画面上看起来是一样的。"]),

    ("FxCorridorMethodNote.Text", [
        "Monthly bars, unadjusted — a currency has no dividend or split to adjust for. The "
        "corridor is the lowest low and the highest high **so far**, so it widens as the months "
        "pass and a pair at 100% is at the dearest it has been in the range, not at a limit. "
        "Coverage differs: USD/CNY reaches back to 2005, the other renminbi pairs to 2016.",
        "Monatskerzen, nicht bereinigt — eine Währung hat keine Dividende und keinen Split. Der "
        "Korridor ist das bisherige Tief und das bisherige Hoch, er weitet sich also mit den "
        "Monaten, und ein Paar bei 100% ist so teuer wie nie in der Spanne, nicht an einer "
        "Grenze. Die Reichweite ist unterschiedlich: USD/CNY reicht bis 2005 zurück, die anderen "
        "Renminbi-Paare bis 2016.",
        "Velas mensuales, sin ajustar — una divisa no tiene dividendo ni split que ajustar. El "
        "corredor es el mínimo y el máximo **hasta ahora**, así que se ensancha con los meses, "
        "y un par al 100% está en lo más caro que ha estado, no en un límite. La cobertura "
        "varía: USD/CNY llega hasta 2005, los demás pares del renminbi hasta 2016.",
        "Bougies mensuelles, non ajustées — une devise n'a ni dividende ni split à ajuster. Le "
        "couloir est le plus bas et le plus haut **jusqu'ici**, il s'élargit donc avec les mois, "
        "et une paire à 100 % est au plus cher qu'elle ait été, pas à une limite. La couverture "
        "diffère : USD/CNY remonte à 2005, les autres paires du renminbi à 2016.",
        "Candele mensili, non rettificate — una valuta non ha dividendi né frazionamenti da "
        "rettificare. Il corridoio è il minimo e il massimo **finora**, quindi si allarga con i "
        "mesi, e una coppia al 100% è al livello più caro che abbia avuto, non a un limite. La "
        "copertura differisce: USD/CNY arriva al 2005, le altre coppie del renminbi al 2016.",
        "Świece miesięczne, bez korekty — waluta nie ma dywidendy ani podziału do skorygowania. "
        "Korytarz to najniższe i najwyższe **dotąd**, więc rozszerza się wraz z miesiącami, a "
        "para na 100% jest najdroższa, jaka była w tym zakresie, a nie przy jakimś limicie. "
        "Zasięg danych jest różny: USD/CNY sięga 2005, pozostałe pary renminbi — 2016.",
        "Velas mensais, sem ajuste — uma moeda não tem dividendo nem desdobramento a ajustar. O "
        "corredor é a mínima e a máxima **até agora**, então ele se alarga com os meses, e um "
        "par a 100% está no mais caro que já esteve, não em um limite. A cobertura varia: "
        "USD/CNY chega a 2005, os outros pares do renminbi a 2016.",
        "Měsíční svíčky, bez úprav — měna nemá dividendu ani rozdělení, které by se upravovalo. "
        "Koridor je nejnižší a nejvyšší **dosud**, takže se s měsíci rozšiřuje, a pár na 100% je "
        "nejdráž, jak kdy v rozpětí byl, ne na limitu. Pokrytí se liší: USD/CNY sahá do roku "
        "2005, ostatní páry renminbi do roku 2016.",
        "Aylık mumlar, düzeltilmemiş — bir para biriminin düzeltilcek temettüsü veya bölünmesi "
        "yok. Koridor, **şimdiye kadarki** en düşük ve en yüksektir, bu yüzden aylar geçtikçe "
        "genişler ve %100'deki bir parite bir sınırda değil, aralıkta gördüğü en pahalı yerdedir. "
        "Kapsam farklı: USD/CNY 2005'e, diğer renminbi pariteleri 2016'ya kadar uzanır.",
        "Месячные бары, без корректировки — у валюты нет ни дивиденда, ни сплита, которые нужно "
        "было бы корректировать. Коридор — это минимум и максимум **на данный момент**, поэтому "
        "он расширяется с месяцами, и пара на 100% находится на самом дорогом уровне в диапазоне, "
        "а не на границе. Охват различается: USD/CNY уходит в 2005, остальные пары с юанем — "
        "в 2016.",
        "月足、調整なし — 通貨に配当も分割もありません。コリドーは**これまでの**最安値と"
        "最高値なので、月が進むほど広がり、100%のペアは上限に達したのではなく、その範囲で"
        "最も高かった位置にいます。データの範囲はペアごとに異なります。USD/CNYは2005年まで、"
        "他の人民元ペアは2016年までです。",
        "월별 봉, 조정 없음 — 통화에는 조정할 배당이나 분할이 없습니다. 코리도는 **지금까지의** "
        "최저와 최고이므로 달이 지날수록 넓어지고, 100%인 쌍은 한계에 닿은 것이 아니라 그 구간에서 "
        "가장 비쌌던 위치에 있습니다. 자료 범위는 쌍마다 다릅니다. USD/CNY는 2005년까지, "
        "다른 위안화 쌍은 2016년까지입니다.",
        "月線，不調整——貨幣沒有股息也沒有拆股需要調整。走廊是**截至目前**的最低與最高，"
        "所以它隨月份推進而變寬；一組貨幣走到 100% 是它在這段區間裡最貴的位置，不是撞到上限。"
        "資料起點各組不同：USD/CNY 可回溯到 2005 年，其他人民幣組別到 2016 年。",
        "月线，不调整——货币没有股息也没有拆股需要调整。走廊是**截至目前**的最低与最高，"
        "所以它随月份推进而变宽；一组货币走到 100% 是它在这段区间里最贵的位置，不是撞到上限。"
        "数据起点各组不同：USD/CNY 可回溯到 2005 年，其他人民币组别到 2016 年。"]),

    # Six placeholders: pairs, months, the pair highest in its own corridor and where, then the
    # same for the lowest. Formatted, not fetched with `Strings.Get` — see FxCorridorNote.
    ("FxCorridorFetched", [
        "{0} pairs · {1} months · highest in its corridor {2} at {3} · lowest {4} at {5}",
        "{0} Paare · {1} Monate · am höchsten im eigenen Korridor {2} bei {3} · am niedrigsten "
        "{4} bei {5}",
        "{0} pares · {1} meses · el más alto en su corredor {2} en {3} · el más bajo {4} en {5}",
        "{0} paires · {1} mois · le plus haut dans son couloir {2} à {3} · le plus bas {4} à {5}",
        "{0} coppie · {1} mesi · la più alta nel proprio corridoio {2} a {3} · la più bassa "
        "{4} a {5}",
        "{0} par · {1} miesięcy · najwyżej w swoim korytarzu {2} przy {3} · najniżej {4} przy {5}",
        "{0} pares · {1} meses · mais alto no próprio corredor {2} em {3} · mais baixo {4} em {5}",
        "{0} párů · {1} měsíců · nejvýše ve vlastním koridoru {2} na {3} · nejníže {4} na {5}",
        "{0} parite · {1} ay · kendi koridorunda en yüksek {2}, {3} · en düşük {4}, {5}",
        "{0} пар · {1} месяцев · выше всего в своём коридоре {2} на {3} · ниже всего {4} на {5}",
        "{0} ペア · {1} か月 · 自分のコリドーで最も高いのは {2}（{3}） · 最も低いのは {4}（{5}）",
        "{0}개 쌍 · {1}개월 · 자기 코리도에서 가장 높은 쌍 {2} {3} · 가장 낮은 쌍 {4} {5}",
        "{0} 組貨幣 · {1} 個月 · 在自己走廊裡位置最高的是 {2}，{3} · 最低的是 {4}，{5}",
        "{0} 组货币 · {1} 个月 · 在自己走廊里位置最高的是 {2}，{3} · 最低的是 {4}，{5}"]),

    ("FxCorridorTooFew", [
        "Too few months in this range for a corridor. Try a longer range.",
        "Zu wenige Monate in diesem Zeitraum für einen Korridor. Versuchen Sie einen längeren.",
        "Demasiados pocos meses en este periodo para un corredor. Pruebe con un periodo más largo.",
        "Trop peu de mois dans cette période pour un couloir. Essayez une période plus longue.",
        "Troppi pochi mesi in questo periodo per un corridoio. Provi un periodo più lungo.",
        "Za mało miesięcy w tym okresie, by utworzyć korytarz. Spróbuj dłuższego okresu.",
        "Meses demaisados poucos neste período para um corredor. Tente um período mais longo.",
        "V tomto období je příliš málo měsíců pro koridor. Zkuste delší období.",
        "Bu aralıkta bir koridor için çok az ay var. Daha uzun bir aralık deneyin.",
        "В этом периоде слишком мало месяцев для коридора. Возьмите период длиннее.",
        "この期間では月数が少なすぎてコリドーになりません。もっと長い期間をお試しください。",
        "이 기간은 코리도를 만들기에 달 수가 너무 적습니다. 더 긴 기간을 선택하세요.",
        "這段區間的月份太少，撐不起一條走廊。換長一點的區間試試。",
        "这段区间的月份太少，撑不起一条走廊。换长一点的区间试试。"]),
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

        for key, values in PAGE:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in PAGE:
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
