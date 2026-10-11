# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.16.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是「重启应用」那条提示钉在
设置页顶端。那是真的，也已经交上去了（1.0.15.0）。接着往后加，这一栏就成了两件事各说一半。

本版是一整个新市场：**加密货币成为第四个市场，带来六个页面。**

- 它不是一个开关，是一个市场：在设置里选它，导航整组换成加密六页，股票那几页让到一边；
  **源连得上它才出现在市场列表里**。
- 六页是：K 线（含 1/5/15 分钟三个周期，画指定的那一天）、定投、持仓、涨跌日历、市值历程、
  市值榜。
- 六页里有两页画市值，而**市值是那一天量出来的，不是今天的流通量乘一个旧价格** —— 所以市值线
  和价格线可以各走各的。
- 市值榜的币**是问出来的**（问排行榜服务「今天哪几个最大」），不是照抄一份写好的名单，稳定币也
  在里面。

**只说用户能感知的那半句，不说实现方式。** 「CoinMetrics 一页只装 4000 行、按资产一个一个填」
「跟 `next_page_token` 翻页」都是代码的事，写出来等于让用户替我们查错。但「市值是量出来的不是
外推的」**必须说**：它决定了那两条线为什么不平行，而这是这一页唯一值得看的那个形状。

**也不顺手加别的东西。** 这一版同时改了说明段（二十四页、四个市场，`port-store-listing-crypto-pages.py`
那一轮），那是「商店说得出的话得和应用里有的东西对上」，不是本版的新增。

**重音字母照写。** 德语的 ü/ä/ö/ß、法语的 é/ç/à、捷克的 ř/ž/ě/ů、波兰语的 ł/ż/ą/ę、土耳其语的
ğ/ı/ş 是这个字的一部分，不是装饰；为了「保险」把它们写成 u/a/o/s/e/c/r/z/l/g 等于在商店里挂一句
拼错的德语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

**脚本名由 manifest 的版本号算出 `10160`，不是取巧写成 `1160`。** `verify-docs.py` 把四段版本
号**全拼**当作文件名（`1.0.16.0` → 四段拼起来是 `10160`；写成 `1160` 是省掉了第三段的一位，那是
留给 `1.1.6.0` 的形状），算不出/找不到就大声失败。

用法：python tools\\port-store-listing-10160.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。本版是一整个市场，比上一版长。每次换文案都要算一遍最长的那一种语言：
# 上限是按字符算的，德/意/葡一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**加密货币成为一个市场，带来六个页面；K 线多了分钟档；
# 市值是那天量出来的不是外推的；市值榜是问出来的。**
NEWS = {
    "zh-Hans":
        "加密货币现在是一个独立的市场。在设置里选它，导航就换成六个加密页面——K 线、定投、持仓、涨跌"
        "日历、市值历程、市值榜——股票那几页让到一边；只有当加密数据源连得上时它才会出现在市场列表"
        "里，所以那个下拉框说的始终是这台机器真能取到的东西。K 线页还多了 1/5/15 分钟三个周期，画"
        "你指定的那一天。六页里有两页画的是市值，而市值那天是多少就是多少，不是今天的流通量乘上一"
        "个旧价格——所以市值线和价格线可以各走各的。市值榜问的是排行榜服务「今天哪几个币最大」，而"
        "不是照抄一份写好的名单，稳定币也在里面。",
    "zh-Hant":
        "加密貨幣現在是一個獨立的市場。在設定裡選它，導覽就換成六個加密頁面——K 線、定期定額、持倉、"
        "漲跌日曆、市值歷程、市值榜——股票那幾頁讓到一邊；只有當加密資料來源連得上時它才會出現在市"
        "場清單裡，所以那個下拉選單說的始終是這台機器真能取到的東西。K 線頁還多了 1/5/15 分鐘三個"
        "週期，畫你指定的那一天。六頁裡有兩頁畫的是市值，而市值那天是多少就是多少，不是今天的流通"
        "量乘上一個舊價格——所以市值線和價格線可以各走各的。市值榜問的是排行榜服務「今天哪幾個幣最"
        "大」，而不是照抄一份寫好的名單，穩定幣也在裡面。",
    "en-US":
        "Cryptocurrency is now a market of its own. Pick it in Settings and the navigation becomes six "
        "crypto pages — candles, DCA, holdings, gain calendar, market cap history and market cap race — "
        "while the stock pages step aside; it appears only when a crypto source answers, so the market "
        "list never offers more than this machine can actually reach. The candle page also takes 1-, "
        "5- and 15-minute periods, drawn for the day you name. Two of the six are about market cap, and "
        "that figure is measured on the day, not today’s supply times an old price: the cap line is "
        "free to part company with the price line. The race asks a ranking service which coins are "
        "largest today instead of reading a list written down in advance — stablecoins included.",
    "ja":
        "暗号資産が独立した市場になりました。設定で選ぶと、ナビゲーションは暗号資産の 6 ページ（ロー"
        "ソク足、積立、保有収益、損益カレンダー、時価総額の推移、時価総額レース）に切り替わり、株式"
        "のページは退きます。暗号資産のデータ源につながるときだけ市場一覧に現れるので、その一覧は常"
        "に「この PC が実際に取得できるもの」を意味します。ローソク足ページには 1 分・5 分・15 分の"
        "周期も加わり、指定した一日を描きます。6 ページのうち 2 ページは時価総額を描きますが、その"
        "値は当日に計測されたものであり、今日の流通量に古い価格を掛けたものではありません —— だから"
        "時価総額の線と価格の線は別々に動けます。時価総額レースは、書き込まれた名簿を読むのではなく"
        "、ランキングサービスに「今日どのコインが大きいか」を尋ねます。ステーブルコインも含まれます"
        "。",
    "ko":
        "암호화폐가 이제 독립된 시장입니다. 설정에서 선택하면 탐색이 암호화폐 여섯 페이지(캔들, 적립 "
        "투자, 보유 수익, 손익 달력, 시가총액 추이, 시가총액 레이스)로 바뀌고 주식 페이지는 물러납니"
        "다. 암호화폐 데이터 출처에 연결될 때만 시장 목록에 나타나므로, 그 목록은 항상 이 컴퓨터가 실"
        "제로 가져올 수 있는 것만 말합니다. 캔들 페이지에는 1분·5분·15분 주기도 생겨 지정한 하루를 "
        "그립니다. 여섯 페이지 중 두 페이지는 시가총액을 그리는데, 그 값은 그날 측정된 값이지 오늘의 "
        "유통량에 옛 가격을 곱한 값이 아닙니다 — 그래서 시가총액 선과 가격 선은 각자 움직일 수 있습니"
        "다. 시가총액 레이스는 적어 둔 명단을 읽는 대신 순위 서비스에 ‘오늘 어떤 코인이 가장 큰가’를 "
        "묻습니다. 스테이블코인도 포함됩니다.",
    "de":
        "Kryptowährungen sind jetzt ein eigener Markt. Wählst du ihn in den Einstellungen, wird die "
        "Navigation zu sechs Krypto-Seiten — Kerzen, Sparplan, Bestände, Gewinnkalender, "
        "Marktkapitalisierung im Verlauf und Rennen der Marktkapitalisierung — und die Aktienseiten "
        "treten zurück. Er erscheint nur, wenn eine Krypto-Quelle antwortet, deshalb bietet die "
        "Marktliste nie mehr an, als dieser Rechner wirklich erreichen kann. Die Kerzen-Seite kennt "
        "außerdem 1-, 5- und 15-Minuten-Perioden und zeichnet den Tag, den du nennst. Zwei der sechs "
        "Seiten zeigen die Marktkapitalisierung, und die ist an dem Tag gemessen, nicht die heutige "
        "Umlaufmenge mal ein alter Kurs: Die Kapitalisierungslinie darf sich von der Kurslinie "
        "entfernen. Das Rennen fragt einen Rangdienst, welche Münzen heute die größten sind, statt eine "
        "aufgeschriebene Liste zu lesen — Stablecoins eingeschlossen.",
    "fr":
        "Les cryptomonnaies sont maintenant un marché à part entière. Choisissez-les dans les paramètres "
        "et la navigation devient six pages crypto — chandeliers, plan DCA, positions, calendrier des "
        "gains, historique de la capitalisation et course des capitalisations — tandis que les pages "
        "d’actions s’effacent ; le marché n’apparaît que lorsqu’une source crypto répond, la liste des "
        "marchés ne propose donc jamais plus que ce que cet ordinateur peut réellement atteindre. La "
        "page des chandeliers accepte aussi les périodes de 1, 5 et 15 minutes et dessine le jour que "
        "vous indiquez. Deux des six pages tracent la capitalisation, et cette valeur est mesurée ce "
        "jour-là — ce n’est pas la quantité en circulation d’aujourd’hui multipliée par un vieux cours : "
        "la courbe de capitalisation est libre de s’écarter de celle du cours. La course demande à un "
        "service de classement quelles sont aujourd’hui les plus grosses capitalisations, au lieu de "
        "relire une liste écrite à l’avance, stablecoins compris.",
    "it":
        "Le criptovalute sono ora un mercato a sé. Sceglile nelle impostazioni e la navigazione diventa "
        "sei pagine cripto — candele, piano DCA, posizioni, calendario dei guadagni, storico della "
        "capitalizzazione e corsa delle capitalizzazioni — mentre le pagine azionarie si fanno da parte; "
        "il mercato compare solo quando una fonte cripto risponde, quindi l’elenco dei mercati non "
        "propone mai più di ciò che questo computer riesce davvero a raggiungere. La pagina delle "
        "candele accetta anche periodi di 1, 5 e 15 minuti e disegna il giorno che indichi. Due delle "
        "sei pagine tracciano la capitalizzazione, ed è un valore misurato in quel giorno, non la "
        "quantità in circolazione di oggi per un prezzo vecchio: la linea della capitalizzazione può "
        "allontanarsi da quella del prezzo. La corsa chiede a un servizio di classifica quali sono oggi "
        "le monete più grandi, invece di rileggere un elenco scritto prima — stablecoin comprese.",
    "es":
        "Las criptomonedas son ahora un mercado propio. Elígelas en la configuración y la navegación se "
        "convierte en seis páginas cripto — velas, plan DCA, posiciones, calendario de ganancias, "
        "historial de capitalización y carrera de capitalizaciones — mientras las páginas de acciones se "
        "apartan; el mercado aparece solo cuando responde una fuente cripto, así que la lista de "
        "mercados nunca ofrece más de lo que este equipo puede alcanzar de verdad. La página de velas "
        "acepta también periodos de 1, 5 y 15 minutos y dibuja el día que indiques. Dos de las seis "
        "páginas trazan la capitalización, y es un valor medido ese día, no la cantidad en circulación "
        "de hoy multiplicada por un precio viejo: la línea de capitalización puede separarse de la del "
        "precio. La carrera pregunta a un servicio de clasificación cuáles son hoy las monedas más "
        "grandes, en lugar de releer una lista escrita de antemano, stablecoins incluidas.",
    "pt-BR":
        "As criptomoedas agora são um mercado próprio. Escolha-as nas configurações e a navegação passa a "
        "ser seis páginas cripto — candles, plano DCA, posições, calendário de ganhos, histórico do valor "
        "de mercado e corrida do valor de mercado — enquanto as páginas de ações saem de cena; o mercado "
        "só aparece quando uma fonte cripto responde, então a lista de mercados nunca oferece mais do que "
        "este computador realmente alcança. A página de candles também aceita períodos de 1, 5 e 15 "
        "minutos e desenha o dia que você indicar. Duas das seis páginas traçam o valor de mercado, e "
        "ele é medido naquele dia, não a quantidade em circulação de hoje vezes um preço antigo: a linha "
        "do valor de mercado pode se afastar da linha do preço. A corrida pergunta a um serviço de "
        "classificação quais são hoje as maiores moedas, em vez de reler uma lista escrita antes — "
        "stablecoins incluídas.",
    "pl":
        "Kryptowaluty są teraz osobnym rynkiem. Wybierz je w ustawieniach, a nawigacja zamieni się w "
        "sześć stron krypto — świece, plan DCA, pozycje, kalendarz zysków, historia kapitalizacji i "
        "wyścig kapitalizacji — a strony akcji ustąpią miejsca; rynek pojawia się tylko wtedy, gdy "
        "odpowie źródło krypto, więc lista rynków nie obiecuje nigdy więcej, niż ten komputer naprawdę "
        "może osiągnąć. Strona świec przyjmuje też okresy 1, 5 i 15 minut i rysuje wskazany przez ciebie "
        "dzień. Dwie z sześciu stron wykreślają kapitalizację, i jest to wartość zmierzona tego dnia, a "
        "nie dzisiejsza podaż w obiegu razy stara cena: linia kapitalizacji może odejść od linii ceny. "
        "Wyścig pyta serwis rankingowy, które monety są dziś największe, zamiast odczytywać wcześniej "
        "spisaną listę — łącznie ze stablecoinami.",
    "cs":
        "Kryptoměny jsou teď samostatným trhem. Vyberete-li je v nastavení, navigace se změní na šest "
        "krypto stránek — svíčky, plán DCA, pozice, kalendář zisků, vývoj tržní kapitalizace a závod "
        "kapitalizací — zatímco akciové stránky ustoupí; trh se objeví jen tehdy, když odpoví zdroj "
        "krypta, takže seznam trhů nenabízí nikdy víc, než tento počítač skutečně dosáhne. Stránka "
        "svíček bere i periody 1, 5 a 15 minut a kreslí den, který určíte. Dvě ze šesti stránek kreslí "
        "tržní kapitalizaci, a je to hodnota změřená ten den, ne dnešní množství v oběhu krát stará "
        "cena: čára kapitalizace se smí od čáry ceny vzdálit. Závod se ptá služby s žebříčkem, které "
        "mince jsou dnes největší, místo aby přečetl předem napsaný seznam — včetně stablecoinů.",
    "ru":
        "Криптовалюты теперь отдельный рынок. Выберите его в настройках, и навигация станет шестью "
        "криптостраницами — свечи, план DCA, позиции, календарь прибыли, история капитализации и гонка "
        "капитализаций — а страницы акций отойдут в сторону; рынок появляется только тогда, когда "
        "отвечает криптоисточник, поэтому список рынков никогда не предлагает больше, чем этот компьютер "
        "реально может достать. Страница свечей принимает и периоды 1, 5 и 15 минут и рисует указанный "
        "вами день. Две из шести страниц рисуют капитализацию, и это измеренная в тот день величина, а "
        "не сегодняшнее количество в обращении, умноженное на старую цену: линия капитализации может "
        "разойтись с линией цены. Гонка спрашивает у сервиса рейтинга, какие монеты сегодня крупнейшие, "
        "вместо того чтобы перечитывать заранее записанный список — включая стейблкоины.",
    "tr":
        "Kripto paralar artık kendi başına bir pazar. Ayarlardan seçtiğinizde gezinme altı kripto "
        "sayfasına dönüşüyor — mumlar, DCA planı, pozisyonlar, kazanç takvimi, piyasa değeri geçmişi ve "
        "piyasa değeri yarışı — hisse sayfaları ise kenara çekiliyor; pazar yalnızca bir kripto kaynağı "
        "yanıt verdiğinde görünüyor, bu yüzden pazar listesi hiçbir zaman bu bilgisayarın gerçekten "
        "ulaşabildiğinden fazlasını önermiyor. Mumlar sayfası 1, 5 ve 15 dakikalık periyotları da alıyor "
        "ve belirttiğiniz günü çiziyor. Altı sayfadan ikisi piyasa değerini çiziyor ve bu değer o gün "
        "ölçülmüş değer; bugünkü dolaşımdaki miktarın eski bir fiyatla çarpılması değil: piyasa değeri "
        "çizgisi fiyat çizgisinden ayrılabilir. Yarış, önceden yazılmış bir listeyi okumak yerine bir "
        "sıralama hizmetine «bugün hangi coinler en büyük» diye soruyor — stabilcoinler dahil.",
}


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # 各文件保持自己的行尾：store-listing.md 是 CRLF。
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    if sorted(NEWS) != sorted(LANGS):
        print("× 文案漏了语言：%s" % sorted(set(LANGS) - set(NEWS)))
        return 1

    changed = 0

    for n, lang in enumerate(LANGS):
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            print(f"× {lang}: 只数到 {len(subs)} 个小标题")
            return 1

        at = subs[1] + 1       # 「此版本的新增功能」下面的正文

        while at < end and not lines[at].strip():
            at += 1

        text = NEWS[lang]

        if lines[at] == text:
            print(f"· {lang}: （已是本版，{len(text)} 字）")
            continue

        lines[at] = text
        changed += 1
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: 「{lines[subs[1]][4:]}」改写（{len(text)} 字）")

    if changed:
        LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))

    longest = max((len(NEWS[l]), l) for l in LANGS)
    over = [(l, len(NEWS[l])) for l in LANGS if len(NEWS[l]) > LIMIT]

    if over:
        print(f"\n！超过商店 {LIMIT} 字上限：{over}")
        return 1

    print(f"\n最长的 {longest[1]} {longest[0]} 字，都在 {LIMIT} 以内")
    print(f"改了 {changed} 条（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
