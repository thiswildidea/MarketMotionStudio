# AShare Motion Studio

Tato aplikace mění ukazatele trhu akcií A na svislá videa pro telefon. Vyberete období, prohlédnete si náhled, dokud se dobře nečte, a exportujete MP4. Nic dalšího instalovat netřeba.

## Volba trhu

V nastavení se volí, z kterého trhu aplikace bere kurzy; výchozí jsou A-akcie. Změna se projeví po restartu aplikace.

- **A-akcie**: všechny stránky jsou k dispozici.
- **Hongkong**: matice výnosů a kalendář fungují; závod sektorů běží na čtyřech subindexech Hang Seng; **údaj za celý trh neexistuje, proto je tato stránka skrytá**.
- **USA**: matice výnosů a kalendář fungují; závod sektorů běží na deseti sektorových ETF SPDR; stránka objemu má jen denní režim, protože minutový endpoint data pro USA nevrací; **částky jsou v dolarech a stránka obratu celého trhu je skrytá**.

## Obrat trhu

Denní obrat celého trhu: částky souhrnných indexů Šanghaje a Šen-čenu sečtené, jeden sloupec na obchodní den.

- Zůstávají jen dny, kdy obchodovaly všechny zahrnuté trhy, aby svátek na jednom z nich nevypadal jako zhroucení součtu.
- Den, který se ještě obchoduje, se vynechává. Nedokončený den obsahuje jen svou otevírací aukci a nakreslil by se jako sloupec přilepený k ose.
- Nebo se dívat jen na jeden segment: každou burzu, každý hlavní trh, STAR, ChiNext. Hlavní trhy se počítají jako součet burzy minus růstový trh; BSE 50 zůstává měrou podle složek.
- Součet za celý trh dává jen trh A-akcií. Při volbě Hongkongu nebo USA se stránka z navigace odstraní.

## Objem a obrat

Objem jedné akcie proti její míře obratu, ve dvou panelech nad sebou.

- Mezi obchodními dny jsou objem a míra obratu proporcionální, takže oba panely mají téměř stejný tvar. V průběhu jednoho dne vypadají minutový objem a kumulovaný obrat skutečně jinak, a to je zajímavější obrázek.
- Zdroj vnitrodenních dat drží jen posledních několik obchodních dní, takže tento režim nabízí právě je, a ne libovolné datum.
- Minutová data jsou k dispozici jen pro A-akcie a Hongkong; v USA se tento režim nenabízí.

## Závod sektorů

Sada sektorů nebo akcií nakreslená jako vodorovné pruhy, které se předhánějí, a pořadí se mění až do posledního snímku.

- Dvě míry: procentní změna období a jeho objem v stovkách milionů juanů. Přepnutí míry jen přebarví stejná data; znovu se nenačítají.
- Čtyři seznamy: odvětví Shenwan úrovně 1, populární témata, vlastní (zaškrtnout) a jednotlivé akcie (přidat hledáním). Vlastní seznam začíná naplněný odvětvími Shenwan úrovně 1.
- Vestavěné seznamy se řídí trhem: obory Shenwan úrovně 1 a populární témata u A-akcií, čtyři subindexy Hang Seng u Hongkongu, deset sektorových ETF SPDR u USA. Vlastní seznam a seznam akcií jsou na každém trhu.
- Období může být 1, 3, 6 nebo 12 měsíců, nebo vlastní počáteční a koncové datum.
- Seznam má minimální a maximální počet položek — málo pruhů není závod, příliš mnoho se slije.

## Matice výnosů

Měsíční pruhy rozložené do mřížky: režim roku ukazuje sezónnost nástroje za desetiletí, režim porovnání staví několik nástrojů vedle sebe, aby ukázal rotaci.

- Režim roku: vyberte nástroj (hledání nebo předvolený široký index); rozsah je 1–10 let nebo vše. Jeden požadavek vrátí desetiletí měsíčních pruhů.
- Režim porovnání: 2–14 nástrojů ze seznamu (odvětví úrovně 1 / témata / široké indexy / vlastní / akcie) vedle sebe, na 6–48 měsíců.
- Mřížka se rozsvěcuje buňku po buňce v časovém pořadí; na konci ukáže nejsilnější a nejslabší měsíc rozsahu a další statistiky.
- Měsíční data pokrývají desetiletí najednou, takže zde není denní limit dní — ale příliš mnoho nástrojů vyjde z rámečku.

## Kalendář zisků a ztrát

Libovolná čínská akce nebo index, jeho denní růst nebo pokles rozložený do kalendářních buněk podle měsíců: červená při růstu, zelená při poklesu.

- Hledejte podle kódu, názvu nebo pinyinu; předvolby jsou široké indexy. Podporovány jsou jen nástroje zvoleného trhu.
- Seznam oblíbených se sdílí se stránkou akcií aplikace — oblíbený přidaný na kterékoli straně se zobrazí v obou.
- Období je 1, 3, 6 nebo 12 měsíců, nebo vlastní; jeden nástroj je stále vázán limitem asi 640 kalendářních dní.
- Závěrečné statistiky uvádějí počet růstových a poklesových obchodních dní.

## Video

Záběr je vždy 9:16. Všechno ostatní určujete vy.

- Délka mění tempo, nezkracuje animaci: úvod, rostoucí sloupce a závěrečné statistiky se rozloží na zvolenou délku.
- Okraje se zapisují proti záběru 1080×1920 a přepočítávají se na rozlišení exportu, takže jednou vyladěné rozvržení platí v každé velikosti. Levý okraj také rozhoduje, kam dopadnou popisky osy: příliš malý, a čísla opustí záběr.
- Vodítka bezpečné oblasti vyznačují, co aplikace v telefonu zakryje vlastním rozhraním. Kreslí se v náhledu a nikdy do souboru.

## Kam se videa ukládají

Exporty se zapisují do složky, kterou vyberete dialogem. Dokud žádná není vybrána, první export se zeptá a pak si odpověď zapamatuje; v nastavení ji lze změnit nebo zapomenout.

## Data a co neřeknou

Kurzy přicházejí z veřejných rozhraní Tencent Finance a záběr zdroj vždy uvádí. Tato videa popisují to, co už bylo zobchodováno. Slouží pouze pro orientaci a nejsou investičním doporučením.

- Obraty se přepočítávají na stovky milionů jüanů a objem přechází na větší jednotku, jakmile si to čísla vyžádají, aby osa zůstala čitelná.
- Obraty se přepočítávají na stovky milionů — jüanů na pevnině a v Hongkongu, dolarů v USA. Každý trh si ponechává svou měnu.
- Období delší než přibližně 640 kalendářních dní se odmítne, místo aby se tiše zkrátilo, protože víc jeden dotaz na zdroj nevrátí.

## Něco není v pořádku?

Napište na gaqo@outlook.com, co jste dělali a co jste místo toho očekávali. Číslo verze je na stránce nastavení.
