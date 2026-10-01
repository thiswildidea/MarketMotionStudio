# Market Motion Studio

Questa app trasforma gli indicatori del mercato delle azioni A in video verticali per il telefono. Scegli un periodo, guardi l'anteprima finché si legge bene, ed esporti un MP4. Non serve installare altro.

## Scegliere il mercato

Nelle impostazioni si sceglie da quale mercato l'app prende le quotazioni; come predefinite, le azioni A. La modifica ha effetto dopo il riavvio dell'app.

- **Azioni A**: tutte e sette le pagine sono disponibili.
- **Hong Kong**: la matrice dei rendimenti e il calendario funzionano; la gara di settori usa i quattro sottoindici Hang Seng; **non esiste un dato per l'intero mercato, quindi quella pagina è nascosta**.
- **Stati Uniti**: la matrice dei rendimenti e il calendario funzionano; la gara di settori usa dieci ETF settoriali SPDR; la pagina dei volumi conserva solo la modalità giornaliera, perché l'endpoint dei minuti non serve dati statunitensi; **gli importi sono in dollari e la pagina del controvalore del mercato è nascosta**.



## Spostarsi tra le pagine

I due pulsanti a sinistra della barra del titolo vanno indietro e avanti tra le pagine visitate, come fa un browser: **Alt+Freccia sinistra** e **Alt+Freccia destra**, oppure i pulsanti laterali del mouse.

- Una pagina resta come l'hai lasciata, quindi tornarci riporta il periodo e l'anteprima nello stato in cui si trovavano, non una pagina appena aperta.
- Come in un browser, scegliere una nuova pagina cancella ciò che stava davanti.
- Funzionano anche con il riquadro di navigazione compresso, proprio quando l'anteprima ha più bisogno di larghezza.

## Controvalore del mercato

Il controvalore scambiato ogni giorno sull'intero mercato: gli importi degli indici composti di Shanghai e Shenzhen sommati, una barra per seduta.

- Restano solo i giorni in cui tutti i mercati inclusi hanno scambiato, così la festività di un singolo mercato non fa sembrare che il totale sia crollato.
- Una seduta ancora in corso viene esclusa. Un giorno non finito contiene solo la sua asta di apertura e si disegnerebbe come una barra appiccicata all'asse.
- Oppure guardare un solo segmento: ciascuna borsa, ciascun mercato principale, STAR, ChiNext. I mercati principali sono ricavati dal totale della borsa meno il suo mercato di crescita; il BSE 50 resta una misura a componenti.
- Solo il mercato delle azioni A dà un totale per l'intero mercato. Con Hong Kong o Stati Uniti la pagina viene rimossa dalla navigazione.

## Volume e rotazione

I volumi di un titolo a confronto con il suo tasso di rotazione, in due pannelli sovrapposti.

- Da una seduta all'altra volumi e tasso di rotazione sono proporzionali, quindi i due pannelli hanno quasi la stessa forma. All'interno di una giornata, i volumi al minuto e la rotazione cumulata risultano davvero diversi, ed è l'immagine più interessante.
- La fonte intraday conserva solo le ultime sedute, quindi quella modalità propone quelle e non una data qualsiasi.
- I dati al minuto sono serviti solo per azioni A e Hong Kong; negli Stati Uniti quella modalità non è proposta.

## Gara di settori

![La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.](media/sector-race.png)

Un insieme di settori o azioni disegnati come barre orizzontali che si sorpassano, e l'ordine cambia fino all'ultimo fotogramma.

- Due misure: la variazione del periodo in % e il suo volume in centinaia di milioni di yuan. Cambiare misura ricolora solo gli stessi dati; non viene rifatta la richiesta.
- Quattro elenchi: settori Shenwan di livello 1, temi di tendenza, personalizzato (spunta le caselle) e azioni singole (aggiunte cercando). L'elenco personalizzato parte riempito con i settori Shenwan di livello 1.
- Gli elenchi integrati seguono il mercato: settori Shenwan di livello 1 e temi di tendenza per le azioni A, i quattro sottoindici Hang Seng per Hong Kong, dieci ETF settoriali SPDR per gli Stati Uniti. Gli elenchi personalizzato e azioni esistono su ogni mercato.
- Il periodo può essere di 1, 3, 6 o 12 mesi, oppure date di inizio e fine personalizzate.
- Un elenco ha un numero minimo e massimo di voci — poche barre non fanno una gara, troppe si accalcano.

## Matrice dei rendimenti

![La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.](media/monthly-matrix.png)

Barre mensili disposte in una griglia: la modalità anno mostra la stagionalità di uno strumento su un decennio, quella confronto mette diversi strumenti affiancati per mostrarne la rotazione.

- Modalità anno: scegli uno strumento (ricerca o un indice ampio predefinito); l'arco è di 1–10 anni o tutti. Una richiesta restituisce un decennio di barre mensili.
- Modalità confronto: da 2 a 14 strumenti di un elenco (settori di livello 1 / temi / indici ampi / personalizzato / azioni) affiancati, su 6–48 mesi.
- La griglia si accende cella per cella in ordine temporale; alla fine mostra il mese più forte e più debole dell'arco, tra altre statistiche.
- I dati mensili coprono un decennio in un colpo solo, quindi qui non c'è il limite giornaliero di giorni — ma troppi strumenti escono dall'inquadratura.

## Calendario di rialzi e ribassi

![La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.](media/gain-calendar.png)

Qualsiasi titolo o indice cinese, il suo rialzo o ribasso giornaliero disposto in celle di calendario per mese: rosso in rialzo, verde in ribasso.

- Cerca per codice, nome o pinyin; i predefiniti sono indici ampi. Solo strumenti del mercato selezionato.
- L'elenco dei preferiti è condiviso con la pagina azioni dell'app: un preferito aggiunto da una parte appare in entrambe.
- Il periodo è di 1, 3, 6 o 12 mesi, o personalizzato; un singolo strumento resta soggetto al limite di circa 640 giorni di calendario.
- Le statistiche finali danno il conteggio delle sedute in rialzo e in ribasso.

## Piano DCA

![La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.](media/dca-plan.png)

Comprare uno strumento a importe e cadenza fissi — ogni giorno di borsa, ogni settimana o ogni mese — e vedere in animazione cosa la disciplina è diventata.

- Gli strumenti a un tocco seguono il mercato: ETF ampi e oro sulle azioni A, i fondi indicizzati di Hong Kong, SPY, QQQ e GLD negli Stati Uniti.
- Importo e frequenza si impostano liberamente; il periodo è di tre, cinque o dieci anni, oppure fino al dato più antico disponibile (circa tredici anni).
- Il rendimento è calcolato su chiusure rettificate all'indietro, senza commissioni. Il risultato descrive la serie di prezzi, non una fattura che qualcuno avrebbe potuto eseguire.

## Rendimento di posizione

![La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.](media/position.png)

Un solo acquisto, mantenuto per anni — un milione in 中国平安 nel 2015, ad esempio — animato come ciò che valore e rendimento hanno fatto.

- I nomi proposti seguono il mercato: in Cina le azioni che la gente dice davvero di aver tenuto (Ping An, Moutai, CMB…), a Hong Kong Tencent, HSBC e il Tracker Fund, negli Stati Uniti Apple, Berkshire e SPY.
- Capitale iniziale e periodo di detenzione sono tuoi; il periodo può essere di tre, cinque o dieci anni, o fino a dove arrivano i dati (circa tredici anni).
- Il rendimento è calcolato su chiusure rettificate all'indietro — dividendi reinvestiti, nessuna commissione. La rettifica all'indietro si ancora alla quotazione e accumula i dividendi in avanti, così i primi anni di un grande pagatore non diventano mai negativi, come può fare la rettifica in avanti.

## Video

L'inquadratura è sempre 9:16. Tutto il resto lo decidi tu.

- La durata cambia il ritmo, non accorcia l'animazione: l'apertura, la crescita delle barre e le statistiche finali vengono ridistribuite sulla lunghezza scelta.
- I margini sono annotati su un'inquadratura di 1080×1920 e riscalati sulla risoluzione di esportazione, così un'impaginazione messa a punto una volta vale in ogni dimensione. Il margine sinistro decide anche dove finiscono le etichette dell'asse: se è troppo piccolo i numeri escono dall'inquadratura.
- Le guide dell'area sicura delimitano ciò che un'app per telefono copre con la propria interfaccia. Sono disegnate nell'anteprima e mai in un file.

## Dove finiscono i video

Le esportazioni vengono scritte in una cartella che scegli con un selettore. Finché non ne è stata scelta una, la prima esportazione la chiede e poi la ricorda; le impostazioni permettono di cambiarla o dimenticarla.

## Immagine di sfondo

La pagina delle impostazioni può mettere un'immagine dietro la finestra, attenuata. Le schede e i pannelli restano opachi e il riquadro di navigazione lascia filtrare solo un poco, quindi l'immagine si vede soprattutto intorno a essi. L'anteprima video ha il proprio fondo opaco e non ne è influenzata.

- Scegli un'immagine dal computer oppure usa direttamente uno degli sfondi e delle immagini della schermata di blocco inclusi in Windows.
- L'immagine scelta viene copiata nella cartella dell'app: spostare o eliminare l'originale non influisce sullo sfondo.
- Il dispositivo di intensità maschera regola quanto l'immagine viene attenuata, dal 30% al 95%.
- Nessuna immagine viene mostrata quando il contrasto elevato è attivo.
## Sfondo dell'animazione

Nella pagina Impostazioni puoi cambiare ciò su cui viene disegnata l'animazione: il gradiente predefinito, due colori tuoi oppure un'immagine. Vale per l'anteprima, per il video esportato e per l'immagine di copertina: tutti e tre li disegna lo stesso renderer, quindi non esiste un «bello nell'anteprima, diverso nel file».

- Con i colori indichi un tono in alto e uno in basso e il fotogramma passa dall'uno all'altro. Meglio scuri: ogni tono di testo è chiaro e uno sfondo chiaro rende i numeri difficili da leggere.

- Scegliere un'immagine funziona come per lo sfondo della finestra: una dal computer o uno sfondo già incluso in Windows. Quella scelta viene copiata nella cartella dell'app.

- L'immagine riempie il formato e l'eccedenza viene ritagliata: le proporzioni non vengono mai deformate.

- Il cursore di attenuazione decide quanto l'immagine viene riportata verso lo sfondo proprio della pagina, dal 20% al 95%.

## I dati, e ciò che non diranno

Le quotazioni vengono dagli endpoint pubblici di Tencent Finance, e l'inquadratura cita sempre la fonte. Questi video descrivono ciò che è già stato scambiato. Sono solo a titolo informativo e non costituiscono una consulenza di investimento.

- I controvalori sono convertiti in centinaia di milioni di yuan, e i volumi passano a un'unità più grande appena i numeri lo richiedono, perché l'asse resti leggibile.
- I controvalori sono convertiti in centinaia di milioni — di yuan sulla terraferma e a Hong Kong, di dollari negli Stati Uniti. Ogni mercato mantiene la propria valuta.
- Un periodo più lungo di circa 640 giorni di calendario viene rifiutato invece di essere troncato in silenzio, perché è tutto quello che una richiesta alla fonte restituisce.

## Aggiornamento

Quando il Microsoft Store ha una versione più recente, accanto a Impostazioni nel riquadro di navigazione compare un pulsante **Aggiorna**; un clic la installa.

- Compare solo quando lo Store ha davvero una versione più recente. Una build di sviluppo o installata a parte non lo vede mai, ed è normale.
- L'app si chiude durante l'installazione e si riavvia con la nuova versione, e il pulsante scompare. Se è in corso un'esportazione, chiede prima.
- Se non si installa, dice perché — solo Wi-Fi, batteria troppo scarica — e l'aggiornamento si può installare anche dal Microsoft Store.

## Qualcosa non va?

Scrivi a gaqo@outlook.com dicendo cosa stavi facendo e cosa ti aspettavi invece. Il numero di versione è nella pagina delle impostazioni.
