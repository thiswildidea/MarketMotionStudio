# AShare Motion Studio

Questa app trasforma gli indicatori del mercato delle azioni A in video verticali per il telefono. Scegli un periodo, guardi l'anteprima finché si legge bene, ed esporti un MP4. Non serve installare altro.

## Scegliere il mercato

Nelle impostazioni si sceglie da quale mercato l'app prende le quotazioni; come predefinite, le azioni A. La modifica ha effetto dopo il riavvio dell'app.

- **Azioni A**: tutte e cinque le pagine sono disponibili.
- **Hong Kong**: la matrice dei rendimenti e il calendario funzionano; la gara di settori usa i quattro sottoindici Hang Seng; **non esiste un dato per l'intero mercato, quindi quella pagina è nascosta**.
- **Stati Uniti**: la matrice dei rendimenti e il calendario funzionano; la gara di settori usa dieci ETF settoriali SPDR; la pagina dei volumi conserva solo la modalità giornaliera, perché l'endpoint dei minuti non serve dati statunitensi; **gli importi sono in dollari e la pagina del controvalore del mercato è nascosta**.

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

Un insieme di settori o azioni disegnati come barre orizzontali che si sorpassano, e l'ordine cambia fino all'ultimo fotogramma.

- Due misure: la variazione del periodo in % e il suo volume in centinaia di milioni di yuan. Cambiare misura ricolora solo gli stessi dati; non viene rifatta la richiesta.
- Quattro elenchi: settori Shenwan di livello 1, temi di tendenza, personalizzato (spunta le caselle) e azioni singole (aggiunte cercando). L'elenco personalizzato parte riempito con i settori Shenwan di livello 1.
- Gli elenchi integrati seguono il mercato: settori Shenwan di livello 1 e temi di tendenza per le azioni A, i quattro sottoindici Hang Seng per Hong Kong, dieci ETF settoriali SPDR per gli Stati Uniti. Gli elenchi personalizzato e azioni esistono su ogni mercato.
- Il periodo può essere di 1, 3, 6 o 12 mesi, oppure date di inizio e fine personalizzate.
- Un elenco ha un numero minimo e massimo di voci — poche barre non fanno una gara, troppe si accalcano.

## Matrice dei rendimenti

Barre mensili disposte in una griglia: la modalità anno mostra la stagionalità di uno strumento su un decennio, quella confronto mette diversi strumenti affiancati per mostrarne la rotazione.

- Modalità anno: scegli uno strumento (ricerca o un indice ampio predefinito); l'arco è di 1–10 anni o tutti. Una richiesta restituisce un decennio di barre mensili.
- Modalità confronto: da 2 a 14 strumenti di un elenco (settori di livello 1 / temi / indici ampi / personalizzato / azioni) affiancati, su 6–48 mesi.
- La griglia si accende cella per cella in ordine temporale; alla fine mostra il mese più forte e più debole dell'arco, tra altre statistiche.
- I dati mensili coprono un decennio in un colpo solo, quindi qui non c'è il limite giornaliero di giorni — ma troppi strumenti escono dall'inquadratura.

## Calendario di rialzi e ribassi

Qualsiasi titolo o indice cinese, il suo rialzo o ribasso giornaliero disposto in celle di calendario per mese: rosso in rialzo, verde in ribasso.

- Cerca per codice, nome o pinyin; i predefiniti sono indici ampi. Solo strumenti del mercato selezionato.
- L'elenco dei preferiti è condiviso con la pagina azioni dell'app: un preferito aggiunto da una parte appare in entrambe.
- Il periodo è di 1, 3, 6 o 12 mesi, o personalizzato; un singolo strumento resta soggetto al limite di circa 640 giorni di calendario.
- Le statistiche finali danno il conteggio delle sedute in rialzo e in ribasso.

## Video

L'inquadratura è sempre 9:16. Tutto il resto lo decidi tu.

- La durata cambia il ritmo, non accorcia l'animazione: l'apertura, la crescita delle barre e le statistiche finali vengono ridistribuite sulla lunghezza scelta.
- I margini sono annotati su un'inquadratura di 1080×1920 e riscalati sulla risoluzione di esportazione, così un'impaginazione messa a punto una volta vale in ogni dimensione. Il margine sinistro decide anche dove finiscono le etichette dell'asse: se è troppo piccolo i numeri escono dall'inquadratura.
- Le guide dell'area sicura delimitano ciò che un'app per telefono copre con la propria interfaccia. Sono disegnate nell'anteprima e mai in un file.

## Dove finiscono i video

Le esportazioni vengono scritte in una cartella che scegli con un selettore. Finché non ne è stata scelta una, la prima esportazione la chiede e poi la ricorda; le impostazioni permettono di cambiarla o dimenticarla.

## I dati, e ciò che non diranno

Le quotazioni vengono dagli endpoint pubblici di Tencent Finance, e l'inquadratura cita sempre la fonte. Questi video descrivono ciò che è già stato scambiato. Sono solo a titolo informativo e non costituiscono una consulenza di investimento.

- I controvalori sono convertiti in centinaia di milioni di yuan, e i volumi passano a un'unità più grande appena i numeri lo richiedono, perché l'asse resti leggibile.
- I controvalori sono convertiti in centinaia di milioni — di yuan sulla terraferma e a Hong Kong, di dollari negli Stati Uniti. Ogni mercato mantiene la propria valuta.
- Un periodo più lungo di circa 640 giorni di calendario viene rifiutato invece di essere troncato in silenzio, perché è tutto quello che una richiesta alla fonte restituisce.

## Qualcosa non va?

Scrivi a gaqo@outlook.com dicendo cosa stavi facendo e cosa ti aspettavi invece. Il numero di versione è nella pagina delle impostazioni.
