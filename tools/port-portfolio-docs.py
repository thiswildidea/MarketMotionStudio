# -*- coding: utf-8 -*-
r"""把 14 份手册的「实时持仓收益」一章改到与当前应用一致。

三处：

1. **手续费那句是假的** —— 那一章还写着「不含手续费」，而费率早在成为页面设置项的那天起
   就是默认开着的（佣金万2.5 最低 5 元、印花税千0.5、过户费万0.1，费用同时进当日收益和
   摊薄成本）。一句已经不成立的话比没有话更糟，因为它正面回答了读者最关心的问题。
   非中文语言把万2.5 写成 0.025% —— 券商的「万几」缩写是中文圈的黑话，直译过去没人懂。

2. **导入那句也是假的** —— 「选截图」的入口整个删掉了。现在的两个入口是粘贴和导入当日
   委托表格（.xlsx）；撤单、废单、未成交自动剔除；缺买卖方向的行挡住导入。新句子里
   「买入」「卖出」二字在各语言里都照写中文原样 —— 解析器认的就是这两个词，写成本语言的
   「买入翻成 buy」等于教读者写一行解析器不认的清单。

3. **补一条列表跟着画面走** —— 播放/拖动时列表显示那一分钟的持仓、当天新开的仓位在其
   成交那一分钟长出一行、卖光的写「已清仓」。这条是新行为，从来没有被写过。

插在哪：第 4 条粗体（买卖点标签）之后，因为它说的也是播放这一件事。
幂等：新句子已经在文件里就跳过。文件编码照原样（帮助手册 LF 无 BOM）。

用法：<venv python> tools/port-portfolio-docs.py     （跑第二遍应当是 14 个 already there）
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listingtext as lt  # noqa: E402

ROOT = lt.HELP

CHAPTER = lt.chapter_of("NavPortfolioPnl")

# ① 手续费：整条替换。前半句照抄原文（那句仍然成立），只换最后那句。
FEES = {
    "zh-Hans": (
        "- **今天的收益从昨收算起**，成交记在它自己那一分钟上 —— 上午买进卖出，曲线在那一分钟拐一下继续走，而不是整段换一条线。不含手续费，所以和券商的「今日盈亏」可能差一笔佣金。",
        "- **今天的收益从昨收算起**，成交记在它自己那一分钟上 —— 上午买进卖出，曲线在那一分钟拐一下继续走，而不是整段换一条线。手续费按这一页设置里的费率算：佣金万2.5、每笔最低 5 元，卖出另收印花税千0.5，买卖两向还有过户费万0.1 —— 就是券商自己的那套数字，可以改，香港的成交也用同一张表。费用同时进当日收益和摊薄成本，所以列表里的成本价对得上券商 App；四项都设成 0 就回到不计费。"),
    "zh-Hant": (
        "- **今天的收益從昨收算起**，成交記在它自己那一分鐘：上午買進賣出，曲線在那一分鐘拐一下繼續走，而不是整段換一條線。不含手續費，所以和券商的「今日損益」可能差一筆佣金。",
        "- **今天的收益從昨收算起**，成交記在它自己那一分鐘：上午買進賣出，曲線在那一分鐘拐一下繼續走，而不是整段換一條線。手續費按這一頁設定裡的費率算：佣金萬2.5、每筆最低 5 元，賣出另收印花稅千0.5，買賣兩向還有過戶費萬0.1 —— 就是券商自己的那套數字，可以改，香港的成交也用同一張表。費用同時進當日損益和攤薄成本，所以列表裡的成本價對得上券商 App；四項都設成 0 就回到不計費。"),
    "en-US": (
        "- **Today's profit is measured from yesterday's close**, and a trade is credited at the minute it happened: buy or sell in the morning and the curve stays continuous through it. Fees are not counted, so the figure can differ from the broker's own by the commission.",
        "- **Today's profit is measured from yesterday's close**, and a trade is credited at the minute it happened: buy or sell in the morning and the curve stays continuous through it. Fees are charged at the rates on the page — a 0.025% commission with a five-yuan floor per fill, 0.05% stamp duty on the sale, a 0.001% transfer fee both ways — the mainland schedule itself, editable, and applied to Hong Kong fills through the same table. They enter the day's curve and the diluted cost alike, which is why the cost beside each row matches the broker's app; set the four rates to zero and the page is back to fee-free."),
    "ja": (
        "- **今日の損益は前日終値から測る。** 約定はその分に入るので、午前に売買しても曲線は途切れない。手数料は含まないため、証券アプリの「今日の損益」とは手数料の分だけずれることがある。",
        "- **今日の損益は前日終値から測る。** 約定はその分に入るので、午前に売買しても曲線は途切れない。手数料はこのページの設定した料率で計算します。売買どちらにも0.025%（1回につき最低5元）、売却には0.05%の印紙税、売買どちらにも0.001%の過戸費 —— 中国本土の証券会社そのものの料率で、変更でき、香港の約定にも同じ表を使います。手数料は当日の損益と平均取得単価の両方に入るので、一覧の単価は証券アプリと一致します。4項目すべて0にすれば手数料なしに戻ります。"),
    "ko": (
        "- **오늘의 손익은 전일 종가에서 잰다.** 체결은 그 분에 반영되므로 오전에 사고팔아도 곡선이 끊기지 않는다. 수수료는 넣지 않으므로 증권 앱의 '오늘 손익'과는 수수료만큼 다를 수 있다.",
        "- **오늘의 손익은 전일 종가에서 잰다.** 체결은 그 분에 반영되므로 오전에 사고팔아도 곡선이 끊기지 않는다. 수수료는 이 페이지 설정의 요율로 계산한다. 매매 양쪽에 0.025%(1회 최저 5위안), 매도에 0.05%의 인지세, 양쪽에 0.001%의 이계비 — 중국 본토 증권사 그 자체의 요율이며 고칠 수 있고 홍콩 체결에도 같은 표를 쓴다. 수수료는 당일 손익과 평균 단가 양쪽에 들어가므로 목록의 단가가 증권 앱과 맞는다. 네 항목을 모두 0으로 하면 수수료 없는 계산으로 돌아간다."),
    "de": (
        "- **Der heutige Gewinn wird ab dem Vortagsschluss gemessen**, und ein Geschäft zählt in der Minute, in der es passiert ist: Kauf oder Verkauf am Vormittag, und die Kurve läuft ohne Sprung durch. Gebühren sind nicht enthalten, deshalb kann die Zahl um die Provision von der des Brokers abweichen.",
        "- **Der heutige Gewinn wird ab dem Vortagsschluss gemessen**, und ein Geschäft zählt in der Minute, in der es passiert ist: Kauf oder Verkauf am Vormittag, und die Kurve läuft ohne Sprung durch. Gebühren werden nach den Sätzen dieser Seite berechnet — 0,025 % Provision je Geschäft (mindestens 5 Yuan), 0,05 % Stempelsteuer beim Verkauf, 0,001 % Übertragungsgebühr je Seite — die Sätze des Festlandbrokers selbst, änderbar, und für Hongkong-Geschäfte gilt dieselbe Tabelle. Sie gehen in die Kurve des Tages wie in die verdünnten Kosten ein, deshalb passt die Kostenzahl neben jeder Zeile zur Broker-App; setzt du alle vier auf null, rechnet die Seite wieder gebührenfrei."),
    "fr": (
        "- **Le gain du jour se mesure depuis la clôture de la veille**, et un ordre compte à la minute où il a été exécuté : acheter ou vendre en matinée et la courbe reste continue. Les frais ne sont pas comptés, d'où un écart possible avec le « gain du jour » du courtier.",
        "- **Le gain du jour se mesure depuis la clôture de la veille**, et un ordre compte à la minute où il a été exécuté : acheter ou vendre en matinée et la courbe reste continue. Les frais suivent les taux de cette page — 0,025 % de commission par ordre (minimum 5 yuans), 0,05 % de droit de timbre à la vente, 0,001 % de frais de transfert dans les deux sens — le barème du courtier continental même, modifiable, et les ordres de Hong Kong passent par la même table. Ils entrent dans la courbe du jour comme dans le coût dilué, si bien que le coût de chaque ligne colle à l'application du courtier ; remettez les quatre à zéro et la page redevient sans frais."),
    "it": (
        "- **Il guadagno di oggi si misura dalla chiusura di ieri**, e un'operazione conta al minuto in cui è avvenuta: comprare o vendere a metà mattina e la curva resta continua. Le commissioni non sono comprese, quindi il numero può differire da quello del broker.",
        "- **Il guadagno di oggi si misura dalla chiusura di ieri**, e un'operazione conta al minuto in cui è avvenuta: comprare o vendere a metà mattina e la curva resta continua. Le commissioni seguono i tassi di questa pagina — 0,025% per operazione (minimo 5 yuan), 0,05% d'imposta di bollo sulla vendita, 0,001% di imposta di trasferimento in entrambi i sensi — il listino del broker continentale stesso, modificabile, e le operazioni di Hong Kong usano la stessa tabella. Entrano nella curva del giorno e nel costo diluito, per questo il costo di ogni riga corrisponde all'app del broker; portate i quattro a zero e la pagina torna a non far pagare nulla."),
    "es": (
        "- **El beneficio de hoy se mide desde el cierre de ayer**, y una operación cuenta en el minuto en que ocurrió: compre o venda a media mañana y la curva sigue sin saltos. No incluye comisiones, así que puede diferir de la cifra del bróker en esa comisión.",
        "- **El beneficio de hoy se mide desde el cierre de ayer**, y una operación cuenta en el minuto en que ocurrió: compre o venda a media mañana y la curva sigue sin saltos. Las comisiones se calculan con las tarifas de esta página — 0,025 % por operación (mínimo 5 yuanes), 0,05 % de impuesto de sello al vender, 0,001 % de tasa de transferencia en ambos sentidos — la tarifa del corredor continental misma, editable, y las operaciones de Hong Kong usan la misma tabla. Entran en la curva del día y en el coste diluido, por eso el coste de cada fila cuadra con la app del bróker; póngalas todas a cero y la página vuelve a no cobrar."),
    "pt-BR": (
        "- **O resultado de hoje é medido a partir do fechamento de ontem**, e uma operação conta no minuto em que aconteceu: comprar ou vender no meio da manhã e a curva continua sem degrau. As taxas não entram, então o número pode diferir do \"resultado de hoje\" da corretora.",
        "- **O resultado de hoje é medido a partir do fechamento de ontem**, e uma operação conta no minuto em que aconteceu: comprar ou vender no meio da manhã e a curva continua sem degrau. As taxas vêm da própria página — 0,025% de corretagem por operação (mínimo de 5 yuanes), 0,05% de imposto de selo na venda, 0,001% de taxa de transferência nos dois lados — a tabela da corretora continental mesma, editável, e as operações de Hong Kong usam a mesma. Elas entram na curva do dia e no custo diluído, e é por isso que o custo de cada linha bate com o app da corretora; zere as quatro e a página volta a não cobrar."),
    "pl": (
        "- **Dzisiejszy wynik liczy się od wczorajszego zamknięcia**, a transakcja wchodzi w minucie, w której się zdarzyła: kupno lub sprzedaż przed południem, a krzywa biegnie bez skoku. Prowizji nie ma, więc liczba może różnić się od tej w aplikacji brokera.",
        "- **Dzisiejszy wynik liczy się od wczorajszego zamknięcia**, a transakcja wchodzi w minucie, w której się zdarzyła: kupno lub sprzedaż przed południem, a krzywa biegnie bez skoku. Prowizje liczą się według stawek z tej strony — 0,025% prowizji od zlecenia (minimum 5 juanów), 0,05% podatku przy sprzedaży, 0,001% opłaty za transfer w obie strony — to stawki kontynentalnego brokera same, do zmiany, a transakcje z Hongkongu używają tej samej tabeli. Wchodzą w krzywą dnia i w rozcieńczony koszt, dlatego koszt przy każdym wierszu zgadza się z aplikacją brokera; ustaw wszystkie cztery na zero, a strona wróci do liczenia bez prowizji."),
    "cs": (
        "- **Dnešní výsledek se měří od včerejšího zavření** a obchod se započítá v minutě, kdy se stal: nákup či prodej dopoledne a křivka jde dál bez skoku. Poplatky v tom nejsou, takže číslo se může od brokera lišit právě o provizi.",
        "- **Dnešní výsledek se měří od včerejšího zavření** a obchod se započítá v minutě, kdy se stal: nákup či prodej dopoledne a křivka jde dál bez skoku. Poplatky se počítají podle sazeb na této stránce — 0,025 % provize z obchodu (minimálně 5 juanů), 0,05 % kolkového při prodeji, 0,001 % převodního poplatku na obou stranách — to jsou sazby kontinentálního brokera samy, lze je změnit, a obchody z Hongkongu používají tutéž tabulku. Vstupují do křivky dne i do zředěných nákladů, proto cena u každého řádku odpovídá aplikaci brokera; nastavte všechny čtyři na nulu a stránka se vrátí k počítání bez poplatků."),
    "ru": (
        "- **Сегодняшний результат считается от вчерашнего закрытия**, а сделка входит в ту минуту, когда произошла: покупка или продажа утром — и кривая идёт без разрыва. Комиссии не учтены, поэтому число может отличаться от «результата дня» у брокера.",
        "- **Сегодняшний результат считается от вчерашнего закрытия**, а сделка входит в ту минуту, когда произошла: покупка или продажа утром — и кривая идёт без разрыва. Комиссии берутся по ставкам этой страницы — 0,025% комиссии со сделки (минимум 5 юаней), 0,05% гербового сбора при продаже, 0,001% сбора за перевод в обе стороны — это ставки материкового брокера сами, их можно менять, и сделки Гонконга идут по той же таблице. Они входят и в кривую дня, и в усреднённую цену, поэтому цена у каждой строки сходится с приложением брокера; поставьте все четыре на ноль — и страница снова считает без комиссий."),
    "tr": (
        "- **Bugünün kârı dünkü kapanıştan ölçülür** ve işlem gerçekleştiği dakikaya yazılır: sabah alıp satarsanız eğri kopmaz. Komisyon dahil değildir, bu yüzden sayı aracı kurumun \"günlük kâr\"ından komisyon kadar farklı olabilir.",
        "- **Bugünün kârı dünkü kapanıştan ölçülür** ve işlem gerçekleştiği dakikaya yazılır: sabah alıp satarsanız eğri kopmaz. Ücretler bu sayfanın oranlarıyla hesaplanır — işlem başına %0,025 komisyon (en az 5 yuan), satışta %0,05 damga vergisi, iki yönde de %0,001 devir ücreti — kara tarafı aracı kurumun kendi oranları, değiştirilebilir ve Hong Kong işlemleri de aynı tabloyu kullanır. Ücretler günün eğrisine de seyreltilmiş maliyete de girer, bu yüzden her satırın yanındaki maliyet aracı kurumun uygulamasıyla uyuşur; dördünü de sıfıra alırsanız sayfa yeniden ücretsiz hesaplar."),
}

# ② 导入：整条替换。截图的入口已经删了，两个入口是粘贴与表格。
IMPORT = {
    "zh-Hans": (
        "- **导入成交可以选截图，也可以直接粘。** 截图用 Windows 自带的识别引擎在本机读（不上传），认出来的字落在一个可以改的框里；解析结果逐行列出，有一行读不出来就不让导入。同一份清单导两次没有副作用：日、时、代码、方向、价、量六样一起才认成一笔。",
        "- **导入成交靠粘贴，也靠表格。** 当天的成交记录可以直接粘进框里，也可以导入券商导出的当日委托表格（.xlsx），方向、代码、价格、数量、时刻照表格的列读。撤单、废单和没有成交的行自动剔掉，不会当成成交进来。解析结果逐行列出，有一行读不出来、或缺了买卖方向，就不让导入 —— 表格每行自带方向，手工粘的要在行首写上「买入」或「卖出」。同一份清单导两次没有副作用：日、时、代码、方向、价、量六样一起才认成一笔。"),
    "zh-Hant": (
        "- **匯入成交可以選截圖，也可以直接貼上。** 截圖用 Windows 內建的辨識引擎在本機讀（不上傳），辨識結果落在一個可以修改的框裡；解析結果逐行列出來，有一行讀不出來就不讓匯入。同一份清單匯兩次沒有副作用：日、時、代碼、方向、價、量六樣一起才認成一筆。",
        "- **匯入成交靠貼上，也靠表格。** 當天的成交記錄可以直接貼進框裡，也可以匯入券商匯出的當日委託表格（.xlsx），方向、代碼、價格、數量、時刻照表格的欄位讀。撤單、廢單和沒有成交的列自動剔除，不會當成成交進來。解析結果逐行列出，有一列讀不出來、或缺了買賣方向，就不讓匯入 —— 表格每列自帶方向，手工貼的要在列首寫上「買入」或「賣出」。同一份清單匯兩次沒有副作用：日、時、代碼、方向、價、量六樣一起才認成一筆。"),
    "en-US": (
        "- **Importing is a screenshot or a paste.** A screenshot is read on this machine by the OCR that ships with Windows (nothing is uploaded), the recognised text lands in a box you can correct, and the parse is shown row by row; one unreadable row and nothing is applied. Importing the same list twice is harmless: day, minute, code, side, price and size together recognise a row that is already in the book.",
        "- **Importing is a paste or a sheet.** The day's fills go in straight from the clipboard, or from the order sheet the broker exports (.xlsx), whose columns carry the side, the code, the price, the size and the minute. Cancelled, rejected and unfilled rows are dropped on the way in — they never become trades. The parse is shown row by row, and one unreadable row, or one without its side, holds the import: the sheet carries the side on every row, and pasted text states it at the head of the line — 买入 or 卖出. Importing the same list twice is harmless: day, minute, code, side, price and size together recognise a row that is already in the book."),
    "ja": (
        "- **約定の取り込みはスクリーンショットか貼り付け。** スクリーンショットは Windows 内蔵の OCR でこの端末上で読む（送信しない）。読み取った文字は修正できる欄に入り、解析結果は一行ずつ並ぶ。読めない行が一つでもあれば取り込まない。同じリストを二度取り込んでも害はない —— 日付・時刻・コード・売買・価格・数量が揃って初めて同じ約定とみなす。",
        "- **約定の取り込みは貼り付けか表。** 当日の約定はそのまま欄に貼っても、証券会社が書き出した当日の注文表（.xlsx）を取り込んでもいい。表からは売買・コード・価格・数量・時刻を列ごとに読む。取消・無効・未成立の行は自動的に除かれ、約定としては扱われない。解析結果は一行ずつ並び、読めない行が一つでも、売買の向きが欠けている行が一つでもあれば取り込まない —— 表にはどの行にも向きが付き、手で貼った文は行頭に「买入」「卖出」を書く。同じリストを二度取り込んでも害はない —— 日付・時刻・コード・売買・価格・数量が揃って初めて同じ約定とみなす。"),
    "ko": (
        "- **체결 가져오기는 스크린샷이나 붙여넣기.** 스크린샷은 Windows에 들어 있는 OCR로 이 컴퓨터에서 읽는다(올리지 않는다). 읽은 글자는 고칠 수 있는 칸에 들어가고, 해석 결과는 한 줄씩 보여 준다. 읽지 못한 줄이 하나라도 있으면 가져오지 않는다. 같은 목록을 두 번 가져와도 무해하다 — 날짜·시각·코드·방향·가격·수량이 모두 같아야 이미 있는 체결로 본다.",
        "- **체결 가져오기는 붙여넣기나 표.** 당일 체결은 그대로 칸에 붙여도 되고, 증권사가 내보낸 당일 주문 표(.xlsx)를 가져와도 된다. 표에서는 방향·코드·가격·수량·시각을 열별로 읽는다. 취소·무효·미체결 행은 자동으로 걸러지며 체결로 쳐주지 않는다. 해석 결과는 한 줄씩 보여 주며, 읽지 못한 줄이 하나라도, 방향이 빠진 줄이 하나라도 있으면 가져오지 않는다 — 표에는 어느 행에나 방향이 있고, 손으로 붙인 글은 행 앞에 '买入'나 '卖出'를 적는다. 같은 목록을 두 번 가져와도 무해하다 — 날짜·시각·코드·방향·가격·수량이 모두 같아야 이미 있는 체결로 본다."),
    "de": (
        "- **Orderimport geht per Screenshot oder per Einfügen.** Ein Screenshot wird auf diesem Rechner von der in Windows eingebauten OCR gelesen (nichts wird hochgeladen), der erkannte Text landet in einem korrigierbaren Feld, und das Ergebnis wird Zeile für Zeile gezeigt; eine unlesbare Zeile verhindert den Import. Dieselbe Liste zweimal zu importieren ist harmlos: Tag, Minute, Code, Richtung, Preis und Stückzahl zusammen erkennen eine bereits gebuchte Zeile.",
        "- **Orderimport geht per Einfügen oder per Tabelle.** Die Geschäfte des Tages kommen direkt aus der Zwischenablage oder aus dem Orderblatt, das der Broker exportiert (.xlsx), dessen Spalten Richtung, Code, Preis, Stückzahl und Minute tragen. Stornierte, abgewiesene und nicht ausgeführte Zeilen fallen unterwegs heraus — sie werden nie zu Geschäften. Das Ergebnis wird Zeile für Zeile gezeigt, und eine unlesbare Zeile oder eine ohne Richtung hält den Import auf: Die Tabelle trägt die Richtung in jeder Zeile, eingefügter Text stellt sie an den Zeilenanfang — 买入 oder 卖出. Dieselbe Liste zweimal zu importieren ist harmlos: Tag, Minute, Code, Richtung, Preis und Stückzahl zusammen erkennen eine bereits gebuchte Zeile."),
    "fr": (
        "- **L'import des ordres se fait par capture d'écran ou par collage.** La capture est lue sur cette machine par l'OCR fourni avec Windows (rien n'est envoyé), le texte reconnu arrive dans une zone corrigeable, et le résultat est présenté ligne par ligne ; une seule ligne illisible annule l'import. Importer deux fois la même liste est sans effet : jour, minute, code, sens, prix et quantité ensemble reconnaissent une ligne déjà enregistrée.",
        "- **L'import des ordres se fait par collage ou par tableur.** Les ordres du jour arrivent directement du presse-papiers, ou de la feuille d'ordres exportée par le courtier (.xlsx), dont les colonnes portent le sens, le code, le prix, la quantité et la minute. Les lignes annulées, rejetées ou non exécutées sont écartées en route — elles ne deviennent jamais des ordres. Le résultat est présenté ligne par ligne, et une ligne illisible, ou sans son sens, retient l'import : la feuille porte le sens sur chaque ligne, et le texte collé l'écrit en tête de ligne — 买入 ou 卖出. Importer deux fois la même liste est sans effet : jour, minute, code, sens, prix et quantité ensemble reconnaissent une ligne déjà enregistrée."),
    "it": (
        "- **L'importazione degli ordini è uno screenshot o un incolla.** Lo screenshot viene letto su questa macchina dall'OCR di Windows (nulla viene inviato), il testo riconosciuto arriva in un riquadro correggibile e il risultato è mostrato riga per riga; una sola riga illeggibile blocca l'importazione. Importare due volte lo stesso elenco non fa danni: giorno, minuto, codice, lato, prezzo e quantità insieme riconoscono una riga già registrata.",
        "- **L'importazione degli ordini è un incolla o un foglio.** Le operazioni del giorno arrivano direttamente dagli appunti o dal foglio ordini esportato dal broker (.xlsx), le cui colonne portano lato, codice, prezzo, quantità e minuto. Le righe annullate, rifiutate e non eseguite vengono scartate lungo la strada — non diventano mai operazioni. Il risultato è mostrato riga per riga, e una riga illeggibile, o senza il suo lato, trattiene l'importazione: il foglio porta il lato su ogni riga, e il testo incollato lo scrive in testa alla riga — 买入 o 卖出. Importare due volte lo stesso elenco non fa danni: giorno, minuto, codice, lato, prezzo e quantità insieme riconoscono una riga già registrata."),
    "es": (
        "- **La importación de órdenes es una captura de pantalla o un pegado.** La captura se lee en este equipo con el OCR que incluye Windows (no se sube nada), el texto reconocido llega a una caja corregible y el resultado se muestra fila por fila; una sola fila ilegible impide importar. Importar dos veces la misma lista es inofensivo: día, minuto, código, sentido, precio y cantidad juntos reconocen una fila ya registrada.",
        "- **La importación de órdenes es un pegado o una hoja.** Las operaciones del día entran directamente del portapapeles, o de la hoja de órdenes que exporta el bróker (.xlsx), cuyas columnas traen el sentido, el código, el precio, la cantidad y el minuto. Las filas anuladas, rechazadas y sin ejecutar se descartan por el camino — nunca se vuelven operaciones. El resultado se muestra fila por fila, y una fila ilegible, o sin su sentido, retiene la importación: la hoja trae el sentido en cada fila, y el texto pegado lo escribe al principio de la línea — 买入 o 卖出. Importar dos veces la misma lista es inofensivo: día, minuto, código, sentido, precio y cantidad juntos reconocen una fila ya registrada."),
    "pt-BR": (
        "- **A importação de ordens é um print ou uma colagem.** O print é lido nesta máquina pelo OCR que vem com o Windows (nada é enviado), o texto reconhecido cai numa caixa corrigível e o resultado aparece linha por linha; uma linha ilegível impede a importação. Importar a mesma lista duas vezes é inofensivo: dia, minuto, código, lado, preço e quantidade juntos reconhecem uma linha já registrada.",
        "- **A importação de ordens é uma colagem ou uma planilha.** As operações do dia entram direto da área de transferência, ou da planilha de ordens que a corretora exporta (.xlsx), cujas colunas trazem o lado, o código, o preço, a quantidade e o minuto. Linhas canceladas, rejeitadas e não executadas são descartadas no caminho — nunca viram operações. O resultado aparece linha por linha, e uma linha ilegível, ou sem o lado, segura a importação: a planilha traz o lado em cada linha, e o texto colado o escreve no começo da linha — 买入 ou 卖出. Importar a mesma lista duas vezes é inofensivo: dia, minuto, código, lado, preço e quantidade juntos reconhecem uma linha já registrada."),
    "pl": (
        "- **Import zleceń to zrzut ekranu albo wklejenie.** Zrzut czyta na tym komputerze OCR wbudowany w Windows (nic nie jest wysyłane), rozpoznany tekst trafia do pola, które można poprawić, a wynik jest pokazywany wiersz po wierszu; jeden nieczytelny wiersz wstrzymuje import. Dwukrotny import tej samej listy nic nie psuje: dzień, minuta, kod, strona, cena i liczba akcji razem rozpoznają już zapisany wiersz.",
        "- **Import zleceń to wklejenie albo arkusz.** Transakcje dnia wchodzą prosto ze schowka albo z arkusza zleceń wyeksportowanego przez brokera (.xlsx), którego kolumny niosą stronę, kod, cenę, liczbę akcji i minutę. Wiersze anulowane, odrzucone i niezrealizowane odpadają po drodze — nigdy nie stają się transakcjami. Wynik jest pokazywany wiersz po wierszu, a jeden nieczytelny wiersz albo wiersz bez strony wstrzymuje import: arkusz niesie stronę w każdym wierszu, a wklejony tekst zapisuje ją na początku wiersza — 买入 albo 卖出. Dwukrotny import tej samej listy nic nie psuje: dzień, minuta, kod, strona, cena i liczba akcji razem rozpoznają już zapisany wiersz."),
    "cs": (
        "- **Import pokynů je snímek obrazovky nebo vložení.** Snímek čte na tomto počítači OCR, které je součástí Windows (nic se neodesílá), rozpoznaný text se objeví v poli, které lze opravit, a výsledek se vypíše řádek po řádku; jediný nepřečtený řádek import zablokuje. Dvakrát importovaný stejný seznam nic nezkazí: den, minuta, kód, strana, cena a počet akcií dohromady rozpoznají už zapsaný řádek.",
        "- **Import pokynů je vložení nebo tabulka.** Obchody dne přijdou přímo ze schránky nebo z tabulky pokynů, kterou broker exportuje (.xlsx), a jež v sloupcích nese stranu, kód, cenu, počet akcí a minutu. Zrušené, odmítnuté a nerealizované řádky cestou odpadnou — nikdy se nestanou obchody. Výsledek se vypíše řádek po řádku, a jeden nepřečtený řádek nebo řádek bez strany import zadrží: tabulka nese stranu v každém řádku, a vložený text ji píše na začátek řádku — 买入 nebo 卖出. Dvakrát importovaný stejný seznam nic nezkazí: den, minuta, kód, strana, cena a počet akcií dohromady rozpoznají už zapsaný řádek."),
    "ru": (
        "- **Импорт заявок — это снимок экрана или вставка.** Снимок читается на этой машине OCR, встроенным в Windows (никуда не отправляется), распознанный текст попадает в поле, которое можно поправить, а результат показывается построчно; одна нечитаемая строка отменяет импорт. Повторный импорт того же списка безвреден: день, минута, код, сторона, цена и количество вместе узнают уже записанную строку.",
        "- **Импорт заявок — это вставка или таблица.** Сделки дня входят прямо из буфера обмена или из таблицы заявок, которую выгружает брокер (.xlsx): её столбцы несут сторону, код, цену, количество и минуту. Отменённые, отклонённые и неисполненные строки отсеиваются по дороге — сделками они никогда не становятся. Результат показывается построчно, и одна нечитаемая строка, или строка без стороны, задерживает импорт: в таблице сторона стоит в каждой строке, а во вставленном тексте она пишется в начале строки — 买入 или 卖出. Повторный импорт того же списка безвреден: день, минута, код, сторона, цена и количество вместе узнают уже записанную строку."),
    "tr": (
        "- **Emir içe aktarma bir ekran görüntüsü ya da yapıştırmadır.** Görüntü bu makinede Windows'un kendi OCR'ı ile okunur (hiçbir yere gönderilmez), tanınan metin düzeltilebilir bir kutuya düşer ve sonuç satır satır gösterilir; okunamayan tek satır aktarmayı durdurur. Aynı listeyi iki kez aktarmak zararsızdır: gün, dakika, kod, yön, fiyat ve adet birlikte, defterde zaten olan satırı tanır.",
        "- **Emir içe aktarma bir yapıştırma ya da bir tablodur.** Günün işlemleri doğrudan panodan ya da aracı kurumun dışa aktardığı emir tablosundan (.xlsx) girer; tablonun sütunları yönü, kodu, fiyatı, adedi ve dakikayı taşır. İptal edilen, reddedilen ve gerçekleşmeyen satırlar yolda ayıklanır — asla işleme dönüşmezler. Sonuç satır satır gösterilir ve okunamayan tek bir satır, ya da yönü eksik bir satır, aktarmayı durdurur: tabloda her satırda yön vardır, yapıştırılan metin ise onu satırın başına yazar — 买入 veya 卖出. Aynı listeyi iki kez aktarmak zararsızdır: gün, dakika, kod, yön, fiyat ve adet birlikte, defterde zaten olan satırı tanır."),
}

# ③ 新增一条：列表跟着画面走。插在第 4 条粗体（买卖点标签）之后。
LIST_FOLLOWS = {
    "zh-Hans": "- **持仓列表跟着画面走。** 播放或拖动进度条，列表显示的就是画面停下的那一分钟的持仓：股数与成本价停在该分钟的数上，当天才买进的新仓位在它成交的那一分钟长出一行，当天卖光的留在原地写「已清仓」。列表和曲线读的永远是同一帧，不会各说各话。",
    "zh-Hant": "- **持倉列表跟著畫面走。** 播放或拖動進度條，列表顯示的就是畫面停下的那一分鐘的持倉：股數與成本價停在該分鐘的數上，當天才買進的新倉位在它成交的那一分鐘長出一行，當天賣光的留在原地寫「已清倉」。列表和曲線讀的永遠是同一幀，不會各說各話。",
    "en-US": "- **The holdings list moves with the picture.** Play or scrub, and the list shows the minute the frame has stopped on: shares and diluted cost sit at that minute's figures, a position opened today grows its row at the minute of its first fill, and one sold out during the day stays where it is, marked sold out. List and curve always read the same frame, so the two can never disagree.",
    "ja": "- **保有銘柄の一覧は画面に合わせて動く。** 再生やスクラブでは、一覧は画面が止まったその分の時点の保有を示します。株数と取得単価はその分の値に止まり、当日新たに買った銘柄はその約定の分に行が増え、当日売り切った銘柄は「売り切り」と書かれたままその場に残ります。一覧と曲線は常に同じフレームを読むので、食い違うことがありません。",
    "ko": "- **보유 목록은 화면을 따라 움직인다.** 재생하거나 슬라이더를 끌면 목록은 화면이 멈춘 그 분의 보유를 보여 준다. 주식 수와 평균 단가는 그 분의 값에 멈추고, 오늘 새로 산 종목은 체결된 그 분에 행이 늘어나며, 오늘 다 판 종목은 '전량 매도'라고 쓰인 채 제자리에 남는다. 목록과 곡선은 언제나 같은 프레임을 읽으므로 서로 어긋나지 않는다.",
    "de": "- **Die Liste der Bestände bewegt sich mit dem Bild.** Beim Abspielen oder Ziehen der Leiste zeigt die Liste die Minute, auf der das Bild steht: Stückzahl und verdünnte Kosten stehen auf den Zahlen dieser Minute, ein heute neu gekaufter Posten bekommt in der Minute seines ersten Geschäfts eine Zeile, und ein heute ganz verkaufter Posten bleibt als verkauft gekennzeichnet, wo er ist. Liste und Kurve lesen immer denselben Rahmen und können sich daher nicht widersprechen.",
    "fr": "- **La liste des lignes suit l'image.** En lecture ou en glissement, la liste montre la minute sur laquelle l'image s'est arrêtée : les titres et le coût dilué restent aux valeurs de cette minute, une position ouverte aujourd'hui fait pousser sa ligne à la minute de son premier ordre, et une position vendue en entier reste où elle est, marquée vendue. La liste et la courbe lisent toujours la même image, elles ne peuvent donc pas se contredire.",
    "it": "- **L'elenco delle posizioni segue l'immagine.** Durante la riproduzione o lo scorrimento, l'elenco mostra il minuto su cui l'immagine si è fermata: azioni e costo diluito restano ai valori di quel minuto, una posizione aperta oggi fa crescere la sua riga al minuto del primo ordine, e una posizione venduta tutta resta dov'è, segnalata come venduta. Elenco e curva leggono sempre la stessa immagine, quindi non possono contraddirsi.",
    "es": "- **La lista de posiciones sigue a la imagen.** Al reproducir o arrastrar la barra, la lista muestra el minuto en que la imagen se detuvo: las acciones y el coste diluido quedan en las cifras de ese minuto, una posición abierta hoy hace crecer su fila en el minuto de su primera operación, y una posición vendida por completo permanece donde está, marcada como vendida. La lista y la curva leen siempre la misma imagen, así que no pueden contradecirse.",
    "pt-BR": "- **A lista de posições acompanha a imagem.** Ao reproduzir ou arrastar a barra, a lista mostra o minuto em que a imagem parou: as ações e o custo diluído ficam nos números desse minuto, uma posição aberta hoje ganha sua linha no minuto da primeira operação, e uma posição vendida por inteiro permanece onde está, marcada como vendida. Lista e curva leem sempre o mesmo quadro, então nunca se contradizem.",
    "pl": "- **Lista pozycji podąża za obrazem.** Przy odtwarzaniu lub przesuwaniu suwaka lista pokazuje minutę, na której zatrzymał się obraz: liczba akcji i rozcieńczony koszt stoją na liczbach tej minuty, pozycja kupiona dziś dorzuca swój wiersz w minucie pierwszej transakcji, a pozycja sprzedana do zera zostaje na miejscu, oznaczona jako sprzedana. Lista i krzywa czytają zawsze tę samą klatkę, więc nie mogą sobie przeczyć.",
    "cs": "- **Seznam pozic jde s obrazem.** Při přehrávání nebo posouvání ukazuje seznam minutu, na které obraz stojí: počet akcí a zředěné náklady stojí na číslech té minuty, pozice koupená dnes přidá svůj řádek v minutě prvního obchodu a pozice prodaná do nuly zůstane na místě, označená jako prodaná. Seznam a křivka čtou vždy týž snímek, takže si nemohou odporovat.",
    "ru": "- **Список позиций движется вместе с картинкой.** При воспроизведении или перетаскивании полосы список показывает минуту, на которой остановился кадр: количество акций и усреднённая цена стоят на цифрах этой минуты, позиция, открытая сегодня, отращивает свою строку в минуту первой сделки, а позиция, проданная дотла, остаётся на месте с пометкой «продано». Список и кривая читают всегда один и тот же кадр, поэтому противоречить друг другу они не могут.",
    "tr": "- **Pozisyon listesi görüntüyle birlikte hareket eder.** Oynatma ya da çubuğu sürükleme sırasında liste, karenin durduğu dakikayı gösterir: hisse adedi ve seyreltilmiş maliyet o dakikanın sayılarında kalır, bugün açılan bir pozisyon ilk işleminin dakikasında satırını büyütür, gün içinde tamamen satılan pozisyon ise 'satıldı' yazılı olduğu yerde kalır. Liste ile eğri her zaman aynı kareyi okur, bu yüzden asla çelişmezler.",
}


def main():
    for tag in lt.LANGS:
        path = ROOT / f"help-{tag}.md"

        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw.decode("utf-8-sig")

        crlf = "\r\n" in body
        if crlf:
            body = body.replace("\r\n", "\n")

        lines = body.split("\n")
        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
        start = heads[CHAPTER]
        end = heads[CHAPTER + 1] if CHAPTER + 1 < len(heads) else len(lines)

        changed = 0

        # ① ② 整行替换（只在目标章里找，别的章不动）。
        for old, new in (FEES[tag], IMPORT[tag]):
            hit = [i for i in range(start, end) if lines[i].strip() == old]

            if hit:
                lines[hit[0]] = new
                changed += 1
            elif not any(lines[i].strip() == new for i in range(start, end)):
                raise AssertionError(f"{tag}: 既找不到旧句也不是新句 —— 手册被改过？{old[:60]}…")

        # ③ 新条插在第 4 条粗体之后。
        if not any(lines[i].strip() == LIST_FOLLOWS[tag] for i in range(start, end)):
            bolds = [i for i in range(start, end) if lines[i].startswith("- **")]

            assert len(bolds) >= 4, f"{tag}: 粗体条不够（{len(bolds)}）"

            at = bolds[3] + 1
            block = ["", LIST_FOLLOWS[tag]] if lines[at].strip() == "" else [LIST_FOLLOWS[tag]]
            lines[at:at] = block
            changed += 1

        if not changed:
            print(f"{tag:9} already there")
            continue

        rebuilt = "\n".join(lines)

        if crlf:
            rebuilt = rebuilt.replace("\n", "\r\n")

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rebuilt.encode("utf-8"))

        print(f"{tag:9} +{changed}")


if __name__ == "__main__":
    main()
