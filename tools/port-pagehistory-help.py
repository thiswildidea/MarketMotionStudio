#!/usr/bin/env python
"""Add a "moving between pages" chapter to all fourteen help documents.

The chapter is new to this app: AgolAdminKit has the same two buttons but no
chapter about them, so the words are written here rather than copied. It sits
second, straight after choosing a market, because it is about getting around
rather than about any one page.

Lines are one per paragraph or bullet, the way the rest of the manual is written:
a paragraph is a single long line and line breaks are left to the renderer.

Idempotent: any previous copy of the chapter is removed first, matched by that
language's own heading. The byte order mark is preserved, and every language must
end up with the same number of chapters in the same position.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HELP = ROOT / "src" / "MarketMotionStudio" / "Assets" / "Help"

# Written fresh: AgolAdminKit ships the buttons without a chapter of its own.
CHAPTER = {
    "en-US": (
        "Moving between pages",
        [
            "The two buttons at the left of the title bar step back and forward through the pages you have visited, as a browser does — **Alt+Left** and **Alt+Right**, or the side buttons on a mouse.",
            "- A page is kept as you left it, so going back to one returns to the period and the preview as they stood, not to a page opened afresh.",
            "- Picking a new page clears what lay ahead, as a browser does.",
            "- They work with the navigation pane collapsed as well, which is when the preview needs the width most.",
        ],
    ),
    "de": (
        "Zwischen Seiten wechseln",
        [
            "Die beiden Schaltflächen links in der Titelleiste gehen durch die besuchten Seiten zurück und vor, wie ein Browser es tut — **Alt+Pfeil links** und **Alt+Pfeil rechts** oder die Seitentasten der Maus.",
            "- Eine Seite bleibt, wie du sie verlassen hast: Zurückgehen führt zur gewählten Spanne und zur Vorschau in genau dem Zustand, nicht zu einer neu geöffneten Seite.",
            "- Wie im Browser löscht das Anwählen einer neuen Seite, was vor dir lag.",
            "- Sie funktionieren auch bei eingeklapptem Navigationsbereich, und genau dann braucht die Vorschau die Breite am meisten.",
        ],
    ),
    "es": (
        "Moverse entre páginas",
        [
            "Los dos botones de la izquierda de la barra de título retroceden y avanzan por las páginas visitadas, como lo hace un navegador: **Alt+Flecha izquierda** y **Alt+Flecha derecha**, o los botones laterales del ratón.",
            "- Cada página se conserva tal como la dejaste, así que volver a ella devuelve el periodo y la vista previa en el estado en que estaban, no una página recién abierta.",
            "- Como en un navegador, elegir una página nueva borra lo que había por delante.",
            "- También funcionan con el panel de navegación plegado, justo cuando la vista previa más necesita el ancho.",
        ],
    ),
    "fr": (
        "Passer d'une page à l'autre",
        [
            "Les deux boutons à gauche de la barre de titre reculent et avancent parmi les pages visitées, comme le fait un navigateur : **Alt+Gauche** et **Alt+Droite**, ou les boutons latéraux de la souris.",
            "- Une page est conservée telle que vous l'avez laissée : y revenir ramène la période et l'aperçu dans l'état où ils étaient, et non une page ouverte à neuf.",
            "- Comme dans un navigateur, choisir une nouvelle page efface ce qui était devant.",
            "- Elles fonctionnent aussi lorsque le volet de navigation est replié, c'est-à-dire au moment où l'aperçu a le plus besoin de largeur.",
        ],
    ),
    "it": (
        "Spostarsi tra le pagine",
        [
            "I due pulsanti a sinistra della barra del titolo vanno indietro e avanti tra le pagine visitate, come fa un browser: **Alt+Freccia sinistra** e **Alt+Freccia destra**, oppure i pulsanti laterali del mouse.",
            "- Una pagina resta come l'hai lasciata, quindi tornarci riporta il periodo e l'anteprima nello stato in cui si trovavano, non una pagina appena aperta.",
            "- Come in un browser, scegliere una nuova pagina cancella ciò che stava davanti.",
            "- Funzionano anche con il riquadro di navigazione compresso, proprio quando l'anteprima ha più bisogno di larghezza.",
        ],
    ),
    "pl": (
        "Przechodzenie między stronami",
        [
            "Dwa przyciski po lewej stronie paska tytułu cofają się i przesuwają do przodu po odwiedzonych stronach, tak jak robi to przeglądarka — **Alt+Strzałka w lewo** i **Alt+Strzałka w prawo** albo boczne przyciski myszy.",
            "- Strona pozostaje taka, jak ją zostawiono, więc powrót do niej przywraca wybrany okres i podgląd w takim stanie, w jakim były, a nie świeżo otwartą stronę.",
            "- Jak w przeglądarce: wybranie nowej strony czyści to, co było przed Tobą.",
            "- Działają także przy zwiniętym panelu nawigacji, czyli wtedy, gdy podgląd najbardziej potrzebuje szerokości.",
        ],
    ),
    "pt-BR": (
        "Navegando entre as páginas",
        [
            "Os dois botões à esquerda da barra de título voltam e avançam pelas páginas visitadas, como faz um navegador: **Alt+Seta para a esquerda** e **Alt+Seta para a direita**, ou os botões laterais do mouse.",
            "- A página é mantida como você a deixou, portanto voltar a ela traz de volta o período e a prévia no estado em que estavam, e não uma página recém-aberta.",
            "- Como em um navegador, escolher uma nova página limpa o que estava à frente.",
            "- Funcionam também com o painel de navegação recolhido, que é quando a prévia mais precisa de largura.",
        ],
    ),
    "cs": (
        "Přecházení mezi stránkami",
        [
            "Dvě tlačítka vlevo v záhlaví procházejí navštívené stránky zpět a vpřed, jako to dělá prohlížeč — **Alt+šipka vlevo** a **Alt+šipka vpravo**, nebo boční tlačítka myši.",
            "- Stránka zůstává tak, jak jste ji opustili, takže návrat na ni vrací zvolené období a náhled ve stavu, v jakém byly, nikoli nově otevřenou stránku.",
            "- Jako v prohlížeči: výběr nové stránky smaže to, co bylo před vámi.",
            "- Fungují i se sbaleným navigačním panelem, tedy právě tehdy, kdy náhled potřebuje šířku nejvíce.",
        ],
    ),
    "tr": (
        "Sayfalar arasında gezinme",
        [
            "Başlık çubuğunun solundaki iki düğme, tıpkı bir tarayıcı gibi, ziyaret ettiğiniz sayfalarda geri ve ileri gider: **Alt+Sol ok** ve **Alt+Sağ ok** ya da farenin yan düğmeleri.",
            "- Sayfa bıraktığınız hâliyle korunur, bu yüzden bir sayfaya dönmek seçili aralığı ve önizlemeyi olduğu gibi geri getirir; yeniden açılmış bir sayfa değildir.",
            "- Tarayıcıdaki gibi, yeni bir sayfa seçmek önünüzdekini siler.",
            "- Gezinme bölmesi katlanmışken de çalışırlar; önizlemenin genişliğe en çok ihtiyaç duyduğu an da budur.",
        ],
    ),
    "ru": (
        "Переход между страницами",
        [
            "Две кнопки слева в заголовке перемещаются по посещённым страницам назад и вперёд, как это делает браузер: **Alt+Стрелка влево** и **Alt+Стрелка вправо** или боковые кнопки мыши.",
            "- Страница сохраняется в том виде, в каком вы её покинули, поэтому возврат к ней восстанавливает выбранный период и предпросмотр в прежнем состоянии, а не открывает страницу заново.",
            "- Как в браузере: выбор новой страницы стирает то, что было впереди.",
            "- Они работают и со свёрнутой панелью навигации — именно тогда, когда предпросмотру больше всего нужна ширина.",
        ],
    ),
    "ja": (
        "ページ間の移動",
        [
            "タイトルバーの左端にある二つのボタンは、ブラウザと同じように訪問済みのページを戻ったり進んだりします。**Alt+←**、**Alt+→**、またはマウスのサイドボタンです。",
            "- ページは離れたときの状態のまま保持されるため、戻ると当時の期間とプレビューがそのまま再現されます。開き直すわけではありません。",
            "- ブラウザと同じく、新しいページを選ぶと前方の履歴は消去されます。",
            "- ナビゲーションウィンドウを折りたたんでいても使えます。プレビューが幅を最も必要とする場面です。",
        ],
    ),
    "ko": (
        "페이지 간 이동",
        [
            "제목 표시줄 왼쪽의 두 버튼은 브라우저처럼 방문한 페이지를 뒤로 또는 앞으로 이동합니다. **Alt+왼쪽 화살표**, **Alt+오른쪽 화살표**, 또는 마우스 측면 버튼입니다.",
            "- 페이지는 떠날 때의 상태로 유지되므로, 돌아가면 그때의 기간과 미리보기가 그대로 나타납니다. 새로 열리는 것이 아닙니다.",
            "- 브라우저와 마찬가지로 새 페이지를 선택하면 앞쪽 기록은 지워집니다.",
            "- 탐색 창이 접혀 있어도 동작합니다. 미리보기가 너비를 가장 필요로 할 때입니다.",
        ],
    ),
    "zh-Hans": (
        "在页面之间切换",
        [
            "标题栏左侧那两个按钮，像浏览器一样在你访问过的页面之间后退和前进：**Alt+向左键**、**Alt+向右键**，或者鼠标侧键。",
            "- 页面按你离开时的样子保留，所以回到某个页面是回到当时的区间和预览，而不是重新打开。",
            "- 像浏览器一样：另选一个新页面，前方的记录就被清空。",
            "- 导航窗格收起时它们照样可用，而那正是预览最需要宽度的时候。",
        ],
    ),
    "zh-Hant": (
        "在頁面之間切換",
        [
            "標題列左側那兩個按鈕，像瀏覽器一樣在你造訪過的頁面之間後退和前進：**Alt+向左鍵**、**Alt+向右鍵**，或者滑鼠側鍵。",
            "- 頁面按你離開時的樣子保留，所以回到某個頁面是回到當時的區間和預覽，而不是重新開啟。",
            "- 像瀏覽器一樣：另選一個新頁面，前方的記錄就被清空。",
            "- 導覽窗格收起時它們照樣可用，而那正是預覽最需要寬度的時候。",
        ],
    ),
}

# Second in the document: it is about getting around, so it belongs before the
# first page's own chapter rather than among them.
POSITION = 1


def main() -> None:
    counts = {}

    for tag, (heading, lines_of_body) in CHAPTER.items():
        path = HELP / f"help-{tag}.md"
        raw = path.read_bytes()

        if not raw.startswith(b"\xef\xbb\xbf"):
            sys.exit(f"{tag}: no byte order mark")

        lines = raw.decode("utf-8-sig").split("\n")

        # Drop an earlier copy: from its heading to the next heading or the end.
        start = next((i for i, line in enumerate(lines) if line.strip() == f"## {heading}"), None)

        if start is not None:
            end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))

            while end > start and lines[end - 1].strip() == "":
                end -= 1

            del lines[start:end]

        headings = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(headings) <= POSITION:
            sys.exit(f"{tag}: only {len(headings)} chapters, cannot insert at {POSITION}")

        block = [f"## {heading}", ""] + lines_of_body[:1] + [""] + lines_of_body[1:] + [""]
        at = headings[POSITION]
        lines[at:at] = block
        path.write_bytes(b"\xef\xbb\xbf" + "\n".join(lines).encode("utf-8"))

        again = [i for i, line in enumerate(lines) if line.startswith("## ")]
        counts[tag] = len(again)
        print(f"{tag:8s} {len(again):3d} chapters, new one at {POSITION}  — {heading}")

    if len(set(counts.values())) != 1:
        sys.exit(f"chapter counts differ: {counts}")

    print(f"OK  14 files agree: {set(counts.values()).pop()} chapters")


if __name__ == "__main__":
    main()
