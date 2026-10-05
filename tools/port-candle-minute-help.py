# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的 K 线那一章加上「分钟周期 + 指定交易日」。

章节正文的归属仍在 `port-candle-help.py`：那 14 段文字是那一章的**唯一**一份原文，本脚本
import 它、在正文里插一条，而不是把整章抄第二遍 —— 抄一遍就是两份会各自漂移的原文。

三件事值得写进帮助里，因为它们在界面上看不出来：

* **只有沪深两市有分钟 K 线。** 港股、美股、北证 50 的分钟档是灰的（源端返空的 `data`）。
* **「交易日」是源端还留着的那些日子，不是日历。** 端点不接受日期区间，只给「最近 N 根」，
  所以能挑的范围随周期变：1 分钟约 4 天、5 分钟约 17 天、15 分钟约 50 天。
* **换一天只重画。** 所有可选的日子都在同一个请求里回来的。

写法：定位那一章的标题行（标题按语言各写各的，从 `port-candle-help.SECTIONS` 取），
改写正文的前三个片段（引子句、周期那条后面的新条目），其余条目原样保留。

文件编码：**照原样**（`had_bom` 记号 + 条件前缀）——帮助手册是 LF 且无 BOM，硬写 BOM 会
在 diff 里表现为首行多一个看不见的字符，肉眼查不出来。

用法：python tools\port-candle-minute-help.py
"""
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

TAGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
        "ja", "ko", "zh-Hans", "zh-Hant"]


def _chapter_text():
    """The fourteen chapters, from the script that owns them."""
    spec = importlib.util.spec_from_file_location("port_candle_help", HERE / "port-candle-help.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.SECTIONS


SECTIONS = _chapter_text()

# 引子句：原文只说「日K、周K、月K 三种周期」，现在多了一档。
INTRO = {
    "en-US": "One instrument's prices as candles: daily, weekly or monthly, or minute candles "
             "for one named trading day — drawn four ways, with its averages and its volume "
             "underneath.",
    "de": "Die Kerzen eines Instruments: täglich, wöchentlich oder monatlich — oder "
          "Minutenkerzen für einen einzelnen Handelstag — auf vier Arten gezeichnet, mit "
          "Durchschnitten und Volumen darunter.",
    "es": "Las velas de un instrumento: diarias, semanales o mensuales — o velas por minuto "
          "de un día de negociación concreto — dibujadas de cuatro formas, con sus medias y "
          "su volumen debajo.",
    "fr": "Les chandeliers d'un instrument : quotidiens, hebdomadaires ou mensuels — ou par "
          "minute pour une journée de bourse précise — dessinés de quatre façons, avec ses "
          "moyennes et son volume en dessous.",
    "it": "Le candele di uno strumento: giornaliere, settimanali o mensili — o al minuto per "
          "una singola giornata di borsa — disegnate in quattro modi, con le medie e il "
          "volume sotto.",
    "pl": "Świece jednego instrumentu: dzienne, tygodniowe lub miesięczne — albo minutowe dla "
          "jednego wybranego dnia sesji — rysowane na cztery sposoby, ze średnimi i "
          "wolumenem poniżej.",
    "pt-BR": "Os candles de um instrumento: diários, semanais ou mensais — ou de minuto para "
             "um único dia de negociação — desenhados de quatro formas, com médias e volume "
             "abaixo.",
    "cs": "Svíčky jednoho nástroje: denní, týdenní nebo měsíční — nebo minutové pro jeden "
          "zvolený obchodní den — kreslené čtyřmi způsoby, s průměry a objemem pod nimi.",
    "tr": "Bir enstrümanın mumları: günlük, haftalık veya aylık — ya da tek bir işlem günü "
          "için dakika mumları — dört farklı şekilde çizilir; altında ortalamaları ve hacmi.",
    "ru": "Свечи одного инструмента: дневные, недельные или месячные — либо минутные за один "
          "выбранный торговый день, — в четырёх видах, со скользящими средними и объёмом "
          "ниже.",
    "ja": "1つの銘柄のローソク足。日足・週足・月足に加えて、指定した取引日1日分の分足も"
          "選べます。4つの描き方で表示し、下段に移動平均と出来高。",
    "ko": "한 종목의 캔들입니다. 일·주·월에 더해, 지정한 거래일 하루치 분봉도 고를 수 "
          "있습니다. 네 가지 방식으로 그리고 아래에 이동평균과 거래량.",
    "zh-Hans": "一只标的的价格 K 线：日K、周K、月K，以及指定某一个交易日的 1／5／15 分钟 K "
               "线。四种画法，下方带均线与成交量。",
    "zh-Hant": "一檔標的的 K 線：日K、週K、月K，以及指定某個交易日的 1／5／15 分鐘 K 線。"
               "四種畫法，下方帶均線與成交量。",
}

# 新条目，插在「周期」那条之后。
MINUTE = {
    "en-US": "- **1, 5 and 15 minutes** draw one trading day: the session from the open to the "
             "close, laid out on an axis that runs by the clock and leaves the ninety minutes "
             "nobody traded off it, so the morning and the afternoon meet across a hairline "
             "where the break was. The source keeps minute candles for Shanghai and Shenzhen "
             "only, and only for the last few sessions — about four days at one minute, "
             "seventeen at five, fifty at fifteen — so **trading day** is a list of the days it "
             "still has rather than a calendar. Picking another of them only draws it again.",

    "de": "- **1, 5 und 15 Minuten** zeichnen einen Handelstag: die Sitzung von der Eröffnung "
          "bis zum Schluss, auf einer Achse nach der Uhr, die die neunzig Minuten ohne Handel "
          "auslässt, sodass sich Vormittag und Nachmittag an einer Haarlinie treffen, statt ein "
          "Drittel des Bildes leer zu lassen. Die Quelle führt Minutenkerzen nur für Shanghai "
          "und Shenzhen und nur für die letzten Sitzungen — etwa vier Tage bei einer Minute, "
          "siebzehn bei fünf, fünfzig bei fünfzehn — daher ist **Handelstag** eine Liste der "
          "noch vorhandenen Tage und kein Kalender. Eine andere Auswahl zeichnet nur neu.",

    "es": "- **1, 5 y 15 minutos** dibujan un día de negociación: la sesión de la apertura al "
          "cierre, en un eje que sigue el reloj y deja fuera los noventa minutos sin "
          "negociación, de modo que la mañana y la tarde se encuentran en una línea fina en vez "
          "de dejar vacío un tercio del dibujo. La fuente solo conserva velas por minuto de "
          "Shanghái y Shenzhen, y solo de las últimas sesiones —unos cuatro días a un minuto, "
          "diecisiete a cinco, cincuenta a quince—, así que **día de negociación** es una lista "
          "de los días que aún tiene, no un calendario. Elegir otro solo vuelve a dibujar.",

    "fr": "- **1, 5 et 15 minutes** dessinent une journée de bourse : la séance de l'ouverture à "
          "la clôture, sur un axe qui suit l'horloge et retire les quatre-vingt-dix minutes sans "
          "cotation, si bien que le matin et l'après-midi se rejoignent sur un filet plutôt que "
          "de laisser un tiers du cadre vide. La source ne conserve les bougies par minute que "
          "pour Shanghai et Shenzhen, et seulement pour les dernières séances — environ quatre "
          "jours à une minute, dix-sept à cinq, cinquante à quinze — donc **Jour de bourse** "
          "est une liste des jours encore disponibles, pas un calendrier. En choisir un autre "
          "ne fait que redessiner.",

    "it": "- **1, 5 e 15 minuti** disegnano una giornata di borsa: la seduta dall'apertura alla "
          "chiusura, su un asse che segue l'orologio ed esclude i novanta minuti senza scambi, "
          "così che mattina e pomeriggio si incontrano su una linea sottile invece di lasciare "
          "vuoto un terzo del quadro. La fonte conserva le candele al minuto solo per Shanghai e "
          "Shenzhen, e solo per le ultime sedute — circa quattro giorni a un minuto, "
          "diciassette a cinque, cinquanta a quindici — quindi **Giornata di borsa** è un "
          "elenco dei giorni ancora disponibili, non un calendario. Sceglierne un altro "
          "ridisegna soltanto.",

    "pl": "- **1, 5 i 15 minut** rysują jeden dzień sesji: od otwarcia do zamknięcia, na osi "
          "według zegara, która pomija dziewięćdziesiąt minut bez handlu, więc przedpołudnie i "
          "popołudnie stykają się na cienkiej linii zamiast zostawiać pustą jedną trzecią obrazu. "
          "Źródło trzyma świece minutowe tylko dla Szanghaju i Shenzhen i tylko za ostatnie "
          "sesje — około czterech dni przy jednej minucie, siedemnastu przy pięciu, "
          "pięćdziesięciu przy piętnastu — więc **Dzień sesji** to lista dni, które jeszcze ma, "
          "a nie kalendarz. Wybór innego dnia tylko przerysowuje.",

    "pt-BR": "- **1, 5 e 15 minutos** desenham um dia de negociação: o pregão da abertura ao "
             "fechamento, num eixo que segue o relógio e deixa fora os noventa minutos sem "
             "negócios, de modo que a manhã e a tarde se encontram numa linha fina em vez de "
             "deixar um terço do quadro vazio. A fonte mantém candles de minuto apenas para "
             "Xangai e Shenzhen, e só das últimas sessões — cerca de quatro dias a um minuto, "
             "dezessete a cinco, cinquenta a quinze — então **Dia de negociação** é uma lista "
             "dos dias que ainda tem, não um calendário. Escolher outro apenas redesenha.",

    "cs": "- **1, 5 a 15 minut** kreslí jeden obchodní den: seanci od otevření do závěru na ose "
          "podle hodin, která vynechává devadesát minut bez obchodování, takže dopoledne a "
          "odpoledne se potkají na tenké čáře, místo aby třetina obrázku zůstala prázdná. Zdroj "
          "uchovává minutové svíčky jen pro Šanghaj a Šen-čen a jen za poslední seance — zhruba "
          "čtyři dny při jedné minutě, sedmnáct při pěti, padesát při patnácti — takže "
          "**Obchodní den** je seznam dnů, které ještě má, a ne kalendář. Výběr jiného dne jen "
          "překreslí.",

    "tr": "- **1, 5 ve 15 dakika** tek bir işlem gününü çizer: açılıştan kapanışa seans, saate "
          "göre kurulan ve hiç işlem geçmeyen doksan dakikayı dışarıda bırakan bir eksende; "
          "öğleden önce ve sonra, resmin üçte birini boş bırakmak yerine ince bir çizgide "
          "buluşur. Kaynak dakika mumlarını yalnızca Şanghay ve Shenzhen için ve yalnızca son "
          "birkaç seans için tutar — bir dakikada yaklaşık dört gün, beşte on yedi, on beşte "
          "elli — bu yüzden **İşlem günü** bir takvim değil, hâlâ elinde olan günlerin "
          "listesidir. Başka bir günü seçmek yalnızca yeniden çizer.",

    "ru": "- **1, 5 и 15 минут** рисуют один торговый день: сессию от открытия до закрытия на "
          "оси по часам, из которой убраны девяносто минут без торговли, поэтому утро и день "
          "сходятся на тонкой линии вместо того, чтобы треть картинки пустовала. Источник хранит "
          "минутные свечи только для Шанхая и Шэньчжэня и только за последние сессии — около "
          "четырёх дней на минутных, семнадцати на пятиминутных, пятидесяти на "
          "пятнадцатиминутных, — поэтому **Торговый день** это список ещё имеющихся дней, а не "
          "календарь. Выбор другого дня только перерисовывает.",

    "ja": "- **1・5・15 分**は1取引日を描きます。寄り付きから引けまでの1日を時計どおりの横軸に"
          "置きますが、取引のなかった90分は軸から外すため、午前と午後は細い線を挟んで接し、"
          "画面の3分の1が空白になることはありません。ソースが分足を保持しているのは上海と深圳"
          "だけで、しかも直近数セッションのみ（1分で約4日、5分で約17日、15分で約50日）です。"
          "そのため**取引日**はカレンダーではなく、いま残っている日の一覧です。"
          "別の日を選んでも再取得せず、描き直すだけです。",

    "ko": "- **1·5·15분**은 하루치 거래일을 그립니다. 시가부터 종가까지의 하루를 시계대로 둔 "
          "가로축에 그리되, 거래가 없었던 90분은 축에서 빼기 때문에 오전과 오후는 가는 선을 "
          "사이에 두고 맞닿고 화면의 3분의 1이 비지 않습니다. 소스가 분봉을 보관하는 곳은 "
          "상하이와 선전뿐이고 최근 몇 세션만입니다(1분 약 4일, 5분 약 17일, 15분 약 50일). "
          "그래서 **거래일**은 달력이 아니라 아직 남아 있는 날의 목록입니다. 다른 날을 골라도 "
          "다시 가져오지 않고 다시 그릴 뿐입니다.",

    "zh-Hans": "- **1／5／15 分钟**画的是**某一个交易日**：从开盘到收盘的那一天，横轴按钟点铺，"
               "但没人交易的 90 分钟不计入轴上，上下午隔着一条细缝相接，画面不再有三分之一是空的。"
               "来源只为沪深两市保留分钟 K 线，而且只留最近几个交易日（1 分钟约 4 天、5 分钟约 "
               "17 天、15 分钟约 50 天），所以**交易日**是它现在还留着的那些日子，不是日历。"
               "换一天只重画，不重新取数。",

    "zh-Hant": "- **1／5／15 分鐘**畫的是**某一個交易日**：從開盤到收盤的那一天，橫軸按鐘點鋪，"
               "但沒人交易的 90 分鐘不計入軸上，上下午隔著一條細縫相接，畫面不再有三分之一是空的。"
               "來源只為滬深兩市保留分鐘 K 線，而且只留最近幾個交易日（1 分鐘約 4 天、5 分鐘約 "
               "17 天、15 分鐘約 50 天），所以**交易日**是它現在還留着的那些日子，不是日曆。"
               "換一天只重畫，不重新取數。",
}


def heading_for(tag):
    """The chapter's title line, from the script that wrote it."""
    return SECTIONS[tag].split("\n", 1)[0].strip()


def bullets_start(tag):
    """How many of the chapter's bullets the chapter text above knows about.

    Only used as a floor for the sanity check below: the live chapter carries more bullets
    than `port-candle-help.py` wrote — the range one was appended later, by another
    script — which is exactly why this pass edits the file in place instead of rewriting
    the chapter from that text. Rewriting it dropped the range bullet on all fourteen
    files, and the diff looked like an ordinary edit.
    """
    return sum(1 for line in SECTIONS[tag].split("\n") if line.startswith("- "))


def marker_for(tag):
    """The bullet's own "- **X**" head — fourteen different ways to say "1, 5 and 15 minutes".

    Cut off the text after the bold head rather than hardcoding fourteen heads twice: editing
    the sentence above once may not be the last time it is edited, and the head is what says
    which bullet this script owns when the sentence behind it has changed.
    """
    line = MINUTE[tag]

    return line[:line.index("**", line.index("**") + 2) + 2]


def main() -> int:
    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")

        text = raw.decode("utf-8-sig").lstrip("\ufeff")

        crlf = "\r\n" in text
        joiner = "\r\n" if crlf else "\n"
        lines = text.split(joiner)

        wanted = heading_for(tag)
        headings = [i for i, line in enumerate(lines) if line.startswith("## ")]
        found = [i for i in headings if lines[i].strip() == wanted]

        if len(found) != 1:
            print(f"{tag}: {len(found)} chapters titled {wanted!r} — refusing to guess")
            return 1

        start = found[0]
        end = next((i for i in headings if i > start), len(lines))

        chapter = lines[start + 1:end]

        # 幂等：这一条已经是一字不差的当前文案就整章不动。少了这一道，第二次跑会把同一条
        # 再插一遍 —— 而重复的一条在渲染出来的帮助页上只是多了一行，截图与逐章校验都看不出来。
        if any(line.strip() == MINUTE[tag] for line in chapter):
            print(f"{tag:9} already there")
            continue

        # 引子句：本章第一个非空行。
        intro = next(i for i, line in enumerate(chapter) if line.strip())

        # 条目：从第一条 "- " 起，到本章最后一条为止。插在第一条之后 —— 按位置而不是按
        # 文字，十四种语言的「周期」写法各不相同。
        bullets = [i for i, line in enumerate(chapter) if line.startswith("- ")]

        if len(bullets) < bullets_start(tag):
            print(f"{tag}: {len(bullets)} bullets in the file, {bullets_start(tag)} expected")
            return 1

        # 已经在里面的**旧版**那一句要就地换掉，不能再来一条。午休从轴上剔掉之后这句话
        # 变了，而它的抬头十四种语言各写各的（"1, 5 and 15 minutes" / "1・5・15 分" …）——
        # 按抬头认这条谁属于我，不去碰同一章里别的条目。
        owned = [i for i in bullets if chapter[i].startswith(marker_for(tag))]

        if owned:
            chapter = (
                chapter[:intro] + [INTRO[tag]] + chapter[intro + 1:owned[0]]
                + [MINUTE[tag]] + chapter[owned[0] + 1:])
        else:
            chapter = (
                chapter[:intro] + [INTRO[tag]] + chapter[intro + 1:bullets[0] + 1]
                + [MINUTE[tag]] + chapter[bullets[0] + 1:])

        lines = lines[:start + 1] + chapter + lines[end:]

        # 照原样写回：BOM 有就有、没有就没有。帮助手册是 LF 且无 BOM，硬写 BOM 会在
        # diff 里表现为首行多一个看不见的字符。
        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + joiner.join(lines).encode("utf-8"))

        print(f"{tag:9} intro + 1 bullet, bom={had_bom}, crlf={crlf}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
