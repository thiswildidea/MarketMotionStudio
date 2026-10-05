# -*- coding: utf-8 -*-
r"""给 14 份帮助手册的「动画背景」那一章补上水印这两条。

水印是这一轮加在设置页的：一个**默认开启**的开关，和一句可以改成自己的话。开着的每一帧
画面——预览、导出的视频、封面图——背景上都斜向重复地带着这句话，画在数据之下。

**三条必须写进手册的事实**，因为它们都不是从画面上能看出来的：

* **默认开着，以及为什么。** 视频会被发到一个完全看不出它是在哪里做出来的地方；让用户自己
  去打开，等于绝大多数文件出去时都没签名。
* **留空不是删掉。** 清空输入框会回到默认那句话；要什么都不加，得把开关关掉。这两件事不说，
  用户会把「清空」当成「关掉」。
* **默认那句话不跟着界面语言变。** 它是一个签名，跟着语言变就等于每台机器上签的名不一样。
  这是这一条唯一需要解释的地方，也是最容易被当成漏翻译而「修好」的地方。

**按章节序号定位**（0-based 22 = 第 23 章「动画背景」），不按标题找：14 种语言的标题各不
相同。插在那一章最后一个条目之后，不新增章节——新增会把后面所有章推后一位，而
`port-dca-motion-help.py` 那类脚本是按序号定位的。

文件编码**照原样**（`had_bom` + `crlf` 记号）：帮助手册是 LF 且无 BOM，硬写 BOM 会在 diff
里表现为首行多一个看不见的字符，肉眼查不出来。

用法：python tools\port-watermark-help.py
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

# 0-based：「动画背景」是第 23 章。
CHAPTER = 22

TAGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
        "ja", "ko", "zh-Hans", "zh-Hant"]

# ---- 条目一：水印是什么、默认开、可以改、留空与关掉各是什么结果 ------------------

WATERMARK = {
    "en-US": "- **Every frame also carries a name across its backdrop: the watermark.** It is on "
             "by default, reads “周期留白” until you change it, and the wording is yours to "
             "edit. It is repeated on a slant over the whole frame, drawn **under** the data, so "
             "it covers nothing; the preview, the exported video and the cover image all carry "
             "it. Left blank it falls back to the default name — to carry nothing at all, switch "
             "it off. The switch is on by default because a video is posted somewhere that shows "
             "nothing of where it was made.",

    "de": "- **Jedes Bild trägt außerdem einen Namen über seinem Hintergrund: das "
          "Wasserzeichen.** Es ist standardmäßig an, steht auf „周期留白“, bis Sie es ändern, und "
          "der Wortlaut gehört Ihnen. Es wird schräg über das ganze Bild wiederholt, **unter** "
          "den Daten gezeichnet, also überdeckt es nichts; Vorschau, exportiertes Video und "
          "Titelbild tragen es gleichermaßen. Leer gelassen gilt wieder der Standardname — damit "
          "gar nichts erscheint, schalten Sie es ab. Der Schalter ist standardmäßig an, weil ein "
          "Video irgendwo landet, das nichts darüber verrät, wo es entstanden ist.",

    "es": "- **Cada fotograma lleva además un nombre sobre su fondo: la marca de agua.** Está "
          "activada por defecto, dice «周期留白» hasta que la cambies, y la redacción es tuya. Se "
          "repite en diagonal por todo el cuadro, dibujada **bajo** los datos, de modo que no "
          "tapa nada; la vista previa, el vídeo exportado y la imagen de portada la llevan "
          "igual. Si se deja vacía vuelve al nombre por defecto — para que no aparezca nada, "
          "desactívala. El interruptor está activado por defecto porque un vídeo se publica en un "
          "lugar que no dice nada de dónde se hizo.",

    "fr": "- **Chaque image porte aussi un nom sur son fond : le filigrane.** Il est activé par "
          "défaut, il dit « 周期留白 » jusqu'à ce que vous le changiez, et le libellé vous "
          "appartient. Il se répète en diagonale sur toute l'image, dessiné **sous** les données, "
          "donc il ne cache rien ; l'aperçu, la vidéo exportée et l'image de couverture le "
          "portent également. Laissé vide, il reprend le nom par défaut — pour ne rien porter du "
          "tout, désactivez-le. L'interrupteur est activé par défaut parce qu'une vidéo est "
          "publiée quelque part qui ne dit rien d'où elle a été faite.",

    "it": "- **Ogni fotogramma porta anche un nome sul proprio sfondo: la filigrana.** È attiva "
          "per impostazione predefinita, dice «周期留白» finché non la cambi, e la formulazione è "
          "tua. Si ripete in diagonale su tutto il quadro, disegnata **sotto** i dati, quindi non "
          "copre nulla; anteprima, video esportato e immagine di copertina la portano allo stesso "
          "modo. Lasciata vuota torna al nome predefinito — per non portare nulla, va disattivata. "
          "L'interruttore è acceso per default perché un video finisce dove nulla dice da dove "
          "viene.",

    "pl": "- **Każda klatka niesie też nazwę na swoim tle: znak wodny.** Jest domyślnie włączony, "
          "głosi „周期留白”, dopóki go nie zmienisz, a treść jest twoja. Powtarza się ukośnie po "
          "całym obrazie, rysowany **pod** danymi, więc niczego nie zasłania; podgląd, "
          "eksportowane wideo i okładka niosą go tak samo. Pusty wraca do nazwy domyślnej — żeby "
          "nie było go wcale, trzeba go wyłączyć. Przełącznik jest domyślnie włączony, bo wideo "
          "trafia w miejsce, które nic nie mówi o tym, gdzie powstało.",

    "pt-BR": "- **Cada quadro também carrega um nome no seu fundo: a marca d'água.** Ela vem "
             "ativada por padrão, diz «周期留白» até você mudar, e a redação é sua. Repete-se na "
             "diagonal por todo o quadro, desenhada **abaixo** dos dados, portanto não cobre nada; "
             "a pré-visualização, o vídeo exportado e a imagem de capa a levam igual. Deixada em "
             "branco volta ao nome padrão — para não levar nada, desligue-a. O interruptor vem "
             "ligado por padrão porque um vídeo é publicado num lugar que não diz nada sobre onde "
             "foi feito.",

    "cs": "- **Každý snímek nese také jméno na svém pozadí: vodoznak.** Je ve výchozím stavu "
          "zapnutý, říká „周期留白“, dokud ho nezměníte, a znění je vaše. Opakuje se šikmo přes "
          "celý obraz, kreslený **pod** daty, takže nic nezakrývá; náhled, exportované video i "
          "titulní obrázek ho nesou stejně. Prázdný se vrací k výchozímu jménu — aby se neslo nic, "
          "je třeba ho vypnout. Přepínač je zapnutý ve výchozím stavu, protože video končí někde, "
          "kde nic neříká, kde vzniklo.",

    "tr": "- **Her kare, fonunda bir ad daha taşır: filigran.** Varsayılan olarak açıktır, siz "
          "değiştirene kadar „周期留白“ yazar ve metin sizindir. Tüm kare boyunca eğik olarak "
          "yinelenir, verilerin **altına** çizilir, yani hiçbir şeyi kapatmaz; önizleme, dışa "
          "aktarılan video ve kapak görseli de onu taşır. Boş bırakılırsa varsayılan ada döner — "
          "hiçbir şey taşınmasın isterseniz kapatmanız gerekir. Anahtar varsayılan olarak açıktır, "
          "çünkü bir video nerede üretildiğini hiç göstermeyen bir yerde yayımlanır.",

    "ru": "- **Каждый кадр несёт также имя на своём фоне: водяной знак.** Он включён по "
          "умолчанию, гласит «周期留白», пока вы его не измените, а формулировка — ваша. Он "
          "повторяется по диагонали по всему кадру, нарисованный **под** данными, поэтому ничего не "
          "закрывает; предпросмотр, экспортированное видео и обложка несут его одинаково. "
          "Оставленный пустым, он возвращается к имени по умолчанию — чтобы не нести ничего, его "
          "нужно выключить. Переключатель включён по умолчанию, потому что видео попадает туда, где "
          "ничто не говорит, где оно сделано.",

    "ja": "- **書き出すフレームの背景には、もうひとつ名前が入ります。透かしです。** 既定でオン、"
          "変更するまで「周期留白」と書かれていて、文面は自分のものにできます。画面いっぱいに斜めに"
          "繰り返し、データの**下**に描かれるので、何も隠しません。プレビュー、書き出した動画、"
          "カバー画像のどれにも入ります。空にすれば既定の名前に戻ります——何も入れたくなければ、"
          "オフにしてください。既定でオンなのは、動画がどこで作られたかを何も示さない場所に投稿"
          "されるものだからです。",

    "ko": "- **모든 프레임의 배경에는 이름이 하나 더 들어갑니다. 워터마크입니다.** 기본으로 켜져 "
          "있고, 바꾸기 전까지는「周期留白」라고 쓰이며, 문구는 자유롭게 바꿀 수 있습니다. 화면 "
          "전체에 비스듬히 반복되고, 데이터 **아래**에 그려지므로 아무것도 가리지 않습니다. "
          "미리보기, 내보낸 영상, 커버 이미지 모두에 들어갑니다. 비워 두면 기본 이름으로 "
          "돌아갑니다 — 아무것도 넣지 않으려면 꺼야 합니다. 기본이 켜짐인 이유는, 영상이 어디서 "
          "만들어졌는지 아무것도 알려주지 않는 곳에 올라가기 때문입니다.",

    "zh-Hans": "- **每一帧的背景上还带着一行名字：水印。** 默认开启，默认写着「周期留白」，可以"
               "改成你自己的话。它斜向重复铺满画面，画在**数据之下**，所以不会挡住任何东西；"
               "预览、导出的视频和封面图都有。留空会回到默认那句话——要什么都不加，得把开关关掉。"
               "开关默认是开的，因为视频会被发到一个完全看不出它是在哪里做出来的地方。",

    "zh-Hant": "- **每一幀的背景上還帶著一行名字：浮水印。** 預設開啟，預設寫著「周期留白」，"
               "可以改成你自己的話。它斜向重複鋪滿畫面，畫在**數據之下**，所以不會擋住任何東西；"
               "預覽、匯出的影片和封面圖都有。留空會回到預設那句話——要什麼都不加，得把開關關掉。"
               "開關預設是開的，因為影片會被發到一個完全看不出它是在哪裡做出來的地方。",
}

# ---- 条目二：默认那句话为什么不跟着界面语言变 ------------------------------------

SIGNATURE = {
    "en-US": "- The default wording does not follow the interface language: a watermark is a "
             "signature, and a signature that changed with the language would be a different one "
             "on every machine.",

    "de": "- Der Standardwortlaut folgt nicht der Sprache der Oberfläche: Ein Wasserzeichen ist "
          "eine Unterschrift, und eine Unterschrift, die mit der Sprache wechselt, wäre auf jedem "
          "Rechner eine andere.",

    "es": "- La redacción por defecto no sigue el idioma de la interfaz: una marca de agua es una "
          "firma, y una firma que cambiara con el idioma sería una distinta en cada equipo.",

    "fr": "- Le libellé par défaut ne suit pas la langue de l'interface : un filigrane est une "
          "signature, et une signature qui changerait avec la langue en serait une différente sur "
          "chaque machine.",

    "it": "- La formulazione predefinita non segue la lingua dell'interfaccia: una filigrana è una "
          "firma, e una firma che cambiasse con la lingua sarebbe una diversa su ogni macchina.",

    "pl": "- Domyślna treść nie podąża za językiem interfejsu: znak wodny to podpis, a podpis, "
          "który zmieniałby się wraz z językiem, byłby na każdym komputerze innym podpisem.",

    "pt-BR": "- A redação padrão não segue o idioma da interface: uma marca d'água é uma "
             "assinatura, e uma assinatura que mudasse com o idioma seria uma diferente em cada "
             "máquina.",

    "cs": "- Výchozí znění se neřídí jazykem rozhraní: vodoznak je podpis, a podpis, který by se "
          "měnil s jazykem, by byl na každém počítači jiný.",

    "tr": "- Varsayılan metin, arayüz dilini takip etmez: bir filigran bir imzadır ve dille "
          "birlikte değişen bir imza her makinede farklı bir imza olurdu.",

    "ru": "- Формулировка по умолчанию не следует за языком интерфейса: водяной знак — это "
          "подпись, а подпись, меняющаяся вместе с языком, была бы на каждой машине другой.",

    "ja": "- 既定の文面は表示言語に合わせて変わりません。透かしは署名であり、言語で変わる署名は"
          "機械ごとに別の署名になってしまいます。",

    "ko": "- 기본 문구는 인터페이스 언어를 따르지 않습니다. 워터마크는 서명이고, 언어에 따라 "
          "바뀌는 서명은 컴퓨터마다 다른 서명이 됩니다.",

    "zh-Hans": "- 默认那句话不跟着界面语言变：水印是一个签名，跟着语言变就等于每台机器上签的名"
               "都不一样。",

    "zh-Hant": "- 預設那句話不跟著介面語言變：浮水印是一個簽名，跟著語言變就等於每台機器上簽的"
               "名都不一樣。",
}


def main():
    for tag in TAGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")

        starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

        assert len(starts) > CHAPTER, f"{tag}: {len(starts)} chapters, need {CHAPTER + 1}"

        start = starts[CHAPTER]
        end = starts[CHAPTER + 1] if CHAPTER + 1 < len(starts) else len(lines)

        chapter = lines[start:end]

        # Idempotent: the first entry is there already, so this chapter has been done.
        if any(line.strip() == WATERMARK[tag] for line in chapter):
            print(f"{tag:9} already there")
            continue

        bullets = [i for i, line in enumerate(chapter) if line.startswith("- ")]

        assert len(bullets) >= 2, f"{tag}: too few bullets in the backdrop chapter"

        last = bullets[-1]

        # After the last entry, with the blank line the others are separated by. The
        # chapter's own trailing blanks are kept, so the file ends as it did.
        chapter = (
            chapter[:last + 1] + ["", WATERMARK[tag], "", SIGNATURE[tag]]
            + chapter[last + 1:])

        lines[start:end] = chapter

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +2 bullets")


if __name__ == "__main__":
    main()
