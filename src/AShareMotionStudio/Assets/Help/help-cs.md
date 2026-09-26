# AShare Motion Studio

Tato aplikace mění ukazatele trhu akcií A na svislá videa pro telefon. Vyberete období, prohlédnete si náhled, dokud se dobře nečte, a exportujete MP4. Nic dalšího instalovat netřeba.

## Obrat celého trhu

Denní obrat celého trhu: částky souhrnných indexů Šanghaje a Šen-čenu sečtené, jeden sloupec na obchodní den.

- Zůstávají jen dny, kdy obchodovaly všechny zahrnuté trhy, aby svátek na jednom z nich nevypadal jako zhroucení součtu.
- Den, který se ještě obchoduje, se vynechává. Nedokončený den obsahuje jen svou otevírací aukci a nakreslil by se jako sloupec přilepený k ose.
- Pekingská volba přidává index BSE 50, který pokrývá jen své složky, ne celou burzu. Je to jiná míra, a menší.

## Objem jedné akcie

Objem jedné akcie proti její míře obratu, ve dvou panelech nad sebou.

- Mezi obchodními dny jsou objem a míra obratu proporcionální, takže oba panely mají téměř stejný tvar. V průběhu jednoho dne vypadají minutový objem a kumulovaný obrat skutečně jinak, a to je zajímavější obrázek.
- Zdroj vnitrodenních dat drží jen posledních několik obchodních dní, takže tento režim nabízí právě je, a ne libovolné datum.

## Závod sektorů

Sada sektorů nebo akcií nakreslená jako vodorovné pruhy, které se předhánějí, a pořadí se mění až do posledního snímku.

- Dvě míry: procentní změna období a jeho objem v stovkách milionů juanů. Přepnutí míry jen přebarví stejná data; znovu se nenačítají.
- Čtyři seznamy: odvětví Shenwan úrovně 1, populární témata, vlastní (zaškrtnout) a jednotlivé akcie (přidat hledáním). Vlastní seznam začíná naplněný odvětvími Shenwan úrovně 1.
- Období může být 1, 3, 6 nebo 12 měsíců, nebo vlastní počáteční a koncové datum.
- Seznam má minimální a maximální počet položek — málo pruhů není závod, příliš mnoho se slije.

## Měsíční matice

Měsíční pruhy rozložené do mřížky: režim roku ukazuje sezónnost nástroje za desetiletí, režim porovnání staví několik nástrojů vedle sebe, aby ukázal rotaci.

- Režim roku: vyberte nástroj (hledání nebo předvolený široký index); rozsah je 1–10 let nebo vše. Jeden požadavek vrátí desetiletí měsíčních pruhů.
- Režim porovnání: 2–14 nástrojů ze seznamu (odvětví úrovně 1 / témata / široké indexy / vlastní / akcie) vedle sebe, na 6–48 měsíců.
- Mřížka se rozsvěcuje buňku po buňce v časovém pořadí; na konci ukáže nejsilnější a nejslabší měsíc rozsahu a další statistiky.
- Měsíční data pokrývají desetiletí najednou, takže zde není denní limit dní — ale příliš mnoho nástrojů vyjde z rámečku.

## Kalendář zisků a ztrát

Libovolná čínská akce nebo index, jeho denní růst nebo pokles rozložený do kalendářních buněk podle měsíců: červená při růstu, zelená při poklesu.

- Hledejte podle kódu, názvu nebo pinyinu; předvolby jsou široké indexy. Podporovány jsou pouze čínské akce a indexy.
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
- Období delší než přibližně 640 kalendářních dní se odmítne, místo aby se tiše zkrátilo, protože víc jeden dotaz na zdroj nevrátí.

## Něco není v pořádku?

Napište na gaqo@outlook.com, co jste dělali a co jste místo toho očekávali. Číslo verze je na stránce nastavení.
