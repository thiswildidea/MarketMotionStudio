# -*- coding: utf-8 -*-
r"""把「极端交易日」这一页的 resw 键注入 14 份 Resources.resw。

第十一个页面的文案：导航名、标题、副标题、卡片说明、口径说明、标的下拉的标题、
状态行、表头的计数词、以及「区间太短」那条错误。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`——
`port-ahpremium-resw.py` 里 `AhPremiumFetched` 就是在这里栽过：第一列写成了中文，
英文界面于是显示一整行中文状态。加键时先确认第一列是英文。

用法：python tools\port-extremedays-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 导航项与「无数据」时舞台上的标题，各语言都短。
NAV = [
    "Extreme days", "Extreme Tage", "Días extremos", "Jours extrêmes", "Giorni estremi",
    "Ekstremalne dni", "Dias extremos", "Extrémní dny", "Aşırı günler",
    "Экстремальные дни", "極端な日", "극단의 날", "極端交易日", "极端交易日",
]

PAGE = [
    # `.Content`, not `.Text`: a NavigationViewItem is a ContentControl, and the x:Uid loader
    # asks for the property the type actually has. Written as `.Text` the app did not start —
    # MainWindow's InitializeComponent threw "Unable to resolve property 'Text' for Uid
    # 'NavExtremeDays'", which is a crash on launch, not a blank label.
    ("NavExtremeDays.Content", NAV),

    ("ExtremeDaysPageTitle.Text", [
        "Extreme trading days", "Extreme Handelstage", "Días extremos de negociación",
        "Jours de trading extrêmes", "Giornate di trading estreme", "Ekstremalne sesje",
        "Dias extremos de negociação", "Extrémní obchodní dny", "Aşırı işlem günleri",
        "Экстремальные торговые дни", "極端な取引日", "극단의 거래일",
        "極端交易日", "极端交易日"]),

    ("ExtremeDaysPageSubtitle.Text", [
        "One instrument's largest single-day moves, ranked by size. The board fills in as the "
        "years pass.",
        "Die größten Tagesbewegungen eines Instruments, nach Größe gereiht. Das Tableau füllt "
        "sich, während die Jahre vergehen.",
        "Los mayores movimientos en un solo día de un instrumento, ordenados por magnitud. El "
        "tablero se llena a medida que pasan los años.",
        "Les plus grands mouvements d'une seule séance d'un instrument, classés par ampleur. Le "
        "tableau se remplit à mesure que les années passent.",
        "I maggiori movimenti di una sola seduta di uno strumento, ordinati per ampiezza. La "
        "classifica si riempie con il passare degli anni.",
        "Największe jednosesyjne ruchy jednego instrumentu, uszeregowane według wielkości. "
        "Tablica wypełnia się wraz z upływem lat.",
        "Os maiores movimentos de um único dia de um instrumento, ordenados por tamanho. O quadro "
        "se preenche à medida que os anos passam.",
        "Největší jednodenní pohyby jednoho nástroje, seřazené podle velikosti. Tabulka se "
        "zaplňuje, jak léta plynou.",
        "Bir enstrümanın en büyük tek günlük hareketleri, büyüklüğe göre sıralanır. Tablo yıllar "
        "geçtikçe dolar.",
        "Самые большие движения одного инструмента за один день, упорядоченные по величине. "
        "Таблица заполняется по мере того, как идут годы.",
        "ある銘柄の最も大きな一日の値動きを、大きさ順に並べたものです。年が進むにつれて表が"
        "埋まっていきます。",
        "하나의 종목에서 가장 컸던 하루 등락을 크기순으로 세운 표입니다. 세월이 흐르며 표가 "
        "채워집니다.",
        "單一標的史上最大的單日漲跌幅，按幅度排序。隨著年份推進，榜單一格一格填滿。",
        "单一标的史上最大的单日涨跌幅，按幅度排序。随着年份推进，榜单一格一格填满。"]),

    ("ExtremeDaysStageTitle", NAV),

    ("ExtremeDaysCount", [
        "One instrument, every trading day in the range. The frame draws the {0} largest moves, "
        "red for a rise and green for a fall.",
        "Ein Instrument, jeder Handelstag des Zeitraums. Das Bild zeichnet die {0} größten "
        "Bewegungen, rot für ein Plus und grün für ein Minus.",
        "Un instrumento, cada día de negociación del periodo. El fotograma dibuja los {0} "
        "movimientos más grandes, rojo para una subida y verde para una bajada.",
        "Un instrument, chaque jour de cotation de la période. L'image trace les {0} plus grands "
        "mouvements, rouge pour une hausse et vert pour une baisse.",
        "Uno strumento, ogni giorno di negoziazione del periodo. Il fotogramma disegna i {0} "
        "movimenti più grandi, rosso per un rialzo e verde per un ribasso.",
        "Jeden instrument, każdy dzień sesyjny okresu. Kadr rysuje {0} największych ruchów, "
        "czerwony dla wzrostu i zielony dla spadku.",
        "Um instrumento, cada dia de negociação do período. O quadro desenha os {0} maiores "
        "movimentos, vermelho para alta e verde para baixa.",
        "Jeden nástroj, každý obchodní den období. Snímek kreslí {0} největších pohybů, červeně "
        "pro růst a zeleně pro pokles.",
        "Bir enstrüman, dönemdeki her işlem günü. Kare en büyük {0} hareketi çizer: yükseliş "
        "kırmızı, düşüş yeşil.",
        "Один инструмент, каждый торговый день периода. Кадр рисует {0} крупнейших движений: "
        "рост красным, падение зелёным.",
        "銘柄は一つ、期間内のすべての取引日。画面には最も大きな {0} 日の値動きを描きます。"
        "上昇は赤、下落は緑です。",
        "종목은 하나, 기간 안의 모든 거래일. 화면에는 가장 컸던 {0}일의 움직임을 그립니다. "
        "오름은 빨강, 내림은 초록입니다.",
        "一個標的，區間內每一個交易日。畫面畫出幅度最大的 {0} 天，漲是紅、跌是綠。",
        "一个标的，区间内每一个交易日。画面画出幅度最大的 {0} 天，涨是红、跌是绿。"]),

    ("ExtremeDaysMethodNote.Text", [
        "Move = the change in the adjusted close from the previous trading day, in per cent. "
        "Ranked by size and not by sign, so a fall stands beside a rise of the same size. A day "
        "is ranked only once it has happened, which is why the board fills in.",
        "Bewegung = die Veränderung des bereinigten Schlusskurses gegenüber dem vorherigen "
        "Handelstag, in Prozent. Nach Größe gereiht, nicht nach Vorzeichen, sodass ein Minus "
        "neben einem gleich großen Plus steht. Ein Tag zählt erst, wenn er vergangen ist — "
        "darum füllt sich das Tableau.",
        "Movimiento = la variación del cierre ajustado respecto al día de negociación anterior, "
        "en porcentaje. Se ordena por magnitud y no por signo, así que una bajada se sitúa "
        "junto a una subida del mismo tamaño. Un día cuenta solo cuando ya ha ocurrido, y por "
        "eso el tablero se llena.",
        "Mouvement = la variation du cours de clôture ajusté par rapport au jour de cotation "
        "précédent, en pourcentage. Classé par ampleur et non par signe, de sorte qu'une baisse "
        "se place à côté d'une hausse de même taille. Un jour n'est classé qu'une fois arrivé, "
        "d'où le tableau qui se remplit.",
        "Movimento = la variazione del close rettificato rispetto al giorno di negoziazione "
        "precedente, in percentuale. Ordinato per ampiezza e non per segno, così una discesa "
        "sta accanto a un rialzo della stessa misura. Un giorno entra in classifica solo dopo "
        "che è avvenuto, ed è per questo che il quadro si riempie.",
        "Ruch = zmiana skorygowanej ceny zamknięcia względem poprzedniego dnia sesyjnego, "
        "w procentach. Uporządkowane według wielkości, nie według znaku, więc spadek stoi "
        "obok równie dużego wzrostu. Dzień liczy się dopiero, gdy się wydarzył — dlatego "
        "tablica się wypełnia.",
        "Movimento = a variação do fechamento ajustado em relação ao dia de negociação anterior, "
        "em porcentagem. Ordenado por tamanho e não por sinal, então uma queda fica ao lado de "
        "uma alta do mesmo tamanho. Um dia só entra na classificação depois de acontecer, e é "
        "por isso que o quadro se preenche.",
        "Pohyb = změna upravené závěrečné ceny oproti předchozímu obchodnímu dni, v procentech. "
        "Řazeno podle velikosti, ne podle znaménka, takže pokles stojí vedle stejně velkého "
        "růstu. Den se počítá, až když nastal — proto se tabulka zaplňuje.",
        "Hareket = önceki işlem gününe göre düzeltilmiş kapanışın değişimi, yüzde olarak. "
        "İşarete göre değil büyüklüğe göre sıralanır, böylece bir düşüş aynı büyüklükteki bir "
        "yükselişin yanında durur. Bir gün ancak gerçekleştikten sonra sıralamaya girer; tablo "
        "bu yüzden dolar.",
        "Движение = изменение скорректированного закрытия относительно предыдущего торгового "
        "дня, в процентах. Ранжируется по величине, а не по знаку, поэтому падение стоит рядом "
        "с равным по величине ростом. День попадает в рейтинг только когда он уже произошёл — "
        "поэтому таблица заполняется.",
        "値動き = 前の取引日に比べた調整済み終値の変化、単位はパーセント。符号ではなく大きさで"
        "並べるので、下落は同じ大きさの上昇の隣に並びます。その日が実際に来て初めて順位に入る"
        "ため、表は少しずつ埋まります。",
        "움직임 = 이전 거래일 대비 조정 종가의 변화, 단위는 퍼센트. 부호가 아니라 크기로 "
        "세우므로 하락은 같은 크기의 상승 옆에 놓입니다. 그날이 실제로 지나야 순위에 오르기 "
        "때문에 표는 조금씩 채워집니다.",
        "漲跌幅 = 相對於上一個交易日的複權收盤價變化，單位是百分比。按幅度排序而不是按正負，"
        "所以下跌會和同等幅度的上漲並排。只有已經發生的日子才進榜，榜單因此是逐步填滿的。",
        "涨跌幅 = 相对于上一个交易日的复权收盘价变化，单位是百分比。按幅度排序而不是按正负，"
        "所以下跌会和同等幅度的上涨并排。只有已经发生的日子才进榜，榜单因此是逐步填满的。"]),

    ("ExtremeDaysInstrument.Header", [
        "Instrument", "Instrument", "Instrumento", "Instrument", "Strumento", "Instrument",
        "Instrumento", "Nástroj", "Enstrüman", "Инструмент", "銘柄", "종목", "標的", "标的"]),

    ("ExtremeDaysUnitCandidates", [
        "candidate days", "Kandidatentage", "días candidatos", "jours candidats",
        "giorni candidati", "dni kandydujących", "dias candidatos", "kandidátních dnů",
        "aday gün", "дней-кандидатов", "候補日", "후보일", "個候選日", "个候选日"]),

    ("ExtremeDaysFetched", [
        "{0} candidate days · {1} trading days · biggest {2} {3} · smallest on the board {4} {5}",
        "{0} Kandidatentage · {1} Handelstage · größte {2} {3} · kleinste im Bild {4} {5}",
        "{0} días candidatos · {1} días de negociación · el mayor {2} {3} · el menor del cuadro "
        "{4} {5}",
        "{0} jours candidats · {1} jours de cotation · le plus grand {2} {3} · le plus petit du "
        "tableau {4} {5}",
        "{0} giorni candidati · {1} giorni di negoziazione · il più grande {2} {3} · il più "
        "piccolo nel quadro {4} {5}",
        "{0} dni kandydujących · {1} dni sesyjnych · największy {2} {3} · najmniejszy w kadrze "
        "{4} {5}",
        "{0} dias candidatos · {1} dias de negociação · maior {2} {3} · menor no quadro {4} {5}",
        "{0} kandidátních dnů · {1} obchodních dnů · největší {2} {3} · nejmenší v obraze {4} {5}",
        "{0} aday gün · {1} işlem günü · en büyük {2} {3} · karedeki en küçük {4} {5}",
        "{0} дней-кандидатов · {1} торговых дней · самый большой {2} {3} · самый маленький в "
        "кадре {4} {5}",
        "候補 {0} 日 · 取引日 {1} 日 · 最大 {2} {3} · 画面内で最小 {4} {5}",
        "후보 {0}일 · 거래일 {1}일 · 최대 {2} {3} · 화면 안 최소 {4} {5}",
        "{0} 個候選日 · {1} 個交易日 · 最大 {2} {3} · 榜尾 {4} {5}",
        "{0} 个候选日 · {1} 个交易日 · 最大 {2} {3} · 榜尾 {4} {5}"]),

    # Its own "longest" label rather than the plan page's: that one says thirteen years because
    # of its own limit, and this page's limit is the walk's — twenty requests of about 640 daily
    # bars, which is thirty-five years. A label borrowed across pages is a label that lies on
    # one of them.
    ("ExtremeDaysRangeMax", [
        "Longest (about 35 years)", "Längste (etwa 35 Jahre)", "Más largo (unos 35 años)",
        "Le plus long (environ 35 ans)", "Il più lungo (circa 35 anni)",
        "Najdłuższy (około 35 lat)", "Mais longo (cerca de 35 anos)", "Nejdelší (asi 35 let)",
        "En uzun (yaklaşık 35 yıl)", "Самый длинный (около 35 лет)", "最長（約 35 年）",
        "최장(약 35년)", "最長（約 35 年）", "最长（约 35 年）"]),

    ("ExtremeDaysTooFew", [
        "Not enough trading days in this range. Try a longer one.",
        "Zu wenig Handelstage in diesem Zeitraum. Versuchen Sie einen längeren.",
        "No hay suficientes días de negociación en este periodo. Pruebe uno más largo.",
        "Pas assez de jours de cotation dans cette période. Essayez plus long.",
        "Troppo pochi giorni di negoziazione in questo periodo. Prova un periodo più lungo.",
        "Za mało dni sesyjnych w tym okresie. Spróbuj dłuższego.",
        "Poucos dias de negociação neste período. Tente um período mais longo.",
        "V tomto období je příliš málo obchodních dnů. Zkuste delší.",
        "Bu dönemde yeterli işlem günü yok. Daha uzun bir dönem deneyin.",
        "В этом периоде слишком мало торговых дней. Возьмите период длиннее.",
        "この期間の取引日が少なすぎます。もっと長い期間をお試しください。",
        "이 기간의 거래일이 너무 적습니다. 더 긴 기간을 선택하세요.",
        "這段區間的交易日太少，換長一點的區間試試。",
        "这段区间的交易日太少，换长一点的区间试试。"]),
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

        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")

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
