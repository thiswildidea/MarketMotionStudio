# AShare Motion Studio

Ta aplikacja zamienia wskaźniki rynku akcji A w pionowe filmy na telefon. Wybierasz okres, patrzysz na podgląd, aż da się go dobrze odczytać, i eksportujesz plik MP4. Nic więcej nie trzeba instalować.

## Wybór rynku

W ustawieniach wybiera się, z którego rynku aplikacja pobiera notowania; domyślnie akcje A. Zmiana działa po ponownym uruchomieniu aplikacji.

- **Akcje A**: dostępne są wszystkie strony.
- **Hongkong**: macierz stóp zwrotu i kalendarz działają; wyścig sektorów korzysta z czterech subindeksów Hang Seng; **nie ma danych dla całego rynku, więc ta strona jest ukryta**.
- **USA**: macierz stóp zwrotu i kalendarz działają; wyścig sektorów korzysta z dziesięciu sektorowych ETF-ów SPDR; strona wolumenu ma tylko tryb dzienny, bo minutowy endpoint nie obsługuje danych z USA; **kwoty są w dolarach, a strona obrotu całego rynku jest ukryta**.

## Obroty rynku

Dzienne obroty całego rynku: kwoty indeksów zbiorczych z Szanghaju i Shenzhen zsumowane, jeden słupek na sesję.

- Zostają tylko dni, w których handlowały wszystkie uwzględnione rynki, żeby święto na jednym z nich nie sprawiało wrażenia, że suma się załamała.
- Sesja wciąż trwająca jest pomijana. Niedokończony dzień zawiera tylko swój fixing otwarcia i narysowałby się jako słupek przyklejony do osi.
- Albo patrzeć na jeden segment: każdą giełdę, każdy rynek główny, STAR, ChiNext. Rynki główne wyliczono jako sumę giełdową minus rynek wzrostu; BSE 50 pozostaje miarą składników.
- Sumę dla całego rynku daje tylko rynek akcji A. Po wyborze Hongkongu lub USA strona znika z nawigacji.

## Wolumen i obrót

Wolumen jednej spółki na tle jej wskaźnika obrotu, w dwóch panelach jeden nad drugim.

- Z sesji na sesję wolumen i wskaźnik obrotu są proporcjonalne, więc oba panele mają niemal ten sam kształt. W ciągu jednego dnia wolumen minutowy i narastający obrót wyglądają naprawdę inaczej, i to jest ciekawszy obraz.
- Źródło danych śróddziennych trzyma tylko ostatnie sesje, więc ten tryb proponuje właśnie je, a nie dowolną datę.
- Dane minutowe są dostępne tylko dla akcji A i Hongkongu; w USA ten tryb nie jest oferowany.

## Wyścig sektorów

Zbiór sektorów lub akcji jako poziome paski, które wyprzedzają się nawzajem, a kolejność zmienia się aż do ostatniej klatki.

- Dwa wskaźniki: zmiana z okresu w % oraz obrót w setkach milionów juanów. Przełączenie wskaźnika tylko przekolorowuje te same dane; nie pobiera ich ponownie.
- Cztery listy: branże Shenwan poziomu 1, popularne tematy, własna (zaznacz), pojedyncze akcje (dodaj przez wyszukiwanie). Własna lista startuje wypełniona branżami Shenwan poziomu 1.
- Wbudowane listy zmieniają się wraz z rynkiem: branże Shenwan poziomu 1 i popularne tematy dla akcji A, cztery subindeksy Hang Seng dla Hongkongu, dziesięć sektorowych ETF-ów SPDR dla USA. Lista własna i lista akcji są na każdym rynku.
- Zakres to 1, 3, 6 lub 12 miesięcy albo dowolna data początkowa i końcowa.
- Lista ma minimalną i maksymalną liczbę pozycji — za mało pasków to nie wyścig, za dużo się zleje.

## Macierz stóp zwrotu

Miesięczne słupki ułożone w siatkę: tryb roku pokazuje sezonowość instrumentu przez dekadę, tryb porównania stawia kilka instrumentów obok siebie, by pokazać rotację.

- Tryb roku: wybierz instrument (wyszukiwanie lub predefiniowany szeroki indeks); zakres to 1–10 lat lub wszystkie. Jedno zapytanie zwraca dekadę miesięcznych słupków.
- Tryb porównania: 2–14 instrumentów z listy (branże poziomu 1 / tematy / szerokie indeksy / własna / akcje) obok siebie, na 6–48 miesięcy.
- Siatka zapala się komórka po komórce w kolejności czasu; na koniec podaje najsilniejszy i najsłabszy miesiąc zakresu oraz inne statystyki.
- Dane miesięczne obejmują dekadę za jednym razem, więc nie ma tu dziennego limitu dni — ale zbyt wiele instrumentów wykracza poza kadr.

## Kalendarz zysków i strat

Dowolna chińska akcja lub indeks, jego dzienny wzrost lub spadek ułożony w komórki kalendarza według miesięcy: czerwony przy wzroście, zielony przy spadku.

- Szukaj po kodzie, nazwie lub pinyinie; predefiniowane to szerokie indeksy. Obsługiwane są tylko instrumenty wybranego rynku.
- Lista ulubionych jest współdzielona z stroną akcji aplikacji — ulubiony dodany w jednym miejscu widać w obu.
- Zakres to 1, 3, 6 lub 12 miesięcy albo dowolny; pojedynczy instrument nadal podlega limitowi około 640 dni kalendarzowych.
- Końcowa statystyka podaje liczbę sesji wzrostowych i spadkowych.

## Film

Kadr jest zawsze 9:16. Wszystko inne ustalasz sam.

- Czas trwania zmienia tempo, a nie skraca animacji: wstęp, wzrost słupków i końcowe statystyki są rozłożone na wybraną długość.
- Marginesy są zapisane względem kadru 1080×1920 i skalowane do rozdzielczości eksportu, więc raz dobrany układ obowiązuje w każdym rozmiarze. Lewy margines decyduje też, gdzie trafiają opisy osi: za mały, i liczby wyjdą poza kadr.
- Linie bezpiecznego obszaru obrysowują to, co aplikacja na telefonie zakrywa własnym interfejsem. Rysują się w podglądzie i nigdy w pliku.

## Gdzie trafiają filmy

Eksporty zapisują się do folderu, który wybierasz w okienku. Dopóki żaden nie został wybrany, pierwszy eksport zapyta i potem zapamięta; ustawienia pozwalają to zmienić albo zapomnieć.

## Dane i to, czego nie powiedzą

Notowania pochodzą z publicznych punktów końcowych Tencent Finance, a kadr zawsze podaje źródło. Te filmy opisują to, co już zostało zawarte. Są wyłącznie informacyjne i nie stanowią porady inwestycyjnej.

- Obroty są przeliczane na setki milionów juanów, a wolumen przechodzi na większą jednostkę, gdy liczby tego wymagają, żeby oś dała się czytać.
- Obroty przelicza się na setki milionów — juanów na kontynencie i w Hongkongu, dolarów w USA. Każdy rynek zachowuje swoją walutę.
- Okres dłuższy niż około 640 dni kalendarzowych jest odrzucany, a nie po cichu skracany, bo tyle zwraca jedno zapytanie do źródła.

## Coś nie działa?

Napisz na gaqo@outlook.com, co robiłeś i czego się zamiast tego spodziewałeś. Numer wersji jest na stronie ustawień.
