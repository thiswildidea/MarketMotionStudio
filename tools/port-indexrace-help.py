# -*- coding: utf-8 -*-
r"""把「指数长跑」一章插进 14 份帮助文档。

位置**按章节序号**定，不按标题文字：新章插在「汇率走廊」之后、「收益矩阵」之前，
因为导航里这三项挨着（极端交易日 → 汇率走廊 → 指数长跑）。14 份文档的章节数与顺序
必须相同，由 verify 脚本另行检查。

文件是 UTF-8 **带 BOM** + LF：`read_bytes().decode('utf-8-sig')` 读，写回时自己补 BOM。
`utf-8-sig` 只吃掉一个 BOM，文件里若已经叠了两个，要用 `lstrip('\ufeff')` 兜住。

幂等：标题已存在就整章重写。**改页面行为就要回来改这里的 BODIES** —— 市值榜那一章
曾经在榜单改了两次之后仍写着旧理由，见 `port-marketcap-help.py` 的说明。

用法：python tools\port-indexrace-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 插在第 10 章「汇率走廊」之后（0 基下标 9），第 11 章「收益矩阵」之前。
AFTER = 9

TITLES = {
    "zh-Hans": "指数长跑",
    "zh-Hant": "指數長跑",
    "en-US": "Index race",
    "ja": "指数レース",
    "ko": "지수 레이스",
    "de": "Index-Rennen",
    "fr": "Course des indices",
    "it": "Corsa degli indici",
    "es": "Carrera de índices",
    "pt-BR": "Corrida de índices",
    "pl": "Wyścig indeksów",
    "cs": "Závod indexů",
    "ru": "Гонка индексов",
    "tr": "Endeks yarışı",
}

BODIES = {
    "zh-Hans": """一个指数一行，行是**这个指数从自己在区间里的第一个月起涨了多少**，不是它的点位。上证指数的
3,800 和标普 500 的 5,700 不在同一把尺上，画点位等于在比谁起点高。

- **晚来的指数在它上场之前不在榜上。** 标普 500 能追溯到 1950 年，道琼斯只到 2009 年，恒生科技
  指数 2020 年才有。它缺席，不是趴在 0.00%——那样会被排在每一个下跌过的指数之上，读出来是
  「这个市场什么都没发生」。
- **月线，不调整。** 指数不派息，但真正的原因是另一条：调整是把一条序列重新定基，两条各自定基的
  序列并排放在一起并不能比。取数走的是 AH 页那条不复权的路径。
- **这一页不看市场设置**：它同时读三个市场，切换市场不影响它。可以只看 A 股、只看港股、只看美股，
  也可以十二个一起看。
- 区间最长那档受数据源月线上限限制（430 根，约三十五年）；不足 12 个月会拒绝取数——那是一场
  冲刺，不是长跑。
""",
    "zh-Hant": """一個指數一行，行是**這個指數從自己在區間裡的第一個月起漲了多少**，不是它的點位。上證指數的
3,800 和標普 500 的 5,700 不在同一把尺上，畫點位等於在比誰起點高。

- **晚來的指數在它上場之前不在榜上。** 標普 500 能追溯到 1950 年，道瓊斯只到 2009 年，恆生科技
  指數 2020 年才有。它缺席，不是趴在 0.00%——那樣會被排在每一個下跌過的指數之上，讀出來是
  「這個市場什麼都沒發生」。
- **月線，不調整。** 指數不派息，但真正的原因是另一條：調整是把一條序列重新定基，兩條各自定基的
  序列並排放在一起並不能比。取數走的是 AH 頁那條不復權的路徑。
- **這一頁不看市場設定**：它同時讀三個市場，切換市場不影響它。可以只看 A 股、只看港股、只看美股，
  也可以十二個一起看。
- 區間最長那檔受資料源月線上限限制（430 根，約三十五年）；不足 12 個月會拒絕取數——那是一場
  衝刺，不是長跑。
""",
    "en-US": """One row per index, and the row is **how far that index has come since its own first month in the
range** — not its level. 3,800 on the Shanghai Composite and 5,700 on the S&P 500 are not two points
on one scale, and drawing levels would be a board about where each index happened to start counting.

- **An index that arrives late is not on the board until it arrives.** The S&P reaches back to 1950,
  the Dow only to 2009, and the Hang Seng Tech index starts in 2020. It is absent, not parked at
  0.00% — parked there it would rank above every index that was ever down, and read as a market in
  which nothing happened.
- **Monthly bars, unadjusted.** An index pays no dividend, but the reason is the other one: an
  adjustment rebases a series, and two rebased series side by side are not comparable. The page takes
  the same raw path through the source that the A+H page takes.
- **The market setting does not govern this page**: it reads three markets at once, and switching the
  market does not change it. You can take the mainland's six, Hong Kong's three, New York's three, or
  all twelve.
- The longest span is held down by the source's monthly ceiling of 430 bars, about thirty-five years;
  a range shorter than twelve months is refused — that is a sprint, not a long run.
""",
    "ja": """指数ごとに1行、行は**その指数が区間内の自分の最初の月からどれだけ進んだか**です。水準では
ありません。上海総合の3,800とS&P 500の5,700は同じ物差しの上にありません。水準を描けば、それは
どの指数が高い場所から数え始めたかという話になります。

- **後から来る指数は、来るまでボードに出ません。** S&Pは1950年まで、ダウは2009年まで、ハンセン
  テック指数は2020年からです。0.00%に置かれるのではなく、いないのです——0.00%に置けば今まで
  下落したどの指数より上に並び、「この市場では何も起きなかった」と読まれます。
- **月足、調整なし。** 指数は配当を払いませんが、理由は別にあります。調整は系列の基準を付け替える
  ことであり、付け替えた二つの系列は並べても比較できません。取数はAHページと同じ、調整なしの
  経路です。
- **このページは市場設定に従いません**：三つの市場を同時に読み、市場を切り替えても変わりません。
  本土の6本、香港の3本、ニューヨークの3本、あるいは12本すべてを選べます。
- 最長の区間はデータ源の月足の上限（430本、約35年）で決まります。12か月未満の区間は拒否されます
  ——それは長距離ではなく短距離です。
""",
    "ko": """지수마다 한 줄, 줄은 **그 지수가 구간 내 자기 첫 달부터 얼마나 왔는지**입니다. 수준이
아닙니다. 상하이종합의 3,800과 S&P 500의 5,700은 같은 자 위의 점이 아닙니다. 수준을 그리면
어느 지수가 높은 곳에서 세기 시작했는지를 겨루는 판이 됩니다.

- **늦게 오는 지수는 올 때까지 보드에 없습니다.** S&P는 1950년까지, 다우는 2009년까지, 항셍
  테크 지수는 2020년부터입니다. 0.00%에 놓이는 것이 아니라 없는 것입니다—0.00%에 놓이면
  지금까지 하락했던 모든 지수 위에 서게 되고, '이 시장에서는 아무 일도 없었다'로 읽힙니다.
- **월별 봉, 조정 없음.** 지수는 배당을 하지 않지만 이유는 다릅니다. 조정은 계열의 기준을 다시
  잡는 것이고, 다시 잡은 두 계열은 나란히 놓아도 비교할 수 없습니다. 자료는 AH 페이지와 같은
  조정 없는 경로로 가져옵니다.
- **이 페이지는 시장 설정을 따르지 않습니다**: 세 시장을 동시에 읽으며 시장을 바꿔도 달라지지
  않습니다. 본토 6개, 홍콩 3개, 뉴욕 3개, 또는 열두 개 모두를 볼 수 있습니다.
- 가장 긴 구간은 자료원의 월별 상한(430개, 약 35년)에 묶입니다. 12개월보다 짧은 구간은
  거절됩니다—그것은 장거리가 아니라 단거리입니다.
""",
    "de": """Eine Zeile je Index, und die Zeile ist **wie weit dieser Index seit seinem eigenen ersten Monat
im Zeitraum gekommen ist** — nicht sein Niveau. 3.800 beim Shanghai Composite und 5.700 beim S&P 500
sind keine zwei Punkte auf einer Skala; Niveaus zu zeichnen wäre ein Bild darüber, wo welcher Index
zufällig zu zählen begann.

- **Ein Index, der später kommt, steht erst ab dann auf dem Bild.** Der S&P reicht bis 1950, der Dow
  nur bis 2009, und der Hang-Seng-Tech-Index beginnt 2020. Er fehlt, statt bei 0,00% zu parken — dort
  stünde er über jedem Index, der je gefallen ist, und man läse einen Markt, in dem nichts geschah.
- **Monatskerzen, nicht bereinigt.** Ein Index zahlt keine Dividende, aber der Grund ist der andere:
  eine Bereinigung basiert eine Reihe neu, und zwei neu basierte Reihen nebeneinander sind nicht
  vergleichbar. Die Seite nimmt denselben unbereinigten Weg durch die Quelle wie die A+H-Seite.
- **Die Markteinstellung gilt hier nicht**: die Seite liest drei Märkte zugleich, und ein Wechsel des
  Marktes ändert sie nicht. Zur Wahl stehen die sechs des Festlands, die drei aus Hongkong, die drei
  aus New York oder alle zwölf.
- Die längste Spanne ist durch die Monatsgrenze der Quelle gedeckelt — 430 Kerzen, etwa
  fünfunddreißig Jahre. Weniger als zwölf Monate werden abgelehnt: das ist ein Sprint, kein
  Langstreckenlauf.
""",
    "fr": """Une ligne par indice, et la ligne est **le chemin parcouru par cet indice depuis son propre
premier mois dans la période** — pas son niveau. 3 800 au Shanghai Composite et 5 700 au S&P 500 ne
sont pas deux points d'une même échelle ; dessiner des niveaux ferait un tableau sur l'endroit où
chaque indice a commencé à compter.

- **Un indice qui arrive tard n'est pas sur le tableau avant d'arriver.** Le S&P remonte à 1950, le
  Dow seulement à 2009, et l'indice Hang Seng Tech commence en 2020. Il est absent, il ne stationne
  pas à 0,00 % — à ce niveau il se classerait au-dessus de tout indice jamais baissier, et se lirait
  comme un marché où rien ne s'est passé.
- **Bougies mensuelles, non ajustées.** Un indice ne verse pas de dividende, mais la raison est
  l'autre : un ajustement rebase une série, et deux séries rebasées côte à côte ne sont pas
  comparables. La page prend le même chemin brut dans la source que la page A+H.
- **Le réglage de marché ne gouverne pas cette page** : elle lit trois marchés à la fois, et changer
  de marché ne la change pas. On peut prendre les six du continent, les trois de Hong Kong, les trois
  de New York, ou les douze.
- La période la plus longue est bornée par le plafond mensuel de la source — 430 bougies, environ
  trente-cinq ans ; moins de douze mois est refusé : c'est un sprint, pas une course de fond.
""",
    "it": """Una riga per indice, e la riga è **quanto quell'indice ha percorso dal proprio primo mese
nell'intervallo** — non il suo livello. 3.800 sullo Shanghai Composite e 5.700 sull'S&P 500 non sono
due punti di una stessa scala: disegnare i livelli sarebbe un quadro su dove ogni indice ha iniziato
a contare.

- **Un indice che arriva tardi non è sulla tavola fino al suo arrivo.** L'S&P arriva al 1950, il Dow
  solo al 2009 e l'indice Hang Seng Tech comincia nel 2020. È assente, non parcheggiato a 0,00%: lì
  si classificherebbe sopra ogni indice mai sceso e si leggerebbe come un mercato in cui non è
  successo niente.
- **Candele mensili, non rettificate.** Un indice non paga dividendi, ma la ragione è l'altra: una
  rettifica ribasa una serie, e due serie ribasate affiancate non sono confrontabili. La pagina
  prende lo stesso percorso grezzo nella fonte della pagina A+H.
- **L'impostazione del mercato non governa questa pagina**: legge tre mercati insieme e cambiare
  mercato non la cambia. Si possono prendere le sei della Cina continentale, le tre di Hong Kong, le
  tre di New York, o tutte e dodici.
- Il periodo più lungo è limitato dal tetto mensile della fonte — 430 candele, circa trentacinque
  anni; meno di dodici mesi viene rifiutato: è uno scatto, non una corsa lunga.
""",
    "es": """Una fila por índice, y la fila es **cuánto ha avanzado ese índice desde su propio primer mes en
el periodo** — no su nivel. 3.800 en el Shanghai Composite y 5.700 en el S&P 500 no son dos puntos de
una misma escala: dibujar niveles sería un tablero sobre dónde empezó a contar cada índice.

- **Un índice que llega tarde no está en el tablero hasta que llega.** El S&P llega hasta 1950, el Dow
  solo hasta 2009, y el índice Hang Seng Tech empieza en 2020. Está ausente, no aparcado en el 0,00%
  — ahí se situaría por encima de todo índice que haya caído alguna vez, y se leería como un mercado
  en el que no pasó nada.
- **Velas mensuales, sin ajustar.** Un índice no paga dividendo, pero la razón es la otra: un ajuste
  rebasó una serie, y dos series rebasadas una al lado de la otra no son comparables. La página toma
  el mismo camino en crudo por la fuente que toma la página A+H.
- **El ajuste de mercado no gobierna esta página**: lee tres mercados a la vez, y cambiar de mercado
  no la cambia. Pueden tomarse las seis del continente, las tres de Hong Kong, las tres de Nueva York
  o las doce.
- El periodo más largo está limitado por el techo mensual de la fuente — 430 velas, unos treinta y
  cinco años; menos de doce meses se rechaza: eso es un esprint, no una carrera de fondo.
""",
    "pt-BR": """Uma linha por índice, e a linha é **o quanto aquele índice avançou desde o seu próprio primeiro
mês no período** — não o seu nível. 3.800 no Shanghai Composite e 5.700 no S&P 500 não são dois pontos
de uma mesma escala: desenhar níveis seria um quadro sobre onde cada índice começou a contar.

- **Um índice que chega tarde não está no quadro até chegar.** O S&P chega a 1950, o Dow apenas a
  2009, e o índice Hang Seng Tech começa em 2020. Ele está ausente, não estacionado em 0,00% — aí se
  colocaria acima de todo índice que já caiu e se leria como um mercado em que nada aconteceu.
- **Velas mensais, sem ajuste.** Um índice não paga dividendo, mas a razão é a outra: um ajuste
  rebaseia uma série, e duas séries rebaseadas lado a lado não são comparáveis. A página toma o mesmo
  caminho bruto na fonte que a página A+H.
- **A configuração de mercado não governa esta página**: ela lê três mercados ao mesmo tempo, e mudar
  o mercado não a muda. Pode-se escolher as seis do continente, as três de Hong Kong, as três de Nova
  York ou as doze.
- O período mais longo é limitado pelo teto mensal da fonte — 430 velas, cerca de trinta e cinco anos;
  menos de doze meses é recusado: isso é uma corrida curta, não uma de fundo.
""",
    "pl": """Jeden wiersz na indeks, a wiersz to **jak daleko ten indeks zaszedł od swojego pierwszego
miesiąca w okresie** — nie jego poziom. 3 800 na Shanghai Composite i 5 700 na S&P 500 to nie dwa
punkty na jednej skali; rysowanie poziomów byłoby tablicą o tym, gdzie który indeks zaczął liczyć.

- **Indeks, który przychodzi później, nie ma go na tablicy, dopóki nie przyjdzie.** S&P sięga 1950,
  Dow tylko 2009, a indeks Hang Seng Tech zaczyna się w 2020. Brakuje go, a nie stoi na 0,00% — tam
  znalazłby się nad każdym indeksem, który kiedykolwiek spadł, i czytałoby się to jako rynek, na
  którym nic się nie wydarzyło.
- **Świece miesięczne, bez korekty.** Indeks nie wypłaca dywidendy, ale powód jest inny: korekta
  zmienia bazę serii, a dwie serie po zmianie bazy nie są porównywalne. Strona idzie tą samą surową
  ścieżką do źródła co strona A+H.
- **Ustawienie rynku tu nie rządzi**: strona czyta trzy rynki naraz, a zmiana rynku jej nie zmienia.
  Można wziąć sześć z kontynentu, trzy z Hongkongu, trzy z Nowego Jorku albo wszystkie dwanaście.
- Najdłuższy okres ogranicza miesięczny sufit źródła — 430 świec, około trzydziestu pięciu lat;
  mniej niż dwanaście miesięcy jest odrzucane: to sprint, nie bieg długi.
""",
    "cs": """Jeden řádek na index a řádek je **jak daleko se ten index dostal od svého prvního měsíce
v rozmezí** — ne jeho úroveň. 3 800 na Shanghai Composite a 5 700 na S&P 500 nejsou dva body na jedné
stupnici; kreslit úrovně by byla tabule o tom, kde který index začal počítat.

- **Index, který přijde později, na tabuli není, dokud nepřijde.** S&P sahá do roku 1950, Dow jen do
  2009 a index Hang Seng Tech začíná v roce 2020. Chybí, nestojí na 0,00 % — tam by se zařadil nad
  každý index, který kdy klesl, a četlo by se to jako trh, kde se nic nestalo.
- **Měsíční svíčky, bez úprav.** Index nevyplácí dividendu, ale důvod je jiný: úprava přebazuje sérii
  a dvě přebazované řady vedle sebe nejsou srovnatelné. Stránka jde stejnou neupravenou cestou ke
  zdroji jako stránka A+H.
- **Nastavení trhu tuto stránku neřídí**: čte tři trhy najednou a změna trhu ji nezmění. Lze vzít šest
  z pevniny, tři z Hongkongu, tři z New Yorku nebo všech dvanáct.
- Nejdelší období omezuje měsíční strop zdroje — 430 svíček, asi třicet pět let; méně než dvanáct
  měsíců je odmítnuto: to je sprint, ne dlouhý běh.
""",
    "ru": """Одна строка на индекс, и строка — это **как далеко индекс ушёл от своего собственного первого
месяца в диапазоне**, а не его уровень. 3 800 у Shanghai Composite и 5 700 у S&P 500 — не две точки
одной шкалы; рисовать уровни значило бы сравнивать, откуда каждый индекс начал отсчёт.

- **Индекс, который приходит позже, не появляется на доске до своего прихода.** S&P уходит в 1950,
  Dow — лишь в 2009, а индекс Hang Seng Tech начинается в 2020. Он отсутствует, а не стоит в 0,00%:
  там он оказался бы выше любого индекса, который когда-либо падал, и читалось бы это как рынок, где
  ничего не произошло.
- **Месячные бары, без корректировки.** Индекс не платит дивидендов, но причина другая: корректировка
  перебазирует ряд, а два перебазированных ряда рядом не сравнимы. Страница идёт тем же «сырым»
  путём к источнику, что и страница A+H.
- **Настройка рынка здесь не главная**: страница читает три рынка сразу, и смена рынка её не меняет.
  Можно взять шесть материковых, три гонконгских, три нью-йоркских или все двенадцать.
- Самый длинный период ограничен месячным потолком источника — 430 баров, около тридцати пяти лет;
  меньше двенадцати месяцев отклоняется: это спринт, а не длинная дистанция.
""",
    "tr": """Her endeks için bir satır ve satır, **o endeksin aralıktaki kendi ilk ayından bu yana ne kadar
yol aldığıdır** — seviyesi değil. Shanghai Composite'ta 3.800 ile S&P 500'de 5.700 aynı ölçeğin iki
noktası değildir; seviyeleri çizmek, hangi endeksin saymaya nereden başladığı üzerine bir tablo
olurdu.

- **Geç gelen bir endeks, gelene kadar tabloda yoktur.** S&P 1950'ye, Dow yalnızca 2009'a uzanır ve
  Hang Seng Teknoloji endeksi 2020'de başlar. %0,00'de durmaz, hiç yoktur — orada dursaydı şimdiye
  kadar düşmüş her endeksin üstünde sıralanır ve 'hiçbir şey olmayan bir piyasa' gibi okunurdu.
- **Aylık mumlar, düzeltilmemiş.** Bir endeks temettü ödemez, ama asıl neden diğeridir: düzeltme bir
  seriyi yeniden bazlar ve yan yana konan iki yeniden bazlanmış seri karşılaştırılamaz. Sayfa,
  kaynağa AH sayfasının gittiği ham yoldan gider.
- **Piyasa ayarı bu sayfayı yönetmez**: üç piyasayı birlikte okur, piyasa değişse de o değişmez.
  Anakaranın altısı, Hong Kong'un üçü, New York'un üçü veya on ikisi birden seçilebilir.
- En uzun dönem, kaynağın aylık tavanıyla sınırlıdır — 430 mum, yaklaşık otuz beş yıl; on iki aydan
  kısa dönemler reddedilir: bu uzun koşu değil, kısa mesafedir.
""",
}


def main():
    for tag, title in TITLES.items():
        path = HELP / f"help-{tag}.md"

        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")
        lines = text.replace("\r\n", "\n").split("\n")

        want = f"## {title}"

        # Idempotent: drop the chapter wherever it already sits, then put it back in place.
        if want in lines:
            at = lines.index(want)

            heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
            after = [i for i in heads if i > at]
            end = after[0] if after else len(lines)

            while end > at and lines[end - 1].strip() == "":
                end -= 1

            del lines[at:end]

        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(heads) < AFTER + 2:
            raise AssertionError(f"{tag}: only {len(heads)} chapters")

        at = heads[AFTER + 1]

        block = [want, ""] + BODIES[tag].rstrip("\n").split("\n") + [""]

        lines[at:at] = block

        out = "\n".join(lines)

        if not out.endswith("\n"):
            out += "\n"

        path.write_bytes(b"\xef\xbb\xbf" + out.encode("utf-8"))

        chapters = sum(1 for line in out.split("\n") if line.startswith("## "))

        print(f"{tag}: inserted after chapter {AFTER + 1}, now {chapters} chapters")


if __name__ == "__main__":
    main()
