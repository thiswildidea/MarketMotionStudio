# -*- coding: utf-8 -*-
r"""把「AH 溢价」一章插进 14 份帮助文档。

位置**按章节序号**定，不按标题文字：新章插在「市值榜竞速」之后（用户看到的是第 8 章），
因为导航里这两项也挨着。14 份文档的章节数与顺序必须相同，由 verify 脚本另行检查。

文件是 UTF-8 **带 BOM** + LF：`read_bytes().decode('utf-8-sig')` 读，写回时自己补 BOM。
`utf-8-sig` 只吃掉一个 BOM，文件里若已经叠了两个，要用 `lstrip('\ufeff')` 兜住。

幂等：标题已存在就整章重写。**改页面行为就要回来改这里的 BODIES** —— 市值榜那一章
曾经在榜单改了两次之后仍写着旧理由，见 `port-marketcap-help.py` 的说明。

用法：python tools\port-ahpremium-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

TITLES = {
    "zh-Hans": "AH 溢价",
    "zh-Hant": "AH 溢價",
    "en-US": "AH premium",
    "ja": "A/H プレミアム",
    "ko": "A/H 프리미엄",
    "de": "A/H-Prämie",
    "fr": "Prime A/H",
    "it": "Premio A/H",
    "es": "Prima A/H",
    "pt-BR": "Prêmio A/H",
    "pl": "Premia A/H",
    "cs": "Prémie A/H",
    "ru": "Премия A/H",
    "tr": "A/H primi",
}

BODIES = {
    "zh-Hans": """同一家公司在两个市场都有上市时，A 股相对 H 股贵多少——按月排成一列横向条形，
名次一路变到最后一帧。

- **溢价 = A 股价格 ÷（H 股价格 × 港元兑人民币）− 1。** 这不是推算出来的历史，是两个市场
  同一时刻的真实成交价，本页也因此是全应用唯一必须取**不复权**价格的地方：后复权会把近期
  价格放大，两个市场各自放大之后不能直接比——工商银行的 A 股在屏幕上卖 8.28 元，复权序列
  却给 13.34，用它算出来的溢价是 +245%，而真实值是 +26%。
- **画面画的是溢价最高的十五家**，所以条形基本都向右长——2026 年 9 月排在第十五位的
  仍有两成以上的溢价。H 股反而比 A 股贵的只有两家（招商银行、药明康德），它们排在名单末尾，
  通常进不了画面。
- **区间越长，能上来的公司越少。** 候选是 69 对知名两地上市公司，但只有两条腿都覆盖整段
  区间的才会被画出来：H 股上市不满两年的对会被去掉。所以「近 3 年」比「最长」多出几对，
  状态栏报的数字就是画面上的对数。
- **取样是月，不是日。** 「最长」约九年——限制来自汇率序列，它只回到 2016 年。A 股、H 股、
  汇率三者的月末日期互不相同，所以是按月归并（取每月的最后一笔），而不是按日期取交集。
- **名单是内建的。** 两个数据源都没有「哪些 A 股同时有 H 股」这类接口，所以清单写在程序里。
  它的诚实之处在于可核对：每一对都在 2026-10-02 回读过行情源一次，海通证券就是那次被剔掉的
  ——它的 H 股在并入国泰海通之后已经退市，留在名单里就是一行永远空着的赛道。
""",
    "zh-Hant": """同一家公司在兩個市場都有上市時，A 股相對 H 股貴多少——按月排成一列橫向條形，
名次一路變到最後一幀。

- **溢價 = A 股價 ÷（H 股價 × 港元兌人民幣）− 1。** 這不是推算出來的歷史，是兩個市場同一
  時刻的真實成交價，本頁也因此是全應用唯一必須取**不複權**價格的地方：後復權會把近期價格
  放大，兩個市場各自放大之後不能直接比——工商銀行的 A 股在螢幕上賣 8.28 元，複權序列卻給
  13.34，用它算出來的溢價是 +245%，而真實值是 +26%。
- **畫面畫的是溢價最高的十五家**，所以條形基本都向右長——2026 年 9 月排第十五位的仍有
  兩成以上的溢價。H 股反而比 A 股貴的只有兩家（招商銀行、藥明康德），它們排在名單末尾，
  通常進不了畫面。
- **區間越長，能上來的公司越少。** 候選是 69 對知名兩地上市公司，但只有兩條腿都覆蓋整段
  區間的才會被畫出來：H 股上市不滿兩年的對會被去掉。所以「近 3 年」比「最長」多出幾對，
  狀態列報的數字就是畫面上的對數。
- **取樣是月，不是日。** 「最長」約九年——限制來自匯率序列，它只回到 2016 年。A 股、H 股、
  匯率三者的月末日期互不相同，所以是按月歸併（取每月的最後一筆），而不是按日期取交集。
- **名單是內建的。** 兩個資料源都沒有「哪些 A 股同時有 H 股」這類介面，所以清單寫在程式裡。
  它的誠實之處在於可核對：每一對都在 2026-10-02 回讀過行情源一次，海通證券就是那次被剔掉的
  ——它的 H 股在併入國泰海通之後已經下市。
""",
    "en-US": """How much more a company's mainland listing costs than its Hong Kong one, for the firms
listed on both sides — month by month, as bars that overtake one another.

- **Premium = A price ÷ (H price × HKD/CNY) − 1.** Nothing here is derived: both legs are prices
  actually paid at the same moment, which is why this is the one page that must fetch
  **unadjusted** prices. A backward-adjusted series inflates recent prices, and two markets
  adjusted separately cannot be compared — ICBC's A share sells at 8.28 on the screen and the
  adjusted series reports 13.34, which turns a +26% premium into +245%.
- **The frame draws the fifteen dearest**, so the bars grow to the right — even the fifteenth
  carried a premium above twenty per cent. Only two of the sixty-nine go the other way, their H
  shares above their A shares, and both sit at the bottom of the list, past where the frame looks.
- **The longer the span, the fewer companies qualify.** Sixty-nine well-known dual listings are
  candidates, but only a pair with both legs covering the whole span is drawn: one whose Hong Kong
  listing is under two years old drops out. So "past 3 years" carries more pairs than "longest",
  and the count in the status line is the count on the frame.
- **Sampled monthly, not daily.** "Longest" is about nine years, and the limit is the exchange
  rate series, which reaches back to 2016 only. The three legs close their months on different
  days, so they are grouped by calendar month and the month's last print is taken, rather than
  intersected on the date itself.
- **The list is built in.** Neither source answers "which mainland listings also have a Hong Kong
  listing", so the pairs are written down — and checkable: every one was read back from the quote
  endpoint on 2026-10-02, and 海通证券 is what that check removed, its H shares delisted after the
  merger into 国泰海通. Kept, it would have been a lane that stayed empty for the whole video.
""",
    "ja": """両方の市場に上場している企業について、A 株が H 株より何割高いか——月ごとに横棒で並べ、
順位は最後のフレームまで入れ替わります。

- **プレミアム = A 株価 ÷（H 株価 × 香港ドル/人民元）− 1。** 推計ではなく、同じ時点で実際に
  売買された二つの価格です。そのためこのページだけは**調整なし**の価格を取ります。後方修正した
  系列は直近の価格を膨らませ、別々に調整した二つの市場は比べられません——工商銀行の A 株は
  画面では 8.28 元ですが、調整済み系列は 13.34 を返し、+26% のプレミアムが +245% になります。
- **描かれるのはプレミアムの高い 15 社**なので、棒はほぼ右に伸びます——15 位でも 2 割超の
  プレミアムがありました。逆に H 株が A 株より高いのは 2 社だけで、いずれもリストの末尾にあり、
  画面には出てきません。
- **期間を長く取るほど、載る企業は減ります。** 候補は有名な両地上場 69 組ですが、両方の足が
  期間全体を覆う組だけを描きます。香港上場が 2 年に満たない組は外れます。
- **抽出は月次です。** 「最長」は約 9 年——上限は為替系列で、2016 年までしか遡れません。
  A 株・H 株・為替の月末日はそれぞれ違うため、日付で交差を取るのではなく暦月でまとめ、
  その月の最後の値を取ります。
- **リストは内蔵です。** 「どの A 株が H 株も持つか」を返す接口はどちらの情報源にもありません。
  その代わり核対できます——全ての組を 2026-10-02 に情報源へ問い直し、海通証券はそこで外れました
  （国泰海通への合併で H 株が上場廃止）。
""",
    "ko": """두 시장에 모두 상장된 기업의 A주가 H주보다 얼마나 비싼지——월 단위로 가로 막대를 늘어놓고
순위는 마지막 프레임까지 바뀝니다.

- **프리미엄 = A 가격 ÷ (H 가격 × 홍콩달러/위안) − 1.** 추정이 아니라 같은 시점에 실제로 거래된
  두 가격입니다. 그래서 이 페이지만 **조정 없는** 가격을 받습니다. 후방 조정 계열은 최근 가격을
  부풀리고, 따로 조정한 두 시장은 비교할 수 없습니다——공상은행 A주는 화면에서 8.28위안인데
  조정 계열은 13.34를 돌려주어 +26% 프리미엄이 +245%가 됩니다.
- **그려지는 것은 프리미엄이 가장 높은 15개**라서 막대는 거의 오른쪽으로 자랍니다——15위도
  20%대의 프리미엄이었습니다. 반대로 H주가 A주보다 비싼 기업은 둘뿐이고, 둘 다 명단 끝에 있어
  화면에는 나오지 않습니다.
- **기간이 길수록 올라오는 기업이 줄어듭니다.** 후보는 유명 양지 상장 69쌍이지만, 두 쪽 모두
  기간 전체를 덮는 쌍만 그립니다. 홍콩 상장이 2년이 안 된 쌍은 빠집니다.
- **표본은 월 단위입니다.** "최장"은 약 9년이며, 한계는 2016년까지만 있는 환율 계열입니다.
  A주·H주·환율의 월말 날짜가 서로 달라 날짜로 교집합을 내지 않고 역월로 묶어 그 달의 마지막 값을 씁니다.
- **목록은 내장입니다.** "어떤 A주가 H주도 있는지"를 답하는 인터페이스는 두 데이터 원본 모두
  없습니다. 대신 검증할 수 있습니다——모든 쌍을 2026-10-02에 원본에 다시 물었고, 하이퉁증권은
  그때 빠졌습니다(궈타이하이퉁 합병 후 H주 상장폐지).
""",
    "de": """Wie viel teurer die Festlandnotierung eines Unternehmens ist als seine Hongkonger — für die
Firmen, die auf beiden Seiten notieren, Monat für Monat als Balken, die sich überholen.

- **Prämie = A-Kurs ÷ (H-Kurs × HKD/CNY) − 1.** Nichts davon ist abgeleitet: beide Seiten sind
  tatsächlich gezahlte Kurse zum selben Zeitpunkt, weshalb diese Seite als einzige
  **unbereinigte** Kurse holt. Eine rückwärts bereinigte Reihe bläht junge Kurse auf, und zwei
  getrennt bereinigte Märkte sind nicht vergleichbar — ICBCs A-Aktie steht mit 8,28 auf dem
  Schirm, die bereinigte Reihe meldet 13,34, und aus +26 % Prämie werden +245 %.
- **Gezeichnet werden die fünfzehn teuersten**, also wachsen die Balken fast alle nach rechts —
  selbst der fünfzehnte lag über zwanzig Prozent. Nur zwei der neunundsechzig laufen andersherum,
  ihre H-Aktien über den A-Aktien, und beide stehen am Ende der Liste, wohin das Bild nicht reicht.
- **Je länger der Zeitraum, desto weniger Unternehmen qualifizieren sich.** Neunundsechzig
  bekannte Doppelnotierungen stehen zur Wahl, gezeichnet wird aber nur ein Paar, dessen beide
  Seiten den ganzen Zeitraum abdecken: wer in Hongkong seit unter zwei Jahren notiert, fällt
  heraus.
- **Monatlich abgetastet.** „Längste" sind etwa neun Jahre, und die Grenze ist die Kursreihe, die
  nur bis 2016 zurückreicht. Die drei Seiten schließen ihre Monate an verschiedenen Tagen, also
  wird nach Kalendermonat gruppiert und der letzte Kurs des Monats genommen, statt auf das Datum
  zu schneiden.
- **Die Liste ist eingebaut.** Keine der beiden Quellen beantwortet „welche Festlandnotierung hat
  auch eine in Hongkong", also stehen die Paare im Programm — und sind prüfbar: jedes wurde am
  2026-10-02 gegen die Kursquelle gelesen, und 海通证券 ist genau das, was diese Prüfung entfernt
  hat (H-Aktien nach der Fusion mit 国泰海通 delistet).
""",
    "fr": """De combien la cotation continentale d'une société dépasse sa cotation hongkongaise, pour les
sociétés cotées des deux côtés — mois après mois, en barres qui se dépassent.

- **Prime = cours A ÷ (cours H × HKD/CNY) − 1.** Rien n'est calculé ici : les deux jambes sont des
  cours réellement payés au même instant, et c'est pourquoi cette page est la seule à récupérer des
  cours **non ajustés**. Une série ajustée vers l'arrière gonfle les cours récents, et deux marchés
  ajustés séparément ne se comparent pas — l'action A d'ICBC s'affiche à 8,28 et la série ajustée
  annonce 13,34, ce qui transforme une prime de +26 % en +245 %.
- **L'image trace les quinze plus chères**, donc les barres poussent vers la droite — la
  quinzième portait encore plus de vingt pour cent. Seules deux des soixante-neuf vont dans l'autre
  sens, leur action H au-dessus de l'action A, et toutes deux finissent en bas de liste, hors champ.
- **Plus la période est longue, moins de sociétés sont retenues.** Soixante-neuf doubles cotations
  connues sont candidates, mais seules celles dont les deux jambes couvrent toute la période sont
  tracées : une cotation hongkongaise de moins de deux ans est écartée.
- **Échantillonnage mensuel.** « Le plus long » fait environ neuf ans, la limite venant de la série
  de change qui ne remonte qu'à 2016. Les trois jambes closent leur mois à des dates différentes :
  on regroupe par mois calendaire et on prend le dernier cours du mois, plutôt que d'intersecter
  sur la date.
- **La liste est intégrée.** Aucune des deux sources ne répond à « quelles cotations continentales
  ont aussi une cotation à Hong Kong ». En revanche elle est vérifiable : chaque paire a été relue
  depuis la source le 2026-10-02, et 海通证券 est ce que cette vérification a retiré (actions H
  radiées après la fusion dans 国泰海通).
""",
    "it": """Quanto costa in più la quotazione continentale di una società rispetto a quella di Hong Kong,
per le società quotate su entrambi i lati — mese per mese, come barre che si sorpassano.

- **Premio = prezzo A ÷ (prezzo H × HKD/CNY) − 1.** Nulla è derivato: entrambe le gambe sono prezzi
  realmente pagati nello stesso istante, ed è per questo che questa è l'unica pagina che prende
  prezzi **non rettificati**. Una serie rettificata all'indietro gonfia i prezzi recenti, e due
  mercati rettificati separatamente non sono confrontabili — l'azione A di ICBC quota 8,28 sullo
  schermo e la serie rettificata ne dichiara 13,34: un premio del +26% diventa +245%.
- **Il fotogramma disegna le quindici più care**, quindi le barre crescono verso destra — anche
  la quindicesima superava il venti per cento. Solo due delle sessantanove vanno al contrario, con
  l'azione H sopra la A, ed entrambe stanno in fondo alla lista, fuori campo.
- **Più lungo il periodo, meno società restano.** Le candidate sono sessantanove doppie quotazioni
  note, ma viene disegnata solo una coppia con entrambe le gambe sull'intero periodo: una
  quotazione a Hong Kong da meno di due anni viene esclusa.
- **Campionamento mensile.** «Il più lungo» è circa nove anni, e il limite è la serie del cambio, che
  risale solo al 2016. Le tre gambe chiudono il mese in giorni diversi: si raggruppa per mese di
  calendario e si prende l'ultimo prezzo del mese, invece di intersecare sulla data.
- **L'elenco è integrato.** Nessuna delle due fonti risponde a «quali quotazioni continentali hanno
  anche una quotazione a Hong Kong». In compenso è verificabile: ogni coppia è stata riletta dalla
  fonte il 2026-10-02, e 海通证券 è ciò che quel controllo ha rimosso (azioni H delistate dopo la
  fusione in 国泰海通).
""",
    "es": """Cuánto más cara es la cotización continental de una compañía que la de Hong Kong, para las
compañías que cotizan en ambos lados: mes a mes, en barras que se adelantan.

- **Prima = precio A ÷ (precio H × HKD/CNY) − 1.** Aquí nada se calcula: las dos partes son precios
  realmente pagados en el mismo instante, y por eso esta es la única página que toma precios **sin
  ajustar**. Una serie ajustada hacia atrás infla los precios recientes, y dos mercados ajustados
  por separado no son comparables: la acción A de ICBC marca 8,28 en pantalla y la serie ajustada
  declara 13,34, con lo que una prima del +26% pasa a +245%.
- **El fotograma dibuja las quince más caras**, así que las barras crecen hacia la derecha:/n  incluso la decimoquinta superaba el veinte por ciento. Solo dos de las sesenta y nueve van al
  revés, con la acción H por encima de la A, y ambas quedan al final de la lista, fuera de cuadro.
- **Cuanto más largo el periodo, menos compañías quedan.** Hay sesenta y nueve dobles cotizaciones
  conocidas como candidatas, pero solo se dibuja la pareja cuyas dos partes cubren todo el periodo:
  una cotización en Hong Kong de menos de dos años se descarta.
- **Muestreo mensual.** «El más largo» son unos nueve años, y el límite es la serie del tipo de
  cambio, que solo llega a 2016. Las tres partes cierran el mes en días distintos, así que se agrupa
  por mes natural y se toma el último precio del mes, en vez de intersecar por fecha.
- **La lista es interna.** Ninguna de las dos fuentes responde a «qué cotizaciones continentales
  tienen también una en Hong Kong». Lo que sí se puede es comprobarla: cada pareja se releyó de la
  fuente el 2026-10-02, y 海通证券 es lo que esa comprobación eliminó (acciones H excluidas de
  cotización tras la fusión con 国泰海通).
""",
    "pt-BR": """Quanto mais cara é a cotação continental de uma companhia do que a de Hong Kong, para as
companhias cotadas dos dois lados — mês a mês, em barras que se ultrapassam.

- **Prêmio = preço A ÷ (preço H × HKD/CNY) − 1.** Nada aqui é calculado: as duas pontas são preços
  realmente pagos no mesmo instante, e é por isso que esta é a única página que busca preços **sem
  ajuste**. Uma série ajustada para trás infla os preços recentes, e dois mercados ajustados
  separadamente não são comparáveis — a ação A do ICBC aparece a 8,28 na tela e a série ajustada
  informa 13,34, transformando um prêmio de +26% em +245%.
- **O quadro desenha as quinze mais caras**, então as barras crescem para a direita — até a
  décima quinta passava de vinte por cento. Só duas das sessenta e nove vão ao contrário, com a ação
  H acima da A, e ambas ficam no fim da lista, fora do quadro.
- **Quanto maior o período, menos companhias entram.** São sessenta e nove duplas cotações
  conhecidas como candidatas, mas só é desenhado o par cujas duas pontas cobrem todo o período: uma
  cotação em Hong Kong com menos de dois anos fica de fora.
- **Amostragem mensal.** O «mais longo» tem cerca de nove anos, e o limite é a série do câmbio, que
  só chega a 2016. As três pontas fecham o mês em dias diferentes, então agrupa-se por mês
  calendário e toma-se o último preço do mês, em vez de cruzar pela data.
- **A lista é interna.** Nenhuma das duas fontes responde «quais cotações continentais também têm
  uma em Hong Kong». Em compensação, ela é conferível: cada par foi relido da fonte em 2026-10-02, e
  海通证券 foi o que essa conferência removeu (ações H deslistadas após a fusão no 国泰海通).
""",
    "pl": """O ile droższe jest notowanie kontynentalne spółki od jej notowania w Hongkongu — dla spółek
notowanych po obu stronach, miesiąc po miesiącu, jako słupki, które się wyprzedzają.

- **Premia = kurs A ÷ (kurs H × HKD/CNY) − 1.** Nic tu nie jest wyliczane: obie nogi to kursy
  faktycznie płacone w tym samym momencie, dlatego ta strona jako jedyna pobiera kursy
  **nieskorygowane**. Seria korygowana wstecz zawyża ostatnie kursy, a dwóch rynków korygowanych
  osobno nie da się porównać — akcja A ICBC kosztuje 8,28 na ekranie, a skorygowana seria podaje
  13,34, zamieniając premię +26% w +245%.
- **Rysowane jest piętnaście najdroższych**, więc słupki rosną w prawo — nawet piętnasta miała
  ponad dwadzieścia procent. Tylko dwie z sześćdziesięciu dziewięciu idą w drugą stronę, ich akcje
  H ponad akcjami A, i obie stoją na końcu listy, poza kadrem.
- **Im dłuższy okres, tym mniej spółek się kwalifikuje.** Kandydatów jest sześćdziesiąt dziewięć
  znanych podwójnych notowań, ale rysowana jest tylko para, której obie nogi pokrywają cały okres:
  notowanie w Hongkongu młodsze niż dwa lata wypada.
- **Próbkowanie miesięczne.** „Najdłuższy" to około dziewięciu lat, a granicą jest seria kursu
  walutowego sięgająca tylko 2016 roku. Trzy nogi kończą miesiąc w różnych dniach, więc grupujemy po
  miesiącu kalendarzowym i bierzemy ostatni kurs miesiąca, zamiast przecinać po dacie.
- **Lista jest wbudowana.** Żadne z dwóch źródeł nie odpowiada na pytanie „które notowania
  kontynentalne mają też notowanie w Hongkongu". Jest za to sprawdzalna: każdą parę odczytano
  ponownie ze źródła 2026-10-02, a 海通证券 wypadło właśnie wtedy (akcje H wycofane po fuzji z
  国泰海通).
""",
    "cs": """O kolik je kontinentální kotace společnosti dražší než její hongkongská — u společností
kotovaných na obou stranách, měsíc po měsíci, jako pruhy, které se předhánějí.

- **Prémie = kurz A ÷ (kurz H × HKD/CNY) − 1.** Nic se tu nepočítá: obě strany jsou kurzy skutečně
  zaplacené ve stejný okamžik, a proto tato stránka jako jediná načítá **neupravené** kurzy. Zpětně
  upravená řada nafukuje nedávné kurzy a dva trhy upravené odděleně srovnávat nelze — akcie A ICBC
  stojí na obrazovce 8,28 a upravená řada hlásí 13,34, čímž se prémie +26 % změní na +245 %.
- **Kreslí se patnáct nejdražších**, takže pruhy rostou doprava — i patnáctá měla přes dvacet
  procent. Jen dva ze šedesáti devíti jdou opačně, jejich akcie H nad akciemi A, a oba stojí na
  konci seznamu, kam obraz nedosáhne.
- **Čím delší období, tím méně společností se vejde.** Kandidátů je šedesát devět známých dvojích
  kotací, ale kreslí se jen pár, jehož obě strany pokrývají celé období: hongkongská kotace mladší
  dvou let vypadne.
- **Vzorkování po měsících.** „Nejdelší" je asi devět let a hranicí je řada kurzu, která sahá jen do
  roku 2016. Tři strany uzavírají měsíc v různých dnech, proto se seskupuje po kalendářním měsíci a
  bere se poslední kurz měsíce, místo protnutí podle data.
- **Seznam je vestavěný.** Ani jeden zdroj neodpovídá na „které kontinentální kotace mají i tu
  hongkongskou". Zato je ověřitelný: každý pár byl 2026-10-02 znovu přečten ze zdroje a 海通证券 je
  to, co tato kontrola odstranila (akcie H vyřazeny po fúzi do 国泰海通).
""",
    "ru": """Насколько бумага компании на материке дороже её гонконгской — для компаний, торгующихся
с обеих сторон, месяц за месяцем, полосами, которые обгоняют друг друга.

- **Премия = цена A ÷ (цена H × HKD/CNY) − 1.** Здесь ничего не выводится: обе ноги — цены,
  фактически уплаченные в один момент, и поэтому только эта страница берёт **нескорректированные**
  цены. Ряд, скорректированный назад, завышает недавние цены, а два рынка, скорректированные по
  отдельности, сравнивать нельзя: бумага A ICBC стоит на экране 8,28, а скорректированный ряд
  сообщает 13,34 — и премия +26 % превращается в +245 %.
- **Рисуются пятнадцать самых дорогих**, поэтому полосы растут вправо — даже у пятнадцатой
  премия была выше двадцати процентов. Лишь две из шестидесяти девяти идут в другую сторону, их
  бумаги H дороже бумаг A, и обе стоят в конце списка, куда кадр не достаёт.
- **Чем длиннее период, тем меньше компаний остаётся.** Кандидатов — шестьдесят девять известных
  двойных листингов, но рисуется только пара, у которой обе ноги покрывают весь период: листинг в
  Гонконге младше двух лет выпадает.
- **Шаг — месяц.** «Самый длинный» — около девяти лет, и предел задаёт ряд курса, который доходит
  только до 2016 года. Три ноги закрывают месяц в разные дни, поэтому группировка идёт по
  календарному месяцу и берётся последняя цена месяца, а не пересечение по дате.
- **Список встроен.** Ни один из двух источников не отвечает на вопрос «у каких материковых бумаг
  есть и гонконгская». Зато его можно проверить: каждая пара 2026-10-02 была перечитана из
  источника, и 海通证券 — то, что эта проверка убрала (бумаги H делистингованы после слияния в
  国泰海通).
""",
    "tr": """İki tarafta da kote olan şirketler için, karadaki kotasyonun Hong Kong kotasyonundan ne kadar
pahalı olduğu — ay ay, birbirini geçen çubuklar olarak.

- **Prim = A fiyatı ÷ (H fiyatı × HKD/CNY) − 1.** Burada hiçbir şey türetilmiyor: iki bacak da aynı
  anda gerçekten ödenen fiyatlar, bu yüzden yalnızca bu sayfa **düzeltilmemiş** fiyat çeker. Geriye
  dönük düzeltilmiş seri son fiyatları şişirir ve ayrı ayrı düzeltilmiş iki piyasa
  karşılaştırılamaz — ICBC'nin A hissesi ekranda 8,28 iken düzeltilmiş seri 13,34 der: +26%'lık
  prim +245% olur.
- **Çizilen, primi en yüksek on beş çift**, bu yüzden çubuklar sağa büyür — on beşinci bile
  yüzde yirmiyi aşıyordu. Altmış dokuz çiftin yalnızca ikisi ters yönde, H hissesi A hissesinin
  üstünde, ve ikisi de listenin sonunda, karenin ulaşmadığı yerde.
- **Dönem uzadıkça giren şirket azalır.** Aday, tanıdık altmış dokuz çift kotasyondur; ancak iki
  bacağı da dönemin tamamını kapsayan çift çizilir: Hong Kong kotesi iki yıldan genç olan düşer.
- **Örnekleme aylık.** "En uzun" yaklaşık dokuz yıldır ve sınır, yalnızca 2016'ya uzanan kur
  serisidir. Üç bacak ayı farklı günlerde kapatır; bu yüzden tarihe göre kesişim alınmaz, takvim
  ayına göre gruplanır ve ayın son fiyatı alınır.
- **Liste gömülüdür.** İki kaynağın hiçbiri "hangi karadaki kotasyonun Hong Kong'da da kotasyonu
  var" sorusunu yanıtlamaz. Buna karşılık doğrulanabilir: her çift 2026-10-02'de kaynaktan yeniden
  okundu ve 海通证券 tam da bu kontrolün çıkardığı şirkettir (国泰海通 birleşmesinden sonra H
  hisseleri işlemden kaldırıldı).
""",
}

# 新章插在第几章之后（0 起算）：市值榜竞速是第 7 章。
AFTER = 6


def main():
    for tag, title in TITLES.items():
        path = HELP / f"help-{tag}.md"

        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")
        lines = text.split("\n")

        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(heads) < AFTER + 2:
            raise AssertionError(f"{tag}: only {len(heads)} chapters")

        want = f"## {title}"

        # Idempotent: drop the chapter wherever it already sits, then put it back in place.
        if want in lines:
            at = lines.index(want)

            after = [i for i in heads if i > at]
            end = after[0] if after else len(lines)

            while end > at and lines[end - 1].strip() == "":
                end -= 1

            del lines[at:end]

            heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

            if len(heads) < AFTER + 2:
                raise AssertionError(f"{tag}: only {len(heads)} chapters after removal")

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
