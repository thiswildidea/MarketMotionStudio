# -*- coding: utf-8 -*-
r"""把市值榜**候选池**里新增的 93 个标的的显示名注入 14 份 Resources.resw，
并把两条页面文案改成"每月取当时前 N 名"的动态版。

和 `port-marketcap-resw.py` 分开，是因为两者给的译文不同：

* 上一个是**会进榜的那十几家**——工商银行、贵州茅台、英伟达——每种语言都值得
  一个像样的名字，所以逐语言手写了 14 列。
* 这一个是**候选池**：六十几只里任何一只都可能在某个月进入前十五，所以名字都
  必须有；但池子里的绝大多数公司在德语、西班牙语里本来就叫英文名。所以这里
  只给中文和英文两列，欧洲语言复用英文名，日文韩文也用英文名。**这是有意的
  降级**，不是遗漏：一个日本人看到 "Anhui Conch Cement" 认得出，看到「海螺水泥」
  认不出。哪只票真的常驻榜上，再给它补本地化写法。

繁体由简体按表转换（公司名用字的简繁差异有限），表外的字原样保留。

用法：python tools\port-marketcap-pool-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# 公司名里会碰到的简繁差异，够用即可 —— 表外的字保留原样，混一两个不影响读。
TRADITIONAL = str.maketrans({
    "团": "團", "银": "銀", "业": "業", "电": "電", "东": "東", "财": "財", "华": "華",
    "万": "萬", "铁": "鐵", "车": "車", "龙": "龍", "泸": "瀘", "讯": "訊", "陕": "陝",
    "药": "藥", "贝": "貝", "尔": "爾", "国": "國", "际": "際", "恒": "恆", "医": "醫",
    "产": "產", "险": "險", "兴": "興", "发": "發", "绿": "綠", "邮": "郵", "储": "儲",
    "迈": "邁", "维": "維", "购": "購", "联": "聯", "腾": "騰", "长": "長", "粮": "糧",
    "号": "號", "寿": "壽", "筑": "築", "学": "學", "智": "智",
    "润": "潤", "创": "創", "汉": "漢", "马": "馬", "丽": "麗",
    "岛": "島", "汇": "匯", "丰": "豐", "泰": "泰", "坚": "堅", "兰": "蘭",
    "诚": "誠", "诺": "諾", "亚": "亞", "翱": "翱", "鲍": "鮑", "盖": "蓋",
    "纳": "納", "逊": "遜", "罗": "羅", "礼": "禮", "顿": "頓", "强": "強",
    "运": "運", "顺": "順", "锋": "鋒", "飞": "飛", "贝": "貝",
})


def traditional(text):
    return text.translate(TRADITIONAL)


# (code, 中文名, 英文名)。中文名与 MarketCaps.cs 里的清单逐字相同。
POOL = [
    # -- A 股：45 只（前十五名之外，但十年里够得着榜单的）
    ("sz002594", "比亚迪", "BYD"),
    ("sz000333", "美的集团", "Midea"),
    ("sh601728", "中国电信", "China Telecom"),
    ("sh600030", "中信证券", "CITIC Securities"),
    ("sh600276", "恒瑞医药", "Hengrui Pharma"),
    ("sh601601", "中国太保", "China Pacific Insurance"),
    ("sz002415", "海康威视", "Hikvision"),
    ("sz300059", "东方财富", "East Money"),
    ("sz000001", "平安银行", "Ping An Bank"),
    ("sh600309", "万华化学", "Wanhua Chemical"),
    ("sz000651", "格力电器", "Gree Electric"),
    ("sh601668", "中国建筑", "China State Construction"),
    ("sh601336", "新华保险", "New China Life"),
    ("sh600887", "伊利股份", "Yili"),
    ("sh600809", "山西汾酒", "Shanxi Fenjiu"),
    ("sh600050", "中国联通", "China Unicom"),
    ("sh601111", "中国国航", "Air China"),
    ("sh601633", "长城汽车", "Great Wall Motor"),
    ("sh601390", "中国中铁", "China Railway"),
    ("sh600585", "海螺水泥", "Anhui Conch Cement"),
    ("sh601012", "隆基绿能", "LONGi Green Energy"),
    ("sh601186", "中国铁建", "China Railway Construction"),
    ("sz002304", "洋河股份", "Yanghe"),
    ("sh600000", "浦发银行", "SPD Bank"),
    ("sh601166", "兴业银行", "Industrial Bank"),
    ("sh600016", "民生银行", "China Minsheng Bank"),
    ("sh601818", "光大银行", "China Everbright Bank"),
    ("sh601169", "北京银行", "Bank of Beijing"),
    ("sh600104", "上汽集团", "SAIC Motor"),
    ("sz000002", "万科A", "China Vanke"),
    ("sh601766", "中国中车", "CRRC"),
    ("sh601989", "中国重工", "CSIC"),
    ("sh600150", "中国船舶", "CSSC"),
    ("sh600031", "三一重工", "Sany Heavy Industry"),
    ("sz000725", "京东方A", "BOE Technology"),
    ("sz002475", "立讯精密", "Luxshare Precision"),
    ("sh603259", "药明康德", "WuXi AppTec"),
    ("sh600438", "通威股份", "Tongwei"),
    ("sh600690", "海尔智家", "Haier Smart Home"),
    ("sz000568", "泸州老窖", "Luzhou Laojiao"),
    ("sh600048", "保利发展", "Poly Developments"),
    ("sz000063", "中兴通讯", "ZTE"),
    ("sh601225", "陕西煤业", "Shaanxi Coal"),
    ("sh601658", "邮储银行", "Postal Savings Bank"),
    ("sh601998", "中信银行", "China CITIC Bank"),

    # -- 港股：20 只
    ("hk00981", "中芯国际", "SMIC"),
    ("hk02020", "安踏体育", "Anta Sports"),
    ("hk01109", "华润置地", "China Resources Land"),
    ("hk00016", "新鸿基地产", "Sun Hung Kai Properties"),
    ("hk00001", "长和", "CK Hutchison"),
    ("hk00883", "中国海洋石油", "CNOOC"),
    ("hk00762", "中国联通", "China Unicom"),
    ("hk01024", "快手", "Kuaishou"),
    ("hk09961", "携程集团", "Trip.com"),
    ("hk09888", "百度集团", "Baidu"),
    ("hk06618", "京东健康", "JD Health"),
    ("hk02331", "李宁", "Li-Ning"),
    ("hk01088", "中国神华", "Shenhua Energy"),
    ("hk00902", "华能国际电力股份", "Huaneng Power"),
    ("hk06862", "海底捞", "Haidilao"),
    ("hk00291", "华润啤酒", "China Resources Beer"),
    ("hk01093", "石药集团", "CSPC Pharma"),
    ("hk01177", "中国生物制药", "Sino Biopharm"),
    ("hk02628", "中国人寿", "China Life"),
    ("hk00788", "中国铁塔", "China Tower"),

    # -- 美股：28 只
    ("usUNH.N", "联合健康", "UnitedHealth"),
    ("usMA.N", "万事达", "Mastercard"),
    ("usCOST.OQ", "好市多", "Costco"),
    ("usHD.N", "家得宝", "Home Depot"),
    ("usPG.N", "宝洁", "Procter & Gamble"),
    ("usJNJ.N", "强生", "Johnson & Johnson"),
    ("usNFLX.OQ", "奈飞", "Netflix"),
    ("usAMD.OQ", "超威半导体", "AMD"),
    ("usCRM.N", "赛富时", "Salesforce"),
    ("usADBE.OQ", "Adobe", "Adobe"),
    ("usKO.N", "可口可乐", "Coca-Cola"),
    ("usPEP.OQ", "百事可乐", "PepsiCo"),
    ("usDIS.N", "迪士尼", "Disney"),
    ("usINTC.OQ", "英特尔", "Intel"),
    ("usCSCO.OQ", "思科", "Cisco"),
    ("usPFE.N", "辉瑞", "Pfizer"),
    ("usBA.N", "波音", "Boeing"),
    ("usGE.N", "GE航天航空", "GE Aerospace"),
    ("usT.N", "美国电话电报", "AT&T"),
    ("usCVX.N", "雪佛龙", "Chevron"),
    ("usMRK.N", "默沙东", "Merck"),
    ("usABBV.N", "艾伯维", "AbbVie"),
    ("usBAC.N", "美国银行", "Bank of America"),
    ("usWFC.N", "富国银行", "Wells Fargo"),
    ("usC.N", "花旗集团", "Citigroup"),
    ("usGS.N", "高盛", "Goldman Sachs"),
    ("usMS.N", "摩根士丹利", "Morgan Stanley"),
    ("usBLK.N", "贝莱德", "BlackRock"),
]

# 两条文案从"固定十五家"改成"每月取当时前 N 名"。
REWRITTEN = [
    ("MarketCapCount", [
        "The field is today's top 200 by market value, plus the listings that have fallen out of "
        "it. Each period shows the top {0}.",
        "Das Feld sind die heutigen Top 200 nach Marktkapitalisierung plus die Werte, die "
        "herausgefallen sind. Jede Periode zeigt die {0} größten.",
        "El grupo son los 200 mayores de hoy por capitalización, más los que han salido de ella. "
        "Cada periodo muestra los {0} mayores.",
        "Le plateau est le top 200 du jour par capitalisation, plus celles qui en sont sorties. "
        "Chaque période montre les {0} plus grandes.",
        "Il campo sono i primi 200 di oggi per capitalizzazione, più quelli usciti. Ogni periodo "
        "mostra i {0} maggiori.",
        "Grono to dzisiejsze top 200 według kapitalizacji plus te, które z niego wypadły. Każdy "
        "okres pokazuje {0} największych.",
        "O grupo são os 200 maiores de hoje por valor de mercado, mais os que saíram. Cada período "
        "mostra os {0} maiores.",
        "Sestava je dnešních 200 největších podle kapitalizace plus ty, které vypadly. Každé "
        "období ukazuje {0} největších.",
        "Kadro, bugünkü piyasa değerine göre ilk 200 artı dışında kalanlar. Her dönem en büyük {0} "
        "tanesini gösterir.",
        "Список — сегодняшние 200 крупнейших по капитализации плюс выбывшие из него. Каждый "
        "период показывает {0} крупнейших.",
        "候補は本日の時価総額上位 200 社と、そこから外れた銘柄です。各期間で上位 {0} 社を表示します。",
        "후보는 오늘의 시가총액 상위 200개와 거기서 밀려난 종목입니다. 각 시점에서 상위 {0}개를 "
        "보여줍니다.",
        "取數時按當前市值取前 200 名作候選池，加上十年裡曾經進榜的公司；每一期顯示市值前 {0} 名。",
        "取数时按当前市值取前 200 名作候选池，加上十年里曾经进榜的公司；每一期显示市值前 {0} 名。"]),

    ("MarketCapRanking", [
        "Reading today's market-value ranking ({0}) …",
        "Die heutige Rangliste nach Marktkapitalisierung wird gelesen ({0}) …",
        "Leyendo la clasificación de hoy por capitalización ({0}) …",
        "Lecture du classement du jour par capitalisation ({0}) …",
        "Lettura della classifica odierna per capitalizzazione ({0}) …",
        "Odczyt dzisiejszego rankingu kapitalizacji ({0}) …",
        "Lendo o ranking de hoje por valor de mercado ({0}) …",
        "Načítání dnešního žebříčku kapitalizace ({0}) …",
        "Bugünkü piyasa değeri sıralaması okunuyor ({0}) …",
        "Читаю сегодняшний рейтинг по капитализации ({0}) …",
        "本日の時価総額ランキングを読み込んでいます（{0}）…",
        "오늘의 시가총액 순위를 읽는 중 ({0}) …",
        "正在讀取當前市值排名（{0}）…",
        "正在读取当前市值排名（{0}）…"]),

    ("MarketCapFetched", [
        "{0} candidates · {1} periods · leading {2} {3} · last {4} {5}",
        "{0} Kandidaten · {1} Perioden · vorn {2} {3} · zuletzt {4} {5}",
        "{0} candidatos · {1} periodos · lidera {2} {3} · último {4} {5}",
        "{0} candidats · {1} périodes · en tête {2} {3} · dernier {4} {5}",
        "{0} candidati · {1} periodi · in testa {2} {3} · ultimo {4} {5}",
        "{0} kandydatów · {1} okresów · lider {2} {3} · ostatni {4} {5}",
        "{0} candidatos · {1} períodos · na frente {2} {3} · último {4} {5}",
        "{0} kandidátů · {1} období · v čele {2} {3} · poslední {4} {5}",
        "{0} aday · {1} dönem · lider {2} {3} · son {4} {5}",
        "{0} кандидатов · {1} периодов · впереди {2} {3} · последний {4} {5}",
        "候補 {0} 銘柄 · {1} 期間 · 首位 {2} {3} · 最下位 {4} {5}",
        "후보 {0}개 · {1}개 기간 · 1위 {2} {3} · 최하위 {4} {5}",
        "{0} 檔候選 · {1} 期 · 領先 {2} {3} · 墊底 {4} {5}",
        "{0} 只候选 · {1} 期 · 领先 {2} {3} · 垫底 {4} {5}"]),

    ("MarketCapMethodNote.Text"
, [
        "A monthly board: membership changes month to month, so joining and leaving both stay on "
        "the frame. A past market value is today's total market value times the adjusted price "
        "ratio over the range — bonus issues and splits cancel in the adjusted series, dividends "
        "do not, so a heavy payer's past value reads low. Only the last frame's figure comes "
        "straight from the source.",
        "Ein monatliches Board: die Mitglieder wechseln von Monat zu Monat, Auf- und Abstieg "
        "bleiben also im Bild. Ein früherer Marktwert ist der heutige Gesamtwert mal das "
        "bereinigte Kursverhältnis über den Zeitraum — Kapitalerhöhungen und Splits heben sich "
        "auf, Dividenden nicht, weshalb ein starker Ausschütter zu niedrig ausfällt.",
        "Un tablero mensual: los miembros cambian mes a mes, así que entrar y salir quedan en la "
        "imagen. Un valor pasado es el valor total de hoy por el cociente de precios ajustado del "
        "periodo — las ampliaciones y los desdoblamientos se anulan, los dividendos no, así que un "
        "pagador fuerte queda bajo.",
        "Un tableau mensuel : les membres changent d'un mois à l'autre, les entrées et les sorties "
        "restent donc à l'image. Une valeur passée est la valeur totale d'aujourd'hui multipliée "
        "par le rapport de prix ajusté — les augmentations et les fractionnements s'annulent, les "
        "dividendes non, donc un gros distributeur ressort bas.",
        "Una classifica mensile: i membri cambiano di mese in mese, quindi entrate e uscite "
        "restano nell'immagine. Un valore passato è il valore totale di oggi per il rapporto di "
        "prezzo rettificato — aumenti e frazionamenti si annullano, i dividendi no.",
        "Tablica miesięczna: skład zmienia się z miesiąca na miesiąc, więc wejścia i wyjścia "
        "zostają w obrazie. Dawna wartość to dzisiejsza wartość całkowita razy skorygowany "
        "stosunek cen — emisje i splity się znoszą, dywidendy nie.",
        "Um quadro mensal: os membros mudam de mês a mês, então entradas e saídas ficam na "
        "imagem. Um valor passado é o valor total de hoje vezes a razão de preços ajustada — "
        "bonificações e desdobramentos se cancelam, os dividendos não.",
        "Měsíční tabule: členství se mění měsíc od měsíce, takže vstupy i výstupy zůstávají v "
        "obraze. Dřívější hodnota je dnešní celková hodnota krát upravený poměr cen — emise a "
        "štěpení se vyruší, dividendy ne.",
        "Aylık bir tablo: üyelik aydan aya değişir, giriş ve çıkışlar karede kalır. Geçmiş bir "
        "değer, bugünkü toplam değerin düzeltilmiş fiyat oranıyla çarpımıdır — bedelsiz "
        "artırımlar ve bölünmeler götürür, temettüler götürmez.",
        "Помесячное табло: состав меняется от месяца к месяцу, поэтому вход и выход остаются в "
        "кадре. Прошлая стоимость — сегодняшняя полная стоимость на скорректированное отношение "
        "цен; допэмиссии и дробления сокращаются, дивиденды — нет.",
        "月ごとのボードです。顔ぶれは毎月変わるので、入榜と落榜の両方が画面に残ります。過去の "
        "時価総額は、今日の時価総額に調整済み価格比率を掛けたもの。増資や分割は相殺され、配当は "
        "相殺されません。",
        "월 단위 보드입니다. 명단은 매달 바뀌므로 진입과 이탈이 모두 화면에 남습니다. 과거 "
        "시가총액은 오늘의 시가총액에 조정 주가 비율을 곱한 값이며, 무상증자와 액면분할은 "
        "상쇄되고 배당은 그렇지 않습니다.",
        "按月的市值榜：名次每個月都在變，進榜與出榜都留在畫面上。過去的市值＝今日總市值 × "
        "期間複權價格比——送股與拆股會互相抵消，分紅不會，所以高分紅公司的歷史市值偏低。",
        "按月的市值榜：名次每个月都在变，进榜与出榜都留在画面上。过去的市值＝今日总市值 × "
        "区间复权价格比——送股与拆股会互相抵消，分红不会，所以高分红公司的历史市值偏低。"]),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224: root node not found` —
    which names the root element, points at the project file, and says nothing about the
    two company names that caused it (Procter & Gamble, AT&T). Escaped here rather than in
    the table above, so the names stay readable where they are written down.
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

        for code, hans, english in POOL:
            key = "INST" + "".join(c for c in code if c.isalnum()).upper()

            if tag == "zh-Hans":
                value = hans
            elif tag == "zh-Hant":
                value = traditional(hans)
            else:
                value = english

            lines.append(entry(key, value))

        for key, values in REWRITTEN:
            lines.append(entry(key, values[LANGS.index(tag)]))

        # Out with the old, in with the new — same rules as the sibling script: the base name
        # (so `X` and `X.Text` both go), and `[^>]*` (the file holds single-line entries and
        # hand-edited ones with xml:space).
        for code, _, _ in POOL:
            key = "INST" + "".join(c for c in code if c.isalnum()).upper()
            text = re.sub(rf'  <data name="{key}"[^>]*>.*?</data>\n', "", text, flags=re.S)

        for key, _ in REWRITTEN:
            base = key.split(".")[0]
            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at = text.rfind("</root>")
        assert at > 0, f"{tag}: no </root>"

        path.write_bytes((text[:at] + "".join(lines) + text[at:]).encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
