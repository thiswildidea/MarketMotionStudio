# -*- coding: utf-8 -*-
r"""把「背景水印」这一轮新加的 resw 键注入 14 份 Resources.resw。

设置页多了一张卡片：一个默认**开启**的开关，和一句可以改的话。开着的每一帧导出画面
（视频、封面 PNG、预览）的背景上都带着这句话，斜向重复、画在数据之下；关掉就什么都不画。

**六个键，都是这张卡片自己的。** 不复用 `SettingsFrameBackdrop*` 那批：那批说的是「画在什么
上面」，这一批说的是「文件出去之后还带着什么」。一个 resw 键只有一个 port 脚本负责，那批归
`port-framebackdrop-resw.py`，这批归这里。

**默认那句话不翻译。** 「周期留白」是一个签名，跟着界面语言变就等于每台机器上签的名不一样 ——
签名最不能有的就是这个。它之所以可编辑，恰恰因为它是用户自己的。所以 `PlaceholderText`
十四份全写同一串，其余五个键照常翻译。

**列序是位置对应的**，14 个值依次给
`en-US de es fr it pl pt-BR cs tr ru ja ko zh-Hant zh-Hans`。第一列必须是英文。

resw 是 **UTF-8 带 BOM + LF**。删键按「基础名 + 可选后缀」匹配，因为文件里单行
`<data name="K">` 与手改过的 `<data name="K" xml:space="preserve">` 两种形态并存。

用法：python tools\port-watermark-resw.py
"""
import re
from pathlib import Path

ROOT = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Strings")

LANGS = ["en-US", "de", "es", "fr", "it", "pl", "pt-BR", "cs", "tr", "ru",
         "ja", "ko", "zh-Hant", "zh-Hans"]

# ---- 卡片标题 -------------------------------------------------------------------

LABEL = [
    "Watermark", "Wasserzeichen", "Marca de agua", "Filigrane", "Filigrana",
    "Znak wodny", "Marca d'água", "Vodoznak", "Filigran", "Водяной знак",
    "透かし", "워터마크", "浮水印", "水印",
]

# ---- 卡片说明 -------------------------------------------------------------------
#
# 三件事必须说清：画在**数据之下**（否则会被当成数据的一部分）、**斜向重复**（否则会被当成
# 一行字）、以及**视频与封面图都有**（否则用户以为只影响预览）。

NOTE = [
    "The name carried across the backdrop of every exported frame — faint, slanted "
    "and repeated, drawn under the data so it never competes with it. It reaches the "
    "video and the cover image as well as the preview.",

    "Der Name, der über den Hintergrund jedes exportierten Bilds liegt — blass, geneigt "
    "und wiederholt, unter den Daten gezeichnet, damit er ihnen nie Konkurrenz macht. "
    "Er gilt für das Video und das Titelbild ebenso wie für die Vorschau.",

    "El nombre que cruza el fondo de cada fotograma exportado — tenue, inclinado y "
    "repetido, dibujado bajo los datos para no competir con ellos. Afecta al vídeo y a "
    "la imagen de portada lo mismo que a la vista previa.",

    "Le nom porté par le fond de chaque image exportée — pâle, incliné et répété, "
    "dessiné sous les données pour ne jamais leur faire concurrence. Il s'applique à la "
    "vidéo et à l'image de couverture comme à l'aperçu.",

    "Il nome che attraversa lo sfondo di ogni fotogramma esportato — tenue, inclinato e "
    "ripetuto, disegnato sotto i dati per non fargli mai concorrenza. Rigguarda il video "
    "e l'immagine di copertina come l'anteprima.",

    "Nazwa niesiona przez tło każdej eksportowanej klatki — blada, pochylona i "
    "powtarzana, rysowana pod danymi, by z nimi nie konkurować. Dotyczy wideo i okładki "
    "tak samo jak podglądu.",

    "O nome que atravessa o fundo de cada quadro exportado — tênue, inclinado e "
    "repetido, desenhado abaixo dos dados para não competir com eles. Vale para o vídeo "
    "e para a imagem de capa como para a pré-visualização.",

    "Jméno nesené pozadím každého exportovaného snímku — slabé, šikmé a opakované, "
    "kreslené pod daty, aby s nimi nesoupeřilo. Platí pro video i titulní obrázek stejně "
    "jako pro náhled.",

    "Dışa aktarılan her karenin fonu boyunca taşınan ad — soluk, eğik ve yinelenen, "
    "verilerle yarışmaması için onların altına çizilir. Önizleme gibi videoya ve kapak "
    "görseline de uygulanır.",

    "Имя, которое несут титры каждого экспортированного кадра — бледное, наклонное и "
    "повторяющееся, нарисованное под данными, чтобы не соперничать с ними. Относится и к "
    "видео, и к обложке, и к предпросмотру.",

    "書き出すすべてのフレームの背景に、斜めに繰り返し薄く記される名前です。データの下に描く"
    "ので、データの読み取りを邪魔しません。プレビューだけでなく動画とカバー画像にも入ります。",

    "내보내는 모든 프레임의 배경에 흐릿하고 비스듬히 반복되는 이름입니다. 데이터와 경쟁하지 "
    "않도록 데이터 아래에 그리며, 미리보기뿐 아니라 영상과 커버 이미지에도 적용됩니다.",

    "每一幀匯出的畫面背景上都會帶著這個名字：淡淡的、斜向重複，畫在數據之下，所以永遠不會和"
    "數據搶眼。預覽、影片與封面圖都有。",

    "每一帧导出的画面背景上都会带着这个名字：淡淡的、斜向重复，画在数据之下，所以永远不会和"
    "数据抢眼。预览、视频与封面图都有。",
]

# ---- 开关 -----------------------------------------------------------------------

TOGGLE = [
    "Sign exported frames", "Exportierte Bilder kennzeichnen",
    "Marcar los fotogramas exportados", "Signer les images exportées",
    "Contrassegnare i fotogrammi esportati", "Oznaczać eksportowane klatki",
    "Marcar os quadros exportados", "Označovat exportované snímky",
    "Dışa aktarılan kareleri imzala", "Подписывать экспортируемые кадры",
    "書き出すフレームに署名する", "내보내는 프레임에 표시하기",
    "為匯出的畫面加上標記", "为导出的画面加上标记",
]

# ---- 输入框 ---------------------------------------------------------------------

SAYS = [
    "What it says", "Was dort steht", "Qué dice", "Ce qu'il dit", "Cosa dice",
    "Co mówi", "O que diz", "Co říká", "Ne yazdığı", "Какой текст",
    "表示する名前", "표시할 이름", "寫什麼", "写什么",
]

# 十四份同一串：它是一个名字，不是一个词。见文件头。
PLACEHOLDER = ["周期留白"] * 14

# ---- 末尾提示 -------------------------------------------------------------------
#
# 三件事：为什么默认开、留空会怎样、关掉会怎样。前两件不说，用户会把「清空」当成「删掉水印」，
# 而它其实是回到默认名；第三件不说，用户会以为关掉只是变淡。

HINT = [
    "On by default: a video is posted somewhere that shows nothing of where it was "
    "made. Left blank it falls back to the name above; switched off, the frames carry "
    "nothing.",

    "Standardmäßig an: Ein Video landet irgendwo, das nichts darüber verrät, wo es "
    "entstanden ist. Leer gelassen gilt wieder der Name darüber; ausgeschaltet tragen "
    "die Bilder nichts.",

    "Activado por defecto: un vídeo se publica en un lugar que no dice nada de dónde se "
    "hizo. Si se deja vacío, vuelve al nombre de arriba; desactivado, los fotogramas no "
    "llevan nada.",

    "Activé par défaut : une vidéo est publiée quelque part qui ne dit rien d'où elle a "
    "été faite. Laissé vide, il reprend le nom ci-dessus ; désactivé, les images ne "
    "portent rien.",

    "Attivo per impostazione predefinita: un video finisce dove nulla dice da dove "
    "viene. Lasciato vuoto torna al nome sopra; disattivato, i fotogrammi non portano "
    "nulla.",

    "Domyślnie włączone: wideo trafia w miejsce, które nic nie mówi o tym, gdzie "
    "powstało. Puste wraca do nazwy powyżej; wyłączone — klatki nie niosą niczego.",

    "Ativado por padrão: um vídeo é publicado em algum lugar que não diz nada sobre onde "
    "foi feito. Deixado em branco, volta ao nome acima; desligado, os quadros não levam "
    "nada.",

    "Ve výchozím stavu zapnuto: video končí někde, kde nic neříká, kde vzniklo. Prázdné "
    "se vrací k výše uvedenému jménu; vypnuto — snímky nenesou nic.",

    "Varsayılan olarak açık: bir video, nerede üretildiğini hiç göstermeyen bir yerde "
    "yayımlanır. Boş bırakılırsa yukarıdaki ada döner; kapatıldığında kareler hiçbir şey "
    "taşımaz.",

    "Включено по умолчанию: видео попадает туда, где ничто не говорит, где оно сделано. "
    "Если оставить пустым, вернётся имя выше; при выключении кадры не несут ничего.",

    "既定でオンです。動画は、どこで作られたかを何も示さない場所に投稿されるものだからです。"
    "空にすれば上の名前に戻り、オフにすればフレームには何も入りません。",

    "기본적으로 켜져 있습니다. 영상은 어디서 만들어졌는지 아무것도 알려주지 않는 곳에 올라가기 "
    "때문입니다. 비워 두면 위의 이름으로 돌아가고, 끄면 프레임에 아무것도 들어가지 않습니다.",

    "預設開啟：影片會被發到一個完全看不出它是在哪裡做出來的地方。留空會回到上面的名字；關掉則"
    "畫面上什麼都不加。",

    "默认开启：视频会被发到一个完全看不出它是在哪里做出来的地方。留空会回到上面的名字；关掉则"
    "画面上什么都不加。",
]

ROWS = [
    ("SettingsWatermarkLabel.Text", LABEL),
    ("SettingsWatermarkNote.Text", NOTE),
    ("SettingsWatermarkToggle.Header", TOGGLE),
    ("SettingsWatermarkText.Header", SAYS),
    ("SettingsWatermarkText.PlaceholderText", PLACEHOLDER),
    ("SettingsWatermarkHint.Text", HINT),
]


def entry(key, value):
    """One resw row, with the value XML-escaped.

    A bare `&` is not legal XML and MakePri reports it as `PRI224`, naming the project file
    rather than the string that caused it.
    """
    safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'  <data name="{key}"><value>{safe}</value></data>\n'


def main():
    # The one value that must be identical in every file. Asserted rather than
    # trusted: a translated placeholder is a watermark that says something
    # different on each machine, and nothing in the build would complain.
    for tag in LANGS:
        assert PLACEHOLDER[LANGS.index(tag)] == "周期留白", tag

    for tag in LANGS:
        path = ROOT / tag / "Resources.resw"

        text = path.read_bytes().decode("utf-8-sig")

        if not text.endswith("\n"):
            text += "\n"

        lines = []

        for key, values in ROWS:
            assert len(values) == len(LANGS), f"{key}: {len(values)} values, expected {len(LANGS)}"

            lines.append(entry(key, values[LANGS.index(tag)]))

        # Idempotent: drop a key of the same base name wherever it already sits, then append.
        # The suffix is optional in the pattern because the two entry shapes coexist.
        for key, _ in ROWS:
            base = key.split(".")[0]

            text = re.sub(
                rf'  <data name="{re.escape(base)}(\.\w+)?"[^>]*>.*?</data>\n',
                "", text, flags=re.S)

        at = text.rfind("</root>")
        assert at > 0, f"{tag}: no </root>"

        text = text[:at] + "".join(lines) + text[at:]

        path.write_bytes(text.encode("utf-8-sig"))

        print(f"{tag}: +{len(lines)} keys")


if __name__ == "__main__":
    main()
