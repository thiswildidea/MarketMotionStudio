# -*- coding: utf-8 -*-
r"""把「市值历程」这一章插进 14 份 `Assets/Help/help-<tag>.md`。

**按序号插，不按标题找。** 章节顺序就是导航顺序（`listingtext.chapter_of`），而标题在
14 种语言里各不相同——拿标题定位等于给每种语言各写一个锚，插错一处就是 14 份全错。
所以这里问导航要这一章是第几章，再插到那个位置上。

幂等：先看那个位置上是不是已经是这一章（比较该语言的标题），是就整段替换，不是就插入。
跑几遍结果一样。

文件是 **LF、无 BOM**（与 resw 相反：那个必须有 BOM）。读用 `utf-8-sig` 并把可能多出来的
BOM 剥掉，写回用 `utf-8`。`read_text/write_text` 会把 CRLF 归一成 LF，git 上表现为整文件
重写，所以一律走 bytes。

用法：python tools\port-caphistory-help.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio")
HELP = ROOT / "src" / "MarketMotionStudio" / "Assets" / "Help"
TOOLS = ROOT / "tools"

sys.path.insert(0, str(TOOLS))

import listingtext  # noqa: E402

NAV_KEY = "NavCapHistory"

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 每种语言：标题、摘要一句、要点若干条（都是已带 `- ` 前缀的整行）
CHAPTERS = {
    "en-US": (
        "Market Value History",

        "One stock's circulating market value day by day, with its share price beneath it on the same time axis. Or several companies at once — one line each, named at its end.",
        [
            "- **The value is recovered, not quoted.** The source has no historical share "
            "count for any day. The count comes from the turnover rate, which is the "
            "volume as a fraction of the shares in circulation — so `volume ÷ turnover "
            "rate` *is* the circulating count, and the value is the day's price times it.",
            "- **The count is a twenty-day median.** The rate arrives with two decimals, "
            "so one day's count carries about a percent of noise, while a share count is "
            "a staircase — it moves on a placement or a buyback and is flat between. The "
            "median keeps the step on the day it happened and drops the rest.",
            "- **Only the shares traded in this market are counted.** Shares the company "
            "lists somewhere else are left out, so a company listed in two places sits "
            "below the “total market value” a quote app shows — that figure prices the "
            "other market's shares at this market's price too. ICBC's gap is entirely "
            "H-shares. Stock still under lock-up in this market is out as well.",
            "- **In Hong Kong the price is a traded average.** That market serves no "
            "unadjusted close, so the price is the amount over the volume, and the lower "
            "panel is labelled “average trade price” rather than “share price”.",
            "- **New York divides by every share, not by the ones that trade.** Its rate "
            "is a fraction of all the shares the company has, insiders' included, so the "
            "line there is a total value rather than a circulating one: the count runs "
            "above a quote app's circulating figure by exactly the insider stake — nothing "
            "at Apple, 4% at NVIDIA, 12% at Tesla. It reaches back to 2009, the same "
            "depth the mainland gets.",
            "- **A ten-year curve reads as if it once went to zero, and does not.** The "
            "axis has to hold the peak, so an early stretch worth a tenth of it sits "
            "within a few pixels of the baseline — 五粮液's 853 亿 against a 13,097 亿 "
            "peak is under seven per cent of it. That is why the low and high marks "
            "print their own figures: a bare dot down there is read as zero.",
            "- **The figure rides the line.** A label at each line's leading end names "
            "the company and gives the value it has reached at that moment, and it moves "
            "with the animation — scrub the bar and it goes with the line. With one "
            "company both panels carry one, value and price, and the big figure over the "
            "panel says the same number; with several the labels are also what tells the "
            "lines apart.",
            "- Span: one, two, five or ten years, or two dates of your own.",
            "Compare several companies at once. Tick more than one chip and each gets a line, named at its own leading end. Several companies' share prices do not share a price axis honestly — put 贵州茅台 beside 京东方A and one of them is a flat line along the bottom — so the lower price panel steps aside and the whole frame goes to market value. Up to six; a seventh is refused rather than quietly dropped, because a frame drawn from six of the seven companies somebody ticked answers about a list nobody chose.",
            "The value axis has two readings. Absolute answers which company is worth more; rebased to 100 at each line's own first day answers whose value grew faster, and is the only readable one once one is several times the other. Either way the date axis is the union of their days rather than the overlap: the overlap would cut a ten-year comparison down to the stretch of whichever listed last.",
        ]),
    "de": (
        "Marktwert-Verlauf",

        "Der Marktwert einer Aktie im Umlauf Tag für Tag, darunter auf derselben Zeitachse ihr Kurs. Oder mehrere Unternehmen zugleich — je eine Linie, am Ende beschriftet.",
        [
            "- **Der Wert ist errechnet, nicht geliefert.** Die Quelle kennt für keinen "
            "Tag eine historische Aktienzahl. Sie folgt aus der Umsatzrate — dem Anteil "
            "des Umsatzes an den umlaufenden Aktien — also ist `Umsatz ÷ Umsatzrate` "
            "genau diese Zahl, und der Wert ist der Tageskurs mal ihr.",
            "- **Die Zahl ist ein Zwanzig-Tage-Median.** Die Rate kommt mit zwei "
            "Dezimalstellen, ein Tag bringt also etwa ein Prozent Rauschen, während eine "
            "Aktienzahl eine Treppe ist: Sie springt bei Kapitalerhöhung oder Rückkauf "
            "und bleibt sonst. Der Median lässt die Stufe am Tag ihres Sprungs.",
            "- **Gezählt werden nur die Aktien dieses Marktes.** Was das Unternehmen "
            "anderswo notiert hat, bleibt draußen; bei doppelter Notierung liegt die Linie "
            "unter der „Gesamtmarktkapitalisierung“, die eine Kurs-App zeigt — dort werden "
            "die anderen Aktien zum Kurs dieses Marktes bewertet. Die Lücke bei ICBC sind "
            "ausschließlich H-Aktien. Noch gebundene Aktien fehlen ebenfalls.",
            "- **In Hongkong ist der Preis ein Handelsdurchschnitt.** Dort gibt es keinen "
            "unbereinigten Schlusskurs, also ist der Preis Umsatz geteilt durch Volumen, "
            "und das untere Feld heißt „durchschnittlicher Handelskurs“.",
            "- **New York teilt durch alle Aktien, nicht durch die handelbaren.** Seine "
            "Rate ist ein Anteil aller Aktien des Unternehmens, auch der von Insidern, "
            "also ist die Linie dort ein Gesamtwert statt eines Umlaufwerts: Die Zahl "
            "liegt genau um den Insider-Anteil über dem Umlaufwert einer Kurs-App — bei "
            "Apple null, bei NVIDIA 4 %, bei Tesla 12 %. Zurück reicht es bis 2009, "
            "dieselbe Tiefe wie auf dem Festland.",
            "- **Eine Zehnjahreskurve liest sich, als wäre sie einmal auf null gefallen "
            "— und das ist sie nicht.** Die Achse muss die Spitze fassen, also liegt ein "
            "früher Abschnitt von einem Zehntel davon nur wenige Pixel über der Grundlinie "
            "— 五粮液s 853 億 gegen eine Spitze von 13.097 億 entspricht das nicht einmal "
            "sieben Prozent der Panelhöhe. Deshalb tragen die Marken ihren eigenen Wert: Ein "
            "bloßer Punkt dort unten wird als null gelesen.",
            "- **Die Zahl fährt auf der Linie mit.** Ein Etikett am vorderen Ende jeder "
            "Linie nennt das Unternehmen und zeigt, welchen Wert es in diesem Moment "
            "erreicht hat; es bewegt sich mit der Animation — schieben Sie den Regler, "
            "und es geht mit der Linie. Bei einem Unternehmen tragen beide Felder je "
            "eines, Wert und Kurs, und die große Zahl über dem Feld nennt dieselbe Zahl; "
            "bei mehreren sind die Etiketten außerdem das, was die Linien "
            "auseinanderhält.",
            "- Zeitraum: ein, zwei, fünf oder zehn Jahre, oder zwei eigene Daten.",
            "Mehrere Unternehmen auf einmal. Bei mehr als einem Chip bekommt jedes eine eigene Linie, am eigenen Ende beschriftet. Die Kurse mehrerer Unternehmen teilen keine ehrliche Preisachse — 贵州茅台 neben 京东方A und eines von beiden ist eine flache Linie am Boden —, darum tritt das untere Preisfeld zurück und der ganze Rahmen gehört dem Marktwert. Bis zu sechs; ein siebtes wird abgelehnt statt still weggelassen, denn ein Bild aus sechs von sieben ausgewählten Unternehmen beantwortet eine Liste, die niemand gewählt hat.",
            "Die Wertachse hat zwei Lesarten. Absolut beantwortet, welches Unternehmen mehr wert ist; auf 100 umbasiert ab dem je eigenen ersten Tag, wessen Wert schneller wuchs — und das ist die einzige lesbare, sobald eines ein Vielfaches des anderen ist. In beiden Fällen ist die Zeitachse die Vereinigung ihrer Tage, nicht der Schnitt: Der Schnitt würde einen Zehnjahresvergleich auf die Spanne der zuletzt notierten Gesellschaft kürzen.",
        ]),
    "es": (
        "Historial de valor de mercado",

        "El valor de mercado en circulación de una acción día a día, con su cotización debajo en el mismo eje temporal. O varias empresas a la vez — una línea cada una, rotulada en su extremo.",
        [
            "- **El valor se reconstruye, no se cita.** La fuente no tiene un número "
            "histórico de acciones para ningún día. Sale de la tasa de rotación, que es el "
            "volumen como fracción de las acciones en circulación — así que `volumen ÷ "
            "tasa de rotación` *es* ese número, y el valor es el precio del día por él.",
            "- **El número es la mediana de veinte días.** La tasa llega con dos "
            "decimales, así que un día trae alrededor de un uno por ciento de ruido, "
            "mientras que el número de acciones es una escalera: salta en una ampliación o "
            "una recompra y no se mueve entre medias. La mediana deja el escalón en el día "
            "en que ocurrió.",
            "- **Solo se cuentan las acciones negociadas en este mercado.** Las que la "
            "empresa cotiza en otro mercado quedan fuera, así que una empresa con doble "
            "cotización queda por debajo de la «capitalización total» que muestra una app "
            "de cotizaciones: esa cifra valora las acciones del otro mercado al precio de "
            "este. En ICBC la diferencia son íntegramente acciones H. Las acciones aún "
            "bloqueadas en este mercado tampoco entran.",
            "- **En Hong Kong el precio es un promedio negociado.** Ese mercado no sirve "
            "un cierre sin ajustar, así que el precio es el importe entre el volumen, y el "
            "panel inferior se llama «precio medio de negociación».",
            "- **Nueva York divide por todas las acciones, no por las que cotizan.** Su "
            "tasa es una fracción de todas las acciones de la empresa, incluidas las de "
            "los directivos, así que la línea es un valor total y no uno en circulación: "
            "la cifra supera la de circulación de una app justo en la participación de "
            "aquellos — nada en Apple, 4 % en NVIDIA, 12 % en Tesla. Llega hasta 2009, la "
            "misma profundidad que en el continente.",
            "- **Una curva de diez años parece haber tocado cero, y no lo hizo.** El eje debe contener el máximo, así que un tramo temprano que vale una décima parte queda a unos pocos píxeles de la base: 853 億 de 五粮液 frente a un máximo de 13.097 億 son menos del siete por ciento de él. Por eso las marcas de mínimo y máximo llevan su cifra: un punto desnudo ahí abajo se lee como cero.",
            "- **La cifra cabalga la línea.** Una etiqueta en el extremo de cada línea "
            "nombra la empresa y da el valor que ha alcanzado en ese momento, y se mueve "
            "con la animación: arrastra la barra y se va con la línea. Con una empresa, "
            "los dos paneles llevan uno cada uno, valor y precio, y la cifra grande sobre "
            "el panel dice el mismo número; con varias, las etiquetas son además lo que "
            "distingue unas líneas de otras.",
            "- Intervalo: uno, dos, cinco o diez años, o dos fechas propias.",
            "Compare varias empresas a la vez. Con más de un chip activo cada una tiene su línea, rotulada en su extremo. Las cotizaciones de varias empresas no comparten un eje de precios honesto — 贵州茅台 junto a 京东方A y una de las dos es una línea plana en el fondo —, así que el panel inferior cede su sitio y todo el marco va al valor de mercado. Hasta seis; una séptima se rechaza en lugar de omitirse en silencio, porque un gráfico hecho con seis de las siete empresas marcadas responde a una lista que nadie eligió.",
            "El eje de valor tiene dos lecturas. El absoluto responde qué empresa vale más; el rebasado a 100 en el primer día de cada una, cuál creció más rápido, y es el único legible cuando una es varias veces la otra. En ambos casos el eje de fechas es la unión de sus días, no la intersección: la intersección recortaría una comparación de diez años al tramo de la que cotizó más tarde.",
        ]),
    "fr": (
        "Historique de la valeur de marché",

        "La valeur de marché en circulation d'une action jour par jour, avec son cours en dessous sur le même axe temporel. Ou plusieurs entreprises à la fois — une courbe chacune, nommée à son extrémité.",
        [
            "- **La valeur est reconstituée, pas citée.** La source n'a de nombre "
            "d'actions historique pour aucun jour. Il vient du taux de rotation, qui est "
            "le volume en fraction des actions en circulation — donc `volume ÷ taux de "
            "rotation` *est* ce nombre, et la valeur est le cours du jour multiplié par lui.",
            "- **Le nombre est une médiane de vingt jours.** Le taux arrive avec deux "
            "décimales : un jour apporte environ un pour cent de bruit, alors que le "
            "nombre d'actions est un escalier — il bouge à une augmentation de capital ou "
            "un rachat et reste plat entre les deux. La médiane laisse la marche au jour "
            "où elle a eu lieu.",
            "- **Seules les actions négociées sur ce marché sont comptées.** Celles que "
            "l'entreprise cote ailleurs sont exclues : une société à double cotation passe "
            "donc sous la « capitalisation totale » des applications de cotation, qui "
            "évalue les actions de l'autre marché au cours de celui-ci. L'écart d'ICBC est "
            "entièrement fait d'actions H. Les actions encore immobilisées sont exclues aussi.",
            "- **À Hong Kong, le prix est une moyenne négociée.** Ce marché ne sert pas "
            "de clôture non ajustée : le prix est le montant divisé par le volume, et le "
            "panneau du bas s'appelle « prix moyen des transactions ».",
            "- **New York divise par toutes les actions, pas par celles qui s'échangent.** "
            "Son taux est une fraction de toutes les actions de la société, y compris "
            "celles des initiés : la courbe est donc une valeur totale et non une valeur "
            "en circulation. Le nombre dépasse la valeur en circulation d'une application "
            "exactement de la part des initiés — rien chez Apple, 4 % chez NVIDIA, 12 % "
            "chez Tesla. Elle remonte jusqu'à 2009, la même profondeur que le continent.",
            "- **Une courbe de dix ans donne l'impression d'être passée par zéro, et ce n'est pas le cas.** L'axe doit contenir le sommet : un segment ancien qui vaut un dixième se tient à quelques pixels de la base — 853 億 pour 五粮液 contre un sommet de 13 097 億, soit moins de sept pour cent de sa hauteur. C'est pourquoi les repères de minimum et de maximum portent leur chiffre : un simple point là-bas se lit comme zéro.",
            "- **Le chiffre chevauche la ligne.** Une étiquette à l'extrémité de chaque "
            "ligne nomme l'entreprise et donne la valeur qu'elle atteint à cet instant, et "
            "elle suit l'animation : faites glisser la barre et elle part avec la ligne. "
            "Avec une entreprise, les deux panneaux en portent une chacun, valeur et "
            "cours, et le grand chiffre au-dessus du panneau dit le même nombre ; avec "
            "plusieurs, les étiquettes sont en plus ce qui distingue les lignes entre "
            "elles.",
            "- Période : un, deux, cinq ou dix ans, ou deux dates à vous.",
            "Comparez plusieurs entreprises à la fois. Avec plus d'une puce cochée, chacune a sa courbe, nommée à son extrémité. Les cours de plusieurs entreprises ne partagent pas d'axe de prix honnête — mettez 贵州茅台 à côté de 京东方A et l'une des deux n'est qu'une ligne plate au ras du bas —, donc le panneau du bas s'efface et tout le cadre va à la valeur de marché. Jusqu'à six ; une septième est refusée plutôt qu'omise en silence, car un graphique fait avec six des sept entreprises cochées répond à une liste que personne n'a choisie.",
            "L'axe des valeurs a deux lectures. L'absolu répond à la question de laquelle vaut le plus ; le rebasement à 100 au premier jour de chacune, à celle qui a le plus progressé, et c'est la seule lisible dès que l'une vaut plusieurs fois l'autre. Dans les deux cas l'axe des dates est l'union de leurs jours, pas l'intersection : l'intersection ramènerait une comparaison de dix ans au seul parcours de la cotation la plus récente.",
        ]),
    "it": (
        "Storia del valore di mercato",

        "Il valore di mercato flottante di un'azione giorno per giorno, con sotto il prezzo sullo stesso asse temporale. Oppure più aziende insieme — una linea ciascuna, nominata all'estremità.",
        [
            "- **Il valore è ricostruito, non quotato.** La fonte non ha un numero "
            "storico di azioni per nessun giorno. Viene dal tasso di rotazione, che è il "
            "volume come frazione delle azioni in circolazione — quindi `volume ÷ tasso di "
            "rotazione` *è* quel numero, e il valore è il prezzo del giorno per esso.",
            "- **Il numero è la mediana di venti giorni.** Il tasso arriva con due "
            "decimali: un giorno porta circa un punto percentuale di rumore, mentre il "
            "numero di azioni è una scala — si muove su un aumento di capitale o un riacquisto "
            "e resta fermo in mezzo. La mediana lascia il gradino nel giorno in cui è avvenuto.",
            "- **Si contano solo le azioni scambiate in questo mercato.** Quelle che la "
            "società quota altrove restano fuori, quindi una società a doppia quotazione "
            "sta sotto la «capitalizzazione totale» mostrata dalle app di quotazioni, che "
            "valuta le azioni dell'altro mercato al prezzo di questo. Il divario di ICBC è "
            "fatto interamente di azioni H. Restano fuori anche le azioni ancora vincolate.",
            "- **A Hong Kong il prezzo è una media degli scambi.** Quel mercato non serve "
            "un closing non rettificato: il prezzo è l'importo diviso il volume, e il "
            "pannello inferiore si chiama «prezzo medio degli scambi».",
            "- **New York divide per tutte le azioni, non per quelle scambiate.** Il suo "
            "tasso è una frazione di tutte le azioni della società, comprese quelle degli "
            "interni, quindi la linea è un valore totale più che uno flottante: il numero "
            "supera la cifra flottante di un'app esattamente della quota degli interni — "
            "nulla in Apple, 4% in NVIDIA, 12% in Tesla. Arriva fino al 2009, la stessa "
            "profondità del continente.",
            "- **Una curva di dieci anni sembra essere passata per zero, e non è così.** L'asse deve contenere il massimo, quindi un tratto iniziale che vale un decimo sta a pochi pixel dalla base: 853 億 di 五粮液 contro un massimo di 13.097 億 sono meno del sette per cento della sua altezza. Per questo i segni di minimo e massimo portano la loro cifra: un punto nudo laggiù si legge come zero.",
            "- **La cifra cavalca la linea.** Un'etichetta sull'estremità di ogni linea "
            "nomina l'azienda e dà il valore che ha raggiunto in quel momento, e si muove "
            "con l'animazione: trascina la barra e se ne va con la linea. Con un'azienda "
            "entrambi i pannelli ne portano una, valore e prezzo, e la cifra grande sopra "
            "il pannello dice lo stesso numero; con più aziende le etichette sono anche "
            "ciò che distingue le linee fra loro.",
            "- Intervallo: uno, due, cinque o dieci anni, oppure due date a scelta.",
            "Confronta più aziende insieme. Con più di un chip attivo ognuna ha la sua linea, nominata all'estremità. I prezzi di più aziende non condividono un asse onesto — 贵州茅台 accanto a 京东方A e una delle due è una linea piatta sul fondo —, quindi il pannello inferiore si fa da parte e tutto il riquadro va al valore di mercato. Fino a sei; la settima è rifiutata invece di essere lasciata fuori in silenzio, perché un grafico fatto con sei delle sette aziende selezionate risponde a un elenco che nessuno ha scelto.",
            "L'asse del valore ha due letture. L'assoluto dice quale azienda vale di più; il ribasamento a 100 sul primo giorno di ciascuna dice quale valore è cresciuto più in fretta, ed è l'unico leggibile quando una vale più volte l'altra. In entrambi i casi l'asse delle date è l'unione dei loro giorni, non l'intersezione: l'intersezione ridurrebbe un confronto di dieci anni al tratto della quotazione più recente.",
        ]),
    "pl": (
        "Historia wartości rynkowej",

        "Wartość rynkowa akcji w obrocie dzień po dniu, a pod nią kurs na tej samej osi czasu. Albo kilka spółek naraz — każda jedną linią, podpisaną na końcu.",
        [
            "- **Wartość jest odtwarzana, nie podawana.** Źródło nie ma historycznej "
            "liczby akcji dla żadnego dnia. Wynika ona ze wskaźnika rotacji, który jest "
            "ułamkiem akcji w obrocie — więc `wolumen ÷ wskaźnik rotacji` *to* ta liczba, "
            "a wartość to kurs dnia razy ona.",
            "- **Liczba to mediana z dwudziestu dni.** Wskaźnik ma dwa miejsca "
            "po przecinku, więc jeden dzień niesie około procentu szumu, podczas gdy "
            "liczba akcji to schody: rusza się przy emisji lub skupie i stoi w miejscu "
            "pomiędzy. Mediana zostawia stopień w dniu, w którym powstał.",
            "- **Liczone są tylko akcje handlowane na tym rynku.** Te, które spółka notuje "
            "gdzie indziej, są pominięte, więc przy podwójnym notowaniu linia jest poniżej "
            "„całkowitej kapitalizacji” z aplikacji z notowaniami — tamte akcje wycenia się "
            "po cenie tego rynku. Różnica w ICBC to w całości akcje H. Pominięte są też "
            "akcje nadal objęte blokadą.",
            "- **W Hongkongu cena to średnia transakcji.** Ten rynek nie daje kursu "
            "zamknięcia bez korekty, więc cena to obrót podzielony przez wolumen, a dolny "
            "panel nazywa się „średnia cena transakcji”.",
            "- **Nowy Jork dzieli przez wszystkie akcje, nie przez te w obrocie.** Jego "
            "wskaźnik jest ułamkiem wszystkich akcji spółki, także należących do osób "
            "związanych, więc linia jest tam wartością całkowitą, nie będącą w obrocie: "
            "liczba przewyższa wartość z aplikacji dokładnie o udział tych osób — w Apple "
            "o zero, w NVIDIA o 4%, w Tesli o 12%. Sięga do 2009 roku, tak samo głęboko "
            "jak w Chinach.",
            "- **Dziesięcioletnia krzywa wygląda, jakby kiedyś spadła do zera — nie spadła.** Oś musi pomieścić szczyt, więc wczesny odcinek wart jedną dziesiątą leży kilka pikseli nad podstawą: 853 億 dla 五粮液 przy szczycie 13 097 億 to poniżej siedmiu procent jego wysokości. Dlatego znaczniki minimum i maksimum podają swoją liczbę: goły punkt tam na dole czyta się jako zero.",
            "- **Liczba jedzie na linii.** Etykieta na końcu każdej linii podaje nazwę "
            "spółki i wartość, jaką osiągnęła w tej chwili, i porusza się razem z "
            "animacją — przeciągnij suwak, a pojedzie z linią. Przy jednej spółce oba "
            "panele mają po jednej etykiecie, wartość i cenę, a duża liczba nad panelem "
            "podaje tę samą liczbę; przy kilku etykiety są też tym, co pozwala odróżnić "
            "linie od siebie.",
            "- Zakres: jeden, dwa, pięć lub dziesięć lat, albo dwie własne daty.",
            "Porównaj kilka spółek naraz. Po zaznaczeniu więcej niż jednego chipa każda dostaje własną linię, podpisaną na końcu. Kursy kilku spółek nie dzielą uczciwie jednej osi cen — postaw 贵州茅台 obok 京东方A, a jedna z nich jest płaską linią przy dolnej krawędzi — więc dolny panel ustępuje i cały kadr należy do wartości rynkowej. Do sześciu; siódma zostaje odrzucona zamiast pominięta po cichu, bo wykres z sześciu spośród siedmiu zaznaczonych spółek odpowiada na listę, której nikt nie wybrał.",
            "Oś wartości ma dwa odczyty. Bezwzględna mówi, która spółka jest warta więcej; przeliczona na 100 w pierwszym dniu każdej z nich — czyja wartość rosła szybciej, i to jest jedyny czytelny odczyt, gdy jedna jest wielokrotnością drugiej. W obu przypadkach oś dat to suma ich dni, nie część wspólna: część wspólna ścięłaby dziesięcioletnie porównanie do okresu najpóźniejszego debiutu.",
        ]),
    "pt-BR": (
        "Histórico de valor de mercado",

        "O valor de mercado em circulação de uma ação dia a dia, com o preço da ação abaixo no mesmo eixo de tempo. Ou várias empresas ao mesmo tempo — uma linha cada, nomeada na ponta.",
        [
            "- **O valor é reconstruído, não citado.** A fonte não tem uma contagem "
            "histórica de ações para nenhum dia. Ela vem da taxa de giro, que é o volume "
            "como fração das ações em circulação — logo `volume ÷ taxa de giro` *é* essa "
            "contagem, e o valor é o preço do dia vezes ela.",
            "- **A contagem é a mediana de vinte dias.** A taxa vem com duas casas "
            "decimais, então um dia traz cerca de um por cento de ruído, enquanto a "
            "contagem de ações é uma escada: move-se numa emissão ou recompra e fica parada "
            "entre elas. A mediana deixa o degrau no dia em que ocorreu.",
            "- **Só entram as ações negociadas neste mercado.** As que a empresa lista em "
            "outro mercado ficam de fora, então uma empresa com dupla listagem fica abaixo "
            "do «valor de mercado total» que um app de cotações mostra — ele precifica as "
            "ações do outro mercado pelo preço deste. A diferença do ICBC são inteiramente "
            "ações H. As ações ainda bloqueadas neste mercado também ficam de fora.",
            "- **Em Hong Kong o preço é uma média negociada.** Esse mercado não serve "
            "fechamento sem ajuste, então o preço é o montante dividido pelo volume, e o "
            "painel inferior se chama «preço médio de negociação».",
            "- **Nova York divide por todas as ações, não pelas negociadas.** Sua taxa é "
            "uma fração de todas as ações da empresa, inclusive as de insiders, então a "
            "linha ali é um valor total, não um valor em circulação: a contagem fica acima "
            "da cifra de circulação de um app exatamente na participação deles — nada na "
            "Apple, 4% na NVIDIA, 12% na Tesla. Vai até 2009, a mesma profundidade do "
            "continente.",
            "- **Uma curva de dez anos parece ter passado por zero, e não passou.** O eixo precisa conter o pico, então um trecho antigo que vale um décimo fica a poucos pixels da base: 853 億 da 五粮液 contra um pico de 13.097 億 são menos de sete por cento da sua altura. Por isso as marcas de mínimo e máximo trazem o próprio número: um ponto nu ali embaixo é lido como zero.",
            "- **O número cavalga a linha.** Um rótulo na ponta de cada linha nomeia a "
            "empresa e dá o valor que ela alcançou naquele momento, e anda junto com a "
            "animação — arraste a barra e ele vai com a linha. Com uma empresa, os dois "
            "painéis levam um cada, valor e preço, e o número grande sobre o painel diz o "
            "mesmo número; com várias, os rótulos são também o que distingue uma linha da "
            "outra.",
            "- Intervalo: um, dois, cinco ou dez anos, ou duas datas próprias.",
            "Compare várias empresas ao mesmo tempo. Com mais de um chip marcado, cada uma ganha uma linha, nomeada na ponta. Os preços de várias empresas não compartilham um eixo de preço honesto — coloque 贵州茅台 ao lado de 京东方A e uma das duas vira uma linha reta no fundo —, então o painel inferior cede lugar e o quadro inteiro vai para o valor de mercado. Até seis; a sétima é recusada em vez de deixada de fora em silêncio, porque um gráfico feito com seis das sete empresas marcadas responde sobre uma lista que ninguém escolheu.",
            "O eixo de valor tem duas leituras. O absoluto responde qual empresa vale mais; o rebaseado em 100 no primeiro dia de cada uma responde qual valor cresceu mais rápido, e é o único legível quando uma vale várias vezes a outra. Nos dois casos o eixo de datas é a união dos dias delas, não a interseção: a interseção encolheria uma comparação de dez anos para o trecho do listing mais recente.",
        ]),
    "cs": (
        "Historie tržní hodnoty",

        "Tržní hodnota jedné akcie v oběhu den po dni a pod ní cena akcie na stejné časové ose. Nebo více firem najednou — každá jednou linií, pojmenovanou na konci.",
        [
            "- **Hodnota je dopočítaná, ne uvedená.** Zdroj nemá historický počet akcií "
            "pro žádný den. Vyplývá z míry obratu, což je objem jako podíl akcií v oběhu "
            "— takže `objem ÷ míra obratu` *je* tento počet a hodnota je denní cena krát "
            "tento počet.",
            "- **Počet je medián dvaceti dnů.** Míra přichází se dvěma desetinnými "
            "místy, takže jeden den nese asi procento šumu, zatímco počet akcií je "
            "schodiště: hýbe se při emisi nebo zpětném odkupu a jinak stojí. Medián "
            "ponechá stupeň na dni, kdy vznikl.",
            "- **Počítají se jen akcie obchodované na tomto trhu.** Ty, které firma kotuje "
            "jinde, zůstávají venku, takže firma kotovaná ve dvou místech leží pod "
            "„celkovou tržní hodnotou” z aplikace s kurzy — tam se ony akcie oceňují cenou "
            "tohoto trhu. Rozdíl u ICBC tvoří výhradně akcie H. Venku jsou i akcie dosud "
            "vázané blokací.",
            "- **V Hongkongu je cena průměrná obchodní.** Tamní trh nedává neupravený "
            "závěr, takže cena je objem peněz dělený objemem akcií a dolní panel se "
            "jmenuje „průměrná obchodní cena“.",
            "- **New York dělí všemi akciemi, ne těmi obchodovanými.** Jeho míra je "
            "podílem všech akcií firmy, včetně akcií zasvěcených osob, takže linie je tam "
            "celkovou hodnotou, ne hodnotou v oběhu: počet převyšuje cifru z aplikace "
            "přesně o podíl těch osob — u Apple o nic, u NVIDIA o 4 %, u Tesly o 12 %. "
            "Dosáhne až do roku 2009, stejně hluboko jako pevnina.",
            "- **Desetiletá křivka vypadá, jako by jednou spadla na nulu — nespadla.** Osa musí pojmout vrchol, takže raný úsek v hodnotě desetiny leží pár pixelů nad základnou: 853 億 u 五粮液 proti vrcholu 13 097 億 je méně než sedm procent jeho výšky. Proto značky minima a maxima nesou vlastní číslo: holý bod tam dole se čte jako nula.",
            "- **Číslo jede po čáře.** Štítek na konci každé čáry pojmenuje firmu a "
            "ukáže hodnotu, které v tu chvíli dosáhla, a pohybuje se s animací — posuňte "
            "jezdec a pojede s čárou. U jedné firmy má každý panel jeden, hodnotu a cenu, "
            "a velké číslo nad panelem říká totéž číslo; u několika jsou štítky zároveň "
            "tím, co od sebe čáry rozezná.",
            "- Rozsah: jeden, dva, pět nebo deset let, anebo dvě vlastní data.",
            "Porovnejte více firem najednou. Při více než jednom zapnutém čipu má každá svou linii, pojmenovanou na konci. Ceny více firem nesdílejí poctivou cenovou osu — dejte 贵州茅台 vedle 京东方A a jedna z nich je plochá čára u spodního okraje —, takže dolní panel ustoupí a celý rám patří tržní hodnotě. Až šest; sedmá je odmítnuta, ne potichu vynechána, protože graf ze šesti ze sedmi zaškrtnutých firem odpovídá na seznam, který nikdo nevybral.",
            "Osa hodnoty má dva výklady. Absolutní říká, která firma má větší hodnotu; přepočtená na 100 v první den každé z nich říká, čí hodnota rostla rychleji, a je to jediný čitelný výklad, když je jedna násobkem druhé. V obou případech je osou dat sjednocení jejich dnů, ne průnik: průnik by zkrátil desetileté srovnání na úsek toho, kdo na burzu vstoupil nejpozději.",
        ]),
    "tr": (
        "Piyasa değeri geçmişi",

        "Bir hissenin dolaşımdaki piyasa değeri gün gün, altında aynı zaman ekseninde fiyatı. Ya da aynı anda birden çok şirket — her biri ucunda adı yazan bir çizgi.",
        [
            "- **Değer kaynaktan alınmaz, geri çıkarılır.** Kaynağın hiçbir güne ait "
            "geçmiş hisse sayısı yok. Sayı devir oranından gelir — devir oranı hacmin "
            "dolaşımdaki hisselere oranıdır — yani `hacim ÷ devir oranı` doğrudan bu "
            "sayıdır ve değer, günün fiyatının bu sayıyla çarpımıdır.",
            "- **Sayı yirmi günlük medyandır.** Oran iki ondalıkla gelir, yani bir gün "
            "yaklaşık yüzde bir gürültü taşır; oysa hisse sayısı bir merdivendir: "
            "sermaye artırımında veya geri alımda sıçrar, arada sabittir. Medyan basamağı "
            "olduğu günde bırakır.",
            "- **Yalnızca bu piyasada işlem gören hisseler sayılır.** Şirketin başka bir "
            "piyasada listelediği hisseler dahil edilmez, bu yüzden iki yerde listelenen "
            "bir şirket, fiyat uygulamasının gösterdiği «toplam piyasa değeri»nin altında "
            "kalır; o değer diğer piyasanın hisselerini bu piyasanın fiyatıyla hesaplar. "
            "ICBC'nin farkı tamamen H hisselerinden oluşur. Bu piyasada hâlâ bloke olan "
            "hisseler de dahil değildir.",
            "- **Hong Kong'da fiyat ortalama işlem fiyatıdır.** O piyasada düzeltilmemiş "
            "kapanış yoktur, bu yüzden fiyat tutarın hacme bölümüdür ve alt panel "
            "«ortalama işlem fiyatı» olarak adlandırılır.",
            "- **New York, işlem görenlerle değil tüm hisselerle böler.** Oranı şirketin "
            "sahip olduğu tüm hisselerin, içeridekiler dahil, bir kesri olduğu için oradaki "
            "çizgi dolaşımdaki değer değil toplam değerdir: sayı, bir fiyat uygulamasının "
            "dolaşımdaki değerini tam olarak içeridekilerin payı kadar aşar — Apple'da "
            "sıfır, NVIDIA'da %4, Tesla'da %12. 2009'a kadar uzanır; anakara kadar derin.",
            "- **On yıllık bir eğri bir zamanlar sıfıra inmiş gibi okunur — inmemiştir.** Eksen zirveyi almak zorunda olduğundan, zirvenin onda biri değerindeki erken bir bölüm tabanın birkaç piksel üstünde kalır: 五粮液'nin 853 億'si 13.097 億 zirveye karşı panelin yüzde yedisinden az eder. Bu yüzden en düşük ve en yüksek işaretleri kendi sayısını yazar: oradaki çıplak bir nokta sıfır olarak okunur.",
            "- **Sayı çizgiyle birlikte gider.** Her çizginin ucundaki etiket şirketi "
            "adlandırır ve o anda ulaştığı değeri verir; animasyonla birlikte hareket "
            "eder — çubuğu çekin, çizgiyle birlikte gider. Tek şirkette iki panelin de "
            "birer etiketi olur, değer ve fiyat, panelin üstündeki büyük sayı ise aynı "
            "sayıyı söyler; birkaç şirkette etiketler ayrıca çizgileri birbirinden ayıran "
            "şeydir.",
            "- Aralık: bir, iki, beş veya on yıl, ya da iki kendi tarihiniz.",
            "Birden çok şirketi aynı anda karşılaştırın. Birden fazla çip açıkken her biri ucunda adı yazan bir çizgi alır. Birden çok şirketin fiyatı dürüst bir fiyat eksenini paylaşmaz — 贵州茅台'yı 京东方A'nın yanına koyun, ikisinden biri dipte düz bir çizgi olur — bu yüzden alt panel geri çekilir ve çerçevenin tamamı piyasa değerine kalır. En fazla altı; yedincisi sessizce atılmak yerine reddedilir, çünkü işaretlenen yedi şirketten altısıyla çizilen grafik kimsenin seçmediği bir listeyi yanıtlar.",
            "Değer ekseninin iki okuması var. Mutlak olan hangi şirketin daha değerli olduğunu; her birinin kendi ilk gününde 100'e indirgenmiş olan kimin değeri daha hızlı büyüdüğünü söyler ve biri diğerinin katları olduğunda okunabilen tek görünüm budur. İkisinde de tarih ekseni günlerin kesişimi değil birleşimidir: kesişim on yıllık bir karşılaştırmayı en son işlem görmeye başlayan şirketin aralığına indirger.",
        ]),
    "ru": (
        "История капитализации",

        "Капитализация одной акции в обращении день за днём, а под ней — цена акции на той же временной оси. Либо несколько компаний сразу — по одной линии на каждую, с подписью на конце.",
        [
            "- **Значение восстанавливается, а не берётся из источника.** У источника нет "
            "исторического числа акций ни для одного дня. Оно следует из оборачиваемости, "
            "которая есть объём как доля акций в обращении — поэтому `объём ÷ "
            "оборачиваемость` и *есть* это число, а значение — цена дня, умноженная на него.",
            "- **Число — медиана двадцати дней.** Оборачиваемость приходит с двумя "
            "знаками после запятой, поэтому один день несёт около процента шума, тогда как "
            "число акций — лестница: оно меняется при размещении или выкупе и стоит между "
            "ними. Медиана оставляет ступень на том дне, когда она появилась.",
            "- **Учитываются только акции, которыми торгуют на этом рынке.** Акции, "
            "размещённые компанией где-то ещё, исключены, поэтому у компании с двойным "
            "листингом линия идёт ниже «общей капитализации» из котировального приложения: "
            "там те акции оценивают по цене этого рынка. Разрыв у ICBC — целиком акции H. "
            "Не входят и акции, всё ещё закрытые на этом рынке.",
            "- **В Гонконге цена — средняя по сделкам.** Там нет нескорректированного "
            "закрытия, поэтому цена — это сумма, делённая на объём, и нижняя панель "
            "называется «средняя цена сделки».",
            "- **Нью-Йорк делит на все акции, а не на торгуемые.** Его оборачиваемость — "
            "доля всех акций компании, включая акции инсайдеров, поэтому линия там — "
            "полная стоимость, а не стоимость в обращении: число превышает показатель "
            "приложения ровно на долю инсайдеров — ноль у Apple, 4% у NVIDIA, 12% у Tesla. "
            "Вглубь — до 2009 года, та же глубина, что и на материке.",
            "- **Десятилетняя кривая читается так, будто она когда-то падала до нуля, — а это не так.** Ось должна вместить пик, поэтому ранний участок в десятую его часть лежит в нескольких пикселях от основания: 853 億 у 五粮液 против пика 13 097 億 — это менее семи процентов её высоты. Поэтому отметки минимума и максимума печатают своё число: голый кружок там внизу читается как ноль.",
            "- **Число едет по линии.** Ярлык у конца каждой линии называет компанию и "
            "показывает, какой стоимости она достигла на этот момент, и движется вместе с "
            "анимацией: потяните ползунок — и он поедет вместе с линией. При одной "
            "компании по одному ярлыку несут обе панели, стоимость и цена, и крупное "
            "число над панелью называет то же самое число; при нескольких ярлыки — это "
            "ещё и то, чем линии различаются.",
            "- Диапазон: один, два, пять или десять лет, либо две свои даты.",
            "Сравните несколько компаний сразу. При нескольких включённых чипах у каждой своя линия с подписью на конце. Цены нескольких компаний не делят честную ценовую ось — поставьте 贵州茅台 рядом с 京东方A, и одна из них окажется плоской линией у дна, — поэтому нижняя панель уступает место и весь кадр отдаётся капитализации. До шести; седьмая отклоняется, а не выбрасывается молча, потому что график из шести из семи отмеченных компаний отвечает на список, которого никто не выбирал.",
            "У оси значений два прочтения. Абсолютное отвечает, какая компания стоит больше; приведённая к 100 на первый день каждой — чья капитализация росла быстрее, и это единственное читаемое прочтение, когда одна во много раз больше другой. В обоих случаях ось дат — объединение их дней, а не пересечение: пересечение свело бы десятилетнее сравнение к отрезку самого позднего листинга.",
        ]),
    "ja": (
        "時価総額の推移",

        "ある銘柄の流通時価総額を日ごとに、同じ時間軸の下に株価を添えて。複数社を同時に、その末端へ名前を付けた線にすることもできます。",
        [
            "- **時価総額は取り出して計算した値です。** ソースはどの日についても過去の"
            "株式数を持っていません。株式数は回転率から逆算します——回転率は出来高の"
            "流通株式に対する割合なので、「出来高 ÷ 回転率」がそのまま流通株式数になり、"
            "時価総額はその日の価格にこの数を掛けたものです。",
            "- **株式数は二十日間の中央値です。** 回転率は小数二桁で返るため、一日の値には"
            "一％前後のノイズが乗ります。一方で株式数は階段で、増資や自社株買いの日に"
            "だけ動き、あとは動きません。中央値はその段を、起きた日の位置に残します。",
            "- **数えるのはこの市場で取引される株式だけです。** この会社が別の市場に"
            "上場している株式は含めないため、二重上場の会社は相場アプリが示す"
            "『総時価総額』より下に来ます——あちらは別市場の株式をこの市場の価格で"
            "換算しているからです。工商銀行の差はすべて H 株です。この市場でまだ"
            "ロックアップされている株式も含まれません。",
            "- **香港の価格は平均売買価格です。** この市場は不复元の終値を返さないため、"
            "価格は売買代金を出来高で割ったものになり、下のパネルは「平均売買価格」と"
            "表記されます。",
            "- **ニューヨークは取引される株ではなく全株式で割ります。** 回転率は会社が"
            "持つ全株式（内部者の分を含む）に対する割合なので、あちらの線は流通時価総額"
            "ではなく総時価総額になります。アプリの流通値を上回る分はちょうど内部者の"
            "持ち分——アップルでゼロ、エヌビディアで 4%、テスラで 12%。遡れるのは"
            "2009 年までで、本土と同じ深さです。",
            "- **十年の曲線は、途中でゼロになったように見えますが、なっていません。** 軸は最高値を収める必要があるため、その十分の一しかない初期の区間は底辺から数ピクセルしか離れません——五粮液の 853 億 は 13,097 億 の最高値に対してその高さの七パーセントに過ぎません。だからこそ最低・最高の印は値そのものを書きます。そこにあるただの点はゼロと読まれてしまうからです。",
            "- **数字は線に乗って動きます。** 各線の先端にラベルが付き、会社名とその時点で到達した価値を示し、アニメーションと一緒に動きます——スライダーを動かせば線とともに移動します。1 社のときは上下両方のパネルに一つずつ付き（価値と株価）、パネルの上の大きな数字は同じ値を示します。複数のときは、このラベルがどの線がどの会社かを見分ける手掛かりにもなります。",
            "- 期間は 1 年、2 年、5 年、10 年、または自分で指定した二つの日付。",
            "複数社を同時に比較できます。チップを二つ以上オンにすると、それぞれ末端に名前の付いた線になります。複数社の株価は正直な価格軸を共有できません——贵州茅台 と 京东方A を並べれば、どちらかは底辺の平らな線になります——だから下の価格パネルは退き、枠のすべてが時価総額に使われます。最大六社。七社目は黙って捨てられるのではなく拒否されます。七社選んだ人のうち六社だけの絵は、誰も選んでいない一覧に答える絵になってしまうからです。",
            "目盛りには二つの読み方があります。絶対値はどちらが大きいかを、各家の初日を 100 とした基準はどちらが速く伸びたかを答え、一方が他方の何倍もあるときに読めるのは後者だけです。どちらの場合も日付軸は共通部分ではなく和集合です。共通部分にすると、十年の比較が最後に上場した銘柄の期間に切り詰められます。",
        ]),
    "ko": (
        "시가총액 추이",

        "한 종목의 유통 시가총액을 날짜별로, 같은 시간축 아래에 주가를 함께. 또는 여러 기업을 한 번에 —— 끝에 이름이 붙은 선 하나씩으로도 볼 수 있습니다.",
        [
            "- **시가총액은 인용되는 값이 아니라 되찾은 값입니다.** 출처에는 어느 날의 "
            "과거 주식 수도 없습니다. 주식 수는 회전율에서 역산합니다——회전율은 유통 "
            "주식 대비 거래량의 비율이므로, 「거래량 ÷ 회전율」이 곧 유통 주식 수이고, "
            "시가총액은 당일 가격에 그 수를 곱한 값입니다.",
            "- **주식 수는 20일 중간값입니다.** 회전율이 소수 둘째 자리로 오므로 하루 "
            "값에는 1% 안팎의 노이즈가 붙습니다. 반면 주식 수는 계단이라, 증자나 "
            "자사주 매입이 있는 날만 움직이고 그 사이에는 그대로입니다. 중간값은 그 단을 "
            "일어난 날에 남겨 둡니다.",
            "- **이 시장에서 거래되는 주식만 셉니다.** 회사가 다른 시장에 상장한 주식은 "
            "빼므로, 이중 상장 기업은 시세 앱이 보여주는 '총 시가총액'보다 아래에 "
            "옵니다. 그 값은 다른 시장의 주식을 이 시장 가격으로 환산하기 때문입니다. "
            "공상은행의 차이는 전부 H주입니다. 이 시장에서 아직 보호예수된 주식도 "
            "들어가지 않습니다.",
            "- **홍콩의 가격은 평균 거래가입니다.** 그 시장은 조정되지 않은 종가를 주지 "
            "않으므로 가격은 거래대금을 거래량으로 나눈 값이고, 아래 패널은 "
            "「평균 거래가」로 표기됩니다.",
            "- **뉴욕은 거래되는 주식이 아니라 전체 주식으로 나눕니다.** 회전율이 내부자 "
            "지분을 포함한 전체 주식에 대한 비율이라서, 그쪽 선은 유통 시가총액이 아니라 "
            "총 시가총액입니다. 앱의 유통 값을 넘는 만큼이 바로 내부자 지분——애플은 "
            "0%, 엔비디아 4%, 테슬라 12%. 2009년까지 거슬러 올라가며, 본토와 같은 깊이입니다.",
            "- **10년 곡선은 중간에 0까지 내려간 것처럼 읽히지만, 그렇지 않습니다.** 축이 최고점을 담아야 하므로, 그 10분의 1에 불과한 초기 구간은 바닥에서 몇 픽셀밖에 떨어지지 않습니다. 五粮液의 853 億은 13,097 億 최고점에 대해 패널 높이의 7퍼센트가 되지 않습니다. 그래서 최저·최고 표시가 값을 함께 씁니다. 거기 있는 민점은 0으로 읽히기 때문입니다.",
            "- **숫자는 선을 따라 움직입니다.** 각 선 끝에 라벨이 붙어 회사 이름과 그 시점에 도달한 가치를 보여주고, 애니메이션과 함께 움직입니다 — 슬라이더를 끌면 선과 같이 갑니다. 회사가 하나일 때는 위아래 두 패널에 각각 하나씩 붙고(가치와 주가), 패널 위의 큰 숫자는 같은 값을 말합니다. 여러 회사일 때는 이 라벨이 선들을 서로 구분하는 유일한 단서이기도 합니다.",
            "- 기간: 1년, 2년, 5년, 10년 또는 직접 지정한 두 날짜.",
            "여러 기업을 동시에 비교하세요. 칩을 두 개 이상 켜면 각각 끝에 이름이 붙은 선이 됩니다. 여러 기업의 주가는 정직한 가격 축을 공유할 수 없습니다——贵州茅台 옆에 京东方A를 놓으면 둘 중 하나는 바닥의 평평한 선이 됩니다——그래서 아래 가격 패널은 물러나고 프레임 전체가 시가총액에 쓰입니다. 최대 6개. 7번째는 조용히 빠지는 것이 아니라 거부됩니다. 일곱 개를 고른 사람의 여섯 개만 그린 그림은 아무도 고르지 않은 목록에 답하는 그림이 됩니다.",
            "값 축에는 두 가지 읽기가 있습니다. 절댓값은 어느 기업이 더 큰지를, 각자의 첫날을 100으로 한 기준은 누가 더 빨리 컸는지를 답하며, 한쪽이 다른 쪽의 몇 배일 때 읽히는 것은 후자뿐입니다. 두 경우 모두 날짜 축은 교집합이 아니라 합집합입니다. 교집합이면 10년 비교가 가장 늦게 상장한 종목의 기간으로 잘립니다.",
        ]),
    "zh-Hant": (
        "市值歷程",

        "一檔股票流通市值逐日的曲線，下方同一時間軸上是它的股價。也可以同時畫幾家公司，各一條線、在末端標出名字。",
        [
            "- **市值是還原出來的，不是行情源給的**：行情源沒有任何一天的歷史股本。股本由"
            "換手率反推——換手率就是成交量占流通股本的比例，所以「成交量 ÷ 換手率」就是"
            "流通股本，市值等於當日價格乘以這個股本。",
            "- **股本取二十日中位數**：換手率只給兩位小數，單日反推有百分之一上下的雜訊；"
            "而股本是階梯，只在增發或回購那天跳一次，其餘時間不動。取中位數壓掉雜訊，"
            "台階留在它發生的那天。",
            "- **圖上只算本市場可交易的股票**：不含這家公司在其它市場的股票，所以兩地上市"
            "的公司會低於行情軟體的「總市值」——後者把其它市場的股票按本市場價格折進來。"
            "工商銀行差的三成全是它的 H 股。本市場尚未解禁的限售股也不在圖上。",
            "- **港股的那條線是成交均價**：那個市場拿不到不復權收盤價，只能取成交額除以"
            "成交量，所以下面那一欄標的是「成交均價」而不是「股價」。",
            "- **美股那一條是總市值**：它的換手率是「全部股本」的比例，內部人持股也算在內，"
            "不像內地與香港只算流通股本。所以它比行情軟體的流通市值高出一截，高的正好是"
            "內部人持股——蘋果 0%、輝達 4%、特斯拉 12%。能回溯到 2009 年，和 A 股一樣深。",
            "- **十年的曲線看起來像跌到過 0，其實沒有。** 縱軸要裝下最高點，所以只值它十分之一的早年那一段，離底邊只有幾個像素——五糧液最低 853 億、最高 13,097 億，前者不到面板高度的百分之七。最低與最高因此都寫出自己的數值：只畫一個圓點在那裡，會被讀成 0。",
            "- **曲線末端跟著數字**：每條線的線頭上是一個標籤，寫著公司名字和它此刻到達的數值，隨動畫一起走——拖動進度條，它跟著線走。只有一隻時上下兩塊面板各掛一個（市值與股價），面板上方那個大數字說的是同一個數；幾隻時，這些標籤也是分辨哪條線是哪一家的唯一線索。",
            "- 區間可選 1 年、2 年、5 年、10 年，或自己填起止日期。",
            "**可以同時畫幾家公司**：勾選兩個以上，各畫一條線、在末端標出名字。幾家公司的股價沒有一套共用的刻度——贵州茅台 的 1,258 元旁邊放 京东方A 的 4.2 元，後者是貼著底邊的一條直線——所以下方的股價面板讓出來，整幅畫面都給市值。最多六家，第七家是拒絕而不是悄悄略過：七家裡只畫六家，答的是一份沒人選過的清單。",
            "**市值刻度有兩種讀法**：絕對值答的是「誰更大」，各家以自己的首日折到 100 答的是「誰漲得更快」——當一家比另一家大好幾倍，絕對值畫面裡小的那條就是貼底的直線，讀得出來的只有第二種。兩種讀法下日期軸都取**聯集**而不是交集：取交集會把十年的比較砍到最年輕那家上市以來的時間。",
        ]),
    "zh-Hans": (
        "市值历程",

        "一只股票流通市值逐日的曲线，下方同一时间轴上是它的股价。也可以同时画几家公司，各一条线、在末端标出名字。",
        [
            "- **市值是还原出来的，不是行情源给的**：行情源没有任何一天的历史股本。股本由"
            "换手率反推——换手率就是成交量占流通股本的比例，所以「成交量 ÷ 换手率」就是"
            "流通股本，市值等于当日价格乘以这个股本。",
            "- **股本取二十日中位数**：换手率只给两位小数，单日反推有百分之一上下的噪声；"
            "而股本是阶梯，只在增发或回购那天跳一次，其余时间不动。取中位数压掉噪声，"
            "台阶留在它发生的那天。",
            "- **图上只算本市场可交易的股票**：不含这家公司在其它市场的股票，所以两地上市"
            "的公司会低于行情软件的「总市值」——后者把其它市场的股票按本市场价格折进来。"
            "工商银行差的三成全是它的 H 股。本市场尚未解禁的限售股也不在图上。",
            "- **港股的那条线是成交均价**：那个市场拿不到不复权收盘价，只能取成交额除以"
            "成交量，所以下面那一栏标的是「成交均价」而不是「股价」。",
            "- **美股那一条是总市值**：它的换手率是「全部股本」的比例，内部人持股也算在内，"
            "不像内地与香港只算流通股本。所以它比行情软件的流通市值高出一截，高的正好是"
            "内部人持股——苹果 0%、英伟达 4%、特斯拉 12%。能回溯到 2009 年，和 A 股一样深。",
            "- **十年的曲线看起来像跌到过 0，其实没有。** 纵轴要装下最高点，所以只值它十分之一的早年那一段，离底边只有几个像素——五粮液最低 853 亿、最高 13,097 亿，前者不到面板高度的百分之七。最低与最高因此都写出自己的数值：只画一个圆点在那里，会被读成 0。",
            "- **曲线末端跟着数字**：每条线的线头上是一个标签，写着公司名字和它此刻到达的数值，随动画一起走——拖动进度条，它跟着线走。只有一只时上下两块面板各挂一个（市值与股价），面板上方那个大数字说的是同一个数；几只时，这些标签也是分辨哪条线是哪一家的唯一线索。",
            "- 区间可选 1 年、2 年、5 年、10 年，或自己填起止日期。",
            "**可以同时画几家公司**：勾选两个以上，各画一条线、在末端标出名字。几家公司的股价没有一套共用的刻度——贵州茅台 的 1,258 元旁边放 京东方A 的 4.2 元，后者是贴着底边的一条直线——所以下方的股价面板让出来，整幅画面都给市值。最多六家，第七家是拒绝而不是悄悄略过：七家里只画六家，答的是一份没人选过的清单。",
            "**市值刻度有两种读法**：绝对值答的是「谁更大」，各家以自己的首日折到 100 答的是「谁涨得更快」——当一家比另一家大好几倍，绝对值画面里小的那条就是贴底的直线，读得出来的只有第二种。两种读法下日期轴都取**并集**而不是交集：取交集会把十年的比较砍到最年轻那家上市以来的时间。",
        ]),
}


def main():
    # 问导航，不数行：章节顺序就是导航顺序，而插进一章会让它后面每一章整体后移。
    saved = sys.argv
    sys.argv = [sys.argv[0]]

    try:
        at = listingtext.chapter_of(NAV_KEY)
    finally:
        sys.argv = saved

    for tag in LANGS:
        title, summary, bullets = CHAPTERS[tag]
        path = HELP / f"help-{tag}.md"

        text = path.read_bytes().decode("utf-8-sig").lstrip("﻿")

        if not text.endswith("\n"):
            text += "\n"

        parts = re.split(r"(?m)^## ", text)
        head = parts[0]
        chapters = parts[1:]

        assert at <= len(chapters), f"{tag}: 只有 {len(chapters)} 章，插不进第 {at} 章"

        body = f"{title}\n\n{summary}\n\n" + "\n\n".join(bullets) + "\n\n\n\n"

        # 幂等：那个位置上已经是这一章就整段替换，否则插入。比标题，因为标题是这一章
        # 在这一门语言里唯一的记号，而位置本身在别处插入一章之后会指到别人身上。
        if at < len(chapters) and chapters[at].split("\n", 1)[0].strip() == title:
            chapters[at] = body
            done = "替换"
        else:
            chapters.insert(at, body)
            done = "插入"

        text = head + "".join("## " + c for c in chapters)

        path.write_bytes(text.encode("utf-8"))

        print(f"{tag}: 第 {at + 1} 章 {done} —— {title}")


if __name__ == "__main__":
    main()
