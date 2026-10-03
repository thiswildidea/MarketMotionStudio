# -*- coding: utf-8 -*-
r"""把「债市固收竞速」一章插进 14 份帮助文档。

位置**按章节序号**定，不按标题文字：新章插在第 12 章「大类资产」之后、第 13 章
「回撤与修复」之前，因为导航里这两页挨着——那一榜把债市留成八行里的一行国债 ETF，
这一页才是债市本身。14 份文档的章节数与顺序必须相同，由 verify 脚本另行检查。

文件是 UTF-8 + LF，**BOM 照原样**（现在这 14 份都不带）：读时记下有没有，写回时照原样补。
写死一个 BOM 会让每次运行都改掉 14 份文件的第一行，而那只在 diff 里看得出来。
`utf-8-sig` 只吃掉一个 BOM，文件里若已经叠了两个，要用 `lstrip('\ufeff')` 兜住。

幂等：标题已存在就整章重写。**改页面行为就要回来改这里的 BODIES** —— 市值榜那一章
曾经在榜单改了两次之后仍写着旧理由，见 `port-marketcap-help.py` 的说明。

用法：python tools\port-bondrace-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 插在第 12 章「大类资产」之后（0 基下标 11），第 13 章「回撤与修复」之前。
AFTER = 11

TITLES = {
    "zh-Hans": "债市固收竞速",
    "zh-Hant": "債市固收競速",
    "en-US": "Bond market",
    "ja": "債券市場",
    "ko": "채권시장",
    "de": "Anleihemarkt",
    "fr": "Marché obligataire",
    "it": "Mercato obbligazionario",
    "es": "Renta fija",
    "pt-BR": "Mercado de títulos",
    "pl": "Rynek obligacji",
    "cs": "Trh dluhopisů",
    "ru": "Рынок облигаций",
    "tr": "Tahvil piyasası",
}

BODIES = {
    "zh-Hans": """一条债券指数一行，条形是**价格变动**——这不等于持有它赚了多少。

- **票息不在数字里。** 这九行全是指数，而源端对指数忽略复权参数，回来的就是报价。债券的收益
  大头是票息，票息永远不出现在报价里：持有者真正赚到的比画面上多，而且每一行差得不
  一样多。
- **和大类资产那一榜故意相反。** 那一榜画的是复权序列，因为基金会派息；这一页不动，因为
  指数不派息。两榜之间不能互相比。
- **九条是内建的固定清单**，不是你自己维护的列表。原本要的「中证全债」在这个源上不存在：
  长得像它的那个代码是「沪分离债」，月线停在 2015 年 8 月；把整个指数代码段扫了一遍也没
  找到全债指数。空出来的位置给了源上答得最深的那几条信用债。
- **起点各不相同。** 最早的一行从 2003-02 开始，深证转债要到 2014-08 才有，所以在十年榜上
  它晚了五年才进场。还没开始的行是缺席，不是 0.00%。
- **月线**，一格一个月；本页不受市场设置影响。不足 12 个月会拒绝取数。
- **从区间里第一个完整月开始。** 源端只会按月作答，一根月线就是那个整月，所以窗口从某个月
  的中间开始时，那个不完整的月不算——起点落在它之后的下一个整月。这就是为什么「近 10 年」
  画出来是 119 个月而不是 120：少的那一个月落在窗口之外。表头那两个日期，就是真正起算和
  结束的日期。
- **三个分组**：全部九条、纯债六条（不含转债）、可转债三条。
""",
    "zh-Hant": """一條債券指數一行，條形是**價格變動**——這不等於持有它賺了多少。

- **票息不在數字裡。** 這九行全是指數，而源端對指數忽略複權參數，回來的就是報價。債券的收益
  大頭是票息，票息永遠不出現在報價裡：持有者真正賺到的比畫面上多，而且每一行差得不
  一樣多。
- **和大類資產那一榜故意相反。** 那一榜畫的是複權序列，因為基金會派息；這一頁不動，因為
  指數不派息。兩榜之間不能互相比。
- **九條是內建的固定清單**，不是你自己維護的列表。原本要的「中證全債」在這個源上不存在：
  長得像它的那個代碼是「滬分離債」，月線停在 2015 年 8 月；把整個指數代碼段掃了一遍也沒
  找到全債指數。空出來的位置給了源上答得最深的那幾條信用債。
- **起點各不相同。** 最早的一行從 2003-02 開始，深證轉債要到 2014-08 才有，所以在十年榜上
  它晚了五年才進場。還沒開始的行是缺席，不是 0.00%。
- **月線**，一格一個月；本頁不受市場設定影響。不足 12 個月會拒絕取數。
- **從區間裡第一個完整月開始。** 源端只會按月作答，一根月線就是那個整月，所以視窗從某個月
  的中間開始時，那個不完整的月不算——起點落在它之後的下一個整月。這就是為什麼「近 10 年」
  畫出來是 119 個月而不是 120：少的那一個月落在視窗之外。表頭那兩個日期，就是真正起算和
  結束的日期。
- **三個分組**：全部九條、純債六條（不含轉債）、可轉債三條。
""",
    "en-US": """One row per bond index, and the bar is a **price change** — which is not the same thing as what
holding it earned.

- **A coupon is not in the number.** All nine rows are indices, and the source ignores the
  adjustment parameter for an index, so what comes back is the quote. A bond pays most of its
  return as coupon, and a coupon never appears in a quote: a holder earned more than this board
  shows, and by different amounts on different rows.
- **Deliberately the opposite of the asset race.** That board is drawn on the adjusted series
  because a fund pays out; this one is left alone because an index does not. The two boards
  cannot be read against each other.
- **Nine rows, and the roster is built in** rather than a list you keep. A CSI total-bond index
  was wanted and does not exist on this source: the code that looks like it is the Shanghai
  detachable-bond index, whose monthly series stops in August 2015, and a sweep of the entire
  index code space found no total-bond index at all. Those seats went to the deepest credit
  indices the source does answer.
- **Start dates differ.** The earliest row begins in 2003-02 and the Shenzhen convertible index
  only in 2014-08, so on a ten-year board it joins five years in. A row that has not started is
  absent, not 0.00%.
- **Monthly**, one bar per month, and the market setting does not govern this page. Fewer than
  twelve months is refused.
- **Begins on the first whole month in the range.** The source answers only in whole months and a
  monthly bar *is* that whole month, so when a window opens in the middle of one that partial
  month does not count — the board starts on the next whole month after it. That is why "past 10
  years" draws 119 months rather than 120: the missing one lies outside the window. The two dates
  in the header are the dates it really begins and ends on.
- **Three groups**: all nine, the six straight bonds without convertibles, and the three
  convertibles.
""",
    "ja": """債券指数 1 本につき 1 行。バーは**価格の変動**であり、保有して稼いだ額とは同じではありません。

- **クーポンは数字に入っていません。** 9 行すべてが指数であり、情報源は指数に対して調整
  パラメータを無視するため、返ってくるのは気配値です。債券は収益の大部分をクーポンで
  支払い、クーポンは気配値に現れません。保有者が実際に得たものはこの盤面より多く、
  しかも行ごとに差があります。
- **資産クラス競速とは意図的に逆です。** あちらはファンドが分配するので調整済み系列で描き、
  こちらは指数が分配しないのでそのままです。二つの盤面は比較できません。
- **9 行は組み込みの固定リスト**で、自分で維持するリストではありません。本来欲しかった
  「中証全債」はこの情報源に存在しません。似たコードは「滬分離債」で月次系列が 2015 年
  8 月で止まっており、指数コード空間を全部走査しても全債指数は見つかりませんでした。
  空いた枠は情報源が答える最深の信用債に回しました。
- **開始はまちまちです。** 最も早い行は 2003-02、深証転債は 2014-08 からなので、10 年の
  盤面には 5 年遅れて登場します。まだ始まっていない行は不在であり、0.00% ではありません。
- **月次**、1 か月に 1 本。市場設定はこのページを管轄しません。12 か月未満は拒否されます。
- **期間内で最初の完全な月から始まります。** 情報源は月単位でしか答えず、月足はその月そのものな
  ので、期間が月の途中から始まる場合、その不完全な月は数えません——起点はその次の完全な月に
  なります。「過去 10 年」が 120 ではなく 119 か月になるのはそのためで、足りない 1 か月は期間の
  外にあります。ヘッダーの 2 つの日付が、実際の開始日と終了日です。
- **3 つのグループ**: 9 本すべて、転換債を除く 6 本の普通債、転換債 3 本。
""",
    "ko": """채권 지수당 한 행이며, 막대는 **가격 변동**입니다. 보유해서 벌어들인 것과는 같지 않습니다.

- **쿠폰은 숫자에 없습니다.** 아홉 행 모두 지수이고, 데이터 원본은 지수에 대해 조정 매개변수를
  무시하므로 돌아오는 것은 호가입니다. 채권은 수익의 대부분을 쿠폰으로 지급하며 쿠폰은 호가에
  나타나지 않습니다. 보유자가 실제로 얻은 것은 이 보드보다 많고, 그 차이는 행마다 다릅니다.
- **자산군 레이스와 의도적으로 반대입니다.** 펀드는 분배하므로 그쪽은 조정 계열로 그리고,
  지수는 분배하지 않으므로 이쪽은 그대로 둡니다. 두 보드는 서로 비교할 수 없습니다.
- **아홉 행은 내장된 고정 목록**이며 직접 관리하는 목록이 아닙니다. 원했던 '중정 전채' 지수는
  이 원본에 존재하지 않습니다. 비슷한 코드는 '상하이 분리채'로 월간 계열이 2015년 8월에
  멈춰 있고, 지수 코드 공간 전체를 훑어도 전채 지수는 없었습니다. 빈자리는 원본이 응답하는
  가장 깊은 신용채에 돌아갔습니다.
- **시작은 제각각입니다.** 가장 이른 행은 2003-02, 선전 전환채 지수는 2014-08부터라 10년 보드에는
  5년 늦게 합류합니다. 아직 시작하지 않은 행은 부재이며 0.00%가 아닙니다.
- **월간**, 한 달에 한 막대. 시장 설정은 이 페이지를 관할하지 않습니다. 12개월 미만은 거부됩니다.
- **구간의 첫 온전한 달부터 시작합니다.** 원본은 월 단위로만 답하고 월봉은 그 달 자체이므로, 구간이
  달 중간에서 시작하면 그 불완전한 달은 세지 않습니다——기점은 그다음 온전한 달입니다.
  '지난 10년'이 120개월이 아니라 119개월로 그려지는 이유가 이것이며, 빠진 한 달은 구간 밖에
  있습니다. 머리말의 두 날짜가 실제 시작일과 종료일입니다.
- **세 그룹**: 전체 9개, 전환채를 뺀 일반채 6개, 전환채 3개.
""",
    "de": """Eine Zeile pro Anleiheindex, und der Balken ist eine **Kursänderung** — nicht dasselbe wie das,
was das Halten eingebracht hat.

- **Der Kupon steckt nicht in der Zahl.** Alle neun Zeilen sind Indizes, und die Quelle ignoriert
  den Adjustierungsparameter bei einem Index, also kommt die Notierung zurück. Eine Anleihe zahlt
  den Großteil ihrer Rendite als Kupon, und ein Kupon erscheint nie in einer Notierung: Wer sie
  hielt, hat mehr verdient, als diese Tafel zeigt — auf jeder Zeile um einen anderen Betrag.
- **Mit Absicht das Gegenteil des Anlageklassen-Rennens.** Jene Tafel wird aus der adjustierten
  Reihe gezeichnet, weil ein Fonds ausschüttet; diese bleibt unangetastet, weil ein Index das nicht
  tut. Die beiden Tafeln sind nicht gegeneinander lesbar.
- **Neun Zeilen, und die Liste ist eingebaut** statt eine, die man selbst pflegt. Ein
  CSI-Gesamtanleiheindex war gewünscht und existiert auf dieser Quelle nicht: Der Code, der so
  aussieht, ist der Shanghai-Abspaltungsanleihen-Index, dessen Monatsreihe im August 2015 endet,
  und eine Durchsuchung des gesamten Index-Coderaums fand überhaupt keinen Gesamtanleiheindex.
  Die Plätze gingen an die tiefsten Kreditindizes, die die Quelle beantwortet.
- **Die Anfänge unterscheiden sich.** Die früheste Zeile beginnt 2003-02, der Shenzhen-Wandlerindex
  erst 2014-08 — auf einer Zehn-Jahres-Tafel stößt er also fünf Jahre später dazu. Eine Zeile, die
  noch nicht begonnen hat, fehlt, statt bei 0,00 % zu stehen.
- **Monatlich**, ein Balken pro Monat, und die Markteinstellung regiert diese Seite nicht. Weniger
  als zwölf Monate werden abgelehnt.
- **Beginnt mit dem ersten vollen Monat im Zeitraum.** Die Quelle antwortet nur in ganzen Monaten,
  und ein Monatsbalken *ist* dieser ganze Monat. Beginnt ein Zeitraum mitten in einem Monat, zählt
  dieser unvollständige Monat nicht — der Kurs startet mit dem nächsten vollen Monat. Deshalb
  zeichnet „letzte 10 Jahre" 119 statt 120 Monate: Der fehlende liegt außerhalb des Zeitraums. Die
  beiden Daten in der Kopfzeile sind die echten Daten.
- **Drei Gruppen**: alle neun, die sechs klassischen Anleihen ohne Wandler, und die drei Wandler.
""",
    "fr": """Une ligne par indice obligataire, et la barre est une **variation de cours** — ce qui n'est pas
la même chose que ce que la détention a rapporté.

- **Le coupon n'est pas dans le chiffre.** Les neuf lignes sont des indices, et la source ignore le
  paramètre d'ajustement pour un indice : ce qui revient est donc la cotation. Une obligation paie
  l'essentiel de son rendement en coupon, et un coupon n'apparaît jamais dans une cotation : le
  détenteur a gagné plus que ce que montre ce tableau, et d'un montant différent sur chaque ligne.
- **Volontairement l'inverse de la course des classes d'actifs.** Ce tableau-là est tracé sur la
  série ajustée parce qu'un fonds distribue ; celui-ci est laissé tel quel parce qu'un indice ne
  distribue pas. Les deux tableaux ne se lisent pas l'un contre l'autre.
- **Neuf lignes, et la liste est intégrée** plutôt qu'entretenue par vous. Un indice CSI « toutes
  obligations » était souhaité et n'existe pas sur cette source : le code qui y ressemble est
  l'indice des obligations détachables de Shanghai, dont la série mensuelle s'arrête en août 2015,
  et un balayage de tout l'espace de codes d'indices n'a trouvé aucun indice obligataire global.
  Ces places sont allées aux indices de crédit les plus profonds que la source répond.
- **Les débuts diffèrent.** La ligne la plus ancienne commence en 2003-02 et l'indice convertible de
  Shenzhen seulement en 2014-08 : sur un tableau de dix ans, il arrive donc cinq ans plus tard. Une
  ligne qui n'a pas commencé est absente, pas à 0,00 %.
- **Mensuel**, une barre par mois, et le réglage de marché ne régit pas cette page. Moins de douze
  mois est refusé.
- **Commence au premier mois entier de la plage.** La source ne répond qu'en mois entiers, et une
  barre mensuelle *est* ce mois entier : lorsqu'une plage commence au milieu d'un mois, ce mois
  incomplet ne compte pas — le tableau démarre au mois entier suivant. C'est pourquoi « 10 ans »
  trace 119 mois et non 120 : le mois manquant se trouve hors plage. Les deux dates de l'en-tête
  sont celles du début et de la fin réels.
- **Trois groupes** : les neuf, les six obligations simples sans convertibles, et les trois
  convertibles.
""",
    "it": """Una riga per indice obbligazionario, e la barra è una **variazione di prezzo** — che non è la
stessa cosa di ciò che ha reso la detenzione.

- **La cedola non è nel numero.** Tutte e nove le righe sono indici, e la fonte ignora il parametro
  di rettifica per un indice, quindi ciò che torna è la quotazione. Un'obbligazione paga la
  maggior parte del suo rendimento come cedola, e una cedola non compare mai in una quotazione:
  chi l'ha detenuta ha guadagnato più di quanto mostra questo tabellone, e in misura diversa su
  ogni riga.
- **Volutamente l'opposto della corsa delle classi di attività.** Quel tabellone è disegnato sulla
  serie rettificata perché un fondo distribuisce; questo è lasciato com'è perché un indice non
  distribuisce. I due tabelloni non si leggono l'uno contro l'altro.
- **Nove righe, e la rosa è incorporata** invece di essere un elenco che mantieni tu. Un indice CSI
  «totale obbligazionario» era richiesto e non esiste su questa fonte: il codice che gli somiglia è
  l'indice delle obbligazioni staccabili di Shanghai, la cui serie mensile si ferma ad agosto 2015,
  e una scansione di tutto lo spazio dei codici indice non ha trovato alcun indice obbligazionario
  totale. Quei posti sono andati agli indici creditizi più profondi a cui la fonte risponde.
- **Le partenze differiscono.** La riga più antica inizia nel 2003-02 e l'indice convertibile di
  Shenzhen solo nel 2014-08, quindi su un tabellone decennale entra con cinque anni di ritardo. Una
  riga non ancora iniziata è assente, non a 0,00%.
- **Mensile**, una barra per mese, e l'impostazione di mercato non governa questa pagina. Meno di
  dodici mesi è rifiutato.
- **Inizia dal primo mese intero dell'intervallo.** La fonte risponde solo in mesi interi, e una
  barra mensile *è* quel mese intero: se l'intervallo inizia a metà mese, quel mese incompleto non
  conta — il quadro parte dal mese intero successivo. Ecco perché «ultimi 10 anni» disegna 119
  mesi invece di 120: quello mancante è fuori intervallo. Le due date in intestazione sono quelle
  reali di inizio e fine.
- **Tre gruppi**: tutte e nove, le sei obbligazioni pure senza convertibili, e le tre convertibili.
""",
    "es": """Una fila por índice de bonos, y la barra es una **variación de precio** — que no es lo mismo que
lo que ganó mantenerlo.

- **El cupón no está en el número.** Las nueve filas son índices, y la fuente ignora el parámetro
  de ajuste para un índice, así que lo que vuelve es la cotización. Un bono paga la mayor parte de
  su renta como cupón, y un cupón nunca aparece en una cotización: quien lo mantuvo ganó más de lo
  que muestra este tablero, y en cada fila por un importe distinto.
- **Deliberadamente lo contrario de la carrera de clases de activo.** Aquel tablero se dibuja con la
  serie ajustada porque un fondo reparte; este se deja intacto porque un índice no reparte. Los dos
  tableros no se pueden leer uno contra otro.
- **Nueve filas, y la lista viene incorporada**, no es una lista que mantengas tú. Se quería un
  índice CSI de «todos los bonos» y no existe en esta fuente: el código que se le parece es el
  índice de bonos desgajados de Shanghái, cuya serie mensual se detiene en agosto de 2015, y un
  barrido de todo el espacio de códigos de índice no encontró ningún índice de bonos total. Esas
  plazas fueron a los índices de crédito más profundos que la fuente sí responde.
- **Los inicios difieren.** La fila más antigua empieza en 2003-02 y el índice convertible de
  Shenzhen solo en 2014-08, así que en un tablero de diez años entra con cinco años de retraso. Una
  fila que aún no ha empezado está ausente, no en 0,00 %.
- **Mensual**, una barra por mes, y el ajuste de mercado no gobierna esta página. Menos de doce
  meses se rechaza.
- **Empieza en el primer mes completo del rango.** La fuente solo responde en meses completos, y
  una barra mensual *es* ese mes completo: si el rango empieza a mitad de mes, ese mes incompleto
  no cuenta — el cuadro arranca en el mes completo siguiente. Por eso «últimos 10 años» dibuja 119
  meses y no 120: el que falta queda fuera del rango. Las dos fechas de la cabecera son las de
  inicio y fin reales.
- **Tres grupos**: las nueve, los seis bonos simples sin convertibles, y los tres convertibles.
""",
    "pt-BR": """Uma linha por índice de títulos, e a barra é uma **variação de preço** — que não é o mesmo que o
que a manutenção rendeu.

- **O cupom não está no número.** As nove linhas são índices, e a fonte ignora o parâmetro de ajuste
  para um índice, então o que volta é a cotação. Um título paga a maior parte do seu retorno como
  cupom, e um cupom nunca aparece numa cotação: quem o manteve ganhou mais do que este quadro
  mostra, e em cada linha por um valor diferente.
- **Deliberadamente o oposto da corrida de classes de ativos.** Aquele quadro é desenhado na série
  ajustada porque um fundo distribui; este fica como está porque um índice não distribui. Os dois
  quadros não podem ser lidos um contra o outro.
- **Nove linhas, e a lista é incorporada**, não uma lista que você mantém. Queria-se um índice CSI de
  «todos os títulos» e ele não existe nesta fonte: o código parecido é o índice de títulos
  desmembrados de Xangai, cuja série mensal para em agosto de 2015, e uma varredura de todo o
  espaço de códigos de índice não achou nenhum índice de títulos total. As vagas foram para os
  índices de crédito mais profundos que a fonte responde.
- **Os inícios diferem.** A linha mais antiga começa em 2003-02 e o índice conversível de Shenzhen
  apenas em 2014-08, então num quadro de dez anos ele entra com cinco anos de atraso. Uma linha que
  ainda não começou está ausente, não em 0,00%.
- **Mensal**, uma barra por mês, e a configuração de mercado não rege esta página. Menos de doze
  meses é recusado.
- **Começa no primeiro mês inteiro do intervalo.** A fonte só responde em meses inteiros, e uma
  barra mensal *é* esse mês inteiro: se o intervalo começa no meio de um mês, esse mês incompleto
  não conta — o quadro parte do mês inteiro seguinte. É por isso que «últimos 10 anos» desenha 119
  meses em vez de 120: o que falta fica fora do intervalo. As duas datas do cabeçalho são as de
  início e fim reais.
- **Três grupos**: as nove, os seis títulos simples sem conversíveis, e os três conversíveis.
""",
    "pl": """Jeden wiersz na indeks obligacji, a słupek to **zmiana ceny** — co nie jest tym samym co zarobek
z trzymania.

- **Kuponu nie ma w liczbie.** Wszystkie dziewięć wierszy to indeksy, a źródło ignoruje parametr
  korekty dla indeksu, więc wraca notowanie. Obligacja wypłaca większość zwrotu jako kupon, a kupon
  nigdy nie pojawia się w notowaniu: posiadacz zarobił więcej, niż pokazuje ta tablica, i na każdym
  wierszu o inną kwotę.
- **Celowo odwrotność wyścigu klas aktywów.** Tamta tablica jest rysowana na serii skorygowanej, bo
  fundusz wypłaca; ta zostaje nietknięta, bo indeks nie wypłaca. Obu tablic nie można czytać
  względem siebie.
- **Dziewięć wierszy, a lista jest wbudowana**, nie jest to lista, którą prowadzisz sam. Chciano
  indeksu CSI „wszystkich obligacji” i nie ma go w tym źródle: przypominający go kod to indeks
  obligacji wydzielonych z Shanghai, którego seria miesięczna kończy się w sierpniu 2015, a
  przejrzenie całej przestrzeni kodów indeksów nie znalazło żadnego indeksu całościowego. Miejsca
  te przypadły najgłębszym indeksom kredytowym, na które źródło odpowiada.
- **Początki się różnią.** Najwcześniejszy wiersz zaczyna się 2003-02, a indeks konwertowalny
  Shenzhen dopiero 2014-08, więc na dziesięcioletniej tablicy wchodzi pięć lat później. Wiersza,
  który jeszcze się nie zaczął, nie ma — nie stoi na 0,00%.
- **Miesięcznie**, jeden słupek na miesiąc, a ustawienie rynku tu nie rządzi. Mniej niż dwanaście
  miesięcy jest odrzucane.
- **Zaczyna się od pierwszego pełnego miesiąca w zakresie.** Źródło odpowiada wyłącznie pełnymi
  miesiącami, a słupek miesięczny *to* ten pełny miesiąc: gdy zakres zaczyna się w połowie
  miesiąca, ten niepełny się nie liczy — wykres rusza od następnego pełnego miesiąca. Dlatego
  „ostatnie 10 lat" rysuje 119, a nie 120 miesięcy: brakujący leży poza zakresem. Dwie daty
  w nagłówku to rzeczywisty początek i koniec.
- **Trzy grupy**: wszystkie dziewięć, sześć zwykłych obligacji bez zamiennych i trzy zamienne.
""",
    "cs": """Jeden řádek na dluhopisový index a pruh je **změna ceny** — co není totéž co to, co držení vyneslo.

- **Kupón v čísle není.** Všech devět řádků jsou indexy a zdroj u indexu ignoruje parametr úpravy,
  takže se vrací kotace. Dluhopis vyplácí většinu výnosu jako kupón a kupón se v kotaci nikdy
  neobjeví: držitel si vydělal víc, než tato tabule ukazuje, a na každém řádku o jinou částku.
- **Záměrně opak závodu tříd aktiv.** Tamtato tabule se kreslí z upravené řady, protože fond
  vyplácí; tato zůstává netknutá, protože index nevyplácí. Obě tabule nelze číst jednu proti druhé.
- **Devět řádků a seznam je vestavěný**, ne takový, který si udržujete sami. Chtěl se index CSI
  „všech dluhopisů“ a na tomto zdroji neexistuje: kód, který se mu podobá, je index oddělených
  dluhopisů Šanghaj, jehož měsíční řada končí v srpnu 2015, a prohledání celého prostoru kódů
  indexů nenašlo žádný celkový dluhopisový index. Tato místa připadla nejhlubším úvěrovým indexům,
  na které zdroj odpovídá.
- **Začátky se liší.** Nejstarší řádek začíná 2003-02 a konvertibilní index Šen-čen až 2014-08, takže
  na desetiletou tabuli nastupuje o pět let později. Řádek, který ještě nezačal, chybí — nestojí na
  0,00 %.
- **Měsíčně**, jeden pruh na měsíc, a nastavení trhu tuto stránku neřídí. Méně než dvanáct měsíců je
  odmítnuto.
- **Začíná prvním celým měsícem v rozsahu.** Zdroj odpovídá jen v celých měsících a měsíční
  sloupec *je* ten celý měsíc: začne-li rozsah uprostřed měsíce, tento neúplný měsíc se nepočítá —
  přehled startuje od následujícího celého měsíce. Proto „posledních 10 let" kreslí 119 měsíců
  místo 120: ten chybějící leží mimo rozsah. Dvě data v záhlaví jsou skutečný začátek a konec.
- **Tři skupiny**: všech devět, šest klasických dluhopisů bez konvertibilních a tři konvertibilní.
""",
    "ru": """Одна строка на индекс облигаций, и полоса — это **изменение цены**, а не то, что принесло владение.

- **Купона в числе нет.** Все девять строк — индексы, а источник игнорирует параметр корректировки
  для индекса, поэтому возвращается котировка. Облигация выплачивает большую часть дохода купоном,
  а купон никогда не появляется в котировке: держатель заработал больше, чем показывает эта доска,
  и на каждой строке — на разную величину.
- **Намеренно противоположно гонке классов активов.** Та доска рисуется по скорректированному ряду,
  потому что фонд выплачивает; эта оставлена как есть, потому что индекс не выплачивает. Две доски
  нельзя читать одну против другой.
- **Девять строк, и список встроен**, а не ведётся вами. Хотелось индекс CSI «всех облигаций», и его
  на этом источнике нет: похожий код — это индекс отделяемых облигаций Шанхая, месячный ряд
  которого обрывается в августе 2015 года, а просмотр всего пространства кодов индексов не нашёл
  никакого сводного облигационного индекса. Эти места достались самым глубоким кредитным индексам,
  на которые источник отвечает.
- **Начала различаются.** Самая ранняя строка начинается в 2003-02, а конвертируемый индекс
  Шэньчжэня — лишь в 2014-08, поэтому на десятилетнюю доску он выходит через пять лет. Строка,
  которая ещё не началась, отсутствует, а не стоит в 0,00%.
- **Ежемесячно**, одна полоса на месяц, и настройка рынка этой страницей не управляет. Меньше
  двенадцати месяцев отклоняется.
- **Начинается с первого полного месяца в диапазоне.** Источник отвечает только целыми месяцами,
  а месячный столбик *и есть* этот целый месяц: если диапазон начинается в середине месяца, этот
  неполный месяц не считается — график стартует со следующего полного месяца. Поэтому «последние
  10 лет» рисуют 119 месяцев, а не 120: недостающий лежит вне диапазона. Две даты в шапке —
  настоящие даты начала и конца.
- **Три группы**: все девять, шесть обычных облигаций без конвертируемых и три конвертируемых.
""",
    "tr": """Her tahvil endeksi için bir satır ve çubuk bir **fiyat değişimi** — bu, elde tutmanın kazandırdığı
ile aynı şey değil.

- **Kupon sayıda yok.** Dokuz satır da endeks ve kaynak bir endeks için düzeltme parametresini
  yoksayıyor, dolayısıyla dönen şey kotasyon. Bir tahvil getirisinin çoğunu kupon olarak öder ve
  kupon hiçbir zaman kotasyonda görünmez: elinde tutan, bu tablonun gösterdiğinden fazlasını
  kazandı, hem de her satırda farklı bir tutarla.
- **Bilerek varlık sınıfı yarışının tersi.** O tablo, fon dağıttığı için düzeltilmiş seriden
  çizilir; bu tabloya dokunulmaz, çünkü endeks dağıtmaz. İki tablo birbirine karşı okunamaz.
- **Dokuz satır ve liste yerleşik**, sizin tuttuğunuz bir liste değil. CSI «tüm tahviller» endeksi
  istendi ve bu kaynakta yok: ona benzeyen kod Şanghay ayrılabilir tahvil endeksi ve aylık serisi
  Ağustos 2015'te duruyor; tüm endeks kod uzayının taranması da hiçbir toplam tahvil endeksi
  bulamadı. Bu yerler kaynağın yanıt verdiği en derin kredi endekslerine gitti.
- **Başlangıçlar farklı.** En eski satır 2003-02'de başlıyor, Shenzhen dönüştürülebilir endeksi ise
  ancak 2014-08'de; yani on yıllık tabloya beş yıl geç katılıyor. Henüz başlamamış bir satır yoktur,
  %0,00'de durmaz.
- **Aylık**, ayda bir çubuk, ve pazar ayarı bu sayfayı yönetmez. On iki aydan kısa dönemler
  reddedilir.
- **Aralıktaki ilk tam ayla başlar.** Kaynak yalnızca tam aylarla yanıt verir ve aylık çubuk *o* tam
  aydır: aralık ayın ortasında başlarsa bu eksik ay sayılmaz — tablo ondan sonraki tam ayla başlar.
  «Son 10 yıl»ın 120 değil 119 ay çizmesinin nedeni budur: eksik olan aralığın dışındadır.
  Başlıktaki iki tarih, gerçek başlangıç ve bitiş tarihleridir.
- **Üç grup**: dokuzu da, dönüştürülebilirler olmadan altı düz tahvil ve üç dönüştürülebilir.
""",
}


def main():
    for tag, title in TITLES.items():
        path = HELP / f"help-{tag}.md"

        raw = path.read_bytes()

        # BOM 与 LF 都**照原样**，与 `port-help-ranges.py` 同一条规矩。这 14 份 md 现下都不带
        # BOM（`1459af4` 起就是），而这个脚本原先无条件写回一个 BOM —— 于是每跑一次就把
        # 14 份文件的第 1 行改一遍，diff 里看着像正文被改，其实只有一个不可见字符。
        had_bom = raw.startswith(b"\xef\xbb\xbf")

        text = raw.decode("utf-8-sig").lstrip("\ufeff")
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

        # Where the chapter goes is a position, not a title: the fourteen files use fourteen
        # different languages for the same heading, so the heading text cannot be looked up.
        at = heads[AFTER + 1]

        # Collapse the blank run above the insertion point to exactly one line. The previous
        # chapter's trailing blanks are already there, and the block below starts with a blank of
        # its own run — leaving both in place grew a second and third blank line above the heading
        # on every run, which is the kind of drift a re-run is supposed to be unable to cause.
        while at > 1 and lines[at - 1].strip() == "" and lines[at - 2].strip() == "":
            del lines[at - 1]
            at -= 1

        block = [want, ""] + BODIES[tag].rstrip("\n").split("\n") + [""]

        lines[at:at] = block

        out = "\n".join(lines)

        if not out.endswith("\n"):
            out += "\n"

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + out.encode("utf-8"))

        chapters = sum(1 for line in out.split("\n") if line.startswith("## "))

        print(f"{tag}: inserted after chapter {AFTER + 1}, now {chapters} chapters")


if __name__ == "__main__":
    main()
