# AShare Motion Studio

Questa app trasforma gli indicatori del mercato delle azioni A in video verticali per il telefono. Scegli un periodo, guardi l'anteprima finché si legge bene, ed esporti un MP4. Non serve installare altro.

## Controvalore del mercato

Il controvalore scambiato ogni giorno sull'intero mercato: gli importi degli indici composti di Shanghai e Shenzhen sommati, una barra per seduta.

- Restano solo i giorni in cui tutti i mercati inclusi hanno scambiato, così la festività di un singolo mercato non fa sembrare che il totale sia crollato.
- Una seduta ancora in corso viene esclusa. Un giorno non finito contiene solo la sua asta di apertura e si disegnerebbe come una barra appiccicata all'asse.
- L'opzione Pechino aggiunge l'indice BSE 50, che copre solo i suoi componenti e non l'intera borsa. È un'altra misura, e più piccola.

## Volumi di un titolo

I volumi di un titolo a confronto con il suo tasso di rotazione, in due pannelli sovrapposti.

- Da una seduta all'altra volumi e tasso di rotazione sono proporzionali, quindi i due pannelli hanno quasi la stessa forma. All'interno di una giornata, i volumi al minuto e la rotazione cumulata risultano davvero diversi, ed è l'immagine più interessante.
- La fonte intraday conserva solo le ultime sedute, quindi quella modalità propone quelle e non una data qualsiasi.

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
- Un periodo più lungo di circa 640 giorni di calendario viene rifiutato invece di essere troncato in silenzio, perché è tutto quello che una richiesta alla fonte restituisce.

## Qualcosa non va?

Scrivi a gaqo@outlook.com dicendo cosa stavi facendo e cosa ti aspettavi invece. Il numero di versione è nella pagina delle impostazioni.
