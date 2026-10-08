# -*- coding: utf-8 -*-
r"""改 14 份帮助手册「K 线走势」章里那条「选两个以上标的」的结尾：说清两件事。

**一、交易日列出的是「共有」的日子。** 用户的原话是「为什么交易日为空」：比较取完数之后
那个下拉是空的。现在它列的是所有标的都有的那些交易日，默认取最近一个完整交易日。不说，
读者会以为这个下拉在比较画面下坏掉了 —— 或者更糟：以为随便挑一天都能比。

**二、分钟周期下曲线相对前收盘起算。** 用户的原话是「上证指数今天跌了 0.79，图上对不上」：
图上那条是 -0.71%，因为零点取的是**当日开盘**。一天是相对前收盘算的，这也是那个大数字和
行情软件给的口径。日线以上没这个问题（那里本来就是区间第一根的开盘，两者差一天，而那
一天正是区间的一部分）。

**为什么不写进 resw**：那句话是控件旁边的一行短说明（「来源只保留最近几个交易日的分钟
K 线——这里列出的是它现在还留着的日子」），对比较画面不算说错，只是不全。事实写在手册
这一处，界面那行不动 —— 一件事在三处说，就必然有一天三处说得不一样。

**为什么按章节号定位**：`listingtext.chapter_of("NavCandle")` 从导航顺序算。写 14 个语言的
标题字符串，就是 14 处会失配的地方。

**为什么按「结尾原句」定位而不是按条数**：这一章有 11 条，而条数会随版本变。结尾原句是
这一条独有的，找到就改、找不到就大声失败 —— 而不是悄悄跳过，留下 13 种语言说了、1 种没说。

**重音字母照写。** 德语的 ü、法语的 é/è/ô、捷克语的 ř/ž/í、土耳其语的 ğ/ı/ş、俄语的
я/ё、韩语的字素都是这个词的一部分，不是装饰。文件是 UTF-8，Python 3 源码默认就是 UTF-8。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM。

幂等：这一条已经以新结尾收尾就跳过。

用法：<venv python> tools/port-candle-boardday-help.py     （跑第二遍应当是 14 个 already there）
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP
CHAPTER = lt.chapter_of("NavCandle")

OLD = {
    "zh-Hans": "分钟周期下所有的标的画在同一个交易日上：它们各自都有的最近一个完整交易日。",
    "zh-Hant": "分鐘週期下所有的標的畫在同一個交易日上：它們各自都有的最近一個完整交易日。",
    "en-US": "On the minute periods all of them are drawn on one trading day: the newest session "
             "every one of them has.",
    "ja": "分足の期間では、すべてが一つの売買日に描かれます。それぞれが持つ最新のセッションです。",
    "ko": "분 단위 기간에서는 모두가 하나의 거래일에 그려집니다. 각각이 가진 가장 최근 세션입니다.",
    "de": "Bei den Minuten-Perioden werden alle am selben Handelstag gezeichnet: an der jüngsten "
          "Sitzung, die jedes von ihnen hat.",
    "fr": "Sur les périodes en minutes, tous sont tracés le même jour de bourse : la séance la "
          "plus récente que chacun possède.",
    "it": "Nei periodi al minuto tutti sono disegnati nella stessa giornata di borsa: la seduta "
          "più recente che ciascuno ha.",
    "es": "En los periodos de minutos todos se dibujan en un mismo día de negociación: la sesión "
          "más reciente que cada uno de ellos tiene.",
    "pt-BR": "Nos períodos de minutos, todos são desenhados no mesmo dia de negociação: a sessão "
             "mais recente que cada um tem.",
    "pl": "W okresach minutowych wszystkie są rysowane w tym samym dniu sesji: najnowszym, jaki "
          "każdy z nich ma.",
    "cs": "V minutových periodách jsou všechny nakresleny v jeden obchodní den: v nejnovější "
          "seanci, kterou každý z nich má.",
    "ru": "На минутных периодах все они рисуются в один торговый день — в самую свежую сессию, "
          "которая есть у каждого.",
    "tr": "Dakika periyotlarında hepsi tek bir işlem gününde çizilir: her birinin sahip olduğu en "
          "yeni seans.",
}

NEW = {
    "zh-Hans": "分钟周期下所有的标的画在同一个交易日上：**交易日**里列的就是它们共有的那些日子，"
               "默认取最近一个完整交易日。分钟周期下的曲线相对**前收盘**起算，所以末端那个数字"
               "就是各标的的当日涨跌幅。",
    "zh-Hant": "分鐘週期下所有的標的畫在同一個交易日上：**交易日**裡列的就是它們共有的那些日子，"
               "預設取最近一個完整交易日。分鐘週期下的曲線相對**前收盤**起算，所以末端那個數字"
               "就是各標的的當日漲跌幅。",
    "en-US": "On the minute periods all of them are drawn on one trading day: **trading day** "
             "lists the ones they all have, opening on the newest whole one, and the curves are "
             "measured from the **previous close** — so the figure at the end is each "
             "instrument's move for the day.",
    "ja": "分足の期間では、すべてが一つの売買日に描かれます。**取引日**にはそれらが共有する日が"
          "並び、既定では直近の完全なセッションです。分足の曲線は**前日終値**を基準に描くため、"
          "末端の数字は各銘柄のその日の騰落率になります。",
    "ko": "분 단위 기간에서는 모두가 하나의 거래일에 그려집니다. **거래일**에는 그것들이 모두 가진 "
          "날이 나열되고, 기본값은 가장 최근의 온전한 세션입니다. 분 단위 곡선은 **전일 종가**를 "
          "기준으로 그리므로 끝의 숫자가 각 종목의 그날 등락률입니다.",
    "de": "Bei den Minuten-Perioden werden alle am selben Handelstag gezeichnet: **Handelstag** "
          "listet die Tage, die alle gemeinsam haben, voreingestellt die jüngste vollständige "
          "Sitzung, und die Kurven werden vom **vorherigen Schluss** aus gemessen — die Zahl am "
          "Ende ist also die Tagesveränderung des jeweiligen Instruments.",
    "fr": "Sur les périodes en minutes, tous sont tracés le même jour de bourse : **Jour de "
          "bourse** liste ceux qu'ils ont en commun, par défaut la séance complète la plus "
          "récente, et les courbes partent du **cours de clôture précédent** — le chiffre au bout "
          "est donc la variation du jour de chaque instrument.",
    "it": "Nei periodi al minuto tutti sono disegnati nella stessa giornata di borsa: **Giornata "
          "di borsa** elenca quelle che hanno in comune, per impostazione predefinita la seduta "
          "completa più recente, e le curve partono dalla **chiusura precedente** — la cifra in "
          "fondo è quindi la variazione del giorno di ciascuno strumento.",
    "es": "En los periodos de minutos todos se dibujan en un mismo día de negociación: **día de "
          "negociación** enumera los que todos comparten, por defecto la sesión completa más "
          "reciente, y las curvas parten del **cierre anterior**, así que la cifra del final es "
          "la variación del día de cada instrumento.",
    "pt-BR": "Nos períodos de minutos, todos são desenhados no mesmo dia de negociação: **Dia de "
             "negociação** lista os que todos têm em comum, por padrão a sessão completa mais "
             "recente, e as curvas partem do **fechamento anterior**, então o número no fim é a "
             "variação do dia de cada instrumento.",
    "pl": "W okresach minutowych wszystkie są rysowane w tym samym dniu sesji: **Dzień sesji** "
          "wylicza te, które mają wszystkie, domyślnie najnowszą pełną sesję, a krzywe liczy się "
          "od **poprzedniego zamknięcia** — liczba na końcu to więc dzienna zmiana każdego "
          "instrumentu.",
    "cs": "V minutových periodách jsou všechny nakresleny v jeden obchodní den: **Obchodní den** "
          "vypisuje ty, které mají všechny společné, ve výchozím stavu nejnovější celou seanci, a "
          "křivky se měří od **předchozího závěru** — číslo na konci je tedy denní změna každého "
          "nástroje.",
    "ru": "На минутных периодах все они рисуются в один торговый день: **Торговый день** "
          "перечисляет те, что есть у всех, по умолчанию — самую свежую полную сессию, а кривые "
          "отсчитываются от **предыдущего закрытия**, так что число на конце — это дневное "
          "изменение каждого инструмента.",
    "tr": "Dakika periyotlarında hepsi tek bir işlem gününde çizilir: **İşlem günü** hepsinin "
          "ortak olduğu günleri listeler, varsayılanı en yeni tam seanstır ve eğriler **önceki "
          "kapanıştan** ölçülür; yani uçtaki sayı her enstrümanın o günkü değişimidir.",
}


def reword(block, tag):
    """这一章里以 OLD[tag] 收尾的那一条，换成以 NEW[tag] 收尾。找不到就抛。"""
    at = [i for i, text in enumerate(block) if text.endswith(OLD[tag])]

    if len(at) != 1:
        raise AssertionError(
            f"{tag}: 以原句收尾的 bullet 有 {len(at)} 条，应当是 1 条。"
            "这一条是这一章独有的、也是最长的，找不到就说明它被改过或换了行 —— 不能猜。")

    was = block[at[0]]

    return block[:at[0]] + [was[:len(was) - len(OLD[tag])] + NEW[tag]] + block[at[0] + 1:]


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

        if any(line.endswith(NEW[tag]) for line in block):
            print(f"{tag:9} already there")
            continue

        lines[starts[CHAPTER]:end] = reword(block, tag)

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))
        print(f"{tag:9} written")


if __name__ == "__main__":
    main()
