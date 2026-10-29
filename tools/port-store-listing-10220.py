# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.22.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 1.0.21.0 那一栏已经交上去了，
所以本版另起一条，只说它之后的改动。1.0.21 之后这台机器上落地的两件事，都在同一个页面上：

- 双屏页终于画自己的标题：行是正确的高度，字从来没画上去。字补上之后，样式跟着设置页里
  那一份全局标题设置（纯色 / 金属 / 浮雕＋取色），与其它页同源。
- 双屏页的下边距滑杆接进画面：竖向行原本全锚在画面顶部，滑杆只改数字不动画面。改成上下
  双轨之后 150—420 全程有效，默认那一档的画面和从前一样。

**只说用户能感知的那半句**，代码细节（TitleBlock.Draw、Row 的双轨重映射、CreditLine）不写。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md
是 **CRLF 无 BOM**，写完照原样写回。脚本名由 manifest 的版本号算出 `10220`。

用法：python tools\\port-store-listing-10220.py      （跑第二遍应当是「改了 0 条」）
"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。
LIMIT = 1500

NEWS = {
    "zh-Hans":
        "本版补齐「持仓·大盘 双屏」页的两处旧账。其一，这一页终于画自己的标题了：行的高度早就留好，"
        "字却从头到尾没画上去——现在连换行一起补上，字体样式（纯色、金属、浮雕）和颜色跟着你在设置页"
        "挑的那一份全局标题设置，不必在这一页再调一遍。其二，下边距滑杆真正接进了画面：以前这一页的"
        "每一行都只在画面顶部生根，滑杆挪半天只是改了一个数字、图画一像素都没动。现在竖着排的那些行"
        "上下各有抓手——上头顶着标题和上边距，下头跟着下边距走，中间按比例舒展或收拢，150 到 420 全"
        "程有效；默认的那一档画面和从前一模一样。",
    "zh-Hant":
        "本版補齊「持倉·大盤 雙屏」頁的兩處舊帳。其一，這一頁終於畫自己的標題了：行的高度早就留好，"
        "字卻從頭到尾沒畫上去——現在連換行一起補上，字體樣式（純色、金屬、浮雕）和顏色跟著你在設定頁"
        "挑的那一份全域標題設定，不必在這一頁再調一次。其二，下邊界滑桿真正接進了畫面：以前這一頁的"
        "每一行都只在畫面頂端生根，滑桿拉半天只是改了一個數字、圖畫一像素都沒動。現在豎著排的那些行"
        "上下各有抓手——上頭頂著標題和上邊界，下頭跟著下邊界走，中間按比例舒展或收攏，150 到 420 全"
        "程有效；預設的那一檔畫面和從前一模一樣。",
    "en-US":
        "This release settles two debts on the Book & Board Split page. First, that page now draws "
        "its own title: the rows were always spaced for it, but the words were never put on the "
        "canvas — they are now, wrapping included, taking their look (plain, gilded or engraved) and "
        "colour from the one set of title settings you pick for the whole app, so nothing has to be "
        "chosen twice. Second, the bottom margin slider reaches the picture: every row on that page "
        "used to take root at the top of the frame and nowhere else, so dragging the slider moved a "
        "number and not one pixel. The rows now have a hold at each end — the title and top margin "
        "above, the bottom margin below — opening out or closing up between them, live across the "
        "whole 150 to 420 range, with the default value drawing exactly what it drew before.",
    "ja":
        "今回の更新は「資産と市場の分割表示」ページの二つの宿題を片づけます。ひとつはタイトルです。"
        "行の高さは最初から空けてあったのに、文字は一度も描かれていませんでした。折り返しも含めて描く"
        "ようになり、書体（単色・金属・浮き彫り）と色は設定ページで選んだアプリ全体のタイトル設定を"
        "そのまま使います。このページで改めて選び直す必要はありません。もうひとつは下マージンのス"
        "ライダーです。このページの行はすべて画面の上辺だけで固定されていたため、いくら動かしても数字が"
        "変わるだけで絵は一画素も動きませんでした。行は両端で支えられるようになりました。上はタイトルと"
        "上マージン、下は下マージンです。その間は比率を保ったまま伸び縮みし、150 から 420 までの全域が"
        "有効になりました。既定値の絵は以前とまったく同じです。",
    "ko":
        "이번 업데이트는 「계좌·시장 분할」 페이지의 오래된 빚 두 가지를 갚습니다. 하나는 제목입니다."
        " 줄 높이는 처음부터 비워 두었지만 글자는 한 번도 그려지지 않았습니다. 줄바꿈까지 이제 그리며,"
        " 글꼴(단색·금속·양각)과 색은 설정 페이지에서 고른 앱 전체 제목 설정을 그대로 따릅니다. 이"
        " 페이지에서 다시 고를 필요는 없습니다. 다른 하나는 아래쪽 여백 슬라이더입니다. 이 페이지의 모든"
        " 줄이 화면의 위쪽에만 뿌리를 두고 있어, 아무리 움직여도 숫자만 바뀌고 그림은 한 픽셀도 움직이지"
        " 않았습니다. 이제 줄은 양끝에서 붙잡힙니다. 위는 제목과 위쪽 여백, 아래는 아래쪽 여백입니다."
        " 그 사이는 비율을 지키며 늘어나고 오므라들어 150부터 420까지 전 구간이 동작합니다. 기본값의"
        " 그림은 이전과 한 치도 다르지 않습니다.",
    "de":
        "Dieses Release begleicht zwei alte Schulden der Seite Depot & Markt geteilt. Erstens zeichnet "
        "diese Seite nun ihre eigene Überschrift: Die Zeilen waren von Anfang an dafür freigehalten, "
        "die Wörter aber nie auf die Fläche gesetzt — das geschieht jetzt, Zeilenumbruch inbegriffen, "
        "und Schriftart (einfarbig, metallisch oder graviert) sowie Farbe nimmt sie aus denselben "
        "Titeleinstellungen, die du in den Einstellungen für die ganze Anwendung wählst. Nichts muss "
        "hier ein zweites Mal eingestellt werden. Zweitens erreicht der Schieber für den unteren Rand "
        "endlich das Bild: Jede Zeile dieser Seite war bisher nur am oberen Rahmen verankert, also "
        "bewegte das Ziehen eine Zahl und keinen einzigen Pixel. Die Zeilen haben nun an beiden Enden "
        "Halt — oben Titel und oberer Rand, unten der untere Rand — und dehnen oder stauchen sich "
        "dazwischen im Verhältnis, über den ganzen Bereich von 150 bis 420. Bei der Voreinstellung "
        "entsteht genau das Bild von zuvor.",
    "fr":
        "Cette version règle deux vieilles dettes de la page Portefeuille & marché partagés. D'abord, "
        "cette page dessine enfin son propre titre : les lignes lui étaient réservées depuis le "
        "départ, mais les mots n'ont jamais été posés sur l'image — c'est fait maintenant, retour à la "
        "ligne compris, et la police (uni, doré ou gravé) comme la couleur viennent des réglages de "
        "titre que tu choisis une fois pour toute l'application. Rien n'est à régler deux fois ici. "
        "Ensuite, le curseur de marge basse atteint enfin le dessin : chaque ligne de cette page "
        "n'était ancrée qu'au bord supérieur, si bien que le tirer ne bougeait qu'un chiffre et pas un "
        "seul pixel. Les lignes tiennent désormais par les deux bouts — en haut le titre et la marge "
        "haute, en bas la marge basse — et s'étirent ou se resserrent entre les deux à proportion, sur "
        "toute la plage de 150 à 420. À la valeur par défaut, l'image est exactement celle d'avant.",
    "it":
        "Questa versione salda due debiti antichi della pagina Portafoglio e mercato divisi. Primo: la "
        "pagina ora disegna il proprio titolo. Le righe erano tenute libere dall'inizio, ma le parole "
        "non sono mai state scritte — ora lo sono, andata a capo compresa, e il carattere (tinta unita, "
        "dorato o inciso) e il colore arrivano dalle stesse impostazioni di titolo che scegli una volta "
        "per tutta l'applicazione: qui non c'è nulla da regolare due volte. Secondo: il cursore del "
        "margine inferiore raggiunge finalmente il disegno. Ogni riga di questa pagina era ancorata "
        "solo al bordo superiore, così spostarlo cambiava un numero e non un pixel. Ora le righe sono "
        "tenute da entrambi i capi — sopra il titolo e il margine alto, sotto il margine basso — e si "
        "aprono o si stringono in proporzione fra i due, su tutta la gamma da 150 a 420. Al valore "
        "predefinito il disegno è esattamente quello di prima.",
    "es":
        "Esta versión salda dos deudas antiguas de la página Cartera y mercado divididos. Primero, esa "
        "página por fin dibuja su propio título: las líneas estaban reservadas desde el principio, "
        "pero las palabras nunca llegaron al lienzo — ya están, con el salto de línea incluido, y la "
        "tipografía (liso, dorado o grabado) y el color salen de los mismos ajustes de título que "
        "eligues una vez para toda la aplicación, sin nada que volver a ajustar aquí. Segundo, la "
        "barra del margen inferior por fin alcanza el dibujo: cada línea de esa página solo echaba "
        "raíces en el borde superior, así que moverla cambiaba un número y ni un solo píxel. Ahora las "
        "líneas se sujetan por los dos extremos — arriba el título y el margen superior, abajo el "
        "margen inferior — y se abren o se cierran entre ambos a escala, en todo el rango de 150 a 420. "
        "Con el valor predeterminado el dibujo es exactamente el de antes.",
    "pt-BR":
        "Esta versão quita duas dívidas antigas da página Carteira e mercado divididos. Primeiro, essa "
        "página finalmente desenha o próprio título: as linhas estavam reservadas desde o começo, mas "
        "as palavras nunca foram para o quadro — agora vão, com a quebra de linha incluída, e a "
        "tipografia (lisa, dourada ou gravada) e a cor vêm dos mesmos ajustes de título que você escolhe "
        "uma vez para todo o aplicativo, sem nada para regular duas vezes aqui. Segundo, a barra da "
        "margem inferior finalmente alcança o desenho: cada linha dessa página criava raízes apenas na "
        "borda de cima, então arrastá-la mudava um número e nenhum pixel. Agora as linhas se apoiam nos "
        "dois extremos — em cima o título e a margem superior, embaixo a margem inferior — e se abrem ou "
        "se fecham entre os dois, em toda a faixa de 150 a 420. No valor padrão o desenho é exatamente o "
        "de antes.",
    "pl":
        "To wydanie spłaca dwa stare długi strony Portfel i rynek na pół. Po pierwsze, ta strona wreszcie "
        "rysuje własny tytuł: wiersze były dla niego od początku odłożone, ale słowa nigdy nie trafiły na "
        "obraz — teraz trafiają, z łamaniem wiersza, a krój (gładki, złocony lub grawerowany) i kolor "
        "biorą się z tych samych ustawień tytułu, które wybierasz raz dla całej aplikacji. Tu nie trzeba "
        "niczego ustawiać powtórnie. Po drugie, suwak dolnego marginesu wreszcie dosięga rysunku: każdy "
        "wiersz tej strony miał korzenie tylko przy górnej krawędzi, więc przesunięcie zmieniało liczbę, "
        "a nie ani jeden piksel. Wiersze trzymają się teraz obu końców — u góry tytuł i margines górny, u "
        "dołu margines dolny — i rozwierają się lub zwierają między nimi proporcjonalnie, w całym "
        "zakresie od 150 do 420. Przy wartości domyślnej rysunek jest dokładnie taki jak wcześniej.",
    "cs":
        "Tato verze vyrovnává dva staré dluhy strany Portfolio a trh napůl. Zaprvé: ta strana si konečně "
        "kreslí vlastní nadpis. Řádky pro něj byly od začátku uvolněné, ale slova se na plátno nikdy "
        "nedostala — teď ano, i se zalamováním, a písmo (hladké, zlacené nebo ryté) i barva přicházejí ze "
        "stejného nastavení nadpisů, které volíš jednou pro celou aplikaci. Zde není co nastavovat "
        "podruhé. Zadruhé: jezdec dolního okraje konečně dosáhne obrázku. Každý řádek té strany dřív "
        "zakořenil jen u horní hrany, takže táhnout znamenalo změnit číslo a ani jeden pixel. Řádky se teď "
        "drží na obou koncích — nahoře nadpis a horní okraj, dole dolní okraj — a mezi nimi se úměrně "
        "roztahují či stahují v celém rozsahu 150 až 420. Při výchozí hodnotě je obrázek přesně takový "
        "jako dřív.",
    "ru":
        "Этот выпуск закрывает два старых долга страницы «Портфель и рынок пополам». Во-первых, страница "
        "наконец рисует собственный заголовок: строки под него были оставлены с самого начала, но слова "
        "ни разу не были написаны — теперь написаны, вместе с переносом, а начертание (гладкое, золотое "
        "или гравированное) и цвет берутся из той самой настройки заголовков, которую ты выбираешь один "
        "раз для всего приложения. Здесь нечего настраивать дважды. Во-вторых, ползунок нижнего поля "
        "наконец доходит до рисунка: каждая строка этой страницы пускала корни только у верхнего края, "
        "поэтому сдвиг менял число и ни одного пикселя. Теперь строки держатся за оба конца — сверху "
        "заголовок и верхнее поле, снизу нижнее поле — и раскрываются или сжимаются между ними "
        "пропорционально, во всём диапазоне от 150 до 420. При значении по умолчанию рисунок в точности "
        "такой же, как прежде.",
    "tr":
        "Bu sürüm, Portföy ve Piyasa bölünmüş sayfasının iki eski borcunu kapatıyor. Birincisi: sayfa "
        "artık kendi başlığını çiziyor. Satırlar en başından beri ona ayrılmıştı ama sözcükler hiç tuvale "
        "yazılmadı — şimdi yazılıyor, satır kaydırmasıyla birlikte; yazı tipi (düz, altın veya oyma) ve "
        "renk, tüm uygulama için bir kez seçtiğin başlık ayarlarından geliyor, burada ikinci kez ayar "
        "yapman gerekmiyor. İkincisi: alt kenar boşluğu kaydırıcısı sonunda çizime ulaştı. Bu sayfanın her "
        "satırı kökünü yalnızca üst kenara salmıştı, bu yüzden kaydırmak bir sayıyı değiştiriyor, tek bir "
        "pikseli değil. Satırlar artık iki ucundan tutunuyor — üstte başlık ve üst kenar boşluğu, altta alt "
        "kenar boşluğu — ve arada 150’den 420’ye tüm aralıkta orana göre açılıp kapanıyor. Öntanımlı "
        "değerde çizim tıpkı eskisi gibi.",
}


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
        return 1

    if sorted(NEWS) != sorted(LANGS):
        print("× 文案漏了语言：%s" % sorted(set(LANGS) - set(NEWS)))
        return 1

    changed = 0

    for n, lang in enumerate(LANGS):
        start = heads[n]
        end = heads[n + 1] if n + 1 < len(heads) else len(lines)
        subs = [i for i in range(start, end) if lines[i].startswith("### ")]

        if len(subs) < 2:
            print(f"× {lang}: 只数到 {len(subs)} 个小标题")
            return 1

        at = subs[1] + 1       # 「此版本的新增功能」下面的正文

        while at < end and not lines[at].strip():
            at += 1

        text = NEWS[lang]

        if lines[at] == text:
            print(f"· {lang}: （已是本版，{len(text)} 字）")
            continue

        lines[at] = text
        changed += 1
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: 「{lines[subs[1]][4:]}」改写（{len(text)} 字）")

    if changed:
        LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))

    longest = max((len(NEWS[l]), l) for l in LANGS)
    over = [(l, len(NEWS[l])) for l in LANGS if len(NEWS[l]) > LIMIT]

    if over:
        print(f"\n！超过商店 {LIMIT} 字上限：{over}")
        return 1

    print(f"\n最长的 {longest[1]} {longest[0]} 字，都在 {LIMIT} 以内")
    print(f"改了 {changed} 条（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
