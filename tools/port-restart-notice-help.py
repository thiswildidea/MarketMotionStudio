# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「选择市场」章各补一条：那句话出现在页面顶端，并带一个重启按钮。

**为什么非说不可**：改市场或改语言时画面上什么都不变（两件都要重启才生效），所以那句提示
就是**唯一的反馈**。它原先写在页面最后一张卡片下面 —— 市场与语言是头两张卡，改完那一眼根本
不在同一屏，于是「看不到」被读成「没生效」。现在钉在顶上，这条说明就是这个行为的出处。

**只加一条，不动原来那句**：原来那句讲的是「改动会在重启后生效」，还对；这一条讲的是**这句话
在哪儿、以及可以直接点重启**，独立成条。

**定位两条腿，缺一条就炸**：

* 章节号取**第 0 章**（`CHAPTER = 0`），不靠页名反查。「选择市场」不属于任何一页 ——
  `listingtext.LEADING_CHAPTERS` 里那两章排在页面之前，导航里没有对应的项，
  `chapter_of("NavMarket")` 会直接抛 `KeyError`。但它仍然是随导航一起长的一章，所以
  下面仍用 `listingtext` 的常量核对一句，免得这个 0 将来被挪走。
* 章节内找**以「A 股 / A-shares / …」开头的那一条**（各语言的市场名首项，见 `FIRST`）：这一章里
  只有它是真正的列表项，其余是正文段落。找不到或找到多条就 `assert` 失败。

文件编码**照原样**（`had_bom` + `crlf`）：帮助手册是 LF 且无 BOM，硬写 BOM 会在 diff 里表现为
首行多一个看不见的字符。

用法：python tools\port-restart-notice-help.py
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP

# 「选择市场」是手册的第 0 章 —— 它在两章导言里，不是任何一页，所以导航里查不到它。
# 用 `listingtext.LEADING_CHAPTERS` 反过来核对：页面从那一章开始，这一章在它之前。
CHAPTER = 0

# 这一章里第一条列表项，各语言用的第一个市场名。用来认出那条列表项的位置 ——
# 新条目插在它**前面**（该章开篇讲市场，第一条列的是哪个市场，重启那句属于更前面）。
FIRST = {
    "en-US": "- **A-shares**",
    "de": "- **A-Aktien**",
    "es": "- **Acciones A**",
    "fr": "- **Actions A**",
    "it": "- **Azioni A**",
    "pl": "- **Akcje A**",
    "pt-BR": "- **Ações A**",
    "cs": "- **A-akcie**",
    "tr": "- **A hisseleri**",
    "ru": "- **A-акции**",
    "ja": "- **A 株**",
    "ko": "- **A주**",
    "zh-Hans": "- **A 股**",
    "zh-Hant": "- **A 股**",
}

# 新条目。说的是**改动之后画面不变，所以提示条钉在顶上**，以及条子上可以直接重启。
ENTRY = {
    "en-US": "- **The choice is stored, not applied.** Nothing on screen changes until the "
             "app is restarted, so the line saying so appears at the **top of the Settings "
             "page**, above the cards and fixed there as you scroll, with a button that "
             "restarts the app for you.",

    "de": "- **Die Wahl wird gespeichert, nicht angewandt.** Auf dem Bildschirm ändert sich "
          "nichts, bis die App neu gestartet wird; deshalb steht der entsprechende Hinweis "
          "**oben auf der Einstellungsseite**, über den Karten und beim Scrollen dort "
          "festgehalten, mit einer Schaltfläche, die die App für Sie neu startet.",

    "es": "- **La elección se guarda, no se aplica.** En pantalla no cambia nada hasta "
          "reiniciar la aplicación, así que el aviso correspondiente aparece **arriba del "
          "todo en la página de ajustes**, sobre las tarjetas y fijo ahí mientras se "
          "desplaza, con un botón que reinicia la aplicación por usted.",

    "fr": "- **Le choix est enregistré, pas appliqué.** Rien ne change à l'écran avant le "
          "redémarrage de l'application : la phrase qui le dit s'affiche donc **en haut de "
          "la page de paramètres**, au-dessus des cartes et y reste fixée pendant le "
          "défilement, avec un bouton qui redémarre l'application pour vous.",

    "it": "- **La scelta viene memorizzata, non applicata.** Sullo schermo non cambia nulla "
          "finché l'app non viene riavviata, quindi la riga che lo dice compare **in cima "
          "alla pagina delle impostazioni**, sopra le schede e resta lì mentre scorri, con "
          "un pulsante che riavvia l'app per te.",

    "pl": "- **Wybór jest zapisywany, nie stosowany.** Na ekranie nic się nie zmieni, dopóki "
          "aplikacja nie zostanie ponownie uruchomiona, więc odpowiedni komunikat pojawia "
          "się **na górze strony ustawień**, nad kartami i pozostaje tam podczas "
          "przewijania, z przyciskiem, który uruchomi aplikację ponownie za Ciebie.",

    "pt-BR": "- **A escolha é guardada, não aplicada.** Nada muda no ecrã até a aplicação "
             "ser reiniciada, por isso a linha que o diz aparece **no topo da página de "
             "definições**, acima dos cartões e fixa ali enquanto se desloca, com um botão "
             "que reinicia a aplicação por si.",

    "cs": "- **Volba se uloží, ale nepoužije.** Na obrazovce se nic nezmění, dokud se "
          "aplikace nerestartuje, takže se příslušný řádek zobrazí **nahoře na stránce "
          "nastavení**, nad kartami, a při posouvání tam zůstává, s tlačítkem, které "
          "aplikaci restartuje za vás.",

    "tr": "- **Seçim kaydedilir, uygulanmaz.** Uygulama yeniden başlatılana kadar ekranda "
          "hiçbir şey değişmez; bu yüzden bunu söyleyen satır **Ayarlar sayfasının en "
          "üstünde**, kartların üzerinde görünür ve sayfayı kaydırdığınızda orada sabit "
          "kalır; yanındaki düğme uygulamayı sizin için yeniden başlatır.",

    "ru": "- **Выбор сохраняется, но не применяется.** На экране ничего не меняется до "
          "перезапуска приложения, поэтому сообщающая об этом строка появляется **вверху "
          "страницы параметров**, над карточками, и остаётся там при прокрутке; рядом — "
          "кнопка, которая перезапустит приложение за вас.",

    "ja": "- **選んだ時点では保存されるだけで、まだ反映されません。** アプリを再起動するまで画面上は"
          "何も変わりません。そのため、その旨の行は**設定ページの最上部**、カードの上に表示され、"
          "スクロールしてもそこに固定されます。となりのボタンでその場で再起動できます。",

    "ko": "- **선택은 저장될 뿐 적용되지는 않습니다.** 앱을 다시 시작하기 전까지 화면은 그대로이므로, "
          "그 사실을 알리는 줄이 **설정 페이지 맨 위에** 카드보다 먼저 나오고 스크롤해도 그 자리에 "
          "고정되며, 옆의 버튼으로 바로 다시 시작할 수 있습니다.",

    "zh-Hans": "- **选完只是记下来，还没有生效。** 重启应用之前画面上不会有任何变化，所以这句话"
               "出现在**设置页最顶端**，在所有卡片之上，页面滚动时也固定在那里；旁边那个按钮"
               "可以直接重启。",

    "zh-Hant": "- **選完只是記下來，還沒有生效。** 重新啟動應用程式之前畫面上不會有任何變化，"
               "所以這句話出現在**設定頁最頂端**，在所有卡片之上，頁面捲動時也固定在那裡；"
               "旁邊那個按鈕可以直接重新啟動。",
}


def main():
    chapter = CHAPTER

    # 一条廉价的护栏：`LEADING_CHAPTERS` 是被商店文案脚本用来把「第几页」换算成「第几章」的，
    # 它变了就说明有章节被挪动过，这一章未必还是第 0 章。
    assert CHAPTER < lt.LEADING_CHAPTERS

    print(f"「选择市场」取第 {chapter + 1} 章")

    for tag in lt.LANGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")
        starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

        assert chapter < len(starts), f"{tag}: {len(starts)} chapters, need {chapter + 1}"

        start = starts[chapter]
        end = starts[chapter + 1] if chapter + 1 < len(starts) else len(lines)
        block = lines[start:end]

        if any(line.strip() == ENTRY[tag] for line in block):
            print(f"{tag:9} 已有")
            continue

        hits = [i for i, line in enumerate(block) if line.startswith(FIRST[tag])]

        assert len(hits) == 1, (
            f"{tag}: {len(hits)} entries start with {FIRST[tag]!r}, expected 1")

        block = block[:hits[0]] + [ENTRY[tag]] + block[hits[0]:]
        lines[start:end] = block

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +1")


if __name__ == "__main__":
    main()
