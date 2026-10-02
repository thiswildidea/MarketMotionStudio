# -*- coding: utf-8 -*-
"""四页清单板都多了「自选股」这一组，帮助里得跟着说 —— 第 11 章还要改掉一句已经错的话。

第十三页（指数长跑）原来写着「月线，不调整」，而它现在**是复权的**：为了能放个股。改的不是措辞
是事实，所以那一句是替换而不是追加。其余三章（大类资产 / 回撤与修复 / 持有胜率）本来就是复权
口径，只需要多一条说明：清单最后一档是自选股，四页共用一份，可以三地混装。

**改一处改全部 14 份**，顺序 = 导航顺序：第 11 章指数长跑、第 12 章大类资产、第 13 章回撤与修复、
第 14 章持有胜率。第 11 章动的是第 2 条 bullet（第 1 条是晚来的指数缺席，第 3 条是不看市场设置）；
其余三章各在最后一条 bullet 之后追加一条。

用法：
    python tools/port-watchlist-help.py            # 只打印要动的地方，不写
    python tools/port-watchlist-help.py --apply    # 真的写
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HELP = os.path.join(ROOT, "src/MarketMotionStudio/Assets/Help")

CHAPTER_INDEX_RACE = 10  # 0-based：第 11 章
CHAPTER_ASSET_RACE = 11  # 0-based：第 12 章
CHAPTER_DRAWDOWN = 12    # 0-based：第 13 章
CHAPTER_HOLD_ODDS = 13   # 0-based：第 14 章

# ---- 1) 第 11 章第 2 条：不调整 → 复权，并把两种口径写清楚 -----------------------------

ADJUSTED = {
    "en-US": """- **Monthly, and adjusted now.** An index pays nothing out, but a stock pays dividends and splits
  its shares: Apple reads +193% across ten years unadjusted and +1183% adjusted, because the
  unadjusted line carries cliffs no holder ever fell off. The indices are untouched by it — asked
  for an adjustment, the source answers an index with the same rows it always did, and all twelve
  came back identical on both calls. What the board does carry is a difference worth stating rather
  than hiding: an index row is a **price** return, because an index is not a holding, while a stock
  row is a **total** one, dividends and splits put back.""",
    "de": """- **Monatlich, und jetzt angepasst.** Ein Index schüttet nichts aus, aber eine Aktie zahlt
  Dividenden und teilt ihre Anteile: Apple liegt über zehn Jahre unangepasst bei +193 % und
  angepasst bei +1183 %, weil die unangepasste Linie Klippen enthält, von denen kein Halter je
  gefallen ist. Die Indizes bleiben unberührt — auf eine Anpassung hin antwortet die Quelle einem
  Index mit denselben Zeilen wie immer, und alle zwölf waren auf beiden Wegen identisch. Was das
  Tableau nun trägt, ist ein Unterschied, den man nennen sollte: Eine Indexzeile ist eine
  **Kurs**rendite, denn ein Index ist keine Position, eine Aktienzeile dagegen eine
  **Gesamt**rendite mit Dividenden und Splits.""",
    "es": """- **Mensual, y ahora ajustado.** Un índice no reparte nada, pero una acción paga dividendos y
  desdobla sus títulos: Apple marca +193 % en diez años sin ajustar y +1183 % ajustado, porque la
  serie sin ajustar lleva acantilados por los que ningún tenedor cayó nunca. Los índices no se
  alteran: si se pide ajuste, la fuente responde a un índice con las mismas filas de siempre, y los
  doce resultaron idénticos en ambas vías. Lo que sí trae el tablero es una diferencia que conviene
  declarar: la fila de un índice es una rentabilidad **de precio**, porque un índice no es una
  posición, mientras que la de una acción es **total**, con dividendos y desdoblamientos
  incorporados.""",
    "fr": """- **Mensuel, et désormais ajusté.** Un indice ne distribue rien, mais une action verse des
  dividendes et divise ses titres : Apple affiche +193 % sur dix ans sans ajustement et +1183 %
  ajusté, car la ligne non ajustée porte des falaises dont aucun détenteur n'est jamais tombé. Les
  indices n'y changent pas : si l'on demande un ajustement, la source répond à un indice avec les
  mêmes lignes qu'avant, et les douze étaient identiques sur les deux voies. Ce que le tableau porte
  désormais est une différence qu'il vaut mieux énoncer : la ligne d'un indice est un rendement
  **de prix**, car un indice n'est pas une position, celle d'une action est un rendement **total**,
  dividendes et divisions remis dedans.""",
    "it": """- **Mensile, e ora aggiustato.** Un indice non distribuisce nulla, ma un'azione paga dividendi e
  fraziona le proprie quote: Apple segna +193 % in dieci anni non aggiustata e +1183 % aggiustata,
  perché la linea non aggiustata porta dirupi da cui nessun detentore è mai caduto. Gli indici non
  ne risentono: se si chiede un aggiustamento, la fonte risponde a un indice con le stesse righe di
  sempre, e tutti e dodici risultarono identici su entrambe le vie. Ciò che la tavola porta ora è
  una differenza da dichiarare: la riga di un indice è un rendimento **di prezzo**, perché un
  indice non è una posizione, quella di un'azione è un rendimento **totale**, con dividendi e
  frazionamenti rimessi dentro.""",
    "pl": """- **Miesięcznie, i teraz już z korektą.** Indeks nic nie wypłaca, ale akcja płaci dywidendy i
  dzieli swoje udziały: Apple pokazuje +193 % w dziesięć lat bez korekty i +1183 % z korektą, bo
  linia bez korekty niesie urwiska, z których żaden posiadacz nigdy nie spadł. Indeksów to nie
  dotyka — poproszona o korektę, źródło odpowiada indeksowi tymi samymi wierszami co zwykle, i
  wszystkie dwanaście wyszły identycznie obiema drogami. To, co tablica teraz niesie, to różnica
  warta wypowiedzenia: wiersz indeksu to zwrot **cenowy**, bo indeks nie jest pozycją, a wiersz
  akcji to zwrot **całkowity**, z dywidendami i podziałami wliczonymi.""",
    "pt-BR": """- **Mensal, e agora ajustado.** Um índice não distribui nada, mas uma ação paga dividendos e
  desdobra suas cotas: a Apple marca +193 % em dez anos sem ajuste e +1183 % com ajuste, porque a
  linha sem ajuste carrega penhascos dos quais nenhum detentor jamais caiu. Os índices não se
  alteram: pedido um ajuste, a fonte responde a um índice com as mesmas linhas de sempre, e os doze
  saíram idênticos nos dois caminhos. O que o quadro agora carrega é uma diferença que vale declarar:
  a linha de um índice é um retorno **de preço**, porque um índice não é uma posição, enquanto a de
  uma ação é um retorno **total**, com dividendos e desdobramentos recolocados.""",
    "cs": """- **Měsíčně, a nyní ajustováno.** Index nic nevyplácí, ale akcie platí dividendy a dělí své
  podíly: Apple ukazuje +193 % za deset let neajustovaně a +1183 % ajustovaně, protože
  neajustovaná čára nese srázy, z nichž žádný držitel nikdy nespadl. Indexů se to nedotkne —
  požádán o úpravu odpoví zdroj indexu týmiž řádky jako vždy, a všech dvanáct vyšlo na obou
  cestách identicky. Co tabule nese nyní, je rozdíl, který stojí za řeč: řádek indexu je
  **cenový** výnos, protože index není pozice, zatímco řádek akcie je výnos **celkový**, s
  dividendami a děleními zpět uvnitř.""",
    "tr": """- **Aylık, ve artık düzeltilmiş.** Bir endeks hiçbir şey dağıtmaz, ama bir hisse temettü öder ve
  paylarını böler: Apple on yılda düzeltilmemiş +193 %, düzeltilmiş +1183 % okur, çünkü
  düzeltilmemiş çizgi hiçbir yatırımcının düşmediği uçurumlar taşır. Endeksler bundan etkilenmez —
  düzeltme istendiğinde kaynak bir endekse her zamanki satırlarla yanıt verir ve on ikisi de iki
  yolda birebir aynı çıktı. Tablonun şimdi taşıdığı şey saklanacak değil söylenecek bir farktır:
  bir endeks satırı **fiyat** getirisidir, çünkü endeks bir pozisyon değildir; bir hisse satırı ise
  temettüleri ve bölünmeleri içine alan **toplam** getiridir.""",
    "ru": """- **Месяцы, и теперь с корректировкой.** Индекс ничего не выплачивает, а акция платит дивиденды и
  дробит свои доли: у Apple за десять лет получается +193 % без корректировки и +1183 % с ней,
  потому что некоppектированная линия несёт обрывы, с которых ни один держатель не падал. На
  индексы это не влияет: в ответ на запрос корректировки источник отдаёт индексу те же строки, что
  и всегда, и все двенадцать сошлись на обоих путях. Что таблица теперь несёт в себе — это разница,
  которую стоит назвать: строка индекса — это **ценовая** доходность, потому что индекс не является
  позицией, а строка акции — **полная**, с дивидендами и дроблениями внутри.""",
    "ja": """- **月足、そして今は調整済みです。** 指数は何も分配しませんが、個別株は配当を出し、株式分割も
  します。Apple は十年で未調整 +193 %、調整済み +1183 % になります。未調整の線には保有者が決して
  落ちていない崖が含まれているからです。指数は影響を受けません。調整を指定してもソースは指数に
  同じ行を返し、十二本すべてが両方の経路で一致しました。このboard が今抱えているのは、隠すより
  述べるべき違いです。指数の行は**価格**リターン（指数は保有物ではない）、個別株の行は配当と
  分割を織り込んだ**トータル**リターンです。""",
    "ko": """- **월간, 그리고 이제 조정 기준입니다.** 지수는 아무것도 지급하지 않지만 개별 종목은 배당을 하고
  주식을 분할합니다. 애플은 십 년间 미조정 +193 %, 조정 +1183 %로 읽히는데, 미조정 선에는 보유자가
  결코 겪지 않은 절벽이 들어 있기 때문입니다. 지수는 영향받지 않습니다. 조정을 요청해도 출처는
  지수에 늘 하던 것과 같은 행을 돌려주고, 열둘 모두 두 경로에서 동일했습니다. 이제 보드가 안고 있는
  것은 숨기기보다 밝혀야 할 차이입니다. 지수 행은 **가격** 수익률(지수는 보유 대상이 아니다)이고,
  개별 종목 행은 배당과 분할을 되돌려 넣은 **총** 수익률입니다.""",
    "zh-Hans": """- **月线，而且现在复权。** 指数不派息，但个股派息、还会拆份额：不复权的苹果十年只有 +193%，
  复权是 +1183%——不复权的曲线上有持有人根本没承受过的断崖。指数不受影响：源端对指数忽略复权
  参数，十二个指数在两条路上给出的序列一个数字都不差。要说清的是随之而来的差别：指数那一行是
  **价格**回报（指数不是持仓，什么也不派发），个股那一行是**含分红与份额折算的总回报**。""",
    "zh-Hant": """- **月線，而且現在復權。** 指數不派息，但個股派息、還會拆份額：不復權的蘋果十年只有 +193%，
  復權是 +1183%——不復權的曲線上有持有人根本沒承受過的斷崖。指數不受影響：源端對指數忽略復權
  參數，十二個指數在兩條路上給出的序列一個數字都不差。要說清的是隨之而來的差別：指數那一行是
  **價格**回報（指數不是持倉，什麼也不派發），個股那一行是**含分紅與份額折算的總回報**。""",
}

# ---- 2) 第 11 章末尾追加：自选股 --------------------------------------------------------

WATCH_11 = {
    "en-US": """- **Or your own list.** The last group in the menu is a list of your own: type a code, a name or
  pinyin to add one, and a mainland share, a Hong Kong one and a New York one can sit on it together
  — this board never asks the market setting. One list, shared by four boards, so a stock added here
  is offered on the asset race, the drawdown board and the hold-odds board too. Fewer than three and
  the fetch is refused.""",
    "de": """- **Oder die eigene Liste.** Die letzte Gruppe im Menü ist eine eigene Liste: Code, Name oder
  Pinyin eintippen, um einen Wert hinzuzufügen, und eine Festlandaktie, eine aus Hongkong und eine
  aus New York dürfen gemeinsam darauf stehen — dieses Tableau fragt die Markteinstellung nie. Eine
  Liste für vier Tableaus: Wer hier eine Aktie ergänzt, findet sie auch beim Anlagenrennen, bei den
  Rücksetzern und bei der Haltequote wieder. Unter dreien wird das Holen verweigert.""",
    "es": """- **O su propia lista.** El último grupo del menú es una lista propia: escriba un código, un
  nombre o pinyin para añadir uno, y un valor continental, uno de Hong Kong y uno de Nueva York
  pueden convivir en ella — este tablero nunca consulta el ajuste de mercado. Una lista para cuatro
  tableros: una acción añadida aquí también se ofrece en la carrera de activos, en las caídas y en
  la tasa de acierto. Con menos de tres se rechaza la descarga.""",
    "fr": """- **Ou votre propre liste.** Le dernier groupe du menu est une liste personnelle : tapez un code,
  un nom ou du pinyin pour en ajouter un, et une valeur continentale, une de Hong Kong et une de
  New York peuvent y figurer ensemble — ce tableau ne consulte jamais le réglage de marché. Une
  liste pour quatre tableaux : une action ajoutée ici est également proposée dans la course
  d'actifs, dans les replis et dans le taux de réussite. En dessous de trois, le chargement est
  refusé.""",
    "it": """- **Oppure la vostra lista.** L'ultimo gruppo del menu è una lista propria: scrivete un codice,
  un nome o il pinyin per aggiungerne uno, e un titolo continentale, uno di Hong Kong e uno di
  New York possono starci insieme — questa tavola non consulta mai l'impostazione di mercato. Una
  lista per quattro tavole: un'azione aggiunta qui è proposta anche nella corsa degli attivi, nei
  ribassi e nel tasso di riuscita. Sotto tre il recupero è rifiutato.""",
    "pl": """- **Albo własna lista.** Ostatnia grupa w menu to lista własna: wpisz kod, nazwę lub pinyin, aby
  dodać jeden walor, i akcja z kontynentu, z Hongkongu oraz z Nowego Jorku mogą być na niej razem
  — ta tablica nigdy nie pyta o ustawienie rynku. Jedna lista dla czterech tablic: akcję dodaną tu
  znajdziesz też w wyścigu aktywów, w obsunięciach i w skuteczności trzymania. Poniżej trzech
  pobieranie jest odrzucane.""",
    "pt-BR": """- **Ou a sua própria lista.** O último grupo do menu é uma lista própria: digite um código, um
  nome ou pinyin para acrescentar um, e um papel do continente, um de Hong Kong e um de Nova York
  podem conviver nela — este quadro nunca consulta a configuração de mercado. Uma lista para quatro
  quadros: uma ação acrescentada aqui também é oferecida na corrida de ativos, nas quedas e na taxa
  de acerto. Abaixo de três, a busca é recusada.""",
    "cs": """- **Nebo vlastní seznam.** Poslední skupina v menu je vlastní seznam: napište kód, název nebo
  pinyin a přidejte jeden, a cenný papír z pevniny, z Hongkongu a z New Yorku mohou být na něm
  zároveň — tato tabule se nikdy neptá na nastavení trhu. Jeden seznam pro čtyři tabule: akcii
  přidanou zde najdete i v závodu aktiv, v poklesech a v úspěšnosti držení. Pod tři se stahování
  odmítne.""",
    "tr": """- **Ya da kendi listeniz.** Menünün son grubu kendi listenizdir: bir tane eklemek için kod, ad
  veya pinyin yazın; anakara, Hong Kong ve New York değerleri birlikte durabilir — bu tablo piyasa
  ayarını hiç sormaz. Dört tablo için tek liste: buraya eklenen bir hisse, varlık yarışında,
  geri çekilmelerde ve tutma başarısında da sunulur. Üçün altında çekme reddedilir.""",
    "ru": """- **Или свой собственный список.** Последняя группа в меню — свой список: введите код, название
  или пинъинь, чтобы добавить одну бумагу, и бумага с материка, из Гонконга и из Нью-Йорка могут
  быть в нём вместе — эта таблица никогда не спрашивает настройку рынка. Один список на четыре
  таблицы: бумагу, добавленную здесь, предложат и в гонке активов, и в просадках, и в доле удачных
  удержаний. Меньше трёх — загрузка отклоняется.""",
    "ja": """- **あるいは自分のリスト。** メニューの最後のグループが自分のリストです。コード・名前・拼音を
  入力して追加します。本土株、香港株、ニューヨーク株を同じリストに置けます。このボードは市場設定を
  尋ねません。四つのボードで一つのリストを共有するため、ここで追加した銘柄は資産レース、
  ドローダウン、保有勝率でも選べます。三つ未満では取得を拒否します。""",
    "ko": """- **또는 직접 만든 목록.** 메뉴의 마지막 그룹이 직접 만든 목록입니다. 코드·이름·병음을 입력해
  하나를 추가하세요. 본토 종목과 홍콩 종목, 뉴욕 종목을 함께 올릴 수 있습니다. 이 보드는 시장 설정을
  묻지 않습니다. 네 개의 보드가 한 목록을 공유하므로, 여기서 추가한 종목은 자산 레이스와 낙폭,
  보유 승률에서도 고를 수 있습니다. 세 개 미만이면 가져오기를 거부합니다.""",
    "zh-Hans": """- **也可以跑你自己那一组。** 清单最后一档是自选股：搜代码、名字或拼音加进去，A股、港股、美股
  可以混装——这一页不看市场设置。四页共用一份清单：在这里加一只，大类资产、回撤与修复、持有胜率
  都能选它。少于三只会拒绝取数。""",
    "zh-Hant": """- **也可以跑你自己那一組。** 清單最後一檔是自選股：搜代碼、名稱或拼音加進去，A股、港股、美股
  可以混裝——這一頁不看市場設置。四頁共用一份清單：在這裡加一檔，大類資產、回撤與修復、持有勝率
  都能選它。少於三檔會拒絕取數。""",
}

# ---- 3) 第 12 / 13 / 14 章末尾追加：同一个说法，三页共用一句 -----------------------------

WATCH_REST = {
    "en-US": """- **Or your own list.** The last group in the menu is a list of your own: type a code, a name or
  pinyin to add one, and the three markets can be mixed on it. One list shared by four boards, so a
  stock added here is offered on the other three as well; it is fetched adjusted, exactly like the
  eight funds, so dividends and share splits are in the number. Fewer than three and the fetch is
  refused.""",
    "de": """- **Oder die eigene Liste.** Die letzte Gruppe im Menü ist eine eigene Liste: Code, Name oder
  Pinyin eintippen, um einen Wert hinzuzufügen, und die drei Märkte dürfen darauf gemischt werden.
  Eine Liste für vier Tableaus: Wer hier eine Aktie ergänzt, findet sie auf den drei anderen
  wieder; geholt wird sie ajustiert, genau wie die acht Fonds, also mit Dividenden und
  Anteilssplits in der Zahl. Unter dreien wird das Holen verweigert.""",
    "es": """- **O su propia lista.** El último grupo del menú es una lista propia: escriba un código, un
  nombre o pinyin para añadir uno, y en ella pueden mezclarse los tres mercados. Una lista para
  cuatro tableros: una acción añadida aquí también se ofrece en los otros tres; se descarga
  ajustada, exactamente como los ocho fondos, de modo que dividendos y desdoblamientos están en la
  cifra. Con menos de tres se rechaza la descarga.""",
    "fr": """- **Ou votre propre liste.** Le dernier groupe du menu est une liste personnelle : tapez un code,
  un nom ou du pinyin pour en ajouter un, et les trois marchés peuvent s'y mélanger. Une liste pour
  quatre tableaux : une action ajoutée ici est également proposée sur les trois autres ; elle est
  chargée ajustée, exactement comme les huit fonds, si bien que dividendes et divisions sont dans
  le chiffre. En dessous de trois, le chargement est refusé.""",
    "it": """- **Oppure la vostra lista.** L'ultimo gruppo del menu è una lista propria: scrivete un codice,
  un nome o il pinyin per aggiungerne uno, e i tre mercati possono esservi mescolati. Una lista per
  quattro tavole: un'azione aggiunta qui è proposta anche sulle altre tre; è scaricata aggiustata,
  esattamente come gli otto fondi, quindi dividendi e frazionamenti sono nel numero. Sotto tre il
  recupero è rifiutato.""",
    "pl": """- **Albo własna lista.** Ostatnia grupa w menu to lista własna: wpisz kod, nazwę lub pinyin, aby
  dodać jeden walor, a trzy rynki można na niej mieszać. Jedna lista dla czterech tablic: akcję
  dodaną tu znajdziesz też na trzech pozostałych; pobiera się ją z korektą, dokładnie jak osiem
  funduszy, więc dywidendy i podziały są w liczbie. Poniżej trzech pobieranie jest odrzucane.""",
    "pt-BR": """- **Ou a sua própria lista.** O último grupo do menu é uma lista própria: digite um código, um
  nome ou pinyin para acrescentar um, e os três mercados podem ser misturados nela. Uma lista para
  quatro quadros: uma ação acrescentada aqui também é oferecida nos outros três; ela é buscada
  ajustada, exatamente como os oito fundos, de modo que dividendos e desdobramentos estão no
  número. Abaixo de três, a busca é recusada.""",
    "cs": """- **Nebo vlastní seznam.** Poslední skupina v menu je vlastní seznam: napište kód, název nebo
  pinyin a přidejte jeden; tři trhy na něm lze míchat. Jeden seznam pro čtyři tabule: akcii
  přidanou zde najdete i na dalších třech; stahuje se ajustovaně, přesně jako osm fondů, takže
  dividendy a dělení jsou v čísle. Pod tři se stahování odmítne.""",
    "tr": """- **Ya da kendi listeniz.** Menünün son grubu kendi listenizdir: bir tane eklemek için kod, ad
  veya pinyin yazın; üç piyasa burada karıştırılabilir. Dört tablo için tek liste: buraya eklenen
  bir hisse diğer üçünde de sunulur; sekiz fonla tamamen aynı şekilde düzeltilmiş çekilir, yani
  temettüler ve pay bölünmeleri sayının içindedir. Üçün altında çekme reddedilir.""",
    "ru": """- **Или свой собственный список.** Последняя группа в меню — свой список: введите код, название
  или пинъинь, чтобы добавить одну бумагу, и три рынка в нём можно смешивать. Один список на
  четыре таблицы: бумагу, добавленную здесь, предложат и на трёх остальных; её загружают с
  корректировкой, точь-в-точь как восемь фондов, поэтому дивиденды и дробления уже в числе.
  Меньше трёх — загрузка отклоняется.""",
    "ja": """- **あるいは自分のリスト。** メニューの最後のグループが自分のリストです。コード・名前・拼音を
  入力して追加し、三つの市場を混在させられます。四つのボードで一つのリストを共有するため、ここで
  追加した銘柄は残り三つでも選べます。取得は八本のファンドとまったく同じく調整済みで、配当と
  分割が数値に含まれます。三つ未満では取得を拒否します。""",
    "ko": """- **또는 직접 만든 목록.** 메뉴의 마지막 그룹이 직접 만든 목록입니다. 코드·이름·병음을 입력해
  하나를 추가하고, 세 시장을 섞어 담을 수 있습니다. 네 개의 보드가 한 목록을 공유하므로 여기서
  추가한 종목은 나머지 세 곳에서도 고를 수 있습니다. 가져오기는 여덟 펀드와 똑같이 조정 기준이며,
  배당과 주식 분할이 수치에 들어 있습니다. 세 개 미만이면 가져오기를 거부합니다.""",
    "zh-Hans": """- **也可以跑你自己那一组。** 清单最后一档是自选股：搜代码、名字或拼音加进去，三个市场可以
  混装。四页共用一份清单——在这里加一只，其余三页都能选它；取数和这八档基金一样走复权，分红与
  份额折算都算在里面。少于三只会拒绝取数。""",
    "zh-Hant": """- **也可以跑你自己那一組。** 清單最後一檔是自選股：搜代碼、名稱或拼音加進去，三個市場可以
  混裝。四頁共用一份清單——在這裡加一檔，其餘三頁都能選它；取數和這八檔基金一樣走復權，分紅與
  份額折算都算在裡面。少於三檔會拒絕取數。""",
}


def chapter_bounds(lines, chapter):
    heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

    if len(heads) <= chapter:
        return None

    start = heads[chapter]
    end = heads[chapter + 1] if len(heads) > chapter + 1 else len(lines)

    return start, end


def bullet_bounds(lines, start, end, index):
    """[at, stop) of one bullet inside a chapter, continuation lines included."""
    found = [i for i in range(start, end) if lines[i].startswith("- ")]

    if len(found) <= index:
        return None

    at = found[index]
    stop = found[index + 1] if len(found) > index + 1 else end

    while stop > at and lines[stop - 1].strip() == "":
        stop -= 1

    return at, stop


def insert_after_last_bullet(lines, start, end):
    """The line number just after the chapter's last bullet."""
    found = [i for i in range(start, end) if lines[i].startswith("- ")]

    if not found:
        return None

    at = found[-1]
    stop = at + 1

    while stop < end and lines[stop].startswith("  "):
        stop += 1

    return stop


def main():
    apply = "--apply" in sys.argv

    jobs = [
        # (chapter, bullet index or None, texts, what it does)
        (CHAPTER_INDEX_RACE, 1, ADJUSTED, "替换第 11 章第 2 条"),
        (CHAPTER_INDEX_RACE, None, WATCH_11, "第 11 章末尾追加"),
        (CHAPTER_ASSET_RACE, None, WATCH_REST, "第 12 章末尾追加"),
        (CHAPTER_DRAWDOWN, None, WATCH_REST, "第 13 章末尾追加"),
        (CHAPTER_HOLD_ODDS, None, WATCH_REST, "第 14 章末尾追加"),
    ]

    # 倒序做：插入会不会打乱后面的行号 —— 从后往前，前面的行号不受影响。
    for chapter, index, texts, what in reversed(jobs):
        for tag, new in texts.items():
            path = os.path.join(HELP, f"help-{tag}.md")

            text = open(path, "rb").read().decode("utf-8-sig").lstrip("\ufeff")
            lines = text.replace("\r\n", "\n").split("\n")

            bounds = chapter_bounds(lines, chapter)

            if bounds is None:
                print(f"!! {tag}: 章节不够")
                continue

            start, end = bounds

            if index is None:
                at = insert_after_last_bullet(lines, start, end)

                if at is None:
                    print(f"!! {tag}: 那一章没有 bullet")
                    continue

                if any(new.split("\n")[0] in line for line in lines[start:end]):
                    print(f"-- {tag}: {what} 已经在，跳过")
                    continue

                if not apply:
                    print(f"--- {tag} · {what}（插在第 {at - start + 1} 行）---")
                    continue

                lines[at:at] = new.split("\n")
            else:
                span = bullet_bounds(lines, start, end, index)

                if span is None:
                    print(f"!! {tag}: bullet 不够")
                    continue

                at, stop = span

                if not apply:
                    print(f"--- {tag} · {what} ---")
                    print("\n".join(lines[at:stop]))
                    print()
                    continue

                lines[at:stop] = new.split("\n")

            out = "\n".join(lines)

            if not out.endswith("\n"):
                out += "\n"

            # 保 BOM：源文件有，写回去也得有。
            with io.open(path, "wb") as handle:
                handle.write(b"\xef\xbb\xbf" + out.encode("utf-8"))

            print(f"{tag}: {what} 已写")


if __name__ == "__main__":
    main()
