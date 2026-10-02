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

## Svíčkový graf

Svíčky jednoho nástroje: denní, týdenní nebo měsíční, kreslené čtyřmi způsoby, s průměry a objemem pod nimi.

- **Interval** určuje, jaké tržní období jedna svíčka pokrývá: den, týden nebo měsíc. Jeho změna načte data znovu, protože na zdroji jde o tři samostatné řady.
- **Způsob zobrazení** určuje, jak jsou tytéž čtyři ceny nakresleny: svíčky, OHLC sloupce, čára závěru nebo plocha závěru. Přepínání nic nenačítá.
- **Animace** je buď přicházení svíček jedna po druhé, dokud není celé období rozkreslené, nebo pevné okno, které se posouvá vpřed. Druhá z nich udrží svíčku na dlouhém období dostatečně širokou ke čtení a její šířka je nastavení **Okno**.
- Klouzavé průměry MA5, MA10 a MA20 lze položit přes svíčky; panel objemu dole lze vypnout a panel ceny místo získá zpět.
- Probíhající týden nebo měsíc je vynechán. Svíčka ze tří dnů není týden.
- Každý trh se čte na své upravené řadě, takže den štěpení akcií není nakreslen jako pokles, a dividenda také ne.
- **Rozsah** se řídí periodou: denní nabízí 3, 6 nebo 12 měsíců a 3, 5 nebo 10 let; týdenní 1, 3, 5 nebo 10 let; měsíční 3, 5 nebo 10 let nebo maximum, které zdroj má (asi 13). Jeden požadavek přinese asi 640 denních svíček a strana se vrací po stránkách, takže deset let — asi 2 500 svíček — se do toho vejde.

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

Nákup jednoho nástroje za pevnou částku v pevných intervalech — každý obchodní den, každý týden nebo každý měsíc — a animace toho, čeho disciplína dosáhla.

- Nástroje na jedno klepnutí sledují trh: široké a zlaté ETF u A-akcí, hongkongské trackerové fondy, ve USA SPY, QQQ a GLD.
- Částku a frekvenci si nastavíte sami; období je tři, pět nebo deset let, nebo tak daleko zpět, jak jsou data k dispozici (zhruba třináct let).
- Výnos se počítá na zpětně upravených cenách, bez poplatků. Výsledek popisuje řadu cen, nikoli účtenku, kterou by někdo mohl realizovat.
- Kromě 3, 5 a 10 let a nejdelšího období lze zvolit i **Vlastní**: zadejte počáteční a koncové datum a stiskněte načtení dat. Dostupných je asi 35 let zpět — zdroj vrací zhruba 640 kalendářních dnů na jeden požadavek a průchod jich provede nejvýše dvacet.

## Výnos pozice

![Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.](media/position.png)

Jediný nákup, držený roky — třeba milion do 中国平安 v roce 2015 — animovaný jako to, co udělaly hodnota a výnos.

- Nabízená jména odpovídají trhu: v Číně akcie, které lidé skutečně říkají, že drželi (Ping An, Moutai, CMB…), v Hongkongu Tencent, HSBC a Tracker Fund, v USA Apple, Berkshire a SPY.
- Počáteční kapitál a doba držení jsou na vás; doba může být tři, pět nebo deset let, nebo až tam, kam data sahají (zhruba třináct let).
- Výnos se počítá ze zpětně upravených cen — dividendy reinvestovány, bez poplatků. Zpětná úprava kotví u prvního dne emise a hromadí dividendy dopředu, takže rané roky štědrého plátce nikdy nejsou nekladné, jak se může stát u dopředné úpravy.
- Stejné **Vlastní** období platí i pro držbu: zadejte dvě data a stiskněte načtení dat. Pokud byl nástroj uveden na trh později, než je zadané datum, držba začíná jeho prvním obchodním dnem.

## Video

Záběr je vždy 9:16. Všechno ostatní určujete vy.

- Délka mění tempo, nezkracuje animaci: úvod, rostoucí sloupce a závěrečné statistiky se rozloží na zvolenou délku.
- Okraje se zapisují proti záběru 1080×1920 a přepočítávají se na rozlišení exportu, takže jednou vyladěné rozvržení platí v každé velikosti. Levý okraj také rozhoduje, kam dopadnou popisky osy: příliš malý, a čísla opustí záběr.
- Vodítka bezpečné oblasti vyznačují, co aplikace v telefonu zakryje vlastním rozhraním. Kreslí se v náhledu a nikdy do souboru.

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
