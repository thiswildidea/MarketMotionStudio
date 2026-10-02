# Market Motion Studio

Diese App macht aus Kennzahlen des A-Aktien-Markts hochformatige Videos für das Telefon. Sie wählen einen Zeitraum, betrachten die Vorschau, bis sie sich gut liest, und exportieren eine MP4-Datei. Mehr muss nicht installiert werden.

## Markt auswählen

In den Einstellungen wird gewählt, aus welchem Markt die App ihre Kurse bezieht; voreingestellt sind A-Aktien. Eine Änderung gilt nach dem Neustart der App.

- **A-Aktien**: alle acht Seiten sind verfügbar.
- **Hongkong**: Renditematrix und Gewinn-Verlust-Kalender funktionieren; das Sektor-Rennen läuft über die vier Hang-Seng-Subindizes; **eine Umsatzzahl für den Gesamtmarkt gibt es nicht, diese Seite wird ausgeblendet**.
- **USA**: Renditematrix und Gewinn-Verlust-Kalender funktionieren; das Sektor-Rennen läuft über zehn SPDR-Sektor-ETFs; die Volumenseite behält nur den Tagesmodus, weil der Minuten-Endpunkt keine US-Daten liefert; **Umsätze werden in Dollar angegeben, und die Seite für den Gesamtmarktumsatz ist ausgeblendet**.



## Zwischen Seiten wechseln

Die beiden Schaltflächen links in der Titelleiste gehen durch die besuchten Seiten zurück und vor, wie ein Browser es tut — **Alt+Pfeil links** und **Alt+Pfeil rechts** oder die Seitentasten der Maus.

- Eine Seite bleibt, wie du sie verlassen hast: Zurückgehen führt zur gewählten Spanne und zur Vorschau in genau dem Zustand, nicht zu einer neu geöffneten Seite.
- Wie im Browser löscht das Anwählen einer neuen Seite, was vor dir lag.
- Sie funktionieren auch bei eingeklapptem Navigationsbereich, und genau dann braucht die Vorschau die Breite am meisten.

## Marktumsatz

Der tägliche Umsatz des gesamten Markts: die Beträge der Composite-Indizes von Shanghai und Shenzhen addiert, ein Balken pro Handelstag.

- Es bleiben nur Tage, an denen alle einbezogenen Märkte gehandelt haben. So kann der Feiertag eines einzelnen Markts die Summe nicht scheinbar einbrechen lassen.
- Ein noch laufender Handelstag wird ausgelassen. Ein unfertiger Tag enthält nur seine Eröffnungsauktion und würde als Balken direkt auf der Achse erscheinen.
- Oder ein Segment allein betrachten: jede der Börsen, jeden Hauptmarkt, STAR, ChiNext. Hauptmärkte werden als Börsenwert minus Wachstumssegment hergeleitet; der BSE 50 bleibt eine Kennzahl der Indexmitglieder.
- Nur der A-Aktienmarkt liefert eine Summe für den ganzen Markt. Bei Hongkong oder USA wird die Seite aus der Navigation entfernt.

## Kerzenchart

Die Kerzen eines Instruments: täglich, wöchentlich oder monatlich, auf vier Arten gezeichnet, mit Durchschnitten und Volumen darunter.

- **Intervall** entscheidet, wie viel Marktzeit eine Kerze abdeckt — ein Tag, eine Woche oder ein Monat. Eine Änderung lädt neu, denn die drei sind auf der Quelle getrennte Reihen.
- **Darstellung** entscheidet, wie dieselben vier Preise gezeichnet werden: Kerzen, OHLC-Balken, Schlusskurslinie oder Schlusskursfläche. Umschalten lädt nichts neu.
- **Ablauf** ist entweder das Eintreffen der Kerzen nacheinander, bis der ganze Zeitraum steht, oder ein festes Fenster, das weiterwandert. Das zweite hält die Kerze auf einem langen Zeitraum breit genug zum Lesen, und wie breit ist die Einstellung **Fenster**.
- Gleitende Durchschnitte MA5, MA10 und MA20 können über die Kerzen gelegt werden; das Volumenfeld darunter lässt sich abschalten, und das Preisfeld nimmt den Platz zurück.
- Eine noch laufende Woche oder ein laufender Monat bleibt draußen. Eine Kerze aus drei Tagen ist keine Woche.
- Jeder Markt wird auf seiner bereinigten Reihe gelesen, damit ein Split-Tag nicht als Rückgang erscheint und eine Dividende auch nicht.

## Volumen und Umschlag

Volumen und Umschlagsrate eines Titels, in zwei übereinanderliegenden Feldern.

- Über Handelstage hinweg sind Volumen und Umschlagsrate proportional, die beiden Felder haben also fast dieselbe Form. Innerhalb eines Tages sehen Minutenvolumen und kumulierte Umschlagsrate wirklich unterschiedlich aus, und das ist das interessantere Bild.
- Die Intraday-Quelle hält nur die letzten Handelstage, daher bietet dieser Modus diese Tage an und kein beliebiges Datum.
- Minutendaten gibt es nur für A-Aktien und Hongkong; in den USA wird dieser Modus nicht angeboten.

## Sektor-Rennen

![Die Seite im Ganzen: Vorschau links, Zeitleiste darunter, Einstellungen rechts.](media/sector-race.png)

Eine Gruppe von Sektoren oder Aktien als waagerechte Balken, die einander überholen, die Reihenfolge ändert sich bis zum letzten Bild.

- Zwei Maße: die Prozentveränderung des Zeitraums und sein Umsatz in Hunderten Millionen Yuan. Das Maß zu wechseln färbt nur dieselben Daten neu ein, es wird nicht neu geladen.
- Vier Listen: Shenwan-Ebene-1-Branchen, beliebte Themen, benutzerdefiniert (ankreuzen) und Einzelaktien (per Suche hinzufügen). Die benutzerdefinierte Liste beginnt mit den Shenwan-Ebene-1-Branchen gefüllt.
- Die eingebauten Listen folgen dem Markt: Shenwan-Ebene-1-Branchen und beliebte Themen bei A-Aktien, die vier Hang-Seng-Subindizes bei Hongkong, zehn SPDR-Sektor-ETFs bei den USA. Die benutzerdefinierte Liste und die Aktienliste gibt es auf jedem Markt.
- Der Zeitraum kann 1, 3, 6 oder 12 Monate betragen oder frei mit Start- und Enddatum gewählt werden.
- Eine Liste hat eine Mindest- und Höchstzahl an Einträgen — zu wenige Balken sind kein Rennen, zu viele ein Wirrwarr.




## Marktkapitalisierungs-Rennen

Die fünfzehn größten Unternehmen eines Marktes als waagerechte Balken nach Marktkapitalisierung —
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





## A/H-Prämie

Wie viel teurer die Festlandnotierung eines Unternehmens ist als seine Hongkonger — für die
Firmen, die auf beiden Seiten notieren, Monat für Monat als Balken, die sich überholen.

- **Prämie = A-Kurs ÷ (H-Kurs × HKD/CNY) − 1.** Nichts davon ist abgeleitet: beide Seiten sind
  tatsächlich gezahlte Kurse zum selben Zeitpunkt, weshalb diese Seite als einzige
  **unbereinigte** Kurse holt. Eine rückwärts bereinigte Reihe bläht junge Kurse auf, und zwei
  getrennt bereinigte Märkte sind nicht vergleichbar — ICBCs A-Aktie steht mit 8,28 auf dem
  Schirm, die bereinigte Reihe meldet 13,34, und aus +26 % Prämie werden +245 %.
- **Dieselbe Lücke wird in zwei Richtungen geschrieben.** Diese Seite nennt A gegen H, wie es üblich
  ist: +194 % heißt, die Festlandaktie kostet fast dreimal so viel wie die Hongkonger. Manche
  Dienste nennen dieselbe Zahl umgekehrt (溢价(H/A)) und zeigen für 新华制药 am selben Tag −66 %.
  Das ist dieselbe Tatsache (1 ÷ (1 − 0,66) − 1 = 1,94) — kein anderer Kurs und kein Rechenfehler.
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

## Extreme Tage

Ein Instrument und die Tage, an denen es sich am stärksten bewegt hat — waagrechte Balken,
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

## Währungskorridore

Eine Zeile je Paar, und **die Zeile ist der Korridor selbst**: ein Ende ist der billigste Stand,
den das Paar in der gewählten Spanne hatte, das andere der teuerste, und die Markierung ist der Kurs
von heute. Dieses Tableau ist also anders als die anderen — anderswo ist die Länge eines Balkens
*wieviel*, hier füllt die Zeile in jedem Bild die ganze Breite, und es bewegen sich die Markierung
und der Korridor um sie herum.

- **Der Korridor weitet sich.** Seine Wände sind das bisherige Tief und das bisherige Hoch, nicht
  die der ganzen Spanne. Ein Monat, der weiter geht als jeder Monat zuvor, drückt eine der beiden
  nach außen, und ein Paar bei 100% ist so teuer wie nie zuvor — nicht an einer Grenze.
- **Jedes Paar wird an der eigenen Spanne gemessen.** 157,92 bei USD/JPY und 1,1245 bei EUR/USD
  sind keine zwei Punkte auf einer Skala; erst die Normierung lässt sechs Paare auf einem Bild
  stehen. Der Preis dafür: ein enger und ein weiter Korridor sehen gleich aus — darum stehen beide
  Enden unter jeder Zeile.
- **Monatskerzen, nicht bereinigt.** Eine Währung hat keine Dividende und keinen Split, und die Seite
  nimmt denselben unbereinigten Weg durch die Quelle den die A+H-Seite nimmt.
- **Die Reichweite ist unterschiedlich, darum sind es zwei Listen**: USD/CNY reicht bis 2005, die
  anderen fünf Renminbi-Paare bis 2016; die wichtigen Crosses beginnen alle 2005-07 und tragen 325
  Monate. Auf einem Tableau zusammen läse man, wann die Quelle welches Paar zu notieren begann.
- **Die Markteinstellung gilt hier nicht**: ein Währungspaar gehört zu keiner Börse, und das Tableau
  ist dasselbe, welcher Markt auch gilt.
- Die längste Spanne ist etwa zwanzig Jahre — die Reichweite der Monatsreihe der Quelle. Weniger als
  zwölf Monate werden abgelehnt: das sind ein paar Wochen Bewegung, kein Korridor.

## Index-Rennen

Eine Zeile je Index, und die Zeile ist **wie weit dieser Index seit seinem eigenen ersten Monat
im Zeitraum gekommen ist** — nicht sein Niveau. 3.800 beim Shanghai Composite und 5.700 beim S&P 500
sind keine zwei Punkte auf einer Skala; Niveaus zu zeichnen wäre ein Bild darüber, wo welcher Index
zufällig zu zählen begann.

- **Ein Index, der später kommt, steht erst ab dann auf dem Bild.** Der S&P reicht bis 1950, der Dow
  nur bis 2009, und der Hang-Seng-Tech-Index beginnt 2020. Er fehlt, statt bei 0,00% zu parken — dort
  stünde er über jedem Index, der je gefallen ist, und man läse einen Markt, in dem nichts geschah.
- **Monatskerzen, nicht bereinigt.** Ein Index zahlt keine Dividende, aber der Grund ist der andere:
  eine Bereinigung basiert eine Reihe neu, und zwei neu basierte Reihen nebeneinander sind nicht
  vergleichbar. Die Seite nimmt denselben unbereinigten Weg durch die Quelle wie die A+H-Seite.
- **Die Markteinstellung gilt hier nicht**: die Seite liest drei Märkte zugleich, und ein Wechsel des
  Marktes ändert sie nicht. Zur Wahl stehen die sechs des Festlands, die drei aus Hongkong, die drei
  aus New York oder alle zwölf.
- Die längste Spanne ist durch die Monatsgrenze der Quelle gedeckelt — 430 Kerzen, etwa
  fünfunddreißig Jahre. Weniger als zwölf Monate werden abgelehnt: das ist ein Sprint, kein
  Langstreckenlauf.

## Anlageklassen

Eine Zeile pro Anlageklasse, und die Zeile ist **was das Halten eingebracht hat** — nicht die
Notierung. Alle acht sind an einer Festlandbörse notierte Fonds, mit demselben Geld gekauft, also
direkt vergleichbar.

- **Ausschüttungen sind eingerechnet, Aktiensplits ebenfalls.** Eine Anleihe und ein Geldmarktfonds
  zahlen fast vollständig in Erträgen: Der Kurs des Geldmarkt-ETF ging in dreizehn Jahren von
  100,161 auf 100,901 — unadjustiert +0,0 %, was die einzige Zeile hier, die nie fiel, als Letzte
  der Tafel zeichnen würde. Ein Fonds, der seine Anteile gesplittet hat, ist drastischer: Der
  Nasdaq-ETF liegt unadjustiert bei +136 %, während der Index, dem er folgt, sich im selben
  Jahrzehnt versechsfacht hat.
- **Mit Absicht das Gegenteil des Index-Rennens.** Ein Index zahlt keine Dividende, jene Seite
  bleibt also unangetastet; ein Fonds zahlt, diese muss adjustiert werden. Die beiden Wege
  mischen sich nicht.
- **Die beiden ausländischen Zeilen tragen den Wechselkurs.** Der Nasdaq- und der Hang-Seng-ETF
  werden in Yuan notiert, die Währungsbewegung steckt also schon darin — genau das, was ein
  Festland-Anleger tatsächlich bekommen hat.
- **Die Anfänge unterscheiden sich.** Die früheste Zeile beginnt 2012, der Rohstofffonds erst 2019.
  Eine Zeile, die noch nicht dabei ist, fehlt, statt bei 0,00 % zu stehen.
- **Die Markteinstellung regiert diese Seite nicht**: alle acht sind auf dem Festland notiert.
  Weniger als zwölf Monate werden abgelehnt.

## Rücksetzer

Eine Zeile ist, **wie weit unter dem eigenen Hoch eine Anlage steht** — nicht was sie verdient
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

## Renditematrix

![Die Seite im Ganzen: Vorschau links, Zeitleiste darunter, Einstellungen rechts.](media/monthly-matrix.png)

Monatsbalken als Raster gelegt: der Jahresmodus zeigt die Saisonalität eines Instruments über ein Jahrzehnt, der Vergleichsmodus stellt mehrere Instrumente nebeneinander, um die Rotation zu zeigen.

- Jahresmodus: ein Instrument wählen (Suche oder ein voreingestellter Breitbandindex); der Bereich ist 1–10 Jahre oder alle. Eine Anfrage liefert ein Jahrzehnt Monatsbalken.
- Vergleichsmodus: 2–14 Instrumente einer Liste (Ebene-1-Branchen / Themen / Breitbandindizes / benutzerdefiniert / Aktien) nebeneinander, über 6 bis 48 Monate.
- Das Raster leuchtet Zelle für Zelle in Zeitfolge auf; am Ende werden der stärkste und schwächste Monat des Bereichs und weitere Kennzahlen gezeigt.
- Monatsdaten decken ein Jahrzehnt auf einmal ab, es gibt also keine tägliche Tagesspanne — doch zu viele Instrumente laufen über das Bild hinaus.

## Gewinn-Verlust-Kalender

![Die Seite im Ganzen: Vorschau links, Zeitleiste darunter, Einstellungen rechts.](media/gain-calendar.png)

Jede chinesische Aktie oder jeder Index, sein täglicher Anstieg oder Rückgang als Kalenderzellen pro Monat: Rot bei Plus, Grün bei Minus.

- Suche nach Code, Name oder Pinyin; Voreinstellungen sind Breitbandindizes. Nur Instrumente des gewählten Markts.
- Die Favoritenliste wird mit der Aktienseite der App geteilt — ein Favorit, der auf einer Seite hinzugefügt wird, erscheint auf beiden.
- Der Zeitraum ist 1, 3, 6 oder 12 Monate oder frei; ein einzelnes Instrument unterliegt weiter der Grenze von etwa 640 Kalendertagen.
- Die Abschlusswerte nennen die Zahl der Handelstage im Plus und im Minus.

## Sparplan

![Die Seite im Ganzen: Vorschau links, Zeitleiste darunter, Einstellungen rechts.](media/dca-plan.png)

Ein Wertpapier zum festen Betrag in festen Abständen gekauft — an jedem Handelstag, wöchentlich oder monatlich — und als Animation verfolgt, was aus der Disziplin geworden ist.

- Die Ein-Tipp-Instrumente folgen dem Markt: Breite und Gold-ETFs auf dem A-Aktien-Markt, die Hongkonger Tracker-Fonds, in den USA SPY, QQQ und GLD.
- Betrag und Rhythmus stellen Sie ein; der Zeitraum ist drei, fünf oder zehn Jahre, oder so weit zurück, wie es Daten gibt (etwa dreizehn Jahre).
- Die Rendite wird auf rückwärts bereinigten Schlusskursen gerechnet, ohne Gebühren. Das Ergebnis beschreibt die Kursreihe, nicht eine Rechnung, die so jemand hätte ausführen können.
- Neben 3, 5 und 10 Jahren und dem längsten Zeitraum kann auch **Benutzerdefiniert** gewählt werden: Anfangs- und Enddatum eintragen und dann die Daten abrufen. Etwa 35 Jahre sind erreichbar — die Quelle liefert pro Anfrage rund 640 Kalendertage, und der Durchlauf macht höchstens zwanzig.

## Depotrendite

![Die Seite im Ganzen: Vorschau links, Zeitleiste darunter, Einstellungen rechts.](media/position.png)

Ein einziger Kauf, über Jahre gehalten — etwa eine Million in 中国平安 im Jahr 2015 — als Animation dessen, was Wert und Rendite taten.

- Die vorgeschlagenen Namen folgen dem Markt: In China sind es die Aktien, die Menschen wirklich lange gehalten haben (Ping An, Moutai, CMB …), in Hongkong Tencent, HSBC und der Tracker Fund, in den USA Apple, Berkshire und SPY.
- Anfangskapital und Haltezeitraum sind frei wählbar; der Zeitraum umfasst drei, fünf oder zehn Jahre — oder alles, was die Daten hergeben (etwa dreizehn Jahre).
- Die Rendite beruht auf rückwärts adjustierten Kursen — Dividenden reinvestiert, ohne Gebühren. Die rückwärtige Adjustierung verankert sich am Börsengang und trägt Dividenden nach vorn, sodass die frühen Jahre eines fleißigen Zahlers nie nichtpositiv werden, wie es die vorwärts adjustierte Reihe zulässt.
- Dieselbe Auswahl **Benutzerdefiniert** gilt für die Haltedauer: zwei Daten eintragen und die Daten abrufen. Wurde das Papier später gelistet als das Anfangsdatum, beginnt die Haltung an seinem ersten Handelstag.

## Video

Das Bild ist immer 9:16. Alles andere bestimmen Sie.

- Die Dauer verändert das Tempo, sie schneidet die Animation nicht ab: Anfang, Wachsen der Balken und die Kennzahlen am Ende werden auf die gewählte Länge neu verteilt.
- Die Ränder sind gegen ein Bild von 1080×1920 notiert und werden auf die Exportauflösung skaliert, ein einmal abgestimmtes Layout gilt also in jeder Größe. Der linke Rand bestimmt auch, wo die Achsenbeschriftungen landen – zu klein gewählt, verlassen die Zahlen das Bild.
- Die Hilfslinien für den sicheren Bereich umreißen, was eine Telefon-App mit ihrer eigenen Oberfläche verdeckt. Sie werden in der Vorschau gezeichnet und niemals in einer Datei.

## Wohin die Videos gehen

Exporte werden in einen Ordner geschrieben, den Sie über einen Dialog wählen. Solange keiner gewählt ist, fragt der erste Export und merkt sich die Antwort; in den Einstellungen lässt sie sich ändern oder vergessen.

## Hintergrundbild

Auf der Einstellungsseite lässt sich ein Bild hinter das Fenster legen, abgedunkelt. Karten und Flächen bleiben deckend, nur die Navigationsspalte lässt ein wenig durch — das Bild zeigt sich also hauptsächlich um sie herum. Die Videovorschau hat ihren eigenen, deckenden Hintergrund und bleibt unberührt.

- Wählen Sie ein Bild vom Computer oder verwenden Sie direkt einen der mitgelieferten Windows-Hintergründe bzw. Sperrbildschirm-Bilder.
- Ein gewähltes Bild wird in den eigenen Ordner der App kopiert; Verschieben oder Löschen des Originals berührt den Hintergrund nicht.
- Der Abdeckungsregler legt fest, wie stark das Bild zurücktritt — von 30 % bis 95 %.
- Bei aktiviertem hohem Kontrast wird kein Hintergrundbild angezeigt.
## Animationshintergrund

Auf der Einstellungsseite lässt sich ändern, worauf die Animation gezeichnet wird: der eingebaute Farbverlauf, zwei eigene Farben oder ein Bild. Es gilt für die Vorschau, das exportierte Video und das Titelbild gleichermaßen – alle drei zeichnet derselbe Renderer, es gibt also kein „in der Vorschau schön, in der Datei anders“.

- Bei Farben geben Sie oben und unten je einen Farbton an; das Bild blendet dazwischen über. Dunkel passt: Jede Schriftfarbe darin ist hell, auf hellem Grund sind die Zahlen schwer zu lesen.

- Der Regler für die Deckkraft bestimmt, wie viel von den zwei Farben verwendet wird: Bei 100 % ist das Bild die gewählte Paarung, darunter scheint der eigene dunkle Verlauf der Seite von unten durch. So bleibt eine helle Paarung lesbar.

- Ein Bild wählen funktioniert wie beim Fensterhintergrund: eines vom Rechner oder ein mitgeliefertes Windows-Hintergrundbild. Ein eigenes wird in den App-Ordner kopiert.

- Das Bild füllt das Format und der Überstand wird beschnitten; die Proportionen werden nicht verzerrt.

- Der Regler für die Abdunklung bestimmt, wie weit das Bild zum eigenen Hintergrund der Seite zurückgenommen wird: 20 % bis 95 %.

## Die Daten, und was sie nicht sagen

Kurse kommen von den öffentlichen Endpunkten von Tencent Finance, und das Bild nennt die Quelle immer. Diese Videos beschreiben, was schon gehandelt wurde. Sie dienen nur als Anhaltspunkt und sind keine Anlageberatung.

- Umsätze werden in Hundert-Millionen-Yuan umgerechnet, und das Volumen wechselt auf eine größere Einheit, sobald die Zahlen es verlangen, damit die Achse lesbar bleibt.
- Umsätze werden in Hunderte Millionen umgerechnet — Yuan auf dem Festland und in Hongkong, Dollar in den USA. Jeder Markt behält seine eigene Währung.
- Ein Zeitraum von mehr als etwa 640 Kalendertagen wird abgelehnt und nicht stillschweigend gekürzt, denn mehr gibt eine Anfrage an die Quelle nicht zurück.

## Aktualisieren

Hat der Microsoft Store eine neuere Version, erscheint im Navigationsbereich neben Einstellungen eine Schaltfläche **Aktualisieren**; ein Klick installiert sie.

- Sie erscheint nur, wenn der Store wirklich eine neuere Version hat. Ein Entwicklungs- oder quergeladenes Build sieht sie nie — das ist so gewollt.
- Die App schließt sich während der Installation und startet mit der neuen Version neu, die Schaltfläche ist dann verschwunden. Läuft gerade ein Export, wird vorher gefragt.
- Klappt es nicht, wird der Grund genannt — nur über WLAN, Akku zu schwach — und das Update lässt sich auch über den Microsoft Store installieren.

## Etwas nicht in Ordnung?

Schreiben Sie an gaqo@outlook.com, was Sie getan und was Sie stattdessen erwartet haben. Die Versionsnummer steht auf der Einstellungsseite.
