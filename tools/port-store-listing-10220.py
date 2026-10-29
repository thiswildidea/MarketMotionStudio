# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.22.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 1.0.21.0 那一栏已经交上去了，
所以本版另起一条，只说它之后的改动。1.0.21 之后这台机器上落地的三件事，都在同一个页面上：

- 双屏页终于画自己的标题：行是正确的高度，字从来没画上去。字补上之后，样式跟着设置页里
  那一份全局标题设置（纯色 / 金属 / 浮雕＋取色），与其它页同源。
- 双屏页的下边距滑杆接进画面：竖向行原本全锚在画面顶部，滑杆只改数字不动画面。改成上下
  双轨之后 150—420 全程有效，默认那一档的画面和从前一样。
- 双屏页两半按同一个节拍播：指数线在自己没有数据的时段（午休、A 股 15:00 之后）平线跟随
  而不是冻住，持仓曲线按分钟推进而不是按条数跳，下面画哪几条指数随账本的市场构成走。
  不带午休播放时中间也不再空等一段。

**只说用户能感知的那半句**，代码细节（TitleBlock.Draw、Row 的双轨重映射、CreditLine）不写。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md
是 **CRLF 无 BOM**，写完照原样写回。脚本名由 manifest 的版本号算出 `10220`。

用法：python tools\\port-store-listing-10220.py      （跑第二遍应当是「改了 0 条」）
"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。
LIMIT = 1500

NEWS = {
    "zh-Hans":
        "本版补齐「持仓·大盘 双屏」页的三处旧账。其一，这一页终于画自己的标题了：行的高度早就留好，"
        "字却从头到尾没画上去——现在连换行一起补上，字体样式（纯色、金属、浮雕）和颜色跟着你在设置页"
        "挑的那一份全局标题设置，不必在这一页再调一遍。其二，下边距滑杆真正接进了画面：以前这一页的"
        "每一行都只在画面顶部生根，滑杆挪半天只是改了一个数字、图画一像素都没动；现在竖着排的行上下"
        "各有抓手，150 到 420 全程有效，默认那一档和从前一模一样。其三，上下两幅图终于按同一个节拍"
        "走：指数线在自己没有数据的时段平着跟到下一个开盘时刻——午休不再冻在 11:30，A 股 15:00 收市"
        "后一路跟到 16:00；持仓曲线改成按分钟推进，两半的线头逐帧落在同一条竖线上。下面画哪几条指数"
        "也跟着账本走：全是 A 股就只画 A 股指数、时间轴收到 15:00，全是港股就只画港股，混合的才把两个"
        "市场都摆上。不带午休播放时，中间也不再空等一段。",
    "zh-Hant":
        "本版補齊「持倉·大盤 雙屏」頁的三處舊帳。其一，這一頁終於畫自己的標題了：行的高度早就留好，"
        "字卻從頭到尾沒畫上去——現在連換行一起補上，字體樣式（純色、金屬、浮雕）和顏色跟著你在設定頁"
        "挑的那一份全域標題設定，不必在這一頁再調一次。其二，下邊界滑桿真正接進了畫面：以前這一頁的"
        "每一行都只在畫面頂端生根，滑桿拉半天只是改了一個數字、圖畫一像素都沒動；現在豎著排的行上下"
        "各有抓手，150 到 420 全程有效，預設那一檔和從前一模一樣。其三，上下兩幅圖終於按同一個節拍"
        "走：指數線在自己沒有數據的時段平著跟到下一個開盤時刻——午休不再凍在 11:30，A 股 15:00 收市"
        "後一路跟到 16:00；持倉曲線改成按分鐘推進，兩半的線頭逐幀落在同一條豎線上。下面畫哪幾條指數"
        "也跟著帳本走：全是 A 股就只畫 A 股指數、時間軸收到 15:00，全是港股就只畫港股，混合的才把兩個"
        "市場都擺上。不帶午休播放時，中間也不再空等一段。",
    "en-US":
        "This release settles three debts on the Book & Board Split page. First, that page now "
        "draws its own title: the rows were always spaced for it, but the words were never put on "
        "the canvas — they are now, wrapping included, taking their look (plain, gilded or engraved) "
        "and colour from the one set of title settings you pick for the whole app, so nothing has to "
        "be chosen twice. Second, the bottom margin slider reaches the picture: every row on that "
        "page used to take root at the top of the frame and nowhere else, so dragging it moved a "
        "number and not one pixel; the rows now have a hold at each end and answer across the whole "
        "150 to 420 range, the default drawing exactly what it drew before. Third, the two halves "
        "play on one beat: an index line runs flat through the stretches where it has no prints — "
        "the lunch break, and the hour after the A-share close at three — instead of stopping dead, "
        "and the book's curve advances by the minute rather than by row count, so every head lands "
        "on the same vertical line frame after frame. Which indices the lower half draws follows the "
        "book: an all-A-share portfolio gets A-share indices and a clock that stops at 15:00, an "
        "all-Hong Kong one gets Hong Kong only, and a mixed book gets both. Played without the lunch "
        "break, nothing stands still midway either.",
    "ja":
        "今回の更新は「資産と市場の分割表示」ページの三つの宿題を片づけます。ひとつはタイトルです。"
        "行の高さは最初から空けてあったのに、文字は一度も描かれていませんでした。折り返しも含めて描く"
        "ようになり、書体（単色・金属・浮き彫り）と色は設定ページで選んだアプリ全体のタイトル設定を"
        "そのまま使います。このページで改めて選び直す必要はありません。もうひとつは下マージンの"
        "スライダーです。このページの行はすべて画面の上辺だけで固定されていたため、いくら動かしても"
        "数字が変わるだけで絵は一画素も動きませんでした。行は両端で支えられるようになり、150 から 420 "
        "までの全域が有効になりました。既定値の絵は以前とまったく同じです。三つめは上下の図が同じ拍子で"
        "進むことです。指数の線は自分のデータがない時間帯を水平に進んで次の立ち会い時刻までつながり"
        "ます——昼休みに 11:30 で止まることはなく、A 株は 15:00 の大引けから 16:00 まで伸びます。"
        "資産の曲線は分数ではなく分で進むようになり、上下の線の頭はどのコマでも同じ縦の位置に揃い"
        "ます。下に描く指数も資産の中身に従います。A 株だけなら A 株の指数だけ、時間軸は 15:00 まで、"
        "香港株だけなら香港の指数だけ、混ざっていれば両方です。昼休みを挟まない設定でも、途中で止まる"
        "ことはありません。",
    "ko":
        "이번 업데이트는 「계좌·시장 분할」 페이지의 오래된 빚 세 가지를 갚습니다. 하나는 제목입니다."
        " 줄 높이는 처음부터 비워 두었지만 글자는 한 번도 그려지지 않았습니다. 줄바꿈까지 이제 그리며,"
        " 글꼴(단색·금속·양각)과 색은 설정 페이지에서 고른 앱 전체 제목 설정을 그대로 따릅니다. 이"
        " 페이지에서 다시 고를 필요는 없습니다. 다른 하나는 아래쪽 여백 슬라이더입니다. 이 페이지의 모든"
        " 줄이 화면의 위쪽에만 뿌리를 두고 있어, 아무리 움직여도 숫자만 바뀌고 그림은 한 픽셀도 움직이지"
        " 않았습니다. 이제 줄은 양끝에서 붙잡혀 150부터 420까지 전 구간이 동작하며, 기본값의 그림은"
        " 이전과 한 치도 다르지 않습니다. 세 번째는 위아래 두 그림이 같은 박자로 움직이는 것입니다."
        " 지수선은 자기 데이터가 없는 구간을 수평으로 이어 다음 개장 시각까지 따라갑니다. 점심 시간에"
        " 11:30에서 굳지 않고, A주는 15:00 폐장 뒤 16:00까지 이어집니다. 계좌 곡선은 칸수가 아니라"
        " 분으로 나아가 두 반쪽의 선 머리가 매 프레임 같은 세로선에 놓입니다. 아래에 그릴 지수도 계좌"
        " 구성에 따릅니다. A주뿐이면 A주 지수만 그리고 시간축은 15:00에서 멈추고, 홍콩뿐이면 홍콩만,"
        " 섞여 있으면 둘 다 그립니다. 점심 시간을 넣지 않고 재생해도 중간에 멈춤이 없습니다.",
    "de":
        "Dieses Release begleicht drei alte Schulden der Seite Depot & Markt geteilt. Erstens zeichnet "
        "diese Seite nun ihre eigene Überschrift: Die Zeilen waren von Anfang an dafür freigehalten, die "
        "Wörter aber nie auf die Fläche gesetzt — das geschieht jetzt, Zeilenumbruch inbegriffen, und "
        "Schriftart (einfarbig, metallisch oder graviert) sowie Farbe nimmt sie aus denselben "
        "Titeleinstellungen, die du für die ganze Anwendung wählst. Zweitens erreicht der Schieber für "
        "den unteren Rand das Bild: Jede Zeile dieser Seite war nur am oberen Rahmen verankert, also "
        "bewegte das Ziehen eine Zahl und keinen Pixel. Die Zeilen haben nun an beiden Enden Halt und "
        "gehorchen über den ganzen Bereich von 150 bis 420; bei der Voreinstellung entsteht das Bild von "
        "zuvor. Drittens laufen beide Hälften im gleichen Takt: Eine Indexlinie läuft über die Strecken, "
        "auf denen sie keine Daten hat, waagerecht bis zur nächsten Handelszeit weiter — sie friert in "
        "der Mittagspause nicht mehr bei 11:30 ein, und die A-Aktien laufen nach dem Schluss um 15:00 bis "
        "16:00 mit. Die Kurve des Depots rückt nach Minuten vor statt nach Zeilenzahl, also landen alle "
        "Köpfe auf derselben senkrechten Linie. Welche Indizes unten stehen, richtet sich nach dem Depot: "
        "Nur A-Aktien heißt nur A-Aktien-Indizes und eine Uhr, die bei 15:00 endet, nur Hongkong heißt "
        "nur Hongkong, gemischt heißt beides. Ohne Mittagspause steht ebenfalls nichts still.",
    "fr":
        "Cette version règle trois vieilles dettes de la page Portefeuille & marché partagés. D'abord, "
        "cette page dessine enfin son propre titre : les lignes lui étaient réservées depuis le départ, "
        "mais les mots n'ont jamais été posés sur l'image — c'est fait maintenant, retour à la ligne "
        "compris, et la police (uni, doré ou gravé) comme la couleur viennent des réglages de titre "
        "choisis une fois pour toute l'application. Ensuite, le curseur de marge basse atteint le dessin "
        ": chaque ligne n'était ancrée qu'au bord supérieur, si bien que le tirer ne bougeait qu'un "
        "chiffre et pas un pixel ; les lignes tiennent désormais par les deux bouts et répondent sur "
        "toute la plage de 150 à 420, la valeur par défaut donnant l'image d'avant. Enfin, les deux "
        "moitiés avancent au même tempo : une ligne d'indice file à plat sur les tronçons où elle n'a "
        "aucune donnée jusqu'à la réouverture — elle ne gèle plus à 11:30 pour la pause déjeuner, et les "
        "A-actions filent jusqu'à 16:00 après la clôture de 15:00. La courbe du portefeuille avance à la "
        "minute et non au nombre de rangées, si bien que toutes les têtes tombent sur la même verticale à "
        "chaque image. Les indices du bas suivent le portefeuille : que des A-actions, et l'on ne dessine "
        "que des indices A avec une horloge arrêtée à 15:00 ; que du Hongkong, et l'on ne garde que "
        "Hongkong ; un panaché, et l'on met les deux. Sans la pause déjeuner, plus rien ne s'immobilise "
        "au milieu non plus.",
    "it":
        "Questa versione salda tre debiti antichi della pagina Portafoglio e mercato divisi. Primo: "
        "la pagina ora disegna il proprio titolo. Le righe erano tenute libere dall'inizio, ma le "
        "parole non sono mai state scritte — ora lo sono, andata a capo compresa, e il carattere "
        "(tinta unita, dorato o inciso) e il colore arrivano dalle stesse impostazioni di titolo che "
        "scegli una volta per tutta l'applicazione: qui non c'è nulla da regolare due volte. Secondo: "
        "il cursore del margine inferiore raggiunge finalmente il disegno. Ogni riga di questa pagina "
        "era ancorata solo al bordo superiore, così spostarlo cambiava un numero e non un pixel; ora "
        "le righe sono tenute da entrambi i capi e rispondono su tutta la gamma da 150 a 420, e al "
        "valore predefinito il disegno è esattamente quello di prima. Terzo: le due metà procedono allo "
        "stesso passo. Una linea di indice corre in piano sui tratti in cui non ha dati fino all'ora "
        "di riapertura — non si congela più alle 11:30 per la pausa pranzo, e le A-actions corrono fino "
        "alle 16:00 dopo la chiusura delle 15:00. La curva del portafoglio avanza al minuto e non a "
        "numero di righe, così tutte le teste cadono fotogramma dopo fotogramma sulla stessa verticale. "
        "Gli indici in basso seguono il portafoglio: solo A-actions, e si disegnano solo indici A con "
        "un orologio che si ferma alle 15:00; solo Hong Kong, e resta Hong Kong; misto, e compaiono "
        "entrambi. Senza la pausa pranzo non si ferma nulla nemmeno a metà.",
    "es":
        "Esta versión salda tres deudas antiguas de la página Cartera y mercado divididos. Primero, "
        "esa página por fin dibuja su propio título: las líneas estaban reservadas desde el principio, "
        "pero las palabras nunca llegaron al lienzo — ya están, con el salto de línea incluido, y la "
        "tipografía (liso, dorado o grabado) y el color salen de los mismos ajustes de título que "
        "eliges una vez para toda la aplicación, sin nada que volver a ajustar aquí. Segundo, la barra "
        "del margen inferior por fin alcanza el dibujo: cada línea de esa página solo echaba raíces en "
        "el borde superior, así que moverla cambiaba un número y ni un solo píxel; ahora las líneas se "
        "sujetan por los dos extremos y responden en todo el rango de 150 a 420, y con el valor "
        "predeterminado el dibujo es exactamente el de antes. Tercero, las dos mitades marchan al mismo "
        "compás: una línea de índice avanza en horizontal por los tramos en que no tiene datos hasta "
        "la hora de reapertura — ya no se congela a las 11:30 con la pausa del almuerzo, y las acciones "
        "A siguen hasta las 16:00 tras el cierre de las 15:00. La curva de la cartera avanza por "
        "minuto y no por número de fila, así que todas las cabezas caen fotograma tras fotograma sobre "
        "la misma vertical. Los índices de abajo siguen a la cartera: solo acciones A, y se dibujan "
        "solo índices A con un reloj que se detiene a las 15:00; solo Hong Kong, y queda Hong Kong; "
        "mixta, y salen ambos. Sin la pausa del almuerzo tampoco se detiene nada a mitad de camino.",
    "pt-BR":
        "Esta versão quita três dívidas antigas da página Carteira e mercado divididos. Primeiro, essa "
        "página finalmente desenha o próprio título: as linhas estavam reservadas desde o começo, mas "
        "as palavras nunca foram para o quadro — agora vão, com a quebra de linha incluída, e a "
        "tipografia (lisa, dourada ou gravada) e a cor vêm dos mesmos ajustes de título que você escolhe "
        "uma vez para todo o aplicativo, sem nada para regular duas vezes aqui. Segundo, a barra da "
        "margem inferior finalmente alcança o desenho: cada linha dessa página criava raízes apenas na "
        "borda de cima, então arrastá-la mudava um número e nenhum pixel; agora as linhas se apoiam nos "
        "dois extremos e respondem em toda a faixa de 150 a 420, e no valor padrão o desenho é "
        "exatamente o de antes. Terceiro, as duas metades andam no mesmo compasso: uma linha de índice "
        "segue reta pelos trechos em que não tem dados até a hora da reabertura — não congela mais às "
        "11:30 na pausa do almoço, e as ações A seguem até as 16:00 depois do fechamento das 15:00. A "
        "curva da carteira avança por minuto, e não por número de linha, então todas as cabeças caem "
        "quadro após quadro na mesma vertical. Os índices de baixo seguem a carteira: só ações A, e "
        "desenham-se só índices A com um relógio que para às 15:00; só Hong Kong, e fica Hong Kong; "
        "misturada, e aparecem os dois. Sem a pausa do almoço nada fica parado no meio tampouco.",
    "pl":
        "To wydanie spłaca trzy stare długi strony Portfel i rynek na pół. Po pierwsze, ta strona "
        "wreszcie rysuje własny tytuł: wiersze były dla niego od początku odłożone, ale słowa nigdy nie "
        "trafiły na obraz — teraz trafiają, z łamaniem wiersza, a krój (gładki, złocony lub grawerowany) "
        "i kolor biorą się z tych samych ustawień tytułu, które wybierasz raz dla całej aplikacji. Tu "
        "nie trzeba niczego ustawiać powtórnie. Po drugie, suwak dolnego marginesu wreszcie dosięga "
        "rysunku: każdy wiersz tej strony miał korzenie tylko przy górnej krawędzi, więc przesunięcie "
        "zmieniało liczbę, a nie ani jeden piksel; teraz wiersze trzymają się obu końców i reagują w "
        "całym zakresie od 150 do 420, a przy wartości domyślnej rysunek jest dokładnie taki jak "
        "wcześniej. Po trzecie, obie połowy idą w jednym rytmie: linia indeksu biegnie poziomo przez "
        "odcinki, na których nie ma danych, aż do godziny otwarcia — nie zamarza już o 11:30 na przerwę "
        "obiadową, a akcje A jadą do 16:00 po zamknięciu o 15:00. Krzywa portfela posuwa się według "
        "minut, nie według liczby wierszy, więc wszystkie głowy lądują klatka po klatce na tej samej "
        "pionowej linii. Indeksy na dole idą za portfelem: same akcje A to tylko indeksy A i zegar "
        "kończący się o 15:00, sam Hongkong to tylko Hongkong, mieszany to jedno i drugie. Bez przerwy "
        "obiadowej nic nie stoi w miejscu również w środku.",
    "cs":
        "Tato verze vyrovnává tři staré dluhy strany Portfolio a trh napůl. Zaprvé: ta strana si "
        "konečně kreslí vlastní nadpis. Řádky pro něj byly od začátku uvolněné, ale slova se na plátno "
        "nikdy nedostala — teď ano, i se zalamováním, a písmo (hladké, zlacené nebo ryté) i barva "
        "přicházejí ze stejného nastavení nadpisů, které volíš jednou pro celou aplikaci. Zde není co "
        "nastavovat podruhé. Zadruhé: jezdec dolního okraje konečně dosáhne obrázku. Každý řádek té "
        "strany dřív zakořenil jen u horní hrany, takže táhnout znamenalo změnit číslo a ani jeden "
        "pixel; teď se řádky drží na obou koncích a poslouchají v celém rozsahu 150 až 420, při výchozí "
        "hodnotě je obrázek přesně takový jako dřív. Zatřetí: obě poloviny jdou v jednom rytmu. Čára "
        "indexu běží vodorovně přes úseky, kde nemá data, až do hodiny otevření — už neztuhne v 11:30 na "
        "polední přestávku a akcie A jedou po uzavření v 15:00 až do 16:00. Křivka portfolia postupuje "
        "po minutách, ne podle počtu řádků, takže všechny hlavy padají snímek za snímkem na tutéž "
        "svislici. Indexy dole se řídí portfoliem: jen akcie A znamená jen indexy A a hodiny končící v "
        "15:00, jen Hongkong znamená jen Hongkong, smíšené znamená obojí. Bez polední přestávky nic "
        "uprostřed také nestojí.",
    "ru":
        "Этот выпуск закрывает три старых долга страницы «Портфель и рынок пополам». Во-первых, "
        "страница наконец рисует собственный заголовок: строки под него были оставлены с самого начала, "
        "но слова ни разу не были написаны — теперь написаны, вместе с переносом, а начертание (гладкое, "
        "золотое или гравированное) и цвет берутся из той самой настройки заголовков, которую ты "
        "выбираешь один раз для всего приложения. Здесь нечего настраивать дважды. Во-вторых, ползунок "
        "нижнего поля наконец доходит до рисунка: каждая строка этой страницы пускала корни только у "
        "верхнего края, поэтому сдвиг менял число и ни одного пикселя; теперь строки держатся за оба "
        "конца и слушаются во всём диапазоне от 150 до 420, а при значении по умолчанию рисунок в "
        "точности такой же, как прежде. В-третьих, обе половины идут в одном такте: линия индекса идёт "
        "горизонтально через отрезки, где у неё нет данных, до часа открытия — она больше не застывает "
        "в 11:30 на обеденный перерыв, а акции А после закрытия в 15:00 дотягивают до 16:00. Кривая "
        "портфеля продвигается по минутам, а не по числу строк, поэтому все головы кадр за кадром ложатся "
        "на одну вертикаль. Индексы внизу следуют за портфелем: одни акции А — рисуются только индексы А "
        "и часы, остановленные в 15:00; один Гонконг — только Гонконг; смешанный — и то и другое. Без "
        "обеденного перерыва посредине тоже ничего не стоит.",
    "tr":
        "Bu sürüm, Portföy ve Piyasa bölünmüş sayfasının üç eski borcunu kapatıyor. Birincisi: sayfa "
        "artık kendi başlığını çiziyor. Satırlar en başından beri ona ayrılmıştı ama sözcükler hiç "
        "tuvale yazılmadı — şimdi yazılıyor, satır kaydırmasıyla birlikte; yazı tipi (düz, altın veya "
        "oyma) ve renk, tüm uygulama için bir kez seçtiğin başlık ayarlarından geliyor, burada ikinci "
        "kez ayar yapman gerekmiyor. İkincisi: alt kenar boşluğu kaydırıcısı sonunda çizime ulaştı. Bu "
        "sayfanın her satırı kökünü yalnızca üst kenara salmıştı, bu yüzden kaydırmak bir sayıyı "
        "değiştiriyor, tek bir pikseli değil; satırlar artık iki ucundan tutunuyor ve 150’den 420’ye "
        "tüm aralıkta söz dinliyor, öntanımlı değerde çizim tıpkı eskisi gibi. Üçüncüsü: iki yarı "
        "aynı tempoda ilerliyor. Endeks çizgisi, verisi olmadığı bölümleri yatay geçip açılış saatine "
        "kadar uzanıyor — öğle arasında 11:30’da donup kalmıyor, A hisseleri de 15:00 kapanışından "
        "sonra 16:00’a kadar gidiyor. Portföy eğrisi satır sayısına göre değil dakikaya göre ilerliyor, "
        "böylece kare kare tüm uçlar aynı düşey çizgiye düşüyor. Alttaki endeksler de portföye uyuyor: "
        "yalnız A hissesi varsa yalnız A endeksleri ve 15:00’te duran bir saat, yalnız Hong Kong varsa "
        "yalnız Hong Kong, karışıksa ikisi birden. Öğle arası gösterilmediğinde ortada da hiçbir şey "
        "durmuyor.",
}


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    if sorted(NEWS) != sorted(LANGS):
        print("× 文案漏了语言：%s" % sorted(set(LANGS) - set(NEWS)))
        return 1

    changed = 0

    for n, lang in enumerate(LANGS):
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            print(f"× {lang}: 只数到 {len(subs)} 个小标题")
            return 1

        at = subs[1] + 1       # 「此版本的新增功能」下面的正文

        while at < end and not lines[at].strip():
            at += 1

        text = NEWS[lang]

        if lines[at] == text:
            print(f"· {lang}: （已是本版，{len(text)} 字）")
            continue

        lines[at] = text
        changed += 1
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: 「{lines[subs[1]][4:]}」改写（{len(text)} 字）")

    if changed:
        LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))

    longest = max((len(NEWS[l]), l) for l in LANGS)
    over = [(l, len(NEWS[l])) for l in LANGS if len(NEWS[l]) > LIMIT]

    if over:
        print(f"\n！超过商店 {LIMIT} 字上限：{over}")
        return 1

    print(f"\n最长的 {longest[1]} {longest[0]} 字，都在 {LIMIT} 以内")
    print(f"改了 {changed} 条（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
