# -*- coding: utf-8 -*-
r"""把「涨跌日历 / 市值历程 / 市值榜」三章插进 14 份 help-*.md。

**位置按序号找，不按标题找**（`POSITION = 23`，也就是「Video」那一章之前）：14 份文件里
标题是各语言自己写的，唯一相同的是顺序。三章作为一整块插入，所以同结构同顺序这条约束
一次就满足了。上一轮 `port-crypto-help.py` 用 20，那三章占住了 20/21/22，所以这一块是 23。

**整块替换才算幂等**。一块里有三个 `##`，所以删旧块不能只删到下一个标题为止 —— 那会留下
另外两章，第二次运行就变成两份。这里按「三章的标题集合」逐行识别。

文件是 **UTF-8 不带 BOM**（2026-10-11 实测 HEAD 上逐份看过）；BOM 与行尾照抄原文。

**这一块要说清的事**（14 份都要说，措辞各自来）：

1. 日历**没有空格**：不是漏掉了休息日，是这个市场不休息；
2. 市值**不是外推**：不是「今天的流通量 × 历史价格」（那样两条线恒平行，这一页就没意义了），
   而是 CoinMetrics 的逐日真值；
3. 市值榜是**实时前 15 名**，不是写死的清单，榜上保留稳定币；
4. **市值历程可以同时画几个币**（10-14 加）：整幅画面让给市值、最多六个、
   刻度两种读法（绝对值／归一到 100）、日期轴取并集；
5. 源端不携带的币是**略过**而不是画成贴地的零线，状态行说出略过了哪几个。

用法：python tools\port-crypto-caps-help.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

TAGS = [
    "en-US", "de", "es", "fr", "it", "pl", "pt-BR",
    "cs", "tr", "ru", "ja", "ko", "zh-Hans", "zh-Hant",
]

# 插在这里：现有最后一章「加密货币持仓收益」之后、「Video」之前。
POSITION = 23

SECTIONS = {
    "en-US": """## Crypto Gain Calendar

One cell per day, coloured by that day's change.

- **A full grid is not missing data.** A stock calendar is mostly holes — weekends, holidays, suspensions — and reads the way a market looks. A coin trades every day of the year, so every square is filled: the picture is denser rather than longer, and what looks like a missing holiday is a market that never closes.
- **Range** is three, six or twelve months, or a span of your own. A custom span is clipped to what the source carries, and the page says where the range really starts rather than beginning later than the date that was typed.
- The first cell is always 0%: there is no prior close inside the range, and reaching outside it for one would make the first cell depend on a day the calendar does not show.
- The colour is the change, not the amount traded. A coin's volume is a count of coins, and nothing on this grid is scaled against it — what the calendar is about is which way the day went and by how much.
- Days here are calendar days. A year of this page is about 365 cells, not the 243 a stock market would give you, and neither figure is approximated.

## Crypto Market Cap History

One coin's circulating market cap over time, with the price over the same days beneath it. Or several coins at once — one line each, named at its end.

- **Where the two lines pull apart, you are looking at issuance and burns.** The price is what one coin costs; the cap is that price times however many coins exist. A cap line that rises while the price line falls is supply growing, not a figure that went wrong.
- **This is measured, not extrapolated.** Multiplying today's supply by an old price is the cheap way to draw this page, and it produces two lines that are the same line — the cap would say nothing the price does not already say. What is drawn here comes from CoinMetrics' public API, which carries a daily circulating cap: Bitcoin reaches back to 2010, other coins as far as the source holds them.
- Market cap here means *circulating* cap — the coins already issued and in circulation, not a fully diluted count that assumes every coin that will ever exist.
- The estimate series every coin carries starts in June 2019. A coin with no exact series begins there, and the page says where the range really starts instead of quietly beginning later.
- **Compare several coins and the whole frame goes to market cap.** Their prices do not share a price axis honestly — put bitcoin beside a coin trading at a fraction of a cent and one of them is a flat line along the bottom — so the lower price panel steps aside and every curve is named at its own leading end. Six is the ceiling: a seventh press is not accepted, because a seventh curve would take a colour the sixth already has.
- The value axis has two readings. Absolute answers which coin is worth more; rebased to 100 at each line's own first day answers whose cap grew faster, and is the only readable one once one is several times the other. Either way the date axis is the union of their days: a coin that only starts in 2019 begins there and is absent before that.
- **A coin the value source does not carry is left out, not drawn flat.** Much of what a search can add is outside CoinMetrics' catalogue, and a flat line along the bottom of a value chart reads as a coin that went to nothing rather than one with no figure to draw. When some are left out the status line names them; with a single coin picked and it coming back empty, the page says the range holds no usable history instead of drawing an empty frame.
- **Range** is twelve, twenty-four, sixty or one hundred and twenty months, or a span of your own. A coin's history may be shorter than the range you asked for — that is the source's floor, not a fetch that failed.

## Crypto Market Cap Race

The fifteen coins with the largest market cap today, and how that order moved day by day.

- **The field is asked for, not written down.** At fetch time the page takes the current top fifteen by market value from CoinGecko's live ranking, so a coin that grew into this size last year is on the board without anybody editing a list. That is also why there is no coin picker here: the field itself is the answer, and what the page asks is which span.
- The day-by-day values come from CoinMetrics, one request for the whole board. They are that source's estimate series, which starts in June 2019 for every coin alike, so the range is clipped there rather than refused — a board on which two coins had eight years of history and thirteen had none would read as coins that appeared out of nowhere.
- **Stablecoins stay on it.** Measured on 2026-10-11, the top thirty carried six of them, and tether was the third largest thing on this market. A board that hid them would be ranking something other than size. What they do to the picture is honest: their line is flat, because a dollar is worth a dollar, so the board shows at a glance which of the largest things here actually move.
- A coin the value source does not carry is dropped rather than drawn flat at zero — a flat line at the bottom of a value race reads as a coin that went to nothing. The board can therefore hold fewer than fifteen, and the status line says how many it got.
- **Range** is twelve, twenty-four or sixty months, or a span of your own, clipped to the estimate series the same way.
""",
    "de": """## Krypto-Gewinnkalender

Ein Feld pro Tag, gefärbt nach der Veränderung dieses Tages.

- **Ein volles Raster ist keine fehlenden Daten.** Ein Aktienkalender besteht meist aus Lücken — Wochenenden, Feiertage, Aussetzungen — und liest sich so, wie ein Markt aussieht. Eine Münze wird an jedem Tag des Jahres gehandelt, also ist jedes Feld gefüllt: Das Bild ist dichter statt länger, und was wie ein fehlender Feiertag aussieht, ist ein Markt, der nie schließt.
- **Zeitraum** sind drei, sechs oder zwölf Monate oder eine eigene Spanne. Eine eigene Spanne wird auf das zugeschnitten, was die Quelle hat, und die Seite sagt, wo der Zeitraum wirklich beginnt, statt später anzufangen als das eingegebene Datum.
- Das erste Feld ist immer 0 %: Es gibt keinen vorherigen Schlusskurs innerhalb der Spanne, und einen außerhalb zu holen würde das erste Feld von einem Tag abhängig machen, den der Kalender nicht zeigt.
- Die Farbe ist die Veränderung, nicht der gehandelte Betrag. Das Volumen einer Münze ist eine Stückzahl, und nichts in diesem Raster wird daran skaliert — worum es dem Kalender geht, ist wohin der Tag ging und wie weit.
- Tage sind hier Kalendertage. Ein Jahr auf dieser Seite sind etwa 365 Felder, nicht die 243, die eine Börse gäbe, und keine der beiden Zahlen ist geschätzt.

## Krypto-Marktkapitalisierung im Verlauf

Die zirkulierende Marktkapitalisierung einer Münze im Verlauf, darunter der Kurs über dieselben Tage. Oder mehrere Münzen auf einmal — je eine Linie, am eigenen Ende beschriftet.

- **Wo die beiden Linien auseinanderlaufen, sieht man Ausgabe und Verbrennung.** Der Kurs ist, was eine Münze kostet; die Kapitalisierung ist dieser Kurs mal der Anzahl existierender Münzen. Eine Kapitalisierungslinie, die steigt, während die Kurslinie fällt, ist wachsendes Angebot, keine falsche Zahl.
- **Das ist gemessen, nicht hochgerechnet.** Den heutigen Bestand mit einem alten Kurs zu multiplizieren ist der billige Weg, diese Seite zu zeichnen, und er liefert zwei Linien, die dieselbe Linie sind — die Kapitalisierung sagte dann nichts, was der Kurs nicht schon sagt. Gezeichnet wird hier, was aus der öffentlichen CoinMetrics-Schnittstelle kommt, die eine tägliche zirkulierende Kapitalisierung führt: Bitcoin reicht bis 2010 zurück, andere Münzen so weit, wie die Quelle sie hält.
- Marktkapitalisierung bedeutet hier die *zirkulierende* — die bereits ausgegebenen und im Umlauf befindlichen Münzen, nicht eine voll verwässerte Zahl, die jede jemals existierende Münze annimmt.
- Die Schätzreihe, die jede Münze hat, beginnt im Juni 2019. Eine Münze ohne exakte Reihe beginnt dort, und die Seite sagt, wo der Zeitraum wirklich anfängt, statt still später zu beginnen.
- **Mehrere Münzen auf einmal, und der ganze Rahmen gehört der Marktkapitalisierung.** Ihre Kurse teilen keine ehrliche Kursachse — Bitcoin neben einer Münze, die einen Bruchteil eines Cents kostet, und eine von beiden ist eine flache Linie am Boden —, darum tritt das untere Kursfeld zurück und jede Kurve wird am eigenen Ende beschriftet. Sechs ist die Obergrenze: ein siebter Druck wird nicht angenommen, denn eine siebte Kurve nähme eine Farbe, die die sechste schon hat.
- Die Wertachse hat zwei Lesarten. Absolut beantwortet, welche Münze mehr wert ist; auf 100 umbasiert ab dem je eigenen ersten Tag, wessen Kapitalisierung schneller wuchs — und das ist die einzige lesbare, sobald eine ein Vielfaches der anderen ist. In beiden Fällen ist die Zeitachse die Vereinigung ihrer Tage: eine Münze, die erst 2019 beginnt, beginnt dort und fehlt davor.
- **Eine Münze, die die Wertquelle nicht führt, wird weggelassen statt flach gezeichnet.** Vieles, was eine Suche hinzufügen kann, liegt außerhalb des Katalogs von CoinMetrics, und eine flache Linie am unteren Rand eines Wertdiagramms liest sich wie eine Münze, die auf nichts hinauslief, nicht wie eine ohne Zahl. Wurden welche weggelassen, nennt die Statuszeile sie; ist nur eine gewählt und kommt leer zurück, sagt die Seite, dass der Zeitraum keine brauchbare Historie enthält, statt einen leeren Rahmen zu zeichnen.
- **Zeitraum** sind zwölf, vierundzwanzig, sechzig oder hundertzwanzig Monate oder eine eigene Spanne. Die Historie einer Münze kann kürzer sein als die verlangte Spanne — das ist die Untergrenze der Quelle, kein fehlgeschlagener Abruf.

## Rennen der Krypto-Marktkapitalisierung

Die fünfzehn Münzen mit der größten Marktkapitalisierung heute und wie sich diese Ordnung Tag für Tag bewegte.

- **Das Teilnehmerfeld wird gefragt, nicht aufgeschrieben.** Beim Abruf nimmt die Seite die aktuellen fünfzehn größten nach Marktwert aus der Live-Rangliste von CoinGecko; eine Münze, die letztes Jahr in diese Größe gewachsen ist, steht also auf dem Tableau, ohne dass jemand eine Liste pflegt. Deshalb gibt es hier auch keine Münzauswahl: Das Feld selbst ist die Antwort, und gefragt wird nach der Spanne.
- Die Tageswerte kommen von CoinMetrics, eine Anfrage für das ganze Tableau. Es ist die Schätzreihe dieser Quelle, die für jede Münze gleich im Juni 2019 beginnt; die Spanne wird deshalb dort beschnitten statt abgelehnt — ein Tableau, auf dem zwei Münzen acht Jahre Historie hätten und dreizehn keine, läse sich wie Münzen, die aus dem Nichts auftauchten.
- **Stablecoins bleiben darauf.** Gemessen am 2026-10-11 trugen die oberen Dreißig sechs von ihnen, und Tether war das drittgrößte Ding auf diesem Markt. Ein Tableau, das sie versteckte, würde etwas anderes als Größe rangieren. Was sie mit dem Bild machen, ist ehrlich: Ihre Linie ist flach, weil ein Dollar einen Dollar wert ist — das Tableau zeigt also auf einen Blick, welche der größten Dinge hier sich wirklich bewegen.
- Eine Münze, die die Wertquelle nicht führt, wird weggelassen statt flach bei null gezeichnet: Eine flache Linie am unteren Rand eines Wertrennens liest sich wie eine Münze, die auf nichts hinauslief. Das Tableau kann also weniger als fünfzehn halten, und die Statuszeile sagt, wie viele es wurden.
- **Zeitraum** sind zwölf, vierundzwanzig oder sechzig Monate oder eine eigene Spanne, auf dieselbe Weise an die Schätzreihe beschnitten.
""",
    "es": """## Calendario de ganancias cripto

Una celda por día, coloreada según la variación de ese día.

- **Una cuadrícula llena no son datos que falten.** Un calendario de acciones está lleno de huecos — fines de semana, festivos, suspensiones — y se lee como se ve un mercado. Una moneda cotiza todos los días del año, así que todas las casillas están rellenas: la imagen es más densa, no más larga, y lo que parece un festivo omitido es un mercado que nunca cierra.
- **Rango** son tres, seis o doce meses, o un tramo propio. Un tramo propio se recorta a lo que la fuente tiene, y la página dice dónde empieza realmente el rango en lugar de empezar más tarde que la fecha escrita.
- La primera celda siempre es 0 %: no hay un cierre previo dentro del rango, y buscarlo fuera haría que la primera casilla dependiera de un día que el calendario no muestra.
- El color es la variación, no el importe negociado. El volumen de una moneda es una cantidad de monedas, y nada en esta cuadrícula se escala con él — de lo que trata el calendario es de hacia dónde fue el día y cuánto.
- Los días aquí son días naturales. Un año en esta página son unas 365 celdas, no los 243 que daría una bolsa, y ninguna de las dos cifras es aproximada.

## Historial de capitalización cripto

La capitalización circulante de una moneda a lo largo del tiempo, con el precio de los mismos días debajo. O varias monedas a la vez — una línea cada una, rotulada en su extremo.

- **Donde las dos líneas se separan, lo que se ve es emisión y quema.** El precio es lo que cuesta una moneda; la capitalización es ese precio por la cantidad de monedas existentes. Una línea de capitalización que sube mientras la del precio baja es oferta que crece, no una cifra equivocada.
- **Esto se mide, no se extrapola.** Multiplicar el suministro de hoy por un precio antiguo es la forma barata de dibujar esta página, y produce dos líneas que son la misma línea: la capitalización no diría nada que el precio no diga ya. Lo que se dibuja aquí viene de la API pública de CoinMetrics, que lleva una capitalización circulante diaria: Bitcoin llega hasta 2010, las demás monedas hasta donde la fuente las tenga.
- Aquí capitalización significa la *circulante* — las monedas ya emitidas y en circulación, no un cálculo totalmente diluido que supone todas las monedas que existirán.
- La serie estimada que tiene cada moneda empieza en junio de 2019. Una moneda sin serie exacta empieza ahí, y la página dice dónde empieza realmente el rango en vez de empezar silenciosamente más tarde.
- **Varias monedas a la vez, y todo el marco va a la capitalización.** Sus precios no comparten un eje de precios honesto — ponga bitcoin al lado de una moneda que cotiza a una fracción de céntimo y una de las dos es una línea plana en el fondo —, así que el panel de precios inferior cede su sitio y cada curva se rotula en su propio extremo. Seis es el techo: una séptima pulsación no se acepta, porque una séptima curva tomaría un color que la sexta ya tiene.
- El eje de valor tiene dos lecturas. El absoluto responde qué moneda vale más; el rebasado a 100 en el primer día de cada una, cuál creció más rápido, y es el único legible cuando una es varias veces la otra. En ambos casos el eje de fechas es la unión de sus días: una moneda que solo empieza en 2019 comienza ahí y falta antes.
- **Una moneda que la fuente de valores no tiene se omite, no se dibuja plana.** Buena parte de lo que una búsqueda puede añadir queda fuera del catálogo de CoinMetrics, y una línea plana en el fondo de un gráfico de valor se lee como una moneda que se fue a nada, no como una sin cifra que dibujar. Cuando se omiten algunas, la línea de estado las nombra; si solo hay una marcada y vuelve vacía, la página dice que el tramo no tiene historia utilizable en lugar de dibujar un marco vacío.
- **Rango** son doce, veinticuatro, sesenta o ciento veinte meses, o un tramo propio. La historia de una moneda puede ser más corta que el rango pedido — eso es el suelo de la fuente, no una consulta que falló.

## Carrera de capitalización cripto

Las quince monedas con mayor capitalización hoy y cómo se movió ese orden día a día.

- **El grupo se pregunta, no se escribe.** Al obtener los datos, la página toma las quince mayores por valor de mercado de la clasificación en vivo de CoinGecko; una moneda que creció hasta ese tamaño el año pasado está en el tablero sin que nadie edite una lista. Por eso tampoco hay selector de moneda aquí: el grupo es la respuesta, y lo que se pregunta es el tramo.
- Los valores diarios vienen de CoinMetrics, una sola consulta para todo el tablero. Son la serie estimada de esa fuente, que empieza en junio de 2019 igual para todas las monedas, así que el rango se recorta ahí en vez de rechazarse: un tablero donde dos monedas tuvieran ocho años de historia y trece ninguna se leería como monedas que aparecieron de la nada.
- **Las monedas estables se quedan.** Medido el 2026-10-11, las treinta primeras llevaban seis de ellas, y tether era la tercera cosa más grande de este mercado. Un tablero que las ocultara estaría ordenando otra cosa que el tamaño. Lo que hacen con la imagen es honesto: su línea es plana, porque un dólar vale un dólar, así que el tablero muestra de un vistazo cuáles de las cosas más grandes aquí se mueven de verdad.
- Una moneda que la fuente de valores no tiene se descarta en lugar de dibujarse plana en cero: una línea plana en el fondo de una carrera de valor se lee como una moneda que acabó en nada. El tablero puede tener por tanto menos de quince, y la línea de estado dice cuántas llegaron.
- **Rango** son doce, veinticuatro o sesenta meses, o un tramo propio, recortado a la serie estimada del mismo modo.
""",
    "fr": """## Calendrier des hausses et baisses crypto

Une case par jour, colorée selon la variation de ce jour.

- **Une grille pleine n'est pas une donnée manquante.** Un calendrier d'actions est surtout fait de trous — week-ends, jours fériés, suspensions — et se lit comme un marché se voit. Une cryptomonnaie se négocie tous les jours de l'année, donc chaque case est remplie : l'image est plus dense, non plus longue, et ce qui ressemble à un jour férié manquant est un marché qui ne ferme jamais.
- **Intervalle** : trois, six ou douze mois, ou une période de votre choix. Une période libre est ramenée à ce que la source possède, et la page dit où l'intervalle commence réellement plutôt que de commencer plus tard que la date saisie.
- La première case est toujours à 0 % : il n'y a pas de clôture précédente dans l'intervalle, et aller la chercher au-dehors ferait dépendre la première case d'un jour que le calendrier ne montre pas.
- La couleur est la variation, pas le montant échangé. Le volume d'une cryptomonnaie est un nombre de jetons, et rien dans cette grille n'est mis à l'échelle avec lui — ce qui intéresse le calendrier, c'est de quel côté la journée est allée et de combien.
- Les jours ici sont des jours civils. Une année sur cette page représente environ 365 cases, et non les 243 que donnerait une bourse, et aucun des deux chiffres n'est approximatif.

## Historique de capitalisation crypto

La capitalisation circulante d'une cryptomonnaie au fil du temps, avec le cours des mêmes jours en dessous. Ou plusieurs cryptomonnaies à la fois — une courbe chacune, nommée à son extrémité.

- **Là où les deux lignes s'écartent, on voit l'émission et la destruction.** Le cours est ce que coûte un jeton ; la capitalisation est ce cours multiplié par le nombre de jetons existants. Une ligne de capitalisation qui monte pendant que celle du cours descend, c'est l'offre qui grandit, pas un chiffre erroné.
- **C'est mesuré, pas extrapolé.** Multiplier l'offre actuelle par un ancien cours est la manière bon marché de tracer cette page, et cela produit deux lignes qui sont la même ligne : la capitalisation ne dirait rien que le cours ne dise déjà. Ce qui est tracé ici vient de l'API publique CoinMetrics, qui porte une capitalisation circulante quotidienne : Bitcoin remonte à 2010, les autres cryptomonnaies aussi loin que la source les garde.
- Ici, capitalisation signifie la capitalisation *circulante* — les jetons déjà émis et en circulation, et non une valorisation entièrement diluée qui suppose tous les jetons qui existeront.
- La série estimée que porte chaque cryptomonnaie commence en juin 2019. Une cryptomonnaie sans série exacte commence là, et la page dit où l'intervalle commence réellement au lieu de commencer discrètement plus tard.
- **Plusieurs cryptomonnaies à la fois, et tout le cadre va à la capitalisation.** Leurs cours ne partagent pas d'axe de prix honnête — mettez bitcoin à côté d'une cryptomonnaie qui vaut une fraction de centime et l'une des deux n'est qu'une ligne plate au ras du bas —, donc le panneau des cours s'efface et chaque courbe est nommée à sa propre extrémité. Six est le plafond : une septième pression n'est pas acceptée, car une septième courbe prendrait une couleur que la sixième a déjà.
- L'axe des valeurs a deux lectures. L'absolu répond à la question de laquelle vaut le plus ; le rebasement à 100 au premier jour de chacune, à celle dont la capitalisation a le plus progressé, et c'est la seule lisible dès que l'une vaut plusieurs fois l'autre. Dans les deux cas l'axe des dates est l'union de leurs jours : une cryptomonnaie qui ne commence qu'en 2019 y commence et manque avant.
- **Une cryptomonnaie absente de la source de valeurs est omise, pas tracée à plat.** Une bonne part de ce qu'une recherche peut ajouter est hors du catalogue de CoinMetrics, et une ligne plate au bas d'un graphique de valeur se lit comme une cryptomonnaie réduite à rien, non comme une qui n'a aucune donnée. Quand il y en a, la ligne d'état les nomme ; s'il n'y en a qu'une de cochée et qu'elle revient vide, la page dit que l'intervalle ne contient pas d'historique exploitable au lieu de tracer un cadre vide.
- **Intervalle** : douze, vingt-quatre, soixante ou cent vingt mois, ou une période de votre choix. L'historique d'une cryptomonnaie peut être plus court que l'intervalle demandé — c'est le plancher de la source, pas une récupération qui a échoué.

## Course des capitalisations crypto

Les quinze cryptomonnaies à la plus forte capitalisation aujourd'hui, et l'évolution de cet ordre jour après jour.

- **Le plateau est demandé, pas écrit.** Au moment de la récupération, la page prend les quinze plus fortes par valeur de marché dans le classement en direct de CoinGecko ; une cryptomonnaie devenue assez grosse l'année dernière figure donc au tableau sans que personne n'édite une liste. C'est aussi pourquoi il n'y a pas de sélecteur de cryptomonnaie ici : le plateau est la réponse, et ce qui est demandé, c'est la période.
- Les valeurs quotidiennes viennent de CoinMetrics, une seule requête pour tout le tableau. C'est la série estimée de cette source, qui commence en juin 2019 de la même façon pour toutes : l'intervalle y est donc ramené plutôt que refusé — un tableau où deux cryptomonnaies auraient huit ans d'historique et treize aucun se lirait comme des cryptomonnaies apparues de nulle part.
- **Les stablecoins y restent.** Mesuré le 2026-10-11, les trente premières en comptaient six, et tether était la troisième plus grosse chose de ce marché. Un tableau qui les cacherait classerait autre chose que la taille. Ce qu'elles font à l'image est honnête : leur ligne est plate, parce qu'un dollar vaut un dollar, si bien que le tableau montre d'un coup d'œil lesquelles des plus grosses choses ici bougent réellement.
- Une cryptomonnaie que la source de valeurs ne porte pas est retirée plutôt que tracée à plat sur zéro : une ligne plate en bas d'une course de valeurs se lit comme une cryptomonnaie réduite à rien. Le tableau peut donc compter moins de quinze, et la ligne d'état dit combien il en a eu.
- **Intervalle** : douze, vingt-quatre ou soixante mois, ou une période de votre choix, ramenée à la série estimée de la même manière.
""",
    "it": """## Calendario dei movimenti crypto

Una cella per giorno, colorata in base alla variazione di quel giorno.

- **Una griglia piena non è un dato mancante.** Un calendario azionario è fatto soprattutto di buchi — fine settimana, festività, sospensioni — e si legge come appare un mercato. Una moneta viene scambiata ogni giorno dell'anno, quindi ogni casella è riempita: l'immagine è più densa, non più lunga, e ciò che sembra una festività mancante è un mercato che non chiude mai.
- **Intervallo**: tre, sei o dodici mesi, oppure un periodo a scelta. Un periodo libero viene ridotto a ciò che la fonte possiede, e la pagina dice dove l'intervallo comincia davvero invece di iniziare più tardi della data inserita.
- La prima cella è sempre 0 %: non c'è una chiusura precedente dentro l'intervallo, e andarla a prendere fuori farebbe dipendere la prima casella da un giorno che il calendario non mostra.
- Il colore è la variazione, non l'importo scambiato. Il volume di una moneta è un conteggio di monete, e nulla in questa griglia vi è scalato — ciò di cui parla il calendario è da che parte è andata la giornata e di quanto.
- I giorni qui sono giorni di calendario. Un anno su questa pagina è circa 365 caselle, non i 243 che darebbe una borsa, e nessuna delle due cifre è approssimata.

## Storia della capitalizzazione crypto

La capitalizzazione circolante di una moneta nel tempo, con il prezzo degli stessi giorni sotto. Oppure più monete insieme — una linea ciascuna, nominata alla sua estremità.

- **Dove le due linee si separano, si vedono emissione e distruzione.** Il prezzo è quanto costa una moneta; la capitalizzazione è quel prezzo per il numero di monete esistenti. Una linea della capitalizzazione che sale mentre quella del prezzo scende è offerta che cresce, non un numero sbagliato.
- **È misurato, non estrapolato.** Moltiplicare l'offerta di oggi per un prezzo vecchio è il modo economico di disegnare questa pagina, e produce due linee che sono la stessa linea: la capitalizzazione non direbbe nulla che il prezzo non dica già. Ciò che si disegna qui viene dall'API pubblica CoinMetrics, che porta una capitalizzazione circolante giornaliera: Bitcoin arriva al 2010, le altre monete fino a dove la fonte le conserva.
- Qui capitalizzazione significa quella *circolante* — le monete già emesse e in circolazione, non un conteggio completamente diluito che presuppone tutte le monete che esisteranno.
- La serie stimata che ogni moneta porta inizia a giugno 2019. Una moneta senza serie esatta inizia lì, e la pagina dice dove l'intervallo comincia davvero invece di iniziare silenziosamente più tardi.
- **Più monete insieme, e tutto il riquadro va alla capitalizzazione.** I loro prezzi non condividono un asse onesto — metta bitcoin accanto a una moneta che vale una frazione di centesimo e una delle due è una linea piatta sul fondo —, quindi il pannello dei prezzi si fa da parte e ogni curva è nominata alla propria estremità. Sei è il tetto: un settimo tocco non viene accettato, perché una settima curva prenderebbe un colore che la sesta ha già.
- L'asse del valore ha due letture. L'assoluto dice quale moneta vale di più; il ribasamento a 100 sul primo giorno di ciascuna dice quale capitalizzazione è cresciuta più in fretta, ed è l'unico leggibile quando una vale più volte l'altra. In entrambi i casi l'asse delle date è l'unione dei loro giorni: una moneta che inizia solo nel 2019 comincia lì e prima manca.
- **Una moneta che la fonte dei valori non porta viene esclusa, non disegnata piatta.** Buona parte di ciò che una ricerca può aggiungere è fuori dal catalogo di CoinMetrics, e una linea piatta in fondo a un grafico di valore si legge come una moneta finita a niente, non come una senza cifre da disegnare. Quando ce ne sono, la riga di stato le nomina; se ne è selezionata una sola e torna vuota, la pagina dice che l'intervallo non contiene storia utilizzabile invece di disegnare un riquadro vuoto.
- **Intervallo**: dodici, ventiquattro, sessanta o centoventi mesi, oppure un periodo a scelta. La storia di una moneta può essere più breve dell'intervallo richiesto — è il limite della fonte, non un recupero fallito.

## Corsa della capitalizzazione crypto

Le quindici monete con la capitalizzazione maggiore oggi e come quest'ordine si è mosso giorno per giorno.

- **Il campo è chiesto, non scritto.** Al momento del recupero la pagina prende le quindici maggiori per valore di mercato dalla classifica in tempo reale di CoinGecko; una moneta diventata abbastanza grande l'anno scorso sta quindi in classifica senza che nessuno modifichi un elenco. Per questo qui non c'è nemmeno un selettore di moneta: il campo è la risposta, e ciò che si chiede è il periodo.
- I valori giornalieri vengono da CoinMetrics, una sola richiesta per tutta la classifica. Sono la serie stimata di quella fonte, che inizia a giugno 2019 allo stesso modo per tutte: l'intervallo vi è quindi ridotto anziché rifiutato — una classifica in cui due monete avessero otto anni di storia e tredici nessuna si leggerebbe come monete apparse dal nulla.
- **Le stablecoin restano.** Misurato il 2026-10-11, le prime trenta ne contavano sei, e tether era la terza cosa più grande di questo mercato. Una classifica che le nascondesse starebbe ordinando altro che la dimensione. Ciò che fanno all'immagine è onesto: la loro linea è piatta, perché un dollaro vale un dollaro, così la classifica mostra a colpo d'occhio quali tra le cose più grandi qui si muovono davvero.
- Una moneta che la fonte dei valori non porta viene esclusa invece di essere disegnata piatta a zero: una linea piatta in fondo a una corsa di valori si legge come una moneta finita a niente. La classifica può quindi contenere meno di quindici, e la riga di stato dice quante ne sono arrivate.
- **Intervallo**: dodici, ventiquattro o sessanta mesi, oppure un periodo a scelta, ridotto alla serie stimata allo stesso modo.
""",
    "pl": """## Kalendarz zmian krypto

Jedno pole na dzień, pokolorowane według zmiany tego dnia.

- **Pełna siatka to nie brakujące dane.** Kalendarz akcji to w większości luki — weekendy, święta, zawieszenia — i czyta się go tak, jak wygląda rynek. Moneta jest notowana każdego dnia roku, więc każde pole jest wypełnione: obraz jest gęstszy, nie dłuższy, a to, co wygląda na pominięte święto, jest rynkiem, który nigdy się nie zamyka.
- **Zakres** to trzy, sześć lub dwanaście miesięcy albo własny przedział. Własny przedział jest przycinany do tego, co ma źródło, a strona mówi, gdzie zakres naprawdę się zaczyna, zamiast zacząć później niż wpisana data.
- Pierwsze pole to zawsze 0 %: w zakresie nie ma wcześniejszego zamknięcia, a sięganie po nie spoza zakresu uzależniałoby pierwsze pola od dnia, którego kalendarz nie pokazuje.
- Kolor to zmiana, nie obrót. Wolumen monety to liczba monet i nic w tej siatce nie jest według niego skalowane — kalendarz mówi o tym, w którą stronę poszedł dzień i jak daleko.
- Dni to tu dni kalendarzowe. Rok na tej stronie to około 365 pól, nie 243, które dałaby giełda, i żadna z tych liczb nie jest przybliżona.

## Historia kapitalizacji krypto

Krążąca kapitalizacja jednej monety w czasie, a pod nią kurs w tych samych dniach. Albo kilka monet naraz — każda własna linia, podpisana na końcu.

- **Tam, gdzie obie linie się rozchodzą, widać emisję i spalanie.** Kurs to cena jednej monety; kapitalizacja to ten kurs razy liczba istniejących monet. Linia kapitalizacji rosnąca, gdy linia kursu spada, to rosnąca podaż, nie zła liczba.
- **To jest mierzone, nie ekstrapolowane.** Pomnożenie dzisiejszej podaży przez stary kurs to tani sposób na narysowanie tej strony i daje dwie linie, które są jedną linią: kapitalizacja nie powiedziałaby niczego, czego kurs już nie mówi. To, co jest tu rysowane, pochodzi z publicznego API CoinMetrics, które prowadzi dzienną kapitalizację krążącą: Bitcoin sięga 2010 roku, pozostałe monety tak daleko, jak źródło je przechowuje.
- Kapitalizacja oznacza tu kapitalizację *krążącą* — monety już wyemitowane i będące w obiegu, nie rozwodnioną wartość zakładającą wszystkie monety, które kiedykolwiek powstaną.
- Seria szacunkowa, którą ma każda moneta, zaczyna się w czerwcu 2019. Moneta bez dokładnej serii zaczyna tam, a strona mówi, gdzie zakres naprawdę się zaczyna, zamiast po cichu zacząć później.
- **Kilka monet naraz, a cały kadr należy do kapitalizacji.** Ich kursy nie dzielą uczciwie jednej osi cen — postaw bitcoin obok monety warta ułamek centa, a jedna z nich jest płaską linią przy dolnej krawędzi — więc dolny panel kursów ustępuje, a każda linia jest podpisana na własnym końcu. Sześć to górna granica: siódme naciśnięcie nie jest przyjmowane, bo siódma linia wzięłaby kolor, który ma już szósta.
- Oś wartości ma dwa odczyty. Bezwzględna mówi, która moneta jest warta więcej; przeliczona na 100 w pierwszym dniu każdej z nich — której kapitalizacja rosła szybciej, i to jest jedyny czytelny odczyt, gdy jedna jest wielokrotnością drugiej. W obu przypadkach oś dat to suma ich dni: moneta, która zaczyna się dopiero w 2019, zaczyna tam i wcześniej jej nie ma.
- **Moneta, której nie ma w źródle wartości, jest pomijana, a nie rysowana płasko.** Wiele z tego, co może dodać wyszukiwanie, jest poza katalogiem CoinMetrics, a płaska linia na dole wykresu wartości czyta się jak moneta, która spadła do zera, a nie jak taka bez danych. Gdy jakieś pominięto, linia stanu je wymienia; jeśli zaznaczono tylko jedną i wraca pusta, strona mówi, że przedział nie ma użytecznej historii, zamiast rysować pusty kadr.
- **Zakres** to dwanaście, dwadzieścia cztery, sześćdziesiąt lub sto dwadzieścia miesięcy albo własny przedział. Historia monety może być krótsza niż żądany zakres — to dolna granica źródła, nie nieudane pobranie.

## Wyścig kapitalizacji krypto

Piętnaście monet o największej kapitalizacji dziś i jak ten porządek zmieniał się dzień po dniu.

- **O tym składzie się pyta, nie zapisuje go z góry.** Przy pobieraniu strona bierze piętnaście największych według wartości rynkowej z aktualnego rankingu CoinGecko; moneta, która urosła do tego rozmiaru w zeszłym roku, jest więc w tabeli, bez tego żeby ktoś edytował listę. Dlatego nie ma tu też wyboru monety: skład jest odpowiedzią, a pytanie dotyczy przedziału.
- Wartości dzienne pochodzą z CoinMetrics, jedno zapytanie dla całej tabeli. To seria szacunkowa tego źródła, która zaczyna się w czerwcu 2019 tak samo dla wszystkich, więc zakres jest tam przycinany zamiast odrzucany: tabela, w której dwie monety miałyby osiem lat historii, a trzynaście żadnej, czytałaby się jak monety, które pojawiły się znikąd.
- **Stablecoiny zostają.** Zmierzone 2026-10-11: w pierwszej trzydziestce było ich sześć, a tether był trzecią co do wielkości rzeczą na tym rynku. Tabela, która by je ukryła, porządkowałaby coś innego niż wielkość. To, co robią z obrazem, jest uczciwe: ich linia jest płaska, bo dolar jest wart dolara, więc tabela pokazuje na pierwszy rzut oka, które z największych rzeczy tu naprawdę się poruszają.
- Moneta, której źródło wartości nie ma, jest pomijana zamiast rysowana płasko przy zerze: płaska linia na dole wyścigu wartości czyta się jak moneta, która spadła do zera. Tabela może więc mieć mniej niż piętnaście pozycji, a linia stanu mówi, ile ich zostało.
- **Zakres** to dwanaście, dwadzieścia cztery lub sześćdziesiąt miesięcy albo własny przedział, przycinany do serii szacunkowej w ten sam sposób.
""",
    "pt-BR": """## Calendário de altas e baixas cripto

Um quadrado por dia, colorido pela variação daquele dia.

- **Uma grade cheia não é dado faltando.** Um calendário de ações é feito principalmente de buracos — fins de semana, feriados, suspensões — e se lê como um mercado se parece. Uma moeda é negociada todos os dias do ano, então todo quadrado está preenchido: a imagem é mais densa, não mais longa, e o que parece um feriado faltando é um mercado que nunca fecha.
- **Intervalo** é três, seis ou doze meses, ou um período próprio. Um período próprio é cortado para o que a fonte tem, e a página diz onde o intervalo realmente começa, em vez de começar mais tarde do que a data digitada.
- O primeiro quadrado é sempre 0 %: não há fechamento anterior dentro do intervalo, e buscá-lo fora faria o primeiro quadrado depender de um dia que o calendário não mostra.
- A cor é a variação, não o valor negociado. O volume de uma moeda é uma contagem de moedas, e nada nesta grade é escalado contra ele — do que o calendário trata é para que lado o dia foi e quanto.
- Os dias aqui são dias corridos. Um ano nesta página é cerca de 365 quadrados, não os 243 que uma bolsa daria, e nenhum dos dois números é aproximado.

## Histórico de capitalização cripto

A capitalização circulante de uma moeda ao longo do tempo, com o preço dos mesmos dias abaixo. Ou várias moedas ao mesmo tempo — uma linha cada, nomeada na ponta.

- **Onde as duas linhas se separam, está a emissão e a queima.** O preço é quanto custa uma moeda; a capitalização é esse preço vezes a quantidade de moedas existentes. Uma linha de capitalização que sobe enquanto a do preço cai é oferta crescendo, não um número errado.
- **Isso é medido, não extrapolado.** Multiplicar a oferta de hoje por um preço antigo é o caminho barato de desenhar esta página, e produz duas linhas que são a mesma linha: a capitalização não diria nada que o preço já não diga. O que se desenha aqui vem da API pública da CoinMetrics, que traz uma capitalização circulante diária: o Bitcoin chega a 2010, as demais moedas até onde a fonte as mantém.
- Aqui capitalização significa a *circulante* — as moedas já emitidas e em circulação, não uma contagem totalmente diluída que pressupõe todas as moedas que existirão.
- A série estimada que cada moeda tem começa em junho de 2019. Uma moeda sem série exata começa ali, e a página diz onde o intervalo realmente começa, em vez de começar silenciosamente mais tarde.
- **Várias moedas ao mesmo tempo, e o quadro inteiro vai para a capitalização.** Os preços delas não compartilham um eixo de preço honesto — coloque o bitcoin ao lado de uma moeda que vale uma fração de centavo e uma das duas vira uma linha reta no fundo —, então o painel de preços cede lugar e cada curva é nomeada na própria ponta. Seis é o teto: um sétimo toque não é aceito, porque uma sétima curva pegaria uma cor que a sexta já tem.
- O eixo de valor tem duas leituras. O absoluto responde qual moeda vale mais; o rebaseado em 100 no primeiro dia de cada uma responde qual capitalização cresceu mais rápido, e é o único legível quando uma vale várias vezes a outra. Nos dois casos o eixo de datas é a união dos dias delas: uma moeda que só começa em 2019 começa ali e falta antes disso.
- **Uma moeda que a fonte de valores não tem é omitida, não desenhada reta.** Boa parte do que uma busca pode acrescentar está fora do catálogo da CoinMetrics, e uma linha reta no fundo de um gráfico de valor se lê como uma moeda que foi a nada, não como uma sem número para desenhar. Quando há omitidas, a linha de status as nomeia; se só uma estiver marcada e voltar vazia, a página diz que o intervalo não tem histórico utilizável em vez de desenhar um quadro vazio.
- **Intervalo** é doze, vinte e quatro, sessenta ou cento e vinte meses, ou um período próprio. A história de uma moeda pode ser mais curta do que o intervalo pedido — esse é o piso da fonte, não uma busca que falhou.

## Corrida de capitalização cripto

As quinze moedas com a maior capitalização hoje e como essa ordem se moveu dia a dia.

- **O campo é perguntado, não escrito.** Na busca, a página pega as quinze maiores por valor de mercado do ranking ao vivo da CoinGecko; uma moeda que cresceu até esse tamanho no ano passado está na tabela sem que ninguém edite uma lista. É por isso também que não há seletor de moeda aqui: o campo é a resposta, e o que se pergunta é o período.
- Os valores diários vêm da CoinMetrics, um único pedido para toda a tabela. É a série estimada dessa fonte, que começa em junho de 2019 igualmente para todas, então o intervalo é cortado ali em vez de recusado: uma tabela em que duas moedas tivessem oito anos de história e treze nenhuma se leria como moedas que apareceram do nada.
- **Stablecoins ficam.** Medido em 2026-10-11, as trinta primeiras tinham seis delas, e tether era a terceira maior coisa deste mercado. Uma tabela que as escondesse estaria ordenando outra coisa que não tamanho. O que fazem com a imagem é honesto: sua linha é reta, porque um dólar vale um dólar, então a tabela mostra de relance quais das maiores coisas aqui realmente se movem.
- Uma moeda que a fonte de valores não tem é descartada em vez de desenhada reta no zero: uma linha reta no fundo de uma corrida de valor se lê como uma moeda que foi a nada. A tabela pode, portanto, ter menos de quinze, e a linha de status diz quantas vieram.
- **Intervalo** é doze, vinte e quatro ou sessenta meses, ou um período próprio, cortado para a série estimada do mesmo modo.
""",
    "cs": """## Kalendář pohybů krypto

Jeden čtvereček za den, obarvený podle změny toho dne.

- **Plná mřížka nejsou chybějící data.** Kalendář akcií je převážně samá díra — víkendy, svátky, pozastavení — a čte se tak, jak trh vypadá. Mince se obchoduje každý den v roce, takže každý čtvereček je vyplněný: obraz je hustší, ne delší, a co vypadá jako chybějící svátek, je trh, který nikdy nezavírá.
- **Rozsah** jsou tři, šest nebo dvanáct měsíců, nebo vlastní období. Vlastní období se zkrátí na to, co zdroj má, a stránka řekne, kde rozsah opravdu začíná, místo aby začal později než zadané datum.
- První čtvereček je vždy 0 %: uvnitř rozsahu není žádný předchozí závěr, a sahat pro něj ven by znamenalo, že první políčko závisí na dni, který kalendář neukazuje.
- Barva je změna, nikoli objem obchodů. Objem mince je počet mincí a nic v této mřížce se podle něj neškáluje — kalendář je o tom, kterým směrem se den vydal a jak daleko.
- Dny jsou tu kalendářní dny. Rok na této stránce je asi 365 čtverečků, ne 243, které by dala burza, a ani jedno číslo není přibližné.

## Historie kapitalizace krypto

Obíhající kapitalizace jedné mince v čase, pod ní cena za stejné dny. Nebo několik mincí najednou — každá vlastní čára, pojmenovaná na svém konci.

- **Tam, kde se obě čáry rozcházejí, vidíte emisi a pálení.** Cena je, kolik stojí jedna mince; kapitalizace je ta cena krát počet existujících mincí. Čára kapitalizace stoupající, zatímco čára ceny klesá, je rostoucí nabídka, ne špatné číslo.
- **To je měřené, ne dopočítané.** Vynásobit dnešní nabídku starou cenou je levný způsob, jak tuto stránku nakreslit, a dává to dvě čáry, které jsou tou samou čarou: kapitalizace by neřekla nic, co cena neříká už teď. Co se tu kreslí, pochází z veřejného API CoinMetrics, které nese denní obíhající kapitalizaci: Bitcoin sahá do roku 2010, ostatní mince tak daleko, jak je zdroj drží.
- Kapitalizace zde znamená tu *obíhající* — mince již vydané a v oběhu, nikoli plně zředěný počet, který počítá všechny mince, které kdy budou existovat.
- Odhadovaná řada, kterou má každá mince, začíná v červnu 2019. Mince bez přesné řady začíná tam, a stránka řekne, kde rozsah opravdu začíná, místo aby potichu začínal později.
- **Několik mincí najednou a celý rám patří kapitalizaci.** Jejich ceny nesdílejí poctivou cenovou osu — postavte bitcoin vedle mince za zlomek centu a jedna z nich je plochá čára u spodního okraje —, takže dolní panel s cenou ustoupí a každá čára je pojmenovaná na svém konci. Šest je strop: sedmé stisknutí se nepřijímá, protože sedmá čára by si vzala barvu, kterou šestá už má.
- Osa hodnoty má dva výklady. Absolutní říká, která mince má větší hodnotu; přepočtená na 100 v první den každé z nich říká, čí kapitalizace rostla rychleji, a je to jediný čitelný výklad, když je jedna násobkem druhé. V obou případech je osou dat sjednocení jejich dnů: mince, která začíná až v roce 2019, tam začíná a předtím chybí.
- **Mince, kterou zdroj hodnot nemá, je vynechána, ne nakreslena ploše.** Mnohé z toho, co může hledání přidat, je mimo katalog CoinMetrics, a plochá čára na spodku grafu hodnot se čte jako mince, která skončila na ničem, ne jako ta bez čísla. Když se nějaké vynechají, stavový řádek je pojmenuje; je-li vybrána jen jedna a vrátí se prázdná, stránka řekne, že období nemá použitelnou historii, místo aby nakreslila prázdný rám.
- **Rozsah** je dvanáct, dvacet čtyři, šedesát nebo sto dvacet měsíců, nebo vlastní období. Historie mince může být kratší než požadovaný rozsah — to je spodní hranice zdroje, ne selhané načtení.

## Závod kapitalizací krypto

Patnáct mincí s největší kapitalizací dnes a jak se toto pořadí den po dni měnilo.

- **O startovním poli se ptá, nezapisuje se.** Při načtení stránka vezme patnáct největších podle tržní hodnoty ze živého žebříčku CoinGecko; mince, která do této velikosti vyrostla loni, je tedy v tabulce, aniž by někdo upravoval seznam. Proto tu také není výběr mince: pole je odpověď a ptá se na období.
- Denní hodnoty pocházejí z CoinMetrics, jeden požadavek pro celou tabulku. Je to odhadovaná řada tohoto zdroje, která začíná v červnu 2019 stejně pro všechny, takže rozsah se tam zkracuje, nikoli odmítá: tabulka, v níž by dvě mince měly osm let historie a třináct žádnou, by se četla jako mince, které se objevily odnikud.
- **Stablecoiny zůstávají.** Měřeno 2026-10-11: v prvních třiceti jich bylo šest a tether byl třetí největší věcí na tomto trhu. Tabulka, která by je skryla, by řadila něco jiného než velikost. Co dělají s obrazem, je poctivé: jejich čára je rovná, protože dolar má hodnotu dolaru, takže tabulka na první pohled ukáže, které z největších věcí se tu opravdu hýbou.
- Mince, kterou zdroj hodnot nemá, je vynechána, nikoli nakreslena ploše na nule: plochá čára na spodku závodu hodnot se čte jako mince, která skončila na ničem. Tabulka proto může mít méně než patnáct a stavový řádek řekne, kolik jich přišlo.
- **Rozsah** je dvanáct, dvacet čtyři nebo šedesát měsíců, nebo vlastní období, zkrácené na odhadovanou řadu stejným způsobem.
""",
    "tr": """## Kripto artış-düşüş takvimi

Güne bir kare, o günün değişimine göre renklendirilmiş.

- **Dolu bir ızgara eksik veri değildir.** Hisse takvimi çoğunlukla boşluklardan oluşur — hafta sonları, tatiller, işlem durdurmaları — ve bir piyasanın göründüğü gibi okunur. Bir coin yılın her günü işlem görür, bu yüzden her kare doludur: görüntü daha uzun değil, daha yoğundur ve eksik bir tatil gibi görünen şey, hiç kapanmayan bir piyasadır.
- **Aralık** üç, altı veya on iki ay ya da kendi belirlediğiniz bir aralıktır. Kendi aralığınız kaynağın sahip olduğu kadarına kırpılır ve sayfa, yazılan tarihten daha geç başlamak yerine aralığın gerçekte nerede başladığını söyler.
- İlk kare her zaman %0'dır: aralık içinde önceki bir kapanış yoktur ve onu dışarıdan almak, ilk kareyi takvimin göstermediği bir güne bağımlı kılardı.
- Renk değişimdir, işlem tutarı değil. Bir coin'in hacmi coin sayısıdır ve bu ızgarada ona göre ölçeklenen hiçbir şey yoktur — takvimin ilgilendiği şey, günün hangi yöne gittiği ve ne kadar gittiğidir.
- Buradaki günler takvim günleridir. Bu sayfada bir yıl yaklaşık 365 karedir, bir borsanın vereceği 243 değil, ve iki sayı da yaklaşık değildir.

## Kripto piyasa değeri geçmişi

Bir coin'in dolaşımdaki piyasa değerinin zaman içindeki seyri, altında aynı günlerin fiyatı. Ya da birden çok coin bir arada — her biri ucunda adı yazan bir çizgi.

- **İki çizginin ayrıldığı yerde görülen şey arz artışı ve yakımdır.** Fiyat, bir coin'in maliyetidir; piyasa değeri ise o fiyatın var olan coin sayısıyla çarpımıdır. Fiyat çizgisi düşerken piyasa değeri çizgisi yükseliyorsa bu büyüyen arzdır, yanlış bir sayı değil.
- **Bu ölçülür, dışarı doğru hesaplanmaz.** Bugünkü arzı eski bir fiyatla çarpmak bu sayfayı çizmenin ucuz yoludur ve aynı çizgi olan iki çizgi üretir: piyasa değeri, fiyatın zaten söylediğinden fazlasını söylemezdi. Burada çizilen, günlük dolaşımdaki piyasa değerini taşıyan herkese açık CoinMetrics API'sinden gelir: Bitcoin 2010'a kadar uzanır, diğer coin'ler kaynağın tuttuğu kadar geriye gider.
- Burada piyasa değeri *dolaşımdaki* değer demektir — halihazırda çıkarılmış ve dolaşımda olan coin'ler, gelecekte var olacak her coin'i varsayan tam seyreltilmiş bir sayım değil.
- Her coin'in taşıdığı tahmin serisi Haziran 2019'da başlar. Kesin serisi olmayan bir coin orada başlar ve sayfa sessizce daha geç başlamak yerine aralığın gerçekte nerede başladığını söyler.
- **Birden çok coin bir arada ve çerçevenin tamamı piyasa değerine kalır.** Fiyatları dürüst bir fiyat eksenini paylaşmaz — bitcoin'i bir centin çok altında işlem gören bir coin'in yanına koyun, ikisinden biri dipte düz bir çizgi olur — bu yüzden alttaki fiyat paneli geri çekilir ve her çizgi kendi ucunda adlandırılır. Altı üst sınırdır: yedinci basış kabul edilmez, çünkü yedinci çizgi altıncının zaten kullandığı bir rengi alırdı.
- Değer ekseninin iki okuması var. Mutlak olan hangi coin'in daha değerli olduğunu; her birinin kendi ilk gününde 100'e indirgenmiş olan hangi piyasa değerinin daha hızlı büyüdüğünü söyler ve biri diğerinin katları olduğunda okunabilen tek görünüm budur. İkisinde de tarih ekseni günlerin birleşimidir: yalnızca 2019'da başlayan bir coin orada başlar ve öncesinde yoktur.
- **Değer kaynağının taşımadığı bir coin, sıfırda düz çizilmek yerine atlanır.** Aramanın ekleyebileceği coin'lerin çoğu CoinMetrics kataloğunun dışındadır ve bir değer grafiğinin dibindeki düz çizgi, çizilecek verisi olmayan bir coin değil, hiçliğe gitmiş bir coin gibi okunur. Atlananlar olduğunda durum satırı onları sayar; yalnızca bir coin seçilip boş dönerse sayfa boş bir çerçeve çizmek yerine aralıkta kullanılabilir geçmiş olmadığını söyler.
- **Aralık** on iki, yirmi dört, altmış veya yüz yirmi ay ya da kendi belirlediğiniz bir aralıktır. Bir coin'in geçmişi istediğiniz aralıktan kısa olabilir — bu kaynağın tabanıdır, başarısız bir çekim değil.

## Kripto piyasa değeri yarışı

Bugün piyasa değeri en yüksek on beş coin ve bu sıranın gün gün nasıl değiştiği.

- **Alan sorulur, yazılmaz.** Veri çekilirken sayfa, CoinGecko'nun canlı sıralamasından piyasa değerine göre güncel ilk on beşi alır; geçen yıl bu büyüklüğe ulaşan bir coin, kimse liste düzenlemeden tabloda yer alır. Bu yüzden burada coin seçici de yoktur: alanın kendisi yanıttır ve sorulan şey aralıktır.
- Günlük değerler CoinMetrics'ten, tüm tablo için tek bir istekle gelir. Bu kaynağın tahmin serisidir ve her coin için aynı şekilde Haziran 2019'da başlar, bu yüzden aralık reddedilmek yerine oraya kırpılır: ikisinin sekiz yıl geçmişi, on üçünün hiç geçmişi olmadığı bir tablo, hiçbir yerden çıkıvermiş coin'ler gibi okunurdu.
- **Stabilcoinler listede kalır.** 2026-10-11 itibarıyla ilk otuzda altı tanesi vardı ve tether bu piyasanın en büyük üçüncü şeyiydi. Onları gizleyen bir tablo, büyüklük dışında bir şeyi sıralardı. Görüntüye yaptıkları dürüstçe: bir dolar bir dolar değerindedir, bu yüzden çizgileri düzdür; tablo böylece buradaki en büyük şeylerden hangilerinin gerçekten hareket ettiğini tek bakışta gösterir.
- Değer kaynağında bulunmayan bir coin, sıfırda düz çizilmek yerine çıkarılır: bir değer yarışının dibindeki düz çizgi, hiçbir şeye dönüşmüş bir coin gibi okunur. Tablo bu yüzden on beşten az tutabilir ve durum satırı kaç tane alındığını söyler.
- **Aralık** on iki, yirmi dört veya altmış ay ya da kendi belirlediğiniz bir aralıktır ve aynı şekilde tahmin serisine kırpılır.
""",
    "ru": """## Календарь роста и падения крипто

Одна клетка на день, цвет — по изменению за этот день.

- **Полная сетка — это не пропущенные данные.** Календарь акций состоит в основном из дыр — выходные, праздники, приостановки торгов — и читается так, как выглядит рынок. Монета торгуется каждый день в году, поэтому заполнена каждая клетка: картинка плотнее, а не длиннее, и то, что похоже на потерянный праздник, — это рынок, который никогда не закрывается.
- **Диапазон** — три, шесть или двенадцать месяцев либо свой отрезок. Свой отрезок обрезается по тому, что есть у источника, и страница говорит, где диапазон действительно начинается, вместо того чтобы начаться позже введённой даты.
- Первая клетка всегда 0 %: внутри диапазона нет предыдущего закрытия, а брать его извне значило бы сделать первую клетку зависимой от дня, которого календарь не показывает.
- Цвет — это изменение, а не объём торгов. Объём монеты — это количество монет, и в этой сетке по нему ничего не масштабируется; календарь о том, куда пошёл день и насколько.
- Дни здесь календарные. Год на этой странице — около 365 клеток, а не 243, которые дала бы биржа, и ни одна из цифр не приблизительная.

## История капитализации крипто

Капитализация одной монеты в обращении во времени, под ней — цена за те же дни. Или несколько монет сразу — у каждой своя линия с подписью на конце.

- **Там, где две линии расходятся, видны эмиссия и сжигание.** Цена — это стоимость одной монеты; капитализация — эта цена, умноженная на число существующих монет. Линия капитализации, растущая, когда линия цены падает, — это растущее предложение, а не неверная цифра.
- **Это измеряется, а не экстраполируется.** Умножить сегодняшнее предложение на старую цену — дешёвый способ нарисовать эту страницу, и он даёт две линии, которые суть одна линия: капитализация не сказала бы ничего, чего цена уже не говорит. Нарисованное здесь взято из публичного API CoinMetrics, который ведёт ежедневную капитализацию в обращении: биткоин доступен с 2010 года, остальные монеты — насколько далеко источник их хранит.
- Здесь капитализация означает капитализацию *в обращении* — уже выпущенные монеты, а не полностью размытый подсчёт, учитывающий все монеты, которые когда-либо будут существовать.
- Оценочная серия, которая есть у каждой монеты, начинается в июне 2019. Монета без точной серии начинается там, и страница говорит, где диапазон действительно начинается, вместо того чтобы молча начаться позже.
- **Несколько монет сразу, и весь кадр отдаётся капитализации.** Их цены не делят честную ценовую ось — поставьте биткоин рядом с монетой ценой в доли цента, и одна из них окажется плоской линией у дна, — поэтому нижняя панель цен уступает место, и каждая линия подписана на своём конце. Шесть — предел: седьмое нажатие не принимается, потому что седьмая линия взяла бы цвет, который уже занят шестой.
- У оси значений два прочтения. Абсолютное отвечает, какая монета стоит больше; приведённая к 100 на первый день каждой — чья капитализация росла быстрее, и это единственное читаемое прочтение, когда одна во много раз больше другой. В обоих случаях ось дат — объединение их дней: монета, которая начинается только в 2019 году, начинается там, а раньше её нет.
- **Монета, которой нет у источника значений, отбрасывается, а не рисуется ровной.** Многое из того, что может добавить поиск, лежит вне каталога CoinMetrics, а ровная линия внизу графика значений читается как монета, обратившаяся в ничто, а не как та, для которой нет числа. Если что-то отброшено, строка состояния их назовёт; если выбрана одна и она вернулась пустой, страница скажет, что в диапазоне нет пригодной истории, вместо того чтобы нарисовать пустой кадр.
- **Диапазон** — двенадцать, двадцать четыре, шестьдесят или сто двадцать месяцев либо свой отрезок. История монеты может оказаться короче запрошенного диапазона — это нижняя граница источника, а не неудачная загрузка.

## Гонка капитализаций крипто

Пятнадцать монет с крупнейшей капитализацией сегодня и то, как этот порядок менялся день за днём.

- **Состав запрашивается, а не записывается.** При загрузке страница берёт пятнадцать крупнейших по рыночной стоимости из живого рейтинга CoinGecko; монета, выросшая до такого размера в прошлом году, попадает в таблицу без того, чтобы кто-то правил список. Поэтому здесь нет и выбора монеты: состав — это ответ, а спрашивается отрезок.
- Ежедневные значения приходят из CoinMetrics, один запрос на всю таблицу. Это оценочная серия источника, которая начинается в июне 2019 одинаково для всех, поэтому диапазон обрезается там, а не отклоняется: таблица, где у двух монет было бы восемь лет истории, а у тринадцати ни одного, читалась бы как монеты, возникшие из ниоткуда.
- **Стейблкоины остаются.** По измерению на 2026-10-11 в первой тридцатке их было шесть, а tether был третьей по величине вещью на этом рынке. Таблица, скрывающая их, ранжировала бы что-то иное, кроме размера. То, что они делают с картинкой, честно: их линия ровная, потому что доллар стоит доллар, — таблица тем самым показывает с одного взгляда, какие из крупнейших вещей здесь действительно двигаются.
- Монета, которой нет у источника значений, отбрасывается, а не рисуется ровной на нуле: ровная линия внизу гонки значений читается как монета, превратившаяся в ничто. Поэтому в таблице может быть меньше пятнадцати, и строка состояния говорит, сколько их получено.
- **Диапазон** — двенадцать, двадцать четыре или шестьдесят месяцев либо свой отрезок, обрезаемый по оценочной серии так же.
""",
    "ja": """## 暗号資産の値動きカレンダー

1 日 1 マス、その日の変化で色分けします。

- **枠がすべて埋まっているのは、データの欠落ではありません。** 株式のカレンダーは穴だらけです。週末、祝日、売買停止があり、市場の見た目そのままに読めます。暗号資産は年中無休で取引されるため、すべてのマスが埋まります。絵は長くなるのではなく密度が上がり、休日の抜け落ちに見えるものは、休まない市場そのものです。
- **期間**は 3・6・12 か月、または任意の期間です。任意の期間はソースが持つ範囲に切り詰められ、ページは入力した日付より後から黙って始めるのではなく、実際にどこから始まるかを伝えます。
- 最初のマスは常に 0 % です。期間内に前日の終値はなく、外から取ってくれば、カレンダーが表示していない日の値に最初のマスが依存することになります。
- 色は変化率であり、売買代金ではありません。暗号資産の出来高は「何枚」という数で、このグリッドはそれを基準にしていません。カレンダーが扱うのは、その日がどちらへ動いたかと、その大きさです。
- ここでの日数は暦日です。このページの 1 年は約 365 マスで、株式市場の 243 ではありません。どちらも概算ではありません。

## 暗号資産の時価総額の推移

ある暗号資産の流通時価総額の推移。下段には同じ期間の価格。複数の銘柄を同時に並べることもできます——それぞれ末端に名前の付いた線になります。

- **2 本の線が離れるところが、新規発行とバーンです。** 価格は 1 枚の値段、時価総額はその価格に存在する枚数を掛けたものです。価格の線が下がっているのに時価総額の線が上がっているなら、それは供給が増えているのであって、数値が壊れているのではありません。
- **これは実測であって外挿ではありません。** 現在の流通量に過去の価格を掛ければこのページは安く描けますが、それは結局同じ 1 本の線を 2 本描くだけで、時価総額は価格がすでに語っていること以上を何も語りません。ここで描いているのは、日次の流通時価総額を保持している公開 API CoinMetrics から取得したものです。ビットコインは 2010 年まで遡れ、その他の銘柄はソースが保持する範囲までです。
- ここでの時価総額は*流通*時価総額、つまりすでに発行され流通している分です。将来発行される分まで含めた完全希薄化後の数値ではありません。
- すべての銘柄が持つ推計系列は 2019 年 6 月に始まります。実測系列がない銘柄はそこから始まり、ページは黙って後から始めるのではなく、期間が実際にどこから始まるかを伝えます。
- **複数の銘柄を並べると、枠のすべてが時価総額に使われます。** 銘柄ごとの価格は正直な価格軸を共有できません——ビットコインの隣に 1 円にも満たない銘柄を置けば、どちらかは底辺の平らな線になります——だから下の価格パネルは退き、各線は自分の末端に名前を付けます。最大六銘柄です。七つ目は受け付けません。七本目の線は六本目がすでに使っている色を取ることになるからです。
- 目盛りには二つの読み方があります。絶対値はどちらが大きいかを、各銘柄の初日を 100 とした基準はどちらが速く伸びたかを答え、一方が他方の何倍もあるときに読めるのは後者だけです。どちらの場合も日付軸は和集合です。2019 年からしかない銘柄はそこから始まり、それ以前は欠けます。
- **時価総額の源が持たない銘柄は、平らに描かずに除外します。** 検索で追加できる銘柄の多くは CoinMetrics の収録外で、時価総額グラフの最下段の平らな線は、描く数字がない銘柄ではなく、無に帰した銘柄に読めます。除外した銘柄があるときは状態行が名前を挙げ、一つだけ選んで空で返ってきたときは、空の枠を描かずに、その期間に使える履歴がないと伝えます。
- **期間**は 12・24・60・120 か月、または任意の期間です。銘柄の履歴が指定より短いことはあります。それはソースの下限であって、失敗した取得ではありません。

## 暗号資産の時価総額レース

現在の時価総額が大きい十五銘柄と、その順位が日々どう動いたか。

- **顔ぶれは書き置きではなく、その都度問い合わせます。** 取得時にページは CoinGecko のリアルタイム順位から時価総額上位 15 件を取ります。昨年この規模に育った銘柄も、誰かがリストを書き換えなくても載ります。だからこのページには銘柄選択がありません。顔ぶれ自体が答えで、問われるのは期間だからです。
- 日々の値は CoinMetrics から、表全体を 1 回のリクエストで取得します。このソースの推計系列で、どの銘柄も同じく 2019 年 6 月始まりです。そのため期間は拒否せずそこで切り詰めます。2 銘柄にだけ 8 年分の履歴があり、残り 13 銘柄に何もない表は、どこからともなく現れた銘柄に見えてしまうからです。
- **ステーブルコインは残します。** 2026-10-11 の実測では上位 30 件に 6 件入っており、tether はこの市場で 3 番目に大きな存在でした。それを隠した表は、大きさ以外の何かを順位付けしていることになります。絵に対する彼らの振る舞いは正直です。1 ドルは 1 ドルなので線は平らになり、この市場で大きなもののうちどれが実際に動いているかが一目で分かります。
- 値のソースにない銘柄は、ゼロで平らに描くのではなく除外します。時価総額レースの最下段にある平らな線は、無に帰した銘柄に読めるからです。したがって表は 15 件より少なくなることがあり、状態行が取れた件数を伝えます。
- **期間**は 12・24・60 か月、または任意の期間で、同じように推計系列に切り詰められます。
""",
    "ko": """## 크립토 등락 캘린더

하루에 한 칸, 그날의 변화로 색을 칠합니다.

- **칸이 모두 채워진 것은 빠진 데이터가 아닙니다.** 주식 캘린더는 대부분 구멍입니다. 주말, 휴일, 거래정지가 있어 시장이 보이는 그대로 읽힙니다. 암호화폐는 연중 매일 거래되므로 모든 칸이 채워집니다. 그림이 길어지는 것이 아니라 촘촘해지는 것이며, 빠진 휴일처럼 보이는 것은 쉬지 않는 시장 그 자체입니다.
- **구간**은 3·6·12개월 또는 직접 지정입니다. 직접 지정한 구간은 소스가 가진 범위로 잘리고, 페이지는 입력한 날짜보다 뒤에서 조용히 시작하는 대신 실제로 어디서 시작하는지를 알려줍니다.
- 첫 칸은 항상 0%입니다. 구간 안에는 이전 종가가 없고, 밖에서 가져오면 캘린더가 보여주지 않는 날에 첫 칸이 의존하게 됩니다.
- 색은 변화율이며 거래대금이 아닙니다. 암호화폐의 거래량은 '몇 개'라는 수량이고 이 그리드는 그것을 기준으로 삼지 않습니다. 캘린더가 다루는 것은 그날 어느 쪽으로 움직였는지와 그 크기입니다.
- 여기서의 날짜는 달력상 날짜입니다. 이 페이지의 1년은 약 365칸이며 증권시장의 243일이 아닙니다. 둘 다 어림수가 아닙니다.

## 크립토 시가총액 추이

암호화폐의 유통 시가총액 추이. 아래에는 같은 기간의 가격.여러 종목을 한 번에 놓을 수도 있습니다 — 각각 끝에 이름이 붙은 선이 됩니다.

- **두 선이 갈라지는 곳이 발행과 소각입니다.** 가격은 한 개의 값이고, 시가총액은 그 가격에 존재하는 개수를 곱한 것입니다. 가격 선이 내려가는데 시가총액 선이 올라가면 그것은 공급이 늘어난 것이지 숫자가 잘못된 것이 아닙니다.
- **이것은 실측이며 외삽이 아닙니다.** 현재 유통량에 과거 가격을 곱하면 이 페이지를 값싸게 그릴 수 있지만, 결국 같은 선을 두 번 그리는 셈이어서 시가총액은 가격이 이미 말하는 것 외에 아무것도 말하지 않습니다. 여기서 그리는 것은 일별 유통 시가총액을 보유한 공개 API CoinMetrics에서 가져온 것입니다. 비트코인은 2010년까지 거슬러 올라가고, 나머지 코인은 소스가 보유한 범위까지입니다.
- 여기서 시가총액은 *유통* 시가총액, 즉 이미 발행되어 유통되는 물량입니다. 앞으로 발행될 물량까지 포함한 완전 희석 기준이 아닙니다.
- 모든 코인이 가진 추정 시리즈는 2019년 6월에 시작합니다. 실측 시리즈가 없는 코인은 거기서 시작하고, 페이지는 조용히 뒤에서 시작하는 대신 구간이 실제로 어디서 시작하는지를 알려줍니다.
- **여러 종목을 함께 놓으면 프레임 전체가 시가총액에 쓰입니다.** 종목별 가격은 정직한 가격 축을 공유할 수 없습니다——비트코인 옆에 1센트도 안 되는 종목을 놓으면 둘 중 하나는 바닥의 평평한 선이 됩니다——그래서 아래 가격 패널은 물러나고 각 선은 자기 끝에 이름이 붙습니다. 최대 6개입니다. 일곱 번째는 받지 않습니다. 일곱 번째 선은 여섯 번째가 이미 쓰고 있는 색을 가져가게 되기 때문입니다.
- 값 축에는 두 가지 읽기가 있습니다. 절댓값은 어느 종목이 더 큰지를, 각자의 첫날을 100으로 한 기준은 누가 더 빨리 컸는지를 답하며, 한쪽이 다른 쪽의 몇 배일 때 읽히는 것은 후자뿐입니다. 두 경우 모두 날짜 축은 합집합입니다. 2019년에야 시작한 종목은 거기서 시작하고 그 이전은 비어 있습니다.
- **시가총액 소스가 갖고 있지 않은 종목은 평평하게 그리지 않고 제외합니다.** 검색으로 추가할 수 있는 종목의 상당수는 CoinMetrics 목록 밖에 있고, 시가총액 그래프 맨 아래의 평평한 선은 그릴 숫자가 없는 종목이 아니라 아무것도 아닌 것이 되어버린 종목으로 읽힙니다. 제외된 종목이 있으면 상태 줄이 이름을 밝히고, 하나만 골랐는데 빈손으로 돌아오면 빈 프레임을 그리는 대신 그 구간에 쓸 만한 이력이 없다고 알려줍니다.
- **구간**은 12·24·60·120개월 또는 직접 지정입니다. 코인의 이력이 요청한 구간보다 짧을 수 있습니다. 그것은 소스의 하한이지 실패한 조회가 아닙니다.

## 크립토 시가총액 레이스

현재 시가총액이 가장 큰 열다섯 코인과 그 순위가 날마다 어떻게 움직였는지.

- **출전 목록은 적어 두는 것이 아니라 매번 묻습니다.** 조회 시점에 페이지는 CoinGecko의 실시간 순위에서 시가총액 상위 15개를 가져옵니다. 지난해 이 규모로 자란 코인도 누가 목록을 고치지 않아도 올라옵니다. 그래서 이 페이지에는 코인 선택이 없습니다. 목록 자체가 답이고, 물어보는 것은 구간이기 때문입니다.
- 일별 값은 CoinMetrics에서 표 전체를 한 번의 요청으로 가져옵니다. 이 소스의 추정 시리즈이며 모든 코인이 같은 2019년 6월에 시작합니다. 그래서 구간은 거부하지 않고 거기서 자릅니다. 두 코인에만 8년치 이력이 있고 열세 코인에 아무것도 없는 표는 어디선가 불쑥 나타난 코인으로 읽히기 때문입니다.
- **스테이블코인은 남겨 둡니다.** 2026-10-11 실측에서 상위 30개 안에 여섯 개가 있었고, 테더는 이 시장에서 세 번째로 큰 존재였습니다. 그것을 숨긴 표는 크기 외의 무언가를 순위 매기는 셈입니다. 그림에서 그것들의 거동은 정직합니다. 1달러는 1달러이므로 선은 평평해지고, 이 시장에서 큰 것들 가운데 무엇이 실제로 움직이는지 한눈에 드러납니다.
- 값 소스에 없는 코인은 0에서 평평하게 그리는 대신 제외합니다. 시가총액 레이스 맨 아래의 평평한 선은 아무것도 아닌 것이 되어버린 코인으로 읽히기 때문입니다. 따라서 표는 열다섯보다 적을 수 있고, 상태 줄이 가져온 개수를 알려줍니다.
- **구간**은 12·24·60개월 또는 직접 지정이며, 같은 방식으로 추정 시리즈에 맞춰 잘립니다.
""",
    "zh-Hans": """## 加密货币涨跌日历

一格一天，按当天的涨跌着色。

- **格子全填满不是缺数据。** 股票日历大半是空的——周末、休市、停牌——它读起来就是市场的样子。加密货币一年里天天交易，所以每一格都有数：画面变密而不是变长，看着像漏掉休息日的那些空格，其实是这个市场从不休息。
- **区间**是三个月、六个月、十二个月，或者自定义。自定义区间会裁剪到源端实际持有的范围，页面会说出区间真正从哪天开始，而不是悄悄从更晚的地方起画。
- 第一格恒为 0%：区间内没有前一天收盘价，而到区间外去取一个，会让第一格依赖一个日历上没有显示的日子。
- 颜色是涨跌幅，不是成交额。加密货币的成交量是「多少枚」，这张网格里没有任何东西按它缩放——日历讲的是这一天往哪边走、走了多远。
- 这里的天数都是自然日。一年的日历约 365 格，不是股市那 243 格，两个数字都不是估算的。

## 加密货币市值历程

某个币种流通市值随时间的变化，下方是同一批日子的价格。也可以同时画几个币种，各一条线、在末端标出名字。

- **两条线分头走的地方，看的就是增发与销毁。** 价格是一枚币值多少；市值是这个价格乘以现存多少枚。价格线在跌而市值线在涨，那是供应在增长，不是数字错了。
- **这是量出来的，不是外推的。** 用今天的流通量乘以一个老价格，是画这一页最省事的办法，而它给出的两条线其实是同一条——那样市值线说不出任何价格线没说过的话。这里画的是 CoinMetrics 公开接口的逐日流通市值：比特币可回溯到 2010 年，其余币按源端持有多少算多少。
- 这里的市值指*流通*市值——已经产出并在流通的币，不是把未来所有币都算进去的完全稀释口径。
- 每个币都有的估算序列统一从 2019 年 6 月开始。没有真值序列的币就从那天起画，页面会说出区间实际从哪天开始，而不是悄悄往后挪。
- **可以同时画几个币种**：勾选两个以上，各画一条线、在末端标出名字。几个币种的价格没有一套共用的刻度——比特币旁边放一个单价不到一分钱的币，后者就是贴着底边的一条直线——所以下方的价格面板让出来，整幅画面都给市值。最多六个：第七个不接受，因为第七条曲线会用到第六条已经用掉的颜色。
- **市值刻度有两种读法**：绝对值答的是「谁更大」，各币以自己的首日折到 100 答的是「谁涨得更快」——当一个币比另一个大好几倍，绝对值画面里小的那条就是贴底的直线，读得出来的只有第二种。两种读法下日期轴都取**并集**而不是交集：2019 年才有数据的币就从那天起画，之前那段是空的，而不是把它拉到和比特币一样长。
- **市值源端不携带的币种是略过，不是画成贴地的零线。** 检索框能添进来的币，大半不在 CoinMetrics 的目录里；而市值图最底下那条平线，读起来是一个归零了的币，而不是一个取不到数的币。有几个被略过时状态行会说出是哪几个；只勾了一个而它恰好没数据时，说的是这个区间里没有取到足够长的市值历史，而不是画一张空图。
- **区间**是十二个月、二十四个月、六十个月、一百二十个月，或者自定义。某个币种的历史可能比你要的区间短——那是源端的尽头，不是取数失败。

## 加密货币市值榜

当前市值最大的十五个币种，以及这个排名逐日怎么演变。

- **榜上的币是问出来的，不是写死的。** 取数那一刻，页面从 CoinGecko 的实时排名里取当前市值前十五名；去年才长到这个体量的币也会在榜上，不需要有人去改清单。所以这一页没有币种选择器：榜单本身就是答案，要问的是区间。
- 逐日数值来自 CoinMetrics，整个榜一次请求取回。用的是它的估算口径，所有币统一从 2019 年 6 月起，因此区间是裁剪到那里而不是拒绝——一张两个币有八年历史、十三个币什么都没有的表，读起来像这些币凭空出现。
- **稳定币保留在榜上。** 2026-10-11 实测，前三十名里有六个稳定币，而泰达币是这个市场上第三大的东西。把它们藏起来的榜，排的就不是「大」了。它们对画面的影响是诚实的：一美元就是一美元，所以它们那条线是平的，于是一眼就能看出这个市场上最大的那些东西里，哪些真的在动。
- 市值源端不携带的币种是丢弃而不是画成贴地的零线——市值榜最底下那条平线，读起来像一个归零了的币。所以榜上可能少于十五个，状态行会说出实际取到几个。
- **区间**是十二个月、二十四个月、六十个月，或者自定义，同样裁剪到估算序列的起点。
""",
    "zh-Hant": """## 加密貨幣漲跌日曆

一格一天，按當天的漲跌著色。

- **格子全填滿不是缺數據。** 股票日曆大半是空的——週末、休市、停牌——它讀起來就是市場的樣子。加密貨幣一年裡天天交易，所以每一格都有數：畫面變密而不是變長，看著像漏掉休息日的那些空格，其實是這個市場從不休息。
- **區間**是三個月、六個月、十二個月，或者自訂。自訂區間會裁剪到源端實際持有的範圍，頁面會說出區間真正從哪天開始，而不是悄悄從更晚的地方起畫。
- 第一格恆為 0%：區間內沒有前一天收盤價，而到區間外去取一個，會讓第一格依賴一個日曆上沒有顯示的日子。
- 顏色是漲跌幅，不是成交額。加密貨幣的成交量是「多少枚」，這張網格裡沒有任何東西按它縮放——日曆講的是這一天往哪邊走、走了多遠。
- 這裡的天數都是自然日。一年的日曆約 365 格，不是股市那 243 格，兩個數字都不是估算的。

## 加密貨幣市值歷程

某個幣種流通市值隨時間的變化，下方是同一批日子的價格。也可以同時畫幾個幣種，各一條線、在末端標出名字。

- **兩條線分頭走的地方，看的就是增發與銷毀。** 價格是一枚幣值多少；市值是這個價格乘以現存多少枚。價格線在跌而市值線在漲，那是供應在增長，不是數字錯了。
- **這是量出來的，不是外推的。** 用今天的流通量乘以一個老價格，是畫這一頁最省事的辦法，而它給出的兩條線其實是同一條——那樣市值線說不出任何價格線沒說過的話。這裡畫的是 CoinMetrics 公開介面的逐日流通市值：比特幣可回溯到 2010 年，其餘幣按源端持有多少算多少。
- 這裡的市值指*流通*市值——已經產出並在流通的幣，不是把未來所有幣都算進去的完全稀釋口徑。
- 每個幣都有的估算序列統一從 2019 年 6 月開始。沒有真值序列的幣就從那天起畫，頁面會說出區間實際從哪天開始，而不是悄悄往後挪。
- **可以同時畫幾個幣種**：勾選兩個以上，各畫一條線、在末端標出名字。幾個幣種的價格沒有一套共用的刻度——比特幣旁邊放一個單價不到一分錢的幣，後者就是貼著底邊的一條直線——所以下方的價格面板讓出來，整幅畫面都給市值。最多六個：第七個不接受，因為第七條曲線會用到第六條已經用掉的顏色。
- **市值刻度有兩種讀法**：絕對值答的是「誰更大」，各幣以自己的首日折到 100 答的是「誰漲得更快」——當一個幣比另一個大好幾倍，絕對值畫面裡小的那條就是貼底的直線，讀得出來的只有第二種。兩種讀法下日期軸都取**聯集**而不是交集：2019 年才有數據的幣就從那天起畫，之前那段是空的，而不是把它拉到和比特幣一樣長。
- **市值源端不攜帶的幣種是略過，不是畫成貼地的零線。** 檢索框能加進來的幣，大半不在 CoinMetrics 的目錄裡；而市值圖最底下那條平線，讀起來是一個歸零了的幣，而不是一個取不到數的幣。有幾個被略過時狀態行會說出是哪幾個；只勾了一個而它恰好沒數據時，說的是這個區間裡沒有取到足夠長的市值歷史，而不是畫一張空圖。
- **區間**是十二個月、二十四個月、六十個月、一百二十個月，或者自訂。某個幣種的歷史可能比你要的區間短——那是源端的盡頭，不是取數失敗。

## 加密貨幣市值榜

目前市值最大的十五個幣種，以及這個排名逐日怎麼演變。

- **榜上的幣是問出來的，不是寫死的。** 取數那一刻，頁面從 CoinGecko 的即時排名裡取目前市值前十五名；去年才長到這個體量的幣也會在榜上，不需要有人去改清單。所以這一頁沒有幣種選擇器：榜單本身就是答案，要問的是區間。
- 逐日數值來自 CoinMetrics，整個榜一次請求取回。用的是它的估算口徑，所有幣統一從 2019 年 6 月起，因此區間是裁剪到那裡而不是拒絕——一張兩個幣有八年歷史、十三個幣什麼都沒有的表，讀起來像這些幣憑空出現。
- **穩定幣保留在榜上。** 2026-10-11 實測，前三十名裡有六個穩定幣，而泰達幣是這個市場上第三大的東西。把它們藏起來的榜，排的就不是「大」了。它們對畫面的影響是誠實的：一美元就是一美元，所以它們那條線是平的，於是一眼就能看出這個市場上最大的那些東西裡，哪些真的在動。
- 市值源端不攜帶的幣種是丟棄而不是畫成貼地的零線——市值榜最底下那條平線，讀起來像一個歸零了的幣。所以榜上可能少於十五個，狀態行會說出實際取到幾個。
- **區間**是十二個月、二十四個月、六十個月，或者自訂，同樣裁剪到估算序列的起點。
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

        # BOM 与行尾照抄原文（这 14 份现在不带 BOM）。
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
