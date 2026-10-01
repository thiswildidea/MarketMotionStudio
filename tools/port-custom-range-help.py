#!/usr/bin/env python
"""Adds the custom span to the plan and the holding chapters of every help manual.

The two pages learned to take two typed dates instead of one of the list's counts,
and both chapters say what the list offers — so both were left listing 3/5/10 years
and "as far back as the data goes" and nothing else.

Idempotent: a chapter that already carries the line is left alone, so the script can
be run again after one of the fourteen files has been edited by hand.

Encoding: the manuals are UTF-8 with a BOM and LF endings. Read and written as bytes
so neither is quietly normalised — see the note in the project's memory.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
HELP = ROOT / "src" / "MarketMotionStudio" / "Assets" / "Help"

# The plan chapter and the holding chapter, by their position among the `## `
# headings. Every manual carries the same chapters in the same order — that is a
# rule the help loader relies on — so the position is the identifier that does not
# need translating.
PLAN = 8
HOLDING = 9

BULLETS = {
    "cs": (
        "Kromě 3, 5 a 10 let a nejdelšího období lze zvolit i **Vlastní**: zadejte "
        "počáteční a koncové datum a stiskněte načtení dat. Dostupných je asi 35 let "
        "zpět — zdroj vrací zhruba 640 kalendářních dnů na jeden požadavek a průchod "
        "jich provede nejvýše dvacet.",
        "Stejné **Vlastní** období platí i pro držbu: zadejte dvě data a stiskněte "
        "načtení dat. Pokud byl nástroj uveden na trh později, než je zadané datum, "
        "držba začíná jeho prvním obchodním dnem.",
    ),
    "de": (
        "Neben 3, 5 und 10 Jahren und dem längsten Zeitraum kann auch "
        "**Benutzerdefiniert** gewählt werden: Anfangs- und Enddatum eintragen und "
        "dann die Daten abrufen. Etwa 35 Jahre sind erreichbar — die Quelle liefert "
        "pro Anfrage rund 640 Kalendertage, und der Durchlauf macht höchstens zwanzig.",
        "Dieselbe Auswahl **Benutzerdefiniert** gilt für die Haltedauer: zwei Daten "
        "eintragen und die Daten abrufen. Wurde das Papier später gelistet als das "
        "Anfangsdatum, beginnt die Haltung an seinem ersten Handelstag.",
    ),
    "en-US": (
        "Besides three, five and ten years and the longest span, the range can be "
        "**Custom**: give a start and an end date, then press Fetch. About 35 years is "
        "reachable — the source serves roughly 640 calendar days per request, and the "
        "walk makes at most twenty of them.",
        "The same **Custom** span works for the holding: give two dates, then press "
        "Fetch. If the instrument listed later than the date you asked for, the "
        "holding starts on its first trading day.",
    ),
    "es": (
        "Además de 3, 5 y 10 años y del tramo más largo, el rango puede ser "
        "**Personalizado**: indica una fecha inicial y una final y pulsa el botón de "
        "obtener datos. Se puede retroceder unos 35 años: la fuente entrega unos 640 "
        "días naturales por petición y el recorrido hace veinte como máximo.",
        "El mismo rango **Personalizado** vale para la tenencia: indica dos fechas y "
        "pulsa obtener datos. Si el instrumento empezó a cotizar después de la fecha "
        "indicada, la tenencia comienza su primer día de negociación.",
    ),
    "fr": (
        "Outre 3, 5 et 10 ans et la période la plus longue, la plage peut être "
        "**Personnalisée** : indiquez une date de début et une date de fin, puis "
        "récupérez les données. Environ 35 ans sont accessibles — la source sert "
        "environ 640 jours civils par requête et le parcours en fait vingt au plus.",
        "La même plage **Personnalisée** s'applique à la détention : indiquez deux "
        "dates, puis récupérez les données. Si le titre a été coté après la date "
        "demandée, la détention commence à son premier jour de cotation.",
    ),
    "it": (
        "Oltre a 3, 5 e 10 anni e all'intervallo più lungo, il periodo può essere "
        "**Personalizzato**: indica una data di inizio e una di fine, poi premi il "
        "pulsante per recuperare i dati. Si può risalire di circa 35 anni: la fonte "
        "restituisce circa 640 giorni di calendario per richiesta e la scansione ne fa "
        "al massimo venti.",
        "Lo stesso periodo **Personalizzato** vale per la detenzione: indica due date, "
        "poi premi il pulsante per recuperare i dati. Se lo strumento è stato quotato "
        "dopo la data indicata, la detenzione inizia nel suo primo giorno di "
        "negoziazione.",
    ),
    "ja": (
        "期間は 3 年・5 年・10 年・最長のほか、**カスタム**も選べます：開始日と終了日を"
        "指定してからデータを取得してください。遡れるのは約 35 年までです——ソースは 1 回の"
        "リクエストで約 640 日分しか返さず、走査は最大 20 回までだからです。",
        "保有期間でも同じく**カスタム**が使えます：2 つの日付を指定してからデータを取得して"
        "ください。銘柄の上場が指定日より後なら、保有はその最初の営業日から始まります。",
    ),
    "ko": (
        "기간은 3·5·10년과 최장 구간 외에 **사용자 지정**도 가능합니다: 시작일과 종료일을 "
        "지정한 뒤 데이터를 가져오세요. 약 35년까지 거슬러 올라갈 수 있습니다——출처는 한 "
        "요청에 약 640일치만 주고, 순회는 최대 스무 번이기 때문입니다.",
        "보유 기간에도 같은 **사용자 지정**을 쓸 수 있습니다: 두 날짜를 지정한 뒤 데이터를 "
        "가져오세요. 종목의 상장일이 지정한 날짜보다 늦으면 보유는 첫 거래일부터 "
        "시작합니다.",
    ),
    "pl": (
        "Oprócz 3, 5 i 10 lat oraz najdłuższego zakresu można wybrać **Własny**: podaj "
        "datę początkową i końcową, a następnie pobierz dane. Dostępnych jest około 35 "
        "lat wstecz — źródło zwraca około 640 dni kalendarzowych na jedno żądanie, a "
        "przejście wykonuje ich najwyżej dwadzieścia.",
        "Ten sam zakres **Własny** działa dla pozycji: podaj dwie daty, a następnie "
        "pobierz dane. Jeśli instrument zadebiutował później niż podana data, pozycja "
        "zaczyna się w jego pierwszym dniu notowań.",
    ),
    "pt-BR": (
        "Além de 3, 5 e 10 anos e do período mais longo, o intervalo pode ser "
        "**Personalizado**: informe a data inicial e a final e pressione o botão de "
        "buscar dados. Dá para voltar cerca de 35 anos — a fonte entrega cerca de 640 "
        "dias corridos por requisição e a varredura faz no máximo vinte.",
        "O mesmo intervalo **Personalizado** vale para a posição: informe duas datas e "
        "pressione buscar dados. Se o ativo passou a ser negociado depois da data "
        "informada, a posição começa no seu primeiro dia de negociação.",
    ),
    "ru": (
        "Кроме 3, 5 и 10 лет и самого длинного периода диапазон может быть **Свой**: "
        "укажите дату начала и дату конца и нажмите получение данных. Доступно около 35 "
        "лет назад — источник отдаёт примерно 640 календарных дней за запрос, а обход "
        "делает не более двадцати.",
        "Тот же диапазон **Свой** работает и для позиции: укажите две даты и нажмите "
        "получение данных. Если инструмент появился на бирже позже указанной даты, "
        "позиция начинается с его первого торгового дня.",
    ),
    "tr": (
        "3, 5 ve 10 yıl ile en uzun aralığın dışında **Özel** de seçilebilir: başlangıç "
        "ve bitiş tarihini verip verileri alın. Yaklaşık 35 yıl geriye gidilebilir — "
        "kaynak istek başına yaklaşık 640 takvim günü veriyor ve tarama en çok yirmi "
        "istek yapıyor.",
        "Aynı **Özel** aralık elde tutma için de geçerlidir: iki tarih verip verileri "
        "alın. Araç belirttiğiniz tarihten sonra işlem görmeye başladıysa, elde tutma "
        "ilk işlem gününde başlar.",
    ),
    "zh-Hans": (
        "区间还能自己填：选「自定义」后给定起始与结束日期，再按获取数据。可回溯约 35 年——"
        "数据源一次只给约 640 个自然日，来回取二十次为止。",
        "持有区间同样可以自己填：选「自定义」后给定两个日期，再按获取数据。标的上市更晚时，"
        "实际起点是它上市那天。",
    ),
    "zh-Hant": (
        "區間還能自己填：選「自訂」後給定起始與結束日期，再按取得資料。可回溯約 35 年——"
        "資料源一次只給約 640 個自然日，來回取二十次為止。",
        "持有區間同樣可以自己填：選「自訂」後給定兩個日期，再按取得資料。標的上市更晚時，"
        "實際起點是它上市那天。",
    ),
}


def chapter_ends(lines):
    """The last line of each `## ` chapter, by the chapter's position."""
    heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
    ends = {}

    for at, head in enumerate(heads):
        stop = heads[at + 1] if at + 1 < len(heads) else len(lines)
        body = lines[head:stop]

        # The chapter's last bullet, not its last line: what follows it is the blank
        # line before the next heading. A chapter with no bullets at all — the ones
        # that are a single paragraph — ends at its last written line.
        bullets = [i for i, line in enumerate(body) if line.startswith("- ")]
        written = [i for i, line in enumerate(body) if line.strip()]

        ends[at] = (bullets[-1] if bullets else written[-1]) + head

    return ends


def main():
    for tag, bullets in sorted(BULLETS.items()):
        path = HELP / f"help-{tag}.md"
        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")
        lines = text.split("\n")
        ends = chapter_ends(lines)

        # Backwards, so inserting into the earlier chapter does not move the line the
        # later one was measured at.
        for at, bullet in ((HOLDING, bullets[1]), (PLAN, bullets[0])):
            if at not in ends:
                raise AssertionError(f"{tag}: no chapter at position {at}")

            line = "- " + bullet

            if line in lines:
                continue

            # Carried here without its bullet mark by an earlier run of this script:
            # repair it rather than adding a second copy beside it.
            bare = [i for i, existing in enumerate(lines) if existing == bullet]

            for i in bare:
                lines[i] = line

            if bare:
                continue

            lines.insert(ends[at] + 1, line)

        path.write_bytes(("\ufeff" + "\n".join(lines)).encode("utf-8"))

        print(f"{tag}: ok")


if __name__ == "__main__":
    main()
