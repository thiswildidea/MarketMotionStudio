# Market Motion Studio

Diese App macht aus Kennzahlen des A-Aktien-Markts hochformatige Videos für das Telefon. Sie wählen einen Zeitraum, betrachten die Vorschau, bis sie sich gut liest, und exportieren eine MP4-Datei. Mehr muss nicht installiert werden.

## Markt auswählen

In den Einstellungen wird gewählt, aus welchem Markt die App ihre Kurse bezieht; voreingestellt sind A-Aktien. Eine Änderung gilt nach dem Neustart der App.

- **A-Aktien**: alle sieben Seiten sind verfügbar.
- **Hongkong**: Renditematrix und Gewinn-Verlust-Kalender funktionieren; das Sektor-Rennen läuft über die vier Hang-Seng-Subindizes; **eine Umsatzzahl für den Gesamtmarkt gibt es nicht, diese Seite wird ausgeblendet**.
- **USA**: Renditematrix und Gewinn-Verlust-Kalender funktionieren; das Sektor-Rennen läuft über zehn SPDR-Sektor-ETFs; die Volumenseite behält nur den Tagesmodus, weil der Minuten-Endpunkt keine US-Daten liefert; **Umsätze werden in Dollar angegeben, und die Seite für den Gesamtmarktumsatz ist ausgeblendet**.

## Marktumsatz

Der tägliche Umsatz des gesamten Markts: die Beträge der Composite-Indizes von Shanghai und Shenzhen addiert, ein Balken pro Handelstag.

- Es bleiben nur Tage, an denen alle einbezogenen Märkte gehandelt haben. So kann der Feiertag eines einzelnen Markts die Summe nicht scheinbar einbrechen lassen.
- Ein noch laufender Handelstag wird ausgelassen. Ein unfertiger Tag enthält nur seine Eröffnungsauktion und würde als Balken direkt auf der Achse erscheinen.
- Oder ein Segment allein betrachten: jede der Börsen, jeden Hauptmarkt, STAR, ChiNext. Hauptmärkte werden als Börsenwert minus Wachstumssegment hergeleitet; der BSE 50 bleibt eine Kennzahl der Indexmitglieder.
- Nur der A-Aktienmarkt liefert eine Summe für den ganzen Markt. Bei Hongkong oder USA wird die Seite aus der Navigation entfernt.

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

## Depotrendite

![Die Seite im Ganzen: Vorschau links, Zeitleiste darunter, Einstellungen rechts.](media/position.png)

Ein einziger Kauf, über Jahre gehalten — etwa eine Million in 中国平安 im Jahr 2015 — als Animation dessen, was Wert und Rendite taten.

- Die vorgeschlagenen Namen folgen dem Markt: In China sind es die Aktien, die Menschen wirklich lange gehalten haben (Ping An, Moutai, CMB …), in Hongkong Tencent, HSBC und der Tracker Fund, in den USA Apple, Berkshire und SPY.
- Anfangskapital und Haltezeitraum sind frei wählbar; der Zeitraum umfasst drei, fünf oder zehn Jahre — oder alles, was die Daten hergeben (etwa dreizehn Jahre).
- Die Rendite beruht auf rückwärts adjustierten Kursen — Dividenden reinvestiert, ohne Gebühren. Die rückwärtige Adjustierung verankert sich am Börsengang und trägt Dividenden nach vorn, sodass die frühen Jahre eines fleißigen Zahlers nie nichtpositiv werden, wie es die vorwärts adjustierte Reihe zulässt.

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
