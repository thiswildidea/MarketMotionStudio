# -*- coding: utf-8 -*-
r"""把「市值榜竞速」一章插进 14 份帮助文档。

位置**按章节序号**定，不按标题文字：新章插在第 6 章（行业板块竞速）之后，
因为导航里这两项也挨着。14 份文档的章节数与顺序必须相同，这一点由
verify 脚本另行检查。

文件是 UTF-8 **带 BOM** + LF：`read_bytes().decode('utf-8-sig')` 读，写回时
自己补 BOM —— 直接 `write_text` 会把 BOM 丢掉、把 CRLF 归一成 LF。另外
`utf-8-sig` 只吃掉一个 BOM，文件里若已经叠了两个（历史上踩过），要用
`lstrip('\ufeff')` 兜住。

幂等：标题已存在就整章重写（先删旧章再插），跑几遍结果一样。**这一条就是
本文件正文的更新方式** —— 榜单的行为改过两次（固定十五只 → 62 只候选动态榜
→ 每次取数问排行的两百只），而正文留在原处，于是应用里那一章有段时间仍在说
「榜单固定十五家，每天都取前十五名要几千次请求」，正好是代码里已经推翻的理由。
改行为就要改这里，然后重跑。

用法：python tools\port-marketcap-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

TITLES = {
    "zh-Hans": "市值榜竞速",
    "zh-Hant": "市值榜競速",
    "en-US": "Market Cap Race",
    "ja": "時価総額レース",
    "ko": "시가총액 레이스",
    "de": "Marktkapitalisierungs-Rennen",
    "fr": "Course des capitalisations",
    "it": "Corsa delle capitalizzazioni",
    "es": "Carrera de capitalización",
    "pt-BR": "Corrida de valor de mercado",
    "pl": "Wyścig kapitalizacji",
    "cs": "Závod tržních kapitalizací",
    "ru": "Гонка капитализаций",
    "tr": "Piyasa değeri yarışı",
}

BODIES = {
    "zh-Hans": """一个市场市值最大的十五家公司，按总市值排成一列横向条形，名次一路变到最后一帧。取样按月。

- **榜单每一期重排**：取数时先向行情源问出当前的市值排名，取前 200 名作候选池，再补上这
  十年里曾经进榜、如今掉出去的老牌公司；每一期在这个池子里取当时的前十五名。所以成员会
  真的进出——2016 年是石油和银行，2026 年多了茅台、宁德时代、工业富联。候选池写在程序里的
  版本曾经漏掉一家刚上市就登顶的公司，所以现在是每次取数现问。
- **历史市值是算出来的**：今日总市值 × 区间复权价格比。送股与拆股会在复权序列里互相抵消，
  所以十送十不会读成公司腰斩；分红不会抵消——它被算作再投资，于是高分红公司的历史市值偏低，
  看起来比实际增长得更快。只有最后一帧那个数字直接来自行情源，其余都是推出来的。
- **还没上市的公司从零长出来**：宁德时代和工业富联 2018 年才上市，它们在自己上市那天从
  基线上长出来，而不是提前占着位置。
- **取样是月不是日**：十年一百二十期、一年十二期，画面表头写的就是月数。市值排名本来就是
  慢变量，按月取样换来的是「一次请求拿完整段历史」。港股与美股只能给固定候选池——它们的
  排行接口拿不到。
- **三个市场各看各的十五家**，不混着排。三个市场的钱不是一种钱，混在一张榜上没有意义。
""",
    "zh-Hant": """一個市場市值最大的十五家公司，按總市值排成一列橫向條形，名次一路變到最後一幀。取樣按月。

- **榜單每一期重排**：取數時先向行情源問出當前的市值排名，取前 200 名作候選池，再補上這
  十年裡曾經進榜、如今掉出去的老牌公司；每一期在這個池子裡取當時的前十五名。所以成員會
  真的進出——2016 年是石油和銀行，2026 年多了茅台、寧德時代、工業富聯。候選池寫在程式裡的
  版本曾經漏掉一家剛上市就登頂的公司，所以現在是每次取數現問。
- **歷史市值是算出來的**：今日總市值 × 區間複權價格比。送股與拆股會在複權序列裡互相抵消，
  所以十送十不會讀成公司腰斬；分紅不會抵消——它被算作再投資，於是高分紅公司的歷史市值偏低，
  看起來比實際增長得更快。只有最後一幀那個數字直接來自行情源，其餘都是推出來的。
- **還沒上市的公司從零長出來**：寧德時代和工業富聯 2018 年才上市，它們在自己上市那天從
  基線上長出來，而不是提前佔著位置。
- **取樣是月不是日**：十年一百二十期、一年十二期，畫面表頭寫的就是月數。市值排名本來就是
  慢變量，按月取樣換來的是「一次請求拿完整段歷史」。港股與美股只能給固定候選池——它們的
  排行介面拿不到。
- **三個市場各看各的十五家**，不混著排。三個市場的錢不是一種錢，混在一張榜上沒有意義。
""",
    "en-US": """One market's fifteen largest companies as horizontal bars ranked by total market value, the
order changing to the last frame. Sampled monthly.

- **The board is re-ranked every period.** A fetch first asks the source for the current ranking
  by market value, takes the top two hundred as its field, and adds the large caps that used to be
  on the board and have dropped out of that ranking; each period then shows the fifteen largest in
  that field. So members really do come and go — 2016 was oil and banks, 2026 has added 茅台,
  宁德时代 and 工业富联. A field written into the program missed a company that listed and went
  straight to the top, so the field is asked for rather than remembered.
- **A past market value is derived**: today's total market value times the adjusted price ratio
  over the range. A bonus issue or a split cancels in the adjusted series, so a ten-for-ten does
  not read as the company halving; a dividend does not cancel — it is reinvested, so a heavy
  payer's past value reads low and it looks like it grew faster than it did. Only the last frame's
  figure comes straight from the source.
- **A company that had not listed yet grows out of nothing**: 宁德时代 and 工业富联 listed in 2018,
  and they rise from the baseline on the day they joined rather than holding a place in advance.
- **The interval is a month, not a day** — a hundred and twenty periods over ten years, twelve over
  one, and the frame's own header counts months. A market-cap ranking is a slow variable, and a
  monthly sample gets a whole history in one request.
- **Each market has its own fifteen.** The three are never mixed: their money is not one money,
  and a board of mixed currencies means nothing. Hong Kong and New York keep a fixed field, because
  no ranking this app can reach serves them.
""",
    "ja": """1 つの市場の時価総額上位 15 社を、時価総額順の横棒として並べます。順位は最後のフレームまで入れ替わります。抽出は月次です。

- **順位は毎期つけ直します。** 取得時にまず情報源へ現在の時価総額ランキングを問い合わせ、
  上位 200 社を候補とし、そこから外れた往年の大型株を加えます。各期はその中から上位 15 社を
  表示します。したがってメンバーは実際に入れ替わります——2016 年は石油と銀行、2026 年は
  茅台・寧徳時代・工業富聯が加わっています。候補をプログラムに書き込んでいた頃は、上場して
  すぐ首位になった会社を取りこぼしました。今は毎回問い合わせます。
- **過去の時価総額は計算値**です。今日の時価総額 × 期間の調整済み価格比率。増資や分割は
  調整済み系列で相殺されるため、10 割 10 株の分割が会社半減として読まれることはありません。
  配当は相殺されません——再投資として扱われるため、高配当銘柄の過去の値は低く出ます。
  情報源から直接来るのは最後のフレームの数字だけです。
- **まだ上場していない会社はゼロから伸びます**：2018 年上場の寧徳時代と工業富聯は、
  上場した日に基準線から伸び上がります。
- **抽出は日次ではなく月次**です。10 年で 120 期、1 年で 12 期、フレームの見出しも月数を
  数えています。時価総額の順位は動きの遅い変数で、月次なら 1 回の要求で全期間が取れます。
- **3 つの市場はそれぞれ別の 15 社**です。混ぜて並べることはしません。香港と米国は固定の
  候補のみ——このアプリから届くランキングがありません。
""",
    "ko": """한 시장의 시가총액 상위 15개 기업을 시가총액 순 가로 막대로 늘어놓습니다. 순위는 마지막 프레임까지 바뀝니다. 표본은 월 단위입니다.

- **순위는 매 시점 다시 매깁니다.** 데이터를 받을 때 먼저 오늘의 시가총액 순위를 물어
  상위 200개를 후보로 삼고, 거기서 밀려난 예전 대형주를 더합니다. 각 시점은 그 안에서 상위
  15개를 보여줍니다. 그래서 구성 종목이 실제로 바뀝니다——2016년은 석유와 은행, 2026년에는
  마오타이·CATL·폭스콘이 들어왔습니다. 후보 명단을 프로그램에 적어 두던 때는 상장하자마자
  1위가 된 기업을 놓쳤습니다. 지금은 매번 물어봅니다.
- **과거 시가총액은 계산값**입니다. 오늘의 시가총액 × 기간의 조정 주가 비율. 무상증자와
  액면분할은 조정 계열에서 상쇄되므로 10대 10 증자가 회사가 반토막 난 것으로 읽히지 않습니다.
  배당은 상쇄되지 않습니다——재투자로 처리되므로 배당을 많이 주는 기업의 과거 값은 낮게
  나옵니다. 데이터 원본에서 바로 오는 숫자는 마지막 프레임뿐입니다.
- **아직 상장하지 않은 기업은 0에서 자라납니다**: 2018년에 상장한 CATL과 폭스콘은 상장한 날
  기준선에서 솟아오릅니다.
- **표본은 일이 아니라 월**입니다. 10년이면 120개 시점, 1년이면 12개이며 프레임의 머리말도
  개월 수를 셉니다. 시가총액 순위는 느린 변수이고, 월 단위면 한 번의 요청으로 전 기간을
  받습니다.
- **세 시장은 각자의 15개**를 봅니다. 섞지 않습니다. 홍콩과 미국은 고정 후보만——이 앱이
  닿는 순위 데이터가 없습니다.
""",
    "de": """Die fünfzehn größten Unternehmen eines Marktes als waagerechte Balken nach Marktkapitalisierung —
die Reihenfolge ändert sich bis zum letzten Bild. Monatlich abgetastet.

- **Die Rangfolge wird jede Periode neu berechnet.** Beim Abruf wird zuerst die aktuelle Rangliste
  nach Marktkapitalisierung erfragt, die besten zweihundert dienen als Feld, dazu kommen die
  Schwergewichte, die früher oben standen und herausgefallen sind; jede Periode zeigt daraus die
  fünfzehn größten. Mitglieder kommen und gehen also wirklich — 2016 waren es Öl und Banken, 2026
  sind 茅台, 宁德时代 und 工业富联 dazugekommen. Ein fest ins Programm geschriebenes Feld hat ein
  Unternehmen verpasst, das neu an die Börse ging und sofort an die Spitze sprang; das Feld wird
  jetzt erfragt statt erinnert.
- **Ein früherer Marktwert ist abgeleitet**: heutige Marktkapitalisierung mal das bereinigte
  Kursverhältnis über den Zeitraum. Kapitalerhöhungen und Splits heben sich in der bereinigten
  Reihe auf; Dividenden nicht — sie werden reinvestiert, weshalb der frühere Wert eines starken
  Ausschütters zu niedrig ausfällt. Nur die Zahl des letzten Bildes stammt direkt von der Quelle.
- **Ein Unternehmen, das noch nicht notiert war, wächst aus dem Nichts**: 2018 notierte Werte
  steigen an ihrem ersten Tag aus der Grundlinie, statt vorher einen Platz zu halten.
- **Das Intervall ist ein Monat, kein Tag** — hundertzwanzig Perioden in zehn Jahren, zwölf in
  einem, und der Kopf des Bildes zählt Monate. Eine Rangfolge nach Marktkapitalisierung ist eine
  langsame Größe, und eine monatliche Abtastung bekommt mit einer Anfrage die ganze Historie.
- **Jeder Markt hat seine eigenen fünfzehn.** Die drei werden nie gemischt: ihr Geld ist nicht
  dasselbe Geld. Hongkong und New York behalten ein festes Feld, weil keine für diese App
  erreichbare Rangliste sie bedient.
""",
    "fr": """Les quinze plus grandes sociétés d'un marché en barres horizontales classées par capitalisation,
l'ordre changeant jusqu'à la dernière image. Échantillonnage mensuel.

- **Le classement est refait à chaque période.** La récupération demande d'abord à la source le
  classement du jour par capitalisation, en retient les deux cents premières comme plateau, et y
  ajoute les valeurs lourdes qui y figuraient et en sont sorties ; chaque période affiche ensuite
  les quinze plus grandes de ce plateau. Les membres entrent et sortent donc réellement — 2016,
  c'était le pétrole et les banques ; 2026 y a ajouté 茅台, 宁德时代 et 工业富联. Un plateau écrit
  dans le programme avait manqué une société entrée en bourse et aussitôt propulsée en tête ; le
  plateau est désormais demandé, non mémorisé.
- **Une capitalisation passée est calculée** : la capitalisation du jour multipliée par le rapport
  de prix ajusté de la période. Une augmentation de capital ou un fractionnement s'annule dans la
  série ajustée ; un dividende non — il est réinvesti, donc la valeur passée d'un gros
  distributeur ressort basse. Seul le chiffre de la dernière image vient directement de la source.
- **Une société pas encore cotée grandit à partir de rien** : les valeurs cotées en 2018 montent
  depuis la ligne de base le jour de leur entrée, sans occuper de place à l'avance.
- **L'intervalle est le mois, pas le jour** — cent vingt périodes sur dix ans, douze sur un an, et
  l'en-tête de l'image compte des mois. Un classement par capitalisation est une grandeur lente, et
  un échantillon mensuel obtient tout l'historique en une requête.
- **Chaque marché a ses propres quinze.** Les trois ne sont jamais mélangés : leur monnaie n'est
  pas la même. Hong Kong et New York gardent un plateau fixe, faute de classement accessible à
  cette application.
""",
    "it": """Le quindici maggiori società di un mercato come barre orizzontali ordinate per
capitalizzazione; l'ordine cambia fino all'ultimo fotogramma. Campionamento mensile.

- **La classifica si rifà a ogni periodo.** Il recupero chiede prima alla fonte la classifica
  odierna per capitalizzazione, ne prende le prime duecento come campo e vi aggiunge i titoli
  pesanti che erano in classifica e ne sono usciti; ogni periodo mostra poi i quindici maggiori di
  quel campo. I membri quindi entrano ed escono davvero — il 2016 era petrolio e banche, il 2026 ha
  aggiunto 茅台, 宁德时代 e 工业富联. Un campo scritto nel programma aveva mancato una società
  quotatasi e subito balzata in testa; ora il campo si chiede invece di ricordarlo.
- **Una capitalizzazione passata è derivata**: la capitalizzazione di oggi per il rapporto di
  prezzo rettificato del periodo. Aumenti di capitale e frazionamenti si annullano nella serie
  rettificata; i dividendi no — vengono reinvestiti, quindi il valore passato di un forte
  distributore risulta basso. Solo la cifra dell'ultimo fotogramma viene dalla fonte.
- **Una società non ancora quotata cresce dal nulla**: i titoli quotati nel 2018 salgono dalla
  linea di base il giorno dell'ingresso, senza occupare un posto in anticipo.
- **L'intervallo è il mese, non il giorno** — centoventi periodi in dieci anni, dodici in uno, e
  l'intestazione del fotogramma conta i mesi. Una classifica per capitalizzazione è una grandezza
  lenta, e un campione mensile ottiene tutta la storia in una richiesta.
- **Ogni mercato ha i suoi quindici.** I tre non si mescolano mai: la loro moneta non è la stessa.
  Hong Kong e New York tengono un campo fisso, perché nessuna classifica raggiungibile da questa
  applicazione li serve.
""",
    "es": """Las quince mayores compañías de un mercado como barras horizontales ordenadas por
capitalización, con el orden cambiando hasta el último fotograma. Muestreo mensual.

- **La clasificación se rehace en cada periodo.** La descarga pregunta primero a la fuente la
  clasificación actual por capitalización, toma las doscientas primeras como grupo y añade los
  valores pesados que estaban en ella y han salido; cada periodo muestra después los quince mayores
  de ese grupo. Así los miembros entran y salen de verdad — 2016 era petróleo y bancos, 2026 ha
  sumado 茅台, 宁德时代 e 工业富联. Un grupo escrito en el programa se dejó una compañía que salió
  a bolsa y se puso primera de inmediato; ahora el grupo se pregunta en vez de recordarse.
- **Una capitalización pasada se calcula**: la capitalización de hoy por el cociente de precios
  ajustado del periodo. Las ampliaciones y los desdoblamientos se anulan en la serie ajustada; los
  dividendos no — se reinvierten, así que el valor pasado de un pagador fuerte queda bajo. Solo la
  cifra del último fotograma viene directamente de la fuente.
- **Una compañía que aún no cotizaba crece desde cero**: los valores que salieron a bolsa en 2018
  suben desde la línea base el día de su entrada, sin ocupar un sitio de antemano.
- **El intervalo es el mes, no el día**: ciento veinte periodos en diez años, doce en uno, y el
  encabezado del fotograma cuenta meses. Una clasificación por capitalización es una magnitud
  lenta, y una muestra mensual obtiene toda la historia en una petición.
- **Cada mercado tiene sus propios quince.** Los tres nunca se mezclan: su dinero no es el mismo.
  Hong Kong y Nueva York mantienen un grupo fijo, porque ninguna clasificación accesible a esta
  aplicación les sirve.
""",
    "pt-BR": """As quinze maiores companhias de um mercado como barras horizontais ordenadas por valor de
mercado, com a ordem mudando até o último quadro. Amostragem mensal.

- **A classificação é refeita a cada período.** A busca pergunta primeiro à fonte a classificação
  atual por valor de mercado, toma as duzentas primeiras como grupo e acrescenta os pesos-pesados
  que estavam nela e saíram; cada período mostra então as quinze maiores desse grupo. Os membros
  entram e saem de verdade — 2016 era petróleo e bancos, 2026 somou 茅台, 宁德时代 e 工业富联. Um
  grupo escrito no programa deixou passar uma companhia que abriu capital e foi direto ao topo;
  agora o grupo é perguntado em vez de lembrado.
- **Um valor de mercado passado é calculado**: o valor de hoje vezes a razão de preços ajustada do
  período. Bonificações e desdobramentos se cancelam na série ajustada; os dividendos não — são
  reinvestidos, então o valor passado de quem paga muito sai baixo. Só o número do último quadro
  vem direto da fonte.
- **Uma companhia que ainda não tinha aberto capital cresce do zero**: os papéis que estrearam em
  2018 sobem da linha de base no dia em que entraram, sem ocupar lugar antes.
- **O intervalo é o mês, não o dia**: cento e vinte períodos em dez anos, doze em um, e o cabeçalho
  do quadro conta meses. Uma classificação por valor de mercado é uma grandeza lenta, e uma amostra
  mensal obtém todo o histórico em uma requisição.
- **Cada mercado tem os seus quinze.** Os três nunca se misturam: o dinheiro deles não é o mesmo.
  Hong Kong e Nova York mantêm um grupo fixo, porque nenhuma classificação acessível a este
  aplicativo os atende.
""",
    "pl": """Piętnaście największych spółek danego rynku jako poziome słupki uszeregowane według
kapitalizacji; kolejność zmienia się do ostatniej klatki. Próbkowanie miesięczne.

- **Ranking jest liczony od nowa w każdym okresie.** Pobranie najpierw pyta źródło o bieżący
  ranking według kapitalizacji, bierze pierwsze dwieście jako grono i dodaje duże spółki, które
  kiedyś były w rankingu, a z niego wypadły; każdy okres pokazuje potem piętnaście największych z
  tego grona. Skład naprawdę się zmienia — w 2016 roku to była ropa i banki, w 2026 doszły 茅台,
  宁德时代 i 工业富联. Grono zapisane w programie pominęło spółkę, która zadebiutowała i od razu
  wskoczyła na szczyt; teraz grono jest pytane, a nie pamiętane.
- **Dawna kapitalizacja jest wyliczana**: dzisiejsza kapitalizacja razy skorygowany stosunek cen
  z okresu. Emisje i splity znoszą się w skorygowanej serii; dywidendy nie — są reinwestowane,
  więc dawna wartość hojnego płatnika wypada nisko. Tylko liczba z ostatniej klatki pochodzi
  wprost ze źródła.
- **Spółka jeszcze nienotowana rośnie od zera**: debiuty z 2018 roku wyrastają z linii bazowej
  w dniu wejścia, zamiast zajmować miejsce zawczasu.
- **Odstęp to miesiąc, nie dzień** — sto dwadzieścia okresów na dziesięć lat, dwanaście na rok,
  a nagłówek klatki liczy miesiące. Ranking kapitalizacji zmienia się powoli, a próbka miesięczna
  dostaje całą historię w jednym zapytaniu.
- **Każdy rynek ma swoje piętnaście.** Trzech nigdy się nie miesza: ich pieniądz to nie ten sam
  pieniądz. Hongkong i Nowy Jork mają stałe grono, bo żaden dostępny tej aplikacji ranking ich nie
  obsługuje.
""",
    "cs": """Patnáct největších společností daného trhu jako vodorovné pruhy seřazené podle tržní
kapitalizace; pořadí se mění až do posledního snímku. Vzorkování po měsících.

- **Žebříček se v každém období počítá znovu.** Načtení se nejprve zeptá zdroje na dnešní žebříček
  podle kapitalizace, vezme prvních dvě stě jako sestavu a přidá velké tituly, které v žebříčku
  bývaly a vypadly z něj; každé období pak ukáže patnáct největších z této sestavy. Členové tedy
  skutečně přibývají a ubývají — v roce 2016 to byla ropa a banky, v roce 2026 přibyly 茅台,
  宁德时代 a 工业富联. Sestava zapsaná v programu minula společnost, která vstoupila na burzu a
  rovnou se dostala na špičku; sestava se teď ptá, místo aby si pamatovala.
- **Dřívější kapitalizace se počítá**: dnešní kapitalizace krát upravený poměr cen za období.
  Emise a štěpení se v upravené řadě vyruší; dividendy ne — reinvestují se, takže dřívější hodnota
  štědrého plátce vychází nízko. Přímo ze zdroje je jen číslo posledního snímku.
- **Společnost, která ještě nebyla na burze, roste od nuly**: tituly uvedené v roce 2018 stoupají
  ze základní linie v den vstupu, místo aby držely místo předem.
- **Interval je měsíc, ne den** — sto dvacet období za deset let, dvanáct za rok, a záhlaví snímku
  počítá měsíce. Žebříček podle kapitalizace je pomalá veličina a měsíční vzorek získá celou
  historii jedním dotazem.
- **Každý trh má svých patnáct.** Ty tři se nikdy nemíchají: jejich peníze nejsou tytéž peníze.
  Hongkong a New York mají pevnou sestavu, protože jim žádný žebříček dostupný této aplikaci
  neposlouží.
""",
    "ru": """Пятнадцать крупнейших компаний одного рынка горизонтальными полосами по капитализации;
порядок меняется до последнего кадра. Шаг — месяц.

- **Список пересчитывается в каждом периоде.** При загрузке сначала запрашивается текущий
  рейтинг по капитализации, первые двести идут в список, к ним добавляются тяжёлые бумаги,
  которые когда-то были в рейтинге и выбыли из него; каждый период показывает пятнадцать
  крупнейших из этого списка. Состав действительно меняется — в 2016 году это были нефть и
  банки, в 2026 добавились 茅台, 宁德时代 и 工业富联. Список, вписанный в программу, пропустил
  компанию, которая вышла на биржу и сразу заняла первое место; теперь список спрашивают, а не
  помнят.
- **Прошлая капитализация выводится**: сегодняшняя капитализация умножается на
  скорректированное отношение цен за период. Допэмиссии и дробления в скорректированном ряду
  сокращаются; дивиденды — нет, они реинвестируются, поэтому прошлая стоимость щедрого
  плательщика выходит заниженной. Прямо из источника приходит только число последнего кадра.
- **Компания, ещё не вышедшая на биржу, растёт из нуля**: бумаги 2018 года поднимаются от
  базовой линии в день выхода, а не занимают место заранее.
- **Шаг — месяц, а не день**: сто двадцать периодов за десять лет, двенадцать за год, и в
  заголовке кадра считается именно число месяцев. Рейтинг по капитализации — медленная
  величина, и месячный шаг получает всю историю одним запросом.
- **У каждого рынка свои пятнадцать.** Три никогда не смешиваются: их деньги — не одни и те же
  деньги. Гонконг и Нью-Йорк обходятся фиксированным списком: доступного этому приложению
  рейтинга для них нет.
""",
    "tr": """Bir piyasanın en büyük on beş şirketi, piyasa değerine göre sıralanmış yatay çubuklar olarak;
sıralama son kareye kadar değişir. Örnekleme aylıktır.

- **Sıralama her dönemde yeniden hesaplanır.** Veri çekilirken önce kaynaktan güncel piyasa değeri
  sıralaması istenir, ilk iki yüz aday olarak alınır ve bir zamanlar listede olup düşen ağır
  hisseler eklenir; her dönem bu kadro içinden en büyük on beşi gösterir. Üyeler gerçekten girer ve
  çıkar — 2016'da petrol ve bankalardı, 2026'da 茅台, 宁德时代 ve 工业富联 eklendi. Programa
  yazılmış bir kadro, halka açılıp hemen zirveye oturan bir şirketi kaçırdı; artık kadro
  hatırlanmıyor, soruluyor.
- **Geçmiş piyasa değeri hesaplanır**: bugünkü piyasa değeri çarpı dönemin düzeltilmiş fiyat oranı.
  Bedelsiz sermaye artırımları ve bölünmeler düzeltilmiş seride birbirini götürür; temettüler
  götürmez — yeniden yatırılır, bu yüzden çok temettü veren bir şirketin geçmiş değeri düşük çıkar.
  Doğrudan kaynaktan gelen tek sayı son kareninkidir.
- **Henüz halka açılmamış şirket sıfırdan büyür**: 2018'de işlem görmeye başlayan hisseler, önceden
  yer tutmak yerine girdikleri gün taban çizgisinden yükselir.
- **Aralık gün değil ay**: on yılda yüz yirmi dönem, bir yılda on iki ve karenin başlığı ay sayısını
  yazar. Piyasa değeri sıralaması yavaş bir değişkendir ve aylık örnekleme tüm geçmişi tek istekte
  alır.
- **Her piyasanın kendi on beşi var.** Üçü asla karıştırılmaz: paraları aynı para değildir.
  Hong Kong ve New York sabit kadro kullanır, çünkü bu uygulamanın erişebildiği bir sıralama
  onlara hizmet etmiyor.
""",
}

# 新章插在第几章之后（0 起算）：行业板块竞速是第 6 章。
AFTER = 5


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

        # The chapter after the one to follow: inserting here keeps every other chapter's
        # number, which is what the verify script's chapter count compares.
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
