# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.11.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是订阅买下就当场生效、
卡片不再消失。那是真的，也已经上架；接着往后加，这一栏就成了两件事各说一半。

本版要说的也是两件事，而且它们是同一件事的两面：

- **曲线末端的数字不再被平台的按钮盖住。** 竖屏视频在手机上播放时，画面右侧约六分之一常年被
  头像、点赞、评论那一条占着。此前市值历程、定投计划、持仓收益三页都把末端的标注画到画面最右边，
  在手机上正好落在那条栏底下；而在应用里看却完全正常，因为应用里没有那套界面——**这正是它一直
  没被发现的原因**。现在三页都收在那条线以内。
- **不想要这个让位的话可以关掉。** 让位要花掉绘图区四分之一的宽度；发到没有那套界面的地方，或者
  宁可要宽度的人，三页各有一个开关把它收回来。

**不提实现方式。** 让位量是个小数而不是开关、它跟着窗口展开的同一个斜坡走、「整段铺满」与
「窗口滚动」在内部怎么分岔——那都是代码的事。用户能感知的只有两件事：数字会不会被盖住，以及
画面有多宽。把内部的措辞写进商店文案，等于让用户替我们查错。

**也不点控件的名字。** 开关和推进方式在各语言里拼法不同，抄错一处就是一句指着不存在的东西的话。
叙述里只说「有这样一个开关」「用滚动窗口推进时」，不引用界面上的字面名称。

**重音字母照写。** 德语的 ü/ä、法语的 é/ç、捷克的 ř/ž、波兰语的 ł/ż、土耳其语的 ğ/ı 是这个字
的一部分，不是装饰；为了「保险」把它们写成 u/a/e/c/r/z/l/g/i 等于在商店里挂一句拼错的德语。
文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

**脚本名由 manifest 的版本号算出 `10110`，不是取巧写成 `1110`。** `verify-docs.py` 把四段版本
号**全拼**当作文件名（`1.0.11.0` → 四段拼起来是 `10110`；写成 `1110` 是省掉了第三段的一位，那是
留给 `1.1.1.0` 的形状），算不出/找不到就大声失败。

用法：python tools\\port-store-listing-10110.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。两句话远够不着，但每次换文案都要算一遍最长的那一种语言 —— 上限是
# 按字符算的，德/法/意语一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**曲线末端的数字不再被平台那一条按钮盖住（竖屏视频右侧约
# 六分之一常年是头像、点赞和评论）；若不需要这个让位，三页各有一个开关把画面宽度收回来。**
# 用滚动窗口推进时，滚动途中照旧让位，只有最后展开成完整区间的那一段才放开，停住的那一帧与
# 一开始就画满整段完全一致。
NEWS = {
    "zh-Hans":
        "本版让曲线末端的数字不再被平台的按钮盖住。竖屏视频在手机上播放时，画面右侧约六分之一常年"
        "被头像、点赞和评论那一条占着；此前市值历程、定投计划、持仓收益三页的数字都画到画面最右边，"
        "在手机上正好落在下面。现在三页都把它们收在那条线以内，导出到短视频平台也不必再手工留白。"
        "若你的视频不落在有那套界面的地方，或者宁可要画面宽度，三页各多了一个开关：打开它，图就把"
        "这一段宽度收回来。用滚动窗口推进时，滚动途中照旧让位，到最后展开成完整区间的那一段才放开，"
        "停住的那一帧与一开始就画满整段完全一致。",
    "zh-Hant":
        "本版讓曲線末端的數字不再被平台的按鈕蓋住。直式影片在手機上播放時，畫面右側約六分之一常年"
        "被頭像、按讚和留言那一條佔著；此前市值歷程、定投計畫、持倉收益三頁的數字都畫到畫面最右邊，"
        "在手機上正好落在下面。現在三頁都把它們收在那條線以內，匯出到短影音平台也不必再手動留白。"
        "若你的影片不落在有那套介面的地方，或者寧可要畫面寬度，三頁各多了一個開關：打開它，圖就把"
        "這一段寬度收回來。用捲動視窗推進時，捲動途中照舊讓位，到最後展開成完整區間的那一段才放開，"
        "停住的那一幀與一開始就畫滿整段完全一致。",
    "en-US":
        "The figures at the leading end of a line no longer land under the platform's buttons. On a "
        "phone the right sixth of a vertical video is permanently taken by the avatar, the like button "
        "and the comment button, and the market-value, savings-plan and holdings pages all drew their "
        "end figures to the very edge of the frame — exactly under it. All three now keep them inside "
        "that line, so a video bound for a short-video platform needs no margin left by hand. If your "
        "video is not going somewhere with that interface, or you would rather have the width, each of "
        "the three pages has a switch that hands the width back to the chart. Advancing by a scrolling "
        "window, the scroll itself still keeps clear; the room is given up only across the closing "
        "stretch where the window opens into the whole range, and the frame the video stops on is "
        "exactly what a chart drawn over the whole range from the first frame looks like.",
    "ja":
        "折れ線の先頭に出す数値が、プラットフォームのボタンの下に置かれなくなりました。縦型動画を"
        "スマートフォンで再生すると、画面右側およそ六分の一はアバター、いいね、コメントのボタンに"
        "常に占有されます。これまで市值・積立・保有の三つのページはいずれも数値を画面の右端まで"
        "描いており、ちょうどその下に重なっていました。三ページとも数値をその線の内側に収めるように"
        "したため、短尺動画のプラットフォームへ書き出す際に手作業で余白を空ける必要はありません。"
        "そのような画面のない場所に出す場合や、横幅を優先したい場合は、三ページそれぞれに用意した"
        "切り替えでグラフにその分の幅を戻せます。スクロールする窓で進める場合、スクロール中は"
        "従来どおり内側に留まり、窓が全区間に開く終盤の伸びでだけ譲りを解きます。動画が止まる最後の"
        "一枚は、最初から全区間を描いたグラフと完全に一致します。",
    "ko":
        "선 끝에 붙는 숫자가 더 이상 플랫폼의 버튼 아래에 놓이지 않습니다. 휴대폰에서 세로 영상을 재생하면"
        " 화면 오른쪽 약 6분의 1은 프로필, 좋아요, 댓글 버튼이 늘 차지합니다. 그동안 시가총액·적립식·"
        "보유 수익 세 페이지 모두 숫자를 화면 오른쪽 끝까지 그렸고, 바로 그 아래에 겹쳤습니다. 세 페이지"
        " 모두 이제 숫자를 그 선 안쪽으로 거두었으므로, 숏폼 플랫폼으로 내보낼 때 여백을 직접 남길 필요가"
        " 없습니다. 그런 화면이 없는 곳에 올리거나 너비를 더 쓰고 싶다면, 세 페이지에 각각 마련된 스위치로"
        " 그래프에 그만큼의 폭을 돌려줄 수 있습니다. 스크롤되는 창으로 진행하면 스크롤하는 동안에는"
        " 종전처럼 안쪽에 머물고, 창이 전체 구간으로 열리는 마지막 구간에서만 양보를 풉니다. 영상이 멈추는"
        " 마지막 프레임은 처음부터 전체 구간을 그린 그래프와 정확히 일치합니다.",
    "de":
        "Die Zahlen am vorderen Ende einer Linie liegen nicht mehr unter den Schaltflächen der "
        "Plattform. Auf dem Telefon ist das rechte Sechstel eines Hochkant-Videos dauerhaft von "
        "Avatar, Gefällt-mir- und Kommentar-Schaltfläche besetzt, und die Seiten für Marktwert, "
        "Sparplan und Position zeichneten ihre Endzahlen bis an den äußersten Rand des Bildes — "
        "genau darunter. Alle drei halten sie nun innerhalb dieser Linie, sodass ein Video für eine "
        "Kurzvideo-Plattform keinen von Hand freigehaltenen Rand braucht. Geht das Video nicht an eine "
        "Oberfläche mit dieser Benutzeroberfläche, oder ist die Breite wichtiger, hat jede der drei "
        "Seiten eine Einstellung, die dem Diagramm diese Breite zurückgibt. Beim Vorrücken mit einem "
        "scrollenden Fenster bleibt das Scrollen selbst wie bisher innerhalb; der Verzicht wird erst "
        "auf der Schlussstrecke aufgegeben, auf der sich das Fenster zum gesamten Zeitraum öffnet, und "
        "das Bild, auf dem das Video anhält, entspricht genau einem Diagramm, das von der ersten "
        "Einstellung an den gesamten Zeitraum zeichnet.",
    "fr":
        "Les chiffres à l'extrémité avant d'une courbe ne passent plus sous les boutons de la "
        "plateforme. Sur un téléphone, le sixième droit d'une vidéo verticale est occupé en permanence "
        "par l'avatar, le bouton « j'aime » et le bouton de commentaire, et les pages de "
        "capitalisation, de plan d'épargne et de position dessinaient leurs chiffres jusqu'au bord "
        "même de l'image — exactement dessous. Les trois les gardent désormais en deçà de cette ligne : "
        "une vidéo destinée à une plateforme de courtes vidéos n'a plus besoin de marge réservée à la "
        "main. Si votre vidéo n'est pas destinée à une surface dotée de cette interface, ou si la "
        "largeur compte davantage, chacune des trois pages dispose d'un réglage qui rend cette largeur "
        "au graphique. Avec l'avancement par fenêtre défilante, le défilement lui-même reste en deçà "
        "comme avant ; la place n'est cédée que sur le dernier tronçon, celui où la fenêtre s'ouvre à "
        "toute la période, et l'image sur laquelle la vidéo s'arrête correspond exactement à un "
        "graphique tracé sur toute la période dès la première image.",
    "it":
        "I numeri all'estremità anteriore di una linea non finiscono più sotto i pulsanti della "
        "piattaforma. Sul telefono il sesto destro di un video verticale è occupato in permanenza "
        "dall'avatar, dal pulsante «mi piace» e da quello dei commenti, e le pagine della "
        "capitalizzazione, del piano di accumulo e della posizione disegnavano i loro numeri fino al "
        "bordo stesso del fotogramma — esattamente lì sotto. Tutte e tre li tengono ora al di qua di "
        "quella linea, così un video destinato a una piattaforma di brevi video non richiede più un "
        "margine lasciato a mano. Se il video non è destinato a una superficie con quella interfaccia, "
        "o se la larghezza conta di più, ciascuna delle tre pagine ha un'impostazione che restituisce "
        "quella larghezza al grafico. Avanzando con una finestra scorrevole, lo scorrimento stesso "
        "resta al di qua come prima; lo spazio si cede solo nell'ultimo tratto, quello in cui la "
        "finestra si apre su tutto il periodo, e il fotogramma su cui il video si ferma corrisponde "
        "esattamente a un grafico disegnato su tutto il periodo fin dalla prima immagine.",
    "es":
        "Las cifras del extremo delantero de una línea ya no quedan debajo de los botones de la "
        "plataforma. En un teléfono, el sexto derecho de un vídeo vertical está ocupado de forma "
        "permanente por el avatar, el botón de «me gusta» y el de comentarios, y las páginas de "
        "capitalización, plan de ahorro y posición dibujaban sus cifras hasta el borde mismo del "
        "fotograma, justo debajo. Las tres las mantienen ahora por detrás de esa línea, de modo que un "
        "vídeo destinado a una plataforma de vídeos cortos ya no necesita un margen reservado a mano. "
        "Si el vídeo no va a una superficie con esa interfaz, o si la anchura importa más, cada una de "
        "las tres páginas tiene un ajuste que devuelve esa anchura al gráfico. Al avanzar con una "
        "ventana deslizante, el desplazamiento en sí se mantiene por detrás como antes; el espacio se "
        "cede solo en el tramo final, aquel en que la ventana se abre a todo el periodo, y el "
        "fotograma en que el vídeo se detiene coincide exactamente con un gráfico dibujado sobre todo "
        "el periodo desde la primera imagen.",
    "pt-BR":
        "Os números na extremidade dianteira de uma linha não ficam mais sob os botões da plataforma. "
        "No telefone, o sexto direito de um vídeo vertical é ocupado permanentemente pelo avatar, pelo "
        "botão de curtir e pelo de comentários, e as páginas de valor de mercado, plano de aportes e "
        "posição desenhavam seus números até a borda mesma do quadro, logo abaixo. As três agora os "
        "mantêm aquém dessa linha, de modo que um vídeo destinado a uma plataforma de vídeos curtos não "
        "precisa mais de uma margem reservada à mão. Se o vídeo não vai para uma superfície com essa "
        "interface, ou se a largura importa mais, cada uma das três páginas tem uma opção que devolve "
        "essa largura ao gráfico. Avançando com uma janela rolante, a rolagem em si permanece aquém "
        "como antes; o espaço só é cedido no trecho final, aquele em que a janela se abre para todo o "
        "período, e o quadro em que o vídeo para coincide exatamente com um gráfico desenhado sobre "
        "todo o período desde a primeira imagem.",
    "pl":
        "Liczby na przednim końcu linii nie trafiają już pod przyciski platformy. Na telefonie prawa "
        "szósta część pionowego wideo jest stale zajęta przez awatar, przycisk polubienia i przycisk "
        "komentarza, a strony kapitalizacji, planu oszczędzania i pozycji rysowały swoje liczby aż do "
        "samej krawędzi kadru, czyli właśnie pod spodem. Wszystkie trzy trzymają je teraz przed tą "
        "linią, więc wideo przeznaczone na platformę krótkich filmów nie wymaga już marginesu "
        "zostawianego ręcznie. Jeśli wideo nie trafia na powierzchnię z takim interfejsem albo "
        "szerokość jest ważniejsza, każda z trzech stron ma ustawienie, które oddaje tę szerokość "
        "wykresowi. Przy przewijaniu okna samo przewijanie pozostaje przed linią jak dotąd; miejsce "
        "oddaje się dopiero na końcowym odcinku, na którym okno otwiera się na cały okres, a klatka, "
        "na której wideo się zatrzymuje, odpowiada dokładnie wykresowi narysowanemu od pierwszej "
        "klatki dla całego okresu.",
    "cs":
        "Čísla na předním konci čáry už nekončí pod tlačítky platformy. Na telefonu je pravá šestina "
        "svislého videa trvale obsazena avatarem, tlačítkem To se mi líbí a tlačítkem pro komentáře, "
        "a strany tržní hodnoty, spořicího plánu a pozice kreslily svá čísla až k samému okraji "
        "snímku, tedy právě pod ním. Všechny tři je nyní drží před touto čarou, takže video určené pro "
        "platformu krátkých videí už nepotřebuje okraj ponechaný ručně. Pokud video nemíří na plochu s "
        "takovým rozhraním nebo je šířka důležitější, má každá ze tří stran nastavení, které tuto "
        "šířku grafu vrací. Při postupu posuvným oknem zůstává samotný posuv před čarou jako dříve; "
        "místo se uvolňuje až v závěrečném úseku, v němž se okno rozevře na celé období, a snímek, na "
        "kterém video zastaví, odpovídá přesně grafu nakreslenému od prvního snímku pro celé období.",
    "ru":
        "Цифры у переднего конца линии больше не оказываются под кнопками платформы. На телефоне правая "
        "шестая часть вертикального видео постоянно занята аватаром, кнопкой «Нравится» и кнопкой "
        "комментария, а страницы капитализации, плана накоплений и позиции рисовали свои числа до "
        "самого края кадра, то есть как раз под ними. Теперь все три держат их за этой линией, поэтому "
        "видео, предназначенное для платформы коротких роликов, не требует поля, оставленного вручную. "
        "Если видео не попадает на поверхность с таким интерфейсом или важнее ширина, у каждой из трёх "
        "страниц есть параметр, который возвращает эту ширину графику. При прокручивающемся окне сама "
        "прокрутка остаётся за линией, как прежде; место уступается только на заключительном отрезке, "
        "где окно раскрывается на весь период, и кадр, на котором видео останавливается, точно "
        "совпадает с графиком, построенным с первого кадра за весь период.",
    "tr":
        "Çizginin ön ucundaki sayılar artık platformun düğmelerinin altına düşmüyor. Telefonda dikey "
        "bir videonun sağ altıda biri sürekli olarak avatar, beğeni düğmesi ve yorum düğmesiyle "
        "doludur; piyasa değeri, birikim planı ve pozisyon sayfaları sayıları karenin ta kenarına "
        "kadar çiziyordu, yani tam olarak onların altına. Üçü de sayıları artık bu çizginin "
        "gerisinde tutuyor, böylece kısa video platformlarına giden bir videoda elle boşluk bırakmak "
        "gerekmiyor. Videonuz böyle bir arayüzü olan bir yere gitmiyorsa ya da genişlik daha "
        "önemliyse, üç sayfanın her birinde bu genişliği grafiğe geri veren bir ayar var. Kayan "
        "pencereyle ilerlerken kaymanın kendisi eskisi gibi çizginin gerisinde kalır; yer yalnızca "
        "pencerenin tüm aralığa açıldığı son bölümde bırakılır ve videonun durduğu kare, ilk kareden "
        "itibaren tüm aralığı çizen bir grafikle birebir örtüşür.",
}


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # 各文件保持自己的行尾：store-listing.md 是 CRLF。
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
    sys.exit(main())
