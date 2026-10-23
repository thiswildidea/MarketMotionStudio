# -*- coding: utf-8 -*-
r"""把四个加密页的章节插进 14 份 help-*.md。

1.0.18 上架时，加密货币第四市场里这四页没有进手册：**比较、涨跌、占比、年度回报**
（导航键 NavCryptoCompare / NavCryptoMovers / NavCryptoDominance / NavCryptoAnnual）。
1.0.18 当时只给市值历程、市值榜、月度收益补了章节，ChangeLog 与商店文案也只提了那三页。
本版把四章补齐，插在「月度收益」之后、与导航顺序一致。

**位置按导航序号找，不按标题找**（listingtext.chapter_of）——但有一点要先想清楚：
chapter_of 假设「导航里它前面的每一章都已存在」。这四章恰好是导航末尾的连续四页，
前面的章全在，所以**升序插入**是对的：先插比较（28），此时它的序号后面正好是「视频」
那章；每插一章，视频往后挪一位，下一章的序号仍然指到视频头顶。若先插年度回报（31），
它会落在「动画背景」中间——序号对了，位置全错。

**幂等**：先按「本章标题行」摘掉旧块再插（与 port-crypto-matrix-help.py 同一招）。
删掉之后再升序插回，对任何「部分存在」的状态都成立。

素材来源：各语言 resw 的页面副标题与注记（本来就是 14 语言写好的），再加数据层
（CryptoCompare.cs / CryptoMovers.cs / CryptoDominance.cs / CryptoAnnualMatrixPage.xaml.cs）
里的关键行为：起点是第一个共同交易日、涨跌是收盘对前日收盘的替代值、占比只对所选集合
加总为 100、共同交易日少于 30 直说、年度回报不含进行中的年份。

**本章暂不带配图行**：五张加密页截图（含月度收益那张欠的）由 `store-screenshots.py
--crypto` 拍好后经 `help-media.py` 裁进 media/，`port-help-images.py` 会把图行挂上——
现在写一个指向不存在文件的图行只会让 verify-docs 红。

文件是 **UTF-8 无 BOM + LF**；行尾照抄原文。

用法：python tools\port-crypto-four-help.py     （跑第二遍应当是「改了 0 处」）
"""
import pathlib
import sys

TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import listingtext  # noqa: E402

HELP = listingtext.HELP

# 插入顺序 = 导航顺序（升序）。理由见文件头的长注。
ORDER = ["NavCryptoCompare", "NavCryptoMovers", "NavCryptoDominance", "NavCryptoAnnual"]

SECTIONS = {
"zh-Hans": {
"NavCryptoCompare": """## 加密货币比较

把几个币放进同一场赛跑：每个币的价格都在第一个共同交易日重设为 100，此后比的是谁涨得快，而不是谁更贵。

- **起点是「所有选中币都有价格的第一天」。** 整场赛跑从那一天出发——晚上市的币会把起点往后拉，因为它没资格从别的币的历史里出发。想要更长的赛道，就别勾刚出生的币。
- **画的是累计涨跌幅，不是价格。** 比特币的六万美元旁边放不下一枚不到一美分的币的价格——前者是一条线，后者是贴底的直线。折成同一比例，六位数的币和一分钱的币才读得动同一张图。
- 最多六个币：第七个不接受，因为第七条曲线会用到第六条已经用掉的颜色。
- **区间**是十二个月、二十四个月、六十个月，或自定义——自定义可以一路选到源端的第一天，比特币的日线从 2014 年 9 月开始。
- 收尾状态行会说出取了几个币、多少天，以及最后领先的是谁。
""",
"NavCryptoMovers": """## 加密货币涨跌

逐日追踪最大的 24 小时涨跌，红涨绿跌，按涨跌幅度排序——一张榜上最大的两种动静都要，而不是一根有向的梯子。

- **每一天的涨跌是收盘对前一日收盘。** 即时 24 小时榜是这类页面天生的本源，但它常年在同一堵墙后面；替代它的是逐日收盘——在一个不睡觉的市场上，昨收到今收本就是对 24 小时变化的公道代理。页面在注记里说清这一点：它是替代值，不是即时的跳动。
- 榜上是谁由你挑：最多六个币，排序只在你选的那组里进行。
- 第一天没有前一日收盘，读出来是零——这一天空着，而不是画一排零。
- **区间**是十二个月、二十四个月、六十个月，或自定义。
""",
"NavCryptoDominance": """## 加密货币占比

逐日显示每个选中币在「所选集合总市值」里的占比——画面上这几个币的占比加总为 100。

- **占比是相对「你挑的那组」，不是相对整个市场。** 来源只给每个币各自的流通市值，不给一个市场总额，所以长条在所选币之间加总为 100。它回答的是「这组里谁大、谁在挪」，不是「比特币占整个市场多少」。
- 分母是活的：去掉一个币，剩下几个按新的总额重新分。
- 流通市值取自 CoinMetrics 的估算口径，所有币站在同一层地板上——占比的跨币与跨日比较因此是诚实的。
- 选中币的共同交易日少于三十天时，页面直说没有可讲的故事，而不是铺一张薄得站不住的表。
- **区间**是十二个月、二十四个月、六十个月，或自定义。
""",
"NavCryptoAnnual": """## 加密货币年度回报

行是币、列是历年，每格是该币那一年的回报，红涨绿跌；最右一栏把显示的每一年复利合并成一个数字。

- **正在走的这一年不进格子。** 半年冒充整年，是对涨跌幅度的一种谎报——所以本年度要等它的最后一个交易日收盘后才出现。
- **一年的回报只问两个数**：那年年终的收盘对上一年年终的收盘。年内怎么颠簸，格子里看不出来——那是逐月那张图的事。
- 区间给不足完整的年度时，页面说「完整年度不足」，而不是用半截的格子凑数。备源只持有约一年日线，切到它时就是这种情形。
- **区间**是十二个月、二十四个月、六十个月，或自定义——默认五年，给得足四个完整年度。
""",
},
"zh-Hant": {
"NavCryptoCompare": """## 加密貨幣比較

把幾個幣放進同一場賽跑：每個幣的價格都在第一個共同交易日重設為 100，此後比的是誰漲得快，而不是誰更貴。

- **起點是「所有選中幣都有價格的第一天」。** 整場賽跑從那一天出發——晚上市的幣會把起點往後拉，因為它沒資格從別的幣的歷史裡出發。想要更長的賽道，就別勾剛出生的幣。
- **畫的是累計漲跌幅，不是價格。** 比特幣的六萬美元旁邊放不下一枚不到一美分的幣的價格——前者是一條線，後者是貼底的直線。折成同一比例，六位數的幣和一分錢的幣才讀得動同一張圖。
- 最多六個幣：第七個不接受，因為第七條曲線會用到第六條已經用掉的顏色。
- **區間**是十二個月、二十四個月、六十個月，或自訂——自訂可以一路選到源端的第一天，比特幣的日線從 2014 年 9 月開始。
- 收尾狀態列會說出取了幾個幣、多少天，以及最後領先的是誰。
""",
"NavCryptoMovers": """## 加密貨幣漲跌

逐日追蹤最大的 24 小時漲跌，紅漲綠跌，按漲跌幅度排序——一張榜上最大的兩種動靜都要，而不是一根有向的梯子。

- **每一天的漲跌是收盤對前一日收盤。** 即時 24 小時榜是這類頁面天生的本源，但它常年在同一堵牆後面；替代它的是逐日收盤——在一個不睡覺的市場上，昨收到今收本就是對 24 小時變化的公道代理。頁面在注記裡說清這一點：它是替代值，不是即時的跳動。
- 榜上是誰由你挑：最多六個幣，排序只在你選的那組裡進行。
- 第一天沒有前一日收盤，讀出來是零——這一天空著，而不是畫一排零。
- **區間**是十二個月、二十四個月、六十個月，或自訂。
""",
"NavCryptoDominance": """## 加密貨幣佔比

逐日顯示每個選中幣在「所選集合總市值」裡的佔比——畫面上這幾個幣的佔比加總為 100。

- **佔比是相對「你挑的那組」，不是相對整個市場。** 來源只給每個幣各自的流通市值，不給一個市場總額，所以長條在所選幣之間加總為 100。它回答的是「這組裡誰大、誰在挪」，不是「比特幣佔整個市場多少」。
- 分母是活的：去掉一個幣，剩下幾個按新的總額重新分。
- 流通市值取自 CoinMetrics 的估算口徑，所有幣站在同一層地板上——佔比的跨幣與跨日比較因此是誠實的。
- 選中幣的共同交易日少於三十天時，頁面直說沒有可講的故事，而不是鋪一張薄得站不住的表。
- **區間**是十二個月、二十四個月、六十個月，或自訂。
""",
"NavCryptoAnnual": """## 加密貨幣年度報酬

行是幣、列是曆年，每格是該幣那一年的報酬，紅漲綠跌；最右一欄把顯示的每一年複利合併成一個數字。

- **正在走的這一年不進格子。** 半年冒充整年，是對漲跌幅度的一種謊報——所以本年度要等它的最後一個交易日收盤後才出現。
- **一年的報酬只問兩個數**：那年年底的收盤對上一年年底的收盤。年內怎麼顛簸，格子裡看不出來——那是逐月那張圖的事。
- 區間給不足完整的年度時，頁面說「完整年度不足」，而不是用半截的格子湊數。備源只持有約一年日線，切到它時就是這種情形。
- **區間**是十二個月、二十四個月、六十個月，或自訂——預設五年，給得足四個完整年度。
""",
},
"en-US": {
"NavCryptoCompare": """## Crypto Compare

Several coins in one race: each coin's price is rebased to 100 on the first day they all have prices, and what races after that is who rises fastest, not who is pricier.

- **The start is the first day every chosen coin has a price.** The whole race sets off from that day — a coin that listed later pulls the start toward itself, because it cannot set out from another coin's history. For a longer track, leave the newborn coins out.
- **What is drawn is cumulative return, not price.** Next to Bitcoin's sixty thousand dollars, the price of a sub-cent coin is a line glued to the floor. Rebased to one scale, a six-figure coin and a one-figure coin can share one picture.
- Six coins at most: a seventh is refused, because the seventh curve would use up the colour the sixth already took.
- **The range** is twelve, twenty-four or sixty months, or custom — and custom reaches back to the source's first day: Bitcoin's daily line begins in September 2014.
- The closing status line says how many coins and days were fetched, and who leads at the end.
""",
"NavCryptoMovers": """## Crypto Movers

The biggest 24-hour moves, day by day — red for rises, green for falls, ranked by size, because a movers board wants the biggest motion in either direction, not a signed ladder.

- **Each day's move is the close over the previous day's close.** A live 24-hour ranking is this page's natural source, but it lives behind the same wall the rest of that endpoint does; the stand-in is the day's close against the day before's — on a market that never sleeps, a fair proxy for the 24-hour change. The note on the page says so plainly: a proxy, not the live tick.
- Who is on the board is yours to pick: six coins at most, ranked within the set you chose.
- Day zero has no previous close and reads zero — the day is left out rather than drawn as a row of nothing.
- **The range** is twelve, twenty-four or sixty months, or custom.
""",
"NavCryptoDominance": """## Crypto Dominance

Each chosen coin's share of the chosen set's total market cap, day by day — the shares sum to one hundred across the coins on the frame.

- **The share is of the set you picked, not of the whole market.** The source serves each coin's circulating cap but no market total, so the bars sum to one hundred across the chosen coins. The question they answer is who is biggest in this set and who is moving — not how much of the entire market Bitcoin holds.
- The denominator is alive: drop a coin and the rest are redivided by the new total.
- Circulating caps come from CoinMetrics on the estimate metric, every coin standing on the same floor — which is what makes the shares honest across coins and over time.
- Fewer than thirty shared days and the page says there is no story to tell, instead of laying a table too thin to stand on.
- **The range** is twelve, twenty-four or sixty months, or custom.
""",
"NavCryptoAnnual": """## Crypto Annual Returns

Coins as rows, calendar years as columns, each cell a coin's return over that year, red for rises and green for falls; the last column compounds every year shown into one figure.

- **The year still being walked stays off the grid.** A half year read as a whole one is a lie about the size of the move, so the running year appears only after its last trading day has closed.
- **A year's return asks two numbers**: that year's final close against the year before's. How the price thrashed inside the year is not in the cell — that is the monthly grid's business.
- When the range cannot supply whole years, the page says so — not enough full years — rather than filling the frame with half columns. The fallback source holds about a single year of dailies, and on it that is exactly the case.
- **The range** is twelve, twenty-four or sixty months, or custom — five years by default, which settles four full columns.
""",
},
"ja": {
"NavCryptoCompare": """## 暗号資産の比較

いくつかのコインを同じレースに乗せる：各コインの価格は最初の共通取引日で 100 に引き直され、その後競うのは誰が速く伸びるかであって、誰が高いかではありません。

- **起点は「選んだコイン全てに価格がある最初の日」。** レース全体がその日から走り出します——後から上場されたコインは起点を手前に引きます。長いトラックが欲しければ、生まれたばかりのコインは外してください。
- **描くのは累積収益率であって価格ではありません。** ビットコインの 6 万ドルの隣に、1 セント未満のコインの価格は置けません——片方は線になり、もう片方は床に張り付く直線になるだけです。同じ尺度に引き直してこそ、6 桁のコインと 1 桁のコインが一枚の図を共有できます。
- 多くて 6 コイン：7 番目は受け付けません。7 本目の曲線は 6 本目がもう使った色を使うことになるからです。
- **期間**は 12・24・60 ヶ月、またはカスタム——カスタムはデータ源の最初の日まで選べます。ビットコインの日線は 2014 年 9 月からです。
- 終了時のステータス行が、取ったコインの数と日数、そして最後に先頭を走っていたのが誰かを伝えます。
""",
"NavCryptoMovers": """## 暗号資産の値動き

最大の 24 時間の値動きを日ごとに追うページ。赤は上昇、緑は下落で、動きの大きさ順に並べます。一枚の榜には上向き下向き両方の一番大きな動きが載るべきであって、符号付きの階段であるべきではありません。

- **各日の値動きは、終値の前日終値に対する比です。** リアルタイムの 24 時間ランキングこそこのページ本来の源ですが、それは常に同じ壁の内側にあります。代わりに立つのは日々の終値——眠らない市場では、前日終値から当日終値への差は 24 時間変化の正当な代理です。注記がはっきり言います：代理値であって、リアルタイムの刻みではない、と。
- 榜に誰を載せるかはあなたが選びます：多くて 6 コイン、順位は選んだ組の中だけで付きます。
- 初日は前日終値がなく 0 と読めます——その日は空欄にし、0 の列は描きません。
- **期間**は 12・24・60 ヶ月、またはカスタム。
""",
"NavCryptoDominance": """## 暗号資産の占有率

選んだ各コインが「選んだコインの合計時価総額」に占める割合を日ごとに示します。画面に載るコインの占有率の合計は 100 になります。

- **占有率は「あなたが選んだ組」に対するもので、市場全体に対するものではありません。** データ源は各コインの流通時価総額は教えても、市場全体の合計は教えません。だから長条は選んだコインの間で 100 に足し合わさります。答えるのは「この組の中で誰が大きく、誰が動いているか」であって「ビットコインが市場全体の何%か」ではありません。
- 分母は生きています：コインを一つ外せば、残りが新しい合計で配り直されます。
- 流通時価総額は CoinMetrics の推計口径で、全コインが同じ床に立っています——占有率の比較がコインをまたいでも日をまたいでも誠実なのはそのためです。
- 共通取引日が 30 日に満たないとき、ページは「語る物語がない」とそのまま言います。薄すぎて立たない表を敷いたりしません。
- **期間**は 12・24・60 ヶ月、またはカスタム。
""",
"NavCryptoAnnual": """## 暗号資産の年間収益

行はコイン、列は暦年、各マスはそのコインのその年の収益。赤は上昇、緑は下落。右端の列は表示された全年の複利を一つの数字にまとめます。

- **進行中の年は格子に載りません。** 半年を一年として読むのは動きの大きさについての嘘です——だから進行中の年は、その年の最終取引日が終わってから現れます。
- **一年の収益に要るのは二つの数字**：その年末の終値と、前の年末の終値。年内の細かな揺れはマスには現れません——それは月次の図の仕事です。
- 期間が完全な年を用意できないとき、ページは「完全な年が足りない」と言います。半端な列で間に合わせたりしません。予備の源は約一年分の日線しか持たず、切り替えたときがまさにその状態です。
- **期間**は 12・24・60 ヶ月、またはカスタム——既定は 5 年で、完全な 4 列分が用意できます。
""",
},
"ko": {
"NavCryptoCompare": """## 암호화폐 비교

여러 코인을 한 레이스에 태웁니다: 각 코인의 가격은 모두가 가격을 갖는 첫날 100으로 다시 놓이고, 그다음부터 다투는 것은 누가 더 빨리 오르는가이지 누가 더 비싼가가 아닙니다.

- **출발점은「선택한 코인 모두가 가격을 갖는 첫날」입니다.** 레이스 전체가 그날 출발합니다 — 늦게 상장된 코인은 출발점을 자신 쪽으로 끌어당깁니다. 더 긴 트랙을 원하면 갓 태어난 코인은 빼십시오.
- **그리는 것은 누적 수익률이지 가격이 아닙니다.** 비트코인의 6만 달러 옆에 1센트도 안 되는 코인의 가격은 놓일 수 없습니다 — 한쪽은 선이 되고 다른 쪽은 바닥에 붙은 직선이 될 뿐입니다. 같은 눈금으로 다시 놓아야 여섯 자릿수 코인과 한 자릿수 코인이 한 장의 그림을 나눠 읽힙니다.
- 많아야 여섯 코인: 일곱 번째는 받지 않습니다. 일곱 번째 곡선이 여섯 번째가 이미 쓴 색을 쓰게 되기 때문입니다.
- **기간**은 12·24·60개월 또는 사용자 지정 — 지정은 데이터 원본의 첫날까지 거슬러 갈 수 있습니다. 비트코인 일선은 2014년 9월부터입니다.
- 마지막 상태 줄이 몇 개의 코인과 몇 일을 가져왔는지, 그리고 마지막까지 선두였던 것이 누구인지 알려 줍니다.
""",
"NavCryptoMovers": """## 암호화폐 등락

가장 큰 24시간 등락을 날마다 추적합니다. 오르면 빨강, 내리면 초록, 크기 순으로 줄을 섭니다. 등락판에는 양방향 중 가장 큰 움직임 둘 다 실려야지 부호가 매겨진 사다리여서는 안 됩니다.

- **각 날의 등락은 종가의 전일 종가에 대한 비율입니다.** 실시간 24시간 랭킹이야말로 이 페이지의 본원이지만 그것은 늘 같은 벽 뒤에 있습니다. 대신 서는 것은 날마다의 종가 — 잠들지 않는 시장에서 어제 종가에서 오늘 종가로의 차이는 24시간 변화의 공정한 대리값입니다. 페이지의 주석이 분명히 말합니다: 대체값이지 실시간 숫자가 아니라고.
- 판에 누가 오르는지는 당신이 고릅니다: 많아야 여섯 코인, 순위는 고른 그룹 안에서만 매겨집니다.
- 첫날은 전일 종가가 없어 0으로 읽힙니다 — 그날은 비우지 0의 줄을 그리지 않습니다.
- **기간**은 12·24·60개월 또는 사용자 지정.
""",
"NavCryptoDominance": """## 암호화폐 점유율

선택한 각 코인이「선택한 코인들의 총 시가총액」에서 차지하는 비중을 날마다 보여 줍니다. 화면의 코인들 점유율 합은 100입니다.

- **점유율은「당신이 고른 그룹」에 대한 것이지 시장 전체에 대한 것이 아닙니다.** 원본은 코인별 유통 시가총액은 주지만 시장 전체의 합계는 주지 않습니다. 그래서 막대는 선택한 코인 사이에서 100으로 합해집니다. 답하는 질문은「이 그룹에서 누가 크고 누가 움직이는가」이지「비트코인이 시장 전체의 몇 퍼센트인가」가 아닙니다.
- 분모는 살아 있습니다: 코인을 하나 빼면 나머지가 새 총액으로 다시 나뉩니다.
- 유통 시가총액은 CoinMetrics의 추정치로, 모든 코인이 같은 바닥에 섭니다 — 점유율 비교가 코인을 넘어도 날을 넘어도 정직한 이유입니다.
- 공통 거래일이 30일에 못 미치면 페이지는「이야기할 이야기가 없다」고 그대로 말합니다. 얇아서 설 수 없는 표를 깔지 않습니다.
- **기간**은 12·24·60개월 또는 사용자 지정.
""",
"NavCryptoAnnual": """## 암호화폐 연간 수익

행은 코인, 열은 연도, 각 칸은 그 코인의 그해 수익입니다. 오르면 빨강, 내리면 초록. 맨 오른쪽 열은 보이는 모든 해를 하나의 숫자로 복리 합산합니다.

- **진행 중인 해는 격자에 들어오지 않습니다.** 반년을 일 년처럼 읽는 것은 등락의 크기에 대한 거짓말입니다 — 그래서 진행 중인 해는 그 해의 마지막 거래일이 닫힌 뒤에 나타납니다.
- **일 년의 수익에는 두 숫자만 필요합니다**: 그해 연말 종가와 전년 연말 종가. 연중의 요동은 칸에 보이지 않습니다 — 그것은 월별 그림의 일입니다.
- 기간이 온전한 해를 공급하지 못하면 페이지는「완전한 해가 부족하다」고 말합니다. 반쪽 열로 때우지 않습니다. 예비 원본은 약 1년치 일선만 갖고 있어, 그쪽으로 바꾸면 바로 이 상황입니다.
- **기간**은 12·24·60개월 또는 사용자 지정 — 기본은 5년으로, 완전한 네 열이 나옵니다.
""",
},
"de": {
"NavCryptoCompare": """## Krypto-Vergleich

Mehrere Coins in einem Rennen: Der Preis jedes Coins wird am ersten gemeinsamen Tag auf 100 neu gesetzt, und was danach wetteifert, ist, wer am schnellsten steigt — nicht, wer teurer ist.

- **Der Start ist der erste Tag, an dem jeder gewählte Coin einen Preis hat.** Das ganze Rennen bricht von diesem Tag auf — ein später notierter Coin zieht den Start zu sich, denn er kann nicht aus der Geschichte eines anderen aufbrechen. Wer eine längere Bahn will, lässt die neugeborenen Coins weg.
- **Gezeichnet wird die kumulierte Rendite, nicht der Preis.** Neben Bitcoins sechzigtausend Dollar hat der Preis eines Coins unter einem Cent keinen Platz — der eine wird zur Linie, der andere zur bodennahen Geraden. Erst auf eine Skala gebracht, lesen ein sechsstelliger und ein einstelliger Coin dasselbe Bild.
- Höchstens sechs Coins: Ein siebter wird abgelehnt, denn die siebte Kurve würde die Farbe gebrauchen, die die sechste schon verbraucht hat.
- **Der Zeitraum** ist zwölf, vierundzwanzig oder sechzig Monate, oder eigen — eigen reicht bis zum ersten Tag der Quelle zurück; Bitcoins Tageslinie beginnt im September 2014.
- Die Statuszeile am Ende sagt, wie viele Coins und Tage geholt wurden und wer zuletzt führte.
""",
"NavCryptoMovers": """## Krypto-Bewegungen

Die größten 24-Stunden-Bewegungen, Tag für Tag — rot für Steigungen, grün für Stürze, der Größe nach geordnet; ein Bewegungsblatt will die größte Bewegung in beide Richtungen, keine Leiter mit Vorzeichen.

- **Die Bewegung eines Tages ist der Schluss gegen den Schluss des Vortages.** Das Live-Ranking der 24 Stunden ist die natürliche Quelle dieser Seite, aber es wohnt hinter derselben Mauer wie der Rest jenes Endpunkts; der Ersatz ist der Tagesschluss gegen den des Vortages — auf einem Markt, der nie schläft, ein redlicher Stellvertreter für die 24-Stunden-Bewegung. Die Anmerkung auf der Seite sagt es klar: ein Stellvertreter, nicht der live Ticker.
- Wer auf dem Blatt steht, wählst du: höchstens sechs Coins, geordnet innerhalb der gewählten Gruppe.
- Tag null hat keinen Vortagsschluss und liest null — der Tag bleibt leer, statt als Reihe aus Nichts gezeichnet zu werden.
- **Der Zeitraum** ist zwölf, vierundzwanzig oder sechzig Monate, oder eigen.
""",
"NavCryptoDominance": """## Krypto-Dominanz

Der Anteil jedes gewählten Coins an der Gesamtkapitalisierung der gewählten Menge, Tag für Tag — die Anteile summieren sich über die Coins im Bild zu Hundert.

- **Der Anteil gilt für die gewählte Menge, nicht für den ganzen Markt.** Die Quelle nennt die Umlaufkapitalisierung jedes Coins, aber keine Marktsumme, darum summieren sich die Balken über die gewählten Coins zu Hundert. Die Frage, die sie beantworten: wer in dieser Menge am größten ist und wer sich bewegt — nicht, wie viel vom ganzen Markt Bitcoin hält.
- Der Nenner lebt: Nimmt man einen Coin heraus, werden die übrigen nach der neuen Summe neu geteilt.
- Die Umlaufkapitalisierungen stammen aus CoinMetrics' Schätzreihe, jeder Coin steht auf demselben Boden — darin sind die Anteile über Coins und über Tage ehrlich.
- Weniger als dreißig gemeinsame Tage, und die Seite sagt geradeheraus, dass es keine Geschichte zu erzählen gibt — statt einen Tisch zu legen, der zu dünn ist, um zu stehen.
- **Der Zeitraum** ist zwölf, vierundzwanzig oder sechzig Monate, oder eigen.
""",
"NavCryptoAnnual": """## Krypto-Jahresrenditen

Coins als Zeilen, Kalenderjahre als Spalten, jede Zelle die Rendite eines Coins in jenem Jahr, rot für Steigungen und grün für Stürze; die letzte Spalte zinst jedes gezeigte Jahr in eine Zahl zusammen.

- **Das noch laufende Jahr bleibt vom Raster fern.** Ein halbes Jahr als ganzes gelesen ist eine Lüge über die Größe der Bewegung — darum erscheint das laufende Jahr erst, nachdem sein letzter Handelstag geschlossen hat.
- **Die Rendite eines Jahres fragt zwei Zahlen**: den Schlussschluss des Jahres gegen den des Vorjahres. Wie der Preis im Innern des Jahres gerang, steht nicht in der Zelle — das ist des Monatsrasters Sache.
- Kann der Zeitraum keine ganzen Jahre liefern, sagt die Seite es — es fehlen ganze Jahre — statt das Feld mit halben Spalten zurechtzuzimmern. Die Ausweichquelle trägt etwa ein einziges Jahr Tageswerte; auf ihr ist es genau dieser Fall.
- **Der Zeitraum** ist zwölf, vierundzwanzig oder sechzig Monate, oder eigen — fünf Jahre als Vorgabe, das tragen vier volle Spalten.
""",
},
"fr": {
"NavCryptoCompare": """## Comparaison crypto

Plusieurs monnaies dans une même course : le prix de chacune est réindexé à 100 le premier jour où toutes ont un prix, et ce qui court ensuite, c'est qui monte le plus vite — non pas qui est le plus cher.

- **Le départ est le premier jour où chaque monnaie choisie a un prix.** Toute la course part de ce jour-là — une monnaie cotée tardivement ramène le départ vers elle, car elle ne peut pas s'élancer depuis l'histoire d'une autre. Pour une piste plus longue, laissez de côté les monnaies nouveau-nées.
- **Ce qui est dessiné est le rendement cumulé, non le prix.** À côté des soixante mille dollars du bitcoin, le prix d'une monnaie à moins d'un cent n'a pas de place — l'un devient une ligne, l'autre une droite collée au plancher. Ramenés à une même échelle, une monnaie à six chiffres et une à un chiffre peuvent se partager une même image.
- Six monnaies au plus : une septième est refusée, car la septième courbe utiliserait la couleur que la sixième a déjà prise.
- **La période** est de douze, vingt-quatre ou soixante mois, ou personnalisée — et la personnalisée remonte jusqu'au premier jour de la source : la ligne journalière du bitcoin commence en septembre 2014.
- La ligne d'état finale dit combien de monnaies et de jours ont été pris, et qui menait à la fin.
""",
"NavCryptoMovers": """## Mouvements crypto

Les plus grands mouvements de 24 heures, jour après jour — rouge pour les hausses, vert pour les baisses, ordonnés par ampleur ; un tableau de mouvements veut la plus grande secousse dans les deux sens, pas une échelle signée.

- **Le mouvement d'un jour est la clôture contre celle de la veille.** Le classement 24 h en direct est la source naturelle de cette page, mais il demeure derrière le même mur que le reste de ce point d'accès ; le remplaçant est la clôture du jour contre celle de la veille — sur un marché qui ne dort jamais, un honnête substitut à la variation de 24 heures. La note sur la page le dit clairement : un substitut, pas le tick en direct.
- Qui figure au tableau, c'est vous qui le choisissez : six monnaies au plus, ordonnées dans l'ensemble choisi.
- Le jour zéro n'a pas de clôture de veille et lit zéro — ce jour reste vide plutôt que dessiné en une rangée de rien.
- **La période** est de douze, vingt-quatre ou soixante mois, ou personnalisée.
""",
"NavCryptoDominance": """## Dominance crypto

La part de chaque monnaie choisie dans la capitalisation totale de l'ensemble choisi, jour après jour — les parts se somment à cent sur les monnaies de l'image.

- **La part vaut pour l'ensemble que vous avez choisi, pas pour tout le marché.** La source donne la capitalisation circulante de chaque monnaie, mais aucun total du marché ; les barres se somment donc à cent sur les monnaies choisies. La question à laquelle elles répondent : qui est le plus grand dans cet ensemble et qui bouge — non pas combien du marché entier le bitcoin détient.
- Le dénominateur est vivant : retirez une monnaie, et les autres sont repartagées selon le nouveau total.
- Les capitalisations circulantes viennent de la série estimée de CoinMetrics, chaque monnaie debout sur le même plancher — c'est de là que les parts sont honnêtes d'une monnaie à l'autre et d'un jour à l'autre.
- Moins de trente jours communs, et la page dit sans détour qu'il n'y a pas d'histoire à raconter — au lieu de dresser une table trop mince pour tenir debout.
- **La période** est de douze, vingt-quatre ou soixante mois, ou personnalisée.
""",
"NavCryptoAnnual": """## Rendements annuels crypto

Les monnaies en lignes, les années civiles en colonnes, chaque cellule le rendement d'une monnaie sur cette année, rouge pour les hausses et vert pour les baisses ; la dernière colonne compose chaque année montrée en un seul chiffre.

- **L'année encore en marche reste hors de la grille.** Une demi-année lue comme entière est un mensonge sur l'ampleur du mouvement — l'année courante n'apparaît donc qu'après la clôture de son dernier jour de bourse.
- **Le rendement d'une année ne demande que deux nombres** : la clôture finale de cette année contre celle de la précédente. Comment le prix a tressailli dans l'année n'est pas dans la cellule — c'est l'affaire de la grille mensuelle.
- Quand la période ne peut fournir des années entières, la page le dit — il manque des années complètes — au lieu de rapiécer le cadre avec des colonnes à moitié. La source de secours ne porte qu'environ une année de cours journaliers ; sur elle, c'est exactement ce cas.
- **La période** est de douze, vingt-quatre ou soixante mois, ou personnalisée — cinq ans par défaut, ce qui pose quatre colonnes entières.
""",
},
"es": {
"NavCryptoCompare": """## Comparar cripto

Varias monedas en una misma carrera: el precio de cada una se reajusta a 100 el primer día en que todas tienen precio, y lo que compite después es quién sube más rápido, no quién es más caro.

- **La salida es el primer día en que cada moneda elegida tiene precio.** Toda la carrera parte de ese día — una moneda cotizada más tarde acerca la salida hacia sí, porque no puede arrancar desde la historia de otra. Para una pista más larga, deja fuera las monedas recién nacidas.
- **Lo que se dibuja es la rentabilidad acumulada, no el precio.** Junto a los sesenta mil dólares del bitcoin, el precio de una moneda de menos de un céntimo no tiene sitio — uno se vuelve línea y el otro una recta pegada al suelo. Llevados a una misma escala, una moneda de seis cifras y otra de una cifra pueden compartir una misma imagen.
- Seis monedas como máximo: una séptima se rechaza, porque la séptima curva usaría el color que la sexta ya tomó.
- **El intervalo** es de doce, veinticuatro o sesenta meses, o personalizado — y el personalizado llega hasta el primer día de la fuente: la línea diaria del bitcoin empieza en septiembre de 2014.
- La línea de estado final dice cuántas monedas y días se obtuvieron y quién iba en cabeza al final.
""",
"NavCryptoMovers": """## Movimientos cripto

Los mayores movimientos de 24 horas, día a día — rojo para las subidas, verde para las caídas, ordenados por tamaño; un tablón de movimientos quiere la mayor sacudida en ambos sentidos, no una escalera con signo.

- **El movimiento de cada día es el cierre contra el cierre de la víspera.** La clasificación de 24 horas en vivo es la fuente natural de esta página, pero vive tras la misma muralla que el resto de ese punto de acceso; el sustituto es el cierre del día contra el de la víspera — en un mercado que nunca duerme, un sustituto honrado de la variación de 24 horas. La nota de la página lo dice claro: un sustituto, no la cotización en vivo.
- Quién está en el tablón lo eliges tú: seis monedas como máximo, ordenadas dentro del conjunto elegido.
- El día cero no tiene cierre previo y lee cero — ese día queda vacío, en vez de dibujarse como una fila de nada.
- **El intervalo** es de doce, veinticuatro o sesenta meses, o personalizado.
""",
"NavCryptoDominance": """## Dominancia cripto

La cuota de cada moneda elegida en la capitalización total del conjunto elegido, día a día — las cuotas suman cien entre las monedas del cuadro.

- **La cuota vale para el conjunto que elegiste, no para todo el mercado.** La fuente da la capitalización circulante de cada moneda, pero ningún total del mercado; así que las barras suman cien entre las monedas elegidas. La pregunta que responden: quién es el más grande en este conjunto y quién se mueve — no cuánto del mercado entero guarda el bitcoin.
- El denominador está vivo: quita una moneda y las demás se reparten de nuevo según el nuevo total.
- Las capitalizaciones circulantes vienen de la serie estimada de CoinMetrics, cada moneda de pie sobre el mismo suelo — de ahí que las cuotas sean honradas de una moneda a otra y de un día a otro.
- Con menos de treinta días comunes, la página dice sin rodeos que no hay historia que contar, en vez de tender una mesa demasiado delgada para sostenerse.
- **El intervalo** es de doce, veinticuatro o sesenta meses, o personalizado.
""",
"NavCryptoAnnual": """## Rendimientos anuales cripto

Monedas en filas, años naturales en columnas, cada celda la rentabilidad de una moneda en ese año, rojo para las subidas y verde para las caídas; la última columna compone cada año mostrado en una sola cifra.

- **El año aún en marcha queda fuera de la cuadrícula.** Medio año leído como entero es una mentira sobre el tamaño del movimiento — el año en curso aparece solo tras el cierre de su último día de bolsa.
- **La rentabilidad de un año pide dos números**: el cierre final de ese año contra el del anterior. Cómo tembló el precio dentro del año no está en la celda — ese es el asunto de la cuadrícula mensual.
- Cuando el intervalo no puede dar años completos, la página lo dice — faltan años completos — en vez de remendar el marco con columnas a medias. La fuente de reserva solo lleva cerca de un año de precios diarios; en ella es exactamente este caso.
- **El intervalo** es de doce, veinticuatro o sesenta meses, o personalizado — cinco años por defecto, que asientan cuatro columnas completas.
""",
},
"it": {
"NavCryptoCompare": """## Confronto crypto

Diverse monete in una stessa gara: il prezzo di ciascuna viene riportato a 100 il primo giorno in cui tutte hanno un prezzo, e ciò che gareggia dopo è chi sale più in fretta, non chi costa di più.

- **La partenza è il primo giorno in cui ogni moneta scelta ha un prezzo.** Tutta la gara parte da quel giorno — una moneta quotata tardi tira la partenza verso di sé, perché non può sganciarsi dalla storia di un'altra. Per una pista più lunga, lascia fuori le monete appena nate.
- **Ciò che è disegnato è il rendimento cumulato, non il prezzo.** Accanto ai sessantamila dollari del bitcoin, il prezzo di una moneta da meno di un centesimo non trova posto — l'uno diventa una linea, l'altro una retta incollata al pavimento. Riportati a una stessa scala, una moneta a sei cifre e una a una cifra possono condividere la stessa immagine.
- Al massimo sei monete: una settima è rifiutata, perché la settima curva userebbe il colore che la sesta ha già preso.
- **L'intervallo** è di dodici, ventiquattro o sessanta mesi, o personalizzato — e il personalizzato risale fino al primo giorno della fonte: la linea giornaliera del bitcoin comincia nel settembre 2014.
- La riga di stato finale dice quante monete e quanti giorni sono stati presi, e chi guidava alla fine.
""",
"NavCryptoMovers": """## Movimenti crypto

I maggiori movimenti di 24 ore, giorno per giorno — rosso per i rialzi, verde per i ribassi, ordinati per entità; un tabellone dei movimenti vuole la scossa più grande in entrambe le direzioni, non una scala con segno.

- **Il movimento di un giorno è la chiusura contro quella del giorno prima.** La classifica live di 24 ore è la fonte naturale di questa pagina, ma abita dietro lo stesso muro del resto di quell'endpoint; la supplente è la chiusura del giorno contro quella del precedente — su un mercato che non dorme mai, un surrogato onesto della variazione di 24 ore. La nota sulla pagina lo dice chiaro: un surrogato, non il tick in diretta.
- Chi sta sul tabellone lo scegli tu: al massimo sei monete, ordinate nell'insieme scelto.
- Il giorno zero non ha chiusura precedente e legge zero — quel giorno resta vuoto, anziché disegnato come una fila di nulla.
- **L'intervallo** è di dodici, ventiquattro o sessanta mesi, o personalizzato.
""",
"NavCryptoDominance": """## Dominanza crypto

La quota di ogni moneta scelta sulla capitalizzazione totale dell'insieme scelto, giorno per giorno — le quote sommano a cento tra le monete dell'inquadratura.

- **La quota vale per l'insieme che hai scelto, non per tutto il mercato.** La fonte dà la capitalizzazione circolante di ogni moneta, ma nessun totale del mercato; le barre quindi sommano a cento tra le monete scelte. La domanda a cui rispondono: chi è il più grande in questo insieme e chi si muove — non quanto di tutto il mercato tiene il bitcoin.
- Il denominatore è vivo: togli una moneta e le altre si ridividono secondo il nuovo totale.
- Le capitalizzazioni circolanti vengono dalla serie stimata di CoinMetrics, ogni moneta in piedi sullo stesso pavimento — da lì che le quote sono oneste da una moneta all'altra e da un giorno all'altro.
- Meno di trenta giorni in comune e la pagina dice senza giri di parole che non c'è una storia da raccontare, invece di stendere una tavola troppo sottile per stare in piedi.
- **L'intervallo** è di dodici, ventiquattro o sessanta mesi, o personalizzato.
""",
"NavCryptoAnnual": """## Rendimenti annuali crypto

Monete in righe, anni civili in colonne, ogni cella il rendimento di una moneta in quell'anno, rosso per i rialzi e verde per i ribassi; l'ultima colonna compone ogni anno mostrato in una sola cifra.

- **L'anno ancora in cammino resta fuori dalla griglia.** Mezzo anno letto come intero è una menzogna sull'ampiezza del movimento — l'anno in corso appare solo dopo la chiusura del suo ultimo giorno di borsa.
- **Il rendimento di un anno chiede due numeri**: la chiusura finale di quell'anno contro quella dell'anno prima. Come il prezzo ha vacillato dentro l'anno non è nella cella — è affare della griglia mensile.
- Quando l'intervallo non può fornire anni interi, la pagina lo dice — mancano anni completi — invece di rattoppare il telaio con colonne a metà. La fonte di riserva porta circa un solo anno di prezzi giornalieri; su di essa è esattamente questo caso.
- **L'intervallo** è di dodici, ventiquattro o sessanta mesi, o personalizzato — cinque anni per impostazione predefinita, che assestano quattro colonne intere.
""",
},
"pt-BR": {
"NavCryptoCompare": """## Comparar cripto

Várias moedas numa mesma corrida: o preço de cada uma é redefinido para 100 no primeiro dia em que todas têm preço, e o que compete depois é quem sobe mais rápido, não quem é mais caro.

- **A largada é o primeiro dia em que cada moeda escolhida tem preço.** A corrida inteira parte desse dia — uma moeda listada tarde puxa a largada para si, porque não pode arrancar da história de outra. Para uma pista mais longa, deixe fora as moedas recém-nascidas.
- **O que se desenha é o retorno acumulado, não o preço.** Ao lado dos sessenta mil dólares do bitcoin, o preço de uma moeda de menos de um centavo não cabe — um vira linha e o outro vira reta colada no chão. Trazidos a uma mesma escala, uma moeda de seis dígitos e uma de um dígito conseguem dividir a mesma imagem.
- Seis moedas no máximo: uma sétima é recusada, porque a sétima curva usaria a cor que a sexta já levou.
- **O intervalo** é de doze, vinte e quatro ou sessenta meses, ou personalizado — e o personalizado alcança o primeiro dia da fonte: a linha diária do bitcoin começa em setembro de 2014.
- A linha de status final diz quantas moedas e dias foram obtidos e quem liderava no fim.
""",
"NavCryptoMovers": """## Movimentos cripto

Os maiores movimentos de 24 horas, dia após dia — vermelho para altas, verde para quedas, ordenados pelo tamanho; um quadro de movimentos quer o maior movimento nos dois sentidos, não uma escada com sinal.

- **O movimento de cada dia é o fechamento contra o da véspera.** A classificação de 24 horas ao vivo é a fonte natural desta página, mas mora atrás da mesma muralha do resto desse ponto de acesso; o substituto é o fechamento do dia contra o da véspera — num mercado que nunca dorme, um substituto honesto da variação de 24 horas. A nota na página diz com clareza: um substituto, não o tick ao vivo.
- Quem está no quadro você escolhe: seis moedas no máximo, ordenadas dentro do conjunto escolhido.
- O dia zero não tem fechamento anterior e lê zero — esse dia fica de fora, em vez de ser desenhado como uma fila de nada.
- **O intervalo** é de doze, vinte e quatro ou sessenta meses, ou personalizado.
""",
"NavCryptoDominance": """## Dominância cripto

A fatia de cada moeda escolhida na capitalização total do conjunto escolhido, dia após dia — as fatias somam cem entre as moedas do quadro.

- **A fatia vale para o conjunto que você escolheu, não para o mercado inteiro.** A fonte dá a capitalização circulante de cada moeda, mas nenhum total do mercado; as barras somam cem entre as moedas escolhidas. A pergunta que respondem: quem é o maior nesse conjunto e quem está se movendo — não quanto do mercado inteiro o bitcoin guarda.
- O denominador está vivo: tire uma moeda e as demais se dividem de novo pelo novo total.
- As capitalizações circulantes vêm da série estimada da CoinMetrics, cada moeda de pé sobre o mesmo chão — daí as fatias serem honestas de uma moeda à outra e de um dia a outro.
- Menos de trinta dias em comum, e a página diz sem rodeios que não há história para contar, em vez de estender uma mesa fina demais para se sustentar.
- **O intervalo** é de doze, vinte e quatro ou sessenta meses, ou personalizado.
""",
"NavCryptoAnnual": """## Retornos anuais cripto

Moedas em linhas, anos civis em colunas, cada célula o retorno de uma moeda naquele ano, vermelho para altas e verde para quedas; a última coluna compõe cada ano mostrado em um só número.

- **O ano ainda em andamento fica fora da grade.** Meio ano lido como inteiro é uma mentira sobre o tamanho do movimento — o ano corrente só aparece depois do fechamento do seu último dia de pregão.
- **O retorno de um ano pede dois números**: o fechamento final daquele ano contra o do anterior. Como o preço se agitou dentro do ano não está na célula — isso é assunto da grade mensal.
- Quando o intervalo não consegue fornecer anos completos, a página diz — faltam anos completos — em vez de remendar o quadro com colunas pela metade. A fonte reserva carrega cerca de um único ano de preços diários; nela, é exatamente esse o caso.
- **O intervalo** é de doze, vinte e quatro ou sessenta meses, ou personalizado — cinco anos por padrão, que assentam quatro colunas completas.
""",
},
"pl": {
"NavCryptoCompare": """## Porównanie krypto

Kilka monet w jednym wyścigu: cena każdej z nich jest przeliczana na 100 w pierwszym wspólnym dniu, a ściga się potem to, kto rośnie najszybciej — nie to, kto jest droższy.

- **Startem jest pierwszy dzień, w którym każda wybrana moneta ma cenę.** Cały wyścig rusza z tego dnia — moneta notowana późno przesuwa start ku sobie, bo nie może wyruszyć z cudzej historii. Chcesz dłuższej bieżni — zostaw świeżo narodzone monety w spokoju.
- **Rysowaną jest skumulowana stopa zwrotu, nie cena.** Obok sześćdziesięciu tysięcy dolarów bitcoina cena monety poniżej centa nie znajdzie miejsca — jedna stanie się linią, druga prostą przyklejoną do podłogi. Dopiero na wspólnej skali moneta sześciocyfrowa i jedno cyfrowa czytają jeden obraz.
- Najwyżej sześć monet: siódma jest odmawiana, bo siódma krzywa użyłaby koloru, który szósta już wzięła.
- **Zakres** to dwanaście, dwadzieścia cztery lub sześćdziesiąt miesięcy albo własny — własny sięga pierwszego dnia źródła: dzienna linia bitcoina zaczyna się we wrześniu 2014.
- Linia stanu na końcu mówi, ile monet i dni przyniesiono i kto prowadził na mecie.
""",
"NavCryptoMovers": """## Ruchy krypto

Największe ruchy 24-godzinne, dzień po dniu — czerwone dla wzrostów, zielone dla spadków, ułożone według rozmiaru; tablica ruchów chce największego poruszenia w obie strony, nie drabiny ze znakiem.

- **Ruch dnia to zamknięcie w stosunku do zamknięcia dnia poprzedniego.** Żywa tablica 24 godzin jest naturalnym źródłem tej strony, lecz mieszka za tą samą murem co reszta tego złącza; zastępcą jest dzienne zamknięcie wobec wczorajszego — na rynku, który nigdy nie śpi, uczciwa namiastka zmiany 24-godzinnej. Nota na stronie mówi to wprost: namiastka, nie tick na żywo.
- Kto siedzi na tablicy, wybierasz ty: najwyżej sześć monet, ułożonych w obrębie wybranego zestawu.
- Dzień zerowy nie ma wczorajszego zamknięcia i czyta zero — ten dzień zostaje pusty, zamiast zostać narysowanym jako rząd niczego.
- **Zakres** to dwanaście, dwadzieścia cztery lub sześćdziesiąt miesięcy albo własny.
""",
"NavCryptoDominance": """## Dominacja krypto

Udział każdej wybranej monety w łącznej kapitalizacji wybranego zestawu, dzień po dniu — udziały sumują się do stu w obrębie monet z obrazu.

- **Udział dotyczy zestawu, który wybrałeś, nie całego rynku.** Źródło podaje kapitalizację w obiegu każdej monety, lecz żadnej sumy rynku; słupki sumują się więc do stu w obrębie wybranych monet. Pytanie, na które odpowiadają: kto jest największy w tym zestawie i kto się rusza — nie to, ile całego rynku trzyma bitcoin.
- Mianownik żyje: weź monetę, a reszta rozdzieli się na nowo według nowej sumy.
- Kapitalizacje w obiegu pochodzą z serii szacunkowej CoinMetrics, każda moneta stoi na tej samej podłodze — stąd udziały są uczciwe od monety do monety i od dnia do dnia.
- Mniej niż trzydzieści wspólnych dni i strona mówi prosto: nie ma historii do opowiedzenia — zamiast rozkładać stół zbyt cienki, żeby stał.
- **Zakres** to dwanaście, dwadzieścia cztery lub sześćdziesiąt miesięcy albo własny.
""",
"NavCryptoAnnual": """## Roczne stopy krypto

Monety w wierszach, lata kalendarzowe w kolumnach, każda komórka to roczna stopa zwrotu monety w danym roku, czerwone dla wzrostów i zielone dla spadków; ostatnia kolumna składa każdy pokazany rok w jedną liczbę.

- **Wciąż trwający rok zostaje poza siatką.** Pół roku czytane jako całe to kłamstwo o rozmiarze ruchu — bieżący rok pojawia się więc dopiero po zamknięciu jego ostatniego dnia notowań.
- **Roczna stopa pyta o dwie liczby**: końcowe zamknięcie tego roku wobec zamknięcia poprzedniego. Jak cena trzepotała w środku roku — tego w komórce nie widać; to sprawa miesięcznej siatki.
- Gdy zakres nie dostarcza pełnych lat, strona mówi to wprost — brakuje pełnych lat — zamiast łatać ramę półkolumnami. Zapasowe źródło niesie ledwie około roku dziennych cen; na nim to właśnie ten przypadek.
- **Zakres** to dwanaście, dwadzieścia cztery lub sześćdziesiąt miesięcy albo własny — domyślnie pięć lat, co daje cztery pełne kolumny.
""",
},
"cs": {
"NavCryptoCompare": """## Srovnání krypto

Několik mincí v jednom závodu: cena každé z nich je první společný den přepočtena na 100 a závodí potom to, kdo roste nejrychleji — ne to, kdo je dražší.

- **Startem je první den, v němž každá vybraná mince má cenu.** Celý závod vybíhá z toho dne — později uvedená mince přitáhne start k sobě, neboť nemůže vyběhnout z cizí historie. Kdo chce delší dráhu, nechá novorozené mince stranou.
- **Kreslí se kumulovaný výnos, nikoli cena.** Vedle šedesáti tisíc dolarů bitcoinu nemá cena mince pod jedním centem místo — jedna se stane linií, druhá přímkou přilepenou k podlaze. Na společné škále čtou šestimístná a jednomístná mince týž obraz.
- Nejvýše šest mincí: sedmá je odmítnuta, neboť sedmá křivka by použila barvu, kterou šestá už vzala.
- **Rozsah** je dvanáct, dvacet čtyři či šedesát měsíců, nebo vlastní — vlastní sahá až k prvnímu dni zdroje: denní linie bitcoinu začíná v září 2014.
- Závěrečný stavový řádek řekne, kolik mincí a dní bylo přineseno a kdo vedl na konci.
""",
"NavCryptoMovers": """## Krypto pohyby

Největší 24hodinové pohyby, den za dnem — červené pro růsty, zelené pro pády, seřazené podle velikosti; tabule pohybů chce největší pohyb na obě strany, ne žebřík se znaménkem.

- **Pohyb dne je uzavření proti uzavření předešlého dne.** Živá 24hodinová tabule je přirozený zdroj této stránky, ale bydlí za touže zdí jako zbytek tohoto rozhraní; náhradou je denní uzavření proti včerejšímu — na trhu, který nikdy nespí, čestný zástupný obraz 24hodinové změny. Poznámka na stránce to říká nahlas: zástupný obraz, ne živý tik.
- Kdo sedí na tabuli, volíte vy: nejvýše šest mincí, seřazených uvnitř vybrané skupiny.
- Den nula nemá včerejší uzavření a čte nulu — ten den zůstává prázdný, místo aby byl kreslen jako řada z ničeho.
- **Rozsah** je dvanáct, dvacet čtyři či šedesát měsíců, nebo vlastní.
""",
"NavCryptoDominance": """## Krypto dominance

Podíl každé vybrané mince na celkové kapitalizaci vybrané skupiny, den za dnem — podíly se sčítají do sta napříč mincemi v obraze.

- **Podíl se týká skupiny, kterou jste vybrali, nikoli celého trhu.** Zdroj dává oběžnou kapitalizaci každé mince, ale žádný součet trhu; sloupce se tedy sčítají do sta napříč vybranými mincemi. Otázka, na niž odpovídají: kdo je v této skupině největší a kdo se hýbe — ne to, kolik celého trhu bitcoin drží.
- Jmenovatel žije: vezměte minci a zbylé se rozdělí znovu podle nového součtu.
- Oběžné kapitalizace pocházejí z odhadované řady CoinMetrics, každá mince stojí na téže podlaze — odtud jsou podíly čestné od mince k minci a od dne k dni.
- Méně než třicet společných dní a stránka říká nahlas, že není co vyprávět — místo aby rozprostřela stůl příliš tenký, aby stál.
- **Rozsah** je dvanáct, dvacet čtyři či šedesát měsíců, nebo vlastní.
""",
"NavCryptoAnnual": """## Roční výnosy krypto

Mince v řádcích, kalendářní roky ve sloupcích, každá buňka ročním výnosem mince v tom roce, červené pro růsty a zelené pro pády; poslední sloupec skládá každý zobrazený rok do jediného čísla.

- **Běžící rok zůstává mimo mřížku.** Půl roku čtené jako celé je lež o velikosti pohybu — běžný rok se proto ukáže až po uzavření svého posledního obchodního dne.
- **Roční výnos si žádá dvě čísla**: konečné uzavření toho roku proti uzavření předešlého. Jak se cena třepotala uvnitř roku, v buňce není — to je věc měsíční mřížky.
- Když rozsah nedodá celé roky, stránka to řekne — chybějí celé roky — místo aby záplatu dělala půlsloupci. Záložní zdroj nese sotva jeden rok denních cen; na něm je právě tento případ.
- **Rozsah** je dvanáct, dvacet čtyři či šedesát měsíců, nebo vlastní — ve výchozím stavu pět let, což nese čtyři plné sloupce.
""",
},
"ru": {
"NavCryptoCompare": """## Сравнение крипто

Несколько монет в одном заезде: цена каждой переустанавливается на 100 в первый общий день, и состязаются после этого не «кто дороже», а «кто растёт быстрее».

- **Старт — первый день, когда у каждой выбранной монеты есть цена.** Весь заезд отправляется из этого дня — монета, вышедшая позже, подтягивает старт к себе: она не может стартовать из чужой истории. Хотите более длинную дорожку — не берите новорождённые монеты.
- **Рисуется накопленная доходность, а не цена.** Рядом с шестьюдесятью тысячами долларов биткоина цена монеты дешевле цента не поместится — одна станет линией, другая — прямой, прилипшей к полу. На общей шкале шестизначная и однозначная монета читают одну картину.
- Не больше шести монет: седьмая отклоняется, ибо седьмая кривая взяла бы цвет, уже потраченный шестой.
- **Диапазон** — двенадцать, двадцать четыре или шестьдесят месяцев, либо свой — свой доходит до первого дня источника: дневная линия биткоина начинается в сентябре 2014 года.
- Заключительная строка состояния скажет, сколько монет и дней получено и кто вёл на финише.
""",
"NavCryptoMovers": """## Движения крипто

Крупнейшие 24-часовые движения, день за днём — красное для роста, зелёное для падения, по убыванию размера: доске движений нужен самый большой толчок в обе стороны, а не лестница со знаком.

- **Движение дня — закрытие против закрытия предыдущего дня.** Живой 24-часовой рейтинг — естественный источник этой страницы, но он живёт за той же стеной, что и весь этот узел; замена — дневное закрытие против вчерашнего: на рынке, который никогда не спит, это честный заместитель 24-часового изменения. Примечание на странице говорит это прямо: заместитель, а не живая котировка.
- Кто на доске — выбираете вы: не больше шести монет, ряды строятся внутри выбранного набора.
- У дня нуля нет вчерашнего закрытия, и он читает ноль — этот день остаётся пустым, а не рисуется рядом из ничего.
- **Диапазон** — двенадцать, двадцать четыре или шестьдесят месяцев, либо свой.
""",
"NavCryptoDominance": """## Доминирование крипто

Доля каждой выбранной монеты в суммарной капитализации выбранного набора, день за днём — доли сходятся в сто по монетам на экране.

- **Доля — относительно выбранного набора, а не всего рынка.** Источник даёт обращающуюся капитализацию каждой монеты, но никакой суммы рынка; потому столбцы сходятся в сто по выбранным монетам. На вопрос, который они отвечают: кто в этом наборе больше и кто движется — а не сколько всего рынка держит биткоин.
- Знаменатель живой: уберите монету — остальные разделятся заново по новой сумме.
- Обращающиеся капитализации идут из расчётного ряда CoinMetrics, каждая монета стоит на одном полу — потому доли честны от монеты к монете и от дня ко дню.
- Меньше тридцати общих дней — и страница скажет прямо: истории не будет, вместо того чтобы стелить стол слишком тонкий, чтобы устоять.
- **Диапазон** — двенадцать, двадцать четыре или шестьдесят месяцев, либо свой.
""",
"NavCryptoAnnual": """## Годовые доходности крипто

Монеты строками, календарные годы столбцами, каждая ячейка — годовая доходность монеты за тот год, красное для роста и зелёное для падения; последний столбец сращивает каждый показанный год в одно число.

- **Идущий год за решётку не входит.** Полгода, прочитанное как целое, — ложь о размере движения, поэтому текущий год появляется лишь после закрытия его последнего торгового дня.
- **Годовой доходности нужны два числа**: заключительное закрытие того года против закрытия предыдущего. Как цена трепетала внутри года, в ячейке не видно — это дело месячной решётки.
- Когда диапазон не даёт целых лет, страница говорит об этом — не хватает полных лет — вместо того чтобы латать раму полустолбцами. Запасной источник несёт около одного года дневных цен; на нём это ровно тот случай.
- **Диапазон** — двенадцать, двадцать четыре или шестьдесят месяцев, либо свой — по умолчанию пять лет, на что встают четыре полных столбца.
""",
},
"tr": {
"NavCryptoCompare": """## Kripto Karşılaştırma

Birkaç coin tek bir yarışta: her coinin fiyatı, hepsinin fiyatının olduğu ilk günde 100'a çekilir ve ondan sonra yarışan, kim daha hızlı yükseliyor — kim daha pahalı değil.

- **Başlangıç, seçilen her coinin fiyatının olduğu ilk gündür.** Yarışın tamamı o günden çıkar — geç kote olan bir coin başlangıcı kendine çeker; çünkü başka bir coinin tarihinden çıkamaz. Daha uzun pist istiyorsanız, yeni doğmuş coinleri dışarıda bırakın.
- **Çizilen şey birikimli getiridir, fiyat değil.** Bitcoinin altmış bin dolarının yanında bir sentin altındaki bir coinin fiyatına yer yoktur — biri çizgiye döner, öteki yere yapışık bir doğruya. Ortak bir ölçeğe çekildiklerinde altı haneli bir coin ile tek haneli bir coin aynı resmi paylaşabilir.
- En çok altı coin: yedincisi kabul edilmez, çünkü yedinci eğri, altıncının çoktan aldığı rengi kullanacaktır.
- **Aralık** on iki, yirmi dört ya da altmış ay, ya da özel — özel, kaynağın ilk gününe kadar gider: bitcoinin günlük çizgisi Eylül 2014'te başlar.
- Kapanıştaki durum satırı kaç coin ve gün alındığını ve sonunda kimin önde olduğunu söyler.
""",
"NavCryptoMovers": """## Kripto Hareketler

En büyük 24 saatlik hareketler, gün gün — yükselişler için kırmızı, düşüşler için yeşil, büyüklüğe göre sıralı; hareketler panosunda iki yönde de en büyük kıpırtı olsun, işaretli bir merdiven değil.

- **Bir günün hareketi, kapanışın bir önceki günün kapanışına oranıdır.** Canlı 24 saatlik sıralama bu sayfanın doğal kaynağıdır ama o, bu ucun gerisinin durduğu duvarın ardında yaşar; yerine geçen, günün kapanışının önceki günün kapanışına oranıdır — hiç uyumayan bir piyasada 24 saatlik değişimin dürüst bir vekilidir. Sayfadaki not bunu açıkça söyler: vekil, canlı fiyat değil.
- Panoda kimin duracağını siz seçersiniz: en çok altı coin, seçtiğiniz küme içinde sıralanır.
- Sıfırıncı günün önceki kapanışı yoktur ve sıfır okur — o gün boş bırakılır, hiçlikten bir sıra olarak çizilmez.
- **Aralık** on iki, yirmi dört ya da altmış ay, ya da özel.
""",
"NavCryptoDominance": """## Kripto Hakimiyeti

Seçilen her coinin seçilen kümenin toplam değerine payı, gün gün — paylar, görüntüdeki coinler arasında yüze toplanır.

- **Pay, seçtiğiniz küme içindir, bütün piyasa için değil.** Kaynak her coinin dolaşımdaki değerini verir ama piyasanın toplamını vermez; çubuklar bu yüzden seçilen coinler arasında yüze toplanır. Yanıtladıkları soru şudur: bu kümede kim en büyük ve kim kıpırdıyor — bitcoinin bütün piyasanın ne kadarını tuttuğu değil.
- Payda yaşıyor: bir coini çıkarın, kalanlar yeni toplama göre yeniden bölünür.
- Dolaşımdaki değerler CoinMetrics'in tahmin serisinden gelir, her coin aynı zeminde durur — payların coinden coine ve günden güne dürüst olması buradan gelir.
- Ortak gün otuzdan az olursa sayfa lafı dolandırmadan der ki: anlatılacak bir hikâye yok — ayakta duramayacak kadar ince bir sofra sermek yerine.
- **Aralık** on iki, yirmi dört ya da altmış ay, ya da özel.
""",
"NavCryptoAnnual": """## Kripto Yıllık Getiriler

Satırlar coinler, sütunlar takvim yılları, her hücre bir coinin o yıldaki getirisi — yükselişler için kırmızı, düşüşler için yeşil; son sütun gösterilen her yılı tek bir sayıda birleştirir.

- **Hâlâ yürüyen yıl ızgaraya girmez.** Yarım yılı bütün okumak hareketin büyüklüğü hakkında yalan söylemektir — içinde bulunulan yıl, son işlem günü kapandıktan sonra görünür.
- **Bir yılın getirisi iki sayı sorar**: o yılın son kapanışı ile bir önceki yılın son kapanışı. Fiyatın yıl içinde nasıl savrulduğu hücrede görünmez — o, aylık ızgaranın işidir.
- Aralık bütün yılları sağlayamadığında sayfa bunu söyler — tam yıllar eksik — çerçeveyi yarım sütunlarla yamamak yerine. Yedek kaynak ancak yaklaşık bir yıl günlük fiyat taşır; onda durum tam olarak budur.
- **Aralık** on iki, yirmi dört ya da altmış ay, ya da özel — öntanımlı beş yıl, dört tam sütunun üstüne oturur.
""",
},
}


def chapter_heading(section):
    return section.split("\n", 1)[0].strip()


def process(text, lang, joiner):
    lines = text.split(joiner)
    sections = SECTIONS[lang]
    removed = 0

    # 先摘掉旧块：按各章标题行精确匹配。
    wanted_heads = {chapter_heading(sections[key]) for key in ORDER}
    heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

    drop = set()
    for n, start in enumerate(heads):
        if lines[start].strip() in wanted_heads:
            end = heads[n + 1] if n + 1 < len(heads) else len(lines)
            drop.update(range(start, end))

    if drop:
        removed = 1
        lines = [line for i, line in enumerate(lines) if i not in drop]

    # 再升序插回：每插一章，后面那章的序号仍然指到「视频」头顶。
    for key in ORDER:
        index = listingtext.chapter_of(key)
        heads = [i for i, line in enumerate(lines) if line.startswith("## ")]

        if index >= len(heads):
            raise SystemExit(f"  ! {lang}: 第 {index} 章不存在（共 {len(heads)} 章）")

        block = sections[key].strip("\n").split("\n")
        lines[index:][0]  # 触碰一下，确认行号有效
        lines[heads[index]:heads[index]] = block + [""]

    return joiner.join(lines), removed


def main():
    changed = 0

    for lang in listingtext.LANGS:
        path = HELP / f"help-{lang}.md"
        raw = path.read_bytes()
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig").lstrip("\ufeff")
        joiner = "\r\n" if "\r\n" in text else "\n"

        updated, removed = process(text, lang, joiner)

        if updated != text:
            path.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + updated.encode("utf-8"))
            mark = "+"
            changed += 1
        else:
            mark = "="

        heads = updated.count(joiner + "## ") + updated.startswith("## ")
        print(f"  {mark} {lang}: {heads} 章{'（摘除旧块后重插）' if removed else ''}")

    print(f"changed {changed} documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
