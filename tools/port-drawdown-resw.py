# -*- coding: utf-8 -*-
r"""把「回撤与修复」这一页的 resw 键注入 14 份 Resources.resw。

第十五个页面的文案：导航名、标题、副标题、标的下拉的头、面板说明、口径说明、
状态行、区间太短那条错误，以及行内那三个小词（最深 / 多久修复 / 至今未修复）。

**复用第十四页的三个键**：标的三组的名字（`AssetRaceListAll` 等）、区间「最长」
（`AssetRaceRangeMax`）、表头计数词（`AssetRaceUnitAssets`）。两页跑的是同一批八档、
共用一份清单，一个东西有两个名字就是让读的人自己翻译。复用不是重复定义——那
条「一个键只能有一个来源」的规矩说的是别把别人已写的键改掉，这里只是读它。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`——
`port-ahpremium-resw.py` 里 `AhPremiumFetched` 就是在这里栽过：第一列写成了中文，
英文界面于是显示一整行中文状态。加键时先确认第一列是英文。

用法：python tools\port-drawdown-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 导航项、页面标题、无数据时舞台上的标题，共用一份：三处说的是同一件事。
NAV = [
    "Drawdowns", "Rücksetzer", "Caídas", "Reculs", "Ribassi", "Obsunięcia",
    "Quedas", "Poklesy", "Düşüşler", "Просадки", "ドローダウン", "낙폭",
    "回撤與修復", "回撤与修复",
]

LIST = [
    "Holdings", "Anlagen", "Instrumentos", "Supports", "Strumenti", "Instrumenty",
    "Ativos", "Nástroje", "Varlıklar", "Инструменты", "銘柄", "종목",
    "標的", "标的",
]

SUBTITLE = [
    "The same eight holdings as the asset race, measured against their own highs instead of "
    "each other: how far below the high a holder sat, and how many months it took to get back.",

    "Dieselben acht Anlagen wie beim Rennen der Anlageklassen, aber am eigenen Hoch gemessen "
    "statt gegeneinander: wie weit unter dem Hoch ein Halter saß und wie viele Monate der Weg "
    "zurück dauerte.",

    "Las mismas ocho inversiones que en la carrera de clases de activos, medidas contra sus "
    "propios máximos en lugar de entre sí: cuánto por debajo del máximo estuvo quien las "
    "mantuvo y cuántos meses costó volver.",

    "Les huit mêmes supports que la course des classes d'actifs, mesurés par rapport à leurs "
    "propres sommets au lieu de les comparer entre eux : à quelle distance du sommet le "
    "détenteur s'est trouvé, et en combien de mois il est remonté.",

    "Gli stessi otto strumenti della corsa delle classi di attività, ma misurati rispetto ai "
    "propri massimi invece che tra loro: quanto sotto il massimo si è trovato chi li deteneva, "
    "e quanti mesi è costato tornarci.",

    "Te same osiem instrumentów co w wyścigu klas aktywów, tyle że mierzone względem własnych "
    "szczytów, nie względem siebie: jak daleko poniżej szczytu był posiadacz i ile miesięcy "
    "zajęła droga powrotna.",

    "Os mesmos oito ativos da corrida de classes de ativos, medidos contra as próprias máximas "
    "em vez de entre si: a que distância da máxima ficou quem os manteve e quantos meses levou "
    "para voltar.",

    "Týchž osm nástrojů jako v závodu tříd aktiv, ale měřených vůči vlastním maximům, ne proti "
    "sobě: jak hluboko pod maximem držitel byl a kolik měsíců trvala cesta zpět.",

    "Varlık sınıfları yarışındaki aynı sekiz varlık, ama birbirine karşı değil kendi "
    "zirvelerine göre ölçülüyor: elinde tutanın zirvenin ne kadar altında kaldığı ve geri "
    "dönüşün kaç ay sürdüğü.",

    "Те же восемь инструментов, что в гонке классов активов, но измеренные по собственным "
    "максимумам, а не друг против друга: насколько ниже максимума оказывался держатель и за "
    "сколько месяцев он вернулся.",

    "資産クラスレースと同じ八つの資産を、互いではなく各自の高値に対して測る——保有者が高値から"
    "どれだけ下にいたか、そして戻るまでに何か月かかったか。",

    "자산군 경주와 같은 여덟 자산을 서로가 아니라 각자의 고점에 견주어 측정한다—보유자가 고점 "
    "아래 얼마나 있었는지, 그리고 되돌아오는 데 몇 달이 걸렸는지.",

    "與「大類資產」同為那八檔，只是不互相比，而是各自比自己的高點：持有者曾落在高點下方多遠，"
    "以及回到高點用了幾個月。",

    "与「大类资产」同为那八档，只是不互相比，而是各自比自己的高点：持有者曾落在高点下方多远，"
    "以及回到高点用了几个月。",
]

NOTE = [
    "A row is how far below its own high a holding sits. The curve is the point: the low and the "
    "climb out of it are two places on it, and the months between them are the half a single "
    "number leaves out.",

    "Eine Zeile ist, wie weit unter dem eigenen Hoch eine Anlage steht. Die Kurve ist der Punkt: "
    "das Tief und der Weg heraus sind zwei Stellen auf ihr, und die Monate dazwischen fehlen in "
    "jeder einzelnen Zahl.",

    "Cada fila es cuánto por debajo de su propio máximo está una inversión. La curva es lo "
    "importante: el mínimo y la salida de él son dos puntos en ella, y los meses entre ambos "
    "son la mitad que un solo número deja fuera.",

    "Une ligne, c'est la distance entre une position et son propre sommet. La courbe est le "
    "sujet : le creux et la remontée y sont deux endroits, et les mois entre les deux sont la "
    "moitié qu'un seul nombre ne dit pas.",

    "Una riga è quanto sotto il proprio massimo si trova uno strumento. La curva è il punto: il "
    "minimo e la risalita sono due punti su di essa, e i mesi fra loro sono la metà che un "
    "numero solo omette.",

    "Wiersz to odległość instrumentu od własnego szczytu. Krzywa jest sednem: dołek i wyjście z "
    "niego to dwa miejsca na niej, a miesiące między nimi to połowa, której jedna liczba nie "
    "oddaje.",

    "Uma linha é a distância entre um ativo e sua própria máxima. A curva é o ponto: o fundo e a "
    "saída dele são dois lugares nela, e os meses entre ambos são a metade que um único número "
    "deixa de fora.",

    "Řádek je vzdálenost nástroje od vlastního maxima. Křivka je to podstatné: minimum a cesta "
    "ven z něj jsou na ní dvě místa a měsíce mezi nimi jsou ta polovina, kterou jediné číslo "
    "vynechává.",

    "Bir satır, bir varlığın kendi zirvesinin ne kadar altında olduğudur. Önemli olan eğri: dip "
    "ve ondan çıkış üzerindeki iki noktadır; aralarındaki aylar ise tek bir sayının dışarıda "
    "bıraktığı yarıdır.",

    "Строка — это насколько инструмент ниже собственного максимума. Кривая и есть суть: минимум "
    "и выход из него — две точки на ней, а месяцы между ними — та половина, которую одно число "
    "не передаёт.",

    "行はその資産が自分の高値からどれだけ下にいるか。要点は曲線——安値とそこからの回復は曲線上"
    "の二つの場所で、その間の月数こそ単一の数字が落とす半分である。",

    "행은 그 자산이 자기 고점에서 얼마나 아래 있는지다. 핵심은 곡선—저점과 그곳에서 빠져나온 "
    "지점은 곡선 위의 두 지점이고, 그 사이의 개월 수야말로 하나의 숫자가 빠뜨리는 절반이다.",

    "一行是它落在自己高點下方多遠。曲線才是重點：低點與爬出來的那一點是曲線上的兩個位置，"
    "中間隔的月數正是單一數字漏掉的那一半。",

    "一行是它落在自己高点下方多远。曲线才是重点：低点与爬出来的那一端是曲线上的两个位置，"
    "中间隔的月数正是单一数字漏掉的那一半。",
]

METHOD = [
    "Monthly and adjusted — dividends and splits put back — and each row starts level on its own "
    "first month in the range. One depth scale for the whole board, so a holding that never "
    "really fell is a flat line: that flatness is what the row says.",

    "Monatlich und adjustiert – Dividenden und Splits eingerechnet – und jede Zeile beginnt auf "
    "ihrem eigenen ersten Monat im Zeitraum mit null. Eine Tiefenskala für die ganze Tafel: "
    "Eine Anlage, die nie wirklich fiel, ist eine flache Linie, und diese Flachheit ist ihre "
    "Aussage.",

    "Mensual y ajustado — dividendos y splits incluidos — y cada fila empieza en su propio primer "
    "mes del periodo. Una sola escala de profundidad para todo el tablero: una inversión que "
    "nunca cayó de verdad es una línea plana, y esa planicie es lo que dice la fila.",

    "Mensuel et ajusté — dividendes et divisions intégrés — et chaque ligne part à plat sur son "
    "propre premier mois dans la période. Une seule échelle de profondeur pour tout le tableau : "
    "un support qui n'est jamais vraiment tombé est une ligne plate, et cette platitude est "
    "précisément ce que la ligne dit.",

    "Mensile e aggiustato — dividendi e frazionamenti inclusi — e ogni riga parte piana nel "
    "proprio primo mese dell'intervallo. Una sola scala di profondità per tutta la tavola: uno "
    "strumento che non è mai caduto davvero è una linea piatta, e quella piattezza è ciò che la "
    "riga dice.",

    "Miesięcznie i z korektą — dywidendy i splity wliczone — a każdy wiersz startuje płasko w "
    "swoim pierwszym miesiącu okresu. Jedna skala głębokości dla całej tablicy: instrument, "
    "który naprawdę nie spadł, jest płaską linią, i ta płaskość jest jego komunikatem.",

    "Mensal e ajustado — dividendos e desdobramentos incluídos — e cada linha começa plana no "
    "seu primeiro mês do período. Uma única escala de profundidade para todo o quadro: um ativo "
    "que nunca caiu de fato é uma linha reta, e essa retidão é o que a linha diz.",

    "Měsíčně a s úpravou — dividendy a štěpení započítány — a každý řádek startuje rovně ve "
    "svém prvním měsíci období. Jedna stupnice hloubky pro celou tabuli: nástroj, který "
    "opravdu neklesl, je rovná čára, a ta rovnost je přesně to, co řádek říká.",

    "Aylık ve düzeltilmiş — temettüler ve bölünmeler dahil — ve her satır kendi ilk ayında düz "
    "başlar. Tüm tablo için tek derinlik ölçeği: gerçekten düşmeyen bir varlık düz bir "
    "çizgidir ve o düzlük satırın söylediği şeydir.",

    "Ежемесячно и с поправкой — дивиденды и сплиты возвращены — и каждая строка начинается ровно "
    "в своём первом месяце диапазона. Одна шкала глубины на всю доску: инструмент, который "
    "по-настоящему не падал, — это прямая линия, и эта прямота и есть то, что строка говорит.",

    "月次・調整済み（配当と分割を戻し込み）、各行は区間内の自分の最初の月から水平に始まる。"
    "深さの目盛りは盤面全体で一つ——本当は下落していない資産は平らな線になり、その平らさこそが"
    "その行の主張である。",

    "월간·조정 기준(배당과 분할 반영)이며 각 행은 구간 내 자신의 첫 달에서 수평으로 시작한다. "
    "깊이 눈금은 보드 전체에 하나뿐—실제로 하락하지 않은 자산은 평평한 선이 되고, 그 평평함이 "
    "바로 그 행의 말이다.",

    "月線、已復原（股息與份額折算都還原），每行從自己在區間裡的第一個月起算為零。整塊板共用一把"
    "深度尺：從來沒真正跌過的那一行就是一條平線——這條平線正是它要說的話。",

    "月线、已复原（股息与份额折算都还原），每行从自己在区间里的第一个月起算为零。整块板共用一把"
    "深度尺：从来没真正跌过的那一行就是一条平线——这条平线正是它要说的话。",
]

# 六个占位符：档数、月数、最深那档的名字与深度、修复用了多久、离自己高点最近的那档。
FETCHED = [
    "Fetched {0} holdings · {1} months · deepest: {2} {3} ({4}) · closest to its high: {5}",
    "{0} Anlagen geladen · {1} Monate · am tiefsten: {2} {3} ({4}) · dem eigenen Hoch am nächsten: {5}",
    "Obtenidas {0} inversiones · {1} meses · la más profunda: {2} {3} ({4}) · la más cerca de su máximo: {5}",
    "{0} supports récupérés · {1} mois · le plus profond : {2} {3} ({4}) · le plus proche de son sommet : {5}",
    "Recuperati {0} strumenti · {1} mesi · il più profondo: {2} {3} ({4}) · il più vicino al proprio massimo: {5}",
    "Pobrano {0} instrumentów · {1} miesięcy · najgłębszy: {2} {3} ({4}) · najbliżej własnego szczytu: {5}",
    "Obtidos {0} ativos · {1} meses · o mais profundo: {2} {3} ({4}) · o mais perto da própria máxima: {5}",
    "Načteno {0} nástrojů · {1} měsíců · nejhlubší: {2} {3} ({4}) · nejblíže vlastnímu maximu: {5}",
    "{0} varlık alındı · {1} ay · en derin: {2} {3} ({4}) · kendi zirvesine en yakın: {5}",
    "Получено инструментов: {0} · месяцев: {1} · самый глубокий: {2} {3} ({4}) · ближе всех к своему максимуму: {5}",
    "{0} 銘柄を取得 · {1} か月 · 最深: {2} {3}（{4}） · 高値に最も近い: {5}",
    "{0}개 종목 조회 · {1}개월 · 가장 깊음: {2} {3}({4}) · 고점에 가장 가까움: {5}",
    "取到 {0} 檔 · {1} 個月 · 最深：{2} {3}（{4}） · 離自己高點最近：{5}",
    "取到 {0} 档 · {1} 个月 · 最深：{2} {3}（{4}） · 离自己高点最近：{5}",
]

TOO_FEW = [
    "Not enough months in that range to measure a drawdown — pick a longer one.",
    "Zu wenige Monate in diesem Zeitraum für einen Rücksetzer – wählen Sie einen längeren.",
    "No hay suficientes meses en ese periodo para medir una caída: elija uno más largo.",
    "Pas assez de mois dans cette période pour mesurer un recul — choisissez une période plus longue.",
    "Non abbastanza mesi in questo intervallo per misurare un ribasso: sceglierne uno più lungo.",
    "Za mało miesięcy w tym okresie, by zmierzyć obsunięcie — wybierz dłuższy.",
    "Meses insuficientes nesse período para medir uma queda — escolha um mais longo.",
    "V tomto období je příliš málo měsíců na měření poklesu — zvolte delší.",
    "Bir düşüşü ölçmek için bu aralıkta yeterince ay yok — daha uzun bir aralık seçin.",
    "В этом диапазоне слишком мало месяцев, чтобы измерить просадку, — выберите подлиннее.",
    "この期間はドローダウンを測るのに月数が足りません——もっと長い期間を選んでください。",
    "낙폭을 측정하기에 이 구간의 개월 수가 부족합니다—더 긴 구간을 고르세요.",
    "這個區間的月份不夠，量不出回撤——請選長一點的區間。",
    "这个区间的月份不够，量不出回撤——请选长一点的区间。",
]

# 行右侧那三行小字。要短：右栏只有 210 个基准像素宽。
DEEPEST = [
    "low {0}", "Tief {0}", "mín. {0}", "plus bas {0}", "min {0}", "dołek {0}",
    "mín. {0}", "minimum {0}", "dip {0}", "минимум {0}", "最安 {0}", "저점 {0}",
    "最深 {0}", "最深 {0}",
]

HEALED = [
    "{0} mo back", "{0} Mon. bis zurück", "{0} meses para volver", "{0} mois pour revenir",
    "{0} mesi per tornare", "{0} mies. powrotu", "{0} meses para voltar", "{0} měs. zpět",
    "{0} ayda döndü", "{0} мес. до возврата", "{0} か月で回復", "{0}개월 회복",
    "{0} 個月修復", "{0} 个月修复",
]

NOT_HEALED = [
    "still under", "noch unter", "aún por debajo", "pas encore revenu", "ancora sotto",
    "wciąż poniżej", "ainda abaixo", "stále pod", "hâlâ altında", "ещё не вернулся",
    "未回復", "미회복", "至今未修復", "至今未修复",
]

NEVER_FELL = [
    "never fell", "nie gefallen", "nunca cayó", "jamais baissé", "mai sceso",
    "nigdy nie spadł", "nunca caiu", "neklesl", "hiç düşmedi", "не падал",
    "下落なし", "하락 없음", "未回撤", "未回撤",
]

ROWS = [
    # `.Content`, not `.Text`: a NavigationViewItem is a ContentControl, and the x:Uid loader
    # asks for the property the type actually has. Written as `.Text` the app does not start.
    ("NavDrawdown.Content", NAV),
    ("DrawdownPageTitle.Text", NAV),
    ("DrawdownStageTitle", NAV),
    ("DrawdownPageSubtitle.Text", SUBTITLE),
    ("DrawdownList.Header", LIST),
    ("DrawdownNote.Text", NOTE),
    ("DrawdownMethodNote.Text", METHOD),
    ("DrawdownFetched", FETCHED),
    ("DrawdownTooFew", TOO_FEW),
    ("DrawdownDeepest", DEEPEST),
    ("DrawdownHealed", HEALED),
    ("DrawdownNotHealed", NOT_HEALED),
    ("DrawdownNeverFell", NEVER_FELL),
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

        for key, values in ROWS:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in ROWS:
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
