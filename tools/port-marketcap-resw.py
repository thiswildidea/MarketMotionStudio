# -*- coding: utf-8 -*-
r"""把「市值榜」这一页要用的 resw 键注入 14 份 Resources.resw。

两类键：

* **INST\*** —— 榜单里 33 个新标的的显示名。键名规则与 C# `InstrumentNames.Key`
  一致：`INST` + 代码的字母数字，全大写（`usWMT.OQ` -> `INSTUSWMTOQ`）。
  没有这一层的名字会直接把行情源的中文画进画面，14 种语言里 13 种是中文
  —— 而且快照端点还会返回「XD中国移」这种带除息前缀的脏名字。
* **页面文案** —— 标题、副标题、口径说明、状态行、三个市值单位。

两种文件格式的坑都在这里避开了：resw 是 UTF-8 **带 BOM** + LF，必须
`read_bytes().decode('utf-8-sig')` 读、`write_bytes()` 写回，`read_text/write_text`
会把 CRLF 归一成 LF，git 上表现为整文件重写。条目是单行格式
`<data name="KEY"><value>VALUE</value></data>`，插在 `</root>` 之前。

幂等：先删掉同名键再插入，跑几遍结果一样。英文/德文等欧洲语言里中国公司用
官方英文名，日文用汉字写法，韩文用韩文汉字词或通用音译 —— 与既有 80 个标的
的做法一致。

用法：python tools\port-marketcap-resw.py
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


# ---- 33 个新标的 -------------------------------------------------------------------
# 列序：en de es fr it pl pt-BR cs tr ru ja ko zh-Hant（+ zh-Hans 取第一列参数）

INSTRUMENTS = [
    # -- A 股 12 -------------------------------------------------------------------
    row("sh601398", "工商银行",
        ["ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC",
         "工商銀行", "공상은행", "工商銀行"]),
    row("sh601939", "建设银行",
        ["CCB", "CCB", "CCB", "CCB", "CCB", "CCB", "CCB", "CCB", "CCB", "CCB",
         "建設銀行", "건설은행", "建設銀行"]),
    row("sh601288", "农业银行",
        ["ABC", "ABC", "ABC", "ABC", "ABC", "ABC", "ABC", "ABC", "ABC", "ABC",
         "農業銀行", "농업은행", "農業銀行"]),
    row("sh601988", "中国银行",
        ["Bank of China", "Bank of China", "Bank of China", "Bank of China", "Bank of China",
         "Bank of China", "Bank of China", "Bank of China", "Bank of China", "Bank of China",
         "中国銀行", "중국은행", "中國銀行"]),
    row("sh600941", "中国移动",
        ["China Mobile", "China Mobile", "China Mobile", "China Mobile", "China Mobile",
         "China Mobile", "China Mobile", "China Mobile", "China Mobile", "China Mobile",
         "中国移動", "중국이동", "中國移動"]),
    row("sh601857", "中国石油",
        ["PetroChina", "PetroChina", "PetroChina", "PetroChina", "PetroChina",
         "PetroChina", "PetroChina", "PetroChina", "PetroChina", "PetroChina",
         "中国石油", "페트로차이나", "中國石油"]),
    row("sh600028", "中国石化",
        ["Sinopec", "Sinopec", "Sinopec", "Sinopec", "Sinopec",
         "Sinopec", "Sinopec", "Sinopec", "Sinopec", "Sinopec",
         "中国石化", "시노펙", "中國石化"]),
    row("sz300750", "宁德时代",
        ["CATL", "CATL", "CATL", "CATL", "CATL", "CATL", "CATL", "CATL", "CATL", "CATL",
         "寧徳時代", "CATL", "寧德時代"]),
    row("sh601138", "工业富联",
        ["Foxconn", "Foxconn", "Foxconn", "Foxconn", "Foxconn",
         "Foxconn", "Foxconn", "Foxconn", "Foxconn", "Foxconn",
         "工業富聯", "폭스콘", "工業富聯"]),
    row("sh601628", "中国人寿",
        ["China Life", "China Life", "China Life", "China Life", "China Life",
         "China Life", "China Life", "China Life", "China Life", "China Life",
         "中国人寿", "중국인수보험", "中國人壽"]),
    row("sh601088", "中国神华",
        ["Shenhua Energy", "Shenhua Energy", "Shenhua Energy", "Shenhua Energy", "Shenhua Energy",
         "Shenhua Energy", "Shenhua Energy", "Shenhua Energy", "Shenhua Energy", "Shenhua Energy",
         "中国神華", "선화에너지", "中國神華"]),
    row("sh601899", "紫金矿业",
        ["Zijin Mining", "Zijin Mining", "Zijin Mining", "Zijin Mining", "Zijin Mining",
         "Zijin Mining", "Zijin Mining", "Zijin Mining", "Zijin Mining", "Zijin Mining",
         "紫金鉱業", "쯔진광업", "紫金礦業"]),

    # -- 港股 10 -------------------------------------------------------------------
    row("hk01398", "工商银行",
        ["ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC", "ICBC",
         "工商銀行", "공상은행", "工商銀行"]),
    row("hk00939", "建设银行",
        ["CCB", "CCB", "CCB", "CCB", "CCB", "CCB", "CCB", "CCB", "CCB", "CCB",
         "建設銀行", "건설은행", "建設銀行"]),
    row("hk03988", "中国银行",
        ["Bank of China", "Bank of China", "Bank of China", "Bank of China", "Bank of China",
         "Bank of China", "Bank of China", "Bank of China", "Bank of China", "Bank of China",
         "中国銀行", "중국은행", "中國銀行"]),
    row("hk00857", "中国石油股份",
        ["PetroChina", "PetroChina", "PetroChina", "PetroChina", "PetroChina",
         "PetroChina", "PetroChina", "PetroChina", "PetroChina", "PetroChina",
         "中国石油", "페트로차이나", "中國石油"]),
    row("hk00386", "中国石油化工股份",
        ["Sinopec", "Sinopec", "Sinopec", "Sinopec", "Sinopec",
         "Sinopec", "Sinopec", "Sinopec", "Sinopec", "Sinopec",
         "中国石化", "시노펙", "中國石化"]),
    row("hk00941", "中国移动",
        ["China Mobile", "China Mobile", "China Mobile", "China Mobile", "China Mobile",
         "China Mobile", "China Mobile", "China Mobile", "China Mobile", "China Mobile",
         "中国移動", "중국이동", "中國移動"]),
    row("hk01810", "小米集团",
        ["Xiaomi", "Xiaomi", "Xiaomi", "Xiaomi", "Xiaomi", "Xiaomi", "Xiaomi", "Xiaomi",
         "Xiaomi", "Xiaomi", "シャオミ", "샤오미", "小米集團"]),
    row("hk09618", "京东集团",
        ["JD.com", "JD.com", "JD.com", "JD.com", "JD.com", "JD.com", "JD.com", "JD.com",
         "JD.com", "JD.com", "京東集団", "징둥", "京東集團"]),
    row("hk09999", "网易",
        ["NetEase", "NetEase", "NetEase", "NetEase", "NetEase", "NetEase", "NetEase",
         "NetEase", "NetEase", "NetEase", "ネットイース", "넷이즈", "網易"]),
    row("hk00388", "香港交易所",
        ["HKEX", "HKEX", "HKEX", "HKEX", "HKEX", "HKEX", "HKEX", "HKEX", "HKEX", "HKEX",
         "香港取引所", "홍콩거래소", "香港交易所"]),

    # -- 美股 11 -------------------------------------------------------------------
    row("usGOOGL.OQ", "谷歌",
        ["Alphabet", "Alphabet", "Alphabet", "Alphabet", "Alphabet", "Alphabet", "Alphabet",
         "Alphabet", "Alphabet", "Alphabet", "アルファベット", "알파벳", "谷歌"]),
    row("usAMZN.OQ", "亚马逊",
        ["Amazon", "Amazon", "Amazon", "Amazon", "Amazon", "Amazon", "Amazon", "Amazon",
         "Amazon", "Amazon", "アマゾン", "아마존", "亞馬遜"]),
    row("usMETA.OQ", "Meta",
        ["Meta", "Meta", "Meta", "Meta", "Meta", "Meta", "Meta", "Meta", "Meta", "Meta",
         "メタ", "메타", "Meta"]),
    row("usTSLA.OQ", "特斯拉",
        ["Tesla", "Tesla", "Tesla", "Tesla", "Tesla", "Tesla", "Tesla", "Tesla",
         "Tesla", "Tesla", "テスラ", "테슬라", "特斯拉"]),
    row("usAVGO.OQ", "博通",
        ["Broadcom", "Broadcom", "Broadcom", "Broadcom", "Broadcom", "Broadcom", "Broadcom",
         "Broadcom", "Broadcom", "Broadcom", "ブロードコム", "브로드컴", "博通"]),
    row("usLLY.N", "礼来",
        ["Eli Lilly", "Eli Lilly", "Eli Lilly", "Eli Lilly", "Eli Lilly", "Eli Lilly",
         "Eli Lilly", "Eli Lilly", "Eli Lilly", "Eli Lilly", "イーライリリー",
         "일라이 릴리", "禮來"]),
    row("usJPM.N", "摩根大通",
        ["JPMorgan", "JPMorgan", "JPMorgan", "JPMorgan", "JPMorgan", "JPMorgan", "JPMorgan",
         "JPMorgan", "JPMorgan", "JPMorgan", "JPモルガン", "JP모건", "摩根大通"]),
    row("usV.N", "Visa",
        ["Visa", "Visa", "Visa", "Visa", "Visa", "Visa", "Visa", "Visa", "Visa", "Visa",
         "ビザ", "비자", "Visa"]),
    row("usXOM.N", "埃克森美孚",
        ["Exxon Mobil", "Exxon Mobil", "Exxon Mobil", "Exxon Mobil", "Exxon Mobil",
         "Exxon Mobil", "Exxon Mobil", "Exxon Mobil", "Exxon Mobil", "Exxon Mobil",
         "エクソンモービル", "엑슨모빌", "埃克森美孚"]),
    row("usWMT.OQ", "沃尔玛",
        ["Walmart", "Walmart", "Walmart", "Walmart", "Walmart", "Walmart", "Walmart",
         "Walmart", "Walmart", "Walmart", "ウォルマート", "월마트", "沃爾瑪"]),
    row("usORCL.N", "甲骨文",
        ["Oracle", "Oracle", "Oracle", "Oracle", "Oracle", "Oracle", "Oracle", "Oracle",
         "Oracle", "Oracle", "オラクル", "오라클", "甲骨文"]),
]

# ---- 16 条页面文案 ------------------------------------------------------------------
# 列序与 LANGS 完全一致（zh-Hans 在最后）。

PAGE = [
    ("NavMarketCap.Content", [
        "Market cap", "Marktkapitalisierung", "Capitalización", "Capitalisation",
        "Capitalizzazione", "Kapitalizacja", "Valor de mercado", "Tržní kapitalizace",
        "Piyasa değeri", "Капитализация", "時価総額", "시가총액", "市值榜", "市值榜"]),

    ("MarketCapPageTitle.Text", [
        "Market Cap Race", "Marktkapitalisierungs-Rennen", "Carrera de capitalización",
        "Course des capitalisations", "Corsa delle capitalizzazioni",
        "Wyścig kapitalizacji", "Corrida de valor de mercado",
        "Závod tržních kapitalizací", "Piyasa değeri yarışı", "Гонка капитализаций",
        "時価総額レース", "시가총액 레이스", "市值榜競速", "市值榜竞速"]),

    ("MarketCapPageSubtitle.Text", [
        "A dozen horizontal bars overtaking one another on total market value, the order "
        "changing to the last frame.",
        "Ein Dutzend waagerechter Balken, die sich nach Marktkapitalisierung überholen — die "
        "Reihenfolge ändert sich bis zum letzten Bild.",
        "Una docena de barras horizontales que se adelantan por capitalización, con el orden "
        "cambiando hasta el último fotograma.",
        "Une douzaine de barres horizontales qui se dépassent selon la capitalisation, l'ordre "
        "changeant jusqu'à la dernière image.",
        "Una dozzina di barre orizzontali che si sorpassano per capitalizzazione, con l'ordine "
        "che cambia fino all'ultimo fotogramma.",
        "Kilkanaście poziomych słupków wyprzedzających się według kapitalizacji — kolejność "
        "zmienia się do ostatniej klatki.",
        "Uma dúzia de barras horizontais se ultrapassando por valor de mercado, com a ordem "
        "mudando até o último quadro.",
        "Tucet vodorovných pruhů, které se předhánějí podle tržní kapitalizace — pořadí se "
        "mění až do posledního snímku.",
        "Bir düzine yatay çubuk piyasa değerine göre birbirini geçiyor; sıralama son kareye "
        "kadar değişiyor.",
        "Полтора десятка горизонтальных полос обгоняют друг друга по капитализации, а порядок "
        "меняется до последнего кадра.",
        "十数本の横棒が時価総額で追い抜き合い、順位は最後のフレームまで入れ替わります。",
        "십여 개의 가로 막대가 시가총액 순으로 서로를 추월하며, 순위는 마지막 프레임까지 바뀝니다.",
        "十幾條橫向條形按總市值互相超車，名次一路變到最後一幀。",
        "十几条横向条形按总市值互相超车，名次一路变到最后一帧。"]),

    ("MarketCapStageTitle", [
        "Market Cap Race", "Marktkapitalisierungs-Rennen", "Carrera de capitalización",
        "Course des capitalisations", "Corsa delle capitalizzazioni",
        "Wyścig kapitalizacji", "Corrida de valor de mercado",
        "Závod tržních kapitalizací", "Piyasa değeri yarışı", "Гонка капитализаций",
        "時価総額レース", "시가총액 레이스", "市值榜競速", "市值榜竞速"]),

    # `MarketCapCount` was here, and the pool script has it now. Both scripts carried a version
    # of it — this one still said "a fixed field of {0} listings" — and every run deleted the
    # other's copy before writing its own, so the page's description of its own field flipped
    # depending on which script was run second. **One key, one script.** The field is now
    # whatever the ranking says it is, so the pool script is the one that knows.

    # `.Text` because this one is set through `x:Uid` on a TextBlock, and an x:Uid needs the
    # property it sets: the loader looks for `Key/Text`, so a bare key resolves to nothing and
    # the paragraph comes out blank. The other page keys here are read in code through
    # `Strings.Get`, where a bare key is the right form.
    ("MarketCapMethodNote.Text", [
        "A past market value is today's total market value times the adjusted price ratio over "
        "the range. Bonus issues and splits cancel out in the adjusted series; dividends do not "
        "— they are reinvested, so a heavy payer's past value reads low. And the last market "
        "value is the only one that came straight from the source; the rest are derived.",
        "Ein früherer Marktwert ist der heutige Gesamtwert mal das bereinigte Kursverhältnis "
        "über den Zeitraum. Kapitalerhöhungen und Splits heben sich in der bereinigten Reihe "
        "auf, Dividenden nicht — sie werden reinvestiert, weshalb der frühere Wert eines "
        "starken Ausschütters zu niedrig ausfällt. Nur der letzte Marktwert stammt direkt von "
        "der Quelle, alle übrigen sind abgeleitet.",
        "Un valor pasado es el valor total de hoy por el cociente de precios ajustado del "
        "periodo. Las ampliaciones y los desdoblamientos se anulan en la serie ajustada; los "
        "dividendos no — se reinvierten, así que el valor pasado de un pagador fuerte queda "
        "bajo. Y el último valor es el único que viene directo de la fuente.",
        "Une valeur passée est la valeur totale d'aujourd'hui multipliée par le rapport de prix "
        "ajusté sur la période. Les augmentations de capital et les fractionnements s'annulent "
        "dans la série ajustée ; les dividendes non — ils sont réinvestis, donc la valeur "
        "passée d'un gros distributeur ressort basse.",
        "Un valore passato è il valore totale di oggi per il rapporto di prezzo rettificato del "
        "periodo. Aumenti di capitale e frazionamenti si annullano nella serie rettificata; i "
        "dividendi no — vengono reinvestiti, quindi il valore passato di un forte distributore "
        "risulta basso.",
        "Dawna wartość to dzisiejsza wartość całkowita razy skorygowany stosunek cen z okresu. "
        "Emisje i splity znoszą się w skorygowanej serii, dywidendy nie — są reinwestowane, "
        "więc dawna wartość hojnie dzielącej się spółki wypada nisko.",
        "Um valor passado é o valor total de hoje vezes a razão de preços ajustada do período. "
        "Bonificações e desdobramentos se cancelam na série ajustada; os dividendos não — são "
        "reinvestidos, então o valor passado de quem paga muito sai baixo.",
        "Dřívější hodnota je dnešní celková hodnota krát upravený poměr cen za období. Emise a "
        "štěpení se v upravené řadě vyruší, dividendy ne — reinvestují se, takže dřívější "
        "hodnota štědrého plátce vychází nízko.",
        "Geçmiş bir değer, bugünkü toplam değerin dönem boyunca düzeltilmiş fiyat oranıyla "
        "çarpımıdır. Bedelsiz sermaye artırımları ve bölünmeler düzeltilmiş seride birbirini "
        "götürür; temettüler götürmez — yeniden yatırılır, bu yüzden çok temettü veren bir "
        "şirketin geçmiş değeri düşük çıkar.",
        "Прошлая стоимость — это сегодняшняя полная стоимость, умноженная на скорректированное "
        "отношение цен за период. Допэмиссии и дробления в скорректированном ряду "
        "сокращаются, дивиденды — нет: они реинвестируются, поэтому прошлая стоимость "
        "щедрого плательщика выходит заниженной.",
        "過去の時価総額は、今日の時価総額に期間の調整済み価格比率を掛けたものです。増資や "
        "分割は調整済み系列で相殺されますが、配当は相殺されません——再投資されるため、"
        "高配当銘柄の過去の値は低めに出ます。",
        "과거 시가총액은 오늘의 시가총액에 기간의 조정 주가 비율을 곱한 값입니다. 무상증자와 "
        "액면분할은 조정 계열에서 상쇄되지만 배당은 그렇지 않습니다——재투자되므로 배당을 많이 "
        "주는 기업의 과거 값은 낮게 나옵니다.",
        "過去的市值＝今日總市值 × 期間複權價格比。送股與拆股會在前復權序列裡互相抵消，"
        "分紅不會——它被算作再投資，所以高分紅公司的歷史市值會偏低。",
        "过去的市值＝今日总市值 × 区间复权价格比。送股与拆股会在复权序列里互相抵消，"
        "分红不会——它被算作再投资，所以高分红公司的历史市值会偏低。"]),

    ("MarketCapListLabel", [
        "Top {0} by market cap", "Top {0} nach Marktkapitalisierung",
        "Top {0} por capitalización", "Top {0} par capitalisation",
        "Top {0} per capitalizzazione", "Top {0} według kapitalizacji",
        "Top {0} por valor de mercado", "Top {0} podle kapitalizace",
        "Piyasa değerine göre ilk {0}", "Топ-{0} по капитализации",
        "時価総額トップ{0}", "시가총액 상위 {0}", "市值前 {0}", "市值前 {0}"]),

    ("MarketCapSnapshotting", [
        "Reading the latest market values …", "Aktuelle Marktkapitalisierungen werden gelesen …",
        "Leyendo los valores de mercado más recientes …",
        "Lecture des capitalisations les plus récentes …",
        "Lettura delle capitalizzazioni più recenti …",
        "Odczyt najnowszych kapitalizacji …", "Lendo os valores de mercado mais recentes …",
        "Načítání nejnovějších kapitalizací …", "En güncel piyasa değerleri okunuyor …",
        "Читаю текущие капитализации …", "最新の時価総額を読み込んでいます …",
        "최신 시가총액을 읽는 중 …", "正在讀取最新總市值 …", "正在读取最新总市值 …"]),

    ("MarketCapSnapshotMissing", [
        "The source returned no market value for {0}.",
        "Die Quelle lieferte keinen Marktwert für {0}.",
        "La fuente no devolvió valor de mercado para {0}.",
        "La source n'a renvoyé aucune capitalisation pour {0}.",
        "La fonte non ha restituito alcuna capitalizzazione per {0}.",
        "Źródło nie zwróciło kapitalizacji dla {0}.",
        "A fonte não retornou valor de mercado para {0}.",
        "Zdroj nevrátil tržní kapitalizaci pro {0}.",
        "Kaynak {0} için piyasa değeri döndürmedi.",
        "Источник не вернул капитализацию для {0}.",
        "情報源が {0} の時価総額を返しませんでした。",
        "데이터 원본이 {0}의 시가총액을 반환하지 않았습니다.",
        "行情源沒有返回「{0}」的市值。", "行情源没有返回「{0}」的市值。"]),

    ("MarketCapNoHistory", [
        "The source returned no price history for {0}.",
        "Die Quelle lieferte keine Kurshistorie für {0}.",
        "La fuente no devolvió historial de precios para {0}.",
        "La source n'a renvoyé aucun historique de cours pour {0}.",
        "La fonte non ha restituito lo storico dei prezzi per {0}.",
        "Źródło nie zwróciło historii kursu dla {0}.",
        "A fonte não retornou histórico de preços para {0}.",
        "Zdroj nevrátil historii cen pro {0}.",
        "Kaynak {0} için fiyat geçmişi döndürmedi.",
        "Источник не вернул историю цен для {0}.",
        "情報源が {0} の価格履歴を返しませんでした。",
        "데이터 원본이 {0}의 가격 이력을 반환하지 않았습니다.",
        "行情源沒有返回「{0}」的歷史行情。", "行情源没有返回「{0}」的历史行情。"]),

    ("MarketCapTooFew", [
        "A market-cap board needs at least 2 listings.",
        "Ein Marktkapitalisierungs-Board braucht mindestens 2 Werte.",
        "Un tablero de capitalización necesita al menos 2 valores.",
        "Un tableau de capitalisation demande au moins 2 valeurs.",
        "Una classifica di capitalizzazione richiede almeno 2 titoli.",
        "Tablica kapitalizacji potrzebuje co najmniej 2 spółek.",
        "Um quadro de valor de mercado precisa de pelo menos 2 papéis.",
        "Tabule kapitalizace potřebuje alespoň 2 tituly.",
        "Piyasa değeri tablosu en az 2 hisse gerektirir.",
        "Для таблицы капитализации нужно минимум 2 бумаги.",
        "時価総額ボードには 2 銘柄以上が必要です。",
        "시가총액 보드에는 최소 2개 종목이 필요합니다.",
        "市值榜至少需要 2 檔。", "市值榜至少需要 2 只。"]),

    # 市值单位。三市场各一个 —— 数字是「本币亿」，标签必须说清是哪一种。
    ("MarketCapUnitCny", [
        "¥100M", "¥100 Mio.", "¥100 M", "¥100 M", "¥100 M", "¥100 M", "¥100 M", "¥100 M",
        "¥100M", "¥100 млн", "億元", "억 위안", "億元", "亿元"]),

    ("MarketCapUnitHkd", [
        "HK$100M", "HK$100 Mio.", "HK$100 M", "HK$100 M", "HK$100 M", "HK$100 M", "HK$100 M",
        "HK$100 M", "HK$100M", "HK$100 млн", "億香港ドル", "억 홍콩달러", "億港元", "亿港元"]),

    ("MarketCapUnitUsd", [
        "$100M", "$100 Mio.", "$100 M", "$100 M", "$100 M", "$100 M", "$100 M", "$100 M",
        "$100M", "$100 млн", "億ドル", "억 달러", "億美元", "亿美元"]),

    # 画面表头那行里的两个量词。串是 `{起} 至 {止} · {月数} {MarketCapUnitMonths} ·
    # {候选数} {MarketCapUnitCandidates}`，所以这两个词都接在数字后面。
    #
    # 月数不是交易日数：这一页的数据是月线（见 MarketCaps.cs 的说明），十年给 120 行、
    # 一年给 12 行。渲染器里原本写死「个交易日」——行业竞速页是日线，两页共用同一个
    # 渲染器，于是市值榜每一帧都在说「12 个交易日」。量词现在由页面给。
    ("MarketCapUnitMonths", [
        "months", "Monate", "meses", "mois", "mesi", "miesięcy", "meses", "měsíců", "ay",
        "мес.", "か月", "개월", "個月", "个月"]),

    # 「只候选」而不是「只个股」：画面上的数字是候选池的大小（两百上下），榜上是十五，
    # 用「只个股」会让人以为这两百只都在榜。
    ("MarketCapUnitCandidates", [
        "candidates", "Kandidaten", "candidatos", "candidats", "candidati", "kandydatów",
        "candidatos", "kandidátů", "aday", "кандидатов", "銘柄", "종목", "檔候選", "只候选"]),
]


# Keys this page used to carry and no longer does. Still cleaned up on every run, or a
# rename leaves the old entry behind for good — and a stale key is invisible until
# somebody translates it.
# MarketCapFetched used to live here; it moved to the pool script when the board became
# monthly (the unit changed from trading days to periods). Both scripts cleaning the same key
# means whichever ran second won, and the loser was the one that inserted it.
REMOVED = ["MarketCapAutoTitle"]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML, and MakePri reports it as `PRI224: root node not found` —
    naming the root element and the project file, and saying nothing about the company name
    that caused it. See the sibling pool script, where this was learned.
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

            # Which of the fourteen is this file? Position in LANGS, not in the row.
            lines.append(entry(key, values[LANGS.index(tag)]))

        for key, values in PAGE:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values"
            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same name wherever it already sits, then append.
        for code, _ in INSTRUMENTS:
            key = "INST" + "".join(c for c in code if c.isalnum()).upper()
            text = re.sub(rf'  <data name="{key}">.*?</data>\n', "", text, flags=re.S)

        # Two details, both learned the hard way here.
        #
        # The optional suffix is matched so that renaming a key from `X` to `X.Text` (what an
        # x:Uid needs) does not leave the old one behind as a second, unused entry.
        #
        # And `[^>]*` after the name, because this file holds two entry shapes: the single-line
        # `<data name="K"><value>v</value></data>` a machine wrote, and a hand-edited
        # `<data name="K" xml:space="preserve">` with the value on the next line. A pattern that
        # insists on `">` matches only the first, so the second survived the delete and the run
        # ended with both `K` and `K.Text` in the file — which MakePri rejects outright (PRI278).
        for key, _ in PAGE:
            # The *base* name is what to match on, not the key: `MarketCapMethodNote.Text` as a
            # literal never matches the bare `MarketCapMethodNote` an earlier run left behind, so
            # the file ended up holding both and MakePri refused the pair.
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        for key in REMOVED:
            text = re.sub(
                rf'  <data name="{re.escape(key)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at = text.rfind("</root>")
        assert at > 0, f"{tag}: no </root>"

        text = text[:at] + "".join(lines) + text[at:]

        # Bytes, not text: read_text/write_text would normalise the line endings and git
        # would see the whole file rewritten.
        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
