# 版本记录 / Changelog

Each version sent to the Store gets one entry here: its number, its date, and what is new in it.
**Releasing is three actions that belong together** — bump `Version` in
`src/MarketMotionStudio/Package.appxmanifest`, add an entry below, and update the
"What's new in this version" line in the store listing. Skipping the middle one is how a
version ends up with no record of what it changed.

每个上架版本在这里留一条：版本号、日期、本版新增。**发版是三个绑定的动作**——改
`Package.appxmanifest` 的 `Version`、在这里加一条、同步商店文案的「此版本的新增功能」。
少做第二步，这个版本就再也说不清自己改了什么。

Two rules decide the number itself (full text in NOTES.md under "Version numbering"): the
fourth section stays 0, and the first cannot be 0. An update must also be higher than the
version already published, or nobody is offered it.
版本号怎么定（详见 NOTES.md 的 "Version numbering"）：第四段恒为 0，第一段不能为 0；
且必须高于已发布版本，否则用户根本收不到更新。

Entries run newest first. / 新版本在上。

---

## 1.0.12.0 — 2026-10-09（更新版 / update）

**本版做了两件各自独立的事：让 K 线页一次比较多只标的，以及把五页底部的数字卡片从手机那条按钮
栏底下挪开。另外修掉一个只有比较画面才会碰上的缺陷——那上面的「导出 MP4」按下去没有反应。**

**一、K 线页可以一次放上多只标的。** 此前在清单上多选几只，画面什么也不做——那个选取器根本没接
上。现在选两只以上就不再画蜡烛：不同标的的价格没有共同的纵轴，所以每只都从自己的起点算累计涨
跌幅，名字与整段的涨跌标在线的末端。轴取的是各标的交易日的**并集**而不是交集，否则一只十年的
与一只三年的并排，前者会被悄悄截成三年；某一天缺数据就向前携带上一个值，因为停牌不是跌到零。
分钟档把所有标的放在同一个交易日上，取它们都有数据的、最近一个完整的交易日。最多六只，那是这
一页调色板上分得开的颜色数。

**二、多只时可以选择怎么排布。** 新加的排布下拉给两种：都画在一张图上，或者每只一张图、上下排
列。分图时每只有自己的纵轴——一只三年里只在两个点以内晃动的标的，画在跑了三十个点的邻居旁边
就是一条直线。**x 轴不复制**：整帧一个时间窗口、一个标签列，所以同一个日期在整幅画面上是同一
个 x，日期行只画一次，画在最下面那格底下。上限三只是**格子的高度**决定的，不是调色板：三格时
每格约占帧高的九分之一，第四格连轴都放不下。第四只起**从轴上也掉下去**，不只是不画——轴是各标
的交易日的并集，画面不管的标的不能拉伸别人被读的日期；被略过的那些会在状态行里点名，而不是悄
悄不画。

**三、两种排布最后都收在同一排卡片上。** 曲线动着的时候名字骑在末端，那是观众正在看的地方；但
一个还在动的数字是抄不下来的。收尾那一段把它们全放进画面下方的一排卡片里，按画的顺序、用各自
的颜色：谁领先、领先多少，可以和刚才标签上那个数对一下。每张卡写名称、涨幅百分比与涨跌额。这
一排就是持仓页一直在用的那一排，现在由一处 `TrackCards` 画，四个渲染器只填空。

**四、涨跌从前一个交易日的收盘价算起。** 用户报「上证指数今天跌了 0.79，图上对不上」：比较画面
把每只从**第一根 K 线的开盘价**量起，而一天的涨跌是相对昨收的。2026-10-08 的 5 分钟线上，上证
指数从开盘量是 −0.7054%，从昨收量是 −0.7884%；科创 50 是 −3.7328% 与 −4.8163%。基准现在只在一
处（`CandleSeries.Baseline`），比较与区间卡片都读它，所以分钟档下的区间卡片也是当日涨跌幅。同
一个屏幕上还报「交易日为空」：那一行被清空后从没填上——比较只能画在每只都交易过的那一天，所以
候选是它们共同的交易日，是交集不是并集。

**五、五页底部的数字卡片不再画到画面最右边。** 帧宽 1080、右边距 150 时那一排的右缘落在 930，
而平台那条竖栏是帧宽的 18%，即 885.6 —— **右缘落在栏内 44 px**，最后一格卡片自己的数字正压在头
像与评论按钮底下。它一直没被发现，是因为卡片的边框是中性灰而不是赛道色：那一排看着像家具，不
像内容。算术收进 `FrameContext.CardRowRight` 一处，五处拷贝都改为调它。与 1.0.11.0 那三页的末端
标注不同，这里不需要开关：卡片只是把剩下的宽度平分，四张卡每张窄掉约 11 px，没有一条线因此
移动。

**This version does two unrelated things: the candle page can hold several instruments at once, and
the row of figures at the foot of five pages no longer sits under the phone's button rail. It also
fixes a fault only a comparison could meet — Export MP4 doing nothing at all when pressed.**

**One — the candle page takes more than one instrument.** Picking several used to do nothing at all:
the picker was not wired up. Two or more no longer draw candles, because prices from different
instruments share no axis; the board is normalised to cumulative change from each instrument's own
starting bar, with its name and its move over the whole span labelled at the line's end. The axis is
the **union** of the trading days, not the intersection — a ten-year instrument next to a three-year
one would otherwise be quietly cut to three — and a missing day carries the last value forward,
because a suspension is not a fall to zero. Minute periods put every instrument on one trading day,
the most recent whole one they all have. Six at most, which is how many distinct hues the board has.

**Two — how they are laid out.** A new layout switch offers two: every instrument on one chart, or one
panel each, stacked. Stacked, each instrument gets its own axis, which is what makes the quiet ones
readable: one that spent three years inside a two-point band, drawn against a neighbour that ran
thirty, is a straight line. **The x axis is not duplicated** — one time window and one label column
for the whole frame, so a date is at one x across the picture, and the date row is drawn once, under
the bottom panel. The limit of three is the panels' **height**, not the palette: three panels leave
each about a ninth of the frame, and a fourth has no room for an axis. The fourth pick is dropped
**from the axis as well as from the picture** — the axis is the union of the days, so an instrument
the frame does not draw cannot stretch the dates a reader reads off everyone else — and it is named in
the status line rather than silently left out.

**Three — both layouts end on the same row of cards.** While the curves move, the names ride their
leading ends, which is where a reader is looking; but a figure that is still moving is a figure that
has to be chased. The closing stretch puts them all in one row under the plot, in the order they are
drawn and in their own colours: who is ahead, by how much, checked against the number the label was
showing a moment ago. Each card carries the name, the percentage and the amount. It is the row the
holdings board has always ended on, now drawn by one `TrackCards` that the four renderers fill in.

**Four — change is measured from the previous close.** Two reports, one screen: the day's move did not
match the number on the chart, and the trading-day box was empty. The comparison measured every
instrument from the first bar's *open*; a day is measured from the *previous close*. On 2026-10-08's
five-minute candles, sh000001 was −0.7054% from its open against −0.7884% from yesterday's close, and
科创50 −3.7328% against −4.8163%. The baseline now lives in one place, `CandleSeries.Baseline`, and
both the comparison and the range card read it, so on a minute period the range card is the day's move
too. The empty box was the page clearing it and never filling it: a comparison can only be drawn on a
day every instrument traded, so the candidates are the days they have in common — an intersection, not
a union.

**Five — the row of cards at the foot of five pages no longer reaches the frame's edge.** With a
1080-wide frame and a right margin of 150, the row ended at 930; the platform's rail is 18% of the
frame, which is 885.6 — so **the row sat 44 px inside the band**, and the last card's own figures
landed under the avatar and the comment button. It went unnoticed because a card's border is a neutral
grey rather than a track colour: the row reads as furniture, not as content. The arithmetic now lives
in one place, `FrameContext.CardRowRight`, and all five copies call it. Unlike the end labels of three
pages in 1.0.11.0, this needs no switch: the cards share what is left, so four cards each lose about
eleven pixels and no line moves.

### 新增 / Added

- **K 线页可以一次比较多只标的 / the candle page compares several instruments** —— 清单那一排变成可
  开关的，两只以上改画累计涨跌幅；轴取交易日并集，缺日向前携带，分钟档取共同的完整交易日，最多
  六只。
- **排布可选「每只一张图」 / a stacked layout, one panel per instrument** —— 上下排列，各有各的纵
  轴，最多三只；x 轴与日期行整帧一份，只画一次；第四只起从轴上也掉，并在状态行里点名。
- **两种排布最后都收在同一排卡片上 / both layouts end on one row of cards** —— 名称、涨幅百分比、
  涨跌额三行，按画的顺序、用各自的颜色；与持仓页那一排是同一处 `TrackCards`。
- **K 线页也有那个越线开关 / the candle page has the band switch too** —— 打开时曲线末端的标注与蜡
  烛的绘图区都收在安全线以内；关掉时用它自己的右边缘，已经把右边距调到比栏还宽的人拿到的仍是原
  先那张图。页面上同时去掉了第二个检索框：选取器自带一个，与页面原来那个一模一样，屏幕上两个相
  同的框没人知道哪个在听。

### 修正 / Fixed

- **比较画面的「导出 MP4」不再毫无反应 / Export MP4 on a comparison answers again** —— 用户报「导出
  MP4 没响应」。按钮是亮的（它的可用性问的是「序列**或**板子有没有」），画面好好地画着，按下去却
  既不弹框、也不写状态行、也不报错、也不写文件，日志里干干净净：两个导出处理器的守卫只问了**序列**
  （`_fetched`），而比较画面**故意把序列清空**、留着板子，于是每一次按下都从第一行静默返回。这一页
  是唯一一个「两个数据源画两张画」的页面，另外十六页各只有一处来源、各问一处——照抄它们的写法正是
  这个缺陷的来源。现在守卫与文件名都问同一处 `FrameSpan`（板子优先，其次序列），与按钮的可用性读
  的是同一件事，所以两者再也不可能各说一套。封面导出同病、同样修掉。
- **五页底部的数字卡片不再压在平台那条按钮栏下 / the cards at the foot of five pages clear the
  platform's rail** —— K线、成交额、日内、定投、持仓五页的四张统计卡此前按 `ChartWidth` 铺到画面
  右缘（1080 帧下 930），安全线在 885.6，右缘落在栏内 44 px；现在五处都改调
  `FrameContext.CardRowRight()`，算术只在一处。
- **分钟档的表头读当日涨跌幅 / the minute headline reads the day's move** —— 表头取的是屏幕前一根，
  5 分钟档下就是五分钟前。2026-10-08 的上证指数画面上写 +0.07%，当日实际 −0.79%。分钟行不带涨跌
  字段，前收要从会话里取：`MinuteSession.CloseBefore(day)` 按窗口里的位置找，不按日历回退一天，
  所以周五不会去要周四的收盘。
- **比较画面的零点取前一个交易日的收盘价 / a comparison is measured from the previous close** ——
  见上第四段；区间卡片与它读同一个基准。
- **交易日的下拉不再是空的 / the trading-day box is no longer empty** —— 候选是各标的共同的交易日，
  取回来就填上；换一天不重新取数。

包已构建：`artifacts/MarketMotionStudio_1.0.12.0_x64_arm64_bundle.msixupload`（149.8 MB / 142.9 MiB，
六个内包）。拆包核验 x64 与 arm64 两个内包的 Identity 都是 `1.0.12.0`，`Package/Properties/
DisplayName` 仍是字面值 `MarketMotionStudio`；包内 14 份手册、70 张配图、`resources.pri` 与 Win2D
的 `Microsoft.Graphics.Canvas.dll` 都在。

判据：K线 22 项、分钟线 71 项、成交额日内 48 项、持仓 151 项、定投 87 项全过。K线多标的这一份
本轮新增四条**源码**断言 —— 守卫只有一处 / 那一处同时读两条来源 / 视频与封面两个文件名都从它取
日期 / 按钮的可用性问的是同一件事 —— 四条已绿；另有一段**真机**断言（按下导出后日志里必须长出
`encode: enter`，`VideoExporter.EncodeAsync` 的第一句，再按取消收尾）**待补跑**：它要独占应用约
八分钟，而跑的时候读者的应用正在编码另一页的视频，不能掐掉。（这一条本来也是**日志先红出来的**：
`crash.log` 里根本没有 `encode: enter`，所以问题在闸口之前，而不在编码器里。）`verify-docs.py`
182 项 0 失败，`verify-resw-uids.py` 14 语言 870 键 0 问题，商店 CSV 43 项 0 失败。商店文案 14 语言
那一栏由 `tools/port-store-listing-10120.py` 改写，最长的法语 1295 字，都在商店 1500 字上限以内。

---

## 1.0.11.0 — 2026-10-08（更新版 / update）

**本版修的是一件「做得对、但只对了一半」的事：三个页面的数字被平台的按钮盖住了。**

竖屏视频在手机上播放时，画面右侧约六分之一常年被头像、点赞、评论那一条占着。这一点在应用里
完全看不出来 —— 应用里没有那套界面，而这三个页面就是在应用里画出来的。市值历程、定投计划、
持仓收益三页都把曲线末端的数值标注画到画面最右边，在手机上正好落在那条栏底下。

根因是一句**假注释**。三页各自抄了一份「标注要留多宽」的算术，三份都按**画面右缘**收边，注释里
写着的理由是「平台那条竖栏本来就在右边距里」。这句从来不是真的：`SafeArea.Right` 是 0.18，1080
宽的帧下是 194 px，**比默认右边距 150 还宽**。于是标注落在帧宽 98% 处，正压在头像和评论按钮下。
（同一个文件里上次已经因为一句假注释丢掉过一版改动，所以这次顺手把注释里那个算错的数也改了：
右边距 260 时并不是「白拿 194 px」，白拿的是右边距本身。）

改法：算术收进 `FrameContext.RightLabelColumn` 一处，三份拷贝都改为调它；收边从画面右缘改到
`SafeRight`。**两种推进方式都让**，不只是「窗口滚动」——「整段铺满」的最后一帧同样贴着右缘，而
那是视频停住不动、观众看得最久的一帧。

让位要花掉绘图区四分之一的宽度，而这笔代价不是每一帧都必须付的。所以三页各多了一个开关，
**默认关**：打开它，图把这一段宽度收回来。开关的类型不是布尔而是 0~1 的小数，因为有一种动效要
用到中间那些值 ——「窗口滚动」的最后一段会展开成完整区间，那时它画的就是「整段铺满」的形状。
让位量因此跟着**窗口展开的同一个斜坡**走到 0：滚动途中照旧让位（那时它还是一个窗口），展开完
画面与整段铺满完全同形。若在开始那一刻直接归零，画面会横跳一下。市值历程没有推进方式可选，
它天然就是整段铺满，所以那里是构造时定死的常量。
Version 1.0.11.0 fixes something that was done right and then half undone: on three pages the
figures sat underneath the platform's buttons.

When a vertical video plays on a phone, the right sixth of the frame is permanently taken by the
avatar, the like button and the comment button. None of that is visible in the app, because the app
draws no such interface — and the app is where these three pages were drawn. The market-value,
savings-plan and holdings pages all drew the labels riding the leading end of their lines to the very
right of the frame, which is exactly where that band sits.

The cause is **a comment that was not true**. Three pages each kept a copy of the arithmetic that
answers "how wide a column do the labels need", all three measured it against the frame's own right
edge, and all three carried the same reason for doing so: that the platform's rail already sat inside
the right margin. It does not. `SafeArea.Right` is 0.18, which on a 1080-wide frame is 194 px —
**wider than the default right margin of 150**. The labels therefore came to rest at 98% of the
frame, under the avatar and the comment button. (A false comment in this file has already cost one
release, so the wrong number in the new comment went as well: with a right margin of 260 it is not
194 px that would be paid twice, it is the margin itself.)

The arithmetic now lives in one place, `FrameContext.RightLabelColumn`, and all three copies call it;
the labels are gathered to `SafeRight` instead of to the frame's edge. **Both advance modes give
way**, not only the scrolling window: the last frame of a fill-the-whole-span chart sits against the
right edge too, and that is the frame the video stops on.

Keeping clear costs the plot a quarter of its width, and that is not a price every frame has to pay,
so each of the three pages now carries a switch for it, **off by default**. The switch is not a
boolean but a fraction, because one motion needs the values in between: a scrolling window spends its
closing stretch opening out into the whole range, and what it draws then is the whole range. So the
reservation shrinks across **the same ramp the window opens on** — the scroll itself keeps clear,
because while it is scrolling it is still a window — and reaches nothing exactly when the opening
finishes, leaving the frame identical to a chart drawn over the whole range from the start. Zeroing it
at the moment the ramp begins would make the picture jump sideways. The market-value page offers no
choice of advance, being the whole range by nature, so there the value is a constant fixed when the
renderer is built.

### 修正 / Fixed

- **末端标注不再压在平台那条按钮栏下 / the end labels clear the platform's rail** —— 市值历程、
  定投计划、持仓收益三页的标注收在帧宽 82% 那条线以内；「整段铺满」与「窗口滚动」两种推进都让。
  真机实测（持仓页，安全线 x=1065、画面右缘 x=1134）：三颗胶囊右缘 1057 / 1055 / 1058。

### 新增 / Added

- **三页各一个开关 / a switch on each of the three pages** —— 打开即允许图形越过右侧安全线，默认关。
  「整段铺满」全程用满宽度；「窗口滚动」滚动途中照旧让位，收尾展开成整段的那一段才放开，末帧与整段
  铺满同形（实测胶囊右缘 1127 / 1124 / 1127，与整段铺满一致；拖到 0.45 处 1048 / 1053 / 1056，
  仍在安全线内）。市值历程页没有推进方式，打开即生效。

包已构建：`artifacts/MarketMotionStudio_1.0.11.0_x64_arm64_bundle.msixupload`（149.8 MB / 142.9 MiB，
六个内包）。拆包核验 x64 与 arm64 两个内包的 Identity 都是 `1.0.11.0`，`Package/Properties/
DisplayName` 仍是字面值 `MarketMotionStudio`；包内 14 份手册、70 张配图、`resources.pri` 与 Win2D
的 `Microsoft.Graphics.Canvas.dll` 都在。

**这一版带着 1.0.10.0 的全部内容**（订阅那两条修复），所以 1.0.10.0 那个包不必再传，直接从这个
版本上传即可。

判据：三份真机脚本全过 —— 持仓 151 项、定投 88 项、市值历程 88 项；`verify-docs.py` 182 项 0 失败，
`verify-resw-uids.py` 14 语言 864 键 0 问题。

---

## 1.0.10.0 — 2026-10-07（更新版 / update）

**本版修正订阅的两个症状。** 一个是：已经在另一个设备上买过订阅的人，设置页那张写着续订日期、可以
「恢复购买」和「管理订阅」的卡片会整块消失 —— 而订阅本身是好的，水印能去掉、MP4 能导出。另一个是：
买完之后要重启应用才生效。

第一个症状只有一条路能成立，这也是它能被诊断出来的原因：卡片在 XAML 里的默认值就是 `Collapsed`，
所以它「消失」等于 `Known == false`；而那一刻 `Subscribed` 已经是 true。两者同时成立，只能是
`Subscribed` 先被置真、`Known` 随后被压假。代码里有两处会这么做，**都出自把「商店答没答」当成
「买没买」** —— 这俩不是同一个问题，也不来自同一个地方：许可证早就在本机、当场就能读；目录要联网，
可能根本不回来。

- 续订日期用**索引器**硬取 `license.AddOnLicenses[offer.StoreId]`。key 不在时索引器**抛异常**而不
  是返回空，被下面那个 `catch` 接住，而那个 catch 把任何失败都读成「商店没回答」。同一个文件里，
  上一行 `Holds()` 的注释自己写着「万一商店对同一个产品给出另一个 StoreId」——一处谨慎，一处假定
  必然命中。
- 目录查询返回空时直接 `return`，**许可证根本没被问过**。一次网络调用的成败，变成了这个人买没买
  的答案。

第二个症状有两层原因。一层是进程内**没有任何地方重读许可证**，而商店的购买窗口是另一个窗口，在那儿
买完回来，这个进程不知道。现在点「导出」之前会先把许可证在本地重读一遍，点击和它该拿到的对话框之间
不再隔着一次网络。另一层是商店的服务器要在购买**返回之后**才过一会儿下发许可证，这正是「我买了、它
还是锁着、重启就好了」的由来；购买成功后现在会等一等，最多再看三次（间隔 1 秒、2 秒）。

顺带两件：`RefreshSubscriptionAsync` 是开出去不等的，一次抛错的刷新会跳过它后面那句结算，卡片就停在
默认的折叠状态上 —— 结算移进了 `finally`。以及那个方法的注释写着「没有任何地方订阅 `Changed` 事件」，
**那是错的**：`WatermarkSettings.cs:33` 就订阅了它。
Version 1.0.10.0 fixes two symptoms around subscribing. One: someone who had paid — often on another
device — could lose the whole settings card that shows the renewal date and offers restore and manage,
while the subscription itself worked, watermark off and MP4 exported. Two: a purchase took effect only
after restarting the app.

The vanishing has exactly one route, which is what makes it diagnosable: the card is Collapsed by
default in XAML, so its absence means `Known` was false, while `Subscribed` had already been set true.
Both hold only if `Subscribed` was set first and `Known` forced false after it. Two places did that,
and **both come from reading "did the Store answer" as "has this person paid"** — not the same
question, and not answered in the same place either. The licence is already on this machine and answers
at once; the catalogue is fetched over the network and may simply not arrive.

- The renewal date was taken with an **indexer**, `license.AddOnLicenses[offer.StoreId]`. A key that is
  not there throws rather than returning nothing, the exception landed in the `catch` below, and that
  `catch` reads any failure as "no answer from the Store". The line above it, in the same file, allows
  for the Store handing back another id for the same product — one place careful, the next assuming the
  key must be there.
- An empty catalogue answer returned early, and **the licence was never consulted**. Whether one network
  call succeeded became the answer to whether this person had paid.

The restart had two causes of its own. Nothing in the process re-read the licence, so a purchase made in
the Store's own window — a different window — was unknown here until the next launch; the licence is now
read locally before exporting asks anyone anything, with no network round trip standing between a click
and the dialog it earns. And the Store grants the licence a moment *after* the purchase returns, which is
precisely how "I bought it, it stayed locked, restarting fixed it" happens; a successful purchase waits
and looks up to three times.

Two things alongside: `RefreshSubscriptionAsync` is fire-and-forget, so one throwing call skipped the
settling after it and left the card at its collapsed default — that settling moved into a `finally`. And
its comment claiming nothing subscribes to the `Changed` event **is wrong**: `WatermarkSettings.cs:33`
does.

### 修正 / Fixed

- **已有订阅时卡片不再消失 / the card stays put once you have paid** —— 「买没买」自己就能让卡片出现，
  不再取决于商店目录有没有答上来；续订日期改走 `TryGetValue` 回落，不再用会抛异常的索引器。
- **购买之后当场生效 / a purchase takes effect immediately** —— 认订阅一律只读本机许可证；成功的购买
  之后最多再看三次，补上商店下发许可证的那一段延迟。
- **一次失败的刷新不再把卡片留在折叠状态 / a failed refresh no longer leaves the card collapsed** ——
  结算移进 `finally`，出错也要给卡片一个答案。

包已构建、但**没有上传**：`artifacts/MarketMotionStudio_1.0.10.0_x64_arm64_bundle.msixupload`
（149.8 MB / 142.8 MiB），拆包核验包内六个内包的 Identity 都是 `1.0.10.0`。上一版那句「直接从这个
版本上传即可」没有兑现 —— 上传之前又攒了两批改动（末端标注让位、越过安全线的开关），它们一并进了
1.0.11.0。**1.0.11.0 带着这一版的全部内容**（订阅那两条修复），所以 1.0.10.0 这个包不必再传。

---

## 1.0.9.0 — 2026-10-07（更新版 / update）

**本版加第十八页：市值历程。** 一只股票的**流通市值**逐日成线，下面是它同一段时间的股价，两块面板
共用一条时间轴；也可以一次放几家公司，一家一条线。

这一页最难的不是画，是**没有任何源端给出历史股本**。市值 = 价格 × 股本，价格源端天天有，股本没有。
本版按一条恒等式把它算回来：**成交量 ÷ 换手率 = 流通股本**（换手率的单位是「占流通股本的百分之几」，
所以成交量除以它正好落回股数），取滚动 30 日的中位数抗住单日异常，再拿当天的价格去乘。对账结果：
A股用不复权收盘价，误差 −0.04%；港股拿不到不复权价，改走**成交额 ÷ 成交量**自算当天均价，误差
+0.08%；美股的换手率源端只给一位有效数字（差 10%），**因此美股不算**，页面只收本市场可交易的股票。

顺带一条要说清楚的口径：这样算出来的是**本市场可交易的那些股份**。两地上市的公司因此会低于行情软件
上「总市值」那个数字 —— 不是算错，是算的不是同一个东西。

线头上的数字是**骑线胶囊**：跟着线走，报的是动画走到那一刻的值，不是序列末值。只放一只时两块面板各
一颗；放几只时，那几个标签是画面上唯一说明哪条线是哪家的东西。
包已构建：`artifacts/MarketMotionStudio_1.0.9.0_x64_arm64_bundle.msixupload`（149.8 MB / 142.8 MiB），
拆包核验包内六个内包的 Identity 都是 `1.0.9.0`。
Version 1.0.9.0 adds the eighteenth page, Market Value History: one company's circulating market
value day by day, with its share price beneath it on the same time axis, or several companies at
once, one line each. The hard part is not drawing it — it is that **no source carries a historical
share count**. Value is price times count, and while the price arrives daily, the count does not, so
it is recovered from an identity: **volume divided by the turnover rate is the circulating count**
(the rate is a percentage *of* the circulating count, so dividing volume by it lands back on shares),
taken as a rolling 30-day median so one odd day cannot move it, then multiplied by that day's price.
Checked against quoted figures: A-shares, using the unadjusted close, land within −0.04%; Hong Kong,
which offers no unadjusted price, derives the day's average as turnover ÷ volume and lands within
+0.08%; US listings are **not computed**, because their turnover rate carries a single significant
digit (a 10% gap) — the page accepts only the stocks traded in the market it is showing. One
consequence worth stating: the figure counts the shares tradable *in this market*, so a company
listed in two places sits below the "total market value" a quote app shows. Not a wrong sum — a
different one. The number riding each line's leading end moves with the animation and reports the
value reached at that moment rather than the last value of the series; with one company both panels
carry one, and with several they are the only thing on the frame that says which line is whose.

### 新增 / Added

- **第十八页「市值历程」/ Market Value History, the eighteenth page** —— 一只或几只，市值与股价
  上下两块面板共轴；多标的时日期轴取**并集**，晚上市的那家从自己第一个交易日起，一次最多 6 家。
- **股本由换手率反推 / the share count is recovered from the turnover rate** —— 市值历史源端没有，
  只能算；美股因换手率精度不足而不算，不是没做。
- **骑线胶囊 / a capsule riding each line** —— 圆角底 + 该线自己颜色的描边，随动画走，报当下值。

---

## 1.0.8.0 — 2026-10-06（更新版 / update）

**本版认的是另一只加载项。** 第一只在合作伙伴中心里建成了「Microsoft Store 托管的易耗品」——
而产品的类型**保存之后不能改**，已发布的 product ID **既不能改也不能复用**，所以它只能由一只
新建的「订阅」型加载项取代：product ID `MarketMotionStudioMonthly`。本版把 `OfferToken` 指向它。

这只替代带来一件值得写下来的事：**本版起不再认旧那只**。易耗品买一次就永久解锁、永不续费，
而它的许可证在代码里**和订阅长得一模一样**（到期日是默认值，被当成「还没到期」）。所以认它
等于在一个写着「订阅」的按钮下面卖一次性买断 —— 名字对得上，东西对不上。
订阅能不能买，取决于那只在商店里是否已发布并关联到本应用；改加载项的配置不需要重新上传应用。
包已构建：`artifacts/MarketMotionStudio_1.0.8.0_x64_arm64_bundle.msixupload`（149.7 MB / 142.8 MiB），
拆包核验包内六个内包的 Identity 都是 `1.0.8.0`。
Version 1.0.8.0 asks for a different add-on. The first one was created in Partner Center as a
Store-managed consumable, and a product's type cannot be changed once the page has been saved, nor
can a published product ID be edited or reused — so a newly created subscription add-on replaces it,
under the product ID `MarketMotionStudioMonthly`, and `OfferToken` now points there. Worth writing
down what that replacement costs: from this version the old one is no longer recognised. A
consumable buys access once and never renews, and its licence is indistinguishable from a live
subscription's here — the expiration date is the default, which reads as "not expired yet".
Recognising it would sell a one-time purchase under a button labelled subscribe: right name, wrong
thing. Whether the subscription is purchasable depends on that add-on being published and associated
with this app; changing an add-on's configuration does not require resubmitting the app.

### 新增 / Added

- **认新建的订阅型加载项 / it asks for the subscription add-on that replaced the consumable** ——
  加载项名从 `MarketMotionStudio` 换成 `MarketMotionStudioMonthly`。只改了这一行：认哪一只始终
  按 token，不按类型，也不按商店生成的 StoreId（后者换环境就换）。

---

## 1.0.7.0 — 2026-10-06（更新版 / update）

**1.0.6.0 已经提交商店**，而它提交的是本版的**前一个构建**：后补的两处改动（查询失败时单独留
一行、以及那行日志漏 `$` 的修复）因此**不属于 1.0.6.0**，要到本版才到用户手上。同一版本号
的包传不进去第二次，这是它们必须等一个版本号的原因。
本版的意思是**把「商店没给加载项」这一句拆成能各自修的几种**。1.0.6.0 的那次真机回报是
`no add-on named MarketMotionStudio among 0` —— 它只说明商店对这个应用一个可买的加载项都没
给出来，而不说明为什么。本版三件事都是为了让下一次测试一次分清，其中第二件**有可能直接把
订阅变成可买的**。
包已构建：`artifacts/MarketMotionStudio_1.0.7.0_x64_arm64_bundle.msixupload`（149.7 MB / 142.8 MiB），
拆包核验包内六个内包的 Identity 都是 `1.0.7.0`、DisplayName 都是预留字面值。
Version 1.0.6.0 has been sent to the Store, and it was the build before this one: two later
repairs — a line of its own when the query itself fails, and the `$` missing from a log — belong
to this version instead, because a package cannot be submitted twice under the same number. What
this version is for is splitting "the Store gave no add-on" into causes that have separate
repairs. The report from 1.0.6.0 was `no add-on named MarketMotionStudio among 0`, which says the
Store offered nothing purchasable for this app and says nothing about why. The package is built —
`artifacts/MarketMotionStudio_1.0.7.0_x64_arm64_bundle.msixupload` (149.7 MB / 142.8 MiB) — and all
six inner packages carry Identity `1.0.7.0` and the reserved literal DisplayName.

### 新增 / Added

- **查询失败不再和「真的没有」长得一样 / a failed query no longer looks like an empty one** ——
  「清单是空的」和「查询压根失败了」在外面长得分毫不差，而它们是两个地方的事：前者要去合作
  伙伴中心修，后者是这台机器这个包（`0x803F6107` 的意思是商店不认它是商店装的）。现在失败时
  单独留一行，并带上 HRESULT。
- **加载项查询不再只问 Durable / the query no longer asks only for Durable** —— 文档口径是
  「订阅型加载项就是 Durable」，只问 Durable 在配对了的世界里确实能找到。但这也是**我们这边
  唯一能造成 `N=0` 的写法**：假如那只加载项在合作伙伴中心被建成了别的类型，只问 Durable 就
  会返回空，而日志会把账算到商店头上。现在三种类型都问（选哪一只始终按 token，不按类型），
  返回的东西连类型一起写出来 —— **这一件有可能直接把订阅变成可买的**。
- **那行日志现在真的会说出 token / the line that names the token now names it** ——
  「商店返回了别的加载项」那个分支漏了 `$`，会原样打印 `{OfferToken}` 字面量。它正是为了
  「一句话里分清两种修法」才写的，却连自己抱怨的是哪个 token 都不说。

### 本版仍然修不了的那一件事

加载项要是在合作伙伴中心没有发布、没有关联到本应用、或者可用性不覆盖用户所在的市场，装本版
的人看到的**仍然是**「订阅没能完成」那个框。**发布加载项不需要重新上传应用**，改的是商店那
一侧的配置；本版只是让下一次测试能一次看清是上面哪一种。

---

## 1.0.6.0 — 2026-10-06（更新版 / update）

**1.0.5.0 已经提交商店**，所以本版只列在它之上新增的改动。1.0.5.0 上传的那份包是 10-06 08:48
重编的（带着「标题折成两行」「导出与去水印改为订阅」「未订阅时浓度钉在上限」这三批），
那三件事因此**不属于本版**。本版只有一件用户可见的事，而它单独发一版是值得的——上一版在
那里留了一个死口。
包已构建：`artifacts/MarketMotionStudio_1.0.6.0_x64_arm64_bundle.msixupload`（149.7 MB / 142.8 MiB），
拆包核验包内六个内包的 Identity 都是 `1.0.6.0`、DisplayName 都是预留字面值。
Version 1.0.5.0 has been sent to the Store, so this entry lists only what is new on top of it. The
package submitted as 1.0.5.0 was the one rebuilt at 08:48 on 10-06, which carried three batches of
change — two-line titles, exporting and watermark removal behind a subscription, and the strength
pinned at its ceiling while nobody is subscribed — so none of those belong to this version. This
version has exactly one thing a user can see, and it is worth a version of its own: the previous one
left a dead end there. The package is built —
`artifacts/MarketMotionStudio_1.0.6.0_x64_arm64_bundle.msixupload` (149.7 MB / 142.8 MiB) — and all
six inner packages carry Identity `1.0.6.0` and the reserved literal DisplayName.

### 新增 / Added

- **订阅买不成的时候不再一声不响 / a purchase that cannot go through no longer says nothing** ——
  上一版留下的是这样一个场面：商店那边没有可买的东西时，`SubscribeAsync` **连商店自己的购买
  框都不开**（没有东西可给，就不去打扰），而 `PermitAsync` 拿到 false 之后十七个页面一律
  `return` —— 于是**「按了订阅」和「什么都没按」在画面上完全一样**，人只能把它读成按钮坏了。
  现在三个答复都要说话：联系不到订阅（商店没有可购买的内容）与购买已报告完成却没有授予权限，
  各弹一句说明并写清原因；「恢复购买」空手而归也说一句——按下它的人相信自己已经付过钱，
  「没找到」和「什么都没变」不是同一件事。**唯一仍然安静的是用户自己关掉商店的窗**，那本来
  就是「不要」的意思。「哪句话答哪个答案」只有一处（`SubscriptionOffer.Explanation`），设置页
  卡片与导出对话框读的是同一份映射——两处各写一份，同一个结果迟早会被讲成两种意思，而每一份
  单看都通顺、也都不被另一份反驳。新增第 17 个订阅键 `SubscriptionFailedTitle`（14 语言）。
  The previous version left this: with nothing to sell, `SubscribeAsync` **never even opens the
  Store's own purchase dialog** (nothing to offer, so nothing to interrupt with), and every one of
  the seventeen pages simply `return`s once `PermitAsync` answers false — so **pressing Subscribe
  and never having pressed it look exactly the same**, and the only reading left is that the button
  is broken. All three answers speak now: no subscription within reach (the Store has nothing to
  sell) and a purchase reported complete that granted nothing each get their own dialog with the
  reason spelled out, and a **Restore purchase** that comes back empty says so too — somebody
  pressing it believes they have already paid, and "not found" is not the same as "nothing
  changed". **The one answer that stays quiet is the user closing the Store's own window**, which is
  what "no" means. Which sentence answers which outcome lives in exactly one place
  (`SubscriptionOffer.Explanation`): the settings card and the export dialog read the same map,
  because two copies is how one outcome ends up described two ways, each of them fluent and each
  uncontradicted by the other. One new subscription key, `SubscriptionFailedTitle`, in 14 languages.
- **商店加载项查询失败时把错误码写进诊断日志 / the add-on query now logs its own error** ——
  之前只记 `no add-on named … among 0`，而「清单是空的」与「查询失败了」在外面长得一模一样；
  少了 `StoreProductQueryResult.ExtendedError` 那一行，排查一律被指引到合作伙伴中心去找，
  真因却可能在这台机器这个包上（`0x803F6107` 的意思是商店不认这个包）。现在两种情况各留一行，
  而且**清单不是空的时候会把商店实际给了哪些加载项逐个写出来**（产品 ID / StoreId / 类型）——
  「一个都没给」与「给了几个、但叫别的名字」是两种完全不同的修法，一句话里分得出来就不用去
  翻仪表盘。
  Until now the log only said `no add-on named … among 0`, and *the list is empty* looks exactly
  like *the query failed* from outside. Without that one line from
  `StoreProductQueryResult.ExtendedError` every investigation is pointed at Partner Center, when
  the cause can as well be this machine or this package — `0x803F6107` means the Store does not
  recognise the package. The two cases now each leave their own line.

### 本版修不了的那一件事 / what this version cannot fix

**订阅能不能买，仍然取决于合作伙伴中心那边，不在本版手里。** 加载项要存在、product ID 要精确
是 `MarketMotionStudio`、要**已发布并关联到本应用**——`GetAssociatedStoreProductsAsync` 只返回
已关联的那些。关联没做好，装了本版的人看到的仍然是设置页**一张整块隐藏的订阅卡片**，以及
导出时那句「联系不到订阅」：**本版把话说出来了，没有把东西变出来。** 加载项发布之后不需要重新
上传应用，改的是商店那一侧的配置。
**Whether the subscription can be bought is still decided in Partner Center, not by this version.**
The add-on has to exist, its product ID has to be exactly `MarketMotionStudio`, and it has to be
**published and associated with this app** — `GetAssociatedStoreProductsAsync` only returns what is
associated. If that is not in place, somebody installing this version still gets **a subscription
card that stays hidden altogether** and the "no subscription within reach" line when exporting: this
version makes the thing *say* something, it does not make it *exist*. Publishing the add-on does not
call for a new submission — what has to change is the Store's configuration.

### 开发侧（不进 Release）/ development only (compiled out of Release)

- `tools/simulate-subscription.py on|off|status`：本地 Debug 解锁导出与水印自定义的开关
  （`LocalState\simulate-subscription.txt`，`#if DEBUG` 包裹，Release 编译掉）。
  真机判据两处：`verify-debug-subscribed-export.py`（不弹订阅框、文件夹里真的多出 mp4）与
  `verify-subscription-failure-told.py`（买不成时那个框真的弹出来，且背靠背开第二个对话框
  不崩）。

---

## 1.0.5.0 — 2026-10-05（更新版 / update）

**1.0.4.0 的包已经构建，但从未提交商店**，所以本版把它带上一起走，1.0.4.0 不再单独上架。
下面只列本版在 1.0.4.0 之上新增的改动；应用的完整能力仍见更下面的 0.0.0.0 条目。包已构建：
`artifacts/MarketMotionStudio_1.0.5.0_x64_arm64_bundle.msixupload`（149.6 MB / 142.6 MiB），
拆包核验包内六个内包的 Identity 都是 `1.0.5.0`、DisplayName 都是预留字面值。此后源码又动过
（标题折成两行这一版、导出与去水印改为订阅这一版、以及未订阅时浓度钉在上限这一版），**提交商店之前要按惯例删掉 `Upload`、
`ForBundle` 与 `*.appxrecipe` 重编同一个包** —— 商店文案不能先于与它匹配的那个包上传。订阅还要
**先在合作伙伴中心把那个加载项建出来**（其标识符是 `MarketMotionStudio`，按月计费），
否则包里的 `StoreSubscription` 在商店里找不到任何可买的东西，登录用户看到的将是一张隐藏的卡片。
Version 1.0.4.0's package was built but never sent to Partner Center, so this version carries it and
1.0.4.0 will not be submitted on its own. What follows is only what this version adds on top of
1.0.4.0; the full feature set is still in the 0.0.0.0 entry below. The package is built —
`artifacts/MarketMotionStudio_1.0.5.0_x64_arm64_bundle.msixupload` (149.6 MB / 142.6 MiB) — and all
six inner packages carry Identity `1.0.5.0` and the reserved literal DisplayName. The source has
moved on since it was built — this is the version that added two-line titles, put exporting
behind a subscription and pinned the watermark's strength while nobody is subscribed — so the
package has to be rebuilt the usual way before it goes up (drop
`Upload`, `ForBundle` and `*.appxrecipe` first): the listing copy must never arrive ahead of the
package it describes. The subscription also needs **the add-on created in Partner Center first**
(identifier `MarketMotionStudio`, billed monthly); without it `StoreSubscription` finds
nothing to sell in the Store, and a signed-in user would be shown a card that stays hidden.

### 新增 / Added

- **导出视频与去掉水印改为按月订阅 / exporting a video and removing the watermark now take a
  monthly subscription** —— 这是本版对**已经在用的人**影响最大的一处，所以写在这里最前面：
  这两件事以前是免费的。改的是这两件，不是应用：十七个图表页的取数、播放动画、保存封面图
  **一律照旧免费**，也不打算收费。未订阅时点「导出」**不是把按钮置灰**，而是弹一个说明
  「订阅买下什么、每月多少」并带「订阅」与「恢复购买」两个动作的对话框 —— 灰按钮只说「不行」，
  而已经想拿文件的人对着它无事可做。水印那个开关在订阅之前**固定为开且搬不动**，下面挂一句
  原因：画面里带的那一层就是文件里会有的那一层，不做「预览干净、导出有标记」这种失信的事。
  同一件事还有另一半：**浓度滑条在订阅之前钉在最高的 40% 而且拖不动** —— 把水印调到看不见
  等于换一种方式把它去掉，留着这个口子，开关那一半的认真就是假的。存过的偏好仍然留着，
  订阅之后它从那处接着走。
  判断只有一处（`Views/SubscriptionOffer.cs`），**十七个页面的导出都问它、且都在编码之前问**；
  **封面 PNG 那条路径上一个闸口也没有**（`verify-subscription.py` 数出 17 / 17 与 0）。许可证
  一律**从源端读**、不自己记一笔「付过了」：记一笔就要自己保鲜，那样要么自己过期、要么永远
  算数。读不到（侧载、商店被策略关掉、加载项还没上架）**一律按未订阅处理** —— 按已付费处理
  等于白送。设置页有一张卡片（月价、续订日、订阅 / 恢复购买 / 管理订阅），在商店够不着的
  机器上整张隐藏而不是显示成空的。
  This is the change that touches people who already use the app, so it goes first: both of these
  used to be free. What changed is those two things, not the app — fetching data, playing the
  animation and saving a cover image stay free on all seventeen pages, and are meant to. Pressing
  **Export** without a subscription **does not grey the button out**; it opens a dialog saying what
  the subscription buys and what it costs, with **Subscribe** and **Restore purchase** on it. A grey
  button only states "no", and somebody who has already decided they want the file has nothing to do
  with that. The watermark switch is **on and immovable** until then, with the reason underneath:
  what the preview carries is what the file carries, rather than a clean preview over a marked
  export. The same thing has a second half: **until then the strength slider sits at its ceiling of
  40% and cannot be dragged**, because turning the mark down until nobody can see it is another way
  of making the switch say something untrue. The stored preference is kept, so subscribing picks it
  up where it was left. The decision lives in exactly one place (`Views/SubscriptionOffer.cs`); **all seventeen
  export handlers ask it, and ask before anything is read for the encode**, while the **cover PNG
  path has no gate at all** (`verify-subscription.py` counts 17 / 17 and 0). The licence is always
  **read from the Store** rather than remembered as "someone paid": a copy would have to be kept
  fresh, and it would either expire on its own schedule or be believed forever. Anything that cannot
  be read — sideloaded build, Store switched off by policy, add-on not published yet — counts as
  **not subscribed**, because counting it as paid is giving the thing away. Settings carries a card
  (price, renewal date, Subscribe / Restore / Manage) that is hidden entirely where the Store cannot
  be reached rather than shown empty.

- **第十七页：债市固收竞速 / the seventeenth page: bond indices** — 九条债券指数一行，条形是
  **价格变动，不是持有回报**：源端对指数忽略复权参数，而债券回报的大半在票息里，票息永远
  不进报价。这与大类资产页刻意相反 —— 那页画在复权序列上，因为基金会分红；这页留空，因为
  指数不分红。两个榜不能对着读。清单内置、不给自选分组：「中证全债」在源端**并不存在**
  （看着像的那个代码是上证分离债指数，月线停在 2015 年 8 月；整个指数代码空间扫过一遍确认
  没有全债指数），那三个位子换成源端确实作答的最深的信用债指数。九行起点各不相同（最早
  2003-02，深证转债 2014-08），十年榜上后者五年后才加入；没开始的行是**缺席**而不是 0.00%。
  Nine bond indices, one per row, and the bar is the **change in the quote, not the return on holding
  it**: the source ignores the adjustment parameter for an index, and most of a bond's return is
  coupon, which never reaches a quote. That is deliberately the opposite of the asset classes page,
  which is drawn on adjusted closes because those funds do pay out. The list is built in rather than
  a watchlist roster: the index that looks like "ChinaBond All" is not it — that code is the Shanghai
  split-coupon index, whose monthly series stops in August 2015 — so those three places go to the
  deepest credit indices the source actually answers for. The nine rows begin on nine different
  months, and a row that has not begun is **absent**, not 0.00%.

- **市场成交额页改成一篮子自选 / Market Turnover draws a basket of your own** — 这一页是唯一把
  清单**加成一个数**的榜，而清单常常是按四个排名榜的需要建的（十几只是常态）。所以 chip 变成
  **开关**：点名字决定它进不进合计，`×` 仍然是删共享清单 —— 两个按钮而不是一个，因为「在看板
  上藏掉一条线」不该等于「改自己的持仓」。打开时默认只画清单里的**第一只**，因为默认那一版
  必须是有人会看的一版。日内那一路同时进来：累计成交额曲线按钟点**线性推进**（这是一根钟，
  缓动会让人以为没人交易了），并**截到 15:00**（端点补到 15:30 是盘后固定价格交易，比日线多
  约 0.1%）。空清单与没勾选**分开报**，因为一句是「往里加标的」，另一句是「把开关点回来」。
  The one board that adds the list into a single number, and the list is usually built for the four
  ranking boards — a dozen entries is normal. So the chip became a **switch**: pressing the name
  decides whether it joins the total, while `×` still removes it from the shared list. Two buttons
  rather than one, because hiding a line on one board should not be editing your holdings. A
  switched board draws only the **first** pick by default, because the default has to be a frame
  somebody would actually watch. Intraday arrived with it: a cumulative-turnover curve advancing
  **linearly** by the clock — a curve that eases looks like trading stopped — and **cut at 15:00**,
  since the 15:30 the endpoint pads to is after-hours fixed-price trading and runs about 0.1% above
  the daily bar. An empty list and nothing ticked are two different messages.

- **K线：指定一个交易日画一天 / Candles: one named trading day** — 分钟周期三档（1 / 5 / 15
  分钟）；选了分钟档就用**交易日下拉**换掉区间下拉，换日只重画不重新取数。端点不接受日期，
  所以一次取回整段（单请求 800 根上限，约 4 个 1 分钟交易日或 50 个 15 分钟交易日），再按
  **根数**与**最后一根是否 15:00** 判定哪几天是完整的一天 —— 只看根数会把被 800 根截断那天
  当成整天。**只有沪深有分钟线**，港股与美股一律返空。横轴按钟点铺，而 90 分钟午休**不在轴
  上**：按墙上那口钟从 09:30 铺到 15:00，午休会实打实吃掉 27% 的宽度（实测最宽空档 27% →
  2.6%），现在上下午各占半个轴、中间留一条 2% 的缝（竖线与「午休」二字保留）。
  Three finer periods — 1, 5 and 15 minutes — and choosing one replaces the range selector with a
  **list of trading days**; changing the day redraws without fetching again. The endpoint takes no
  date, so one request carries the whole window (800 bars, about four 1-minute sessions or fifty
  15-minute ones) and a day counts as whole only by **how many bars it carries and whether the last
  is stamped 15:00** — bar count alone would call the day the 800-bar cap cut short a full session.
  **Only Shanghai and Shenzhen have minute bars**; Hong Kong and US codes answer with an empty body.
  The axis is laid out by the clock, but the ninety-minute lunch break is **not on the axis**: going
  from 09:30 to 15:00 by the wall clock let lunch take 27% of the width (measured: the widest gap
  fell from 27% to 2.6%), so morning and afternoon now take half each with a 2% seam between.

- **持仓收益：最多六只放在一起比，曲线末端实时显示收益金额 / Position Return: up to six
  holdings at once, each carrying its gain on the curve** — 一页回答「这几只里哪只更值得买」。
  六只共用一帧、各占一色，颜色按**清单里的顺序**取而不是哈希 —— 哈希是稳定的但**不互斥**，
  六只里两只撞成同色就是一条线跟自己比。每只在**自己那条线的末端**挂一个胶囊，写着名字与赚
  了多少金额，跟着曲线一起长，所以那个数字始终是「这一帧」的，而不是只有最后一帧才对。写
  **金额**不写百分比：两只买在不同日子，百分比本来就不可比。两只以上时中间的大数字换成**领先
  那只的金额与名字**，收尾换成每只一张卡。**只有一只时**同样有那个末端胶囊 —— 这是这次需求
  的一半。
  One page answering "which of these was the better buy". Six holdings share one frame in six
  colours, assigned by the **order they were listed** rather than by hash — a hash is stable but not
  *distinct*, and two of six coming out identical is a line compared with itself. Each carries a
  capsule at the **end of its own line** naming the instrument and the money it made, riding the line
  as it grows, so the number is the one for *this* frame rather than one that only becomes true at
  the last. **Money, not percent**: two holdings bought on different days are not comparable as
  ratios. With more than one, the headline becomes the **leader's amount and name** and the closing
  cards become one per holding. **A single holding gets the capsule too** — that was half of the
  request.

  三处口径，每处都有一个「看着对」的错答案：日期轴取**并集**（取交集会把十年对比悄悄截成最
  年轻那只的三年，而画面、状态行、期数全都正常）；晚上市的**从自己第一个交易日起、之前不画**
  （沿本金拉平线会画出「在它还买不到的年份里亏钱」）；第七只**拒绝取数**而不是静默少画（少画
  的画面完全正常、看不出少了谁），跨市场的标的同样过滤掉并报出名字 —— 它那份钱不是本市场的
  货币，画上去就是一条错的线。
  Three points of basis, each with a wrong answer that looks right: the axis is the **union** of
  their trading days (intersecting would quietly cut a ten-year comparison down to the youngest
  holding's three years, with the frame, the status line and the period count all looking normal);
  a listing that began later **starts later and is not drawn before it existed** (pulling it flat
  along the capital would invent years in which it was losing money); a seventh is **refused** rather
  than silently dropped — a frame that drew six looks exactly like one you failed to add the seventh
  to — and a pick from another market is dropped the same visible way, because its amount is in a
  currency the frame is not quoting.

- **标题可以折成两行 / titles may wrap onto a second line** — 以前标题是一行，一行放不下就缩字号；
  现在先折行：标题框里按回车就在那里断，一行放不下时按画面宽度自动折出第二行，**最多两行**，
  两行仍放不下才按比例缩字号（最多缩到一半）。折出第二行时下面的整摞（副标题、交易日、日期、
  运行中的总额、绘图区）一起下移一行的高度，底部不动，所以图表相应变矮；只占一行的标题，画面与
  改动前**一字不差**。十一个标题（十个渲染器加空数据时的底板）共用一处测量与一处让位算术：
  **行数必须在读第一个行锚点之前算出来** —— 晚一步就是两行字叠在副标题上，而画面看着只是
  「字重了一点」，状态行与界面树全绿。
  Titles used to be one line that gave way by shrinking; now they wrap first: Return in the box
  breaks them where you put it, a line too wide folds onto a second, **two at most**, and only when
  two will not hold it does the size come down (to half at most). A second line moves the whole stack
  below it — subtitle, session, date, the running total, the plot — down one row while the bottom
  margin stays put, so the chart is that much shorter; a title that fits on one line leaves the frame
  **exactly** as it was. Eleven titles (ten renderers plus the empty-data backdrop) share one
  measurement and one piece of shift arithmetic, and the **line count has to be known before the first
  row anchor is read**: work it out any later and two lines print on top of the subtitle, which reads
  as nothing more than slightly heavier type, with the status line and the UI tree both green.

### 修复 / Fixed

- **两个榜共用的月线起点口径 / a month-window bug shared by two boards** — 源端只以**整月**作
  答，且以该月**最后一天**命名那一行；而窗口是从今天倒推 N 个月算出来的，起点落在某个月的中
  间 —— 那半个月被当成了一个整月，等于白送一个月，而表头上的首尾两个日期看起来是对的。现在
  两端都先对齐到整月再去问源端。大类资产页抄了同一套算术，一起修：十年榜从 120 个月变成 119
  个月，sz399307 从 +63.04% 降到 +62.26%。
  The source only answers in **whole months** and names each row after that month's **last day**,
  while the window was computed by counting N months back from today — so the start landed mid-month
  and that partial month counted as a whole one, a free month, with the two dates in the header
  looking correct. Both ends now align to whole months before asking. The asset classes page carried
  the same arithmetic and was fixed with it: the ten-year board went from 120 months to 119, and
  sz399307 from +63.04% to +62.26%.

### 已知限制 / Known limits（沿用 1.0.4.0，另加两条 / unchanged from 1.0.4.0, plus two）

- 分钟 K 线**只有沪深**：港股与美股代码在分钟端点上一律返空，所以那两个市场没有这一档。
  Minute candles are **Shanghai and Shenzhen only**: Hong Kong and US codes answer the minute
  endpoint with an empty body, so those two markets do not get the mode.
- 持仓页一次最多**六只**：六张末端标签、六张卡片、六条曲线还是一场比较，十几只就是一张码。
  Position Return carries **six** at a time: six end labels, six cards and six curves are still a
  comparison; a dozen is a barcode.
- 图标只换在导航里：设置与帮助仍是系统字形（问号与齿轮），工具条上的字形也没有重画。
  The new icons are in the navigation only; Settings and Help keep their glyphs.
- 成交量换手率与行业板块竞速的日线区间上限仍是约 900 个自然日，一次请求的天花板就到那里。
  The daily ceiling on Volume & Turnover and Sector Race is still about 900 calendar days.
- 美股没有日内模式（那个分时端点的 `data` 是 list 不是 object），日内只有最近几个交易日可选。
  There is no intraday mode on the United States (that endpoint returns a list, not an object).
- 一块榜上的行内文字是**一个字号**：整块榜算一次，行与行不会各自缩放。
  The row text on a board is **one size**, computed once for the board.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份改成 1.0.5.0 的
内容：第十七页债市固收、成交额页的自选篮、K线的指定交易日、持仓页的六只对比，**以及所有页面的
标题可以折成两行**。同一份文件里「说明」的图表页数与「产品功能」的图表条数从十六改成十七 ——
第十七页插在**大类资产之后**，页面上早已在，只是从来没进过商店文案。三处各由一个脚本按语言改，
幂等，且按整行精确匹配 —— 某语言的措辞与脚本里的不一致时会报错，而不是留下一个旧数字。
标题那一条**不手写**：商店文案里那句话直接取自 14 份帮助手册「视频」章里那一句（`port-title-wrap-help.py`
是它唯一的事实来源），免得同一件事在两处各写一遍、慢慢讲成两种意思。加上它以后最长的一语种落到
1229 字符，仍在商店 1500 的硬上限之内。**订阅那句写在「说明」段（长期成立的事实），不只写在
「新增功能」（只说一次）** —— 把原本免费的导出与去水印改成订阅，商店里不说、用户装完才发现，
是差评的写法。四处改动都在同一个脚本里（`port-store-listing-1050.py`），CSV 由 `port-listing-csv.py`
跟一次、`verify-listing-csv.py` 逐格比对（43 项）。
The fourteen "What's new" lines now describe 1.0.5.0: the bond page, the turnover basket, one named
candles day, six holdings at once, **and titles that wrap onto a second line**. The description's page
count and the features bullet went from sixteen to seventeen — the bond page sits **after Asset
Classes**, has been in the app all along and had never reached the listing. One script per edit,
idempotent and matching whole lines, so a language whose wording differs fails loudly instead of
keeping a stale number. The title sentence is not hand-written for the store: it comes straight out of
the sentence already sitting in the Video chapter of the fourteen manuals, because two places telling
the same thing eventually tell it differently. **The subscription sentence goes into the description**
— a standing fact — **rather than only into "What's new"**, which says it once: turning two formerly
free things into a paid subscription without saying so in the listing is how one-star reviews are
written. All four edits live in one script (`port-store-listing-1050.py`), and the CSV is regenerated
by `port-listing-csv.py` and compared cell by cell by `verify-listing-csv.py` (43 checks).

---

## 1.0.4.0 — 2026-10-02（更新版 / update）

**1.0.3.0 已经提交商店、正在认证**，所以下面只列本版在它之上新增的改动。应用的完整能力仍见
更下面的 0.0.0.0 条目。包已构建：`artifacts/MarketMotionStudio_1.0.4.0_x64_arm64_bundle.msixupload`
（149.3 MB / 142.4 MiB），拆包核验 x64 与 arm64 两个内包的 Identity 都是 `1.0.4.0`。
Version 1.0.3.0 has been submitted to the Store and is in certification, so what follows is only what
this version adds on top of it. The full feature set is still in the 0.0.0.0 entry below. The package
is built — `artifacts/MarketMotionStudio_1.0.4.0_x64_arm64_bundle.msixupload` (149.3 MB / 142.4 MiB) — and both
inner packages, x64 and arm64, carry Identity `1.0.4.0`.

### 新增 / Added

- **八个新页面：从第九页到第十六页 / eight new pages, the ninth through the sixteenth** — 1.0.3.0
  停在第八页。这一版把导航里的十六页排满了：市值榜、AH 溢价、极端交易日、汇率走廊、指数长跑、
  大类资产、回撤与修复、持有胜率。它们不是八个并列的功能，是三种问法：
  Eight pages arrived between the eighth and the sixteenth. They are not eight parallel features but
  three ways of asking a question.
  - **市值榜竞速 / Market Cap Race** — 一个市场市值最大的十五家公司，按月排成横向条形，名次一路
    变到最后一帧。候选池宽到两百只以上：A 股取当日榜单、再并上一份历史档案（万科、中国重工、
    上汽这些今天不在前排、当年在的公司），港股与美股各有一份写死的池子，**并且只服务内地**的新浪
    排行接口对它们返空。所以「谁上榜」是算出来的，不是写死的十五个。
    One market's fifteen largest companies as horizontal bars, sampled monthly, the order changing to
    the last frame. The field runs past two hundred names: on the mainland it is today's ranking plus
    an archive of the companies that led in earlier windows, while Hong Kong and the United States
    use a written list, because the ranking endpoint this app has is mainland-only and answers with
    nothing for the other two.
  - **AH 溢价 / AH premium** — 同一家公司在两地上市时，A 股相对 H 股贵多少，按月，名次一路变。
    它比的是**两个 listing 的价格**，所以走的是不复权那一侧 —— 复权只在一侧生效会把两地价格
    比成两件不同的事。
    How much more a company's mainland listing costs than its Hong Kong one, for the firms listed on
    both sides. It compares two listings' prices, so it uses the unadjusted series: adjusting one
    side and not the other would compare two different things.
  - **极端交易日 / Extreme days** — 一个标的历史上单日波动最大的那些天。**这一页的行是日子，不是
    公司**，全应用只有它这样；排名按**幅度**而不是按涨跌符号，因为 −7.7% 应该和 +8.1% 并排坐着。
    One instrument's biggest single-day moves, ranked by size. **Its rows are days, not companies**,
    which no other page does, and it ranks by magnitude rather than by sign so that −7.7% sits beside
    +8.1% instead of under every rise.
  - **汇率走廊 / Currency corridors** — 一组货币一行，**行本身就是那条走廊**：一头是这组货币在
    区间里到过的最便宜，另一头是最贵，游标是它现在的汇率。所以别处的条形长度在这里没有意义 ——
    每一行都占满整行，动的是游标和走廊本身。
    One row per pair, and the row *is* the corridor: one end the cheapest the pair has been in the
    span, the other the dearest, the marker where the rate is now. Bar length means nothing here —
    every row fills the width and what moves is the marker and the corridor.
  - **指数长跑 / Index race** — 一行是一个指数，行是**这个指数从自己在区间里的第一个月起涨了多少**，
    不是点位。上证指数的 3,800 和标普 500 的 5,700 不在同一把尺上。
    One row per index, and the row is how far that index has come since its own first month in the
    range — not its level. 3,800 on the Shanghai Composite and 5,700 on the S&P 500 are not two
    points on one scale.
  - **大类资产 / Asset classes** — 一行是一类资产，行是**持有它到今天赚了多少**。八档都是境内
    交易所挂牌的基金，买它们的钱是同一种钱，所以能直接比。
    One row per asset class, and the row is what holding it earned. All eight are funds on a mainland
    exchange, bought with the same money, so they compare directly.
  - **回撤与修复 / Drawdowns** — 一行是**它落在自己高点下方多远**：不是它赚了多少，而是赚到
    这些要付出什么。跑的是和大类资产同样的八档，只是不互相比，而是各自比自己的高点。
    A row is how far below its own high a holding sits — not what it earned, but what it cost to earn
    it. The same eight holdings as the asset race, measured against themselves.
  - **持有胜率 / Hold odds** — 一行是**已走完的持有中赚钱的那一部分**：在区间里每一个可以买进
    并持有同样时长的月份中，最后是赚的占多少。打分的是「持有」这件事多常成立。
    A row is the share of finished entries that gained — of all the months a holder could have bought
    in and held for the same length of time, the share that ended up ahead.
  - **后四页的数字走复权**，与第十三页之前那几页**相反**，因为问的问题相反：这一组问的是
    「持有赚了多少」，而拆过份额的基金不复权价格曲线会断崖、货币基金的收益几乎全在分红里
    （不复权十三年 +0.03%，复权 +18.76%，两者差着一整个数量级）。**源端对指数忽略复权参数**
    ——十二个指数两路取回来的差值全是 0.0000 —— 所以指数那一行是价格回报，个股与基金那一行
    是总回报，这一条写在页面的口径说明里。
    The last four pages use the adjusted series, the opposite of the pages before them, because they
    ask the opposite question: what holding it earned. Without adjustment a fund that split has a
    cliff in its price and a money-market fund's return — which is nearly all in its distributions —
    reads as +0.03% over thirteen years instead of +18.76%. The source ignores the adjustment
    parameter for indices (all twelve come back identical on the two paths), so an index row is a
    price return while a stock or fund row is a total return, and the page says so.
- **四页清单板共用一份自选 / the four boards share one watchlist** — 指数长跑、大类资产、回撤与
  修复、持有胜率用的是同一份清单，可以三个市场混装，改一处四页都看得到。换一组就丢掉已经取到
  的数（留着会把上一组曲线的形状画在下一组的名字底下）；取数成功后清单里的名字会改成端点叫的
  那一个。最少三只、最多十六只。
  The index race, the asset race, the drawdown page and the hold-odds page read one shared list, and
  it may mix all three markets. Changing it discards the data already fetched — keeping it would draw
  the previous group's shape under the next group's names — and after a fetch the entries take the
  names the endpoint calls them by.
- **极端交易日的标的区改成和 K线页一样 / the extreme-days page takes any instrument** — 搜索框 +
  一键预设 + 共享收藏，换标的连已取的数一起丢。此前它只能看一份固定名单里的标的。
  A search box, one-tap presets and the shared favourites, replacing a fixed list.
- **十六个页面各有各的图标 / an icon drawn for each of the sixteen pages** — 导航里原先有
  **三对页面共用同一个系统字形**：K线与行业板块竞速（`E9E9`）、成交量换手率与持有胜率（`E9D2`）、
  市场成交额与持仓收益（`E9D9`）。一个形状说不了两个页面，而 Segoe Fluent Icons 里能用的字形
  就那么多，页面长大了装不下。现在十六幅都是画出来的：20×20 网格上的描边骨架（线、圆环、折线、
  箭头）由 shapely 外扩求并成填充几何，落在 `Themes/Icons.xaml`，跟随深浅主题变色，包里不加
  任何位图。每幅图都带两个定位点把包围盒钉成 `[2,18]²`——`PathIcon` 按包围盒等比缩放，没有它们
  宽扁的会被撑高、瘦高的会被压扁。帮助与设置保留系统字形：问号和齿轮是这套菜单里唯一从来没有
  歧义的两个。
  Three pairs of pages had been sharing one system glyph: Candles with Sector Race (`E9E9`),
  Volume & Turnover with Hold Odds (`E9D2`), Market Turnover with Position Replay (`E9D9`). One
  shape cannot mean two pages, and there are only so many usable glyphs in Segoe Fluent Icons.
  All sixteen are drawn instead: a stroke skeleton on a 20×20 grid — lines, rings, polylines,
  arrowheads — expanded and unioned by shapely into the filled geometry a `PathIcon` needs, kept in
  `Themes/Icons.xaml`, taking its colour from the light or dark theme and adding no bitmap to the
  package. Each drawing carries two registration marks that pin its bounding box to `[2,18]²`,
  because `PathIcon` scales by bounding box and, without them, a wide icon is stretched tall and a
  tall one squashed flat. Help and settings keep their glyphs: a question mark and a gear are the
  two shapes in this menu that were never ambiguous.
- **条形榜的行内文字按条形定大小 / a bar board's row text is sized by its own bar** — 市值榜这一页
  的字体比应用里任何一页都小，而且不是风格问题：行文字按**行距**算（`min(30, 行距 × 0.34)`），
  行数越多字越小，而市值榜是全应用行数最多的榜。十五行算出来 27，**够不到那个 30 的上限** ——
  应用里每一块榜都长在上限上，只有最需要空间的这一块没有；预览约按三分之一缩放，27 落在屏幕上
  是 8 像素高的字，汉字在 8 像素上没有笔画可放。现在按**它自己那条条形**算（`min(36, 条形高 ×
  0.72)`）：行距管的是两行隔多远，条形管的是每行多高，而文字是画在条形上或紧贴条形画的。名字栏
  同步从 150 宽到 176，否则最长的那家（伯克希尔B）在更大的字号上装不下，而渲染器的做法是**缩
  整列**——两个字的名字跟着一起缩。条内标注的墨色也改成从条形自己的颜色挑：白的在深色那一半
  是对的，在浅色那一半读不出来（白字压在黄色条上是 2.1:1，而大字的底线是 3:1）。涨跌着色的
  榜不跟着换 —— 那里的颜色就是意思，同尺寸的一涨一跌写两种墨色会读成两种标注。
  名字能用的宽度也随之改成**画面左边到绘图区**，不再只是那条 176 的栏：名字右对齐贴着条形，
  条形榜左边又没有 Y 轴，那条边距本来就是空的。只给栏宽时，港股榜最长的名字（中国石油化工股份，
  八个字）要 261 基线像素而栏里只有 152，于是**整列被压到 19** —— 连腾讯控股和美团一起 ——
  只为让一个名字留在一条它不必留在里面的带子里。最后，行名字一律改成**亮白**（此前只有夺冠
  那一行是白的，其余是淡蓝 `#C9D8F5`，在预览的三分之一缩放下读成灰）：冠军行另有光晕，不靠
  墨色。市场成交额页是时间轴柱状图、没有行名字，那边贴在柱子上的极值标注同样改成亮白，颜色
  留在外框上 —— 最高与最低本就写着字。**回撤与修复页**（名字栏与条形榜是同一个元素，而它的
  行数由自选清单决定）三条规则一并生效：它是旧规则的原样副本，十六个持仓的清单只问到 22 字号，
  而三个持仓的清单问 50 拿 30 —— 同一批标的、两张清单、两种字号。
  The market-cap board's type was the smallest in the app, and not by taste: row text was measured
  against the **row pitch** (`min(30, pitch × 0.34)`), so it shrank as rows were added, and this is
  the densest board in the app. Fifteen rows asked for 27 and got 27 — every other board reaches the
  cap, and the one with the most to fit is the one that did not. On the preview, drawn at about a
  third of the frame, 27 baseline pixels is a glyph eight screen pixels tall, and a CJK character has
  no strokes left at eight pixels. It is measured against **its own bar** now (`min(36, bar ×
  0.72)`): the pitch says how far apart two rows are, the bar says how tall each one is drawn, and
  the text sits on the bar. The name column went from 150 to 176 with it — at the larger size the
  longest name (伯克希尔B) no longer fits, and what the renderer does when a name does not fit is
  shrink the *whole column*, two-character names included. The ink inside a bar now comes from that
  bar's own colour: white is right on the dark half of the palette and unreadable on the light half —
  white on the amber is 2.1:1, where large text needs 3:1. A sign-coloured board keeps white for both
  signs, because there the colours are the meaning. A name may now use everything between the frame's
  edge and the plot, not only the 176-pixel gutter: names are right-aligned against the plot and a
  bar race has no Y axis, so that margin holds nothing. Against the gutter alone, Hong Kong's longest
  name (中国石油化工股份, eight characters) asked for 261 baseline pixels and the gutter held 152, so
  the fit shrank the column to 19 — every row, 腾讯控股 included — for the sake of one name. Finally,
  row names are **white** for every row rather than only the champion's: the others were pale blue
  (`#C9D8F5`), which reads as grey at the preview's scale, and the champion is already marked by its
  glow. The market-turnover page is a column chart along a time axis and has no row names; there the
  extreme callout on a bar is white too, with the colour kept on the box — the words 最高 and 最低
  are the label. The drawdown page carries the same name column as the ranking boards and its row
  count is set by the user's own list, so all three rules apply there as well — it was a verbatim
  copy of the old rules, and sixteen holdings asked for 22 while three asked for 50 and got 30: the
  same instruments at two different sizes.
- **四页的区间按接口实测重定 / four range menus, re-cut against what the endpoints return** —
  实测发现 `count` 是**根数不是天数**，源端从结束日往回数、忽略起始日：要 365 天回 365 根、要 640
  回 640、要 1825 仍然只有 640 根。所以超长区间丢的是**头部**，回来的图短一截却完全正常——这正是
  区间最不该给出的答案。据此：K线日线加了 **5 年与 10 年**两档（日线走分页，6 × 640 = 3840 根，
  约 15 年；实测十年是 2462 根）；成交量换手率与行业板块竞速加了 **24 个月**一档，自定义区间的
  上限从 640 天改到 **900 天**（旧阈值会把源端答得出来的两年拦下），日期选择器同步收窄；市值榜
  加了「**最长**」与「**自定义**」，它的天花板是月线自己的 180 个月，而不是按日线算出来的三十五年。
  新增 `TencentKline.MostDaysPerRequest = 900`（天），与既有的 `MostBarsPerRequest = 640`（根）
  分开——拿根数去挡天数会拦下源端答得出来的区间。
  Measured: `count` is a number of **bars**, not of days, and the source counts backwards from the
  end date, ignoring the start — ask for 365 days and 365 bars come back, ask for 640 and 640 come
  back, ask for 1825 and it is still 640. So a span past the ceiling loses its **head**, and a
  chart with its first years missing is a shorter chart that looks entirely correct, which is the
  one answer a span must not give. Accordingly: daily candles gained **5 and 10 years** (daily
  pages backwards, 6 × 640 = 3840 bars, about fifteen years; ten years measured at 2,462 bars);
  Volume & Turnover and Sector Race gained **24 months**, and the ceiling on a custom span went
  from 640 to **900 days** — the old one refused two years the source answers happily — with the
  date pickers narrowed to match; Market Cap Race gained **Longest** and **Custom**, its ceiling
  being the monthly series' own 180 periods rather than the thirty-five years a daily walk would
  suggest. `TencentKline.MostDaysPerRequest = 900` (days) now sits beside `MostBarsPerRequest =
  640` (bars): using a bar count to police a number of days refuses spans the source will answer.
  **三对页面共用同一个系统字形**：K线与行业板块竞速（`E9E9`）、成交量换手率与持有胜率（`E9D2`）、
  市场成交额与持仓收益（`E9D9`）。一个形状说不了两个页面，而 Segoe Fluent Icons 里能用的字形
  就那么多，页面长大了装不下。现在十六幅都是画出来的：20×20 网格上的描边骨架（线、圆环、折线、
  箭头）由 shapely 外扩求并成填充几何，落在 `Themes/Icons.xaml`，跟随深浅主题变色，包里不加
  任何位图。每幅图都带两个定位点把包围盒钉成 `[2,18]²`——`PathIcon` 按包围盒等比缩放，没有它们
  宽扁的会被撑高、瘦高的会被压扁。帮助与设置保留系统字形：问号和齿轮是这套菜单里唯一从来没有
  歧义的两个。
  Three pairs of pages had been sharing one system glyph: Candles with Sector Race (`E9E9`),
  Volume & Turnover with Hold Odds (`E9D2`), Market Turnover with Position Replay (`E9D9`). One
  shape cannot mean two pages, and there are only so many usable glyphs in Segoe Fluent Icons.
  All sixteen are drawn instead: a stroke skeleton on a 20×20 grid — lines, rings, polylines,
  arrowheads — expanded and unioned by shapely into the filled geometry a `PathIcon` needs, kept in
  `Themes/Icons.xaml`, taking its colour from the light or dark theme and adding no bitmap to the
  package. Each drawing carries two registration marks that pin its bounding box to `[2,18]²`,
  because `PathIcon` scales by bounding box and, without them, a wide icon is stretched tall and a
  tall one squashed flat. Help and settings keep their glyphs: a question mark and a gear are the
  two shapes in this menu that were never ambiguous.
- **四页的区间按接口实测重定 / four range menus, re-cut against what the endpoints return** —
  实测发现 `count` 是**根数不是天数**，源端从结束日往回数、忽略起始日：要 365 天回 365 根、要 640
  回 640、要 1825 仍然只有 640 根。所以超长区间丢的是**头部**，回来的图短一截却完全正常——这正是
  区间最不该给出的答案。据此：K线日线加了 **5 年与 10 年**两档（日线走分页，6 × 640 = 3840 根，
  约 15 年；实测十年是 2462 根）；成交量换手率与行业板块竞速加了 **24 个月**一档，自定义区间的
  上限从 640 天改到 **900 天**（旧阈值会把源端答得出来的两年拦下），日期选择器同步收窄；市值榜
  加了「**最长**」与「**自定义**」，它的天花板是月线自己的 180 个月，而不是按日线算出来的三十五年。
  新增 `TencentKline.MostDaysPerRequest = 900`（天），与既有的 `MostBarsPerRequest = 640`（根）
  分开——拿根数去挡天数会拦下源端答得出来的区间。
  Measured: `count` is a number of **bars**, not of days, and the source counts backwards from the
  end date, ignoring the start — ask for 365 days and 365 bars come back, ask for 640 and 640 come
  back, ask for 1825 and it is still 640. So a span past the ceiling loses its **head**, and a
  chart with its first years missing is a shorter chart that looks entirely correct, which is the
  one answer a span must not give. Accordingly: daily candles gained **5 and 10 years** (daily
  pages backwards, 6 × 640 = 3840 bars, about fifteen years; ten years measured at 2,462 bars);
  Volume & Turnover and Sector Race gained **24 months**, and the ceiling on a custom span went
  from 640 to **900 days** — the old one refused two years the source answers happily — with the
  date pickers narrowed to match; Market Cap Race gained **Longest** and **Custom**, its ceiling
  being the monthly series' own 180 periods rather than the thirty-five years a daily walk would
  suggest. `TencentKline.MostDaysPerRequest = 900` (days) now sits beside `MostBarsPerRequest =
  640` (bars): using a bar count to police a number of days refuses spans the source will answer.

### 改进 / Changed

- **帮助手册 14 份补上了本版的口径 / the manual now says what the menus do** — K线、成交量换手率、
  市值榜三章各多一句本页的档位；「数据，以及它不会告诉你的事」里那条「超过约 640 个自然日会被
  拒绝」改成按页分档的说法，并写明为什么不能悄悄截断。改动由 `tools/port-help-ranges.py` 按
  **章节位置**注入（14 种语言里"第 N 章的最后一条 bullet"都是同一处，而按句子匹配要写 14 份正则）。
  The Candles, Volume and Market Cap chapters each gained a line about that page's entries, and the
  "longer than about 640 calendar days is refused" line in the data chapter now states the ceiling
  per page and why nothing is quietly truncated. `tools/port-help-ranges.py` injects them by
  **chapter position** — "the last bullet of chapter N" is the same place in all fourteen
  languages, where matching a sentence means fourteen patterns.
- **商店文案从十页补到十六页 / the store listing stopped saying ten pages** — 说明段还写着「十大
  图表页」，而后加的六页（极端交易日、汇率走廊、指数长跑、大类资产、回撤与修复、持有胜率）从来
  没进过商店文案。现在补上了，描述**取自各语言帮助手册那一章的首句**（那是项目自己翻的、与界面
  一致的说法），页面名取自 resw，破折号抄这一段自己已有的那一条（德语那段用的是短破折号）。
  十四条「此版本的新增功能」改写为本版内容——它们此前还在一页一页地数「新增第八个图表页」，与
  「十六大图表页」并排是自相矛盾的；历史留在 CHANGELOG 里。
  The description still said "Ten chart pages" while the six pages added since — extreme days,
  currency corridors, index race, asset classes, drawdowns, hold odds — had never made it into the
  copy. They are in now, each described by **the first sentence of that chapter in the same
  language's manual** (the project's own translation, the same words the UI uses), named from resw,
  and dashed with whatever that section already uses (the German one writes an en dash). The
  fourteen "What's new" lines were rewritten for this version: they were still counting "an eighth
  chart page", which contradicts "Sixteen chart pages" sitting above it. The history lives here.

### 修复 / Fixed

- **十四份资源里那句方法说明说反过话 / the method note in fourteen resource files said the
  opposite of what the code does** — 指数长跑那一句写着「月线，不调整」（英文 "Monthly bars,
  unadjusted"），而代码早已改成走复权序列。页面上的这一行文字没有 UIA 节点（它画在预览面上），
  所以改口径那次没有脚本能拦住它：数字全对、画面全对、状态行全对，只有那句说明在说反话。
  `tools/port-indexrace-adjnote.py` 改掉 14 份，`verify-indexrace.py` 补了三条断言 —— 页面挂着
  那句说明、14 份都不含各自语言的「不调整」、英文那句含 adjusted 且写明价格回报与总回报之别。
  The index race said "Monthly bars, unadjusted" while the code had already moved to the adjusted
  series. That line is drawn on the preview surface and has no automation node, so when the basis
  changed nothing could catch it: the numbers were right, the frame was right, the status line was
  right, and the sentence that describes the method said the reverse.

### 已知限制 / Known limits（沿用 1.0.3.0，除下一条 / unchanged from 1.0.3.0 except the last）

- 图标只换在导航里：设置与帮助仍是系统字形（问号与齿轮），工具条上的字形也没有重画。
  The new icons are in the navigation only; Settings and Help keep their glyphs, and the toolbar's
  glyphs were not redrawn.
- 成交量换手率与行业板块竞速的日线区间上限仍是约 900 个自然日，一次请求的天花板就到那里。
  The daily ceiling on Volume & Turnover and Sector Race is still about 900 calendar days, which is
  where one request stops.
- 美股没有日内模式（那个分时端点的 `data` 是 list 不是 object），日内只有最近几个交易日可选。
  There is no intraday mode on the United States (that endpoint returns a list, not an object), and
  intraday offers only the last few trading days.
- 一块榜上的行内文字是**一个字号**：整块榜算一次，行与行不会各自缩放（逐行缩放看起来像一封剪贴
  信，不像一份清单）。所以一块榜里最矮的那一行字体最小。
  The row text on a board is **one size**: computed once for the board, never scaled per row — rows
  scaled individually read as a ransom note rather than as a list. The shortest row on a board
  therefore carries the smallest type.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份改成**新页面优先**
的内容：第九到第十六页八个新页面逐条列出，共享自选、自绘图标、四页区间各一句带过（那一栏有
1500 字符的上限，八个页面用德/法/意语写就已经顶到一千二）。同一份文件里「说明」的图表页数与
「产品功能」的图表条数从十改成十六，说明段补上六条。三处各由一个脚本按语言改
（`tools/port-store-listing-pages.py`、`tools/port-store-listing-whatsnew.py`），幂等，且按整行精确
匹配——某语言的措辞与脚本里的不一致时会报错而不是留下一个旧数字。这两个文件都是 CRLF，脚本读写
都保持原样。
The fourteen "What's new" lines lead with the **new pages**: the eight that arrived between the
ninth and the sixteenth, with the shared watchlist, the drawn icons and the four range menus in a
sentence each — the field is capped at 1,500 characters, and eight pages already run past 1,200 in
German, French and Italian. The description's page count and the features bullet went from ten to
sixteen, with six entries added to the list. A script per edit does it per language
(`tools/port-store-listing-pages.py`, `tools/port-store-listing-whatsnew.py`), idempotent and
matching whole lines, so a language whose wording differs fails loudly instead of keeping a stale
number. Both files are CRLF and the scripts keep them that way.

---

## 1.0.3.0 — 2026-10-01（更新版 / update）

**1.0.2.0 那一版只构建成包、从未上传商店**，所以它写下的内容（页面导航、三个市场的复权口径等）
是随本版一起到达用户的。下面只列本版在 1.0.2.0 之上新增的改动。应用的完整能力仍见下面的
0.0.0.0 条目。
Version 1.0.2.0 was built but never uploaded, so what its entry describes — page navigation, the
adjustment basis across the three markets — reaches users as part of this one. What follows is only
what this version adds on top of it. The full feature set is still in the 0.0.0.0 entry below.

### 新增 / Added

- **第八页：K线走势 / an eighth page: Candles** — 一只标的的价格画成 K 线，日线 / 周线 / 月线
  任选，四种画法（蜡烛、美国线、收盘线、面积），带 MA5/10/20 均线与成交量副图；区间的涨跌幅和
  最高、最低点标在画面上。动画有两种且可切换：**逐根生长**——从区间第一根长到最后一根；
  **固定窗口滚动**——窗口宽度固定，画面带着一段行情向前走。指数、个股、ETF 都能画，三个市场
  都支持。它在导航里排在「市场成交额」正下方，与帮助手册里的顺序一致。
  One instrument's prices as candles, daily, weekly or monthly, drawn four ways — candles, OHLC
  bars, a closing line, a closing area — with MA5/10/20 averages and a volume panel beneath, the
  range's return and its high and low marked on the frame. Two animations, switchable: **growing**,
  one candle at a time from the range's first to its last, and **scrolling**, a fixed-width window
  walking forward through the range. Indices, stocks and ETFs all draw, on all three markets. It
  sits directly under Market Turnover in the navigation, which is where the manual puts it.
- **自定义数据区间 / a custom span, on three pages** — K线走势、定投计划、持仓收益的区间下拉
  都多了一档「自定义」：选它就露出起始日期与结束日期两个框，取回来的就是这两个日期之间的行情。
  此前定投与持仓只能选区间长度（3 / 5 / 10 年 / 最长），K线页则完全没有这一档。两个日期的可选
  范围不是随手定的：这三个页面都要把日线一段一段往回翻，一页约 640 个自然日，能翻多少次是定
  死的，所以日期框的上限就钉在那条线上（K线页约 10 年，定投与持仓约 35 年）。超出上限会在发
  请求之前就拒绝——再往前，回溯会在走到你要的起点之前先用完请求次数，序列会悄悄从更晚的一天
  开始，而填两个日期的全部意义就是那天是那天。起始日期晚于结束日期同样在发请求前拒绝：否则源
  端只会含糊地说「天数太少」，而画面里上一次那条曲线还站在两个它从没走过的日期底下。
  Candles, the DCA plan and the position replay each gained a **Custom** entry in their range
  dropdown: pick it and two date boxes appear, a start and an end, and the fetch returns exactly
  what lies between them. The plan and the position could only take a length before — three, five
  or ten years, or as far back as there is — and the candle page had no such entry at all. The
  range the boxes offer is not arbitrary: all three pages walk daily bars backwards a page at a
  time, about 640 calendar days to a page, with a fixed ceiling on requests, so the boxes stop
  where the walk stops (roughly ten years on the candle page, thirty-five on the other two). Asking
  for more is refused before any request goes out — past that line the walk runs out of requests
  before it reaches the day you asked for, and the series quietly starts later, while the whole
  point of typing two dates is that the day is the day. A start later than the end is refused for
  the same reason: otherwise the source answers something vague about too few days, and the
  previous curve is left standing under two dates it never visited.

### 改进 / Changed

- **动画背景的颜色档有了不透明度 / an opacity for a colour backdrop** — 选「颜色」时两个色标
  下面多一条滑条（20–100，默认 100）：100% 就是所选的两个颜色本身，往低调会从底下透出这一页
  原本的深色渐变。方向故意与图片档那条相反：图片带着自己的配色来，需要被压回去（浓度越高越接近
  默认底）；颜色是你选的，要决定的是用多少。两条各自只在自己的类型下出现。
  A colour backdrop gained a slider under its two swatches, 20–100 with 100 the default: at 100 the
  frame is the two colours you picked, and turning it down lets the page's own dark gradient show
  through from beneath. Deliberately the opposite direction from the picture's slider — a picture
  arrives with its own colouring and has to be pushed back, while a colour is yours and the question
  is how much of it to use. Each appears only under its own kind.
- **颜色改动在设置页就有回应 / a colour change answers on the page it was made** — 两个取色器下面
  多了一条 40 像素的渐变条，画的就是这一页会被填成的样子（底＝默认渐变，上＝所选色按不透明度），
  改颜色或拖滑条时它跟着变。此前唯一的反馈是下拉里那个 18 像素的色块，而画面在另一个页面上，
  于是「刚才那一下有没有生效」在选颜色的那一页上没有答案。
  A forty-pixel bar under the two pickers draws what the frame will be filled with — the page's
  default gradient beneath, the chosen colours over it at their opacity — and follows both the
  colours and the slider. The only feedback before was an eighteen-pixel swatch in each dropdown,
  with the frame itself on another page, so "did that do anything" had no answer where the colour
  was chosen.
- **上边距的最小值从 230 放宽到 40 / the top margin's floor is 40 now** — 默认仍是 230（手机
  状态栏遮住的那 0.12 帧高就是 230 基线像素，低于它标题会被压到状态栏底下），但最小值此前也是
  230，等于这个滑块只能往上、不能往下。现在可以收到 40。
  The default is still 230 — the 0.12 of the frame a phone's own interface covers, below which a
  top margin can only slide the title under the status bar — but the minimum was 230 too, so the
  slider could only ever go up. It now goes down to 40.

### 修复 / Fixed

- **K线表头的四价行压住了日期行 / the candle header's quote row sat on its date** — 表头四行
  （标题、副标题、日期、开高低收）里，四价那一行还硬写着上一版留下来的一个裸数字，加上大数字的
  发光会向外糊约 25 像素，压到了下面一行。四行现在是命名常量，按发光半径重排。
  Of the header's four rows — title, subtitle, date, open/high/low/close — the quote row still
  carried a bare number left over from an earlier pass, and the glow behind the large figures
  blurs about twenty-five pixels outward, so it sat on the row beneath. The four rows are named
  constants now, spaced with the glow's radius in mind.
- **日期行没有落在两行中间 / the date was not centred between its neighbours** — 按基线取中点仍
  差 4 像素：中文副标题挂在基线下方 4 像素，四价行的中文标签又有 22 像素高。居中现在按**墨迹**
  算而不是按基线，实测上下间隙各 42.2 像素。成交额、定投、持仓三页的同一行同此改法。
  Taking the midpoint of the two baselines was still four pixels out: a CJK subtitle hangs four
  pixels below its baseline and the quote row's CJK labels are twenty-two tall. Centring is
  measured on the ink now rather than on the baseline — 42.2 pixels of clear space above and below.
  The same row on the turnover, plan and position pages was corrected the same way.
- **美股代码大小写导致取不到数据，标题还写错 / a US code in the wrong case fetched nothing, and
  the title was wrong** — 搜索端点返回小写 `usaapl.oq`，而 K 线端点只认 `usAAPL.OQ`，对小写返回
  **空数据而不是报错**，看起来像一只没有历史的标的；标题则直接把代码大写印成 `USAAPL`。代码现在
  在第一次拿到时就按市场规范化，画面上的名字用端点随行情一起返回的那个。
  The search endpoint answers in lower case (`usaapl.oq`) while the candle endpoint will only read
  `usAAPL.OQ` — and answers a lower-case code with *no data* rather than an error, which reads as an
  instrument with no history. The title printed the code upper-cased as `USAAPL`. A code is
  canonicalised for its market as soon as it is known, and the name the frame shows is the one the
  endpoint returns alongside the series.

### 已知限制 / Known limits（沿用 1.0.2.0，本版未变 / unchanged from 1.0.2.0）

- 导出规格为 720×1280 / 1080×1920 / 1440×2560 三种尺寸 × 30 / 60 fps。1440p60 长片有过一次
  卡在第 3,200 帧、文件被截断的情况，未复现也未定位原因。
  Export offers three sizes × 30/60 fps; one 1440p60 run stalled at frame 3,200 and left a
  truncated file — not reproduced, cause unknown.
- 动画背景是全局一份，不能按页面分别设置；也没有纯单色模式与多图轮播。
  The frame backdrop is one global setting, not per page; there is no single-colour mode and no
  slideshow of several pictures.
- 商店截图仍是七个页面，K线走势页的截图尚未拍摄。
  The Store screenshots still show seven pages; the candle page has not been captured yet.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为**只写
本次改动**：K线走势页、三页的自定义区间、颜色档的不透明度、上边距放宽，以及两处修复。同一份文件
里「说明」的图表页数与「产品功能」的图表条数也跟着从七改成八。
之前这些改动是手写到 14 份里的，本版起由一个脚本（`tools/port-store-listing.py`）按语言改，
幂等，且每处都按整行精确匹配——某语言的措辞与脚本里的不一致时会报错而不是留下一个旧数字。
The fourteen "What's new in this version" lines now describe only this release: the candle page,
the custom span on three pages, opacity for a colour backdrop, the relaxed top margin, and two
fixes. The description's page count and the features bullet in the same file moved from seven to
eight. These edits used to be made by hand in fourteen places; from this version a script does it
(`tools/port-store-listing.py`), idempotent and matching whole lines, so a language whose wording
differs fails loudly instead of keeping a stale number.

---

## 1.0.2.0 — 2026-10-01（更新版 / update）

**本版只构建成包、未上传商店；内容随 1.0.3.0 一起发布。**
Built but never uploaded; its contents shipped with 1.0.3.0.

**1.0.1.0 之后的第一版更新，下面只列本次改动。** 应用的完整能力见下面的 0.0.0.0 条目——
那一版已发布，这里不重复。
The first update after 1.0.1.0; only the changes are listed. See the 0.0.0.0 entry below for the
full feature set — that version is published and is not repeated here.

### 新增 / Added

- **页面导航：标题栏加了后退与前进 / Back and Forward in the title bar** — 两个按钮按浏览器
  的方式来走访问过的页面：一条后退栈、一条前进栈，打开新页面会清掉前进栈，最多记 50 条。
  Alt+← / Alt+→ 与鼠标侧键同样有效；后退时页面从左滑入，前进时从右。导航窗格收起时它们
  照样可用——9:16 的预览要和参数面板抢宽度，窗格折叠起来的时候，这是回到刚才那一页最快
  的路。
  Two buttons in the title bar walk the pages you have visited the way a browser does: a back
  stack and a forward stack, a new visit clearing the forward stack, fifty entries at most.
  Alt+Left, Alt+Right and the side buttons on a mouse do the same, and the transition knows the
  direction — a step back slides the page in from the left, a step forward from the right. They
  are there with the navigation pane collapsed too: the 9:16 preview competes with the parameter
  panel for width, and once the pane is folded away this is the quickest way back to the page
  you were on.

### 修复 / Fixed

- **港股与美股的价格没有复权 / Hong Kong and US prices were unadjusted** — 定投计划与持仓
  收益要的是「任意两天之比就是持有者真实赚到的」那种价格，也就是复权价，而行情源只在 A 股
  上直接给得出。港股与美股拿到的是不复权的收盘价，于是拆股那一天成了一次凭空的暴跌：腾讯
  控股 2014-05-15 一拆五，图上是从 514 跌到 108.8，一夜 −78.83%；苹果 2020-08-31 一拆四，
  −74.15%。分红同样没有算进去——除息那天的下跌留在了曲线上，而那份现金没有回到持有者手里。
  现在这两个市场各走自己的复权端点：港股用 `hkfqkline` 的后复权，美股用 `usfqkline` 的前
  复权（前复权与后复权只差一个贯穿全序列的常数因子，在「份额 = 金额 ÷ 价」「市值 = 份额 ×
  价」里正好抵消）。十三年的月度定投，苹果从 +99.7% 回到 +576.4%，特斯拉从 +24.2% 回到
  +1061.2%，腾讯从 +48.2% 回到 +82.3%。指数与从未分派过的信托仍然用不复权的行——它们本来
  就没有可复权的东西。
  The plan and the position need a price whose ratio between any two days is what a holder
  actually earned, which is to say an adjusted one — and the source only serves that directly for
  an A-share. Hong Kong and US codes came back unadjusted, so a split arrived as a collapse out of
  nowhere: 腾讯控股's one-for-five on 2014-05-15 read as a close of 514.0 falling to 108.8
  overnight, minus 78.83 per cent, and Apple's four-for-one on 2020-08-31 as minus 74.15.
  Dividends were missing too — the drop on the ex-date stayed on the curve while the cash it paid
  out never came back to the holder. Each venue now goes to the endpoint that carries its adjusted
  rows: `hkfqkline` for Hong Kong, `usfqkline` for the United States, whose only adjusted series
  is the forward-adjusted one. Forward and backward differ by a single constant factor over the
  whole series, and that factor cancels in everything these pages derive — a buy is
  `amount / price` and a marking is `shares × price`. Over thirteen years of monthly
  buying, Apple goes from +99.7% to +576.4%, Tesla from +24.2% to +1061.2%, Tencent from +48.2%
  to +82.3%. Indices and trusts that have never distributed still read their unadjusted rows,
  having nothing to adjust for.

- **其余页面的价格也没有复权 / every other page was unadjusted too** — 上一轮只把定投与
  持仓这两个「按价买入」的页面换到了各市场自己的复权端点，其余页面仍留在通用端点的前复权
  上。而通用端点对港股和美股根本不给复权序列，对 A 股的高分红股给的是**负数**收盘价——
  贵州茅台 2010-09 至 2015-12 的月线，1280 根里有 1280 根是负的。于是：
  - 收益矩阵：收盘价非正数被当作无效值丢掉，茅台静默少了 7 个月、五粮液少 6 个月，剩下的
    两个月被当成相邻月算收益；港股与美股则完全没有复权，腾讯 2014-05-15 一拆五在月线上是
    −78.83%，苹果 2020-08-31 一拆四是 −74.15%。
  - 行业板块竞速：美股十只行业 ETF 里 XLK / XLY / XLE / XLB / XLU 在 2025-12-05 各自凭空
    跌掉约一半；自选股里放进高分红股，读到的同样是负价。
  - 涨跌日历：自定义区间拉回几年前时，日涨幅由负价算出。
  现在凡是要画收益的页面一律走总回报序列：A 股 `newfqkline` 的后复权、港股 `hkfqkline`
  的后复权、美股 `usfqkline` 的前复权，月线同样按市场选端点。复权后最差月：茅台从
  −65.99% 回到 −26.23%，苹果从 −69.64% 回到 −18.11%，XLK 从 −49.70% 回到 −11.95%；
  丢月数全部归零。**成交量与换手率那一页刻意留在前复权**——它靠「量 × 价 ≈ 额」判成交量
  的单位是手还是股，换成后复权会把价乘上整个复权因子（伊利股份是 84.5），判成「股」就差
  一百倍。
  The last round moved only the two pages that buy at a price — the plan and the
  position — onto each venue's own adjusted endpoint. Every other page stayed on the
  general endpoint's forward-adjusted series, which for a Hong Kong or US code is not
  adjusted at all and for an A-share heavy payer is *negative*: every one of 贵州茅台's
  1280 monthly closes between 2010-09 and 2015-12 is below zero. So the gain matrix
  dropped those months as invalid — seven of them for 茅台, six for 五粮液 — and read
  the two months either side of the hole as adjacent; Hong Kong and US months were
  wholly unadjusted, 腾讯控股's one-for-five of 2014-05-15 arriving as minus 78.83 per
  cent and Apple's four-for-one as minus 74.15. The sector race showed five of the ten
  US sector ETFs losing roughly half their value on 2025-12-05, and a watchlist holding
  a heavy payer reading negative prices. The gain calendar's daily returns came from
  those same closes once a custom range reached back a few years. Every page that draws
  a return now reads the total-return series: `newfqkline` backward-adjusted for an
  A-share, `hkfqkline` backward-adjusted for Hong Kong, `usfqkline` forward-adjusted for
  the United States, and the monthly request choosing its endpoint the same way. The
  worst month after: 茅台 −65.99% to −26.23%, Apple −69.64% to −18.11%, XLK −49.70% to
  −11.95%; no month dropped anywhere. **The volume page stays forward-adjusted on
  purpose** — it tells a listing's volume unit, lots or shares, from "volume × price ≈
  amount", and the backward-adjusted price is that price times the listing's whole
  adjustment factor, which for 伊利股份 is eighty-four: reading "shares" would put every
  bar a hundredth of what it is.

- **美股复权序列里没有成交额 / the US adjusted series carries no turnover** — 美股的前复权
  每行只有六个字段，到成交量为止，没有成交额也没有换手率。竞速页的成交额榜和涨跌日历的
  合计列会因此全部变成零。这两页现在拿到复权价之后，再向通用端点要一次成交额按日期合并：
  拆股改变的是价格与股数，不改变当天换手的钱，所以未复权那一行里的成交额本来就是对的。
  A US row on the adjusted series carries six fields and stops at the volume: no amount
  and no change rate behind it, which left the race's turnover board and the calendar's
  totals column at zero. Those two pages now ask the general endpoint for the window's
  turnover as well and merge it in by date. A split divides the price and multiplies the
  share count; it does not change the money that changed hands, so the unadjusted row's
  figure was the right one all along.

- **一次网络抖动就把这只票永久降级成不复权 / one dropped request degraded a code for
  good** — 复权端点只要失败一次，这个代码在本轮会话里就改用通用端点的未复权行，而一次
  定投要翻二十页，中间抖一下的概率并不小。现在把两种失败分开：请求压根没到源端（超时、
  连接中断、网关返回一段 HTML 而不是 JSON）最多重试两次再降级；源端明确回答「没有这个
  代码」则立刻降级，问第二遍也不会变。
  One failure on the venue's own endpoint was enough to move a code onto the general
  endpoint's unadjusted rows for the rest of the session, and a plan walks twenty pages,
  so a single blip was not unlikely. Two kinds of failure are told apart now: a request
  that never reached the source — a timeout, a broken connection, a gateway answering
  with HTML instead of JSON — is worth two more attempts, while an answer that says the
  source does not serve this code here is not, and degrades at once.

- **定投计划与持仓收益取不到数 / the plan and position pages failed to fetch** — 这两个页面
  要把十几年的日线一段一段往回翻，最后一段是「区间起点到已拿到的最早一根之前」；区间起点
  如果落在周末或假期（例如「近 5 年」从 2021-10-01 起，紧跟着就是国庆长假），这一小段里
  一根 K 线也没有。行情源按请求的窗口裁剪，于是返回空——而代码把「窗口里没有 K 线」当成
  错误抛了出去，多年数据已经拿到手，整条回溯却倒在了最后一步，页面报出一句英文的
  `no daily bars in that range.`。现在空窗口照空处理，回溯按既定规则停下。任何起点落在
  休市日的区间都会碰到它，一年里大约三分之一的日子。
  Both pages walk years of daily bars back one page at a time, and the last step asks for the
  stretch between the range's start and the earliest bar already held. When the start lands on a
  weekend or a public holiday — "the last five years" from 2026-10-01 starts on 2021-10-01, the
  first day of the National Day week — that stretch holds no bars at all, and the source, which
  clips rows to the window it was asked for, answers with nothing. The code took "no bars in the
  window" for a failure and threw, so a walk that had already gathered years of data died on its
  last step and the page reported `no daily bars in that range.` An empty window is now read as an
  empty window and the walk stops as it was designed to. Any range whose start falls on a day the
  market is shut runs into this — roughly a third of the calendar.

- **画面上写着的是上一个标的的名字 / the frame named the previous instrument** — 在定投计划与
  持仓收益里换标的时，画面标题只在取数成功后才跟着变；取数失败（比如上面那条）就停在旧名字
  上，于是图上写着「沪深300ETF定投计划」而失败信息里的代码是另一个。现在换标的那一刻就重画：
  属于旧标的的曲线一并清掉，标题立刻是新标的的名字。恢复参数时若存的只有代码没有名字，也
  不再回落到本市场的第一个内置标的（那同样是给画面安了一个不存在的名字）。
  On both pages the frame's title only followed a new pick once the fetch succeeded, so a failed
  fetch left the old name standing over the new code — the chart said "沪深300ETF plan" while the
  error named another instrument. The frame is redrawn the moment a pick is made now: the previous
  instrument's series is dropped and the title is the new instrument's. And when a restored
  preference carries a code but no name, the fallback is the code rather than the market's first
  built-in — which was the same defect wearing a friendlier name.

- **行业板块竞速的板块名跟随界面语言 / the race's sector names follow the language** — 内置
  列表（中证一级行业、热门主题板块、恒生分类指数、美股行业 ETF）的板块名用的是行情源自己的
  中文，于是在其他 13 种语言下，一张英文标题、英文副标题的图上，每一行都是中文。这些名字
  现在按代码查界面语言，与自选股的名称走同一条路；查不到的仍回落到源端原名。
  A built-in roster carried the quote source's own Chinese, so in the other thirteen languages a
  chart with an English title and an English caption still had a Chinese word on every row. The
  names are looked up by code now, as watchlist names already were; a code with no entry still
  falls back to the name the source gave.

- **切换市场后竞速列表回来的还是同一份 / the roster comes back as the same list** — 竞速列表
  的选中项此前是按位置记的，而只有一个内置列表的市场菜单更短，同一个位置落到的是另一份列表：
  「自定义板块」重启后会变成「自选股」。现在按标识记，位置上没有对应项时回落到第一个内置
  列表——与取数时已有的回退一致。
  The chosen roster was remembered by position, and a market with one built-in list has a shorter
  menu — the same position pointed at a different list, turning "custom sectors" into "watchlist
  stocks" across a restart. It is remembered by identity now, falling back to the first built-in
  list where the position has no equivalent, as the fetch itself already did.

### 已知限制 / Known limits（沿用 1.0.1.0，本版未变 / unchanged from 1.0.1.0）

- 导出规格为 720×1280 / 1080×1920 / 1440×2560 三种尺寸 × 30 / 60 fps。1440p60 长片有过一次
  卡在第 3,200 帧、文件被截断的情况，未复现也未定位原因。
  Export offers three sizes × 30/60 fps; one 1440p60 run stalled at frame 3,200 and left a
  truncated file — not reproduced, cause unknown.
- 动画背景是全局一份，不能按页面分别设置；也没有纯单色模式与多图轮播。
  The frame backdrop is one global setting, not per page; there is no single-colour mode and no
  slideshow of several pictures.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为**只写
本次改动**：页面导航、板块名跟随语言、取数失败与标题两处修复，以及复权口径（三个市场、全部
画收益的页面）。
The fourteen "What's new in this version" lines now describe only this release: page navigation,
sector names following the language, the fetch failure and the title, and the adjustment basis —
all three markets, every page that draws a return.

---

## 1.0.1.0 — 2026-09-29（更新版 / update）

**1.0.0.0 之后的第一版更新，下面只列本次改动。** 应用的完整能力见下面的 0.0.0.0 条目——
那一版已发布，这里不重复。
The first update after 1.0.0.0; only the changes are listed. See the 0.0.0.0 entry below for the
full feature set — that version is published and is not repeated here.

### 新增 / Added

- **动画背景可自定义 / the animation's backdrop is yours to set** — 设置页新增「动画背景」：
  默认渐变、自选两色渐变、或一张图片（可从电脑选，也可直接用 Windows 自带壁纸，最近 6 张
  留档）。图片按「填满」铺开并裁掉多余部分，压暗浓度 20–95% 可调。它同时作用于预览、导出的
  视频和封面图——三者由同一个渲染器绘制，所以文件里看到的就是预览里看到的。
  A new Settings card decides what every frame is drawn on: the built-in gradient, a two-colour
  gradient of your own, or a picture — from your computer or Windows' own wallpapers, the last six
  kept. Pictures fill the frame and are cropped rather than stretched, dimmed 20–95%. It reaches the
  exported video and the cover image as well as the preview, because one renderer draws all three.

### 改进 / Changed

- **设置页内容居中 / the Settings page is centred** — 那列固定宽度的卡片改为在窗口里居中，
  宽窗口下不再贴着左侧导航栏。
  The column of cards now sits centred in the window instead of against the navigation pane.
- **帮助手册新增「动画背景」一节 / the manual documents the new backdrop** — 14 份手册各加
  一章（现为 15 章），讲清三种背景、图片的铺法与浓度范围。
  All fourteen manuals gained a chapter on it (now fifteen); the chapter count is checked by the
  injection script, the way the resource keys are.

### 已知限制 / Known limits（沿用，本版未变 / unchanged）

- 导出规格为 720×1280 / 1080×1920 / 1440×2560 三种尺寸 × 30 / 60 fps。1440p60 长片有过一次
  卡在第 3,200 帧、文件被截断的情况，未复现也未定位原因。
  Export offers three sizes × 30/60 fps; one 1440p60 run stalled at frame 3,200 and left a
  truncated file — not reproduced, cause unknown.
- 美股日线未做拆股调整，长区间曲线在拆股处会出现断崖。
  US daily bars are not split-adjusted; a long range shows a cliff at a split.
- 动画背景是全局一份，不能按页面分别设置；也没有纯单色模式与多图轮播。
  The frame backdrop is one global setting, not per page; there is no single-colour mode and no
  slideshow of several pictures.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为**只写
本次改动**：动画背景可自定义。
The fourteen "What's new in this version" lines now describe only this change: the custom
animation backdrop.

---

## 1.0.0.0 — 2026-09-28（更新版 / update）

**这是商店中 0.0.0.0 之后的第一版更新，下面只列本次改动。** 应用的完整能力见下面的
0.0.0.0 条目——那一版已经发布，这里不重复。
The first update after 0.0.0.0 in the Store; only the changes are listed. See the 0.0.0.0 entry
below for the full feature set — that version is already published and is not repeated here.

### 新增 / Added

- **窗口背景图片 / window background image** — 可任选一张图片作为窗口背景，遮罩浓度
  30–95% 可调，最近 6 张留档；高对比度主题下自动不显示。
  Pick an image as the window background, dim it 30–95%, keep the last six. Suppressed
  automatically under a high-contrast theme.
- **商店更新检查 / Store update check** — 商店有新版本时，导航栏「设置」右侧出现
  「更新」按钮；静默安装或经商店弹窗安装，装完自动重启应用。
  When the Store has a newer version, an Update button appears beside Settings: silent where
  the Store allows it, otherwise through the Store's own prompt, then the app restarts.
- **帮助文档配图 / pictures in the help document** — 14 份手册各配 5 张本语言的页面截图，
  图文相间；截图按语言取，日文手册配日文窗口。
  Each of the fourteen manuals carries five pictures of its own language — a Japanese manual
  shows a Japanese window.
- **标的显示名本地化 / instrument names follow the interface language** — 80 个常用标的的
  显示名随界面语言走（请求仍用代码，不变）。
  Eighty common instruments are named in the interface language; requests still go by code.

### 改进 / Changed

- **应用名随系统显示语言 / the app name follows the OS display language** — 开始菜单、
  应用列表与系统设置里显示的是**产品名**：中文系统显示「行情指标动画工作室」，其余显示
  Market Motion Studio。此前这三处都写死为包标识 `MarketMotionStudio`——那是标识符，
  不是产品名，任何语言下都长这样。未提供的语言回退英文。
  Start menu, Apps list and Settings now show the **product name** in the OS display language;
  all three previously carried the package identity, which is an identifier rather than a
  product name and reads the same in every language. Unlisted languages fall back to English.

### 已知限制 / Known limits（沿用 0.0.0.0，本版未变 / unchanged from 0.0.0.0）

- 导出规格为 720×1280 / 1080×1920 / 1440×2560 三种尺寸 × 30 / 60 fps。六档都出过片，
  但 1440p60 长片（5,400 帧）有一次卡在第 3,200 帧、文件被截断，未复现也未定位原因。
  Export offers three sizes × 30/60 fps. All six have produced a file; one 1440p60 run of
  5,400 frames stalled at frame 3,200 and left a truncated file — not reproduced, cause unknown.
- 美股日线未做拆股调整，长区间曲线在拆股处会出现断崖。
  US daily bars are not split-adjusted; a long range shows a cliff at a split.
- 港美股没有全市场成交额口径，市场成交额页在这两个市场下不存在。
  Hong Kong and US have no whole-market turnover figure, so that page is absent there.
- 定投计划与持仓收益页只能选区间长度，不能指定精确起始日期。
  The DCA and position pages take a range length, not an exact start date.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为
**只写本次改动**（此前误写成「首个发布版本」+ 全部能力，那是已发布的 0.0.0.0 的内容）。
原缺的意大利语整节已补齐，法语功能列表被截成 `- c` 的那一条已修复。
这份文案原本放在 `artifacts/`，而该目录在 `.gitignore` 里——等于没有备份；现已挪到
`docs/store-listing.md` 纳入版本控制。

---

## 0.0.0.0 — 2026-09-27（首个上架版本，已发布 / first published version）

**已发布上线，用户现在装得到的就是这一版。**
Published and live — this is the version users have.

### 新增 / Added

- **七个图表页 / seven chart pages** — 市场成交额、成交量与换手率、行业板块竞速、
  收益矩阵、涨跌日历、定投计划、持仓收益。
  Market turnover, volume & turnover rate, sector race, return matrix, up/down calendar,
  DCA plan, position replay.
- **三个市场 / three markets** — A股、港股、美股；在设置里切换，重启后生效。
  A-share, Hong Kong and US, switched in Settings; the change takes effect after a restart.
- **14 种界面语言 / 14 interface languages** — en-US、de、es、fr、it、pl、pt-BR、cs、tr、
  ru、ja、ko、zh-Hans、zh-Hant。帮助手册同样 14 份。
- **导出 / export** — 9:16 竖屏 H.264 MP4，三种尺寸（720×1280 / 1080×1920 / 1440×2560）
  × 30 / 60 fps，外加同帧封面 PNG；预览与编码器共用同一渲染器，所以导出的每一帧都等于
  预览看到的那一帧。
  9:16 vertical H.264 MP4 in three sizes (720×1280 / 1080×1920 / 1440×2560) at 30 or 60 fps,
  plus a cover PNG of the same frame. Preview and encoder share one renderer, so every exported
  frame is the frame the preview showed.

### 关于这个版本号 / About this number

0.0.0.0 是 09-26 上传 `0.2.0.1` 被拒之后改出来的：那条报错的真实含义是**第四位必须为 0**，
当时被误读成「必须全零」。它侥幸通过了校验，但违反「第一段不能为 0」，而且没有上升空间——
更新必须高于已发布版本。所以下一版直接跳到 `1.0.0.0`（1.0.0.0 > 0.0.0.0，用户能收到更新）。
0.0.0.0 came from misreading the rejection of 0.2.0.1 on 09-26: the error meant *the fourth
section must be 0*, not *all four must be 0*. It passed validation by luck, breaks the
"first section cannot be 0" rule, and has nowhere to go — an update must be higher. Hence
1.0.0.0, which is higher and will reach users.

---

## 模板 / Template for the next version

```
## X.Y.Z.0 — 日期 / date

### 新增 / Added
- 功能名 / Feature name — 一句话说明 / one line.

### 改进 / Changed
- 改了什么、为什么 / what changed and why.

### 修复 / Fixed
- 修了什么、原来什么症状 / what was wrong and how it showed.

### 商店文案同步 / Store listing
- docs/store-listing.md：14 份「此版本的新增功能」已更新到本版。
```
