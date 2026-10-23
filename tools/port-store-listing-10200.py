# -*- coding: utf-8 -*-
"""把商店文案（docs/store-listing.md，14 语言）的「此版本的新增功能」改到 1.0.20.0。

**这一栏是「换」不是「加」，历史留在 CHANGELOG.md。** 1.0.18.0 那一栏已经交上去了，
所以本版另起一条，只说它之后的改动。1.0.18 之后这台机器上落地的，全是实时持仓收益页
的重做与标题样式全局化：

- 持仓列表跟着时间轴走：每一分钟的股数、成本、盈亏都在动（不再只在收尾出现）。
- 曲线经过成交时弹出买入/卖出点文字标签；交易费率成为页面设置项。
- 页眉的「持仓市值」按画面当前分钟实时计算——1.0.19–1.0.20 之交修的那处：原来印的
  是收盘值，一行两句话说的不是同一分钟。
- 成交导入改为粘贴或表格文件（截图识别入路与买卖按钮撤掉）；持仓列表可整份导出/导入
  （CSV，逐行校验，一行不合全拒）。
- 管理持仓对话框显示最新收盘持仓；检索建议显示记录转储的毛病修掉。
- 关闭应用时把当天未折的成交自动折进账本（滚动账本）。
- 标题样式全局化：三款标题与配色在设置页选一次，所有页面即改即生效。
- 1.0.18 已上线的四个加密页（比较/涨跌/占比/年度回报）本版补齐 14 语言手册与商店介绍。

**只说用户能感知的那半句**，代码细节（RollForward、指纹去重、PnlSample）不写。
加密那四页写「上个版本已上线、本版补齐介绍」，不冒充本版新功能。

定位与幂等：每个语言段里第二个 `###` 小标题之后的第一段正文，整行比对。store-listing.md
是 **CRLF 无 BOM**，写完照原样写回。脚本名由 manifest 的版本号算出 `10200`。

用法：python tools\\port-store-listing-10200.py      （跑第二遍应当是「改了 0 条」）
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
LISTING = REPO / "docs" / "store-listing.md"

LANGS = ["zh-Hans", "zh-Hant", "en-US", "ja", "ko", "de", "fr", "it",
         "es", "pt-BR", "pl", "cs", "ru", "tr"]

# 商店这一栏的硬上限。
LIMIT = 1500

NEWS = {
    "zh-Hans":
        "本版重做实时持仓收益页：持仓列表跟着时间轴走，每一分钟的股数、成本与盈亏都在动；"
        "曲线经过成交时弹出买入/卖出点文字标签；交易费率成为页面设置项；页眉的「持仓市值」"
        "按画面当前分钟实时计算，买入卖出即动。成交导入改为粘贴或表格文件，持仓列表可整份"
        "导出与导入（CSV）。管理持仓对话框显示最新收盘持仓，检索问题已修复；关闭应用时会把"
        "当天未记的成交自动折进账本。标题样式改为全局设置：三款标题与配色在设置页选一次，"
        "所有页面即改即生效。加密货币比较、涨跌、占比、年度回报四个页面上个版本已上线，本版"
        "为它们补齐了 14 种语言的手册与商店介绍。",
    "zh-Hant":
        "本版重做即時持倉收益頁：持倉清單跟著時間軸走，每一分鐘的股數、成本與損益都在動；"
        "曲線經過成交時彈出買入/賣出點文字標籤；交易費率成為頁面設定項；頁眉的「持倉市值」"
        "按畫面當前分鐘即時計算，買入賣出即動。成交匯入改為貼上或表格檔案，持倉清單可整份"
        "匯出與匯入（CSV）。管理持倉對話框顯示最新收盤持倉，檢索問題已修復；關閉應用程式時"
        "會把當天未記的成交自動折進帳本。標題樣式改為全域設定：三款標題與配色在設定頁選"
        "一次，所有頁面即改即生效。加密貨幣比較、漲跌、佔比、年度報酬四個頁面上個版本已"
        "上線，本版為它們補齊了 14 種語言的手冊與商店介紹。",
    "en-US":
        "This release reworks the live portfolio page: the holdings list follows the timeline, "
        "with shares, cost and P&L moving minute by minute; the curve raises buy/sell labels as "
        "it passes each fill; commission rates become a page setting; and the position value in "
        "the header is computed for the frame's own minute, moving with every buy and sell. "
        "Trade import switches to paste or a spreadsheet file, and the holdings list can be "
        "exported and re-imported whole as CSV. The manage-holdings dialog shows the latest "
        "close and its search glitch is fixed; on shutdown the day's unrecorded fills are folded "
        "into the ledger automatically. Title styles become a global setting: pick one of three "
        "title designs and colours in Settings, and every page follows at once. The four crypto "
        "pages — Compare, Movers, Dominance and Annual Returns — shipped last release; this one "
        "completes their manuals and store text in all 14 languages.",
    "ja":
        "今回の更新は、リアルタイム保有損益ページの作り直しです。保有リストがタイムラインに沿って動き、"
        "株数・取得単価・損益が一分ごとに変わります。曲線が約定を通過するときに「買い / 売り」の文字"
        "ラベルが出ます。手数料率はページの設定項目になり、ヘッダーの保有評価額は表示中の一分で"
        "リアルタイムに計算され、売買のたびに動きます。約定の取り込みは貼り付けか表ファイルになり、"
        "保有リストは CSV で丸ごと書き出し・読み込みできます。保有管理ダイアログは最新の大引け時点の"
        "保有を示し、検索の不具合を直しました。終了時には、まだ帳簿に折り込まれていない当日の約定を"
        "自動で折り込みます。タイトルのスタイルは全体設定になりました。三つのスタイルと配色を設定"
        "ページで一度選べば、全ページがすぐに反映します。暗号資産の比較・値動き・占有率・年間収益の"
        "四ページは前回の版で既に搭載済みですが、本版で 14 言語のマニュアルとストア紹介を補いました。",
    "ko":
        "이번 업데이트는 실시간 보유 손익 페이지를 다시 만든 것입니다. 보유 목록이 타임라인을 따라 움직이며 "
        "주식 수·평단가·손익이 1분마다 바뀝니다. 곡선이 체결을 지날 때 매수/매도 문자 레이블이 나타납니다. "
        "수수료율은 페이지 설정 항목이 되었고, 머리글의 보유 평가액은 화면의 그 1분 기준으로 실시간 계산되어 "
        "매매 때마다 움직입니다. 체결 가져오기는 붙여넣기나 표 파일로 바뀌었고, 보유 목록은 CSV로 통째로 "
        "내보내고 가져올 수 있습니다. 보유 관리 대화상자는 최신 종가 시점의 보유를 보여 주며 검색 문제를 "
        "고쳤습니다. 종료할 때 아직 장부에 반영되지 않은 당일 체결이 자동으로 반영됩니다. 제목 스타일은 "
        "전역 설정이 되었습니다. 세 가지 스타일과 색을 설정 페이지에서 한 번 고르면 모든 페이지에 곧바로 "
        "적용됩니다. 암호화폐 비교·등락·점유율·연간 수익 네 페이지는 지난 버전에 이미 들어 있었고, 이번 "
        "버전에서 14개 언어의 매뉴얼과 스토어 소개를 채웠습니다.",
    "de":
        "Dieses Release baut die Seite Depot live um: Die Bestandsliste folgt der Zeitleiste, Stückzahl, "
        "Einstand und Gewinn/Verlust bewegen sich Minute für Minute; beim Passieren jedes Abschlusses "
        "erscheint ein Kauf-/Verkauf-Label; die Gebührenrate wird zu einer Seiteneinstellung; und der "
        "Positionswert in der Kopfzeile wird für die jeweilige Minute berechnet und bewegt sich mit "
        "jedem Kauf und Verkauf. Der Import von Abschlüssen wechselt zu Einfügen oder Tabellendatei, "
        "und die Bestandsliste lässt sich als CSV ganz exportieren und wieder einlesen. Der Dialog "
        "Bestand verwalten zeigt den letzten Schlussbestand, und der Suchfehler ist behoben; beim "
        "Beenden werden die nicht verbuchten Abschlüsse des Tages automatisch ins Konto gefaltet. "
        "Titeldesigns werden zur globalen Einstellung: Drei Titelentwürfe und Farben einmal in den "
        "Einstellungen gewählt, und jede Seite folgt sofort. Die vier Krypto-Seiten Vergleich, "
        "Bewegungen, Dominanz und Jahresrenditen kamen im letzten Release; dieses ergänzt ihre "
        "Handbücher und Shop-Texte in allen 14 Sprachen.",
    "fr":
        "Cette version refait la page P&L en direct : la liste des positions suit la frise, les titres, "
        "le prix de revient et le résultat bougent minute par minute ; la courbe fait apparaître une "
        "étiquette achat/vente en passant sur chaque opération ; le taux de frais devient un réglage de "
        "la page ; et la valeur de position dans l'en-tête est calculée à la minute affichée, bougeant à "
        "chaque achat et vente. L'import d'opérations passe au collage ou au fichier tableur, et la liste "
        "des positions s'exporte et se réimporte entière en CSV. La boîte Gérer les positions montre la "
        "dernière clôture, et son défaut de recherche est corrigé ; à la fermeture, les opérations du "
        "jour non encore comptabilisées sont versées au registre automatiquement. Les styles de titre "
        "deviennent un réglage global : trois dessins de titre et couleurs choisis une fois dans les "
        "réglages, et chaque page suit aussitôt. Les quatre pages crypto — Comparaison, Mouvements, "
        "Dominance et Rendements annuels — sont arrivées à la version précédente ; celle-ci achève leurs "
        "manuels et textes de boutique dans les 14 langues.",
    "it":
        "Questa versione rifà la pagina P&L in tempo reale: l'elenco delle posizioni segue la linea del "
        "tempo, con azioni, costo medio e utile/perdita che si muovono minuto per minuto; la curva fa "
        "comparire un'etichetta acquisto/vendita al passaggio su ogni eseguito; il tasso di commissioni "
        "diventa un'impostazione della pagina; e il valore di posizione nell'intestazione è calcolato al "
        "minuto mostrato, muovendosi a ogni acquisto e vendita. L'importazione degli eseguiti passa a "
        "incolla o file di foglio di calcolo, e l'elenco delle posizioni si esporta e reimporta intero in "
        "CSV. La finestra Gestisci posizioni mostra l'ultima chiusura e il difetto di ricerca è corretto; "
        "alla chiusura, gli eseguiti del giorno non ancora registrati confluiscono automaticamente nel "
        "registro. Gli stili del titolo diventano un'impostazione globale: tre disegni di titolo e colori "
        "scelti una volta nelle impostazioni, e ogni pagina li segue subito. Le quattro pagine crypto — "
        "Confronto, Movimenti, Dominanza e Rendimenti annuali — sono arrivate con la versione precedente; "
        "questa completa i loro manuali e testi dello store in tutte le 14 lingue.",
    "es":
        "Esta versión rehace la página de P&L en vivo: la lista de posiciones sigue la línea de tiempo, "
        "con títulos, coste medio y ganancia/pérdida moviéndose minuto a minuto; la curva muestra una "
        "etiqueta de compra/venta al pasar por cada operación; la tasa de comisiones pasa a ser un ajuste "
        "de la página; y el valor de posición de la cabecera se calcula en el minuto mostrado, moviéndose "
        "con cada compra y venta. La importación de operaciones pasa a pegado o archivo de hoja de "
        "cálculo, y la lista de posiciones se exporta y reimporta entera en CSV. El cuadro Gestionar "
        "posiciones muestra el último cierre, y su fallo de búsqueda queda corregido; al cerrar, las "
        "operaciones del día aún no registradas se incorporan automáticamente al libro. Los estilos de "
        "título pasan a ser un ajuste global: tres diseños de título y colores elegidos una vez en "
        "Ajustes, y cada página los sigue al momento. Las cuatro páginas de cripto — Comparar, "
        "Movimientos, Dominancia y Rendimientos anuales — llegaron en la versión anterior; esta completa "
        "sus manuales y textos de la tienda en los 14 idiomas.",
    "pt-BR":
        "Esta versão refaz a página de P&L ao vivo: a lista de posições segue a linha do tempo, com "
        "ações, preço médio e lucro/prejuízo se movendo minuto a minuto; a curva mostra um rótulo de "
        "compra/venda ao passar por cada negócio; a taxa de corretagem vira um ajuste da página; e o "
        "valor de posição no cabeçalho é calculado no minuto exibido, movendo-se a cada compra e venda. "
        "A importação de negócios passa a colar ou arquivo de planilha, e a lista de posições pode ser "
        "exportada e reimportada inteira em CSV. O diálogo Gerenciar posições mostra o último "
        "fechamento, e sua falha de busca foi corrigida; ao fechar, os negócios do dia ainda não "
        "registrados entram automaticamente no livro. Os estilos de título viram um ajuste global: três "
        "desenhos de título e cores escolhidos uma vez em Configurações, e todas as páginas os seguem "
        "na hora. As quatro páginas de cripto — Comparar, Movimentos, Dominância e Retornos anuais — "
        "chegaram na versão anterior; esta completa os manuais delas e os textos da loja nos 14 idiomas.",
    "pl":
        "To wydanie przebudowuje stronę wyniku na żywo: lista pozycji podąża za osią czasu — liczba "
        "akcji, cena nabycia i zysk/strata ruszają się co minutę; krzywa pokazuje etykietę "
        "kupna/sprzedaży przy mijaniu każdej transakcji; stawka prowizji staje się ustawieniem strony; "
        "a wartość pozycji w nagłówku jest liczona dla pokazywanej minuty i rusza się przy każdym "
        "kupnie i sprzedaży. Import transakcji przechodzi na wklejanie albo plik arkusza, a listę "
        "pozycji można wyeksportować i zaimportować w całości jako CSV. Okno Zarządzanie pozycjami "
        "pokazuje ostatnie zamknięcie, a jego błąd wyszukiwania jest naprawiony; przy zamykaniu "
        "niezaksięgowane transakcje dnia trafiają automatycznie do księgi. Style tytułu stają się "
        "ustawieniem globalnym: trzy projekty tytułu i barwy wybiera się raz w ustawieniach, a każda "
        "strona od razu za nimi idzie. Cztery strony krypto — Porównanie, Ruchy, Dominacja i Roczne "
        "stopy — przyszły w poprzednim wydaniu; to uzupełnia ich podręczniki i teksty sklepu we "
        "wszystkich 14 językach.",
    "cs":
        "Tato verze přestavuje stránku výsledku živě: seznam pozic sleduje časovou osu — počty akcií, "
        "vstupní cena a zisk/ztráta se hýbou minutu co minutu; křivka ukazuje štítek nákupu/prodeje při "
        "průchodu každým obchodem; sazba poplatků se stává nastavením stránky; a hodnota pozice v "
        "záhlaví se počítá pro zobrazenou minutu a hýbe se s každým nákupem a prodejem. Import obchodů "
        "přechází na vložení nebo tabulkový soubor a seznam pozic lze vyexportovat a znovu načíst celý "
        "jako CSV. Dialog Správa pozic ukazuje poslední uzavření a jeho chyba hledání je opravena; při "
        "uzavření se nezaúčtované obchody dne automaticky zapíší do knihy. Styly titulku se stávají "
        "globálním nastavením: tři podoby titulku a barvy se jednou zvolí v nastavení a každá stránka "
        "je hned následuje. Čtyři krypto stránky — Srovnání, Pohyby, Dominance a Roční výnosy — přišly "
        "v předchozí verzi; tato doplňuje jejich příručky a texty obchodu ve všech 14 jazycích.",
    "ru":
        "Этот выпуск перестраивает страницу «Портфель онлайн»: список позиций следует за шкалой "
        "времени — число акций, себестоимость и прибыль/убыток меняются минута за минутой; кривая "
        "показывает подпись «покупка/продажа», проходя через каждую сделку; ставка комиссии становится "
        "настройкой страницы; а стоимость позиций в шапке считается для показанной минуты и движется "
        "с каждой покупкой и продажей. Импорт сделок переходит на вставку или файл таблицы, а список "
        "позиций можно целиком выгрузить и загрузить обратно в CSV. Диалог управления портфелем "
        "показывает позиции последнего закрытия, ошибка поиска исправлена; при закрытии незаписанные "
        "сделки дня автоматически попадают в книгу. Стили заголовка становятся глобальной настройкой: "
        "три вида заголовка и цвета выбираются один раз в настройках — и каждая страница сразу им "
        "следует. Четыре криптостраницы — Сравнение, Движения, Доминирование и Годовые доходности — "
        "вышли в прошлом выпуске; этот дополняет их руководства и тексты магазина на всех 14 языках.",
    "tr":
        "Bu sürüm Canlı portföy sayfasını yeniden kuruyor: pozisyon listesi zaman çizelgesini izliyor — "
        "hisse adedi, maliyet ve kâr/zarar dakikada bir değişiyor; eğri her işlemin üzerinden geçerken "
        "alış/satış etiketi çıkarıyor; komisyon oranı sayfa ayarı oluyor; ve başlıktaki pozisyon değeri "
        "gösterilen dakika için hesaplanıyor, her alım satımla birlikte hareket ediyor. İşlem aktarımı "
        "yapıştırmaya veya tablo dosyasına geçiyor; pozisyon listesi CSV olarak bütün halde dışa "
        "aktarılıp geri yüklenebiliyor. Portföy yönetimi penceresi son kapanıştaki pozisyonları "
        "gösteriyor ve arama hatası düzeltildi; kapanışta günün henüz kaydedilmemiş işlemleri otomatik "
        "olarak deftere geçiyor. Başlık stilleri genel ayar oluyor: üç başlık tasarımı ve renk ayarlar "
        "sayfasında bir kez seçiliyor ve her sayfa hemen izliyor. Dört kripto sayfası — Karşılaştırma, "
        "Hareketler, Hakimiyet ve Yıllık Getiriler — önceki sürümde gelmişti; bu sürüm 14 dilin "
        "hepsinde kılavuzlarını ve mağaza metinlerini tamamlıyor.",
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
    sys.exit(main())
