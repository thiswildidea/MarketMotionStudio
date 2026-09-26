# AShare Motion Studio

Diese App macht aus Kennzahlen des A-Aktien-Markts hochformatige Videos für das Telefon. Sie wählen einen Zeitraum, betrachten die Vorschau, bis sie sich gut liest, und exportieren eine MP4-Datei. Mehr muss nicht installiert werden.

## Marktumsatz

Der tägliche Umsatz des gesamten Markts: die Beträge der Composite-Indizes von Shanghai und Shenzhen addiert, ein Balken pro Handelstag.

- Es bleiben nur Tage, an denen alle einbezogenen Märkte gehandelt haben. So kann der Feiertag eines einzelnen Markts die Summe nicht scheinbar einbrechen lassen.
- Ein noch laufender Handelstag wird ausgelassen. Ein unfertiger Tag enthält nur seine Eröffnungsauktion und würde als Balken direkt auf der Achse erscheinen.
- Oder ein Segment allein betrachten: jede der Börsen, jeden Hauptmarkt, STAR, ChiNext. Hauptmärkte werden als Börsenwert minus Wachstumssegment hergeleitet; der BSE 50 bleibt eine Kennzahl der Indexmitglieder.

## Einzelwert-Volumen

Volumen und Umschlagsrate eines Titels, in zwei übereinanderliegenden Feldern.

- Über Handelstage hinweg sind Volumen und Umschlagsrate proportional, die beiden Felder haben also fast dieselbe Form. Innerhalb eines Tages sehen Minutenvolumen und kumulierte Umschlagsrate wirklich unterschiedlich aus, und das ist das interessantere Bild.
- Die Intraday-Quelle hält nur die letzten Handelstage, daher bietet dieser Modus diese Tage an und kein beliebiges Datum.

## Sektor-Rennen

Eine Gruppe von Sektoren oder Aktien als waagerechte Balken, die einander überholen, die Reihenfolge ändert sich bis zum letzten Bild.

- Zwei Maße: die Prozentveränderung des Zeitraums und sein Umsatz in Hunderten Millionen Yuan. Das Maß zu wechseln färbt nur dieselben Daten neu ein, es wird nicht neu geladen.
- Vier Listen: Shenwan-Ebene-1-Branchen, beliebte Themen, benutzerdefiniert (ankreuzen) und Einzelaktien (per Suche hinzufügen). Die benutzerdefinierte Liste beginnt mit den Shenwan-Ebene-1-Branchen gefüllt.
- Der Zeitraum kann 1, 3, 6 oder 12 Monate betragen oder frei mit Start- und Enddatum gewählt werden.
- Eine Liste hat eine Mindest- und Höchstzahl an Einträgen — zu wenige Balken sind kein Rennen, zu viele ein Wirrwarr.

## Monatsmatrix

Monatsbalken als Raster gelegt: der Jahresmodus zeigt die Saisonalität eines Instruments über ein Jahrzehnt, der Vergleichsmodus stellt mehrere Instrumente nebeneinander, um die Rotation zu zeigen.

- Jahresmodus: ein Instrument wählen (Suche oder ein voreingestellter Breitbandindex); der Bereich ist 1–10 Jahre oder alle. Eine Anfrage liefert ein Jahrzehnt Monatsbalken.
- Vergleichsmodus: 2–14 Instrumente einer Liste (Ebene-1-Branchen / Themen / Breitbandindizes / benutzerdefiniert / Aktien) nebeneinander, über 6 bis 48 Monate.
- Das Raster leuchtet Zelle für Zelle in Zeitfolge auf; am Ende werden der stärkste und schwächste Monat des Bereichs und weitere Kennzahlen gezeigt.
- Monatsdaten decken ein Jahrzehnt auf einmal ab, es gibt also keine tägliche Tagesspanne — doch zu viele Instrumente laufen über das Bild hinaus.

## Gewinn-Verlust-Kalender

Jede chinesische Aktie oder jeder Index, sein täglicher Anstieg oder Rückgang als Kalenderzellen pro Monat: Rot bei Plus, Grün bei Minus.

- Suche nach Code, Name oder Pinyin; Voreinstellungen sind Breitbandindizes. Nur chinesische Aktien und Indizes.
- Die Favoritenliste wird mit der Aktienseite der App geteilt — ein Favorit, der auf einer Seite hinzugefügt wird, erscheint auf beiden.
- Der Zeitraum ist 1, 3, 6 oder 12 Monate oder frei; ein einzelnes Instrument unterliegt weiter der Grenze von etwa 640 Kalendertagen.
- Die Abschlusswerte nennen die Zahl der Handelstage im Plus und im Minus.

## Video

Das Bild ist immer 9:16. Alles andere bestimmen Sie.

- Die Dauer verändert das Tempo, sie schneidet die Animation nicht ab: Anfang, Wachsen der Balken und die Kennzahlen am Ende werden auf die gewählte Länge neu verteilt.
- Die Ränder sind gegen ein Bild von 1080×1920 notiert und werden auf die Exportauflösung skaliert, ein einmal abgestimmtes Layout gilt also in jeder Größe. Der linke Rand bestimmt auch, wo die Achsenbeschriftungen landen – zu klein gewählt, verlassen die Zahlen das Bild.
- Die Hilfslinien für den sicheren Bereich umreißen, was eine Telefon-App mit ihrer eigenen Oberfläche verdeckt. Sie werden in der Vorschau gezeichnet und niemals in einer Datei.

## Wohin die Videos gehen

Exporte werden in einen Ordner geschrieben, den Sie über einen Dialog wählen. Solange keiner gewählt ist, fragt der erste Export und merkt sich die Antwort; in den Einstellungen lässt sie sich ändern oder vergessen.

## Die Daten, und was sie nicht sagen

Kurse kommen von den öffentlichen Endpunkten von Tencent Finance, und das Bild nennt die Quelle immer. Diese Videos beschreiben, was schon gehandelt wurde. Sie dienen nur als Anhaltspunkt und sind keine Anlageberatung.

- Umsätze werden in Hundert-Millionen-Yuan umgerechnet, und das Volumen wechselt auf eine größere Einheit, sobald die Zahlen es verlangen, damit die Achse lesbar bleibt.
- Ein Zeitraum von mehr als etwa 640 Kalendertagen wird abgelehnt und nicht stillschweigend gekürzt, denn mehr gibt eine Anfrage an die Quelle nicht zurück.

## Etwas nicht in Ordnung?

Schreiben Sie an gaqo@outlook.com, was Sie getan und was Sie stattdessen erwartet haben. Die Versionsnummer steht auf der Einstellungsseite.
