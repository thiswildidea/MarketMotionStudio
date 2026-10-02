# -*- coding: utf-8 -*-
r"""把「回撤与修复」这一章插进 14 份帮助文档。

插在第 12 章「大類資產」之后（0 基下标 11），第 13 章「收益矩阵」之前 → 24 章。
两页是同一批八档、同一副算术，章节也应当挨着。

用法：python tools\port-drawdown-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 插在第 12 章「大類資產」之后（0 基下标 11），第 13 章「收益矩阵」之前。
AFTER = 11

TITLES = {
    "zh-Hans": "回撤与修复",
    "zh-Hant": "回撤與修復",
    "en-US": "Drawdowns",
    "ja": "ドローダウン",
    "ko": "낙폭과 회복",
    "de": "Rücksetzer",
    "fr": "Reculs",
    "it": "Ribassi",
    "es": "Caídas",
    "pt-BR": "Quedas",
    "pl": "Obsunięcia",
    "cs": "Poklesy",
    "ru": "Просадки",
    "tr": "Düşüşler",
}

BODIES = {
    "zh-Hans": """一行是**它落在自己高點下方多遠**——不是它賺了多少，而是賺到這些要付出什麼。跑的是和大類資產
那一页同样的八档，只是不互相比，而是各自比自己的高点。

- **曲線才是重點。** 這裏其他地方都把數字畫成長度，長度只能說「此刻水有多深」。深度是一段時間
  裡的形狀：低點與爬出來的那一端是曲線上的兩個位置，它們在畫面上隔開的距離就是中間經過的月數。
- **兩個數字不成比例。** 近十年裡納指 ETF 最深跌 25.52%，六個月就回到高點；中證500ETF 跌
  56.07%，用了八十六個月。只印一個數字的話，後者看起來只是前者的加重版，實際上不是。
- **整塊板共用一把深度尺。** 若每行按自己最慘的那次縮放，貨幣 ETF 的 0.2% 會被畫成和中證500
  的 56% 一樣深的深淵——而這塊板存在的理由恰恰是說這兩者不能相提並論。所以它是一條貼著高點線的
  平線，**這條平線就是它要說的話**。
- **復權、月線、從各自第一個月起算**，理由與大類資產那一页相同：基金的分紅從不出現在價格裡，
  2019 年才有的那一档，不會拿它還沒出現時的高點來量。
- **行仍然在競速。** 排序按「離自己的高點多遠」，離高點最近的在最上面，隨著月份推進互相換位。
- **黃金與豆粕在本次實測時仍未修復**——板面把這類下跌標成「未修復」，因為區間結束時它還沒爬回去。

這一頁不看市場設置：八檔都在境內掛牌。區間不足 12 個月會拒絕取數。
""",

    "zh-Hant": """一行是**它落在自己高點下方多遠**——不是它賺了多少，而是賺到這些要付出什麼。跑的是和大類資產
那一頁同樣的八檔，只是不互相比，而是各自比自己的高點。

- **曲線才是重點。** 這裡其他地方都把數字畫成長度，長度只能說「此刻水有多深」。深度是一段時間
  裡的形狀：低點與爬出來的那一端是曲線上的兩個位置，它們在畫面上隔開的距離就是中間經過的月數。
- **兩個數字不成比例。** 近十年裡納指 ETF 最深跌 25.52%，六個月就回到高點；中證500ETF 跌
  56.07%，用了八十六個月。只印一個數字的話，後者看起來只是前者的加重版，實際上不是。
- **整塊板共用一把深度尺。** 若每行按自己最慘的那次縮放，貨幣 ETF 的 0.2% 會被畫成和中證500
  的 56% 一樣深的深淵——而這塊板存在的理由恰恰是說這兩者不能相提並論。所以它是一條貼著高點線的
  平線，**這條平線就是它要說的話**。
- **復權、月線、從各自第一個月起算**，理由與大類資產那一頁相同：基金的分紅從不出現在價格裡，
  2019 年才有的那一檔，不會拿它還沒出現時的高點來量。
- **行仍然在競速。** 排序按「離自己的高點多遠」，離高點最近的在最上面，隨著月份推進互相換位。
- **黃金與豆粕在本次實測時仍未修復**——板面把這類下跌標成「未修復」，因為區間結束時它還沒爬回去。

這一頁不看市場設置：八檔都在境內掛牌。區間不足 12 個月會拒絕取數。
""",

    "en-US": """A row is **how far below its own high a holding sits** — not what it earned, but what it cost to
earn it. The same eight holdings as the asset race, measured against themselves instead of each
other.

- **The curve is the point.** Everywhere else in this app a value is drawn as a length, which can
  only say how deep the water is at this instant. A depth is a shape over time: the low and the
  climb out of it are two places on the curve, and the distance between them across the frame is
  the months it took.
- **The two numbers do not rise together.** Over the last ten years the Nasdaq fund fell 25.52%
  and was level again in six months; the CSI 500 fund fell 56.07% and took eighty-six. Printed as
  one number, the second looks like more of the same thing as the first and is not.
- **One depth scale for the whole board.** Scaling each row to its own worst would draw the
  money-market fund's 0.2% as a chasm the size of the CSI 500's 56%, on a board whose whole claim
  is that those are not comparable. So that row is a flat line pinned to its high-water line — and
  **the flatness is what it says**.
- **Adjusted, monthly, and from each holding's own first month**, for the reasons the asset race
  gives: a fund's distributions never appear in its price, and a holding that joins in 2019 is not
  measured against a high it did not have.
- **The rows still race.** They are ordered by how far below their own high they are, closest to
  its high at the top, and they trade places as their months pass.
- **Gold and the commodity fund were still under water when this was measured** — the board reports
  that kind of fall as open, because the range ended before it was mended.

Not governed by the market setting: all eight are quoted on a mainland exchange. Fewer than twelve
months in the range is refused.
""",

    "ja": """行は**その資産が自分の高値からどれだけ下にいるか**——稼いだ額ではなく、それを稼ぐのに何が必要
だったか。資産クラスと同じ八つの資産を、互いではなく各自の高値に対して測る。

- **要点は曲線。** このアプリの他の場所では値は長さとして描かれ、長さは「今この瞬間の深さ」しか
  言えない。深さは時間の上の形——安値とそこからの回復は曲線上の二つの場所で、画面上でそれらが
  隔たっている距離が、その間に経過した月数である。
- **二つの数字は比例しない。** 近十年でナスダック ETF は最深 25.52%、六か月で高値に戻った；
  CSI500 ETF は 56.07% 下落し、八十六か月かかった。一つの数字だけを印刷すれば、後者は前者の
  焼き直しに見えるが、実際はそうではない。
- **盤面全体で一つの深さの物差し。** 各行を自分の最悪値で縮めれば、マネー・マーケット・ファンドの
  0.2% が CSI500 の 56% と同じ深さの峡谷として描かれる——しかしこの板の存在理由はまさに
  「この二つは比べられない」と言うことだ。ゆえにその行は高値線に張り付いた平らな線であり、
  **その平らさこそが主張である**。
- **調整済み・月次・各自の最初の月から**、資産クラスのページと同じ理由：ファンドの分配金は価格に
  現れないし、2019 年から参加した資産を、それが存在しなかった高値で測ることはしない。
- **行は依然として競う。** 自分の高値からの距離で並び、高値に最も近いものが上になり、月が進む
  につれて入れ替わる。
- **実測時点で金と商品ファンドはまだ水没中**——この手の下落は「未回復」と表示される。区間が
  終わった時点でまだ戻っていないからだ。

市場設定の管轄外：八つすべてが本土の取引所に上場している。区間が 12 か月未満なら拒否する。
""",

    "ko": """행은 **그 자산이 자기 고점에서 얼마나 아래 있는지**—얼마를 벌었는가가 아니라, 그것을 버는 데
무엇을 견뎠는가. 자산군 경주와 같은 여덟 자산을 서로가 아니라 각자의 고점에 견주어 측정한다.

- **핵심은 곡선.** 이 앱의 다른 곳에서 값은 길이로 그려지고, 길이는 "이 순간 물이 얼마나 깊은가"만
  말할 수 있다. 깊이는 시간 위의 형태—저점과 그곳에서 빠져나온 지점은 곡선 위의 두 지점이고,
  화면에서 둘이 떨어진 거리가 바로 그 사이의 개월 수다.
- **두 숫자는 비례하지 않는다.** 지난 십 년간 나스닥 ETF는 가장 깊게 25.52% 하락했고 여섯 달 만에
  고점으로 돌아왔다; CSI500 ETF는 56.07% 하락해 여든여섯 달이 걸렸다. 숫자 하나만 적으면 후자는
  전자의 강화판처럼 보이지만, 실제로는 그렇지 않다.
- **보드 전체에 깊이 눈금은 하나.** 각 행을 자기 최악치에 맞춰 축소하면 머니마켓 펀드의 0.2%가
  CSI500의 56%와 같은 심연으로 그려진다—그러나 이 보드가 존재하는 이유는 바로 그 둘이 비교 대상이
  아니라고 말하는 것이다. 그러므로 그 행은 고점선에 붙은 평평한 선이며, **그 평평함이 곧 그 행의
  말이다**.
- **조정·월간·각자의 첫 달부터**, 자산군 페이지와 같은 이유: 펀드의 분배금은 가격에 나타나지 않고,
  2019년에 합류한 자산을 그것이 없던 시점의 고점으로 재지 않는다.
- **행은 여전히 경주한다.** 자기 고점에서의 거리로 정렬되어 고점에 가장 가까운 쪽이 위에 오고,
  달이 지나며 자리를 바꾼다.
- **측정 시점에 금과 상품 펀드는 여전히 물속**—이런 하락은 "미회복"으로 표시된다. 구간이 끝날 때까지
  아직 돌아오지 않았기 때문이다.

시장 설정의 관할이 아니다: 여덟 모두 본토 거래소에 상장되어 있다. 구간이 12개월 미만이면 거부한다.
""",

    "de": """Eine Zeile ist, **wie weit unter dem eigenen Hoch eine Anlage steht** — nicht was sie verdient
hat, sondern was es gekostet hat, es zu verdienen. Dieselben acht Anlagen wie bei den
Anlageklassen, am eigenen Hoch gemessen statt gegeneinander.

- **Die Kurve ist der Punkt.** Überall sonst in dieser App wird ein Wert als Länge gezeichnet, und
  eine Länge kann nur sagen, wie tief das Wasser in diesem Augenblick ist. Eine Tiefe ist eine Form
  über die Zeit: das Tief und der Weg heraus sind zwei Stellen auf der Kurve, und ihr Abstand über
  das Bild ist die Zahl der Monate dazwischen.
- **Die zwei Zahlen steigen nicht gemeinsam.** In den letzten zehn Jahren fiel der Nasdaq-Fonds um
  25,52 % und war nach sechs Monaten wieder eben; der CSI-500-Fonds fiel um 56,07 % und brauchte
  sechsundachtzig. Als eine Zahl gedruckt wirkt das zweite wie eine Steigerung des ersten — und ist
  es nicht.
- **Eine Tiefenskala für die ganze Tafel.** Würde jede Zeile auf ihr eigenes Tief skaliert, wäre
  die 0,2 % des Geldmarktfonds ein Abgrund von der Größe der 56 % des CSI 500 — auf einer Tafel,
  deren ganzer Anspruch lautet, dass die beiden nicht vergleichbar sind. Also ist diese Zeile eine
  flache Linie an ihrer Hochwasserlinie, und **diese Flachheit ist ihre Aussage**.
- **Adjustiert, monatlich und ab dem jeweils ersten eigenen Monat**, aus den Gründen, die die
  Anlageklassen nennen: Ausschüttungen eines Fonds erscheinen nie in seinem Preis, und eine Anlage,
  die erst 2019 dazukommt, wird nicht an einem Hoch gemessen, das sie nicht hatte.
- **Die Zeilen rennen weiter.** Sie sind danach geordnet, wie weit sie unter dem eigenen Hoch
  stehen — dem Hoch am nächsten oben — und tauschen die Plätze, während die Monate vergehen.
- **Gold und der Rohstofffonds lagen bei dieser Messung noch unter Wasser** — die Tafel meldet
  solche Rücksetzer als offen, weil der Zeitraum endete, bevor sie behoben waren.

Nicht von der Markteinstellung abhängig: alle acht werden an einer Festlandbörse gehandelt.
Weniger als zwölf Monate im Zeitraum werden abgelehnt.
""",

    "fr": """Une ligne, c'est **la distance entre une position et son propre sommet** — pas ce qu'elle a
rapporté, mais ce qu'il a fallu endurer pour le rapporter. Les huit mêmes supports que la course
des classes d'actifs, mesurés par rapport à eux-mêmes au lieu de l'être entre eux.

- **La courbe est le sujet.** Partout ailleurs dans cette application, une valeur est dessinée
  comme une longueur, et une longueur ne peut dire que la profondeur de l'eau à cet instant. Une
  profondeur est une forme dans le temps : le creux et la remontée sont deux endroits de la courbe,
  et la distance qui les sépare sur l'image est le nombre de mois écoulés entre eux.
- **Les deux nombres ne montent pas ensemble.** Sur les dix dernières années, le fonds Nasdaq a
  perdu 25,52 % et était revenu à niveau en six mois ; le fonds CSI 500 a perdu 56,07 % et a mis
  quatre-vingt-six mois. Imprimé comme un seul nombre, le second a l'air d'une version aggravée du
  premier — et il ne l'est pas.
- **Une seule échelle de profondeur pour tout le tableau.** Mettre chaque ligne à l'échelle de son
  propre pire ferait des 0,2 % du fonds monétaire un gouffre de la taille des 56 % du CSI 500, sur
  un tableau dont toute la raison d'être est de dire que ces deux-là ne se comparent pas. Cette
  ligne est donc une ligne plate collée à sa ligne de plus-haut — et **cette platitude est précisément
  ce qu'elle dit**.
- **Ajusté, mensuel, et à partir du premier mois propre à chaque support**, pour les raisons que
  donne la course des classes d'actifs : les distributions d'un fonds n'apparaissent jamais dans
  son cours, et un support qui n'arrive qu'en 2019 n'est pas mesuré contre un sommet qu'il n'avait
  pas.
- **Les lignes courent toujours.** Elles sont ordonnées par la distance qui les sépare de leur
  propre sommet — le plus proche de son sommet en haut — et elles échangent leurs places à mesure
  que les mois passent.
- **L'or et le fonds de matières premières étaient encore sous l'eau lors de cette mesure** — le
  tableau signale ce genre de recul comme ouvert, parce que la période s'est terminée avant qu'il
  ne soit réparé.

Ne dépend pas du réglage de marché : les huit sont cotés sur une place de marché continentale.
Moins de douze mois dans la période est refusé.
""",

    "it": """Una riga è **quanto sotto il proprio massimo si trova uno strumento** — non quanto ha guadagnato,
ma cosa è costato guadagnarlo. Gli stessi otto strumenti della corsa delle classi di attività,
misurati rispetto a sé stessi invece che tra loro.

- **La curva è il punto.** In ogni altra parte di questa app un valore è disegnato come una
  lunghezza, e una lunghezza può dire solo quanto è profonda l'acqua in quell'istante. Una
  profondità è una forma nel tempo: il minimo e la risalita sono due punti sulla curva, e la
  distanza che li separa sul fotogramma è il numero di mesi trascorsi.
- **I due numeri non crescono insieme.** Negli ultimi dieci anni il fondo Nasdaq è sceso del 25,52%
  ed è tornato in pari in sei mesi; il fondo CSI 500 è sceso del 56,07% e ha impiegato
  ottantasei mesi. Stampato come un numero solo, il secondo sembra una versione aggravata del
  primo — e non lo è.
- **Una sola scala di profondità per tutta la tavola.** Scalare ogni riga sul proprio peggior
  momento disegnerebbe lo 0,2% del fondo monetario come un baratro grande quanto il 56% del CSI
  500, su una tavola la cui intera ragione d'essere è dire che quei due non sono paragonabili.
  Quindi quella riga è una linea piatta attaccata alla sua linea di massimo — e **quella piattezza
  è ciò che dice**.
- **Aggiustato, mensile e dal primo mese proprio di ciascuno strumento**, per le ragioni che dà la
  corsa delle classi di attività: le distribuzioni di un fondo non compaiono mai nel suo prezzo, e
  uno strumento che arriva solo nel 2019 non è misurato contro un massimo che non aveva.
- **Le righe corrono ancora.** Sono ordinate per quanto sono sotto il proprio massimo — la più
  vicina al proprio massimo in alto — e si scambiano di posto mentre i mesi passano.
- **Oro e fondo di materie prime erano ancora sott'acqua al momento di questa misurazione** — la
  tavola segnala questo tipo di ribasso come aperto, perché l'intervallo è finito prima che fosse
  riparato.

Non dipende dall'impostazione del mercato: tutti e otto sono quotati su una borsa continentale.
Meno di dodici mesi nell'intervallo viene rifiutato.
""",

    "es": """Una fila es **cuánto por debajo de su propio máximo está una inversión** — no lo que ganó, sino
lo que costó ganarlo. Las mismas ocho inversiones que la carrera de clases de activos, medidas
contra sí mismas en lugar de entre sí.

- **La curva es el punto.** En el resto de la aplicación un valor se dibuja como una longitud, y
  una longitud solo puede decir cuán profunda está el agua en ese instante. Una profundidad es una
  forma en el tiempo: el mínimo y la salida de él son dos lugares de la curva, y la distancia que
  los separa en el fotograma es el número de meses transcurridos.
- **Los dos números no suben juntos.** En los últimos diez años el fondo Nasdaq cayó un 25,52% y
  volvió a estar nivelado en seis meses; el fondo CSI 500 cayó un 56,07% y tardó ochenta y seis.
  Impreso como un solo número, el segundo parece una versión agravada del primero — y no lo es.
- **Una sola escala de profundidad para todo el tablero.** Escalar cada fila según su propio peor
  momento dibujaría el 0,2% del fondo monetario como un abismo del tamaño del 56% del CSI 500, en
  un tablero cuyo propósito entero es decir que esos dos no son comparables. Así que esa fila es
  una línea plana pegada a su línea de máximo — y **esa planicie es lo que dice**.
- **Ajustado, mensual y desde el primer mes propio de cada inversión**, por las razones que da la
  carrera de clases de activos: las distribuciones de un fondo nunca aparecen en su precio, y una
  inversión que llega en 2019 no se mide contra un máximo que no tenía.
- **Las filas siguen compitiendo.** Se ordenan por cuán por debajo de su propio máximo están — la
  más cerca de su máximo arriba — e intercambian puestos a medida que pasan los meses.
- **El oro y el fondo de materias primas seguían bajo el agua cuando se midió esto** — el tablero
  reporta ese tipo de caída como abierta, porque el periodo terminó antes de que se reparara.

No depende del ajuste de mercado: los ocho cotizan en una bolsa continental. Menos de doce meses
en el periodo se rechaza.
""",

    "pt-BR": """Uma linha é **a distância entre um ativo e sua própria máxima** — não o que ele rendeu, mas o que
custou para render. Os mesmos oito ativos da corrida de classes de ativos, medidos contra si mesmos
em vez de entre si.

- **A curva é o ponto.** Em todo o resto deste aplicativo um valor é desenhado como um
  comprimento, e um comprimento só pode dizer quão profunda está a água naquele instante. Uma
  profundidade é uma forma no tempo: o fundo e a saída dele são dois lugares na curva, e a
  distância que os separa no quadro é o número de meses decorridos.
- **Os dois números não sobem juntos.** Nos últimos dez anos o fundo Nasdaq caiu 25,52% e voltou ao
  nível em seis meses; o fundo CSI 500 caiu 56,07% e levou oitenta e seis. Impresso como um único
  número, o segundo parece uma versão agravada do primeiro — e não é.
- **Uma única escala de profundidade para todo o quadro.** Escalar cada linha pelo seu próprio pior
  momento desenharia os 0,2% do fundo de mercado monetário como um abismo do tamanho dos 56% do CSI
  500, num quadro cujo sentido inteiro é dizer que os dois não são comparáveis. Por isso essa
  linha é uma linha reta colada à sua linha de máxima — e **essa retidão é o que ela diz**.
- **Ajustado, mensal e a partir do primeiro mês próprio de cada ativo**, pelas razões que a corrida
  de classes de ativos dá: as distribuições de um fundo nunca aparecem no seu preço, e um ativo que
  chega em 2019 não é medido contra uma máxima que não tinha.
- **As linhas continuam correndo.** São ordenadas por quão abaixo da própria máxima estão — a mais
  perto da própria máxima no topo — e trocam de lugar enquanto os meses passam.
- **Ouro e o fundo de commodities ainda estavam debaixo d'água quando isto foi medido** — o quadro
  reporta esse tipo de queda como aberta, porque o período terminou antes de ser reparada.

Não depende da configuração de mercado: todos os oito são cotados numa bolsa continental. Menos de
doze meses no período é recusado.
""",

    "pl": """Wiersz to **jak daleko poniżej własnego szczytu jest instrument** — nie ile zarobił, lecz ile
kosztowało wytrzymanie tego zarobku. Te same osiem instrumentów co w wyścigu klas aktywów, tyle że
mierzone względem siebie samych, nie względem innych.

- **Krzywa jest sednem.** W całej tej aplikacji wartość rysowana jest jako długość, a długość może
  powiedzieć tylko, jak głęboka jest woda w tej jednej chwili. Głębokość jest kształtem w czasie:
  dołek i wyjście z niego to dwa miejsca na krzywej, a odległość między nimi w kadrze to liczba
  miesięcy, jakie upłynęły.
- **Te dwie liczby nie rosną razem.** W ostatnich dziesięciu latach fundusz Nasdaq spadł o 25,52%
  i wrócił do poziomu w sześć miesięcy; fundusz CSI 500 spadł o 56,07% i potrzebował osiemdziesięciu
  sześciu. Wydrukowana jako jedna liczba, druga wygląda na wzmocnioną wersję pierwszej — a nie jest.
- **Jedna skala głębokości dla całej tablicy.** Skalowanie każdego wiersza według jego własnego
  najgorszego momentu narysowałoby 0,2% funduszu rynku pieniężnego jako otchłań wielkości 56% CSI
  500 — na tablicy, której cały sens polega na tym, że tych dwóch nie można porównywać. Dlatego ten
  wiersz jest płaską linią przy własnej linii szczytu — i **ta płaskość jest jego komunikatem**.
- **Z korektą, miesięcznie i od własnego pierwszego miesiąca**, z powodów podanych przez wyścig
  klas aktywów: dystrybucje funduszu nigdy nie pojawiają się w jego cenie, a instrument, który
  dołącza w 2019, nie jest mierzony względem szczytu, którego nie miał.
- **Wiersze wciąż biegną.** Są uporządkowane według odległości od własnego szczytu — najbliżej
  szczytu na górze — i zamieniają się miejscami wraz z upływem miesięcy.
- **Złoto i fundusz towarowy były w chwili pomiaru wciąż pod wodą** — tablica zgłasza taki spadek
  jako otwarty, bo okres skończył się, zanim został naprawiony.

Nie podlega ustawieniu rynku: wszystkie osiem jest notowanych na giełdzie kontynentalnej. Mniej niż
dwanaście miesięcy w okresie jest odrzucane.
""",

    "cs": """Řádek je **jak hluboko pod vlastním maximem se nástroj nachází** — ne kolik vydělal, ale co stálo
to vydělat. Týchž osm nástrojů jako v závodu tříd aktiv, ale měřených vůči sobě samým, ne proti
sobě navzájem.

- **Křivka je to podstatné.** Všude jinde v této aplikaci se hodnota kreslí jako délka, a délka
  umí říct jen to, jak hluboká je voda v tomto okamžiku. Hloubka je tvar v čase: minimum a cesta
  ven z něj jsou dvě místa na křivce a vzdálenost mezi nimi napříč snímkem je počet měsíců, které
  uplynuly.
- **Obě čísla nestoupají společně.** Za posledních deset let fond Nasdaq klesl o 25,52 % a byl
  zpět na úrovni za šest měsíců; fond CSI 500 klesl o 56,07 % a potřeboval osmdesát šest. Vytištěno
  jako jedno číslo vypadá druhé jako zostřená verze prvního — a není.
- **Jedna stupnice hloubky pro celou tabuli.** Škálovat každý řádek podle jeho vlastního nejhoršího
  okamžiku by nakreslilo 0,2 % fondu peněžního trhu jako propast velikosti 56 % CSI 500 — na tabuli,
  jejíž celý smysl je říct, že tyto dvě věci nejsou srovnatelné. Ten řádek je proto rovná čára
  přilepená na svou linii maxima — a **ta rovnost je přesně to, co říká**.
- **S úpravou, měsíčně a od vlastního prvního měsíce**, z důvodů, které uvádí závod tříd aktiv:
  výnosy fondu se v jeho ceně nikdy neobjeví a nástroj, který přichází až v roce 2019, se neměří
  proti maximu, které neměl.
- **Řádky stále závodí.** Jsou seřazeny podle vzdálenosti od vlastního maxima — nejblíže vlastnímu
  maximu nahoře — a vyměňují si místa, jak měsíce plynou.
- **Zlato a komoditní fond byly při tomto měření stále pod vodou** — tabule hlásí takový pokles jako
  otevřený, protože období skončilo dřív, než byl napraven.

Neřídí se nastavením trhu: všech osm je kótováno na kontinentální burze. Méně než dvanáct měsíců
v období je odmítnuto.
""",

    "ru": """Строка — это **насколько инструмент ниже собственного максимума**: не сколько он заработал, а чего
стоило это заработать. Те же восемь инструментов, что в гонке классов активов, но измеренные по
себе, а не друг против друга.

- **Кривая — вот суть.** Во всём остальном приложении значение рисуют как длину, а длина способна
  сказать лишь, насколько глубоко вода в этот момент. Глубина — это форма во времени: минимум и
  выход из него — две точки на кривой, и расстояние между ними по кадру — это число месяцев между
  ними.
- **Два числа не растут вместе.** За последние десять лет фонд Nasdaq упал на 25,52 % и вернулся к
  уровню через шесть месяцев; фонд CSI 500 упал на 56,07 % и потратил восемьдесят шесть. Напечатанное
  одним числом, второе выглядит как усиленная версия первого — и не является ею.
- **Одна шкала глубины на всю доску.** Масштабировать каждую строку по её собственному худшему
  моменту — значит нарисовать 0,2 % фонда денежного рынка бездной размером с 56 % CSI 500, на доске,
  весь смысл которой в том, что эти двое несравнимы. Поэтому эта строка — плоская линия, прижатая к
  своей линии максимума, и **именно эта прямота и есть то, что она говорит**.
- **С поправкой, ежемесячно и от собственного первого месяца** — по причинам, которые приводит гонка
  классов активов: выплаты фонда никогда не появляются в его цене, а инструмент, пришедший в 2019
  году, не измеряется по максимуму, которого у него не было.
- **Строки по-прежнему бегут.** Они упорядочены по тому, насколько ниже своего максимума находятся, —
  ближайший к своему максимуму сверху — и меняются местами по мере того, как идут месяцы.
- **Золото и товарный фонд на момент измерения были всё ещё под водой** — доска сообщает такое падение
  как открытое, потому что диапазон закончился раньше, чем оно было залечено.

Не зависит от настройки рынка: все восемь котируются на континентальной бирже. Меньше двенадцати
месяцев в диапазоне отклоняется.
""",

    "tr": """Bir satır, **bir varlığın kendi zirvesinin ne kadar altında olduğudur** — ne kazandığı değil, onu
kazanmanın neye mal olduğu. Varlık sınıfları yarışındaki sekiz varlığın aynısı, ama birbirine karşı
değil kendine göre ölçülüyor.

- **Önemli olan eğri.** Bu uygulamanın geri kalanında bir değer uzunluk olarak çizilir ve uzunluk
  ancak o anda suyun ne kadar derin olduğunu söyleyebilir. Derinlik zaman içindeki bir biçimdir:
  dip ve ondan çıkış, eğrinin üzerindeki iki yerdir ve kare boyunca aralarındaki mesafe, arada geçen
  ay sayısıdır.
- **İki sayı birlikte artmaz.** Son on yılda Nasdaq fonu %25,52 düştü ve altı ayda yeniden eşit
  duruma geldi; CSI 500 fonu %56,07 düştü ve seksen altı ay sürdü. Tek sayı olarak basıldığında
  ikincisi, birincisinin ağırlaştırılmış hâli gibi görünür — ve değildir.
- **Tüm tablo için tek derinlik ölçeği.** Her satırı kendi en kötü anına göre ölçeklemek, para piyasası
  fonunun %0,2'sini CSI 500'ün %56'sı büyüklüğünde bir uçurum olarak çizerdi — oysa bu tablonun varlık
  sebebi tam olarak bu ikisinin karşılaştırılamayacağını söylemektir. Bu yüzden o satır, kendi zirve
  çizgisine yapışık düz bir çizgidir ve **o düzlük onun söylediği şeydir**.
- **Düzeltilmiş, aylık ve her varlığın kendi ilk ayından**, varlık sınıflarının verdiği gerekçelerle:
  bir fonun dağıtımları fiyatında hiç görünmez ve 2019'da katılan bir varlık, sahip olmadığı bir
  zirveye göre ölçülmez.
- **Satırlar hâlâ yarışıyor.** Kendi zirvelerinin ne kadar altında olduklarına göre sıralanırlar —
  zirvesine en yakın olan en üstte — ve aylar geçtikçe yer değiştirirler.
- **Altın ve emtia fonu ölçüm yapıldığında hâlâ suyun altındaydı** — tablo bu tür düşüşü açık olarak
  bildirir, çünkü aralık onarılmadan önce sona ermiştir.

Piyasa ayarına bağlı değil: sekizi de anakara borsasında kote. Aralıkta on iki aydan az varsa reddedilir.
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
