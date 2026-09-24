# AShare Motion Studio

Diese App macht aus Kennzahlen des A-Aktien-Markts hochformatige Videos für das Telefon. Sie wählen einen Zeitraum, betrachten die Vorschau, bis sie sich gut liest, und exportieren eine MP4-Datei. Mehr muss nicht installiert werden.

## Marktumsatz

Der tägliche Umsatz des gesamten Markts: die Beträge der Composite-Indizes von Shanghai und Shenzhen addiert, ein Balken pro Handelstag.

- Es bleiben nur Tage, an denen alle einbezogenen Märkte gehandelt haben. So kann der Feiertag eines einzelnen Markts die Summe nicht scheinbar einbrechen lassen.
- Ein noch laufender Handelstag wird ausgelassen. Ein unfertiger Tag enthält nur seine Eröffnungsauktion und würde als Balken direkt auf der Achse erscheinen.
- Die Peking-Option ergänzt den BSE-50-Index, der nur seine Indexmitglieder abdeckt und nicht die ganze Börse. Das ist eine andere Kennzahl, und eine kleinere.

## Einzelwert-Volumen

Volumen und Umschlagsrate eines Titels, in zwei übereinanderliegenden Feldern.

- Über Handelstage hinweg sind Volumen und Umschlagsrate proportional, die beiden Felder haben also fast dieselbe Form. Innerhalb eines Tages sehen Minutenvolumen und kumulierte Umschlagsrate wirklich unterschiedlich aus, und das ist das interessantere Bild.
- Die Intraday-Quelle hält nur die letzten Handelstage, daher bietet dieser Modus diese Tage an und kein beliebiges Datum.

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
