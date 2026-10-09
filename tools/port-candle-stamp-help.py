# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「K 线走势」那一章补一条：比较画面现在写着它画到了哪一天。

**为什么非说不可**：多标的的画面在标题下面多了一块东西，而**这块东西是什么，画面上一个字都
没有**。分钟档是两行：上面那一行是「哪一天」，下面那一行是画面**此刻画到的时分**（跟着画面
走，不是「9:30 - 15:00」那种写死的交易时段）；日／周／月档只有上面那一行，而它同样是画面
**此刻画到的那一天** —— 也跟着画面走。不说明的话，读到的人只会当第二行是上面那行的注脚，或
者反过来把日／周／月 那一行读成「区间的起始日」（它写的是那一刻，不是区间的头）。

**为什么日／周／月只有一行**：那三档的「最新一刻」本来就是一个日期，而上面那行已经在说日期
了 —— 两个同样形状的日期叠着，读出来是「同一个日期写了两遍」。所以这三档把**那一行自己**改成
跟着画面走：日／周／月 的轴以天计，画面画到第几根，那一行就是那一根的日子。

**这是这一条第四次改**：第一次（第二行是区间「9:30 - 15:00」）、第二次（区间改成那一刻、字号
提到画面大字）、第三次（第二行退回分钟档、字号回到 22、日/周/月 只剩区间起始日）都进过手册，
所以脚本认得**上一次那一句** —— 撞见就**原地替换**，不是再插一条（插两条 = 画面上同一件事说
两遍，而 `git diff` 照样是纯新增，看不出来）。

**为什么按章节号定位**：`listingtext.chapter_of("NavCandle")` 从导航顺序算，导航顺序就是章节
顺序。写 14 个语言的标题字符串就是 14 处会失配的地方。

**不引用任何控件名字**：复选框、下拉框的名字在 14 种语言里各不相同，抄错一处就是一句指着不
存在的控件的说明。

**插在哪**：这一章**第一段连续的 `- ` 列表的末尾**。这一章的列表是完整的一段。

**重音字母照写。** 德语的 ä/ö/ü、法语的 é/è/ç、捷克语的 ř/ž/ů、土耳其语的 ğ/ı/ş、俄语的
я/ё 都是这个字的一部分，不是装饰；为了「保险」写成 a/o/u/e/c/r/z/g/i/s 等于在应用里挂一句
拼错的外语。文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM。

幂等：这一章里已经有这一条就跳过。

用法：<venv python> tools/port-candle-stamp-help.py      （跑第二遍应当是 14 个 already there）
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP
CHAPTER = lt.chapter_of("NavCandle")

LINE = {
    "zh-Hans": "- **比较画面说得出它画到了哪一天。** 分钟线（1／5／15 分钟）标题下面写两行：上面是"
               "那**一个交易日**的日期，下面一行是画面**此刻画到的时分** —— 跟着画面一分钟一分钟往"
               "前走；日／周／月线只有上面那一行，写画面**此刻画到的那一天**，跟着画面一天一天往"
               "前走。只有多标的的画面加这一块 —— 单标的的画面本来就把日期写在表头。",
    "zh-Hant": "- **比較畫面說得出它畫到了哪一天。** 分鐘線（1／5／15 分鐘）標題下面寫兩行：上面是"
               "那**一個交易日**的日期，下面一行是畫面**此刻畫到的時分** —— 跟著畫面一分鐘一分鐘往"
               "前走；日／週／月線只有上面那一行，寫畫面**此刻畫到的那一天**，跟著畫面一天一天往"
               "前走。只有多標的的畫面加這一塊 —— 單標的的畫面本來就把日期寫在表頭。",
    "en-US": "- **A comparison says which day it has drawn up to.** The minute periods (1, 5 and "
             "15) write two lines under the headline: that one trading day on top, and under it the "
             "time of day the frame has reached, moving with the picture minute by minute. The "
             "daily, weekly and monthly periods write the top line only — the day the frame has "
             "reached, moving with the picture day by day. Only the multi-instrument frames add this "
             "block — the single-instrument frame already carries the date of the candle it is "
             "drawing.",
    "ja": "- **複数銘柄の画面は、それがどの日まで描いたのかを言う。** 分足（1／5／15 分）は見出しの"
          "下に二行書く：上はその**一日**の日付、その下は画面が**いま描いている時刻** —— 絵とともに"
          "一分ずつ進む。日足・週足・月足は上の一行だけ、画面が**いま描いている日**を書く —— 絵と"
          "ともに一日ずつ進む。この塊が加わるのは複数銘柄の画面だけ —— 単一銘柄の画面はもともと表頭"
          "にそのローソク足の日付を出している。",
    "ko": "- **비교 화면은 어느 날까지 그렸는지 말해 준다.** 분봉(1／5／15분)은 제목 아래 두 줄을"
          " 적는다: 위는 그 **하루**의 날짜, 아래는 화면이 **지금 그리고 있는 시각** —— 그림과 함께"
          " 1분씩 나아간다. 일봉·주봉·월봉은 위의 한 줄만, 화면이 **지금 그리고 있는 날**을 적는다 ——"
          " 그림과 함께 하루씩 나아간다. 이 묶음이 붙는 것은 여러 종목을 그릴 때뿐 —— 종목 하나의"
          " 화면은 원래 머리에 그 봉의 날짜를 적고 있다.",
    "de": "- **Ein Vergleich sagt, bis zu welchem Tag er gezeichnet hat.** Die Minuten-Perioden (1, "
          "5 und 15) schreiben zwei Zeilen unter die Überschrift: oben jenen **einen Handelstag**, "
          "darunter die **Uhrzeit, die das Bild gerade erreicht** —— sie geht mit dem Bild Minute für "
          "Minute weiter. Die Tages-, Wochen- und Monats-Perioden schreiben nur die obere Zeile: den "
          "**Tag, den das Bild gerade erreicht** —— sie geht mit dem Bild Tag für Tag weiter. Diesen "
          "Block bekommen nur die Rahmen mit mehreren Instrumenten —— der Rahmen für ein einzelnes "
          "Instrument trägt das Datum der Kerze, die er zeichnet, schon in seiner Kopfzeile.",
    "fr": "- **Une comparaison dit jusqu'à quel jour elle a tracé.** Les périodes en minutes (1, 5 "
          "et 15) écrivent deux lignes sous le titre : en haut ce **seul jour de bourse**, en dessous "
          "l'**heure que l'image atteint à cet instant** —— elle avance avec l'image minute par "
          "minute. Les périodes quotidienne, hebdomadaire et mensuelle n'écrivent que la ligne du "
          "haut : le **jour que l'image atteint à cet instant** —— elle avance avec l'image jour "
          "après jour. Seules les images à plusieurs instruments ajoutent ce bloc —— l'image d'un "
          "seul instrument porte déjà la date de la bougie qu'elle trace dans son en-tête.",
    "it": "- **Un confronto dice fino a quale giorno ha disegnato.** I periodi al minuto (1, 5 e 15) "
          "scrivono due righe sotto il titolo: sopra quel **singolo giorno di borsa**, sotto "
          "l'**orario che l'immagine raggiunge in questo momento** —— avanza con l'immagine minuto "
          "per minuto. I periodi giornaliero, settimanale e mensile scrivono solo la riga superiore: "
          "il **giorno che l'immagine raggiunge in questo momento** —— avanza con l'immagine giorno "
          "per giorno. Questo blocco lo aggiungono solo i fotogrammi con più strumenti —— quello con "
          "un solo strumento porta già la data della candela che sta disegnando nella sua "
          "intestazione.",
    "es": "- **Una comparación dice hasta qué día ha dibujado.** Los periodos de minutos (1, 5 y 15) "
          "escriben dos líneas bajo el título: arriba ese **único día de negociación**, debajo la "
          "**hora que el cuadro alcanza en este momento** —— avanza con el cuadro minuto a minuto. "
          "Los periodos diario, semanal y mensual escriben solo la línea de arriba: el **día que el "
          "cuadro alcanza en este momento** —— avanza con el cuadro día a día. Este bloque lo añaden "
          "solo los fotogramas con varios instrumentos —— el de un solo instrumento ya lleva la fecha "
          "de la vela que está dibujando en su encabezado.",
    "pt-BR": "- **Uma comparação diz até que dia ela desenhou.** Os períodos de minutos (1, 5 e 15) "
             "escrevem duas linhas sob o título: em cima aquele **único dia de negociação**, embaixo "
             "a **hora que o quadro alcança neste momento** —— ela avança com o quadro minuto a "
             "minuto. Os períodos diário, semanal e mensal escrevem só a linha de cima: o **dia que o "
             "quadro alcança neste momento** —— avança com o quadro dia a dia. Esse bloco só é "
             "acrescentado pelos quadros com vários instrumentos —— o de um único instrumento já traz "
             "a data da vela que está desenhando no seu cabeçalho.",
    "pl": "- **Porównanie mówi, do którego dnia doszło.** Okresy minutowe (1, 5 i 15) piszą dwie "
          "linijki pod nagłówkiem: u góry ten **jeden dzień sesji**, pod nim **godzinę, do której "
          "kadr właśnie doszedł** —— posuwa się wraz z obrazem minuta po minucie. Okresy dzienny, "
          "tygodniowy i miesięczny piszą tylko górną linijkę: **dzień, do którego kadr właśnie "
          "doszedł** —— posuwa się wraz z obrazem dzień po dniu. Ten blok dostają tylko kadry z "
          "kilcoma instrumentami —— kadr z jednym instrumentem już nosi datę rysowanej świecy w "
          "nagłówku.",
    "cs": "- **Srovnání říká, ke kterému dni dokreslilo.** Minutové periody (1, 5 a 15) píší dva "
          "řádky pod nadpisem: nahoře ten **jeden obchodní den**, pod ním **čas, kterého obraz právě "
          "dosáhl** —— postupuje s obrazem minutu po minutě. Denní, týdenní a měsíční periody píší "
          "jen horní řádek: **den, kterého obraz právě dosáhl** —— postupuje s obrazem den po dni. "
          "Tento blok dostávají jen obrazy s více nástroji —— obraz s jedním nástrojem už nese datum "
          "kreslené svíčky ve své hlavičce.",
    "ru": "- **Сравнение говорит, до какого дня оно дорисовало.** Минутные периоды (1, 5 и 15) пишут "
          "две строки под заголовком: сверху тот **один торговый день**, под ним **время, которого "
          "кадр сейчас достиг** —— оно идёт вместе с кадром минута за минутой. Дневной, недельный и "
          "месячный периоды пишут только верхнюю строку: **день, которого кадр сейчас достиг** —— он "
          "идёт вместе с кадром день за днём. Этот блок получают только кадры с несколькими "
          "инструментами —— кадр с одним инструментом уже несёт дату рисуемой свечи в своём заголовке.",
    "tr": "- **Karşılaştırma hangi güne kadar çizdiğini söyler.** Dakika periyotları (1, 5 ve 15) "
          "başlığın altına iki satır yazar: üstte o **tek işlem günü**, altında karenin **o anda "
          "ulaştığı saat** —— kare ilerledikçe dakika dakika ilerler. Günlük, haftalık ve aylık "
          "periyotlar yalnızca üst satırı yazar: karenin **o anda ulaştığı gün** —— kare ilerledikçe "
          "gün gün ilerler. Bu bloğu yalnızca birden çok enstrümanlı kareler ekler —— tek "
          "enstrümanlı kare, çizdiği mumun tarihini zaten başlığında taşır.",
}

# 这一条已经进过三次手册，第 1、2 版早已被替换掉；撞见**上一次那一句**（第三版：分钟档两行、
# 日/周/月 只剩区间起始日）就原地换掉，不是再插一条 —— 插两条是画面上同一件事说两遍。
OLD = {
    "zh-Hans": "- **比较画面说得出这是哪一段。** 分钟线（1／5／15 分钟）标题下面写两行：上面是那"
               "**一个交易日**的日期，下面一行是画面**此刻画到的钟点** —— 跟着画面一分钟一分钟往"
               "前走；日／周／月线只有上面那一行，写区间的**起始日**。只有多标的的画面加这一块 ——"
               " 单标的的画面本来就把日期写在表头。",
    "zh-Hant": "- **比較畫面說得出這是哪一段。** 分鐘線（1／5／15 分鐘）標題下面寫兩行：上面是那"
               "**一個交易日**的日期，下面一行是畫面**此刻畫到的鐘點** —— 跟著畫面一分鐘一分鐘往"
               "前走；日／週／月線只有上面那一行，寫區間的**起始日**。只有多標的的畫面加這一塊 ——"
               " 單標的的畫面本來就把日期寫在表頭。",
    "en-US": "- **A comparison says which stretch of time it is a picture of.** The minute periods "
             "(1, 5 and 15) write two lines under the headline: that one trading day on top, and "
             "under it the clock the frame has reached at this moment, walking with the picture "
             "minute by minute. The daily, weekly and monthly periods write the top line only: the "
             "first day of the span. Only the multi-instrument frames add this block — the "
             "single-instrument frame already carries the date of the candle it is drawing.",
    "ja": "- **複数銘柄の画面は、それがどの期間の絵なのかを言う。** 分足（1／5／15 分）は見出しの下"
          "に二行書く：上はその**一日**の日付、その下は画面が**いま描いている時刻** —— 絵とともに"
          "一分ずつ進む。日足・週足・月足は上の一行だけ、区間の**最初の日**を書く。この塊が加わる"
          "のは複数銘柄の画面だけ —— 単一銘柄の画面はもともと表頭にそのローソク足の日付を出して"
          "いる。",
    "ko": "- **비교 화면은 어느 구간을 그린 것인지 말해 준다.** 분봉(1／5／15분)은 제목 아래 두 줄을"
          " 적는다: 위는 그 **하루**의 날짜, 아래는 화면이 **지금 그리고 있는 시각** —— 그림과 함께"
          " 1분씩 나아간다. 일봉·주봉·월봉은 위의 한 줄만, 구간의 **첫날**을 적는다. 이 묶음이 붙는"
          " 것은 여러 종목을 그릴 때뿐 —— 종목 하나의 화면은 원래 머리에 그 봉의 날짜를 적고 있다.",
    "de": "- **Ein Vergleich sagt, welcher Zeitabschnitt er ist.** Die Minuten-Perioden (1, 5 und "
          "15) schreiben zwei Zeilen unter die Überschrift: oben jenen **einen Handelstag**, "
          "darunter die **Uhrzeit, die das Bild gerade erreicht** —— sie geht mit dem Bild Minute "
          "für Minute weiter. Die Tages-, Wochen- und Monats-Perioden schreiben nur die obere "
          "Zeile: den **ersten Tag** des Zeitraums. Diesen Block bekommen nur die Rahmen mit "
          "mehreren Instrumenten —— der Rahmen für ein einzelnes Instrument trägt das Datum der "
          "Kerze, die er zeichnet, schon in seiner Kopfzeile.",
    "fr": "- **Une comparaison dit de quelle période elle est l'image.** Les périodes en minutes "
          "(1, 5 et 15) écrivent deux lignes sous le titre : en haut ce **seul jour de bourse**, "
          "en dessous l'**heure que l'image atteint à cet instant** —— elle avance avec l'image "
          "minute par minute. Les périodes quotidienne, hebdomadaire et mensuelle n'écrivent que "
          "la ligne du haut : le **premier jour** de l'intervalle. Seules les images à plusieurs "
          "instruments ajoutent ce bloc —— l'image d'un seul instrument porte déjà la date de la "
          "bougie qu'elle trace dans son en-tête.",
    "it": "- **Un confronto dice di quale intervallo di tempo è l'immagine.** I periodi al minuto "
          "(1, 5 e 15) scrivono due righe sotto il titolo: sopra quel **singolo giorno di borsa**, "
          "sotto l'**orario che l'immagine raggiunge in questo momento** —— avanza con l'immagine "
          "minuto per minuto. I periodi giornaliero, settimanale e mensile scrivono solo la riga "
          "superiore: il **primo giorno** dell'intervallo. Questo blocco lo aggiungono solo i "
          "fotogrammi con più strumenti —— quello con un solo strumento porta già la data della "
          "candela che sta disegnando nella sua intestazione.",
    "es": "- **Una comparación dice de qué tramo de tiempo es la imagen.** Los periodos de minutos "
          "(1, 5 y 15) escriben dos líneas bajo el título: arriba ese **único día de negociación**, "
          "debajo la **hora que el cuadro alcanza en este momento** —— avanza con el cuadro minuto "
          "a minuto. Los periodos diario, semanal y mensual escriben solo la línea de arriba: el "
          "**primer día** del intervalo. Este bloque lo añaden solo los fotogramas con varios "
          "instrumentos —— el de un solo instrumento ya lleva la fecha de la vela que está "
          "dibujando en su encabezado.",
    "pt-BR": "- **Uma comparação diz de qual intervalo de tempo ela é a imagem.** Os períodos de "
             "minutos (1, 5 e 15) escrevem duas linhas sob o título: em cima aquele **único dia de "
             "negociação**, embaixo a **hora que o quadro alcança neste momento** —— ela avança com "
             "o quadro minuto a minuto. Os períodos diário, semanal e mensal escrevem só a linha de "
             "cima: o **primeiro dia** do intervalo. Esse bloco só é acrescentado pelos quadros com "
             "vários instrumentos —— o de um único instrumento já traz a data da vela que está "
             "desenhando no seu cabeçalho.",
    "pl": "- **Porównanie mówi, który odcinek czasu przedstawia.** Okresy minutowe (1, 5 i 15) piszą "
          "dwie linijki pod nagłówkiem: u góry ten **jeden dzień sesji**, pod nim **godzinę, do "
          "której kadr właśnie doszedł** —— posuwa się wraz z obrazem minuta po minucie. Okresy "
          "dzienny, tygodniowy i miesięczny piszą tylko górną linijkę: **pierwszy dzień** zakresu. "
          "Ten blok dostają tylko kadry z kilkoma instrumentami —— kadr z jednym instrumentem już "
          "nosi datę rysowanej świecy w nagłówku.",
    "cs": "- **Srovnání říká, který úsek času zobrazuje.** Minutové periody (1, 5 a 15) píší dva "
          "řádky pod nadpisem: nahoře ten **jeden obchodní den**, pod ním **čas, kterého obraz "
          "právě dosáhl** —— postupuje s obrazem minutu po minutě. Denní, týdenní a měsíční periody "
          "píší jen horní řádek: **první den** rozsahu. Tento blok dostávají jen obrazy s více "
          "nástroji —— obraz s jedním nástrojem už nese datum kreslené svíčky ve své hlavičce.",
    "ru": "- **Сравнение говорит, какой отрезок времени оно показывает.** Минутные периоды (1, 5 и "
          "15) пишут две строки под заголовком: сверху тот **один торговый день**, под ним "
          "**время, которого кадр сейчас достиг** —— оно идёт вместе с кадром минута за минутой. "
          "Дневной, недельный и месячный периоды пишут только верхнюю строку: **первый день** "
          "интервала. Этот блок получают только кадры с несколькими инструментами —— кадр с одним "
          "инструментом уже несёт дату рисуемой свечи в своём заголовке.",
    "tr": "- **Karşılaştırma, hangi zaman aralığının resmi olduğunu söyler.** Dakika periyotları "
          "(1, 5 ve 15) başlığın altına iki satır yazar: üstte o **tek işlem günü**, altında "
          "karenin **o anda ulaştığı saat** —— kare ilerledikçe dakika dakika ilerler. Günlük, "
          "haftalık ve aylık periyotlar yalnızca üst satırı yazar: aralığın **ilk günü**. Bu bloğu "
          "yalnızca birden çok enstrümanlı kareler ekler —— tek enstrümanlı kare, çizdiği mumun "
          "tarihini zaten başlığında taşır.",
}


def insert(block, line):
    """插在这一章**第一段连续的 `- ` 列表**的末尾。"""
    run = []
    runs = []

    for i, text in enumerate(block):
        if text.startswith("- "):
            run.append(i)
        elif run:
            runs.append(run)
            run = []

    if run:
        runs.append(run)

    if not runs:
        raise AssertionError("this chapter has no bullet list")

    at = runs[0][-1] + 1

    return block[:at] + [line] + block[at:]


def main():
    for tag in lt.LANGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")
        starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

        end = starts[CHAPTER + 1] if CHAPTER + 1 < len(starts) else len(lines)
        block = lines[starts[CHAPTER]:end]

        spun = [line.strip() for line in block]

        if LINE[tag] in spun:
            print(f"{tag:9} already there")
            continue

        if OLD[tag] in spun:
            block[spun.index(OLD[tag])] = LINE[tag]
            note = "rewritten"
        else:
            block = insert(block, LINE[tag])
            note = "written"

        lines[starts[CHAPTER]:end] = block

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))
        print(f"{tag:9} {note}")


if __name__ == "__main__":
    main()
