# AShare Motion Studio

Ta aplikacja zamienia wskaźniki rynku akcji A w pionowe filmy na telefon. Wybierasz okres, patrzysz na podgląd, aż da się go dobrze odczytać, i eksportujesz plik MP4. Nic więcej nie trzeba instalować.

## Obroty całego rynku

Dzienne obroty całego rynku: kwoty indeksów zbiorczych z Szanghaju i Shenzhen zsumowane, jeden słupek na sesję.

- Zostają tylko dni, w których handlowały wszystkie uwzględnione rynki, żeby święto na jednym z nich nie sprawiało wrażenia, że suma się załamała.
- Sesja wciąż trwająca jest pomijana. Niedokończony dzień zawiera tylko swój fixing otwarcia i narysowałby się jako słupek przyklejony do osi.
- Opcja pekińska dodaje indeks BSE 50, który obejmuje tylko swoje spółki, a nie całą giełdę. To inna miara, i mniejsza.

## Wolumen spółki

Wolumen jednej spółki na tle jej wskaźnika obrotu, w dwóch panelach jeden nad drugim.

- Z sesji na sesję wolumen i wskaźnik obrotu są proporcjonalne, więc oba panele mają niemal ten sam kształt. W ciągu jednego dnia wolumen minutowy i narastający obrót wyglądają naprawdę inaczej, i to jest ciekawszy obraz.
- Źródło danych śróddziennych trzyma tylko ostatnie sesje, więc ten tryb proponuje właśnie je, a nie dowolną datę.

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
- Okres dłuższy niż około 640 dni kalendarzowych jest odrzucany, a nie po cichu skracany, bo tyle zwraca jedno zapytanie do źródła.

## Coś nie działa?

Napisz na gaqo@outlook.com, co robiłeś i czego się zamiast tego spodziewałeś. Numer wersji jest na stronie ustawień.
