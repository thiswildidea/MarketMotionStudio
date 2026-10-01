#!/usr/bin/env python3
"""Broaden the adjustment sentence in the store listing's fourteen "what's new"
lines.

The first pass at the adjustment fix described it as a Hong Kong and US problem,
because that was all that had been verified then. It is not: the general
endpoint's forward-adjusted series is wrong for an A-share heavy payer too —
its historical closes come back negative — so the gain matrix was dropping
months, and the race and the calendar were reading those closes as well. Every
page that draws a return now reads the total-return series, in all three
markets, and the listing should say so.

Idempotent: a line that already carries the new sentence is left alone.

Store field limit for "What's new in this version" is 1500 characters; the
script refuses to write anything longer.

Run: python tools/store-listing-adjustment.py
"""

from __future__ import annotations

import pathlib

PATH = pathlib.Path(r"D:\software\MarketMotionStudio\docs\store-listing.md")
LIMIT = 1500

# (old trailing sentence, new trailing sentence), in the file's own order.
PAIRS = [
    # zh-Hans
    ("另外，港股与美股的价格此前没有复权——拆股那天在图上是一次凭空的暴跌，分红也没有算进收益；"
     "现在这两个市场各走自己的复权序列。",
     "另外，价格此前没有复权——拆股那天在图上是一次凭空的暴跌，高分红股的历史收盘价甚至是负数；"
     "收益矩阵、行业板块竞速、涨跌日历读的都是同一批价格。现在三个市场、所有画收益的页面都走各自"
     "的复权序列。"),
    # zh-Hant
    ("另外，港股與美股的價格此前沒有復權——拆股那天在圖上是一次憑空的暴跌，分紅也沒有算進收益；"
     "現在這兩個市場各走自己的復權序列。",
     "另外，價格此前沒有復權——拆股那天在圖上是一次憑空的暴跌，高分紅股的歷史收盤價甚至是負數；"
     "收益矩陣、行業板塊競速、漲跌日曆讀的都是同一批價格。現在三個市場、所有畫收益的頁面都走各自"
     "的復權序列。"),
    # en-US
    ("Hong Kong and US prices were unadjusted too: a split arrived as a collapse out of nowhere, "
     "and dividends never came back to the holder. Both venues now read their adjusted series.",
     "Prices were unadjusted too: a split arrived as a collapse out of nowhere, and on a heavy "
     "dividend payer the historical closes were negative — the return matrix, the sector race and "
     "the calendar all read them. Now all three markets and every page that draws a return read "
     "their own adjusted series."),
    # ja
    ("また、香港株と米国株の価格は調整されていませんでした——分割の日が根拠のない暴落として描かれ、"
     "配当も収益に含まれていませんでした。両市場は現在、調整済みの系列を読みます。",
     "また、価格は調整されていませんでした——分割の日が根拠のない暴落として描かれ、高配当銘柄では"
     "過去の終値が負になることさえありました。収益マトリックス、業種レース、カレンダーも同じ価格を"
     "読んでいました。現在は3つの市場すべてと、収益を描くすべてのページがそれぞれの調整済み系列を"
     "読みます。"),
    # ko
    ("또한 홍콩과 미국 가격은 조정되지 않았습니다. 분할이 근거 없는 폭락으로 나타나고 배당도 수익에 "
     "반영되지 않았습니다. 두 시장은 이제 조정된 시계열을 읽습니다.",
     "가격도 조정되지 않았습니다. 분할이 근거 없는 폭락으로 나타나고, 고배당 종목은 과거 종가가 음수가 "
     "되기까지 했습니다. 수익 매트릭스, 업종 레이스, 캘린더도 같은 가격을 읽었습니다. 이제 세 시장 "
     "모두와 수익을 그리는 모든 페이지가 각자의 조정 시계열을 읽습니다."),
    # de
    ("Außerdem waren die Kurse aus Hongkong und den USA unbereinigt: Ein Split erschien als "
     "Absturz aus dem Nichts, und Dividenden fehlten im Ertrag. Beide Märkte lesen nun ihre "
     "bereinigten Reihen.",
     "Außerdem waren die Kurse unbereinigt: Ein Split erschien als Absturz aus dem Nichts, und bei "
     "stark ausschüttenden Werten waren die historischen Schlusskurse sogar negativ — "
     "Renditematrix, Sektorrennen und Kalender lasen dieselben Werte. Nun lesen alle drei Märkte "
     "und jede Seite, die eine Rendite zeichnet, ihre eigene bereinigte Reihe."),
    # fr
    ("En outre, les cours de Hong Kong et des États-Unis n'étaient pas ajustés : un "
     "fractionnement apparaissait comme un effondrement sans cause et les dividendes manquaient. "
     "Les deux places lisent désormais leurs séries ajustées.",
     "En outre, les cours n'étaient pas ajustés : un fractionnement apparaissait comme un "
     "effondrement sans cause, et pour les gros distributeurs de dividendes les clôtures "
     "historiques étaient même négatives — la matrice de rendement, la course sectorielle et le "
     "calendrier lisaient les mêmes valeurs. Désormais les trois marchés et toutes les pages qui "
     "tracent un rendement lisent leur propre série ajustée."),
    # it
    ("Inoltre i prezzi di Hong Kong e degli Stati Uniti non erano rettificati: un frazionamento "
     "appariva come un crollo immotivato e i dividendi mancavano. Ora entrambe le piazze leggono "
     "le loro serie rettificate.",
     "Inoltre i prezzi non erano rettificati: un frazionamento appariva come un crollo immotivato "
     "e per i titoli ad alto dividendo le chiusure storiche erano persino negative — la matrice "
     "dei rendimenti, la corsa settoriale e il calendario leggevano gli stessi valori. Ora tutti "
     "e tre i mercati e ogni pagina che disegna un rendimento leggono la propria serie "
     "rettificata."),
    # es
    ("Además, los precios de Hong Kong y Estados Unidos no estaban ajustados: un desdoblamiento "
     "aparecía como un desplome sin causa y los dividendos faltaban. Ahora ambas plazas leen sus "
     "series ajustadas.",
     "Además, los precios no estaban ajustados: un desdoblamiento aparecía como un desplome sin "
     "causa y en los valores de alto dividendo los cierres históricos eran incluso negativos — la "
     "matriz de rentabilidad, la carrera sectorial y el calendario leían los mismos valores. Ahora "
     "los tres mercados y todas las páginas que dibujan una rentabilidad leen su propia serie "
     "ajustada."),
    # pt-BR
    ("Além disso, os preços de Hong Kong e dos Estados Unidos não eram ajustados: um "
     "desdobramento aparecia como uma queda sem causa e os dividendos faltavam. Agora ambas as "
     "praças leem suas séries ajustadas.",
     "Além disso, os preços não eram ajustados: um desdobramento aparecia como uma queda sem causa "
     "e, nos papéis de alto dividendo, os fechamentos históricos eram até negativos — a matriz de "
     "retorno, a corrida setorial e o calendário liam os mesmos valores. Agora os três mercados e "
     "todas as páginas que desenham um retorno leem sua própria série ajustada."),
    # pl
    ("Ponadto ceny z Hongkongu i USA nie były korygowane: split pojawiał się jako nagły krach, a "
     "dywidendy nie wracały do właściciela. Oba rynki czytają teraz skorygowane serie.",
     "Ponadto ceny nie były korygowane: split pojawiał się jako nagły krach, a przy spółkach o "
     "wysokiej dywidendzie historyczne zamknięcia były wręcz ujemne — macierz stóp zwrotu, wyścig "
     "sektorów i kalendarz czytały te same wartości. Teraz wszystkie trzy rynki i każda strona "
     "rysująca stopę zwrotu czytają własną skorygowaną serię."),
    # cs
    ("Kromě toho nebyly ceny z Hongkongu a USA upraveny: štěpení se jevilo jako pád bez příčiny a "
     "dividendy chyběly. Obě burzy nyní čtou upravené řady.",
     "Kromě toho nebyly ceny upraveny: štěpení se jevilo jako pád bez příčiny a u akcií s "
     "vysokou dividendou byla historická zavírací cena dokonce záporná — matice výnosů, sektorový "
     "závod a kalendář čtou tatáž data. Nyní všechny tři trhy i každá stránka kreslící výnos čtou "
     "vlastní upravenou řadu."),
    # ru
    ("Кроме того, цены Гонконга и США не были скорректированы: дробление выглядело как обвал без "
     "причины, а дивиденды не учитывались. Теперь оба рынка читают скорректированные ряды.",
     "Кроме того, цены не были скорректированы: дробление выглядело как обвал без причины, а у "
     "акций с высокими дивидендами исторические закрытия были даже отрицательными — матрица "
     "доходности, гонка секторов и календарь читали те же значения. Теперь все три рынка и все "
     "страницы, рисующие доходность, читают собственный скорректированный ряд."),
    # tr
    ("Ayrıca Hong Kong ve ABD fiyatları düzeltilmemişti: bir bölünme nedensiz bir çöküş gibi "
     "görünüyor, temettüler de hesaba katılmıyordu. Artık iki piyasa da düzeltilmiş serilerini "
     "okuyor.",
     "Ayrıca fiyatlar düzeltilmemişti: bir bölünme nedensiz bir çöküş gibi görünüyor, yüksek "
     "temettülü hisselerde geçmiş kapanışlar eksiye bile düşüyordu — getiri matrisi, sektör yarışı "
     "ve takvim de aynı fiyatları okuyordu. Artık üç pazar da ve getiri çizen her sayfa kendi "
     "düzeltilmiş serisini okuyor."),
]

HEADINGS = [28, 64, 100, 136, 172, 208, 244, 280, 316, 351, 387, 423, 459, 495]


def main() -> None:
    raw = PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "文件不该有 BOM"

    text = raw.decode("utf-8")
    lines = text.split("\n")

    assert len(PAIRS) == len(HEADINGS), "每条语言要配一个行号"

    for line_number, (old, new) in zip(HEADINGS, PAIRS):
        index = line_number + 1  # 标题、空行、正文
        para = lines[index]

        if new in para:
            print(f"  {line_number}: 已改过，跳过")
            continue

        assert old in para, f"第 {line_number} 行没找到原文：{old[:40]}"
        para = para.replace(old, new)

        assert len(para) <= LIMIT, f"第 {line_number} 行 {len(para)} 字符，超过 {LIMIT}"
        lines[index] = para
        print(f"  {line_number}: {len(para)} 字符")

    PATH.write_bytes("\n".join(lines).encode("utf-8"))
    again = PATH.read_bytes()
    assert not again.startswith(b"\xef\xbb\xbf"), "写回来不该带 BOM"

    longest = max(len(lines[n + 1]) for n in HEADINGS)
    print(f"\n十四份已更新，最长 {longest} 字符（上限 {LIMIT}），无 BOM。")


if __name__ == "__main__":
    main()
