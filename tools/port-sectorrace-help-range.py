#!/usr/bin/env python3
"""Brings the sector race's interval line in all fourteen help files in line with the page.

The page's span menu gained two years (`tools/port-range-24m.py`) because the endpoint's own answer
is two and a half: the sector race asks for one request per entrant, and that request carries 640
**bars**, not 640 days. The help said "1, 3, 6 or 12 months", which was true of the menu and is now
one entry short of it.

**One line, not two, and the difference matters.** The gain-loss calendar page carries a nearly
identical sentence — same numbers, same four languages' worth of wording — and that page's menu was
not touched: it asks one request per instrument over a span it wants every single day of, so its own
six-hundred-and-forty-day ceiling is the right one and it stays. Each replacement below is anchored
to the whole line, so the calendar's version cannot be caught by accident.

Idempotent: a file whose line already carries two years is left alone. No BOM (markdown here), LF
preserved.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
HELP = ROOT / "src" / "MarketMotionStudio" / "Assets" / "Help"

LINES = {
    "help-cs.md": (
        "- Období může být 1, 3, 6 nebo 12 měsíců, nebo vlastní počáteční a koncové datum.",
        "- Období může být 1, 3, 6, 12 nebo 24 měsíců, nebo vlastní počáteční a koncové datum. "
        "Vlastní rozsah sahá přibližně 900 dní — tolik zvládne jeden požadavek — a výběr dat tam končí.",
    ),
    "help-de.md": (
        "- Der Zeitraum kann 1, 3, 6 oder 12 Monate betragen oder frei mit Start- und Enddatum gewählt werden.",
        "- Der Zeitraum kann 1, 3, 6, 12 oder 24 Monate betragen oder frei mit Start- und Enddatum "
        "gewählt werden. Ein eigener Zeitraum reicht etwa 900 Tage weit — so viel wie eine Anfrage — "
        "und die Datumsauswahl endet dort.",
    ),
    "help-en-US.md": (
        "- The interval can be 1, 3, 6 or 12 months, or a custom start and end date.",
        "- The interval can be 1, 3, 6, 12 or 24 months, or a custom start and end date. A custom "
        "span reaches about 900 days — one request's worth — and the date pickers stop there.",
    ),
    "help-es.md": (
        "- El periodo puede ser de 1, 3, 6 o 12 meses, o fechas de inicio y fin personalizadas.",
        "- El periodo puede ser de 1, 3, 6, 12 o 24 meses, o fechas de inicio y fin personalizadas. "
        "Un intervalo personalizado llega a unos 900 días — lo que abarca una solicitud — y los "
        "selectores de fecha terminan ahí.",
    ),
    "help-fr.md": (
        "- La période peut être de 1, 3, 6 ou 12 mois, ou des dates de début et de fin personnalisées.",
        "- La période peut être de 1, 3, 6, 12 ou 24 mois, ou des dates de début et de fin "
        "personnalisées. Un intervalle personnalisé remonte à environ 900 jours — la portée d'une "
        "requête — et les sélecteurs de date s'arrêtent là.",
    ),
    "help-it.md": (
        "- Il periodo può essere di 1, 3, 6 o 12 mesi, oppure date di inizio e fine personalizzate.",
        "- Il periodo può essere di 1, 3, 6, 12 o 24 mesi, oppure date di inizio e fine "
        "personalizzate. Un intervallo personalizzato arriva a circa 900 giorni — quanto copre una "
        "richiesta — e i selettori di data si fermano lì.",
    ),
    "help-ja.md": (
        "- 期間は1、3、6、12ヶ月、または開始・終了日の指定が選べます。",
        "- 期間は1、3、6、12、24ヶ月、または開始・終了日の指定が選べます。指定した期間は約900日まで "
        "— 1回のリクエストで取れる範囲 — で、日付の選択はそこで止まります。",
    ),
    "help-ko.md": (
        "- 구간은 1, 3, 6, 12개월 또는 시작·종료일 지정이 가능합니다.",
        "- 구간은 1, 3, 6, 12, 24개월 또는 시작·종료일 지정이 가능합니다. 직접 지정한 기간은 약 "
        "900일까지 — 한 번의 요청이 닿는 범위 — 이며 날짜 선택기는 거기서 멈춥니다.",
    ),
    "help-pl.md": (
        "- Zakres to 1, 3, 6 lub 12 miesięcy albo dowolna data początkowa i końcowa.",
        "- Zakres to 1, 3, 6, 12 lub 24 miesiące albo dowolna data początkowa i końcowa. Własny "
        "zakres sięga około 900 dni — tyle, ile obejmuje jedno żądanie — i tam kończą się selektory dat.",
    ),
    "help-pt-BR.md": (
        "- O intervalo pode ser de 1, 3, 6 ou 12 meses, ou datas de início e fim personalizadas.",
        "- O intervalo pode ser de 1, 3, 6, 12 ou 24 meses, ou datas de início e fim personalizadas. "
        "Um intervalo personalizado alcança cerca de 900 dias — o alcance de uma solicitação — e os "
        "seletores de data param aí.",
    ),
    "help-ru.md": (
        "- Период — 1, 3, 6 или 12 месяцев либо произвольные даты начала и конца.",
        "- Период — 1, 3, 6, 12 или 24 месяца либо произвольные даты начала и конца. Свой интервал "
        "охватывает около 900 дней — столько берёт один запрос — и выбор дат на этом останавливается.",
    ),
    "help-tr.md": (
        "- Dönem 1, 3, 6 veya 12 ay ya da özel başlangıç ve bitiş tarihi olabilir.",
        "- Dönem 1, 3, 6, 12 veya 24 ay ya da özel başlangıç ve bitiş tarihi olabilir. Kendi "
        "aralığınız yaklaşık 900 güne ulaşır — bir isteğin kapsadığı kadar — ve tarih seçiciler orada durur.",
    ),
    "help-zh-Hans.md": (
        "- 区间可选 1、3、6、12 个月或自定义起止日。",
        "- 区间可选 1、3、6、12、24 个月或自定义起止日。自定义区间最长约 900 天 ——"
        "也就是一次请求能取的量 —— 日期选择器到此为止。",
    ),
    "help-zh-Hant.md": (
        "- 區間可選 1、3、6、12 個月或自訂起止日。",
        "- 區間可選 1、3、6、12、24 個月或自訂起止日。自訂區間最長約 900 天 ——"
        "也就是一次請求能取的量 —— 日期選擇器到此為止。",
    ),
}


def main():
    changed = []
    skipped = []
    problem = []

    for name, (old, new) in sorted(LINES.items()):
        path = HELP / name

        if not path.exists():
            problem.append(f"{name} (missing)")
            continue

        text = path.read_text(encoding="utf-8").lstrip("\ufeff")

        if new in text:
            skipped.append(name)
            continue

        if text.count(old) != 1:
            problem.append(f"{name} ({text.count(old)} matches)")
            continue

        text = text.replace(old, new)

        # Written as bytes with no BOM: help files are markdown, and one arriving with a byte-order
        # mark is a heading the reader renders as a stray character.
        path.write_bytes(text.encode("utf-8"))
        changed.append(name)

    print(f"changed : {len(changed)}  {' '.join(changed)}")
    print(f"skipped : {len(skipped)}  {' '.join(skipped) or '-'}")
    print(f"problem : {len(problem)}  {' '.join(problem) or '-'}")

    # The calendar page's own sentence must be untouched — that is the whole point of anchoring to
    # a whole line. It is the only other place offering these four numbers, so after this runs the
    # count of four-entry lines should be exactly one per file and none of them should be the race's.
    four = []

    for path in sorted(HELP.glob("help-*.md")):
        hits = [line for line in path.read_text(encoding="utf-8").splitlines()
                if line.startswith("- ") and ("1, 3, 6" in line or "1、3、6" in line)
                and "24" not in line]

        four.append(f"{path.name}:{len(hits)}")

    print(f"four-entry lines left (the calendar's, one per file): {' '.join(four)}")


if __name__ == "__main__":
    main()
