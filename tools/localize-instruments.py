# -*- coding: utf-8 -*-
r"""把 80 个内置标的的本地化显示名注入 14 份 Resources.resw。

键名规则与 C# InstrumentNames.Key 一致："Inst" + 代码去掉非字母数字
（保留大小写），如 usSPY.AM -> InstusSPYAM。显示名查 resw，请求参数
仍用代码本身——名字只是标签，永远不进请求。

翻译顺序（13 列）：en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant
zh-Hans 的值 = 源中文名本身。注入位置：</root> 之前，14 份顺序一致。

用法：python tools\localize-instruments.py   （可重复运行，先清旧 Inst 键）
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")
LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru", "ja", "ko", "zh-Hant"]

# ---- 共享概念（13 列） ------------------------------------------------------------
ENERGY      = ["Energy", "Energie", "Energía", "Énergie", "Energia", "Energetyka", "Energia", "Energetika", "Enerji", "Энергетика", "エネルギー", "에너지", "能源"]
MATERIALS   = ["Materials", "Materialien", "Materiales", "Matériaux", "Materiali", "Materiały", "Materiais", "Materiály", "Malzeme", "Материалы", "素材", "소재", "材料"]
INDUSTRIALS = ["Industrials", "Industrie", "Industria", "Industrie", "Industria", "Przemysł", "Indústria", "Průmysl", "Sanayi", "Промышленность", "工業", "산업", "工業"]
CONS_DISC   = ["Consumer Discretionary", "Zyklischer Konsum", "Consumo discrecional", "Consommation discrétionnaire", "Consumo discrezionale", "Konsumpcja cykliczna", "Consumo discricionário", "Cyklická spotřeba", "İhtiyari Tüketim", "Циклическое потребление", "任意消費", "임의소비", "可選消費"]
CONS_STAP   = ["Consumer Staples", "Basiskonsum", "Consumo básico", "Consommation de base", "Consumo di base", "Konsumpcja podstawowa", "Consumo básico", "Základní spotřeba", "Zorunlu Tüketim", "Базовое потребление", "必需消費", "필수소비", "主要消費"]
CONS_STAP2  = [*CONS_STAP[:12], "必需消費"]                      # 必需消费（SPDR）
HEALTH      = ["Health Care", "Gesundheit", "Salud", "Santé", "Sanità", "Ochrona zdrowia", "Saúde", "Zdravotnictví", "Sağlık", "Здравоохранение", "医療", "의료", "醫藥衛生"]
HEALTH2     = [*HEALTH[:12], "醫療"]                             # 医疗
FINANCIALS  = ["Financials", "Finanzen", "Financiero", "Finance", "Finanza", "Finanse", "Financeiro", "Finance", "Finans", "Финансы", "金融", "금융", "金融"]
INFOTECH    = ["Information Technology", "Informationstechnologie", "Tecnología", "Technologie", "Tecnologia", "Technologie informatyczne", "Tecnologia", "Informační technologie", "Bilgi Teknolojisi", "Информационные технологии", "情報技術", "정보기술", "資訊科技"]
COMMS       = ["Communication Services", "Telekommunikation", "Comunicación", "Communication", "Comunicazioni", "Łączność", "Comunicação", "Telekomunikace", "İletişim", "Связь", "通信", "통신", "通信"]
UTILITIES   = ["Utilities", "Versorger", "Servicios públicos", "Services publics", "Servizi pubblici", "Użyteczność publiczna", "Serviços públicos", "Veřejné služby", "Kamu Hizmetleri", "Коммунальные услуги", "公益事業", "유틸리티", "公用事業"]
TECH        = ["Technology", "Technologie", "Tecnología", "Technologie", "Tecnologia", "Technologia", "Tecnologia", "Technologie", "Teknoloji", "Технологии", "テクノロジー", "기술", "科技"]
REALESTATE  = ["Real Estate", "Immobilien", "Inmobiliario", "Immobilier", "Immobiliare", "Nieruchomości", "Imobiliário", "Nemovitosti", "Gayrimenkul", "Недвижимость", "不動産", "부동산", "房地產"]
PROPERTY    = [*REALESTATE[:12], "地產"]                          # 地产（恒生）
DEFENSE     = ["Defense", "Verteidigung", "Defensa", "Défense", "Difesa", "Obronność", "Defesa", "Obrana", "Savunma", "Оборона", "防衛", "방위", "國防"]
NEWENERGY   = ["New Energy", "Neue Energien", "Energías renovables", "Énergies nouvelles", "Nuove energie", "Nowa energia", "Novas energias", "Nové energie", "Yeni Enerji", "Новая энергетика", "新エネルギー", "신재생에너지", "新能源"]
ENVIRONMENT = ["Environment", "Umwelt", "Medio ambiente", "Environnement", "Ambiente", "Środowisko", "Ambiental", "Životní prostředí", "Çevre", "Экология", "環境", "환경", "環保"]

def etf(name13):
    """ETF 组：仅译 'ETF' 一词的语言差异，名字部分保留拉丁转写。"""
    return name13

CSI300ETF   = ["CSI 300 ETF", "CSI-300-ETF", "ETF CSI 300", "ETF CSI 300", "ETF CSI 300", "ETF CSI 300", "ETF CSI 300", "ETF CSI 300", "CSI 300 ETF", "ETF CSI 300", "滬深300ETF", "CSI 300 ETF", "滬深300ETF"]
CSI500ETF   = ["CSI 500 ETF", "CSI-500-ETF", "ETF CSI 500", "ETF CSI 500", "ETF CSI 500", "ETF CSI 500", "ETF CSI 500", "ETF CSI 500", "CSI 500 ETF", "ETF CSI 500", "中証500ETF", "CSI 500 ETF", "中證500ETF"]
CHINEXT_ETF = ["ChiNext ETF", "ChiNext-ETF", "ETF ChiNext", "ETF ChiNext", "ETF ChiNext", "ETF ChiNext", "ETF ChiNext", "ETF ChiNext", "ChiNext ETF", "ETF ChiNext", "創業板ETF", "치넥스트 ETF", "創業板ETF"]
GOLD_ETF    = ["Gold ETF", "Gold-ETF", "ETF de oro", "ETF or", "ETF oro", "ETF złota", "ETF ouro", "ETF zlata", "Altın ETF", "Золотой ETF", "ゴールドETF", "골드ETF", "黃金ETF"]
NASDAQ_ETF  = ["Nasdaq ETF", "Nasdaq-ETF", "ETF Nasdaq", "ETF Nasdaq", "ETF Nasdaq", "ETF Nasdaq", "ETF Nasdaq", "ETF Nasdaq", "Nasdaq ETF", "ETF Nasdaq", "ナスダックETF", "나스닥 ETF", "那指ETF"]
SP500_ETF   = ["S&P 500 ETF", "S&P-500-ETF", "ETF S&P 500", "ETF S&P 500", "ETF S&P 500", "ETF S&P 500", "ETF S&P 500", "ETF S&P 500", "S&P 500 ETF", "ETF S&P 500", "S&P500 ETF", "S&P 500 ETF", "標普500ETF"]
NQ100_ETF   = ["Nasdaq-100 ETF", "Nasdaq-100-ETF", "ETF Nasdaq-100", "ETF Nasdaq-100", "ETF Nasdaq-100", "ETF Nasdaq-100", "ETF Nasdaq-100", "ETF Nasdaq-100", "Nasdaq 100 ETF", "ETF Nasdaq-100", "ナスダック100 ETF", "나스닥100 ETF", "那指100ETF"]
DOW_ETF     = ["Dow ETF", "Dow-ETF", "ETF Dow", "ETF Dow Jones", "ETF Dow", "ETF Dow", "ETF Dow", "ETF Dow", "Dow ETF", "ETF Dow", "ダウETF", "다우 ETF", "道瓊ETF"]
RUSSELL_ETF = ["Russell 2000 ETF", "Russell-2000-ETF", "ETF Russell 2000", "ETF Russell 2000", "ETF Russell 2000", "ETF Russell 2000", "ETF Russell 2000", "ETF Russell 2000", "Russell 2000 ETF", "ETF Russell 2000", "ラッセル2000 ETF", "러셀 2000 ETF", "羅素2000ETF"]

NAMES = [
    # -- 中证一级行业（10）
    ("sh000928", "能源",     ENERGY),
    ("sh000929", "材料",     MATERIALS),
    ("sh000930", "工业",     INDUSTRIALS),
    ("sh000931", "可选消费", CONS_DISC),
    ("sh000932", "主要消费", CONS_STAP),
    ("sh000933", "医药卫生", HEALTH),
    ("sh000934", "金融",     FINANCIALS),
    ("sh000935", "信息技术", INFOTECH),
    ("sh000936", "通信",     COMMS),
    ("sh000937", "公用事业", UTILITIES),
    # -- 主题（15）
    ("sz399997", "白酒",     ["Liquor", "Baijiu", "Licores", "Spiritueux", "Distillati", "Alkohole", "Destilados", "Alkohol", "Alkollü İçecekler", "Алкоголь", "酒類", "주류", "白酒"]),
    ("sz399975", "证券",     ["Brokerages", "Brokerage", "Corretaje", "Courtage", "Brokerage", "Maklerskie", "Corretoras", "Brokeráž", "Aracılık", "Брокеры", "証券", "증권", "證券"]),
    ("sz399986", "银行",     ["Banks", "Banken", "Bancos", "Banques", "Banche", "Banki", "Bancos", "Banky", "Bankalar", "Банки", "銀行", "은행", "銀行"]),
    ("sz399989", "医疗",     HEALTH2),
    ("sz399967", "军工",     DEFENSE),
    ("sz399971", "传媒",     ["Media", "Medien", "Medios", "Médias", "Media", "Media", "Mídia", "Média", "Medya", "Медиа", "メディア", "미디어", "媒體"]),
    ("sz399808", "新能源",   NEWENERGY),
    ("sz399976", "新能源车", ["Electric Vehicles", "Elektroautos", "Vehículos eléctricos", "Véhicules électriques", "Auto elettriche", "Pojazdy elektryczne", "Veículos elétricos", "Elektromobily", "Elektrikli Araçlar", "Электромобили", "電気自動車", "전기차", "新能源車"]),
    ("sh000827", "环保",     ENVIRONMENT),
    ("sh000922", "红利",     ["Dividend", "Dividende", "Dividendo", "Dividendes", "Dividendo", "Dywidenda", "Dividendos", "Dividenda", "Temettü", "Дивиденды", "配当", "배당", "紅利"]),
    ("sz399998", "煤炭",     ["Coal", "Kohle", "Carbón", "Charbon", "Carbone", "Węgiel", "Carvão", "Uhlí", "Kömür", "Уголь", "石炭", "석탄", "煤炭"]),
    ("sh000819", "有色金属", ["Nonferrous Metals", "Nichteisenmetalle", "Metales no ferrosos", "Métaux non ferreux", "Metalli non ferrosi", "Metale nieżelazne", "Metais não ferrosos", "Neželezné kovy", "Demir Dışı Metaller", "Цветные металлы", "非鉄金属", "비철금속", "有色金屬"]),
    ("sz399995", "基建",     ["Infrastructure", "Infrastruktur", "Infraestructura", "Infrastructures", "Infrastrutture", "Infrastruktura", "Infraestrutura", "Infrastruktura", "Altyapı", "Инфраструктура", "インフラ", "인프라", "基建"]),
    ("sh000949", "农业",     ["Agriculture", "Agrar", "Agricultura", "Agriculture", "Agricoltura", "Rolnictwo", "Agricultura", "Zemědělství", "Tarım", "Сельское хозяйство", "農業", "농업", "農業"]),
    ("sz399996", "智能家居", ["Smart Home", "Smart Home", "Hogar inteligente", "Domotique", "Casa intelligente", "Inteligentny dom", "Casa inteligente", "Chytrá domácnost", "Akıllı Ev", "Умный дом", "スマートホーム", "스마트홈", "智慧家庭"]),
    # -- 恒生分类（4）
    ("hkHSF", "金融",     FINANCIALS),
    ("hkHSP", "地产",     PROPERTY),
    ("hkHSU", "公用事业", UTILITIES),
    ("hkHSC", "工商",     ["Commerce & Industry", "Handel und Industrie", "Comercio e industria", "Commerce et industrie", "Commercio e industria", "Handel i przemysł", "Comércio e indústria", "Obchod a průmysl", "Ticaret ve Sanayi", "Торговля и промышленность", "商工業", "상공", "工商"]),
    # -- SPDR 行业（10）
    ("usXLK.AM", "科技",     TECH),
    ("usXLF.AM", "金融",     FINANCIALS),
    ("usXLV.AM", "医疗",     HEALTH2),
    ("usXLY.AM", "可选消费", CONS_DISC),
    ("usXLP.AM", "必需消费", CONS_STAP2),
    ("usXLI.AM", "工业",     INDUSTRIALS),
    ("usXLE.AM", "能源",     ENERGY),
    ("usXLB.AM", "材料",     MATERIALS),
    ("usXLU.AM", "公用事业", UTILITIES),
    ("usXLRE.AM", "房地产",  REALESTATE),
    # -- 港股指数与个股（8）
    ("hkHSI",    "恒生指数", ["Hang Seng Index", "Hang-Seng-Index", "Índice Hang Seng", "Indice Hang Seng", "Indice Hang Seng", "Indeks Hang Seng", "Índice Hang Seng", "Index Hang Seng", "Hang Seng Endeksi", "Индекс Hang Seng", "ハンセン指数", "항셍지수", "恆生指數"]),
    ("hkHSCEI",  "国企指数", ["China Enterprises", "China Enterprises", "Empresas de China", "Entreprises de Chine", "Imprese cinesi", "Przedsiębiorstwa chińskie", "Empresas da China", "Čínské podniky", "Çin Şirketleri", "Китайские предприятия", "中国企業指数", "HSCEI", "國企指數"]),
    ("hkHSTECH", "恒生科技", ["Hang Seng TECH", "Hang Seng TECH", "Hang Seng TECH", "Hang Seng TECH", "Hang Seng TECH", "Hang Seng TECH", "Hang Seng TECH", "Hang Seng TECH", "Hang Seng TECH", "Hang Seng TECH", "ハンセンTECH", "항셍테크", "恆生科技"]),
    ("hk00700",  "腾讯控股", ["Tencent", "Tencent", "Tencent", "Tencent", "Tencent", "Tencent", "Tencent", "Tencent", "Tencent", "Tencent", "テンセント", "텐센트", "騰訊控股"]),
    ("hk09988",  "阿里巴巴", ["Alibaba", "Alibaba", "Alibaba", "Alibaba", "Alibaba", "Alibaba", "Alibaba", "Alibaba", "Alibaba", "Alibaba", "アリババ", "알리바바", "阿里巴巴"]),
    ("hk03690",  "美团",     ["Meituan", "Meituan", "Meituan", "Meituan", "Meituan", "Meituan", "Meituan", "Meituan", "Meituan", "Meituan", "美団", "메이투안", "美團"]),
    ("hk00005",  "汇丰控股", ["HSBC", "HSBC", "HSBC", "HSBC", "HSBC", "HSBC", "HSBC", "HSBC", "HSBC", "HSBC", "HSBC", "HSBC", "滙豐控股"]),
    ("hk01299",  "友邦保险", ["AIA", "AIA", "AIA", "AIA", "AIA", "AIA", "AIA", "AIA", "AIA", "AIA", "AIA", "AIA", "友邦保險"]),
    # -- A股 ETF 与指数（7）
    ("sh510300", "沪深300ETF", CSI300ETF),
    ("sh510500", "中证500ETF", CSI500ETF),
    ("sz159915", "创业板ETF",  CHINEXT_ETF),
    ("sh518880", "黄金ETF",    GOLD_ETF),
    ("sh513100", "纳指ETF",    NASDAQ_ETF),
    ("sh000001", "上证指数",   ["Shanghai Composite", "Shanghai Composite", "Shanghái Composite", "Composite de Shanghai", "Shanghai Composite", "Shanghai Composite", "Xangai Composite", "Shanghai Composite", "Şanghay Composite", "Шанхайский композит", "上海総合指数", "상하이종합", "上證指數"]),
    ("sz399006", "创业板指",   ["ChiNext", "ChiNext", "ChiNext", "ChiNext", "ChiNext", "ChiNext", "ChiNext", "ChiNext", "ChiNext", "ChiNext", "ChiNext", "치넥스트", "創業板指"]),
    # -- 港股 ETF（3）
    ("hk02800", "盈富基金",     ["Tracker Fund", "Tracker Fund", "Fondo Tracker", "Fonds Tracker", "Tracker Fund", "Fundusz Tracker", "Fundo Tracker", "Fond Tracker", "Tracker Fonu", "Фонд Tracker", "トラッカーファンド", "트래커 펀드", "盈富基金"]),
    ("hk02828", "恒生中国企业", ["China Enterprises ETF", "China-Enterprises-ETF", "ETF de empresas de China", "ETF entreprises de Chine", "ETF imprese cinesi", "ETF chińskich przedsiębiorstw", "ETF empresas da China", "ETF čínských podniků", "Çin Şirketleri ETF", "Китайские предприятия ETF", "中国企業ETF", "중국기업 ETF", "恆生中國企業"]),
    ("hk03067", "安硕恒生科技", ["iShares HS TECH", "iShares HS TECH", "iShares Hang Seng TECH", "iShares Hang Seng TECH", "iShares Hang Seng TECH", "iShares Hang Seng TECH", "iShares Hang Seng TECH", "iShares Hang Seng TECH", "iShares Hang Seng TECH", "iShares Hang Seng TECH", "iSharesハンセンTECH", "아이셰어 항셍테크", "安碩恆生科技"]),
    # -- 美股 ETF（5）
    ("usSPY.AM", "标普500ETF",   SP500_ETF),
    ("usQQQ.OQ", "纳指100ETF",   NQ100_ETF),
    ("usDIA.AM", "道琼斯ETF",    DOW_ETF),
    ("usIWM.AM", "罗素2000ETF",  RUSSELL_ETF),
    ("usGLD.AM", "黄金ETF",      GOLD_ETF),
    # -- A股个股（5）
    ("sh601318", "中国平安", ["Ping An", "Ping An", "Ping An", "Ping An", "Ping An", "Ping An", "Ping An", "Ping An", "Ping An", "Ping An", "平安保険", "핑안", "中國平安"]),
    ("sh600519", "贵州茅台", ["Kweichow Moutai", "Kweichow Moutai", "Kweichow Moutai", "Kweichow Moutai", "Kweichow Moutai", "Kweichow Moutai", "Kweichow Moutai", "Kweichow Moutai", "Kweichow Moutai", "Kweichow Moutai", "貴州茅台", "구이저우마오타이", "貴州茅台"]),
    ("sh600036", "招商银行", ["Merchants Bank", "China Merchants Bank", "Banco Merchants", "Banque Merchants", "China Merchants Bank", "Bank Merchants", "Banco Merchants", "Merchants Bank", "Merchants Bank", "China Merchants Bank", "招商銀行", "자오상은행", "招商銀行"]),
    ("sh600900", "长江电力", ["Yangtze Power", "Yangtze Power", "Yangtze Power", "Yangtze Power", "Yangtze Power", "Yangtze Power", "Yangtze Power", "Yangtze Power", "Yangtze Power", "Yangtze Power", "長江電力", "창장전력", "長江電力"]),
    ("sz000858", "五粮液",   ["Wuliangye", "Wuliangye", "Wuliangye", "Wuliangye", "Wuliangye", "Wuliangye", "Wuliangye", "Wuliangye", "Wuliangye", "Wuliangye", "ウーリャンイエ", "우량예", "五糧液"]),
    # -- 美股个股与指数（7）
    ("usAAPL.OQ", "苹果",     ["Apple", "Apple", "Apple", "Apple", "Apple", "Apple", "Apple", "Apple", "Apple", "Apple", "アップル", "애플", "蘋果"]),
    ("usBRK.B.N", "伯克希尔B", ["Berkshire B", "Berkshire B", "Berkshire B", "Berkshire B", "Berkshire B", "Berkshire B", "Berkshire B", "Berkshire B", "Berkshire B", "Berkshire B", "バークシャーB", "버크셔B", "波克夏B"]),
    ("usNVDA.OQ", "英伟达",   ["NVIDIA", "NVIDIA", "NVIDIA", "NVIDIA", "NVIDIA", "NVIDIA", "NVIDIA", "NVIDIA", "NVIDIA", "NVIDIA", "エヌビディア", "엔비디아", "輝達"]),
    ("usMSFT.OQ", "微软",     ["Microsoft", "Microsoft", "Microsoft", "Microsoft", "Microsoft", "Microsoft", "Microsoft", "Microsoft", "Microsoft", "Microsoft", "マイクロソフト", "마이크로소프트", "微軟"]),
    ("usDJI", "道琼斯",   ["Dow Jones", "Dow Jones", "Dow Jones", "Dow Jones", "Dow Jones", "Dow Jones", "Dow Jones", "Dow Jones", "Dow Jones", "Доу-Джонс", "ダウ平均", "다우존스", "道瓊斯"]),
    ("usIXIC", "纳斯达克", ["Nasdaq", "Nasdaq", "Nasdaq", "Nasdaq", "Nasdaq", "Nasdaq", "Nasdaq", "Nasdaq", "Nasdaq", "NASDAQ", "ナスダック", "나스닥", "那斯達克"]),
    ("usINX",  "标普500", ["S&P 500", "S&P 500", "S&P 500", "S&P 500", "S&P 500", "S&P 500", "S&P 500", "S&P 500", "S&P 500", "S&P 500", "S&P500", "S&P 500", "標普500"]),
    # -- A股宽基指数补齐（6）
    ("sz399001", "深证成指", ["Shenzhen Component", "Shenzhen Component", "Shenzhen Component", "Shenzhen Component", "Shenzhen Component", "Shenzhen Component", "Shenzhen Component", "Shenzhen Component", "Şenzhen Component", "Шэньчжэньский композит", "深セン成分指数", "선전성분", "深證成指"]),
    ("sh000300", "沪深300",  ["CSI 300", "CSI 300", "CSI 300", "CSI 300", "CSI 300", "CSI 300", "CSI 300", "CSI 300", "CSI 300", "CSI 300", "CSI300", "CSI 300", "滬深300"]),
    ("sh000905", "中证500",  ["CSI 500", "CSI 500", "CSI 500", "CSI 500", "CSI 500", "CSI 500", "CSI 500", "CSI 500", "CSI 500", "CSI 500", "CSI500", "CSI 500", "中證500"]),
    ("sh000688", "科创50",   ["STAR 50", "STAR 50", "STAR 50", "STAR 50", "STAR 50", "STAR 50", "STAR 50", "STAR 50", "STAR 50", "STAR 50", "STAR50", "스타50", "科創50"]),
    ("sz399005", "中小100",  ["SME 100", "SME 100", "SME 100", "SME 100", "SME 100", "SME 100", "SME 100", "SME 100", "SME 100", "SME 100", "中小100", "중소100", "中小100"]),
    ("sh000016", "上证50",   ["SSE 50", "SSE 50", "SSE 50", "SSE 50", "SSE 50", "SSE 50", "SSE 50", "SSE 50", "SSE 50", "SSE 50", "上証50", "상증50", "上證50"]),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def key_of(code):
    # 与 C# InstrumentNames.Key 一致：去非字母数字 + 整体大写
    # （搜索接口返回小写 usspy.am，Market 规范是 usSPY.AM，大写归一后同一键）
    return "INST" + re.sub(r"[^A-Za-z0-9]", "", code).upper()


def main():
    # 校验翻译列数
    for code, zh, t in NAMES:
        assert len(t) == len(LANGS), f"{code} 翻译列数 {len(t)} != {len(LANGS)}"

    keys = [key_of(code) for code, _, _ in NAMES]
    assert len(set(keys)) == len(keys), "键名冲突"

    for lang in ["zh-Hans"] + LANGS:
        path = ROOT / lang / "Resources.resw"
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")

        # 先清掉旧的 Inst 键（可重复运行）
        text = re.sub(r'\n  <data name="Inst[^"]*"><value>[^<]*</value></data>', "", text)

        # 按统一顺序生成注入块
        lines = []
        for (code, zh, t), key in zip(NAMES, keys):
            value = zh if lang == "zh-Hans" else t[LANGS.index(lang)]
            lines.append(f'  <data name="{key}"><value>{esc(value)}</value></data>')
        block = "\n".join(lines)

        assert text.count("</root>") == 1
        text = text.replace("</root>", block + "\n</root>")

        # 保持 UTF-8 BOM 与原有行尾
        path.write_bytes(text.encode("utf-8") if not raw.startswith(b"\xef\xbb\xbf") else b"\xef\xbb\xbf" + text.encode("utf-8"))
        print(f"{lang}: 注入 {len(NAMES)} 键")

    # 键序一致性校验
    import hashlib
    digest = {}
    for lang in ["zh-Hans"] + LANGS:
        path = ROOT / lang / "Resources.resw"
        text = path.read_bytes().decode("utf-8-sig")
        order = re.findall(r'<data name="(Inst[^"]*)"', text)
        digest[lang] = hashlib.md5(",".join(order).encode()).hexdigest()
    assert len(set(digest.values())) == 1, f"键序不一致: {digest}"
    print("14 份键序一致 ✓  共", len(NAMES), "键")


if __name__ == "__main__":
    main()
