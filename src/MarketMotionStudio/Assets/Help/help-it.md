# Market Motion Studio

Questa app trasforma gli indicatori del mercato delle azioni A in video verticali per il telefono. Scegli un periodo, guardi l'anteprima finché si legge bene, ed esporti un MP4. Non serve installare altro.

## Scegliere il mercato

Nelle impostazioni si sceglie da quale mercato l'app prende le quotazioni; come predefinite, le azioni A. La modifica ha effetto dopo il riavvio dell'app.

- **Azioni A**: tutte e otto le pagine sono disponibili.
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

## Candele

Le candele di uno strumento: giornaliere, settimanali o mensili, disegnate in quattro modi, con le medie e il volume sotto.

- **Intervallo** decide quanto tempo di mercato copre una candela: un giorno, una settimana o un mese. Cambiarlo ricarica i dati, perché sulla fonte le tre sono serie distinte.
- **Tipo di disegno** decide come vengono disegnati gli stessi quattro prezzi: candele, barre OHLC, linea di chiusura o area di chiusura. Passare dall'uno all'altro non ricarica nulla.
- **Animazione** è l'arrivo delle candele una dopo l'altra finché tutto l'intervallo è tracciato, oppure una finestra fissa che avanza. La seconda è ciò che mantiene la candela abbastanza larga da leggersi su un intervallo lungo, e quella ampiezza è l'impostazione **Finestra**.
- Le medie mobili MA5, MA10 e MA20 possono essere sovrapposte alle candele; il pannello del volume sotto può essere spento, e il pannello del prezzo riprende lo spazio.
- Una settimana o un mese ancora in corso resta fuori. Una candela fatta di tre giorni non è una settimana.
- Ogni mercato è letto sulla sua serie rettificata, quindi un giorno di frazionamento non è disegnato come un calo, e nemmeno un dividendo.
- **L'intervallo** segue il periodo: il giornaliero offre 3, 6 o 12 mesi e 3, 5 o 10 anni; il settimanale 1, 3, 5 o 10 anni; il mensile 3, 5 o 10 anni, oppure il massimo di cui la fonte dispone (circa 13). Una richiesta porta circa 640 barre giornaliere e la pagina torna indietro una pagina alla volta: dieci anni, circa 2.500 barre, ci stanno dentro.

## Volume e rotazione

I volumi di un titolo a confronto con il suo tasso di rotazione, in due pannelli sovrapposti.

- Da una seduta all'altra volumi e tasso di rotazione sono proporzionali, quindi i due pannelli hanno quasi la stessa forma. All'interno di una giornata, i volumi al minuto e la rotazione cumulata risultano davvero diversi, ed è l'immagine più interessante.
- La fonte intraday conserva solo le ultime sedute, quindi quella modalità propone quelle e non una data qualsiasi.
- I dati al minuto sono serviti solo per azioni A e Hong Kong; negli Stati Uniti quella modalità non è proposta.
- Sul giornaliero l'intervallo è di 1, 3, 6, 12 o 24 mesi, oppure una data di inizio e di fine scelte da te; un intervallo personalizzato si ferma a circa 900 giorni di calendario — quanto restituisce una richiesta — e anche i selettori di data si fermano lì. La modalità intraday propone di scegliere uno dei pochi giorni disponibili.

## Gara di settori

![La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.](media/sector-race.png)

Un insieme di settori o azioni disegnati come barre orizzontali che si sorpassano, e l'ordine cambia fino all'ultimo fotogramma.

- Due misure: la variazione del periodo in % e il suo volume in centinaia di milioni di yuan. Cambiare misura ricolora solo gli stessi dati; non viene rifatta la richiesta.
- Quattro elenchi: settori Shenwan di livello 1, temi di tendenza, personalizzato (spunta le caselle) e azioni singole (aggiunte cercando). L'elenco personalizzato parte riempito con i settori Shenwan di livello 1.
- Gli elenchi integrati seguono il mercato: settori Shenwan di livello 1 e temi di tendenza per le azioni A, i quattro sottoindici Hang Seng per Hong Kong, dieci ETF settoriali SPDR per gli Stati Uniti. Gli elenchi personalizzato e azioni esistono su ogni mercato.
- Il periodo può essere di 1, 3, 6, 12 o 24 mesi, oppure date di inizio e fine personalizzate. Un intervallo personalizzato arriva a circa 900 giorni — quanto copre una richiesta — e i selettori di data si fermano lì.
- Un elenco ha un numero minimo e massimo di voci — poche barre non fanno una gara, troppe si accalcano.




## Corsa delle capitalizzazioni

Le quindici maggiori società di un mercato come barre orizzontali ordinate per
capitalizzazione; l'ordine cambia fino all'ultimo fotogramma. Campionamento mensile.

- **La classifica si rifà a ogni periodo.** Il recupero chiede prima alla fonte la classifica
  odierna per capitalizzazione, ne prende le prime duecento come campo e vi aggiunge i titoli
  pesanti che erano in classifica e ne sono usciti; ogni periodo mostra poi i quindici maggiori di
  quel campo. I membri quindi entrano ed escono davvero — il 2016 era petrolio e banche, il 2026 ha
  aggiunto 茅台, 宁德时代 e 工业富联. Un campo scritto nel programma aveva mancato una società
  quotatasi e subito balzata in testa; ora il campo si chiede invece di ricordarlo.
- **Una capitalizzazione passata è derivata**: la capitalizzazione di oggi per il rapporto di
  prezzo rettificato del periodo. Aumenti di capitale e frazionamenti si annullano nella serie
  rettificata; i dividendi no — vengono reinvestiti, quindi il valore passato di un forte
  distributore risulta basso. Solo la cifra dell'ultimo fotogramma viene dalla fonte.
- **Una società non ancora quotata cresce dal nulla**: i titoli quotati nel 2018 salgono dalla
  linea di base il giorno dell'ingresso, senza occupare un posto in anticipo.
- **L'intervallo è il mese, non il giorno** — centoventi periodi in dieci anni, dodici in uno, e
  l'intestazione del fotogramma conta i mesi. Una classifica per capitalizzazione è una grandezza
  lenta, e un campione mensile ottiene tutta la storia in una richiesta.
- **Ogni mercato ha i suoi quindici.** I tre non si mescolano mai: la loro moneta non è la stessa.
- L'intervallo è gli ultimi 12 mesi, 3, 5 o 10 anni, o **Massimo** — una richiesta restituisce tutti i 180 periodi mensili, circa quindici anni, ed è lì che finisce questa voce. Sono offerte anche una data di inizio e una di fine scelte da te.
  Hong Kong e New York tengono un campo fisso, perché nessuna classifica raggiungibile da questa
  applicazione li serve.





## Premio A/H

Quanto costa in più la quotazione continentale di una società rispetto a quella di Hong Kong,
per le società quotate su entrambi i lati — mese per mese, come barre che si sorpassano.

- **Premio = prezzo A ÷ (prezzo H × HKD/CNY) − 1.** Nulla è derivato: entrambe le gambe sono prezzi
  realmente pagati nello stesso istante, ed è per questo che questa è l'unica pagina che prende
  prezzi **non rettificati**. Una serie rettificata all'indietro gonfia i prezzi recenti, e due
  mercati rettificati separatamente non sono confrontabili — l'azione A di ICBC quota 8,28 sullo
  schermo e la serie rettificata ne dichiara 13,34: un premio del +26% diventa +245%.
- **Lo stesso divario si scrive nei due sensi.** Questa pagina dà A contro H, la forma consueta:
  +194% significa che l'azione continentale vale quasi il triplo di quella di Hong Kong. Alcuni
  servizi mostrano lo stesso numero al contrario (溢价(H/A)) e per 新华制药 danno −66% nello stesso
  giorno. È lo stesso fatto (1 ÷ (1 − 0,66) − 1 = 1,94): non un altro prezzo né un errore.
- **Il fotogramma disegna le quindici più care**, quindi le barre crescono verso destra — anche
  la quindicesima superava il venti per cento. Solo due delle sessantanove vanno al contrario, con
  l'azione H sopra la A, ed entrambe stanno in fondo alla lista, fuori campo.
- **Più lungo il periodo, meno società restano.** Le candidate sono sessantanove doppie quotazioni
  note, ma viene disegnata solo una coppia con entrambe le gambe sull'intero periodo: una
  quotazione a Hong Kong da meno di due anni viene esclusa.
- **Campionamento mensile.** «Il più lungo» è circa nove anni, e il limite è la serie del cambio, che
  risale solo al 2016. Le tre gambe chiudono il mese in giorni diversi: si raggruppa per mese di
  calendario e si prende l'ultimo prezzo del mese, invece di intersecare sulla data.
- **L'elenco è integrato.** Nessuna delle due fonti risponde a «quali quotazioni continentali hanno
  anche una quotazione a Hong Kong». In compenso è verificabile: ogni coppia è stata riletta dalla
  fonte il 2026-10-02, e 海通证券 è ciò che quel controllo ha rimosso (azioni H delistate dopo la
  fusione in 国泰海通).

## Giorni estremi

Uno strumento e i giorni in cui si è mosso di più — barre orizzontali ordinate per ampiezza.
**Le righe di questo quadro sono giorni, non aziende**, cosa che nessun'altra pagina qui fa: il
valore di una riga è lo spostamento di quel giorno rispetto alla chiusura del giorno precedente, e
una volta che quel giorno è passato il valore non cambia più.

- **Il movimento è la variazione del close rettificato.** Rettificato, perché un giorno di stacco
  del dividendo non è un crollo: quel mattino il prezzo scende del dividendo, e una serie non
  rettificata metterebbe quel giorno in cima alle più grandi cadute della storia, mentre chi
  deteneva il titolo non ha perso nulla.
- **Ordinato per ampiezza, non per segno.** −7,7 % e +8,1 % sono movimenti della stessa misura e
  quindi stanno vicini; ordinare i valori con segno metterebbe ogni ribasso sotto ogni rialzo. Le
  barre crescono quindi da entrambi i lati: **un rialzo a destra, in rosso; un ribasso a sinistra,
  in verde**.
- **Un giorno entra in classifica solo quando è arrivato.** I ventiquattro movimenti più grandi del
  periodo sono i candidati e il fotogramma ne disegna i quindici più grandi; un giorno non partecipa
  finché non arriva la sua data, così il quadro si riempie con il passare degli anni invece di
  essere pieno dall'inizio.
- **Qualsiasi strumento quotato dal mercato, non solo gli indici ampi.** Scrivete un codice, un
  nome o il pinyin nella casella di ricerca: un'azione singola e un fondo quotato stanno su questa
  tavola quanto un indice, e l'elenco sotto è solo una scorciatoia ai soliti. Cambiare mercato
  sostituisce quell'elenco e lascia indietro uno strumento di un altro mercato; scegliere strumento
  o intervallo salva solo una preferenza — nulla viene scaricato finché non si preme 取数.
- **Il periodo più lungo è di circa trentacinque anni**, che è il limite della fonte: una richiesta
  porta circa 640 barre giornaliere e il riavvolgimento ne fa al massimo venti. Un periodo con meno
  di sessanta giorni di negoziazione viene rifiutato — il giorno più grande di un mese tranquillo
  non è un fatto che merita un quadro.
- **La data in alto nel fotogramma è l'asse del tempo**, la barra sotto è l'avanzamento. La riga
  di intestazione porta il periodo, il numero di giorni di negoziazione e il numero di giorni
  candidati.

## Corridoi valutari

Una riga per coppia, e **la riga è il corridoio stesso**: un'estremità è il livello più basso
che la coppia ha avuto nel periodo scelto, l'altra il più alto, e l'indicatore è il cambio di oggi.
Questo tabellone non è come gli altri — altrove la lunghezza di una barra dice *quanto*, qui la riga
occupa tutta la larghezza in ogni fotogramma, e a muoversi sono l'indicatore e il corridoio intorno.

- **Il corridoio si allarga.** Le sue pareti sono il minimo e il massimo **finora**, non quelli di
  tutto il periodo. Un mese che va oltre tutti i precedenti spinge una delle due verso l'esterno, e
  una coppia al 100% è al livello più caro che abbia mai avuto — non a un limite.
- **Ogni coppia è misurata sul proprio intervallo.** 157,92 su USD/JPY e 1,1245 su EUR/USD non sono
  due punti di una stessa scala; è la normalizzazione che permette a sei coppie di stare su un
  quadro. Il prezzo da pagare è che un corridoio stretto e uno largo si vedono allo stesso modo, e
  per questo i due estremi sono scritti sotto ogni riga.
- **Candele mensili, non rettificate.** Una valuta non ha dividendi né frazionamenti da rettificare,
  e la pagina prende lo stesso percorso grezzo nella fonte che prende la pagina A+H.
- **La copertura differisce, ed è per questo che le liste sono due**: USD/CNY arriva al 2005, le
  altre cinque coppie del renminbi al 2016; i principali cross cominciano tutti nel 2005-07 e portano
  325 mesi. Su un tabellone solo si leggerebbe quando la fonte ha iniziato a quotare ogni coppia.
- **L'impostazione di mercato non vale qui**: una coppia di valute non appartiene a nessuna Borsa, e
  il tabellone è lo stesso qualunque sia il mercato in vigore.
- Il periodo più lungo è di circa vent'anni, la copertura mensile della fonte; meno di dodici mesi
  viene rifiutato — sono poche settimane di movimento, non un corridoio.

## Corsa degli indici

Una riga per indice, e la riga è **quanto quell'indice ha percorso dal proprio primo mese
nell'intervallo** — non il suo livello. 3.800 sullo Shanghai Composite e 5.700 sull'S&P 500 non sono
due punti di una stessa scala: disegnare i livelli sarebbe un quadro su dove ogni indice ha iniziato
a contare.

- **Un indice che arriva tardi non è sulla tavola fino al suo arrivo.** L'S&P arriva al 1950, il Dow
  solo al 2009 e l'indice Hang Seng Tech comincia nel 2020. È assente, non parcheggiato a 0,00%: lì
  si classificherebbe sopra ogni indice mai sceso e si leggerebbe come un mercato in cui non è
  successo niente.
- **Mensile, e ora aggiustato.** Un indice non distribuisce nulla, ma un'azione paga dividendi e
  fraziona le proprie quote: Apple segna +193 % in dieci anni non aggiustata e +1183 % aggiustata,
  perché la linea non aggiustata porta dirupi da cui nessun detentore è mai caduto. Gli indici non
  ne risentono: se si chiede un aggiustamento, la fonte risponde a un indice con le stesse righe di
  sempre, e tutti e dodici risultarono identici su entrambe le vie. Ciò che la tavola porta ora è
  una differenza da dichiarare: la riga di un indice è un rendimento **di prezzo**, perché un
  indice non è una posizione, quella di un'azione è un rendimento **totale**, con dividendi e
  frazionamenti rimessi dentro.
- **L'impostazione del mercato non governa questa pagina**: legge tre mercati insieme e cambiare
  mercato non la cambia. Si possono prendere le sei della Cina continentale, le tre di Hong Kong, le
  tre di New York, o tutte e dodici.
- Il periodo più lungo è limitato dal tetto mensile della fonte — 430 candele, circa trentacinque
  anni; meno di dodici mesi viene rifiutato: è uno scatto, non una corsa lunga.
- **Oppure la vostra lista.** L'ultimo gruppo del menu è una lista propria: scrivete un codice,
  un nome o il pinyin per aggiungerne uno, e un titolo continentale, uno di Hong Kong e uno di
  New York possono starci insieme — questa tavola non consulta mai l'impostazione di mercato. Una
  lista per quattro tavole: un'azione aggiunta qui è proposta anche nella corsa degli attivi, nei
  ribassi e nel tasso di riuscita. Sotto tre il recupero è rifiutato.

## Classi di attività

Una riga per classe di attività, e la riga è **ciò che la detenzione ha reso** — non la
quotazione. Tutti e otto sono fondi quotati su una borsa continentale, comprati con lo stesso
denaro, quindi direttamente confrontabili.

- **I dividendi sono reinseriti, e anche i frazionamenti.** Un'obbligazione e un fondo monetario
  pagano quasi interamente in reddito: il prezzo dell'ETF monetario è passato da 100,161 a 100,901
  in tredici anni, che non aggiustato è +0,0% — e disegnerebbe in fondo alla tavola l'unica riga
  qui che non è mai scesa. Un fondo che ha frazionato le quote è ancora più netto: l'ETF Nasdaq
  segna +136% non aggiustato, mentre l'indice che replica è salito di sei volte nello stesso
  decennio.
- **Volutamente l'opposto della corsa degli indici.** Un indice non paga dividendi, quindi quella
  pagina è lasciata com'è; un fondo li paga, quindi questa va aggiustata. Le due strade non si
  mescolano.
- **Le due righe estere portano il cambio.** Gli ETF Nasdaq e Hang Seng sono quotati in yuan, quindi
  la valuta è già dentro — che è ciò che un detentore continentale ha davvero ottenuto.
- **Le partenze differiscono.** La riga più antica inizia nel 2012 e il fondo su materie prime solo
  nel 2019. Una riga non ancora entrata è assente, non a 0,00%.
- **L'impostazione di mercato non governa questa pagina**: tutti e otto sono quotati sul continente.
  Meno di dodici mesi è rifiutato.
- **Oppure la vostra lista.** L'ultimo gruppo del menu è una lista propria: scrivete un codice,
  un nome o il pinyin per aggiungerne uno, e i tre mercati possono esservi mescolati. Una lista per
  quattro tavole: un'azione aggiunta qui è proposta anche sulle altre tre; è scaricata aggiustata,
  esattamente come gli otto fondi, quindi dividendi e frazionamenti sono nel numero. Sotto tre il
  recupero è rifiutato.

## Ribassi

Una riga è **quanto sotto il proprio massimo si trova uno strumento** — non quanto ha guadagnato,
ma cosa è costato guadagnarlo. Gli stessi otto strumenti della corsa delle classi di attività,
misurati rispetto a sé stessi invece che tra loro.

- **La curva è il punto.** In ogni altra parte di questa app un valore è disegnato come una
  lunghezza, e una lunghezza può dire solo quanto è profonda l'acqua in quell'istante. Una
  profondità è una forma nel tempo: il minimo e la risalita sono due punti sulla curva, e la
  distanza che li separa sul fotogramma è il numero di mesi trascorsi.
- **I due numeri non crescono insieme.** Negli ultimi dieci anni il fondo Nasdaq è sceso del 25,52%
  ed è tornato in pari in sei mesi; il fondo CSI 500 è sceso del 56,07% e ha impiegato
  ottantasei mesi. Stampato come un numero solo, il secondo sembra una versione aggravata del
  primo — e non lo è.
- **Una sola scala di profondità per tutta la tavola.** Scalare ogni riga sul proprio peggior
  momento disegnerebbe lo 0,2% del fondo monetario come un baratro grande quanto il 56% del CSI
  500, su una tavola la cui intera ragione d'essere è dire che quei due non sono paragonabili.
  Quindi quella riga è una linea piatta attaccata alla sua linea di massimo — e **quella piattezza
  è ciò che dice**.
- **Aggiustato, mensile e dal primo mese proprio di ciascuno strumento**, per le ragioni che dà la
  corsa delle classi di attività: le distribuzioni di un fondo non compaiono mai nel suo prezzo, e
  uno strumento che arriva solo nel 2019 non è misurato contro un massimo che non aveva.
- **Le righe corrono ancora.** Sono ordinate per quanto sono sotto il proprio massimo — la più
  vicina al proprio massimo in alto — e si scambiano di posto mentre i mesi passano.
- **Oro e fondo di materie prime erano ancora sott'acqua al momento di questa misurazione** — la
  tavola segnala questo tipo di ribasso come aperto, perché l'intervallo è finito prima che fosse
  riparato.
- **Oppure la vostra lista.** L'ultimo gruppo del menu è una lista propria: scrivete un codice,
  un nome o il pinyin per aggiungerne uno, e i tre mercati possono esservi mescolati. Una lista per
  quattro tavole: un'azione aggiunta qui è proposta anche sulle altre tre; è scaricata aggiustata,
  esattamente come gli otto fondi, quindi dividendi e frazionamenti sono nel numero. Sotto tre il
  recupero è rifiutato.

Non dipende dall'impostazione del mercato: tutti e otto sono quotati su una borsa continentale.
Meno di dodici mesi nell'intervallo viene rifiutato.

## Tasso di riuscita

Una riga è **la quota delle entrate concluse che hanno guadagnato** — fra tutti i mesi in cui si
sarebbe potuti entrare e mantenere per la stessa durata, la quota finita in guadagno. Gli stessi
otto strumenti della corsa delle classi di attività e della tavola dei ribassi, valutati sul fatto
che tenerli abbia funzionato, non su quanto abbiano reso.

- **Un'entrata è fortuna; ottantaquattro sono un tasso.** Ogni mese dell'intervallo è un'entrata e
  tutte sono mantenute per la stessa durata: detenere tre anni su dieci anni sono ottantaquattro
  entrate per riga, non una. Condividono i mesi, ed è proprio questo il punto: diradarle a tre
  indipendenti lascerebbe un tasso con tre osservazioni dentro.
- **Un'entrata conta dal mese in cui finisce.** Ciò che è comprato negli ultimi tre anni
  dell'intervallo non è finito, e contare un'entrata non finita come perdita piegherebbe ogni riga
  verso il basso alla fine per la sola ragione del calendario. La tavola parte quindi dal primo mese
  in cui un'entrata poteva finire.
- **Una riga entra quando sei entrate sono concluse.** Un'entrata è 0% o 100%, e ciascuno di questi
  due numeri a un'estremità della classifica è un'estremità che non ha meritato.
- **Aggiustato, mensile e dal primo mese proprio di ciascuno strumento**, per le ragioni che dà la
  corsa delle classi di attività: le distribuzioni di un fondo non compaiono mai nel suo prezzo, e
  un fondo lanciato nel 2019 non ha entrate del 2016 da aver vinte o perse.
- **Il periodo di detenzione è l'unica nuova scelta di questa tavola.** Un anno e cinque anni sugli
  stessi dieci anni sono due domande diverse con due risposte diverse, e le otto righe si
  riordinano fra le due.
- **Le righe corrono ancora.** Sono ordinate per il loro tasso — più spesso in guadagno in alto — e
  si scambiano di posto mentre i mesi passano.
- **Oppure la vostra lista.** L'ultimo gruppo del menu è una lista propria: scrivete un codice,
  un nome o il pinyin per aggiungerne uno, e i tre mercati possono esservi mescolati. Una lista per
  quattro tavole: un'azione aggiunta qui è proposta anche sulle altre tre; è scaricata aggiustata,
  esattamente come gli otto fondi, quindi dividendi e frazionamenti sono nel numero. Sotto tre il
  recupero è rifiutato.

Misurato sugli ultimi dieci anni con una detenzione di tre anni: il fondo Nasdaq era in vantaggio
su tutte le ottantaquattro entrate e il fondo di Hong Kong sul quaranta per cento di esse — due
righe che la corsa delle classi di attività separa per dieci anni di rendimento totale e che questa
tavola separa per il semplice fatto di essere entrati.

Non dipende dall'impostazione del mercato: tutti e otto sono quotati su una borsa continentale.
Meno di dodici mesi nell'intervallo viene rifiutato.

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
- Oltre a 3, 5 e 10 anni e all'intervallo più lungo, il periodo può essere **Personalizzato**: indica una data di inizio e una di fine, poi premi il pulsante per recuperare i dati. Si può risalire di circa 35 anni: la fonte restituisce circa 640 giorni di calendario per richiesta e la scansione ne fa al massimo venti.

## Rendimento di posizione

![La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.](media/position.png)

Un solo acquisto, mantenuto per anni — un milione in 中国平安 nel 2015, ad esempio — animato come ciò che valore e rendimento hanno fatto.

- I nomi proposti seguono il mercato: in Cina le azioni che la gente dice davvero di aver tenuto (Ping An, Moutai, CMB…), a Hong Kong Tencent, HSBC e il Tracker Fund, negli Stati Uniti Apple, Berkshire e SPY.
- Capitale iniziale e periodo di detenzione sono tuoi; il periodo può essere di tre, cinque o dieci anni, o fino a dove arrivano i dati (circa tredici anni).
- Il rendimento è calcolato su chiusure rettificate all'indietro — dividendi reinvestiti, nessuna commissione. La rettifica all'indietro si ancora alla quotazione e accumula i dividendi in avanti, così i primi anni di un grande pagatore non diventano mai negativi, come può fare la rettifica in avanti.
- Lo stesso periodo **Personalizzato** vale per la detenzione: indica due date, poi premi il pulsante per recuperare i dati. Se lo strumento è stato quotato dopo la data indicata, la detenzione inizia nel suo primo giorno di negoziazione.

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

- La barra dell'opacità decide quanto si usano i due colori: al 100% il fotogramma è la coppia scelta, più in basso lascia intravedere il gradiente scuro della pagina. È questo che tiene leggibile una coppia chiara.

- Scegliere un'immagine funziona come per lo sfondo della finestra: una dal computer o uno sfondo già incluso in Windows. Quella scelta viene copiata nella cartella dell'app.

- L'immagine riempie il formato e l'eccedenza viene ritagliata: le proporzioni non vengono mai deformate.

- Il cursore di attenuazione decide quanto l'immagine viene riportata verso lo sfondo proprio della pagina, dal 20% al 95%.

## I dati, e ciò che non diranno

Le quotazioni vengono dagli endpoint pubblici di Tencent Finance, e l'inquadratura cita sempre la fonte. Questi video descrivono ciò che è già stato scambiato. Sono solo a titolo informativo e non costituiscono una consulenza di investimento.

- I controvalori sono convertiti in centinaia di milioni di yuan, e i volumi passano a un'unità più grande appena i numeri lo richiedono, perché l'asse resti leggibile.
- I controvalori sono convertiti in centinaia di milioni — di yuan sulla terraferma e a Hong Kong, di dollari negli Stati Uniti. Ogni mercato mantiene la propria valuta.
- Un intervallo più lungo di quanto una richiesta possa restituire viene rifiutato invece di essere troncato in silenzio: circa 900 giorni di calendario sul giornaliero, circa quindici anni sulla pagina Candele, che sfoglia indietro una pagina alla volta, e tutta la storia sul mensile. Troncare in silenzio è il risultato peggiore — a mancare è l'**inizio**, e un grafico senza i suoi primi anni è un grafico più corto che sembra del tutto normale.

## Aggiornamento

Quando il Microsoft Store ha una versione più recente, accanto a Impostazioni nel riquadro di navigazione compare un pulsante **Aggiorna**; un clic la installa.

- Compare solo quando lo Store ha davvero una versione più recente. Una build di sviluppo o installata a parte non lo vede mai, ed è normale.
- L'app si chiude durante l'installazione e si riavvia con la nuova versione, e il pulsante scompare. Se è in corso un'esportazione, chiede prima.
- Se non si installa, dice perché — solo Wi-Fi, batteria troppo scarica — e l'aggiornamento si può installare anche dal Microsoft Store.

## Qualcosa non va?

Scrivi a gaqo@outlook.com dicendo cosa stavi facendo e cosa ti aspettavi invece. Il numero di versione è nella pagina delle impostazioni.
