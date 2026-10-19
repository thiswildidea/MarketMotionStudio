# -*- coding: utf-8 -*-
r"""给 14 份 help-*.md 补上「实时持仓收益」这一章。

**位置由导航算，不抄行号。** 这一章插在「持仓收益」与「加密货币 K 线」之间，也就是导航里
`NavPortfolioPnl` 那一项的位置 —— `listingtext.chapter_of("NavPortfolioPnl")` 读
`MainWindow.xaml` 的顺序，往前数两章领头的那两节。写死「第 21 章」会在这份手册再插一章时
指向别处，而错法很安静：整章还在，只是挂到了别的页名下。

**这一章必须有。** 往导航里插一页而不给手册补一章，后面每一章都整体前移一位：
`verify-docs.py` 的 `picture_checks` 拿 `chapter_of` 去点各章的配图，于是从加密 K 线那章
起全部指错（实测一次报红 84 项）—— 报的是「这一章点的是上一张图」，而真正的病根在这里。

**幂等**：标题已经在这份文件里就跳过。**换行按原文**：help-*.md 是 LF 无 BOM（实测）。

用法：python tools\port-portfolio-help.py
"""

import pathlib
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
HELP = TOOLS.parent / "src" / "MarketMotionStudio" / "Assets" / "Help"

sys.path.insert(0, str(TOOLS))

import listingtext  # noqa: E402

LANGS = listingtext.LANGS

# 每份手册的这一章：标题、导语、条目。事实只有一个来源（这一页的行为），14 份说的是同一件事。
NEW = {
    "zh-Hans": (
        "实时持仓收益",
        "自己持有的那几只，按分钟记着今天挣了多少：从 9:30 到收盘的收益曲线，开市时自动刷新。",
        [
            "**这份持仓是你自己的。** 按代码添加一只，股数和成本照券商 App 填；也可以每天把当天的成交记录导进来。"
            "代码自带交易所 —— `sh`、`sz`、`bj` 是内地三个市场，`hk` 是港股 —— 所以一份账本能同时装着两边，"
            "港股的持仓按港元记账。",

            "**成本是摊薄成本**，也就是券商 App 写在那一行旁边的数：买入摊到全部股数上，卖出把成交额从剩余股数的成本里扣掉"
            "（卖得比成本高就摊低，卖得比成本低就摊高），卖光了这只就从账本上消失。"
            "导入成交之后给一个券商不认的成本，这一页每个数字都会和你用来核对的 App 对不上。",

            "**今天的收益从昨收算起**，成交记在它自己那一分钟上 —— 上午买进卖出，曲线在那一分钟拐一下继续走，"
            "而不是整段换一条线。不含手续费，所以和券商的「今日盈亏」可能差一笔佣金。",

            "**横轴从 9:30 走到真正开市那些市场的收盘**：沪深 15:00、港股 16:00。午间休市画成一条带子并写上"
            "「午间休市」，而不是画成两小时不动的平线。一边休市时，那几只标着「休市」、不进曲线，"
            "而不是拿上一场的价冒充今天。",

            "**开市时自动刷新**：工作日 9:15 到 16:10 之间每 30 秒读一次，开关关掉就不读。"
            "收盘之后也不再问 —— 一天已经定了，每半分钟问一次只会得到同一组数。",

            "**导入成交可以选截图，也可以直接粘。** 截图用 Windows 自带的识别引擎在本机读（不上传），"
            "认出来的字落在一个可以改的框里；解析结果逐行列出，有一行读不出来就不让导入。"
            "同一份清单导两次没有副作用：日、时、代码、方向、价、量六样一起才认成一笔。",

            "账本存在应用自己的目录里，重启还在。这一页也是唯一一页「画的是读者自己」的 —— "
            "别的页画市场，金额算的都是当时那个市场的钱。",

            "第一本账是从这一页做出来时的那九只开始的；不用的逐行移除，再添自己的。",
        ],
    ),
    "zh-Hant": (
        "即時持倉收益",
        "自己持有的那幾檔，按分鐘記著今天賺了多少：從 9:30 到收盤的收益曲線，開市時自動更新。",
        [
            "**這份持倉是你自己的。** 按代碼加入一檔，股數與成本照券商 App 填；也可以每天把當天的成交紀錄匯進來。"
            "代碼自帶交易所 —— `sh`、`sz`、`bj` 是內地三個市場，`hk` 是港股 —— 所以一本帳能同時裝兩邊，"
            "港股的持倉按港元記帳。",

            "**成本是攤薄成本**，也就是券商 App 寫在那一行旁邊的數字：買進攤到全部股數上，賣出把成交金額從剩餘股數的成本裡扣掉"
            "（賣得比成本高就攤低，賣得比成本低就攤高），賣光的那一檔就從帳本上消失。",

            "**今天的收益從昨收算起**，成交記在它自己那一分鐘：上午買進賣出，曲線在那一分鐘拐一下繼續走，"
            "而不是整段換一條線。不含手續費，所以和券商的「今日損益」可能差一筆佣金。",

            "**橫軸從 9:30 走到真正開市那些市場的收盤**：滬深 15:00、港股 16:00。午間休市畫成一條帶子並標上"
            "「午間休市」，而不是畫成兩小時不動的平線。一邊休市時，那幾檔標著「休市」、不進曲線，"
            "而不是拿上一場的價冒充今天。",

            "**開市時自動更新**：週一到週五 9:15 到 16:10 之間每 30 秒讀一次，開關關掉就不讀。"
            "收盤之後也不再問 —— 一天已經定了。",

            "**匯入成交可以選截圖，也可以直接貼上。** 截圖用 Windows 內建的辨識引擎在本機讀（不上傳），"
            "辨識結果落在一個可以修改的框裡；解析結果逐行列出來，有一行讀不出來就不讓匯入。"
            "同一份清單匯兩次沒有副作用：日、時、代碼、方向、價、量六樣一起才認成一筆。",

            "帳本存在應用程式自己的資料夾裡，重新啟動還在。這一頁也是唯一一頁「畫的是讀者自己」的 —— "
            "別的頁畫市場，金額算的都是當時那個市場的錢。",

            "第一本帳是從這一頁做出來時的那九檔開始的；不用的逐列移除，再添自己的。",
        ],
    ),
    "en-US": (
        "Live portfolio P&L",
        "Your own holdings, marked to the minute: what today has made or cost since 09:30, refreshed while the market is open.",
        [
            "**The book is yours.** Add a holding by its code with the shares and the cost your broker shows, or import "
            "the day's filled orders. Codes carry their venue — `sh`, `sz` and `bj` for the mainland's three boards, `hk` "
            "for Hong Kong — so one book holds both, and a Hong Kong cost is kept in Hong Kong dollars.",

            "**Cost is the diluted figure**, the one the broker app prints beside the position: a purchase spreads over "
            "every share, a sale nets its proceeds off what the rest of them cost (lowering it when the sale was above "
            "cost and raising it when it was not), and selling out takes the name off the book. Importing trades and then "
            "showing a cost the broker does not show would make every figure here disagree with the app it is checked against.",

            "**Today's profit is measured from yesterday's close**, and a trade is credited at the minute it happened: buy "
            "or sell in the morning and the curve stays continuous through it. Fees are not counted, so the figure can "
            "differ from the broker's own by the commission.",

            "**The axis runs from 09:30 to the close of the venues that actually traded.** Shanghai and Shenzhen end at "
            "15:00, Hong Kong at 16:00, and the lunch break is shaded and named rather than drawn as two hours of flat "
            "line. A venue closed for the day leaves its holdings marked closed and out of the curve, rather than priced "
            "off a session that is not today's.",

            "**Refresh is automatic while the market is open**: every 30 seconds on weekdays between 09:15 and 16:10, "
            "while the switch is on. After the close it stops asking — a settled day answers every poll with the same numbers.",

            "**Importing is a screenshot or a paste.** A screenshot is read on this machine by the OCR that ships with "
            "Windows (nothing is uploaded), the recognised text lands in a box you can correct, and the parse is shown row "
            "by row; one unreadable row and nothing is applied. Importing the same list twice is harmless: day, minute, "
            "code, side, price and size together recognise a row that is already in the book.",

            "The book lives in the app's own folder and survives restarts. This is also the one page whose subject is the "
            "reader — every other page draws a market, and its amounts are in the currency of the market in force.",

            "The first book is the nine positions this page was built from; remove them a row at a time and add your own.",
        ],
    ),
    "ja": (
        "リアルタイム保有損益",
        "自分の保有銘柄を分単位で評価する：9:30 から引けまでの今日の損益曲線。取引時間中は自動で更新される。",
        [
            "**台帳は自分のもの。** 銘柄コードで追加し、株数とコストは証券アプリに出ている数字をそのまま入れる。"
            "当日の約定履歴を取り込むこともできる。コードが市場を表す —— `sh` `sz` `bj` は中国本土の三市場、`hk` は香港 —— "
            "なので一冊の台帳に両方を載せられ、香港銘柄のコストは香港ドルで持つ。",

            "**コストは希薄化後のコスト**で、証券アプリが銘柄の横に出しているのと同じ数字：買いは全部の株数に配分され、"
            "売りは約定代金を残りの株数のコストから差し引く（コストより高く売れば下がり、安く売れば上がる）。"
            "全部売れば台帳から消える。",

            "**今日の損益は前日終値から測る。** 約定はその分に入るので、午前に売買しても曲線は途切れない。"
            "手数料は含まないため、証券アプリの「今日の損益」とは手数料の分だけずれることがある。",

            "**横軸は 09:30 から、実際に取引のあった市場の引けまで**：上海・深センは 15:00、香港は 16:00。"
            "昼休みは帯で塗って「昼休み」と書き、二時間動かない平らな線にはしない。"
            "片方が休場の日は、その銘柄に「休場」と付けて曲線から外す —— 今日ではない取引の値で埋めない。",

            "**取引時間中は自動更新**：平日 09:15〜16:10 のあいだ 30 秒ごと（スイッチが入っているとき）。"
            "引けたあとは問い合わせない —— 終わった一日は何度聞いても同じ数字しか返らない。",

            "**約定の取り込みはスクリーンショットか貼り付け。** スクリーンショットは Windows 内蔵の OCR でこの端末上で読む"
            "（送信しない）。読み取った文字は修正できる欄に入り、解析結果は一行ずつ並ぶ。読めない行が一つでもあれば取り込まない。"
            "同じリストを二度取り込んでも害はない —— 日付・時刻・コード・売買・価格・数量が揃って初めて同じ約定とみなす。",

            "台帳はアプリのフォルダに保存され、再起動しても残る。このページは「読者自身を描く」唯一のページでもある —— "
            "ほかのページは市場を描き、金額はそのときの市場の通貨で数える。",

            "最初の台帳はこのページを作ったときの九銘柄から始まる。不要なものは一行ずつ消して、自分のものを足せばよい。",
        ],
    ),
    "ko": (
        "실시간 보유 손익",
        "내 보유 종목을 분 단위로 평가한다: 9:30부터 장 마감까지 오늘의 손익 곡선. 장중에는 자동으로 새로 고친다.",
        [
            "**장부는 내 것이다.** 종목 코드로 추가하고 수량과 원가는 증권 앱에 보이는 값을 그대로 적는다. "
            "당일 체결 내역을 가져올 수도 있다. 코드에 시장이 들어 있다 — `sh` `sz` `bj`는 중국 본토 세 시장, `hk`는 홍콩 — "
            "그래서 한 장부에 둘 다 담기고, 홍콩 종목의 원가는 홍콩달러로 둔다.",

            "**원가는 희석 원가**로, 증권 앱이 종목 옆에 적어 주는 그 값이다: 매수는 전체 수량에 나눠지고, "
            "매도는 체결 금액을 남은 수량의 원가에서 빼낸다(원가보다 비싸게 팔면 내려가고 싸게 팔면 올라간다). "
            "전부 팔면 장부에서 사라진다.",

            "**오늘의 손익은 전일 종가에서 잰다.** 체결은 그 분에 반영되므로 오전에 사고팔아도 곡선이 끊기지 않는다. "
            "수수료는 넣지 않으므로 증권 앱의 '오늘 손익'과는 수수료만큼 다를 수 있다.",

            "**가로축은 09:30부터 실제로 거래된 시장의 마감까지**: 상하이·선전은 15:00, 홍콩은 16:00. "
            "점심 휴장은 띠로 칠하고 '점심 휴장'이라 적는다 — 두 시간짜리 평평한 선으로 그리지 않는다. "
            "한쪽이 휴장이면 그 종목은 '휴장'으로 표시하고 곡선에서 뺀다. 오늘이 아닌 장의 값으로 채우지 않는다.",

            "**장중에는 자동으로 새로 고친다**: 평일 09:15~16:10 사이 30초마다, 스위치가 켜져 있을 때. "
            "마감 뒤에는 묻지 않는다 — 끝난 하루는 몇 번을 물어도 같은 숫자만 돌아온다.",

            "**체결 가져오기는 스크린샷이나 붙여넣기.** 스크린샷은 Windows에 들어 있는 OCR로 이 컴퓨터에서 읽는다(올리지 않는다). "
            "읽은 글자는 고칠 수 있는 칸에 들어가고, 해석 결과는 한 줄씩 보여 준다. 읽지 못한 줄이 하나라도 있으면 가져오지 않는다. "
            "같은 목록을 두 번 가져와도 무해하다 — 날짜·시각·코드·방향·가격·수량이 모두 같아야 이미 있는 체결로 본다.",

            "장부는 앱 폴더에 저장되어 다시 켜도 남는다. 이 페이지는 '독자 자신을 그리는' 유일한 페이지이기도 하다 — "
            "다른 페이지는 시장을 그리고, 금액은 그때 그 시장의 통화로 센다.",

            "첫 장부는 이 페이지를 만들 때의 아홉 종목에서 시작한다. 필요 없는 줄은 하나씩 지우고 내 것을 더하면 된다.",
        ],
    ),
    "de": (
        "Depot live",
        "Die eigenen Positionen, minutenweise bewertet: was der heutige Tag seit 09:30 gebracht oder gekostet hat, "
        "während der Handelszeit laufend aktualisiert.",
        [
            "**Das Depot gehört Ihnen.** Eine Position über ihren Code mit Stückzahl und dem Kostenwert hinzufügen, den Ihr "
            "Broker anzeigt — oder die ausgeführten Orders des Tages importieren. Der Code trägt den Handelsplatz: `sh`, "
            "`sz` und `bj` für die drei festlandchinesischen Börsen, `hk` für Hongkong. Ein Depot hält also beide, und ein "
            "Hongkong-Kostenwert bleibt in Hongkong-Dollar.",

            "**Der Kostenwert ist der verwässerte**, genau die Zahl, die die Broker-App neben die Position schreibt: ein "
            "Kauf verteilt sich auf alle Stücke, ein Verkauf rechnet seinen Erlös gegen die Kosten der verbleibenden "
            "Stücke (er senkt sie, wenn der Verkauf über dem Einstand lag, und hebt sie, wenn nicht), und ein restlos "
            "verkaufter Titel verlässt das Depot.",

            "**Der heutige Gewinn wird ab dem Vortagsschluss gemessen**, und ein Geschäft zählt in der Minute, in der es "
            "passiert ist: Kauf oder Verkauf am Vormittag, und die Kurve läuft ohne Sprung durch. Gebühren sind nicht "
            "enthalten, deshalb kann die Zahl um die Provision von der des Brokers abweichen.",

            "**Die Achse läuft von 09:30 bis zum Schluss der Handelsplätze, die wirklich gehandelt haben**: Shanghai und "
            "Shenzhen bis 15:00, Hongkong bis 16:00. Die Mittagspause wird als Band gezeichnet und benannt, nicht als zwei "
            "Stunden gerade Linie. Ist eine Seite geschlossen, stehen ihre Positionen auf „geschlossen\" und bleiben aus "
            "der Kurve — statt mit dem Kurs einer Sitzung gerechnet zu werden, die nicht die heutige ist.",

            "**Während der Handelszeit aktualisiert die Seite selbst**: werktags zwischen 09:15 und 16:10 alle 30 Sekunden, "
            "solange der Schalter an ist. Nach dem Schluss fragt sie nicht mehr — ein abgeschlossener Tag antwortet auf "
            "jede Abfrage mit denselben Zahlen.",

            "**Orderimport geht per Screenshot oder per Einfügen.** Ein Screenshot wird auf diesem Rechner von der in "
            "Windows eingebauten OCR gelesen (nichts wird hochgeladen), der erkannte Text landet in einem korrigierbaren "
            "Feld, und das Ergebnis wird Zeile für Zeile gezeigt; eine unlesbare Zeile verhindert den Import. Dieselbe "
            "Liste zweimal zu importieren ist harmlos: Tag, Minute, Code, Richtung, Preis und Stückzahl zusammen erkennen "
            "eine bereits gebuchte Zeile.",

            "Das Depot liegt im eigenen Ordner der App und überlebt Neustarts. Diese Seite ist außerdem die einzige, deren "
            "Thema der Leser selbst ist — alle anderen zeichnen einen Markt, und ihre Beträge stehen in der Währung des "
            "eingestellten Marktes.",

            "Das erste Depot besteht aus den neun Positionen, mit denen diese Seite entstanden ist; entfernen Sie sie Zeile "
            "für Zeile und fügen Sie Ihre eigenen hinzu.",
        ],
    ),
    "fr": (
        "P&L en direct",
        "Vos propres positions, valorisées à la minute : ce que la séance a rapporté ou coûté depuis 09:30, rafraîchi "
        "pendant que le marché est ouvert.",
        [
            "**Le portefeuille est le vôtre.** Ajoutez une ligne par son code, avec la quantité et le coût affichés par "
            "votre courtier — ou importez les ordres exécutés du jour. Le code porte la place : `sh`, `sz` et `bj` pour "
            "les trois Bourses du continent, `hk` pour Hong Kong. Un seul portefeuille tient donc les deux, et un coût de "
            "Hong Kong reste en dollars de Hong Kong.",

            "**Le coût est le coût dilué**, celui que l'application du courtier écrit à côté de la position : un achat se "
            "répartit sur toutes les actions, une vente déduit son produit du coût des actions restantes (il baisse si la "
            "vente s'est faite au-dessus du coût, il monte sinon), et une position soldée quitte le portefeuille.",

            "**Le gain du jour se mesure depuis la clôture de la veille**, et un ordre compte à la minute où il a été "
            "exécuté : acheter ou vendre en matinée et la courbe reste continue. Les frais ne sont pas comptés, d'où un "
            "écart possible avec le « gain du jour » du courtier.",

            "**L'axe va de 09:30 à la clôture des places qui ont réellement traité** : Shanghai et Shenzhen à 15:00, Hong "
            "Kong à 16:00. La pause de midi est hachurée et nommée, pas dessinée comme deux heures de ligne plate. Si une "
            "place est fermée, ses lignes portent « fermé » et sortent de la courbe, au lieu d'être valorisées sur une "
            "séance qui n'est pas celle du jour.",

            "**Le rafraîchissement est automatique pendant la séance** : toutes les 30 secondes en semaine entre 09:15 et "
            "16:10, tant que l'interrupteur est activé. Après la clôture, la page cesse d'interroger : une journée "
            "terminée répond la même chose à chaque requête.",

            "**L'import des ordres se fait par capture d'écran ou par collage.** La capture est lue sur cette machine par "
            "l'OCR fourni avec Windows (rien n'est envoyé), le texte reconnu arrive dans une zone corrigeable, et le "
            "résultat est présenté ligne par ligne ; une seule ligne illisible annule l'import. Importer deux fois la même "
            "liste est sans effet : jour, minute, code, sens, prix et quantité ensemble reconnaissent une ligne déjà "
            "enregistrée.",

            "Le portefeuille est stocké dans le dossier de l'application et survit aux redémarrages. C'est aussi la seule "
            "page dont le sujet soit le lecteur — les autres dessinent un marché, et leurs montants sont dans la devise du "
            "marché choisi.",

            "Le premier portefeuille reprend les neuf positions avec lesquelles cette page a été conçue ; retirez-les une à "
            "une et ajoutez les vôtres.",
        ],
    ),
    "it": (
        "P&L in tempo reale",
        "Le proprie posizioni, valorizzate al minuto: quanto la giornata ha reso o costato dalle 09:30, aggiornate mentre "
        "il mercato è aperto.",
        [
            "**Il portafoglio è tuo.** Aggiungi una posizione per codice, con la quantità e il costo che mostra il broker — "
            "oppure importa gli ordini eseguiti del giorno. Il codice porta la piazza: `sh`, `sz` e `bj` per i tre mercati "
            "della Cina continentale, `hk` per Hong Kong. Un solo portafoglio tiene entrambi, e un costo di Hong Kong resta "
            "in dollari di Hong Kong.",

            "**Il costo è quello diluito**, lo stesso che l'app del broker scrive accanto alla posizione: un acquisto si "
            "distribuisce su tutte le azioni, una vendita detrae il ricavato dal costo delle azioni rimaste (scende se la "
            "vendita è sopra il costo, sale se è sotto), e una posizione chiusa esce dal portafoglio.",

            "**Il guadagno di oggi si misura dalla chiusura di ieri**, e un'operazione conta al minuto in cui è avvenuta: "
            "comprare o vendere a metà mattina e la curva resta continua. Le commissioni non sono comprese, quindi il "
            "numero può differire da quello del broker.",

            "**L'asse va dalle 09:30 alla chiusura delle piazze che hanno davvero scambiato**: Shanghai e Shenzhen alle "
            "15:00, Hong Kong alle 16:00. La pausa pranzo è tracciata come fascia e nominata, non disegnata come due ore di "
            "linea piatta. Se una piazza è chiusa, le sue posizioni sono marcate «chiuso» e restano fuori dalla curva, "
            "invece di essere prezzate su una sessione che non è quella di oggi.",

            "**L'aggiornamento è automatico mentre il mercato è aperto**: ogni 30 secondi nei giorni feriali fra le 09:15 e "
            "le 16:10, con l'interruttore acceso. Dopo la chiusura smette di interrogare: una giornata conclusa risponde "
            "sempre gli stessi numeri.",

            "**L'importazione degli ordini è uno screenshot o un incolla.** Lo screenshot viene letto su questa macchina "
            "dall'OCR di Windows (nulla viene inviato), il testo riconosciuto arriva in un riquadro correggibile e il "
            "risultato è mostrato riga per riga; una sola riga illeggibile blocca l'importazione. Importare due volte lo "
            "stesso elenco non fa danni: giorno, minuto, codice, lato, prezzo e quantità insieme riconoscono una riga già "
            "registrata.",

            "Il portafoglio sta nella cartella dell'app e sopravvive ai riavvii. È anche l'unica pagina il cui soggetto è il "
            "lettore — le altre disegnano un mercato e i loro importi sono nella valuta del mercato scelto.",

            "Il primo portafoglio parte dalle nove posizioni con cui questa pagina è nata; toglile una per una e aggiungi "
            "le tue.",
        ],
    ),
    "es": (
        "P&L en vivo",
        "Sus propias posiciones, valoradas al minuto: lo que la sesión ha ganado o costado desde las 09:30, actualizado "
        "mientras el mercado está abierto.",
        [
            "**La cartera es suya.** Añada una posición por su código, con las acciones y el coste que muestra su bróker — "
            "o importe las órdenes ejecutadas del día. El código lleva el mercado: `sh`, `sz` y `bj` para los tres del "
            "continente, `hk` para Hong Kong. Una sola cartera contiene ambos, y un coste de Hong Kong se guarda en dólares "
            "de Hong Kong.",

            "**El coste es el diluido**, el mismo que la aplicación del bróker escribe junto a la posición: una compra se "
            "reparte entre todas las acciones, una venta descuenta su importe del coste de las que quedan (baja si la "
            "venta fue por encima del coste y sube si fue por debajo), y una posición cerrada sale de la cartera.",

            "**El beneficio de hoy se mide desde el cierre de ayer**, y una operación cuenta en el minuto en que ocurrió: "
            "compre o venda a media mañana y la curva sigue sin saltos. No incluye comisiones, así que puede diferir de la "
            "cifra del bróker en esa comisión.",

            "**El eje va de las 09:30 al cierre de los mercados que realmente negociaron**: Shanghái y Shenzhen a las "
            "15:00, Hong Kong a las 16:00. El descanso del mediodía se sombrea y se nombra, no se dibuja como dos horas de "
            "línea plana. Si un mercado está cerrado, sus posiciones se marcan «cerrado» y quedan fuera de la curva, en vez "
            "de valorarse con una sesión que no es la de hoy.",

            "**La actualización es automática mientras el mercado está abierto**: cada 30 segundos en días laborables entre "
            "las 09:15 y las 16:10, con el interruptor activado. Después del cierre deja de preguntar: una sesión terminada "
            "responde lo mismo a cada consulta.",

            "**La importación de órdenes es una captura de pantalla o un pegado.** La captura se lee en este equipo con el "
            "OCR que incluye Windows (no se sube nada), el texto reconocido llega a una caja corregible y el resultado se "
            "muestra fila por fila; una sola fila ilegible impide importar. Importar dos veces la misma lista es "
            "inofensivo: día, minuto, código, sentido, precio y cantidad juntos reconocen una fila ya registrada.",

            "La cartera se guarda en la carpeta de la aplicación y sobrevive a los reinicios. Es además la única página cuyo "
            "tema es el propio lector — las demás dibujan un mercado y sus importes están en la moneda del mercado elegido.",

            "La primera cartera son las nueve posiciones con las que nació esta página; quite las que no use una a una y "
            "añada las suyas.",
        ],
    ),
    "pt-BR": (
        "P&L ao vivo",
        "Suas próprias posições, marcadas ao minuto: o que o dia rendeu ou custou desde as 09:30, atualizado enquanto o "
        "mercado está aberto.",
        [
            "**A carteira é sua.** Adicione uma posição pelo código, com a quantidade e o custo que a corretora mostra — ou "
            "importe as ordens executadas do dia. O código carrega a praça: `sh`, `sz` e `bj` para os três mercados do "
            "continente, `hk` para Hong Kong. Uma carteira guarda as duas, e um custo de Hong Kong fica em dólares de Hong "
            "Kong.",

            "**O custo é o diluído**, o mesmo que o aplicativo da corretora escreve ao lado da posição: uma compra se "
            "espalha por todas as ações, uma venda abate o valor recebido do custo das que restam (cai se a venda foi acima "
            "do custo, sobe se foi abaixo), e uma posição zerada sai da carteira.",

            "**O resultado de hoje é medido a partir do fechamento de ontem**, e uma operação conta no minuto em que "
            "aconteceu: comprar ou vender no meio da manhã e a curva continua sem degrau. As taxas não entram, então o "
            "número pode diferir do \"resultado de hoje\" da corretora.",

            "**O eixo vai das 09:30 ao fechamento das praças que realmente negociaram**: Xangai e Shenzhen às 15:00, Hong "
            "Kong às 16:00. O intervalo do almoço é sombreado e nomeado, não desenhado como duas horas de linha reta. Com "
            "uma praça fechada, suas posições ficam marcadas como «fechado» e fora da curva, em vez de precificadas por uma "
            "sessão que não é a de hoje.",

            "**A atualização é automática enquanto o mercado está aberto**: a cada 30 segundos em dias úteis entre 09:15 e "
            "16:10, com o interruptor ligado. Depois do fechamento ela para de perguntar: um dia encerrado responde o mesmo "
            "a cada consulta.",

            "**A importação de ordens é um print ou uma colagem.** O print é lido nesta máquina pelo OCR que vem com o "
            "Windows (nada é enviado), o texto reconhecido cai numa caixa corrigível e o resultado aparece linha por linha; "
            "uma linha ilegível impede a importação. Importar a mesma lista duas vezes é inofensivo: dia, minuto, código, "
            "lado, preço e quantidade juntos reconhecem uma linha já registrada.",

            "A carteira fica na pasta do aplicativo e sobrevive a reinícios. É também a única página cujo assunto é o "
            "próprio leitor — as outras desenham um mercado, e seus valores estão na moeda do mercado escolhido.",

            "A primeira carteira são as nove posições com que esta página nasceu; remova uma a uma as que não usar e "
            "acrescente as suas.",
        ],
    ),
    "pl": (
        "Wynik na żywo",
        "Własne pozycje wyceniane co minutę: ile dzisiejsza sesja dała lub kosztowała od 09:30, odświeżane w czasie handlu.",
        [
            "**Portfel jest twój.** Dodaj pozycję po kodzie, z liczbą akcji i kosztem, jaki pokazuje broker — albo "
            "zaimportuj dzisiejsze zrealizowane zlecenia. Kod niesie rynek: `sh`, `sz` i `bj` to trzy giełdy "
            "kontynentalne, `hk` to Hongkong. Jeden portfel mieści oba, a koszt z Hongkongu pozostaje w dolarach "
            "hongkońskich.",

            "**Koszt jest rozwodniony** — ten sam, który aplikacja brokera pisze obok pozycji: zakup rozkłada się na "
            "wszystkie akcje, sprzedaż odejmuje uzyskaną kwotę od kosztu pozostałych akcji (spada, gdy sprzedano drożej niż "
            "koszt, rośnie, gdy taniej), a pozycja zamknięta znika z portfela.",

            "**Dzisiejszy wynik liczy się od wczorajszego zamknięcia**, a transakcja wchodzi w minucie, w której się "
            "zdarzyła: kupno lub sprzedaż przed południem, a krzywa biegnie bez skoku. Prowizji nie ma, więc liczba może "
            "różnić się od tej w aplikacji brokera.",

            "**Oś biegnie od 09:30 do zamknięcia tych rynków, które naprawdę handlowały**: Szanghaj i Shenzhen do 15:00, "
            "Hongkong do 16:00. Przerwa południowa jest zacieniowana i podpisana, a nie narysowana jako dwie godziny "
            "płaskiej linii. Gdy jedna strona nie handluje, jej pozycje są oznaczone jako „zamknięte\" i wypadają z "
            "krzywej, zamiast być wyceniane sesją, która nie jest dzisiejsza.",

            "**Odświeżanie jest automatyczne w czasie sesji**: co 30 sekund w dni robocze między 09:15 a 16:10, gdy "
            "przełącznik jest włączony. Po zamknięciu przestaje pytać — zakończony dzień odpowiada tym samym na każde "
            "zapytanie.",

            "**Import zleceń to zrzut ekranu albo wklejenie.** Zrzut czyta na tym komputerze OCR wbudowany w Windows (nic "
            "nie jest wysyłane), rozpoznany tekst trafia do pola, które można poprawić, a wynik jest pokazywany wiersz po "
            "wierszu; jeden nieczytelny wiersz wstrzymuje import. Dwukrotny import tej samej listy nic nie psuje: dzień, "
            "minuta, kod, strona, cena i liczba akcji razem rozpoznają już zapisany wiersz.",

            "Portfel jest zapisany w folderze aplikacji i przetrwa restart. To także jedyna strona, której tematem jest sam "
            "czytelnik — pozostałe rysują rynek, a ich kwoty są w walucie wybranego rynku.",

            "Pierwszy portfel to dziewięć pozycji, z którymi ta strona powstała; usuń zbędne po jednej i dodaj własne.",
        ],
    ),
    "cs": (
        "Výsledek živě",
        "Vlastní pozice oceňované po minutě: co dnešní seance přinesla nebo stála od 09:30, aktualizované během obchodování.",
        [
            "**Portfolio je vaše.** Přidejte pozici podle kódu, s počtem akcií a nákladem, který ukazuje broker — nebo "
            "importujte dnešní provedené pokyny. Kód nese trh: `sh`, `sz` a `bj` jsou tři pevninské burzy, `hk` Hongkong. "
            "Jedno portfolio unese obojí a náklad z Hongkongu zůstává v hongkongských dolarech.",

            "**Náklad je zředěný** — stejný, jaký aplikace brokera píše vedle pozice: nákup se rozloží na všechny akcie, "
            "prodej odečte získanou částku z nákladu zbývajících akcií (klesne, prodalo-li se nad nákladem, stoupne, "
            "prodalo-li se pod ním), a uzavřená pozice z portfolia zmizí.",

            "**Dnešní výsledek se měří od včerejšího zavření** a obchod se započítá v minutě, kdy se stal: nákup či prodej "
            "dopoledne a křivka jde dál bez skoku. Poplatky v tom nejsou, takže číslo se může od brokera lišit právě o "
            "provizi.",

            "**Osa jde od 09:30 do zavření těch trhů, které skutečně obchodovaly**: Šanghaj a Šen-čen do 15:00, Hongkong do "
            "16:00. Polední přestávka je podbarvená a popsaná, ne nakreslená jako dvě hodiny rovné čáry. Když je jedna "
            "strana zavřená, její pozice jsou označené jako „zavřeno\" a z křivky vypadnou — místo aby se oceňovaly seancí, "
            "která není dnešní.",

            "**Během obchodování se obnovuje samo**: každých 30 sekund v pracovní dny mezi 09:15 a 16:10, pokud je přepínač "
            "zapnutý. Po zavření se přestane ptát — uzavřený den odpovídá na každý dotaz stejně.",

            "**Import pokynů je snímek obrazovky nebo vložení.** Snímek čte na tomto počítači OCR, které je součástí Windows "
            "(nic se neodesílá), rozpoznaný text se objeví v poli, které lze opravit, a výsledek se vypíše řádek po řádku; "
            "jediný nepřečtený řádek import zablokuje. Dvakrát importovaný stejný seznam nic nezkazí: den, minuta, kód, "
            "strana, cena a počet akcií dohromady rozpoznají už zapsaný řádek.",

            "Portfolio je uložené ve složce aplikace a přežije restart. Tahle stránka je také jediná, jejímž tématem je sám "
            "čtenář — ostatní kreslí trh a jejich částky jsou v měně zvoleného trhu.",

            "První portfolio tvoří devět pozic, se kterými tahle stránka vznikla; nepotřebné po jedné odstraňte a přidejte "
            "svoje.",
        ],
    ),
    "ru": (
        "Портфель онлайн",
        "Свои позиции, оценённые по минутам: сколько день принёс или стоил с 09:30, с обновлением во время торгов.",
        [
            "**Портфель ваш.** Добавьте позицию по коду, с количеством акций и себестоимостью, которую показывает "
            "брокер, — или импортируйте исполненные за день заявки. Код несёт площадку: `sh`, `sz` и `bj` — три "
            "материковые биржи, `hk` — Гонконг. Один портфель держит и то и другое, а себестоимость гонконгской позиции "
            "остаётся в гонконгских долларах.",

            "**Себестоимость — размытая**, та же, что приложение брокера пишет рядом с позицией: покупка распределяется "
            "на все акции, продажа вычитает выручку из себестоимости оставшихся (падает, если продано выше "
            "себестоимости, и растёт, если ниже), а закрытая позиция уходит из портфеля.",

            "**Сегодняшний результат считается от вчерашнего закрытия**, а сделка входит в ту минуту, когда произошла: "
            "покупка или продажа утром — и кривая идёт без разрыва. Комиссии не учтены, поэтому число может отличаться "
            "от «результата дня» у брокера.",

            "**Ось идёт с 09:30 до закрытия тех площадок, которые действительно торговали**: Шанхай и Шэньчжэнь — до "
            "15:00, Гонконг — до 16:00. Обеденный перерыв закрашен и подписан, а не нарисован как два часа ровной "
            "линии. Если одна сторона закрыта, её позиции помечены «закрыто» и выпадают из кривой, вместо того чтобы "
            "считаться по сессии, которая не сегодняшняя.",

            "**Обновление идёт само во время торгов**: каждые 30 секунд по будням с 09:15 до 16:10, пока переключатель "
            "включён. После закрытия страница перестаёт спрашивать: завершённый день отвечает одинаково на любой запрос.",

            "**Импорт заявок — это снимок экрана или вставка.** Снимок читается на этой машине OCR, встроенным в "
            "Windows (никуда не отправляется), распознанный текст попадает в поле, которое можно поправить, а результат "
            "показывается построчно; одна нечитаемая строка отменяет импорт. Повторный импорт того же списка безвреден: "
            "день, минута, код, сторона, цена и количество вместе узнают уже записанную строку.",

            "Портфель хранится в папке приложения и переживает перезапуск. Это ещё и единственная страница, чей "
            "предмет — сам читатель: остальные рисуют рынок, и суммы на них в валюте выбранного рынка.",

            "Первый портфель — те девять позиций, с которых эта страница началась; уберите ненужные по одной и добавьте "
            "свои.",
        ],
    ),
    "tr": (
        "Canlı portföy",
        "Kendi pozisyonlarınız, dakika dakika değerlenmiş: günün 09:30'dan bu yana ne kazandırdığı ya da neye mal olduğu, "
        "piyasa açıkken kendiliğinden yenilenir.",
        [
            "**Defter sizin.** Bir pozisyonu koduyla, aracı kurumun gösterdiği adet ve maliyetle ekleyin — ya da günün "
            "gerçekleşen emirlerini içe aktarın. Kodu piyasayı taşır: `sh`, `sz` ve `bj` ana karadaki üç borsa, `hk` Hong "
            "Kong. Tek defter ikisini birden tutar ve Hong Kong maliyeti Hong Kong doları olarak kalır.",

            "**Maliyet seyreltilmiş maliyettir**; aracı kurum uygulamasının pozisyonun yanına yazdığı sayı budur: alış tüm "
            "adetlere yayılır, satış elde edileni kalan adetlerin maliyetinden düşer (maliyetin üstünde satıldıysa düşer, "
            "altında satıldıysa yükselir), tümüyle satılan pozisyon defterden çıkar.",

            "**Bugünün kârı dünkü kapanıştan ölçülür** ve işlem gerçekleştiği dakikaya yazılır: sabah alıp satarsanız eğri "
            "kopmaz. Komisyon dahil değildir, bu yüzden sayı aracı kurumun \"günlük kâr\"ından komisyon kadar farklı "
            "olabilir.",

            "**Eksen 09:30'dan, gerçekten işlem gören piyasaların kapanışına kadar gider**: Şanghay ve Shenzhen 15:00, Hong "
            "Kong 16:00. Öğle arası bir bant olarak boyanır ve adlandırılır, iki saatlik düz bir çizgi olarak çizilmez. Bir "
            "taraf kapalıysa o pozisyonlar \"kapalı\" diye işaretlenir ve eğrinin dışında kalır; bugünün olmayan bir "
            "seansın fiyatıyla doldurulmaz.",

            "**Piyasa açıkken yenileme kendiliğindendir**: hafta içi 09:15 ile 16:10 arasında 30 saniyede bir, anahtar "
            "açıkken. Kapanıştan sonra sormayı bırakır: bitmiş bir gün her sorguya aynı sayılarla cevap verir.",

            "**Emir içe aktarma bir ekran görüntüsü ya da yapıştırmadır.** Görüntü bu makinede Windows'un kendi OCR'ı ile "
            "okunur (hiçbir yere gönderilmez), tanınan metin düzeltilebilir bir kutuya düşer ve sonuç satır satır "
            "gösterilir; okunamayan tek satır aktarmayı durdurur. Aynı listeyi iki kez aktarmak zararsızdır: gün, dakika, "
            "kod, yön, fiyat ve adet birlikte, defterde zaten olan satırı tanır.",

            "Defter uygulamanın kendi klasöründe durur ve yeniden başlatmada korunur. Bu sayfa aynı zamanda konusu okurun "
            "kendisi olan tek sayfadır — ötekiler bir piyasayı çizer ve tutarları seçili piyasanın para birimindedir.",

            "İlk defter, bu sayfanın doğduğu dokuz pozisyondur; kullanmadıklarınızı tek tek çıkarıp kendi pozisyonlarınızı "
            "ekleyin.",
        ],
    ),
}


def block(title, intro, bullets):
    """一章的正文：标题、一行配图说明的位置（图由 port-help-images.py 补）、导语、条目。"""
    lines = [f"## {title}", "", intro, ""]

    for bullet in bullets:
        lines.append("- " + bullet)
        lines.append("")

    return "\n".join(lines)


def main():
    index = listingtext.chapter_of("NavPortfolioPnl")
    print("这一章插在第 %d 章（0 起）\n" % index)

    changed = 0

    for lang in LANGS:
        path = HELP / f"help-{lang}.md"
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
        bom = raw.startswith(b"\xef\xbb\xbf")

        if "\r" in text:
            sys.exit("%s 里有 CR：手册应当是 LF 无 BOM，先查清楚再写" % path)

        title, intro, bullets = NEW[lang]
        heading = "## " + title

        if heading in text:
            print("%-9s 已经有这一章（跳过）" % lang)
            continue

        lines = text.split("\n")
        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if index >= len(heads):
            sys.exit("%s 只有 %d 章，放不下第 %d 章" % (path, len(heads), index))

        at = heads[index]
        before = "\n".join(lines[:at]).rstrip("\n")

        after = "\n".join(lines[at:])

        text = before + "\n\n" + block(title, intro, bullets).rstrip("\n") + "\n\n" + after

        # 校验：这一章落在 index 那一位，前后两章还是原来那两章。
        check = [line for line in text.split("\n") if line.startswith("## ")]

        if check[index] != heading:
            sys.exit("%s 插完对不上位置：第 %d 章是「%s」" % (path, index, check[index]))

        if check[index + 1] != lines[at].strip():
            # 整行比，别削前缀：削掉 "## " 之后两边永远不相等，于是脚本以
            # 「挤掉了后面那一章」的理由退出，而一次也没写 —— 报错指向了错的地方。
            sys.exit("%s 插完把它后面那一章挤掉了" % path)

        path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
        changed += 1
        print("%-9s 插入「%s」，第 %d 章" % (lang, title, index))

    print("\n改了 %d 份" % changed)


if __name__ == "__main__":
    main()
