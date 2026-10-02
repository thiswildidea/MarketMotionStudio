# -*- coding: utf-8 -*-
r"""把「AH 溢价」这一页的 resw 键注入 14 份 Resources.resw。

两类键：

* **INST\*** —— 69 对里 40 个还没有名字的 A 腿。键名规则与 C# `InstrumentNames.Key`
  一致：`INST` + 代码的字母数字，全大写（`sh601328` -> `INSTSH601328`）。
  缺这一层，画面就会把行情源的中文画进去（本次实测里 `XD中国石`、`XD海螺水`、
  `万  科Ａ` 都是源端当天返回的脏名字）。
* **页面文案** —— 导航名、标题、副标题、名单说明、口径说明、状态行、进度与两条错误、
  量词「对」、「最长」那一档。

命名风格与既有的 80 个标的保持一致（见 `port-marketcap-resw.py`）：
欧洲语言用官方英文名，日文用汉字/片假名写法，韩文用汉字词或通用音译，繁体按字表转。

用法：python tools\port-ahpremium-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]


def row(code, hans, thirteen):
    """13 列译文 + 简体中文源名，凑成 14 列。"""
    assert len(thirteen) == 13, f"{code}: {len(thirteen)} columns, expected 13"

    return (code, [*thirteen, hans])


# ---- 40 个新标的 -------------------------------------------------------------------
# 列序：en de es fr it pl pt-BR cs tr ru ja ko zh-Hant（+ zh-Hans 取第一列参数）

INSTRUMENTS = [
    row("sh601328", "交通银行", [
        "Bank of Communications", "Bank of Communications", "Bank of Communications",
        "Bank of Communications", "Bank of Communications", "Bank of Communications",
        "Bank of Communications", "Bank of Communications", "Bank of Communications",
        "Bank of Communications", "交通銀行", "교통은행", "交通銀行"]),
    row("sh601319", "中国人保", [
        "PICC", "PICC", "PICC", "PICC", "PICC", "PICC", "PICC", "PICC", "PICC",
        "PICC", "中国人民保険", "인민보험", "中國人保"]),
    row("sh600938", "中国海油", [
        "CNOOC", "CNOOC", "CNOOC", "CNOOC", "CNOOC", "CNOOC", "CNOOC", "CNOOC",
        "CNOOC", "CNOOC", "中国海洋石油", "중국해양석유", "中國海油"]),
    row("sh601898", "中煤能源", [
        "China Coal", "China Coal", "China Coal", "China Coal", "China Coal",
        "China Coal", "China Coal", "China Coal", "China Coal", "China Coal",
        "中煤能源", "중메이에너지", "中煤能源"]),
    row("sh600188", "兖矿能源", [
        "Yankuang Energy", "Yankuang Energy", "Yankuang Energy", "Yankuang Energy",
        "Yankuang Energy", "Yankuang Energy", "Yankuang Energy", "Yankuang Energy",
        "Yankuang Energy", "Yankuang Energy", "兖鉱能源", "연광에너지", "兗礦能源"]),
    row("sh601600", "中国铝业", [
        "Chalco", "Chalco", "Chalco", "Chalco", "Chalco", "Chalco", "Chalco",
        "Chalco", "Chalco", "Chalco", "中国アルミ", "중국알루미늄", "中國鋁業"]),
    row("sh600362", "江西铜业", [
        "Jiangxi Copper", "Jiangxi Copper", "Jiangxi Copper", "Jiangxi Copper",
        "Jiangxi Copper", "Jiangxi Copper", "Jiangxi Copper", "Jiangxi Copper",
        "Jiangxi Copper", "Jiangxi Copper", "江西銅業", "장시동업", "江西銅業"]),
    row("sh603993", "洛阳钼业", [
        "China Molybdenum", "China Molybdenum", "China Molybdenum", "China Molybdenum",
        "China Molybdenum", "China Molybdenum", "China Molybdenum", "China Molybdenum",
        "China Molybdenum", "China Molybdenum", "洛陽モリブデン", "뤄양몰리브덴", "洛陽鉬業"]),
    row("sz000898", "鞍钢股份", [
        "Angang Steel", "Angang Steel", "Angang Steel", "Angang Steel", "Angang Steel",
        "Angang Steel", "Angang Steel", "Angang Steel", "Angang Steel", "Angang Steel",
        "鞍鋼股份", "안강강철", "鞍鋼股份"]),
    row("sh600808", "马钢股份", [
        "Maanshan Iron & Steel", "Maanshan Iron & Steel", "Maanshan Iron & Steel",
        "Maanshan Iron & Steel", "Maanshan Iron & Steel", "Maanshan Iron & Steel",
        "Maanshan Iron & Steel", "Maanshan Iron & Steel", "Maanshan Iron & Steel",
        "Maanshan Iron & Steel", "馬鞍山鋼鉄", "마안산강철", "馬鋼股份"]),
    row("sh601800", "中国交建", [
        "CCCC", "CCCC", "CCCC", "CCCC", "CCCC", "CCCC", "CCCC", "CCCC", "CCCC",
        "CCCC", "中国交通建設", "중국교통건설", "中國交建"]),
    row("sh601618", "中国中冶", [
        "MCC", "MCC", "MCC", "MCC", "MCC", "MCC", "MCC", "MCC", "MCC", "MCC",
        "中国冶金", "중국야금", "中國中冶"]),
    row("sh601238", "广汽集团", [
        "GAC Group", "GAC Group", "GAC Group", "GAC Group", "GAC Group", "GAC Group",
        "GAC Group", "GAC Group", "GAC Group", "GAC Group", "広汽グループ",
        "광치그룹", "廣汽集團"]),
    row("sz000338", "潍柴动力", [
        "Weichai Power", "Weichai Power", "Weichai Power", "Weichai Power",
        "Weichai Power", "Weichai Power", "Weichai Power", "Weichai Power",
        "Weichai Power", "Weichai Power", "濰柴動力", "웨이차이파워", "濰柴動力"]),
    row("sh600115", "中国东航", [
        "China Eastern Airlines", "China Eastern Airlines", "China Eastern Airlines",
        "China Eastern Airlines", "China Eastern Airlines", "China Eastern Airlines",
        "China Eastern Airlines", "China Eastern Airlines", "China Eastern Airlines",
        "China Eastern Airlines", "中国東方航空", "중국동방항공", "中國東航"]),
    row("sh600029", "南方航空", [
        "China Southern Airlines", "China Southern Airlines", "China Southern Airlines",
        "China Southern Airlines", "China Southern Airlines", "China Southern Airlines",
        "China Southern Airlines", "China Southern Airlines", "China Southern Airlines",
        "China Southern Airlines", "中国南方航空", "중국남방항공", "南方航空"]),
    row("sh601992", "金隅集团", [
        "BBMG", "BBMG", "BBMG", "BBMG", "BBMG", "BBMG", "BBMG", "BBMG", "BBMG",
        "BBMG", "金隅集団", "진위그룹", "金隅集團"]),
    row("sh600011", "华能国际", [
        "Huaneng Power", "Huaneng Power", "Huaneng Power", "Huaneng Power",
        "Huaneng Power", "Huaneng Power", "Huaneng Power", "Huaneng Power",
        "Huaneng Power", "Huaneng Power", "華能国際電力", "화넝전력", "華能國際"]),
    row("sh601991", "大唐发电", [
        "Datang Power", "Datang Power", "Datang Power", "Datang Power", "Datang Power",
        "Datang Power", "Datang Power", "Datang Power", "Datang Power", "Datang Power",
        "大唐発電", "다탕발전", "大唐發電"]),
    row("sh600027", "华电国际", [
        "Huadian Power", "Huadian Power", "Huadian Power", "Huadian Power",
        "Huadian Power", "Huadian Power", "Huadian Power", "Huadian Power",
        "Huadian Power", "Huadian Power", "華電国際電力", "화뎬전력", "華電國際"]),
    row("sz003816", "中国广核", [
        "CGN Power", "CGN Power", "CGN Power", "CGN Power", "CGN Power", "CGN Power",
        "CGN Power", "CGN Power", "CGN Power", "CGN Power", "中広核", "CGN파워", "中國廣核"]),
    row("sh601607", "上海医药", [
        "Shanghai Pharma", "Shanghai Pharma", "Shanghai Pharma", "Shanghai Pharma",
        "Shanghai Pharma", "Shanghai Pharma", "Shanghai Pharma", "Shanghai Pharma",
        "Shanghai Pharma", "Shanghai Pharma", "上海医薬", "상하이의약", "上海醫藥"]),
    row("sh600196", "复星医药", [
        "Fosun Pharma", "Fosun Pharma", "Fosun Pharma", "Fosun Pharma", "Fosun Pharma",
        "Fosun Pharma", "Fosun Pharma", "Fosun Pharma", "Fosun Pharma", "Fosun Pharma",
        "復星医薬", "포선제약", "復星醫藥"]),
    row("sh600332", "白云山", [
        "Baiyunshan", "Baiyunshan", "Baiyunshan", "Baiyunshan", "Baiyunshan",
        "Baiyunshan", "Baiyunshan", "Baiyunshan", "Baiyunshan", "Baiyunshan",
        "白雲山", "바이윈산", "白雲山"]),
    row("sz000756", "新华制药", [
        "Xinhua Pharma", "Xinhua Pharma", "Xinhua Pharma", "Xinhua Pharma",
        "Xinhua Pharma", "Xinhua Pharma", "Xinhua Pharma", "Xinhua Pharma",
        "Xinhua Pharma", "Xinhua Pharma", "山東新華製薬", "산둥신화제약", "新華製藥"]),
    row("sz000513", "丽珠集团", [
        "Livzon Pharma", "Livzon Pharma", "Livzon Pharma", "Livzon Pharma",
        "Livzon Pharma", "Livzon Pharma", "Livzon Pharma", "Livzon Pharma",
        "Livzon Pharma", "Livzon Pharma", "麗珠医薬", "리주제약", "麗珠集團"]),
    row("sz300759", "康龙化成", [
        "Pharmaron", "Pharmaron", "Pharmaron", "Pharmaron", "Pharmaron", "Pharmaron",
        "Pharmaron", "Pharmaron", "Pharmaron", "Pharmaron", "康龍化成", "파마론", "康龍化成"]),
    row("sz300347", "泰格医药", [
        "Tigermed", "Tigermed", "Tigermed", "Tigermed", "Tigermed", "Tigermed",
        "Tigermed", "Tigermed", "Tigermed", "Tigermed", "泰格医薬", "타이거메드", "泰格醫藥"]),
    row("sh601888", "中国中免", [
        "CTG Duty Free", "CTG Duty Free", "CTG Duty Free", "CTG Duty Free",
        "CTG Duty Free", "CTG Duty Free", "CTG Duty Free", "CTG Duty Free",
        "CTG Duty Free", "CTG Duty Free", "中国中免", "CTG듀티프리", "中國中免"]),
    row("sh600660", "福耀玻璃", [
        "Fuyao Glass", "Fuyao Glass", "Fuyao Glass", "Fuyao Glass", "Fuyao Glass",
        "Fuyao Glass", "Fuyao Glass", "Fuyao Glass", "Fuyao Glass", "Fuyao Glass",
        "福耀ガラス", "푸야오글라스", "福耀玻璃"]),
    row("sh601919", "中远海控", [
        "COSCO Shipping", "COSCO Shipping", "COSCO Shipping", "COSCO Shipping",
        "COSCO Shipping", "COSCO Shipping", "COSCO Shipping", "COSCO Shipping",
        "COSCO Shipping", "COSCO Shipping", "中遠海運控股", "코스코해운", "中遠海控"]),
    row("sh600026", "中远海能", [
        "COSCO Shipping Energy", "COSCO Shipping Energy", "COSCO Shipping Energy",
        "COSCO Shipping Energy", "COSCO Shipping Energy", "COSCO Shipping Energy",
        "COSCO Shipping Energy", "COSCO Shipping Energy", "COSCO Shipping Energy",
        "COSCO Shipping Energy", "中遠海運能源", "코스코해운에너지", "中遠海能"]),
    row("sh600999", "招商证券", [
        "China Merchants Securities", "China Merchants Securities",
        "China Merchants Securities", "China Merchants Securities",
        "China Merchants Securities", "China Merchants Securities",
        "China Merchants Securities", "China Merchants Securities",
        "China Merchants Securities", "China Merchants Securities",
        "招商証券", "자오상증권", "招商證券"]),
    row("sh601211", "国泰海通", [
        "Guotai Haitong", "Guotai Haitong", "Guotai Haitong", "Guotai Haitong",
        "Guotai Haitong", "Guotai Haitong", "Guotai Haitong", "Guotai Haitong",
        "Guotai Haitong", "Guotai Haitong", "国泰海通", "궈타이하이퉁", "國泰海通"]),
    row("sz000776", "广发证券", [
        "GF Securities", "GF Securities", "GF Securities", "GF Securities",
        "GF Securities", "GF Securities", "GF Securities", "GF Securities",
        "GF Securities", "GF Securities", "広発証券", "광파증권", "廣發證券"]),
    row("sh601688", "华泰证券", [
        "Huatai Securities", "Huatai Securities", "Huatai Securities", "Huatai Securities",
        "Huatai Securities", "Huatai Securities", "Huatai Securities", "Huatai Securities",
        "Huatai Securities", "Huatai Securities", "華泰証券", "화타이증권", "華泰證券"]),
    row("sh601881", "中国银河", [
        "China Galaxy Securities", "China Galaxy Securities", "China Galaxy Securities",
        "China Galaxy Securities", "China Galaxy Securities", "China Galaxy Securities",
        "China Galaxy Securities", "China Galaxy Securities", "China Galaxy Securities",
        "China Galaxy Securities", "中国銀河証券", "중국은허증권", "中國銀河"]),
    row("sh600958", "东方证券", [
        "Orient Securities", "Orient Securities", "Orient Securities", "Orient Securities",
        "Orient Securities", "Orient Securities", "Orient Securities", "Orient Securities",
        "Orient Securities", "Orient Securities", "東方証券", "동방증권", "東方證券"]),
    row("sh601788", "光大证券", [
        "Everbright Securities", "Everbright Securities", "Everbright Securities",
        "Everbright Securities", "Everbright Securities", "Everbright Securities",
        "Everbright Securities", "Everbright Securities", "Everbright Securities",
        "Everbright Securities", "光大証券", "광다증권", "光大證券"]),
    row("sz000166", "申万宏源", [
        "Shenwan Hongyuan", "Shenwan Hongyuan", "Shenwan Hongyuan", "Shenwan Hongyuan",
        "Shenwan Hongyuan", "Shenwan Hongyuan", "Shenwan Hongyuan", "Shenwan Hongyuan",
        "Shenwan Hongyuan", "Shenwan Hongyuan", "申万宏源", "선완훙위안", "申萬宏源"]),
]

# ---- 页面文案 ----------------------------------------------------------------------
# 列序同上。带 `.Text` 的键走 x:Uid，必须是 `键.属性` 的形状。

PAGE = [
    ("NavAhPremium.Content", [
        "AH premium", "A/H-Prämie", "Prima A/H", "Prime A/H", "Premio A/H",
        "Premia A/H", "Prêmio A/H", "Prémie A/H", "A/H primi", "Премия A/H",
        "A/H プレミアム", "A/H 프리미엄", "AH 溢價", "AH 溢价"]),

    ("AhPremiumPageTitle.Text", [
        "AH premium", "A/H-Prämie", "Prima A/H", "Prime A/H", "Premio A/H",
        "Premia A/H", "Prêmio A/H", "Prémie A/H", "A/H primi", "Премия A/H",
        "A/H プレミアム", "A/H 프리미엄", "AH 溢價", "AH 溢价"]),

    ("AhPremiumStageTitle", [
        "AH premium", "A/H-Prämie", "Prima A/H", "Prime A/H", "Premio A/H",
        "Premia A/H", "Prêmio A/H", "Prémie A/H", "A/H primi", "Премия A/H",
        "A/H プレミアム", "A/H 프리미엄", "AH 溢價", "AH 溢价"]),

    ("AhPremiumPageSubtitle.Text", [
        "One company, two listings, two currencies — how much more expensive the mainland "
        "share is, month by month, as bars that overtake one another.",
        "Ein Unternehmen, zwei Notierungen, zwei Währungen — wie viel teurer die A-Aktie ist, "
        "Monat für Monat, als Balken, die sich überholen.",
        "Una empresa, dos cotizaciones, dos monedas: cuánto más cara es la acción A, mes a mes, "
        "en barras que se adelantan.",
        "Une entreprise, deux cotations, deux monnaies — de combien l'action A est plus chère, "
        "mois après mois, en barres qui se dépassent.",
        "Una società, due quotazioni, due valute: quanto costa in più l'azione A, mese per mese, "
        "in barre che si sorpassano.",
        "Jedna spółka, dwa notowania, dwie waluty — o ile droższa jest akcja A, miesiąc po "
        "miesiącu, jako słupki, które się wyprzedzają.",
        "Uma empresa, duas cotações, duas moedas — quanto mais cara é a ação A, mês a mês, em "
        "barras que se ultrapassam.",
        "Jedna společnost, dvě kotace, dvě měny — o kolik je akcie A dražší, měsíc po měsíci, "
        "jako pruhy, které se předhánějí.",
        "Tek şirket, iki kote, iki para birimi — A hissesi ne kadar daha pahalı, ay ay, "
        "birbirini geçen çubuklar olarak.",
        "Одна компания, два листинга, две валюты — насколько дороже её бумага на материке, "
        "месяц за месяцем, полосами, которые обгоняют друг друга.",
        "同じ企業が二つの市場で付ける価格差——A 株が何割高いかを、月ごとに並べて追い抜き合います。",
        "같은 기업이 두 시장에서 받는 가격 차이—A주가 얼마나 더 비싼지를 월 단위로 늘어놓고 "
        "서로 추월합니다.",
        "同一家公司在兩個市場的價差——A 股比 H 股貴多少，按月排成一列互相超車。",
        "同一家公司在两个市场的价差——A 股比 H 股贵多少，按月排成一列互相超车。"]),

    ("AhPremiumListLabel", [
        "{0} A+H pairs", "{0} A+H-Paare", "{0} pares A+H", "{0} paires A+H",
        "{0} coppie A+H", "{0} par A+H", "{0} pares A+H", "{0} párů A+H",
        "{0} A+H çifti", "{0} пар A+H", "{0} 組の A+H", "{0}개 A+H", "{0} 對 A+H",
        "{0} 对 A+H"]),

    ("AhPremiumUnitPairs", [
        "pairs", "Paare", "pares", "paires", "coppie", "par", "pares", "párů",
        "çift", "пар", "組", "개", "對", "对"]),

    ("AhPremiumCount", [
        "Famous companies listed on both sides: A shares on the mainland and H shares in Hong "
        "Kong. The longer the span, the fewer pairs qualify — one whose Hong Kong listing is "
        "younger than two years is left out. Each frame shows the {0} with the highest premium.",
        "Bekannte Unternehmen, die beidseitig notieren: A-Aktien auf dem Festland, H-Aktien in "
        "Hongkong. Je länger der Zeitraum, desto weniger Paare bleiben — ein Paar, dessen "
        "Hongkong-Notierung jünger als zwei Jahre ist, entfällt. Jedes Bild zeigt die {0} mit "
        "der höchsten Prämie.",
        "Compañías conocidas cotizadas en ambos lados: acciones A en el continente y acciones H "
        "en Hong Kong. Cuanto más largo el periodo, menos pares quedan: uno cuya cotización en "
        "Hong Kong no llega a dos años se descarta. Cada fotograma muestra los {0} con mayor prima.",
        "Des sociétés connues cotées des deux côtés : actions A sur le continent, actions H à "
        "Hong Kong. Plus la période est longue, moins il reste de paires — une paire dont la "
        "cotation à Hong Kong a moins de deux ans est écartée. Chaque image montre les {0} à "
        "prime la plus élevée.",
        "Società note quotate su entrambi i lati: azioni A sul continente, azioni H a Hong Kong. "
        "Più lungo il periodo, meno coppie restano — una coppia la cui quotazione a Hong Kong ha "
        "meno di due anni viene esclusa. Ogni fotogramma mostra le {0} con il premio più alto.",
        "Znane spółki notowane po obu stronach: akcje A na kontynencie, akcje H w Hongkongu. "
        "Im dłuższy okres, tym mniej par — para, której notowanie w Hongkongu ma mniej niż dwa "
        "lata, wypada. Każda klatka pokazuje {0} o najwyższej premii.",
        "Companhias conhecidas cotadas nos dois lados: ações A no continente e ações H em Hong "
        "Kong. Quanto maior o período, menos pares restam — um par cuja cotação em Hong Kong tem "
        "menos de dois anos fica de fora. Cada quadro mostra os {0} de maior prêmio.",
        "Známé společnosti kotované na obou stranách: akcie A na pevnině, akcie H v Hongkongu. "
        "Čím delší období, tím méně párů — pár, jehož hongkongská kotace je mladší než dva roky, "
        "vypadne. Každý snímek ukazuje {0} s nejvyšší prémií.",
        "İki tarafta kote olan tanıdık şirketler: karada A hissesi, Hong Kong'da H hissesi. "
        "Dönem uzadıkça uygun çift sayısı azalır — Hong Kong kotesi iki yıldan genç olan çift "
        "dışarıda kalır. Her kare, primi en yüksek {0} çifti gösterir.",
        "Известные компании, торгующиеся с двух сторон: A-акции на материке и H-акции в "
        "Гонконге. Чем длиннее период, тем меньше остаётся пар — пара, чей гонконгский листинг "
        "моложе двух лет, отбрасывается. В каждом кадре — {0} с наибольшей премией.",
        "本土と香港の両方に上場する有名企業です。期間を長く取るほど残る組は減ります——"
        "香港上場が 2 年に満たない組は外れます。各フレームにはプレミアムの高い {0} 組を表示します。",
        "본토와 홍콩 양쪽에 상장된 유명 기업입니다. 기간이 길수록 남는 쌍이 줄어듭니다——"
        "홍콩 상장이 2년이 안 된 쌍은 제외됩니다. 각 프레임은 프리미엄이 가장 높은 {0}쌍을 보여줍니다.",
        "兩地上市的知名公司：A 股在本土，H 股在香港。區間越長，合格的对越少——H 股上市不足兩年的"
        "會被去掉。每一幀顯示溢價最高的 {0} 對。",
        "两地上市的知名公司：A 股在本土，H 股在香港。区间越长，合格的對越少——H 股上市不足两年的"
        "会被去掉。每一帧显示溢价最高的 {0} 对。"]),

    ("AhPremiumMethodNote.Text", [
        "Premium = A price ÷ (H price × HKD/CNY) − 1. Both legs are prices actually paid — no "
        "adjustment — because a backward-adjusted series inflates recent prices, and two markets "
        "adjusted separately cannot be compared. The rate is a mid rate from a public quote "
        "service. Some services state the same gap the other way round — H against A, and "
        "negative — which is the reciprocal of this figure, not another price.",
        "Prämie = A-Kurs ÷ (H-Kurs × HKD/CNY) − 1. Beide Seiten sind tatsächlich gezahlte Kurse — "
        "ohne Bereinigung, weil eine rückwärts bereinigte Reihe junge Kurse aufbläht und zwei "
        "getrennt bereinigte Märkte nicht vergleichbar sind. Der Kurs ist ein Mittelkurs aus "
        "einem öffentlichen Kursdienst. Manche Dienste nennen dieselbe Lücke umgekehrt — H gegen "
        "A, negativ —, und das ist der Kehrwert dieser Zahl, kein anderer Kurs.",
        "Prima = precio A ÷ (precio H × HKD/CNY) − 1. Ambas partes son precios realmente "
        "pagados —sin ajuste—, porque una serie ajustada hacia atrás infla los precios recientes "
        "y dos mercados ajustados por separado no son comparables. El tipo es un tipo medio de "
        "un servicio público de cotizaciones. Algunos servicios dan la misma diferencia al revés "
        "— H frente a A, en negativo —, y eso es el recíproco de esta cifra, no otro precio.",
        "Prime = cours A ÷ (cours H × HKD/CNY) − 1. Les deux jambes sont des cours réellement "
        "payés — sans ajustement —, car une série ajustée vers l'arrière gonfle les cours "
        "récents et deux marchés ajustés séparément ne se comparent pas. Le taux est un taux "
        "moyen d'un service de cotation public. Certains services donnent le même écart à "
        "l'envers — H contre A, en négatif —, soit l'inverse de ce chiffre, pas un autre cours.",
        "Premio = prezzo A ÷ (prezzo H × HKD/CNY) − 1. Entrambe le gambe sono prezzi realmente "
        "pagati — nessun aggiustamento —, perché una serie rettificata all'indietro gonfia i "
        "prezzi recenti e due mercati rettificati separatamente non sono confrontabili. Il cambio "
        "è un cambio medio da un servizio pubblico di quotazioni. Alcuni servizi mostrano lo "
        "stesso divario al contrario — H contro A, in negativo —: è il reciproco di questa cifra, "
        "non un altro prezzo.",
        "Premia = kurs A ÷ (kurs H × HKD/CNY) − 1. Obie nogi to kursy faktycznie płacone — bez "
        "korekty — bo seria korygowana wstecz zawyża ostatnie kursy, a dwóch rynków korygowanych "
        "osobno nie da się porównać. Kurs to kurs średni z publicznego serwisu notowań. Niektóre "
        "serwisy podają tę samą różnicę odwrotnie — H do A, na minusie —, a to odwrotność tej "
        "liczby, nie inny kurs.",
        "Prêmio = preço A ÷ (preço H × HKD/CNY) − 1. As duas pontas são preços realmente pagos — "
        "sem ajuste —, porque uma série ajustada para trás infla os preços recentes e dois "
        "mercados ajustados separadamente não são comparáveis. A taxa é uma taxa média de um "
        "serviço público de cotações. Alguns serviços mostram a mesma diferença ao contrário — H "
        "contra A, em negativo —, e isso é o inverso deste número, não outro preço.",
        "Prémie = kurz A ÷ (kurz H × HKD/CNY) − 1. Obě strany jsou skutečně placené kurzy — bez "
        "úpravy —, protože zpětně upravená řada nafukuje nedávné kurzy a dva trhy upravené "
        "odděleně srovnávat nelze. Kurz je střední kurz z veřejné služby kotací. Některé služby "
        "uvádějí stejnou mezeru obráceně — H vůči A, v záporu —, což je převrácená hodnota tohoto "
        "čísla, ne jiný kurz.",
        "Prim = A fiyatı ÷ (H fiyatı × HKD/CNY) − 1. İki bacak da gerçekten ödenen fiyatlardır — "
        "düzeltme yok —, çünkü geriye dönük düzeltilmiş seri son fiyatları şişirir ve ayrı ayrı "
        "düzeltilmiş iki piyasa karşılaştırılamaz. Kur, halka açık bir kotasyon servisinden "
        "alınan orta kurdur. Bazı servisler aynı farkı ters yönde verir — H'ye karşı A, negatif "
        "olarak —, ki bu bu sayının tersidir, başka bir fiyat değil.",
        "Премия = цена A ÷ (цена H × HKD/CNY) − 1. Обе ноги — фактически уплаченные цены, без "
        "корректировки: ряд, скорректированный назад, завышает недавние цены, а два рынка, "
        "скорректированные по отдельности, сравнивать нельзя. Курс — средний, из публичного "
        "сервиса котировок. Некоторые сервисы показывают тот же разрыв наоборот — H к A, со "
        "знаком минус —, и это обратная величина этого числа, а не другая цена.",
        "プレミアム = A 株価 ÷（H 株価 × 香港ドル/人民元）− 1。両方とも実際に売買された価格を使い、"
        "調整はかけません——後方修正した系列は直近の価格を膨らませ、別々に調整した二つの市場は"
        "比べられないからです。為替は公開相場サービスの中値です。同じ差を逆向き（H 対 A、"
        "マイナス表記）で出す行情サイトもありますが、それはこの数字の逆数であって、"
        "別の価格ではありません。",
        "프리미엄 = A 가격 ÷ (H 가격 × 홍콩달러/위안) − 1. 두 쪽 모두 실제로 거래된 가격이며 "
        "조정하지 않습니다——후방 조정 계열은 최근 가격을 부풀리고, 따로 조정한 두 시장은 "
        "비교할 수 없기 때문입니다. 환율은 공개 시세 서비스의 중간값입니다. 같은 차이를 "
        "반대로(H 대비 A, 마이너스) 표기하는 사이트도 있는데, 그것은 이 숫자의 역수일 뿐 "
        "다른 가격이 아닙니다.",
        "溢價 = A 股價 ÷（H 股價 × 港元兌人民幣）− 1。兩條腿都用實際成交價，不做任何調整——"
        "後復權會把近期價格放大，而兩個市場各自調整後不能直接比。匯率取公開行情服務的中間價。"
        "有些行情站把同一個差距倒過來寫（H 對 A，帶負號），那是這個數字的倒數，不是另一個價格。",
        "溢价 = A 股价 ÷（H 股价 × 港元兑人民币）− 1。两条腿都用实际成交价，不做任何调整——"
        "后复权会把近期价格放大，而两个市场各自调整后不能直接比。汇率取公开行情服务的中间价。"
        "有些行情站把同一个差距倒过来写（H 对 A，带负号），那是这个数字的倒数，不是另一个价格。"]),

    # 「榜尾」而不是「最便宜」：画面画的是溢价最高的 15 家，第 15 名仍是 +78.8%，
    # 叫它"最便宜"会让人以为场上有个负溢价的公司在榜上——真正负溢价的两家
    # （招商银行、药明康德）排在名单末尾，进不了这 15 名。
    ("AhPremiumFetched", [
        "{0} 对 · {1} 个月 · 最高 {2} {3} · 榜尾 {4} {5}",
        "{0} Paare · {1} Monate · höchste {2} {3} · Schlusslicht {4} {5}",
        "{0} pares · {1} meses · más alta {2} {3} · último del cuadro {4} {5}",
        "{0} paires · {1} mois · plus forte {2} {3} · dernière du classement {4} {5}",
        "{0} coppie · {1} mesi · più alto {2} {3} · ultimo in classifica {4} {5}",
        "{0} par · {1} miesięcy · najwyższa {2} {3} · ostatnia w tabeli {4} {5}",
        "{0} pares · {1} meses · maior {2} {3} · último do quadro {4} {5}",
        "{0} párů · {1} měsíců · nejvyšší {2} {3} · poslední v tabulce {4} {5}",
        "{0} çift · {1} ay · en yüksek {2} {3} · listenin sonu {4} {5}",
        "{0} пар · {1} месяцев · выше всех {2} {3} · последняя в списке {4} {5}",
        "{0} 組 · {1} か月 · 最高 {2} {3} · 最下位 {4} {5}",
        "{0}쌍 · {1}개월 · 최고 {2} {3} · 최하위 {4} {5}",
        "{0} 對 · {1} 個月 · 最高 {2} {3} · 榜尾 {4} {5}",
        "{0} 对 · {1} 个月 · 最高 {2} {3} · 榜尾 {4} {5}"]),

    ("AhPremiumReadingRate", [
        "Reading the exchange rate (HKD/CNY) …",
        "Wechselkurs wird gelesen (HKD/CNY) …",
        "Leyendo el tipo de cambio (HKD/CNY) …",
        "Lecture du taux de change (HKD/CNY) …",
        "Lettura del cambio (HKD/CNY) …",
        "Odczyt kursu (HKD/CNY) …",
        "Lendo a taxa de câmbio (HKD/CNY) …",
        "Načítání kurzu (HKD/CNY) …",
        "Döviz kuru okunuyor (HKD/CNY) …",
        "Читаю курс (HKD/CNY) …",
        "為替（香港ドル/人民元）を読み込んでいます …",
        "환율(홍콩달러/위안)을 읽는 중 …",
        "正在讀取匯率（港元兌人民幣）…",
        "正在读取汇率（港元兑人民币）…"]),

    ("AhPremiumNoRate", [
        "The exchange rate did not come back, so no premium can be worked out.",
        "Der Wechselkurs kam nicht zurück, also lässt sich keine Prämie berechnen.",
        "El tipo de cambio no llegó, así que no se puede calcular ninguna prima.",
        "Le taux de change n'est pas revenu : aucune prime ne peut être calculée.",
        "Il cambio non è arrivato, quindi nessun premio può essere calcolato.",
        "Kurs nie wrócił, więc nie da się obliczyć premii.",
        "A taxa de câmbio não voltou, então nenhum prêmio pode ser calculado.",
        "Kurz se nevrátil, takže prémii nelze spočítat.",
        "Döviz kuru gelmedi, dolayısıyla prim hesaplanamaz.",
        "Курс не пришёл, поэтому премию вычислить нельзя.",
        "為替が取得できなかったため、プレミアムを計算できません。",
        "환율을 받지 못해 프리미엄을 계산할 수 없습니다.",
        "取不到匯率，算不出溢價。",
        "取不到汇率，算不出溢价。"]),

    ("AhPremiumTooFew", [
        "Not enough pairs reach back over this span. Try a shorter one.",
        "Zu wenige Paare reichen über diesen Zeitraum zurück. Versuchen Sie einen kürzeren.",
        "Muy pocos pares cubren este periodo. Pruebe uno más corto.",
        "Trop peu de paires remontent sur cette période. Essayez une période plus courte.",
        "Troppe poche coppie coprono questo periodo. Provane uno più corto.",
        "Zbyt mało par sięga tego okresu. Spróbuj krótszego.",
        "Poucos pares cobrem este período. Tente um período mais curto.",
        "Na toto období se nedostane dost párů. Zkuste kratší.",
        "Bu dönemi kapsayan çift sayısı yetersiz. Daha kısa bir dönem deneyin.",
        "Слишком мало пар покрывают этот период. Возьмите короче.",
        "この期間をカバーする組が足りません。もっと短い期間をお試しください。",
        "이 기간을 채우는 쌍이 부족합니다. 더 짧은 기간을 선택하세요.",
        "能覆蓋這段區間的對太少，換短一點的區間試試。",
        "能覆盖这段区间的對太少，换短一点的区间试试。"]),

    ("AhRangeMax", [
        "Longest (about 9 years)", "Längste (etwa 9 Jahre)", "Más largo (unos 9 años)",
        "Le plus long (environ 9 ans)", "Il più lungo (circa 9 anni)",
        "Najdłuższy (około 9 lat)", "Mais longo (cerca de 9 anos)", "Nejdelší (asi 9 let)",
        "En uzun (yaklaşık 9 yıl)", "Самый длинный (около 9 лет)", "最長（約 9 年）",
        "최장(약 9년)", "最長（約 9 年）", "最长（约 9 年）"]),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML, and MakePri reports it as `PRI224: root node not found` —
    naming the root element and the project file, and saying nothing about the company name
    that caused it. "Maanshan Iron & Steel" is why this line exists.
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

        for code, values in INSTRUMENTS:
            key = "INST" + "".join(c for c in code if c.isalnum()).upper()
            lines.append(entry(key, values[LANGS.index(tag)]))

        for key, values in PAGE:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same name wherever it already sits, then append.
        for code, _ in INSTRUMENTS:
            key = "INST" + "".join(c for c in code if c.isalnum()).upper()
            text = re.sub(rf'  <data name="{key}">.*?</data>\n', "", text, flags=re.S)

        # The base name is what to match on, not the key: `AhPremiumMethodNote.Text` as a literal
        # never matches the bare `AhPremiumMethodNote` an earlier run could have left.
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
