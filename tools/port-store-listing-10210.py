# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.21.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 1.0.20.0 那一栏已经交上去了，
所以本版另起一条，只说它之后的改动。1.0.20 之后这台机器上落地的四件事：

- 新增第三十一页「持仓·大盘 双屏」：上半持仓当日盈亏、下半 A 股与港股指数分钟线，
  两幅图共用一条时间轴（挂在两图之间）；持仓曲线末尾一路跟随的胶囊标签写当日金额，
  每条指数线末尾一枚标签写指数名与实时涨跌幅。
- 条形竞速系列页新增五种画面形态（竞速 / 领奖台 / 天际线立柱 / 金字塔 / 聚焦天际线）。
- 排行榜挂公司 Logo（同花顺页内直链 + 缓存，无头像时退为名次徽章）。
- 修一处卡死：取数后在样式列表里切换，同步解码旧表格在 UI 线程上死锁。

**只说用户能感知的那半句**，代码细节（Peek sync decode、SectorRaceRenderer.Style、
CompanyLogoCache）不写。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md
是 **CRLF 无 BOM**，写完照原样写回。脚本名由 manifest 的版本号算出 `10210`。

用法：python tools\\port-store-listing-10210.py      （跑第二遍应当是「改了 0 条」）
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
        "本版新增第三十一页「持仓·大盘 双屏」：上半是持仓当日盈亏的分钟曲线，下半是 A 股与港股指数的"
        "分钟走势，两幅图共用同一条时间轴——时间轴挂在两图之间，逐分钟对着看，是谁带动当日盈亏、谁"
        "在拖累一目了然。持仓曲线的末尾跟着一枚胶囊标签写出当日金额，每条指数线的末尾各挂一枚标签"
        "写出指数名与实时涨跌幅，红涨绿跌，两个面板的标题也按各自的正负着色。两幅图各自带上了带数值的 Y 轴刻度，收益曲线上也标出了全天盈利最多与亏损最多的两个时刻。条形竞速系列新增五种"
        "画面形态，排行榜开始挂上公司 Logo。另修一处卡死：取数之后在样式列表里切换，应用会不再响应。",
    "zh-Hant":
        "本版新增第三十一頁「持倉·大盤 雙屏」：上半是持倉當日損益的分鐘曲線，下半是 A 股與港股指數的"
        "分鐘走勢，兩幅圖共用同一條時間軸——時間軸掛在兩圖之間，逐分鐘對著看，是誰帶動當日損益、誰"
        "在拖累一目了然。持倉曲線的末尾跟著一枚膠囊標籤寫出當日金額，每條指數線的末尾各掛一枚標籤"
        "寫出指數名與即時漲跌幅，紅漲綠跌，兩個面板的標題也按各自的正負著色。兩幅圖各自帶上了帶數值的 Y 軸刻度，損益曲線上也標出了全天獲利最多與虧損最多的兩個時刻。條形競速系列新增五種"
        "畫面形態，排行榜開始掛上公司 Logo。另修一處卡死：取數之後在樣式清單裡切換，應用程式會不再"
        "回應。",
    "en-US":
        "This release adds the thirty-first page, Book & Board Split: the day's P&L minute by "
        "minute above, A-share and Hong Kong index lines below, both on one clock whose axis "
        "hangs between the two pictures — read them against the same minute and it is plain which "
        "holding carried the day and which dragged it. A pill follows the head of the P&L curve "
        "with the day's money on it; each index line ends in a tag with its name and live change, "
        "red when up and green when down, and the two panel headings are inked in their own signs. Each picture carries its own Y axis with values, and the P&L curve marks the minute it gained the most and the minute it lost the most. "
        "The bar-race pages gain five shapes, and their leader boards carry company logos for the "
        "first time. One freeze is also fixed: switching a style in the list after a fetch used to "
        "leave the app unresponsive.",
    "ja":
        "今回の更新で三十一ページ目「資産と市場の分割表示」が加わりました。上半分にその日の保有損益を"
        "一分ごと、下半分に A 株と香港株の指数の値動きを描きます。二つの絵は同じ時間軸を共有し、軸は"
        "絵と絵の間に置かれます。同じ一分で見比べれば、当日の損益を牽引した銘柄と足を引っ張った銘柄"
        "が一目でわかります。保有曲線の先頭にはその日の金額を書いたカプセルがついて動き、指数の線の"
        "終わりには名前と騰落率のラベルが出ます。上昇は赤、下落は緑で、二つのパネルの見出しもその"
        "符号に合わせて色づきます。二つの絵にはそれぞれ数値つきの Y 軸がつき、損益の曲線には一日で最も稼いだ瞬間と最も損した瞬間に印がつきます。棒のレースのページに五つの表示形が増え、順位表には初めて会社の"
        "ロゴが入りました。また、データを取った直後にスタイルを切り替えると固まる不具合を直しました。",
    "ko":
        "이번 업데이트는 서른한 번째 페이지「계좌·시장 분할」을 더합니다. 위에는 그날의 보유 손익을 "
        "1분 단위로, 아래에는 A주와 홍콩 지수의 움직임을 그립니다. 두 그림은 같은 시간축을 쓰고 축은 "
        "그림 사이에 놓입니다. 같은 1분으로 견주어 보면 그날 손익을 이끈 종목과 끌어내린 종목이 "
        "한눈에 보입니다. 보유 곡선의 머리에는 그날 금액을 적은 알약표가 따라붙고, 지수선 끝에는 "
        "이름과 실시간 등락률 라벨이 붙습니다. 오르면 빨강, 내리면 초록이며 두 패널의 제목도 각자"
        "부호에 맞춰 색을 칠합니다. 두 그림에는 각각 눈금이 달린 Y축이 있고, 손익 곡선에는 하루 중 가장 벌어들인 순간과 가장 잃은 순간에 표시가 붙습니다. 막대 경주 페이지에 다섯 가지 화면 형태가 늘고 순위표에 처음으로 "
        "회사 로고가 들어갔습니다. 또한 데이터를 가져온 뒤 스타일을 바꾸면 멈추던 문제도 고쳤습니다.",
    "de":
        "Dieses Release bringt die einunddreißigste Seite, Depot & Markt geteilt: oben das "
        "Tagesergebnis des Depots Minute für Minute, unten die Verläufe der A-Aktien- und der "
        "Hongkong-Indizes. Beide Bilder teilen eine Uhr, deren Achse zwischen ihnen hängt — in "
        "derselben Minute gelesen zeigt sich, welche Position den Tag getragen und welche ihn "
        "gedrückt hat. Eine Kapsel folgt dem Kopf der Ergebniskurve mit dem Tagesbetrag; jede "
        "Indexlinie endet mit einem Etikett aus Namen und augenblicklicher Veränderung — rot bei "
        "Plus, grün bei Minus —, und beide Paneltitel sind im eigenen Vorzeichen eingefärbt. Jedes Bild trägt eine eigene Y-Achse mit Werten, und die Ergebniskurve markiert die Minute des größten Gewinns und die des größten Verlusts. Die "
        "Balkenrennen-Seiten erhalten fünf Bildformen, und ihre Bestenlisten zeigen erstmals die "
        "Logos der Gesellschaften. Behoben ist außerdem ein Hänger: Ein Wechsel des Stils direkt "
        "nach dem Datenabruf ließ die Anwendung nicht mehr reagieren.",
    "fr":
        "Cette version ajoute la trente et unième page, Portefeuille & marché partagés : en haut le "
        "résultat du jour du portefeuille minute par minute, en bas le parcours des indices A et de "
        "Hong Kong. Les deux dessins partagent une même horloge dont l'axe est placé entre eux : lus "
        "à la même minute, ils montrent tout de suite quelle position a porté la journée et laquelle "
        "l'a plombée. Une pastille suit la tête de la courbe avec le montant du jour ; chaque ligne "
        "d'indice se termine par une étiquette avec son nom et sa variation en direct — rouge à la "
        "hausse, vert à la baisse —, et les deux titres de panneau se colorent à leur propre signe. Chaque dessin porte son propre axe Y chiffré, et la courbe de résultat marque la minute du plus grand gain et celle de la plus grande perte. "
        "Les pages de course de barres reçoivent cinq formes d'affichage, et leurs classements "
        "affichent pour la première fois les logos des sociétés. Un gel est aussi corrigé : changer "
        "de style après une récupération laissait l'application sans réponse.",
    "it":
        "Questa versione aggiunge la trentunesima pagina, Portafoglio e mercato divisi: in alto il "
        "risultato del giorno del portafoglio minuto per minuto, in basso l'andamento degli indici A "
        "e di Hong Kong. I due disegni condividono un solo orologio, con l'asse appeso fra loro: "
        "letti allo stesso minuto mostrano subito quale posizione ha sorretto la giornata e quale "
        "l'ha appesantita. Una capsula segue la testa della curva con la cifra del giorno; ogni "
        "linea di indice finisce con un'etichetta con il nome e la variazione in diretta — rosso al "
        "rialzo, verde al ribasso —, e i due titoli dei pannelli si tingono del proprio segno. Ogni disegno porta il proprio asse Y con i valori, e la curva del risultato segna il minuto del guadagno maggiore e quello della perdita maggiore. Le "
        "pagine di corsa delle barre ricevono cinque forme, e le loro classifiche mostrano per la "
        "prima volta i loghi delle società. È corretto anche un blocco: cambiare stile dopo un "
        "recupero dati lasciava l'applicazione senza risposta.",
    "es":
        "Esta versión añade la página treinta y una, Cartera y mercado, divididos: arriba el "
        "resultado del día de la cartera minuto a minuto y abajo el recorrido de los índices A y de "
        "Hong Kong. Los dos dibujos comparten un mismo reloj, con el eje colgado entre ellos: "
        "leídos en el mismo minuto dejan claro qué posición sostuvo la jornada y cuál la lastró. Una "
        "píldora sigue la cabeza de la curva con el importe del día; cada línea de índice termina en "
        "una etiqueta con su nombre y su variación en vivo — rojo al alza, verde a la baja —, y los "
        "dos títulos de panel se tiñen de su propio signo. Cada dibujo lleva su propio eje Y con valores, y la curva de resultado marca el minuto de la mayor ganancia y el de la mayor pérdida. Las páginas de carrera de barras reciben "
        "cinco formas, y sus clasificaciones muestran por primera vez los logotipos de las "
        "empresas. También se corrige un bloqueo: cambiar de estilo tras una descarga dejaba la "
        "aplicación sin respuesta.",
    "pt-BR":
        "Esta versão acrescenta a trigésima primeira página, Carteira e mercado divididos: em cima o "
        "resultado do dia da carteira minuto a minuto, embaixo o traçado dos índices A e de Hong "
        "Kong. Os dois desenhos compartilham um só relógio, com o eixo pendurado entre eles: lidos "
        "no mesmo minuto, deixam claro qual posição sustentou o dia e qual o puxou para baixo. Uma "
        "pílula segue a cabeça da curva com o valor do dia; cada linha de índice termina numa "
        "etiqueta com o nome e a variação ao vivo — vermelho na alta, verde na baixa —, e os dois "
        "títulos de painel assumem o próprio sinal. Cada desenho traz o próprio eixo Y com valores, e a curva de resultado marca o minuto do maior ganho e o da maior perda. As páginas de corrida de barras recebem cinco "
        "formas e suas classificações mostram pela primeira vez os logotipos das empresas. Também "
        "corrigimos um travamento: mudar de estilo depois de uma consulta deixava o aplicativo sem "
        "resposta.",
    "pl":
        "To wydanie dodaje trzydziestą pierwszą stronę, Portfel i rynek, na pół: u góry wynik dnia "
        "portfela minuta po minucie, u dołu przebieg indeksów A i Hongkongu. Oba rysunki mają jeden "
        "zegar, a jego oś wisi między nimi: czytane w tej samej minucie od razu pokazują, która "
        "pozycja dzień niosła, a która go ciągnęła w dół. Za głową krzywej idzie kapsułka z kwotą "
        "dnia; każda linia indeksu kończy się etykietą z nazwą i bieżącą zmianą — czerwono przy "
        "wzroście, zielono przy spadku — a oba nagłówki paneli przyjmują własny znak. Każdy rysunek ma własną oś Y z wartościami, a krzywa wyniku oznacza minutę największego zysku i minutę największej straty. Strony wyścigu "
        "słupków dostają pięć form, a ich tablice po raz pierwszy pokazują logo spółek. Naprawiono "
        "też zawieszenie: zmiana stylu po pobraniu danych zostawiała aplikację bez odpowiedzi.",
    "cs":
        "Tato verze přidává třicátou první stránku Portfolio a trh napůl: nahoře výsledek dne "
        "portfolia minutu po minutě, dole průběh indexů A a Hongkongu. Oba obrázky sdílejí jeden "
        "čas a jeho osa visí mezi nimi: čtené ve stejné minutě hned ukážou, která pozice den "
        "nesla a která ho stahovala. Za hlavou křivky jde tobolka s částkou dne; každá čára indexu "
        "končí štítkem se jménem a živou změnou — červeně při růstu, zeleně při poklesu — a oba "
        "nadpisy panelů se barví svým znakem. Každý obrázek má vlastní osu Y s hodnotami a křivka výsledku označuje minutu největšího zisku a minutu největší ztráty. Strany závodu sloupců dostávají pět podob a jejich "
        "tabulky poprvé ukazují loga firem. Opraveno je i zatuhnutí: změna stylu po načtení dat "
        "nechávala aplikaci bez odezvy.",
    "ru":
        "Этот выпуск добавляет тридцать первую страницу «Портфель и рынок, пополам»: сверху результат "
        "дня портфеля минута за минутой, снизу ход индексов A-акций и Гонконга. Оба рисунка делят "
        "одну шкалу времени, и ось висит между ними: читаемые в одну и ту же минуту, они сразу "
        "показывают, какая позиция день несла, а какая тянула вниз. За головой кривой идёт капсула с "
        "суммой дня; каждая линия индекса заканчивается подписью с названием и текущим изменением — "
        "красная при росте, зелёная при падении —, а оба заголовка панелей окрашены в свой знак. У каждого рисунка своя ось Y с подписями, а кривая результата отмечает минуту наибольшей прибыли и минуту наибольшего убытка. "
        "Страницы гонки столбцов получают пять форм, и их таблицы впервые показывают логотипы "
        "компаний. Исправлена и «заморозка»: смена стиля после загрузки данных оставляла приложение "
        "без ответа.",
    "tr":
        "Bu sürüm otuz birinci sayfayı ekliyor, Portföy ve Piyasa bölünmüş: üstte portföyün gün içi "
        "kâr/zararı dakika dakika, altta A hissesi ve Hong Kong endekslerinin seyri. İki çizim de "
        "tek bir saat kullanır ve eksen ikisinin arasında durur: aynı dakikada okunduğunda günü "
        "hangi pozisyonun taşıdığı, hangisinin aşağı çektiği hemen görülür. Eğrinin başını günün "
        "tutarını yazan bir kapsül izler; her endeks çizgisi adını ve canlı değişimini yazan bir "
        "etiketle biter — yükselişte kırmızı, düşüşte yeşil — ve iki panelin başlığı da kendi işaretine "
        "göre renklenir. Her çizimin kendi değerli Y ekseni var ve kâr/zarar eğrisi o gün en çok kazandıran ve en çok kaybettiren dakikayı işaretliyor. Çubuk yarışı sayfaları beş görünüm kazandı ve sıralama tabloları ilk kez "
        "şirket logolarını gösteriyor. Bir donma da düzeltildi: veri çekildikten sonra stil "
        "değiştirmek uygulamayı yanıtsız bırakıyordu.",
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
