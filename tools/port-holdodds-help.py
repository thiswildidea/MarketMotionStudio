# -*- coding: utf-8 -*-
r"""把「持有胜率」这一章插进 14 份帮助文档。

插在第 13 章「回撤与修复」之后（0 基下标 12），第 14 章「收益矩阵」之前 → 25 章。
三页（大类资产 / 回撤与修复 / 持有胜率）跑同一批八档，章节也应当连着：
赚了多少、付出了什么代价、以及随便什么时候进去这事儿有多常成立。

用法：python tools\port-holdodds-help.py
"""
from pathlib import Path

HELP = Path(r"D:\software\MarketMotionStudio\src\MarketMotionStudio\Assets\Help")

# 插在第 13 章「回撤与修复」之后（0 基下标 12）。
AFTER = 12

TITLES = {
    "zh-Hans": "持有胜率",
    "zh-Hant": "持有勝率",
    "en-US": "Hold odds",
    "ja": "保有勝率",
    "ko": "보유 승률",
    "de": "Haltequote",
    "fr": "Taux de réussite",
    "it": "Tasso di riuscita",
    "es": "Tasa de acierto",
    "pt-BR": "Taxa de acerto",
    "pl": "Skuteczność",
    "cs": "Úspěšnost",
    "ru": "Доля удачных",
    "tr": "Tutma oranı",
}

BODIES = {
    "zh-Hans": """一行是**已走完的持有中賺錢的那一部分**——在區間裡每一個可以買進並持有相同時間的月份中，
最後是賺的那一部分佔多少。跑的是和大類資產、回撤與修復同樣的八檔，打分的是「持有」這件事多常成立，
而不是賺了多少。

- **一次是運氣，八十四次才是比率。** 區間裡每一個月都是一次買進，每一次都持有相同的時間，所以
  十年裡的三年持有是八十四次，不是一次。它們之間共用月份，這正是要緊的地方：為了讓樣本彼此獨立
  而把它們稀釋到三次，剩下的是一個只有三個觀測值的比率。
- **一次持有從「走完的那個月」才計入。** 區間最後三年買進的還沒走完，把沒走完的算成虧損，會讓
  每一行在末尾只因為日曆而向下彎。所以板面從第一個可能有持有走完的月份開始。
- **一個行要有六次持有走完才上板。** 一次持有是 0% 或 100%，而這兩個數字無論哪個落在排名的
  一端，都不是它掙來的。
- **復權、月線、從各自第一個月起算**，理由與前兩頁相同：基金的分紅從不出現在價格裡，2019 年
  才有的那一档沒有 2016 年的持有可以計勝負。
- **持有期是這一頁唯一的新選項。** 同樣這十年，持有一年與持有五年是兩個不同的問題，答案也不同，
  八檔的排序在兩者之間會重排。
- **行仍然在競速。** 排序按勝率，最常賺的在最上面，隨著月份推進互相換位。

近十年、持有三年實測：納指 ETF 八十四次持有全部是賺的，恒生 ETF 只有四成——這兩行在「大類資產」
那一页是被十年總收益拉開的，在這一页是被「進去這件事到底成不成立」拉開的。

這一頁不看市場設置：八檔都在境內掛牌。區間不足 12 個月會拒絕取數。
""",

    "zh-Hant": """一行是**已走完的持有中賺錢的那一部分**——在區間裡每一個可以買進並持有相同時間的月份中，
最後是賺的那一部分佔多少。跑的是和大類資產、回撤與修復同樣的八檔，打分的是「持有」這件事多常成立，
而不是賺了多少。

- **一次是運氣，八十四次才是比率。** 區間裡每一個月都是一次買進，每一次都持有相同的時間，所以
  十年裡的三年持有是八十四次，不是一次。它們之間共用月份，這正是要緊的地方：為了讓樣本彼此獨立
  而把它們稀釋到三次，剩下的是一個只有三個觀測值的比率。
- **一次持有從「走完的那個月」才計入。** 區間最後三年買進的還沒走完，把沒走完的算成虧損，會讓
  每一行在末尾只因為日曆而向下彎。所以板面從第一個可能有持有走完的月份開始。
- **一個行要有六次持有走完才上板。** 一次持有是 0% 或 100%，而這兩個數字無論哪個落在排名的
  一端，都不是它掙來的。
- **復權、月線、從各自第一個月起算**，理由與前兩頁相同：基金的分紅從不出現在價格裡，2019 年
  才有的那一檔沒有 2016 年的持有可以計勝負。
- **持有期是這一頁唯一的新選項。** 同樣這十年，持有一年與持有五年是兩個不同的問題，答案也不同，
  八檔的排序在兩者之間會重排。
- **行仍然在競速。** 排序按勝率，最常賺的在最上面，隨著月份推進互相換位。

近十年、持有三年實測：納指 ETF 八十四次持有全部是賺的，恒生 ETF 只有四成——這兩行在「大類資產」
那一頁是被十年總收益拉開的，在這一頁是被「進去這件事到底成不成立」拉開的。

這一頁不看市場設置：八檔都在境內掛牌。區間不足 12 個月會拒絕取數。
""",

    "en-US": """A row is **the share of finished entries that gained** — of all the months a holder could have
bought in and held for the same length of time, the share that ended up ahead. The same eight
holdings as the asset race and the drawdown board, scored on whether holding them worked rather
than on how much they made.

- **One entry is luck; eighty-four of them are a rate.** Every month in the range is an entry and
  each is held for the same length of time, so a three-year hold across ten years is eighty-four
  entries per row, not one. They share months, and that is the point: thinning them out to three
  independent ones would leave a rate with three observations in it.
- **An entry counts from the month it finishes.** Nothing bought in the last three years of the
  range has finished, and counting an unfinished entry as a loss would bend every row downwards at
  the end for no reason but the calendar. So the board opens on the first month an entry could have
  finished on.
- **A row joins on its sixth finished entry.** One entry is 0% or 100%, and either number sitting
  at an end of the ranking is an end it has not earned.
- **Adjusted, monthly, and from each holding's own first month**, for the reasons the asset race
  gives: a fund's distributions never appear in its price, and a fund launched in 2019 has no 2016
  entry to have won or lost.
- **The holding period is this board's one new choice.** One year and five years over the same ten
  years are different questions with different answers, and the eight rows reorder between them.
- **The rows still race.** They are ordered by their rate, most often ahead at the top, and they
  trade places as their months pass.

Measured over the last ten years with a three-year hold: the Nasdaq fund was ahead on all
eighty-four of its entries and the Hong Kong fund on forty per cent of them — two rows the asset
race separates by ten years of total return and this board separates by whether walking in worked
at all.

Not governed by the market setting: all eight are quoted on a mainland exchange. Fewer than twelve
months in the range is refused.
""",

    "ja": """行は**完了したエントリーのうち利益になった割合**——区間内で買って同じ期間だけ保有できるすべての
月のうち、最終的にプラスになったものの割合。資産クラス、ドローダウンと同じ八つの資産を、
いくら稼いだかではなく保有が成立した頻度で採点する。

- **一つは運、八十四個は率。** 区間の各月がエントリーで、どれも同じ期間だけ保有する。したがって
  十年間の三年保有は八十四回であって一回ではない。互いの月を共有するが、それが要点——標本を
  独立させるために三つに間引けば、三つの観測値しかない率が残る。
- **エントリーは完了した月から数える。** 区間の最後の三年で買った分はまだ終わっていない。
  終わっていないものを損失として数えれば、どの行も末尾でカレンダー的理由だけで下向きに曲がる。
  ゆえに板は、最初のエントリーが完了しうる月から始まる。
- **六つのエントリーが完了した時点で行が参加する。** 一つのエントリーは 0% か 100% であり、
  どちらが順位の端に置かれても、それは稼いだ席ではない。
- **調整済み・月次・各自の最初の月から**、資産クラスのページと同じ理由：ファンドの分配金は価格に
  現れないし、2019 年設定のファンドに 2016 年のエントリーは存在しない。
- **保有期間はこの板で唯一の新しい選択肢。** 同じ十年でも一年と五年では問うていることが違い、
  八つの行はその間で並び替わる。
- **行は依然として競う。** 率の順に並び、最も高くプラスで終わるものが上になり、月が進むにつれて
  入れ替わる。

近十年・三年保有の実測：ナスダック ETF は八十四回すべてがプラス、香港 ETF は四割——この二行は
資産クラスの板では十年の総収益で引き離され、この板では「そもそも成立したか」で引き離される。

市場設定の管轄外：八つすべてが本土の取引所に上場している。区間が 12 か月未満なら拒否する。
""",

    "ko": """행은 **이익으로 끝난 완료 진입의 비율**—구간 안에서 사서 같은 기간 보유할 수 있었던 모든 달 중,
결국 플러스가 된 것의 비율. 자산군·낙폭 보드와 같은 여덟 자산을, 얼마를 벌었는지가 아니라 보유가
얼마나 자주 통했는지로 평가한다.

- **하나의 진입은 운이고, 여든네 개는 비율이다.** 구간의 매달이 진입이며 모두 같은 기간 보유한다.
  따라서 십 년 동안의 삼 년 보유는 한 번이 아니라 여든네 번이다. 서로 달을 공유하지만 그것이
  요점—표본을 독립적으로 만들려고 셋으로 줄이면, 관측값이 셋뿐인 비율만 남는다.
- **진입은 끝난 달부터 센다.** 구간 마지막 삼 년에 산 것은 아직 끝나지 않았다. 끝나지 않은 것을
  손실로 세면 모든 행이 달력 때문에 끝에서 아래로 휜다. 그러므로 보드는 첫 진입이 끝날 수 있는
  달에서 시작한다.
- **여섯 진입이 끝나면 행이 합류한다.** 하나의 진입은 0% 아니면 100%이고, 어느 쪽이든 순위의 한 끝에
  놓이는 것은 스스로 얻은 자리가 아니다.
- **조정·월간·각자의 첫 달부터**, 자산군 페이지와 같은 이유: 펀드의 분배금은 가격에 나타나지 않고,
  2019년에 생긴 펀드에는 2016년 진입이 존재하지 않는다.
- **보유 기간은 이 보드의 유일한 새 선택지.** 같은 십 년이라도 일 년과 오 년은 다른 질문이고 답도
  다르며, 여덟 행은 그 사이에서 순서가 바뀐다.
- **행은 여전히 경주한다.** 비율 순으로 정렬되어 가장 자주 플러스인 쪽이 위에 오고, 달이 지나며
  자리를 바꾼다.

지난 십 년·삼 년 보유 실측: 나스닥 ETF는 여든네 번 모두 플러스였고 홍콩 ETF는 사할뿐이었다—이 두
행은 자산군 보드에서는 십 년 총수익으로 갈리고, 이 보드에서는 "아예 통했는지"로 갈린다.

시장 설정의 관할이 아니다: 여덟 모두 본토 거래소에 상장되어 있다. 구간이 12개월 미만이면 거부한다.
""",

    "de": """Eine Zeile ist **der Anteil der beendeten Einstiege, die gewonnen haben** — von allen Monaten, in
denen man hätte einsteigen und gleich lang halten können, der Anteil, der am Ende im Plus lag.
Dieselben acht Anlagen wie bei den Anlageklassen und den Rücksetzern, bewertet danach, ob das
Halten funktionierte, nicht danach, wie viel es einbrachte.

- **Ein Einstieg ist Glück; vierundachtzig sind eine Quote.** Jeder Monat im Zeitraum ist ein
  Einstieg, und alle werden gleich lang gehalten: ein dreijähriges Halten über zehn Jahre sind
  vierundachtzig Einstiege pro Zeile, nicht einer. Sie teilen sich Monate, und genau das ist der
  Punkt — sie auf drei unabhängige auszudünnen ließe eine Quote mit drei Beobachtungen übrig.
- **Ein Einstieg zählt ab dem Monat, in dem er endet.** Was in den letzten drei Jahren des Zeitraums
  gekauft wurde, ist nicht beendet; ein nicht beendeter Einstieg als Verlust gezählt würde jede
  Zeile am Ende allein wegen des Kalenders nach unten biegen. Die Tafel beginnt daher mit dem
  ersten Monat, in dem ein Einstieg überhaupt enden konnte.
- **Eine Zeile kommt dazu, sobald sechs Einstiege beendet sind.** Ein Einstieg ist 0 % oder 100 %,
  und jede dieser Zahlen an einem Ende der Rangliste ist ein Ende, das sie sich nicht verdient hat.
- **Adjustiert, monatlich und ab dem jeweils ersten eigenen Monat**, aus den Gründen, die die
  Anlageklassen nennen: Ausschüttungen eines Fonds erscheinen nie in seinem Preis, und ein 2019
  aufgelegter Fonds hat keinen Einstieg aus 2016, den er gewinnen oder verlieren konnte.
- **Die Haltedauer ist die einzige neue Wahl auf dieser Tafel.** Ein Jahr und fünf Jahre über
  dieselben zehn Jahre sind zwei verschiedene Fragen mit zwei verschiedenen Antworten, und die
  acht Zeilen ordnen sich dazwischen neu.
- **Die Zeilen rennen weiter.** Sie sind nach ihrer Quote geordnet — am häufigsten im Plus oben —
  und tauschen die Plätze, während die Monate vergehen.

Gemessen über die letzten zehn Jahre mit drei Jahren Haltedauer: Der Nasdaq-Fonds lag bei allen
vierundachtzig Einstiegen vorn, der Hongkong-Fonds bei vierzig Prozent von ihnen — zwei Zeilen, die
die Anlageklassen nach zehn Jahren Gesamtertrag trennt und diese Tafel danach trennt, ob das
Einsteigen überhaupt funktioniert hat.

Nicht von der Markteinstellung abhängig: alle acht werden an einer Festlandbörse gehandelt. Weniger
als zwölf Monate im Zeitraum werden abgelehnt.
""",

    "fr": """Une ligne, c'est **la part des entrées terminées qui ont gagné** — parmi tous les mois où l'on
aurait pu entrer et garder la même durée, la part qui s'est terminée dans le vert. Les huit mêmes
supports que la course des classes d'actifs et le tableau des reculs, notés sur le fait de savoir
si les détenir a fonctionné, non sur ce qu'ils ont rapporté.

- **Une entrée, c'est de la chance ; quatre-vingt-quatre, c'est un taux.** Chaque mois de la
  période est une entrée, et toutes sont gardées la même durée : détenir trois ans sur dix ans,
  c'est quatre-vingt-quatre entrées par ligne, pas une. Elles partagent des mois, et c'est là le
  point : les réduire à trois entrées indépendantes laisserait un taux avec trois observations.
- **Une entrée compte à partir du mois où elle se termine.** Ce qui est acheté dans les trois
  dernières années de la période n'est pas terminé ; compter une entrée non terminée comme une
  perte ferait plier chaque ligne vers le bas à la fin pour la seule raison du calendrier. Le
  tableau commence donc au premier mois où une entrée pouvait se terminer.
- **Une ligne arrive dès que six entrées sont terminées.** Une entrée, c'est 0 % ou 100 %, et
  chacun de ces deux nombres à un bout du classement est un bout qu'elle n'a pas mérité.
- **Ajusté, mensuel, et à partir du premier mois propre à chaque support**, pour les raisons que
  donne la course des classes d'actifs : les distributions d'un fonds n'apparaissent jamais dans
  son cours, et un fonds lancé en 2019 n'a aucune entrée de 2016 à avoir gagnée ou perdue.
- **La durée de détention est le seul nouveau choix de ce tableau.** Un an et cinq ans sur les
  mêmes dix ans sont deux questions différentes avec deux réponses différentes, et les huit lignes
  se réordonnent entre les deux.
- **Les lignes courent toujours.** Elles sont ordonnées par leur taux — le plus souvent en gain
  en haut — et échangent leurs places à mesure que les mois passent.

Mesuré sur les dix dernières années avec une détention de trois ans : le fonds Nasdaq était en
avance sur ses quatre-vingt-quatre entrées et le fonds de Hong Kong sur quarante pour cent d'entre
elles — deux lignes que la course des classes d'actifs sépare par dix ans de rendement total et que
ce tableau sépare par le fait d'entrer, tout simplement.

Ne dépend pas du réglage de marché : les huit sont cotés sur une place continentale. Moins de douze
mois dans la période est refusé.
""",

    "it": """Una riga è **la quota delle entrate concluse che hanno guadagnato** — fra tutti i mesi in cui si
sarebbe potuti entrare e mantenere per la stessa durata, la quota finita in guadagno. Gli stessi
otto strumenti della corsa delle classi di attività e della tavola dei ribassi, valutati sul fatto
che tenerli abbia funzionato, non su quanto abbiano reso.

- **Un'entrata è fortuna; ottantaquattro sono un tasso.** Ogni mese dell'intervallo è un'entrata e
  tutte sono mantenute per la stessa durata: detenere tre anni su dieci anni sono ottantaquattro
  entrate per riga, non una. Condividono i mesi, ed è proprio questo il punto: diradarle a tre
  indipendenti lascerebbe un tasso con tre osservazioni dentro.
- **Un'entrata conta dal mese in cui finisce.** Ciò che è comprato negli ultimi tre anni
  dell'intervallo non è finito, e contare un'entrata non finita come perdita piegherebbe ogni riga
  verso il basso alla fine per la sola ragione del calendario. La tavola parte quindi dal primo mese
  in cui un'entrata poteva finire.
- **Una riga entra quando sei entrate sono concluse.** Un'entrata è 0% o 100%, e ciascuno di questi
  due numeri a un'estremità della classifica è un'estremità che non ha meritato.
- **Aggiustato, mensile e dal primo mese proprio di ciascuno strumento**, per le ragioni che dà la
  corsa delle classi di attività: le distribuzioni di un fondo non compaiono mai nel suo prezzo, e
  un fondo lanciato nel 2019 non ha entrate del 2016 da aver vinte o perse.
- **Il periodo di detenzione è l'unica nuova scelta di questa tavola.** Un anno e cinque anni sugli
  stessi dieci anni sono due domande diverse con due risposte diverse, e le otto righe si
  riordinano fra le due.
- **Le righe corrono ancora.** Sono ordinate per il loro tasso — più spesso in guadagno in alto — e
  si scambiano di posto mentre i mesi passano.

Misurato sugli ultimi dieci anni con una detenzione di tre anni: il fondo Nasdaq era in vantaggio
su tutte le ottantaquattro entrate e il fondo di Hong Kong sul quaranta per cento di esse — due
righe che la corsa delle classi di attività separa per dieci anni di rendimento totale e che questa
tavola separa per il semplice fatto di essere entrati.

Non dipende dall'impostazione del mercato: tutti e otto sono quotati su una borsa continentale.
Meno di dodici mesi nell'intervallo viene rifiutato.
""",

    "es": """Una fila es **la proporción de entradas terminadas que ganaron** — de todos los meses en que se
pudo entrar y mantener el mismo tiempo, la parte que acabó en ganancia. Las mismas ocho inversiones
que la carrera de clases de activos y el tablero de caídas, puntuadas por si mantenerlas funcionó,
no por cuánto dieron.

- **Una entrada es suerte; ochenta y cuatro son una tasa.** Cada mes del periodo es una entrada y
  todas se mantienen el mismo tiempo, así que mantener tres años a lo largo de diez son ochenta y
  cuatro entradas por fila, no una. Comparten meses, y ahí está el punto: reducirlas a tres
  independientes dejaría una tasa con tres observaciones dentro.
- **Una entrada cuenta desde el mes en que termina.** Lo comprado en los últimos tres años del
  periodo no ha terminado, y contar una entrada sin terminar como pérdida doblaría cada fila hacia
  abajo al final por la sola razón del calendario. El tablero empieza por tanto en el primer mes en
  que una entrada podía haber terminado.
- **Una fila entra cuando han terminado seis entradas.** Una entrada es 0 % o 100 %, y cualquiera
  de esas dos cifras en un extremo de la clasificación es un extremo que no ha ganado.
- **Ajustado, mensual y desde el primer mes propio de cada inversión**, por las razones que da la
  carrera de clases de activos: las distribuciones de un fondo nunca aparecen en su precio, y un
  fondo lanzado en 2019 no tiene entradas de 2016 que ganar o perder.
- **El periodo de tenencia es la única elección nueva de este tablero.** Un año y cinco años sobre
  los mismos diez años son dos preguntas distintas con dos respuestas distintas, y las ocho filas
  se reordenan entre una y otra.
- **Las filas siguen corriendo.** Se ordenan por su tasa — la que más veces acaba en ganancia
  arriba — y se intercambian los puestos mientras pasan los meses.

Medido en los últimos diez años con una tenencia de tres años: el fondo Nasdaq acabó en ganancia
en las ochenta y cuatro entradas y el fondo de Hong Kong en el cuarenta por ciento de ellas — dos
filas que la carrera de clases de activos separa por diez años de rentabilidad total y este tablero
separa por si entrar, sencillamente, funcionó.

No depende del ajuste de mercado: las ocho cotizan en un mercado continental. Menos de doce meses
en el periodo se rechaza.
""",

    "pt-BR": """Uma linha é **a parcela das entradas concluídas que ganharam** — de todos os meses em que se
poderia ter entrado e mantido pelo mesmo tempo, a parte que terminou no positivo. Os mesmos oito
ativos da corrida de classes de ativos e do quadro de quedas, pontuados por quantas vezes mantê-los
funcionou, não por quanto renderam.

- **Uma entrada é sorte; oitenta e quatro são uma taxa.** Cada mês do período é uma entrada e todas
  são mantidas pelo mesmo tempo, então manter três anos ao longo de dez são oitenta e quatro
  entradas por linha, não uma. Elas compartilham meses, e esse é o ponto: reduzi-las a três
  independentes deixaria uma taxa com três observações dentro.
- **Uma entrada conta a partir do mês em que termina.** O que foi comprado nos últimos três anos do
  período ainda não terminou, e contar uma entrada inacabada como perda dobraria cada linha para
  baixo no fim pela única razão do calendário. O quadro começa, portanto, no primeiro mês em que
  uma entrada podia ter terminado.
- **Uma linha entra quando seis entradas terminaram.** Uma entrada é 0% ou 100%, e qualquer um
  desses dois números numa ponta do ranking é uma ponta que ela não conquistou.
- **Ajustado, mensal e a partir do primeiro mês de cada ativo**, pelas razões que dá a corrida de
  classes de ativos: as distribuições de um fundo nunca aparecem no seu preço, e um fundo lançado em
  2019 não tem entradas de 2016 para ganhar ou perder.
- **O período de manutenção é a única escolha nova deste quadro.** Um ano e cinco anos sobre os
  mesmos dez anos são duas perguntas diferentes com duas respostas diferentes, e as oito linhas se
  reordenam entre elas.
- **As linhas continuam correndo.** Ordenam-se pela taxa — a que mais vezes termina no positivo no
  topo — e trocam de lugar enquanto os meses passam.

Medido nos últimos dez anos com manutenção de três anos: o fundo Nasdaq terminou no positivo em
todas as oitenta e quatro entradas e o fundo de Hong Kong em quarenta por cento delas — duas linhas
que a corrida de classes de ativos separa por dez anos de retorno total e este quadro separa por
algo mais simples: entrar, pura e simplesmente, funcionou ou não.

Não depende da configuração de mercado: os oito são cotados numa bolsa continental. Menos de doze
meses no período é recusado.
""",

    "pl": """Wiersz to **udział zakończonych wejść, które zarobiły** — ze wszystkich miesięcy, w których można
było wejść i trzymać równie długo, część zakończona na plusie. Te same osiem instrumentów co w
wyścigu klas aktywów i na tablicy obsunięć, oceniane według tego, czy trzymanie ich zadziałało, a
nie według tego, ile dały zarobić.

- **Jedno wejście to szczęście; osiemdziesiąt cztery to wskaźnik.** Każdy miesiąc okresu jest
  wejściem i każde jest trzymane równie długo, więc trzymanie trzy lata w ciągu dziesięciu to
  osiemdziesiąt cztery wejścia na wiersz, nie jedno. Współdzielą miesiące i to jest sedno:
  przerzedzenie ich do trzech niezależnych zostawiłoby wskaźnik z trzema obserwacjami w środku.
- **Wejście liczy się od miesiąca, w którym się kończy.** To, co kupione w ostatnich trzech latach
  okresu, jeszcze się nie zakończyło, a policzenie niezakończonego wejścia jako straty wygięłoby
  każdy wiersz w dół na końcu wyłącznie z powodu kalendarza. Tablica zaczyna się więc w pierwszym
  miesiącu, w którym wejście mogło się zakończyć.
- **Wiersz dołącza, gdy zakończy się sześć wejść.** Jedno wejście to 0% albo 100%, i każda z tych
  dwóch liczb na końcu rankingu jest końcem, na który nie zapracowała.
- **Z korektą, miesięcznie i od pierwszego własnego miesiąca każdego instrumentu**, z powodów,
  które podaje wyścig klas aktywów: dystrybucje funduszu nigdy nie pojawiają się w jego cenie, a
  fundusz uruchomiony w 2019 nie ma wejść z 2016, które mógłby wygrać albo przegrać.
- **Okres utrzymania to jedyny nowy wybór na tej tablicy.** Jeden rok i pięć lat w tych samych
  dziesięciu latach to dwa różne pytania z dwiema różnymi odpowiedziami, a osiem wierszy
  porządkuje się między nimi na nowo.
- **Wiersze wciąż biegną.** Są uporządkowane według wskaźnika — najczęściej na plusie na górze — i
  zamieniają się miejscami wraz z upływem miesięcy.

Zmierzone w ostatnich dziesięciu latach przy trzymaniu trzy lata: fundusz Nasdaq był na plusie przy
wszystkich osiemdziesięciu czterech wejściach, a fundusz z Hongkongu przy czterdziestu procentach z
nich — dwa wiersze, które wyścig klas aktywów rozdziela dziesięcioma latami całkowitego zwrotu, a
ta tablica rozdziela tym, czy w ogóle udało się wejść.

Nie zależy od ustawienia rynku: wszystkie osiem jest notowanych na giełdzie kontynentalnej. Mniej
niż dwanaście miesięcy w okresie jest odrzucane.
""",

    "cs": """Řádek je **podíl uzavřených vstupů, které vydělaly** — ze všech měsíců, v nichž se dalo vstoupit a
držet stejně dlouho, ta část, která skončila v plusu. Týchž osm nástrojů jako v závodu tříd aktiv a
na tabuli poklesů, hodnocených podle toho, jestli jejich držení fungovalo, ne podle toho, kolik
vynesly.

- **Jeden vstup je náhoda; osmdesát čtyři je míra.** Každý měsíc období je vstup a každý je držen
  stejně dlouho, takže tříleté držení v průběhu deseti let je osmdesát čtyři vstupů na řádek, ne
  jeden. Sdílejí měsíce a v tom je pointa: zredukovat je na tři nezávislé by ponechalo míru se
  třemi pozorováními uvnitř.
- **Vstup se počítá od měsíce, v němž končí.** To, co je koupeno v posledních třech letech období,
  ještě neskončilo, a započítat neskončený vstup jako ztrátu by na konci ohne každý řádek dolů
  jenom kvůli kalendáři. Tabule proto začíná prvním měsícem, v němž vstup mohl skončit.
- **Řádek nastupuje, jakmile skončí šest vstupů.** Jeden vstup je 0 % nebo 100 %, a kterákoli z těch
  dvou cifer na konci pořadí je konec, který si nezasloužil.
- **S úpravou, měsíčně a od prvního vlastního měsíce každého nástroje**, z důvodů, které uvádí
  závod tříd aktiv: distribuce fondu se v jeho ceně nikdy neobjeví a fond založený v roce 2019 nemá
  žádné vstupy z roku 2016, které by mohl vyhrát nebo prohrát.
- **Doba držení je jediná nová volba na této tabuli.** Jeden rok a pět let ve stejných deseti letech
  jsou dvě různé otázky se dvěma různými odpověďmi a osm řádků se mezi nimi přerovná.
- **Řádky stále běží.** Řadí se podle své míry — nejčastěji v plusu nahoře — a vyměňují si místa,
  jak měsíce plynou.

Měřeno za posledních deset let s tříletým držením: fond Nasdaq byl v plusu při všech osmdesáti
čtyřech vstupech a fond z Hongkongu při čtyřiceti procentech z nich — dva řádky, které závod tříd
aktiv odděluje deseti lety celkového výnosu a tato tabule odděluje tím, jestli se vůbec povedlo
vstoupit.

Neřídí se nastavením trhu: všech osm je kótováno na kontinentální burze. Méně než dvanáct měsíců
v období je odmítnuto.
""",

    "ru": """Строка — это **доля завершённых входов, которые оказались в плюсе**: из всех месяцев, в которые
можно было войти и держать одинаково долго, та часть, что закончилась с прибылью. Те же восемь
инструментов, что в гонке классов активов и на доске просадок, но оценённые по тому, сработало ли
их удержание, а не по тому, сколько они принесли.

- **Один вход — это везение; восемьдесят четыре — это доля.** Каждый месяц диапазона — это вход, и
  все они держатся одинаково долго, поэтому трёхлетнее удержание на протяжении десяти лет — это
  восемьдесят четыре входа на строку, а не один. Они делят месяцы, и в этом суть: проредить их до
  трёх независимых значило бы оставить долю с тремя наблюдениями внутри.
- **Вход считается с месяца, в котором он завершился.** Купленное в последние три года диапазона
  ещё не завершилось, и незавершённый вход, посчитанный как убыток, загнул бы каждую строку вниз на
  конце только из-за календаря. Поэтому доска начинается с первого месяца, в котором вход вообще мог
  завершиться.
- **Строка появляется, когда завершились шесть входов.** Один вход — это 0% или 100%, и любая из
  этих двух цифр на краю рейтинга — это край, который она не заслужила.
- **С поправкой, ежемесячно и от собственного первого месяца каждого инструмента**, по причинам,
  которые приводит гонка классов активов: выплаты фонда никогда не появляются в его цене, и фонд,
  запущенный в 2019 году, не имеет входов 2016 года, которые мог бы выиграть или проиграть.
- **Срок удержания — единственный новый выбор на этой доске.** Один год и пять лет на тех же десяти
  годах — это два разных вопроса с двумя разными ответами, и восемь строк перестраиваются между
  ними.
- **Строки по-прежнему бегут.** Они упорядочены по своей доле — чаще всего в плюсе сверху — и
  меняются местами по мере того, как идут месяцы.

Измерено за последние десять лет при удержании три года: фонд Nasdaq был в плюсе на всех
восьмидесяти четырёх входах, а фонд Гонконга — на сорока процентах из них. Это две строки, которые
гонка классов активов разделяет десятью годами суммарной доходности, а эта доска разделяет тем,
сработал ли вообще сам вход.

Не зависит от настройки рынка: все восемь котируются на континентальной бирже. Меньше двенадцати
месяцев в диапазоне отклоняется.
""",

    "tr": """Bir satır, **kazançla biten tamamlanmış girişlerin payı** — aynı süre boyunca girilip tutulabilecek
tüm ayların içinde, artıda bitenlerin oranı. Varlık sınıfları yarışı ve düşüş tablosundaki aynı
sekiz varlık; puan, ne kadar kazandırdığına değil, elde tutmanın işe yarayıp yaramadığına göre
veriliyor.

- **Bir giriş şanstır; seksen dördü bir orandır.** Aralıktaki her ay bir giriştir ve hepsi aynı süre
  tutulur, dolayısıyla on yıl içindeki üç yıllık tutuş satır başına seksen dört giriştir, bir değil.
  Ayları paylaşırlar ve mesele tam olarak budur: onları üç bağımsız girişe indirmek, içinde üç
  gözlem olan bir oran bırakırdı.
- **Bir giriş, bittiği aydan itibaren sayılır.** Aralığın son üç yılında alınan henüz bitmemiştir;
  bitmemiş bir girişi zarar saymak, her satırı sonunda sırf takvim yüzünden aşağı büker. Bu yüzden
  tablo, bir girişin bitebileceği ilk ayda açılır.
- **Altı giriş tamamlandığında satır katılır.** Bir giriş ya %0 ya %100'dür ve bu iki sayıdan hangisi
  sıralamanın bir ucunda durursa dursun, o uç hak edilmiş bir uç değildir.
- **Düzeltilmiş, aylık ve her varlığın kendi ilk ayından**, varlık sınıflarının verdiği gerekçelerle:
  bir fonun dağıtımları fiyatında hiç görünmez ve 2019'da kurulan bir fonun kazanıp kaybedebileceği
  2016 girişi yoktur.
- **Tutma süresi bu tablonun tek yeni seçimi.** Aynı on yıl için bir yıl ile beş yıl farklı sorulardır
  ve farklı cevapları vardır; sekiz satır ikisi arasında yeniden sıralanır.
- **Satırlar hâlâ yarışıyor.** Oranlarına göre dizilirler — en sık artıda biten üstte — ve aylar
  geçtikçe yer değiştirirler.

Son on yılda üç yıllık tutuşla ölçüldüğünde: Nasdaq fonu seksen dört girişinin tamamında öndeydi,
Hong Kong fonu ise bunların yüzde kırkında — varlık sınıfları yarışının on yıllık toplam getiriyle
ayırdığı iki satırı bu tablo, "içeri girmek işe yaradı mı" ile ayırıyor.

Piyasa ayarına bağlı değil: sekizi de anakara borsasında kote. Aralıkta on iki aydan az varsa
reddedilir.
""",
}


def main():
    for tag, title in TITLES.items():
        path = HELP / f"help-{tag}.md"

        text = path.read_bytes().decode("utf-8-sig").lstrip("\ufeff")
        lines = text.replace("\r\n", "\n").split("\n")

        want = f"## {title}"

        # Idempotent: drop the chapter wherever it already sits, then put it back in place.
        if want in lines:
            at = lines.index(want)

            heads = [i for i, line in enumerate(lines) if line.startswith("## ")]
            after = [i for i in heads if i > at]
            end = after[0] if after else len(lines)

            while end > at and lines[end - 1].strip() == "":
                end -= 1

            del lines[at:end]

        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if len(heads) < AFTER + 2:
            raise AssertionError(f"{tag}: only {len(heads)} chapters")

        at = heads[AFTER + 1]

        block = [want, ""] + BODIES[tag].rstrip("\n").split("\n") + [""]

        lines[at:at] = block

        out = "\n".join(lines)

        if not out.endswith("\n"):
            out += "\n"

        path.write_bytes(b"\xef\xbb\xbf" + out.encode("utf-8"))

        chapters = sum(1 for line in out.split("\n") if line.startswith("## "))

        print(f"{tag}: inserted after chapter {AFTER + 1}, now {chapters} chapters")


if __name__ == "__main__":
    main()
