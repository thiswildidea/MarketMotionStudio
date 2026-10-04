# -*- coding: utf-8 -*-
r"""往 14 份帮助文档的「市场成交额」那一章末尾补两条要点：自选篮，与日内分时。

**为什么要补**：那一章原本写着"只保留所有市场都交易的那天"。那条规则是给**板块**用的
——板块由指数合成，指数每个交易日都有行情，所以"取交集"从来没咬过人。自选篮里放进
个股之后它就成了错的：个股会停牌，交集下"一只停牌 = 那一天从图上消失"，而图上少一天
和那天本来就没交易长得一模一样。所以新要点必须把两条规则并排写出来，而不是只加一条。

第二条要点写日内：那是这一页的第三种画面形态，取的是**另一个端点**（分时而不是日线），
只留最近五个交易日，且必须截到 15:00。

位置**按章节序号**定（第 3 章，0 基下标 2），不按标题文字 —— 14 份文档的标题是 14 种语言。

文件是 UTF-8 + LF，**BOM 照原样**（这 14 份都不带）：读时记下有没有，写回时照原样补。

幂等：用正文第一行当哨兵，已存在就先删掉旧的再追加 —— 跑几遍结果一样。

用法：python tools\port-turnover-watchlist-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 「市场成交额」是第 3 章（0 基下标 2）：前两章是「选市场」与「翻页」，不是页面。
CHAPTER = 2

BODIES = {
    "en-US": """- **Your own list.** The last entry on the board menu is the list you keep — indices and shares
  side by side, shared with the four roster boards. Only mainland codes can be added up: turnover
  is reported in each market's own currency, so a Hong Kong or New York name is left out, and the
  status line says how many. A day is on the axis if *any* member traded; a member with no row
  for that day — halted, or not yet listed — contributes nothing. That is deliberately the
  opposite of the rule the boards above use: an index never halts, a share does, and dropping the
  day would make a halt look like a day on which nothing traded anywhere.
- **The change under a basket** is the equal-weighted average of the members' own daily changes,
  each measured against its own previous close. Equal-weighted because a list is not a portfolio:
  there is no holding size to weight by.
- **One session, minute by minute.** The third form is a separate fetch: the running total from
  the opening bell to the close on a single day. The source keeps the last five sessions and no
  more, so no range is offered — the frame names the day it drew. The curve stops at 15:00,
  because the half hour the endpoint adds after that is after-hours trading, which the daily
  figure leaves out too. The four closing cards are the day's total and what share of it fell in
  the morning, the afternoon, and the last half hour — a chart of *when* money moved, so three of
  the four are shares rather than amounts. The BSE 50 is the one board that reports minutes with
  no amount column at all, and it is refused rather than counted as nothing.""",

    "zh-Hans": """- **自选清单。** 板块菜单最后一项是你自己维护的那份清单：指数和个股可以混装，与另外四个榜单
  共用一份。只有境内代码能进这个篮子——成交额是各市场各报各的币种，港股美股会被挡下，状态行
  会说挡了几只。只要**有一只**交易，那一天就在轴上；某只那天没有行情（停牌，或还没上市）就
  贡献 0。这与上面那些板块的规则**故意相反**：指数不会停牌，个股会，而把那天丢掉会让停牌看起来
  像"那天哪儿都没成交"。
- **篮子下面的涨跌**是各成员自己日涨跌的等权平均，各自对照自己的前一根收盘。等权是因为一份
  清单不是一个组合——没有持仓市值可以拿来加权。
- **一个交易日，一分钟一分钟地走。** 第三种形态是另一次取数：某一天从开盘到收盘的累计成交额。
  源端只留最近五个交易日，所以不给区间选择——画面上写着它画的是哪一天。曲线停在 15:00，因为
  端点在那之后多补的半小时是盘后固定价格交易，日线那个数字也不算它。四张结算卡是全天合计，
  以及上午、下午、尾盘半小时各占多少——这一页问的是钱**什么时候**动的，所以四张里有三张是
  占比而不是金额。北证 50 是唯一一个"有分时但没有成交额列"的板块，它被拒掉，而不是当成 0。""",

    "zh-Hant": """- **自選清單。** 板塊選單最後一項是你自己維護的那份清單：指數和個股可以混裝，與另外四個榜單
  共用一份。只有境內代碼能進這個籃子——成交額是各市場各報各的幣別，港股美股會被擋下，狀態列
  會說擋了幾支。只要**有一支**交易，那一天就在軸上；某支那天沒有行情（停牌，或還沒上市）就
  貢獻 0。這與上面那些板塊的規則**故意相反**：指數不會停牌，個股會，而把那天丟掉會讓停牌看起來
  像「那天哪兒都沒成交」。
- **籃子下面的漲跌**是各成員自己日漲跌的等權平均，各自對照自己的前一根收盤。等權是因為一份
  清單不是一個組合——沒有持倉市值可以拿來加權。
- **一個交易日，一分鐘一分鐘地走。** 第三種形態是另一次取數：某一天從開盤到收盤的累計成交額。
  源端只留最近五個交易日，所以不給區間選擇——畫面上寫著它畫的是哪一天。曲線停在 15:00，因為
  端點在那之後多補的半小時是盤後固定價格交易，日線那個數字也不算它。四張結算卡是全天合計，
  以及上午、下午、尾盤半小時各占多少——這一頁問的是錢**什麼時候**動的，所以四張裡有三張是
  占比而不是金額。北證 50 是唯一一個「有分時但沒有成交額欄」的板塊，它被拒掉，而不是當成 0。""",

    "ja": """- **マイリスト。** ボードメニューの最後の項目は、あなたが管理するリストです。指数と個株を
  混在でき、他の 4 つのボードと同じリストを共有します。合計できるのは中国本土のコードだけ
  です。売買代金は市場ごとに自国通貨で報告されるため、香港株や米国株は除外され、状態行に
  その数が表示されます。軸に載る日は**いずれか 1 件でも**取引された日です。その日の行がない
  銘柄（売買停止、あるいは未上場）は 0 を加えます。これは上のボードとは**意図的に逆**の規則
  です。指数は売買停止になりませんが個株はなり、日を落とせば停止が「どこでも取引のなかった
  日」に見えてしまいます。
- **バスケットの騰落率**は、各銘柄が自分の前日の終値と比べた日次変化の等加重平均です。
  リストはポートフォリオではないため、加重に使える保有残高がありません。
- **1 日を 1 分ずつ。** 3 つ目の形態は別の取得です。ある一日の寄り付きから大引けまでの累計
  売買代金です。ソースは直近 5 セッションしか保持しないため、期間選択はなく、画面が描いた
  日付を明示します。曲線は 15:00 で止まります。端点がその後に追加する 30 分は日中の取引時間
  外であり、日足の数値にも含まれません。4 枚のカードは一日の合計と、前場・後場・終盤 30 分の
  割合です。この頁が問うのは**いつ**資金が動いたかなので、4 枚中 3 枚は金額ではなく割合です。
  北証 50 は「分足はあるが売買代金の列がない」唯一のボードで、0 として扱わずに拒否されます。""",

    "ko": """- **내 목록.** 보드 메뉴의 마지막 항목은 직접 관리하는 목록입니다. 지수와 종목을 함께 담을 수
  있고, 다른 네 보드와 같은 목록을 공유합니다. 더할 수 있는 것은 중국 본토 코드뿐입니다.
  거래대금은 각 시장이 자기 통화로 보고하므로 홍콩·미국 종목은 제외되며 상태 줄에 그 수가
  표시됩니다. 축에 올라오는 날은 **하나라도** 거래된 날입니다. 그날 행이 없는 종목(거래정지,
  또는 미상장)은 0을 더합니다. 이는 위 보드들과 **의도적으로 반대**인 규칙입니다. 지수는
  거래정지되지 않지만 종목은 그렇게 되고, 날을 빼면 정지가 "아무 데서도 거래가 없었던 날"처럼
  보이기 때문입니다.
- **바스켓의 등락률**은 각 종목이 자기 직전 종가와 견준 일간 변화의 동일가중 평균입니다.
  목록은 포트폴리오가 아니므로 가중에 쓸 보유 규모가 없습니다.
- **하루를 1분씩.** 세 번째 형태는 별도의 조회입니다. 어느 하루의 개장부터 종가까지의 누적
  거래대금입니다. 소스는 최근 5개 세션만 보관하므로 구간 선택이 없고, 화면이 그린 날짜를
  밝힙니다. 곡선은 15:00에서 멈춥니다. 단자가 그 뒤에 덧붙이는 30분은 장후 거래이며 일간
  수치에도 들어 있지 않습니다. 네 장의 카드는 하루 합계와 오전·오후·마지막 30분의 비중입니다.
  이 페이지가 묻는 것은 돈이 **언제** 움직였는가이므로, 넉 장 중 세 장은 금액이 아니라 비중입니다.
  북증 50은 "분별 데이터는 있으나 거래대금 열이 없는" 유일한 보드로, 0으로 취급하지 않고
  거부됩니다.""",

    "de": """- **Eigene Liste.** Der letzte Eintrag im Board-Menü ist Ihre eigene Liste — Indizes und Aktien
  nebeneinander, gemeinsam mit den vier Roster-Boards. Addiert werden nur Festlandcodes: Der
  Umsatz wird in der Währung des jeweiligen Marktes gemeldet, daher bleiben Hongkong- und
  US-Namen außen vor, und die Statuszeile sagt, wie viele. Ein Tag steht auf der Achse, wenn
  *irgend ein* Mitglied gehandelt hat; ein Mitglied ohne Zeile für diesen Tag — ausgesetzt oder
  noch nicht gelistet — steuert nichts bei. Das ist absichtlich das Gegenteil der Regel der
  Boards oben: Ein Index wird nie ausgesetzt, eine Aktie schon, und ein gestrichener Tag ließe
  eine Aussetzung wie einen Tag aussehen, an dem nirgends gehandelt wurde.
- **Die Veränderung unter einem Korb** ist der gleich gewichtete Mittelwert der täglichen
  Veränderungen der Mitglieder, jeweils gegen den eigenen Vortagesschluss. Gleich gewichtet, weil
  eine Liste kein Portfolio ist — es gibt keine Positionsgröße, nach der sich gewichten ließe.
- **Eine Sitzung, Minute für Minute.** Die dritte Form ist ein eigener Abruf: die laufende Summe
  vom Opening bis zum Schluss eines einzigen Tages. Die Quelle hält nur die letzten fünf Sitzungen,
  daher wird kein Zeitraum angeboten — das Bild nennt den Tag, den es gezeichnet hat. Die Kurve
  endet um 15:00, denn die halbe Stunde, die der Endpunkt danach anhängt, ist nachbörslicher
  Handel, den auch die Tageszahl nicht enthält. Die vier Karten sind die Tagessumme und die
  Anteile von Vormittag, Nachmittag und der letzten halben Stunde — eine Grafik darüber, *wann*
  Geld floss, weshalb drei der vier Karten Anteile sind und keine Beträge. Der BSE 50 ist das
  einzige Board, das Minuten ohne Umsatzspalte meldet, und wird abgelehnt statt als nichts
  gezählt.""",

    "fr": """- **Votre liste.** La dernière entrée du menu est la liste que vous tenez — indices et actions
  côte à côte, partagée avec les quatre tableaux à roster. Seuls les codes continentaux peuvent
  être additionnés : les transactions sont publiées dans la devise de chaque marché, donc un nom
  de Hong Kong ou de New York est écarté, et la ligne d'état dit combien. Un jour figure sur
  l'axe dès que *n'importe quel* membre a traité ; un membre sans ligne ce jour-là — suspendu, ou
  pas encore coté — n'apporte rien. C'est délibérément l'inverse de la règle des tableaux
  ci-dessus : un indice n'est jamais suspendu, une action si, et supprimer le jour ferait
  ressembler une suspension à un jour sans aucune transaction nulle part.
- **La variation sous un panier** est la moyenne équipondérée des variations quotidiennes propres
  à chaque membre, mesurée contre sa propre clôture précédente. Équipondérée parce qu'une liste
  n'est pas un portefeuille : il n'y a aucune taille de position par laquelle pondérer.
- **Une séance, minute par minute.** La troisième forme est une autre requête : le total cumulé
  de l'ouverture à la clôture d'un seul jour. La source ne garde que les cinq dernières séances,
  donc aucun intervalle n'est proposé — l'image nomme le jour qu'elle a tracé. La courbe s'arrête
  à 15:00, car la demi-heure ajoutée ensuite par le point d'accès est du hors-séance, que le
  chiffre quotidien exclut également. Les quatre cartes sont le total du jour et la part du
  matin, de l'après-midi et de la dernière demi-heure — un graphique de *quand* l'argent a
  circulé, donc trois cartes sur quatre sont des parts et non des montants. Le BSE 50 est le seul
  tableau à renvoyer des minutes sans colonne de transactions ; il est refusé plutôt que compté
  pour rien.""",

    "it": """- **La vostra lista.** L'ultima voce del menu è la lista che gestite voi — indici e azioni
  fianco a fianco, condivisa con le quattro tavole a roster. Si possono sommare solo i codici
  continentali: gli scambi sono pubblicati nella valuta di ogni mercato, quindi un nome di Hong
  Kong o di New York resta fuori e la riga di stato dice quanti. Un giorno è sull'asse se
  *qualunque* membro ha trattato; un membro senza riga per quel giorno — sospeso, o non ancora
  quotato — non contribuisce. È deliberatamente il contrario della regola delle tavole sopra: un
  indice non viene mai sospeso, un'azione sì, e togliere il giorno farebbe sembrare una sospensione
  un giorno in cui non si è trattato da nessuna parte.
- **La variazione sotto un paniere** è la media equal-ponderata delle variazioni giornaliere
  proprie di ogni membro, misurata contro la propria chiusura precedente. Equal-ponderata perché
  una lista non è un portafoglio: non c'è una dimensione della posizione con cui ponderare.
- **Una seduta, minuto per minuto.** La terza forma è una richiesta separata: il totale
  progressivo dall'apertura alla chiusura di un solo giorno. La fonte conserva solo le ultime
  cinque sedute, quindi non si offre alcun intervallo — il quadro nomina il giorno che ha
  disegnato. La curva si ferma alle 15:00, perché la mezz'ora che l'endpoint aggiunge dopo è
  after-hours, che anche il dato giornaliero esclude. Le quattro schede sono il totale del giorno
  e la quota di mattina, pomeriggio e ultima mezz'ora — un grafico di *quando* il denaro si è
  mosso, quindi tre schede su quattro sono quote e non importi. Il BSE 50 è l'unica tavola che
  riporta minuti senza colonna degli scambi, e viene rifiutata invece di essere contata come nulla.""",

    "es": """- **Su lista.** La última entrada del menú es la lista que usted mantiene — índices y acciones
  juntos, compartida con las cuatro tablas de roster. Solo se pueden sumar los códigos
  continentales: la contratación se publica en la divisa de cada mercado, así que un nombre de
  Hong Kong o de Nueva York queda fuera y la línea de estado dice cuántos. Un día está en el eje
  si *algún* miembro negoció; un miembro sin fila ese día — suspendido, o aún sin cotizar — no
  aporta nada. Es deliberadamente lo contrario de la regla de las tablas de arriba: un índice
  nunca se suspende, una acción sí, y eliminar el día haría que una suspensión pareciera un día
  sin negociación en ninguna parte.
- **La variación bajo una cesta** es el promedio equiponderado de las variaciones diarias propias
  de cada miembro, medidas contra su cierre anterior. Equiponderado porque una lista no es una
  cartera: no hay tamaño de posición con el que ponderar.
- **Una sesión, minuto a minuto.** La tercera forma es otra consulta: el acumulado desde la
  apertura hasta el cierre de un solo día. La fuente solo guarda las últimas cinco sesiones, así
  que no se ofrece ningún rango — el cuadro nombra el día que dibujó. La curva se detiene a las
  15:00, porque la media hora que añade el endpoint después es negociación fuera de horario, que
  la cifra diaria tampoco incluye. Las cuatro tarjetas son el total del día y la parte que
  correspondió a la mañana, la tarde y la última media hora — un gráfico de *cuándo* se movió el
  dinero, así que tres de las cuatro son proporciones y no importes. El BSE 50 es la única tabla
  que devuelve minutos sin columna de contratación, y se rechaza en lugar de contarse como nada.""",

    "pt-BR": """- **Sua lista.** A última entrada do menu é a lista que você mantém — índices e ações lado a
  lado, compartilhada com as quatro tabelas de roster. Só códigos continentais podem ser somados:
  o giro é informado na moeda de cada mercado, então um nome de Hong Kong ou Nova York fica de
  fora e a linha de estado diz quantos. Um dia entra no eixo se *algum* membro negociou; um membro
  sem linha naquele dia — suspenso, ou ainda não listado — não contribui. É deliberadamente o
  oposto da regra das tabelas acima: um índice nunca é suspenso, uma ação sim, e remover o dia
  faria uma suspensão parecer um dia em que nada foi negociado em lugar algum.
- **A variação sob uma cesta** é a média equiponderada das variações diárias próprias de cada
  membro, medida contra seu próprio fechamento anterior. Equiponderada porque uma lista não é uma
  carteira: não há tamanho de posição para ponderar.
- **Um pregão, minuto a minuto.** A terceira forma é outra consulta: o acumulado da abertura ao
  fechamento de um único dia. A fonte guarda apenas as últimas cinco sessões, portanto nenhum
  intervalo é oferecido — o quadro nomeia o dia que desenhou. A curva para às 15:00, porque a meia
  hora que o endpoint acrescenta depois é negociação após o pregão, que o número diário também não
  inclui. Os quatro cartões são o total do dia e a fatia da manhã, da tarde e dos últimos trinta
  minutos — um gráfico de *quando* o dinheiro se moveu, então três dos quatro são fatias e não
  valores. O BSE 50 é a única tabela que devolve minutos sem coluna de giro, e é recusada em vez
  de contada como nada.""",

    "pl": """- **Twoja lista.** Ostatnia pozycja menu to lista, którą prowadzisz — indeksy i akcje obok siebie,
  współdzielona z czterema tablicami roster. Sumować można tylko kody z kontynentu: obroty są
  podawane w walucie każdego rynku, więc nazwa z Hongkongu lub Nowego Jorku wypada, a wiersz
  stanu mówi, ile. Dzień jest na osi, gdy *ktokolwiek* z członków handlował; członek bez wiersza
  za ten dzień — zawieszony albo jeszcze nienotowany — wnosi zero. To celowo odwrotność reguły
  tablic powyżej: indeks nigdy nie zostaje zawieszony, akcja tak, a usunięcie dnia sprawiłoby, że
  zawieszenie wygląda jak dzień, w którym nigdzie nie handlowano.
- **Zmiana pod koszykiem** to średnia ważona równo dziennych zmian poszczególnych członków,
  każda wobec własnego poprzedniego zamknięcia. Ważona równo, bo lista to nie portfel: nie ma
  wielkości pozycji, według której można by ważyć.
- **Jedna sesja, minuta po minucie.** Trzecia forma to osobne pobranie: narastająca suma od
  otwarcia do zamknięcia jednego dnia. Źródło trzyma tylko pięć ostatnich sesji, więc nie ma
  wyboru zakresu — obraz podaje dzień, który narysował. Krzywa kończy się o 15:00, bo pół godziny
  dodane potem przez endpoint to handel po sesji, którego nie ma też w liczbie dziennej. Cztery
  karty to suma dnia oraz udziały przedpołudnia, popołudnia i ostatnich trzydziestu minut — wykres
  tego, *kiedy* pieniądz się poruszył, więc trzy z czterech kart to udziały, a nie kwoty. BSE 50
  to jedyna tablica zwracająca minuty bez kolumny obrotu i jest odrzucana, a nie liczona jako
  zero.""",

    "cs": """- **Váš seznam.** Poslední položka menu je seznam, který si vedete — indexy a akcie vedle sebe,
  sdílený se čtyřmi roster tabulemi. Sčítat lze pouze pevninské kódy: obrat je uváděn v měně
  každého trhu, takže název z Hongkongu nebo New Yorku zůstane venku a stavový řádek řekne kolik.
  Den je na ose, pokud *někdo* z členů obchodoval; člen bez řádku pro tento den — pozastavený,
  nebo ještě nekótovaný — nepřidá nic. Je to záměrně opak pravidla tabulí výše: index se nikdy
  nepozastaví, akcie ano, a vypuštění dne by způsobilo, že pozastavení vypadá jako den, kdy se
  neobchodovalo nikde.
- **Změna pod košem** je rovnoměrně vážený průměr denních změn jednotlivých členů, každá proti
  vlastní předchozí zavírací ceně. Rovnoměrně vážený proto, že seznam není portfolio: není zde
  velikost pozice, podle které by se dalo vážit.
- **Jeden den, minutu po minutě.** Třetí forma je samostatné načtení: průběžný součet od otevření
  do zavření jediného dne. Zdroj drží jen posledních pět seancí, takže žádný rozsah nenabízí —
  obraz pojmenuje den, který nakreslil. Křivka končí v 15:00, protože půlhodina, kterou endpoint
  přidává poté, je after-hours obchodování, které denní číslo také neobsahuje. Čtyři karty jsou
  celkový součet dne a podíly dopoledne, odpoledne a poslední půlhodiny — graf toho, *kdy* se
  peníze pohybovaly, takže tři ze čtyř kart jsou podíly, ne částky. BSE 50 je jediná tabule, která
  vrací minuty bez sloupce obratu, a je odmítnuta, nikoli započtena jako nic.""",

    "ru": """- **Ваш список.** Последний пункт меню — список, который вы ведёте: индексы и акции рядом,
  общий с четырьмя таблицами-ростерами. Складываются только материковые коды: оборот публикуется
  в валюте каждого рынка, поэтому названия из Гонконга или Нью-Йорка исключаются, а строка
  состояния говорит, сколько. День попадает на ось, если торговал *любой* участник; участник без
  строки за этот день — приостановленный или ещё не торгуемый — не добавляет ничего. Это
  намеренно обратно правилу таблиц выше: индекс никогда не приостанавливают, акцию — да, и
  удаление дня сделало бы приостановку похожей на день, когда нигде не торговали.
- **Изменение под корзиной** — равновзвешенное среднее собственных дневных изменений участников,
  каждое к своей предыдущей цене закрытия. Равновзвешенное, потому что список — это не портфель:
  нет размера позиции, по которому можно было бы взвешивать.
- **Одна сессия, минута за минутой.** Третья форма — отдельный запрос: накопленный итог от
  открытия до закрытия одного дня. Источник хранит только пять последних сессий, поэтому
  диапазон не предлагается — кадр называет день, который он нарисовал. Кривая останавливается в
  15:00, потому что полчаса, которые endpoint добавляет после, — это послеторговый период, его
  нет и в дневной цифре. Четыре карточки — итог дня и доли утра, дня и последних тридцати минут:
  график о том, *когда* двигались деньги, поэтому три из четырёх — доли, а не суммы. BSE 50 —
  единственная таблица, которая отдаёт минуты без колонки оборота; она отклоняется, а не
  считается нулём.""",

    "tr": """- **Kendi listeniz.** Menünün son girdisi, sizin tuttuğunuz listedir — endeksler ve hisseler yan
  yana, dört roster tablosuyla paylaşılır. Yalnızca anakara kodları toplanabilir: işlem hacmi her
  piyasanın kendi para biriminde bildirilir, bu yüzden Hong Kong veya New York adı dışarıda kalır
  ve durum satırı kaç tane olduğunu söyler. Bir gün, *herhangi bir* üye işlem gördüyse eksende
  yer alır; o güne ait satırı olmayan üye — işleme kapatılmış ya da henüz listelenmemiş — hiçbir
  şey eklemez. Bu, yukarıdaki tabloların kuralının kasıtlı olarak tersidir: bir endeks asla
  kapatılmaz, bir hisse kapatılır ve günü atmak, kapatılmayı hiçbir yerde işlem olmayan bir gün
  gibi gösterirdi.
- **Sepetin altındaki değişim**, her üyenin kendi önceki kapanışına göre ölçülen günlük
  değişimlerinin eşit ağırlıklı ortalamasıdır. Eşit ağırlıklıdır, çünkü bir liste portföy değildir:
  ağırlıklandıracak bir pozisyon büyüklüğü yoktur.
- **Tek bir seans, dakika dakika.** Üçüncü biçim ayrı bir sorgudur: tek bir günün açılıştan
  kapanışa kadar biriken toplamı. Kaynak yalnızca son beş seansı saklar, bu yüzden aralık
  sunulmaz — kare, çizdiği günü adlandırır. Eğri 15:00'te durur, çünkü uç noktanın sonra eklediği
  yarım saat, günlük rakamın da içermediği seans sonrası işlemlerdir. Dört kart, günün toplamı ile
  sabah, öğleden sonra ve son yarım saatin payıdır — para*ın ne zaman* hareket ettiğinin grafiği,
  bu yüzden dörtten üçü tutar değil paydır. BSE 50, işlem hacmi sütunu olmadan dakika bildiren tek
  tablodur ve hiç sayılmak yerine reddedilir.""",
}


def main():
    for tag, body in BODIES.items():
        path = HELP / f"help-{tag}.md"

        raw = path.read_bytes()

        # BOM 与 LF 都**照原样**，与 `port-help-ranges.py` 同一条规矩。
        had_bom = raw.startswith(b"\xef\xbb\xbf")

        text = raw.decode("utf-8-sig").lstrip("\ufeff")
        lines = text.replace("\r\n", "\n").split("\n")

        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(heads) <= CHAPTER:
            raise AssertionError(f"{tag}: only {len(heads)} chapters")

        at = heads[CHAPTER]
        end = heads[CHAPTER + 1] if len(heads) > CHAPTER + 1 else len(lines)

        # Idempotent: the block is appended at the end of the chapter, so its own first line is
        # the sentinel — drop it (and only it) wherever it already sits.
        sentinel = body.split("\n")[0]

        if sentinel in lines[at:end]:
            start = at + lines[at:end].index(sentinel)
            last = end - 1

            while last > start and lines[last].strip() == "":
                last -= 1

            del lines[start:last + 1]

            heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
            at = heads[CHAPTER]
            end = heads[CHAPTER + 1] if len(heads) > CHAPTER + 1 else len(lines)

        # One blank line between the last bullet and the block, never two: the chapter already
        # ends with its own blank, and a re-run would otherwise stack another one every time.
        while end - 1 > at and lines[end - 1].strip() == "" and lines[end - 2].strip() == "":
            del lines[end - 1]
            end -= 1

        block = body.rstrip("\n").split("\n") + [""]

        lines[end:end] = block

        out = "\n".join(lines)

        if not out.endswith("\n"):
            out += "\n"

        path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + out.encode("utf-8"))

        chapters = sum(1 for line in out.split("\n") if line.startswith("## "))

        print(f"{tag}: chapter {CHAPTER + 1}, +{len(block)} lines, {chapters} chapters")


if __name__ == "__main__":
    main()
