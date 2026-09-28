# -*- coding: utf-8 -*-
r"""给 14 份帮助文档加「更新」章节——商店更新按钮的说明。

插在每份文档的**最后一章之前**（最后一章是「出了问题？/Trouble?」那一类
收尾章），这样 14 份的章节数和顺序保持一致——项目的铁律是改一处就改全部。

措辞取自各语言 resw 里已有的 NavUpdate / NavUpdateTip / UpdateFailed /
UpdateNeedsWiFi / UpdateLowBattery，术语不做二次创造。

用法：python tools\port-update-help.py   （可重复运行，先删旧章节）
"""
import re
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 语言 -> (章节标题, 段落, [条目...])
CHAPTERS = {
    "zh-Hans": (
        "更新",
        "Microsoft Store 里出现新版本时，导航栏「设置」的右边会多出一个**更新**按钮，点一下就能装。",
        [
            "只在商店确实有新版本时出现。直接安装的开发版或侧载版看不到它，这是正常的。",
            "安装期间应用会关闭，装好后以新版本自动重启，按钮随之消失。正在导出时会先问一句。",
            "装不上时会说明原因，例如只能在 Wi-Fi 下下载、电量过低。也可以直接到 Microsoft Store 里更新。",
        ],
    ),
    "zh-Hant": (
        "更新",
        "Microsoft Store 裡出現新版本時，導覽列「設定」的右邊會多出一個**更新**按鈕，點一下就能裝。",
        [
            "只在商店確實有新版本時出現。直接安裝的開發版或側載版看不到它，這是正常的。",
            "安裝期間應用程式會關閉，裝好後以新版本自動重新啟動，按鈕隨之消失。正在匯出時會先問一句。",
            "裝不上時會說明原因，例如只能在 Wi-Fi 下下載、電量過低。也可以直接到 Microsoft Store 裡更新。",
        ],
    ),
    "en-US": (
        "Updating",
        "When the Microsoft Store has a newer version, an **Update** button appears beside Settings in the navigation pane; one click installs it.",
        [
            "It only appears when the Store really has a newer version. A development or sideloaded build never sees it, and that is expected.",
            "The app closes while the update installs and starts again on the new version, and the button is gone. If an export is running, it asks first.",
            "If it cannot install, it says why — Wi-Fi only, battery too low — and the update can also be installed from the Microsoft Store.",
        ],
    ),
    "ja": (
        "更新",
        "Microsoft Store に新しいバージョンがあると、ナビゲーション ウィンドウの「設定」の横に **更新** ボタンが表示され、クリックするとインストールできます。",
        [
            "ストアに実際に新しいバージョンがあるときだけ表示されます。直接インストールした開発版やサイドロード版では表示されません。",
            "インストール中はアプリが閉じ、新しいバージョンで自動的に再起動するとボタンは消えます。書き出し中は先に確認します。",
            "インストールできないときは理由を知らせます(Wi-Fi のみ、バッテリー残量が少ないなど)。Microsoft Store からもインストールできます。",
        ],
    ),
    "ko": (
        "업데이트",
        "Microsoft Store에 새 버전이 있으면 탐색 창의 설정 옆에 **업데이트** 버튼이 나타나고, 누르면 설치됩니다.",
        [
            "스토어에 실제로 새 버전이 있을 때만 나타납니다. 직접 설치한 개발 버전이나 사이드로드 버전에서는 보이지 않습니다.",
            "설치하는 동안 앱이 닫히고 새 버전으로 자동으로 다시 시작되면 버튼이 사라집니다. 내보내는 중이면 먼저 물어봅니다.",
            "설치할 수 없으면 이유를 알려 줍니다(Wi-Fi에서만, 배터리 부족 등). Microsoft Store에서도 설치할 수 있습니다.",
        ],
    ),
    "de": (
        "Aktualisieren",
        "Hat der Microsoft Store eine neuere Version, erscheint im Navigationsbereich neben Einstellungen eine Schaltfläche **Aktualisieren**; ein Klick installiert sie.",
        [
            "Sie erscheint nur, wenn der Store wirklich eine neuere Version hat. Ein Entwicklungs- oder quergeladenes Build sieht sie nie — das ist so gewollt.",
            "Die App schließt sich während der Installation und startet mit der neuen Version neu, die Schaltfläche ist dann verschwunden. Läuft gerade ein Export, wird vorher gefragt.",
            "Klappt es nicht, wird der Grund genannt — nur über WLAN, Akku zu schwach — und das Update lässt sich auch über den Microsoft Store installieren.",
        ],
    ),
    "es": (
        "Actualizar",
        "Cuando Microsoft Store tiene una versión más reciente, aparece un botón **Actualizar** junto a Configuración en el panel de navegación; con un clic se instala.",
        [
            "Solo aparece cuando la Store tiene de verdad una versión más reciente. Una compilación de desarrollo o instalada aparte nunca lo ve, y eso es lo esperado.",
            "La aplicación se cierra mientras se instala y vuelve a abrirse con la nueva versión, y el botón desaparece. Si hay una exportación en curso, pregunta antes.",
            "Si no se puede instalar, dice por qué —solo por Wi-Fi, batería demasiado baja— y también se puede instalar desde Microsoft Store.",
        ],
    ),
    "fr": (
        "Mise à jour",
        "Quand le Microsoft Store propose une version plus récente, un bouton **Mettre à jour** apparaît à côté de Paramètres dans le volet de navigation ; un clic l'installe.",
        [
            "Il n'apparaît que si le Store a réellement une version plus récente. Une version de développement ou installée à côté ne le voit jamais, et c'est normal.",
            "L'application se ferme pendant l'installation et redémarre sur la nouvelle version, et le bouton disparaît. Si un export est en cours, elle demande d'abord.",
            "Si l'installation échoue, la raison est donnée — Wi-Fi uniquement, batterie trop faible — et la mise à jour peut aussi être installée depuis le Microsoft Store.",
        ],
    ),
    "it": (
        "Aggiornamento",
        "Quando il Microsoft Store ha una versione più recente, accanto a Impostazioni nel riquadro di navigazione compare un pulsante **Aggiorna**; un clic la installa.",
        [
            "Compare solo quando lo Store ha davvero una versione più recente. Una build di sviluppo o installata a parte non lo vede mai, ed è normale.",
            "L'app si chiude durante l'installazione e si riavvia con la nuova versione, e il pulsante scompare. Se è in corso un'esportazione, chiede prima.",
            "Se non si installa, dice perché — solo Wi-Fi, batteria troppo scarica — e l'aggiornamento si può installare anche dal Microsoft Store.",
        ],
    ),
    "pl": (
        "Aktualizowanie",
        "Gdy w Microsoft Store jest nowsza wersja, w panelu nawigacji obok Ustawień pojawia się przycisk **Aktualizuj**; jedno kliknięcie ją instaluje.",
        [
            "Pojawia się tylko wtedy, gdy w Store naprawdę jest nowsza wersja. Kompilacja deweloperska albo zainstalowana z boku nigdy go nie zobaczy i tak ma być.",
            "Aplikacja zamyka się na czas instalacji i uruchamia ponownie w nowej wersji, a przycisk znika. Jeśli trwa eksport, najpierw zapyta.",
            "Jeśli instalacja się nie uda, poda powód — tylko przez Wi-Fi, za słaba bateria — a aktualizację można też zainstalować z Microsoft Store.",
        ],
    ),
    "pt-BR": (
        "Atualização",
        "Quando a Microsoft Store tem uma versão mais nova, aparece um botão **Atualizar** ao lado de Configurações no painel de navegação; um clique instala.",
        [
            "Ele só aparece quando a Store realmente tem uma versão mais nova. Uma compilação de desenvolvimento ou instalada por fora nunca o vê, e isso é esperado.",
            "O aplicativo fecha durante a instalação e abre de novo na nova versão, e o botão some. Se uma exportação estiver rodando, ele pergunta antes.",
            "Se não conseguir instalar, ele diz o motivo — só por Wi-Fi, bateria fraca — e a atualização também pode ser instalada pela Microsoft Store.",
        ],
    ),
    "cs": (
        "Aktualizace",
        "Když má Microsoft Store novější verzi, objeví se v navigačním panelu vedle Nastavení tlačítko **Aktualizovat**; jedno kliknutí ji nainstaluje.",
        [
            "Objeví se jen tehdy, když Store skutečně nabízí novější verzi. Vývojové sestavení nebo sestavení nainstalované mimo Store ho nikdy neuvidí a tak to má být.",
            "Během instalace se aplikace zavře a spustí se v nové verzi, tlačítko zmizí. Pokud právě probíhá export, nejdřív se zeptá.",
            "Když instalace selže, řekne proč — jen přes Wi-Fi, slabá baterie — a aktualizaci lze nainstalovat i z Microsoft Storu.",
        ],
    ),
    "ru": (
        "Обновление",
        "Когда в Microsoft Store появляется более новая версия, на панели навигации рядом с «Параметрами» появляется кнопка **Обновить**; одно нажатие её устанавливает.",
        [
            "Кнопка появляется только тогда, когда в Store действительно есть новая версия. Сборка для разработки или установленная в обход Store её не увидит — так и задумано.",
            "На время установки приложение закрывается и запускается в новой версии, а кнопка исчезает. Если идёт экспорт, оно сначала спросит.",
            "Если установить не удалось, оно скажет почему — только по Wi-Fi, низкий заряд — а обновление можно установить и из Microsoft Store.",
        ],
    ),
    "tr": (
        "Güncelleme",
        "Microsoft Store'da daha yeni bir sürüm olduğunda gezinti bölmesinde Ayarlar'ın yanında bir **Güncelle** düğmesi görünür; tek tıkla kurulur.",
        [
            "Yalnızca Store'da gerçekten daha yeni bir sürüm varsa görünür. Geliştirme veya yandan yüklenmiş bir derlemede hiç görünmez, bu normaldir.",
            "Yükleme sırasında uygulama kapanır ve yeni sürümle yeniden başlar, düğme kaybolur. Dışa aktarma sürüyorsa önce sorar.",
            "Kurulamazsa nedenini söyler — yalnızca Wi-Fi, pil çok düşük — ve güncelleme Microsoft Store'dan da kurulabilir.",
        ],
    ),
}


def main():
    for lang, (title, paragraph, bullets) in CHAPTERS.items():
        path = HELP / f"help-{lang}.md"
        text = path.read_text(encoding="utf-8")

        # 可重复运行：先删掉上一版插进去的章节（从标题到下一个 ## 之前）
        text = re.sub(
            r"\n## %s\n\n.*?(?=\n## )" % re.escape(title), "", text, flags=re.S
        )

        block = "\n".join([f"## {title}", "", paragraph, "", *[f"- {b}" for b in bullets], ""])

        # 插在最后一章之前
        marks = [m for m in re.finditer(r"(?m)^## ", text)]
        assert marks, f"{lang}: 找不到章节"
        cut = marks[-1].start()

        text = text[:cut] + block + "\n" + text[cut:]
        path.write_text(text, encoding="utf-8")
        print(f"{lang}: 已插入「{title}」")

    # 章节结构一致性校验
    import hashlib

    digests = {}
    for lang in CHAPTERS:
        text = (HELP / f"help-{lang}.md").read_text(encoding="utf-8")
        heads = re.findall(r"(?m)^## .*$", text)
        digests[lang] = (len(heads), hashlib.md5(str(len(heads)).encode()).hexdigest())
    counts = {c for c, _ in digests.values()}
    assert len(counts) == 1, f"章节数不一致: {digests}"
    print("14 份章节数一致 ✓  每份", counts.pop(), "章")


if __name__ == "__main__":
    main()
