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

## Objem a obrat

Objem jedné akcie proti její míře obratu, ve dvou panelech nad sebou.

- Mezi obchodními dny jsou objem a míra obratu proporcionální, takže oba panely mají téměř stejný tvar. V průběhu jednoho dne vypadají minutový objem a kumulovaný obrat skutečně jinak, a to je zajímavější obrázek.
- Zdroj vnitrodenních dat drží jen posledních několik obchodních dní, takže tento režim nabízí právě je, a ne libovolné datum.
- Minutová data jsou k dispozici jen pro A-akcie a Hongkong; v USA se tento režim nenabízí.

## Závod sektorů

![Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.](media/sector-race.png)

Sada sektorů nebo akcií nakreslená jako vodorovné pruhy, které se předhánějí, a pořadí se mění až do posledního snímku.

- Dvě míry: procentní změna období a jeho objem v stovkách milionů juanů. Přepnutí míry jen přebarví stejná data; znovu se nenačítají.
- Čtyři seznamy: odvětví Shenwan úrovně 1, populární témata, vlastní (zaškrtnout) a jednotlivé akcie (přidat hledáním). Vlastní seznam začíná naplněný odvětvími Shenwan úrovně 1.
- Vestavěné seznamy se řídí trhem: obory Shenwan úrovně 1 a populární témata u A-akcií, čtyři subindexy Hang Seng u Hongkongu, deset sektorových ETF SPDR u USA. Vlastní seznam a seznam akcií jsou na každém trhu.
- Období může být 1, 3, 6 nebo 12 měsíců, nebo vlastní počáteční a koncové datum.
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
  Hongkong a New York mají pevnou sestavu, protože jim žádný žebříček dostupný této aplikaci
  neposlouží.

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
- Období delší než přibližně 640 kalendářních dní se odmítne, místo aby se tiše zkrátilo, protože víc jeden dotaz na zdroj nevrátí.

## Aktualizace

Když má Microsoft Store novější verzi, objeví se v navigačním panelu vedle Nastavení tlačítko **Aktualizovat**; jedno kliknutí ji nainstaluje.

- Objeví se jen tehdy, když Store skutečně nabízí novější verzi. Vývojové sestavení nebo sestavení nainstalované mimo Store ho nikdy neuvidí a tak to má být.
- Během instalace se aplikace zavře a spustí se v nové verzi, tlačítko zmizí. Pokud právě probíhá export, nejdřív se zeptá.
- Když instalace selže, řekne proč — jen přes Wi-Fi, slabá baterie — a aktualizaci lze nainstalovat i z Microsoft Storu.

## Něco není v pořádku?

Napište na gaqo@outlook.com, co jste dělali a co jste místo toho očekávali. Číslo verze je na stránce nastavení.
