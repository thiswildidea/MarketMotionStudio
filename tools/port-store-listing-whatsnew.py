"""改写商店文案里那十四条「此版本的新增功能」。

为什么是**换掉**而不是接着往后加：说明段刚从十页补到十六页，而那十四条还在说
「本版新增第八个图表页 K线」「本版新增第九个图表页 市值榜竞速」—— 一页一页数着加上去
的旧版本说明，和「十六大图表页」并排放在一起是自相矛盾的。商店这一栏问的是本版，
历史留在 CHANGELOG.md 里。

本版要说两件事：十六页各有自己画的图标（此前三对页面共用同一个系统字形），以及
四个页面的区间按接口实测重定（超长区间会被拒绝，因为悄悄截断丢的是开头）。

定位：每个语言段里第二个 `###` 小标题之后的第一段正文。幂等：那一段已经以新文案
开头就跳过。
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]


def news(lang):
    return {
        "zh-Hans":
            "本版为十六个页面各画了一个图标。此前有三对页面共用同一个系统字形——一个形状说不了两个页面。"
            "十六个图标现在都是按页面意思画出来的矢量几何，跟着浅色或深色主题变色。 "
            "另外，四个页面的数据区间按行情接口实际能返回的数量重新划定：K线的日线多了 5 年与 10 年两档"
            "（日线会一页页往回翻，能到约十五年）；成交量换手率与行业板块竞速多了 24 个月一档，"
            "自定义区间的上限从 640 天放到 900 天——那才是一次请求能取回的量；市值榜竞速多了「最长」一档，"
            "月线一次请求就给满 180 期，约十五年。区间超出接口能给的范围会被直接拒绝，而不是悄悄截断："
            "悄悄截断丢的是开头，而开头少了几年的图看起来完全正常。",
        "zh-Hant":
            "本版為十六個頁面各畫了一個圖示。此前有三對頁面共用同一個系統字形——一個形狀說不了兩個頁面。"
            "十六個圖示現在都是按頁面意思畫出來的向量幾何，跟著淺色或深色主題變色。 "
            "另外，四個頁面的資料區間按行情介面實際能回傳的數量重新劃定：K線的日線多了 5 年與 10 年兩檔"
            "（日線會一頁頁往回翻，能到約十五年）；成交量與換手率、行業板塊競速多了 24 個月一檔，"
            "自訂區間的上限從 640 天放到 900 天——那才是一次請求能取回的量；市值榜競速多了「最長」一檔，"
            "月線一次請求就給滿 180 期，約十五年。區間超出介面能給的範圍會被直接拒絕，而不是悄悄截斷："
            "悄悄截斷丟的是開頭，而開頭少了幾年的圖看起來完全正常。",
        "en-US":
            "Every page now has an icon drawn for it. Three pairs of pages had been sharing one "
            "system glyph, and one shape cannot mean two pages. All sixteen are drawn as vector "
            "geometry and take their colour from the light or dark theme. "
            "The range menus of four pages were also re-cut against what the quote endpoints "
            "actually return: daily candles gained 5 and 10 years, the page walking backwards a "
            "page at a time for some fifteen years in all; Volume & Turnover and Sector Race "
            "gained 24 months, and the ceiling on a custom span went from 640 to 900 days, which "
            "is what one request really returns; Market Cap Race gained a Longest entry, one "
            "request returning all 180 monthly periods, about fifteen years. A range beyond what "
            "the source can give is refused rather than quietly truncated — truncating loses the "
            "beginning, and a chart missing its first years is a shorter chart that looks entirely "
            "correct.",
        "ja":
            "このバージョンでは、十六のページそれぞれにページのためのアイコンを描きました。"
            "以前は三組のページが同じシステム字形を共有していました——ひとつの形で二つのページは表せません。"
            "十六個のアイコンはすべてページの意味に合わせたベクター図形で、"
            "ライトテーマとダークテーマで色が変わります。 "
            "また、四つのページのデータ期間を、相場 API が実際に返す量に合わせて見直しました。"
            "ローソク足の日足に 5 年と 10 年を追加（日足はページごとに遡るため、約十五年まで届きます）。"
            "出来高・回転率とセクターレースには 24 か月を追加し、カスタム期間の上限を 640 日から 900 日"
            "に広げました——それが一回のリクエストで取得できる量です。時価総額レースには「最長」を追加。"
            "月足は一回のリクエストで 180 期、約十五年がすべて返ります。"
            "ソースが返せる範囲を超える期間は、こっそり切り詰めるのではなく拒否します。"
            "切り詰めると失われるのは冒頭で、最初の数年が抜けたグラフは短くなっただけで、"
            "見た目はまったく普通だからです。",
        "ko":
            "이 버전에서는 열여섯 개 페이지에 각 페이지를 위해 그린 아이콘을 붙였습니다. "
            "이전에는 세 쌍의 페이지가 같은 시스템 글리프를 공유했는데, 하나의 모양이 두 페이지를 뜻할 수는 "
            "없습니다. 열여섯 개 모두 페이지의 뜻에 맞춘 벡터 도형으로 그렸으며, 밝은 테마와 어두운 테마에 "
            "따라 색이 바뀝니다. "
            "또한 네 페이지의 데이터 구간을 시세 API가 실제로 반환하는 양에 맞춰 다시 정했습니다. "
            "캔들 차트의 일간에 5년과 10년을 추가했습니다(일간은 페이지 단위로 거슬러 올라가므로 "
            "약 십오 년까지 닿습니다). 거래량·회전율과 업종 경주에는 24개월을 추가하고, 사용자 지정 구간의 "
            "상한을 640일에서 900일로 넓혔습니다——한 번의 요청으로 가져올 수 있는 양입니다. "
            "시가총액 레이스에는 「가장 긴 구간」을 추가했고, 월간은 한 번의 요청으로 180개 기간, "
            "약 십오 년이 모두 돌아옵니다. 소스가 줄 수 있는 범위를 넘는 구간은 조용히 잘라내지 않고 "
            "거부합니다. 잘라내면 사라지는 것은 앞부분이며, 첫 몇 년이 빠진 차트는 짧아졌을 뿐 "
            "전혀 정상적으로 보이기 때문입니다.",
        "de":
            "In dieser Version hat jede der sechzehn Seiten ihr eigenes Symbol. Vorher teilten "
            "sich drei Seitenpaare ein und dasselbe Systemzeichen — eine Form kann nicht zwei "
            "Seiten bedeuten. Alle sechzehn sind nun als Vektorgeometrie gezeichnet und nehmen "
            "ihre Farbe aus dem hellen oder dem dunklen Thema. "
            "Außerdem wurden die Zeiträume von vier Seiten an das angepasst, was die "
            "Kurs-Endpunkte wirklich liefern: Tageskerzen bekamen 5 und 10 Jahre, die Seite "
            "blättert seitenweise zurück und erreicht damit etwa fünfzehn Jahre; Volumen und "
            "Umschlag sowie das Sektor-Rennen bekamen 24 Monate, und die Obergrenze eines eigenen "
            "Zeitraums stieg von 640 auf 900 Tage — so viel gibt eine Anfrage wirklich her; das "
            "Marktkapitalisierungs-Rennen bekam einen Eintrag „Längster“, denn eine Anfrage "
            "liefert alle 180 Monatsperioden, etwa fünfzehn Jahre. Ein Zeitraum jenseits dessen, "
            "was die Quelle liefern kann, wird abgelehnt statt still gekürzt: Gekürzt wird nämlich "
            "der Anfang, und ein Diagramm ohne seine ersten Jahre ist ein kürzeres Diagramm, das "
            "völlig normal aussieht.",
        "fr":
            "Dans cette version, chacune des seize pages a son icône. Auparavant, trois paires de "
            "pages partageaient le même glyphe système, et une forme ne peut pas désigner deux "
            "pages. Les seize sont désormais dessinées en géométrie vectorielle et prennent la "
            "couleur du thème clair ou sombre. "
            "Les plages de quatre pages ont aussi été recalées sur ce que les endpoints de cotation "
            "renvoient réellement : le quotidien des chandeliers gagne 5 et 10 ans, la page "
            "remontant page par page sur une quinzaine d'années au total ; Volume et rotation "
            "ainsi que la course de secteurs gagnent 24 mois, et le plafond d'une plage "
            "personnalisée passe de 640 à 900 jours — ce qu'une requête ramène vraiment ; la course "
            "des capitalisations gagne une entrée « Maximale », une requête ramenant les 180 "
            "périodes mensuelles, soit une quinzaine d'années. Une plage au-delà de ce que la "
            "source peut rendre est refusée plutôt que tronquée en silence : ce qui disparaît "
            "alors, c'est le début, et un graphique amputé de ses premières années est un graphique "
            "plus court qui a l'air parfaitement normal.",
        "it":
            "In questa versione ognuna delle sedici pagine ha la sua icona. Prima tre coppie di "
            "pagine condividevano lo stesso glifo di sistema, e una forma non può significare due "
            "pagine. Tutte e sedici sono ora disegnate come geometria vettoriale e prendono il "
            "colore dal tema chiaro o scuro. "
            "Anche gli intervalli di quattro pagine sono stati rimisurati su ciò che gli endpoint "
            "delle quotazioni restituiscono davvero: il giornaliero di Candele guadagna 5 e 10 "
            "anni, con la pagina che sfoglia indietro una pagina alla volta per circa quindici "
            "anni in tutto; Volume e rotazione e la corsa dei settori guadagnano 24 mesi, e il "
            "tetto di un intervallo personalizzato passa da 640 a 900 giorni — quanto restituisce "
            "davvero una richiesta; la corsa delle capitalizzazioni guadagna una voce «Massimo», "
            "perché una richiesta restituisce tutti i 180 periodi mensili, circa quindici anni. Un "
            "intervallo oltre ciò che la fonte può dare viene rifiutato invece di essere troncato "
            "in silenzio: a mancare sarebbe l'inizio, e un grafico senza i suoi primi anni è un "
            "grafico più corto che sembra del tutto normale.",
        "es":
            "En esta versión cada una de las dieciséis páginas tiene su propio icono. Antes tres "
            "pares de páginas compartían el mismo glifo del sistema, y una forma no puede "
            "significar dos páginas. Las dieciséis están dibujadas ahora como geometría vectorial "
            "y toman el color del tema claro u oscuro. "
            "También se han reajustado los rangos de cuatro páginas a lo que los endpoints de "
            "cotización devuelven de verdad: el diario de Velas gana 5 y 10 años, retrocediendo la "
            "página página a página unos quince años en total; Volumen y rotación y la carrera de "
            "sectores ganan 24 meses, y el techo de un intervalo personalizado sube de 640 a 900 "
            "días — lo que una petición devuelve realmente; la carrera de capitalización gana una "
            "entrada «Máximo», porque una petición devuelve los 180 periodos mensuales, unos quince "
            "años. Un rango más allá de lo que la fuente puede dar se rechaza en lugar de "
            "recortarse en silencio: lo que se pierde es el principio, y un gráfico sin sus primeros "
            "años es un gráfico más corto que parece completamente normal.",
        "pt-BR":
            "Nesta versão cada uma das dezesseis páginas tem seu próprio ícone. Antes três pares de "
            "páginas compartilhavam o mesmo glifo do sistema, e uma forma não pode significar duas "
            "páginas. As dezesseis agora são desenhadas como geometria vetorial e assumem a cor do "
            "tema claro ou escuro. "
            "Os intervalos de quatro páginas também foram reajustados ao que os endpoints de "
            "cotação realmente devolvem: o diário de Candlestick ganha 5 e 10 anos, com a página "
            "voltando página por página ao longo de cerca de quinze anos; Volume e giro e a corrida "
            "de setores ganham 24 meses, e o teto de um intervalo personalizado sobe de 640 para "
            "900 dias — o que um pedido realmente devolve; a corrida de valor de mercado ganha uma "
            "entrada «Máximo», porque um pedido devolve todos os 180 períodos mensais, cerca de "
            "quinze anos. Um intervalo além do que a fonte pode dar é recusado em vez de cortado em "
            "silêncio: o que se perde é o começo, e um gráfico sem seus primeiros anos é um gráfico "
            "mais curto que parece inteiramente normal.",
        "pl":
            "W tej wersji każda z szesnastu stron ma własną ikonę. Wcześniej trzy pary stron "
            "korzystały z tego samego glifu systemowego, a jeden kształt nie może oznaczać dwóch "
            "stron. Wszystkie szesnaście narysowano teraz jako geometrię wektorową, która bierze "
            "kolor z jasnego lub ciemnego motywu. "
            "Przejrzano też zakresy czterech stron pod kątem tego, co endpointy notowań faktycznie "
            "zwracają: interwał dzienny świec zyskał 5 i 10 lat, a strona cofa się strona po "
            "stronie, łącznie około piętnastu lat; Wolumen i obrót oraz wyścig sektorów zyskały "
            "24 miesiące, a limit własnego zakresu wzrósł z 640 do 900 dni — tyle naprawdę zwraca "
            "jedno żądanie; wyścig kapitalizacji zyskał pozycję „Najdłuższy“, bo jedno żądanie "
            "zwraca wszystkie 180 okresów miesięcznych, około piętnaście lat. Zakres większy niż "
            "źródło może oddać jest odrzucany zamiast po cichu ucinany: ucięty zostaje początek, a "
            "wykres bez pierwszych lat to po prostu krótszy wykres, który wygląda zupełnie normalnie.",
        "cs":
            "V této verzi má každá z šestnácti stran vlastní ikonu. Dříve tři dvojice stran "
            "sdílely stejný systémový glyf a jeden tvar nemůže znamenat dvě strany. Všech šestnáct "
            "je nyní nakresleno jako vektorová geometrie a bere barvu ze světlého nebo tmavého "
            "motivu. "
            "Rozsahy čtyř stran byly také znovu změřeny podle toho, co koncové body kurzů "
            "skutečně vracejí: denní interval svíček získal 5 a 10 let, strana se vrací po "
            "stránkách, celkem asi patnáct let; Objem a obrat a závod sektorů získaly 24 měsíců a "
            "strop vlastního rozsahu stoupl z 640 na 900 dnů — tolik jeden požadavek skutečně "
            "vrátí; závod kapitalizací získal položku „Nejdelší“, protože jeden požadavek vrátí "
            "všech 180 měsíčních období, asi patnáct let. Rozsah větší, než může zdroj dát, je "
            "odmítnut místo tichého zkrácení: chyběl by začátek, a graf bez prvních let je jen "
            "kratší graf, který vypadá naprosto normálně.",
        "ru":
            "В этой версии у каждой из шестнадцати страниц своя иконка. Раньше три пары страниц "
            "делили один системный глиф, а одна форма не может означать две страницы. Все "
            "шестнадцать теперь нарисованы как векторная геометрия и берут цвет из светлой или "
            "тёмной темы. "
            "Диапазоны четырёх страниц тоже пересчитаны по тому, что реально возвращают конечные "
            "точки котировок: дневной интервал свечей получил 5 и 10 лет — страница листает назад "
            "по страницам, всего около пятнадцати лет; «Объём и оборачиваемость» и гонка секторов "
            "получили 24 месяца, а предел пользовательского диапазона поднялся с 640 до 900 дней — "
            "столько действительно возвращает один запрос; гонка капитализаций получила пункт "
            "«Максимальный», потому что один запрос возвращает все 180 месячных периодов, около "
            "пятнадцати лет. Диапазон больше того, что может дать источник, отклоняется, а не "
            "обрезается молча: пропадает начало, а график без первых лет — это просто более "
            "короткий график, который выглядит совершенно нормально.",
        "tr":
            "Bu sürümde on altı sayfanın her birinin kendine ait bir simgesi var. Önceden üç sayfa "
            "çifti aynı sistem glifini paylaşıyordu ve bir şekil iki sayfayı anlatamaz. On altısı "
            "da artık vektör geometrisi olarak çiziliyor ve rengini açık ya da koyu temadan alıyor. "
            "Dört sayfanın aralıkları da kotasyon uç noktalarının gerçekten döndürdüğü miktara göre "
            "yeniden ayarlandı: mum grafiğinin günlüğü 5 ve 10 yıl kazandı, sayfa sayfa geri "
            "giderek toplamda yaklaşık on beş yıla ulaşıyor; Hacim ve devir ile sektör yarışı 24 ay "
            "kazandı ve özel aralığın sınırı 640 günden 900 güne çıktı — bir isteğin gerçekten "
            "döndürdüğü kadar; piyasa değeri yarışı 「En uzun」 seçeneğini kazandı, çünkü bir istek "
            "180 aylık dönemin tamamını, yaklaşık on beş yılı döndürüyor. Kaynağın verebileceğinden "
            "uzun bir aralık sessizce kısaltılmaz, reddedilir: eksilen kısım başlangıçtır ve ilk "
            "yılları çıkmış bir grafik, tamamen normal görünen daha kısa bir grafiktir.",
    }[lang]


def main():
    raw = LISTING.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        print("× store-listing.md 带着 BOM —— 商店文案不能带，先去掉再跑")
        return 1

    # store-listing.md 是 CRLF，帮助手册是 LF —— 各文件保持自己的行尾。不剥掉 \r 的话，
    # "这一行是不是已经改过了"永远比不出来（每次都差一个 \r），幂等就成了空话。
    crlf = b"\r\n" in raw
    lines = raw.decode("utf-8").replace("\r\n", "\n").split("\n")
    heads = [i for i, s in enumerate(lines) if s.startswith("## ")]

    if len(heads) != 14:
        print(f"× 数到 {len(heads)} 个语言段，应当是 14")
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

        line = news(lang)

        if lines[at] == line:
            print(f"· {lang}: （已是本版）")
            continue

        lines[at] = line
        changed += 1
        heads = [i for i, s in enumerate(lines) if s.startswith("## ")]
        print(f"· {lang}: 「{lines[subs[1]][4:]}」改写（{len(line)} 字）")

    LISTING.write_bytes(("\r\n" if crlf else "\n").join(lines).encode("utf-8"))
    too_long = [l for l in LANGS if len(news(l)) > 1500]

    if too_long:
        print(f"\n！超过商店 1500 字上限：{too_long}")

    print(f"\n改了 {changed} 条（跑第二遍应当是 0）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
