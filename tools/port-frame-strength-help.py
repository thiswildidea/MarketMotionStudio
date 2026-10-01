# -*- coding: utf-8 -*-
"""给 14 份帮助手册的「动画背景」一节加一条关于不透明度的要点。

**按章节标题定位，不按行号**：14 种语言的标题不同，行号也不同；锚在每份自己的
标题之后、该节第一条要点（颜色那条）之后插入。幂等可重跑：已经存在就不动。
读 utf-8-sig、按原样写回（保 BOM 保行尾）。
"""

import pathlib
import sys

ROOT = pathlib.Path(r"D:/software/MarketMotionStudio/src/MarketMotionStudio/Assets/Help")

# 章节标题照 port-framebackdrop-help.py 里的那份，别另起一套。
TITLES = {
    "cs": "Pozadí animace",
    "de": "Animationshintergrund",
    "en-US": "Animation background",
    "es": "Fondo de la animación",
    "fr": "Fond de l'animation",
    "it": "Sfondo dell'animazione",
    "ja": "アニメーションの背景",
    "ko": "애니메이션 배경",
    "pl": "Tło animacji",
    "pt-BR": "Fundo da animação",
    "ru": "Фон анимации",
    "tr": "Animasyon arka planı",
    "zh-Hans": "动画背景",
    "zh-Hant": "動畫背景",
}

BULLET = {
    "en-US": "The opacity slider sets how much of the two colours is used: at 100% the frame is "
             "the pair as chosen, and lower lets the page's own dark gradient through from "
             "underneath. It is what keeps a light pair readable.",
    "de": "Der Regler für die Deckkraft bestimmt, wie viel von den zwei Farben verwendet wird: "
          "Bei 100 % ist das Bild die gewählte Paarung, darunter scheint der eigene dunkle "
          "Verlauf der Seite von unten durch. So bleibt eine helle Paarung lesbar.",
    "es": "El control de opacidad decide cuánto se usan los dos colores: al 100 % el fotograma es "
          "la pareja elegida y por debajo deja ver el degradado oscuro propio de la página. Es lo "
          "que mantiene legible una combinación clara.",
    "fr": "Le curseur d'opacité règle la part des deux couleurs : à 100 %, l'image est la paire "
          "choisie, et en dessous le dégradé sombre de la page apparaît par-dessous. C'est ce qui "
          "garde une paire claire lisible.",
    "it": "La barra dell'opacità decide quanto si usano i due colori: al 100% il fotogramma è la "
          "coppia scelta, più in basso lascia intravedere il gradiente scuro della pagina. È "
          "questo che tiene leggibile una coppia chiara.",
    "pl": "Suwak krycia określa, ile z dwóch kolorów zostanie użyte: przy 100% klatka to po prostu "
          "wybrana para, a niżej spod spodu prześwituje własny ciemny gradient strony. To właśnie "
          "utrzymuje czytelność jasnej pary.",
    "pt-BR": "O controle de opacidade define quanto das duas cores é usado: em 100% o quadro é o "
             "par escolhido e abaixo disso o degradê escuro da própria página aparece por baixo. "
             "É isso que mantém um par claro legível.",
    "cs": "Posuvník krytí určuje, kolik z obou barev se použije: při 100 % je snímek vybranou "
          "dvojicí a níže zespodu prosvítá vlastní tmavý přechod stránky. Právě to udrží světlou "
          "dvojici čitelnou.",
    "tr": "Opaklık kaydırıcısı iki rengin ne kadarının kullanılacağını belirler: %100'de kare "
          "seçilen ikilinin kendisidir, altında sayfanın kendi koyu gradyanı alttan görünür. Açık "
          "bir ikiliyi okunur tutan şey budur.",
    "ru": "Ползунок непрозрачности задаёт, сколько берётся от двух цветов: при 100 % кадр — это "
          "выбранная пара, а ниже сквозь неё проступает собственный тёмный градиент страницы. "
          "Именно это сохраняет читаемость светлой пары.",
    "ja": "不透明度のスライダーは二色をどれだけ使うかを決めます。100% なら選んだ二色そのもの、"
          "下げるとページ本来の暗いグラデーションが下から透けます。明るい組み合わせを読みやすく"
          "保つのはこの設定です。",
    "ko": "불투명도 슬라이더는 두 색을 얼마나 쓸지 정합니다. 100%면 고른 두 색 그대로이고, "
          "낮추면 페이지 고유의 어두운 그라데이션이 아래에서 비칩니다. 밝은 조합을 읽을 수 있게 "
          "지켜 주는 것이 바로 이것입니다.",
    "zh-Hans": "不透明度滑条决定这两个颜色用多少：100% 就是所选的颜色本身，调低会让这一页原本的深色底从下面透上来。选了偏亮的颜色时，靠它保住数字的可读性。",
    "zh-Hant": "不透明度滑桿決定這兩個顏色用多少：100% 就是所選的顏色本身，調低會讓這一頁原本的深色底從下面透上來。選了偏亮的顏色時，靠它保住數字的可讀性。",
}


def insert(text: str, title: str, bullet: str) -> tuple[str, str]:
    heading = text.find(f"## {title}")

    if heading < 0:
        return text, "no heading"

    # 该节第一条要点：颜色那条。插在它后面，让不透明度紧跟着它所调节的东西。
    first = text.find("\n- ", heading)

    if first < 0:
        return text, "no bullet"

    end = text.find("\n", first + 1)
    end = len(text) if end < 0 else end

    if bullet in text:
        return text, "already there"

    return text[:end] + f"\n\n- {bullet}" + text[end:], "inserted"


def main() -> int:
    written = 0
    unchanged = 0

    for tag, title in sorted(TITLES.items()):
        path = ROOT / f"help-{tag}.md"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        original = path.read_bytes()
        text = original.decode("utf-8-sig").lstrip("\ufeff")

        text, what = insert(text, title, BULLET[tag])

        if what in ("no heading", "no bullet"):
            print(f"{tag}: {what}")
            return 1

        if what == "already there":
            unchanged += 1
            print(f"{tag:9} already there")
            continue

        path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
        written += 1
        print(f"{tag:9} written")

    print(f"\n14 languages, {written} written, {unchanged} unchanged")

    return 0


if __name__ == "__main__":
    sys.exit(main())
