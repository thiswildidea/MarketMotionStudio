# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「K 线走势」那一章补一条：比较画面现在写着它是哪一段。

**为什么非说不可**：新加的那两行里，**第二行不是自明的**。分钟线那一行是画面**此刻画到的钟点**，
跟着画面走（它是窗口的右缘，不是「9:30 - 15:00」那种写死的交易时段）；日／周／月线那一行是
区间的起止两天 —— 上下排着两个同样格式的日期，不说明的话读的人只能猜它们谁是头谁是尾（猜错
了就是把图读反）。而这一处又说不得一个字：画面上没有标签的地方，写「起」「止」就又要 14 份
翻译，还要占掉那两行的宽度。

**第二行的字号也是要说的**：它是画面的大字 —— 与另外几个画「一个数字」的页面同字号。不写这
一句，读到的人只会当它是日期的注脚（它原来就是 22px 的一行小字，比副标题还小）。

**改过一次**：这一条已经进过一次手册（那时第二行还是「当天交易的钟点」，没说字号也不跟着
走）。所以脚本认得旧那一句 —— 撞见就**原地替换**，不是再插一条（插两条 = 画面上同一件事说两
遍，而 `git diff` 照样是纯新增，看不出来）。

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
    "zh-Hans": "- **比较画面说得出这是哪一段。** 标题下面两行：分钟线写那**一个交易日**的日期，下面"
               "一行是画面**此刻画到的钟点** —— 画面的大字，跟着画面走；日／周／月线写区间的**起止"
               "两天**。只有多标的的画面加这两行 —— 单标的的画面本来就把日期写在表头。",
    "zh-Hant": "- **比較畫面說得出這是哪一段。** 標題下面兩行：分鐘線寫那**一個交易日**的日期，下面"
               "一行是畫面**此刻畫到的鐘點** —— 畫面的大字，跟著畫面走；日／週／月線寫區間的**起止"
               "兩天**。只有多標的的畫面加這兩行 —— 單標的的畫面本來就把日期寫在表頭。",
    "en-US": "- **A comparison says which stretch of time it is a picture of.** Two lines under the "
             "headline: the minute periods name that one trading day, and under it — at headline "
             "size, moving as the picture moves — the clock the frame has reached at this moment; "
             "the daily, weekly and monthly ones name the first and last day of the span. Only the "
             "multi-instrument frames add these two — the single-instrument frame already carries "
             "the date of the candle it is drawing.",
    "ja": "- **複数銘柄の画面は、それがどの期間の絵なのかを言う。** 見出しの下に二行：分足はその**"
          "一日**の日付を書き、その下に画面が**いま描いている時刻**を —— 絵の大字で、絵の進行に"
          "合わせて動く。日足・週足・月足は区間の**最初と最後の日**を書く。この二行が加わるのは複数"
          "銘柄の画面だけ —— 単一銘柄の画面はもともと表頭にそのローソク足の日付を出している。",
    "ko": "- **비교 화면은 어느 구간을 그린 것인지 말해 준다.** 제목 아래 두 줄: 분봉은 그 **하루**의"
          " 날짜를 적고, 그 아래에 화면이 **지금 그리고 있는 시각**을 —— 화면의 큰 글씨로, 그림이"
          " 진행되며 따라 움직인다. 일봉·주봉·월봉은 구간의 **첫날과 마지막 날**을 적는다. 이 두 줄이"
          " 붙는 것은 여러 종목을 그릴 때뿐 —— 종목 하나의 화면은 원래 머리에 그 봉의 날짜를 적고"
          " 있다.",
    "de": "- **Ein Vergleich sagt, welcher Zeitabschnitt er ist.** Zwei Zeilen unter der Überschrift:"
          " Die Minuten-Perioden nennen jenen **einen Handelstag** und darunter — in der Größe einer "
          "Schlagzeile und mit dem Bild mitgehend — die **Uhrzeit, die das Bild gerade erreicht**; "
          "die Tages-, Wochen- und Monats-Perioden nennen den **ersten und den letzten Tag** des "
          "Zeitraums. Diese zwei Zeilen bekommen nur die Rahmen mit mehreren Instrumenten —— der "
          "Rahmen für ein einzelnes Instrument trägt das Datum der Kerze, die er zeichnet, schon in "
          "seiner Kopfzeile.",
    "fr": "- **Une comparaison dit de quelle période elle est l'image.** Deux lignes sous le titre : "
          "les périodes en minutes nomment ce **seul jour de bourse** et, en dessous — à la taille "
          "d'un titre et en suivant l'image — l'**heure que l'image a atteinte à cet instant** ; les "
          "périodes quotidienne, hebdomadaire et mensuelle nomment le **premier et le dernier jour** "
          "de l'intervalle. Seules les images à plusieurs instruments ajoutent ces deux lignes —— "
          "l'image d'un seul instrument porte déjà la date de la bougie qu'elle trace dans son "
          "en-tête.",
    "it": "- **Un confronto dice di quale intervallo di tempo è l'immagine.** Due righe sotto il "
          "titolo: i periodi al minuto indicano quel **singolo giorno di borsa** e, sotto — in corpo "
          "da titolo e seguendo l'immagine — l'**orario che l'immagine ha raggiunto in quel "
          "momento**; quelli giornaliero, settimanale e mensile indicano il **primo e l'ultimo "
          "giorno** dell'intervallo. Queste due righe le aggiungono solo i fotogrammi con più "
          "strumenti —— quello con un solo strumento porta già la data della candela che sta "
          "disegnando nella sua intestazione.",
    "es": "- **Una comparación dice de qué tramo de tiempo es la imagen.** Dos líneas bajo el título: "
          "los periodos de minutos nombran ese **único día de negociación** y, debajo — con el "
          "tamaño de un titular y siguiendo al cuadro — la **hora que el cuadro ha alcanzado en ese "
          "momento**; los periodos diario, semanal y mensual nombran el **primer y el último día** "
          "del intervalo. Estas dos líneas las añaden solo los fotogramas con varios instrumentos "
          "—— el de un solo instrumento ya lleva la fecha de la vela que está dibujando en su "
          "encabezado.",
    "pt-BR": "- **Uma comparação diz de qual intervalo de tempo ela é a imagem.** Duas linhas sob o "
             "título: os períodos de minutos nomeiam aquele **único dia de negociação** e, abaixo — "
             "no tamanho de uma manchete e acompanhando o quadro — a **hora que o quadro alcançou "
             "naquele momento**; os períodos diário, semanal e mensal nomeiam o **primeiro e o "
             "último dia** do intervalo. Essas duas linhas só são acrescentadas pelos quadros com "
             "vários instrumentos —— o de um único instrumento já traz a data da vela que está "
             "desenhando no seu cabeçalho.",
    "pl": "- **Porównanie mówi, który odcinek czasu przedstawia.** Dwie linijki pod nagłówkiem: "
          "okresy minutowe podają ten **jeden dzień sesji**, a pod nim — wielkością nagłówka i wraz "
          "z ruchem obrazu — **godzinę, do której kadr właśnie doszedł**; okresy dzienny, "
          "tygodniowy i miesięczny podają **pierwszy i ostatni dzień** zakresu. Te dwie linijki "
          "dostają tylko kadry z kilkoma instrumentami —— kadr z jednym instrumentem już nosi datę "
          "rysowanej świecy w nagłówku.",
    "cs": "- **Srovnání říká, který úsek času zobrazuje.** Dva řádky pod nadpisem: minutové periody "
          "uvádějí ten **jeden obchodní den** a pod ním — velikostí nadpisu a spolu s pohybem obrazu "
          "— **čas, kterého obraz právě dosáhl**; denní, týdenní a měsíční periody uvádějí **první a "
          "poslední den** rozsahu. Tyto dva řádky přidávají jen obrazy s více nástroji —— obraz s "
          "jedním nástrojem už nese datum kreslené svíčky ve své hlavičce.",
    "ru": "- **Сравнение говорит, какой отрезок времени оно показывает.** Две строки под заголовком: "
          "минутные периоды называют тот **один торговый день**, а под ним — размером заголовка и "
          "вместе с движением кадра — **время, которого кадр сейчас достиг**; дневной, недельный и "
          "месячный — **первый и последний день** интервала. Эти две строки добавляют только кадры "
          "с несколькими инструментами —— кадр с одним инструментом уже несёт дату рисуемой свечи в "
          "своём заголовке.",
    "tr": "- **Karşılaştırma, hangi zaman aralığının resmi olduğunu söyler.** Başlığın altında iki "
          "satır: dakika periyotları o **tek işlem gününü** yazar, altında ise — başlık boyutunda ve "
          "kare ilerledikçe — karenin **o anda ulaştığı saati** gösterir; günlük, haftalık ve aylık "
          "periyotlar ise aralığın **ilk ve son gününü** yazar. Bu iki satırı yalnızca birden çok "
          "enstrümanlı kareler ekler —— tek enstrümanlı kare, çizdiği mumun tarihini zaten "
          "başlığında taşır.",
}

# 这一条进过一次手册，那时第二行还是「当天交易的钟点」、也没说字号。撞见旧那一句就**原地换掉**，
# 不是再插一条 —— 插两条是画面上同一件事说两遍。
OLD = {
    "zh-Hans": "- **比较画面说得出这是哪一段。** 标题下面两行：分钟线写那**一个交易日**的日期和画面"
               "实际画到的钟点，日／周／月线写区间的**起止两天**。只有多标的的画面加这两行 —— 单标"
               "的的画面本来就把日期写在表头。",
    "zh-Hant": "- **比較畫面說得出這是哪一段。** 標題下面兩行：分鐘線寫那**一個交易日**的日期和畫面"
               "實際畫到的鐘點，日／週／月線寫區間的**起止兩天**。只有多標的的畫面加這兩行 —— 單標"
               "的的畫面本來就把日期寫在表頭。",
    "en-US": "- **A comparison says which stretch of time it is a picture of.** Two lines under the "
             "headline: the minute periods name that one trading day and the clock the frame "
             "actually reaches, while the daily, weekly and monthly ones name the first and last "
             "day of the span. Only the multi-instrument frames add these two — the "
             "single-instrument frame already carries the date of the candle it is drawing.",
    "ja": "- **複数銘柄の画面は、それがどの期間の絵なのかを言う。** 見出しの下に二行：分足はその**"
          "一日**の日付と画面が実際に描いている時刻を書き、日足・週足・月足は区間の**最初と最後の"
          "日**を書く。この二行が加わるのは複数銘柄の画面だけ —— 単一銘柄の画面はもともと表頭に"
          "そのローソク足の日付を出している。",
    "ko": "- **비교 화면은 어느 구간을 그린 것인지 말해 준다.** 제목 아래 두 줄: 분봉은 그 **하루**의"
          " 날짜와 화면이 실제로 그린 시각을, 일봉·주봉·월봉은 구간의 **첫날과 마지막 날**을 적는다."
          " 이 두 줄이 붙는 것은 여러 종목을 그릴 때뿐 —— 종목 하나의 화면은 원래 머리에 그 봉의"
          " 날짜를 적고 있다.",
    "de": "- **Ein Vergleich sagt, welcher Zeitabschnitt er ist.** Zwei Zeilen unter der Überschrift:"
          " Die Minuten-Perioden nennen jenen **einen Handelstag** und die Uhrzeit, die das Bild "
          "tatsächlich erreicht, die Tages-, Wochen- und Monats-Perioden nennen den **ersten und "
          "den letzten Tag** des Zeitraums. Diese zwei Zeilen bekommen nur die Rahmen mit mehreren "
          "Instrumenten —— der Rahmen für ein einzelnes Instrument trägt das Datum der Kerze, die "
          "er zeichnet, schon in seiner Kopfzeile.",
    "fr": "- **Une comparaison dit de quelle période elle est l'image.** Deux lignes sous le titre : "
          "les périodes en minutes nomment ce **seul jour de bourse** et les heures que l'image "
          "atteint réellement, les périodes quotidienne, hebdomadaire et mensuelle nomment le "
          "**premier et le dernier jour** de l'intervalle. Seules les images à plusieurs instruments "
          "ajoutent ces deux lignes —— l'image d'un seul instrument porte déjà la date de la bougie "
          "qu'elle trace dans son en-tête.",
    "it": "- **Un confronto dice di quale intervallo di tempo è l'immagine.** Due righe sotto il "
          "titolo: i periodi al minuto indicano quel **singolo giorno di borsa** e l'orario che "
          "l'immagine raggiunge davvero, quelli giornaliero, settimanale e mensile indicano il "
          "**primo e l'ultimo giorno** dell'intervallo. Queste due righe le aggiungono solo i "
          "fotogrammi con più strumenti —— quello con un solo strumento porta già la data della "
          "candela che sta disegnando nella sua intestazione.",
    "es": "- **Una comparación dice de qué tramo de tiempo es la imagen.** Dos líneas bajo el título:"
          " los periodos de minutos nombran ese **único día de negociación** y la hora que el cuadro "
          "alcanza realmente, mientras que los periodos diario, semanal y mensual nombran el "
          "**primer y el último día** del intervalo. Estas dos líneas las añaden solo los fotogramas "
          "con varios instrumentos —— el de un solo instrumento ya lleva la fecha de la vela que "
          "está dibujando en su encabezado.",
    "pt-BR": "- **Uma comparação diz de qual intervalo de tempo ela é a imagem.** Duas linhas sob o "
             "título: os períodos de minutos nomeiam aquele **único dia de negociação** e a hora que "
             "o quadro realmente alcança, enquanto os períodos diário, semanal e mensal nomeiam o "
             "**primeiro e o último dia** do intervalo. Essas duas linhas só são acrescentadas pelos "
             "quadros com vários instrumentos —— o de um único instrumento já traz a data da vela que "
             "está desenhando no seu cabeçalho.",
    "pl": "- **Porównanie mówi, który odcinek czasu przedstawia.** Dwie linijki pod nagłówkiem: "
          "okresy minutowe podają ten **jeden dzień sesji** i godzinę, którą kadr rzeczywiście "
          "obejmuje, a okresy dzienny, tygodniowy i miesięczny podają **pierwszy i ostatni dzień** "
          "zakresu. Te dwie linijki dostają tylko kadry z kilkoma instrumentami —— kadr z jednym "
          "instrumentem już nosi datę rysowanej świecy w nagłówku.",
    "cs": "- **Srovnání říká, který úsek času zobrazuje.** Dva řádky pod nadpisem: minutové periody "
          "uvádějí ten **jeden obchodní den** a čas, který obraz skutečně dosáhne, denní, týdenní a "
          "měsíční periody uvádějí **první a poslední den** rozsahu. Tyto dva řádky přidávají jen "
          "obrazy s více nástroji —— obraz s jedním nástrojem už nese datum kreslené svíčky ve své "
          "hlavičce.",
    "ru": "- **Сравнение говорит, какой отрезок времени оно показывает.** Две строки под заголовком: "
          "минутные периоды называют тот **один торговый день** и время, которого кадр действительно "
          "достигает, а дневной, недельный и месячный — **первый и последний день** интервала. Эти "
          "две строки добавляют только кадры с несколькими инструментами —— кадр с одним "
          "инструментом уже несёт дату рисуемой свечи в своём заголовке.",
    "tr": "- **Karşılaştırma, hangi zaman aralığının resmi olduğunu söyler.** Başlığın altında iki "
          "satır: dakika periyotları o **tek işlem gününü** ve karenin gerçekten ulaştığı saati, "
          "günlük, haftalık ve aylık periyotlar ise aralığın **ilk ve son gününü** yazar. Bu iki "
          "satırı yalnızca birden çok enstrümanlı kareler ekler —— tek enstrümanlı kare, çizdiği "
          "mumun tarihini zaten başlığında taşır.",
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
            at = spun.index(OLD[tag])
            block[at] = LINE[tag]
            lines[starts[CHAPTER]:end] = block
            print(f"{tag:9} rewritten")
        else:
            lines[starts[CHAPTER]:end] = insert(block, LINE[tag])
            print(f"{tag:9} written")

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))
        print(f"{tag:9} written")


if __name__ == "__main__":
    main()
