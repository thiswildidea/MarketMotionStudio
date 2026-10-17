# -*- coding: utf-8 -*-
r"""把「加密货币月度收益」页用到的 resw 键注入 14 份 Resources.resw。

这一页是股票收益矩阵（MonthlyMatrixPage）的加密市场读法，渲染器与装配代码都共用，
但**取数与边界是币市自己的**，所以界面文字单独一族键，不与 Matrix* 共用名字：

1. A 股那页的状态行说「月K」，加密没有月K接口 —— 月份是从日线折叠出来的，措辞照实说。
2. 两条边界要在页面上说清：**进行中的月不算**（半个月的涨跌不能冒充整月）；
   **日线源端约十年封顶**，所以年数选择只到十年为止（备源只有一年）。
3. 格子颜色是涨红跌绿（MatrixRenderer 自己的约定），副标题里点一句。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配（见 port-crypto-caps-resw.py）。

用法：python tools\port-crypto-matrix-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 导航 / 页头 -----------------------------------------------------------------
#
# 带 crypto：导航里它的股票孪生项（收益矩阵）在别的市场分组里，名字只写「月度收益」的话，
# 两个市场的读者都要靠位置猜。照涨跌日历三页的先例，导航词自带市场名。

NAV_MATRIX = [
    "Crypto Monthly Returns", "Krypto-Monatsrenditen", "Rendimientos mensuales cripto",
    "Rendements mensuels crypto", "Rendimenti mensili crypto",
    "Miesięczne stopy zwrotu krypto", "Retornos mensais cripto",
    "Měsíční výnosy krypto", "Kripto aylık getiriler",
    "Месячная доходность крипто", "暗号資産の月次リターン",
    "크립토 월간 수익률", "加密貨幣月度收益", "加密货币月度收益",
]

MATRIX_TITLE = NAV_MATRIX

MATRIX_SUBTITLE = [
    "One coin's month-by-month moves as a year × month grid, red for rises and green for falls. Each month is its last daily close against the month before's, folded out of the daily bars; the last column is the whole year compounded.",
    "Die Bewegungen einer Münze Monat für Monat als Jahr-×-Monat-Raster, rot für Steigungen und grün für Stürze. Jeder Monat ist sein letzter Tagesschluss gegen den des Vormonats, aus den Tageskursen gefaltet; die letzte Spalte ist das ganze Jahr aufgezinst.",
    "Los movimientos mes a mes de una moneda en una cuadrícula de año × mes, rojo para las subidas y verde para las bajadas. Cada mes es su último cierre diario contra el del mes anterior, plegado de los datos diarios; la última columna es el año completo compuesto.",
    "Les mouvements mois par mois d'une cryptomonnaie en une grille année × mois, rouge pour les hausses et vert pour les baisses. Chaque mois est son dernier cours quotidien face à celui du mois précédent, replié depuis les cours journaliers ; la dernière colonne est l'année entière composée.",
    "I movimenti mese per mese di una moneta in una griglia anno × mese, rosso per i rialzi e verde per i ribassi. Ogni mese è la sua ultima chiusura giornaliera contro quella del mese precedente, ripiegata dai dati giornalieri; l'ultima colonna è l'intero anno composto.",
    "Zmiany monety miesiąc po miesiącu jako siatka rok × miesiąc, czerwony dla wzrostów, zielony dla spadków. Każdy miesiąc to jego ostatni kurs dzienny wobec kursu z poprzedniego miesiąca, złożony z kursów dziennych; ostatnia kolumna to cały rok skumulowany.",
    "Os movimentos mês a mês de uma moeda em uma grade de ano × mês, vermelho para altas e verde para baixas. Cada mês é seu último fechamento diário contra o do mês anterior, dobrado dos dados diários; a última coluna é o ano inteiro composto.",
    "Měsíční pohyby jedné mince jako mřížka rok × měsíc, červená pro růsty, zelená pro poklesy. Každý měsíc je jeho poslední denní kurz proti kurzu z předchozího měsíce, složený z denních kurzů; poslední sloupec je celý rok složený.",
    "Bir coin'in ay ay hareketleri, yıl × ay ızgarası olarak; yükselişler kırmızı, düşüşler yeşil. Her ay, önceki ayın kapanışına karşı kendi son günlük kapanışıdır ve günlük verilerden katlanır; son sütun bileşik edilmiş bütün yıldır.",
    "Помесячная динамика монеты в виде сетки «год × месяц», красный — рост, зелёный — падение. Каждый месяц — это его последний дневной курс против курса предыдущего месяца, сложенный из дневных данных; последний столбец — весь год с реинвестированием.",
    "ある暗号資産の月ごとの動きを「年 × 月」の格子で示します。上が赤、下が緑。各月は前月比の月末終値で、日足から折り畳んだもの。右端の列は一年を複利で合算した値です。",
    "한 코인의 월별 움직임을 연도 × 월 격자로 보여줍니다. 상승은 빨강, 하락은 초록. 각 월은 전월 대비 그 달의 마지막 일간 종가이며, 일봉에서 접어 만든 것입니다. 마지막 열은 1년 전체를 복리로 합산한 값입니다.",
    "把某個幣種逐月的漲跌畫成年 × 月的格子，漲紅跌綠。每個月是它最後一天的收盤對上一個月的比值，由日線折疊而成；最右一欄是全年複利合計。",
    "把某个币种逐月的涨跌画成年 × 月的格子，涨红跌绿。每个月是它最后一天的收盘对上一个月的比值，由日线折叠而成；最右一栏是全年复利合计。",
]

# ---- 说明与状态行 ----------------------------------------------------------------

MATRIX_NOTE = [
    "A month counts only when it is over: the month being walked is not on the grid. The daily source holds about ten years, which is where the year list stops, and the fallback source carries a single year.",
    "Ein Monat zählt erst, wenn er vorbei ist: der laufende Monat steht nicht im Raster. Die Tagesquelle umfasst etwa zehn Jahre, dort endet die Jahresliste, und die Ausweichquelle trägt ein einziges Jahr.",
    "Un mes cuenta solo cuando terminó: el mes en curso no está en la cuadrícula. La fuente diaria cubre unos diez años, y ahí se detiene la lista de años; la fuente de respaldo lleva un solo año.",
    "Un mois ne compte que lorsqu'il est terminé : le mois en cours n'est pas sur la grille. La source journalière couvre une dizaine d'années, et c'est là que la liste des années s'arrête ; la source de secours ne porte qu'une année.",
    "Un mese conta solo quando è finito: il mese in corso non è sulla griglia. La fonte giornaliera copre circa dieci anni, ed è lì che l'elenco degli anni si ferma; la fonte di riserva porta un solo anno.",
    "Miesiąc liczy się dopiero, gdy się skończył: bieżącego miesiąca nie ma na siatce. Źródło dzienne obejmuje około dziesięć lat i tam kończy się lista lat; źródło zapasowe niesie tylko jeden rok.",
    "Um mês só conta quando terminou: o mês em andamento não está na grade. A fonte diária cobre cerca de dez anos, e é aí que a lista de anos para; a fonte de reserva carrega um único ano.",
    "Měsíc se počítá, až skončil: běžící měsíc v mřížce není. Denní zdroj pokrývá zhruba deset let, tam seznam let končí; záložní zdroj nese jediný rok.",
    "Bir ay ancak bittiğinde sayılır: içinde bulunduğumuz ay ızgarada yok. Günlük kaynak yaklaşık on yıl tutar, yıl listesi orada biter; yedek kaynak yalnızca bir yıl taşır.",
    "Месяц считается, только когда он закончился: текущего месяца на сетке нет. Дневной источник хранит около десяти лет — на этом список годов и заканчивается; резервный источник несёт лишь один год.",
    "月は終わってから数えます。進行中の月は格子に載りません。日足の取得元はおよそ十年を持っており、年の選択肢はそこまで。予備の取得元は一年分だけです。",
    "월은 끝나야 셉니다. 진행 중인 달은 격자에 없습니다. 일봉 출처는 약 10년을 갖고 있어 연도 목록이 거기까지이며, 예비 출처는 1년치만 갖고 있습니다.",
    "沒走完的月不算：進行中的那個月不會出現在格子上。日線源端約有十年，年數就到十年為止；備用源端只有一年。",
    "没走完的月不算：进行中的那个月不会出现在格子上。日线源端约有十年，年数就到十年为止；备用源端只有一年。",
]

MATRIX_FETCHING = [
    "Fetching {0}'s daily bars, folding into months …",
    "Tageskurse von {0} werden geholt und zu Monaten gefaltet …",
    "Obteniendo los datos diarios de {0}, plegándolos en meses …",
    "Récupération des cours journaliers de {0}, repli en mois …",
    "Recupero dei dati giornalieri di {0}, ripiegati in mesi …",
    "Pobieranie dziennych kursów {0}, składanie w miesiące …",
    "Obtendo os dados diários de {0}, dobrando em meses …",
    "Načítají se denní kurzy {0} a skládají do měsíců …",
    "{0} günlük verileri alınıyor, aylara katlanıyor …",
    "Получение дневных данных {0}, свёртка в месяцы …",
    "{0} の日足を取得し、月に折り畳んでいます …",
    "{0}의 일봉을 가져와 월로 접는 중 …",
    "正在取 {0} 的日線，折成月 …",
    "正在取 {0} 的日线，折成月 …",
]

ROWS = [
    ("NavCryptoMatrix.Content", NAV_MATRIX),
    ("CryptoMatrixPageTitle.Text", MATRIX_TITLE),
    ("CryptoMatrixPageSubtitle.Text", MATRIX_SUBTITLE),
    ("CryptoMatrixNote.Text", MATRIX_NOTE),
    ("CryptoMatrixFetching", MATRIX_FETCHING),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project
    file rather than the string that caused it.
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
        for key in [k for k, _ in ROWS]:
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
