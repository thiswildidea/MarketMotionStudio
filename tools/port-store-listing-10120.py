# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.12.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 上一版那一栏说的是曲线末端的数字不再被
平台的按钮盖住。那是真的，也已经上架；接着往后加，这一栏就成了两件事各说一半。

本版要说三件事，都是用户在画面上看得见的：

- **K 线页可以一次比较多个标的。** 此前在清单上多选几只，画面什么也不做。
- **多只时可以选择怎么排布**：都画在一张图上，或者每只一张图、上下排列（最多三只）。
  两种排布最后都收在同一排卡片上，写明每只涨了百分之多少、涨跌了多少。
- **数字不再被手机上的那条按钮栏盖住** —— 这次是五页底部的数字卡片，以及分钟档表头改读
  当日涨跌幅（涨跌从前一个交易日的收盘价算起，而不是当天开盘）。

**不提实现方式。** 縱轴是并集还是交集、第四只是从轴上掉下去还是只是不画、让位量为什么是小数
而不是开关 —— 那都是代码的事。用户能感知的只有：几只画在一起、怎么排、最后那排卡片写的什么、
数字会不会被盖住。把内部的措辞写进商店文案，等于让用户替我们查错。

**也不点控件的名字。** 开关和下拉在各语言里拼法不同，抄错一处就是一句指着不存在的东西的话。
叙述里只说「可以选」「有一个开关」，不引用界面上的字面名称。

**重音字母照写。** 德语的 ü/ä、法语的 é/ç、捷克的 ř/ž、波兰语的 ł/ż、土耳其语的 ğ/ı 是这个字
的一部分，不是装饰；为了「保险」把它们写成 u/a/e/c/r/z/l/g/i 等于在商店里挂一句拼错的德语。
文件是 UTF-8，Python 3 源码默认就是 UTF-8，没有需要绕开的编码问题。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md 是
**CRLF 无 BOM**，写完照原样写回（剥掉 `\r` 比对，否则每次都差一个 `\r`，幂等就成了空话）。

**脚本名由 manifest 的版本号算出 `10120`，不是取巧写成 `1120`。** `verify-docs.py` 把四段版本
号**全拼**当作文件名（`1.0.12.0` → 四段拼起来是 `10120`；写成 `1120` 是省掉了第三段的一位，那是
留给 `1.1.2.0` 的形状），算不出/找不到就大声失败。

用法：python tools\\port-store-listing-10120.py      （跑第二遍应当是「改了 0 条」）
"""

import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。三件事比上一版的两件事长，每次换文案都要算一遍最长的那一种语言 ——
# 上限是按字符算的，德/意/葡一句能顶到中文的三倍长。
LIMIT = 1500

# 本版那一句。十四种语言同一种说法：**K 线页可以一次比较多个标的，排布可选同一张图或每只一张图
# （上下排列，最多三只，多出来的会点名），两种排布最后都收在一排写着涨幅与涨跌额的卡片上；涨跌
# 改从前一个交易日的收盘价算起，分钟档表头也随之读当日涨跌幅；五页底部的数字卡片不再画到画面
# 最右边，不再落在手机那条按钮栏下面。**
NEWS = {
    "zh-Hans":
        "本版 K 线页可以一次比较多个标的：多选几只就画在一起，每只从自己的起点算涨跌幅——价格不同的"
        "标的没有共同的纵轴。排布可选「同一张图」，也可选每只一张图、上下排列，最多三只，多出来的会"
        "点名说明；两种排布最后都有一排卡片，写明每只涨了百分之多少、涨跌了多少。涨跌改从前一个交易"
        "日的收盘价算起：一天的涨跌本来就是相对昨收，不是相对当天开盘；分钟档的表头也因此读当日涨跌"
        "幅。另外，手机上看竖屏视频时画面右侧约六分之一常年是头像、点赞和评论那一条，此前 K线、成交"
        "额、日内、定投、持仓五页底部的数字卡片都画到画面最右边，正好落在下面；现在五页都收在那条线"
        "以内。若视频不落在有那套界面的地方，K线页可以把这段宽度收回来。",
    "zh-Hant":
        "本版 K 線頁可以一次比較多個標的：多選幾檔就畫在一起，每檔從自己的起點算漲跌幅——價格不同的"
        "標的沒有共同的縱軸。排布可選「同一張圖」，也可選每檔一張圖、上下排列，最多三檔，多出來的會"
        "點名說明；兩種排布最後都有一排卡片，寫明每檔漲了百分之多少、漲跌了多少。漲跌改從前一個交易"
        "日的收盤價算起：一天的漲跌本來就是相對昨收，不是相對當天開盤；分鐘檔的表頭也因此讀當日漲跌"
        "幅。另外，手機上看直式影片時畫面右側約六分之一常年是頭像、按讚和留言那一條，此前 K線、成交"
        "額、日內、定期定額、持倉五頁底部的數字卡片都畫到畫面最右邊，正好落在下面；現在五頁都收在那"
        "條線以內。若影片不落在有那套介面的地方，K線頁可以把這段寬度收回來。",
    "en-US":
        "This version lets the candle page compare several instruments at once: pick more than one and "
        "they are drawn together, each measured as a change from its own starting point, because "
        "instruments at different prices share no axis. The layout is either every instrument on one "
        "chart, or one chart each, stacked — three at most, and any beyond that are named rather than "
        "silently left out. Either way the animation ends on a row of cards giving each instrument's "
        "percentage and the amount it moved. Change is now measured from the previous session's close, "
        "which is what a day's move means — not from the day's own opening — and the minute view's "
        "headline reads the day's move for the same reason. Separately: on a phone the right sixth of a "
        "vertical video is permanently the avatar, the like button and the comment button, and the row "
        "of figures at the foot of the candle, turnover, intraday, savings-plan and holdings pages ran "
        "to the very edge of the frame, exactly under it. All five now keep it inside that line, and the "
        "candle page hands the width back when a video is not going anywhere with that interface.",
    "ja":
        "今回のバージョンでは、ローソク足ページで複数の銘柄を一度に比較できます。複数を選ぶと同じ画面"
        "に描かれ、価格帯の違う銘柄に共通の軸はないため、それぞれが自分の始点からの騰落率で描かれま"
        "す。並べ方は「1枚のチャート」と「銘柄ごとに1枚、上下に並べる」から選べ、後者は最大3銘柄まで"
        "で、それ以上は名前を挙げて説明します。どちらの場合も最後にカードが1列並び、銘柄ごとの騰落率"
        "と価格の増減が示されます。また、騰落の基準を前営業日の終値に変更しました。一日の値動きは当日"
        "の始値ではなく前日終値との差だからです。分足のヘッダーも同じ理由で当日の値動きを示します。"
        "さらに、スマートフォンで縦型動画を見るとき画面右側の約六分の一は常にアイコン・いいね・コメン"
        "トの帯に覆われますが、ローソク足、売買代金、日内、積立、保有の5ページ下部の数値カードは画面"
        "の右端まで描かれており、まさにその下に置かれていました。5ページともその線の内側に収めました。"
        "その帯のない場所に投稿する場合は、ローソク足ページでこの幅を取り戻せます。",
    "ko":
        "이번 버전에서는 캔들 페이지에서 여러 종목을 한 번에 비교할 수 있습니다. 여러 개를 고르면 한 화면"
        "에 함께 그려지고, 가격대가 다른 종목에는 공통 축이 없으므로 각 종목이 자기 시작점からの 등락률로"
        " 그려집니다. 배치는 「한 장의 차트」와 「종목마다 한 장, 위아래로 배치」중에서 고를 수 있고, "
        "후자는 최대 3종목까지이며 넘치는 종목은 이름을 밝힙니다. 두 방식 모두 마지막에 카드 한 줄이 놓여"
        " 종목별 등락률과 가격 변동액을 보여줍니다. 또한 등락의 기준을 직전 거래일 종가로 바꿨습니다. "
        "하루의 등락은 당일 시가가 아니라 전일 종가와의 차이이기 때문입니다. 분 단위 차트의 머리글도 같은"
        " 이유로 당일 등락을 보여줍니다. 아울러 휴대폰에서 세로 영상을 볼 때 화면 오른쪽 약 6분의 1은 늘 "
        "프로필·좋아요·댓글 띠가 차지하는데, 캔들·거래대금·일중·적립·보유 다섯 페이지 아래쪽의 숫자 "
        "카드는 화면 맨 오른쪽까지 그려져 바로 그 아래에 놓여 있었습니다. 다섯 페이지 모두 그 선 안쪽으로"
        " 옮겼습니다. 그런 띠가 없는 곳에 올릴 때는 캔들 페이지에서 이 폭을 되돌릴 수 있습니다.",
    "de":
        "Diese Version lässt die Kerzen-Seite mehrere Werte auf einmal vergleichen: Wählt man mehrere, "
        "werden sie gemeinsam gezeichnet, jeder als Veränderung ab seinem eigenen Startpunkt, denn Werte "
        "mit unterschiedlichen Kursen teilen keine Achse. Die Anordnung ist wählbar: alle in einem "
        "Diagramm, oder ein eigenes Diagramm je Wert, untereinander, höchstens drei; weitere werden "
        "namentlich genannt statt stillschweigend weggelassen. Beide enden auf einer Kartenreihe, die je "
        "Wert die Prozentzahl und den Betrag nennt. Die Veränderung wird nun ab dem Schlusskurs des "
        "vorherigen Handelstags gemessen — eine Tagesveränderung ist die zum Schlusskurs des Vortags, "
        "nicht zum eigenen Eröffnungskurs — und die Überschrift der Minutenansicht liest deshalb "
        "ebenfalls die Veränderung des Tages. Außerdem: Auf dem Telefon belegt das rechte Sechstel eines "
        "senkrechten Videos dauerhaft die Leiste mit Profilbild, Gefällt-mir-Schaltfläche und "
        "Kommentarschaltfläche; die Zahlenkarten am Fuß der Seiten Kerzen, Umsatz, Intraday, Sparplan und "
        "Position reichten bisher bis zum äußersten Rand des Bildes und lagen genau darunter. Alle fünf "
        "bleiben nun innerhalb dieser Linie, und für Videos ohne solche Leiste gibt die Kerzen-Seite die "
        "Breite zurück.",
    "fr":
        "Cette version permet à la page Chandeliers de comparer plusieurs instruments à la fois : "
        "choisissez-en plusieurs et ils sont tracés ensemble, chacun mesuré depuis son propre point de "
        "départ, car des instruments à des cours différents n'ont pas d'axe commun. La disposition se "
        "choisit : tous sur un même graphique, ou un graphique par instrument, empilés, trois au maximum "
        "— les suivants sont nommés au lieu d'être omis en silence. Dans les deux cas, l'animation se "
        "termine sur une rangée de cartes donnant, pour chacun, le pourcentage et le montant. La "
        "variation se mesure désormais depuis la clôture de la séance précédente : la variation d'une "
        "journée se mesure au cours de clôture de la veille, pas à l'ouverture du jour — et l'en-tête de "
        "la vue minutes lit donc lui aussi la variation du jour. Par ailleurs, sur un téléphone, le "
        "sixième droit d'une vidéo verticale est occupé en permanence par la barre de l'avatar, du bouton "
        "J'aime et du bouton Commentaire ; les cartes de chiffres au bas des pages Chandeliers, Volume "
        "d'échanges, Intrajournalier, Plan d'épargne et Position allaient jusqu'au bord même du cadre, "
        "c'est-à-dire exactement dessous. Les cinq restent désormais en deçà de cette ligne, et la page "
        "Chandeliers rend la largeur pour une vidéo qui ne va pas là où cette barre existe.",
    "it":
        "Questa versione permette alla pagina Candele di confrontare più strumenti insieme: scegliendone "
        "diversi vengono disegnati insieme, ciascuno misurato dal proprio punto di partenza, perché "
        "strumenti con prezzi diversi non hanno un asse comune. La disposizione si sceglie: tutti in un "
        "grafico, oppure un grafico per strumento, impilati, al massimo tre — quelli in più sono indicati "
        "per nome invece di essere omessi in silenzio. In entrambi i casi l'animazione si chiude su una "
        "fila di schede che riporta, per ciascuno, la percentuale e l'importo. La variazione ora si "
        "misura dalla chiusura della seduta precedente: la variazione di una giornata si misura rispetto "
        "alla chiusura del giorno prima, non all'apertura del giorno — e per lo stesso motivo "
        "l'intestazione della vista a minuti legge la variazione del giorno. Inoltre, sul telefono il "
        "sesto destro di un video verticale è occupato in permanenza dalla barra con l'immagine del "
        "profilo, il pulsante Mi piace e il pulsante Commento; le schede di cifre in fondo alle pagine "
        "Candele, Volumi, Intraday, Piano di accumulo e Posizione arrivavano fino al bordo stesso del "
        "fotogramma, cioè esattamente sotto. Tutte e cinque restano ora entro quella linea, e la pagina "
        "Candele restituisce la larghezza per i video che non vanno dove quella barra c'è.",
    "es":
        "Esta versión permite que la página de Velas compare varios instrumentos a la vez: al elegir "
        "varios se dibujan juntos, cada uno medido desde su propio punto de partida, porque instrumentos "
        "con precios distintos no comparten eje. La disposición se elige: todos en un gráfico, o un "
        "gráfico por instrumento, apilados, tres como máximo — los que sobran se indican por su nombre en "
        "lugar de omitirse en silencio. En ambos casos la animación termina en una fila de tarjetas con "
        "el porcentaje y el importe de cada uno. La variación se mide ahora desde el cierre de la sesión "
        "anterior: la variación de un día se mide respecto al cierre de la víspera, no respecto a la "
        "apertura del día — y por lo mismo el encabezado de la vista de minutos lee también la variación "
        "del día. Además, en el teléfono el sexto derecho de un vídeo vertical lo ocupa siempre la barra "
        "del avatar, del botón Me gusta y del botón de comentarios; las tarjetas de cifras al pie de las "
        "páginas Velas, Volumen, Intradía, Plan de ahorro y Posición llegaban hasta el mismo borde del "
        "fotograma, es decir, justo debajo. Las cinco se quedan ahora dentro de esa línea, y la página de "
        "Velas devuelve el ancho para los vídeos que no van a un sitio con esa barra.",
    "pt-BR":
        "Esta versão permite que a página de Candles compare vários instrumentos de uma vez: ao escolher "
        "vários, eles são desenhados juntos, cada um medido a partir do seu próprio ponto de partida, "
        "porque instrumentos com preços diferentes não compartilham um eixo. O layout pode ser escolhido: "
        "todos em um gráfico, ou um gráfico por instrumento, empilhados, no máximo três — os excedentes "
        "são indicados pelo nome em vez de serem omitidos em silêncio. Nos dois casos a animação termina "
        "em uma fileira de cartões com o percentual e o valor de cada um. A variação agora é medida a "
        "partir do fechamento da sessão anterior: a variação de um dia se mede em relação ao fechamento "
        "da véspera, não à abertura do dia — e pelo mesmo motivo o cabeçalho da vista de minutos também "
        "lê a variação do dia. Além disso, no telefone o sexto direito de um vídeo vertical é ocupado "
        "permanentemente pela barra do avatar, do botão de curtida e do botão de comentário; os cartões "
        "de números no rodapé das páginas Candles, Volume, Intraday, Plano de aportes e Posição iam até a "
        "própria borda do quadro, ou seja, exatamente abaixo. As cinco agora ficam dentro dessa linha, e "
        "a página de Candles devolve a largura para os vídeos que não vão a um lugar com essa barra.",
    "pl":
        "Ta wersja pozwala stronie Świece porównywać kilka instrumentów naraz: po wybraniu kilku są "
        "rysowane razem, każdy mierzony od własnego punktu startowego, bo instrumenty o różnych cenach nie "
        "mają wspólnej osi. Układ wybiera się: wszystkie na jednym wykresie albo osobny wykres dla każdego, "
        "jeden pod drugim, najwyżej trzy — pozostałe są wymienione z nazwy, a nie pominięte po cichu. W obu "
        "przypadkach animacja kończy się rzędem kart z procentem i kwotą dla każdego. Zmianę mierzy się "
        "teraz od zamknięcia poprzedniej sesji: zmiana dnia to różnica względem wczorajszego zamknięcia, "
        "nie względem otwarcia dnia — i z tego samego powodu nagłówek widoku minutowego pokazuje zmianę "
        "dnia. Poza tym na telefonie prawa szósta część pionowego wideo jest stale zajęta przez pasek z "
        "awatarem, przyciskiem polubienia i przyciskiem komentarza; karty z liczbami na dole stron Świece, "
        "Obroty, W ciągu dnia, Plan oszczędzania i Pozycja sięgały do samej krawędzi kadru, czyli "
        "dokładnie pod ten pasek. Wszystkie pięć zostaje teraz wewnątrz tej linii, a strona Świec oddaje "
        "szerokość, gdy wideo nie trafia tam, gdzie ten pasek jest.",
    "cs":
        "Tato verze umožňuje stránce Svíce porovnat více nástrojů najednou: vyberete-li jich více, jsou "
        "nakresleny společně, každý měřený od vlastního počátečního bodu, protože nástroje s různými cenami "
        "nemají společnou osu. Uspořádání lze zvolit: všechny v jednom grafu, nebo vlastní graf pro každý, "
        "pod sebou, nejvýše tři — další jsou uvedeny jménem, místo aby byly potichu vynechány. V obou "
        "případech animace končí řadou karet s procentem a částkou pro každý. Změna se nyní měří od "
        "závěrečného kurzu předchozího obchodního dne: změna dne se měří ke včerejšímu závěru, ne k "
        "otevření dne — a ze stejného důvodu záhlaví minutového zobrazení čte denní změnu. Kromě toho: na "
        "telefonu je pravá šestina svislého videa trvale obsazena pruhem s avatarem, tlačítkem To se mi "
        "líbí a tlačítkem komentáře; karty s čísly na spodku stránek Svíce, Obrat, V průběhu dne, Plán "
        "spoření a Pozice sahaly až k samému okraji snímku, tedy přesně pod něj. Všech pět nyní zůstává "
        "uvnitř této linie a stránka Svíc vrací šířku, když video neputuje tam, kde je tento pruh.",
    "ru":
        "В этой версии страница «Свечи» умеет сравнивать несколько инструментов сразу: выберите несколько "
        "— и они рисуются вместе, каждый как изменение от собственной начальной точки, потому что у "
        "инструментов с разной ценой нет общей оси. Раскладку можно выбрать: все на одном графике либо "
        "отдельный график для каждого, друг под другом, не более трёх — остальные называются по имени, а "
        "не отбрасываются молча. В обоих случаях анимация заканчивается рядом карточек с процентами и "
        "суммой по каждому. Изменение теперь считается от закрытия предыдущей сессии: изменение дня "
        "считается ко вчерашнему закрытию, а не к открытию дня — поэтому и заголовок минутного вида "
        "показывает изменение дня. Кроме того, на телефоне правая шестая часть вертикального видео занята "
        "полосой с аватаром, кнопкой «Нравится» и кнопкой комментария; карточки с цифрами внизу страниц "
        "«Свечи», «Оборот», «Внутри дня», «План сбережений» и «Позиция» доходили до самого края кадра, то "
        "есть оказывались точно под ней. Теперь все пять остаются внутри этой линии, а страница «Свечи» "
        "возвращает ширину, когда видео не попадает туда, где такой полосы нет.",
    "tr":
        "Bu sürümde Mum sayfası birden fazla enstrümanı aynı anda karşılaştırabiliyor: birkaçını "
        "seçtiğinizde birlikte çizilir, her biri kendi başlangıç noktasından ölçülür, çünkü farklı "
        "fiyatlardaki enstrümanların ortak bir ekseni yoktur. Düzen seçilebilir: hepsi tek bir grafikte ya "
        "da her birine kendi grafiği, alt alta, en çok üç — fazlası sessizce atılmaz, adıyla belirtilir. "
        "İki durumda da animasyon, her birinin yüzdesini ve tutarını veren bir kart sırasıyla biter. "
        "Değişim artık önceki seansın kapanışından ölçülüyor: bir günün değişimi o günün açılışına değil "
        "dünkü kapanışa göre ölçülür — aynı nedenle dakika görünümünün başlığı da günün değişimini okur. "
        "Ayrıca telefonda dikey bir videonun sağ altıda biri sürekli olarak avatar, beğeni düğmesi ve "
        "yorum düğmesinden oluşan şeritle doludur; Mum, Hacim, Gün içi, Birikim planı ve Pozisyon "
        "sayfalarının altındaki sayı kartları karenin ta kenarına kadar uzanıyor, yani tam olarak onun "
        "altında kalıyordu. Beşi de artık bu çizginin içinde kalıyor ve video böyle bir şeridin olmadığı "
        "bir yere gidiyorsa Mum sayfası genişliği geri veriyor.",
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
