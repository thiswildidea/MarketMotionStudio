# -*- coding: utf-8 -*-
r"""把「指数长跑」这一页的 resw 键注入 14 份 Resources.resw。

第十三个页面的文案：导航名、标题、副标题、指数组下拉（标题 + 四项）、区间「最长」、
面板说明、口径说明、状态行、表头的计数词、以及「区间太短」那条错误。

表头的周期词不在这里：它复用 `MarketCapUnitMonths`（个月）——同一个词、同一个意思，
再加一份新键只是给翻译多一条要维护的行。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`——
`port-ahpremium-resw.py` 里 `AhPremiumFetched` 就是在这里栽过：第一列写成了中文，
英文界面于是显示一整行中文状态。加键时先确认第一列是英文。

用法：python tools\port-indexrace-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 导航项、页面标题、以及无数据时舞台上的标题，共用一份：三处说的是同一件事。
NAV = [
    "Index race", "Index-Rennen", "Carrera de índices", "Course des indices",
    "Corsa degli indici", "Wyścig indeksów", "Corrida de índices", "Závod indexů",
    "Endeks yarışı", "Гонка индексов", "指数レース", "지수 레이스",
    "指數長跑", "指数长跑",
]

PAGE = [
    # `.Content`, not `.Text`: a NavigationViewItem is a ContentControl, and the x:Uid loader
    # asks for the property the type actually has. Written as `.Text` the app does not start —
    # MainWindow's InitializeComponent throws, which is a crash on launch, not a blank label.
    ("NavIndexRace.Content", NAV),

    ("IndexRacePageTitle.Text", NAV),

    ("IndexRaceStageTitle", NAV),

    ("IndexRacePageSubtitle.Text", [
        "Twelve indices from three markets on one board. Each is measured from its own first "
        "month in the range, so what is compared is the change, not the level.",
        "Zwölf Indizes aus drei Märkten auf einem Board. Jeder wird ab seinem eigenen ersten "
        "Monat im Zeitraum gemessen, verglichen wird also die Veränderung, nicht das Niveau.",
        "Doce índices de tres mercados en un mismo tablero. Cada uno se mide desde su propio "
        "primer mes en el periodo, así que lo comparado es la variación, no el nivel.",
        "Douze indices de trois marchés sur un même tableau. Chacun est mesuré à partir de son "
        "propre premier mois de la période : ce qui est comparé, c'est la variation, pas le "
        "niveau.",
        "Dodici indici di tre mercati su un'unica tavola. Ognuno è misurato dal proprio primo "
        "mese nell'intervallo, quindi si confronta la variazione, non il livello.",
        "Dwanaście indeksów z trzech rynków na jednej tablicy. Każdy mierzony od własnego "
        "pierwszego miesiąca w okresie, więc porównywana jest zmiana, nie poziom.",
        "Doze índices de três mercados em um mesmo quadro. Cada um é medido a partir do seu "
        "próprio primeiro mês no período, então o comparado é a variação, não o nível.",
        "Dvanáct indexů ze tří trhů na jedné tabuli. Každý se měří od svého prvního měsíce "
        "v rozmezí, takže se porovnává změna, ne úroveň.",
        "Üç piyasadan on iki endeks tek tabloda. Her biri, aralıktaki kendi ilk ayından itibaren "
        "ölçülür; karşılaştırılan değişimdir, seviye değil.",
        "Двенадцать индексов с трёх рынков на одной доске. Каждый измеряется от своего первого "
        "месяца в диапазоне, поэтому сравнивается изменение, а не уровень.",
        "三つの市場から12の指数を1つのボードに。それぞれ範囲内の自分の最初の月から測るので、"
        "比べるのは水準ではなく変化です。",
        "세 시장의 지수 12개를 한 보드에. 각각 구간 내 자기 첫 달부터 측정하므로 비교하는 것은 "
        "수준이 아니라 변화입니다.",
        "三個市場的十二個指數放在同一張榜上。每一個都從自己在區間裡的第一個月起算，所以比的"
        "是變化，不是點位。",
        "三个市场的十二个指数放在同一张榜上。每一个都从自己在区间里的第一个月起算，所以比的"
        "是变化，不是点位。"]),

    ("IndexRaceList.Header", [
        "Indices", "Indizes", "Índices", "Indices", "Indici", "Indeksy", "Índices", "Indexy",
        "Endeksler", "Индексы", "指数", "지수", "指數", "指数"]),

    ("IndexRaceListAll", [
        "All twelve", "Alle zwölf", "Los doce", "Les douze", "Tutti e dodici",
        "Wszystkie dwanaście", "Os doze", "Všech dvanáct", "On ikisi de",
        "Все двенадцать", "12本すべて", "열두 개 모두", "全部十二個", "全部十二个"]),

    ("IndexRaceListAShare", [
        "Mainland A-shares", "Festland-Aktien", "Acciones A del continente",
        "Actions A continentales", "Azioni A della Cina continentale", "Akcje A z kontynentu",
        "Ações A do continente", "Pevninské akcie A", "Anakara A hisseleri",
        "Материковые акции A", "中国本土A株", "본토 A주", "A股", "A股"]),

    ("IndexRaceListHongKong", [
        "Hong Kong", "Hongkong", "Hong Kong", "Hong Kong", "Hong Kong", "Hongkong",
        "Hong Kong", "Hongkong", "Hong Kong", "Гонконг", "香港", "홍콩", "港股", "港股"]),

    ("IndexRaceListUnitedStates", [
        "United States", "USA", "Estados Unidos", "États-Unis", "Stati Uniti",
        "Stany Zjednoczone", "Estados Unidos", "Spojené státy", "ABD", "США", "米国", "미국",
        "美股", "美股"]),

    ("IndexRaceRangeMax", [
        "Longest", "Längster", "Más largo", "Le plus long", "Il più lungo", "Najdłuższy",
        "Mais longo", "Nejdelší", "En uzun", "Самый длинный", "最長", "가장 긴",
        "最長", "最长"]),

    # No placeholder in it: the group is whatever was chosen, and a card that counts rows before
    # the fetch has run is a card that has to be rewritten on every fetch — and one read with
    # `Strings.Get` shows a literal "{0}", which two pages here have already done.
    # A TextBlock's x:Uid asks for `.Text`, so the key carries it even though nothing in code
    # reads it — a bare key here is a blank card and a verify failure, not a fallback.
    ("IndexRaceNote.Text", [
        "One row per index. The row is the change that index has made since its own first month "
        "in the range — never its level, because 3,800 and 5,700 are not two points on one "
        "scale. An index whose history begins later is not on the board until it begins: it is "
        "absent, not at zero.",
        "Eine Zeile je Index. Die Zeile ist die Veränderung, die dieser Index seit seinem "
        "eigenen ersten Monat im Zeitraum gemacht hat — nie sein Niveau, denn 3.800 und 5.700 "
        "sind keine zwei Punkte auf einer Skala. Ein Index, dessen Geschichte später beginnt, "
        "steht erst ab dann auf dem Board: er fehlt, statt null zu sein.",
        "Una fila por índice. La fila es la variación que ese índice ha tenido desde su propio "
        "primer mes en el periodo — nunca su nivel, porque 3.800 y 5.700 no son dos puntos de "
        "una misma escala. Un índice cuya historia empieza más tarde no está en el tablero "
        "hasta que empieza: no está, no está a cero.",
        "Une ligne par indice. La ligne est la variation de cet indice depuis son propre premier "
        "mois dans la période — jamais son niveau, car 3 800 et 5 700 ne sont pas deux points "
        "d'une même échelle. Un indice dont l'historique commence plus tard n'est pas sur le "
        "tableau avant ce moment : il est absent, pas à zéro.",
        "Una riga per indice. La riga è la variazione che quell'indice ha fatto dal proprio "
        "primo mese nell'intervallo — mai il suo livello, perché 3.800 e 5.700 non sono due "
        "punti di una stessa scala. Un indice la cui storia inizia dopo non è sulla tavola "
        "fino ad allora: è assente, non a zero.",
        "Jeden wiersz na indeks. Wiersz to zmiana, jaką ten indeks zrobił od swojego "
        "pierwszego miesiąca w okresie — nigdy jego poziom, bo 3 800 i 5 700 to nie są dwa "
        "punkty na jednej skali. Indeks, którego historia zaczyna się później, nie ma go na "
        "tablicy, dopóki się nie zacznie: brakuje go, a nie jest zerem.",
        "Uma linha por índice. A linha é a variação que esse índice teve desde o seu próprio "
        "primeiro mês no período — nunca o seu nível, porque 3.800 e 5.700 não são dois pontos "
        "na mesma escala. Um índice cujo histórico começa depois não está no quadro até "
        "começar: ele está ausente, não em zero.",
        "Jeden řádek na index. Řádek je změna, kterou ten index udělal od svého prvního měsíce "
        "v rozmezí — nikdy jeho úroveň, protože 3 800 a 5 700 nejsou dva body na jedné stupnici. "
        "Index, jehož historie začíná později, na tabuli není, dokud nezačne: chybí, není nulový.",
        "Her endeks için bir satır. Satır, o endeksin aralıktaki kendi ilk ayından bu yana "
        "yaptığı değişimdir — seviyesi asla, çünkü 3.800 ile 5.700 aynı ölçeğin iki noktası "
        "değil. Geçmişi daha sonra başlayan bir endeks, başlayana kadar tabloda yoktur: sıfırda "
        "değil, hiç yoktur.",
        "Одна строка на индекс. Строка — это изменение индекса с его собственного первого месяца "
        "в диапазоне, но не его уровень: 3 800 и 5 700 — не две точки на одной шкале. Индекс, "
        "чья история начинается позже, не появляется на доске до своего начала: он отсутствует, "
        "а не стоит в нуле.",
        "指数ごとに1行。行は、その指数が範囲内の自分の最初の月からどれだけ動いたか——水準では"
        "ありません。3,800と5,700は同じ物差しの上の2点ではないからです。歴史が後に始まる指数は、"
        "始まるまでボードに出ません。ゼロではなく、いないのです。",
        "지수마다 한 줄. 줄은 그 지수가 구간 내 자기 첫 달부터 얼마나 움직였는지입니다. 수준이 "
        "아닙니다. 3,800과 5,700은 같은 척도 위의 두 점이 아니기 때문입니다. 역사가 나중에 "
        "시작하는 지수는 시작할 때까지 보드에 없습니다. 0이 아니라 없는 것입니다.",
        "每一個指數一行。那一行的長度是它從自己在區間裡的第一個月起漲了多少——不是它的點位，"
        "因為 3,800 與 5,700 不是同一把尺上的兩點。歷史起步比較晚的指數，在它起步之前不會"
        "出現在榜上：那時它是缺席，不是零。",
        "每一个指数一行。那一行的长度是它从自己在区间里的第一个月起涨了多少——不是它的点位，"
        "因为 3,800 与 5,700 不是同一把尺上的两点。历史起步比较晚的指数，在它起步之前不会"
        "出现在榜上：那时它是缺席，不是零。"]),

    ("IndexRaceMethodNote.Text", [
        "Monthly bars, unadjusted — an index pays no dividend, and an adjustment is a rebasing "
        "of one series, so two rebased series side by side are not comparable. Coverage differs: "
        "the S&P reaches back to 1950, the Dow to 2009 and the Hang Seng Tech index to 2020. "
        "This board is not governed by the market setting: it reads three markets at once.",
        "Monatskerzen, nicht bereinigt — ein Index zahlt keine Dividende, und eine Bereinigung "
        "ist eine Neubasierung einer Reihe; zwei neu basierte Reihen nebeneinander sind nicht "
        "vergleichbar. Die Reichweite ist unterschiedlich: der S&P reicht bis 1950 zurück, der "
        "Dow bis 2009 und der Hang-Seng-Tech-Index bis 2020. Dieses Board richtet sich nicht "
        "nach der Markteinstellung: es liest drei Märkte zugleich.",
        "Velas mensuales, sin ajustar — un índice no paga dividendo, y un ajuste es un "
        "rebasamiento de una serie, así que dos series rebasadas una al lado de la otra no son "
        "comparables. La cobertura varía: el S&P llega hasta 1950, el Dow hasta 2009 y el "
        "índice Hang Seng Tech hasta 2020. Este tablero no depende del ajuste de mercado: lee "
        "tres mercados a la vez.",
        "Bougies mensuelles, non ajustées — un indice ne verse pas de dividende, et un ajustement "
        "est un rebasage d'une série : deux séries rebasées côte à côte ne sont pas comparables. "
        "La couverture diffère : le S&P remonte à 1950, le Dow à 2009 et l'indice Hang Seng Tech "
        "à 2020. Ce tableau ne dépend pas du réglage de marché : il lit trois marchés à la fois.",
        "Candele mensili, non rettificate — un indice non paga dividendi, e una rettifica è una "
        "rideterminazione della base di una serie: due serie ribasate affiancate non sono "
        "confrontabili. La copertura differisce: l'S&P arriva al 1950, il Dow al 2009 e l'indice "
        "Hang Seng Tech al 2020. Questa tavola non dipende dall'impostazione del mercato: legge "
        "tre mercati insieme.",
        "Świece miesięczne, bez korekty — indeks nie wypłaca dywidendy, a korekta to zmiana "
        "bazy jednej serii, więc dwie serie po zmianie bazy nie są porównywalne. Zasięg danych "
        "jest różny: S&P sięga 1950, Dow 2009, a indeks Hang Seng Tech 2020. Ta tablica nie "
        "zależy od ustawienia rynku: czyta trzy rynki naraz.",
        "Velas mensais, sem ajuste — um índice não paga dividendo, e um ajuste é uma rebaseação "
        "de uma série, então duas séries rebaseadas lado a lado não são comparáveis. A cobertura "
        "varia: o S&P chega a 1950, o Dow a 2009 e o índice Hang Seng Tech a 2020. Este quadro "
        "não depende da configuração de mercado: ele lê três mercados ao mesmo tempo.",
        "Měsíční svíčky, bez úprav — index nevyplácí dividendu a úprava je přebázování jedné "
        "řady, takže dvě přebázované řady vedle sebe nejsou srovnatelné. Pokrytí se liší: S&P "
        "sahá do roku 1950, Dow do 2009 a index Hang Seng Tech do 2020. Tato tabule se neřídí "
        "nastavením trhu: čte tři trhy najednou.",
        "Aylık mumlar, düzeltilmemiş — bir endeks temettü ödemez ve düzeltme bir serinin "
        "yeniden bazlanmasıdır, bu yüzden yan yana konan iki yeniden bazlanmış seri "
        "karşılaştırılamaz. Kapsam farklı: S&P 1950'ye, Dow 2009'a ve Hang Seng Teknoloji "
        "endeksi 2020'ye kadar uzanır. Bu tablo piyasa ayarına bağlı değildir: üç piyasayı "
        "birlikte okur.",
        "Месячные бары, без корректировки — у индекса нет дивидендов, а корректировка "
        "перебазирует ряд, поэтому два перебазированных ряда рядом не сравнимы. Охват различается: "
        "S&P уходит в 1950, Dow — в 2009, а индекс Hang Seng Tech — в 2020. Эта доска не зависит "
        "от настройки рынка: она читает три рынка одновременно.",
        "月足、調整なし — 指数に配当はなく、調整は系列の基準の付け替えなので、付け替えた二つの"
        "系列を並べても比較できません。データの範囲は異なります。S&Pは1950年、ダウは2009年、"
        "ハンセンテック指数は2020年までです。このボードは市場設定に従いません。三つの市場を"
        "同時に読みます。",
        "월별 봉, 조정 없음 — 지수에는 배당이 없고 조정은 계열의 기준을 다시 잡는 것이므로, "
        "다시 잡은 두 계열을 나란히 놓고 비교할 수 없습니다. 자료 범위는 다릅니다. S&P는 "
        "1950년, 다우는 2009년, 항셍 테크 지수는 2020년까지입니다. 이 보드는 시장 설정의 "
        "영향을 받지 않습니다. 세 시장을 동시에 읽습니다.",
        "月線，不調整——指數不發股息，而調整是把一條序列重新定基，兩條各自重新定基的序列"
        "放在一起並不能比。資料起點各不相同：標普 500 可回溯到 1950 年，道瓊斯到 2009 年，"
        "恆生科技指數到 2020 年。這一頁不受市場設定管轄：它同時讀三個市場。",
        "月线，不调整——指数不发股息，而调整是把一条序列重新定基，两条各自重新定基的序列"
        "放在一起并不能比。数据起点各不相同：标普 500 可回溯到 1950 年，道琼斯到 2009 年，"
        "恒生科技指数到 2020 年。这一页不受市场设置管辖：它同时读三个市场。"]),

    # Six placeholders: indices, months, the leader and by how much, then the same for the last
    # of them. Formatted, not fetched with `Strings.Get` — see IndexRaceNote.
    ("IndexRaceFetched", [
        "{0} indices · {1} months · ahead {2} at {3} · behind {4} at {5}",
        "{0} Indizes · {1} Monate · vorn {2} bei {3} · hinten {4} bei {5}",
        "{0} índices · {1} meses · primero {2} con {3} · último {4} con {5}",
        "{0} indices · {1} mois · en tête {2} à {3} · dernier {4} à {5}",
        "{0} indici · {1} mesi · primo {2} a {3} · ultimo {4} a {5}",
        "{0} indeksów · {1} miesięcy · pierwszy {2} przy {3} · ostatni {4} przy {5}",
        "{0} índices · {1} meses · na frente {2} com {3} · atrás {4} com {5}",
        "{0} indexů · {1} měsíců · první {2} na {3} · poslední {4} na {5}",
        "{0} endeks · {1} ay · önde {2}, {3} · geride {4}, {5}",
        "{0} индексов · {1} месяцев · впереди {2} с {3} · позади {4} с {5}",
        "{0} 指数 · {1} か月 · 首位 {2}（{3}） · 最下位 {4}（{5}）",
        "{0}개 지수 · {1}개월 · 선두 {2} {3} · 최하위 {4} {5}",
        "{0} 個指數 · {1} 個月 · 領先的是 {2}，{3} · 墊底的是 {4}，{5}",
        "{0} 个指数 · {1} 个月 · 领先的是 {2}，{3} · 垫底的是 {4}，{5}"]),

    # The header's count word, printed after the number of rows. Supplied by the page for the
    # reason the renderer's own note gives: the renderer cannot see what the rows are.
    ("IndexRaceUnitIndices", [
        "indices", "Indizes", "índices", "indices", "indici", "indeksów", "índices", "indexů",
        "endeks", "индексов", "指数", "개 지수", "個指數", "个指数"]),

    ("IndexRaceTooFew", [
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


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project file
    rather than the string that caused it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        lines = []

        for key, values in PAGE:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in PAGE:
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
