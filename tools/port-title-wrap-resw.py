# -*- coding: utf-8 -*-
r"""改写「标题文字」下面那句说明，14 语言。

**为什么非改不可**：那句现在写着「过长的标题会按比例缩小字号而不是被裁掉，最多缩到一半」。
折行上线之后，一行放不下的标题是**折成第二行**，只有在两行也放不下时才缩字号 ——
把缩字号说成第一手段，正好把新增的那条规则讲反了。用户按这句话去预期，会以为折行没生效。

**只换第二句**：第一句「留空则使用默认标题」仍然成立，别动 14 份里已经定稿的句子。
整值重写而不是替换某个句子：按语言查表比在译文里搜索更不会出错。

幂等。写回**照原样**（`had_bom` 记号 + 行尾检查）：resw 是 LF 且**必须带 BOM**。

用法：python tools\port-title-wrap-resw.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

NOTE = {
    "en-US": "Leave it empty to use the default. Press Enter to break it where you want; a title too wide for one line wraps onto a second — two lines at most — and only then does the size give way, to half size at most. A second line pushes everything below it down by one row.",

    "de": "Leer lassen, um den Standardtitel zu verwenden. Mit der Eingabetaste brechen Sie den Titel dort, wo er brechen soll; passt er nicht in eine Zeile, läuft er automatisch in eine zweite um — höchstens zwei Zeilen — und erst dann gibt die Schriftgröße nach, höchstens auf die halbe Größe. Eine zweite Zeile schiebt alles darunter um eine Zeile nach unten.",

    "es": "Déjelo vacío para usar el título predeterminado. Pulsa Intro para partirlo donde quieras; si no cabe en una línea se ajusta solo a una segunda —dos como máximo— y solo entonces cede el tamaño, hasta la mitad. Una segunda línea empuja hacia abajo una fila todo lo que hay debajo.",

    "fr": "Laissez vide pour utiliser le titre par défaut. Appuyez sur Entrée pour le couper où vous voulez ; s'il ne tient pas sur une ligne il se replie seul sur une deuxième — deux au maximum — et ce n'est qu'alors que la taille cède, jusqu'à la moitié. Une deuxième ligne décale d'une ligne tout ce qui suit.",

    "it": "Lascialo vuoto per usare il titolo predefinito. Premi Invio per spezzarlo dove vuoi; se non entra in una riga va a capo da solo su una seconda —due al massimo— e solo allora la dimensione cede, fino a metà. Una seconda riga sposta di una riga tutto ciò che sta sotto.",

    "pl": "Zostaw puste, aby użyć tytułu domyślnego. Naciśnij Enter, aby złamać tytuł tam, gdzie chcesz; gdy nie mieści się w jednej linii, sam przechodzi do drugiej — najwyżej dwóch — i dopiero wtedy maleje stopień pisma, najwyżej do połowy. Druga linia przesuwa wszystko poniżej o jeden wiersz.",

    "pt-BR": "Deixe vazio para usar o título padrão. Pressione Enter para quebrá-lo onde quiser; se não couber em uma linha ele quebra sozinho em uma segunda — no máximo duas — e só então o tamanho cede, até a metade. Uma segunda linha empurra uma linha para baixo tudo o que vem depois.",

    "cs": "Nechte prázdné, chcete-li použít výchozí titulek. Stisknutím Enteru titulek zlomíte tam, kde chcete; když se nevejde na jeden řádek, zalomí se sám na druhý — nejvýše dva — a teprve pak ustoupí velikost písma, nejvýše na polovinu. Druhý řádek posune vše pod ním o jeden řádek dolů.",

    "tr": "Varsayılan başlığı kullanmak için boş bırakın. Başlığı istediğiniz yerden kırmak için Enter'a basın; tek satıra sığmazsa kendiliğinden ikinci satıra kayar — en fazla iki satır — ve ancak o zaman yazı boyutu küçülür, en çok yarı boyuta kadar. İkinci satır altındaki her şeyi bir satır aşağı iter.",

    "ru": "Оставьте пустым, чтобы использовать заголовок по умолчанию. Нажмите Enter, чтобы разорвать заголовок там, где нужно; если он не помещается в одну строку, он сам переносится на вторую — не более двух — и только тогда уступает размер шрифта, не более чем вдвое. Вторая строка сдвигает всё под ней на одну строку вниз.",

    "ja": "空のままにすると既定のタイトルを使います。Enter で好きな位置で改行できます。1 行に収まらないときは自動で 2 行目に折り返し（最大 2 行）、それでも収まらないときだけ文字サイズが縮小します（最小で半分まで）。2 行目が出ると、その下の内容が 1 行分下がります。",

    "ko": "비워 두면 기본 제목을 씁니다. Enter로 원하는 곳에서 줄을 바꿀 수 있습니다. 한 줄에 들어가지 않으면 자동으로 두 번째 줄로 접히며(최대 두 줄), 두 줄로도 부족할 때만 글자 크기가 줄어듭니다(최소 절반까지). 두 번째 줄이 생기면 아래 내용이 한 줄만큼 내려갑니다.",

    "zh-Hans": "留空则使用默认标题。标题里可以按回车手动换行；一行放不下会按宽度自动折成第二行（最多两行），两行仍放不下才按比例缩小字号（最多缩到一半）。折出第二行时下面的内容整体下移一行。",

    "zh-Hant": "留空則使用預設標題。標題裡可以按 Enter 手動斷行；一行放不下會按寬度自動折成第二行（最多兩行），兩行還放不下才按比例縮小字級（最多縮到一半）。折出第二行時下面的內容整體下移一行。",
}

PATTERN = re.compile(r'(<data name="StudioTitleNote\.Text"><value>)(.*?)(</value>)', re.S)


def main() -> int:
    written = 0
    unchanged = 0

    for tag, note in NOTE.items():
        path = ROOT / tag / "Resources.resw"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")

        text = raw.decode("utf-8-sig").lstrip("\ufeff")

        if not PATTERN.search(text):
            print(f"{tag}: StudioTitleNote.Text is not in this file")
            return 1

        replaced, count = PATTERN.subn(lambda m: m.group(1) + note + m.group(3), text, count=1)

        if count != 1:
            print(f"{tag}: {count} replacements, expected one")
            return 1

        if replaced == text:
            unchanged += 1
            print(f"{tag:9} unchanged")
            continue

        if "\r\n" in replaced:
            print(f"{tag}: the file came back with CRLF endings")
            return 1

        if not had_bom:
            print(f"{tag}: the file has lost its BOM")
            return 1

        path.write_bytes(b"\xef\xbb\xbf" + replaced.encode("utf-8"))

        written += 1
        print(f"{tag:9} written")

    print(f"\n14 languages, {written} written, {unchanged} unchanged")

    return 0


if __name__ == "__main__":
    sys.exit(main())
