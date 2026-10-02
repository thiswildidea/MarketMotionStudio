# -*- coding: utf-8 -*-
r"""把「极端交易日」一章插进 14 份帮助文档。

位置**按章节序号**定，不按标题文字：新章插在「AH 溢价」之后、 「收益矩阵」之前，
因为导航里这三项挨着（市值榜 → AH 溢价 → 极端交易日）。14 份文档的章节数与顺序
必须相同，由 verify 脚本另行检查。

文件是 UTF-8 **带 BOM** + LF：`read_bytes().decode('utf-8-sig')` 读，写回时自己补 BOM。
`utf-8-sig` 只吃掉一个 BOM，文件里若已经叠了两个，要用 `lstrip('\ufeff')` 兜住。

幂等：标题已存在就整章重写。**改页面行为就要回来改这里的 BODIES** —— 市值榜那一章
曾经在榜单改了两次之后仍写着旧理由，见 `port-marketcap-help.py` 的说明。

用法：python tools\port-extremedays-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 插在第 8 章「AH 溢价」之后（0 基下标 7），第 9 章「收益矩阵」之前。
AFTER = 7

TITLES = {
    "zh-Hans": "极端交易日",
    "zh-Hant": "極端交易日",
    "en-US": "Extreme days",
    "ja": "極端な取引日",
    "ko": "극단의 거래일",
    "de": "Extreme Tage",
    "fr": "Jours extrêmes",
    "it": "Giorni estremi",
    "es": "Días extremos",
    "pt-BR": "Dias extremos",
    "pl": "Ekstremalne dni",
    "cs": "Extrémní dny",
    "ru": "Экстремальные дни",
    "tr": "Aşırı günler",
}

BODIES = {
    "zh-Hans": """一个标的，它历史上最猛的那些天——按幅度排成一列横向条形。**这一页的行是「日子」，
不是公司**，全应用只有它这样：每一行的值是那一天相对上一个交易日的复权收盘价变化，而这个名字
一旦定下就不再变。

- **涨跌幅 = 复权收盘价相对上一交易日的变化。** 用复权价是因为除权日本身不是暴跌：一只股票
  分红除权那天价格会掉一大截，不复权的序列会把那天算成史上最大跌幅，而持有的人什么都没损失。
- **按幅度排序，不按正负。** −7.7% 和 +8.1% 是同样大的动作，所以它们排在一起；如果按带符号的
  值排，所有的跌都会沉到所有的涨下面。条形也因此向两边长：**涨向右、红，跌向左、绿**。
- **只有已经发生的日子才进榜。** 区间里幅度最大的 24 天是候选，画面画其中最大的 15 天；一个
  日子在它真正到来之前不参与排序，所以榜是随着年份推进一格一格填满的，而不是一开始就满的。
- **标的只有一个，是当前市场的宽基指数之一**（A 股：上证指数、深证成指、沪深300…）。换市场会
  换掉这一整份清单；换标的或换区间都只存偏好，按「取数」才真的去取。
- **区间最长约 35 年**，限制来自数据源：一次请求只给约 640 根日线，回溯最多二十次。区间太短
  （不足 60 个交易日）会拒绝取数——那种区间里的「最大单日」只是平静月份的波动。
- **画面顶部的日期在走，那是时间轴**，底下是进度条。表头那行写着区间、交易日数与候选天数。
""",
    "zh-Hant": """一個標的，它歷史上最猛的那些天——按幅度排成一列橫向條形。**這一頁的列是「日子」，
不是公司**，全應用只有它這樣：每一列的值是那一天相對上一個交易日的複權收盤價變化，而這個數
一旦定下就不再變。

- **漲跌幅 = 複權收盤價相對上一交易日的變化。** 用複權價是因為除權日本身不是暴跌：一檔股票
  分紅除權那天價格會掉一大截，不複權的序列會把那天算成史上最大跌幅，而持有的人什麼都沒損失。
- **按幅度排序，不按正負。** −7.7% 和 +8.1% 是同樣大的動作，所以它們排在一起；若按帶符號的
  值排，所有的跌都會沉到所有的漲下面。條形也因此向兩邊長：**漲向右、紅，跌向左、綠**。
- **只有已經發生的日子才進榜。** 區間裡幅度最大的 24 天是候選，畫面畫其中最大的 15 天；一個
  日子在它真正到來之前不參與排序，所以榜是隨著年份推進一格一格填滿的，而不是一開始就滿的。
- **標的只有一個，是當前市場的寬基指數之一**（A 股：上證指數、深證成指、滬深300…）。換市場會
  換掉這一整份清單；換標的或換區間都只存偏好，按「取數」才真的去取。
- **區間最長約 35 年**，限制來自資料源：一次請求只給約 640 根日線，回溯最多二十次。區間太短
  （不足 60 個交易日）會拒絕取數——那種區間裡的「最大單日」只是平靜月份的波動。
- **畫面頂部的日期在走，那是時間軸**，底下是進度條。表頭那行寫著區間、交易日數與候選天數。
""",
    "en-US": """One instrument, and the days it moved the most — horizontal bars ranked by size. **The rows of
this board are days, not companies**, which no other page here does: a row's value is how far the
instrument moved on that day against the previous trading day's close, and once that day has
happened the value never changes again.

- **The move is the change in the adjusted close.** Adjusted, because an ex-dividend day is not a
  crash: a stock's price drops by the dividend on that morning, and an unadjusted series would put
  that day at the top of a board of the largest falls in history, when nobody holding it lost
  anything.
- **Ranked by size, not by sign.** −7.7% and +8.1% are the same size of move, so they stand next
  to each other; ranking the signed values would file every fall underneath every rise. The bars
  therefore grow both ways: **a rise to the right, in red; a fall to the left, in green**.
- **A day is ranked only once it has happened.** The twenty-four largest moves in the span are the
  candidates and the frame draws the fifteen largest of those; a day does not take part until its
  own date arrives, so the board fills in as the years pass rather than starting full.
- **There is one instrument, one of the current market's broad indices** (in the A-share market:
  the Shanghai composite, the Shenzhen component, the CSI 300 and so on). Changing the market
  changes the whole list; changing the instrument or the span only saves a preference — nothing is
  fetched until 取数 is pressed.
- **The longest span is about thirty-five years**, which is the source's limit: one request carries
  about 640 daily bars and the walk makes at most twenty. A span with fewer than sixty trading days
  is refused — the largest single day inside a quiet month is not a fact worth a board.
- **The date at the top of the frame is the time axis**, and the bar underneath it is the progress.
  The header line carries the span, the trading-day count and the number of candidate days.
""",
    "ja": """銘柄は一つ、その歴史で最も動いた日々——大きさ順に並べた横向きのバー。**このボードの
行は「会社」ではなく「日」です**。ここだけの特徴で、行の値はその日の、前の取引日の終値に対する
動きであり、その日が過ぎれば値はもう変わりません。

- **値動きは調整済み終値の変化です。** 調整済みを使うのは、配当落ち日が暴落ではないからです。
  配当落ちの朝に株価は下落しますが、未調整の系列はそれを史上最大の下落としてしまいます。
- **符号ではなく大きさで並べます。** −7.7% と +8.1% は同じ大きさの動きなので隣に並びます。
  符号つきの値で並べると、すべての下落がすべての上昇の下に沈みます。バーはしたがって
  両側に伸びます。**上昇は右・赤、下落は左・緑**です。
- **その日が来るまでは順位に入りません。** 期間内で最も大きい 24 日が候補で、画面にはそのうち
  大きい 15 日を描きます。自分の日が来るまでその行は並びに参加しないので、表は年が進むにつれて
  埋まっていきます。
- **銘柄は一つ、現在の市場の主要指数のいずれかです**（A 株：上海総合、深セン成分、滬深300
  など）。市場を変えるとリストごと変わります。銘柄や期間の変更は偏好を保存するだけで、
  「取数」を押すまでは取得しません。
- **最長は約 35 年**で、これはソースの制限です（1 回の要求は約 640 本、さかのぼりは最大 20
  回）。60 取引日に満たない期間は拒否されます。
- **画面上部の日付が時間軸**、下が進捗バーです。ヘッダー行には期間、取引日数、候補日数が
  並びます。
""",
    "ko": """종목은 하나, 그리고 그 역사에서 가장 크게 움직인 날들 — 크기순으로 세운 가로 막대.
**이 보드의 행은 회사가 아니라 '날'입니다.** 이 앱에서 유일한 방식으로, 행의 값은 그날의
직전 거래일 종가 대비 움직임이며, 그날이 지나면 값은 다시는 바뀌지 않습니다.

- **움직임은 조정 종가의 변화입니다.** 조정가를 쓰는 이유는 배당락일이 폭락이 아니기 때문입니다.
  배당락일 아침 주가는 떨어지지만, 무조정 시계열은 그날을 역사상 최대 낙폭으로 올려 버립니다.
- **부호가 아니라 크기로 세웁니다.** −7.7%와 +8.1%는 같은 크기의 움직임이므로 나란히 놓입니다.
  부호가 있는 값으로 세우면 모든 하락이 모든 상승 아래로 가라앉습니다. 그래서 막대는 양쪽으로
  자랍니다. **오름은 오른쪽·빨강, 내림은 왼쪽·초록**입니다.
- **그날이 와야 순위에 오릅니다.** 구간에서 가장 큰 24일이 후보이고, 화면에는 그중 큰 15일을
  그립니다. 자기 날이 오기 전까지 그 행은 순위에 참여하지 않으므로, 표는 세월이 흐르며 채워집니다.
- **종목은 하나, 현재 시장의 대표 지수 가운데 하나입니다**(A주: 상하이종합, 선전성분,
  후선300 등). 시장을 바꾸면 목록 전체가 바뀝니다. 종목이나 구간을 바꾸는 것은 선호만 저장하며,
  '取数'를 눌러야 실제로 가져옵니다.
- **최장은 약 35년**이며 이는 출처의 한계입니다(요청 한 번에 약 640개, 최대 20회 소급).
  60 거래일이 안 되는 구간은 거부됩니다.
- **화면 위쪽의 날짜가 시간축**, 아래는 진행 바입니다. 헤더 줄에는 구간, 거래일 수,
  후보 일수가 적힙니다.
""",
    "de": """Ein Instrument und die Tage, an denen es sich am stärksten bewegt hat — waagrechte Balken,
nach Größe gereiht. **Die Zeilen dieses Tableaus sind Tage, keine Unternehmen**, was sonst keine
Seite hier tut: Der Wert einer Zeile ist die Bewegung gegenüber dem Schlusskurs des vorherigen
Handelstags, und sobald der Tag vergangen ist, ändert sich dieser Wert nie wieder.

- **Die Bewegung ist die Veränderung des bereinigten Schlusskurses.** Bereinigt, weil ein
  Ex-Dividenden-Tag kein Crash ist: Der Kurs fällt an jenem Morgen um die Dividende, und eine
  unbereinigte Reihe setzte diesen Tag an die Spitze der größten Verluste der Geschichte, obwohl
  niemand, der die Aktie hielt, etwas verloren hat.
- **Nach Größe gereiht, nicht nach Vorzeichen.** −7,7 % und +8,1 % sind gleich große Bewegungen
  und stehen daher nebeneinander; nach Vorzeichen gereiht läge jedes Minus unter jedem Plus.
  Deshalb wachsen die Balken in beide Richtungen: **ein Plus nach rechts, rot; ein Minus nach
  links, grün**.
- **Ein Tag zählt erst, wenn er vergangen ist.** Die vierundzwanzig größten Bewegungen des
  Zeitraums sind die Kandidaten, gezeichnet werden die fünfzehn größten davon. Ein Tag nimmt erst
  an der Reihung teil, wenn sein Datum gekommen ist, darum füllt sich das Tableau mit den Jahren.
- **Es gibt ein Instrument, einen breiten Index des aktuellen Marktes** (im A-Aktien-Markt:
  Shanghai Composite, Shenzhen Component, CSI 300 und so weiter). Ein anderer Markt tauscht die
  ganze Liste; ein anderes Instrument oder ein anderer Zeitraum speichert nur eine Einstellung —
  geholt wird erst mit 取数.
- **Der längste Zeitraum ist etwa fünfunddreißig Jahre**, das ist die Grenze der Quelle: Eine
  Anfrage liefert etwa 640 Tageskerzen, der Rücklauf macht höchstens zwanzig. Weniger als sechzig
  Handelstage werden abgelehnt — der größte Tag eines ruhigen Monats ist kein Fakt für ein Tableau.
- **Das Datum oben im Bild ist die Zeitachse**, der Balken darunter der Fortschritt. Die
  Kopfzeile nennt den Zeitraum, die Zahl der Handelstage und die Zahl der Kandidatentage.
""",
    "fr": """Un instrument, et les jours où il a le plus bougé — des barres horizontales classées par
ampleur. **Les lignes de ce tableau sont des jours, pas des entreprises**, ce qu'aucune autre page
ici ne fait : la valeur d'une ligne est le mouvement de ce jour par rapport à la clôture du jour de
cotation précédent, et une fois ce jour passé la valeur ne change plus jamais.

- **Le mouvement est la variation du cours de clôture ajusté.** Ajusté, parce qu'un jour de
  détachement de dividende n'est pas un krach : le cours baisse du montant du dividende ce matin-là,
  et une série non ajustée placerait ce jour en tête des plus grandes baisses de l'histoire, alors
  que personne n'a rien perdu.
- **Classé par ampleur, pas par signe.** −7,7 % et +8,1 % sont des mouvements de même taille et se
  tiennent donc côte à côte ; classer les valeurs signées mettrait chaque baisse sous chaque hausse.
  Les barres poussent donc des deux côtés : **une hausse vers la droite, en rouge ; une baisse vers
  la gauche, en vert**.
- **Un jour n'est classé qu'une fois arrivé.** Les vingt-quatre plus grands mouvements de la période
  sont les candidats et l'image en dessine les quinze plus grands ; un jour ne participe pas avant sa
  propre date, donc le tableau se remplit au fil des années au lieu d'être plein dès le début.
- **Il y a un seul instrument, l'un des indices larges du marché courant** (dans le marché A :
  le composite de Shanghai, le composant de Shenzhen, le CSI 300 et ainsi de suite). Changer de
  marché change toute la liste ; changer d'instrument ou de période ne fait qu'enregistrer une
  préférence — rien n'est chargé avant d'avoir pressé 取数.
- **La période la plus longue est d'environ trente-cinq ans**, c'est la limite de la source : une
  requête porte environ 640 barres quotidiennes et le retour en arrière en fait vingt au plus. Une
  période de moins de soixante jours de cotation est refusée — le plus grand jour d'un mois calme
  n'est pas un fait qui mérite un tableau.
- **La date en haut de l'image est l'axe du temps**, la barre dessous est la progression. La ligne
  d'en-tête porte la période, le nombre de jours de cotation et le nombre de jours candidats.
""",
    "it": """Uno strumento e i giorni in cui si è mosso di più — barre orizzontali ordinate per ampiezza.
**Le righe di questo quadro sono giorni, non aziende**, cosa che nessun'altra pagina qui fa: il
valore di una riga è lo spostamento di quel giorno rispetto alla chiusura del giorno precedente, e
una volta che quel giorno è passato il valore non cambia più.

- **Il movimento è la variazione del close rettificato.** Rettificato, perché un giorno di stacco
  del dividendo non è un crollo: quel mattino il prezzo scende del dividendo, e una serie non
  rettificata metterebbe quel giorno in cima alle più grandi cadute della storia, mentre chi
  deteneva il titolo non ha perso nulla.
- **Ordinato per ampiezza, non per segno.** −7,7 % e +8,1 % sono movimenti della stessa misura e
  quindi stanno vicini; ordinare i valori con segno metterebbe ogni ribasso sotto ogni rialzo. Le
  barre crescono quindi da entrambi i lati: **un rialzo a destra, in rosso; un ribasso a sinistra,
  in verde**.
- **Un giorno entra in classifica solo quando è arrivato.** I ventiquattro movimenti più grandi del
  periodo sono i candidati e il fotogramma ne disegna i quindici più grandi; un giorno non partecipa
  finché non arriva la sua data, così il quadro si riempie con il passare degli anni invece di
  essere pieno dall'inizio.
- **C'è un solo strumento, uno degli indici ampi del mercato corrente** (nel mercato A: il
  composite di Shanghai, il componente di Shenzhen, il CSI 300 e così via). Cambiare mercato
  sostituisce tutta la lista; cambiare strumento o periodo salva solo una preferenza — non si
  scarica nulla finché non si preme 取数.
- **Il periodo più lungo è di circa trentacinque anni**, che è il limite della fonte: una richiesta
  porta circa 640 barre giornaliere e il riavvolgimento ne fa al massimo venti. Un periodo con meno
  di sessanta giorni di negoziazione viene rifiutato — il giorno più grande di un mese tranquillo
  non è un fatto che merita un quadro.
- **La data in alto nel fotogramma è l'asse del tempo**, la barra sotto è l'avanzamento. La riga
  di intestazione porta il periodo, il numero di giorni di negoziazione e il numero di giorni
  candidati.
""",
    "es": """Un instrumento y los días en que más se movió — barras horizontales ordenadas por magnitud.
**Las filas de este tablero son días, no empresas**, algo que no hace ninguna otra página: el valor
de una fila es cuánto se movió ese día respecto al cierre del día anterior, y una vez ocurrido ese
día el valor ya no cambia.

- **El movimiento es la variación del cierre ajustado.** Ajustado, porque un día de descuento de
  dividendo no es un desplome: esa mañana el precio cae el importe del dividendo, y una serie sin
  ajustar pondría ese día a la cabeza de las mayores caídas de la historia, cuando nadie perdió
  nada.
- **Ordenado por magnitud, no por signo.** −7,7 % y +8,1 % son movimientos del mismo tamaño y por
  eso se colocan juntos; ordenar por el valor con signo pondría cada bajada debajo de cada subida.
  Las barras crecen hacia los dos lados: **una subida hacia la derecha, en rojo; una bajada hacia
  la izquierda, en verde**.
- **Un día se clasifica solo cuando ha ocurrido.** Los veinticuatro movimientos más grandes del
  periodo son los candidatos y el fotograma dibuja los quince mayores; un día no participa hasta
  que llega su fecha, así que el tablero se llena con los años en lugar de empezar lleno.
- **Hay un solo instrumento, uno de los índices amplios del mercado actual** (en el mercado A:
  el compuesto de Shanghái, el componente de Shenzhen, el CSI 300 y así sucesivamente). Cambiar de
  mercado cambia toda la lista; cambiar de instrumento o de periodo solo guarda una preferencia —
  no se descarga nada hasta pulsar 取数.
- **El periodo más largo es de unos treinta y cinco años**, que es el límite de la fuente: una
  petición trae unas 640 barras diarias y el retroceso hace veinte como máximo. Un periodo con
  menos de sesenta días de negociación se rechaza — el día más grande de un mes tranquilo no es un
  dato que merezca un tablero.
- **La fecha en la parte superior es el eje del tiempo** y la barra de abajo es el progreso. La
  línea de encabezado lleva el periodo, el número de días de negociación y el de días candidatos.
""",
    "pt-BR": """Um instrumento e os dias em que ele mais se moveu — barras horizontais ordenadas por
tamanho. **As linhas deste quadro são dias, não empresas**, o que nenhuma outra página aqui faz: o
valor de uma linha é quanto aquele dia se moveu em relação ao fechamento do dia anterior e, depois
que o dia passa, o valor nunca mais muda.

- **O movimento é a variação do fechamento ajustado.** Ajustado, porque um dia de desconto de
  dividendo não é um crash: naquela manhã o preço cai o valor do dividendo, e uma série sem ajuste
  colocaria esse dia no topo das maiores quedas da história, quando ninguém perdeu nada.
- **Ordenado por tamanho, não por sinal.** −7,7 % e +8,1 % são movimentos do mesmo tamanho e por
  isso ficam lado a lado; ordenar pelo valor com sinal poria cada queda abaixo de cada alta. As
  barras crescem para os dois lados: **alta para a direita, em vermelho; queda para a esquerda, em
  verde**.
- **Um dia só entra na classificação quando acontece.** Os vinte e quatro maiores movimentos do
  período são os candidatos e o quadro desenha os quinze maiores deles; um dia não participa até
  que sua data chegue, então o quadro se preenche com os anos em vez de começar cheio.
- **Há um único instrumento, um dos índices amplos do mercado atual** (no mercado A: o composto de
  Xangai, o componente de Shenzhen, o CSI 300 e assim por diante). Mudar de mercado troca toda a
  lista; mudar o instrumento ou o período só salva uma preferência — nada é buscado até apertar 取数.
- **O período mais longo é de cerca de trinta e cinco anos**, que é o limite da fonte: um pedido
  traz cerca de 640 barras diárias e o retrocesso faz no máximo vinte. Um período com menos de
  sessenta dias de negociação é recusado — o maior dia de um mês tranquilo não é um fato que mereça
  um quadro.
- **A data no topo do quadro é o eixo do tempo** e a barra abaixo é o progresso. A linha de
  cabeçalho traz o período, o número de dias de negociação e o de dias candidatos.
""",
    "pl": """Jeden instrument i dni, w których poruszył się najmocniej — poziome słupki uporządkowane
według wielkości. **Wierszami tej tablicy są dni, nie spółki**, czego nie robi żadna inna strona:
wartością wiersza jest ruch z danego dnia względem zamknięcia poprzedniej sesji i gdy ten dzień
minie, wartość już się nie zmienia.

- **Ruch to zmiana skorygowanej ceny zamknięcia.** Skorygowanej, bo dzień odcięcia dywidendy nie
  jest krachem: tego ranka cena spada o dywidendę, a seria bez korekty umieściłaby ten dzień na
  czele największych spadków w historii, choć nikt nic nie stracił.
- **Uporządkowane według wielkości, nie według znaku.** −7,7 % i +8,1 % to ruchy tej samej
  wielkości, więc stoją obok siebie; sortowanie wartości ze znakiem umieściłoby każdy spadek pod
  każdym wzrostem. Słupki rosną więc w obie strony: **wzrost w prawo, na czerwono; spadek w lewo,
  na zielono**.
- **Dzień liczy się dopiero, gdy nadejdzie.** Dwudziestu czterech kandydatów to największe ruchy
  okresu, a kadr rysuje piętnaście największych z nich. Dzień nie bierze udziału w rankingu, póki
  nie nadejdzie jego data, więc tablica zapełnia się wraz z latami zamiast być pełna od początku.
- **Instrument jest jeden, jeden z szerokich indeksów bieżącego rynku** (na rynku A: Shanghai
  Composite, Shenzhen Component, CSI 300 i tak dalej). Zmiana rynku wymienia całą listę; zmiana
  instrumentu lub okresu tylko zapisuje preferencję — nic nie jest pobierane, dopóki nie naciśniesz
  取数.
- **Najdłuższy okres to około trzydzieści pięć lat**, co jest ograniczeniem źródła: jedno żądanie
  niesie około 640 świec dziennych, a cofanie wykonuje się najwyżej dwadzieścia razy. Okres
  krótszy niż sześćdziesiąt sesji jest odrzucany — największy dzień spokojnego miesiąca to nie jest
  fakt wart tablicy.
- **Data u góry kadru to oś czasu**, a pasek pod nią to postęp. Wiersz nagłówka niesie okres,
  liczbę sesji i liczbę dni kandydackich.
""",
    "cs": """Jeden nástroj a dny, kdy se pohnul nejvíce — vodorovné pruhy seřazené podle velikosti.
**Řádky této tabulky jsou dny, ne firmy**, co žádná jiná strana nedělá: hodnotou řádku je pohyb
onoho dne proti závěru předchozího obchodního dne, a jakmile ten den nastane, hodnota se už nezmění.

- **Pohyb je změna upravené závěrečné ceny.** Upravené, protože den odpočtu dividendy není krach:
  toho rána cena klesne o dividendu a neupravená řada by ten den postavila na vrchol největších
  pádů historie, přestože nikdo nic neztratil.
- **Řazeno podle velikosti, ne podle znaménka.** −7,7 % a +8,1 % jsou pohyby stejné velikosti, a
  tak stojí vedle sebe; řazení podle hodnoty se znaménkem by každý pokles odsunulo pod každý růst.
  Pruhy proto rostou oběma směry: **růst doprava, červeně; pokles doleva, zeleně**.
- **Den se počítá, až když nastane.** Kandidáty je dvacet čtyři největších pohybů období a snímek
  kreslí patnáct největších z nich; den se řazení neúčastní, dokud nepřijde jeho datum, takže se
  tabulka zaplňuje s léty místo aby byla plná od začátku.
- **Nástroj je jeden, jeden ze širokých indexů aktuálního trhu** (na trhu A: Shanghai Composite,
  Shenzhen Component, CSI 300 a tak dále). Změna trhu vymění celý seznam; změna nástroje nebo
  období jen uloží předvolbu — nic se nestahuje, dokud nestisknete 取数.
- **Nejdelší období je asi třicet pět let**, což je mez zdroje: jedna žádost nese asi 640 denních
  svíček a vracení se provede nejvýše dvacetkrát. Období kratší než šedesát obchodních dnů je
  odmítnuto — největší den klidného měsíce není fakt hodný tabulky.
- **Datum nahoře ve snímku je časová osa** a pruh pod ním je průběh. Hlavičková řada nese období,
  počet obchodních dnů a počet kandidátních dnů.
""",
    "ru": """Один инструмент и дни, когда он двигался сильнее всего — горизонтальные полосы,
упорядоченные по величине. **Строки этой таблицы — дни, а не компании**, чего нет больше ни на
одной странице: значение строки — насколько инструмент сдвинулся в этот день относительно
закрытия предыдущего торгового дня, и как только этот день прошёл, значение больше не меняется.

- **Движение — это изменение скорректированного закрытия.** Скорректированного, потому что день
  отсечки дивиденда — это не обвал: в то утро цена падает на величину дивиденда, и ряд без коррекции
  поставил бы этот день во главе крупнейших падений в истории, хотя никто ничего не потерял.
- **Ранжируется по величине, а не по знаку.** −7,7 % и +8,1 % — движения одной величины, поэтому
  они стоят рядом; сортировка по значению со знаком поместила бы каждое падение под каждый рост.
  Полосы поэтому растут в обе стороны: **рост вправо, красным; падение влево, зелёным**.
- **День попадает в рейтинг, только когда наступил.** Кандидаты — двадцать четыре крупнейших
  движения периода, кадр рисует пятнадцать крупнейших из них; день не участвует, пока не пришла его
  дата, поэтому таблица заполняется по мере лет, а не полна с самого начала.
- **Инструмент один, один из широких индексов текущего рынка** (на рынке A: сводный Шанхая,
  компонент Шэньчжэня, CSI 300 и так далее). Смена рынка меняет весь список; смена инструмента или
  периода лишь сохраняет настройку — ничего не загружается, пока не нажата 取数.
- **Самый длинный период — около тридцати пяти лет**, это предел источника: один запрос несёт около
  640 дневных баров, а возврат назад делается не более двадцати раз. Период короче шестидесяти
  торговых дней отклоняется — самый большой день спокойного месяца не факт, достойный таблицы.
- **Дата вверху кадра — это ось времени**, полоса под ней — прогресс. Строка заголовка несёт
  период, число торговых дней и число дней-кандидатов.
""",
    "tr": """Tek bir enstrüman ve en çok hareket ettiği günler — büyüklüğe göre sıralanmış yatay
çubuklar. **Bu tablonun satırları şirket değil gündür**, buradaki başka hiçbir sayfa bunu yapmaz:
bir satırın değeri, o günün önceki işlem gününün kapanışına göre hareketidir ve o gün geçtiğinde
değer bir daha değişmez.

- **Hareket, düzeltilmiş kapanıştaki değişimdir.** Düzeltilmiş, çünkü temettü düşüm günü bir çöküş
  değildir: o sabah fiyat temettü kadar düşer ve düzeltilmemiş seri bu günü tarihin en büyük
  düşüşlerinin başına koyardı — oysa elinde tutan kimse bir şey kaybetmemiştir.
- **İşarete göre değil büyüklüğe göre sıralanır.** −%7,7 ile +%8,1 aynı büyüklükte hareketlerdir,
  bu yüzden yan yana dururlar; işaretli değere göre sıralamak her düşüşü her yükselişin altına
  koyardı. Çubuklar bu yüzden iki yana büyür: **yükseliş sağa, kırmızı; düşüş sola, yeşil**.
- **Bir gün ancak gerçekleştiğinde sıralamaya girer.** Dönemin en büyük yirmi dört hareketi
  adaydır, kare bunların en büyük on beşini çizer; bir gün kendi tarihi gelmeden sıralamaya katılmaz,
  bu yüzden tablo baştan dolu olmak yerine yıllar geçtikçe dolar.
- **Tek bir enstrüman vardır: mevcut piyasanın geniş endekslerinden biri** (A pazarında: Şanghay
  bileşik, Shenzhen bileşen, CSI 300 ve benzeri). Pazarı değiştirmek tüm listeyi değiştirir;
  enstrümanı veya dönemi değiştirmek yalnızca tercihi kaydeder — 取数 tuşuna basılmadan hiçbir şey
  çekilmez.
- **En uzun dönem yaklaşık otuz beş yıldır**, bu kaynağın sınırıdır: bir istek yaklaşık 640 günlük
  bar taşır ve geriye yürüme en çok yirmi kez yapılır. Altmış işlem gününden kısa dönemler
  reddedilir — sakin bir ayın en büyük günü tabloya değer bir olgu değildir.
- **Karenin üstündeki tarih zaman eksenidir**, altındaki çubuk ilerlemedir. Başlık satırı dönemi,
  işlem günü sayısını ve aday gün sayısını taşır.
""",
}


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
