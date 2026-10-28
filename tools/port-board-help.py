#!/usr/bin/env python3
"""Adds the 持仓·大盘 双屏 section to all fourteen help files.

The new page (`Pages/BoardPage.xaml`) sits between 实时持仓收益 and the crypto pages in
the menu, so its section goes between those two in the manual. Both neighbours' headings
are read from each language's own resource file — the manual's headings are the page
titles, and the resource file is their only source — so the script carries no per-language
anchors to drift.

Idempotent: a file that already carries the new heading is left alone. Help markdown is
LF, no BOM.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "MarketMotionStudio"

SECTIONS = {
    "zh-Hans": """## 持仓·大盘 双屏

上半是持仓的当日盈亏，下半是 A 股与港股指数的实时走势：两边各占一半，共用一根时钟，动画一起一分钟一分钟往前走。

- **上半画你自己的账**，和「实时持仓收益」读的是同一本：当日盈亏曲线、零轴，今天的盈亏数字就标在曲线末端，还标出贡献最大与拖累最大的两只（可按设置把股票名藏成 \\*）。管理持仓与导入成交这页也有——同一套对话框、同一本账，任何一页改了，另一页取数后就是最新。

- **两个半屏可以互换**（指数在上或收益在上），两条曲线一样宽，好对照着看；午休可以从时间轴上拿掉——两个市场同显时，拿掉的是双方都休的 12:00–13:00。四项费率与「实时持仓收益」是同一份设置，在这页改，那页重取数后同样生效。

- **下半只画指数**：A 股六个（上证、沪深300、深证成指、中证500、创业板指、上证50）与港股三个（恒生、国企、恒生科技），默认选上证和恒生。个股、ETF、币种都不在这页 —— 它回答的是「大盘今天怎么走」。

- **指数一律按昨收换算成涨跌幅**：恒生两万三千点与上证三千六百点没法同轴比价，换成百分比之后才放得进同一张图。图例在右侧，跟着画面走。

- **时间轴看到谁收盘为止**：只选 A 股指数，画到 15:00；选了港股指数，画到 16:00。两边都选时，A 股线在 15:00 收盘后走平，并画一条竖线写「A 股收盘 15:00」，港股继续走到 16:00。

- **数据是最近一个交易日的分钟行情**：开盘时看是「此刻」，收盘后取一次就是全天。开市时可打开自动刷新（每 30 秒），和「实时持仓收益」一个节奏。

- 视频时长、标题、背景与导出，和其它页一样在右侧面板里设置。
""",
    "zh-Hant": """## 持倉·大盤 雙屏

上半是持倉的當日盈虧，下半是 A 股與港股指數的即時走勢：兩邊各佔一半，共用一根時鐘，動畫一起一分鐘一分鐘往前走。

- **上半畫你自己的帳**，和「即時持倉收益」讀的是同一本：當日盈虧曲線、零軸，今天的盈虧數字就標在曲線末端，還標出貢獻最大與拖累最大的兩隻（可按設定把股票名藏成 \\*）。管理持倉與匯入成交這頁也有——同一套對話框、同一本帳，任何一頁改了，另一頁取數後就是最新。

- **兩個半屏可以互換**（指數在上或收益在上），兩條曲線一樣寬，好對照著看；午休可以從時間軸上拿掉——兩個市場同顯時，拿掉的是雙方都休的 12:00–13:00。四項費率與「即時持倉收益」是同一份設定，在這頁改，那頁重取數後同樣生效。

- **下半只畫指數**：A 股六個（上證、滬深300、深證成指、中證500、創業板指、上證50）與港股三個（恆生、國企、恆生科技），預設選上證和恆生。個股、ETF、幣種都不在這頁 —— 它回答的是「大盤今天怎麼走」。

- **指數一律按昨收換算成漲跌幅**：恆生兩萬三千點與上證三千六百點沒法同軸比價，換成百分比之後才放得進同一張圖。圖例在右側，跟著畫面走。

- **時間軸看到誰收盤為止**：只選 A 股指數，畫到 15:00；選了港股指數，畫到 16:00。兩邊都選時，A 股線在 15:00 收盤後走平，並畫一條豎線寫「A 股收盤 15:00」，港股繼續走到 16:00。

- **資料是最近一個交易日的分鐘行情**：開盤時看是「此刻」，收盤後取一次就是全天。開市時可打開自動重新整理（每 30 秒），和「即時持倉收益」一個節奏。

- 影片時長、標題、背景與匯出，和其它頁一樣在右側面板裡設定。
""",
    "en-US": """## Book & Board Split

The book's day above, mainland and Hong Kong indexes below: half the frame each, on one clock, the animation walking forward a minute at a time together.

- **The upper half draws your own book** — the same one the Intraday P&L page reads: the day's profit curve on its zero line, today's figure riding the curve's end, plus the best and the worst contributor named (their names can be hidden behind asterisks). Manage holdings and import trades live here too — the same dialogs over the same book, and an edit on either page is the other page's next fetch.

- **The two halves can swap** (indexes on top, or the book on top), the two curves run the same width so they read against each other, and the midday pause can come off the clock — with both venues on the frame, the pause taken out is the one both keep, 12:00 to 13:00. The four fee rates are the intraday page's own setting: change them here and that page recomputes with them too.

- **The lower half draws indexes only**: six mainland ones (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) and three from Hong Kong (Hang Seng, HSCEI, Hang Seng Tech), the SSE Composite and the Hang Seng ticked to start. Stocks, ETFs and coins are not on this page — it answers how the market is doing today.

- **Every index is plotted as its change against yesterday's close**: the Hang Seng at twenty-three thousand and the SSE at thirty-six hundred cannot share an axis, percentages can. The legend sits to the right and moves with the frame.

- **The clock runs to whoever closes last**: mainland indexes only, to 15:00; a Hong Kong index selected, to 16:00. With both, the mainland lines hold flat after the 15:00 close under a rule marked "mainland close 15:00", while Hong Kong keeps going to 16:00.

- **The data is the latest trading day, minute by minute**: during the session it reads as "right now"; one fetch after the close is the whole day. While the market is open the auto-refresh can be switched on (every 30 seconds), the same beat as the intraday page.

- Duration, title, backdrop and export are set in the panel on the right, like every other page.
""",
    "ja": """## 資産と市場の分割表示

上に保有資産の当日損益、下に A 股と香港指数のリアルタイム推移：半分ずつ、一つの時計で、アニメーションは一分ずつ一緒に進みます。

- **上半分はあなた自身の帳簿**を描きます。「時間内損益」と同じ帳を読みます。当日の損益カーブとゼロ軸、その日の数字はカーブの先端に添え、最大の貢献と最大の足引っ張りも名前付きで示します（設定で名前を \\* で隠せます）。保有管理と約定の取り込みもこのページにあります——同じダイアログ、同じ帳で、どちらで変えてももう一方の次の取得で最新になります。

- **二つの半分は入れ替えられます**（インデックスを上に、あるいは損益を上に）。二つの曲線は同じ幅で並び見比べられ、昼休みは時間軸から外せます——両市場を同時に出しているとき外れるのは、双方が休んでいる 12:00–13:00 です。四つの手数料は「時間内損益」と同じ設定で、こちらで変えればあちらの再取得にも反映されます。

- **下の半分は指数だけ**：A 股六本（上証、滬深300、深証成指、中証500、創業板指、上証50）と香港三本（恒生、国企、恒生テック）。既定は上証と恒生。個別株・ETF・通貨はこのページにありません —— 答えるのは「市場は今日どう動いたか」。

- **指数はすべて前日終値比の％で描きます**：恒生の二万三千と上証の三千六百は同じ軸に乗らない。パーセントに換えて初めて一枚の図になる。凡例は右側、画面と一緒に動きます。

- **時計は最も遅い終値まで**：A 股だけなら 15:00 まで、香港指数が入れば 16:00 まで。両方なら、A 股の線は 15:00 の終了後 horizontal に延び、「A 股終了 15:00」の縦線が立ち、香港は 16:00 まで進みます。

- **データは直近取引日の分足**：取引時間中は「いま」、終了後に一度取れば一日分。取引時間中は自動更新（30 秒ごと）を付けられます、リアルタイム損益と同じ調子で。

- 動画の長さ・タイトル・背景・書き出しは、他のページと同じく右のパネルで。
""",
    "ko": """## 계좌·시장 분할

위쪽은 보유 계좌의 당일 손익, 아래쪽은 A주와 홍콩 지수의 실시간 흐름: 반씩, 하나의 시계로, 애니메이션은 함께 1분씩 앞으로 갑니다.

- **위쪽 절반은 자신의 계좌를 그립니다.** 「실시간 손익」과 같은 장부를 읽습니다. 당일 손익 곡선과 0축, 그날의 숫자는 곡선 끝에 붙고, 가장 크게 기여한 종목과 가장 크게 발목 잡은 종목도 이름으로 표시됩니다(설정에서 이름을 \\*로 가릴 수 있습니다). 계좌 관리와 체결 가져오기도 이 페이지에 있습니다 — 같은 대화상자, 같은 장부이며, 한쪽에서 고치면 다른 쪽은 다시 가져오기로 최신이 됩니다.

- **두 절반은 서로 바꿀 수 있습니다**(지수를 위에, 또는 수익을 위에). 두 곡선은 같은 폭이라 나란히 비교되며, 점심시간은 시간축에서 뺄 수 있습니다 — 두 시장을 함께 표시할 때 빠지는 것은 둘 다 쉬는 12:00–13:00입니다. 네 가지 수수료는 「실시간 손익」과 같은 설정으로, 여기서 바꾸면 그쪽 재가져오기에도 반영됩니다.

- **아래쪽은 지수만**: A주 여섯(상해지수, CSI 300, 심천성분, CSI 500, 친업판지수, 상해50)과 홍콩 셋(항셍, 국기, 항생테크). 기본값은 상해지수와 항셍. 개별주·ETF·코인은 이 페이지에 없습니다 —— 대답하는 것은 "시장이 오늘 어떻게 움직였나".

- **지수는 모두 전일 종가 대비 %로 그립니다**: 항셍 이만삼천과 상해 삼천육백은 같은 축에 못 탑니다. 퍼센트로 바꿔야 한 장의 그림이 됩니다. 범례는 오른쪽, 화면과 함께 움직입니다.

- **시계는 가장 늦게 닫는 곳까지**: A주만 고르면 15:00까지, 홍콩 지수가 들어가면 16:00까지. 둘 다면 A주 선은 15:00 마감 후 수평으로 이어지고 「A주 마감 15:00」 세로선이 서며, 홍콩은 16:00까지 갑니다.

- **데이터는 최근 거래일의 분별 시세**: 장중에는 "지금", 마감 후 한 번 가져오면 하루 전체. 장중에는 자동 새로 고침(30초마다)을 켤 수 있습니다, 실시간 수익과 같은 박자로.

- 영상 길이·제목·배경·내보내기는 다른 페이지처럼 오른쪽 패널에서.
""",
    "de": """## Depot & Markt geteilt

Oben der Tag des Depots, unten die Festland- und Hongkong-Indizes: je die halbe Bildhöhe, eine Uhr für beide, die Animation geht Minute für Minute zusammen vorwärts.

- **Die obere Hälfte zeichnet Ihr eigenes Depot** — dasselbe, das die Seite «Intraday P&L» liest: die Tageskurve auf ihrer Nulllinie, die Zahl des Tages am Ende der Kurve, dazu bester und schlechtester Beitrag mit Namen (die Namen lassen sich hinter Sternchen verbergen). Depot verwalten und Trades importieren gibt es auch hier — dieselben Dialoge über dasselbe Depot, und eine Änderung auf einer Seite ist der nächste Abruf der anderen.

- **Die beiden Hälften lassen sich tauschen** (Indizes oben oder das Depot oben), beide Kurven laufen gleich breit und lassen sich so direkt vergleichen, und die Mittagspause kann von der Achse genommen werden — mit beiden Märkten im Bild wird die gemeinsame Pause 12:00–13:00 herausgenommen. Die vier Gebührensätze sind die Einstellung der Intraday-Seite: hier geändert, rechnet sie dort beim nächsten Abruf mit.

- **Die untere Hälfte zeichnet nur Indizes**: sechs vom Festland (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) und drei aus Hongkong (Hang Seng, HSCEI, Hang Seng Tech), vorgewählt sind SSE Composite und Hang Seng. Einzelwerte, ETFs und Münzen gehören nicht auf diese Seite — sie antwortet darauf, wie der Markt heute lief.

- **Jeder Index wird als Veränderung zum Vortagsschluss gezeichnet**: der Hang Seng bei dreiundzwanzigtausend und der SSE bei dreitausendsechshundert teilen keine Achse; Prozente schon. Die Legende steht rechts und wandert mit dem Bild mit.

- **Die Uhr läuft bis zum späteren Schluss**: nur Festland, bis 15:00; mit einem Hongkong-Index, bis 16:00. Bei beiden halten die Festlandlinien nach 15:00 flach unter einer Marke „Festland-Schluss 15:00", während Hongkong bis 16:00 weiterläuft.

- **Die Daten sind die Minutenkurse des letzten Handelstags**: während der Sitzung „jetzt", nach Schluss ein Abruf für den ganzen Tag. Bei offener Börse lässt sich die automatische Aktualisierung einschalten (alle 30 Sekunden), im Takt der Intraday-Seite.

- Länge, Titel, Hintergrund und Export wie auf jeder anderen Seite, im Panel rechts.
""",
    "fr": """## Portefeuille & marché partagés

En haut la journée du portefeuille, en bas les indices du continent et de Hong Kong : une moitié chacun, une seule horloge, l'animation avance minute par minute ensemble.

- **La moitié supérieure dessine votre propre portefeuille** — le même que la page « P&L intraday » lit : la courbe du jour sur sa ligne zéro, le chiffre du jour au bout de la courbe, et les meilleur et pire contributeurs nommés (leurs noms peuvent être masqués par des astérisques). Gérer le portefeuille et importer les transactions sont là aussi — les mêmes boîtes de dialogue sur le même carnet, et une modification d'un côté est le prochain rafraîchissement de l'autre.

- **Les deux moitiés peuvent s'échanger** (indices en haut, ou portefeuille en haut), les deux courbes ont la même largeur pour se comparer, et la pause du midi peut sortir de l'axe — avec les deux places à l'écran, c'est la pause commune de 12:00 à 13:00 qui est retirée. Les quatre taux de frais sont le réglage de la page intraday : changés ici, elle les applique aussi à son prochain rafraîchissement.

- **La moitié basse ne dessine que des indices** : six du continent (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) et trois de Hong Kong (Hang Seng, HSCEI, Hang Seng Tech), SSE Composite et Hang Seng cochés au départ. Les actions, ETF et monnaies ne sont pas sur cette page — elle répond à « comment le marché a-t-il tourné aujourd'hui ».

- **Chaque indice est tracé en variation depuis la clôture d'hier** : le Hang Seng à vingt-trois mille et le SSE à trois mille six cents ne partagent pas d'axe ; les pourcentages, oui. La légende est à droite et suit l'image.

- **L'horloge court jusqu'à la dernière clôture** : continent seul, jusqu'à 15:00 ; un indice hongkongais coché, jusqu'à 16:00. Avec les deux, les lignes du continent restent plates après la clôture de 15:00 sous un trait « clôture continentale 15:00 », et Hong Kong continue jusqu'à 16:00.

- **Les données sont les minutes du dernier jour de bourse** : pendant la séance c'est « maintenant » ; un fetch après la clôture donne la journée entière. L'actualisation automatique (toutes les 30 secondes) peut être activée, au même rythme que la page intraday.

- Durée, titre, fond et export se règlent dans le panneau de droite, comme partout.
""",
    "es": """## Cartera y mercado, divididos

Arriba el día de la cartera, abajo los índices del continente y de Hong Kong: media pantalla cada uno, un solo reloj, la animación avanza minuto a minuto junta.

- **La mitad superior dibuja tu propia cartera** — la misma que lee la página «P&L intradía»: la curva del día sobre su línea cero, la cifra del día al final de la curva, y el mejor y el peor aporte nombrados (los nombres pueden ocultarse con asteriscos). Gestionar cartera e importar operaciones también están aquí — los mismos diálogos sobre el mismo libro, y un cambio en una página es la siguiente lectura de la otra.

- **Las dos mitades pueden intercambiarse** (índices arriba, o la cartera arriba), las dos curvas corren con la misma anchura para compararlas, y la pausa del mediodía puede salir del eje — con ambas plazas en pantalla, la que se quita es la común de 12:00 a 13:00. Las cuatro comisiones son el ajuste de la página intradía: cambiadas aquí, aquélla también las aplica en su próxima lectura.

- **La mitad inferior dibuja solo índices**: seis del continente (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) y tres de Hong Kong (Hang Seng, HSCEI, Hang Seng Tech); SSE Composite y Hang Seng marcados de inicio. Acciones, ETF y monedas no están en esta página — responde a cómo fue el mercado hoy.

- **Cada índice se traza como variación desde el cierre de ayer**: el Hang Seng a veintitrés mil y el SSE a tres mil seiscientos no comparten eje; los porcentajes sí. La leyenda está a la derecha y se mueve con la imagen.

- **El reloj corre hasta el cierre más tardío**: solo continente, hasta las 15:00; con un índice de Hong Kong, hasta las 16:00. Con ambos, las líneas del continente quedan planas tras el cierre de 15:00 bajo una regla «cierre continental 15:00», y Hong Kong sigue hasta las 16:00.

- **Los datos son los minutos del último día de bolsa**: durante la sesión es «ahora»; una lectura tras el cierre da el día completo. Con la sesión abierta puede activarse la actualización automática (cada 30 segundos), al mismo compás que la página intradía.

- Duración, título, fondo y exportación se ajustan en el panel de la derecha, como en todas las páginas.
""",
    "it": """## Portafoglio e mercato divisi

Sopra la giornata del portafoglio, sotto gli indici del continente e di Hong Kong: metà schermo ciascuno, un solo orologio, l'animazione avanza minuto per minuto insieme.

- **La metà superiore disegna il tuo portafoglio** — lo stesso che legge la pagina «P&L intraday»: la curva del giorno sulla sua linea dello zero, la cifra del giorno in fondo alla curva, e il migliore e il peggiore contributo con nome (i nomi possono essere nascosti con asterischi). Gestisci portafoglio e importa operazioni sono qui pure — le stesse finestre sullo stesso registro, e una modifica su una pagina è la prossima lettura dell'altra.

- **Le due metà si possono scambiare** (indici sopra, o portafoglio sopra), le due curve corrono alla stessa larghezza per confrontarle, e la pausa di mezzogiorno può uscire dall'asse — con entrambe le piazze nel fotogramma, quella tolta è la comune dalle 12:00 alle 13:00. Le quattro commissioni sono l'impostazione della pagina intraday: cambiate qui, vale anche lì alla prossima lettura.

- **La metà inferiore disegna solo indici**: sei del continente (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) e tre di Hong Kong (Hang Seng, HSCEI, Hang Seng Tech); SSE Composite e Hang Seng spuntati all'inizio. Azioni, ETF e monete non sono su questa pagina — risponde a come è andato il mercato oggi.

- **Ogni indice è tracciato come variazione dalla chiusura di ieri**: l'Hang Seng a ventitremila e l'SSE a tremilaseicento non condividono un asse; le percentuali sì. La legenda è a destra e si muove con l'immagine.

- **L'orologio corre fino all'ultima chiusura**: solo continente, fino alle 15:00; con un indice di Hong Kong, fino alle 16:00. Con entrambi, le linee del continente restano piatte dopo la chiusura delle 15:00 sotto un tratto «chiusura continentale 15:00», mentre Hong Kong prosegue fino alle 16:00.

- **I dati sono i minuti dell'ultima giornata di borsa**: durante la seduta è «adesso»; un prelievo dopo la chiusura dà la giornata intera. Con la seduta aperta si può attivare l'aggiornamento automatico (ogni 30 secondi), allo stesso passo della pagina intraday.

- Durata, titolo, sfondo ed esportazione si regolano nel pannello a destra, come su ogni pagina.
""",
    "pt-BR": """## Carteira e mercado divididos

Em cima o dia da carteira, em baixo os índices do continente e de Hong Kong: meia tela para cada, um só relógio, a animação avança minuto a minuto junta.

- **A metade superior desenha a sua própria carteira** — a mesma que a página «P&L intradiário» lê: a curva do dia sobre a linha zero, o número do dia no fim da curva, e o melhor e o pior contribuinte nomeados (os nomes podem ser ocultados com asteriscos). Gerir carteira e importar negócios também estão aqui — os mesmos diálogos sobre o mesmo livro, e uma mudança numa página é a próxima leitura da outra.

- **As duas metades podem trocar de lugar** (índices em cima, ou a carteira em cima), as duas curvas correm com a mesma largura para compará-las, e a pausa do meio-dia pode sair do eixo — com as duas praças no quadro, a que sai é a comum das 12:00 às 13:00. As quatro taxas são o ajuste da página intradiária: mudas aqui, ela também as aplica na próxima leitura.

- **A metade de baixo desenha só índices**: seis do continente (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) e três de Hong Kong (Hang Seng, HSCEI, Hang Seng Tech); SSE Composite e Hang Seng marcados de início. Ações, ETFs e moedas não estão nesta página — ela responde como o mercado foi hoje.

- **Cada índice é traçado como variação desde o fechamento de ontem**: o Hang Seng a vinte e três mil e o SSE a três mil e seiscentos não dividem eixo; porcentagens, sim. A legenda fica à direita e acompanha a imagem.

- **O relógio corre até o fechamento mais tarde**: só continente, até 15:00; com um índice de Hong Kong, até 16:00. Com os dois, as linhas do continente ficam planas após o fechamento de 15:00 sob um traço «fechamento do continente 15:00», e Hong Kong segue até 16:00.

- **Os dados são os minutos do último dia de pregão**: durante a sessão é «agora»; uma leitura após o fechamento dá o dia inteiro. Com o pregão aberto, a atualização automática (a cada 30 segundos) pode ser ligada, no mesmo compasso da página intradiária.

- Duração, título, fundo e exportação se ajustam no painel à direita, como em toda página.
""",
    "ru": """## Портфель и рынок, пополам

Сверху день портфеля, снизу индексы материка и Гонконга: по половине кадра, на одних часах, анимация идёт вперёд минута за минутой вместе.

- **Верхняя половина рисует ваш собственный портфель** — тот же, что читает страница «Интрадей П&У»: кривая дня на нулевой линии, цифра дня на конце кривой, лучший и худший вклад с именами (имена можно скрыть звёздочками). Управление портфелем и импорт сделок есть и здесь — те же диалоги над тем же файлом, и правка на одной странице — это следующий запрос другой.

- **Половины можно поменять местами** (индексы сверху или портфель сверху), обе кривые идут одной шириной и читаются вровень, а обед можно снять с оси — при обеих площадках на кадре снимается общая пауза 12:00–13:00. Четыре тарифа — та же настройка страницы интрадей: меняете здесь, она применит их при следующем запросе.

- **Нижняя половина рисует только индексы**: шесть с материка (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) и три гонконгских (Hang Seng, HSCEI, Hang Seng Tech); по умолчанию отмечены SSE Composite и Hang Seng. Акций, ETF и монет здесь нет — страница отвечает на вопрос, как сегодня шёл рынок.

- **Каждый индекс рисуется изменением от вчерашнего закрытия**: Hang Seng на двадцати трёх тысячах и SSE на трёх тысячах шестистах не делят одну ось; проценты — делят. Легенда справа и движется вместе с кадром.

- **Часы идут до позднего закрытия**: только материк — до 15:00; выбран гонконгский индекс — до 16:00. С обоими линии материка после закрытия 15:00 держатся плоско под чертой «закрытие материка 15:00», а Гонконг идёт до 16:00.

- **Данные — поминутные котировки последнего торгового дня**: во время сессии это «сейчас»; одно обновление после закрытия даёт весь день. При открытой сессии можно включить автообновление (каждые 30 секунд), в том же ритме, что и страница интрадей.

- Длительность, заголовок, фон и экспорт настраиваются в панели справа, как на всякой странице.
""",
    "pl": """## Portfel i rynek, na pół

U góry dzień portfela, u dołu indeksy Chin kontynentalnych i Hongkongu: po połowie kadru, na jednym zegarze, animacja idzie do przodu minuta po minucie razem.

- **Górna połowa rysuje twój własny portfel** — ten sam, który czyta strona «Intraday P&L»: krzywa dnia na linii zera, liczba dnia na końcu krzywej, największy wkład i największa brzda z nazwami (nazwy można ukryć gwiazdkami). Zarządzanie portfelem i import zleceń są też tutaj — te same okna nad tym samym rejestrem, i zmiana na jednej stronie to następne pobranie drugiej.

- **Połówki można zamienić** (indeksy u góry albo portfel u góry), obie krzywe biegną tą samą szerokością i czytają się w rzędzie, a przerwa obiadowa może zejść z osi — przy obu rynkach na kadrze znika wspólna przerwa 12:00–13:00. Cztery stawki to ustawienie strony intraday: zmienione tutaj, ona też je zastosuje przy następnym pobraniu.

- **Dolna połowa rysuje tylko indeksy**: sześć z kontynentu (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) i trzy z Hongkongu (Hang Seng, HSCEI, Hang Seng Tech); domyślnie zaznaczone są SSE Composite i Hang Seng. Akcji, ETF i monet tu nie ma — strona odpowiada, jak dziś szedł rynek.

- **Każdy indeks rysowany jest jako zmiana od wczorajszego zamknięcia**: Hang Seng na dwudziestu trzech tysiącach i SSE na trzech tysiącach sześciuset nie dzielą osi; procenty — dzielą. Legenda po prawej i wędruje z obrazem.

- **Zegar biegnie do późniejszego zamknięcia**: sam kontynent — do 15:00; zaznaczony indeks hongkoński — do 16:00. Z oboma linie kontynentu po zamknięciu 15:00 trzymają się płasko pod kreską «zamknięcie kontynentu 15:00», a Hongkong idzie do 16:00.

- **Dane to minuty ostatniego dnia sesji**: w czasie sesji to «teraz»; jedno pobranie po zamknięciu daje cały dzień. Przy otwartej sesji można włączyć automatyczne odświeżanie (co 30 sekund), w tym samym rytmie co strona intraday.

- Długość, tytuł, tło i eksport ustawia się w panelu po prawej, jak na każdej stronie.
""",
    "tr": """## Portföy ve Piyasa bölünmüş

Üstte portföyün günü, altta Çin anakarası ve Hong Kong endeksleri: yarısı yarıya, tek saat, animasyon birlikte dakika dakika ilerler.

- **Üst yarı kendi portföyünüzü çizer** — «Gün içi kâr» sayfasının okuduğu aynı defter: günün kâr eğrisi sıfır çizgisi üzerinde, günün rakamı eğrinin ucunda, en iyi ve en kötü katkı isimleriyle (isimler istenirse \\* ile gizlenir). Portföyü yönet ve işlemleri içe aktar da burada — aynı defter üzerinde aynı pencereler; bir sayfada yapılan değişiklik diğerinin sonraki çekimidir.

- **İki yarı yer değiştirebilir** (endeksler üstte ya da portföy üstte), iki eğri aynı genişlikte akar ve karşılaştırılır; öğle arası eksenden çıkarılabilir — her iki piyasa da kadrajdayken çıkarılan, ikisinin de kapalı olduğu 12:00–13:00'dir. Dört komisyon oranı gün içi sayfasının kendi ayarıdır: burada değiştirilirse o da sonraki çekiminde uygular.

- **Alt yarı yalnızca endeks çizer**: anakaradan altısı (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) ve Hong Kong'dan üçü (Hang Seng, HSCEI, Hang Seng Tech); başlangıçta SSE Composite ve Hang Seng işlidir. Hisse, ETF ve coin bu sayfada değil — sayfa bugün piyasasının nasıl gittiğini yanıtlar.

- **Her endeks dünkü kapanışa göre değişim olarak çizilir**: yirmi üç bindeki Hang Seng ile üç bin altı yüzdaki SSE aynı ekseni paylaşamaz; yüzdeler paylaşır. Gösterge sağda ve görüntüyle birlikte yürür.

- **Saat en geç kapanışa kadar koşar**: yalnız anakara — 15:00'e; bir Hong Kong endeksi işliyse — 16:00'ya. İkisi de seçiliyken anakara çizgileri 15:00 kapanışından sonra «anakara kapanışı 15:00» çizgisi altında düz kalır, Hong Kong 16:00'ya kadar sürer.

- **Veriler son işlem gününün dakikalarıdır**: seans sırasında «şimdi»; kapanıştan sonra bir çekim günün tamamını verir. Piyasa açıkken otomatik yenileme (30 saniyede bir) açılabilir, gün içi sayfasıyla aynı tempoda.

- Süre, başlık, arka plan ve dışa aktarma her sayfada olduğu gibi sağdaki panelde ayarlanır.
""",
    "cs": """## Portfolio a trh napůl

Nahoře den portfolia, dole indexy pevninské Číny a Hongkongu: po polovině rámu, na jedny hodiny, animace jde dopředu minutu za minutou spolu.

- **Horní polovina kreslí tvůj vlastní portfol** — ten samý, který čte stránka «Intraday P&L»: křivka dne na nulové linii, číslo dne na konci křivky, největší přínos a největší brzda se jmény (jména lze skrýt hvězdičkami). Správa portfolia a import obchodů jsou i tady — stejná okna nad stejným registrem, a úprava na jedné straně je příští stažení druhé.

- **Poloviny lze prohodit** (indexy nahoře, nebo portfol nahoře), obě křivky běží stejně široko a čtou se vedle sebe, a polední pauza může z osi zmizet — s oběma trhy v záběru mizí společná pauza 12:00–13:00. Čtyři sazby jsou nastavení stránky intraday: změněné tady, použije je i ona při příštím stažení.

- **Dolní polovina kreslí jen indexy**: šest z pevniny (SSE Composite, CSI 300, SZSE Component, CSI 500, ChiNext, SSE 50) a tři z Hongkongu (Hang Seng, HSCEI, Hang Seng Tech); předvoleny jsou SSE Composite a Hang Seng. Akcie, ETF a mince na této stránce nejsou — odpovídá na to, jak dnes šel trh.

- **Každý index se kreslí jako změna od včerejšího uzavření**: Hang Seng ve třiadvaceti tisících a SSE v šestiapůltisících jednu osu nesdílejí; procenta ano. Legenda vpravo a jde s obrazem.

- **Hodiny běží do pozdějšího uzavření**: jen pevnina — do 15:00; zaškrtnut hongkongský index — do 16:00. S oběma drží se linie pevniny po uzavření 15:00 v rovině pod čarou «uzavření pevniny 15:00», a Hongkong jde do 16:00.

- **Data jsou minuty posledního obchodního dne**: během seance je to «teď»; jedno stažení po uzavření dá celý den. Za otevřené burzy lze zapnout automatickou aktualizaci (každých 30 sekund), ve stejném rytmu jako stránka intraday.

- Délku, titul, pozadí a export nastavíš v panelu vpravo, jako na každé stránce.
""",
}

LANGS = ["cs", "de", "en-US", "es", "fr", "it", "ja", "ko", "pl", "pt-BR", "ru", "tr", "zh-Hans", "zh-Hant"]


def resw_value(lang: str, key: str) -> str:
    text = (SRC / "Strings" / lang / "Resources.resw").read_text(encoding="utf-8-sig")

    start = text.index(f'<data name="{key}">')
    value_start = text.index("<value>", start) + len("<value>")
    value_end = text.index("</value>", value_start)

    return text[value_start:value_end]


changed = 0

for lang in LANGS:
    path = SRC / "Assets" / "Help" / f"help-{lang}.md"
    text = path.read_text(encoding="utf-8")

    heading = SECTIONS[lang].splitlines()[0]

    if heading in text:
        # 小节已在：整节替换。这一节的唯一事实源就是本脚本里的 SECTIONS，
        # 文案改了哪句、加删了哪条，这里说了算 —— 逐句补丁反而会漂。
        lines = text.splitlines(keepends=True)
        start = next(i for i, l in enumerate(lines) if l.rstrip() == heading)
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        text = "".join(lines[:start]) + SECTIONS[lang].rstrip() + "\n\n" + "".join(lines[end:])
        path.write_text(text, encoding="utf-8", newline="")
        changed += 1
        print(f"{lang}: section replaced")
        continue

    # The section goes in where the crypto pages begin — the manual follows the menu's
    # order, and the menu puts the board between the intraday page and the crypto one.
    # Both neighbours' headings come from the language's own resource file, so the anchor
    # cannot drift from what the reader actually sees.
    current = resw_value(lang, "PortfolioPnlPageTitle.Text")
    following = resw_value(lang, "CryptoCandlePageTitle.Text")

    following_heading = f"## {following}"

    if following_heading not in text:
        print(f"{lang}: anchor heading not found ({following_heading!r})")
        continue

    text = text.replace(following_heading, SECTIONS[lang].rstrip() + "\n\n" + following_heading, 1)
    path.write_text(text, encoding="utf-8", newline="")
    changed += 1
    print(f"{lang}: inserted after {current!r}")

print(f"changed {changed} files")
