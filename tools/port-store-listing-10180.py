# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.18.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 1.0.17.0 那一栏说的是手册补齐；那已经
交上去了，所以本版**另起一条，只说它之后的改动**——四个功能，都在这台机器的 1.0.17.0 之后：

- 加密 K 线：币种检索改为在线检索实际币种（和 A 股那页一样的做法），不再限死一张固定列表。
- 加密货币市值历程：支持同时画多只币种、各一条线，并可切换「实际数值 / 归一到 100」两种刻度。
- 加密货币新增「月度收益」页：把一只币逐月涨跌铺成年×月的红绿热力表。
- 持仓收益页的牛熊图标移到名称与收益框的正上方居中。

**只说用户能感知的那半句**，代码细节（Yahoo 日线折月、A 股矩阵渲染器复用）不写。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

脚本名由 manifest 的版本号算出 `10180`（1.0.18.0 → 四段拼起来）。`verify-docs.py` 把四段版本号
**全拼**当作文件名，算不出/找不到就大声失败。

用法：python tools\\port-store-listing-10180.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。
LIMIT = 1500

NEWS = {
    "zh-Hans":
        "本版聚焦加密货币与持仓页。加密 K 线现在像 A 股那样在线检索真实币种，不再限于固定列表；"
        "加密货币市值历程支持同时画多只币种、各一条线，并可切换「实际数值 / 归一到 100」两种刻度；"
        "加密货币新增月度收益页，把一只币逐月涨跌铺成年×月的红绿热力表。持仓收益页的牛熊图标移到"
        "名称与收益框的正上方居中。",
    "zh-Hant":
        "本版聚焦加密貨幣與持倉頁。加密 K 線現在像 A 股那樣線上檢索真實幣種，不再限於固定清單；"
        "加密貨幣市值歷程支援同時畫多隻幣種、各一條線，並可切換「實際數值 / 歸一到 100」兩種刻度；"
        "加密貨幣新增月度收益頁，把一隻幣逐月漲跌鋪成年×月的紅綠熱力表。持倉收益頁的牛熊圖標移到"
        "名稱與收益框的正上方居中。",
    "en-US":
        "This release focuses on crypto and the holdings page. Crypto K-line now searches real coins "
        "online, like the A-share page, instead of a fixed list. Crypto market-cap history draws "
        "several coins at once, one line each, with a switch between actual values and rebased-to-100. "
        "A new Crypto Monthly Returns page lays a coin's month-by-month gains and losses across a "
        "year-by-month red-and-green heat table. On the holdings page, the bull/bear badge moves to "
        "sit centred on top of the name-and-figure label.",
    "ja":
        "今回の更新は暗号資産と保有ページが中心です。暗号資産の K 線は A 株ページと同じく実在する通貨を"
        "オンライン検索し、固定リストに縛られなくなりました。暗号資産の時価総額の推移は複数通貨を同時に"
        "描き、それぞれ一本の線になり、「実数値 / 100 への正規化」の二つの目盛りを切り替えられます。"
        "暗号資産に月次リターンページが加わり、一つのコインの月ごとの値動きを年×月の赤緑ヒートマップに"
        "広げます。保有ページでは、牛熊のアイコンが名称と金額のラベルの真上中央に移りました。",
    "ko":
        "이번 업데이트는 암호화폐와 보유 페이지 중심입니다. 암호화폐 K선은 A주 페이지처럼 실제 코인을 "
        "온라인으로 검색하며 고정 목록에 얽매이지 않습니다. 암호화폐 시가총액 추이는 여러 코인을 한 번에 "
        "그리고 각각 한 줄씩, 「실제 수치 / 100 기준 정규화」 두 눈금을 전환할 수 있습니다. 암호화폐에 "
        "월간 수익 페이지가 추가되어 한 코인의 매월 등락을 연×월의 빨강·초록 히트맵으로 펼칩니다. "
        "보유 페이지에서 황소·곰 아이콘은 이름과 금액 라벨의 정확히 위쪽 중앙으로 옮겨졌습니다.",
    "de":
        "Dieses Release konzentriert sich auf Krypto und die Haltedauer-Seite. Der Krypto-Kurschart "
        "sucht jetzt wie die A-Aktien-Seite echte Coins online, statt einer festen Liste. Die "
        "Krypto-Marktkapitalisierung zeichnet mehrere Coins zugleich, jeweils eine Linie, und "
        "schaltet zwischen tatsächlichen Werten und auf 100 normiert um. Neu ist die Krypto-Seite "
        "Monatliche Rendite, die ein Coin in einer rot-grünen Jahres-×-Monats-Tabelle Monat für Monat "
        "zeigt. Auf der Haltedauer-Seite sitzt das Stier/Bär-Symbol nun mittig über der "
        "Namens-und-Betrag-Beschriftung.",
    "fr":
        "Cette version porte sur la crypto et la page de position. Le chandelier crypto recherche "
        "maintenant de vraies monnaies en ligne, comme la page A, au lieu d'une liste fixe. "
        "L'historique de capitalisation crypto dessine plusieurs monnaies à la fois, une ligne chacune, "
        "avec un choix entre valeurs réelles et réindexé à 100. Une page Rendements mensuels crypto "
        "arrive : elle étale les hausses et baisses d'un coin mois par mois dans un tableau rouge-vert "
        "année × mois. Sur la page de position, l'icône taureau/ours se place centrée au-dessus du "
        "libellé nom-montant.",
    "it":
        "Questa versione riguarda cripto e la pagina della posizione. Il candle crypto ora cerca monete "
        "reali online, come la pagina A, anziché da una lista fissa. La storia della capitalizzazione "
        "crypto disegna più monete insieme, una linea ciascuna, e commuta tra valori reali e ribasati a "
        "100. Arriva la pagina Rendimenti mensili crypto: distende i rialzi e ribassi di un coin mese "
        "per mese in una tabella rosso-verde anno × mese. Nella pagina posizione, l'icona toro/orso si "
        "sposta centrata sopra l'etichetta nome-importo.",
    "es":
        "Esta versión gira en torno a cripto y la página de posición. El velas cripto ahora busca "
        "monedas reales en línea, como la página A, en lugar de una lista fija. El historial de "
        "capitalización cripto dibuja varias monedas a la vez, una línea cada una, y alterna entre "
        "valores reales y rebasados a 100. Llega la página Rendimientos mensuales cripto, que extiende "
        "las subidas y bajadas de un coin mes a mes en una tabla roja y verde año × mes. En la página "
        "de posición, el icono toro/oso se sitúa centrado encima de la etiqueta nombre-importe.",
    "pt-BR":
        "Este lançamento foca em cripto e na página de posição. O candlestick cripto agora busca moedas "
        "reais online, como a página A, em vez de uma lista fixa. O histórico de capitalização cripto "
        "desenha várias moedas de uma vez, uma linha cada, e alterna entre valores reais e reindexado a "
        "100. Chega a página Retornos mensais cripto, que estende altas e baixas de um coin mês a mês "
        "numa tabela vermelho-verde ano × mês. Na página de posição, o ícone touro/urso vai para o "
        "centro acima do rótulo nome-valor.",
    "pl":
        "To wydanie skupia się na krypto i stronie pozycji. Świeca krypto teraz szuka prawdziwych "
        "coinów online, jak strona A, zamiast stałej listy. Historia kapitalizacji krypto rysuje kilka "
        "coinów naraz, po jednej linii, i przełącza między wartościami rzeczywistymi a przeliczonymi na "
        "100. Nowa strona Miesięczne stopy zwrotu krypto rozkłada wzrosty i spadki coina miesiąc po "
        "miesiącu w czerwono-zielonej tabeli rok × miesiąc. Na stronie pozycji ikona byk/niedźwiedź "
        "przesuwa się na środek nad etykietą nazwa-kwota.",
    "cs":
        "Toto vydání se točí kolem krypta a stránky pozice. Krypto svíčka teď hledá skutečné coiny "
        "online jako stránka A, místo pevného seznamu. Historie tržní kapitalizace krypta kreslí více "
        "coinů najednou, každý jednou čarou, a přepíná mezi skutečnými hodnotami a přepočtem na 100. "
        "Přibyla stránka Měsíční výnosy krypta, která rozloží růsty a propady coina měsíc po měsíci do "
        "červeno-zelené tabulky rok × měsíc. Na stránce pozice sedí ikona býk/medvěd vycentrovaná nad "
        "štítkem název-částka.",
    "ru":
        "Этот выпуск посвящён крипто и странице позиции. Свечи крипто теперь ищут реальные монеты "
        "онлайн, как страница A, а не по фиксированному списку. История капитализации крипто рисует "
        "несколько монет сразу, по одной линии, и переключается между реальными значениями и "
        "приведёнными к 100. Добавилась страница Месячная доходность крипто, раскладывающая рост и "
        "падения монеты помесячно в красно-зелёной таблице год × месяц. На странице позиции значок "
        "бык/медведь переехал в центр прямо над подписью «имя — сумма».",
    "tr":
        "Bu sürüm kripto ve pozisyon sayfasına odaklanıyor. Kripto mum grafiği artık A sayfasındaki "
        "gibi gerçek coinleri çevrimiçi arıyor, sabit bir listeyle sınırlı değil. Kripto piyasa değeri "
        "geçmişi birden çok coini aynı anda, her biri bir çizgi olacak şekilde çiziyor ve gerçek "
        "değerler ile 100'e göre normalize arasında geçiş yapıyor. Kripto için Aylık Getiriler sayfası "
        "eklendi; bir coin'in aylık yükseliş ve düşüşlerini yıl × ay kırmızı-yeşil ısı tablosuna seriyor. "
        "Pozisyon sayfasında boğa/ayı simgesi artık ad-tutar etiketinin tam üstünde, ortada duruyor.",
}


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

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
