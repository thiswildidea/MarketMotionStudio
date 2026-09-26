# AShare Motion Studio

**A股指标动画工作室** — a Windows desktop tool that turns A-share market indicators into
vertical data-visualisation videos and exports them as H.264 MP4.

The product has two names on purpose. Chinese markets get 「A股指标动画工作室」; everywhere
else, and in the Store listing and the package identity, it is AShare Motion Studio. See
"Languages" below.

Status: **five pages working, and export working on all of them.** Market Turnover fetches
live quotes and animates them as a bar race or a turnover calendar; its parameters are remembered
between runs; a cover PNG and an MP4 both export at full resolution.
Stock Volume does the same for one instrument — search by code, name or pinyin, two modes (daily
bars and per-minute intraday), favourites, covers and exports all verified against live data for
贵州茅台. Sector Race is the third: a dozen sectors' or stocks' bars overtaking one another,
their order interpolated smoothly to the last frame, on four rosters and two metrics. Monthly
Matrix is the fourth — a decade of monthly bars per request, cells lighting up in time order, as
a year × month seasonality table or a targets × months rotation, both verified live (上证指数
ten years; CSI Level-1 twelve months). Gain-loss Calendar is the fifth: the whole-market page's
return calendar freed from its fixed series, run on any A-share stock or index.

**Export is now measured rather than designed.** Three consecutive 90-second 1080p30 exports, driven
through the live app against 65 trading days of fetched data:

| | measured |
|---|---|
| wall time to encode 2,700 frames | 28 s, 35 s, 28 s — about a third of the video's own length |
| container | `ftyp` + `uuid` + `mdat` + `moov`, **no `moof`** — a plain, non-fragmented MP4 |
| duration in `mvhd` | 90.00 s, exactly as asked |
| samples in `stsz` | 2,700, one per frame drawn |
| size | 18.9–21.0 MB (High quality, 10 Mbps) |
| **the picture** | the last decoded frame matches a cover export of the same frame at a mean difference of **2.23** — the residue is H.264. Unflipped it was 26.99, which is how the vertical flip was found |

**Every format the settings offer has now been through the encoder**, each verified upright by
the same cover comparison, in a fresh session with both files exported back to back:

| format | frames | wall time | result |
|---|---|---|---|
| 1080×1920 · 30 fps | 2,700 | 28–35 s | complete, non-fragmented, MAD 2.25 |
| 1080×1920 · 60 fps | 5,400 | 58 s | complete, non-fragmented |
| 1440×2560 · 30 fps | 2,700 | 53 s | complete, non-fragmented, MAD 1.87 |
| 1440×2560 · 60 fps | 3,900 | 85 s | complete, non-fragmented, MAD 1.87 |

One 1440p60 run of 5,400 frames stalled at sample 3,200 with the app alive and the file left
truncated. It has not reproduced and no cause is established — see NOTES before assuming the
format is at fault.

That turned on one line: `MediaTranscoder.HardwareAccelerationEnabled` has to be **false**. See
"Things learned the hard way" — with it true, `PrepareMediaStreamSourceTranscodeAsync` never returns,
and nothing anywhere reports an error.

## What it is for

The two tools this replaces (`ashare-turnover-studio` and `stock-dual-studio`) were single
HTML files that drew on a canvas and recorded it with `MediaRecorder`. They worked, and they
carried three limitations that came from the browser rather than from the problem:

- **Export took as long as the video.** `MediaRecorder` timestamps frames by the wall clock,
  so a ninety-second video took ninety seconds to write, and feeding frames faster produced a
  video that played fast.
- **The output was fragmented MP4** (`ftyp` + `moov` + many `moof`/`mdat`). Platforms
  re-encode on upload so posting was fine, but editors read the timeline unreliably.
- **Edge or Chrome had to be installed**, because the H.264 encoder was the browser's.

Drawing with Win2D and encoding through Media Foundation removes all three: the encoder owns
the clock, the container is an ordinary MP4, and nothing outside the package is required.
Fetching over `HttpClient` also disposes of CORS and the JSONP workaround entirely.

## The three indicators

**Market Turnover** — the whole market's daily turnover: the Shanghai and Shenzhen composite
amounts added together. Only days on which every included market traded are kept, so one market's
holiday cannot make the total appear to collapse. A session still in progress is dropped, because
an unfinished day holds only its opening auction. The Beijing option adds the BSE 50 index, which
covers its constituents rather than the whole exchange — a different measure, and a smaller one,
so it is off by default.

It draws in **two forms, switchable at any time without re-fetching**, because they answer
different questions about one fetch. The **bar race** puts time on the horizontal axis, so a run of
heavy days reads as a run, and closes with the mean line and the two extremes boxed. The **turnover
calendar** gives one block per month with cells lighting up day by day, so a busy fortnight is a
patch of colour you can point at — which a time axis spreads out. The gain/loss calendar that once
completed this trio is its own page now (below): two places producing the same video is a choice
nobody needs, and the whole-market copy could only ever name one index.

**Turnover and daily change are not summed the same way, and that asymmetry decides the design.**
Turnover is a quantity, so Shanghai plus Shenzhen is a whole-market figure. A percentage change is a
ratio, and adding two of them means nothing — so the return series is the *leading venue's alone*,
which is why the return calendar's subtitle names the index rather than the combination. One fetch
carries both measures; a `Metric` object says which one a frame is drawing and supplies everything
that follows from the choice: the values, their colours, how a figure reads, the closing cards, and
which two days get boxed.

**The series covers whichever slice of the market was picked.** Eight scopes: both exchanges,
either exchange, either main board, STAR, ChiNext, and both-exchanges-plus-BSE-50. Every board is
measured by a *composite* index — on this source the Shenzhen component and composite carry the
same amount while the STAR 50 carries a third of its board, so composites are the one rule that
keeps every number the same kind of number. The main boards have no composite of their own, so they
are derived per day as the exchange total less its growth board; both sides come from the same
source and the same口径, so the subtraction is exact. The whole-market figure is unchanged by the
rescope: the Shenzhen composite's amount is what the component index always carried.

The calendar has two layout decisions that exist because the frame is portrait. It draws
**Monday to Friday only**: A-shares do not trade at weekends, so two of seven columns would always
be empty while costing every cell nearly a third of its width. And the number of month-blocks per
row is **searched rather than ruled** — every count from one to four is tried and whichever yields
the largest cell wins. On a tall frame height is the binding constraint, so the best arrangement
depends on how many months there are in a way no fixed rule captures; four months land on two
columns of two, a year on four columns of four, and nobody has to choose.

**Stock Volume** — one stock's volume against its turnover rate, as two stacked panels, in
either of two modes. Across trading days the two series are proportional and the panels have
nearly the same shape; within one day, per-minute volume and cumulative turnover look
genuinely different, which is the better picture. The intraday source only keeps the last few
trading days, so that mode offers those rather than an arbitrary date. The stock is found by
code, Chinese name or pinyin through the same quote vendor's suggestion box, and a favourites
row keeps the codes worth coming back to — both stored locally, nothing sent anywhere.

**Sector Race** — a dozen horizontal bars overtaking one another, their order changing to the
last frame: the form where the suspense survives to the end, which a single growing series
cannot hold. Four rosters — the ten CSI Level-1 industries (mutually exclusive, collectively
exhaustive), fifteen hot themes, a custom pick from their union, or a watchlist of stocks — on
two metrics: cumulative return (zero axis centred, red up green down) or cumulative turnover
(monotonic — the story of where the money went). The smoothness is the ranking itself being
interpolated: each day's standings are precomputed, a row's position eases between its two
neighbouring days' ranks, and the axis range interpolates with them, so two racers trading
places cross instead of swapping. Rosters and metrics are bounded — three to sixteen racers,
or a vertical frame is a barcode — and the bounds are stated where the choice is made.

**Monthly Matrix** — months as cells lighting up in time order, on a clock the daily pages
cannot share: one request of monthly bars holds about eleven years, so a range selector built
for daily bars would say things the matrix cannot honour, which is why this is its own page
rather than a fourth form. Two kinds from one renderer — the kinds differ in what the rows and
columns *are*, resolved when the spec is built. Year × month reads one instrument's
seasonality, with every calendar month averaged across the years for the closing cards;
targets × months reads rotation, folding into horizontal bands of twelve when the months
exceed one row's width, each band carrying its own heads and a sub-total, so cells stay big
enough to read. Both compound the range by multiplying — a +20% month and a −20% month are
−4% together, and adding them to zero overstates exactly the volatile ranges a matrix is read
for. Cell colour is red up green down with depth as the square root of magnitude over the
frame's largest: linear puts nearly every month at the same dark tone, because most months
are far smaller than the extreme.

**Gain-loss Calendar** — the whole-market page's return calendar as its own page, on **any
A-share stock or index** rather than one fixed composite — which is why that copy was removed
from the whole-market page: its only instrument was one preset here. No renderer of its own: the calendar
grid is metric-driven, so this page is a different *loader* — one instrument's daily bars
shaped into the series record the whole-market page builds from three indices' — behind the
same grid, colour ramp and closing cards. The stock is found the way the per-stock page finds
one (code, Chinese name or pinyin, filtered to A-shares because the bars endpoint speaks
nothing else), with one-tap presets for the broad indices and **the same watchlist** as the
per-stock page — a favourite is a fact about the instrument, not about the page it was added
on. Cell colour depth goes as the **square root** of the move, not linearly: most days are
small against a period's largest one, and a linear ramp leaves nearly every cell at the same
near-black while the picture says only "there was one big day". Verified live both ways:
上证指数 by preset, 贵州茅台 by typed code, each fetched, covered and encoded to MP4 with the
last frame matching its cover.

**The title is yours on every page.** Type one, or leave the box empty to get the default —
a fixed label on the whole-market chart, the fetched instrument's name on the per-stock one.
A title too long for the frame is scaled down to fit rather than clipped or wrapped, to half
size at most: clipping loses words silently and wrapping pushes the layout down into the chart,
while type that is legibly too small reads as "shorten this". The preview redraws as you type,
which is what makes that legible.

**Both pages can hide the title altogether.** It started per-stock only — the whole-market
title names a market rather than an instrument, so there was nothing to keep out of frame —
but a frame holding just the number is a legitimate look, and the switch was already free:
the panel, the persistence and the stage renderer all implemented it. Hiding gives the title's
row back to the chart: everything below shifts up into the freed row while the bottom margin
holds the lower edge still, so the chart area grows by one title row, and unchecking the box
restores the previous layout exactly rather than approximately. That exactness is why the shift
is expressed as "the title row is present or absent" (`FrameContext.ContentTop` on the per-stock
stage, `TurnoverRenderer.Row` on the whole-market indicators) rather than as an offset applied
to everything underneath.

## Design rules

**The preview and the encoder run the same renderer.** `IFrameRenderer.Draw` is handed a
`FrameContext` and draws in the video's own pixels. The preview differs by one transform
applied before the call; the encoder applies none. A renderer therefore cannot behave
differently in a preview than in a file, and "what you see is what is exported" is a property
of the structure rather than a claim to re-test whenever a renderer changes.

**A renderer is a pure function of progress, not of time.** `Draw` receives the fraction of
the way through and must not depend on having been called for earlier frames. That is what
lets the encoder decide the clock — the thing the browser version could not do — and what
makes the same fraction produce the same picture at 30 and at 60 fps.

**Every measurement is in baseline pixels against 1080×1920**, multiplied by
`FrameContext.Scale` at draw time. No drawing code contains a resolution, so a margin tuned
at 1080p is the same margin at 1440p. A font size assigned directly is the one bug this rule
exists to prevent, and its symptom — correct at 1080p, wrong at 1440p — reads as a layout
fault rather than a missing multiplication.

**All four margins mean the same thing: how far the nearest content is from that edge.**
The bottom margin measures to the *lowest thing drawn* — the data-source credit — not to the
chart's baseline. The credit, the statistic cards and the baseline above it are spaced by fixed
amounts, so the margin moves that whole stack as a unit without changing the gaps inside it.

This is worth stating as a rule because the obvious alternative was tried first and cost the
design something: while the bottom margin measured to the baseline, "250" meant a different
thing on the bottom than on the left, the two indicators needed *different* bottom margins to
look alike, and the credit's distance from the frame edge moved with the margin — so the one
element that guarantees a video says where its numbers came from could be pushed off the bottom.
With the unified meaning, `ChartMargins.Default` is a single 150/150/250 plus the top's
safe-area floor of 230 for both pages.
`FrameContext` follows suit: `CreditLine` is the anchor, and the baseline is derived from it by
`BaselineAbove(gap)` — a method, not a property, because the gap is a property of the indicator
and not of the margins.

**The top margin is the same idea with a floor the others do not have.** It measures from the
top of the frame to the title block, but a phone covers the first 0.12 of the frame with its
own interface, so below that floor the only thing a top margin could do is slide the title
under the status bar. Its range therefore starts at 230 baseline pixels — the floor, which
reproduces the pre-margin layout exactly — and every top-anchored row moves through
`FrameContext.TopRow(fraction)`, so the header block and the plot shift together as one unit
and the spacing inside the stack cannot change.

**The safe-area guides are drawn by the preview, not by the renderer.** The encoder does not
own a `PreviewSurface`, so the guides structurally cannot reach a file. The browser version
guaranteed the same thing twice — the guides were DOM elements outside the canvas *and* were
hidden during recording — and either mechanism could have been forgotten.

**The video's palette does not follow the app's theme.** A file is watched somewhere else. If
its colours followed the machine that made it, two people exporting the same data would get
different videos and neither preview would predict the result.

**Say what the data is, and what it is not.** The frame always carries its source, and the
reference-only disclaimer is in the Store description, on both indicator pages, in Settings
and at the end of the help document. That is four places on purpose: they are the four places
someone arrives from.

## Things learned the hard way

Facts that cost time here, kept so they do not have to be found twice. The parent shell's
own list is in `D:\code\AgolAdminKit\README.md` and still applies; these are new.

**A page's XAML root element must be the base class, not `Page`.** The XAML compiler
generates the other half of the partial class deriving from whatever the root tag names, so a
`<Page>` root with a `: StudioPage` code-behind is two declarations with different base types.
The error is `CS0263`, which names the code-behind file and says nothing about the XAML that
actually decided it.

**`Colors` is `Microsoft.UI.Colors` in WinUI 3, but the struct it yields is
`Windows.UI.Color`.** A file with `using Windows.UI;` resolves `Color` and fails on `Colors`,
which reads as a missing using rather than as two namespaces splitting one concept.

**MakePri logs `PRI249: Invalid qualifier` for every language folder whose tag contains a
hyphen** — `en-US`, `pt-BR`, `zh-Hans`, `zh-Hant` — because it tries the hyphenated name as a
`qualifier-value` pair before falling back. It is **cosmetic**: the built index holds all
fourteen `Language-*` qualifiers and all fourteen candidates for every key, which is how this
was settled rather than assumed. Renaming the help documents does not silence it; they were
never the cause.

**The help documents are named `help-<tag>.md`, with one dot.** Not because of the warning
above, but because MakePri genuinely does read dot-separated filename segments as qualifiers —
that is how `Square44x44Logo.targetsize-16.png` works. A name like `help.en-US.md` puts a
language tag in qualifier position and survives only on the fallback; `help-en-US.md` puts
nothing there.

**A WinUI 3 package carries a machine-learning runtime whether or not the app uses one.**
`onnxruntime.dll` and `DirectML.dll` account for roughly 80 MB across the architectures in
the bundle, against a 65 MB per-architecture package. Nothing here calls them. See NOTES.

**Win2D's native component is `Microsoft.Graphics.Canvas.dll`, under `runtimes/<rid>/native/`.**
Searching a package for "Win2D" or "Direct2D" finds nothing and looks like a dependency that
failed to travel.

**Measuring text in Win2D needs a `CanvasTextLayout`, and the drawing session is the resource
creator it wants.** `new CanvasTextLayout(session, text, format, 0, 0)` with `NoWrap` gives the
natural width in `LayoutBounds`, which is what shrink-to-fit needs; there is no "measure" call on
the session itself. Passing 0 for the maximum width does not mean zero — it means unconstrained.

**Win2D positions text by its layout box; a canvas positions it by the alphabetic baseline.**
`ctx.fillText(s, x, y)` puts the baseline at `y`; `DrawText` puts the *top* there. Porting
coordinates across without correcting drops every line by its ascent, roughly a fifth of the
font size, which on a five-line title block crowds the lines together and reads as spacing that
was never tuned. `CanvasTextLayout.LineMetrics[0].Baseline` is the ascent, so the conversion is
exact — it lives in `Render/Ink.cs` and nothing else is allowed to place text.

**A glow has to blur the shape, not approximate its bounding box.** Win2D has no
`shadowBlur`, and the cheap substitute — concentric translucent rectangles — is fine behind a
two-pixel bar and visibly a *box* behind a 128-pixel number. The real thing is short: record
into a `CanvasCommandList`, wrap it in a `GaussianBlurEffect` with `BorderMode.Soft`, and
composite. Its `BlurAmount` is a Gaussian sigma, about half a canvas `shadowBlur`, so a source
value of 24 comes across as 12.

**The Tencent kline endpoint ignores the start date in its `param`.** It returns the last
`count` bars ending at the end date, so `count` is what decides how far back it reaches and the
range has to be trimmed client-side. Counting calendar days over-fetches, which is what you
want; trusting the server to honour the start silently returns a different range than asked for.

**Each bar in that response is a heterogeneous array — field 6 is an empty JSON object.**
Deserializing a bar as `string[]` therefore fails on *every* response rather than on an unusual
one. Read by index with `JsonElement` and touch only the fields you need: 0 is the date, 8 is
turnover in 万元.

**It serves JSON under `Content-Type: text/html`.** The content type is no use as a check; the
envelope's own `code` field is.

**`CultureInfo.CurrentCulture` does not follow the language the app is showing.** A language
pinned in Settings goes through `PrimaryLanguageOverride`, which redirects *resource* lookup; the
thread's culture still follows the operating system. On an English Windows showing a Chinese
interface, `CurrentCulture` is `en-US` — which rendered a calendar's month as "Jun" and its
weekday row as "M T W T F" inside an otherwise Chinese frame, in a video meant for a Chinese
audience. The fix is the trick this shell already uses to pick the help document: let the
resources name the answer. `CultureName` is a per-language string, so whichever language MRT
resolved — including through its own fallback rules — is the one that answers, and there is one
resolution instead of two free to disagree. `Strings.Culture` is the only culture user-visible
words may be formatted with.

Numbers are the exception and deliberately use `InvariantCulture`: comma-grouped thousands are
what this audience reads on a financial chart, and following the interface language would print
"23.807" in German and "23 807" in Russian for the same series. Words follow the interface,
magnitudes do not.

**`Measure` is an inherited method on every `UIElement`, so it is a poor name for a type.** A class
called `Measure` compiles everywhere except inside a `Page`, where `Measure.Turnover` resolves the
layout method and fails with `CS0119: 'UIElement.Measure(Size)' is a method, which is not valid in
the given context` — an error that names layout and says nothing about the type that caused it. The
same trap waits for `Arrange`, `Content` and `Resources`. It is now `Metric`.

**Win2D hands back pixels top-down; Media Foundation's uncompressed RGB samples are bottom-up.** Feed one to the other and every frame comes out mirrored about the horizontal axis. Nothing else notices: the container is a valid MP4, `mvhd` carries the right duration, `stsz` holds exactly the frames that were drawn, and the export takes the time it should. **A video can be upside down while every property you can read out of its container is correct**, which is why this survived a verification pass that checked all of them. What found it was decoding the last frame and comparing it against a cover export of the same frame. Flipping the decoded frame vertically took the mean absolute difference against the cover from 26.99 to **2.29** — the residue is H.264 — against 29.21 for a horizontal flip and 12.85 for 180°. One axis, unambiguously. The fix is in `VideoExporter.FlipRows`, on the pixel buffer — not a transform on the drawing session, which would have made the file differ from the preview in a way nobody could see.

**`MediaTranscoder.HardwareAccelerationEnabled = true` hangs `PrepareMediaStreamSourceTranscodeAsync` on this machine, silently.** This cost the better part of a day, because every observable symptom points somewhere else: the process stays alive and responsive, no exception is thrown, no `MediaStreamSource.Starting` is ever raised, no sample is ever requested, and the `.mp4` the code created just before the call is deleted by its own `catch`. From outside it is indistinguishable from a folder picker waiting for input — which is what it was taken for, twice. What found it was a `CrashLog.Note` before and after each `await` in the method: the trace stopped dead on the line between them. Setting the flag false, the same 2,700 frames encode in about 28 seconds. The lesson is not "do not use hardware acceleration" — it is that **a hung `await` reports nothing at all, and a trace is the only instrument that can see it**.

**Reading an MP4 while it is still being written produces a confident wrong answer.** A container check run a few seconds after `TranscodeAsync` returned found `ftyp`, `uuid` and `mdat` and no `moov`, which reads as a corrupt or fragmented file. The `moov` was simply not flushed yet; the same file checked a minute later is complete and correct. Stat the file's size twice, or wait, before concluding anything about a container.

**`System.Drawing` is enough to generate a complete MSIX logo set, including the `.ico`.**
Writing PNG-compressed entries (the Vista `.ico` form) rather than BMP entries is what keeps
the alpha correct; the 256-pixel entry records its size as `0`, because the field is one byte.

## Layout

```
src/AShareMotionStudio/
  Market/          TencentKline (the only HTTP to a quote source), TurnoverSeries
  Render/          VideoFormat, ChartMargins, SafeArea, FrameContext, IFrameRenderer,
                   Palette, Ink (text and effects), AnimationPlan and Easing,
                   Metric (turnover vs daily change), TurnoverRenderer (shared chrome)
                   with BarRaceRenderer and CalendarHeatmapRenderer, StageRenderer,
                   FrameExporter (one frame to PNG)
  Views/           PreviewSurface (the letterboxed 9:16 canvas), VideoSettingsPanel, Dialogs
  Pages/           StudioPage base, the two indicator pages, Settings, Help, Playback
  Localization/    Strings lookup and the language override
  Strings/<bcp47>/ Fourteen Resources.resw
  Assets/Help/     Fourteen help-<tag>.md
  Diagnostics/     Crash log
tools/new-icons.ps1  Generates every image the manifest declares
```

`Render/` has no dependency on XAML and `Views/PreviewSurface` is the only thing that knows a
preview exists. That split is what the first design rule above rests on.

`Render/Ink.cs` is the only place text is positioned or blurred, for the reason in "Things
learned the hard way": both operations differ from the canvas originals in ways that are easy to
get subtly wrong and hard to spot afterwards.

`TurnoverRenderer` is the abstract base holding everything the two whole-market forms share — the
background, the title block with its running total, the closing statistic cards, the credit and
the progress bar — with one abstract member for the plot area. That mirrors the source, which has
a shared `drawHeader`/`drawStats`/`drawProgress` and branches only on the chosen view.

`StageRenderer` draws an empty frame — the background, a gridline, the credit — and is what the
Stock Volume page shows *before* anything is fetched. It is *not* a shared base across indicators —
the two source tools are separate implementations with different layout anchors, and an earlier
assumption here that they could share a stage was wrong: the whole-market forms put their plot top
at a fixed fraction of frame height, while the per-stock one stacks two panels whose tops and
bottoms hang from different anchors entirely.

## Building

Requires Visual Studio 2026 (18.x), the Windows SDK 26100, and the .NET 10 SDK.

```powershell
$msb = "C:\Program Files\Microsoft Visual Studio\18\Professional\MSBuild\Current\Bin\MSBuild.exe"

# Debug build
& $msb src\AShareMotionStudio\AShareMotionStudio.csproj /restore /p:Platform=x64 /p:Configuration=Debug

# Store submission package, x64 and ARM64 in one bundle
& $msb src\AShareMotionStudio\AShareMotionStudio.csproj /restore `
  /p:Configuration=Release /p:Platform=x64 `
  /p:AppxBundlePlatforms="x64|arm64" /p:AppxBundle=Always `
  /p:UapAppxPackageBuildMode=StoreUpload /p:AppxPackageSigningEnabled=false `
  /p:GenerateAppxPackageOnBuild=true /p:AppxPackageDir="$PWD\artifacts\\"
```

The second command produces `artifacts\AShareMotionStudio_<version>_x64_arm64_bundle.msixupload`,
which is the file Partner Center takes.

Use `Build`, not `Rebuild`, when the app may be running: `Rebuild` cleans first, the clean
succeeds, the copy back fails on the locked exe, and the output folder is left without
`runtimeconfig.json` and `deps.json` — at which point the apphost claims .NET is not
installed, which is false.

To run a local build, enable Developer Mode and register the loose files:

```powershell
cd src\AShareMotionStudio\bin\x64\Debug\net10.0-windows10.0.26100.0
Add-AppxPackage -Register .\AppxManifest.xml
```

Re-run `tools\new-icons.ps1` only after changing the palette; the generated files are
committed, so a fresh clone packages without it.

## Languages

The interface ships in fourteen: English, German, Spanish, French, Italian, Polish,
Portuguese (Brazil), Czech, Turkish, Russian, Japanese, Korean, Simplified Chinese and
Traditional Chinese. It follows Windows by default and can be pinned in Settings; the change
takes effect at the next start, offered there as a button, because `x:Uid` is resolved when
XAML loads and never re-read.

Translations live in `Strings\<bcp47>\Resources.resw` and the SDK picks them up from the
folder name, so a language is added by adding a folder. The manifest declares `x-generate`
rather than a list, so it cannot disagree with what is there. The help page carries the manual
in the same fourteen, and which document it opens is named by a resource key rather than
worked out from the current culture — one answer to the question instead of two that can
disagree.

**The product name is translated, in exactly two markets.** This departs from the parent
shell's rule that a product name is never translated, and it is deliberate: the product was
commissioned with a Chinese name and an English one, so `AppTitle.Text` carries
「A股指标动画工作室」 in `zh-Hans` and 「A股指標動畫工作室」 in `zh-Hant`, and the English
name everywhere else. The package identity and the Store listing name stay English in every
market.

Every language carries the same keys in the same order. All fourteen currently report 90 keys
with no encoding damage, and all fourteen help documents parse to 24 blocks.

## Appearance

Light, dark, or whatever Windows is set to, from Settings. It changes as you pick it — a theme
is re-read by elements already on screen, which the language is not. The window uses Mica; the
preview draws an opaque frame of its own inside it, because what the video will look like must
not depend on the colour of the wallpaper behind the app.

## Settings are remembered, results are not

Range, duration, resolution, frame rate, quality, margins, the typed title, the chosen form, the
guides — all persisted, because re-entering them every session is the friction that makes a feature
go unused. A fetched series is deliberately not: it belongs to one moment, so keeping it would mean
deciding how long it stays true, and a stale chart is worse than an empty one.

Two details that are not incidental. Keys are **prefixed per page**, because the video and layout
controls are one shared control used by both indicators — without the prefix, tuning the margins for
one chart would silently retune the other. And writes are **coalesced over 400 ms**, because
dragging a slider raises a change per step and a settings write per step is a hundred writes for one
gesture.

## Covers, and why they matter more than they look

**Save cover PNG** writes whichever frame the preview is parked on, at the full export resolution.
Useful on its own for a post thumbnail — and it is the first thing here to render **off-screen**,
which is the mechanism the video encoder needs: a `CanvasRenderTarget` at the real size, the
production renderer drawn into it with no transform, the result read back. If a cover comes out
matching the preview, the encoder's drawing half is already proved and only its muxing half is new.

It also tests the single-render-path rule from the other side: the preview draws through a scaling
transform, a cover draws at 1:1, and a cover that does not match the preview means that rule has been
broken somewhere.

## Where videos go

Exports are written to a folder chosen through a picker and remembered as a future-access
token rather than as a path. This is not incidental: **MSIX silently redirects
`%LOCALAPPDATA%` writes** into the package container while the path string the app holds still
points at the original location, so the browser tools' habit of writing to
`桌面\A股成交额视频\` would produce a file the app reports having written where the user
cannot find it. A folder the user picked is not redirected. Nothing is chosen up front; the
first export asks and then remembers.

## Not done yet

- **The per-stock export at 1440p60 has run once** (a 90-second 242-minute intraday file and a
  daily one, both verified upright against their covers) — but not the full format matrix the
  whole-market page has been through, nor the Beijing venue, nor a cancel mid-export. See NOTES.
