# -*- coding: utf-8 -*-
"""Put a picture at the head of each manual chapter that has one.

Placed by chapter number, not by heading text: the headings are translated and
matching on them would need one table of fourteen titles. The chapters are in
the same order in every language — that is the rule the manuals are held to —
so the fifth chapter is the same page in all of them.

Idempotent: a document that already carries the picture is left alone, so this
can be run again after adding a language.

One caption per language rather than one per chapter. The heading two lines
above already names the page; what the caption adds is what the reader is
looking at, and that is the same sentence five times over.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELP = os.path.join(ROOT, "src", "MarketMotionStudio", "Assets", "Help")

LANGS = [
    "zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de",
    "es", "fr", "it", "pl", "pt-BR", "cs", "ru", "tr",
]

# Chapter number (1-based, counting `##` headings) -> picture file.
CHAPTERS = {
    4: "sector-race.png",
    5: "monthly-matrix.png",
    6: "gain-calendar.png",
    7: "dca-plan.png",
    8: "position.png",
}

CAPTIONS = {
    "zh-Hans": "这一页的全貌：左侧预览、下方播放进度条、右侧参数面板。",
    "zh-Hant": "這一頁的全貌：左側預覽、下方播放進度條、右側參數面板。",
    "en-US": "The page in full: preview on the left, scrubber below, settings on the right.",
    "ja": "このページの全景：左がプレビュー、下が再生スライダー、右が設定パネルです。",
    "ko": "이 페이지의 전체 모습: 왼쪽 미리보기, 아래 재생 슬라이더, 오른쪽 설정 패널.",
    "de": "Die Seite im Ganzen: Vorschau links, Zeitleiste darunter, Einstellungen rechts.",
    "es": "La página completa: vista previa a la izquierda, barra de reproducción abajo, ajustes a la derecha.",
    "fr": "La page en entier : aperçu à gauche, barre de lecture en bas, réglages à droite.",
    "it": "La pagina per intero: anteprima a sinistra, barra di riproduzione sotto, impostazioni a destra.",
    "pl": "Strona w całości: podgląd po lewej, pasek odtwarzania poniżej, ustawienia po prawej.",
    "pt-BR": "A página inteira: pré-visualização à esquerda, barra de reprodução abaixo, ajustes à direita.",
    "cs": "Stránka jako celek: náhled vlevo, přehrávací lišta dole, nastavení vpravo.",
    "ru": "Страница целиком: предпросмотр слева, полоса воспроизведения снизу, настройки справа.",
    "tr": "Sayfanın tamamı: solda önizleme, altta oynatma çubuğu, sağda ayarlar.",
}


def add_pictures(text, lang):
    lines = text.split("\n")
    caption = CAPTIONS[lang]

    out = []
    chapter = 0
    added = 0

    for line in lines:
        out.append(line)

        if line.startswith("## "):
            chapter += 1
            picture = CHAPTERS.get(chapter)

            if picture is None:
                continue

            reference = f"![{caption}](media/{picture})"

            # Already there from an earlier run.
            if reference in text:
                continue

            out.extend(["", reference])
            added += 1

    return "\n".join(out), added


def main():
    failures = []

    for lang in LANGS:
        path = os.path.join(HELP, f"help-{lang}.md")

        if not os.path.exists(path):
            failures.append(f"{lang}: no document")
            continue

        with open(path, "rb") as handle:
            raw = handle.read()

        text = raw.decode("utf-8-sig")
        updated, added = add_pictures(text, lang)

        chapters = sum(1 for line in updated.split("\n") if line.startswith("## "))
        pictures = updated.count("](media/")

        if pictures != len(CHAPTERS):
            failures.append(f"{lang}: {pictures} pictures, expected {len(CHAPTERS)}")

        if added:
            # Written back as bytes: read_text/write_text would normalise the line
            # endings and turn every one of these files into a whole-file diff.
            with open(path, "wb") as handle:
                handle.write(updated.encode("utf-8-sig"))

        print(f"  {lang}: +{added} pictures, {pictures} total, {chapters} chapters")

    if failures:
        print("\n".join("  ! " + item for item in failures))
        return 1

    print("all fourteen documents carry the same five pictures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
