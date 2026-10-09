# Market Motion Studio

Tato aplikace mění ukazatele trhu akcií A na svislá videa pro telefon. Vyberete období, prohlédnete si náhled, dokud se dobře nečte, a exportujete MP4. Nic dalšího instalovat netřeba.

## Volba trhu

V nastavení se volí, z kterého trhu aplikace bere kurzy; výchozí jsou A-akcie. Změna se projeví po restartu aplikace.

- **A-akcie**: všech osm stránek je k dispozici.
- **Hongkong**: matice výnosů a kalendář fungují; závod sektorů běží na čtyřech subindexech Hang Seng; **údaj za celý trh neexistuje, proto je tato stránka skrytá**.
- **USA**: matice výnosů a kalendář fungují; závod sektorů běží na deseti sektorových ETF SPDR; stránka objemu má jen denní režim, protože minutový endpoint data pro USA nevrací; **částky jsou v dolarech a stránka obratu celého trhu je skrytá**.



## Přecházení mezi stránkami

Dvě tlačítka vlevo v záhlaví procházejí navštívené stránky zpět a vpřed, jako to dělá prohlížeč — **Alt+šipka vlevo** a **Alt+šipka vpravo**, nebo boční tlačítka myši.

- Stránka zůstává tak, jak jste ji opustili, takže návrat na ni vrací zvolené období a náhled ve stavu, v jakém byly, nikoli nově otevřenou stránku.
- Jako v prohlížeči: výběr nové stránky smaže to, co bylo před vámi.
- Fungují i se sbaleným navigačním panelem, tedy právě tehdy, kdy náhled potřebuje šířku nejvíce.

## Obrat trhu

Denní obrat celého trhu: částky souhrnných indexů Šanghaje a Šen-čenu sečtené, jeden sloupec na obchodní den.

- Zůstávají jen dny, kdy obchodovaly všechny zahrnuté trhy, aby svátek na jednom z nich nevypadal jako zhroucení součtu.
- Den, který se ještě obchoduje, se vynechává. Nedokončený den obsahuje jen svou otevírací aukci a nakreslil by se jako sloupec přilepený k ose.
- Nebo se dívat jen na jeden segment: každou burzu, každý hlavní trh, STAR, ChiNext. Hlavní trhy se počítají jako součet burzy minus růstový trh; BSE 50 zůstává měrou podle složek.
- Součet za celý trh dává jen trh A-akcií. Při volbě Hongkongu nebo USA se stránka z navigace odstraní.

- **Váš seznam.** Poslední položka menu je seznam, který si vedete — indexy a akcie vedle sebe,
  sdílený se čtyřmi roster tabulemi. Sčítat lze pouze pevninské kódy: obrat je uváděn v měně
  každého trhu, takže název z Hongkongu nebo New Yorku zůstane venku a stavový řádek řekne kolik.
  Den je na ose, pokud *někdo* z členů obchodoval; člen bez řádku pro tento den — pozastavený,
  nebo ještě nekótovaný — nepřidá nic. Je to záměrně opak pravidla tabulí výše: index se nikdy
  nepozastaví, akcie ano, a vypuštění dne by způsobilo, že pozastavení vypadá jako den, kdy se
  neobchodovalo nikde. Tato tabule své položky **sčítá**, takže kliknutím na název jej do součtu
  přidáte nebo vynecháte, a otevírá se pouze s **první**. Seznam bývá stavěný pro žebříčky, kde je
  tucet názvů běžný; tucet sečtený je číslo o nikom.
- **Změna pod košem** je rovnoměrně vážený průměr denních změn jednotlivých členů, každá proti
  vlastní předchozí zavírací ceně. Rovnoměrně vážený proto, že seznam není portfolio: není zde
  velikost pozice, podle které by se dalo vážit.
- **Jeden den, minutu po minutě.** Třetí forma je samostatné načtení: průběžný součet od otevření
  do zavření jediného dne. Zdroj drží jen posledních pět seancí, takže žádný rozsah nenabízí —
  obraz pojmenuje den, který nakreslil. Křivka končí v 15:00, protože půlhodina, kterou endpoint
  přidává poté, je after-hours obchodování, které denní číslo také neobsahuje. Čtyři karty jsou
  celkový součet dne a podíly dopoledne, odpoledne a poslední půlhodiny — graf toho, *kdy* se
  peníze pohybovaly, takže tři ze čtyř kart jsou podíly, ne částky. BSE 50 je jediná tabule, která
  vrací minuty bez sloupce obratu, a je odmítnuta, nikoli započtena jako nic.

## Svíčkový graf

Svíčky jednoho nástroje: denní, týdenní nebo měsíční — nebo minutové pro jeden zvolený obchodní den — kreslené čtyřmi způsoby, s průměry a objemem pod nimi.

- **Interval** určuje, jaké tržní období jedna svíčka pokrývá: den, týden nebo měsíc. Jeho změna načte data znovu, protože na zdroji jde o tři samostatné řady.
- **1, 5 a 15 minut** kreslí jeden obchodní den: seanci od otevření do závěru na ose podle hodin, která vynechává devadesát minut bez obchodování, takže dopoledne a odpoledne se potkají na tenké čáře, místo aby třetina obrázku zůstala prázdná. Zdroj uchovává minutové svíčky jen pro Šanghaj a Šen-čen a jen za poslední seance — zhruba čtyři dny při jedné minutě, sedmnáct při pěti, padesát při patnácti — takže **Obchodní den** je seznam dnů, které ještě má, a ne kalendář. Výběr jiného dne jen překreslí.
- **Způsob zobrazení** určuje, jak jsou tytéž čtyři ceny nakresleny: svíčky, OHLC sloupce, čára závěru nebo plocha závěru. Přepínání nic nenačítá.
- **Animace** je buď přicházení svíček jedna po druhé, dokud není celé období rozkreslené, nebo pevné okno, které se posouvá vpřed. Druhá z nich udrží svíčku na dlouhém období dostatečně širokou ke čtení a její šířka je nastavení **Okno**.
- **Posuvné okno se na konci otevře.** Se začátkem závěrečného úseku se okno rozšíří zpět až k prvnímu dni rozsahu, takže snímek, na kterém animace skončí, je celý rozsah, nikoli jeho poslední několik desítek dnů.
- Klouzavé průměry MA5, MA10 a MA20 lze položit přes svíčky; panel objemu dole lze vypnout a panel ceny místo získá zpět.
- Probíhající týden nebo měsíc je vynechán. Svíčka ze tří dnů není týden.
- Každý trh se čte na své upravené řadě, takže den štěpení akcií není nakreslen jako pokles, a dividenda také ne.
- **Rozsah** se řídí periodou: denní nabízí 3, 6 nebo 12 měsíců a 3, 5 nebo 10 let; týdenní 1, 3, 5 nebo 10 let; měsíční 3, 5 nebo 10 let nebo maximum, které zdroj má (asi 13). Jeden požadavek přinese asi 640 denních svíček a strana se vrací po stránkách, takže deset let — asi 2 500 svíček — se do toho vejde.
- **Dva nebo více nástrojů udělají ze záběru srovnání.** Jména ve tvém seznamu jsou přepínače: zapni druhý a záběr přestane kreslit svíčky — ceny dvou nástrojů nemají žádnou osu, kterou by mohly sdílet — a místo toho nakreslí, co každý z nich udělal, jako kumulativní procento. Každá křivka je pojmenována na svém vlastním předním konci, s tím, jak je v zobrazovaném okamžiku napřed nebo pozadu. V minutových periodách jsou všechny nakresleny v jeden obchodní den: **Obchodní den** vypisuje ty, které mají všechny společné, ve výchozím stavu nejnovější celou seanci, a křivky se měří od **předchozího závěru** — číslo na konci je tedy denní změna každého nástroje.
- **Několik nástrojů může sdílet jeden graf, nebo mít každý svůj.** Při **Rozvržení** nastaveném na „graf pro každý” dostane každý nástroj vlastní panel, pod sebou, s osou škálovanou na vlastní rozsah a s nulovou linií uvnitř; osa x a data jsou společné a kreslí se jednou, pod spodním panelem. Dělené zobrazení zvládne tři, takže při více než třech vybraných se kreslí první tři v pořadí seznamu a zbytek se vypíše ve stavovém řádku. Přepnutí mezi oběma rozvrženími nic nenačítá znovu. V obou případech je dole v rámu jedna karta na nástroj: velkým písmem jeho **změna za období** a pod ní, o kolik bodů — nebo o kolik peněz — se pohnul; stejné číslo, jaké ukazuje popisek na konci jeho křivky.
- **Pás na pravé straně lze uvolnit, chcete-li šířku.** Ve výchozím nastavení je vypnutý: platforma kreslí svůj avatar a tlačítka „to se mi líbí“ a komentářů na té straně svislého videa a svíčky a konce křivek nakreslené pod nimi jsou na telefonu skryté, přestože jsou tu zcela čitelné. Zapnutý: oba obrazy, které tato stránka kreslí, jdou až k vlastnímu okraji záběru — svíčky až k němu a s nimi jméno a číslo na konci srovnávací křivky; posuvné okno drží odstup, dokud je oknem, a spolu s oknem se rozevře na plnou šířku.
- **Srovnání říká, který úsek času zobrazuje.** Dva řádky pod nadpisem: minutové periody uvádějí ten **jeden obchodní den** a pod ním — velikostí nadpisu a spolu s pohybem obrazu — **čas, kterého obraz právě dosáhl**; denní, týdenní a měsíční periody uvádějí **první a poslední den** rozsahu. Tyto dva řádky přidávají jen obrazy s více nástroji —— obraz s jedním nástrojem už nese datum kreslené svíčky ve své hlavičce.

## Objem a obrat

Objem jedné akcie proti její míře obratu, ve dvou panelech nad sebou.

- Mezi obchodními dny jsou objem a míra obratu proporcionální, takže oba panely mají téměř stejný tvar. V průběhu jednoho dne vypadají minutový objem a kumulovaný obrat skutečně jinak, a to je zajímavější obrázek.
- Zdroj vnitrodenních dat drží jen posledních několik obchodních dní, takže tento režim nabízí právě je, a ne libovolné datum.
- Minutová data jsou k dispozici jen pro A-akcie a Hongkong; v USA se tento režim nenabízí.
- U denních dat je rozsah 1, 3, 6, 12 nebo 24 měsíců, nebo vlastní datum začátku a konce; vlastní rozsah končí asi na 900 kalendářních dnech — tolik vrátí jeden požadavek — a výběr data končí tamtéž. V intradenním režimu si vybíráte jeden z několika dostupných dnů.

## Závod sektorů

![Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.](media/sector-race.png)

Sada sektorů nebo akcií nakreslená jako vodorovné pruhy, které se předhánějí, a pořadí se mění až do posledního snímku.

- Dvě míry: procentní změna období a jeho objem v stovkách milionů juanů. Přepnutí míry jen přebarví stejná data; znovu se nenačítají.
- Čtyři seznamy: odvětví Shenwan úrovně 1, populární témata, vlastní (zaškrtnout) a jednotlivé akcie (přidat hledáním). Vlastní seznam začíná naplněný odvětvími Shenwan úrovně 1.
- Vestavěné seznamy se řídí trhem: obory Shenwan úrovně 1 a populární témata u A-akcií, čtyři subindexy Hang Seng u Hongkongu, deset sektorových ETF SPDR u USA. Vlastní seznam a seznam akcií jsou na každém trhu.
- Období může být 1, 3, 6, 12 nebo 24 měsíců, nebo vlastní počáteční a koncové datum. Vlastní rozsah sahá přibližně 900 dní — tolik zvládne jeden požadavek — a výběr dat tam končí.
- Seznam má minimální a maximální počet položek — málo pruhů není závod, příliš mnoho se slije.




## Závod tržních kapitalizací

Patnáct největších společností daného trhu jako vodorovné pruhy seřazené podle tržní
kapitalizace; pořadí se mění až do posledního snímku. Vzorkování po měsících.

- **Žebříček se v každém období počítá znovu.** Načtení se nejprve zeptá zdroje na dnešní žebříček
  podle kapitalizace, vezme prvních dvě stě jako sestavu a přidá velké tituly, které v žebříčku
  bývaly a vypadly z něj; každé období pak ukáže patnáct největších z této sestavy. Členové tedy
  skutečně přibývají a ubývají — v roce 2016 to byla ropa a banky, v roce 2026 přibyly 茅台,
  宁德时代 a 工业富联. Sestava zapsaná v programu minula společnost, která vstoupila na burzu a
  rovnou se dostala na špičku; sestava se teď ptá, místo aby si pamatovala.
- **Dřívější kapitalizace se počítá**: dnešní kapitalizace krát upravený poměr cen za období.
  Emise a štěpení se v upravené řadě vyruší; dividendy ne — reinvestují se, takže dřívější hodnota
  štědrého plátce vychází nízko. Přímo ze zdroje je jen číslo posledního snímku.
- **Společnost, která ještě nebyla na burze, roste od nuly**: tituly uvedené v roce 2018 stoupají
  ze základní linie v den vstupu, místo aby držely místo předem.
- **Interval je měsíc, ne den** — sto dvacet období za deset let, dvanáct za rok, a záhlaví snímku
  počítá měsíce. Žebříček podle kapitalizace je pomalá veličina a měsíční vzorek získá celou
  historii jedním dotazem.
- **Každý trh má svých patnáct.** Ty tři se nikdy nemíchají: jejich peníze nejsou tytéž peníze.
- Rozsah je posledních 12 měsíců, 3, 5 nebo 10 let, nebo **Nejdelší** — jeden požadavek vrátí všech 180 měsíčních období, asi patnáct let, a tam tato položka končí. Lze zadat i vlastní datum začátku a konce.
  Hongkong a New York mají pevnou sestavu, protože jim žádný žebříček dostupný této aplikaci
  neposlouží.





## Historie tržní hodnoty

Tržní hodnota jedné akcie v oběhu den po dni a pod ní cena akcie na stejné časové ose. Nebo více firem najednou — každá jednou linií, pojmenovanou na konci.

- **Hodnota je dopočítaná, ne uvedená.** Zdroj nemá historický počet akcií pro žádný den. Vyplývá z míry obratu, což je objem jako podíl akcií v oběhu — takže `objem ÷ míra obratu` *je* tento počet a hodnota je denní cena krát tento počet.
- **Pás na pravé straně lze uvolnit, chcete-li šířku.** Ve výchozím nastavení je vypnutý: platforma kreslí svůj avatar a tlačítka „to se mi líbí“ a komentářů na té straně svislého videa a číslo pod nimi je na telefonu skryté, přestože je tu zcela čitelné. Zapnutý: panely kreslí až k vlastnímu okraji záběru a graf je široký jako záběr.

- **Počet je medián dvaceti dnů.** Míra přichází se dvěma desetinnými místy, takže jeden den nese asi procento šumu, zatímco počet akcií je schodiště: hýbe se při emisi nebo zpětném odkupu a jinak stojí. Medián ponechá stupeň na dni, kdy vznikl.

- **Počítají se jen akcie obchodované na tomto trhu.** Ty, které firma kotuje jinde, zůstávají venku, takže firma kotovaná ve dvou místech leží pod „celkovou tržní hodnotou” z aplikace s kurzy — tam se ony akcie oceňují cenou tohoto trhu. Rozdíl u ICBC tvoří výhradně akcie H. Venku jsou i akcie dosud vázané blokací.

- **V Hongkongu je cena průměrná obchodní.** Tamní trh nedává neupravený závěr, takže cena je objem peněz dělený objemem akcií a dolní panel se jmenuje „průměrná obchodní cena“.

- **New York dělí všemi akciemi, ne těmi obchodovanými.** Jeho míra je podílem všech akcií firmy, včetně akcií zasvěcených osob, takže linie je tam celkovou hodnotou, ne hodnotou v oběhu: počet převyšuje cifru z aplikace přesně o podíl těch osob — u Apple o nic, u NVIDIA o 4 %, u Tesly o 12 %. Dosáhne až do roku 2009, stejně hluboko jako pevnina.

- **Desetiletá křivka vypadá, jako by jednou spadla na nulu — nespadla.** Osa musí pojmout vrchol, takže raný úsek v hodnotě desetiny leží pár pixelů nad základnou: 853 億 u 五粮液 proti vrcholu 13 097 億 je méně než sedm procent jeho výšky. Proto značky minima a maxima nesou vlastní číslo: holý bod tam dole se čte jako nula.

- **Číslo jede po čáře.** Štítek na konci každé čáry pojmenuje firmu a ukáže hodnotu, které v tu chvíli dosáhla, a pohybuje se s animací — posuňte jezdec a pojede s čárou. U jedné firmy má každý panel jeden, hodnotu a cenu, a velké číslo nad panelem říká totéž číslo; u několika jsou štítky zároveň tím, co od sebe čáry rozezná.

- Rozsah: jeden, dva, pět nebo deset let, anebo dvě vlastní data.

Porovnejte více firem najednou. Při více než jednom zapnutém čipu má každá svou linii, pojmenovanou na konci. Ceny více firem nesdílejí poctivou cenovou osu — dejte 贵州茅台 vedle 京东方A a jedna z nich je plochá čára u spodního okraje —, takže dolní panel ustoupí a celý rám patří tržní hodnotě. Až šest; sedmá je odmítnuta, ne potichu vynechána, protože graf ze šesti ze sedmi zaškrtnutých firem odpovídá na seznam, který nikdo nevybral.

Osa hodnoty má dva výklady. Absolutní říká, která firma má větší hodnotu; přepočtená na 100 v první den každé z nich říká, čí hodnota rostla rychleji, a je to jediný čitelný výklad, když je jedna násobkem druhé. V obou případech je osou dat sjednocení jejich dnů, ne průnik: průnik by zkrátil desetileté srovnání na úsek toho, kdo na burzu vstoupil nejpozději.



## Prémie A/H

O kolik je kontinentální kotace společnosti dražší než její hongkongská — u společností
kotovaných na obou stranách, měsíc po měsíci, jako pruhy, které se předhánějí.

- **Prémie = kurz A ÷ (kurz H × HKD/CNY) − 1.** Nic se tu nepočítá: obě strany jsou kurzy skutečně
  zaplacené ve stejný okamžik, a proto tato stránka jako jediná načítá **neupravené** kurzy. Zpětně
  upravená řada nafukuje nedávné kurzy a dva trhy upravené odděleně srovnávat nelze — akcie A ICBC
  stojí na obrazovce 8,28 a upravená řada hlásí 13,34, čímž se prémie +26 % změní na +245 %.
- **Stejný rozdíl se píše dvěma směry.** Tato stránka uvádí A vůči H, tedy obvyklou formu: +194 %
  znamená, že kontinentální akcie stojí téměř třikrát více než hongkongská. Některé služby ukazují
  stejné číslo obráceně (溢价(H/A)) a pro 新华制药 dají týž den −66 %. Je to stejný fakt
  (1 ÷ (1 − 0,66) − 1 = 1,94), ne jiný kurz ani chyba.
- **Kreslí se patnáct nejdražších**, takže pruhy rostou doprava — i patnáctá měla přes dvacet
  procent. Jen dva ze šedesáti devíti jdou opačně, jejich akcie H nad akciemi A, a oba stojí na
  konci seznamu, kam obraz nedosáhne.
- **Čím delší období, tím méně společností se vejde.** Kandidátů je šedesát devět známých dvojích
  kotací, ale kreslí se jen pár, jehož obě strany pokrývají celé období: hongkongská kotace mladší
  dvou let vypadne.
- **Vzorkování po měsících.** „Nejdelší" je asi devět let a hranicí je řada kurzu, která sahá jen do
  roku 2016. Tři strany uzavírají měsíc v různých dnech, proto se seskupuje po kalendářním měsíci a
  bere se poslední kurz měsíce, místo protnutí podle data.
- **Seznam je vestavěný.** Ani jeden zdroj neodpovídá na „které kontinentální kotace mají i tu
  hongkongskou". Zato je ověřitelný: každý pár byl 2026-10-02 znovu přečten ze zdroje a 海通证券 je
  to, co tato kontrola odstranila (akcie H vyřazeny po fúzi do 国泰海通).

## Extrémní dny

Jeden nástroj a dny, kdy se pohnul nejvíce — vodorovné pruhy seřazené podle velikosti.
**Řádky této tabulky jsou dny, ne firmy**, co žádná jiná strana nedělá: hodnotou řádku je pohyb
onoho dne proti závěru předchozího obchodního dne, a jakmile ten den nastane, hodnota se už nezmění.

- **Pohyb je změna upravené závěrečné ceny.** Upravené, protože den odpočtu dividendy není krach:
  toho rána cena klesne o dividendu a neupravená řada by ten den postavila na vrchol největších
  pádů historie, přestože nikdo nic neztratil.
- **Řazeno podle velikosti, ne podle znaménka.** −7,7 % a +8,1 % jsou pohyby stejné velikosti, a
  tak stojí vedle sebe; řazení podle hodnoty se znaménkem by každý pokles odsunulo pod každý růst.
  Pruhy proto rostou oběma směry: **růst doprava, červeně; pokles doleva, zeleně**.
- **Den se počítá, až když nastane.** Kandidáty je dvacet čtyři největších pohybů období a snímek
  kreslí patnáct největších z nich; den se řazení neúčastní, dokud nepřijde jeho datum, takže se
  tabulka zaplňuje s léty místo aby byla plná od začátku.
- **Jakýkoli nástroj, který trh kotuje, nejen široké indexy.** Napište kód, název nebo pinyin do
  vyhledávání: jedna akcie a burzovně obchodovaný fond patří na tuto tabuli stejně jako index,
  a seznam pod ním je jen zkratka k obvyklým. Změna trhu tento seznam vymění a ponechá stranou
  nástroj z jiného trhu; volba nástroje nebo rozsahu uloží jen předvolbu — nic se nestahuje, dokud
  nestisknete 取数.
- **Nejdelší období je asi třicet pět let**, což je mez zdroje: jedna žádost nese asi 640 denních
  svíček a vracení se provede nejvýše dvacetkrát. Období kratší než šedesát obchodních dnů je
  odmítnuto — největší den klidného měsíce není fakt hodný tabulky.
- **Datum nahoře ve snímku je časová osa** a pruh pod ním je průběh. Hlavičková řada nese období,
  počet obchodních dnů a počet kandidátních dnů.

## Měnové koridory

Jeden řádek na pár a **ten řádek je sám koridor**: jeden konec je nejnižší úroveň, na které
pár ve zvoleném období byl, druhý nejvyšší, a značka je dnešní kurz. Tahle tabule se tedy liší od
ostatních — jinde délka pruhu říká *kolik*, tady řádek v každém snímku zabírá celou šířku a pohybuje
se značka spolu s koridorem kolem ní.

- **Koridor se rozšiřuje.** Jeho stěny jsou nejnižší a nejvyšší **dosud**, ne za celé období. Měsíc,
  který zajde dál než všechny předchozí, vytlačí jednu ze stěn ven, a pár na 100% je nejdráž, jak kdy
  byl — ne na nějakém limitu.
- **Každý pár se měří vlastním rozpětím.** 157,92 u USD/JPY a 1,1245 u EUR/USD nejsou dva body na
  jedné stupnici; teprve normalizace umožní šesti párům stát na jednom obraze. Cenou je, že úzký a
  široký koridor vypadají stejně — proto jsou obě hodnoty vypsány pod každým řádkem.
- **Měsíční svíčky, bez úprav.** Měna nemá dividendu ani rozdělení, které by se upravovalo, a stránka
  jde stejnou neupravenou cestou ke zdroji jako stránka A+H.
- **Pokrytí se liší, a proto jsou dvě nabídky**: USD/CNY sahá do roku 2005, ostatních pět párů
  renminbi do roku 2016; hlavní crosy začínají všechny v roce 2005-07 a nesou 325 měsíců. Na jedné
  tabuli by se četlo, kdy zdroj který pár začal kotovat.
- **Nastavení trhu se tu neuplatní**: měnový pár nepatří žádné burze a tabule je stejná, ať platí
  kterýkoli trh.
- Nejdelší období je asi dvacet let, což je měsíční pokrytí zdroje; méně než dvanáct měsíců je
  odmítnuto — to je pár týdnů pohybu, ne koridor.

## Závod indexů

Jeden řádek na index a řádek je **jak daleko se ten index dostal od svého prvního měsíce
v rozmezí** — ne jeho úroveň. 3 800 na Shanghai Composite a 5 700 na S&P 500 nejsou dva body na jedné
stupnici; kreslit úrovně by byla tabule o tom, kde který index začal počítat.

- **Index, který přijde později, na tabuli není, dokud nepřijde.** S&P sahá do roku 1950, Dow jen do
  2009 a index Hang Seng Tech začíná v roce 2020. Chybí, nestojí na 0,00 % — tam by se zařadil nad
  každý index, který kdy klesl, a četlo by se to jako trh, kde se nic nestalo.
- **Měsíčně, a nyní ajustováno.** Index nic nevyplácí, ale akcie platí dividendy a dělí své
  podíly: Apple ukazuje +193 % za deset let neajustovaně a +1183 % ajustovaně, protože
  neajustovaná čára nese srázy, z nichž žádný držitel nikdy nespadl. Indexů se to nedotkne —
  požádán o úpravu odpoví zdroj indexu týmiž řádky jako vždy, a všech dvanáct vyšlo na obou
  cestách identicky. Co tabule nese nyní, je rozdíl, který stojí za řeč: řádek indexu je
  **cenový** výnos, protože index není pozice, zatímco řádek akcie je výnos **celkový**, s
  dividendami a děleními zpět uvnitř.
- **Nastavení trhu tuto stránku neřídí**: čte tři trhy najednou a změna trhu ji nezmění. Lze vzít šest
  z pevniny, tři z Hongkongu, tři z New Yorku nebo všech dvanáct.
- Nejdelší období omezuje měsíční strop zdroje — 430 svíček, asi třicet pět let; méně než dvanáct
  měsíců je odmítnuto: to je sprint, ne dlouhý běh.
- **Nebo vlastní seznam.** Poslední skupina v menu je vlastní seznam: napište kód, název nebo
  pinyin a přidejte jeden, a cenný papír z pevniny, z Hongkongu a z New Yorku mohou být na něm
  zároveň — tato tabule se nikdy neptá na nastavení trhu. Jeden seznam pro čtyři tabule: akcii
  přidanou zde najdete i v závodu aktiv, v poklesech a v úspěšnosti držení. Pod tři se stahování
  odmítne.

## Třídy aktiv

Jeden řádek na třídu aktiv a řádek je **co držení vyneslo** — ne kotace. Všech osm jsou fondy
kotované na kontinentální burze, koupené za stejné peníze, takže je lze srovnávat přímo.

- **Dividendy jsou zpět započteny, a štěpení také.** Dluhopis a fond peněžního trhu platí téměř
  celou výnosem: cena fondu peněžního trhu šla za třináct let ze 100,161 na 100,901, což je bez
  úpravy +0,0 % — a nakreslilo by na konec tabule jediný řádek, který nikdy neklesl. Fond po
  štěpení podílů je ještě výraznější: ETF Nasdaq má bez úpravy +136 %, zatímco index, který sleduje,
  ve stejném desetiletí vzrostl šestinásobně.
- **Záměrně opak závodu indexů.** Index nevyplácí dividendu, takže tamta stránka zůstává bez úprav;
  fond vyplácí, takže tato se upravovat musí. Ty dvě cesty se nemíchají.
- **Dva zahraniční řádky nesou kurz.** ETF Nasdaq a Hang Seng jsou kotovány v jüanech, takže měna je
  už uvnitř — přesně to, co držitel z pevniny skutečně dostal.
- **Začátky se liší.** Nejstarší řádek začíná v roce 2012 a komoditní fond až v roce 2019. Řádek,
  který ještě nenastoupil, chybí — nestojí na 0,00 %.
- **Nastavení trhu tuto stránku neřídí**: všech osm je kotováno na pevnině. Méně než dvanáct měsíců
  je odmítnuto.
- **Nebo vlastní seznam.** Poslední skupina v menu je vlastní seznam: napište kód, název nebo
  pinyin a přidejte jeden; tři trhy na něm lze míchat. Jeden seznam pro čtyři tabule: akcii
  přidanou zde najdete i na dalších třech; stahuje se ajustovaně, přesně jako osm fondů, takže
  dividendy a dělení jsou v čísle. Pod tři se stahování odmítne.

## Trh dluhopisů

Jeden řádek na dluhopisový index a pruh je **změna ceny** — co není totéž co to, co držení vyneslo.

- **Kupón v čísle není.** Všech devět řádků jsou indexy a zdroj u indexu ignoruje parametr úpravy,
  takže se vrací kotace. Dluhopis vyplácí většinu výnosu jako kupón a kupón se v kotaci nikdy
  neobjeví: držitel si vydělal víc, než tato tabule ukazuje, a na každém řádku o jinou částku.
- **Záměrně opak závodu tříd aktiv.** Tamtato tabule se kreslí z upravené řady, protože fond
  vyplácí; tato zůstává netknutá, protože index nevyplácí. Obě tabule nelze číst jednu proti druhé.
- **Devět řádků a seznam je vestavěný**, ne takový, který si udržujete sami. Chtěl se index CSI
  „všech dluhopisů“ a na tomto zdroji neexistuje: kód, který se mu podobá, je index oddělených
  dluhopisů Šanghaj, jehož měsíční řada končí v srpnu 2015, a prohledání celého prostoru kódů
  indexů nenašlo žádný celkový dluhopisový index. Tato místa připadla nejhlubším úvěrovým indexům,
  na které zdroj odpovídá.
- **Začátky se liší.** Nejstarší řádek začíná 2003-02 a konvertibilní index Šen-čen až 2014-08, takže
  na desetiletou tabuli nastupuje o pět let později. Řádek, který ještě nezačal, chybí — nestojí na
  0,00 %.
- **Měsíčně**, jeden pruh na měsíc, a nastavení trhu tuto stránku neřídí. Méně než dvanáct měsíců je
  odmítnuto.
- **Začíná prvním celým měsícem v rozsahu.** Zdroj odpovídá jen v celých měsících a měsíční
  sloupec *je* ten celý měsíc: začne-li rozsah uprostřed měsíce, tento neúplný měsíc se nepočítá —
  přehled startuje od následujícího celého měsíce. Proto „posledních 10 let" kreslí 119 měsíců
  místo 120: ten chybějící leží mimo rozsah. Dvě data v záhlaví jsou skutečný začátek a konec.
- **Tři skupiny**: všech devět, šest klasických dluhopisů bez konvertibilních a tři konvertibilní.

## Poklesy

Řádek je **jak hluboko pod vlastním maximem se nástroj nachází** — ne kolik vydělal, ale co stálo
to vydělat. Týchž osm nástrojů jako v závodu tříd aktiv, ale měřených vůči sobě samým, ne proti
sobě navzájem.

- **Křivka je to podstatné.** Všude jinde v této aplikaci se hodnota kreslí jako délka, a délka
  umí říct jen to, jak hluboká je voda v tomto okamžiku. Hloubka je tvar v čase: minimum a cesta
  ven z něj jsou dvě místa na křivce a vzdálenost mezi nimi napříč snímkem je počet měsíců, které
  uplynuly.
- **Obě čísla nestoupají společně.** Za posledních deset let fond Nasdaq klesl o 25,52 % a byl
  zpět na úrovni za šest měsíců; fond CSI 500 klesl o 56,07 % a potřeboval osmdesát šest. Vytištěno
  jako jedno číslo vypadá druhé jako zostřená verze prvního — a není.
- **Jedna stupnice hloubky pro celou tabuli.** Škálovat každý řádek podle jeho vlastního nejhoršího
  okamžiku by nakreslilo 0,2 % fondu peněžního trhu jako propast velikosti 56 % CSI 500 — na tabuli,
  jejíž celý smysl je říct, že tyto dvě věci nejsou srovnatelné. Ten řádek je proto rovná čára
  přilepená na svou linii maxima — a **ta rovnost je přesně to, co říká**.
- **S úpravou, měsíčně a od vlastního prvního měsíce**, z důvodů, které uvádí závod tříd aktiv:
  výnosy fondu se v jeho ceně nikdy neobjeví a nástroj, který přichází až v roce 2019, se neměří
  proti maximu, které neměl.
- **Řádky stále závodí.** Jsou seřazeny podle vzdálenosti od vlastního maxima — nejblíže vlastnímu
  maximu nahoře — a vyměňují si místa, jak měsíce plynou.
- **Zlato a komoditní fond byly při tomto měření stále pod vodou** — tabule hlásí takový pokles jako
  otevřený, protože období skončilo dřív, než byl napraven.
- **Nebo vlastní seznam.** Poslední skupina v menu je vlastní seznam: napište kód, název nebo
  pinyin a přidejte jeden; tři trhy na něm lze míchat. Jeden seznam pro čtyři tabule: akcii
  přidanou zde najdete i na dalších třech; stahuje se ajustovaně, přesně jako osm fondů, takže
  dividendy a dělení jsou v čísle. Pod tři se stahování odmítne.

Neřídí se nastavením trhu: všech osm je kótováno na kontinentální burze. Méně než dvanáct měsíců
v období je odmítnuto.

## Úspěšnost

Řádek je **podíl uzavřených vstupů, které vydělaly** — ze všech měsíců, v nichž se dalo vstoupit a
držet stejně dlouho, ta část, která skončila v plusu. Týchž osm nástrojů jako v závodu tříd aktiv a
na tabuli poklesů, hodnocených podle toho, jestli jejich držení fungovalo, ne podle toho, kolik
vynesly.

- **Jeden vstup je náhoda; osmdesát čtyři je míra.** Každý měsíc období je vstup a každý je držen
  stejně dlouho, takže tříleté držení v průběhu deseti let je osmdesát čtyři vstupů na řádek, ne
  jeden. Sdílejí měsíce a v tom je pointa: zredukovat je na tři nezávislé by ponechalo míru se
  třemi pozorováními uvnitř.
- **Vstup se počítá od měsíce, v němž končí.** To, co je koupeno v posledních třech letech období,
  ještě neskončilo, a započítat neskončený vstup jako ztrátu by na konci ohne každý řádek dolů
  jenom kvůli kalendáři. Tabule proto začíná prvním měsícem, v němž vstup mohl skončit.
- **Řádek nastupuje, jakmile skončí šest vstupů.** Jeden vstup je 0 % nebo 100 %, a kterákoli z těch
  dvou cifer na konci pořadí je konec, který si nezasloužil.
- **S úpravou, měsíčně a od prvního vlastního měsíce každého nástroje**, z důvodů, které uvádí
  závod tříd aktiv: distribuce fondu se v jeho ceně nikdy neobjeví a fond založený v roce 2019 nemá
  žádné vstupy z roku 2016, které by mohl vyhrát nebo prohrát.
- **Doba držení je jediná nová volba na této tabuli.** Jeden rok a pět let ve stejných deseti letech
  jsou dvě různé otázky se dvěma různými odpověďmi a osm řádků se mezi nimi přerovná.
- **Řádky stále běží.** Řadí se podle své míry — nejčastěji v plusu nahoře — a vyměňují si místa,
  jak měsíce plynou.
- **Nebo vlastní seznam.** Poslední skupina v menu je vlastní seznam: napište kód, název nebo
  pinyin a přidejte jeden; tři trhy na něm lze míchat. Jeden seznam pro čtyři tabule: akcii
  přidanou zde najdete i na dalších třech; stahuje se ajustovaně, přesně jako osm fondů, takže
  dividendy a dělení jsou v čísle. Pod tři se stahování odmítne.

Měřeno za posledních deset let s tříletým držením: fond Nasdaq byl v plusu při všech osmdesáti
čtyřech vstupech a fond z Hongkongu při čtyřiceti procentech z nich — dva řádky, které závod tříd
aktiv odděluje deseti lety celkového výnosu a tato tabule odděluje tím, jestli se vůbec povedlo
vstoupit.

Neřídí se nastavením trhu: všech osm je kótováno na kontinentální burze. Méně než dvanáct měsíců
v období je odmítnuto.

## Matice výnosů

![Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.](media/monthly-matrix.png)

Měsíční pruhy rozložené do mřížky: režim roku ukazuje sezónnost nástroje za desetiletí, režim porovnání staví několik nástrojů vedle sebe, aby ukázal rotaci.

- Režim roku: vyberte nástroj (hledání nebo předvolený široký index); rozsah je 1–10 let nebo vše. Jeden požadavek vrátí desetiletí měsíčních pruhů.
- Režim porovnání: 2–14 nástrojů ze seznamu (odvětví úrovně 1 / témata / široké indexy / vlastní / akcie) vedle sebe, na 6–48 měsíců.
- Mřížka se rozsvěcuje buňku po buňce v časovém pořadí; na konci ukáže nejsilnější a nejslabší měsíc rozsahu a další statistiky.
- Měsíční data pokrývají desetiletí najednou, takže zde není denní limit dní — ale příliš mnoho nástrojů vyjde z rámečku.

## Kalendář zisků a ztrát

![Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.](media/gain-calendar.png)

Libovolná čínská akce nebo index, jeho denní růst nebo pokles rozložený do kalendářních buněk podle měsíců: červená při růstu, zelená při poklesu.

- Hledejte podle kódu, názvu nebo pinyinu; předvolby jsou široké indexy. Podporovány jsou jen nástroje zvoleného trhu.
- Seznam oblíbených se sdílí se stránkou akcií aplikace — oblíbený přidaný na kterékoli straně se zobrazí v obou.
- Období je 1, 3, 6 nebo 12 měsíců, nebo vlastní; jeden nástroj je stále vázán limitem asi 640 kalendářních dní.
- Závěrečné statistiky uvádějí počet růstových a poklesových obchodních dní.

## DCA plán

![Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.](media/dca-plan.png)

Nákup jednoho nástroje za pevnou částku v pevných intervalech — každý obchodní den, každý týden nebo každý měsíc — a animace toho, čeho disciplína dosáhla. Několik plánů může sdílet jeden obraz: po jedné čáře hodnoty na každý, s běžným ziskem na jejím konci.

- Nástroje pocházejí z **vašeho seznamu**, téhož, který sdílejí ostatní tabule: napište kód nebo název a přidejte jej; přepínač na každém chipu rozhoduje, zda je na tomto obraze, a × jej odebere ze sdíleného seznamu (a tím i z ostatních tabulí). Řádek na jeden klik jde za trhem — široké a zlaté ETF u A-akcií, hongkongské trackerové fondy, ve USA SPY, QQQ a GLD — a stisk tento název přidá a hned ho vykreslí.
- **2 až 6 plánů na jednom obraze.** Každý vkládá stejnou částku ve stejném rytmu a nakupuje od svého prvního obchodního dne. Kreslí se jen čáry hodnoty: šest výplní přes sebe je bláto, a při stejné částce a rytmu leží šest čar vkladů přesně na sobě — proto se čára vkladů kreslí jednou, pro plán, který vložil nejvíc, protože kreslit tu s nejmenším vkladem by ostatní ukazovala lepší. Datová osa je sjednocením jejich dnů: nástroj uvedený později prostě začíná později a předtím tam není. Šest je strop — nad ním získání odmítne, místo aby potichu nakreslilo některé z nich — a nástroj z jiného trhu zůstane venku. U několika plánů se velké číslo uprostřed stává výnosem v procentech **vedoucího** plánu, ne jeho penězi: pozdější kótování vložilo méně, a vydělat méně není totéž co být horším plánem.
- **Číslo jede na čáře.** Štítek na konci každého plánu jej pojmenuje a uvede peníze, o které je v daném okamžiku napřed; pohybuje se s animací — potáhněte lištou a půjde s čarou. U jednoho plánu je velké číslo uprostřed stále výnosem v procentech a štítek je tam přesto.
- Částku a frekvenci si nastavíte sami; období je tři, pět nebo deset let, nebo tak daleko zpět, jak jsou data k dispozici (zhruba třináct let).
- Výnos se počítá na zpětně upravených cenách, bez poplatků. Výsledek popisuje řadu cen, nikoli účtenku, kterou by někdo mohl realizovat.
- Kromě 3, 5 a 10 let a nejdelšího období lze zvolit i **Vlastní**: zadejte počáteční a koncové datum a stiskněte načtení dat. Dostupných je asi 35 let zpět — zdroj vrací zhruba 640 kalendářních dnů na jeden požadavek a průchod jich provede nejvýše dvacet.
- **Dva způsoby animace.** *Celé období* rozloží celý rozsah najednou; *posuvné okno* drží okno s pevným počtem obchodních dnů a posouvá je od začátku do konce rozsahu — jen tak zůstanou výkyvy dlouhé denní řady čitelné. Okno má význam jen při posouvání a oba způsoby čtou **stejné kurzy** — přepnutí nic nenačítá. **Svislá osa se pro okno nepřepočítává**: odstup mezi oběma čarami *je* výsledkem plánu, a přepočet by ho roztáhl spolu s oknem.
- **Posuvné okno se na konci otevře.** Se začátkem závěrečného úseku se okno rozšíří zpět až k prvnímu dni rozsahu, takže snímek, na kterém animace skončí, je celý rozsah, nikoli jeho poslední několik desítek dnů.
- **Pás na pravé straně lze uvolnit, chcete-li šířku.** Ve výchozím nastavení je vypnutý: platforma kreslí svůj avatar a tlačítka „to se mi líbí“ a komentářů na té straně svislého videa a číslo pod nimi je na telefonu skryté, přestože je tu zcela čitelné. Zapnutý: záběr, který vyplňuje celý rozsah, kreslí od první snímku až k vlastnímu okraji záběru; posuvné okno drží odstup, dokud je oknem, a spolu s oknem se rozevře na plnou šířku — snímek, na kterém video skončí, je tedy celý rozsah od okraje k okraji.

## Výnos pozice

![Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.](media/position.png)

Jeden nákup, držený dlouho — milion do stejného nástroje od roku 2015 — animovaný tak, aby ukázal, co léta udělala s hodnotou a výnosem. Několik pozic může sdílet jeden obraz: po jedné čáře na každou, s běžným ziskem na jejím konci.

- Pozice pocházejí z **vašeho seznamu**, téhož, který sdílejí ostatní tabule: napište kód nebo název a přidejte ji; přepínač na každém chipu rozhoduje, zda je na tomto obraze, a × ji odebere ze sdíleného seznamu (a tím i z ostatních tabulí). Řádek na jeden klik jde za trhem — 中国平安 a 贵州茅台 pro pevninu, 腾讯, 汇丰 a 盈富基金 pro Hongkong, Apple, Berkshire a SPY pro New York — a stisk tento název přidá a hned ho vykreslí.
- **2 až 6 pozic na jednom obraze.** Každá je koupena jednou, za stejnou částku, ve svůj vlastní první obchodní den, takže jsou čáry přímo srovnatelné a vzdálenost mezi dvěma z nich je v každém datu odpovědí na „kam to bylo lepší dát“. Datová osa je sjednocením jejich dnů: nástroj kótovaný později prostě začíná později a předtím tam není, místo aby byl vykreslen vodorovně na úrovni vkladu. Šest je strop — nad ním načtení odmítne, místo aby jich pár tiše vykreslilo — a pozice z jiného trhu zůstává vynechána, protože částky jsou zde v měně platného trhu.
- **Číslo jede po čáře.** Štítek na konci každé pozice ji pojmenuje a ukáže, kolik v tu chvíli vydělala, a pohybuje se s animací — posuňte jezdec a pojede s čárou. U jedné pozice zůstává velké číslo uprostřed výnosem v procentech; u několika se stává částkou, kterou vydělala **vedoucí**, s jejím jménem pod tím, a závěrečné karty jsou po jedné na pozici místo čtyř čísel o jedné.
- Počáteční kapitál a doba držení jsou na vás; doba může být tři, pět nebo deset let, nebo až tam, kam data sahají (zhruba třináct let).
- Výnos se počítá ze zpětně upravených cen — dividendy reinvestovány, bez poplatků. Zpětná úprava kotví u prvního dne emise a hromadí dividendy dopředu, takže rané roky štědrého plátce nikdy nejsou nekladné, jak se může stát u dopředné úpravy.
- Stejné **Vlastní** období platí i pro držbu: zadejte dvě data a stiskněte načtení dat. Pokud byl nástroj uveden na trh později, než je zadané datum, držba začíná jeho prvním obchodním dnem.
- **Dva způsoby animace.** *Celé období* rozloží celý rozsah najednou, takže tvar křivky na obrazovce je její tvar v čase. *Posuvné okno* drží okno s pevným počtem obchodních dnů a posouvá je od začátku do konce rozsahu — jen tak zůstanou výkyvy dlouhé denní řady čitelné, protože rozložená na dvanáct let jsou tři měsíce poklesu dva pixely. Okno má význam jen při posouvání a oba způsoby čtou **stejné kurzy** — přepnutí nic nenačítá.
- **Posuvné okno se na konci otevře.** Se začátkem závěrečného úseku se okno rozšíří zpět až k prvnímu dni rozsahu, takže snímek, na kterém animace skončí, je celý rozsah, nikoli jeho poslední několik desítek dnů.
- **Pás na pravé straně lze uvolnit, chcete-li šířku.** Ve výchozím nastavení je vypnutý: platforma kreslí svůj avatar a tlačítka „to se mi líbí“ a komentářů na té straně svislého videa a číslo pod nimi je na telefonu skryté, přestože je tu zcela čitelné. Zapnutý: záběr, který vyplňuje celý rozsah, kreslí od první snímku až k vlastnímu okraji záběru; posuvné okno drží odstup, dokud je oknem, a spolu s oknem se rozevře na plnou šířku — snímek, na kterém video skončí, je tedy celý rozsah od okraje k okraji.

## Video

Záběr je vždy 9:16. Všechno ostatní určujete vy.

- Délka mění tempo, nezkracuje animaci: úvod, rostoucí sloupce a závěrečné statistiky se rozloží na zvolenou délku.
- Okraje se zapisují proti záběru 1080×1920 a přepočítávají se na rozlišení exportu, takže jednou vyladěné rozvržení platí v každé velikosti. Levý okraj také rozhoduje, kam dopadnou popisky osy: příliš malý, a čísla opustí záběr.
- Vodítka bezpečné oblasti vyznačují, co aplikace v telefonu zakryje vlastním rozhraním. Kreslí se v náhledu a nikdy do souboru.
- Titulek může být na více řádcích: v poli titulku stiskněte Enter a zlomte ho tam, kde chcete. Když se nevejde na jeden řádek, zalomí se sám na druhý, nejvýše na dva; teprve když ani dva nestačí, ustoupí velikost písma. Druhý řádek posune vše pod ním o jeden řádek dolů, takže graf je o tolik nižší.
- **Název a číslo na konci křivky se zastaví před rozhraním platformy.** Aplikace v telefonu kreslí svůj avatar a tlačítka „to se mi líbí“ a komentářů po pravé straně svislého videa, takže kreslicí plocha končí před pravým okrajem záběru a aktuální bod křivky — spolu s názvem a číslem — se zastaví vlevo od toho pásu. Graf je užší než záběr, a proto.

- Vše až do posledního kroku je zdarma: načtení dat, přehrání animace, uložení titulního obrázku. **Export** je jediné místo, které žádá měsíční předplatné, a po stisku vysvětlí, co kupuje a kolik stojí. Obnovuje se, dokud ho v Microsoft Storu nezrušíte.

## Kam se videa ukládají

Exporty se zapisují do složky, kterou vyberete dialogem. Dokud žádná není vybrána, první export se zeptá a pak si odpověď zapamatuje; v nastavení ji lze změnit nebo zapomenout.

## Obrázek na pozadí

Na stránce nastavení lze za okno umístit ztmavený obrázek. Karty a panely zůstávají neprůhledné a navigační panel propouští jen málo — obrázek je tak vidět hlavně kolem nich. Náhled videa má vlastní neprůhledné pozadí a nedotkne se ho to.

- Vyberte obrázek z počítače nebo použijte přímo některou z tapet a obrázků uzamčené obrazovky, které Windows nabízí.
- Vybraný obrázek se zkopíruje do složky aplikace — přesunutí nebo smazání originálu pozadí neovlivní.
- Posuvník intenzity masky určuje, jak moc se obrázek ztmaví, v rozsahu 30–95 %.
- Když je zapnutý vysoký kontrast, obrázek na pozadí se nezobrazuje.
## Pozadí animace

Na stránce nastavení můžete změnit, na co se animace kreslí: vestavěný přechod, dvě vlastní barvy nebo obrázek. Platí to pro náhled, exportované video i titulní obrázek – všechny tři kreslí stejný renderer, takže neexistuje „v náhledu hezké, v souboru jinak“.

- U barev zadáte horní a dolní odstín a snímek mezi nimi přechází. Tmavé jsou lepší: každý odstín textu je světlý a na světlém pozadí se čísla špatně čtou.

- Posuvník krytí určuje, kolik z obou barev se použije: při 100 % je snímek vybranou dvojicí a níže zespodu prosvítá vlastní tmavý přechod stránky. Právě to udrží světlou dvojici čitelnou.

- Výběr obrázku funguje stejně jako u pozadí okna: obrázek z počítače nebo tapeta, kterou Windows už mají. Vybraný se zkopíruje do složky aplikace.

- Obrázek vyplní formát a přebytek se ořízne, takže se proporce nikdy neroztáhnou.

- Posuvník ztmavení určuje, jak silně se obrázek vrací k vlastnímu pozadí stránky: 20 % až 95 %.

- **Každý snímek nese také jméno na svém pozadí: vodoznak.** Je ve výchozím stavu zapnutý, říká „周期留白“, dokud ho nezměníte, a znění je vaše. Opakuje se šikmo přes celý obraz, kreslený **pod** daty, takže nic nezakrývá; náhled, exportované video i titulní obrázek ho nesou stejně. Prázdný se vrací k výchozímu jménu — aby se neslo nic, je třeba ho vypnout. Přepínač je zapnutý ve výchozím stavu, protože video končí někde, kde nic neříká, kde vzniklo.

- Odebrání vodoznaku je jedna ze dvou věcí, které předplatné kupuje. Dokud neexistuje, přepínač zůstává zapnutý a nejde s ním pohnout — a přesně to ponese každý snímek, takže se náhled a soubor nikdy nerozejdou.


- **Jak značka vypadá, je také vaše.** Písmo je jakékoli písmo nainstalované v tomto počítači — každá položka seznamu je napsána písmem, které uvádí —, barva je ta, kterou dá výběrník, a síla je, kolik z té barvy se použije: ve výchozím stavu 10%, nejvíce 40%, a i na maximum je značka kreslena pod daty. Všechny tři platí pro náhled, exportované video i titulní obrázek stejně.

- **Dokud neexistuje předplatné, tento posuvník zůstává na 40 %.** Ztlumení značky patří k jejímu odebrání: aplikace bez předplatného kreslí každý snímek plnou silou a z této hodnoty posuvník nejde pohnout. Uvedených 10 % je hodnota, od které začíná, jakmile předplatné existuje.
- Výchozí znění se neřídí jazykem rozhraní: vodoznak je podpis, a podpis, který by se měnil s jazykem, by byl na každém počítači jiný.

## Data a co neřeknou

Kurzy přicházejí z veřejných rozhraní Tencent Finance a záběr zdroj vždy uvádí. Tato videa popisují to, co už bylo zobchodováno. Slouží pouze pro orientaci a nejsou investičním doporučením.

- Obraty se přepočítávají na stovky milionů jüanů a objem přechází na větší jednotku, jakmile si to čísla vyžádají, aby osa zůstala čitelná.
- Obraty se přepočítávají na stovky milionů — jüanů na pevnině a v Hongkongu, dolarů v USA. Každý trh si ponechává svou měnu.
- Rozsah delší, než může jeden požadavek vrátit, je odmítnut místo tichého zkrácení: asi 900 kalendářních dnů u denních dat, asi patnáct let na straně svíček, která listuje zpět po stránkách, a celá historie u měsíčních. Tiché zkrácení je nejhorší výsledek — chybí pak **začátek**, a graf bez prvních let je jen kratší graf, který vypadá naprosto normálně.

## Aktualizace

Když má Microsoft Store novější verzi, objeví se v navigačním panelu vedle Nastavení tlačítko **Aktualizovat**; jedno kliknutí ji nainstaluje.

- Objeví se jen tehdy, když Store skutečně nabízí novější verzi. Vývojové sestavení nebo sestavení nainstalované mimo Store ho nikdy neuvidí a tak to má být.
- Během instalace se aplikace zavře a spustí se v nové verzi, tlačítko zmizí. Pokud právě probíhá export, nejdřív se zeptá.
- Když instalace selže, řekne proč — jen přes Wi-Fi, slabá baterie — a aktualizaci lze nainstalovat i z Microsoft Storu.

## Něco není v pořádku?

Napište na gaqo@outlook.com, co jste dělali a co jste místo toho očekávali. Číslo verze je na stránce nastavení.
