"""Adds the frame colour's opacity, in all fourteen languages.

Two new keys under the animation backdrop card: the label for the opacity slider
and the note under it. 100 percent is the two colours as chosen, which is what the
colour choice meant before this slider existed, so the note explains the direction
rather than the scale: lower lets the frame's own dark gradient through, and the
reason to want that is that every number in a frame is drawn in a light tone.

Inserted after SettingsFrameBackdropColourNote.Text so all fourteen files keep the
same key order — a key in a different place in one file is a difference a diff has
to explain every time, for no gain.

Idempotent: a key that is already there has its value rewritten instead of being
added again. Files are written back as UTF-8 with a BOM and LF endings.

Run:  <venv python> tools/port-frame-strength-resw.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

LABEL = {
    "en-US": "Opacity",
    "de": "Deckkraft",
    "es": "Opacidad",
    "fr": "Opacité",
    "it": "Opacità",
    "pl": "Krycie",
    "pt-BR": "Opacidade",
    "cs": "Krytí",
    "tr": "Opaklık",
    "ru": "Непрозрачность",
    "ja": "不透明度",
    "ko": "불투명도",
    "zh-Hans": "不透明度",
    "zh-Hant": "不透明度",
}

NOTE = {
    "en-US": "At 100% the frame is the two colours as chosen. Lower lets the frame's own dark gradient through, which is how a light pair stays readable: every number in a frame is drawn in a light tone.",
    "de": "Bei 100 % ist das Bild die zwei gewählten Farben. Niedriger lässt den eigenen dunklen Verlauf des Bildes durchscheinen — so bleibt eine helle Wahl lesbar, denn jede Zahl darin ist in einem hellen Ton gezeichnet.",
    "es": "Al 100 % el fotograma son los dos colores elegidos. Por debajo deja pasar el degradado oscuro propio del fotograma: así una elección clara sigue siendo legible, porque todas las cifras se dibujan en tonos claros.",
    "fr": "À 100 %, l'image est les deux couleurs choisies. En dessous, son propre dégradé sombre transparaît : ainsi un choix clair reste lisible, car tous les chiffres y sont dessinés dans des teintes claires.",
    "it": "Al 100% il fotogramma sono i due colori scelti. Più in basso lascia passare il gradiente scuro del fotogramma stesso: è così che una scelta chiara resta leggibile, perché ogni numero è disegnato in una tinta chiara.",
    "pl": "Przy 100% klatka to po prostu dwa wybrane kolory. Niżej przeziera własny ciemny gradient klatki — w ten sposób jasny wybór pozostaje czytelny, bo każda liczba jest rysowana jasnym tonem.",
    "pt-BR": "Em 100% o quadro são as duas cores escolhidas. Abaixo disso o degradê escuro do próprio quadro aparece por baixo: é assim que uma escolha clara continua legível, pois todos os números são desenhados em tons claros.",
    "cs": "Při 100 % je snímek prostě dvojicí zvolených barev. Níže prosvítá vlastní tmavý přechod snímku — tím zůstane i světlá volba čitelná, protože každé číslo je kresleno světlým tónem.",
    "tr": "%100'de kare seçilen iki rengin kendisidir. Daha düşüğü karenin kendi koyu gradyanını alttan gösterir: açık bir seçim böylece okunur kalır, çünkü her sayı açık bir tonla çizilir.",
    "ru": "При 100 % кадр — это два выбранных цвета. Ниже сквозь него проступает собственный тёмный градиент кадра: так светлый выбор остаётся читаемым, ведь каждое число нарисовано светлым тоном.",
    "ja": "100% なら選んだ二色そのものです。下げるとフレーム本来の暗いグラデーションが下から透けます。数字はどれも明るい色で描かれるため、明るい配色を選んでも読みやすさを保てます。",
    "ko": "100%면 선택한 두 색 그대로입니다. 낮추면 프레임 고유의 어두운 그라데이션이 아래에서 비칩니다. 숫자는 모두 밝은 색으로 그려지므로 밝은 조합을 골라도 읽을 수 있습니다.",
    "zh-Hans": "100% 就是所选的两个颜色本身。调低会让画面自己的深色底从下面透上来——帧内数字都按浅色绘制，所以选了偏亮的配色时这样仍能看清。",
    "zh-Hant": "100% 就是所選的兩個顏色本身。調低會讓畫面自己的深色底從下面透上來——畫面裡的數字都按淺色繪製，所以選了偏亮的配色時這樣仍能看清。",
}

ANCHOR = "SettingsFrameBackdropColourNote.Text"

TEMPLATE = '  <data name="{key}" xml:space="preserve"><value>{value}</value></data>'


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def upsert(text: str, key: str, value: str) -> tuple[str, str]:
    """The file with the key set to the value. Returns the text and what was done."""
    line = TEMPLATE.format(key=key, value=escape(value))
    existing = re.compile(
        r'  <data name="' + re.escape(key) + r'" xml:space="preserve"><value>.*?</value></data>')

    if existing.search(text):
        return existing.sub(lambda _: line, text, count=1), "rewritten"

    anchor = re.compile(
        r'(  <data name="' + re.escape(ANCHOR) + r'" xml:space="preserve"><value>.*?</value></data>\n)')

    if not anchor.search(text):
        return text, "no anchor"

    return anchor.sub(lambda m: m.group(1) + line + "\n", text, count=1), "inserted"


def main() -> int:
    touched = 0
    unchanged = 0

    for tag in sorted(LABEL):
        path = ROOT / tag / "Resources.resw"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")

        for key, table in (("SettingsFrameStrengthLabel.Text", LABEL),
                           ("SettingsFrameStrengthNote.Text", NOTE)):
            text, what = upsert(text, key, table[tag])

            if what == "no anchor":
                print(f"{tag}: {ANCHOR} is not in this file")
                return 1

        if text == path.read_bytes().decode("utf-8-sig").lstrip("\ufeff"):
            unchanged += 1
            print(f"{tag:9} unchanged")
            continue

        if "\r\n" in text:
            print(f"{tag}: the file came back with CRLF endings")
            return 1

        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

        touched += 1
        print(f"{tag:9} written")

    print(f"\n14 languages, {touched} written, {unchanged} unchanged")

    return 0


if __name__ == "__main__":
    sys.exit(main())
