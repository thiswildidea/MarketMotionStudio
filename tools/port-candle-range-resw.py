"""Adds the candle page's "that range is too long" line to all fourteen languages.

The page grew a custom span, and a custom span is the one the source cannot be trusted
with: past what a single walk holds it answers with the newest candles alone, so the
chart begins years after the start date and looks like a chart that does not. The line
names the period and the ceiling, both of which come in as arguments — `{0}` is 日K or
周K or 月K, `{1}` is the number of candles.

Inserted after `CandleFetched`, at the end of the candle block, so the file stays in the
order it was already in. Idempotent; files keep their BOM and their LF endings.

Run:  <venv python> tools/port-candle-range-resw.py
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

KEY = "CandleRangeTooLong"

TEXT = {
    "en-US": "That range is too long — {0} reaches about {1} candles at most. Move the start date later.",
    "de": "Der Zeitraum ist zu lang — {0} erreicht höchstens etwa {1} Kerzen. Verschieben Sie das Startdatum nach hinten.",
    "es": "El intervalo es demasiado largo: {0} alcanza unas {1} velas como máximo. Adelanta la fecha de inicio.",
    "fr": "La période est trop longue : {0} atteint environ {1} bougies au maximum. Avancez la date de début.",
    "it": "L'intervallo è troppo lungo: {0} arriva a circa {1} candele al massimo. Sposta avanti la data di inizio.",
    "pl": "Zakres jest zbyt długi — {0} sięga najwyżej około {1} świec. Przesuń datę początkową do przodu.",
    "pt-BR": "O intervalo é longo demais — {0} alcança cerca de {1} candles no máximo. Adiante a data de início.",
    "cs": "Rozsah je příliš dlouhý — {0} pojme nejvýše přibližně {1} svíček. Posuňte datum začátku dopředu.",
    "tr": "Aralık çok uzun — {0} en fazla yaklaşık {1} mum alır. Başlangıç tarihini ileri alın.",
    "ru": "Слишком длинный период — {0} вмещает не более {1} свечей. Сдвиньте дату начала вперёд.",
    "ja": "期間が長すぎます。{0}で取得できるのは最大およそ {1} 本です。開始日を後ろにずらしてください。",
    "ko": "기간이 너무 깁니다. {0}은(는) 최대 약 {1}개까지 가져올 수 있습니다. 시작 날짜를 뒤로 미루세요.",
    "zh-Hans": "区间过长：{0}最多能取约 {1} 根，请把起始日期往后调。",
    "zh-Hant": "區間過長：{0}最多能取約 {1} 根，請把起始日期往後調。",
}

ANCHOR = '<data name="CandleFetched">'


def main() -> int:
    written = 0
    skipped = 0

    for tag, text in TEXT.items():
        path = ROOT / tag / "Resources.resw"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        body = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")

        if f'<data name="{KEY}">' in body:
            skipped += 1
            print(f"{tag:9} already there")
            continue

        at = body.find(ANCHOR)

        if at < 0:
            print(f"{tag}: no {ANCHOR} to anchor to")
            return 1

        end = body.index("\n", at) + 1
        line = f'  <data name="{KEY}"><value>{text}</value></data>\n'

        replaced = body[:end] + line + body[end:]

        path.write_bytes(b"\xef\xbb\xbf" + replaced.encode("utf-8"))

        written += 1
        print(f"{tag:9} written")

    print(f"\n14 languages, {written} written, {skipped} already in place")

    return 0


if __name__ == "__main__":
    sys.exit(main())
