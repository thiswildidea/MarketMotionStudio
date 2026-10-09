# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.13.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是 K 线页可以一次比较多
个标的、排布可以选、涨跌改从前一交易日收盘算起、五页底部的卡片不再压在手机那条按钮栏下。那是真
的，也已经交上去了（1.0.12.0，审核中）。接着往后加，这一栏就成了两件事各说一半。

本版只有一件事，且是用户在画面上看得见的：**多标的的画面说出「画面走到哪儿了」** —— 日／周／月
那一行日期跟着画面走，写的是正在画的那一天；1／5／15 分钟档上面是那一个交易日的日期，下面多一
行跟着画面一分钟一分钟走的钟点。

**不提实现方式。** 两行读的是窗口右缘那一个数、分钟档为什么上面那行不动、26 px 是怎么从 128 退回
来的 —— 那都是代码的事。用户能感知的只有：画面上方现在会说走到哪一天／哪个钟点。把内部的措辞写
进商店文案，等于让用户替我们查错。

**也不点控件的名字。** 周期下拉在各语言里拼法不同，抄错一处就是一句指着不存在的东西的话。只说
「日线、周线、月线」和「1／5／15 分钟档」这些画面上本来就在说的词。

**重音字母照写。** 德语的 ü/ä、法语的 é/ç、捷克的 ř/ž、波兰语的 ł/ż、土耳其语的 ğ/ı 是这个字
的一部分，不是装饰；为了「保险」把它们写成 u/a/e/c/r/z/l/g/i 等于在商店里挂一句拼错的德语。
文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

**脚本名由 manifest 的版本号算出 `10130`，不是取巧写成 `1130`。** `verify-docs.py` 把四段版本
号**全拼**当作文件名（`1.0.13.0` → 四段拼起来是 `10130`；写成 `1130` 是省掉了第三段的一位，那是
留给 `1.1.3.0` 的形状），算不出/找不到就大声失败。

用法：python tools\\port-store-listing-10130.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。本版只说一件事，比上一版的三件事短得多 —— 但每次换文案都要算一遍最长的
# 那一种语言：上限是按字符算的，德/意/葡一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**比较多只标的时画面上方会说走到哪儿了 —— 日／周／月是跟着
# 画面走的那一天，1／5／15 分钟档是那一个交易日加一行跟着走的钟点；单标的的画面本来就有日期。**
NEWS = {
    "zh-Hans":
        "本版 K 线页一次比较多只标的时，画面上方会说出「画面走到哪儿了」：日线、周线、月线那一"
        "行跟着画面走，写的是正在画的那一天，不是区间从哪天起；1／5／15 分钟档上面是那一个交易日"
        "的日期，下面多一行钟点，跟着画面一分钟一分钟地走。只有多标的的画面加这一块 —— 单标的的"
        "画面本来就有日期。",
    "zh-Hant":
        "本版 K 線頁一次比較多檔標的時，畫面上方會說出「畫面走到哪兒了」：日線、週線、月線那一"
        "行跟著畫面走，寫的是正在畫的那一天，不是區間從哪天起；1／5／15 分鐘檔上面是那一個交易日"
        "的日期，下面多一行時刻，跟著畫面一分鐘一分鐘地走。只有多標的的畫面加這一塊 —— 單標的的"
        "畫面本來就有日期。",
    "en-US":
        "This version adds one line to a frame comparing several instruments: it says where the "
        "picture has got to. On the daily, weekly and monthly periods the date walks with the "
        "animation and names the candle being drawn, not the first day of the range. On the 1-, 5- "
        "and 15-minute periods the top row names the trading day and a row under it gives the time "
        "of day, moving minute by minute with the picture. Only frames with several instruments get "
        "it — a frame with one has always carried its own date.",
    "ja":
        "今回のバージョンでは、複数の銘柄を比較する画面の上部に「今どこまで描いたか」が表示されま"
        "す。日足・週足・月足では日付の行がアニメーションとともに動き、期間の初日ではなく今描いて"
        "いる足の日付を示します。1分・5分・15分では上段にその取引日の日付、下段に時刻が表示され、"
        "時刻は画面とともに一分ずつ進みます。この表示は複数銘柄を比較する画面だけで、銘柄が一つの"
        "画面には以前から日付が表示されています。",
    "ko":
        "이번 버전에서는 여러 종목을 비교하는 화면 위에 「화면이 어디까지 왔는지」가 표시됩니다. "
        "일·주·월 봉에서 날짜 줄은 애니메이션과 함께 움직이며, 구간의 첫날이 아니라 지금 그리고 있는 "
        "봉의 날짜를 보여줍니다. 1·5·15분 봉에서는 위 줄에 그 거래일의 날짜, 아래 줄에 시각이 표시되"
        "고, 시각은 화면과 함께 일 분씩 움직입니다. 이 표시는 여러 종목을 비교하는 화면에만 추가되며,"
        " 종목이 하나인 화면에는 원래 날짜가 표시되어 있습니다.",
    "de":
        "Diese Version fügt dem Bild, das mehrere Werte vergleicht, eine Zeile hinzu: es sagt jetzt, "
        "wo es angekommen ist. Bei Tages-, Wochen- und Monatskerzen läuft die Datumszeile mit der "
        "Animation mit und nennt den Tag der Kerze, die gerade gezeichnet wird — nicht den ersten Tag "
        "des Zeitraums. Bei 1, 5 und 15 Minuten nennt die obere Zeile den Handelstag und eine Zeile "
        "darunter die Uhrzeit, die mit dem Bild Minute für Minute weiterläuft. Nur Bilder mit "
        "mehreren Werten erhalten sie; ein Bild mit einem Wert trug sein Datum schon immer.",
    "fr":
        "Cette version ajoute une ligne à l'image qui compare plusieurs instruments : elle dit "
        "maintenant où elle en est. En journalier, hebdomadaire et mensuel, la ligne de date suit "
        "l'animation et nomme la bougie en cours de tracé, et non le premier jour de la période. En "
        "1, 5 et 15 minutes, la ligne du haut nomme le jour de bourse et une ligne en dessous donne "
        "l'heure, qui avance minute par minute avec l'image. Seules les images à plusieurs "
        "instruments en bénéficient ; avec un seul instrument, la date a toujours été là.",
    "it":
        "Questa versione aggiunge una riga all'immagine che confronta più strumenti: ora dice a che "
        "punto è. Nei periodi giornaliero, settimanale e mensile la riga della data segue "
        "l'animazione e indica la candela che si sta disegnando, non il primo giorno "
        "dell'intervallo. Nei periodi da 1, 5 e 15 minuti la riga superiore indica il giorno di "
        "borsa e una riga sotto di essa l'ora, che avanza minuto per minuto con l'immagine. Solo le "
        "immagini con più strumenti la ricevono: con un solo strumento la data c'è sempre stata.",
    "es":
        "Esta versión añade una línea a la imagen que compara varios instrumentos: ahora dice por "
        "dónde va. En periodos diario, semanal y mensual, la línea de la fecha avanza con la "
        "animación y nombra la vela que se está dibujando, no el primer día del rango. En periodos de "
        "1, 5 y 15 minutos la línea superior da el día de negociación y una línea debajo la hora, que "
        "avanza minuto a minuto con la imagen. Solo la reciben las imágenes con varios instrumentos; "
        "con uno solo la fecha ya estaba.",
    "pt-BR":
        "Esta versão acrescenta uma linha à imagem que compara vários instrumentos: agora ela diz "
        "onde está. Nos períodos diário, semanal e mensal, a linha da data acompanha a animação e "
        "mostra a vela que está sendo desenhada, não o primeiro dia do intervalo. Nos períodos de 1, "
        "5 e 15 minutos, a linha de cima dá o dia de negociação e uma linha abaixo a hora, que avança "
        "minuto a minuto com a imagem. Só as imagens com vários instrumentos a recebem; com um único "
        "instrumento a data sempre esteve lá.",
    "pl":
        "Ta wersja dodaje jedną linię do obrazu porównującego kilka instrumentów: mówi on teraz, "
        "dokąd doszedł. W okresach dziennym, tygodniowym i miesięcznym linia daty porusza się razem "
        "z animacją i podaje dzień właśnie rysowanej świecy, a nie pierwszy dzień zakresu. W okresach "
        "1, 5 i 15 minut górna linia podaje dzień sesji, a poniżej jest godzina, która przesuwa się z "
        "obrazem minuta po minucie. Dotyczy to tylko obrazów z kilkoma instrumentami — przy jednym "
        "instrumencie data była od zawsze.",
    "cs":
        "Tato verze přidává jeden řádek obrazu, který porovnává více nástrojů: říká nyní, kam "
        "došel. V denním, týdenním a měsíčním období se řádek s datem pohybuje s animací a uvádí den "
        "právě kreslené svíce, nikoli první den rozsahu. V obdobích 1, 5 a 15 minut horní řádek "
        "uvádí obchodní den a pod ním čas, který postupuje s obrazem minutu po minutě. Dostane jej "
        "jen obraz s více nástroji; u jednoho nástroje tam datum bylo vždy.",
    "ru":
        "В этой версии у кадра, сравнивающего несколько инструментов, появилась строка, которая "
        "говорит, до какого момента дошёл рисунок. На дневном, недельном и месячном периодах строка "
        "с датой движется вместе с анимацией и называет день рисуемой свечи, а не первый день "
        "диапазона. На периодах 1, 5 и 15 минут верхняя строка называет торговый день, а под ней "
        "идёт время, которое идёт вместе с рисунком минута за минутой. Это касается только кадров "
        "с несколькими инструментами; у одного инструмента дата была и раньше.",
    "tr":
        "Bu sürümde birden fazla enstrümanı karşılaştıran kareye bir satır ekleniyor: kare artık "
        "nereye geldiğini söylüyor. Günlük, haftalık ve aylık dönemlerde tarih satırı animasyonla "
        "birlikte ilerler ve aralığın ilk gününü değil, çizilmekte olan mumun gününü söyler. 1, 5 ve "
        "15 dakikalık dönemlerde üst satır işlem gününü, altındaki satır da kareyle birlikte dakika "
        "dakika ilerleyen saati verir. Bu yalnızca birden fazla enstrümanın olduğu karelerde görünür; "
        "tek enstrümanın karesinde tarih zaten vardı.",
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
