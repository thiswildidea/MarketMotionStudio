# -*- coding: utf-8 -*-
"""14 份帮助文档插入「背景图片」章节（第 11 章「数据…」之前）。可重复运行。"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CHAPTERS = {
    "zh-Hans": """## 背景图片

设置页可以为窗口选一张背景图片，以调暗的方式显示在所有内容后面。卡片和面板保持不透明，导航栏只透出一点，所以图片主要在它们周围露出来；视频预览有自己的底色，不受影响。

- 可以从电脑里选一张，也可以直接用 Windows 自带的壁纸和锁屏图片。
- 自己选的图片会复制一份保存，移动或删除原文件不影响背景。
- 遮罩强度决定图片被压暗的程度，范围 30%–95%。
- 系统开启了高对比度时不显示背景图片。
""",
    "zh-Hant": """## 背景圖片

設定頁可以為視窗選一張背景圖片，以調暗的方式顯示在所有內容後面。卡片和面板保持不透明，導覽列只透出一點，所以圖片主要在它們周圍露出來；影片預覽有自己的底色，不受影響。

- 可以從電腦裡選一張，也可以直接使用 Windows 內建的桌布與鎖定畫面圖片。
- 自己選的圖片會複製一份儲存，移動或刪除原檔不影響背景。
- 遮罩強度決定圖片被壓暗的程度，範圍 30%–95%。
- 系統開啟高對比時不顯示背景圖片。
""",
    "en-US": """## Background picture

The Settings page can put a picture behind the window, dimmed. Cards and panels stay opaque and the navigation pane lets only a little through, so the picture shows mainly around them; the video preview has its own solid backdrop and is unaffected.

- Pick one from your computer, or use one of the wallpapers and lock-screen pictures Windows already ships.
- A picture you pick is copied into the app's own folder, so moving or deleting the original does not affect the background.
- The dimming slider sets how far the picture is pushed back, from 30% to 95%.
- No picture is shown while high contrast is on.
""",
    "ja": """## 背景画像

設定ページで、ウィンドウの背後に暗くした画像を表示できます。カードやパネルは不透明のまま、ナビゲーション部分だけがわずかに透け、画像は主にその周囲に現れます。動画プレビューは独自の不透明な背景を持つため、影響を受けません。

- パソコン内の画像を選ぶほか、Windows に付属の壁紙やロック画面の画像をそのまま使えます。
- 選んだ画像はアプリのフォルダーにコピーして保存するため、元のファイルを移動・削除しても背景には影響しません。
- 「マスクの強さ」で画像を暗くする度合いを 30%〜95% の範囲で調節できます。
- ハイ コントラストが有効な間は背景画像を表示しません。
""",
    "ko": """## 배경 이미지

설정 페이지에서 창 뒤에 어둡게 처리된 배경 이미지를 표시할 수 있습니다. 카드와 패널은 불투명하게 유지되고 탐색 창은 조금만 비치므로, 이미지는 주로 그 주변에 나타납니다. 동영상 미리보기는 자체적인 불투명 배경을 가지므로 영향을 받지 않습니다.

- 컴퓨터에서 이미지를 선택하거나, Windows에 내장된 배경화면 및 잠금 화면 이미지를 그대로 사용할 수 있습니다.
- 선택한 이미지는 앱 폴더에 복사되어 저장되므로, 원본 파일을 이동하거나 삭제해도 배경에는 영향이 없습니다.
- 마스크 강도 슬라이더로 이미지를 얼마나 어둡게 할지 30%–95% 범위에서 조절합니다.
- 고대비가 켜져 있는 동안에는 배경 이미지를 표시하지 않습니다.
""",
    "de": """## Hintergrundbild

Auf der Einstellungsseite lässt sich ein Bild hinter das Fenster legen, abgedunkelt. Karten und Flächen bleiben deckend, nur die Navigationsspalte lässt ein wenig durch — das Bild zeigt sich also hauptsächlich um sie herum. Die Videovorschau hat ihren eigenen, deckenden Hintergrund und bleibt unberührt.

- Wählen Sie ein Bild vom Computer oder verwenden Sie direkt einen der mitgelieferten Windows-Hintergründe bzw. Sperrbildschirm-Bilder.
- Ein gewähltes Bild wird in den eigenen Ordner der App kopiert; Verschieben oder Löschen des Originals berührt den Hintergrund nicht.
- Der Abdeckungsregler legt fest, wie stark das Bild zurücktritt — von 30 % bis 95 %.
- Bei aktiviertem hohem Kontrast wird kein Hintergrundbild angezeigt.
""",
    "es": """## Imagen de fondo

La página de configuración puede colocar una imagen detrás de la ventana, atenuada. Las tarjetas y paneles siguen siendo opacos y el panel de navegación deja pasar solo un poco, de modo que la imagen se ve sobre todo a su alrededor. La vista previa del vídeo tiene su propio fondo sólido y no se ve afectada.

- Elija una imagen del equipo o use directamente uno de los fondos y las imágenes de pantalla de bloque que incluye Windows.
- La imagen elegida se copia a la carpeta de la aplicación; mover o eliminar el original no afecta al fondo.
- El control de intensidad de máscara define cuánto se oscurece la imagen, del 30 % al 95 %.
- No se muestra ninguna imagen mientras el alto contraste esté activado.
""",
    "fr": """## Image d'arrière-plan

La page des paramètres peut placer une image derrière la fenêtre, assombrie. Les cartes et les panneaux restent opaques et le volet de navigation ne laisse passer qu'un peu de l'image, qui apparaît surtout autour d'eux. L'aperçu vidéo possède son propre fond opaque et n'est pas concerné.

- Choisissez une image sur l'ordinateur ou utilisez directement l'un des fonds d'écran et images d'écran de verrouillage fournis avec Windows.
- L'image choisie est copiée dans le dossier propre à l'application : déplacer ou supprimer l'original ne touche pas l'arrière-plan.
- Le curseur d'intensité du voile détermine à quel point l'image est atténuée, de 30 % à 95 %.
- Aucune image n'est affichée tant que le contraste élevé est activé.
""",
    "it": """## Immagine di sfondo

La pagina delle impostazioni può mettere un'immagine dietro la finestra, attenuata. Le schede e i pannelli restano opachi e il riquadro di navigazione lascia filtrare solo un poco, quindi l'immagine si vede soprattutto intorno a essi. L'anteprima video ha il proprio fondo opaco e non ne è influenzata.

- Scegli un'immagine dal computer oppure usa direttamente uno degli sfondi e delle immagini della schermata di blocco inclusi in Windows.
- L'immagine scelta viene copiata nella cartella dell'app: spostare o eliminare l'originale non influisce sullo sfondo.
- Il dispositivo di intensità maschera regola quanto l'immagine viene attenuata, dal 30% al 95%.
- Nessuna immagine viene mostrata quando il contrasto elevato è attivo.
""",
    "pl": """## Obraz w tle

Na stronie ustawień można umieścić obraz za oknem, przyciemniony. Karty i panele pozostają nieprzezroczyste, a okienko nawigacji przepuszcza tylko trochę — obraz widać głównie wokół nich. Podgląd wideo ma własne nieprzezroczyste tło i pozostaje bez zmian.

- Wybierz obraz z komputera lub użyj wprost jednej z tapet i obrazów ekranu blokady dołączonych do systemu Windows.
- Wybrany obraz jest kopiowany do folderu aplikacji — przeniesienie lub usunięcie oryginału nie wpływa na tło.
- Suwak intensywności maski określa, jak bardzo obraz zostaje przygaszony, w zakresie od 30% do 95%.
- Gdy włączony jest wysoki kontrast, obraz w tle nie jest pokazywany.
""",
    "pt-BR": """## Imagem de fundo

A página de configurações pode colocar uma imagem atrás da janela, escurecida. Os cartões e painéis permanecem opacos e o painel de navegação deixa passar só um pouco — a imagem aparece principalmente ao redor deles. A prévia do vídeo tem seu próprio fundo sólido e não é afetada.

- Escolha uma imagem do computador ou use diretamente um dos planos de fundo e imagens da tela de bloqueio que acompanham o Windows.
- A imagem escolhida é copiada para a pasta do aplicativo; mover ou excluir o original não afeta o fundo.
- O controle de intensidade da máscara define o quanto a imagem é escurecida, de 30% a 95%.
- Nenhuma imagem é mostrada enquanto o alto contraste estiver ativado.
""",
    "cs": """## Obrázek na pozadí

Na stránce nastavení lze za okno umístit ztmavený obrázek. Karty a panely zůstávají neprůhledné a navigační panel propouští jen málo — obrázek je tak vidět hlavně kolem nich. Náhled videa má vlastní neprůhledné pozadí a nedotkne se ho to.

- Vyberte obrázek z počítače nebo použijte přímo některou z tapet a obrázků uzamčené obrazovky, které Windows nabízí.
- Vybraný obrázek se zkopíruje do složky aplikace — přesunutí nebo smazání originálu pozadí neovlivní.
- Posuvník intenzity masky určuje, jak moc se obrázek ztmaví, v rozsahu 30–95 %.
- Když je zapnutý vysoký kontrast, obrázek na pozadí se nezobrazuje.
""",
    "tr": """## Arka plan resmi

Ayarlar sayfası, pencerenin arkasına karartılmış bir resim koyabilir. Kartlar ve paneller opak kalır, gezinti bölmesi yalnızca biraz geçirir — resim asıl olarak çevrelerinde görünür. Video önizlemesinin kendi opak arka planı vardır ve etkilenmez.

- Bilgisayarınızdan bir resim seçin ya da Windows ile gelen duvar kağıtlarını ve kilit ekranı resimlerini doğrudan kullanın.
- Seçilen resim uygulamanın kendi klasörüne kopyalanır; özgün dosyayı taşımak veya silmek arka planı etkilemez.
- Maske yoğunluğu kaydırıcısı, resmin ne kadar karartılacağını %30–95 arasında belirler.
- Yüksek karşıtlık açıkken arka plan resmi gösterilmez.
""",
    "ru": """## Фоновое изображение

На странице параметров можно поместить за окно затемнённое изображение. Карточки и панели остаются непрозрачными, область навигации пропускает лишь немного — изображение видно в основном вокруг них. У предпросмотра видео собственный непрозрачный фон, он не затронут.

- Выберите изображение на компьютере или возьмите прямо одну из обоев и картинок экрана блокировки, поставляемых с Windows.
- Выбранное изображение копируется в папку приложения: перемещение или удаление оригинала на фон не влияет.
- Ползунок интенсивности маски задаёт, насколько изображение приглушено, от 30 % до 95 %.
- Пока включена высокая контрастность, фоновое изображение не показывается.
""",
}


def main():
    root = r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help"
    for tag, chapter in CHAPTERS.items():
        path = os.path.join(root, f"help-{tag}.md")
        with open(path, "rb") as f:
            text = f.read().decode("utf-8-sig")

        if chapter.strip().splitlines()[0] in text:
            print(f"{tag}: 已有，跳过")
            continue

        # 第 11 章标题行（0 起 index 10）之前插入
        lines = text.splitlines(keepends=True)
        heads = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
        assert len(heads) == 12, (tag, len(heads))
        insert_at = heads[10]

        block = chapter if chapter.endswith("\n") else chapter + "\n"
        new = "".join(lines[:insert_at]) + block + "".join(lines[insert_at:])

        with open(path, "wb") as f:
            f.write(b"\xef\xbb\xbf" + new.encode("utf-8"))
        print(f"{tag}: 插入于第 {insert_at + 1} 行前")

    # 章节数一致性校验
    counts = set()
    for path in glob.glob(os.path.join(root, "help-*.md")):
        with open(path, "rb") as f:
            t = f.read().decode("utf-8-sig")
        counts.add(sum(1 for ln in t.splitlines() if ln.startswith("## ")))
    print("章节数一致:", counts)


if __name__ == "__main__":
    main()
