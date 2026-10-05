# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「持仓收益」那一章补上多标的对比与曲线上的收益数字。

三件事值得写进帮助里，因为它们在界面上看不出来：

* **标的是共享的自选清单。** 与本项目其它五个榜单同一份；页面上的一键预设是「加进清单
  并画出来」，不是「换一个标的」。
* **同一笔本金、各自的第一个交易日、日期轴取并集。** 上市晚的那只从它自己的第一天开始
  画，在此之前画面上没有它——不是从零开始的一条直线。
* **最多 6 只，多了拒绝而不是少画。** 少画的画面看起来完全正常，所以这条必须写在帮助里，
  否则用户只会以为「勾了九只，出来六只」是坏了。

**章节序号不写死**：用 `listingtext.chapter_of("Position")` 读导航顺序算出来。往导航
中间插一页，后面每章 +1，写死序号会让说明挂到错章头上，14 语言全错而每句都通顺。

**注入方式**：定位标题行，改写引子句与第一条条目，并在第一条之后插入两条新条目。
其余条目（本金与区间、后复权口径、自定义区间）原样保留 —— 整章重写会丢掉后来由
`port-custom-range-help.py` 追加的那一条。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在
diff 里表现为首行多一个看不见的字符，肉眼查不出来。

用法：python tools\port-position-help.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

sys.path.insert(0, str(HERE))

import listingtext  # noqa: E402

CHAPTER = listingtext.chapter_of("NavPosition")

TAGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
        "ja", "ko", "zh-Hans", "zh-Hant"]

INTRO = {
    "en-US": "One purchase, held — a million of the same name since 2015 — animated to show what "
             "the years did to its value and its return. Several holdings can share the one frame: "
             "a line each, with its running profit riding the line's leading end.",

    "de": "Ein Kauf, lange gehalten — etwa eine Million derselben Aktie seit 2015 — animiert, um "
          "zu zeigen, was die Jahre mit Wert und Rendite gemacht haben. Mehrere Anlagen können "
          "sich ein Bild teilen: eine Linie je Anlage, mit dem laufenden Gewinn an ihrem "
          "vorderen Ende.",

    "es": "Una compra, mantenida —un millón del mismo valor desde 2015—, animada para mostrar lo "
          "que los años hicieron con su valor y su rentabilidad. Varias posiciones pueden "
          "compartir el mismo cuadro: una línea cada una, con su ganancia actual en su extremo.",

    "fr": "Un achat, conservé — un million du même nom depuis 2015 — animé pour montrer ce que les "
          "années ont fait à sa valeur et à sa performance. Plusieurs positions peuvent partager "
          "le même cadre : une ligne chacune, avec son gain courant à son extrémité.",

    "it": "Un acquisto, tenuto — un milione dello stesso nome dal 2015 — animato per mostrare cosa "
          "hanno fatto gli anni al suo valore e al suo rendimento. Più posizioni possono "
          "condividere lo stesso quadro: una linea ciascuna, con il guadagno corrente in coda.",

    "pl": "Jeden zakup, trzymany długo — milion w tym samym instrumencie od 2015 roku — animowany, "
          "by pokazać, co lata zrobiły z wartością i stopą zwrotu. Kilka pozycji może dzielić "
          "jeden obraz: po jednej linii na każdą, z bieżącym zyskiem na jej końcu.",

    "pt-BR": "Uma compra, mantida — um milhão do mesmo ativo desde 2015 — animada para mostrar o "
             "que os anos fizeram com seu valor e seu retorno. Várias posições podem dividir o "
             "mesmo quadro: uma linha cada, com o lucro atual na sua ponta.",

    "cs": "Jeden nákup, držený dlouho — milion do stejného nástroje od roku 2015 — animovaný tak, "
          "aby ukázal, co léta udělala s hodnotou a výnosem. Několik pozic může sdílet jeden "
          "obraz: po jedné čáře na každou, s běžným ziskem na jejím konci.",

    "tr": "Tek alım, uzun süre elde tutma — 2015'ten beri aynı varlıktan bir milyon — yılların "
          "değere ve getiriye ne yaptığını gösteren bir animasyon. Birkaç pozisyon aynı kareyi "
          "paylaşabilir: her birine bir çizgi, ucunda o anki kâr.",

    "ru": "Одна покупка, удержанная надолго — миллион в одной и той же бумаге с 2015 года — "
          "анимация о том, что годы сделали со стоимостью и доходностью. Несколько позиций могут "
          "делить один кадр: по линии на каждую, с текущей прибылью у её конца.",

    "ja": "一度買って長期保有——たとえば 2015 年に同じ銘柄を 100 万分——その後の評価額と収益率の"
          "推移をアニメーションで見ます。複数の銘柄を同じ画面に載せることもでき、1 銘柄ごとに "
          "1 本の線、その先端には今の収益額が付きます。",

    "ko": "한 번 사서 오래 보유 — 예컨대 2015년에 같은 종목을 100만큼 — 그동안 평가액과 수익률이 "
          "어떻게 움직였는지 애니메이션으로 봅니다. 여러 종목을 한 화면에 올릴 수 있고, 종목마다 "
          "선 하나, 그 끝에는 지금의 수익 금액이 따라붙습니다.",

    "zh-Hans": "一笔买入、长期持有——比如 2015 年 100 万买入同一个名字——动画展示这些年市值与收益率的"
               "起落。也可以把几只放在同一张图上比：每只一条线，末端跟着它此刻的收益数字。",

    "zh-Hant": "一筆買入、長期持有——比如 2015 年 100 萬買入同一個名字——動畫展示這些年市值與收益率"
               "的起落。也可以把幾隻放在同一張圖上比：每隻一條線，末端跟著它此刻的收益數字。",
}

# 原来那条「一键标的随市场变……」，改成先说清单、再说一键预设。
PICKS = {
    "en-US": "- The holdings come from your **own list**, the one the other boards share: search a "
             "code or a name to add one, each chip's switch decides whether it is on this frame, "
             "and the × takes it off the shared list (and off those other boards with it). The "
             "one-tap row follows the market — 中国平安 and 贵州茅台 for the mainland, 腾讯, 汇丰 "
             "and 盈富基金 for Hong Kong, Apple, Berkshire and SPY for New York — and a press adds "
             "that name and draws it straight away.",

    "de": "- Die Anlagen stammen aus **Ihrer eigenen Liste**, derselben, die auch die anderen "
          "Tafeln nutzen: Code oder Namen eintippen, um eine aufzunehmen; der Schalter auf jedem "
          "Chip entscheidet, ob sie auf diesem Bild ist, und das × nimmt sie von der geteilten "
          "Liste (und damit auch von den anderen Tafeln). Die Ein-Klick-Zeile folgt dem Markt — "
          "中国平安 und 贵州茅台 für das Festland, 腾讯, 汇丰 und 盈富基金 für Hongkong, Apple, "
          "Berkshire und SPY für New York — und ein Druck nimmt den Namen auf und zeichnet ihn "
          "sofort.",

    "es": "- Las posiciones salen de **tu propia lista**, la misma que comparten los otros "
          "paneles: busca un código o un nombre para añadir uno, el interruptor de cada chip "
          "decide si está en este cuadro, y la × lo quita de la lista compartida (y con ello de "
          "los otros paneles). La fila de un toque sigue al mercado —中国平安 y 贵州茅台 en "
          "continental, 腾讯, 汇丰 y 盈富基金 en Hong Kong, Apple, Berkshire y SPY en Nueva York— "
          "y al pulsar se añade ese nombre y se dibuja al momento.",

    "fr": "- Les positions viennent de **votre propre liste**, celle que partagent les autres "
          "tableaux : cherchez un code ou un nom pour en ajouter une, l'interrupteur de chaque "
          "pastille décide si elle figure sur ce cadre, et le × la retire de la liste partagée "
          "(et donc des autres tableaux). La rangée en un clic suit le marché — 中国平安 et "
          "贵州茅台 pour le continent, 腾讯, 汇丰 et 盈富基金 pour Hong Kong, Apple, Berkshire et "
          "SPY pour New York — et une pression ajoute ce nom et le dessine aussitôt.",

    "it": "- Le posizioni arrivano dalla **tua lista**, la stessa che condividono gli altri "
          "pannelli: cerca un codice o un nome per aggiungerne una, l'interruttore su ogni chip "
          "decide se è su questo quadro, e la × la toglie dalla lista condivisa (e quindi dagli "
          "altri pannelli). La riga a un tocco segue il mercato — 中国平安 e 贵州茅台 per la Cina "
          "continentale, 腾讯, 汇丰 e 盈富基金 per Hong Kong, Apple, Berkshire e SPY per New York "
          "— e una pressione aggiunge quel nome e lo disegna subito.",

    "pl": "- Pozycje pochodzą z **Twojej listy**, tej samej, którą dzielą inne tablice: wpisz kod "
          "lub nazwę, aby dodać pozycję; przełącznik na chipie decyduje, czy jest na tym obrazie, "
          "a × usuwa ją ze wspólnej listy (a więc i z innych tablic). Wiersz jednego dotknięcia "
          "idzie za rynkiem — 中国平安 i 贵州茅台 dla kontynentu, 腾讯, 汇丰 i 盈富基金 dla Hongkongu, "
          "Apple, Berkshire i SPY dla Nowego Jorku — a dotknięcie dodaje tę nazwę i od razu ją "
          "rysuje.",

    "pt-BR": "- As posições vêm da **sua própria lista**, a mesma que os outros painéis "
             "compartilham: busque um código ou um nome para acrescentar uma, o interruptor de "
             "cada chip decide se ela está neste quadro, e o × a remove da lista compartilhada (e "
             "com isso dos outros painéis). A linha de um toque segue o mercado — 中国平安 e "
             "贵州茅台 na China continental, 腾讯, 汇丰 e 盈富基金 em Hong Kong, Apple, Berkshire e "
             "SPY em Nova York — e um toque acrescenta esse nome e o desenha na hora.",

    "cs": "- Pozice pocházejí z **vašeho seznamu**, téhož, který sdílejí ostatní tabule: napište "
          "kód nebo název a přidejte ji; přepínač na každém chipu rozhoduje, zda je na tomto "
          "obraze, a × ji odebere ze sdíleného seznamu (a tím i z ostatních tabulí). Řádek na "
          "jeden klik jde za trhem — 中国平安 a 贵州茅台 pro pevninu, 腾讯, 汇丰 a 盈富基金 pro "
          "Hongkong, Apple, Berkshire a SPY pro New York — a stisk tento název přidá a hned ho "
          "vykreslí.",

    "tr": "- Pozisyonlar **kendi listenizden** gelir; diğer tabloların da paylaştığı liste: bir "
          "kod ya da ad arayıp ekleyin, her chip'in anahtarı o pozisyonun bu karede olup "
          "olmadığını belirler, × ise onu paylaşılan listeden (ve dolayısıyla diğer tablolardan) "
          "çıkarır. Tek dokunuş satırı piyasaya göre değişir — ana kara için 中国平安 ve 贵州茅台, "
          "Hong Kong için 腾讯, 汇丰 ve 盈富基金, New York için Apple, Berkshire ve SPY — ve bir "
          "dokunuş o adı ekleyip hemen çizer.",

    "ru": "- Позиции берутся из **вашего списка**, того самого, что и у других табло: введите код "
          "или название, чтобы добавить; переключатель на чипе решает, попадёт ли она в кадр, а × "
          "убирает её из общего списка (и тем самым с других табло). Строка быстрого выбора "
          "зависит от рынка — 中国平安 и 贵州茅台 для материка, 腾讯, 汇丰 и 盈富基金 для Гонконга, "
          "Apple, Berkshire и SPY для Нью-Йорка — и нажатие добавляет это название и сразу его "
          "рисует.",

    "ja": "- 銘柄は**マイリスト**（他のタブと同じ一つのリスト）から取ります。コードか名前を検索して"
          "追加し、各 chip のスイッチでこの画面に載せるかどうかを決め、× は共有リストから外します"
          "（他のタブからも消えます）。上の一括ボタンは市場ごとに変わります——本土は 中国平安 と "
          "贵州茅台、香港は 腾讯・汇丰・盈富基金、ニューヨークは Apple・Berkshire・SPY——押すとその"
          "銘柄をリストに加えてすぐ描きます。",

    "ko": "- 종목은 **내 목록**(다른 탭과 함께 쓰는 하나의 목록)에서 가져옵니다. 코드나 이름을 검색해 "
          "추가하고, 각 chip의 스위치로 이 화면에 올릴지 정하며, ×는 공유 목록에서 빼냅니다(다른 "
          "탭에서도 사라집니다). 위의 한 번 누르기 버튼은 시장에 따라 바뀝니다 — 본토는 中国平安, "
          "贵州茅台, 홍콩은 腾讯·汇丰·盈富基金, 뉴욕은 Apple·Berkshire·SPY — 누르면 그 종목이 목록에 "
          "들어가고 곧바로 그려집니다.",

    "zh-Hans": "- 标的是你的**自选清单**，与其它榜单共用一份：在框里搜代码或名字加进去，chip 上的开关"
               "决定它上不上这张图，× 把它从清单里删掉（其它榜单也跟着少一条）。上方的「一键标的」随"
               "市场变——A 股是中国平安、贵州茅台这些长期持有的名字，港股是腾讯、汇丰与盈富基金，"
               "美股是苹果、伯克希尔与 SPY——点一下即加入清单并画出来。",

    "zh-Hant": "- 標的是你的**自選清單**，與其它榜單共用一份：在框裡搜代碼或名字加進去，chip 上的開關"
               "決定它上不上這張圖，× 把它從清單裡刪掉（其它榜單也跟著少一條）。上方的「一鍵標的」隨"
               "市場變——A 股是中國平安、貴州茅台這些長期持有的名字，港股是騰訊、匯豐與盈富基金，"
               "美股是蘋果、波克夏與 SPY——點一下即加入清單並畫出來。",
}

# 新条目一：多标的怎么比。
COMPARE = {
    "en-US": "- **2 to 6 of your holdings on one frame.** Each is bought once with the same "
             "amount, on its own first trading day, so the lines are directly comparable and the "
             "distance between two of them at any date is the answer to \"which was the better "
             "place for it\". The date axis is the union of their days: a listing that starts "
             "later simply begins later, and is absent before that rather than drawn flat along "
             "the capital. Six is the ceiling — past it the fetch refuses rather than quietly "
             "drawing some of them — and a holding from another market is left off, because the "
             "amounts here are the currency of the market in force.",

    "de": "- **2 bis 6 Anlagen in einem Bild.** Jede wird einmal mit demselben Betrag an ihrem "
          "eigenen ersten Handelstag gekauft, also sind die Linien direkt vergleichbar, und der "
          "Abstand zwischen zweien ist zu jedem Datum die Antwort auf „welche war der bessere "
          "Platz dafür“. Die Zeitachse ist die Vereinigung ihrer Tage: eine später notierte Aktie "
          "beginnt einfach später und fehlt davor, statt flach am Kapital zu liegen. Sechs ist die "
          "Obergrenze — darüber verweigert der Abruf, statt still ein paar davon zu zeichnen — und "
          "eine Anlage aus einem anderen Markt bleibt weg, weil die Beträge hier in der Währung "
          "des geltenden Marktes laufen.",

    "es": "- **De 2 a 6 posiciones en un cuadro.** Cada una se compra una vez con el mismo importe, "
          "en su propio primer día de negociación, así que las líneas son directamente "
          "comparables y la distancia entre dos cualesquiera, en cualquier fecha, responde a "
          "«cuál era el mejor sitio para ese dinero». El eje de fechas es la unión de sus días: "
          "un valor que empieza más tarde simplemente empieza más tarde, y antes de eso no está "
          "en vez de dibujarse plano sobre el capital. Seis es el tope —por encima, la descarga "
          "se niega en lugar de dibujar solo algunas— y una posición de otro mercado queda fuera, "
          "porque los importes aquí son la moneda del mercado en vigor.",

    "fr": "- **De 2 à 6 positions sur un même cadre.** Chacune est achetée une fois, du même "
          "montant, à son propre premier jour de cotation : les lignes sont donc directement "
          "comparables, et l'écart entre deux d'entre elles à une date donnée est la réponse à "
          "« lequel était le meilleur endroit pour cet argent ». L'axe des dates est l'union de "
          "leurs jours : une valeur cotée plus tard commence simplement plus tard, et n'est pas "
          "présente avant, au lieu d'être tracée à plat sur le capital. Six est le plafond — "
          "au-delà, la récupération refuse au lieu d'en dessiner quelques-unes — et une position "
          "d'un autre marché est écartée, car les montants ici sont dans la devise du marché en "
          "vigueur.",

    "it": "- **Da 2 a 6 posizioni in un quadro.** Ognuna è comprata una volta con lo stesso "
          "importo, nel proprio primo giorno di borsa, quindi le linee sono direttamente "
          "confrontabili e la distanza fra due di esse è, a ogni data, la risposta a «quale era "
          "il posto migliore per quei soldi». L'asse delle date è l'unione dei loro giorni: uno "
          "strumento quotato più tardi inizia semplicemente più tardi, e prima non c'è, invece "
          "di essere disegnato piatto sul capitale. Sei è il tetto — oltre, il recupero rifiuta "
          "invece di disegnarne qualcuna in silenzio — e una posizione di un altro mercato resta "
          "fuori, perché gli importi qui sono nella valuta del mercato in vigore.",

    "pl": "- **Od 2 do 6 pozycji na jednym obrazie.** Każda jest kupowana raz, za tę samą kwotę, "
          "w swoim pierwszym dniu sesyjnym, więc linie są wprost porównywalne, a odległość między "
          "dwiema z nich w dowolnej dacie odpowiada na pytanie „gdzie było lepiej to położyć”. Oś "
          "dat to suma ich dni: instrument notowany później po prostu zaczyna się później i przed "
          "tym go nie ma, zamiast być rysowany płasko po koszcie. Sześć to pułap — powyżej "
          "pobieranie odmawia, zamiast po cichu narysować kilka z nich — a pozycja z innego rynku "
          "zostaje pominięta, bo kwoty tutaj są w walucie obowiązującego rynku.",

    "pt-BR": "- **De 2 a 6 posições num quadro.** Cada uma é comprada uma vez com o mesmo valor, "
             "no seu próprio primeiro dia de negociação, então as linhas são diretamente "
             "comparáveis e a distância entre duas delas, em qualquer data, responde a «qual era "
             "o melhor lugar para esse dinheiro». O eixo de datas é a união dos dias delas: um "
             "ativo listado mais tarde simplesmente começa mais tarde, e antes disso não está lá "
             "em vez de ser desenhado plano sobre o capital. Seis é o teto — acima disso a "
             "obtenção recusa em vez de desenhar algumas em silêncio — e uma posição de outro "
             "mercado fica de fora, porque os valores aqui são na moeda do mercado em vigor.",

    "cs": "- **2 až 6 pozic na jednom obraze.** Každá je koupena jednou, za stejnou částku, ve svůj "
          "vlastní první obchodní den, takže jsou čáry přímo srovnatelné a vzdálenost mezi dvěma "
          "z nich je v každém datu odpovědí na „kam to bylo lepší dát“. Datová osa je sjednocením "
          "jejich dnů: nástroj kótovaný později prostě začíná později a předtím tam není, místo "
          "aby byl vykreslen vodorovně na úrovni vkladu. Šest je strop — nad ním načtení odmítne, "
          "místo aby jich pár tiše vykreslilo — a pozice z jiného trhu zůstává vynechána, protože "
          "částky jsou zde v měně platného trhu.",

    "tr": "- **Tek karede 2 ile 6 pozisyon.** Her biri aynı tutarla, kendi ilk işlem gününde bir "
          "kez alınır; böylece çizgiler doğrudan karşılaştırılabilir ve ikisi arasındaki mesafe "
          "her tarihte \"parayı nereye koymak daha iyiydi\" sorusunun cevabıdır. Tarih ekseni "
          "günlerinin birleşimidir: sonra işlem görmeye başlayan varlık yalnızca daha sonra "
          "başlar ve öncesinde maliyet çizgisi boyunca düz çizilmek yerine hiç görünmez. Sınır "
          "altıdır — üstünde getirme, birkaçını sessizce çizmek yerine reddeder — ve başka bir "
          "piyasadan pozisyon dışarıda kalır, çünkü buradaki tutarlar geçerli piyasanın para "
          "birimidir.",

    "ru": "- **От 2 до 6 позиций в одном кадре.** Каждая куплена один раз на одну и ту же сумму, в "
          "свой собственный первый торговый день, поэтому линии прямо сравнимы, а расстояние между "
          "двумя из них на любую дату и есть ответ на вопрос «куда это было лучше вложить». Ось дат "
          "— объединение их дней: бумага, начавшая торговаться позже, просто начинается позже, а до "
          "этого её нет, вместо того чтобы тянуться ровно по вложенному. Шесть — предел: сверх него "
          "загрузка отказывает, а не рисует молча часть из них; позиция с другого рынка остаётся в "
          "стороне, потому что суммы здесь в валюте действующего рынка.",

    "ja": "- **同じ画面に 2〜6 銘柄**。どの銘柄も同じ金額を、それぞれ自身の最初の取引日に一度だけ"
          "買うので、線はそのまま比べられ、任意の日付での 2 本の差が「どちらに置く方が良かったか」"
          "の答えになります。日付軸は各銘柄の日の和集合で、上場が遅い銘柄は単に遅く始まり、それ以前"
          "は元本の高さに平らに描かれるのではなく、そもそも存在しません。上限は 6 銘柄で、超えると"
          "一部だけを黙って描くのではなく取得を拒否します。また、金額は現在の市場の通貨なので、"
          "別市場の銘柄は載りません。",

    "ko": "- **한 화면에 2~6종목**. 모두 같은 금액을 각자의 첫 거래일에 한 번씩 사므로 선을 그대로 "
          "비교할 수 있고, 어느 날짜에서든 두 선 사이의 거리가 \"어디에 두는 게 더 나았나\"의 답이 "
          "됩니다. 날짜 축은 각 종목 날짜의 합집합이라, 늦게 상장한 종목은 그냥 늦게 시작하고 그 "
          "전에는 원금 높이로 평평하게 그려지는 대신 아예 없습니다. 상한은 6종목이며, 넘으면 몇 "
          "개만 조용히 그리는 대신 가져오기를 거부합니다. 금액은 현재 시장의 통화이므로 다른 시장 "
          "종목은 빠집니다.",

    "zh-Hans": "- **可以同时比 2~6 只**：每只都是同一笔本金、按它自己的首个交易日买入，所以几条线直接"
               "可比，任意一天两条线之间的距离就是「这笔钱放在哪儿更好」的答案。日期轴取并集——上市"
               "晚的那只从它自己的第一天开始画，在此之前画面上没有它，而不是沿本金拉一条平的。上限"
               "是 6 只，超了会拒绝取数而不是少画几只；别的市场的标的不会画上来，因为这里的金额是"
               "当前市场的货币。",

    "zh-Hant": "- **可以同時比 2~6 隻**：每隻都是同一筆本金、按它自己的首個交易日買入，所以幾條線直接"
               "可比，任意一天兩條線之間的距離就是「這筆錢放在哪裡更好」的答案。日期軸取並集——上市"
               "晚的那隻從它自己的第一天開始畫，在此之前畫面上沒有它，而不是沿本金拉一條平的。上限"
               "是 6 隻，超了會拒絕取數而不是少畫幾隻；別的市場的標的不會畫上來，因為這裡的金額是"
               "當前市場的貨幣。",
}

# 新条目二：曲线上那个数字。
FIGURE = {
    "en-US": "- **The figure rides the line.** A label at each holding's leading end names it and "
             "gives the money it is up at that moment, and it moves with the animation — scrub the "
             "bar and it goes with the line. With one holding the big figure in the middle is "
             "still the return in per cent; with several it becomes the money the **leader** is "
             "up, with that holding's name underneath, and the closing cards become one per "
             "holding rather than the four figures describing one.",

    "de": "- **Die Zahl fährt auf der Linie mit.** Ein Etikett am vorderen Ende jeder Anlage "
          "nennt sie und zeigt, wie viel Gewinn sie in diesem Moment hat; es bewegt sich mit der "
          "Animation — schieben Sie den Regler, und es geht mit der Linie. Bei einer Anlage bleibt "
          "die große Zahl in der Mitte die Rendite in Prozent; bei mehreren wird sie der Gewinn "
          "der **führenden** und trägt deren Namen darunter, und die Abschlusskarten werden eine "
          "je Anlage statt der vier Zahlen für eine.",

    "es": "- **La cifra cabalga la línea.** Una etiqueta en el extremo de cada posición la nombra "
          "y da el dinero que gana en ese momento, y se mueve con la animación: arrastra la barra "
          "y se va con la línea. Con una posición, el número grande del centro sigue siendo la "
          "rentabilidad en porcentaje; con varias pasa a ser el dinero que gana la **líder**, con "
          "su nombre debajo, y las tarjetas finales pasan a ser una por posición en lugar de las "
          "cuatro cifras que describen una.",

    "fr": "- **Le chiffre chevauche la ligne.** Une étiquette à l'extrémité de chaque position la "
          "nomme et donne le gain en argent à cet instant, et elle suit l'animation : faites "
          "glisser la barre et elle part avec la ligne. Avec une position, le grand chiffre du "
          "milieu reste le rendement en pourcentage ; avec plusieurs, il devient le gain de la "
          "**meneuse**, son nom juste en dessous, et les cartes de fin deviennent une par "
          "position au lieu des quatre chiffres qui en décrivent une.",

    "it": "- **La cifra cavalca la linea.** Un'etichetta sull'estremità di ogni posizione la "
          "nomina e dà il guadagno in denaro in quel momento, e si muove con l'animazione: "
          "trascina la barra e se ne va con la linea. Con una posizione il numero grande al "
          "centro resta il rendimento in percentuale; con più posizioni diventa il denaro "
          "guadagnato dalla **prima**, con il suo nome sotto, e le schede finali diventano una "
          "per posizione invece delle quattro cifre che ne descrivono una.",

    "pl": "- **Liczba jedzie na linii.** Etykieta na końcu każdej pozycji podaje jej nazwę i "
          "kwotę zysku w tej chwili, i porusza się razem z animacją — przeciągnij suwak, a "
          "pojedzie z linią. Przy jednej pozycji duża liczba na środku to nadal stopa zwrotu w "
          "procentach; przy kilku staje się kwotą zysku **lidera**, z jego nazwą pod spodem, a "
          "karty na koniec są po jednej na pozycję, zamiast czterech liczb o jednej.",

    "pt-BR": "- **O número cavalga a linha.** Um rótulo na ponta de cada posição a nomeia e dá o "
             "dinheiro que ela rende naquele momento, e anda junto com a animação — arraste a "
             "barra e ele vai com a linha. Com uma posição, o número grande do meio continua "
             "sendo o retorno em porcentagem; com várias ele passa a ser o dinheiro que a "
             "**líder** rende, com o nome dela embaixo, e os cartões finais passam a ser um por "
             "posição em vez das quatro cifras que descrevem uma.",

    "cs": "- **Číslo jede po čáře.** Štítek na konci každé pozice ji pojmenuje a ukáže, kolik v tu "
          "chvíli vydělala, a pohybuje se s animací — posuňte jezdec a pojede s čárou. U jedné "
          "pozice zůstává velké číslo uprostřed výnosem v procentech; u několika se stává částkou, "
          "kterou vydělala **vedoucí**, s jejím jménem pod tím, a závěrečné karty jsou po jedné na "
          "pozici místo čtyř čísel o jedné.",

    "tr": "- **Sayı çizgiyle birlikte gider.** Her pozisyonun ucundaki etiket onu adlandırır ve o "
          "andaki kâr tutarını verir; animasyonla birlikte hareket eder — çubuğu çekin, çizgiyle "
          "birlikte gider. Tek pozisyonda ortadaki büyük sayı yine yüzde getiridir; birkaç "
          "pozisyonda **öndeki**nin kâr tutarına dönüşür, altında o varlığın adı yazar ve kapanış "
          "kartları tek bir varlığı anlatan dört sayı yerine her pozisyon için birer kart olur.",

    "ru": "- **Число едет по линии.** Ярлык у конца каждой позиции называет её и показывает, "
          "сколько она заработала на этот момент, и движется вместе с анимацией: потяните "
          "ползунок — и он поедет вместе с линией. При одной позиции крупное число в середине "
          "по-прежнему доходность в процентах; при нескольких оно становится суммой, которую "
          "заработала **лидирующая**, с её названием под ним, а итоговые карточки — по одной на "
          "позицию вместо четырёх чисел об одной.",

    "ja": "- **数字は線に乗って動きます。** 各銘柄の線の先端にラベルが付き、その名前とその時点の収益額を"
          "示し、アニメーションと一緒に動きます——スライダーを動かせば線とともに移動します。1 銘柄の"
          "ときは中央の大きな数字はこれまでどおり収益率（％）です。複数のときは**首位**の銘柄の収益額"
          "に変わり、その下に銘柄名が入り、締めのカードは 1 銘柄を説明する 4 枚ではなく 1 銘柄 1 枚に"
          "なります。",

    "ko": "- **숫자는 선을 따라 움직입니다.** 각 종목 선 끝에 라벨이 붙어 이름과 그 시점의 수익 금액을 "
          "보여주고, 애니메이션과 함께 움직입니다 — 슬라이더를 끌면 선과 같이 갑니다. 한 종목일 때 "
          "가운데 큰 숫자는 여전히 수익률(%)이고, 여러 종목일 때는 **선두** 종목의 수익 금액으로 바뀌며 "
          "그 아래에 종목 이름이 붙고, 마무리 카드는 한 종목을 설명하는 네 장이 아니라 종목마다 한 장이 "
          "됩니다.",

    "zh-Hans": "- **曲线末端跟着数字**：每只的线头上是一个标签，写着它的名字和此刻的收益金额，随动画一起"
               "走——拖动进度条，它跟着线走。一只时中间那个大数字仍是收益率；几只时它换成**领先那只**的"
               "收益金额，下面写着是哪一只，收尾的卡片也从「描述一只的四张」变成「每只一张」。",

    "zh-Hant": "- **曲線末端跟著數字**：每隻的線頭上是一個標籤，寫著它的名字和此刻的收益金額，隨動畫一起"
               "走——拖動進度條，它跟著線走。一隻時中間那個大數字仍是收益率；幾隻時它換成**領先那隻**的"
               "收益金額，下面寫著是哪一隻，收尾的卡片也從「描述一隻的四張」變成「每隻一張」。",
}


def main():
    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")

        # Chapters open on a "## " line, and their position among those is the navigation order.
        # Spliced as lines rather than rebuilt from a split on the heading: putting a split back
        # together has to reproduce the newline the split ate, and getting that wrong rewrites
        # every heading in fourteen files.
        starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

        assert len(starts) > CHAPTER, f"{tag}: {len(starts)} chapters, need {CHAPTER + 1}"

        start = starts[CHAPTER]
        end = starts[CHAPTER + 1] if CHAPTER + 1 < len(starts) else len(lines)

        chapter = lines[start:end]

        # Idempotent: the new entry is there already, so this chapter has been done.
        if any(line.strip() == COMPARE[tag] for line in chapter):
            print(f"{tag:9} already there")
            continue

        # The intro is the first line that is neither the heading, nor blank, nor the page
        # picture — the picture sits between the heading and the prose.
        intro = next(
            i for i, line in enumerate(chapter)
            if i > 0 and line.strip() and not line.lstrip().startswith("!["))

        bullets = [i for i, line in enumerate(chapter) if line.startswith("- ")]

        assert len(bullets) >= 1, f"{tag}: no bullet in the holding chapter"

        chapter = (
            chapter[:intro] + [INTRO[tag]]
            + chapter[intro + 1:bullets[0]] + [PICKS[tag], COMPARE[tag], FIGURE[tag]]
            + chapter[bullets[0] + 1:])

        lines[start:end] = chapter

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} intro + 2 bullets")


if __name__ == "__main__":
    main()
