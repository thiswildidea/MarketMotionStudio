"""Rewrites the three per-language paragraphs of the Store listing.

`docs/store-listing.md` is the copy that goes into Partner Center, in fourteen
languages, and each language repeats the same three things: a description that
enumerates the pages, a "what's new in this version" line, and a bullet list of
product features. All three name a count or a list, so a new page changes
fourteen files' worth of text by hand — which is how it used to drift.

One script, one place to edit. Every replacement is an exact match, so a run
that finds nothing to do says so rather than guessing, and running it twice
changes nothing the second time.
"""

import re
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "docs" / "store-listing.md"

# Each entry: what the page-count line says before and after, the bullet to add
# to the page list, the new "what's new" paragraph, and the feature bullet's
# before and after.
#
# The count and the feature bullet are matched as whole lines, so a language
# whose wording differs from the one here fails loudly instead of silently
# keeping the old number.
LANGS = {
    "zh-Hans": dict(
        count_from="七大图表页：",
        count_to="八大图表页：",
        bullet="• K线——一只标的的日/周/月 K 线，四种画法，带均线与成交量副图",
        whats_new=(
            "本版新增第八个图表页「K线」：一只标的的价格画成 K 线，日线/周线/月线任选，"
            "四种画法（蜡烛、美国线、收盘线、面积），带 MA5/10/20 均线与成交量副图，"
            "区间涨跌幅和最高/最低点会标在画面上；动画可以逐根生长，也可以在固定窗口里向前滚动。"
            "指数、个股、ETF 都能画，三个市场都支持。 "
            "K线、定投计划、持仓收益三个页面现在都支持自定义区间——选「自定义」后填起始和结束日期，"
            "取回来的就是这个区间。 "
            "动画背景选「颜色」时多了一条「不透明度」：100% 就是所选的两个颜色本身，"
            "往低调会从底下透出这一页原本的深色渐变，方便用亮色时数字仍然读得清；"
            "设置页里那条渐变预览会跟着一起变。 "
            "另外，设置页的顶部边距最小值从 230 放宽到 40（默认仍是 230），需要更满的画面时可以往上收。 "
            "还修好了 K 线表头四价行与日期行的重叠，以及美股代码大小写导致的取不到数据。"
        ),
        feat_from="- 七种图表：成交额、量价、板块竞速、收益矩阵、涨跌日历、定投、持仓",
        feat_to="- 八种图表：成交额、量价、板块竞速、收益矩阵、涨跌日历、定投、持仓、K线",
    ),
    "zh-Hant": dict(
        count_from="七大圖表頁：",
        count_to="八大圖表頁：",
        bullet="• K線——一檔標的的日線/週線/月線，四種畫法，帶均線與成交量副圖",
        whats_new=(
            "本版新增第八個圖表頁「K線」：一檔標的的價格畫成 K 線，日線/週線/月線任選，"
            "四種畫法（蠟燭、美國線、收盤線、面積），帶 MA5/10/20 均線與成交量副圖，"
            "區間漲跌幅和最高/最低點會標在畫面上；動畫可以逐根生長，也可以在固定窗口裡向前滾動。"
            "指數、個股、ETF 都能畫，三個市場都支援。 "
            "K線、定期定額計畫、持倉收益三個頁面現在都支援自訂區間——選「自訂」後填起始和結束日期，"
            "取回來的就是這個區間。 "
            "動畫背景選「顏色」時多了一條「不透明度」：100% 就是所選的兩個顏色本身，"
            "往低調會從底下透出這一頁原本的深色漸層，方便用亮色時數字仍然讀得清；"
            "設定頁裡那條漸層預覽會跟著一起變。 "
            "另外，設定頁的頂部邊距最小值從 230 放寬到 40（預設仍是 230），需要更滿的畫面時可以往上收。 "
            "還修好了 K 線表頭四價行與日期行的重疊，以及美股代碼大小寫導致的取不到資料。"
        ),
        feat_from="- 七種圖表：成交額、量價、板塊競速、收益矩陣、漲跌日曆、定期定額、持倉",
        feat_to="- 八種圖表：成交額、量價、板塊競速、收益矩陣、漲跌日曆、定期定額、持倉、K線",
    ),
    "en-US": dict(
        count_from="Seven chart pages:",
        count_to="Eight chart pages:",
        bullet="• Candles — one instrument's daily/weekly/monthly candles, four ways, with moving averages and a volume panel",
        whats_new=(
            "New in this version: an eighth chart page, Candles — one instrument's prices as candles, "
            "daily, weekly or monthly, drawn four ways (candles, OHLC bars, a closing line, a closing area), "
            "with MA5/10/20 and a volume panel, and the range's return and its high and low marked on the frame. "
            "The animation either grows candle by candle across the whole range or walks forward inside a window of it. "
            "Indices, stocks and ETFs all draw, on all three markets. "
            "Candles, the DCA plan and the position replay now take a custom span: pick Custom, fill in a start "
            "and an end date, and that is the range you get back. "
            "A colour backdrop gained an opacity slider — 100% is the two colours you picked, and turning it down "
            "lets the page's own dark gradient show through, which keeps figures readable on a light colour; the "
            "gradient preview in Settings moves with it. "
            "The top margin's minimum has been relaxed from 230 to 40, the default still being 230, for frames "
            "that want less air. "
            "Also fixed: the candle header's quote row overlapped the date row, and a US code in the wrong case "
            "fetched no data at all."
        ),
        feat_from="- Seven charts: turnover, volume, sector race, return matrix, calendar, DCA, position replay",
        feat_to="- Eight charts: turnover, volume, sector race, return matrix, calendar, DCA, position replay, candles",
    ),
    "ja": dict(
        count_from="7 つのチャートページ：",
        count_to="8 つのチャートページ：",
        bullet="• ローソク足 — 1 銘柄の日足・週足・月足を4種類の描き方で。移動平均線と出来高パネル付き",
        whats_new=(
            "このバージョンの新機能：8 つ目のチャートページ「ローソク足」——1 つの銘柄の価格を"
            "日足・週足・月足から選んで描き、4 種類の描き方（ローソク足、OHLC、終値ライン、終値エリア）に対応。"
            "MA5/10/20 と出来高パネルを備え、期間の騰落率と高値・安値を画面に表示します。"
            "アニメーションは1本ずつ伸びる方式と、固定ウィンドウで前進する方式の2種類。"
            "指数・個別株・ETF に対応し、3 市場すべてで使えます。 "
            "ローソク足・積立投資・保有収益の3ページで期間のカスタム指定に対応しました。"
            "「カスタム」を選んで開始日と終了日を入力すると、その期間だけを取得します。 "
            "アニメーション背景で「色」を選んだときに「不透明度」スライダーが追加されました。"
            "100% なら選んだ2色そのまま、下げるとページ本来の暗いグラデーションが透けて見え、"
            "明るい色でも数値が読みやすくなります。設定画面のグラデーションプレビューも連動します。 "
            "また、上部余白の最小値を 230 から 40 に緩和しました（既定値は 230 のまま）。 "
            "あわせて、ローソク足のヘッダーで四本値と日付が重なる問題と、"
            "米国株コードの大文字小文字の違いでデータが取得できない問題も修正しました。"
        ),
        feat_from="- 7 種類のチャート：売買代金、量価、セクターレース、リターンマトリクス、カレンダー、積立、保有収益",
        feat_to="- 8 種類のチャート：売買代金、量価、セクターレース、リターンマトリクス、カレンダー、積立、保有収益、ローソク足",
    ),
    "ko": dict(
        count_from="7가지 차트 페이지:",
        count_to="8가지 차트 페이지:",
        bullet="• 캔들 — 하나의 종목을 일/주/월 단위로, 네 가지 방식으로. 이동평균선과 거래량 패널 포함",
        whats_new=(
            "이 버전의 새 기능: 여덟 번째 차트 페이지 「캔들」——하나의 종목 가격을 일/주/월 단위로 캔들 차트로 그리며, "
            "네 가지 방식(캔들, OHLC, 종가선, 종가 영역)을 지원합니다. MA5/10/20과 거래량 패널이 함께 표시되고, "
            "구간 수익률과 고점·저점이 화면에 표시됩니다. 애니메이션은 캔들 하나씩 자라나는 방식과 "
            "고정 창 안에서 앞으로 이동하는 방식 중에서 고를 수 있습니다. 지수·개별 주식·ETF를 모두 그릴 수 있고 "
            "세 시장 모두 지원합니다. "
            "캔들·적립 투자·보유 수익 세 페이지에서 이제 구간을 직접 지정할 수 있습니다. "
            "「사용자 지정」을 고르고 시작일과 종료일을 입력하면 그 구간만 가져옵니다. "
            "애니메이션 배경에서 「색」을 고르면 「불투명도」 슬라이더가 생깁니다. 100%는 고른 두 색 그대로이고, "
            "낮추면 페이지 본래의 어두운 그라데이션이 비쳐 보여 밝은 색에서도 숫자가 읽힙니다. "
            "설정의 그라데이션 미리보기도 함께 변합니다. "
            "또한 위쪽 여백의 최솟값을 230에서 40으로 완화했습니다(기본값은 여전히 230). "
            "이와 함께 캔들 헤더에서 시가·고가·저가·종가 행과 날짜 행이 겹치던 문제와, "
            "미국 종목 코드의 대소문자 차이로 데이터를 가져오지 못하던 문제도 고쳤습니다."
        ),
        feat_from="- 7가지 차트: 거래대금, 거래량, 업종 경주, 수익 매트릭스, 달력, 적립 투자, 보유 수익",
        feat_to="- 8가지 차트: 거래대금, 거래량, 업종 경주, 수익 매트릭스, 달력, 적립 투자, 보유 수익, 캔들",
    ),
    "de": dict(
        count_from="Sieben Diagrammseiten:",
        count_to="Acht Diagrammseiten:",
        bullet="• Kerzen — ein Instrument täglich, wöchentlich oder monatlich, in vier Darstellungen, mit Durchschnitten und Volumenpanel",
        whats_new=(
            "Neu in dieser Version: eine achte Diagrammseite, Kerzen — die Kurse eines Instruments als Kerzen, "
            "täglich, wöchentlich oder monatlich, in vier Darstellungen (Kerzen, OHLC-Balken, Schlusskurslinie, "
            "Schlusskursfläche), mit MA5/10/20 und einem Volumenpanel; die Rendite des Zeitraums sowie Hoch und "
            "Tief werden im Bild markiert. Die Animation wächst entweder Kerze für Kerze über den ganzen Zeitraum "
            "oder läuft in einem festen Fenster vorwärts. Indizes, Aktien und ETFs zeichnen, in allen drei Märkten. "
            "Kerzen, Sparplan und Depotrendite nehmen jetzt einen eigenen Zeitraum: „Benutzerdefiniert“ wählen, "
            "Start- und Enddatum eintragen, und genau dieser Zeitraum kommt zurück. "
            "Ein Farbhintergrund hat einen Deckkraft-Regler bekommen — 100 % sind die beiden gewählten Farben, "
            "weiter herunter scheint der dunkle Verlauf der Seite durch, damit Zahlen auf einer hellen Farbe lesbar "
            "bleiben; die Verlaufsvorschau in den Einstellungen zieht mit. "
            "Die Untergrenze des oberen Rands wurde von 230 auf 40 gelockert; der Standard bleibt 230. "
            "Außerdem behoben: die Kurszeile in der Kerzen-Kopfzeile überlappte die Datumszeile, und US-Codes mit "
            "falscher Groß-/Kleinschreibung lieferten gar keine Daten."
        ),
        feat_from="- Sieben Diagramme: Umsatz, Volumen, Sektor-Rennen, Renditematrix, Kalender, Sparplan, Depotrendite",
        feat_to="- Acht Diagramme: Umsatz, Volumen, Sektor-Rennen, Renditematrix, Kalender, Sparplan, Depotrendite, Kerzen",
    ),
    "fr": dict(
        count_from="Sept pages de graphiques :",
        count_to="Huit pages de graphiques :",
        bullet="• Chandeliers — un instrument en quotidien, hebdomadaire ou mensuel, quatre tracés, avec moyennes mobiles et panneau de volume",
        whats_new=(
            "Nouveautés de cette version : une huitième page de graphiques, Chandeliers — les cours d'un instrument "
            "en chandeliers, en quotidien, hebdomadaire ou mensuel, avec quatre tracés (chandeliers, barres OHLC, "
            "ligne de clôture, aire de clôture), les moyennes MA5/10/20 et un panneau de volume ; la performance de "
            "la période ainsi que le plus haut et le plus bas sont annotés à l'image. L'animation fait pousser les "
            "chandeliers un par un sur toute la période, ou avance dans une fenêtre fixe. Indices, actions et ETF se "
            "tracent, sur les trois marchés. "
            "Chandeliers, plan DCA et rendement de position acceptent désormais une période personnalisée : "
            "choisissez Personnalisé, saisissez une date de début et une date de fin, et c'est cette période qui revient. "
            "Un fond en couleur a gagné un curseur d'opacité : 100 % donne les deux couleurs choisies, et le baisser "
            "laisse transparaître le dégradé sombre propre à la page, pour que les chiffres restent lisibles sur une "
            "couleur claire ; l'aperçu du dégradé dans les paramètres suit. "
            "Le minimum de la marge haute est assoupli de 230 à 40, la valeur par défaut restant 230. "
            "Également corrigé : la ligne des cours de l'en-tête des chandeliers chevauchait la ligne de date, et les "
            "codes américains mal capitalisés ne ramenaient aucune donnée."
        ),
        feat_from="- Sept graphiques : volume d'échanges, volume et rotation, course de secteurs, matrice des rendements, calendrier, plan DCA, rendement de position",
        feat_to="- Huit graphiques : volume d'échanges, volume et rotation, course de secteurs, matrice des rendements, calendrier, plan DCA, rendement de position, chandeliers",
    ),
    "it": dict(
        count_from="Sette pagine di grafici:",
        count_to="Otto pagine di grafici:",
        bullet="• Candele — uno strumento in giornaliero, settimanale o mensile, quattro tracciati, con medie mobili e pannello dei volumi",
        whats_new=(
            "Novità di questa versione: un'ottava pagina di grafici, Candele — i prezzi di uno strumento come candele, "
            "giornaliere, settimanali o mensili, con quattro tracciamenti (candele, barre OHLC, linea di chiusura, "
            "area di chiusura), le medie MA5/10/20 e un pannello dei volumi; il rendimento del periodo con massimo e "
            "minimo è annotato nell'immagine. L'animazione fa crescere le candele una a una su tutto il periodo oppure "
            "avanza dentro una finestra fissa. Indici, azioni ed ETF si disegnano, su tutti e tre i mercati. "
            "Candele, piano di accumulo e rendimento della posizione accettano ora un intervallo personalizzato: "
            "scegli Personalizzato, indica una data di inizio e una di fine, e quello è l'intervallo che arriva. "
            "Uno sfondo a colori ha guadagnato una barra di opacità: 100 % sono i due colori scelti, abbassandola "
            "traspare il gradiente scuro proprio della pagina, così le cifre restano leggibili su un colore chiaro; "
            "l'anteprima del gradiente nelle impostazioni segue. "
            "Il minimo del margine superiore è stato allentato da 230 a 40, con 230 ancora come predefinito. "
            "Inoltre corretti: la riga dei prezzi nell'intestazione delle candele che sovrapponeva la riga della data, "
            "e i codici USA con maiuscole/minuscole errate che non restituivano alcun dato."
        ),
        feat_from="- Sette grafici: volume degli scambi, volume e rotazione, corsa dei settori, matrice dei rendimenti, calendario, piano DCA, rendimento della posizione",
        feat_to="- Otto grafici: volume degli scambi, volume e rotazione, corsa dei settori, matrice dei rendimenti, calendario, piano DCA, rendimento della posizione, candele",
    ),
    "es": dict(
        count_from="Siete páginas de gráficos:",
        count_to="Ocho páginas de gráficos:",
        bullet="• Velas — un instrumento en diario, semanal o mensual, con cuatro trazados, medias móviles y panel de volumen",
        whats_new=(
            "Novedades de esta versión: una octava página de gráficos, Velas — los precios de un instrumento como velas, "
            "diarias, semanales o mensuales, con cuatro trazados (velas, barras OHLC, línea de cierre, área de cierre), "
            "las medias MA5/10/20 y un panel de volumen; la rentabilidad del periodo junto con el máximo y el mínimo se "
            "anotan en la imagen. La animación hace crecer las velas una a una sobre todo el periodo o avanza dentro de "
            "una ventana fija. Índices, acciones y ETF se dibujan, en los tres mercados. "
            "Velas, el plan DCA y la rentabilidad de la cartera aceptan ahora un periodo personalizado: elige "
            "Personalizado, indica una fecha de inicio y una de fin, y ese es el periodo que llega. "
            "Un fondo de color ha ganado un control de opacidad: el 100 % son los dos colores elegidos y al bajarlo "
            "transparenta el degradado oscuro propio de la página, para que las cifras sigan legibles sobre un color "
            "claro; la vista previa del degradado en los ajustes acompaña. "
            "El mínimo del margen superior se ha relajado de 230 a 40, con 230 todavía como valor por defecto. "
            "También se ha corregido: la fila de precios del encabezado de las velas se solapaba con la fila de la fecha, "
            "y los códigos estadounidenses con mayúsculas/minúsculas incorrectas no devolvían ningún dato."
        ),
        feat_from="- Siete gráficos: volumen negociado, volumen y rotación, carrera de sectores, matriz de rentabilidad, calendario, plan DCA, rentabilidad de cartera",
        feat_to="- Ocho gráficos: volumen negociado, volumen y rotación, carrera de sectores, matriz de rentabilidad, calendario, plan DCA, rentabilidad de cartera, velas",
    ),
    "pt-BR": dict(
        count_from="Sete páginas de gráficos:",
        count_to="Oito páginas de gráficos:",
        bullet="• Candlestick — um instrumento em diário, semanal ou mensal, com quatro traçados, médias móveis e painel de volume",
        whats_new=(
            "Novidades desta versão: uma oitava página de gráficos, Candlestick — os preços de um instrumento como candles, "
            "diários, semanais ou mensais, com quatro traçados (candles, barras OHLC, linha de fechamento, área de "
            "fechamento), as médias MA5/10/20 e um painel de volume; o retorno do período com a máxima e a mínima é "
            "anotado na imagem. A animação faz os candles crescerem um a um sobre todo o período ou avança dentro de uma "
            "janela fixa. Índices, ações e ETFs são desenhados, nos três mercados. "
            "Candlestick, o plano DCA e o retorno de posição agora aceitam um período personalizado: escolha "
            "Personalizado, informe a data inicial e a final, e é esse período que volta. "
            "Um fundo colorido ganhou um controle de opacidade: 100 % são as duas cores escolhidas e, ao reduzi-lo, o "
            "gradiente escuro próprio da página transparece, para que os números continuem legíveis sobre uma cor clara; "
            "a prévia do gradiente nas configurações acompanha. "
            "O mínimo da margem superior foi relaxado de 230 para 40, com 230 ainda como padrão. "
            "Também corrigidos: a linha de preços no cabeçalho dos candles se sobrepondo à linha da data, e os códigos "
            "dos EUA com caixa errada não retornando nenhum dado."
        ),
        feat_from="- Sete gráficos: volume financeiro, volume e giro, corrida de setores, matriz de retorno, calendário, plano DCA, retorno de posição",
        feat_to="- Oito gráficos: volume financeiro, volume e giro, corrida de setores, matriz de retorno, calendário, plano DCA, retorno de posição, candles",
    ),
    "pl": dict(
        count_from="Siedem stron wykresów:",
        count_to="Osiem stron wykresów:",
        bullet="• Świece — jeden instrument w ujęciu dziennym, tygodniowym lub miesięcznym, cztery sposoby, ze średnimi i panelem wolumenu",
        whats_new=(
            "Co nowego w tej wersji: ósma strona wykresów, Świece — ceny jednego instrumentu jako świece, dzienne, "
            "tygodniowe lub miesięczne, w czterech sposobach rysowania (świecie, słupki OHLC, linia zamknięcia, "
            "obszar zamknięcia), ze średnimi MA5/10/20 i panelem wolumenu; stopa zwrotu z okresu oraz maksimum i "
            "minimum są opisane na obrazie. Animacja albo dorasta świeca po świecy na całym okresie, albo przesuwa się "
            "w stałym oknie. Indeksy, akcje i ETF-y rysują się na wszystkich trzech rynkach. "
            "Świece, plan DCA i zwrot z pozycji przyjmują teraz własny okres: wybierz Niestandardowy, podaj datę "
            "początkową i końcową i właśnie ten okres wraca. "
            "Kolorowe tło zyskało suwak krycia: 100 % to wybrane dwa kolory, a obniżenie go przepuszcza ciemny gradient "
            "właściwy dla strony, dzięki czemu liczby pozostają czytelne na jasnym kolorze; podgląd gradientu w "
            "ustawieniach zmienia się razem z nim. "
            "Dolna granica górnego marginesu została złagodzona ze 230 do 40, a wartość domyślna to nadal 230. "
            "Naprawiono też: wiersz cen w nagłówku świec nachodził na wiersz daty, a amerykańskie kody z niewłaściwą "
            "wielkością liter nie zwracały żadnych danych."
        ),
        feat_from="- Siedem wykresów: obroty, wolumen, wyścig sektorów, macierz stóp zwrotu, kalendarz, plan DCA, zwrot z pozycji",
        feat_to="- Osiem wykresów: obroty, wolumen, wyścig sektorów, macierz stóp zwrotu, kalendarz, plan DCA, zwrot z pozycji, świece",
    ),
    "cs": dict(
        count_from="Sedm stránek s grafy:",
        count_to="Osm stránek s grafy:",
        bullet="• Svíčky — jeden nástroj denně, týdně nebo měsíčně, čtyři způsoby, s průměry a panelem objemu",
        whats_new=(
            "Co je nového v této verzi: osmá stránka s grafy, Svíčky — ceny jednoho nástroje jako svíčky, denní, "
            "týdenní nebo měsíční, ve čtyřech způsobech vykreslení (svíčky, OHLC sloupky, čára závěru, plocha závěru), "
            "s klouzavými průměry MA5/10/20 a panelem objemu; výnos období spolu s maximem a minimem je v obraze "
            "označen. Animace buď dorůstá svíčku po svíčce přes celé období, nebo postupuje v pevném okně. "
            "Indexy, akcie a ETF se kreslí na všech třech trzích. "
            "Svíčky, DCA plán a výnos pozice nyní přijímají vlastní období: vyberte Vlastní, zadejte datum začátku a "
            "konce a právě to období se vrátí. "
            "Barevné pozadí získalo posuvník krytí: 100 % jsou vybrané dvě barvy, snížením prosvítá tmavý gradient "
            "vlastní stránce, takže čísla zůstávají čitelná i na světlé barvě; náhled gradientu v nastavení se mění "
            "zároveň. "
            "Dolní mez horního okraje byla uvolněna z 230 na 40, výchozí hodnota je stále 230. "
            "Opraveno také: řádek cen v záhlaví svíček se překrýval s řádkem data a americké kódy s nesprávnou "
            "velikostí písmen nevracely žádná data."
        ),
        feat_from="- Sedm grafů: obrat, objem, závod sektorů, matice výnosů, kalendář, DCA plán, výnos pozice",
        feat_to="- Osm grafů: obrat, objem, závod sektorů, matice výnosů, kalendář, DCA plán, výnos pozice, svíčky",
    ),
    "ru": dict(
        count_from="Семь страниц с графиками:",
        count_to="Восемь страниц с графиками:",
        bullet="• Свечи — один инструмент в дневном, недельном или месячном виде, четыре способа, со средними и панелью объёма",
        whats_new=(
            "Что нового в этой версии: восьмая страница графиков, Свечи — цены одного инструмента свечами, дневными, "
            "недельными или месячными, в четырёх видах (свечи, бары OHLC, линия закрытия, область закрытия), "
            "со скользящими средними MA5/10/20 и панелью объёма; доходность периода вместе с максимумом и минимумом "
            "подписана на кадре. Анимация либо наращивает свечи одну за другой по всему периоду, либо идёт вперёд "
            "внутри фиксированного окна. Индексы, акции и ETF рисуются на всех трёх рынках. "
            "Свечи, план DCA и доходность позиции теперь принимают свой период: выберите «Свой», укажите дату начала "
            "и конца — и вернётся именно он. "
            "Цветовой фон получил ползунок непрозрачности: 100 % — это выбранные два цвета, а при уменьшении сквозь них "
            "проступает тёмный градиент самой страницы, чтобы цифры оставались читаемыми на светлом цвете; "
            "предварительный просмотр градиента в настройках меняется вместе с ним. "
            "Нижний предел верхнего поля ослаблен с 230 до 40, по умолчанию по-прежнему 230. "
            "Также исправлено: строка цен в заголовке свечей перекрывала строку даты, а американские коды "
            "с неверным регистром не возвращали данных вовсе."
        ),
        feat_from="- Семь графиков: оборот, объём, гонка секторов, матрица доходности, календарь, план DCA, доходность позиции",
        feat_to="- Восемь графиков: оборот, объём, гонка секторов, матрица доходности, календарь, план DCA, доходность позиции, свечи",
    ),
    "tr": dict(
        count_from="Yedi grafik sayfası:",
        count_to="Sekiz grafik sayfası:",
        bullet="• Mumlar — bir enstrüman günlük, haftalık veya aylık, dört çizim biçimi, hareketli ortalamalar ve hacim paneliyle",
        whats_new=(
            "Bu sürümdeki yenilikler: sekizinci grafik sayfası, Mumlar — bir enstrümanın fiyatları günlük, haftalık "
            "veya aylık mumlar olarak, dört çizim biçimiyle (mumlar, OHLC çubukları, kapanış çizgisi, kapanış alanı), "
            "MA5/10/20 hareketli ortalamalar ve hacim paneliyle; dönemin getirisi ile en yüksek ve en düşük değer "
            "karede işaretlenir. Animasyon ya tüm dönem boyunca mum mum büyür ya da sabit bir pencere içinde ilerler. "
            "Endeksler, hisseler ve ETF'ler çizilir, üç piyasada da. "
            "Mumlar, DCA planı ve pozisyon getirisi artık özel bir dönem kabul ediyor: Özel'i seçin, başlangıç ve "
            "bitiş tarihini girin, dönen veri tam olarak o dönem olur. "
            "Renkli bir arka plan bir opaklık kaydırıcısı kazandı: %100 seçtiğiniz iki rengin kendisi, düşürdüğünüzde "
            "sayfanın kendi koyu gradyanı alttan görünür, böylece açık bir renkte bile rakamlar okunur kalır; "
            "ayarlardaki gradyan önizlemesi de birlikte değişir. "
            "Üst kenar boşluğunun alt sınırı 230'dan 40'a gevşetildi, varsayılan yine 230. "
            "Ayrıca düzeltildi: mum başlığındaki fiyat satırı tarih satırının üzerine biniyordu ve harf büyüklüğü "
            "yanlış ABD kodları hiç veri getirmiyordu."
        ),
        feat_from="- Yedi grafik: işlem hacmi, hacim ve devir, sektör yarışı, getiri matrisi, takvim, DCA planı, pozisyon getirisi",
        feat_to="- Sekiz grafik: işlem hacmi, hacim ve devir, sektör yarışı, getiri matrisi, takvim, DCA planı, pozisyon getirisi, mumlar",
    ),
}


def split_block(block):
    """Splits one language's block into its heading and its three `###` sections.

    The parts are returned as mutable lists on purpose. Editing the lines of a
    string split — and then writing the *original* block — changes nothing at
    all, and the script reports success while the file is untouched: exactly
    what happened on the first run of this.
    """
    lines = block.split("\n")
    first = next(i for i, line in enumerate(lines) if line.startswith("### "))
    prefix = lines[:first]

    parts = []
    head = None
    body = []

    for line in lines[first:]:
        if line.startswith("### "):
            if head is not None:
                parts.append([head, body])
            head = line
            body = []
        else:
            body.append(line)

    if head is not None:
        parts.append([head, body])

    return prefix, parts


def join_block(prefix, parts):
    lines = list(prefix)

    for head, body in parts:
        lines.append(head)
        lines.extend(body)

    return "\n".join(lines)


def main():
    text = PATH.read_text(encoding="utf-8")
    blocks = text.split("\n## ")

    if len(blocks) != len(LANGS) + 1:
        raise AssertionError(
            f"{len(blocks) - 1} language blocks, expected {len(LANGS)}")

    done = []
    touched = False

    for index, block in enumerate(blocks[1:], start=1):
        title = block.split("\n", 1)[0].strip()

        # The heading carries the tag in parentheses — full-width in the CJK
        # headings, half-width elsewhere, and `Português (Brasil) (pt-BR)` has
        # two pairs, of which the tag is the last.
        parens = re.findall(r"[（(]([^）)]*)[）)]", title)

        if not parens:
            raise AssertionError(f"no language tag in heading {title!r}")

        tag = parens[-1].strip()

        if tag not in LANGS:
            raise AssertionError(f"unknown block: {title!r} -> {tag!r}")

        spec = LANGS[tag]
        prefix, parts = split_block(block)

        if len(parts) != 3:
            raise AssertionError(f"{tag}: {len(parts)} sections, expected 3")

        # ---- 1) the page count, and the candles page in the list
        body = parts[0][1]
        hits = [i for i, line in enumerate(body) if spec["count_from"] in line]

        # Already saying the new number is a finished run, not a mismatch.
        if not hits and any(spec["count_to"] in line for line in body):
            hits = []
        elif len(hits) != 1:
            raise AssertionError(
                f"{tag}: count line {spec['count_from']!r} found {len(hits)} times")

        for at in hits:
            body[at] = body[at].replace(spec["count_from"], spec["count_to"])
            touched = True

        bullets = [i for i, line in enumerate(body)
                   if line.startswith("• ") or line.startswith("- •")]

        if not bullets:
            raise AssertionError(f"{tag}: no page bullets found")

        last = bullets[-1]

        if not any(spec["bullet"] in line for line in body):
            # The list is a hard-wrapped Markdown paragraph, so a line ending in
            # two spaces is what keeps the next one on its own row.
            pad = body[last][len(body[last].rstrip()):]
            body.insert(last + 1, spec["bullet"] + pad)
            touched = True

        # ---- 2) what's new in this version: the section's only paragraph
        body = parts[1][1]
        paras = [i for i, line in enumerate(body) if line.strip()]

        if len(paras) != 1:
            raise AssertionError(
                f"{tag}: {len(paras)} paragraphs in the what's-new section")

        at = paras[0]

        if body[at].strip() != spec["whats_new"]:
            body[at] = spec["whats_new"]
            touched = True

        # ---- 3) the feature bullet naming the charts
        body = parts[2][1]
        hits = [i for i, line in enumerate(body)
                if line.strip() == spec["feat_from"]]

        if len(hits) != 1 and not any(spec["feat_to"] == line.strip() for line in body):
            raise AssertionError(
                f"{tag}: feature line {spec['feat_from']!r} found {len(hits)} times")

        if hits:
            body[hits[0]] = spec["feat_to"]
            touched = True

        blocks[index] = join_block(prefix, parts)
        done.append(tag)

    if touched:
        PATH.write_text("\n## ".join(blocks), encoding="utf-8")

    print(f"{len(done)} languages: {', '.join(done)}")
    print("rewritten" if touched else "already up to date")


if __name__ == "__main__":
    main()
