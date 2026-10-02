# -*- coding: utf-8 -*-
r"""把「汇率走廊」一章插进 14 份帮助文档。

位置**按章节序号**定，不按标题文字：新章插在「极端交易日」之后、「收益矩阵」之前，
因为导航里这三项挨着（AH 溢价 → 极端交易日 → 汇率走廊）。14 份文档的章节数与顺序
必须相同，由 verify 脚本另行检查。

文件是 UTF-8 **带 BOM** + LF：`read_bytes().decode('utf-8-sig')` 读，写回时自己补 BOM。
`utf-8-sig` 只吃掉一个 BOM，文件里若已经叠了两个，要用 `lstrip('\ufeff')` 兜住。

幂等：标题已存在就整章重写。**改页面行为就要回来改这里的 BODIES** —— 市值榜那一章
曾经在榜单改了两次之后仍写着旧理由，见 `port-marketcap-help.py` 的说明。

用法：python tools\port-fxcorridor-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 插在第 9 章「极端交易日」之后（0 基下标 8），第 10 章「收益矩阵」之前。
AFTER = 8

TITLES = {
    "zh-Hans": "汇率走廊",
    "zh-Hant": "匯率走廊",
    "en-US": "Currency corridors",
    "ja": "為替コリドー",
    "ko": "환율 코리도",
    "de": "Währungskorridore",
    "fr": "Couloirs de devises",
    "it": "Corridoi valutari",
    "es": "Corredores de divisas",
    "pt-BR": "Corredores de câmbio",
    "pl": "Korytarze walutowe",
    "cs": "Měnové koridory",
    "ru": "Валютные коридоры",
    "tr": "Döviz koridorları",
}

BODIES = {
    "zh-Hans": """一组货币一行，**行本身就是那条走廊**：一头是这组货币在所选区间里到过的最便宜，另一头是
最贵，游标是它现在的汇率。所以它和别的榜不一样——别处条形的长度是「有多少」，这里的行在每一帧
里都占满整行，动的是游标，以及走廊本身。

- **走廊会变宽。** 上下沿是**截至目前**的最低与最高，不是整段区间的。月份推进，走出新低或新高，
  走廊就被撑开一点。走到 100% 是说它正处在自己到过的最贵位置，不是撞上了什么上限。
- **每一组都按自己的区间量。** 157.92 的 USD/JPY 和 1.1245 的 EUR/USD 不在同一把尺子上；先归一
  化，六组才站得进同一块画面。代价是窄走廊和宽走廊看起来一样，所以行下方印着两端的数字。
- **月线，不调整。** 货币没有股息也没有拆股要调整，取数走的是 AH 页那条不复权的路径。
- **起点各组不同，所以分成两组来选**：USD/CNY 可回溯到 2005 年，另外五组人民币货币对到 2016 年；
  主要交叉盘六组都从 2005 年 7 月起、各有 325 个月。混在一张画面上，读出来的是数据源何时开始
  报价，而不是货币怎么样。
- **这一页不看市场设置**：货币对不属于任何一个股票市场，切到港股或美股它还是这些对。
- 区间最长那档受数据源月线覆盖限制，约二十年；不足 12 个月会拒绝取数——那不是走廊，是几周的
  波动。
""",
    "zh-Hant": """一組貨幣一行，**行本身就是那條走廊**：一頭是這組貨幣在所選區間裡到過的最便宜，另一頭是
最貴，游標是它現在的匯率。所以它和別的榜不一樣——別處條形的長度是「有多少」，這裡的行在每一幀
裡都佔滿整行，動的是游標，以及走廊本身。

- **走廊會變寬。** 上下沿是**截至目前**的最低與最高，不是整段區間的。月份推進，走出新低或新高，
  走廊就被撐開一點。走到 100% 是說它正處在自己到過的最貴位置，不是撞上了什麼上限。
- **每一組都按自己的區間量。** 157.92 的 USD/JPY 和 1.1245 的 EUR/USD 不在同一把尺子上；先歸一
  化，六組才站得進同一塊畫面。代價是窄走廊和寬走廊看起來一樣，所以行下方印著兩端的數字。
- **月線，不調整。** 貨幣沒有股息也沒有拆股要調整，取數走的是 AH 頁那條不復權的路徑。
- **起點各組不同，所以分成兩組來選**：USD/CNY 可回溯到 2005 年，另外五組人民幣貨幣對到 2016 年；
  主要交叉盤六組都從 2005 年 7 月起、各有 325 個月。混在一張畫面上，讀出來的是資料源何時開始
  報價，而不是貨幣怎麼樣。
- **這一頁不看市場設定**：貨幣對不屬於任何一個股票市場，切到港股或美股它還是這些對。
- 區間最長那檔受資料源月線覆蓋限制，約二十年；不足 12 個月會拒絕取數——那不是走廊，是幾週的
  波動。
""",
    "en-US": """One row per pair, and **the row is the corridor itself**: one end is the cheapest the pair has
been in the chosen span, the other the dearest, and the marker is where the rate is now. So this
board is not like the others — elsewhere a bar's length is *how much*, and here the row is full
width in every frame; what moves is the marker, and the corridor around it.

- **The corridor widens.** Its walls are the lowest low and the highest high **so far**, not over
  the whole span. A month that goes further than any month before it pushes one of them outwards,
  and a pair sitting at 100% is at the dearest it has ever been — not at a limit.
- **Every pair is measured against its own range.** 157.92 on USD/JPY and 1.1245 on EUR/USD are not
  two points on one scale; normalising each corridor is what lets six pairs stand on one board. The
  cost is that a narrow corridor and a wide one look alike, which is why the floor and the ceiling
  are printed under every row.
- **Monthly bars, unadjusted.** A currency has no dividend and no split to adjust for, and the page
  takes the same raw path through the source that the A+H page takes.
- **Coverage differs, which is why the two lists are separate**: USD/CNY reaches back to 2005, the
  other five renminbi pairs to 2016; the major crosses all begin in 2005-07 and carry 325 months
  each. Put them on one board and what you are reading is when the source started quoting each pair.
- **The market setting does not apply here**: a currency pair belongs to no stock market, and the
  board is the same whichever one is in force.
- The longest span is about twenty years, which is the source's monthly coverage; a range shorter
  than twelve months is refused — that is a few weeks of movement, not a corridor.
""",
    "ja": """通貨ペアごとに1行、そして**その行自体がコリドーです**：一方の端はそのペアが選んだ区間で
最も安かった水準、もう一方は最も高かった水準、マーカーは現在のレートです。したがってこの面は
他の表とは違います——他の場所ではバーの長さが「どれだけ」ですが、ここでは行は毎フレーム全幅で、
動くのはマーカーとその周りのコリドーです。

- **コリドーは広がります。** 上下の壁は区間全体ではなく**これまでの**最安値と最高値です。それ
  までのどの月より外へ出た月が、壁のどちらかを押し広げます。100%にあるペアは、これまでで最も
  高かった位置にいるのであって、上限に達したわけではありません。
- **どのペアも自分のレンジで測ります。** USD/JPY の 157.92 と EUR/USD の 1.1245 は同じ物差しの
  上にある点ではありません。それぞれを正規化するからこそ六つのペアが一つの画面に並びます。その
  代償として狭いコリドーと広いコリドーが同じに見えるため、下限と上限を各行の下に印刷しています。
- **月足、調整なし。** 通貨に配当も分割もありません。取数は AH ページと同じ、調整なしの経路を
  通ります。
- **データの起点がペアごとに違うので、リストは二つに分かれています**：USD/CNY は 2005 年まで、
  他の人民元ペアは 2016 年まで。主要クロスは六つとも 2005 年 7 月からで、それぞれ 325 か月です。
  一つの画面に混ぜると、読むことになるのは貨幣の姿ではなく、データ源がいつから各ペアを載せたか
  という話になります。
- **市場設定はこのページに効きません**：通貨ペアはどの株式市場にも属しません。どの市場が選ばれ
  ていても同じ面です。
- 最長の区間は約二十年で、これはデータ源の月足の範囲です。12 か月未満の区間は拒否されます——
  それはコリドーではなく、数週間のかたよりです。
""",
    "ko": """통화쌍마다 한 줄, 그리고 **그 줄 자체가 코리도입니다**: 한쪽 끝은 그 쌍이 선택한 구간에서
가장 쌌던 수준, 다른 쪽은 가장 비쌌던 수준이고, 표식은 현재 환율입니다. 그래서 이 판은 다른 판과
다릅니다—다른 곳에서 막대의 길이는 '얼마나'지만, 여기서는 줄이 매 프레임 전체 너비이고 움직이는
것은 표식과 그 주위의 코리도입니다.

- **코리도는 넓어집니다.** 위아래 벽은 구간 전체가 아니라 **지금까지의** 최저와 최고입니다. 이전
  어떤 달보다 멀리 간 달이 벽 중 하나를 밀어냅니다. 100%에 있는 쌍은 지금까지 가장 비쌌던 위치에
  있는 것이지, 한계에 닿은 것이 아닙니다.
- **모든 쌍은 자기 구간으로 측정됩니다.** USD/JPY의 157.92와 EUR/USD의 1.1245는 같은 자 위의 점이
  아닙니다. 각각을 정규화하기 때문에 여섯 쌍이 한 화면에 설 수 있습니다. 대가로 좁은 코리도와 넓은
  코리도가 같아 보이므로, 하한과 상한을 각 줄 아래에 적어 둡니다.
- **월별 봉, 조정 없음.** 통화에는 배당도 분할도 없습니다. 자료는 AH 페이지와 같은 조정 없는 경로로
  가져옵니다.
- **자료 시작점이 쌍마다 달라 목록이 둘로 나뉩니다**: USD/CNY는 2005년까지, 다른 위안화 쌍은
  2016년까지입니다. 주요 크로스는 여섯 개 모두 2005년 7월부터이며 각각 325개월입니다. 한 화면에
  섞으면 읽게 되는 것은 통화의 모습이 아니라 자료원이 각 쌍을 언제부터 실었는가입니다.
- **시장 설정은 이 페이지에 적용되지 않습니다**: 통화쌍은 어느 주식시장에도 속하지 않습니다. 어떤
  시장이든 같은 판입니다.
- 가장 긴 구간은 약 20년으로, 자료원의 월별 범위입니다. 12개월보다 짧은 구간은 거절됩니다—그것은
  코리도가 아니라 몇 주간의 흔들림입니다.
""",
    "de": """Eine Zeile je Paar, und **die Zeile ist der Korridor selbst**: ein Ende ist der billigste Stand,
den das Paar in der gewählten Spanne hatte, das andere der teuerste, und die Markierung ist der Kurs
von heute. Dieses Tableau ist also anders als die anderen — anderswo ist die Länge eines Balkens
*wieviel*, hier füllt die Zeile in jedem Bild die ganze Breite, und es bewegen sich die Markierung
und der Korridor um sie herum.

- **Der Korridor weitet sich.** Seine Wände sind das bisherige Tief und das bisherige Hoch, nicht
  die der ganzen Spanne. Ein Monat, der weiter geht als jeder Monat zuvor, drückt eine der beiden
  nach außen, und ein Paar bei 100% ist so teuer wie nie zuvor — nicht an einer Grenze.
- **Jedes Paar wird an der eigenen Spanne gemessen.** 157,92 bei USD/JPY und 1,1245 bei EUR/USD
  sind keine zwei Punkte auf einer Skala; erst die Normierung lässt sechs Paare auf einem Bild
  stehen. Der Preis dafür: ein enger und ein weiter Korridor sehen gleich aus — darum stehen beide
  Enden unter jeder Zeile.
- **Monatskerzen, nicht bereinigt.** Eine Währung hat keine Dividende und keinen Split, und die Seite
  nimmt denselben unbereinigten Weg durch die Quelle den die A+H-Seite nimmt.
- **Die Reichweite ist unterschiedlich, darum sind es zwei Listen**: USD/CNY reicht bis 2005, die
  anderen fünf Renminbi-Paare bis 2016; die wichtigen Crosses beginnen alle 2005-07 und tragen 325
  Monate. Auf einem Tableau zusammen läse man, wann die Quelle welches Paar zu notieren begann.
- **Die Markteinstellung gilt hier nicht**: ein Währungspaar gehört zu keiner Börse, und das Tableau
  ist dasselbe, welcher Markt auch gilt.
- Die längste Spanne ist etwa zwanzig Jahre — die Reichweite der Monatsreihe der Quelle. Weniger als
  zwölf Monate werden abgelehnt: das sind ein paar Wochen Bewegung, kein Korridor.
""",
    "fr": """Une ligne par paire, et **la ligne est le couloir lui-même** : une extrémité est le niveau le
plus bas que la paire a connu dans la période choisie, l'autre le plus haut, et le repère est le
cours actuel. Ce tableau n'est donc pas comme les autres — ailleurs la longueur d'une barre dit
*combien*, ici la ligne occupe toute la largeur à chaque image, et ce qui bouge est le repère, avec
le couloir autour de lui.

- **Le couloir s'élargit.** Ses murs sont le plus bas et le plus haut **jusqu'ici**, pas ceux de
  toute la période. Un mois qui va plus loin que tous ceux d'avant pousse l'un des deux vers
  l'extérieur, et une paire à 100 % est au plus cher qu'elle ait jamais été — pas à une limite.
- **Chaque paire est mesurée à sa propre fourchette.** 157,92 sur USD/JPY et 1,1245 sur EUR/USD ne
  sont pas deux points d'une même échelle ; c'est la normalisation qui permet à six paires de tenir
  sur une image. Le prix à payer : un couloir étroit et un couloir large se ressemblent — d'où les
  deux bornes imprimées sous chaque ligne.
- **Bougies mensuelles, non ajustées.** Une devise n'a ni dividende ni split à ajuster, et la page
  prend le même chemin brut dans la source que la page A+H.
- **La couverture diffère, et c'est pourquoi il y a deux listes** : USD/CNY remonte à 2005, les cinq
  autres paires du renminbi à 2016 ; les grands cross commencent tous en 2005-07 et portent 325 mois.
  Sur un seul tableau, on lirait la date à laquelle la source a commencé à coter chaque paire.
- **Le réglage de marché ne s'applique pas ici** : une paire de devises n'appartient à aucune Bourse,
  et le tableau est le même quel que soit le marché en vigueur.
- La période la plus longue est d'environ vingt ans, la couverture mensuelle de la source ; moins de
  douze mois est refusé — c'est quelques semaines de mouvement, pas un couloir.
""",
    "it": """Una riga per coppia, e **la riga è il corridoio stesso**: un'estremità è il livello più basso
che la coppia ha avuto nel periodo scelto, l'altra il più alto, e l'indicatore è il cambio di oggi.
Questo tabellone non è come gli altri — altrove la lunghezza di una barra dice *quanto*, qui la riga
occupa tutta la larghezza in ogni fotogramma, e a muoversi sono l'indicatore e il corridoio intorno.

- **Il corridoio si allarga.** Le sue pareti sono il minimo e il massimo **finora**, non quelli di
  tutto il periodo. Un mese che va oltre tutti i precedenti spinge una delle due verso l'esterno, e
  una coppia al 100% è al livello più caro che abbia mai avuto — non a un limite.
- **Ogni coppia è misurata sul proprio intervallo.** 157,92 su USD/JPY e 1,1245 su EUR/USD non sono
  due punti di una stessa scala; è la normalizzazione che permette a sei coppie di stare su un
  quadro. Il prezzo da pagare è che un corridoio stretto e uno largo si vedono allo stesso modo, e
  per questo i due estremi sono scritti sotto ogni riga.
- **Candele mensili, non rettificate.** Una valuta non ha dividendi né frazionamenti da rettificare,
  e la pagina prende lo stesso percorso grezzo nella fonte che prende la pagina A+H.
- **La copertura differisce, ed è per questo che le liste sono due**: USD/CNY arriva al 2005, le
  altre cinque coppie del renminbi al 2016; i principali cross cominciano tutti nel 2005-07 e portano
  325 mesi. Su un tabellone solo si leggerebbe quando la fonte ha iniziato a quotare ogni coppia.
- **L'impostazione di mercato non vale qui**: una coppia di valute non appartiene a nessuna Borsa, e
  il tabellone è lo stesso qualunque sia il mercato in vigore.
- Il periodo più lungo è di circa vent'anni, la copertura mensile della fonte; meno di dodici mesi
  viene rifiutato — sono poche settimane di movimento, non un corridoio.
""",
    "es": """Una fila por par, y **la fila es el corredor mismo**: un extremo es el nivel más bajo que el par
ha tenido en el periodo elegido, el otro el más alto, y la marca es la cotización de hoy. Este
tablero no es como los demás — en los demás la longitud de una barra dice *cuánto*, aquí la fila
ocupa todo el ancho en cada fotograma, y lo que se mueve es la marca, junto con el corredor.

- **El corredor se ensancha.** Sus paredes son el mínimo y el máximo **hasta ahora**, no los de todo
  el periodo. Un mes que va más lejos que todos los anteriores empuja una de las dos hacia afuera, y
  un par al 100% está en lo más caro que ha estado nunca — no en un límite.
- **Cada par se mide contra su propio rango.** 157,92 en USD/JPY y 1,1245 en EUR/USD no son dos
  puntos de una misma escala; es la normalización la que permite que seis pares quepan en un cuadro.
  El precio es que un corredor estrecho y uno ancho se ven igual, y por eso ambos extremos se
  imprimen bajo cada fila.
- **Velas mensuales, sin ajustar.** Una divisa no tiene dividendo ni split que ajustar, y la página
  toma el mismo camino en crudo por la fuente que toma la página A+H.
- **La cobertura difiere, y por eso hay dos listas**: USD/CNY llega hasta 2005, los otros cinco
  pares del renminbi hasta 2016; los principales cruces empiezan todos en 2005-07 y traen 325 meses.
  En un solo tablero se leería cuándo empezó la fuente a cotizar cada par.
- **El ajuste de mercado no aplica aquí**: un par de divisas no pertenece a ninguna bolsa, y el
  tablero es el mismo sea cual sea el mercado en vigor.
- El periodo más largo es de unos veinte años, la cobertura mensual de la fuente; menos de doce meses
  se rechaza — son unas semanas de movimiento, no un corredor.
""",
    "pt-BR": """Uma linha por par, e **a linha é o corredor em si**: uma ponta é o nível mais baixo que o par
teve no período escolhido, a outra o mais alto, e o marcador é a cotação de hoje. Este quadro não é
como os outros — nos outros o comprimento de uma barra diz *quanto*, aqui a linha ocupa toda a
largura em cada quadro, e o que se move é o marcador, junto com o corredor.

- **O corredor se alarga.** Suas paredes são a mínima e a máxima **até agora**, não as de todo o
  período. Um mês que vai além de todos os anteriores empurra uma das duas para fora, e um par a
  100% está no mais caro que já esteve — não em um limite.
- **Cada par é medido contra a própria faixa.** 157,92 em USD/JPY e 1,1245 em EUR/USD não são dois
  pontos de uma mesma escala; é a normalização que permite que seis pares caibam num quadro. O preço
  é que um corredor estreito e um largo se parecem, e por isso os dois extremos são impressos sob
  cada linha.
- **Velas mensais, sem ajuste.** Uma moeda não tem dividendo nem desdobramento a ajustar, e a página
  toma o mesmo caminho bruto na fonte que a página A+H.
- **A cobertura difere, e por isso há duas listas**: USD/CNY chega a 2005, os outros cinco pares do
  renminbi a 2016; os principais cruzamentos começam todos em 2005-07 e trazem 325 meses. Num quadro
  só, ler-se-ia quando a fonte começou a cotar cada par.
- **A configuração de mercado não se aplica aqui**: um par de moedas não pertence a nenhuma bolsa, e
  o quadro é o mesmo seja qual for o mercado em vigor.
- O período mais longo é de cerca de vinte anos, a cobertura mensal da fonte; menos de doze meses é
  recusado — são algumas semanas de movimento, não um corredor.
""",
    "pl": """Jeden wiersz na parę, i **ten wiersz jest korytarzem**: jeden koniec to najniższy poziom, na
jakim para była w wybranym okresie, drugi — najwyższy, a znacznik to kurs z dziś. Ta tablica nie jest
więc jak inne — gdzie indziej długość słupka mówi *ile*, tu wiersz w każdej klatce zajmuje całą
szerokość, a porusza się znacznik wraz z korytarzem wokół niego.

- **Korytarz się rozszerza.** Jego ściany to najniższe i najwyższe **dotąd**, nie w całym okresie.
  Miesiąc, który wyjdzie dalej niż wszystkie wcześniejsze, wypycha jedną ze ścian, a para na 100%
  jest najdroższa, jaka kiedykolwiek była — nie przy jakimś limicie.
- **Każda para mierzona jest własnym zakresem.** 157,92 na USD/JPY i 1,1245 na EUR/USD to nie dwa
  punkty na jednej skali; to normalizacja pozwala sześciu parom stanąć na jednym obrazie. Ceną jest
  to, że wąski i szeroki korytarz wyglądają tak samo — dlatego obie wartości są wypisane pod każdym
  wierszem.
- **Świece miesięczne, bez korekty.** Waluta nie ma dywidendy ani podziału do skorygowania, a strona
  idzie tą samą surową ścieżką do źródła co strona A+H.
- **Zasięg danych jest różny, dlatego są dwie listy**: USD/CNY sięga 2005, pozostałe pięć par
  renminbi — 2016; główne crossy zaczynają się wszystkie w 2005-07 i mają po 325 miesięcy. Na jednej
  tablicy czytałoby się, od kiedy źródło zaczęło notować każdą parę.
- **Ustawienie rynku tu nie działa**: para walutowa nie należy do żadnej giełdy, a tablica jest ta
  sama niezależnie od wybranego rynku.
- Najdłuższy okres to około dwudziestu lat — tyle obejmują miesięczne dane źródła. Mniej niż
  dwanaście miesięcy jest odrzucane: to kilka tygodni ruchu, nie korytarz.
""",
    "cs": """Jeden řádek na pár a **ten řádek je sám koridor**: jeden konec je nejnižší úroveň, na které
pár ve zvoleném období byl, druhý nejvyšší, a značka je dnešní kurz. Tahle tabule se tedy liší od
ostatních — jinde délka pruhu říká *kolik*, tady řádek v každém snímku zabírá celou šířku a pohybuje
se značka spolu s koridorem kolem ní.

- **Koridor se rozšiřuje.** Jeho stěny jsou nejnižší a nejvyšší **dosud**, ne za celé období. Měsíc,
  který zajde dál než všechny předchozí, vytlačí jednu ze stěn ven, a pár na 100% je nejdráž, jak kdy
  byl — ne na nějakém limitu.
- **Každý pár se měří vlastním rozpětím.** 157,92 u USD/JPY a 1,1245 u EUR/USD nejsou dva body na
  jedné stupnici; teprve normalizace umožní šesti párům stát na jednom obraze. Cenou je, že úzký a
  široký koridor vypadají stejně — proto jsou obě hodnoty vypsány pod každým řádkem.
- **Měsíční svíčky, bez úprav.** Měna nemá dividendu ani rozdělení, které by se upravovalo, a stránka
  jde stejnou neupravenou cestou ke zdroji jako stránka A+H.
- **Pokrytí se liší, a proto jsou dvě nabídky**: USD/CNY sahá do roku 2005, ostatních pět párů
  renminbi do roku 2016; hlavní crosy začínají všechny v roce 2005-07 a nesou 325 měsíců. Na jedné
  tabuli by se četlo, kdy zdroj který pár začal kotovat.
- **Nastavení trhu se tu neuplatní**: měnový pár nepatří žádné burze a tabule je stejná, ať platí
  kterýkoli trh.
- Nejdelší období je asi dvacet let, což je měsíční pokrytí zdroje; méně než dvanáct měsíců je
  odmítnuto — to je pár týdnů pohybu, ne koridor.
""",
    "ru": """Одна строка на пару, и **строка сама является коридором**: один конец — самый низкий уровень,
на котором пара была в выбранном периоде, другой — самый высокий, а маркер — сегодняшний курс.
Эта таблица не похожа на остальные: в других длина полосы говорит *сколько*, здесь строка в каждом
кадре занимает всю ширину, а движутся маркер и коридор вокруг него.

- **Коридор расширяется.** Его стены — минимум и максимум **на данный момент**, а не за весь период.
  Месяц, который выходит дальше всех прежних, раздвигает одну из стен, и пара на 100% находится на
  самом дорогом уровне, на котором была когда-либо, — а не у границы.
- **Каждая пара измеряется своим диапазоном.** 157,92 у USD/JPY и 1,1245 у EUR/USD — не две точки
  одной шкалы; именно нормировка позволяет шести парам поместиться на одном кадре. Цена этого в том,
  что узкий и широкий коридор выглядят одинаково, — поэтому обе границы напечатаны под строкой.
- **Месячные бары, без корректировки.** У валюты нет ни дивиденда, ни сплита, которые нужно
  корректировать, и страница идёт тем же «сырым» путём к источнику, что и страница A+H.
- **Охват различается, поэтому список их два**: USD/CNY уходит в 2005, остальные пять пар с юанем —
  в 2016; основные кроссы начинаются все в 2005-07 и несут по 325 месяцев. На одной таблице читалось
  бы, когда источник начал котировать каждую пару.
- **Настройка рынка здесь не действует**: валютная пара не принадлежит ни одной бирже, и таблица
  одна и та же при любом выбранном рынке.
- Самый длинный период — около двадцати лет, это месячный охват источника; меньше двенадцати месяцев
  отклоняется — это несколько недель движения, а не коридор.
""",
    "tr": """Her parite için bir satır, ve **satırın kendisi koridordur**: bir ucu paritenin seçilen
dönemde gördüğü en düşük seviye, diğeri en yüksek, işaret ise bugünkü kur. Bu tablo diğerlerine
benzemez — başka yerlerde çubuğun uzunluğu *ne kadar* der, burada satır her karede tüm genişliği
kaplar; hareket eden işaret ve çevresindeki koridordur.

- **Koridor genişler.** Duvarları tüm dönemin değil, **şimdiye kadarki** en düşük ve en yüksektir.
  Önceki tüm aylardan ileri giden bir ay duvarlardan birini dışa iter ve %100'deki bir parite bir
  sınırda değil, şimdiye kadarki en pahalı yerindedir.
- **Her parite kendi aralığıyla ölçülür.** USD/JPY'de 157,92 ile EUR/USD'de 1,1245 aynı ölçeğin
  üzerinde iki nokta değildir; altı pariteyi tek bir görüntüye sığdıran şey normalizasyondur. Bedeli,
  dar bir koridorla geniş bir koridorun aynı görünmesidir — bu yüzden iki uç her satırın altına
  yazılır.
- **Aylık mumlar, düzeltilmemiş.** Bir para biriminin düzeltilecek temettüsü veya bölünmesi yoktur ve
  sayfa kaynağa AH sayfasının gittiği ham yoldan gider.
- **Kapsam farklı, bu yüzden iki liste var**: USD/CNY 2005'e, diğer beş renminbi paritesi 2016'ya
  kadar uzanır; ana çaprazların hepsi 2005-07'de başlar ve 325 ay taşır. Tek tabloda okunacak şey,
  kaynağın her pariteyi ne zaman kotlamaya başladığı olurdu.
- **Piyasa ayarı burada geçmez**: bir para birimi çifti hiçbir borsaya ait değildir ve tablo, hangi
  piyasa seçilmiş olursa olsun aynıdır.
- En uzun dönem yaklaşık yirmi yıldır; bu kaynağın aylık kapsamıdır. On iki aydan kısa dönemler
  reddedilir — bu bir koridor değil, birkaç haftalık harekettir.
""",
}


def main():
    for tag, title in TITLES.items():
        path = HELP / f"help-{tag}.md"

        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")
        lines = text.replace("\r\n", "\n").split("\n")

        want = f"## {title}"

        # Idempotent: drop the chapter wherever it already sits, then put it back in place.
        if want in lines:
            at = lines.index(want)

            heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
            after = [i for i in heads if i > at]
            end = after[0] if after else len(lines)

            while end > at and lines[end - 1].strip() == "":
                end -= 1

            del lines[at:end]

        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(heads) < AFTER + 2:
            raise AssertionError(f"{tag}: only {len(heads)} chapters")

        at = heads[AFTER + 1]

        block = [want, ""] + BODIES[tag].rstrip("\n").split("\n") + [""]

        lines[at:at] = block

        out = "\n".join(lines)

        if not out.endswith("\n"):
            out += "\n"

        path.write_bytes(b"\xef\xbb\xbf" + out.encode("utf-8"))

        chapters = sum(1 for line in out.split("\n") if line.startswith("## "))

        print(f"{tag}: inserted after chapter {AFTER + 1}, now {chapters} chapters")


if __name__ == "__main__":
    main()
