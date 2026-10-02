# -*- coding: utf-8 -*-
r"""把「大类资产」这一页的 resw 键注入 14 份 Resources.resw。

第十四个页面的文案：导航名、标题、副标题、资产下拉（标题 + 三组）、区间「最长」、
面板说明、口径说明、状态行、表头的计数词、「区间太短」那条错误，
再加上八只基金的 `INST*` 名字——英文界面上那一列要读得懂是哪一类资产。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`——
`port-ahpremium-resw.py` 里 `AhPremiumFetched` 就是在这里栽过：第一列写成了中文，
英文界面于是显示一整行中文状态。加键时先确认第一列是英文。

`INST*` 的键名由代码机械生成（`InstrumentNames.Key`）：代码去掉非字母数字、大写，
前面加 `INST`。`sh510300` → `INSTSH510300`。这里写的是名字，不是代码。

用法：python tools\port-assetrace-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 导航项、页面标题、以及无数据时舞台上的标题，共用一份：三处说的是同一件事。
NAV = [
    "Asset classes", "Anlageklassen", "Clases de activos", "Classes d'actifs",
    "Classi di attività", "Klasy aktywów", "Classes de ativos", "Třídy aktiv",
    "Varlık sınıfları", "Классы активов", "資産クラス", "자산군",
    "大類資產", "大类资产",
]

PAGE = [
    # `.Content`, not `.Text`: a NavigationViewItem is a ContentControl, and the x:Uid loader
    # asks for the property the type actually has. Written as `.Text` the app does not start.
    ("NavAssetRace.Content", NAV),

    ("AssetRacePageTitle.Text", NAV),

    ("AssetRaceStageTitle", NAV),

    ("AssetRacePageSubtitle.Text", [
        "Eight asset classes you could actually have held, on one board. Each is measured from "
        "its own first month in the range, so what is compared is the money that was left, not "
        "the quote.",
        "Acht Anlageklassen, die man wirklich hätte halten können, auf einer Tafel. Jede wird ab "
        "ihrem eigenen ersten Monat im Zeitraum gemessen – verglichen wird also das Geld, das "
        "übrig blieb, nicht die Notierung.",
        "Ocho clases de activos que realmente se podrían haber mantenido, en un mismo tablero. "
        "Cada una se mide desde su propio primer mes en el periodo, así que lo comparado es el "
        "dinero que quedó, no la cotización.",
        "Huit classes d'actifs que l'on aurait réellement pu détenir, sur un même tableau. "
        "Chacune est mesurée à partir de son propre premier mois de la période : ce qui est "
        "comparé, c'est l'argent restant, pas le cours.",
        "Otto classi di attività che si sarebbero potute detenere davvero, su un'unica tavola. "
        "Ognuna è misurata dal proprio primo mese nell'intervallo, quindi si confronta il denaro "
        "rimasto, non la quotazione.",
        "Osiem klas aktywów, które naprawdę można było trzymać, na jednej tablicy. Każda mierzona "
        "od własnego pierwszego miesiąca w okresie, więc porównywane są pieniądze, które "
        "zostały, a nie notowanie.",
        "Oito classes de ativos que você realmente poderia ter mantido, em um mesmo quadro. Cada "
        "uma é medida a partir do seu próprio primeiro mês no período, então o comparado é o "
        "dinheiro que restou, não a cotação.",
        "Osm tříd aktiv, které bylo skutečně možné držet, na jedné tabuli. Každá se měří od "
        "svého prvního měsíce v rozmezí, takže se porovnávají peníze, které zbyly, ne kotace.",
        "Gerçekten tutulabilecek sekiz varlık sınıfı tek tabloda. Her biri aralıktaki kendi ilk "
        "ayından itibaren ölçülür; karşılaştırılan geriye kalan paradır, kotasyon değil.",
        "Восемь классов активов, которые действительно можно было держать, на одной доске. Каждый "
        "измеряется от своего первого месяца в диапазоне, поэтому сравниваются оставшиеся деньги, "
        "а не котировка.",
        "実際に保有できた8つの資産クラスを1つのボードに。それぞれ範囲内の自分の最初の月から"
        "測るので、比べるのは残ったお金であり、気配値ではありません。",
        "실제로 보유할 수 있었던 여덟 개 자산군을 한 보드에. 각각 구간 내 자기 첫 달부터 "
        "측정하므로 비교하는 것은 남은 돈이며 시세가 아닙니다.",
        "八類真的可以持有的資產放在同一張榜上。每一個都從自己在區間裡的第一個月起算，所以比的"
        "是最後到手的錢，不是報價。",
        "八类真的可以持有的资产放在同一张榜上。每一个都从自己在区间里的第一个月起算，所以比的"
        "是最后到手的钱，不是报价。"]),

    ("AssetRaceList.Header", [
        "Asset class", "Anlageklasse", "Clase de activo", "Classe d'actifs",
        "Classe di attività", "Klasa aktywów", "Classe de ativos", "Třída aktiv",
        "Varlık sınıfı", "Класс активов", "資産クラス", "자산군", "資產", "资产"]),

    ("AssetRaceListAll", [
        "All eight", "Alle acht", "Las ocho", "Les huit", "Tutte e otto",
        "Wszystkie osiem", "Todas as oito", "Všech osm", "Sekizinin tümü",
        "Все восемь", "すべての8つ", "여덟 개 모두", "全部八類", "全部八类"]),

    ("AssetRaceListEquity", [
        "Shares", "Aktien", "Acciones", "Actions", "Azioni", "Akcje", "Ações", "Akcie",
        "Hisse senetleri", "Акции", "株式", "주식", "股票", "股票"]),

    # Bonds, gold, a commodity and cash — named by what they are not, because the four of them
    # share no word in any of these languages.
    ("AssetRaceListNonEquity", [
        "Everything else", "Alles andere", "Todo lo demás", "Tout le reste",
        "Tutto il resto", "Wszystko inne", "Todo o resto", "Vše ostatní",
        "Diğerleri", "Всё остальное", "株式以外", "기타", "非股票", "非股票"]),

    ("AssetRaceRangeMax", [
        "Longest", "Längster", "El más largo", "Le plus long", "Il più lungo",
        "Najdłuższy", "O mais longo", "Nejdelší", "En uzun", "Самый длинный",
        "最長", "가장 긴", "最長", "最长"]),

    ("AssetRaceNote.Text", [
        "One row per asset class. The bar is what holding it earned — dividends put back in, and "
        "share splits too, because a bond and a cash fund pay almost entirely in income, and a "
        "fund that split its units has a cliff in its own price.",
        "Eine Zeile pro Anlageklasse. Der Balken ist, was das Halten eingebracht hat — "
        "Ausschüttungen wieder eingerechnet und Aktiensplits ebenfalls, weil eine Anleihe und "
        "ein Geldmarktfonds fast vollständig in Erträgen zahlen und ein Fonds, der seine Anteile "
        "gesplittet hat, einen Abgrund im eigenen Kurs hat.",
        "Una fila por clase de activo. La barra es lo que ganó mantenerlo — dividendos "
        "reintegrados, y también splits, porque un bono y un fondo monetario pagan casi por "
        "completo en rentas, y un fondo que dividió sus participaciones tiene un acantilado en "
        "su propio precio.",
        "Une ligne par classe d'actifs. La barre est ce que la détention a rapporté — dividendes "
        "réintégrés, et scissions aussi, car une obligation et un fonds monétaire paient presque "
        "entièrement en revenus, et un fonds qui a divisé ses parts a une falaise dans son propre "
        "cours.",
        "Una riga per classe di attività. La barra è ciò che la detenzione ha reso — dividendi "
        "reinseriti e anche frazionamenti, perché un'obbligazione e un fondo monetario pagano "
        "quasi interamente in reddito, e un fondo che ha frazionato le quote ha un dirupo nel "
        "proprio prezzo.",
        "Jeden wiersz na klasę aktywów. Słupek to zarobek z trzymania — z wliczonymi dywidendami "
        "i również podziałami, bo obligacja i fundusz rynku pieniężnego płacą prawie wyłącznie "
        "dochodem, a fundusz po podziale jednostek ma urwisko we własnej cenie.",
        "Uma linha por classe de ativos. A barra é o que a manutenção rendeu — dividendos "
        "reintegrados e também desdobramentos, porque um título e um fundo de mercado monetário "
        "pagam quase inteiramente em renda, e um fundo que desdobrou cotas tem um penhasco no "
        "próprio preço.",
        "Jeden řádek na třídu aktiv. Sloupec je to, co držení vyneslo — zpět započtené dividendy "
        "a také štěpení, protože dluhopis a fond peněžního trhu platí téměř celou výnosem, a fond "
        "po štěpení podílů má ve vlastní ceně sráz.",
        "Her varlık sınıfı için bir satır. Çubuk, onu tutmanın kazandırdığıdır — temettüler "
        "geri konularak ve pay bölünmeleri de, çünkü bir tahvil ve bir para piyasası fonu "
        "neredeyse tamamen getiri olarak öder ve paylarını bölen bir fonun kendi fiyatında bir "
        "uçurum vardır.",
        "Одна строка на класс активов. Столбец — это то, что принесло владение: дивиденды "
        "возвращены в ряд, и дробления тоже, потому что облигация и фонд денежного рынка платят "
        "почти целиком доходом, а у фонда, дробившего паи, в собственной цене есть обрыв.",
        "資産クラスごとに1行。バーは保有して得たものです——配当を戻し入れ、分配や分割も同様に。"
        "債券とマネーマーケットファンドはそのほとんどを収益で支払うからであり、受益権を分割した"
        "ファンドは自分の価格に崖を持つからです。",
        "자산군마다 한 행. 막대는 보유해서 얻은 것입니다—배당을 되돌려 넣고 분할도 마찬가지로, "
        "채권과 머니마켓펀드는 거의 전부를 수익으로 지급하고, 수익증권을 분할한 펀드는 자기 "
        "가격에 절벽을 갖기 때문입니다.",
        "每一類資產一行。那一行的長度是持有它賺了多少——分紅算回去了，份額折算也算回去了，因為"
        "債券和貨幣基金的收益幾乎全在分紅裡，而拆過份額的基金，自己的價格曲線會斷一截。",
        "每一类资产一行。那一行的长度是持有它赚了多少——分红算回去了，份额折算也算回去了，因为"
        "债券和货币基金的收益几乎全在分红里，而拆过份额的基金，自己的价格曲线会断一截。"]),

    # The one paragraph that says why this board is adjusted when the index race is not.
    ("AssetRaceMethodNote.Text", [
        "Monthly, backward-adjusted — the opposite of the index race: an index pays no dividend, "
        "so nothing is adjusted there, while a fund does, and leaving it out would draw cash as "
        "0.00%. All eight are quoted on a mainland exchange, so the two overseas rows carry the "
        "exchange rate inside them. Start dates differ: the earliest is 2012, the commodity fund "
        "only from 2019. This page is not governed by the market setting.",
        "Monatlich, rückwärts adjustiert — das Gegenteil des Index-Rennens: Ein Index zahlt keine "
        "Dividende, dort wird also nichts adjustiert, ein Fonds hingegen schon, und ließe man es "
        "weg, würde Bargeld mit 0,00 % gezeichnet. Alle acht werden an einer Festlandbörse "
        "gehandelt, die beiden ausländischen Zeilen tragen den Wechselkurs also in sich. Die "
        "Anfänge unterscheiden sich: der früheste ist 2012, der Rohstofffonds erst ab 2019. "
        "Diese Seite unterliegt nicht der Markteinstellung.",
        "Mensual, ajustado hacia atrás — lo contrario de la carrera de índices: un índice no paga "
        "dividendos, así que allí no se ajusta nada, mientras que un fondo sí, y omitirlo "
        "dibujaría el efectivo como 0,00 %. Las ocho cotizan en una bolsa continental, así que "
        "las dos filas extranjeras llevan el tipo de cambio dentro. Los inicios difieren: el más "
        "temprano es 2012, el fondo de materias primas solo desde 2019. Esta página no está "
        "gobernada por el ajuste de mercado.",
        "Mensuel, ajusté en arrière — le contraire de la course des indices : un indice ne verse "
        "pas de dividende, rien n'y est donc ajusté, alors qu'un fonds en verse, et l'omettre "
        "dessinerait le cash à 0,00 %. Les huit sont cotés sur une place continentale, les deux "
        "lignes étrangères portent donc le change en elles. Les débuts diffèrent : le plus "
        "ancien est 2012, le fonds matières premières seulement à partir de 2019. Cette page "
        "n'est pas régie par le réglage de marché.",
        "Mensile, aggiustato all'indietro — l'opposto della corsa degli indici: un indice non paga "
        "dividendi, quindi lì non si aggiusta nulla, mentre un fondo sì, e ometterlo "
        "disegnerebbe il contante come 0,00%. Tutti e otto sono quotati su una borsa continentale, "
        "quindi le due righe estere portano il cambio al loro interno. Le partenze differiscono: "
        "la più antica è il 2012, il fondo su materie prime solo dal 2019. Questa pagina non è "
        "governata dall'impostazione di mercato.",
        "Miesięcznie, korygowany wstecz — odwrotność wyścigu indeksów: indeks nie płaci dywidend, "
        "więc tam nic się nie koryguje, a fundusz tak, i pominięcie tego narysowałoby gotówkę jako "
        "0,00%. Wszystkie osiem jest notowanych na giełdzie kontynentalnej, więc dwa zagraniczne "
        "wiersze mają kurs w środku. Początki się różnią: najwcześniejszy to 2012, fundusz "
        "towarowy dopiero od 2019. Ta strona nie podlega ustawieniu rynku.",
        "Mensal, ajustado para trás — o oposto da corrida de índices: um índice não paga "
        "dividendos, então nada é ajustado lá, enquanto um fundo paga, e omitir isso desenharia "
        "o caixa como 0,00%. Todas as oito são cotadas em uma bolsa continental, então as duas "
        "linhas estrangeiras trazem o câmbio dentro de si. Os inícios diferem: o mais antigo é "
        "2012, o fundo de commodities apenas a partir de 2019. Esta página não é governada pela "
        "configuração de mercado.",
        "Měsíčně, zpětně upraveno — opak závodu indexů: index nevyplácí dividendu, takže se tam "
        "nic neupravuje, zatímco fond ano, a vynechání by nakreslilo hotovost jako 0,00 %. Všech "
        "osm je kotováno na kontinentální burze, takže dva zahraniční řádky mají kurz uvnitř. "
        "Začátky se liší: nejdříve 2012, komoditní fond až od 2019. Tato stránka se neřídí "
        "nastavením trhu.",
        "Aylık, geriye dönük düzeltilmiş — endeks yarışının tersi: bir endeks temettü ödemez, "
        "orada hiçbir şey düzeltilmez; bir fon ise öder ve bu bırakılırsa nakit %0,00 olarak "
        "çizilirdi. Sekizi de bir anakara borsasında işlem görür, bu yüzden iki yabancı satır "
        "kuru içinde taşır. Başlangıçlar farklı: en erkeni 2012, emtia fonu yalnızca 2019'dan "
        "itibaren. Bu sayfa pazar ayarına tabi değildir.",
        "Ежемесячно, с поправкой назад — противоположность гонке индексов: индекс не платит "
        "дивидендов, там ничего не корректируется, а фонд платит, и если этого не сделать, "
        "наличные были бы нарисованы как 0,00%. Все восемь котируются на материковой бирже, "
        "поэтому две "
        "зарубежные строки несут курс внутри себя. Начала различаются: самое раннее — 2012 год, "
        "товарный фонд — только с 2019. Этой страницей настройка рынка не управляет.",
        "月足・後復権——指数レースとは逆です。指数は配当を払わないので何も調整しませんが、"
        "ファンドは払うからであり、省けば現金は0.00%として描かれます。8本すべてが本土の取引所で"
        "売買されるため、海外の2行には為替が内側に入っています。開始はまちまちです。最も古いもの"
        "は2012年、コモディティファンドは2019年からです。このページは市場設定に従いません。",
        "월간, 후복권—지수 레이스와 정반대입니다. 지수는 배당을 지급하지 않으므로 아무것도 "
        "조정하지 않지만 펀드는 지급하므로, 이를 빠뜨리면 현금이 0.00%로 그려집니다. 여덟 개 모두 "
        "본토 거래소에 상장되어 있어 해외 두 행은 환율을 안에 담고 있습니다. 시작은 제각각입니다. "
        "가장 이른 것은 2012년, 상품 펀드는 2019년부터입니다. 이 페이지는 시장 설정의 적용을 "
        "받지 않습니다.",
        "月線，後複權——與指數長跑正好相反：指數不發股息，所以那裡什麼都不調整；基金會發，省掉它"
        "就會把現金畫成 0.00%。八檔都在境內交易所掛牌，所以境外那兩行已經把匯率含在裡面。起點"
        "各不相同：最早的是 2012 年，商品基金要到 2019 年才有。這一頁不受市場設置管轄。",
        "月线，后复权——与指数长跑正好相反：指数不发股息，所以那里什么都不调整；基金会发，省掉"
        "它就会把现金画成 0.00%。八档都在境内交易所挂牌，所以境外那两行已经把汇率含在里面。起点"
        "各不相同：最早的是 2012 年，商品基金要到 2019 年才有。这一页不受市场设置管辖。"]),

    ("AssetRaceFetched", [
        "{0} assets · {1} months · ahead is {2}, {3} · behind is {4}, {5}",
        "{0} Anlagen · {1} Monate · vorn {2} mit {3} · hinten {4} mit {5}",
        "{0} activos · {1} meses · delante {2} con {3} · detrás {4} con {5}",
        "{0} actifs · {1} mois · devant {2} avec {3} · derrière {4} avec {5}",
        "{0} attività · {1} mesi · davanti {2} con {3} · dietro {4} con {5}",
        "{0} aktywów · {1} miesięcy · z przodu {2} z {3} · z tyłu {4} z {5}",
        "{0} ativos · {1} meses · na frente {2} com {3} · atrás {4} com {5}",
        "{0} aktiv · {1} měsíců · první {2} na {3} · poslední {4} na {5}",
        "{0} varlık · {1} ay · önde {2}, {3} · geride {4}, {5}",
        "{0} активов · {1} месяцев · впереди {2} с {3} · позади {4} с {5}",
        "{0} 資産 · {1} か月 · 首位 {2}（{3}） · 最下位 {4}（{5}）",
        "{0}개 자산 · {1}개월 · 선두 {2} {3} · 최하위 {4} {5}",
        "{0} 個標的 · {1} 個月 · 領先的是 {2}，{3} · 墊底的是 {4}，{5}",
        "{0} 个标的 · {1} 个月 · 领先的是 {2}，{3} · 垫底的是 {4}，{5}"]),

    # The header's count word, printed after the number of rows. Supplied by the page for the
    # reason the renderer's own note gives: the renderer cannot see what the rows are.
    ("AssetRaceUnitAssets", [
        "assets", "Anlagen", "activos", "actifs", "attività", "aktywów", "ativos", "aktiv",
        "varlık", "активов", "資産", "개 자산", "個標的", "个标的"]),

    ("AssetRaceTooFew", [
        "Too few months in this range for a race. Try a longer range.",
        "Zu wenige Monate in diesem Zeitraum für ein Rennen. Versuchen Sie einen längeren.",
        "Demasiados pocos meses en este periodo para una carrera. Pruebe con un periodo más largo.",
        "Trop peu de mois dans cette période pour une course. Essayez une période plus longue.",
        "Troppi pochi mesi in questo periodo per una corsa. Provi un periodo più lungo.",
        "Za mało miesięcy w tym okresie na wyścig. Spróbuj dłuższego okresu.",
        "Meses demaisados poucos neste período para uma corrida. Tente um período mais longo.",
        "V tomto období je příliš málo měsíců na závod. Zkuste delší období.",
        "Bu aralıkta bir yarış için çok az ay var. Daha uzun bir aralık deneyin.",
        "В этом периоде слишком мало месяцев для гонки. Возьмите период длиннее.",
        "この期間では月数が少なすぎてレースになりません。もっと長い期間をお試しください。",
        "이 기간은 레이스를 만들기에 달 수가 너무 적습니다. 더 긴 기간을 선택하세요.",
        "這段區間的月份太少，跑不成一場比賽。換長一點的區間試試。",
        "这段区间的月份太少，跑不成一场比赛。换长一点的区间试试。"]),
]

# 八只基金的名字里，只有四只需要这里写：sh510300、sh510500、sh518880、sh513100
# 早就在 `Markets.cs` 的预设里（定投、持仓、K线三页的候选），`INST*` 键本来就有。
# **一个键只能有一个来源**——那四只归预设那条线，这里动它们会波及三页的预设按钮，
# 所以这里只补清单上另外四只的键。页面读名字走 `InstrumentNames.Display`，
# 那四只照样有英文名，只是不由这份脚本写。
ETF = [
    ("INSTSZ159920", [
        "Hang Seng ETF", "Hang-Seng-ETF", "ETF Hang Seng", "ETF Hang Seng", "ETF Hang Seng",
        "ETF Hang Seng", "ETF Hang Seng", "ETF Hang Seng", "Hang Seng ETF", "ETF Hang Seng",
        "ハンセンETF", "항셍 ETF", "恆生ETF", "恒生ETF"]),

    ("INSTSH511010", [
        "Government bond ETF", "Staatsanleihen-ETF", "ETF de bonos del Estado",
        "ETF d'obligations d'État", "ETF titoli di Stato", "ETF obligacji skarbowych",
        "ETF de títulos públicos", "ETF státních dluhopisů", "Devlet tahvili ETF",
        "ETF гос. облигаций", "国債ETF", "국채 ETF", "國債ETF", "国债ETF"]),

    ("INSTSZ159985", [
        "Soybean meal ETF", "Sojaschrot-ETF", "ETF de harina de soja", "ETF tourteau de soja",
        "ETF farina di soia", "ETF śruty sojowej", "ETF de farelo de soja", "ETF sojového šrotu",
        "Soya küspesi ETF", "ETF соевого шрота", "大豆ミールETF", "대두박 ETF",
        "豆粕ETF", "豆粕ETF"]),

    ("INSTSH511880", [
        "Money market ETF", "Geldmarkt-ETF", "ETF del mercado monetario", "ETF monétaire",
        "ETF del mercato monetario", "ETF rynku pieniężnego", "ETF de mercado monetário",
        "ETF peněžního trhu", "Para piyasası ETF", "ETF денежного рынка",
        "マネーマーケットETF", "머니마켓 ETF", "貨幣ETF", "货币ETF"]),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project file
    rather than the string that caused it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    rows = PAGE + ETF

    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        lines = []

        for key, values in rows:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in rows:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at = text.rfind("</root>")
        assert at > 0, f"{tag}: no </root>"

        text = text[:at] + "".join(lines) + text[at:]

        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
