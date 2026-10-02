# Market Motion Studio

Ta aplikacja zamienia wskaźniki rynku akcji A w pionowe filmy na telefon. Wybierasz okres, patrzysz na podgląd, aż da się go dobrze odczytać, i eksportujesz plik MP4. Nic więcej nie trzeba instalować.

## Wybór rynku

W ustawieniach wybiera się, z którego rynku aplikacja pobiera notowania; domyślnie akcje A. Zmiana działa po ponownym uruchomieniu aplikacji.

- **Akcje A**: dostępnych jest wszystkich osiem stron.
- **Hongkong**: macierz stóp zwrotu i kalendarz działają; wyścig sektorów korzysta z czterech subindeksów Hang Seng; **nie ma danych dla całego rynku, więc ta strona jest ukryta**.
- **USA**: macierz stóp zwrotu i kalendarz działają; wyścig sektorów korzysta z dziesięciu sektorowych ETF-ów SPDR; strona wolumenu ma tylko tryb dzienny, bo minutowy endpoint nie obsługuje danych z USA; **kwoty są w dolarach, a strona obrotu całego rynku jest ukryta**.



## Przechodzenie między stronami

Dwa przyciski po lewej stronie paska tytułu cofają się i przesuwają do przodu po odwiedzonych stronach, tak jak robi to przeglądarka — **Alt+Strzałka w lewo** i **Alt+Strzałka w prawo** albo boczne przyciski myszy.

- Strona pozostaje taka, jak ją zostawiono, więc powrót do niej przywraca wybrany okres i podgląd w takim stanie, w jakim były, a nie świeżo otwartą stronę.
- Jak w przeglądarce: wybranie nowej strony czyści to, co było przed Tobą.
- Działają także przy zwiniętym panelu nawigacji, czyli wtedy, gdy podgląd najbardziej potrzebuje szerokości.

## Obroty rynku

Dzienne obroty całego rynku: kwoty indeksów zbiorczych z Szanghaju i Shenzhen zsumowane, jeden słupek na sesję.

- Zostają tylko dni, w których handlowały wszystkie uwzględnione rynki, żeby święto na jednym z nich nie sprawiało wrażenia, że suma się załamała.
- Sesja wciąż trwająca jest pomijana. Niedokończony dzień zawiera tylko swój fixing otwarcia i narysowałby się jako słupek przyklejony do osi.
- Albo patrzeć na jeden segment: każdą giełdę, każdy rynek główny, STAR, ChiNext. Rynki główne wyliczono jako sumę giełdową minus rynek wzrostu; BSE 50 pozostaje miarą składników.
- Sumę dla całego rynku daje tylko rynek akcji A. Po wyborze Hongkongu lub USA strona znika z nawigacji.

## Wykres świecowy

Świece jednego instrumentu: dzienne, tygodniowe lub miesięczne, rysowane na cztery sposoby, ze średnimi i wolumenem poniżej.

- **Interwał** decyduje, jaki czas rynkowy obejmuje jedna świeca: dzień, tydzień lub miesiąc. Zmiana go pobiera dane ponownie, bo na źródle to trzy osobne serie.
- **Rodzaj wykresu** decyduje, jak te same cztery ceny są rysowane: świece, słupki OHLC, linia zamknięcia lub obszar zamknięcia. Przełączanie niczego nie pobiera.
- **Animacja** to pojawianie się świec jedna po drugiej, aż cały zakres zostanie narysowany, albo stałe okno, które przesuwa się w przód. To drugie sprawia, że świeca na długim zakresie zostaje dość szeroka do odczytania, a jej szerokość to ustawienie **Okno**.
- Średnie kroczące MA5, MA10 i MA20 można nałożyć na świece; panel wolumenu poniżej można wyłączyć, a panel ceny odzyskuje to miejsce.
- Tydzień lub miesiąc wciąż trwający zostaje pominięty. Świeca złożona z trzech dni nie jest tygodniem.
- Każdy rynek jest czytany na swojej serii skorygowanej, więc dzień splitu nie jest rysowany jako spadek, tak samo jak dywidenda.
- **Zakres** zależy od interwału: dzienny daje 3, 6 lub 12 miesięcy albo 3, 5 lub 10 lat; tygodniowy 1, 3, 5 lub 10 lat; miesięczny 3, 5 lub 10 lat lub maksimum, jakie ma źródło (około 13). Jedno żądanie przynosi około 640 świec dziennych, a strona cofa się strona po stronie, więc dziesięć lat — około 2.500 świec — mieści się w tym.

## Wolumen i obrót

Wolumen jednej spółki na tle jej wskaźnika obrotu, w dwóch panelach jeden nad drugim.

- Z sesji na sesję wolumen i wskaźnik obrotu są proporcjonalne, więc oba panele mają niemal ten sam kształt. W ciągu jednego dnia wolumen minutowy i narastający obrót wyglądają naprawdę inaczej, i to jest ciekawszy obraz.
- Źródło danych śróddziennych trzyma tylko ostatnie sesje, więc ten tryb proponuje właśnie je, a nie dowolną datę.
- Dane minutowe są dostępne tylko dla akcji A i Hongkongu; w USA ten tryb nie jest oferowany.
- W interwale dziennym zakres to 1, 3, 6, 12 lub 24 miesiące albo własne daty początku i końca; zakres niestandardowy kończy się na około 900 dniach kalendarzowych — tyle zwraca jedno żądanie — i wybór dat kończy się w tym samym miejscu. Tryb intraday pozwala wybrać jeden z kilku dostępnych dni.

## Wyścig sektorów

![Strona w całości: podgląd po lewej, pasek odtwarzania poniżej, ustawienia po prawej.](media/sector-race.png)

Zbiór sektorów lub akcji jako poziome paski, które wyprzedzają się nawzajem, a kolejność zmienia się aż do ostatniej klatki.

- Dwa wskaźniki: zmiana z okresu w % oraz obrót w setkach milionów juanów. Przełączenie wskaźnika tylko przekolorowuje te same dane; nie pobiera ich ponownie.
- Cztery listy: branże Shenwan poziomu 1, popularne tematy, własna (zaznacz), pojedyncze akcje (dodaj przez wyszukiwanie). Własna lista startuje wypełniona branżami Shenwan poziomu 1.
- Wbudowane listy zmieniają się wraz z rynkiem: branże Shenwan poziomu 1 i popularne tematy dla akcji A, cztery subindeksy Hang Seng dla Hongkongu, dziesięć sektorowych ETF-ów SPDR dla USA. Lista własna i lista akcji są na każdym rynku.
- Zakres to 1, 3, 6, 12 lub 24 miesiące albo dowolna data początkowa i końcowa. Własny zakres sięga około 900 dni — tyle, ile obejmuje jedno żądanie — i tam kończą się selektory dat.
- Lista ma minimalną i maksymalną liczbę pozycji — za mało pasków to nie wyścig, za dużo się zleje.




## Wyścig kapitalizacji

Piętnaście największych spółek danego rynku jako poziome słupki uszeregowane według
kapitalizacji; kolejność zmienia się do ostatniej klatki. Próbkowanie miesięczne.

- **Ranking jest liczony od nowa w każdym okresie.** Pobranie najpierw pyta źródło o bieżący
  ranking według kapitalizacji, bierze pierwsze dwieście jako grono i dodaje duże spółki, które
  kiedyś były w rankingu, a z niego wypadły; każdy okres pokazuje potem piętnaście największych z
  tego grona. Skład naprawdę się zmienia — w 2016 roku to była ropa i banki, w 2026 doszły 茅台,
  宁德时代 i 工业富联. Grono zapisane w programie pominęło spółkę, która zadebiutowała i od razu
  wskoczyła na szczyt; teraz grono jest pytane, a nie pamiętane.
- **Dawna kapitalizacja jest wyliczana**: dzisiejsza kapitalizacja razy skorygowany stosunek cen
  z okresu. Emisje i splity znoszą się w skorygowanej serii; dywidendy nie — są reinwestowane,
  więc dawna wartość hojnego płatnika wypada nisko. Tylko liczba z ostatniej klatki pochodzi
  wprost ze źródła.
- **Spółka jeszcze nienotowana rośnie od zera**: debiuty z 2018 roku wyrastają z linii bazowej
  w dniu wejścia, zamiast zajmować miejsce zawczasu.
- **Odstęp to miesiąc, nie dzień** — sto dwadzieścia okresów na dziesięć lat, dwanaście na rok,
  a nagłówek klatki liczy miesiące. Ranking kapitalizacji zmienia się powoli, a próbka miesięczna
  dostaje całą historię w jednym zapytaniu.
- **Każdy rynek ma swoje piętnaście.** Trzech nigdy się nie miesza: ich pieniądz to nie ten sam
- Zakres to ostatnie 12 miesięcy, 3, 5 lub 10 lat albo **Najdłuższy** — jedno żądanie zwraca wszystkie 180 okresów miesięcznych, około piętnastu lat, i tam kończy się ta pozycja. Możesz też podać własne daty początku i końca.
  pieniądz. Hongkong i Nowy Jork mają stałe grono, bo żaden dostępny tej aplikacji ranking ich nie
  obsługuje.





## Premia A/H

O ile droższe jest notowanie kontynentalne spółki od jej notowania w Hongkongu — dla spółek
notowanych po obu stronach, miesiąc po miesiącu, jako słupki, które się wyprzedzają.

- **Premia = kurs A ÷ (kurs H × HKD/CNY) − 1.** Nic tu nie jest wyliczane: obie nogi to kursy
  faktycznie płacone w tym samym momencie, dlatego ta strona jako jedyna pobiera kursy
  **nieskorygowane**. Seria korygowana wstecz zawyża ostatnie kursy, a dwóch rynków korygowanych
  osobno nie da się porównać — akcja A ICBC kosztuje 8,28 na ekranie, a skorygowana seria podaje
  13,34, zamieniając premię +26% w +245%.
- **Tę samą różnicę zapisuje się w obie strony.** Ta strona podaje A do H, czyli formę przyjętą w
  branży: +194% znaczy, że akcja kontynentalna kosztuje prawie trzy razy tyle co hongkońska.
  Niektóre serwisy pokazują tę samą liczbę odwrotnie (溢价(H/A)) i dla 新华制药 dają −66% tego
  samego dnia. To ten sam fakt (1 ÷ (1 − 0,66) − 1 = 1,94), a nie inny kurs ani błąd.
- **Rysowane jest piętnaście najdroższych**, więc słupki rosną w prawo — nawet piętnasta miała
  ponad dwadzieścia procent. Tylko dwie z sześćdziesięciu dziewięciu idą w drugą stronę, ich akcje
  H ponad akcjami A, i obie stoją na końcu listy, poza kadrem.
- **Im dłuższy okres, tym mniej spółek się kwalifikuje.** Kandydatów jest sześćdziesiąt dziewięć
  znanych podwójnych notowań, ale rysowana jest tylko para, której obie nogi pokrywają cały okres:
  notowanie w Hongkongu młodsze niż dwa lata wypada.
- **Próbkowanie miesięczne.** „Najdłuższy" to około dziewięciu lat, a granicą jest seria kursu
  walutowego sięgająca tylko 2016 roku. Trzy nogi kończą miesiąc w różnych dniach, więc grupujemy po
  miesiącu kalendarzowym i bierzemy ostatni kurs miesiąca, zamiast przecinać po dacie.
- **Lista jest wbudowana.** Żadne z dwóch źródeł nie odpowiada na pytanie „które notowania
  kontynentalne mają też notowanie w Hongkongu". Jest za to sprawdzalna: każdą parę odczytano
  ponownie ze źródła 2026-10-02, a 海通证券 wypadło właśnie wtedy (akcje H wycofane po fuzji z
  国泰海通).

## Ekstremalne dni

Jeden instrument i dni, w których poruszył się najmocniej — poziome słupki uporządkowane
według wielkości. **Wierszami tej tablicy są dni, nie spółki**, czego nie robi żadna inna strona:
wartością wiersza jest ruch z danego dnia względem zamknięcia poprzedniej sesji i gdy ten dzień
minie, wartość już się nie zmienia.

- **Ruch to zmiana skorygowanej ceny zamknięcia.** Skorygowanej, bo dzień odcięcia dywidendy nie
  jest krachem: tego ranka cena spada o dywidendę, a seria bez korekty umieściłaby ten dzień na
  czele największych spadków w historii, choć nikt nic nie stracił.
- **Uporządkowane według wielkości, nie według znaku.** −7,7 % i +8,1 % to ruchy tej samej
  wielkości, więc stoją obok siebie; sortowanie wartości ze znakiem umieściłoby każdy spadek pod
  każdym wzrostem. Słupki rosną więc w obie strony: **wzrost w prawo, na czerwono; spadek w lewo,
  na zielono**.
- **Dzień liczy się dopiero, gdy nadejdzie.** Dwudziestu czterech kandydatów to największe ruchy
  okresu, a kadr rysuje piętnaście największych z nich. Dzień nie bierze udziału w rankingu, póki
  nie nadejdzie jego data, więc tablica zapełnia się wraz z latami zamiast być pełna od początku.
- **Dowolny instrument notowany na tym rynku, nie tylko szerokie indeksy.** Wpisz kod, nazwę lub
  pinyin w polu wyszukiwania: pojedyncza akcja i fundusz notowany na giełdzie pasują tu tak samo jak
  indeks, a lista poniżej to tylko skrót do najczęstszych. Zmiana rynku podmienia tę listę i porzuca
  instrument z innego rynku; wybór instrumentu lub zakresu zapisuje tylko preferencję — nic nie jest
  pobierane, dopóki nie naciśniesz 取数.
- **Najdłuższy okres to około trzydzieści pięć lat**, co jest ograniczeniem źródła: jedno żądanie
  niesie około 640 świec dziennych, a cofanie wykonuje się najwyżej dwadzieścia razy. Okres
  krótszy niż sześćdziesiąt sesji jest odrzucany — największy dzień spokojnego miesiąca to nie jest
  fakt wart tablicy.
- **Data u góry kadru to oś czasu**, a pasek pod nią to postęp. Wiersz nagłówka niesie okres,
  liczbę sesji i liczbę dni kandydackich.

## Korytarze walutowe

Jeden wiersz na parę, i **ten wiersz jest korytarzem**: jeden koniec to najniższy poziom, na
jakim para była w wybranym okresie, drugi — najwyższy, a znacznik to kurs z dziś. Ta tablica nie jest
więc jak inne — gdzie indziej długość słupka mówi *ile*, tu wiersz w każdej klatce zajmuje całą
szerokość, a porusza się znacznik wraz z korytarzem wokół niego.

- **Korytarz się rozszerza.** Jego ściany to najniższe i najwyższe **dotąd**, nie w całym okresie.
  Miesiąc, który wyjdzie dalej niż wszystkie wcześniejsze, wypycha jedną ze ścian, a para na 100%
  jest najdroższa, jaka kiedykolwiek była — nie przy jakimś limicie.
- **Każda para mierzona jest własnym zakresem.** 157,92 na USD/JPY i 1,1245 na EUR/USD to nie dwa
  punkty na jednej skali; to normalizacja pozwala sześciu parom stanąć na jednym obrazie. Ceną jest
  to, że wąski i szeroki korytarz wyglądają tak samo — dlatego obie wartości są wypisane pod każdym
  wierszem.
- **Świece miesięczne, bez korekty.** Waluta nie ma dywidendy ani podziału do skorygowania, a strona
  idzie tą samą surową ścieżką do źródła co strona A+H.
- **Zasięg danych jest różny, dlatego są dwie listy**: USD/CNY sięga 2005, pozostałe pięć par
  renminbi — 2016; główne crossy zaczynają się wszystkie w 2005-07 i mają po 325 miesięcy. Na jednej
  tablicy czytałoby się, od kiedy źródło zaczęło notować każdą parę.
- **Ustawienie rynku tu nie działa**: para walutowa nie należy do żadnej giełdy, a tablica jest ta
  sama niezależnie od wybranego rynku.
- Najdłuższy okres to około dwudziestu lat — tyle obejmują miesięczne dane źródła. Mniej niż
  dwanaście miesięcy jest odrzucane: to kilka tygodni ruchu, nie korytarz.

## Wyścig indeksów

Jeden wiersz na indeks, a wiersz to **jak daleko ten indeks zaszedł od swojego pierwszego
miesiąca w okresie** — nie jego poziom. 3 800 na Shanghai Composite i 5 700 na S&P 500 to nie dwa
punkty na jednej skali; rysowanie poziomów byłoby tablicą o tym, gdzie który indeks zaczął liczyć.

- **Indeks, który przychodzi później, nie ma go na tablicy, dopóki nie przyjdzie.** S&P sięga 1950,
  Dow tylko 2009, a indeks Hang Seng Tech zaczyna się w 2020. Brakuje go, a nie stoi na 0,00% — tam
  znalazłby się nad każdym indeksem, który kiedykolwiek spadł, i czytałoby się to jako rynek, na
  którym nic się nie wydarzyło.
- **Miesięcznie, i teraz już z korektą.** Indeks nic nie wypłaca, ale akcja płaci dywidendy i
  dzieli swoje udziały: Apple pokazuje +193 % w dziesięć lat bez korekty i +1183 % z korektą, bo
  linia bez korekty niesie urwiska, z których żaden posiadacz nigdy nie spadł. Indeksów to nie
  dotyka — poproszona o korektę, źródło odpowiada indeksowi tymi samymi wierszami co zwykle, i
  wszystkie dwanaście wyszły identycznie obiema drogami. To, co tablica teraz niesie, to różnica
  warta wypowiedzenia: wiersz indeksu to zwrot **cenowy**, bo indeks nie jest pozycją, a wiersz
  akcji to zwrot **całkowity**, z dywidendami i podziałami wliczonymi.
- **Ustawienie rynku tu nie rządzi**: strona czyta trzy rynki naraz, a zmiana rynku jej nie zmienia.
  Można wziąć sześć z kontynentu, trzy z Hongkongu, trzy z Nowego Jorku albo wszystkie dwanaście.
- Najdłuższy okres ogranicza miesięczny sufit źródła — 430 świec, około trzydziestu pięciu lat;
  mniej niż dwanaście miesięcy jest odrzucane: to sprint, nie bieg długi.
- **Albo własna lista.** Ostatnia grupa w menu to lista własna: wpisz kod, nazwę lub pinyin, aby
  dodać jeden walor, i akcja z kontynentu, z Hongkongu oraz z Nowego Jorku mogą być na niej razem
  — ta tablica nigdy nie pyta o ustawienie rynku. Jedna lista dla czterech tablic: akcję dodaną tu
  znajdziesz też w wyścigu aktywów, w obsunięciach i w skuteczności trzymania. Poniżej trzech
  pobieranie jest odrzucane.

## Klasy aktywów

Jeden wiersz na klasę aktywów, a wiersz to **ile zarobiło trzymanie** — nie notowanie. Wszystkie
osiem to fundusze notowane na giełdzie kontynentalnej, kupione za te same pieniądze, więc można je
porównywać wprost.

- **Dywidendy są wliczone, i podziały też.** Obligacja i fundusz rynku pieniężnego płacą prawie
  wyłącznie dochodem: cena funduszu rynku pieniężnego przeszła w trzynaście lat ze 100,161 do
  100,901, co bez korekty jest +0,0% — narysowałoby na dole tablicy jedyny wiersz, który nigdy nie
  spadł. Fundusz po podziale jednostek jest bardziej jaskrawy: ETF Nasdaq ma bez korekty +136%,
  podczas gdy indeks, który naśladuje, w tej samej dekadzie wzrósł sześciokrotnie.
- **Celowo odwrotność wyścigu indeksów.** Indeks nie płaci dywidend, więc tamta strona zostaje
  nietknięta; fundusz płaci, więc tę trzeba korygować. Tych dwóch dróg się nie miesza.
- **Dwa zagraniczne wiersze niosą kurs.** ETF-y Nasdaq i Hang Seng są notowane w juanach, więc
  waluta jest już w środku — to właśnie dostał posiadacz z kontynentu.
- **Początki się różnią.** Najwcześniejszy wiersz zaczyna się w 2012, a fundusz towarowy dopiero w
  2019. Wiersza, który jeszcze nie wszedł, nie ma — nie stoi na 0,00%.
- **Ustawienie rynku tu nie rządzi**: wszystkie osiem jest notowanych na kontynencie. Mniej niż
  dwanaście miesięcy jest odrzucane.
- **Albo własna lista.** Ostatnia grupa w menu to lista własna: wpisz kod, nazwę lub pinyin, aby
  dodać jeden walor, a trzy rynki można na niej mieszać. Jedna lista dla czterech tablic: akcję
  dodaną tu znajdziesz też na trzech pozostałych; pobiera się ją z korektą, dokładnie jak osiem
  funduszy, więc dywidendy i podziały są w liczbie. Poniżej trzech pobieranie jest odrzucane.

## Obsunięcia

Wiersz to **jak daleko poniżej własnego szczytu jest instrument** — nie ile zarobił, lecz ile
kosztowało wytrzymanie tego zarobku. Te same osiem instrumentów co w wyścigu klas aktywów, tyle że
mierzone względem siebie samych, nie względem innych.

- **Krzywa jest sednem.** W całej tej aplikacji wartość rysowana jest jako długość, a długość może
  powiedzieć tylko, jak głęboka jest woda w tej jednej chwili. Głębokość jest kształtem w czasie:
  dołek i wyjście z niego to dwa miejsca na krzywej, a odległość między nimi w kadrze to liczba
  miesięcy, jakie upłynęły.
- **Te dwie liczby nie rosną razem.** W ostatnich dziesięciu latach fundusz Nasdaq spadł o 25,52%
  i wrócił do poziomu w sześć miesięcy; fundusz CSI 500 spadł o 56,07% i potrzebował osiemdziesięciu
  sześciu. Wydrukowana jako jedna liczba, druga wygląda na wzmocnioną wersję pierwszej — a nie jest.
- **Jedna skala głębokości dla całej tablicy.** Skalowanie każdego wiersza według jego własnego
  najgorszego momentu narysowałoby 0,2% funduszu rynku pieniężnego jako otchłań wielkości 56% CSI
  500 — na tablicy, której cały sens polega na tym, że tych dwóch nie można porównywać. Dlatego ten
  wiersz jest płaską linią przy własnej linii szczytu — i **ta płaskość jest jego komunikatem**.
- **Z korektą, miesięcznie i od własnego pierwszego miesiąca**, z powodów podanych przez wyścig
  klas aktywów: dystrybucje funduszu nigdy nie pojawiają się w jego cenie, a instrument, który
  dołącza w 2019, nie jest mierzony względem szczytu, którego nie miał.
- **Wiersze wciąż biegną.** Są uporządkowane według odległości od własnego szczytu — najbliżej
  szczytu na górze — i zamieniają się miejscami wraz z upływem miesięcy.
- **Złoto i fundusz towarowy były w chwili pomiaru wciąż pod wodą** — tablica zgłasza taki spadek
  jako otwarty, bo okres skończył się, zanim został naprawiony.
- **Albo własna lista.** Ostatnia grupa w menu to lista własna: wpisz kod, nazwę lub pinyin, aby
  dodać jeden walor, a trzy rynki można na niej mieszać. Jedna lista dla czterech tablic: akcję
  dodaną tu znajdziesz też na trzech pozostałych; pobiera się ją z korektą, dokładnie jak osiem
  funduszy, więc dywidendy i podziały są w liczbie. Poniżej trzech pobieranie jest odrzucane.

Nie podlega ustawieniu rynku: wszystkie osiem jest notowanych na giełdzie kontynentalnej. Mniej niż
dwanaście miesięcy w okresie jest odrzucane.

## Skuteczność

Wiersz to **udział zakończonych wejść, które zarobiły** — ze wszystkich miesięcy, w których można
było wejść i trzymać równie długo, część zakończona na plusie. Te same osiem instrumentów co w
wyścigu klas aktywów i na tablicy obsunięć, oceniane według tego, czy trzymanie ich zadziałało, a
nie według tego, ile dały zarobić.

- **Jedno wejście to szczęście; osiemdziesiąt cztery to wskaźnik.** Każdy miesiąc okresu jest
  wejściem i każde jest trzymane równie długo, więc trzymanie trzy lata w ciągu dziesięciu to
  osiemdziesiąt cztery wejścia na wiersz, nie jedno. Współdzielą miesiące i to jest sedno:
  przerzedzenie ich do trzech niezależnych zostawiłoby wskaźnik z trzema obserwacjami w środku.
- **Wejście liczy się od miesiąca, w którym się kończy.** To, co kupione w ostatnich trzech latach
  okresu, jeszcze się nie zakończyło, a policzenie niezakończonego wejścia jako straty wygięłoby
  każdy wiersz w dół na końcu wyłącznie z powodu kalendarza. Tablica zaczyna się więc w pierwszym
  miesiącu, w którym wejście mogło się zakończyć.
- **Wiersz dołącza, gdy zakończy się sześć wejść.** Jedno wejście to 0% albo 100%, i każda z tych
  dwóch liczb na końcu rankingu jest końcem, na który nie zapracowała.
- **Z korektą, miesięcznie i od pierwszego własnego miesiąca każdego instrumentu**, z powodów,
  które podaje wyścig klas aktywów: dystrybucje funduszu nigdy nie pojawiają się w jego cenie, a
  fundusz uruchomiony w 2019 nie ma wejść z 2016, które mógłby wygrać albo przegrać.
- **Okres utrzymania to jedyny nowy wybór na tej tablicy.** Jeden rok i pięć lat w tych samych
  dziesięciu latach to dwa różne pytania z dwiema różnymi odpowiedziami, a osiem wierszy
  porządkuje się między nimi na nowo.
- **Wiersze wciąż biegną.** Są uporządkowane według wskaźnika — najczęściej na plusie na górze — i
  zamieniają się miejscami wraz z upływem miesięcy.
- **Albo własna lista.** Ostatnia grupa w menu to lista własna: wpisz kod, nazwę lub pinyin, aby
  dodać jeden walor, a trzy rynki można na niej mieszać. Jedna lista dla czterech tablic: akcję
  dodaną tu znajdziesz też na trzech pozostałych; pobiera się ją z korektą, dokładnie jak osiem
  funduszy, więc dywidendy i podziały są w liczbie. Poniżej trzech pobieranie jest odrzucane.

Zmierzone w ostatnich dziesięciu latach przy trzymaniu trzy lata: fundusz Nasdaq był na plusie przy
wszystkich osiemdziesięciu czterech wejściach, a fundusz z Hongkongu przy czterdziestu procentach z
nich — dwa wiersze, które wyścig klas aktywów rozdziela dziesięcioma latami całkowitego zwrotu, a
ta tablica rozdziela tym, czy w ogóle udało się wejść.

Nie zależy od ustawienia rynku: wszystkie osiem jest notowanych na giełdzie kontynentalnej. Mniej
niż dwanaście miesięcy w okresie jest odrzucane.

## Macierz stóp zwrotu

![Strona w całości: podgląd po lewej, pasek odtwarzania poniżej, ustawienia po prawej.](media/monthly-matrix.png)

Miesięczne słupki ułożone w siatkę: tryb roku pokazuje sezonowość instrumentu przez dekadę, tryb porównania stawia kilka instrumentów obok siebie, by pokazać rotację.

- Tryb roku: wybierz instrument (wyszukiwanie lub predefiniowany szeroki indeks); zakres to 1–10 lat lub wszystkie. Jedno zapytanie zwraca dekadę miesięcznych słupków.
- Tryb porównania: 2–14 instrumentów z listy (branże poziomu 1 / tematy / szerokie indeksy / własna / akcje) obok siebie, na 6–48 miesięcy.
- Siatka zapala się komórka po komórce w kolejności czasu; na koniec podaje najsilniejszy i najsłabszy miesiąc zakresu oraz inne statystyki.
- Dane miesięczne obejmują dekadę za jednym razem, więc nie ma tu dziennego limitu dni — ale zbyt wiele instrumentów wykracza poza kadr.

## Kalendarz zysków i strat

![Strona w całości: podgląd po lewej, pasek odtwarzania poniżej, ustawienia po prawej.](media/gain-calendar.png)

Dowolna chińska akcja lub indeks, jego dzienny wzrost lub spadek ułożony w komórki kalendarza według miesięcy: czerwony przy wzroście, zielony przy spadku.

- Szukaj po kodzie, nazwie lub pinyinie; predefiniowane to szerokie indeksy. Obsługiwane są tylko instrumenty wybranego rynku.
- Lista ulubionych jest współdzielona z stroną akcji aplikacji — ulubiony dodany w jednym miejscu widać w obu.
- Zakres to 1, 3, 6 lub 12 miesięcy albo dowolny; pojedynczy instrument nadal podlega limitowi około 640 dni kalendarzowych.
- Końcowa statystyka podaje liczbę sesji wzrostowych i spadkowych.

## Plan DCA

![Strona w całości: podgląd po lewej, pasek odtwarzania poniżej, ustawienia po prawej.](media/dca-plan.png)

Kupowanie jednego instrumentu na stałą kwotę w stałych odstępach — w każdy dzień sesji, co tydzień lub co miesiąc — i animacja tego, czym stała się dyscyplina.

- Instrumenty jednym dotknięciem podążają za rynkiem: szerokie i złote ETF na akcjach A, hongkongskie fundusze śledzące, w USA SPY, QQQ i GLD.
- Kwotę i częstotliwość ustawiasz sam; okres to trzy, pięć lub dziesięć lat, albo tak daleko wstecz, jak sięgają dane (około trzynastu lat).
- Stopa zwrotu liczona jest na cenach skorygowanych wstecz, bez opłat. Wynik opisuje szereg cen, a nie rachunek, który ktokolwiek mógłby zrealizować.
- Oprócz 3, 5 i 10 lat oraz najdłuższego zakresu można wybrać **Własny**: podaj datę początkową i końcową, a następnie pobierz dane. Dostępnych jest około 35 lat wstecz — źródło zwraca około 640 dni kalendarzowych na jedno żądanie, a przejście wykonuje ich najwyżej dwadzieścia.

## Zwrot z pozycji

![Strona w całości: podgląd po lewej, pasek odtwarzania poniżej, ustawienia po prawej.](media/position.png)

Jeden zakup, trzymany latami — na przykład milion w 中国平安 w 2015 roku — animowany jako to, co zrobiły wartość i stopa zwrotu.

- Proponowane nazwy podążają za rynkiem: w Chinach akcje, które ludzie faktycznie mówią, że trzymali (Ping An, Moutai, CMB…), w Hongkongu Tencent, HSBC i Tracker Fund, w USA Apple, Berkshire i SPY.
- Kapitał początkowy i okres trzymania należą do ciebie; okres to trzy, pięć lub dziesięć lat — albo tak daleko, jak sięgają dane (około trzynastu lat).
- Zwrot liczony jest na cenach skorygowanych wstecz — dywidendy reinwestowane, bez opłat. Korekta wstecz kotwi się w pierwszym dniu notowań i narasta o dywidendy w przód, więc wczesne lata szczodrego płatnika nigdy nie stają się niedodatnie, jak to możliwe przy korekcie w przód.
- Ten sam zakres **Własny** działa dla pozycji: podaj dwie daty, a następnie pobierz dane. Jeśli instrument zadebiutował później niż podana data, pozycja zaczyna się w jego pierwszym dniu notowań.

## Film

Kadr jest zawsze 9:16. Wszystko inne ustalasz sam.

- Czas trwania zmienia tempo, a nie skraca animacji: wstęp, wzrost słupków i końcowe statystyki są rozłożone na wybraną długość.
- Marginesy są zapisane względem kadru 1080×1920 i skalowane do rozdzielczości eksportu, więc raz dobrany układ obowiązuje w każdym rozmiarze. Lewy margines decyduje też, gdzie trafiają opisy osi: za mały, i liczby wyjdą poza kadr.
- Linie bezpiecznego obszaru obrysowują to, co aplikacja na telefonie zakrywa własnym interfejsem. Rysują się w podglądzie i nigdy w pliku.

## Gdzie trafiają filmy

Eksporty zapisują się do folderu, który wybierasz w okienku. Dopóki żaden nie został wybrany, pierwszy eksport zapyta i potem zapamięta; ustawienia pozwalają to zmienić albo zapomnieć.

## Obraz w tle

Na stronie ustawień można umieścić obraz za oknem, przyciemniony. Karty i panele pozostają nieprzezroczyste, a okienko nawigacji przepuszcza tylko trochę — obraz widać głównie wokół nich. Podgląd wideo ma własne nieprzezroczyste tło i pozostaje bez zmian.

- Wybierz obraz z komputera lub użyj wprost jednej z tapet i obrazów ekranu blokady dołączonych do systemu Windows.
- Wybrany obraz jest kopiowany do folderu aplikacji — przeniesienie lub usunięcie oryginału nie wpływa na tło.
- Suwak intensywności maski określa, jak bardzo obraz zostaje przygaszony, w zakresie od 30% do 95%.
- Gdy włączony jest wysoki kontrast, obraz w tle nie jest pokazywany.
## Tło animacji

Na stronie ustawień możesz zmienić to, na czym rysowana jest animacja: wbudowany gradient, dwa własne kolory albo obraz. Dotyczy to podglądu, eksportowanego wideo i obrazu okładki — wszystkie trzy rysuje ten sam renderer, więc nie ma „ładnie w podglądzie, inaczej w pliku”.

- Przy kolorach podajesz ton górny i dolny, a klatka przechodzi między nimi. Lepiej ciemne: każdy odcień tekstu jest jasny, a jasne tło utrudnia odczyt liczb.

- Suwak krycia określa, ile z dwóch kolorów zostanie użyte: przy 100% klatka to po prostu wybrana para, a niżej spod spodu prześwituje własny ciemny gradient strony. To właśnie utrzymuje czytelność jasnej pary.

- Wybór obrazu działa tak samo jak dla tła okna: obraz z komputera albo tapeta dołączona do Windows. Wybrany jest kopiowany do folderu aplikacji.

- Obraz wypełnia klatkę, a nadmiar jest przycinany, więc proporcje nigdy się nie rozciągają.

- Suwak przyciemnienia decyduje, jak mocno obraz jest cofany do własnego tła strony: od 20% do 95%.

## Dane i to, czego nie powiedzą

Notowania pochodzą z publicznych punktów końcowych Tencent Finance, a kadr zawsze podaje źródło. Te filmy opisują to, co już zostało zawarte. Są wyłącznie informacyjne i nie stanowią porady inwestycyjnej.

- Obroty są przeliczane na setki milionów juanów, a wolumen przechodzi na większą jednostkę, gdy liczby tego wymagają, żeby oś dała się czytać.
- Obroty przelicza się na setki milionów — juanów na kontynencie i w Hongkongu, dolarów w USA. Każdy rynek zachowuje swoją walutę.
- Zakres dłuższy niż to, co jedno żądanie może zwrócić, jest odrzucany zamiast po cichu ucięty: około 900 dni kalendarzowych na interwale dziennym, około piętnastu lat na stronie świec, która cofa się strona po stronie, i cała historia na miesięcznym. Ciche ucięcie to najgorszy wynik — znika wtedy **początek**, a wykres bez pierwszych lat to po prostu krótszy wykres, który wygląda zupełnie normalnie.

## Aktualizowanie

Gdy w Microsoft Store jest nowsza wersja, w panelu nawigacji obok Ustawień pojawia się przycisk **Aktualizuj**; jedno kliknięcie ją instaluje.

- Pojawia się tylko wtedy, gdy w Store naprawdę jest nowsza wersja. Kompilacja deweloperska albo zainstalowana z boku nigdy go nie zobaczy i tak ma być.
- Aplikacja zamyka się na czas instalacji i uruchamia ponownie w nowej wersji, a przycisk znika. Jeśli trwa eksport, najpierw zapyta.
- Jeśli instalacja się nie uda, poda powód — tylko przez Wi-Fi, za słaba bateria — a aktualizację można też zainstalować z Microsoft Store.

## Coś nie działa?

Napisz na gaqo@outlook.com, co robiłeś i czego się zamiast tego spodziewałeś. Numer wersji jest na stronie ustawień.
