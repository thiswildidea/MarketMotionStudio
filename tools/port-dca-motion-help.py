# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「定投计划」那一章补上这一轮的三件事。

与持仓页相同的能力，落到这里要写的东西**不一样**，所以这套文案是另起的（资源键同样是
另起的 `Dca*` 而不是复用 `Holdings*`）：

* **多只怎么画。** 持仓页是「几条线直接可比」；这里多了一只**共享的投入线**——金额与频率
  相同时六条投入线完全重合，画满只是噪音，所以只画投得最多的那份。这个决定用户看不见，
  而且画最少的会让别人看起来更赚，必须写下来。
* **大数字按收益率选领先。** 与持仓页不同：定投里上市晚的那只投得少，赚得少不等于计划
  更差。按金额选会把「投得久」当成「计划好」。
* **纵轴不随窗口重算。** 持仓页的理由是「本金线是常数」；这里的理由是**两条线之间的距离
  就是定投的结果**，重算会让它随窗口一起变宽。

**章节序号不写死**：用 `listingtext.chapter_of("NavDcaPlan")` 读导航顺序算出来（实测
17）。写死序号会让说明挂到错章头上，14 语言全错而每句都通顺。

**注入方式**：改引子句与第一条条目，在第一条之后插入两条（多只、末端数字），在章末
追加一条（推进方式）。其余条目原样保留 —— 整章重写会丢掉后来由 `port-custom-range-help.py`
追加的那一条。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在
diff 里表现为首行多一个看不见的字符，肉眼查不出来。

用法：python tools\port-dca-motion-help.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

sys.path.insert(0, str(HERE))

import listingtext  # noqa: E402

CHAPTER = listingtext.chapter_of("NavDcaPlan")

TAGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
        "ja", "ko", "zh-Hans", "zh-Hant"]

INTRO = {
    "en-US": "Buying a fixed amount on a fixed cadence — every trading day, every week or every "
             "month — and watching what the discipline turned into. Several plans can share the "
             "one frame: a value line each, with its running profit riding the line's leading end.",

    "de": "Ein Wertpapier zum festen Betrag in festen Abständen gekauft — an jedem Handelstag, "
          "wöchentlich oder monatlich — und als Animation verfolgt, was aus der Disziplin "
          "geworden ist. Mehrere Pläne können sich ein Bild teilen: eine Wertlinie je Plan, mit "
          "dem laufenden Gewinn an ihrem vorderen Ende.",

    "es": "Comprar un valor con importe y cadencia fijos — cada día de bolsa, cada semana o cada "
          "mes — y ver en animación lo que la disciplina llegó a ser. Varios planes pueden "
          "compartir el mismo cuadro: una línea de valor cada uno, con su ganancia actual en su "
          "extremo.",

    "fr": "Acheter un titre à montant et cadence fixes — chaque jour de bourse, chaque semaine ou "
          "chaque mois — et voir en animation ce que la discipline a produit. Plusieurs plans "
          "peuvent partager le même cadre : une ligne de valeur chacun, avec son gain courant à "
          "son extrémité.",

    "it": "Comprare uno strumento a importo e cadenza fissi — ogni giorno di borsa, ogni settimana "
          "o ogni mese — e vedere in animazione cosa la disciplina è diventata. Più piani possono "
          "condividere lo stesso quadro: una linea di valore ciascuno, con il guadagno corrente "
          "sulla sua estremità.",

    "pl": "Kupowanie jednego instrumentu na stałą kwotę w stałych odstępach — w każdy dzień "
          "sesji, co tydzień lub co miesiąc — i animacja tego, czym stała się dyscyplina. Kilka "
          "planów może dzielić jeden obraz: po jednej linii wartości na każdy, z bieżącym zyskiem "
          "na jej końcu.",

    "pt-BR": "Comprar um ativo com valor e frequência fixos — todo dia de pregão, toda semana ou "
             "todo mês — e ver em animação o que a disciplina virou. Vários planos podem dividir "
             "o mesmo quadro: uma linha de valor cada, com o lucro atual na sua ponta.",

    "cs": "Nákup jednoho nástroje za pevnou částku v pevných intervalech — každý obchodní den, "
          "každý týden nebo každý měsíc — a animace toho, čeho disciplína dosáhla. Několik plánů "
          "může sdílet jeden obraz: po jedné čáře hodnoty na každý, s běžným ziskem na jejím "
          "konci.",

    "tr": "Sabit tutarla sabit aralıklarla bir varlık almak — her işlem günü, her hafta veya her "
          "ay — ve disiplinin neye dönüştüğünü animasyonla görmek. Birkaç plan aynı kareyi "
          "paylaşabilir: her birine bir değer çizgisi, ucunda o anki kâr.",

    "ru": "Покупка одного инструмента на фиксированную сумму с фиксированным интервалом — каждый "
          "торговый день, еженедельно или ежемесячно — и анимация того, во что превратилась "
          "дисциплина. Несколько планов могут делить один кадр: по линии стоимости на каждый, с "
          "текущей прибылью у её конца.",

    "ja": "一定額を一定の頻度で——毎営業日、毎週、または毎月——買い続けると、積み上がった投入額と"
          "評価額の差をアニメで見せます。複数のプランを同じ画面に載せることもでき、プランごとに"
          "評価額の線が 1 本、その先端には今の収益額が付きます。",

    "ko": "일정 금액을 일정한 주기로——매 거래일, 매 주, 또는 매 월——사 모으는 과정에서 누적 "
          "투입액과 평가액이 벌어지는 경주를 애니메이션으로 보여줍니다. 여러 계획을 한 화면에 "
          "올릴 수도 있고, 계획마다 평가액 선 하나, 그 끝에는 지금의 수익 금액이 따라붙습니다.",

    "zh-Hans": "按固定金额、固定频率买入——每个交易日、每周或每月——动画展示累计投入与市值的赛跑。"
               "也可以让几份计划同场比：每份一条市值线，末端跟着它此刻的收益金额。",

    "zh-Hant": "按固定金額、固定頻率買入——每個交易日、每週或每月——動畫展示累計投入與市值的賽跑。"
               "也可以讓幾份計劃同場比：每份一條市值線，末端跟著它此刻的收益金額。",
}

# 原来那条「一键标的随市场变……」，改成先说清单、再说一键预设。
PICKS = {
    "en-US": "- The instruments come from your **own list**, the one the other boards share: "
             "search a code or a name to add one, each chip's switch decides whether it is on "
             "this frame, and the × takes it off the shared list (and off those other boards "
             "with it). The one-tap row follows the market — broad and gold ETFs on the A-share "
             "market, the Hong Kong tracker funds, SPY, QQQ and GLD in the United States — and a "
             "press adds that name and draws it straight away.",

    "de": "- Die Instrumente stammen aus **Ihrer eigenen Liste**, derselben, die auch die anderen "
          "Tafeln nutzen: Code oder Namen eintippen, um eines aufzunehmen; der Schalter auf "
          "jedem Chip entscheidet, ob es auf diesem Bild ist, und das × nimmt es von der "
          "geteilten Liste (und damit auch von den anderen Tafeln). Die Ein-Klick-Zeile folgt "
          "dem Markt — breite und Gold-ETFs auf dem A-Aktien-Markt, die Hongkonger "
          "Tracker-Fonds, in den USA SPY, QQQ und GLD — und ein Druck nimmt den Namen auf und "
          "zeichnet ihn sofort.",

    "es": "- Los instrumentos salen de **tu propia lista**, la misma que comparten los otros "
          "paneles: busca un código o un nombre para añadir uno, el interruptor de cada chip "
          "decide si está en este cuadro, y la × lo quita de la lista compartida (y con ello de "
          "los otros paneles). La fila de un toque sigue al mercado — ETF amplios y de oro en "
          "las acciones A, los fondos rastreados de Hong Kong, SPY, QQQ y GLD en Estados Unidos "
          "— y al pulsar se añade ese nombre y se dibuja al momento.",

    "fr": "- Les instruments viennent de **votre propre liste**, celle que partagent les autres "
          "tableaux : cherchez un code ou un nom pour en ajouter un, l'interrupteur de chaque "
          "pastille décide s'il figure sur ce cadre, et le × le retire de la liste partagée (et "
          "donc des autres tableaux). La rangée en un clic suit le marché — ETF larges et or sur "
          "les actions A, fonds indiciels de Hong Kong, SPY, QQQ et GLD aux États-Unis — et une "
          "pression ajoute ce nom et le dessine aussitôt.",

    "it": "- Gli strumenti arrivano dalla **tua lista**, la stessa che condividono gli altri "
          "pannelli: cerca un codice o un nome per aggiungerne uno, l'interruttore su ogni chip "
          "decide se è su questo quadro, e la × lo toglie dalla lista condivisa (e quindi dagli "
          "altri pannelli). La riga a un tocco segue il mercato — ETF ampi e oro sulle azioni A, "
          "i fondi indicizzati di Hong Kong, SPY, QQQ e GLD negli Stati Uniti — e una pressione "
          "aggiunge quel nome e lo disegna subito.",

    "pl": "- Instrumenty pochodzą z **Twojej listy**, tej samej, którą dzielą inne tablice: wpisz "
          "kod lub nazwę, aby dodać; przełącznik na chipie decyduje, czy jest na tym obrazie, a "
          "× usuwa go ze wspólnej listy (a więc i z innych tablic). Wiersz jednego dotknięcia "
          "idzie za rynkiem — szerokie i złote ETF na akcjach A, hongkongskie fundusze śledzące, "
          "w USA SPY, QQQ i GLD — a dotknięcie dodaje tę nazwę i od razu ją rysuje.",

    "pt-BR": "- Os ativos vêm da **sua própria lista**, a mesma que os outros painéis "
             "compartilham: busque um código ou um nome para acrescentar um, o interruptor de "
             "cada chip decide se ele está neste quadro, e o × o remove da lista compartilhada "
             "(e com isso dos outros painéis). A linha de um toque segue o mercado — ETFs amplos "
             "e de ouro nas ações A, os fundos índice de Hong Kong, SPY, QQQ e GLD nos Estados "
             "Unidos — e um toque acrescenta esse nome e o desenha na hora.",

    "cs": "- Nástroje pocházejí z **vašeho seznamu**, téhož, který sdílejí ostatní tabule: "
          "napište kód nebo název a přidejte jej; přepínač na každém chipu rozhoduje, zda je na "
          "tomto obraze, a × jej odebere ze sdíleného seznamu (a tím i z ostatních tabulí). "
          "Řádek na jeden klik jde za trhem — široké a zlaté ETF u A-akcií, hongkongské "
          "trackerové fondy, ve USA SPY, QQQ a GLD — a stisk tento název přidá a hned ho "
          "vykreslí.",

    "tr": "- Varlıklar **kendi listenizden** gelir; diğer tabloların da paylaştığı liste: bir kod "
          "ya da ad arayıp ekleyin, her chip'in anahtarı onun bu karede olup olmadığını "
          "belirler, × ise onu paylaşılan listeden (ve dolayısıyla diğer tablolardan) çıkarır. "
          "Tek dokunuş satırı piyasaya göre değişir: A hisselerinde geniş ve altın ETF'ler, Hong "
          "Kong takip fonları, ABD'de SPY, QQQ ve GLD — bir dokunuş o adı ekleyip hemen çizer.",

    "ru": "- Инструменты берутся из **вашего списка**, того самого, что и у других табло: "
          "введите код или название, чтобы добавить; переключатель на чипе решает, попадёт ли он "
          "в кадр, а × убирает его из общего списка (и тем самым с других табло). Строка "
          "быстрого выбора зависит от рынка — широкие и золотые ETF у A-акций, гонконгские "
          "трекер-фонды, SPY, QQQ и GLD в США — и нажатие добавляет это название и сразу его "
          "рисует.",

    "ja": "- 銘柄は**マイリスト**（他のタブと同じ一つのリスト）から取ります。コードか名前を検索して"
          "追加し、各 chip のスイッチでこの画面に載せるかどうかを決め、× は共有リストから外します"
          "（他のタブからも消えます）。上の一括ボタンは市場ごとに変わります——A 株は広基 ETF と"
          "ゴールド ETF、香港はトラッカーファンド、米国は SPY・QQQ・GLD——押すとその銘柄をリスト"
          "に加えてすぐ描きます。",

    "ko": "- 종목은 **내 목록**(다른 탭과 함께 쓰는 하나의 목록)에서 가져옵니다. 코드나 이름을 "
          "검색해 추가하고, 각 chip의 스위치로 이 화면에 올릴지 정하며, ×는 공유 목록에서 "
          "빼냅니다(다른 탭에서도 사라집니다). 위의 한 번 누르기 버튼은 시장에 따라 바뀝니다 — "
          "A주는 광폭 ETF와 금 ETF, 홍콩은 트래커 펀드, 미국은 SPY·QQQ·GLD — 누르면 그 종목이 "
          "목록에 들어가고 곧바로 그려집니다.",

    "zh-Hans": "- 标的是你的**自选清单**，与其它榜单共用一份：在框里搜代码或名字加进去，chip 上的"
               "开关决定它上不上这张图，× 把它从清单里删掉（其它榜单也跟着少一条）。上方的「一键"
               "标的」随市场变——A 股是宽基 ETF 与黄金 ETF，港股是盈富基金等追踪基金，美股是 "
               "SPY、QQQ 与 GLD——点一下即加入清单并画出来。",

    "zh-Hant": "- 標的是你的**自選清單**，與其它榜單共用一份：在框裡搜代碼或名字加進去，chip 上的"
               "開關決定它上不上這張圖，× 把它從清單裡刪掉（其它榜單也跟著少一條）。上方的「一鍵"
               "標的」隨市場變——A 股是寬基 ETF 與黃金 ETF，港股是盈富基金等追蹤基金，美股是 "
               "SPY、QQQ 與 GLD——點一下即加入清單並畫出來。",
}

# 新条目一：多份计划怎么比 —— 这里与持仓页的差别（共享投入线、按收益率选领先）才是重点。
COMPARE = {
    "en-US": "- **2 to 6 plans on one frame.** Each puts in the same amount at the same cadence, "
             "buying from its own first trading day. Only the value lines are drawn: six fills "
             "stacked over each other are mud, and at one amount and one cadence the six invested "
             "lines land exactly on top of one another, so the invested line is drawn once — for "
             "the plan that put in the most, since drawing the least would flatter the rest. The "
             "date axis is the union of their days: a listing that starts later begins later, and "
             "is absent before that. Six is the ceiling — past it the fetch refuses rather than "
             "quietly drawing some of them — and an instrument from another market is left off. "
             "With several, the big figure in the middle becomes the **leader's** return in per "
             "cent rather than its money: a later listing has had less paid in, and earning less "
             "is not the same as being the worse plan.",

    "de": "- **2 bis 6 Pläne in einem Bild.** Jeder zahlt denselben Betrag in demselben Rhythmus "
          "ein, ab dem jeweils eigenen ersten Handelstag. Gezeichnet werden nur die Wertlinien: "
          "sechs Füllungen übereinander sind Matsch, und bei gleichem Betrag und Rhythmus liegen "
          "die sechs Einzahlungslinien genau aufeinander, deshalb wird die Einzahlungslinie "
          "einmal gezeichnet — für den Plan mit den höchsten Einzahlungen, weil die niedrigste zu "
          "zeichnen die übrigen zu gut aussehen ließe. Die Zeitachse ist die Vereinigung ihrer "
          "Tage: ein später gelistetes Papier beginnt später und fehlt davor. Sechs ist die "
          "Obergrenze — darüber verweigert der Abruf, statt still ein paar davon zu zeichnen — "
          "und ein Instrument aus einem anderen Markt bleibt weg. Bei mehreren wird die große "
          "Zahl in der Mitte zur Rendite des **führenden** Plans in Prozent statt zu seinem Geld: "
          "Eine spätere Notierung hat weniger eingezahlt, und weniger Gewinn ist nicht dasselbe "
          "wie ein schlechterer Plan.",

    "es": "- **De 2 a 6 planes en un cuadro.** Cada uno aporta el mismo importe con la misma "
          "cadencia, comprando desde su propio primer día de cotización. Solo se dibujan las "
          "líneas de valor: seis rellenos apilados son barro, y con el mismo importe y cadencia "
          "las seis líneas de lo aportado caen exactamente una sobre otra, así que la línea de lo "
          "aportado se dibuja una vez — la del plan que más aportó, porque dibujar la que menos "
          "aportó haría ver mejor a los demás. El eje de fechas es la unión de sus días: un valor "
          "que cotiza más tarde simplemente empieza más tarde, y antes de eso no está. Seis es el "
          "tope —por encima, la descarga se niega en lugar de dibujar solo algunos— y un "
          "instrumento de otro mercado queda fuera. Con varios, la cifra grande del centro pasa a "
          "ser la rentabilidad en porcentaje del plan **líder**, no su dinero: una cotización más "
          "tardía ha aportado menos, y ganar menos no es lo mismo que ser el plan peor.",

    "fr": "- **De 2 à 6 plans sur un même cadre.** Chacun verse le même montant à la même cadence, "
          "en achetant depuis son propre premier jour de cotation. Seules les lignes de valeur "
          "sont tracées : six aplats superposés, c'est de la boue, et à montant et cadence égaux "
          "les six lignes de versement tombent exactement l'une sur l'autre — la ligne des "
          "versements est donc tracée une seule fois, pour le plan qui a le plus versé, car "
          "tracer le plus petit versement ferait paraître les autres meilleurs. L'axe des dates "
          "est l'union de leurs jours : une cote plus tardive commence simplement plus tard, et "
          "n'est pas présente avant. Six est le plafond — au-delà, la récupération refuse au lieu "
          "d'en dessiner quelques-uns — et un instrument d'un autre marché est écarté. Avec "
          "plusieurs, le grand chiffre au centre devient le rendement en pourcentage du plan **en "
          "tête**, et non son argent : une cote plus tardive a moins versé, et gagner moins n'est "
          "pas être le plus mauvais plan.",

    "it": "- **Da 2 a 6 piani in un quadro.** Ciascuno versa lo stesso importo con la stessa "
          "cadenza, comprando dal proprio primo giorno di borsa. Si disegnano solo le linee di "
          "valore: sei riempimenti sovrapposti sono fango, e a parità di importo e cadenza le sei "
          "linee dei versamenti cadono esattamente una sull'altra, quindi la linea dei versamenti "
          "si disegna una volta sola — per il piano che ha versato di più, perché disegnare quello "
          "che ha versato di meno farebbe apparire gli altri migliori. L'asse delle date è "
          "l'unione dei loro giorni: uno strumento quotato più tardi inizia semplicemente più "
          "tardi e prima non c'è. Sei è il tetto — oltre, il recupero rifiuta invece di "
          "disegnarne qualcuno in silenzio — e uno strumento di un altro mercato resta fuori. Con "
          "più piani, la grande cifra al centro diventa il rendimento in percentuale del piano "
          "**in testa**, non il suo denaro: una quotazione più tarda ha versato meno, e "
          "guadagnare meno non è essere il piano peggiore.",

    "pl": "- **Od 2 do 6 planów na jednym obrazie.** Każdy wpłaca tę samą kwotę w tym samym "
          "rytmie, kupując od własnego pierwszego dnia sesyjnego. Rysowane są tylko linie "
          "wartości: sześć wypełnień jeden na drugim to błoto, a przy tej samej kwocie i rytmie "
          "sześć linii wpłat pada dokładnie jedna na drugą — więc linię wpłat rysuje się raz, dla "
          "planu, który wpłacił najwięcej, bo narysowanie najmniejszej wpłaty upiększyłoby "
          "pozostałe. Oś dat to suma ich dni: instrument notowany później po prostu zaczyna się "
          "później i wcześniej go nie ma. Sześć to pułap — powyżej pobieranie odmawia, zamiast po "
          "cichu narysować kilka z nich — a instrument z innego rynku zostaje pominięty. Przy "
          "kilku planach wielka liczba pośrodku staje się stopą zwrotu w procentach planu "
          "**prowadzącego**, a nie jego kwotą: późniejsza notacja wpłaciła mniej, a zarobić mniej "
          "to nie to samo co być gorszym planem.",

    "pt-BR": "- **De 2 a 6 planos num quadro.** Cada um aporta o mesmo valor na mesma frequência, "
             "comprando desde o seu próprio primeiro dia de negociação. Só as linhas de valor são "
             "desenhadas: seis preenchimentos empilhados são lama, e com o mesmo valor e "
             "frequência as seis linhas do aportado caem exatamente umas sobre as outras — então "
             "a linha do aportado é desenhada uma vez, para o plano que mais aportou, porque "
             "desenhar a que menos aportou faria os outros parecerem melhores. O eixo de datas é "
             "a união dos dias deles: um ativo listado mais tarde simplesmente começa mais tarde, "
             "e antes disso não está lá. Seis é o teto — acima disso a obtenção recusa em vez de "
             "desenhar alguns em silêncio — e um ativo de outro mercado fica de fora. Com vários, "
             "o número grande no meio passa a ser o retorno em porcentagem do plano **líder**, "
             "não o seu dinheiro: uma listagem mais tardia aportou menos, e ganhar menos não é o "
             "mesmo que ser o plano pior.",

    "cs": "- **2 až 6 plánů na jednom obraze.** Každý vkládá stejnou částku ve stejném rytmu a "
          "nakupuje od svého prvního obchodního dne. Kreslí se jen čáry hodnoty: šest výplní přes "
          "sebe je bláto, a při stejné částce a rytmu leží šest čar vkladů přesně na sobě — proto "
          "se čára vkladů kreslí jednou, pro plán, který vložil nejvíc, protože kreslit tu s "
          "nejmenším vkladem by ostatní ukazovala lepší. Datová osa je sjednocením jejich dnů: "
          "nástroj uvedený později prostě začíná později a předtím tam není. Šest je strop — nad "
          "ním získání odmítne, místo aby potichu nakreslilo některé z nich — a nástroj z jiného "
          "trhu zůstane venku. U několika plánů se velké číslo uprostřed stává výnosem v "
          "procentech **vedoucího** plánu, ne jeho penězi: pozdější kótování vložilo méně, a "
          "vydělat méně není totéž co být horším plánem.",

    "tr": "- **Bir karede 2 ila 6 plan.** Her biri aynı tutarı aynı sıklıkta yatırır ve kendi ilk "
          "işlem gününden itibaren alır. Yalnızca değer çizgileri çizilir: üst üste altı dolgu "
          "çamurdur, ve aynı tutar ve sıklıkta altı yatırım çizgisi tamamen üst üste biner — bu "
          "yüzden yatırım çizgisi bir kez çizilir, en çok yatıran plan için; çünkü en az yatıranı "
          "çizmek diğerlerini daha iyi gösterirdi. Tarih ekseni günlerinin birleşimidir: daha "
          "geç kote olan yalnızca daha geç başlar ve öncesinde yoktur. Sınır altıdır — üstünde "
          "veri çekme, sessizce birkaçını çizmek yerine reddeder — ve başka bir piyasanın varlığı "
          "dışarıda kalır. Birkaçı birlikteyken ortadaki büyük sayı, **öndeki** planın yüzde "
          "olarak getirisi olur, parası değil: daha geç kote olan daha az yatırmıştır, ve daha "
          "az kazanmak daha kötü plan olmak değildir.",

    "ru": "- **От 2 до 6 планов в одном кадре.** Каждый вносит одну и ту же сумму с той же "
          "периодичностью, покупая со своего первого торгового дня. Рисуются только линии "
          "стоимости: шесть заливок друг поверх друга — это грязь, а при одинаковой сумме и "
          "периодичности шесть линий взносов ложатся точно друг на друга, поэтому линия взносов "
          "рисуется один раз — для плана, который внёс больше всех, потому что нарисовать "
          "наименьший взнос значило бы приукрасить остальные. Ось дат — объединение их дней: "
          "инструмент, допущенный позже, просто начинается позже, и раньше его нет. Шесть — "
          "предел; выше получение отказывает вместо того, чтобы молча нарисовать несколько — и "
          "инструмент с другого рынка не берётся. При нескольких планах большая цифра посередине "
          "становится доходностью **лидирующего** плана в процентах, а не его деньгами: более "
          "поздний листинг внёс меньше, и заработать меньше — не то же, что быть планом хуже.",

    "ja": "- **2〜6 プランを同じ画面に載せられます。** どれも同じ金額を同じ頻度で、それぞれ自分の"
          "最初の営業日から買います。描くのは評価額の線だけです——塗りを 6 枚重ねると泥になり、"
          "金額と頻度が同じなら 6 本の投入額の線は完全に重なります。だから投入額の線は 1 本だけ、"
          "最も多く積んだプランの分を描きます（一番少ない分を描くと、他が得に見えます）。日付軸は"
          "和集合で、上場が遅い銘柄は遅く始まり、それ以前には存在しません。上限は 6 つ——超えると、"
          "こっそり何本か描くのではなく取得を拒否します——別市場の銘柄は載りません。複数のとき、"
          "中央の大きな数字は**首位**のプランの収益率（％）になり、金額ではなくなります。上場が"
          "遅いものは積んだ額が少ないので、稼ぎが少ないことは計画が劣ることと同じではありません。",

    "ko": "- **한 화면에 2~6개 계획.** 모두 같은 금액을 같은 주기로, 각자 자신의 첫 거래일부터 "
          "삽니다. 그리는 것은 평가액 선뿐입니다 — 채움을 여섯 겹 쌓으면 진흙이 되고, 금액과 "
          "주기가 같으면 여섯 개의 투입액 선은 완전히 겹칩니다. 그래서 투입액 선은 한 번만, 가장 "
          "많이 넣은 계획의 것을 그립니다(가장 적게 넣은 것을 그리면 나머지가 더 잘난 것처럼 "
          "보입니다). 날짜 축은 합집합이고, 상장이 늦은 종목은 늦게 시작하며 그 이전에는 없습니다. "
          "상한은 6개 — 넘으면 조용히 몇 개만 그리는 대신 받아오기를 거부합니다 — 다른 시장의 "
          "종목은 올리지 않습니다. 여러 개일 때 가운데 큰 숫자는 **선두** 계획의 수익률(%)이 되며 "
          "금액이 아닙니다. 상장이 늦은 종목은 넣은 돈이 적으므로, 덜 벌었다고 해서 계획이 더 "
          "나쁜 것은 아닙니다.",

    "zh-Hans": "- **可以同时比 2~6 份**：每份每期投同样的钱、频率相同，各自从自己的首个交易日买起。"
               "画面上只画市值线——六层填充叠在一起是一团泥，而金额与频率相同时六条投入线完全"
               "重合，所以投入只画一条，画的是投得最多的那份（画最少的会让别人看起来更赚）。"
               "日期轴取并集：上市晚的那只从它自己的第一天开始画，在此之前画面上没有它。上限 "
               "6 份，超了会拒绝取数而不是少画几份；别的市场的标的不会画上来。几份一起时中间"
               "那个大数字换成**领先那份**的收益率——按收益率而不是收益金额选：上市晚的投得少，"
               "赚得少不等于计划更差。",

    "zh-Hant": "- **可以同時比 2~6 份**：每份每期投同樣的錢、頻率相同，各自從自己的首個交易日買起。"
               "畫面上只畫市值線——六層填充疊在一起是一團泥，而金額與頻率相同時六條投入線完全"
               "重合，所以投入只畫一條，畫的是投得最多的那份（畫最少的會讓別人看起來更賺）。"
               "日期軸取聯集：上市晚的那隻從它自己的第一天開始畫，在此之前畫面上沒有它。上限 "
               "6 份，超了會拒絕取數而不是少畫幾份；別的市場的標的不會畫上來。幾份一起時中間"
               "那個大數字換成**領先那份**的收益率——按收益率而不是收益金額選：上市晚的投得少，"
               "賺得少不等於計劃更差。",
}

# 新条目二：末端跟着的收益金额。
FIGURE = {
    "en-US": "- **The figure rides the line.** A label at each plan's leading end names it and "
             "gives the money it is up at that moment, and it moves with the animation — scrub "
             "the bar and it goes with the line. With one plan the big figure in the middle is "
             "still the return in per cent, and the label is there all the same.",

    "de": "- **Die Zahl läuft auf der Linie mit.** Ein Etikett am vorderen Ende jedes Plans nennt "
          "ihn und nennt den Betrag, um den er in diesem Moment vorne liegt; es wandert mit der "
          "Animation — ziehen Sie an der Leiste, geht es mit der Linie mit. Bei einem Plan ist "
          "die große Zahl in der Mitte weiterhin die Rendite in Prozent, und das Etikett ist "
          "trotzdem da.",

    "es": "- **La cifra cabalga la línea.** Una etiqueta en el extremo de cada plan lo nombra y "
          "da el dinero que lleva ganado en ese momento, y se mueve con la animación — arrastra "
          "la barra y va con la línea. Con un solo plan la cifra grande del centro sigue siendo "
          "la rentabilidad en porcentaje, y la etiqueta está igualmente.",

    "fr": "- **Le chiffre suit la ligne.** Une étiquette à l'extrémité de chaque plan le nomme et "
          "donne l'argent qu'il a gagné à cet instant ; elle bouge avec l'animation — tirez la "
          "barre et elle suit la ligne. Avec un seul plan, le grand chiffre au centre reste le "
          "rendement en pourcentage, et l'étiquette est là tout de même.",

    "it": "- **La cifra segue la linea.** Un'etichetta all'estremità di ogni piano lo nomina e dà "
          "il denaro che ha guadagnato in quel momento; si muove con l'animazione — trascina la "
          "barra e va con la linea. Con un solo piano la grande cifra al centro è ancora il "
          "rendimento in percentuale, e l'etichetta c'è comunque.",

    "pl": "- **Liczba jedzie na linii.** Etykieta na końcu każdego planu nazywa go i podaje "
          "kwotę, o jaką jest w tym momencie do przodu; porusza się z animacją — pociągnij pasek, "
          "a pójdzie z linią. Przy jednym planie wielka liczba pośrodku to nadal stopa zwrotu w "
          "procentach, a etykieta i tak jest.",

    "pt-BR": "- **O número acompanha a linha.** Um rótulo na ponta de cada plano o nomeia e dá o "
             "dinheiro que ele ganhou naquele momento; move-se com a animação — arraste a barra e "
             "ele vai com a linha. Com um só plano o número grande no meio continua sendo o "
             "retorno em porcentagem, e o rótulo está lá do mesmo jeito.",

    "cs": "- **Číslo jede na čáře.** Štítek na konci každého plánu jej pojmenuje a uvede peníze, "
          "o které je v daném okamžiku napřed; pohybuje se s animací — potáhněte lištou a půjde s "
          "čarou. U jednoho plánu je velké číslo uprostřed stále výnosem v procentech a štítek je "
          "tam přesto.",

    "tr": "- **Sayı çizginin üstünde gider.** Her planın ucundaki etiket onu adlandırır ve o anda "
          "kazandığı parayı verir; animasyonla birlikte hareket eder — çubuğu sürükleyin, çizgiyle "
          "gider. Tek planla ortadaki büyük sayı yine yüzde getiridir, ve etiket yine de oradadır.",

    "ru": "- **Цифра едет на линии.** Метка на конце каждого плана называет его и даёт деньги, "
          "которые он к этому моменту заработал; она движется вместе с анимацией — тяните полосу, "
          "и она идёт с линией. При одном плане большая цифра посередине всё так же доходность в "
          "процентах, и метка при этом есть.",

    "ja": "- **数字は線の上を一緒に動きます。** 各プランの先端のラベルに名前と、その時点でいくら"
          "儲かっているかが出ます。アニメーションと一緒に動くので、バーをドラッグすると線と一緒に"
          "ついてきます。プランが 1 つのとき中央の大きな数字はこれまでどおり収益率で、ラベルも"
          "同じように出ます。",

    "ko": "- **숫자가 선을 타고 갑니다.** 각 계획의 끝에 붙은 라벨에 이름과 그 시점의 수익 금액이 "
          "나옵니다. 애니메이션과 함께 움직이므로 막대를 끌면 선과 같이 갑니다. 계획이 하나일 때 "
          "가운데 큰 숫자는 여전히 수익률이고, 라벨도 마찬가지로 있습니다.",

    "zh-Hans": "- **每条线末端跟着数字**：写着这份计划的名字和此刻的收益金额，随动画一起走——拖动"
               "进度条，它跟着线走。一份时中间那个大数字是收益率，末端那颗标签仍然在。",

    "zh-Hant": "- **每條線末端跟著數字**：寫著這份計劃的名字和此刻的收益金額，隨動畫一起走——拖動"
               "進度條，它跟著線走。一份時中間那個大數字是收益率，末端那顆標籤仍然在。",
}

# 新条目三：两种推进方式，以及纵轴为什么不跟着窗口重算。
MOTION = {
    "en-US": "- **Two motions.** *Grow across the span* lays the whole range down at once; "
             "*scroll a window* holds a window of a fixed number of trading days and walks it "
             "from the start of the range to its end — the only way a long daily series keeps its "
             "wobbles readable. The window only counts while scrolling, and both motions read "
             "**the same marks**: switching re-fetches nothing. **The vertical axis is not "
             "rescaled per window**: the gap between the two lines *is* the result of a plan, and "
             "rescaling would widen it along with the window.",

    "de": "- **Zwei Ablaufarten.** *Über die ganze Spanne* legt den gesamten Zeitraum auf einmal "
          "hin; *Fenster weiterbewegen* hält ein Fenster aus einer festen Zahl von Handelstagen "
          "und schiebt es vom Anfang bis zum Ende des Zeitraums — nur so bleiben die Ausschläge "
          "einer langen Tagesreihe lesbar. Das Fenster zählt nur beim Weiterbewegen, und beide "
          "Arten lesen **dieselben Kurse** — Umschalten lädt nichts neu. **Die senkrechte Achse "
          "wird nicht je Fenster neu skaliert**: der Abstand zwischen den beiden Linien *ist* das "
          "Ergebnis eines Plans, und eine Neuskalierung würde ihn mit dem Fenster breiter ziehen.",

    "es": "- **Dos modos de avance.** *Crecer por todo el periodo* despliega todo el intervalo de "
          "una vez; *desplazar una ventana* mantiene una ventana de un número fijo de días de "
          "cotización y la recorre del inicio al fin del intervalo — es la única forma de que una "
          "serie diaria larga conserve legibles sus oscilaciones. La ventana solo cuenta al "
          "desplazar, y ambos modos leen **los mismos datos**: cambiar no vuelve a descargar. "
          "**El eje vertical no se reescala por ventana**: la distancia entre las dos líneas *es* "
          "el resultado de un plan, y reescalar la ensancharía junto con la ventana.",

    "fr": "- **Deux animations.** *Tracer tout l'intervalle* déploie toute la période d'un coup ; "
          "*fenêtre glissante* garde une fenêtre d'un nombre fixe de jours de cotation et la fait "
          "avancer du début à la fin de la période — le seul moyen de garder lisibles les "
          "oscillations d'une longue série quotidienne. La fenêtre ne compte qu'en défilement, et "
          "les deux animations lisent **les mêmes données** : en changer ne recharge rien. "
          "**L'axe vertical n'est pas rééchelonné par fenêtre** : l'écart entre les deux lignes "
          "*est* le résultat d'un plan, et le rééchelonner l'élargirait avec la fenêtre.",

    "it": "- **Due animazioni.** *Tutto l'intervallo* dispiega l'intero periodo in una volta; "
          "*finestra scorrevole* mantiene una finestra di un numero fisso di giorni di "
          "contrattazione e la fa avanzare dall'inizio alla fine del periodo: è l'unico modo "
          "perché una lunga serie giornaliera resti leggibile nei suoi movimenti. La finestra "
          "conta solo nello scorrimento, ed entrambe le animazioni leggono **gli stessi dati**: "
          "cambiare non ricarica nulla. **L'asse verticale non è riscalato per finestra**: la "
          "distanza fra le due linee *è* il risultato di un piano, e riscalarla la allargherebbe "
          "insieme alla finestra.",

    "pl": "- **Dwa tryby animacji.** *Cały zakres naraz* rozkłada cały okres za jednym razem; "
          "*przesuwne okno* utrzymuje okno o stałej liczbie dni sesyjnych i przesuwa je od "
          "początku do końca okresu — tylko tak długa seria dzienna zachowuje czytelne wahania. "
          "Okno liczy się tylko przy przewijaniu, a oba tryby czytają **te same dane** — "
          "przełączenie nic nie pobiera ponownie. **Oś pionowa nie jest przeliczana dla okna**: "
          "odstęp między dwiema liniami *jest* wynikiem planu, a przeliczenie rozciągnęłoby go "
          "razem z oknem.",

    "pt-BR": "- **Dois modos de avanço.** *Todo o período* dispõe o intervalo inteiro de uma vez; "
             "*janela deslizante* mantém uma janela de um número fixo de dias de negociação e a "
             "percorre do início ao fim do intervalo — é a única forma de uma longa série diária "
             "manter as oscilações legíveis. A janela só conta ao deslizar, e os dois modos leem "
             "**os mesmos dados**: trocar não baixa nada de novo. **O eixo vertical não é "
             "reescalado por janela**: a distância entre as duas linhas *é* o resultado de um "
             "plano, e reescalar a alargaria junto com a janela.",

    "cs": "- **Dva způsoby animace.** *Celé období* rozloží celý rozsah najednou; *posuvné okno* "
          "drží okno s pevným počtem obchodních dnů a posouvá je od začátku do konce rozsahu — "
          "jen tak zůstanou výkyvy dlouhé denní řady čitelné. Okno má význam jen při posouvání a "
          "oba způsoby čtou **stejné kurzy** — přepnutí nic nenačítá. **Svislá osa se pro okno "
          "nepřepočítává**: odstup mezi oběma čarami *je* výsledkem plánu, a přepočet by ho "
          "roztáhl spolu s oknem.",

    "tr": "- **İki ilerleme biçimi.** *Aralığın tamamı* tüm dönemi bir anda serer; *kayan pencere* "
          "sabit sayıda işlem gününden oluşan bir pencereyi aralığın başından sonuna kadar "
          "yürütür — uzun bir günlük serinin dalgalanmalarını okunur tutmanın tek yolu budur. "
          "Pencere yalnızca kaydırırken anlam taşır ve iki biçim de **aynı fiyatları** okur — "
          "geçiş yeniden veri çekmez. **Dikey eksen pencereye göre yeniden ölçeklenmez**: iki "
          "çizgi arasındaki mesafe planın *ta kendisidir*; yeniden ölçeklemek onu pencereyle "
          "birlikte genişletirdi.",

    "ru": "- **Два способа продвижения.** «Весь диапазон» раскладывает весь период сразу; "
          "«скользящее окно» держит окно из фиксированного числа торговых дней и ведёт его от "
          "начала периода к концу — только так у длинного дневного ряда колебания остаются "
          "читаемыми. Окно имеет смысл только при прокрутке, и оба способа читают **одни и те же "
          "цены** — переключение ничего не загружает заново. **Вертикальная ось не "
          "пересчитывается под окно**: расстояние между двумя линиями и *есть* результат плана, а "
          "пересчёт растянул бы его вместе с окном.",

    "ja": "- **2 つの進行方式。**「全区間を描く」は期間全体を一度に敷き詰めます。「窓をスクロール」"
          "は一定の営業日数の窓を期間の先頭から末尾まで動かします——長い日次系列の揺れを読める形で"
          "保つにはこれしかありません。窓はスクロール時だけ意味を持ち、どちらも**同じデータ**を"
          "読むので、切り替えても再取得はしません。**縦軸は窓ごとに再計算しません**——2 本の線の"
          "あいだの距離こそが定投の結果であり、再計算すれば窓と一緒に広がってしまいます。",

    "ko": "- **두 가지 진행 방식.** *전체 구간 그리기*는 기간 전체를 한 번에 펼칩니다. *창 이동*은 "
          "고정된 거래일 수의 창을 기간 처음부터 끝까지 밀어 갑니다 — 긴 일별 계열의 흔들림을 읽을 "
          "수 있게 유지하는 유일한 방법입니다. 창은 이동할 때만 의미가 있고, 두 방식 모두 **같은 "
          "데이터**를 읽으므로 전환해도 다시 받지 않습니다. **세로 축은 창마다 다시 계산하지 "
          "않습니다** — 두 선 사이의 거리야말로 적립식 투자 결과이며, 다시 계산하면 창과 함께 "
          "넓어집니다.",

    "zh-Hans": "- **两种推进方式**：「整段铺满」把整段区间一次铺开，「窗口滚动」拿一个固定天数的"
               "窗口从起点走到终点——日线长期走势只有这样才能看得出起伏。窗口只在滚动时有效，两种"
               "走法看的是同一份数据、切换不会重新取数。**纵轴不跟着窗口重算**：两条线之间的距离"
               "就是定投的结果，重算会把它随窗口一起变宽。",

    "zh-Hant": "- **兩種推進方式**：「整段鋪滿」把整段區間一次鋪開，「視窗滾動」拿一個固定天數的"
               "視窗從起點走到終點——日線長期走勢只有這樣才能看得出起伏。視窗只在滾動時有效，兩種"
               "走法看的是同一份資料、切換不會重新取數。**縱軸不跟著視窗重算**：兩條線之間的距離"
               "就是定投的結果，重算會把它隨視窗一起變寬。",
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

        assert len(bullets) >= 2, f"{tag}: too few bullets in the DCA chapter"

        chapter = (
            chapter[:intro] + [INTRO[tag]]
            + chapter[intro + 1:bullets[0]] + [PICKS[tag], COMPARE[tag], FIGURE[tag]]
            + chapter[bullets[0] + 1:bullets[-1] + 1] + [MOTION[tag]]
            + chapter[bullets[-1] + 1:])

        lines[start:end] = chapter

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} intro + 3 bullets")


if __name__ == "__main__":
    main()
