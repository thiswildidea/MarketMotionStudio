# -*- coding: utf-8 -*-
r"""把第十七页「债市固收竞速」要用的 resw 键注入 14 份 Resources.resw。

两类键：

* **INST\*** —— 榜上 9 个债券指数的显示名。键名规则与 C# `InstrumentNames.Key` 一致：
  `INST` + 代码的字母数字，全大写（`sz399307` -> `INSTSZ399307`）。没有这一层，
  画面会把行情源的中文名直接画上去——14 种语言里 13 种都读不懂。
  名字一律取**快照返回的真名**，不是猜的：`sh000012` 是「国债指数」，`sh000023` 是
  「沪分离债」（不是中证全债，且停在 2015-08），`sh000145` 是「优势资源」（不是国债）。
* **页面文案** —— 导航项、标题、副标题、两条口径说明、分组名、区间档、量词、状态行。

**那条口径说明是这一页的重点**：榜上九行全是交易所债券指数，源端对指数忽略复权参数，
所以画出来的是**价格涨跌，不含票息**。债券的收益大头在票息里，于是每一行都被低估，
而且低估的幅度各行不同。这话必须写进文案——不写，读者会把国债那行的 +43.70% 当成
「持有十年国债赚了 43.7%」。

resw 是 UTF-8 **带 BOM** + LF：必须 `read_bytes().decode('utf-8-sig')` 读、
`write_bytes()` 写回。删键按「基础名 + 可选后缀 + `[^>]*`」匹配——文件里两种条目格式并存。

幂等：先删同名键再插入，跑几遍结果一样。

用法：python tools\port-bondrace-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 每条文案都写满 14 列，列序与 LANGS 完全一致：
# en-US, de, es, fr, it, pl, pt-BR, cs, tr, ru, ja, ko, zh-Hant, zh-Hans


# ---- 9 个债券指数 --------------------------------------------------------------------
# 代码与名字都来自 qt.gtimg.cn 快照实测（2026-10-03），月线连续且末月为 2026-09。

INSTRUMENTS = [
    ("sh000012", [
        "Treasury bond index", "Staatsanleihen-Index", "Índice de bonos del Estado",
        "Indice des obligations d'État", "Indice dei titoli di Stato",
        "Indeks obligacji skarbowych", "Índice de títulos do Tesouro",
        "Index státních dluhopisů", "Hazine tahvili endeksi",
        "Индекс государственных облигаций", "国債指数", "국채지수", "國債指數", "国债指数"]),

    ("sh000013", [
        "Enterprise bond index", "Unternehmensanleihen-Index", "Índice de bonos de empresa",
        "Indice des obligations d'entreprise", "Indice delle obbligazioni societarie",
        "Indeks obligacji przedsiębiorstw", "Índice de bônus corporativos",
        "Index podnikových dluhopisů", "Kurumsal tahvil endeksi",
        "Индекс корпоративных облигаций", "企業債指数", "기업채지수", "企債指數", "企债指数"]),

    ("sh000022", [
        "Shanghai corporate bond", "Shanghai-Unternehmensanleihe",
        "Bono corporativo de Shanghái", "Obligation d'entreprise de Shanghai",
        "Obbligazione societaria di Shanghai", "Obligacja korporacyjna Shanghai",
        "Bônus corporativo de Xangai", "Podnikový dluhopis Šanghaj",
        "Şanghay kurumsal tahvili", "Корпоративная облигация Шанхая",
        "滬公司債", "상하이 회사채", "滬公司債", "沪公司债"]),

    ("sz399301", [
        "Shenzhen credit bond", "Shenzhen-Kreditobligation", "Bono de crédito de Shenzhen",
        "Obligation de crédit de Shenzhen", "Obbligazione creditizia di Shenzhen",
        "Obligacja kredytowa Shenzhen", "Bônus de crédito de Shenzhen",
        "Úvěrový dluhopis Šen-čen", "Shenzhen kredi tahvili",
        "Кредитная облигация Шэньчжэня", "深信用債", "선전 신용채", "深信用債", "深信用债"]),

    ("sz399302", [
        "Shenzhen corporate bond", "Shenzhen-Unternehmensanleihe",
        "Bono corporativo de Shenzhen", "Obligation d'entreprise de Shenzhen",
        "Obbligazione societaria di Shenzhen", "Obligacja korporacyjna Shenzhen",
        "Bônus corporativo de Shenzhen", "Podnikový dluhopis Šen-čen",
        "Shenzhen kurumsal tahvili", "Корпоративная облигация Шэньчжэня",
        "深公司債", "선전 회사채", "深公司債", "深公司债"]),

    ("sh000061", [
        "Shanghai enterprise bond 30", "Shanghai-Unternehmensanleihe 30",
        "Bono corporativo 30 de Shanghái", "Obligation d'entreprise 30 de Shanghai",
        "Obbligazione societaria 30 di Shanghai", "Obligacja przedsiębiorstw 30 Shanghai",
        "Bônus corporativo 30 de Xangai", "Podnikový dluhopis 30 Šanghaj",
        "Şanghay kurumsal tahvil 30", "Корпоративная облигация 30 Шанхая",
        "滬企業債30", "상하이 기업채30", "滬企債30", "沪企债30"]),

    ("sh000832", [
        "CSI convertible bond", "CSI-Wandelanleihe", "Bono convertible CSI",
        "Obligation convertible CSI", "Obbligazione convertibile CSI",
        "Obligacja zamienna CSI", "Bônus conversível CSI", "Konvertibilní dluhopis CSI",
        "CSI dönüştürülebilir tahvil", "Конвертируемая облигация CSI",
        "中証転債", "중정 전환채", "中證轉債", "中证转债"]),

    ("sh000139", [
        "SSE convertible bond", "SSE-Wandelanleihe", "Bono convertible SSE",
        "Obligation convertible SSE", "Obbligazione convertibile SSE",
        "Obligacja zamienna SSE", "Bônus conversível SSE", "Konvertibilní dluhopis SSE",
        "SSE dönüştürülebilir tahvil", "Конвертируемая облигация SSE",
        "上証転債", "상증 전환채", "上證轉債", "上证转债"]),

    ("sz399307", [
        "SZSE convertible bond", "SZSE-Wandelanleihe", "Bono convertible SZSE",
        "Obligation convertible SZSE", "Obbligazione convertibile SZSE",
        "Obligacja zamienna SZSE", "Bônus conversível SZSE", "Konvertibilní dluhopis SZSE",
        "SZSE dönüştürülebilir tahvil", "Конвертируемая облигация SZSE",
        "深証転債", "심증 전환채", "深證轉債", "深证转债"]),
]


# ---- 13 条页面文案 --------------------------------------------------------------------

PAGE = [
    ("NavBondRace.Content", [
        "Bond market", "Anleihemarkt", "Renta fija", "Marché obligataire",
        "Mercato obbligazionario", "Rynek obligacji", "Mercado de títulos",
        "Trh dluhopisů", "Tahvil piyasası", "Рынок облигаций", "債券市場",
        "채권시장", "債市固收", "债市固收"]),

    ("BondRacePageTitle.Text", [
        "Bond Market Race", "Anleihemarkt-Rennen", "Carrera de renta fija",
        "Course du marché obligataire", "Corsa del mercato obbligazionario",
        "Wyścig rynku obligacji", "Corrida do mercado de títulos",
        "Závod dluhopisových trhů", "Tahvil piyasası yarışı", "Гонка рынка облигаций",
        "債券市場レース", "채권시장 레이스", "債市固收競速", "债市固收竞速"]),

    ("BondRacePageSubtitle.Text", [
        "Nine bond indices — government, credit and convertibles — each measured from its own "
        "first month in the range, so what is compared is the move, not the level.",

        "Neun Anleiheindizes — Staatsanleihen, Unternehmensanleihen und Wandler — jeder ab seinem "
        "eigenen ersten Monat im Zeitraum gemessen, also wird die Bewegung verglichen, nicht das "
        "Niveau.",

        "Nueve índices de bonos — Estado, crédito y convertibles — cada uno medido desde su propio "
        "primer mes en el periodo: se compara el movimiento, no el nivel.",

        "Neuf indices obligataires — État, crédit et convertibles — chacun mesuré depuis son "
        "propre premier mois dans la période : c'est le mouvement qui est comparé, pas le niveau.",

        "Nove indici obbligazionari — governativi, creditizi e convertibili — ciascuno misurato "
        "dal proprio primo mese nel periodo: si confronta il movimento, non il livello.",

        "Dziewięć indeksów obligacji — skarbowe, kredytowe i zamienne — każdy liczony od własnego "
        "pierwszego miesiąca w okresie, więc porównywany jest ruch, nie poziom.",

        "Nove índices de títulos — governo, crédito e conversíveis — cada um medido a partir do "
        "seu próprio primeiro mês no período: compara-se o movimento, não o nível.",

        "Devět dluhopisových indexů — státní, úvěrové a konvertibilní — každý měřený od svého "
        "vlastního prvního měsíce v období, takže se porovnává pohyb, nikoli úroveň.",

        "Dokuz tahvil endeksi — hazine, kredi ve dönüştürülebilir — her biri dönemdeki kendi ilk "
        "ayından ölçülür; karşılaştırılan hareket, seviye değil.",

        "Девять индексов облигаций — государственных, кредитных и конвертируемых — каждый "
        "измеряется от своего первого месяца в периоде, поэтому сравнивается движение, а не "
        "уровень.",

        "国債・社債・転換債の 9 本の債券指数を、それぞれ期間内で自分自身の最初の月から"
        "計測します。比較するのは水準ではなく動きです。",

        "국채·신용채·전환채 등 9개 채권 지수를 각각 기간 내 자신의 첫 달부터 측정합니다. "
        "비교하는 것은 수준이 아니라 움직임입니다.",

        "九條債券指數——國債、信用債、可轉債——各自從自己在區間內的第一個月起算，"
        "所以比的是變動，不是點位。",

        "九条债券指数——国债、信用债、可转债——各自从自己在区间内的第一个月起算，"
        "所以比的是变动，不是点位。"]),

    # 这一条是整页最该被读到的话：价格指数不含票息。
    ("BondRaceNote.Text", [
        "One row per bond index. The bar is a price change: a bond's coupon — most of what a bond "
        "pays — never appears in its quote, so what a holder earned was more than this, and by "
        "different amounts on different rows.",

        "Eine Zeile pro Anleiheindex. Der Balken ist eine Kursänderung: der Kupon — das meiste, was "
        "eine Anleihe zahlt — taucht in ihrer Notierung nie auf. Was ein Halter verdient hat, war "
        "also mehr, und auf jeder Zeile um einen anderen Betrag.",

        "Una fila por índice. La barra es una variación de precio: el cupón — la mayor parte de lo "
        "que paga un bono — nunca aparece en su cotización, así que lo que ganó quien lo mantuvo "
        "fue más, y en cada fila por un importe distinto.",

        "Une ligne par indice. La barre est une variation de cours : le coupon — l'essentiel de ce "
        "que paie une obligation — n'apparaît jamais dans sa cotation. Ce qu'un détenteur a gagné "
        "était donc plus, et d'un montant différent sur chaque ligne.",

        "Una riga per indice. La barra è una variazione di prezzo: la cedola — la maggior parte di "
        "ciò che paga un'obbligazione — non compare mai nella sua quotazione, quindi chi l'ha "
        "detenuta ha guadagnato di più, e in misura diversa su ogni riga.",

        "Jeden wiersz na indeks. Słupek to zmiana ceny: kupon — większość tego, co obligacja "
        "wypłaca — nigdy nie pojawia się w jej notowaniu, więc posiadacz zarobił więcej, a na "
        "każdym wierszu o inną kwotę.",

        "Uma linha por índice. A barra é uma variação de preço: o cupom — a maior parte do que um "
        "título paga — nunca aparece em sua cotação, então quem o manteve ganhou mais, e em cada "
        "linha por um valor diferente.",

        "Jeden řádek na index. Pruh je změna ceny: kupón — většina toho, co dluhopis vyplácí — se "
        "v jeho kotaci nikdy neobjeví, takže držitel vydělal více, a na každém řádku o jinou "
        "částku.",

        "Her endeks bir satır. Çubuk fiyat değişimi: kupon — bir tahvilin ödediğinin çoğu — "
        "fiyatında hiç görünmez, dolayısıyla elinde tutanın kazancı bundan fazlaydı ve her "
        "satırda farklı bir tutarla.",

        "Одна строка на индекс. Полоса — это изменение цены: купон — большая часть того, что "
        "платит облигация — никогда не появляется в её котировке, поэтому держатель заработал "
        "больше, и на каждой строке — на разную величину.",

        "指数 1 本につき 1 行。バーは価格の変動です。債券が支払う額の大部分であるクーポンは"
        "気配値に現れないため、保有者が実際に得たものはこれより多く、しかも行ごとに差があります。",

        "지수당 한 행. 막대는 가격 변동입니다. 채권이 지급하는 대부분인 쿠폰은 호가에 "
        "나타나지 않으므로 보유자가 실제로 얻은 것은 이보다 많고, 그 차이는 행마다 다릅니다.",

        "一條指數一行。條形是價格變動：債券付出的大部分是票息，而票息永遠不出現在報價裡——"
        "所以持有者真正賺到的比這個數字多，而且每一行差得不一樣多。",

        "一条指数一行。条形是价格变动：债券付出的大部分是票息，而票息永远不出现在报价里——"
        "所以持有者真正赚到的比这个数字多，而且每一行差得不一样多。"]),

    ("BondRaceList.Header", [
        "Bond group", "Anleihegruppe", "Grupo de bonos", "Groupe d'obligations",
        "Gruppo obbligazioni", "Grupa obligacji", "Grupo de títulos", "Skupina dluhopisů",
        "Tahvil grubu", "Группа облигаций", "債券グループ", "채권 그룹", "債券分組", "债券分组"]),

    ("BondRaceListAll", [
        "All nine", "Alle neun", "Los nueve", "Les neuf", "Tutti e nove", "Wszystkie dziewięć",
        "Todos os nove", "Všech devět", "Dokuzu da", "Все девять", "9 本すべて",
        "전체 9개", "全部九條", "全部九条"]),

    ("BondRaceListPure", [
        "Straight bonds", "Klassische Anleihen", "Bonos simples", "Obligations simples",
        "Obbligazioni pure", "Zwykłe obligacje", "Títulos simples", "Klasické dluhopisy",
        "Düz tahviller", "Обычные облигации", "普通債", "일반채", "純債", "纯债"]),

    ("BondRaceListConvert", [
        "Convertibles", "Wandler", "Convertibles", "Convertibles", "Convertibili",
        "Zamienne", "Conversíveis", "Konvertibilní", "Dönüştürülebilirler",
        "Конвертируемые", "転換債", "전환채", "可轉債", "可转债"]),

    ("BondRaceRangeMax", [
        "Longest", "Längster", "Más largo", "Le plus long", "Il più lungo", "Najdłuższy",
        "Mais longo", "Nejdelší", "En uzun", "Самый длинный", "最長", "가장 긴",
        "最長", "最长"]),

    # 画面表头那行接在数字后面的量词：「9 个债券指数」。渲染器只留日线兜底，
    # 计数词与周期词（MarketCapUnitMonths）都由页面传。
    ("BondRaceUnitBonds", [
        "bond indices", "Anleiheindizes", "índices de bonos", "indices obligataires",
        "indici obbligazionari", "indeksów obligacji", "índices de títulos",
        "dluhopisových indexů", "tahvil endeksi", "индексов облигаций", "債券指数",
        "채권 지수", "個債券指數", "个债券指数"]),

    ("BondRaceStageTitle", [
        "Bond market", "Anleihemarkt", "Renta fija", "Marché obligataire",
        "Mercato obbligazionario", "Rynek obligacji", "Mercado de títulos", "Trh dluhopisů",
        "Tahvil piyasası", "Рынок облигаций", "債券市場", "채권시장", "債市固收", "债市固收"]),

    ("BondRaceMethodNote.Text", [
        "Monthly and unadjusted — the opposite of the asset race: an index pays no coupon into "
        "its own quote, so there is nothing to put back, while a fund does. Start dates differ: "
        "the earliest begins in 2003-02 and the Shenzhen convertible index only in 2014-08, so it "
        "joins a ten-year board five years in. This page is not governed by the market setting.",

        "Monatlich und nicht bereinigt — das Gegenteil des Anleihe-Fonds-Rennens: ein Index zahlt "
        "keinen Kupon in seine eigene Notierung, also gibt es nichts zurückzurechnen, bei einem "
        "Fonds schon. Die Starttermine unterscheiden sich: der früheste beginnt 2003-02, der "
        "Shenzhen-Wandlerindex erst 2014-08 — er stößt also fünf Jahre später dazu. Diese Seite "
        "richtet sich nicht nach der Markteinstellung.",

        "Mensual y sin ajustar — lo contrario de la carrera de fondos: un índice no paga cupón en "
        "su propia cotización, así que no hay nada que reincorporar, mientras que un fondo sí. "
        "Las fechas de inicio difieren: la más temprana empieza en 2003-02 y el índice "
        "convertible de Shenzhen solo en 2014-08, así que entra en un tablero de diez años con "
        "cinco años de retraso. Esta página no depende del ajuste de mercado.",

        "Mensuel et non ajusté — l'inverse de la course des fonds : un indice ne verse aucun "
        "coupon dans sa propre cotation, il n'y a donc rien à réintégrer, alors qu'un fonds si. "
        "Les dates de début diffèrent : la plus ancienne commence en 2003-02 et l'indice "
        "convertible de Shenzhen seulement en 2014-08, qui rejoint donc un tableau de dix ans "
        "avec cinq ans de retard. Cette page ne dépend pas du réglage de marché.",

        "Mensile e non rettificato — l'opposto della corsa dei fondi: un indice non paga cedole "
        "nella propria quotazione, quindi non c'è nulla da reintegrare, mentre un fondo sì. Le "
        "date di inizio differiscono: la più antica parte dal 2003-02 e l'indice convertibile di "
        "Shenzhen solo dal 2014-08, quindi entra in un tabellone decennale con cinque anni di "
        "ritardo. Questa pagina non dipende dall'impostazione del mercato.",

        "Miesięcznie i bez korekty — odwrotnie niż w wyścigu funduszy: indeks nie wypłaca kuponu "
        "do własnego notowania, więc nie ma czego doliczać, fundusz — owszem. Daty początkowe "
        "różnią się: najwcześniejsza to 2003-02, a indeks konwertowalny Shenzhen dopiero "
        "2014-08, więc na dziesięcioletniej tablicy dołącza po pięciu latach. Ta strona nie "
        "zależy od ustawienia rynku.",

        "Mensal e sem ajuste — o oposto da corrida de fundos: um índice não paga cupom em sua "
        "própria cotação, então não há nada a reintegrar, enquanto um fundo tem. As datas de "
        "início diferem: a mais antiga começa em 2003-02 e o índice conversível de Shenzhen "
        "apenas em 2014-08, então ele entra num quadro de dez anos com cinco anos de atraso. "
        "Esta página não depende da configuração de mercado.",

        "Měsíčně a neupraveno — opak závodu fondů: index nevyplácí kupón do vlastní kotace, takže "
        "není co připočítat, u fondu ano. Počáteční data se liší: nejstarší začíná 2003-02 a "
        "konvertibilní index Šen-čen až 2014-08, takže na desetiletou tabuli nastupuje po pěti "
        "letech. Tato stránka se neřídí nastavením trhu.",

        "Aylık ve düzeltilmemiş — fon yarışının tersi: bir endeks kendi fiyatına kupon ödemez, "
        "yani geri eklenecek bir şey yoktur; fon ise öder. Başlangıç tarihleri farklı: en eskisi "
        "2003-02'de, Shenzhen dönüştürülebilir endeksi ise ancak 2014-08'de başlar, yani on "
        "yıllık tabloya beş yıl sonra katılır. Bu sayfa pazar ayarından etkilenmez.",

        "Ежемесячно и без корректировки — противоположность гонке фондов: индекс не выплачивает "
        "купон в собственную котировку, так что возвращать нечего, а у фонда — есть. Даты начала "
        "различаются: самая ранняя — 2003-02, а конвертируемый индекс Шэньчжэня — только "
        "2014-08, то есть на десятилетнюю доску он выходит через пять лет. Эта страница не "
        "зависит от настройки рынка.",

        "月次・未調整——ファンド競速とは逆です。指数は自らの気配値にクーポンを支払わないため、"
        "戻し入れるものがありません（ファンドにはあります）。開始月はまちまちで、最古は"
        "2003-02、深センの転換債指数は 2014-08 からなので、十年の盤面には 5 年遅れて登場します。"
        "このページは市場設定に左右されません。",

        "월간·무조정——펀드 레이스와 반대입니다. 지수는 자기 호가에 쿠폰을 지급하지 않으므로 "
        "되돌려 넣을 것이 없지만(펀드는 있음), 시작월은 제각각입니다. 가장 이른 것은 2003-02,"
        "선전 전환채 지수는 2014-08부터라 10년 보드에는 5년 늦게 합류합니다. 이 페이지는 시장 "
        "설정의 영향을 받지 않습니다.",

        "月線、未復權——與大類資產那一榜相反：指數不會把票息算進自己的報價，所以沒有東西"
        "需要加回去，基金則不然。起點各不相同：最早從 2003-02 開始，深圳的可轉債指數要到 "
        "2014-08 才有，所以在十年榜上它晚了五年才進場。本頁不受市場設定影響。",

        "月线、未复权——与大类资产那一榜相反：指数不会把票息算进自己的报价，所以没有东西"
        "需要加回去，基金则不然。起点各不相同：最早从 2003-02 开始，深圳的可转债指数要到 "
        "2014-08 才有，所以在十年榜上它晚了五年才进场。本页不受市场设置影响。"]),

    ("BondRaceFetched", [
        "{0} indices · {1} months · ahead is {2}, {3} · behind is {4}, {5}",
        "{0} Indizes · {1} Monate · vorn liegt {2}, {3} · hinten {4}, {5}",
        "{0} índices · {1} meses · delante va {2}, {3} · detrás {4}, {5}",
        "{0} indices · {1} mois · en tête {2}, {3} · en queue {4}, {5}",
        "{0} indici · {1} mesi · in testa {2}, {3} · in coda {4}, {5}",
        "{0} indeksów · {1} miesięcy · z przodu {2}, {3} · z tyłu {4}, {5}",
        "{0} índices · {1} meses · na frente {2}, {3} · atrás {4}, {5}",
        "{0} indexů · {1} měsíců · v čele {2}, {3} · na konci {4}, {5}",
        "{0} endeks · {1} ay · önde {2}, {3} · arkada {4}, {5}",
        "{0} индексов · {1} мес. · впереди {2}, {3} · позади {4}, {5}",
        "{0} 指数 · {1} か月 · 首位は {2}、{3} · 最下位は {4}、{5}",
        "{0}개 지수 · {1}개월 · 선두 {2}, {3} · 최하위 {4}, {5}",
        "{0} 條指數 · {1} 個月 · 領先的是 {2}，{3} · 墊底的是 {4}，{5}",
        "{0} 条指数 · {1} 个月 · 领先的是 {2}，{3} · 垫底的是 {4}，{5}"]),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML, and MakePri reports it as `PRI224: root node not found`,
    naming the root element rather than the value that broke it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        at = LANGS.index(tag)
        lines = []

        for code, values in INSTRUMENTS:
            assert len(values) == len(LANGS), f"{code}: {len(values)} values"
            key = "INST" + "".join(c for c in code if c.isalnum()).upper()
            lines.append(entry(key, values[at]))

        for key, values in PAGE:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values"
            lines.append(entry(key, values[at]))

        # Idempotent: drop a key of the same name wherever it already sits, then append.
        # `[^>]*` after the name because this file holds two entry shapes — the single-line
        # `<data name="K">` a machine wrote and the hand-edited
        # `<data name="K" xml:space="preserve">` — and a pattern that insists on `">` matches
        # only the first, which is how a file once ended up holding both `K` and `K.Text`
        # (PRI278: key defined as both a resource and a scope).
        for code, _ in INSTRUMENTS:
            key = "INST" + "".join(c for c in code if c.isalnum()).upper()
            text = re.sub(rf'  <data name="{key}">.*?</data>\n', "", text, flags=re.S)

        for key, _ in PAGE:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at_root = text.rfind("</root>")
        assert at_root > 0, f"{tag}: no </root>"

        text = text[:at_root] + "".join(lines) + text[at_root:]

        # Bytes, not text: read_text/write_text would normalise the line endings and git
        # would see the whole file rewritten.
        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
