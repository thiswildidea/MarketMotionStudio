"""Rewrites the margin note, in all fourteen languages.

The top margin used to be clamped at the phone's safe area, and the note said so:
"the title can never slide under it". That is no longer true — the margin may now be
drawn in above the band, which is the point of lowering its floor — so the sentence
is replaced rather than left standing as a claim the renderer no longer honours.

Only the last sentence changes; the first two say things that are still the case.
Rewriting the whole value rather than patching a sentence keeps this a lookup by
language rather than a search for translated words.

Idempotent. Files are written back as UTF-8 with a BOM and LF endings, which is what
they are now; key order is untouched because nothing is added or removed.

Run:  <venv python> tools/port-margin-note-resw.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "src" / "MarketMotionStudio" / "Strings"

NOTE = {
    "en-US": "Measured against 1080×1920 and scaled to the chosen resolution, so a value tuned here holds at every size. The left margin also decides where the axis labels land. The top margin opens at 230, the band a phone keeps for its own interface; set it lower and the title moves into the strip a status bar covers.",
    "de": "Gemessen gegen 1080×1920 und auf die gewählte Auflösung skaliert; ein hier abgestimmter Wert gilt daher in jeder Größe. Der linke Rand bestimmt außerdem, wo die Achsenbeschriftungen landen. Der obere Rand beginnt bei 230 — dem Bereich, den sich das Telefon für seine eigene Oberfläche reserviert; darunter rutscht der Titel in den Streifen, den die Statusleiste überdeckt.",
    "es": "Medidos sobre 1080×1920 y escalados a la resolución elegida, así que un valor ajustado aquí sirve en todos los tamaños. El margen izquierdo decide además dónde caen las etiquetas del eje. El margen superior parte de 230, la banda que el teléfono reserva para su propia interfaz; por debajo, el título entra en la franja que cubre la barra de estado.",
    "fr": "Exprimées par rapport à 1080×1920 puis mises à l'échelle de la résolution choisie ; une valeur réglée ici reste valable à toutes les tailles. La marge gauche détermine aussi où se posent les graduations de l'axe. La marge haute part de 230, la bande que le téléphone réserve à sa propre interface ; en dessous, le titre entre dans la zone couverte par la barre d'état.",
    "it": "Misurati su 1080×1920 e riscalati sulla risoluzione scelta, così un valore messo a punto qui vale a ogni dimensione. Il margine sinistro decide anche dove finiscono le etichette dell'asse. Il margine superiore parte da 230, la fascia che il telefono riserva alla propria interfaccia; sotto quel valore il titolo entra nella striscia coperta dalla barra di stato.",
    "pl": "Mierzone względem 1080×1920 i skalowane do wybranej rozdzielczości, więc wartość dobrana tutaj obowiązuje w każdym rozmiarze. Lewy margines decyduje też, gdzie trafiają opisy osi. Górny margines startuje od 230 — tyle telefon rezerwuje na własny interfejs; poniżej tytuł wchodzi w pas zasłaniany przez pasek stanu.",
    "pt-BR": "Medidas contra 1080×1920 e escalonadas para a resolução escolhida, então um valor ajustado aqui vale em qualquer tamanho. A margem esquerda também decide onde caem os rótulos do eixo. A margem superior começa em 230, a faixa que o celular reserva para a própria interface; abaixo disso o título entra na faixa coberta pela barra de status.",
    "cs": "Měřeno proti 1080×1920 a přepočítáno na zvolené rozlišení, takže hodnota vyladěná tady platí v každé velikosti. Levý okraj také rozhoduje, kam dopadnou popisky osy. Horní okraj začíná na 230 — tolik si telefon rezervuje pro vlastní rozhraní; pod touto hodnotou se titulek posune do pásu, který překrývá stavový řádek.",
    "tr": "1080×1920 tabanına göre ölçülür ve seçilen çözünürlüğe oranlanır; burada ayarlanan bir değer her boyutta geçerlidir. Sol kenar boşluğu ayrıca eksen etiketlerinin nereye düşeceğini belirler. Üst kenar boşluğu 230'dan başlar; telefonun kendi arayüzü için ayırdığı bant budur. Altına inildiğinde başlık durum çubuğunun kapattığı şeride girer.",
    "ru": "Отмеряются от 1080×1920 и масштабируются под выбранное разрешение, поэтому подобранное здесь значение верно при любом размере. Левое поле также определяет, где встанут подписи оси. Верхнее поле начинается с 230 — полосы, которую телефон оставляет под собственный интерфейс; ниже заголовок уходит в зону, перекрытую строкой состояния.",
    "ja": "1080×1920 を基準とした値で、描画時に選んだ解像度へ比例拡大されます。ここで調整した値は解像度を変えてもそのまま使えます。左マージンは Y 軸目盛りの位置も決めます。 上マージンは既定値 230 がスマホが自前のUIのために確保する帯で、これより小さくするとタイトルがステータスバーの重なる帯に入ります。",
    "ko": "1080×1920 기준으로 적은 값이며 선택한 해상도에 비례해 확대됩니다. 여기서 맞춘 값은 해상도를 바꿔도 그대로 쓸 수 있습니다. 왼쪽 여백은 Y축 눈금의 위치도 결정합니다. 위쪽 여백의 기본값 230은 휴대폰이 자체 UI를 위해 확보한 영역이며, 더 줄이면 제목이 상태 표시줄이 덮는 띠로 들어갑니다.",
    "zh-Hans": "以 1080×1920 为基准记数，渲染时按所选分辨率等比缩放，所以在这里调好的值换分辨率不用重调。左边距同时决定 Y 轴刻度的落点。 上边距默认 230，正是手机留给系统界面的那条安全区；调得更小，标题就会进入状态栏覆盖的那一条带。",
    "zh-Hant": "以 1080×1920 為基準計數，算繪時按所選解析度等比縮放，所以在這裡調好的值換解析度不必重調。左邊界同時決定 Y 軸刻度的落點。 上邊界預設 230，正是手機保留給系統介面的那條安全區；調得更小，標題就會進入狀態列覆蓋的那一條帶。",
}

PATTERN = re.compile(r'(<data name="StudioMarginNote\.Text"><value>)(.*?)(</value>)', re.S)


def main() -> int:
    written = 0
    unchanged = 0

    for tag, note in NOTE.items():
        path = ROOT / tag / "Resources.resw"

        if not path.exists():
            print(f"missing: {path}")
            return 1

        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")

        if not PATTERN.search(text):
            print(f"{tag}: StudioMarginNote.Text is not in this file")
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

        path.write_bytes(b"\xef\xbb\xbf" + replaced.encode("utf-8"))

        written += 1
        print(f"{tag:9} written")

    print(f"\n14 languages, {written} written, {unchanged} unchanged")

    return 0


if __name__ == "__main__":
    sys.exit(main())
