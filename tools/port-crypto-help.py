# -*- coding: utf-8 -*-
r"""把「加密货币」三章插进 14 份 help-*.md。

**位置按序号找，不按标题找**（`POSITION = 20`，也就是「Video」那一章之前）：14 份文件里
标题是各语言自己写的，唯一相同的是顺序。三章作为一整块插入，所以同结构同顺序这条约束
一次就满足了。

**整块替换才算幂等**。一块里有三个 `##`，所以删旧块不能只删到下一个标题为止 —— 那会留下
另外两章，第二次运行就变成两份。这里按「三章的标题集合」逐行识别：碰到属于这一块的标题
就一直丢，碰到下一个不属于它的标题才继续留。

文件是 **UTF-8 带 BOM**；行尾照抄原文（CRLF 或 LF），否则整块在 git 里显示成重写。

用法：python tools\port-crypto-help.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

TAGS = [
    "en-US", "de", "es", "fr", "it", "pl", "pt-BR",
    "cs", "tr", "ru", "ja", "ko", "zh-Hans", "zh-Hant",
]

# 插在这里：现有最后一页章节之后、「Video」之前。
POSITION = 20

SECTIONS = {
    "en-US": """## Crypto Candles

One coin's daily prices as candles, in US dollars, from a public source. Weekly and monthly are gathered from those same days.

- The twelve coins on offer are the ones both sources carry with years of daily history behind them. There is no search box: the two sources spell the same coin differently, and a name typed into one reaches neither.
- **Period** — day, week or month — changes which series is drawn, so changing it fetches again. **Style** and **Motion** do not; they redraw what is already here.
- A coin trades every day of the year, so a range has no holiday to step over and no day missing from it, and a coin neither pays a dividend nor splits: the close *is* the return, and no adjustment is applied anywhere on these three pages.
- When only the fallback source can be reached, it has one price a day rather than four, and candles and bars are then drawn as a line — a body and two wicks made out of a single close is a shape the coin never made. The page says so under the style box when that is the case.
- Up to six coins can be drawn at once; a seventh press is not accepted, because a seventh curve would take a colour the sixth already has. Compared side by side they are drawn as cumulative change, since the coins are not priced in the same range.
- **These three pages appear only when a source answers.** Both sources are outside the mainland's reach, so a machine inside it simply does not get them in the menu — three items offering data they cannot fetch would be three items that fail.

## Crypto DCA Plan

Buying one coin on a fixed rhythm — weekly, say, or monthly — and what that plan is worth today.

- **Frequency** and **Amount** say how often and how much, in US dollars. The plan buys on the first day of each period the range covers.
- What is drawn is the money put in against what the holding is worth, day by day, with the buys marked: a fall you bought into reads differently from one you did not.
- Up to six plans can be compared. Compared, they are drawn as cumulative change rather than as money, so a coin priced at 60,000 dollars and one priced at half a dollar can be read against each other.
- A coin listed after the range began starts at its own first day, and a coin with no price anywhere in the range is named on the status line rather than drawn as a flat line.
- Days here are calendar days. A coin trades on every one of them, so a year of weekly buying is about 52 buys and a year of monthly buying is 12, and neither figure is approximated.

## Crypto Holdings Return

A sum put into one coin on a day, and what it is worth now.

- **Capital** is the sum, in US dollars; the range says the day it went in and the day to stop. The page buys at the first close in the range and holds to the last.
- What is drawn is the holding's value day by day against the money that went in, so the line sits above its starting point while the holding is ahead and below it when it is not.
- Up to six coins can be held side by side; a seventh press is not accepted. Compared, each is drawn as cumulative change rather than as value, so two coins bought at very different prices can be read together.
- Days here are calendar days, and a coin trades on every one of them: a year of holding is about 365 days, not the 243 a stock market would give you.
- If only the fallback source can be reached, the range it can fill is about a year. The page then says where the range really starts, rather than quietly beginning later than the date that was typed.
""",
    "de": """## Krypto-Kerzen

Die Tageskerzen einer Münze, in US-Dollar, aus einer öffentlichen Quelle. Wochen- und Monatskerzen werden aus denselben Tagen gebildet.

- Die zwölf angebotenen Münzen sind die, zu denen beide Quellen jahrelange Tageshistorie haben. Es gibt kein Suchfeld: Die beiden Quellen schreiben dieselbe Münze unterschiedlich, und ein eingetippter Name erreicht keine von beiden.
- **Intervall** — Tag, Woche oder Monat — entscheidet, welche Reihe gezeichnet wird, und lädt daher neu. **Darstellung** und **Ablauf** tun das nicht; sie zeichnen nur neu, was schon hier ist.
- Eine Münze wird an jedem Tag des Jahres gehandelt: Ein Zeitraum hat keine Feiertage zu überspringen und keinen fehlenden Tag. Eine Münze zahlt weder Dividende noch splittet sie — der Schlusskurs *ist* die Rendite, und auf diesen drei Seiten wird nirgends bereinigt.
- Wenn nur die Ersatzquelle erreichbar ist, hat sie einen Kurs pro Tag statt vier, und Kerzen und Balken werden dann als Linie gezeichnet: Ein Körper mit zwei Dochten aus einem einzigen Schlusskurs ist eine Form, die die Münze nie hatte. Die Seite sagt das unter dem Darstellungsfeld, wenn es so ist.
- Bis zu sechs Münzen lassen sich gleichzeitig zeichnen; ein siebter Druck wird nicht angenommen, denn eine siebte Kurve nähme eine Farbe, die die sechste schon hat. Im Vergleich werden sie als kumulative Veränderung gezeichnet, weil die Münzen nicht in derselben Größenordnung notieren.
- **Diese drei Seiten erscheinen nur, wenn eine Quelle antwortet.** Beide Quellen liegen außerhalb der Reichweite des Festlands; ein Rechner dort bekommt sie im Menü schlicht nicht — drei Einträge, die Daten anbieten, die sie nicht holen können, wären drei Einträge, die scheitern.

## Krypto-Sparplan

Eine Münze in festem Rhythmus kaufen — etwa wöchentlich oder monatlich — und was dieser Plan heute wert ist.

- **Rhythmus** und **Betrag** sagen, wie oft und wie viel, in US-Dollar. Der Plan kauft am ersten Tag jedes Zeitraums, den die Spanne umfasst.
- Gezeichnet wird das eingezahlte Geld gegen den Wert des Bestands, Tag für Tag, mit markierten Käufen: Ein Rückgang, in den hineingekauft wurde, liest sich anders als einer, in den nicht hineingekauft wurde.
- Bis zu sechs Pläne lassen sich vergleichen. Im Vergleich werden sie als kumulative Veränderung gezeichnet statt als Geld, damit sich eine Münze zu 60.000 Dollar und eine zu einem halben Dollar gegeneinander lesen lassen.
- Eine Münze, die erst nach Beginn der Spanne gelistet wurde, beginnt an ihrem eigenen ersten Tag, und eine Münze ohne Kurs in der ganzen Spanne wird auf der Statuszeile genannt statt als flache Linie gezeichnet.
- Tage sind hier Kalendertage. Eine Münze wird an jedem gehandelt: Ein Jahr wöchentlichen Kaufens sind etwa 52 Käufe, ein Jahr monatlichen Kaufens 12, und keine der beiden Zahlen ist geschätzt.

## Ertrag der Krypto-Bestände

Ein Betrag, an einem Tag in eine Münze gelegt, und was er heute wert ist.

- **Kapital** ist der Betrag in US-Dollar; die Spanne nennt den Tag des Einstiegs und den Tag, an dem Schluss ist. Die Seite kauft zum ersten Schlusskurs der Spanne und hält bis zum letzten.
- Gezeichnet wird der Wert des Bestands Tag für Tag gegen das eingezahlte Geld: Die Linie liegt über ihrem Startpunkt, solange der Bestand im Plus ist, und darunter, wenn nicht.
- Bis zu sechs Münzen lassen sich nebeneinander halten; ein siebter Druck wird nicht angenommen. Im Vergleich wird jede als kumulative Veränderung gezeichnet statt als Wert, damit zwei zu ganz unterschiedlichen Kursen gekaufte Münzen zusammen lesbar sind.
- Tage sind hier Kalendertage, und eine Münze wird an jedem gehandelt: Ein Jahr Halten sind etwa 365 Tage, nicht die 243, die eine Börse gäbe.
- Wenn nur die Ersatzquelle erreichbar ist, reicht ihre Spanne etwa ein Jahr. Die Seite sagt dann, wo die Spanne wirklich beginnt, statt still später anzufangen als das eingegebene Datum.
""",
    "es": """## Velas cripto

Las velas diarias de una moneda, en dólares estadounidenses, de una fuente pública. Las semanales y mensuales se agrupan a partir de esos mismos días.

- Las doce monedas ofrecidas son las que ambas fuentes tienen con años de historial diario. No hay buscador: las dos fuentes escriben la misma moneda de forma distinta, y un nombre tecleado no llega a ninguna.
- **Intervalo** — día, semana o mes — cambia qué serie se dibuja, así que cambiarlo vuelve a consultar la fuente. **Tipo de dibujo** y **Animación** no; solo redibujan lo que ya está aquí.
- Una moneda cotiza todos los días del año: un rango no tiene festivos que saltar ni días que falten, y una moneda no paga dividendo ni hace split: el cierre *es* la rentabilidad, y en estas tres páginas no se aplica ningún ajuste.
- Si solo se alcanza la fuente de respaldo, esta tiene un precio al día en lugar de cuatro, y entonces las velas y las barras se dibujan como línea: un cuerpo con dos mechas hecho de un solo cierre es una forma que la moneda nunca tuvo. La página lo dice bajo el selector de dibujo cuando ese es el caso.
- Se pueden dibujar hasta seis monedas a la vez; una séptima pulsación no se acepta, porque una séptima curva tomaría un color que la sexta ya tiene. Comparadas se dibujan como variación acumulada, porque las monedas no cotizan en el mismo orden de magnitud.
- **Estas tres páginas solo aparecen cuando una fuente responde.** Ambas fuentes están fuera del alcance de China continental, así que un equipo allí simplemente no las ve en el menú: tres entradas que ofrecen datos que no pueden obtener serían tres entradas que fallan.

## Plan DCA cripto

Comprar una moneda con ritmo fijo — semanal, por ejemplo, o mensual — y cuánto vale ese plan hoy.

- **Frecuencia** e **Importe** dicen cada cuánto y cuánto, en dólares estadounidenses. El plan compra el primer día de cada periodo que cubre el rango.
- Lo que se dibuja es el dinero aportado contra lo que vale la posición, día a día, con las compras marcadas: una caída en la que compraste se lee distinto de una en la que no.
- Se pueden comparar hasta seis planes. Comparados se dibujan como variación acumulada en lugar de dinero, para que una moneda a 60.000 dólares y otra a medio dólar puedan leerse juntas.
- Una moneda listada después de que empezara el rango empieza en su propio primer día, y una moneda sin precio en todo el rango se nombra en la línea de estado en lugar de dibujarse como una línea plana.
- Los días aquí son días naturales. Una moneda cotiza en todos ellos: un año de compras semanales son unas 52 compras y uno de mensuales, 12, y ninguna de las dos cifras es aproximada.

## Rentabilidad de la cartera cripto

Una suma puesta en una moneda un día, y cuánto vale hoy.

- **Capital** es la suma, en dólares estadounidenses; el rango dice el día en que entró y el día de parada. La página compra al primer cierre del rango y mantiene hasta el último.
- Lo que se dibuja es el valor de la posición día a día contra el dinero aportado: la línea queda por encima de su punto de partida mientras la posición gana y por debajo cuando no.
- Se pueden mantener hasta seis monedas a la vez; una séptima pulsación no se acepta. Comparadas, cada una se dibuja como variación acumulada en lugar de valor, para que dos monedas compradas a precios muy distintos puedan leerse juntas.
- Los días aquí son días naturales, y una moneda cotiza en todos: un año de mantenimiento son unos 365 días, no los 243 que daría una bolsa.
- Si solo se alcanza la fuente de respaldo, el rango que puede llenar es de about un año. La página dice entonces dónde empieza realmente el rango, en lugar de empezar silenciosamente más tarde que la fecha escrita.
""",
    "fr": """## Chandeliers crypto

Les chandeliers quotidiens d'une cryptomonnaie, en dollars américains, depuis une source publique. Les hebdomadaires et mensuels sont regroupés à partir de ces mêmes jours.

- Les douze cryptomonnaies proposées sont celles que les deux sources portent avec des années d'historique quotidien. Il n'y a pas de champ de recherche : les deux sources écrivent la même cryptomonnaie différemment, et un nom tapé n'atteint ni l'une ni l'autre.
- **Granularité** — jour, semaine ou mois — change la série tracée, et relance donc la récupération. **Type de tracé** et **Animation** non ; ils redessinent ce qui est déjà là.
- Une cryptomonnaie se négocie tous les jours de l'année : un intervalle n'a aucun jour férié à sauter et aucun jour manquant, et une cryptomonnaie ne verse ni dividende ni ne fractionne : la clôture *est* le rendement, et aucun ajustement n'est appliqué sur ces trois pages.
- Si seule la source de repli est atteignable, elle n'a qu'un prix par jour au lieu de quatre, et chandeliers et barres sont alors tracés en ligne — un corps et deux mèches faits d'une seule clôture est une forme que la cryptomonnaie n'a jamais eue. La page le dit sous la liste de tracé lorsque c'est le cas.
- Jusqu'à six cryptomonnaies peuvent être tracées à la fois ; une septième pression n'est pas acceptée, car une septième courbe prendrait une couleur que la sixième a déjà. Comparées, elles sont tracées en variation cumulée, parce qu'elles ne se négocient pas dans la même échelle de prix.
- **Ces trois pages n'apparaissent que lorsqu'une source répond.** Les deux sources sont hors de portée de la Chine continentale : une machine qui s'y trouve ne les voit tout simplement pas dans le menu — trois entrées offrant des données qu'elles ne peuvent pas récupéreraient seraient trois entrées qui échouent.

## Plan DCA crypto

Acheter une cryptomonnaie à rythme fixe — hebdomadaire, disons, ou mensuel — et ce que ce plan vaut aujourd'hui.

- **Fréquence** et **Montant** disent à quelle fréquence et combien, en dollars américains. Le plan achète le premier jour de chaque période couverte par l'intervalle.
- Ce qui est tracé est l'argent versé contre la valeur de la position, jour par jour, avec les achats marqués : une baisse dans laquelle vous avez acheté se lit différemment d'une baisse dans laquelle vous n'avez pas acheté.
- Jusqu'à six plans peuvent être comparés. Comparés, ils sont tracés en variation cumulée plutôt qu'en argent, pour qu'une cryptomonnaie à 60 000 dollars et une à un demi-dollar puissent se lire l'une contre l'autre.
- Une cryptomonnaie cotée après le début de l'intervalle commence à son propre premier jour, et une cryptomonnaie sans prix dans tout l'intervalle est nommée sur la ligne d'état plutôt que tracée en ligne plate.
- Les jours ici sont des jours civils. Une cryptomonnaie se négocie chacun d'eux : une année d'achats hebdomadaires représente environ 52 achats, une année d'achats mensuels 12, et aucun des deux chiffres n'est approximatif.

## Rendement du portefeuille crypto

Une somme placée dans une cryptomonnaie un jour donné, et ce qu'elle vaut aujourd'hui.

- **Capital** est la somme, en dollars américains ; l'intervalle dit le jour de l'entrée et le jour d'arrêt. La page achète à la première clôture de l'intervalle et conserve jusqu'à la dernière.
- Ce qui est tracé est la valeur de la position jour par jour contre l'argent versé : la ligne se situe au-dessus de son point de départ tant que la position est en gain, et en dessous lorsqu'elle ne l'est pas.
- Jusqu'à six cryptomonnaies peuvent être détenues côte à côte ; une septième pression n'est pas acceptée. Comparées, chacune est tracée en variation cumulée plutôt qu'en valeur, pour que deux cryptomonnaies achetées à des prix très différents puissent se lire ensemble.
- Les jours ici sont des jours civils, et une cryptomonnaie se négocie chacun d'eux : une année de détention représente environ 365 jours, et non les 243 que donnerait une bourse.
- Si seule la source de repli est atteignable, l'intervalle qu'elle peut remplir est d'environ un an. La page dit alors où l'intervalle commence réellement, plutôt que de commencer silencieusement plus tard que la date saisie.
""",
    "it": """## Candele crypto

Le candele giornaliere di una moneta, in dollari statunitensi, da una fonte pubblica. Settimanali e mensili sono raggruppate a partire dagli stessi giorni.

- Le dodici monete offerte sono quelle che entrambe le fonti hanno con anni di storia giornaliera. Non c'è una casella di ricerca: le due fonti scrivono la stessa moneta in modo diverso, e un nome digitato non raggiunge né l'una né l'altra.
- **Intervallo** — giorno, settimana o mese — cambia quale serie viene disegnata, quindi cambiarlo ricarica. **Stile** e **Animazione** no: ridisegnano solo ciò che è già qui.
- Una moneta viene scambiata ogni giorno dell'anno: un intervallo non ha festività da saltare né giorni mancanti, e una moneta non paga dividendi né fraziona: la chiusura *è* il rendimento, e su queste tre pagine non si applica alcun aggiustamento.
- Se è raggiungibile solo la fonte di riserva, questa ha un prezzo al giorno invece di quattro, e candele e barre vengono allora disegnate come linea: un corpo con due stoppini fatto da una sola chiusura è una forma che la moneta non ha mai avuto. La pagina lo dice sotto la lista dello stile quando è questo il caso.
- Fino a sei monete possono essere disegnate insieme; una settima pressione non viene accettata, perché una settima curva prenderebbe un colore che la sesta ha già. Nel confronto sono disegnate come variazione cumulata, perché le monete non hanno prezzi nello stesso ordine di grandezza.
- **Queste tre pagine appaiono solo quando una fonte risponde.** Entrambe le fonti sono fuori dalla portata della Cina continentale, quindi una macchina lì dentro non le trova affatto nel menu: tre voci che offrono dati che non possono recuperare sarebbero tre voci che falliscono.

## Piano DCA crypto

Comprare una moneta a ritmo fisso — settimanale, per dire, o mensile — e quanto vale oggi quel piano.

- **Frequenza** e **Importo** dicono ogni quanto e quanto, in dollari statunitensi. Il piano compra il primo giorno di ogni periodo coperto dall'intervallo.
- Ciò che si disegna è il denaro versato contro il valore della posizione, giorno per giorno, con gli acquisti segnati: un calo in cui avete comprato si legge diversamente da uno in cui non l'avete fatto.
- Fino a sei piani possono essere confrontati. Nel confronto sono disegnati come variazione cumulata anziché come denaro, così una moneta a 60.000 dollari e una a mezzo dollaro possono leggersi l'una contro l'altra.
- Una moneta quotata dopo l'inizio dell'intervallo parte dal proprio primo giorno, e una moneta senza prezzo in tutto l'intervallo viene nominata sulla riga di stato anziché disegnata come una linea piatta.
- I giorni qui sono giorni di calendario. Una moneta viene scambiata in ognuno di essi: un anno di acquisti settimanali sono circa 52 acquisti, uno di acquisti mensili 12, e nessuna delle due cifre è approssimata.

## Rendimento del portafoglio crypto

Una somma messa in una moneta in un giorno, e quanto vale oggi.

- **Capitale** è la somma, in dollari statunitensi; l'intervallo dice il giorno in cui è entrata e il giorno in cui fermarsi. La pagina compra alla prima chiusura dell'intervallo e mantiene fino all'ultima.
- Ciò che si disegna è il valore della posizione giorno per giorno contro il denaro versato: la linea sta sopra il proprio punto di partenza mentre la posizione è in guadagno e sotto quando non lo è.
- Fino a sei monete possono essere detenute affiancate; una settima pressione non viene accettata. Nel confronto ciascuna è disegnata come variazione cumulata anziché come valore, così due monete comprate a prezzi molto diversi possono leggersi insieme.
- I giorni qui sono giorni di calendario, e una moneta viene scambiata in ognuno di essi: un anno di detenzione sono circa 365 giorni, non i 243 che darebbe una borsa.
- Se è raggiungibile solo la fonte di riserva, l'intervallo che riesce a riempire è di circa un anno. La pagina dice allora dove l'intervallo comincia davvero, invece di iniziare silenziosamente più tardi della data digitata.
""",
    "pl": """## Świece krypto

Dzienne świece jednej monety, w dolarach amerykańskich, z publicznego źródła. Tygodniowe i miesięczne są grupowane z tych samych dni.

- Dwanaście oferowanych monet to te, dla których oba źródła mają lata historii dziennej. Nie ma pola wyszukiwania: oba źródła piszą tę samą monetę inaczej, a wpisana nazwa nie trafia do żadnego z nich.
- **Interwał** — dzień, tydzień lub miesiąc — zmienia to, która seria jest rysowana, więc zmiana go pobiera dane od nowa. **Styl** i **Przebieg** nie: one tylko przerysowują to, co już jest.
- Moneta jest notowana każdego dnia roku: zakres nie ma świąt do przeskoczenia ani brakujących dni, a moneta nie płaci dywidendy ani nie dzieli się — kurs zamknięcia *jest* zwrotem i na tych trzech stronach nie stosuje się żadnej korekty.
- Gdy dostępne jest tylko źródło zapasowe, ma ono jedną cenę dziennie zamiast czterech, i wtedy świece oraz słupki są rysowane jako linia: korpus z dwoma knotami zrobiony z jednego zamknięcia to kształt, którego moneta nigdy nie miała. Strona mówi o tym pod listą stylu, gdy tak właśnie jest.
- Jednocześnie można rysować do sześciu monet; siódme naciśnięcie nie jest przyjmowane, bo siódma krzywa wzięłaby kolor, który ma już szósta. W porównaniu rysowane są jako skumulowana zmiana, bo monety nie mają cen w tej samej skali.
- **Te trzy strony pojawiają się tylko wtedy, gdy jakieś źródło odpowie.** Oba źródła są poza zasięgiem Chin kontynentalnych, więc komputer tam po prostu nie dostaje ich w menu: trzy pozycje oferujące dane, których nie mogą pobrać, byłyby trzema pozycjami, które zawodzą.

## Plan DCA krypto

Kupowanie jednej monety w stałym rytmie — powiedzmy tygodniowym lub miesięcznym — i ile ten plan jest dziś wart.

- **Częstotliwość** i **Kwota** mówią jak często i ile, w dolarach amerykańskich. Plan kupuje pierwszego dnia każdego okresu objętego zakresem.
- Rysowane są wpłacone pieniądze przeciwko wartości pozycji, dzień po dniu, z zaznaczonymi zakupami: spadek, w który kupowałeś, czyta się inaczej niż taki, w który nie kupowałeś.
- Można porównać do sześciu planów. W porównaniu rysowane są jako skumulowana zmiana, a nie jako pieniądze, żeby moneta po 60 000 dolarów i moneta po pół dolara dały się czytać obok siebie.
- Moneta notowana po rozpoczęciu zakresu zaczyna od własnego pierwszego dnia, a moneta bez ceny w całym zakresie jest wymieniona w linii stanu zamiast narysowana jako płaska linia.
- Dni to tu dni kalendarzowe. Moneta jest notowana w każdy z nich: rok tygodniowych zakupów to około 52 zakupy, rok miesięcznych to 12 i żadna z tych liczb nie jest przybliżona.

## Zwrot portfela krypto

Kwota włożona w jedną monetę pewnego dnia i ile jest dziś warta.

- **Kapitał** to kwota w dolarach amerykańskich; zakres mówi, którego dnia weszła i którego dnia skończyć. Strona kupuje po pierwszym zamknięciu w zakresie i trzyma do ostatniego.
- Rysowana jest wartość pozycji dzień po dniu przeciwko wpłaconym pieniądzom: linia jest powyżej punktu startu, dopóki pozycja jest na plusie, a poniżej, gdy nie jest.
- Obok siebie można trzymać do sześciu monet; siódme naciśnięcie nie jest przyjmowane. W porównaniu każda jest rysowana jako skumulowana zmiana, a nie jako wartość, żeby dwie monety kupione po bardzo różnych cenach dały się czytać razem.
- Dni to tu dni kalendarzowe i moneta jest notowana w każdy z nich: rok trzymania to około 365 dni, a nie 243, które dałaby giełda.
- Gdy dostępne jest tylko źródło zapasowe, jego zakres to około rok. Strona mówi wtedy, gdzie zakres naprawdę się zaczyna, zamiast po cichu zacząć później niż wpisana data.
""",
    "pt-BR": """## Velas cripto

As velas diárias de uma moeda, em dólares americanos, de uma fonte pública. As semanais e mensais são agrupadas a partir desses mesmos dias.

- As doze moedas oferecidas são as que ambas as fontes têm com anos de histórico diário. Não há caixa de busca: as duas fontes escrevem a mesma moeda de formas diferentes, e um nome digitado não chega a nenhuma.
- **Intervalo** — dia, semana ou mês — muda qual série é desenhada, então mudá-lo busca de novo. **Estilo** e **Animação** não; eles apenas redesenhå o que já está aqui.
- Uma moeda é negociada todos os dias do ano: um intervalo não tem feriado para pular nem dia faltando, e uma moeda não paga dividendo nem sofre desdobramento: o fechamento *é* o retorno, e nenhum ajuste é aplicado nestas três páginas.
- Quando só a fonte reserva é alcançável, ela tem um preço por dia em vez de quatro, e então velas e barras são desenhadas como linha: um corpo com dois pavios feito de um único fechamento é uma forma que a moeda nunca teve. A página diz isso sob a lista de estilo quando é esse o caso.
- Até seis moedas podem ser desenhadas ao mesmo tempo; um sétimo toque não é aceito, porque uma sétima curva tomaria uma cor que a sexta já tem. Comparadas, são desenhadas como variação acumulada, já que as moedas não têm preços na mesma escala.
- **Estas três páginas aparecem apenas quando uma fonte responde.** Ambas as fontes estão fora do alcance da China continental, então uma máquina lá simplesmente não as recebe no menu: três itens oferecendo dados que não conseguem buscar seriam três itens que falham.

## Plano DCA cripto

Comprar uma moeda em ritmo fixo — semanal, digamos, ou mensal — e quanto esse plano vale hoje.

- **Frequência** e **Valor** dizem com que frequência e quanto, em dólares americanos. O plano compra no primeiro dia de cada período coberto pelo intervalo.
- O que se desenha é o dinheiro colocado contra o valor da posição, dia a dia, com as compras marcadas: uma queda em que você comprou se lê de forma diferente de uma em que não comprou.
- Até seis planos podem ser comparados. Comparados, são desenhados como variação acumulada em vez de dinheiro, para que uma moeda a 60 mil dólares e outra a meio dólar possam ser lidas uma contra a outra.
- Uma moeda listada depois do início do intervalo começa no seu próprio primeiro dia, e uma moeda sem preço em todo o intervalo é nomeada na linha de status em vez de desenhada como uma linha reta.
- Os dias aqui são dias corridos. Uma moeda é negociada em todos eles: um ano de compras semanais dá cerca de 52 compras e um de compras mensais, 12, e nenhum dos dois números é aproximado.

## Retorno da carteira cripto

Uma quantia colocada em uma moeda em um dia, e quanto vale hoje.

- **Capital** é a quantia, em dólares americanos; o intervalo diz o dia em que entrou e o dia de parar. A página compra no primeiro fechamento do intervalo e mantém até o último.
- O que se desenha é o valor da posição dia a dia contra o dinheiro colocado: a linha fica acima do ponto de partida enquanto a posição está no lucro e abaixo quando não está.
- Até seis moedas podem ser mantidas lado a lado; um sétimo toque não é aceito. Comparadas, cada uma é desenhada como variação acumulada em vez de valor, para que duas moedas compradas a preços muito diferentes possam ser lidas juntas.
- Os dias aqui são dias corridos, e uma moeda é negociada em todos eles: um ano de manutenção são cerca de 365 dias, não os 243 que uma bolsa daria.
- Quando só a fonte reserva é alcançável, o intervalo que ela consegue preencher é de cerca de um ano. A página diz então onde o intervalo realmente começa, em vez de começar silenciosamente mais tarde do que a data digitada.
""",
    "cs": """## Krypto svíčky

Denní svíčky jedné mince v amerických dolarech z veřejného zdroje. Týdenní a měsíční jsou složeny ze stejných dnů.

- Dvanáct nabízených mincí jsou ty, k nimž oba zdroje mají roky denní historie. Vyhledávací pole tu není: oba zdroje píšou tutéž minci jinak a název napsaný do jednoho nedosáhne ani na jeden.
- **Interval** — den, týden nebo měsíc — mění to, která řada se kreslí, takže jeho změna znovu načítá data. **Styl** a **Průběh** ne; jen překreslují to, co už je tu.
- Mince se obchoduje každý den v roce: rozsah nemá svátky, které by musel přeskočit, ani chybějící dny, a mince nevyplácí dividendu ani se neštěpí — závěr *je* výnos a na těchto třech stránkách se žádná úprava neprovádí.
- Když je dosažitelný jen záložní zdroj, má jeden denní kurz místo čtyř, a svíčky i sloupce se pak kreslí jako čára: tělo se dvěma knoty udělané z jediného závěru je tvar, který mince nikdy neměla. Stránka to říká pod volbou stylu, když je to tento případ.
- Najednou lze kreslit až šest mincí; sedmý stisk se nepřijímá, protože sedmá křivka by vzala barvu, kterou už má šestá. Při porovnání se kreslí jako kumulativní změna, protože mince nemají ceny ve stejném řádu.
- **Tyto tři stránky se objeví jen tehdy, když nějaký zdroj odpoví.** Oba zdroje jsou mimo dosah pevninské Číny, takže počítač tam je v menu prostě nedostane: tři položky nabízející data, která nemohou načíst, by byly tři položky, které selžou.

## Plán krypto DCA

Nakupovat jednu minci v pevném rytmu — řekněme týdně nebo měsíčně — a za kolik je ten plán dnes.

- **Frekvence** a **Částka** říkají jak často a kolik, v amerických dolarech. Plán nakupuje první den každého období, které rozsah pokrývá.
- Kreslí se vložené peníze proti hodnotě pozice, den po dni, s vyznačenými nákupy: pokles, do kterého jste nakupovali, se čte jinak než ten, do kterého jste nenakupovali.
- Porovnat lze až šest plánů. Při porovnání se kreslí jako kumulativní změna místo peněz, aby mince za 60 000 dolarů a mince za půl dolaru šly číst proti sobě.
- Mince zařazená až po začátku rozsahu začíná svým vlastním prvním dnem, a mince bez kurzu v celém rozsahu je uvedena na stavovém řádku místo aby byla nakreslena jako rovná čára.
- Dny jsou tu kalendářní dny. Mince se obchoduje každý z nich: rok týdenních nákupů je asi 52 nákupů, rok měsíčních 12, a ani jedno číslo není přibližné.

## Výnos krypto portfolia

Částka vložená do jedné mince v jednom dni a kolik má dnes hodnotu.

- **Kapitál** je částka v amerických dolarech; rozsah říká den vstupu a den, kdy skončit. Stránka nakupuje za první závěr v rozsahu a drží do posledního.
- Kreslí se hodnota pozice den po dni proti vloženým penězům: čára je nad svým startem, dokud je pozice v plusu, a pod ním, když není.
- Vedle sebe lze držet až šest mincí; sedmý stisk se nepřijímá. Při porovnání se každá kreslí jako kumulativní změna místo hodnoty, aby dvě mince koupené za velmi různé ceny šly číst společně.
- Dny jsou tu kalendářní dny a mince se obchoduje každý z nich: rok držení je asi 365 dnů, ne 243, které by dala burza.
- Když je dosažitelný jen záložní zdroj, rozsah, který dokáže zaplnit, je asi rok. Stránka pak řekne, kde rozsah opravdu začíná, místo aby potichu začínal později než zadané datum.
""",
    "tr": """## Kripto mumlar

Bir coin'in günlük mumları, ABD doları cinsinden, herkese açık bir kaynaktan. Haftalık ve aylık mumlar aynı günlerden toplanır.

- Sunulan on iki coin, her iki kaynağın da yıllarca günlük geçmişe sahip olduğu coin'ler. Arama kutusu yok: iki kaynak aynı coini farklı yazıyor ve birine yazılan isim ikisine de ulaşmıyor.
- **Dönem** — gün, hafta veya ay — hangi serinin çizildiğini değiştirir, bu yüzden değiştirmek yeniden veri getirir. **Stil** ve **Akış** getirmez; sadece burada olanı yeniden çizer.
- Bir coin yılın her günü işlem görür: bir aralığın atlanacak tatili ve eksik günü yoktur; bir coin temettü ödemez ve bölünmez — kapanış *getirinin kendisidir* ve bu üç sayfada hiçbir düzeltme uygulanmaz.
- Yalnızca yedek kaynağa ulaşılabiliyorsa, günde dört fiyat yerine bir fiyat vardır ve bu durumda mumlar ile çubuklar çizgi olarak çizilir: tek bir kapanıştan yapılmış bir gövde ve iki fitil, coin'in hiç almadığı bir biçimdir. Sayfa bunu, o durumda stil kutusunun altında söyler.
- Aynı anda en fazla altı coin çizilebilir; yedinci basış kabul edilmez, çünkü yedinci eğri altıncının sahip olduğu rengi alırdı. Karşılaştırıldıklarında kümülatif değişim olarak çizilirler, çünkü coin'ler aynı fiyat aralığında değildir.
- **Bu üç sayfa yalnızca bir kaynak yanıt verdiğinde görünür.** Her iki kaynak da anakaranın erişiminin dışında, bu yüzden oradaki bir makine menüde onları hiç görmez: getiremeyecekleri veriyi sunan üç girdi, başarısız olan üç girdi olurdu.

## Kripto DCA planı

Bir coin'i sabit bir ritimle almak — diyelim haftalık veya aylık — ve bu planın bugünkü değeri.

- **Sıklık** ve **Tutar**, ABD doları cinsinden ne sıklıkla ve ne kadar alınacağını söyler. Plan, aralığın kapsadığı her dönemin ilk gününde alır.
- Çizilen, konulan para ile pozisyonun değeridir; gün gün, alımlar işaretlenmiş olarak: içine alım yaptığınız bir düşüş, yapmadığınız bir düşüşten farklı okunur.
- En fazla altı plan karşılaştırılabilir. Karşılaştırıldıklarında para olarak değil kümülatif değişim olarak çizilirler, böylece 60.000 dolarlık bir coin ile yarım dolarlık bir coin birbirine karşı okunabilir.
- Aralık başladıktan sonra listelenen bir coin kendi ilk gününde başlar ve aralıkta hiç fiyatı olmayan bir coin düz bir çizgi olarak çizilmek yerine durum satırında adıyla belirtilir.
- Buradaki günler takvim günleridir. Bir coin hepsinde işlem görür: haftalık alımla bir yıl yaklaşık 52 alım, aylık alımla 12 alımdır ve iki sayı da yaklaşık değildir.

## Kripto varlık getirisi

Bir gün bir coin'e konulan bir tutar ve onun bugünkü değeri.

- **Sermaye**, ABD doları cinsinden tutardır; aralık hangi gün girildiğini ve hangi gün durulacağını söyler. Sayfa aralıktaki ilk kapanışta alır ve son kapanışa kadar tutar.
- Çizilen, pozisyonun gün gün değeridir, konulan paranın karşısında: pozisyon kârdaysa çizgi başlangıç noktasının üstünde, değilse altında durur.
- Yan yana en fazla altı coin tutulabilir; yedinci basış kabul edilmez. Karşılaştırıldıklarında her biri değer olarak değil kümülatif değişim olarak çizilir, böylece çok farklı fiyatlardan alınmış iki coin birlikte okunabilir.
- Buradaki günler takvim günleridir ve bir coin hepsinde işlem görür: bir yıl tutmak yaklaşık 365 gündür, bir borsanın vereceği 243 değil.
- Yalnızca yedek kaynağa ulaşılabiliyorsa, doldurabildiği aralık yaklaşık bir yıldır. Sayfa o zaman aralığın gerçekte nerede başladığını söyler, yazılan tarihten sessizce daha geç başlamak yerine.
""",
    "ru": """## Криптосвечи

Дневные свечи одной монеты в долларах США из открытого источника. Недельные и месячные собираются из тех же дней.

- Двенадцать предлагаемых монет — те, по которым у обоих источников есть годы дневной истории. Поля поиска нет: два источника пишут одну монету по-разному, и введённое имя не дойдёт ни до одного.
- **Период** — день, неделя или месяц — меняет то, какая серия рисуется, поэтому его смена запрашивает данные заново. **Стиль** и **Анимация** — нет; они лишь перерисовывают то, что уже здесь.
- Монета торгуется каждый день в году: в диапазоне нет праздников, которые нужно перешагнуть, и нет пропущенных дней, а монета не платит дивиденды и не дробится: закрытие *и есть* доходность, и на этих трёх страницах никакая коррекция не применяется.
- Если доступен только резервный источник, у него одна цена в день вместо четырёх, и тогда свечи и бары рисуются линией: тело с двумя тенями из одного закрытия — это форма, которой монета никогда не имела. Страница говорит об этом под списком стиля, когда это так.
- Одновременно можно нарисовать до шести монет; седьмое нажатие не принимается, потому что седьмая кривая взяла бы цвет, который уже есть у шестой. При сравнении они рисуются как накопленное изменение, потому что цены монет не в одном диапазоне.
- **Эти три страницы появляются только тогда, когда какой-то источник отвечает.** Оба источника вне досягаемости материкового Китая, поэтому машина там просто не получит их в меню: три пункта, предлагающие данные, которые они не могут получить, были бы тремя пунктами, которые не работают.

## Криптоплан DCA

Покупка одной монеты в заданном ритме — скажем, еженедельно или ежемесячно — и сколько этот план стоит сегодня.

- **Частота** и **Сумма** говорят, как часто и сколько, в долларах США. План покупает в первый день каждого периода, который охватывает диапазон.
- Рисуется внесённые деньги против стоимости позиции, день за днём, с отмеченными покупками: падение, в которое вы покупали, читается иначе, чем то, в которое не покупали.
- Сравнить можно до шести планов. При сравнении они рисуются как накопленное изменение, а не как деньги, чтобы монету за 60 000 долларов и монету за полдоллара можно было читать друг против друга.
- Монета, появившаяся после начала диапазона, начинается со своего первого дня, а монета без цены во всём диапазоне называется в строке состояния, а не рисуется плоской линией.
- Дни здесь календарные. Монета торгуется в каждый из них: год еженедельных покупок — это около 52 покупок, год ежемесячных — 12, и ни одна из цифр не приблизительная.

## Доходность криптопортфеля

Сумма, вложенная в одну монету в определённый день, и сколько она стоит сейчас.

- **Капитал** — это сумма в долларах США; диапазон говорит, в какой день она вошла и в какой день остановиться. Страница покупает по первому закрытию в диапазоне и держит до последнего.
- Рисуется стоимость позиции день за днём против внесённых денег: линия выше своей стартовой точки, пока позиция в плюсе, и ниже, когда нет.
- Рядом можно держать до шести монет; седьмое нажатие не принимается. При сравнении каждая рисуется как накопленное изменение, а не как стоимость, чтобы две монеты, купленные по очень разным ценам, можно было читать вместе.
- Дни здесь календарные, и монета торгуется в каждый из них: год владения — это около 365 дней, а не 243, которые дала бы биржа.
- Если доступен только резервный источник, диапазон, который он может заполнить, — около года. Страница тогда говорит, где диапазон действительно начинается, вместо того чтобы молча начаться позже введённой даты.
""",
    "ja": """## 暗号資産のローソク足

ある暗号資産の日足、米ドル建て、公開ソースから。週足と月足は同じ日足から集計します。

- 選べる 12 銘柄は、どちらのソースにも何年分もの日次データがあるものです。検索欄はありません。2 つのソースで同じ銘柄の綴りが違い、入力した名前はどちらにも届かないからです。
- **期間**（日・週・月）は描く系列を変えるので、変更すると再取得します。**描き方**と**進行**は再取得しません。すでに手元にあるデータを描き直すだけです。
- 暗号資産は年中無休で取引されます。区間に飛ばす休日はなく、欠ける日もありません。また配当も分割もないため、終値がそのままリターンであり、この 3 ページではどこにも調整をかけていません。
- 予備のソースにしか届かない場合、1 日あたり 4 本ではなく 1 本の値しかなく、ローソク足とバーは線で描かれます。1 つの終値から作った胴体と 2 本のヒゲは、その銘柄が一度も作っていない形だからです。その場合は描き方の下にその旨が出ます。
- 同時に描けるのは最大 6 銘柄で、7 つ目は受け付けません。7 本目の曲線は 6 本目と同じ色になるためです。複数を比べるときは価格ではなく累積騰落率で描きます。銘柄によって価格の桁が違うからです。
- **この 3 つのページは、どちらかのソースが応答したときだけ表示されます。** どちらのソースも中国本土からは届かないため、その環境ではメニューに現れません。取れないデータを並べる項目は、失敗する項目になるだけだからです。

## 暗号資産つみたて計画

ある暗号資産を一定のリズムで買い続ける（週次、あるいは月次）計画と、その今日の価値。

- **頻度**と**金額**は、米ドルで「どれくらいの頻度で、いくら」かを指定します。計画は区間に含まれる各期の初日に買います。
- 描かれるのは、投入した資金と保有額の価値の日々の推移で、買い付けが印で示されます。買い向かった下落と、買わなかった下落は読み方が違います。
- 計画は最大 6 件まで比較できます。比較時は金額ではなく累積騰落率で描くため、6 万ドルの銘柄と 0.5 ドルの銘柄も並べて読めます。
- 区間の開始より後に上場した銘柄はその銘柄自身の初日から始まり、区間内に価格がまったくない銘柄は平坦な線として描かずに状態行で名前を出します。
- ここでの日数は暦日です。暗号資産は毎日取引されるため、週次なら 1 年で約 52 回、月次なら 12 回の買い付けで、どちらも概算ではありません。

## 暗号資産の保有収益

ある日に暗号資産に投じた金額と、そのいまの価値。

- **元本**は米ドル建ての金額で、区間は投入日と終了日を指定します。ページは区間内の最初の終値で買い、最後の終値まで持ち続けます。
- 描かれるのは保有額の価値の日々の推移と、投入した資金との対比です。含み益なら線は開始点より上に、そうでなければ下にきます。
- 並べて持てるのは最大 6 銘柄で、7 つ目は受け付けません。比較時は価値ではなく累積騰落率で描くため、まったく違う価格で買った 2 銘柄も一緒に読めます。
- ここでの日数は暦日で、暗号資産は毎日取引されます。1 年保有すれば約 365 日であり、株式市場の 243 日ではありません。
- 予備のソースにしか届かない場合、埋められる区間は約 1 年です。そのときページは、入力した日付より後から黙って始めるのではなく、区間が実際にどこから始まるかを伝えます。
""",
    "ko": """## 크립토 캔들

공개 소스에서 가져온 암호화폐의 일봉, 미국 달러 기준. 주봉과 월봉은 같은 일봉에서 모읍니다.

- 고를 수 있는 12개 코인은 두 소스 모두에 수년치 일별 데이터가 있는 종목입니다. 검색창은 없습니다. 두 소스가 같은 코인을 다르게 적고, 입력한 이름은 어느 쪽에도 닿지 않기 때문입니다.
- **주기**(일·주·월)는 그리는 계열을 바꾸므로 바꾸면 다시 가져옵니다. **표시 방식**과 **진행 방식**은 다시 가져오지 않고 이미 있는 데이터를 다시 그릴 뿐입니다.
- 암호화폐는 연중 매일 거래됩니다. 구간에 건너뛸 휴일이 없고 빠진 날도 없습니다. 배당도 없고 액면분할도 없으므로 종가가 곧 수익이며, 이 세 페이지에서는 어디에도 조정을 하지 않습니다.
- 예비 소스에만 닿는 경우 하루에 네 가격이 아니라 하나의 가격만 있고, 그러면 캔들과 바는 선으로 그립니다. 하나의 종가로 만든 몸통과 두 개의 꼬리는 그 코인이 한 번도 만든 적 없는 모양이기 때문입니다. 그때는 표시 방식 아래에 그 사실이 나옵니다.
- 동시에 그릴 수 있는 코인은 최대 6개이고 일곱 번째는 받지 않습니다. 일곱 번째 곡선이 여섯 번째와 같은 색을 쓰게 되기 때문입니다. 여러 개를 비교할 때는 가격이 아니라 누적 변화로 그립니다. 코인마다 가격 단위가 다르기 때문입니다.
- **이 세 페이지는 소스가 응답할 때만 나타납니다.** 두 소스 모두 중국 본토에서는 닿지 않으므로 그 환경에서는 메뉴에 아예 나오지 않습니다. 가져올 수 없는 데이터를 내놓는 항목은 실패하는 항목일 뿐입니다.

## 크립토 적립 계획

암호화폐를 일정한 리듬으로 매수하는(주간 또는 월간) 계획과 그 계획의 오늘 가치.

- **주기**와 **금액**은 미국 달러로 얼마나 자주, 얼마씩인지를 정합니다. 계획은 구간에 포함된 각 기간의 첫날에 매수합니다.
- 그려지는 것은 넣은 돈과 보유분의 가치가 날짜별로 대비된 것이며 매수 시점이 표시됩니다. 매수한 하락과 매수하지 않은 하락은 읽는 법이 다릅니다.
- 계획은 최대 6개까지 비교할 수 있습니다. 비교할 때는 금액이 아니라 누적 변화로 그리므로 6만 달러 코인과 0.5달러 코인도 나란히 읽을 수 있습니다.
- 구간 시작 뒤에 상장된 코인은 그 코인 자신의 첫날부터 시작하고, 구간 안에 가격이 아예 없는 코인은 평평한 선으로 그리지 않고 상태 줄에 이름을 밝힙니다.
- 여기서의 날짜는 달력상 날짜입니다. 암호화폐는 매일 거래되므로 주간이면 1년에 약 52회, 월간이면 12회 매수이며 어느 쪽도 어림수가 아닙니다.

## 크립토 보유 수익

어느 날 암호화폐에 넣은 금액과 그 지금의 가치.

- **자본**은 미국 달러 기준 금액이고, 구간은 들어간 날과 멈출 날을 정합니다. 페이지는 구간의 첫 종가에 매수해 마지막 종가까지 보유합니다.
- 그려지는 것은 보유분의 가치가 날짜별로, 넣은 돈과 대비된 것입니다. 보유분이 이익이면 선이 시작점 위에, 아니면 아래에 놓입니다.
- 나란히 보유할 수 있는 코인은 최대 6개이고 일곱 번째는 받지 않습니다. 비교할 때는 가치가 아니라 누적 변화로 그리므로 아주 다른 가격에 산 두 코인도 함께 읽을 수 있습니다.
- 여기서의 날짜는 달력상 날짜이고 암호화폐는 매일 거래됩니다. 1년 보유는 약 365일이며, 증권시장의 243일이 아닙니다.
- 예비 소스에만 닿는 경우 채울 수 있는 구간은 약 1년입니다. 그때 페이지는 입력한 날짜보다 뒤에서 조용히 시작하는 대신, 구간이 실제로 어디서 시작하는지를 알려줍니다.
""",
    "zh-Hans": """## 加密货币 K 线

某个币种的日 K 线，以美元计价，取自公开数据源。周线与月线由同一批日线聚合而成。

- 可选的十二个币种，是两个源都持有多年日线历史的那些。这里没有搜索框：两个源对同一个币种的写法不同，敲进去的名字哪个源都到不了。
- **周期**（日、周、月）决定画的是哪一条序列，所以改它会重新取数；**画法**与**推进方式**不会，它们只是把已经在手的数据重画一遍。
- 加密货币一年里天天交易：区间里没有要跳过的休市日，也不会缺任何一天；既不分红也不拆股，所以收盘价本身就是收益，这三页上任何地方都不做复权。
- 当只能连上备用源时，一天只有一个价格而不是四个，蜡烛图与柱状图会改以折线绘制——由一个收盘价造出来的实体和两根影线，是这个币种从没走出过的形状。这种情况下样式框下面会写出来。
- 同时最多画六个币种，按第七个不接受，因为第七条曲线会用到第六条已经用掉的颜色。多个一起比时画的是累计涨跌幅而不是价格，因为各币种的价格根本不在同一个量级上。
- **这三个页面只在某个源应答时出现。** 两个源都在中国大陆之外，所以在大陆的机器上它们根本不进菜单——三个取不到数据的入口，就是三个会失败的入口。

## 加密货币定投计划

按固定节奏买入某个币种（比如每周或每月），以及这份计划今天值多少。

- **频率**与**金额**决定多久买一次、每次买多少，单位是美元。计划在区间内每一期的第一天买入。
- 画的是投进去的钱与持仓市值的逐日对照，买入点会标出来：买进去的那次下跌，和没买的那次下跌，读起来不是一回事。
- 最多可以对比六份计划。对比时画的是累计涨跌幅而不是金额，这样 6 万美元的币种和 0.5 美元的币种也能放在一张图里读。
- 晚于区间起点才上市的币种从它自己的第一天开始；整个区间里都没有价格的币种会在状态行报出名字，而不是画成一条平线。
- 这里的天数都是自然日。加密货币天天交易，所以按周买一年大约 52 次、按月买 12 次，两个数字都不是估算的。

## 加密货币持仓收益

某一天把一笔钱投进某个币种，以及它现在值多少。

- **本金**是那笔钱的美元金额，区间给出投进去的那天和截止的那天。页面在区间第一个收盘价买入，一直持有到最后一个收盘价。
- 画的是持仓市值的逐日变化与投进去的钱之间的对照：赚着的时候线在起点之上，亏着的时候在起点之下。
- 最多可以并排持有六个币种，按第七个不接受。对比时每个画的是累计涨跌幅而不是市值，这样买入价相差很远的两个币种也能一起读。
- 这里的天数都是自然日，而且加密货币天天交易：持有一年是约 365 天，不是股市那 243 天。
- 当只能连上备用源时，它能填满的区间大约只有一年。这时页面会说出区间实际从哪天开始，而不是悄悄从比输入日期更晚的地方起画。
""",
    "zh-Hant": """## 加密貨幣 K 線

某個幣種的日 K 線，以美元計價，取自公開數據源。週線與月線由同一批日線聚合而成。

- 可選的十二個幣種，是兩個源都持有多年日線歷史的那些。這裡沒有搜尋框：兩個源對同一個幣種的寫法不同，敲進去的名字哪個源都到不了。
- **週期**（日、週、月）決定畫的是哪一條序列，所以改它會重新取數；**畫法**與**推進方式**不會，它們只是把已經在手的數據重畫一遍。
- 加密貨幣一年裡天天交易：區間裡沒有要跳過的休市日，也不會缺任何一天；既不配息也不拆股，所以收盤價本身就是收益，這三頁上任何地方都不做復權。
- 當只能連上備用源時，一天只有一個價格而不是四個，蠟燭圖與柱狀圖會改以折線繪製——由一個收盤價造出來的實體和兩根影線，是這個幣種從沒走出過的形狀。這種情況下樣式框下面會寫出來。
- 同時最多畫六個幣種，按第七個不接受，因為第七條曲線會用到第六條已經用掉的顏色。多個一起比時畫的是累計漲跌幅而不是價格，因為各幣種的價格根本不在同一個量級上。
- **這三個頁面只在某個源應答時出現。** 兩個源都在中國大陸之外，所以在大陸的機器上它們根本不進選單——三個取不到數據的入口，就是三個會失敗的入口。

## 加密貨幣定投計劃

按固定節奏買入某個幣種（比如每週或每月），以及這份計劃今天值多少。

- **頻率**與**金額**決定多久買一次、每次買多少，單位是美元。計劃在區間內每一期的第一天買入。
- 畫的是投進去的錢與持倉市值的逐日對照，買入點會標出來：買進去的那一刻下跌，和沒買的那次下跌，讀起來不是一回事。
- 最多可以對比六份計劃。對比時畫的是累計漲跌幅而不是金額，這樣 6 萬美元的幣種和 0.5 美元的幣種也能放在一張圖裡讀。
- 晚於區間起點才上市的幣種從它自己的第一天開始；整個區間裡都沒有價格的幣種會在狀態行報出名字，而不是畫成一條平線。
- 這裡的天數都是自然日。加密貨幣天天交易，所以按週買一年大約 52 次、按月買 12 次，兩個數字都不是估算的。

## 加密貨幣持倉收益

某一天把一筆錢投進某個幣種，以及它現在值多少。

- **本金**是那筆錢的美元金額，區間給出投進去的那天和截止的那天。頁面在區間第一個收盤價買入，一直持有到最後一個收盤價。
- 畫的是持倉市值的逐日變化與投進去的錢之間的對照：賺著的時候線在起點之上，虧著的時候在起點之下。
- 最多可以並排持有六個幣種，按第七個不接受。對比時每個畫的是累計漲跌幅而不是市值，這樣買入價相差很遠的兩個幣種也能一起讀。
- 這裡的天數都是自然日，而且加密貨幣天天交易：持有一年是約 365 天，不是股市那 243 天。
- 當只能連上備用源時，它能填滿的區間大約只有一年。這時頁面會說出區間實際從哪天開始，而不是悄悄從比輸入日期更晚的地方起畫。
""",
}


def chapter_titles(tag):
    """这一块三章的标题行，用来认旧块。"""
    return {line.strip() for line in SECTIONS[tag].split("\n") if line.startswith("## ")}


def main() -> int:
    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        raw = path.read_bytes()

        # 有没有 BOM 照抄：这 14 份文件现在是**不带** BOM 的（2026-10-11 实测，HEAD 上
        # 逐份看过），而 `port-candle-help.py` 那句「它们现在带 BOM」已经过时了。照抄
        # 而不是一律写，否则这一轮的 diff 里会多出一行「标题行被改过」 —— 看起来像整份
        # 文件被重写，实际只是行首多了一个零宽字符。
        had_bom = raw.startswith(b"\xef\xbb\xbf")

        text = raw.decode("utf-8-sig").lstrip("\ufeff")

        crlf = "\r\n" in text
        joiner = "\r\n" if crlf else "\n"
        lines = text.split(joiner)

        # 整块摘掉：一块里有三个 `##`，只删到下一个标题会留下另外两章，第二次运行就成了两份。
        titles = chapter_titles(tag)

        kept = []
        skipping = False

        for line in lines:
            if line.startswith("## "):
                skipping = line.strip() in titles

            if not skipping:
                kept.append(line)

        headings = [i for i, line in enumerate(kept) if line.startswith("## ")]

        if len(headings) <= POSITION:
            print(f"{tag}: only {len(headings)} headings, expected more than {POSITION}")
            return 1

        section = SECTIONS[tag].rstrip("\n").split("\n")

        # 位置由序号定，不由标题定：14 份文件里唯一相同的是顺序。
        at = headings[POSITION]

        lines = kept[:at] + section + [""] + kept[at:]

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + joiner.join(lines).encode("utf-8"))

        print(f"{tag:9} inserted before {kept[at]!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
