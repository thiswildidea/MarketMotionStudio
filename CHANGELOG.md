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

## 1.0.2.0 — 2026-10-01（更新版 / update）

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
- 美股日线未做拆股调整，长区间曲线在拆股处会出现断崖。
  US daily bars are not split-adjusted; a long range shows a cliff at a split.
- 动画背景是全局一份，不能按页面分别设置；也没有纯单色模式与多图轮播。
  The frame backdrop is one global setting, not per page; there is no single-colour mode and no
  slideshow of several pictures.

### 商店文案同步 / Store listing

`docs/store-listing.md` 的「此版本的新增功能 / What's new in this version」14 份已改为**只写
本次改动**：页面导航。
The fourteen "What's new in this version" lines now describe only this change: page navigation.

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
