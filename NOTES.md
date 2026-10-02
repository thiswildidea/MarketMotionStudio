# Working notes

Open questions and unfinished edges, kept out of the README because they describe the state of
the work rather than the tool. Settled reasoning lives in commit messages; this file is only
for what is still owed.

Last reviewed: 2026-10-02 (after the twelfth page: currency corridors, the board whose rows are
ranges; see the end).

## The whole-market page was audited line for line against the source HTML

Every figure in the reference README's feature list was checked against the page and against
`ashare_turnover_studio.html`: the four-stop colour ramp at 0.45 and 0.75, the three-stop
background, `easeOutBack` at 1.1, the 278/192 credit and card spacing, the plot top at 0.377,
the 2.5 s-or-4 % opening and the 3–8 s closing, the 640-day refusal, the unfinished-session
drop, the intersect-to-common-days rule, the square-root colour depth, the five-column calendar
and its searched block-column count. **All of them were already correct.** Nothing in the
renderer or the data layer needed changing.

Four things were wrong or missing, and all four are now fixed:

- `PreviewSurface.Margins` started from `108/108/480`, a figure left over from before the bottom
  margin was redefined as content-to-edge. It is what the first frame is laid out with, so it
  was a third answer about where the baseline sits. Now `ChartMargins.Default`.
- **Export and Play were live over an empty frame.** `OnExport` and `OnSaveCover` both return
  early when there is no series, but only the cover button was disabled — so pressing Export
  before fetching did nothing and said nothing, which reads as a broken button. The source tool
  disables its play and export buttons for the same reason. All three now follow
  `_series is not null` in the one place that knows.
- A custom range set the wrong way round reached `TencentKline` and came back as an English
  `ArgumentException` inside an otherwise translated status line. `MarketTurnover.LoadAsync`
  now refuses it with `TurnoverRangeReversed`, in fourteen languages. It is the one rejection
  the page cannot rule out by construction: the month ranges count backwards from today, but
  the custom range is two pickers that can be set either way round.
- README's "Not done yet" still claimed fetching and the two renderers were unbuilt. That was
  true once and is true of Stock Volume only now.

**Verified by building: 0 warnings, 0 errors; all fourteen resw carry 132 keys in the same
order with `fffd=0` and `doubled=0`; the new key's fourteen values are all present in the
compiled `resources.pri`.** Verified by running the app too, later the same day: the three buttons
read `enabled=False` on a fresh window and `enabled=True` after a fetch of 65 trading days, which
is the change itself rather than the build that contains it.

Two things about checking that output are worth not rediscovering. `resources.pri` stores a
value as **UTF-8 when it is ASCII and UTF-16 when it is not**, so an English string searched
only as UTF-16 reads as missing; and string literals in the DLL sit at odd byte offsets often
enough that decoding the whole file from byte zero misses them — search the raw UTF-16LE byte
sequence instead. Both failures look exactly like the change not having been built, which is
why the check above carries a negative control.

## Before the first Store submission

**Data rights are the real gate, and nothing in the code can settle them.** Both indicators
read Tencent Finance's undocumented endpoints — `proxy.finance.qq.com/.../newfqkline/get`,
`ifzq.gtimg.cn`, `qt.gtimg.cn`, `smartbox.gtimg.cn`. A-share quote data is licensed by the
Shanghai and Shenzhen exchanges, and Store policy requires the publisher to hold rights to
content the app redistributes. A video *is* redistribution: the numbers leave the machine
inside a file meant to be posted publicly. This wants an answer from whoever can give one
legally, before submitting rather than after a rejection. It is the same shape as the parent
shell's unresolved Esri icon licence, and it is the more exposed of the two because the output
is public by design.

Worth pricing the alternatives while that is open: a licensed vendor feed, or shipping without
the fetch and letting the user supply a CSV. The second is unattractive but it is a product
that can ship.

**Package identity is decided once, and it is already decided.** `Identity Name` and `Publisher`
come from the name reserved in Partner Center and cannot be changed for that product afterwards;
the display name can. The manifest now carries the reserved identity `8166Yxw.MarketMotionStudio`
with the Partner Center publisher `CN=7092F3CD-…`, so the identity is frozen — changing either
one stops already-installed copies from ever receiving an update. (The package identity
`MarketMotionStudio` is frozen too and never changes — only the display name and Store listing
name were renamed when the app grew beyond A-shares to Hong Kong and US markets.)

**The shell name is a resource reference, but the package name is not.** `DisplayName` appears in
three manifest places — `Properties`, `uap:VisualElements`, `uap5:StartupTask`.

`Properties/DisplayName` is the one Partner Center checks against the reservation, and it has to
carry the reserved name literally: `MarketMotionStudio`. It was `ms-resource:AppDisplayName`
until the 1.0.1.0 upload came back with three errors, one per language the resource resolves to
(*"使用了你未保留的显示名称"* — Market Motion Studio, 行情指标动画工作室, 行情指標動畫工作室).
None of those is reserved; only `MarketMotionStudio` is.

The other two stay `ms-resource:AppDisplayName`, so the Start menu, the Apps list and Settings
show the product name in the OS display language instead of the identity. Localising
`uap:VisualElements` is the supported way to get a translated shell name — the reservation check
does not apply to it. It cannot reuse `AppTitle.Text` for
this: that is a *property* identifier owned by `x:Uid`, and one resource file may not hold both
`X` and `X.Text`. A display language the app does not ship falls back to English, which is
`DefaultLanguage` — pinned to `en-US` in the csproj rather than left to the toolchain default.

**Version numbering: two hard rules and one that follows from them.** The version is four
sections, `Major.Minor.Build.Revision`.

- **Revision must be 0.** It is reserved for the Store, which may change it after certification.
  This is what the 2026-09-26 upload rejection was really about: the package said `0.2.0.1`, and
  the error reads *"Apps are not allowed to have a Version with a revision number other than
  zero specified in the app manifest"* — not, as it was first read, a demand for all zeros.
  `0.0.0.0` satisfied the rule by accident and got through, which is how a wrong rule got written
  down.
- **Major cannot be 0.** Each part is 0–65535, the first excepted. So the first submission is
  `1.0.0.0`, not `0.x`.
- **An update must be higher than what customers already have** on the same device family, or
  they are simply never offered it. That alone rules out staying on `0.0.0.0`.

So: `1.0.0.0` first, then `1.0.1.0` for fixes and `1.1.0.0` for features, fourth section always
0. Settings and the contact mail read the version straight from the package, so a version a user
reports may show a non-zero fourth section — that is the Store's own edit, not a build mistake.
Locally, a loose layout will not re-register at a version lower than or equal to the one already
registered, so bump before `Add-AppxPackage -Register`.

**The disclaimer is in four places and should stay in all four.** Store description, both
indicator pages, Settings, and the end of the help document. A financial app that draws market
data has to say what it is not, and each of those is a place someone arrives from without
passing the others.

**The contact address is inherited and probably wrong.** `SettingsPage.ContactAddress` and the
last line of all fourteen help documents say `gaqo@outlook.com`, carried over from the parent
shell. If this product has its own address, that is fifteen files.

## The package carries ~80 MB of machine-learning runtime it never uses

Measured from the bundle built on 2026-09-24, not estimated:

| entry | size |
|---|---|
| `runtimes/win-arm64/native/onnxruntime.dll` | 21.9 MB |
| `runtimes/win-x64/native/onnxruntime.dll` | 21.7 MB |
| `runtimes/win-arm64ec/native/onnxruntime.dll` | 19.4 MB |
| `runtimes/win-arm64ec/native/DirectML.dll` | 18.9 MB |
| `runtimes/win-x64/native/DirectML.dll` | 18.7 MB |
| `runtimes/win-arm64/native/DirectML.dll` | 18.6 MB |

Each per-architecture `.msix` is about 65 MB. `Microsoft.Windows.SDK.NET.dll` is another
26 MB, which is ordinary for the Windows App SDK; the ML runtimes are not, because nothing in
this app calls them. They arrive with `Microsoft.WindowsAppSDK` 2.5.1.

**Unresolved.** A search of the Windows App SDK's `.props` and `.targets` in the local NuGet
cache for a property naming ML, AI, ONNX or DirectML found nothing, so there may be no opt-out
switch at this version, or it may be named something the search did not anticipate — the
search finding nothing is not evidence that nothing exists. Worth one focused attempt before
release, because a first-time download is the one number a Store listing cannot hide, and it
is far cheaper to fix now than after users have the large version. Do not guess at a property
name and declare it fixed: measure the bundle again.

## The renderers are the next real work, and the source is the HTML

The whole-market renderers exist: `TurnoverRenderer` holds the shared chrome, with
`BarRaceRenderer` and `CalendarHeatmapRenderer` over it. What does not exist is the per-stock
one, and `StageRenderer` is the empty frame standing in for it.

**`ashare_turnover_studio.html` has been read twice now** — once at 677 lines for the bar form,
once at 804 for the calendar — and both forms are ports of it. **`stock_dual_studio.html`
(1061 lines) has still not been read**, and that is what the per-stock renderer needs. Reading it
is the first step of that work, not an optional check.

**What reading the first file corrected, as a warning about the second.** Every one of these was
wrong in code written from the README alone:

- **The colour ramp's stops are not evenly spaced.** Cyan sits at 0.45 and orange at 0.75, so
  the warm end is compressed into the top quarter — which is what makes an exceptional day stand
  out instead of merely being redder. Evenly spaced stops flatten the one distinction the colour
  exists to draw. `Palette.RateRamp` is still guessed and is the obvious place for the same
  mistake to be sitting right now.
- **The background is a three-stop vertical gradient**, not a flat fill.
- **The margin sliders have different ranges per side**: 40–260 step 2 for left and right,
  150–420 step 5 for the bottom, 230–450 step 5 for the top. A single 40–700 range let the
  bottom margin be set to values that push content out of frame; the top's floor is the
  phone's safe area in baseline pixels (0.12 × 1920), because below it the only thing a top
  margin could do is slide the title under the status bar.
- **The default duration is 90 seconds**, not 45.
- **`CreditGap` is 278 baseline pixels and the statistic cards sit 192 above the credit.** The
  values invented for `StageRenderer` were 150 and 60 — close enough to look plausible and wrong
  enough to misplace the whole lower stack.
- **The plot top is a fixed fraction of frame height (0.377)**, not a measurement below the
  title rows. It has to clear a 128-pixel running total whose own position is also a fraction,
  so deriving it from stacked row heights would drift whenever a font changed. Read through
  `FrameContext.TopRow` so the user's top margin moves it with the header block — a renderer
  that multiplied the fraction itself would leave the plot behind when the header moved.
- **`easeOutBack` uses 1.1, not the textbook 1.70158.** With a hundred bars rising at once the
  standard overshoot reads as wobble.

`FrameContext.TitleRowHeight` (90) came from the per-stock README and is the one invented-looking
number that turned out to be stated.

**The cumulative series must not use a bouncing ease.** The intraday turnover curve is
monotonic, and `easeOutBack` on a monotonic value draws an overshoot-and-retreat that reads as
the data going backwards. The browser version already learned this and used `easeOutCubic`
there; the distinction has to survive the port.

## Owed on the data layer

- **`Ink.Glow` runs an effect graph per glowing element per frame.** At 30 fps with one growing
  bar that is one blur per frame, which is fine; the per-stock chart has a following light on its
  cumulative curve as well. If the preview starts dropping frames, this is the first thing to
  measure, and the fix is to record the command list once per frame rather than once per element.
- **Nothing is cached between fetches.** Pressing Get data twice re-requests the same days. Not
  worth fixing for a button somebody presses deliberately, but worth knowing before any feature
  fetches on its own.
- **`TencentKline` sends no `Referer` and identifies itself as `MarketMotionStudio/0.1`.** That is
  deliberate — a request that says what it is can be blocked on purpose rather than by
  fingerprinting — but it also means this traffic is trivially identifiable, which is a
  consideration for the data-rights question above rather than a technical one.

## The encoder works now, and the cause was one property

`Render/VideoExporter.cs` completes an export. **Three consecutive 90-second 1080p30 runs** from the
live app, driven through UI Automation against 65 fetched trading days:

| run | `encode: enter` | `transcode returned` | wall time | samples |
|---|---|---|---|---|
| 1 | 10:40:33.996 | 10:41:02.905 | 28.9 s | 2700/2700 |
| 2 | 10:43:37.709 | 10:44:05.047 | 27.3 s | 2700/2700 |
| 3 | 10:46:46.893 | 10:47:21.613 | 34.7 s | 2700/2700 |

**The fix was `MediaTranscoder.HardwareAccelerationEnabled = false`.** That is the only line that
changed between the run that hung and the run that worked; same machine, same build otherwise, same
data.

**Where it was actually stuck, which was not any of the four candidates listed here before.**
`CrashLog.Note` was added before and after each `await` in `EncodeAsync`. The trace ran

```
encode: file created ...      <- CreateFileAsync succeeded
encode: opening file stream
encode: file stream open
encode: calling PrepareMediaStreamSourceTranscodeAsync
```

and then stopped. So: the folder resolves fine, the descriptor and `CanvasDevice` are built fine,
`CreateFileAsync` succeeds — and **`PrepareMediaStreamSourceTranscodeAsync` never returns**. The
process stays alive and responsive; `MediaStreamSource.Starting` is **never raised** and no sample is
ever requested, so the failure is before the pipeline ever opens the source. The file created moments
earlier is deleted by this method's own `catch`, which is why no `.mp4` was ever found — the earlier
"no file is created" reading was the cleanup hiding the evidence.

The four-way guess this replaces (`OutputFolder`, descriptor, `CanvasDevice`, `OnExport` never
running) was wrong in all four. The trace is what settled it, and it is worth saying plainly: reading
the UI distinguishes none of these, because a closed InfoBar looks the same whether the code never ran
or ran and hung.

**Verified about the output, by reading the boxes rather than by opening it in a player:**

- `ftyp` → `uuid` → `mdat` → `moov`, and **no `moof` anywhere** — a plain, non-fragmented MP4, which
  is the claim the whole design was built to make.
- `mvhd` duration `2700000 / 30000` = **90.00 s**, exactly the duration asked for.
- `stsz` sample count **2700**, one per frame drawn; one `vide` handler, no audio track.
- 18.9 MB at High (10 Mbps).
- The second and third runs wrote `...(2).mp4` beside the first, so
  `CreationCollisionOption.GenerateUniqueName` is doing its job.

Two measurement traps, both of which produced a wrong answer once:

- **Reading the file too early.** A container check seconds after the transcode returned found no
  `moov` and read as a broken file. The `moov` had not been flushed. Stat it twice.
- **Misreading `stsz`.** Its fields are `sample_size` then `sample_count` at `+8` and `+12` after the
  type, not at `+12`. Reading from the wrong offset reported 6553 samples, a number that looks
  plausible and is about 2.4× too many.
- **Misreading the progress unit.** `PrepareTranscodeResult.TranscodeAsync().AsTask(…, progress)`
  reports a **percentage 0–100**, and the page multiplied it by 100 again, so the status read
  "Encoding… 1211%". The conversion now lives in `VideoExporter`, which clamps as well — the
  pipeline has been seen to overshoot at the end — and callers keep the fraction the parameter
  documents. A live run sampled 1% → 13% → 25% → … → 96% → done, monotonically.

**The format matrix has now been through the encoder**, driven over UI automation with the
flip-check comparing each video's last frame against a cover exported in the same session:

| format | frames | wall time | result |
|---|---|---|---|
| 1080×1920 · 30 fps | 2,700 | 28–35 s | complete, `moov` present, upright (MAD 2.25) |
| 1080×1920 · 60 fps | 5,400 | 58 s | complete, `moov` present, 33.0 MB |
| 1440×2560 · 30 fps | 2,700 | 53 s | complete, `moov` present, upright (MAD 1.87 same-session) |
| 1440×2560 · 60 fps | 3,900 | 85 s | complete, `moov` present, upright (MAD 1.87 same-session) |

**One 1440p60 run stalled** — at sample 3,200 of 5,400, app alive, file left truncated at
`mdat` with no `moov`. It has not reproduced: a later 1440p60 run of 3,900 frames completed
cleanly in a fresh session. The stall and the success differ in session age, frame count
(5,400 vs 3,900) and export count in the session, so no single cause is established. If it
comes back, the first suspicion is the long-lived session rather than the format, and the
instrument is the same per-`await` trace that found the hardware-acceleration hang.

**Still owed here.** The `bj899050` path has not been through the encoder; the diagnostic
`CrashLog.Note` calls that found this have been removed again, per the note on `CrashLog.Note`
itself. If export ever stops, put a trace back before reaching for anything else. The Stock
Volume page has since had its own exports — daily and intraday, 1440p60, both verified upright —
through the same `VideoExporter`, so the notes below about that method apply to it too.

**Do not turn hardware acceleration back on without measuring.** Software encoding already beats real
time by about 3×, so the case for the GPU is not obvious, and the failure mode is a silent hang.

### The first export that completed was upside down

Reported from watching the file: the whole frame was mirrored about the horizontal axis. The cause
is a row-order disagreement — **Win2D hands back pixels top-down, Media Foundation's uncompressed RGB
video samples are bottom-up** — and nothing outside the pixels could have revealed it. The container
was a valid non-fragmented MP4, `mvhd` read 90.00 s, `stsz` held the 2,700 frames that were drawn,
and the export finished in 28 seconds. Every property the previous pass checked was correct.

**How it was diagnosed, which is the reusable part.** `Save cover PNG` renders the same frame through
the same renderer at 1:1 with no transform, and the page parks on progress 1.0 after a fetch while
exporting does not move the scrub — so the cover and the video's *last* decoded frame are the same
frame. Decoding with PyAV and taking the mean absolute difference against the cover under each
orientation:

| orientation applied to the decoded frame | MAD before the fix | MAD after |
|---|---|---|
| none | 26.99 | **2.23** |
| flipped vertically | **2.29** | 26.84 |
| flipped horizontally | 29.21 | 13.98 |
| rotated 180° | 12.85 | 28.95 |

The two columns are the same table with the winner swapped, which is the whole diagnosis: one axis,
with a residue of ~2 explained by H.264. Worth noting that the eye said "rotated 180°" at first, and
the arithmetic says vertical only — 12.85 vs 2.29 is not close.

The fix is `VideoExporter.FlipRows`, applied to the pixel buffer before the sample is built. It costs
one row of scratch, not a second frame, and measures free: 29.8 s and 34.8 s for the same 2,700
frames, against 28–35 s before it.

**Owed:** the fix was verified at 1080p30, 1440p30 and 1440p60, each by comparing the *last*
frame. Nobody has watched a corrected file play, and the middle of the animation has not been
compared frame by frame — though the transform is per-frame and has no notion of where in the
animation it is.

**A measurement trap worth keeping, because it manufactured a bug that was not there.** The
first 1440p comparison came out at MAD 11 against 2 at 1080p, and looked like a resolution bug:
the plot area was shifted and the bars a different width, while the title block matched. The
cause was the harness, twice over. `SetFocus` + `{Home}` on "the first slider in the tree" had
moved a **margin** slider, not the duration one — margins move the plot area and are
per-session state. And the two files being compared had been exported either side of an app
restart, so they carried different margins. Re-exporting the cover and the video back to back
in one session dropped the difference to 1.87. **A cover/video comparison is only evidence if
both files come from the same session, untouched in between.**

**One real bug was found and fixed, and it is worth knowing about beyond this class.** The first
version drew frames on the media pipeline's `SampleRequested` thread using
`CanvasDevice.GetSharedDevice()` — the same device the UI draws the preview with. Concurrent access to
one D3D device from two threads is not serialised for you, and the failure mode is brutal: **the
process disappears with no crash log, no Windows Error Reporting entry and no fault in the event
log.** It is indistinguishable from somebody closing the window, which is exactly how it was
misdiagnosed for a while. Giving the exporter `new CanvasDevice()` stopped it dead. Anything that
draws off the UI thread needs its own device.

Also now observed rather than assumed: `profile.Audio = null` alongside a video-only
`MediaStreamSource` is accepted — `prepared.CanTranscode` came back `True` with `FailureReason=None`
on all three runs.

## What the encoder has to honour, and how to check it

`IFrameRenderer` is a pure function of `Progress` precisely so the encoder can own the clock.
The shape that follows: walk `0 → 1` in `Format.FrameCount(duration)` steps, draw each frame
into a `CanvasRenderTarget`, feed the pixels to a `MediaStreamSource`, and transcode to
H.264 MP4 with `MediaTranscoder` at `Format.BitsPerSecond`.

**Both of the things this section used to ask to be verified are now verified**, in the encoder
section above: the container is a plain MP4 with no `moof`, and a 90-second export takes about 28
seconds. They stay listed because they are the two properties a change to the encoder or to
`IFrameRenderer` can still break, and the way to re-check them is unchanged — read the boxes, and
time it.

`Playback` deliberately *is* wall-clock, because a preview exists to answer "is this too fast
to read". Do not let that leak into the encoder.

## Data-layer details the browser version had to discover

Carried forward so they are not rediscovered. All of these are handled in the HTML and none of
them are handled here yet.

- Science-and-technology-board volume is quoted in **shares, not lots**. The browser version
  detects it by taking the median of `volume × price ÷ amount` and normalises. A chart that
  silently mixes the two units is wrong by a factor of 100 for those names.
- The intraday endpoint **pads to 15:30** after the close, and the tail is a flat run where
  cumulative volume stops changing. Both have to be trimmed or the video ends on a still.
- The intraday endpoint **does not return turnover rate**. It is derived: float market cap ÷
  current price gives float shares, then cumulative volume ÷ that.
- Responses are **GBK while the header claims UTF-8**. In .NET this needs
  `CodePagesEncodingProvider`; `System.Text.Encoding.CodePages` is deliberately *not*
  referenced yet, because a package that arrives before the code using it cannot be judged by
  what it is doing.
- A single request returns at most about **640 calendar days**. The UI should refuse a longer
  range rather than truncate it silently, which is what the READMEs say the browser version
  does.

## Decisions worth re-examining

- **No notification-area icon and no startup task.** The parent shell has both because an
  organization scan runs for half an hour and must survive the window being closed. A native
  encode of a 90-second video is foreground work somebody is watching, so the tray would have
  bought an extra third-party dependency — `H.NotifyIcon.WinUI`, which goes through Store
  certification and whose licence becomes this project's problem — for no benefit. What
  replaced it is the window title saying what is running, which is the only thing a window
  behind another window can still say. If an export of a 1440p/60 video turns out to take
  minutes rather than seconds, revisit this.
- **`VideoSettingsPanel.SetDefaultMargins` is gone, along with the per-page margin defaults.**
  The two indicators started from 108/108/480 and 110/110/230, and both now start from
  `ChartMargins.Default` (150/150/250). The divergence existed only because the bottom margin
  measured to the chart baseline, and the upstream tools removed the reason for it when they
  redefined that margin as content-to-edge. The mechanism went with it rather than being kept
  "in case": a setter implying a difference that no longer exists is a claim about the design.
  If the two ever want different margins again, this is the thing to bring back, and the
  condition is a genuine difference in what sits below the baseline — not a difference in taste.
- **`AppServices` holds only `BackgroundWork`.** No shared series cache. Two pages drawing two
  different indicators of two different things have nothing to share, and a shared cache would
  only create the question of when to invalidate it. If a third indicator reuses the first
  one's data, this is where that changes.
- **`Playback` is a 60 Hz `DispatcherTimer` rather than `CompositionTarget.Rendering`.** Good
  enough to judge pacing, and it does not tie preview smoothness to the compositor. If the
  preview stutters on large series, the redraw cost is the thing to measure first, not the
  timer.
- **Margins are capped per side, not by one constant.** The side sliders run 40–260 in steps of
  2 and the bottom runs 150–420 in steps of 5, which is the source tool's own range rather than
  a guess — a single 40–700 range let the bottom margin be set to values that pushed content out
  of frame. `FrameContext.PlotHeight` still clamps to at least 1, so a maximum bottom margin on
  a short frame draws as nothing rather than as an inverted chart. The figures are constants
  rather than bounds derived from the frame, which is defensible while both indicators want the
  same stack below the baseline; if they ever differ, that is the thing to revisit.

## Not verified from a build

This is what can and cannot be claimed as of the last review.

**Verified here:** both configurations compile; the Store bundle builds and reports
`PackageSuccessfullyCreated`; the inner x64 package holds all fourteen help documents,
nineteen logo and splash assets, `resources.pri` and Win2D's native
`Microsoft.Graphics.Canvas.dll` for x64 and arm64; all fourteen resw files carry 90 keys in
the same order with no `U+FFFD` and no double-encoded sequences; every `x:Uid` names a
property its element actually has; all 90 defined keys are reached from either C# or XAML;
all fourteen help documents parse to the same number of blocks (77 as of the pictures; the count
is not the contract, all fourteen agreeing is); every generated PNG is 32-bit with a
transparent corner and an opaque centre, and the `.ico` loads.

**Verified by running it**, registered from the debug output and driven through UI Automation:

- The window opens, carries its own title and icon, and navigation reaches all four pages.
- The preview letterboxes a 9:16 frame and `StageRenderer` draws it: title block under the top
  safe area, four dashed gridlines, a brighter baseline, the credit hanging below it, and the
  progress bar on the bottom edge.
- Both pages start from `ChartMargins.Default`, 150/150/250, and the credit sits low in the
  frame rather than in the middle of a dead band — the bottom margin is measuring to the
  lowest content, as intended.
- Hiding the title on the per-stock page does what its README says, measured rather than
  eyeballed: the subtitle moved up 25 preview pixels, which at that preview's scale (about
  310 device pixels for a 1080-pixel frame) is 90 baseline pixels — exactly one title row —
  while the baseline and the credit did not move at all, because the bottom margin holds the
  lower edge. Turning it back off restored the first layout.
- The title box, its placeholder (the fetched instrument's name on the per-stock page, a fixed
  label on the whole-market one) and the shrink-to-fit note all render.
- **Market Turnover works end to end against live data.** A three-month fetch returned 67
  trading days for Shanghai plus Shenzhen; the frame drew the title block, the running total with
  its date advancing, the axis at rounded 10,000 steps, the bars in the corrected ramp, the mean
  line at 23,807, both extremes boxed with their dates, the four statistic cards
  (23,807 / 36,600 / 16,127 / 2.27x) and the credit. Scrubbing to 0.45 showed bars grown only as
  far as 2026-08-07, per-bar date labels faded in behind them, and none of the closing elements —
  so the stagger, the per-bar fades and the finale gating all behave.
- Three defects were found by looking at that frame and fixed: dates rendered as `6/24/2026`
  because a `DateOnly` went into a format string and picked up the current culture; the status
  line printed `23807` where the frame printed `23,807`; and the glow behind the running total
  was a visible box, because the concentric-rectangle approximation does not survive being put
  behind 128-pixel glyphs. It is now a real `GaussianBlurEffect` over a `CanvasCommandList`.
- **The calendar heat map works, in both its layout decisions.** Four month blocks for a
  three-month range (the span crosses four calendar months) were arranged two by two by the
  column search; cells coloured consistently with the bar form, warm in June and July and cool in
  August and September. Scrubbed to 0.62 the August block was filling to 2026-08-26 and the
  September block had not appeared at all, which is the documented behaviour — a block's frame
  arrives just before its own first day, so cells never land in empty space.
- **The gain/loss calendar works.** 37 up days against 29 down over 67 trading days, best +1.79%,
  worst −3.05%, the running figure reading "−1.22" in green with the correct sign and two decimals,
  and the title and subtitle switching to name the index rather than the market combination. The
  square-root depth mapping does what it is for: small moves are visibly red or green rather than
  all collapsing to near-black.
- The card counts are worth knowing about before someone reports them as a bug: **37 + 29 = 66
  against 67 days**. Day zero is 0% because the day before it is outside the range, and the counts
  are strictly greater and strictly less than zero, so an unchanged day belongs to neither. Honest
  rather than tidy, and stated here because "the numbers do not add up" is the obvious first
  reading.
- **Settings persistence survives a restart**, driven end to end: duration 90 → 65, left margin
  150 → 212, form bars → gain/loss calendar; the window closed through its own close path (which
  ended the app, as designed with no tray icon); on relaunch all three came back. So
  `StudioPreferences.Restoring` is doing its job — a handler firing as a control is assigned is not
  writing a half-restored value back over the one being read.
- **The cover export works, and it is the more important of the two tests.** A 1080×1920 PNG,
  32-bit and fully opaque, written to the remembered folder with the metric's default title in the
  file name. Its numbers are identical to the preview screenshots taken earlier — 16,534 running
  total, mean 23,807, high 36,600, low 16,127, ratio 2.27x — which is `one-render-path.mdc` verified
  from the encoder's side rather than the preview's: the same renderer through a transform and at
  1:1 produces the same frame.
  - It also answers an open question above: the extreme markers **are** legible at 1080p. They were
    illegible only in a quarter-scale preview.
  - **One unexplained thing, recorded rather than smoothed over.** The first invocation reported
    success naming a file, and an unfiltered listing of that folder immediately afterwards showed no
    such file; a second invocation produced it. No crash log, no exception, and the message is only
    written on the success path. Either the first write went somewhere else or the report preceded
    the write becoming visible. Worth one focused look before trusting the success message, because
    a save that says it worked and did not is the worst class of bug this feature can have.
  - Unrelated to the app, but it cost time: `Get-ChildItem -Filter "*_1080x1920.png"` does **not**
    match a file whose name begins with CJK characters. An unfiltered listing found it immediately.
    Use `Where-Object` on the extension rather than `-Filter` when names may be non-ASCII.
- A fourth defect surfaced only in the calendar, and it is the most generally useful finding so
  far: the month read **"Jun"** and the weekday row **"M T W T F"** inside a Chinese frame.
  `CultureInfo.CurrentCulture` follows the operating system, not the language the app resolved —
  see the README entry. Fixed by having each resw declare its own `CultureName`, so the culture
  comes from the same resolution that chose every other string. Worth remembering that this bug
  is invisible on a machine whose system locale already matches the chosen language, which is
  most development machines.
- The bit-rate readout computes: 1080×1920 at 30 fps on High shows "约 10.0 Mbps".
- The safe-area toggle draws the three occlusion zones over the frame.
- Choosing a language and pressing restart works end to end: the app came back in Simplified
  Chinese and Settings read the stored choice back as 简体中文.
- `WindowPlacement` restored a maximised window across that restart.
- Settings shows the real package-container path
  (`...\Packages\MarketMotionStudio.Dev_cdwthxytk4q78\LocalState`), which is the MSIX
  redirection the output-folder design exists to work around, visible rather than described.
- The output folder starts unset, and **Forget** is correctly disabled until one is chosen.
- The help page renders all of the hand-written Markdown subset — headings, paragraphs and
  wrapped bullets — in Chinese.
- **A completed MP4 export, three times.** Driven end to end — launch, fetch 65 trading days,
  press 导出 MP4 — three consecutive 90-second 1080p30 runs finished: 2700/2700 samples in 28.9 s,
  27.3 s and 34.7 s, each leaving an 18.9 MB file whose boxes are `ftyp`/`uuid`/`mdat`/`moov`
  with no `moof`, whose `mvhd` duration is 90.00 s, and whose `stsz` count is 2700. Details and the
  two measurement traps behind those numbers are in the encoder section above.
- Fetching reports honestly on live data: `共 65 个交易日（2026-06-26 ~ 2026-09-24）· 日均 23,481 ·
  最高 36,600 · 最低 16,127`, with commas grouped the way the frame groups them.
- **Play, export and cover are disabled on a fresh window and enabled after a fetch** — read off
  the live UI Automation tree, not inferred from the code.
- No `crash.log`, no Windows Error Reporting entry, and no fault in the Application log across
  roughly a dozen launches. The app also sat untouched for 25 seconds and then took a
  navigation to Stock Volume without incident, which is how "it keeps dying" was ruled out —
  the window was being closed by hand, and with no tray icon that ends the app by design.

**Still not seen:**

- Playback in motion. Scrubbing has now been exercised through automation, but the transport has
  never been *started*, so whether the thumb fights the person holding it during playback is
  still untested — and so is whether a 67-bar frame redraws fast enough at 60 Hz to look like
  the video rather than like a slideshow. That second one matters: if the preview cannot keep up,
  it stops answering the question it exists for.
- **Everything about the `bj899050` path.** Including the Beijing index has never been switched
  on against the live endpoint, so neither the third request nor the intersect-to-common-days
  rule has run with three venues. The two-venue case is what was verified.
- **The refusal paths.** A range over 640 days, a range with fewer than three trading days, a
  custom range whose start is not before its end, and a network failure all have messages and
  none has been triggered. Setting the two date pickers the wrong way round is the easiest of
  the four to reach and worth trying first.
- **Playback still has not been started**, so the 60 Hz redraw cost of a 67-bar frame is unmeasured.
- **The calendar's extreme markers at full resolution.** The peak and low cells get a boxed
  outline and a label at 20 baseline pixels, which in a preview scaled to about a quarter is
  under a pixel of stroke and illegible — so it could not be judged from the screenshots. It
  should be legible at 1080p and that is the size to check it at. The bar form's equivalents were
  clearly visible and are fine.
- **A month starting on a weekend.** `CellOf` computes the week index on a seven-day week even
  though five columns are drawn, which is what keeps rows correct when the 1st is a Thursday. The
  ranges tested happened not to include a month whose first trading day is far into its first
  week, so the row arithmetic has not been stressed. A January (1st often a holiday) is the case
  to try.
- **Every language except Simplified Chinese.** The culture fix was verified in zh-Hans on an
  en-US system. The other twelve read their `CultureName` through the same path, and the check
  above confirms all fourteen declare a valid tag matching their folder, but no frame has been
  drawn in any of them.
- **Shrink-to-fit has never been given a title long enough to shrink.** `StageRenderer.FitSize`
  measures with a `CanvasTextLayout` and clamps at half size, and both of those paths are
  untried: every title seen so far fitted, so the code that runs is the early return. Type
  something absurd into the box and watch it reach the floor rather than keep going.
- Whether the 360-pixel parameter column survives German and Russian, the two that overflow a
  column tuned in English. Chinese fits comfortably.
- Whether any of the fourteen translations reads badly to a native speaker.
- **Export at anything other than 1080p30.** Three runs all used the default resolution and frame
  rate. 1440p and 60 fps have never been through `MediaTranscoder`, and neither has the cancel
  button — every run was allowed to finish.
- **Export from the Stock Volume page.** Its export button shares `VideoExporter`, but the page has
  no renderer and no series, so it has never been clickable.
- **Export with the `bj899050` venue included**, which changes the series rather than the encoder.
- **That the exported video looks like the preview *throughout*.** This has moved a long way: the
  last decoded frame now matches a cover export of the same frame at a mean difference of 2.23, and
  that is what caught the vertical flip. But it is one frame out of 2,700. Nothing has compared a
  mid-animation frame, and nobody has watched the corrected file play end to end.

To run it again:

```powershell
cd src\MarketMotionStudio\bin\x64\Debug\net10.0-windows10.0.26100.0
Add-AppxPackage -Register .\AppxManifest.xml
```

## Translations are unreviewed

The fourteen languages were produced in one pass and **no native speaker has read them**. They
are good enough to develop and demo against; they are not good enough to ship to paying users
unchecked. The help documents are the larger half of that by volume and carry more meaning per
sentence.

Review these first, because they are the strings where a wrong word misleads about data rather
than about a control:

- `TurnoverIncludeBeijingNote` — that the Beijing option is a *different measure*, not merely
  an addition. A reader who misses this publishes a chart whose axis label is wrong.
- `StudioDisclaimer` — the reference-only line, in all fourteen.
- `SettingsSourcesNote` — where the data comes from and that an unfinished day is excluded.
- `StudioMarginNote` — that the numbers are baseline pixels, not pixels of the chosen
  resolution.

The rest is navigation and status text, where an awkward phrase is merely awkward.

Placeholders are positional. Every `{n}` must survive translation, and `PageWorkFailed`,
`SettingsContactFailed` and `TitleBusy` each carry two.

The checks that hold the set together are in `.cursor/rules/keep-translations-complete.mdc`.
All fourteen must report `ok`, `fffd=0`, `doubled=0`, and all fourteen help documents must
report the same block count.

## Help documents: the three missing pages are now written (all fourteen)

The sector-race, monthly-matrix and gain-loss-calendar pages had no help sections in any of the
fourteen files. Each now has a section inserted after "个股成交量 / Stock Volume" and before
"视频 / Video", describing the two measures/rosters (race), the year-vs-compare modes (matrix) and
the shared watchlist plus the ~640-day cap (calendar). All fourteen parse to 42 blocks, so the
`keep-translations-complete.mdc` equality check still passes.

Still owed, minor: the "视频 / Video" section could mention the title box and the cover-button
export, and a line that parameters are remembered but data is not. Small, and not part of the
cross-language block-count contract, so left rather than half-done.

## Scaffold markers to remove

Two resource strings exist only to say a feature is not built, and both should go with the
feature that replaces them — along with the handlers that show them in
`MarketTurnoverPage.OnFetch`, `OnExport`, `StockVolumePage.OnFetch`, `OnExport`,
`OnSearchTextChanged` and `OnSearchSubmitted`:

- `StudioDataLayerPending`
- `StudioEncoderPending`

They are deliberately shown through the pages' own status bar rather than as disabled buttons
with no explanation, so the state is legible rather than looking like a fault. That also means
they are easy to leave in by accident: fourteen languages each, and nothing in the build will
mention them.

## The fifth page, and what reusing a renderer actually cost

**Gain-loss Calendar** is the whole-market page's return view freed from its fixed series. The
claim worth writing down is that it has **no renderer of its own**: `CalendarHeatmapRenderer`
takes whatever `TurnoverSeries` it is handed, so "any stock or index" is one loader
(`InstrumentCalendar`) that shapes one instrument's bars into that record, behind
`Metric.Return`. The same grid, colour ramp, closing cards and extremes as the whole-market
form — because they are the same code, not because they were re-implemented.

- **The subtitle had a name baked in.** `ReturnMetric.Subtitle` was a fixed string ("上证指数 ·…")
  because the whole-market page's returns come from one venue. Naming an arbitrary instrument
  meant a new `TurnoverSeries.ReturnSource` field and a `{0}` in the resource string — the
  whole-market page passes the composite's name, the calendar page passes the fetched one, and
  the rendered line is unchanged on the page it came from. The lesson generalises: a fixed
  string is a field that was never asked for.
- **`StockBarsAsync` is the universal loader.** Its guard accepts any sh/sz/bj-prefixed code and
  the endpoint answers indices as happily as stocks — and it extracts the instrument's display
  name from the response's `qt` block, which `DailyBarsAsync` throws away. One round trip, bars
  and name together. The `qfqday`-preferred parse is also right for a price-change calendar.
- **Day zero is 0%**, as on the whole-market page. The alternative — fetching one bar before the
  range so the first day has a real change — makes the first cell depend on a day the calendar
  does not show, and the two pages must agree on that or the same range draws different pictures.
- **The watchlist is shared with the per-stock page** by writing the favourites key under that
  page's preferences prefix. This is the one deliberate cross-page key: a favourite is a fact
  about the instrument, not about the page it was added on, and two lists would drift apart the
  moment either is edited.
- **The suggestion list is filtered to A-shares** — the bars endpoint's guard is an 8-character
  two-letter-plus-six-digit shape, and a Hong Kong row that refuses on click is a suggestion
  that lied. Typing a raw code is normalised the same way and refused with the same message.
- **Found by testing, not building:** the nav item showed the literal text "NavigationViewItem"
  — the resource key was written as `NavGainCalendar` where the x:Uid mechanism reads
  `NavGainCalendar.Content`. `Strings.Get` silently returns the key for unknown keys; the XAML
  compiler does not check uid keys at all. **Both gaps are silent, so neither is caught by a
  build** — a new x:Uid key's name must be checked against the control's property, not assumed.
- **Verified live, both paths:** 上证指数 by preset click, 贵州茅台 by typed code — each
  fetched (~4 s), covered, and the stock encoded to a 10 s 300-frame MP4: plain container, last
  frame against the cover at MAD 1.76 as-is versus 17.65 flipped. Driving caveat for next time:
  UIA's `SelectionItemPattern.Select` on an `AutoSuggestBox` suggestion does **not** fire
  `QuerySubmitted`, so the "pick a suggestion" path cannot be driven that way — type the code
  and press Enter instead.

## The market page's gain/loss view was removed, not ported

Once the gain-loss calendar had its own page on any stock or index, the whole-market page's
copy of the view had nothing left to offer: the same renderer, the same metric, and one
instrument that is a preset on the other page. Two places producing the same video is a choice
nobody needs. The view is gone from the combo, `ChosenMetric` collapsed back to
`Metric.Turnover`, and `TurnoverViewReturns` was deleted from all fourteen resw files (241 keys,
same order everywhere). **The `Metric.Return` strings stay** — the gain-loss calendar page uses
them through the same metric object; removing strings a live page still reads would be exactly
the kind of "cleanup" that is actually a regression.

What made the removal safe to verify: a saved preference of `View = 2` from the three-view era
falls through the restore's range check to the first view rather than throwing — the check was
written for a different reason, and this is the second time it has paid. Verified live: the
combo lists two items, the calendar form fetches and covers, and the exported frame is the
turnover heatmap, not the change calendar.

Resolved: the help documents now describe all five pages — the sector-race, matrix and gain-loss
calendar sections were added to all fourteen files (see "Help documents: the three missing pages").

## The notification-area icon, ported from AgolAdminKit

Closing the window used to end the app, because there was nothing to bring it back from.
The tray is that something: `H.NotifyIcon.WinUI` 2.4.1 (the reference app ships the same
version against the same net10 + WindowsAppSDK 2.5.1 stack), a `TaskbarIcon` in the
window's tree that outlives the window being hidden, a menu of Open and Exit, and a
Settings switch tied to the stored `ShowTrayIcon`. The two settings are one setting on
purpose: with the icon off there is no way back to a hidden window, so close then means
close — `CloseHidesToTray` is just `ShowTrayIcon`, and the app can never end up running
and unreachable.

Two findings worth keeping:

- **`MenuFlyoutItem`'s uid suffix is `.Text`, not `.Content`.** Written as `.Content` the
  app dies at launch with `XamlParseException: Unable to resolve property 'Content'` —
  the third instance of this bug class (after `NavGainCalendar` and `StockAddFavourite`),
  and again invisible to the compiler. When porting XAML from a reference, copy its resw
  key names before writing the markup.
- **`AppInstance.Activated` fires off the UI thread.** The second launch's
  bring-to-front call went straight from that thread to `AppWindow.Show()` and silently
  did nothing — no exception, no log, and a hidden window that stayed hidden. The fix is
  one line: `BringToFront` marshals through the window's dispatcher. The tray menu
  commands needed no such treatment; H.NotifyIcon dispatches those itself.

Verified live, every branch: close hides with the process alive; a second launch recovers
the window in about a second; the icon itself responds (Win+B, Enter reached and activated
it twice, independently); with the switch off, close exits the process; the switch state
survives a restart; and turning it back on restores close-to-tray. Driving note: real
window closes from a harness go through `PostMessageW(hwnd, WM_CLOSE, 0, 0)` — neither
`WindowControl.Close` nor `Alt+F4` is usable from `uiautomation`.

## Start with Windows, the third AgolAdminKit port

The startup task pairs with the tray: the declaration lives in the manifest as
`uap5:StartupTask` with `Enabled="false"` — Windows requires the declaration to exist
before the app may ask, but starting at logon is the user's decision, and Task Manager's
Startup tab shows the DisplayName where the user can override the app permanently. The
exe name inside the extension is spelled out; `$targetnametoken$` is rewritten on the
Application element and nowhere else, so tokenised it survives MakeAppx and fails real
package validation. When Windows launches the app through the task, the activation kind
says so, and the window stays hidden in the notification area instead of landing in
front of whoever just logged in — but only while the tray icon is on, since without it
the hidden app would be unreachable.

**The finding that cost an hour: changing the manifest requires a version bump.**
`Add-AppxPackage -Register` of an already-installed development package succeeds
silently when only code changed — every previous redeploy had done exactly that — and
fails with `0x80073CFB` ("already installed, reinstall forbidden") once the manifest
differs. Silently, in the first attempt, because the failure surfaced only as
`StartupTask.GetAsync` throwing "Couldn't find a StartupTask in the appx manifest with
the input taskId" at runtime — a message that reads like a manifest problem but is a
registration one. The diagnosis path that worked: the app's own log said what was
missing, the deployment log (`0x80073CFB`) said why re-registering had not taken, and
the fix was `Version="0.1.0.0" → "0.2.0.0"` in `Package.appxmanifest`. Data survives the
bump; removing the package first would not.

Verified live: the switch reads its initial state from Windows, enabling reports Enabled
and survives a full process restart (the state comes back from `StartupTask.GetAsync`,
not from the app's own storage), disabling likewise persists. Left disabled — running at
logon is the user's call, and the switch is where they make it.

## A market setting, and what the source can actually quote

Settings now picks **A-shares / Hong Kong / the United States**, default A-shares, stored like
the language and needing a restart for the same reason. Before writing a line of it, each page
was measured against the endpoint on each market — the point being that "the page could work on
Hong Kong" is a claim about the *source*, not about the market's existence, and only one of the
five turned out to be answerable either way by reasoning.

**Whole-market turnover is the one thing neither market can supply.** Hong Kong's codes are the
Hang Seng indices, each carrying the turnover of its own constituents; adding them
double-counts everything in more than one. The US index "amount" is its volume multiplied by
the index level — the level of the Dow is not a price anyone paid, so the product is a number
with no meaning. Both are worse than absent, because they sit on the same axis and look like
the real figure. That page is therefore **removed from the navigation** on those markets, not
left to draw nothing.

**The US minute endpoint answers with an empty body and code −1.** So Stock Volume keeps its
daily mode there and the mode radio group is hidden entirely rather than disabled — a control
that leads to an empty fetch is worse than no control.

**Hong Kong's sector breakdown is four coarse sub-indices** (finance, property, utilities, and
commerce & industry, which is the remainder once the other three are taken out and so carries
about seven tenths of the index). Coarse is what the source has; inventing a fifth list would
be worse than saying so. The US has no sector index at all, so the race runs on the ten SPDR
sector ETFs, which are mutually exclusive and exhaustive over the S&P 500 the way the CSI
Level-1 industries are over the A-shares.

**The amount field's unit belongs to the venue, not to the endpoint.** Ten thousand of it is
one 亿 in Shanghai, Shenzhen and Hong Kong; in New York the field is plain dollars, so a
hundred million of it is. One divisor for all three is a figure out by ten thousand, and
nothing on an axis label would make the difference visible — this was the single change most
likely to have shipped silently wrong.

Two more that were found because a wrong answer was indistinguishable from a right one:

- The search endpoint answers `usaapl.oq` while the chart endpoint will only read `usAAPL.OQ`,
  and answers a lowercase code with **no bars rather than an error** — which reads as an
  instrument with no history. Canonicalised where the code is first known.
- A US ticker with no exchange suffix (`usAAPL`) comes back as **one bar from 2011**. An error
  would have been better. The venues are tried in turn and the first that answers with a real
  history wins.

**Owed:** the US calendar/matrix totals column carries the index's synthetic amount, because
that figure only feeds the animation plan's axis maths and is never drawn — but it is not a real
number and would be wrong the moment anything displays it. And Hong Kong's four sub-indices have
never been watched through a full race; the data is there, the picture has not been looked at.

## The sixth page — the DCA plan, and what years cost the data layer

**DCA Plan** is built: `DcaPlanner` (the loader), `DcaRenderer` (two lines on one axis —
invested in amber, value in red, the gap between them filled warm or cool — with the ratio
as the headline reading and four closing cards), and `DcaPlanPage` on the same page skeleton
as the calendar: search, one-tap presets, favourites shared with the per-stock page,
cadence/span/amount, the shared video panel. Twenty-nine keys in all fourteen resw files
(now 307 keys, same order everywhere, `fffd=0`), and a help section in all fourteen
documents (twelve sections each, block counts equal).

**Every preset code was probed against the endpoint before being written down** — seven
A-share (broad ETFs, gold ETF, a Nasdaq tracker, two indices), five Hong Kong, five US —
and all seventeen answered with bars and a display name (`artifacts/verify-dca-endpoint.txt`).
The pagination facts the planner is built on were measured the same way: **640 bars to a
request, confirmed**, and five requests reach 2013-07 for 沪深300ETF, 2013-09 for the
Tracker Fund and 2014-01 for SPY — so "as far back as available" is about a dozen years on
all three markets, and the twenty-request backstop in `DcaPlanner` is twice what the
deepest plan needs.

**Verified live through the running app** (driven by UI Automation, screenshots in
`artifacts/dca-state*.png`):

- **Fetch:** 沪深300ETF, every trading day, ¥100, past three years → status reads
  「已取 726 个交易日（2023-09-26 至 2026-09-24），定投 726 期」, the frame drew
  +17.0% with 市值 8.8万 against 投入 7.4万. The ten-year plan had been fetched by hand
  earlier the same day: 2016-05-03 → 2026-09-24, **2,429 buys**, +35.4% — which is the
  four-request walk producing a real plan, seen with eyes.
- **Cover:** 1080×1920 PNG written to the remembered folder, name carrying the span.
- **Export:** 45-second 1080p30, **18.9 s wall time**, 7.5 MB, boxes
  `ftyp`/`uuid`/`mdat`/`moov` with no `moof`, `mvhd` exactly 45.00 s, `stsz` 1,350 =
  45 × 30 — one sample per frame drawn. Same `VideoExporter`, nothing new to trust.

**Three driving traps from tonight, all reusable:**

- **A control handle captured before a click hangs forever when read afterwards.** Not an
  exception, not a timeout — the property get blocks. Every poll must re-find the control;
  a fresh search costs milliseconds and cannot hang.
- **A button scrolled out of its panel reports `BoundingRectangle` 0×0 and `IsOffscreen`
  true, and both `Click` and `Invoke` silently do nothing useful from there.** Scroll the
  ancestor `ScrollViewer` until `IsOffscreen` is false, then invoke.
- **Endpoint latency swung from seconds to minutes tonight** (a five-year, three-request
  fetch took minutes; a three-year one took seconds). A poll loop that assumes seconds
  misreads a slow fetch as a hang, and the page's own three-minute timeout is the clock to
  trust — when it fires the status says so.

**Owed on this page:** the Hong Kong and US preset lists have never been fetched through
the page; the weekly and monthly cadences have never been run (only daily); the saved
instrument falling back to the market's first preset has not been exercised; and the export
has been through 1080p30 only, like every page's first export.


## The seventh page — Position Return, and the negative-close trap

**Position Return** is built: `PositionLoader` (one purchase at the range's first close, then
mark-to-market), `PositionRenderer` (flat capital line against the value line, fill coloured
by which is on top, ratio as the headline, drawdown promoted to a closing card), and
`PositionPage` on the shared skeleton. Thirteen new keys (now 307, same order everywhere,
`fffd=0`), help section fourteen times (twelve sections each). Both year-long pages now
share `HistoryWalk.ClosesAsync`, the backwards walk the plan page grew.

**The trap this page found: the forward-adjusted series can go through zero.** 中国平安's
qfq closes arrive **negative** for 280 trading days (2013-09 → late 2014, worst −5.09),
because the forward adjustment rebases to today and a decade of dividends pushes the early
years under. A ratio chart survives this; a page that *buys at a price* does not — shares
come out negative and the frame draws a −1,146% holding, which is exactly what the first
live fetch did. The fix is not a clamp: **both year-long pages now ask for `hfq`**, the
backward-adjusted series, which anchors at the listing so every close is positive and the
ratio between two days is the real total return with dividends reinvested. Hong Kong and US
rows come back unadjusted whatever is asked (`day` alone), which for those venues is the
same question. `StockBarsAsync` grew an `adjustment` parameter (default `qfq`, so the ratio
pages are untouched); **the parameter must be passed through both of its own call sites** —
the bare-US branch *and* the main path. The main path was missed on the first pass and the
page kept drawing qfq numbers; the debug log in `FetchStockBarsAsync` (param + response keys,
temp) is what found it, and the log is removed now.

**Verified live through the running app**: 中国平安, ¥1,000,000, longest range — status
「已取 3,160 个交易日（2013-09-26 至 2026-09-24），持有 4,746 天」, frame reads
**+301.0%**, cards 市值 407万 / 本金 100万 / +307万 / **−53.8%** drawdown. Cross-checked
against an independent fetch: hfq buy 38.76, last 155.43, +301.0% — the frame and the
spreadsheet agree. The qfq pathology was reproduced in the log before the fix and is absent
after it.

## The help documents carry pictures

Five of the fourteen chapters — sector race, return matrix, gain-loss calendar, DCA plan and
holdings return — now open with a screenshot of the page they describe, so the words have
something to point at. The other chapters have none: there is no screenshot of the settings page
yet, and the whole-market chapter's page does not exist in every market.

`HelpDocument` learned one line shape, `![caption](media/sector-race.png)` on a line of its own,
and draws it as a bordered card with the caption in small grey text under it. Everything else
about the renderer is unchanged, including what it does with lines it cannot lay out.

**The pictures are per language and the documents are not.** A reference names one file;
`media/x.png` resolves to `media/<tag>/x.png` first and to `media/x.png` second, with `<tag>` read
off the document's own file name — the same decision that chose the manual. Fourteen folders, five
pictures each, taken from that language's own store screenshots so a Japanese manual shows a
Japanese window. The reference inside the prose stays identical in all fourteen files, and the
captions are the five-per-language sentences in `tools/port-help-images.py`.

They are built by `tools/help-media.py`, which crops the title bar, the navigation rail and the
window border off the store captures — at the manual's column width a whole window prints as a
smudge, and the controls are the reason the picture is there. **70 files, 7.6 MB.** The package
was 63.4 MB before this; expect roughly 71 MB for the next one, and measure rather than assume.

Insertion is `tools/port-help-images.py`, by chapter *number* rather than heading text — the
headings are translated, so matching on them would need a table of fourteen titles. It is
idempotent and verified: all fourteen documents went from 72 blocks to 77, all fourteen the same.

**Verified by running it**: the help page renders five bordered cards with legible screenshots at
the manual's column width, each with its caption; `crash.log` carries no `Help picture missing`
line, so all seventy resolutions found their file. **Verified in the 1.0.1.0 Store package (2026-09-29)**: all seventy files survive, across all
fourteen `media/<tag>/` folders, alongside the fourteen help documents, `resources.pri` and
Win2D's native `Microsoft.Graphics.Canvas.dll` for x64, x86 and arm64. The inner x64 and arm64
packages are ~74 MB each, so the bundle — 148.8 MB as a `.msixupload` — is not what a device
downloads; the Store serves one architecture.

## 1.0.3.0, and what the eighth page left owed

**1.0.2.0 was built and never uploaded.** Its `.msixupload` (`artifacts/`, 2026-10-01 11:34) was
never sent to Partner Center, so its entry in the CHANGELOG — page navigation, the adjustment
basis across all three markets — describes something no user has. 1.0.3.0 carries it. If a
1.0.2.0 upload ever happens, the next number has to clear 1.0.3.0.

**The Store gallery is three pages short.** `tools/store-screenshots.py` walks the seven pages that
existed when it was written, and the listing copy — bumped to ten at the user's instruction, ahead
of the release that carries them — names all ten in all fourteen languages. Capturing the candle
page, the market-cap board and the A+H page is what closes it; nothing else about the listing is owed.

**And the copy now describes a build nobody has.** The market-cap board is unreleased: the
`artifacts/` package is 1.0.3.0 and carries eight pages, so the listing and the newest package
disagree until the next version is cut. That is a deliberate state, not an oversight — the copy is
written for the version being prepared — but it does mean **the listing must not be uploaded before
the package that matches it.** The alternative (leave the copy at eight until the package exists) was
rejected: the copy is the thing that gets forgotten at the end of a release, and a listing that
already names the page is one less thing to remember.

**Owed on the candle page:** the Hong Kong market has not been fetched through it at all (the
A-share and US paths are 18 checks each); the weekly and monthly periods have not been driven
through the page; and no export has been run at any format other than the default. Scrolling
animation has been watched, growing has been watched; neither has been *encoded*.

**Owed on the custom spans:** the two date boxes cannot be driven through UI Automation — a
WinUI `DatePicker` exposes a `FlyoutButton` and no scrollable ancestor, so `verify-custom-range.py`
asserts the panel appears and that a fetch returns the custom span, rather than setting the dates
themselves. The reversal and over-length refusals are therefore asserted through the loader
(`CandleLoader.WalkAsync`, `HistoryWalk`) rather than through the UI. If a picker ever needs to be
driven, that is the wall and it has not been climbed.

**Owed on the help documents:** they carry seventeen chapters now, and five of them still have
pictures — the candle chapter has none, so the manual describes the newest page with no picture
while four older ones have one.

**Three reusable findings from this round**, all already recorded where they belong — in the
skills, not here: a WinUI 3 combo's popup items live in the *main window's* own UIA tree, so
excluding the window finds nothing and including it finds the navigation pane too, and the popup
has to be told apart by what opening the combo added; the settings page's scroller is a
`PaneControl` in UIA, not a `ScrollViewer`, which is why every earlier attempt to scroll it did
nothing; and — the one that cost a run — **"the popup added nothing" has to be the wait condition,
not "a row exists"**, because the walk returns the navigation pane's eleven rows whether or not the
menu opened, so a poll that stops on "any rows at all" returns the navigation pane the instant it
starts and the caller compares that against a written-out list. `combo_labels` answered with the nav
items and the page was reported as having no range options at all.

## The market-cap board: what it was built on, and what it owes

**Why the board is a field rather than a fixed fifteen.** The first version fixed fifteen listings
and ranked those against each other. It was built that way on a cost estimate — a daily series is
about 640 calendar days to a request, so a wide field over ten years is thousands of requests — and
the estimate was wrong: **the monthly endpoint returns three hundred bars in one reply**, on all
three venues, so the field costs one request per listing and the board is rebuilt month by month.
The board now shows the fifteen largest at each moment, and its membership changes: December 2016 is
ICBC, CCB, PetroChina, Bank of China, ABC, China Life, Sinopec, Merchants Bank; September 2026 has
replaced several of them with 茅台, 宁德时代, 工业富联, 紫金矿业 and 比亚迪.

**The month-to-date bug that the first run of it found.** The axis was the plain union of every
date in the field, and a monthly row is dated on the month's last *trading* day — which for a
listing suspended mid-month is mid-month. Sixty-two listings' dates then come to 139 for a hundred
and twenty months, and in each of those nineteen extra "periods" one listing advanced while the
other sixty-one carried a stale value. Grouped by `(year, month)` and dated on the group's latest,
it is 120. The same class of mistake is available to any page that builds a date axis from more than
one instrument.

**The ranking source, and why there is one.** The field started as a hand-written list of
sixty-two names and that was a mistake with a date on it: 长鑫科技 listed, became the largest
company on the mainland — **37,194 亿, ahead of 工商银行** — and the board did not carry it. Nothing
about writing the list more carefully would have helped; the list was written before the company
existed. The field is now today's top two hundred, asked of a ranking endpoint at fetch time.

Tencent has no ranking. Three paths were tried and three came back empty or refused:
`stock.gtimg.cn/data/index.php?appn=rank&t=ranka/...` → `data:''`; `cgi-bin/rank/pt/getRank` →
`{"rank_list":[],"total":0}`; `cgi-bin/rank/hs/getBoardRankList` → HTTP 400. Sina's
`vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData` works:
`?page=1&num=100&sort=mktcap&asc=0&node=hs_a` returns the mainland sorted by market value, **capped
at a hundred rows per page** (asking for 150 returns 100), `mktcap` in 万元, and `symbol` in the same
shape the quote source uses. Its `node=hk_stock` and `node=us_stock` both answer `[]`, which is why
Hong Kong and New York keep a fixed field.

**Eastmoney was tried first and refused to answer** (`push2.eastmoney.com/api/qt/clist/get?fid=f20`
worked once and then closed the connection on every subsequent attempt). It is the ranking endpoint
most projects reach for, and this one being rate-limited out of the running on the first day is
worth knowing before reaching for it again.

**The archive, with the values it was built on** (snapshot endpoint, 2026-10-01).
Kept because these are literals in `MarketCaps.cs` and a literal nobody can re-check is a literal
that rots. **The mainland's entries are an archive now, not the field**: the field is asked for at
fetch time (today's top two hundred), and what stays in the file is the companies that used to be up
there and are not any more — the ones a ten-year board needs and a ranking cannot supply. Hong Kong
and New York have no ranking to ask, so there the table *is* the field. The A-share rows below are
the state when the page was built, then grown to sixty-two; the 93 additions were each read back
from the snapshot endpoint in the same session (all valid, venues included) before being written
down. Total market value in 亿 of the venue's currency:

| A-share | | Hong Kong | | United States | |
|---|---|---|---|---|---|
| sh601398 工商银行 | 29,510 | hk00700 腾讯控股 | 39,189 | usNVDA 英伟达 | 55,147 |
| sh601939 建设银行 | 28,933 | hk00005 汇丰控股 | 27,084 | usAAPL 苹果 | 48,602 |
| sh601288 农业银行 | 24,394 | hk01398 工商银行 | 27,479 | usGOOGL 谷歌 | 42,081 |
| sh601988 中国银行 | 21,685 | hk00939 建设银行 | 25,689 | usMSFT 微软 | 38,086 |
| sh600941 中国移动 | 20,780 | hk09988 阿里巴巴 | 21,215 | usAMZN 亚马逊 | 26,874 |
| sh601857 中国石油 | 20,517 | hk03988 中国银行 | 19,607 | usMETA Meta | 18,474 |
| sh600519 贵州茅台 | 15,734 | hk00857 中国石油 | 17,689 | usAVGO 博通 | 16,765 |
| sz300750 宁德时代 | 13,470 | hk00941 中国移动 | 17,233 | usTSLA 特斯拉 | 14,013 |
| sh601138 工业富联 | 11,549 | hk01299 友邦保险 | 7,615 | usBRK.B 伯克希尔B | 10,660 |
| sh600036 招商银行 | 10,406 | hk01810 小米集团 | 6,511 | usLLY 礼来 | 10,314 |
| sh601628 中国人寿 | 10,373 | hk09999 网易 | 6,166 | usJPM 摩根大通 | 8,794 |
| sh601088 中国神华 | 10,368 | hk00386 中国石化 | 5,336 | usWMT 沃尔玛 | 8,245 |
| sh601318 中国平安 | 9,650 | hk00388 香港交易所 | 4,917 | usV Visa | 6,746 |
| sh601899 紫金矿业 | 7,921 | hk03690 美团 | 4,428 | usXOM 埃克森美孚 | 6,692 |
| sh600028 中国石化 | 6,374 | hk09618 京东集团 | 2,804 | usORCL 甲骨文 | 4,162 |

**The snapshot endpoint and the chart endpoint want the code in opposite shapes.** `usAAPL.OQ`
is the only thing the chart endpoint reads and the only thing this one *silently ignores* —
`usAAPL` is the only thing it answers. Not an error on either side: the wrong shape comes back
as no data, so a board built on chart codes fetches fifteen sets of prices and no market values
at all, which reads as "this endpoint is empty". `StockDirectory.SnapshotCode` strips the venue
and `usBRK.B.N` keeps its own dot.

**A fix the tenth page of history forced.** `FetchStockBarsAsync` threw on a response with no
bars, so the first window the walk asked for that lay entirely before a listing existed ended a
fetch that had already gathered nine years. 中国移动 listed on the mainland in 2022; a ten-year
window reaches past that by construction. The bare-US-ticker path had already settled the rule —
"nothing in this window is not the same as nothing under this name" — and the main path now
follows it: an empty window is an empty window, which is what `HistoryWalk`'s stop condition
reads it as. **Anything else that walks backwards past a listing date would have hit this.**

**A shared renderer speaking for data it cannot see.** The market-cap board draws through the sector
race's renderer, and that renderer ended its header line with `Strings.Get("StockTradingDaysUnit")`
— the word 个交易日, written into the drawing code. It was true for the page it was written for and
false for the page that inherited it: twelve months of market-cap data were announced as "12 个交易日"
in every frame, and the frame is the artefact that outlives the app. The count word was already
supplied by the page (`UnitWord`) for exactly this reason; the span word is now too (`SpanWord`), and
the renderer keeps only a fallback for the daily case it was built for. **The test of a shared
renderer is not "does it draw the same shape" but "does every word it draws belong to the caller"** —
`verify-marketcap.py` now asserts the renderer no longer carries the day word at all.

**And a string table will not catch it either.** The unit is not a translation problem: the 14
languages all read correctly, and the resw file's own copy of the page never mentions trading days
because it counts 期. The wrong word came out of the *drawing* code, so a translation sweep passes
and the frame is still wrong. `MarketCapUnitMonths` / `MarketCapUnitCandidates` are checked for
content as well as for presence now — a key that is the right shape and the wrong word is what this
costs.

**Owed on this page:** Hong Kong and New York have not been driven through it (the lists were
read back from the snapshot endpoint, which is how they were chosen, but no page fetch has run
against either); the custom span has not been exercised; no export has been run at any format;
and the sector race's own regression after the renderer's name-gutter change was checked only by
eye — the marketplace board's screenshot, not a re-run of `verify-*` for the race. The header's own
wording is now checked on the market-cap side only, and by source rather than by pixels: the line is
drawn into the preview surface, so there is no UIA node to read and no text in a screenshot to
assert on.

## The A+H page: what the list is, and what it owes

**The field, as measured on 2026-09-30** — the month every pair last has a settled close for. Premium
is `A ÷ (H × HKD/CNY) − 1`, computed from **unadjusted** prices on both legs; the source was read
again for every row here, and all sixty-nine answered. Kept because these codes are literals in
`AhPremium.cs`, and a literal nobody can re-check is a literal that rots — **and one already did**:
海通证券 was in the list when the page was designed, and its H shares were delisted after the merger
into 国泰海通, so the field is seventy minus one rather than seventy.

| pair | company | premium | months |
|---|---|---|---|
| `sz000756` / `hk00719` | 新华制药 | +194.0% | 123 |
| `sh601238` / `hk02238` | 广汽集团 | +191.0% | 123 |
| `sh601992` / `hk02009` | 金隅集团 | +165.8% | 123 |
| `sh601991` / `hk00991` | 大唐发电 | +132.8% | 123 |
| `sh601788` / `hk06178` | 光大证券 | +127.5% | 116 |
| `sh601633` / `hk02333` | 长城汽车 | +122.5% | 123 |
| `sh601618` / `hk01618` | 中国中冶 | +120.3% | 123 |
| `sz000166` / `hk06806` | 申万宏源 | +112.8% | 84 |
| `sh601800` / `hk01800` | 中国交建 | +106.4% | 123 |
| `sz000898` / `hk00347` | 鞍钢股份 | +105.3% | 123 |
| `sh600188` / `hk01171` | 兖矿能源 | +98.6% | 123 |
| `sh600029` / `hk01055` | 南方航空 | +90.7% | 123 |
| `sh601881` / `hk06881` | 中国银河 | +89.0% | 111 |
| `sh600808` / `hk00323` | 马钢股份 | +82.0% | 123 |
| `sz000002` / `hk02202` | 万科A | +78.8% | 117 |
| `sh600958` / `hk03958` | 东方证券 | +77.4% | 117 |
| `sh601111` / `hk00753` | 中国国航 | +75.2% | 123 |
| `sh600332` / `hk00874` | 白云山 | +73.5% | 121 |
| `sh601607` / `hk02607` | 上海医药 | +71.4% | 123 |
| `sz000513` / `hk01513` | 丽珠集团 | +69.5% | 123 |
| `sh601319` / `hk01339` | 中国人保 | +66.5% | 89 |
| `sz300759` / `hk03759` | 康龙化成 | +65.5% | 81 |
| `sh600938` / `hk00883` | 中国海油 | +63.3% | 54 |
| `sh601186` / `hk01186` | 中国铁建 | +61.8% | 123 |
| `sz003816` / `hk01816` | 中国广核 | +60.5% | 81 |
| `sh601390` / `hk00390` | 中国中铁 | +57.4% | 121 |
| `sh601898` / `hk01898` | 中煤能源 | +56.1% | 123 |
| `sh601628` / `hk02628` | 中国人寿 | +52.8% | 123 |
| `sh600196` / `hk02196` | 复星医药 | +52.3% | 123 |
| `sh600115` / `hk00670` | 中国东航 | +51.4% | 123 |
| `sh600362` / `hk00358` | 江西铜业 | +48.7% | 123 |
| `sh601336` / `hk01336` | 新华保险 | +46.5% | 123 |
| `sz300347` / `hk03347` | 泰格医药 | +45.9% | 74 |
| `sh600028` / `hk00386` | 中国石化 | +39.9% | 123 |
| `sh600999` / `hk06099` | 招商证券 | +37.6% | 114 |
| `sz000776` / `hk01776` | 广发证券 | +36.8% | 123 |
| `sh600011` / `hk00902` | 华能国际 | +36.6% | 123 |
| `sh600027` / `hk01071` | 华电国际 | +36.4% | 123 |
| `sh601766` / `hk01766` | 中国中车 | +36.0% | 123 |
| `sh601857` / `hk00857` | 中国石油 | +35.8% | 123 |
| `sh601600` / `hk02600` | 中国铝业 | +34.7% | 119 |
| `sh601939` / `hk00939` | 建设银行 | +31.9% | 123 |
| `sh600026` / `hk01138` | 中远海能 | +31.6% | 123 |
| `sh601211` / `hk02611` | 国泰海通 | +31.2% | 108 |
| `sh603993` / `hk03993` | 洛阳钼业 | +30.5% | 123 |
| `sh601988` / `hk03988` | 中国银行 | +29.5% | 123 |
| `sh601601` / `hk02601` | 中国太保 | +29.2% | 123 |
| `sz002594` / `hk01211` | 比亚迪 | +29.0% | 123 |
| `sh601888` / `hk01880` | 中国中免 | +28.7% | 50 |
| `sh600585` / `hk00914` | 海螺水泥 | +26.8% | 123 |
| `sh601088` / `hk01088` | 中国神华 | +26.2% | 121 |
| `sh601818` / `hk06818` | 光大银行 | +25.8% | 123 |
| `sh601398` / `hk01398` | 工商银行 | +25.7% | 123 |
| `sh601688` / `hk06886` | 华泰证券 | +25.1% | 123 |
| `sh601998` / `hk00998` | 中信银行 | +24.2% | 123 |
| `sh600030` / `hk06030` | 中信证券 | +24.1% | 123 |
| `sh601288` / `hk01288` | 农业银行 | +23.1% | 123 |
| `sh600016` / `hk01988` | 民生银行 | +18.6% | 123 |
| `sh601318` / `hk02318` | 中国平安 | +18.3% | 123 |
| `sh600690` / `hk06690` | 海尔智家 | +18.1% | 70 |
| `sh601919` / `hk01919` | 中远海控 | +15.8% | 122 |
| `sh601658` / `hk01658` | 邮储银行 | +15.4% | 81 |
| `sh600660` / `hk03606` | 福耀玻璃 | +14.8% | 123 |
| `sh601328` / `hk03328` | 交通银行 | +8.5% | 123 |
| `sh601899` / `hk02899` | 紫金矿业 | +8.2% | 123 |
| `sz000338` / `hk02338` | 潍柴动力 | +2.3% | 123 |
| `sz000333` / `hk00300` | 美的集团 | +2.2% | 25 |
| `sh600036` / `hk03968` | 招商银行 | -6.2% | 123 |
| `sh603259` / `hk02359` | 药明康德 | -9.0% | 88 |

**The trap this page is built around.** Both legs must come from the *unadjusted* series. The rest of
this app fetches `qfq`/`hfq` on purpose — a return is a ratio and adjustment is what makes a decade
comparable to itself — but a ratio between two markets adjusted separately is a ratio between two
different scales. ICBC's A share sells at 8.28 and the backward-adjusted series reports 13.34, so the
first version of this page's own probe reported a +245% premium on a stock trading at +26%, and the
same probe read 招商银行 at +404%. `TencentKline.RawBarsAsync` is the empty-adjustment call that
fixes it, and it exists for this page. **An empty adjustment at the general endpoint returns the plain
block**; `hkfqkline` cannot do it, answering an empty adjustment with `data: []`.

**The axis is a month, and it has to be.** The A share's month closes on its last trading day, the H
share's on the last business day, the rate's on the last banking day — three different dates in most
months. Intersecting on the date found 94 months where there are 123. Grouped by year and month, and
dated on the month's own last day, they line up. This is the third time this project has paid for the
same lesson (the market-cap board reported 139 periods for 120 months).

**"The value is wrong" was a reading, not a computation.** The first doubt raised against this page
was that 新华制药's premium "is about 65%, not 194%", with a screenshot of the frame. It was the
direction: 雪球 prints the same company on the same close as `溢价(H/A) −65.97%`, and the page prints
A against H, so the two are the same fact — 1 ÷ (1 − 0.66) − 1 = 1.94. Checked against two other
sources before answering, because "the reader read it the other way" is also a convenient thing to
believe: 東方財富 quoted 比价(A/H) 2.82 / 溢价(A/H) 181.80% on 2026-09-25 and 經濟通 189.1% on
2026-09-23, both of which bracket the page's own +193.96% for 2026-09-30. Both close prices were also
read back from two sources independently (Tencent 14.60 / 5.815, Sina 14.600 / 5.815). **What changed
was wording, not arithmetic**: the card's method note and all fourteen manuals now say the other
direction exists and is the same number. The same pass fixed a real defect found while in there — the
Spanish manual had a literal `/n` where a line break was meant, in the one bullet it was easiest to
miss.

**Owed on this page:** the English interface has not been driven through it, and no export has been
run at any format — the preview and the encoder share a renderer, so an export is the other half of
the verification. The custom span has not been exercised. The frame has been read at two spans
(three years: 68 pairs, 36 months; the longest: 52 pairs, 123 months) plus one independent
recomputation of the dearest premium, which matched the page to 0.04 of a percentage point.

## The eleventh page: extreme days

One instrument, and the days it moved the most — horizontal bars ranked by size. **The row is a
day**, which no other page here does, and it inverts what a race is: every other board gives a racer
a value that moves day by day, and this one gives a row a value that is fixed the moment that day
closed. What moves is membership. A day is worth nothing until it happens, so the board fills in as
the years pass, and a day larger than the fifteenth takes its place and pushes someone off. The
field is twenty-four candidate days, the frame draws fifteen.

**Ranked by magnitude, and that is the page's whole argument.** −7.7% and +8.1% are the same size of
move and belong next to each other; ranking the signed values files every fall below every rise, and
the board becomes a list of good days with the crashes underneath. Bars grow both ways from the zero
axis — a rise to the right in red, a fall to the left in green — which is also the first board whose
bars are coloured by what the row says rather than by a hash of its code: a company is a thing a
viewer follows up a board, and a day is not.

**Days that have not happened yet are not on it.** This is the one that needed a renderer change.
Before its own date a row is worth zero, and ranked by magnitude it sits at the bottom of the
field — which is not far enough, because twenty-four candidates of which five have happened still
fill a fifteen-row frame, ten of them reading 0.00%. `HideEmptyRows` skips a row whose value is zero
*at that day*, and that is also what makes the board visibly fill up instead of starting full.

**The move is the change in the adjusted close.** An ex-dividend day is not a crash: the price drops
by the dividend that morning, and an unadjusted series would put that day at the top of a board of
the largest falls in history, when nobody holding the stock lost anything. Indices are what the page
is asked about normally and there the distinction is invisible, which is why it is stated rather
than left to be discovered on a stock.

**Measured on 2026-10-02**, A-shares, ten years: 24 candidate days over 2,427 trading days,
biggest 2024-09-30 +8.06%, bottom of the drawn board 2018-10-22 +4.09%. The same span on 深证成指
gave +10.67% and a −5.31% at the bottom, which is what proves the sign is carried and the ranking is
by size. Both figures were recomputed independently by `tools/verify-extremedays.py` straight from
the source's daily bars, and matched to two decimals. `verify-extremedays.py` is 32 checks, 32 pass.

**The longest span is about thirty-five years**, which is the walk's limit and not a choice: one
request carries about 640 daily bars and the walk makes twenty. Its label is its own key rather than
the plan page's "longest", because that one says thirteen years for its own reason — a label borrowed
across pages is a label that lies on one of them.

**Two defects found in the A+H page while this one was being built**, both fixed here:
- `AhPremiumCount` carries a `{0}` for the board's size and the page read it with `Strings.Get`, so
  the panel showed a literal "{0}". Now formatted. The new page copied the defect and fixed it in the
  same pass; both pages now have a check asserting the placeholder is gone.
- `AhPremiumFetched`'s fourteen values are read positionally, and the slot en-US reads held the
  Chinese string — the English interface reported a whole status line in Chinese. No UI test running
  in Chinese would see it, so the check is against the file: the English value must contain no CJK.

**A third defect, found by the app refusing to start.** The new nav item's key was written
`NavExtremeDays.Text`; a NavigationViewItem is a ContentControl and the `x:Uid` loader asks for
`.Content`. `MainWindow.InitializeComponent` threw `Unable to resolve property 'Text' while
processing properties for Uid 'NavExtremeDays'` — a crash on launch, three times, recorded in
`crash.log`. The load-bearing part is that the crash log said exactly which Uid and which property.

**The bug worth remembering: a renderer option that has to be a constructor argument.** Ranking by
magnitude was written as a property, because that is how the renderer's other options are spelled
(`UnitWord`, `SpanWord`, `HideEmptyRows`, `ColourBySign`) — and the ranking table is built **inside
the constructor**, which runs *before* an object initialiser. So `new SectorRaceRenderer(…) {
RankByMagnitude = true }` sorted by sign and said nothing at all. The frame drew the eight biggest
rises and the seven smallest falls: on 上证指数 over ten years the second, third and fourth largest
moves are all crashes (−7.72%, −7.34%, −6.62%), and the first build showed none of them, with the
board's bottom at +4.09% instead of −7.72% at the top of the field. **Nothing in the UI could
distinguish it from a correct board** — the board filled, the bars were red and green, the numbers
were real, and the layout was exactly what the page would have drawn if the index had no crashes.

It survived the first verification run, which was 32 checks and passed, because **the status line
ranks by magnitude itself** — the page reports its own standings and those were right — while the
renderer was drawing a different board. What catches it is the pixels: the frame is captured, cropped
to the preview's own rectangle and its red and green pixels are counted, because a board of the
largest moves either way on an instrument that has crashed must show both. That check was added and
the option became the constructor's fifth parameter, with a check that the page passes it as an
argument and *not* as an initialiser.

**Owed on this page:** the English interface has not been driven through it (the instrument names and
the row labels are checked another way — every broad index has an `INST*` key in all fourteen
languages, and a row's name is an ISO date, which needs no translating); no export has been run at
any format; the custom span has not been exercised; nor has the Hong Kong or United States market
been through it.

## The twelfth page: currency corridors

One row per pair, and **the row is the range itself** — the floor and the ceiling the pair has
traded between in the span — with the rate as a marker somewhere along it. This is the board where
a row is a *place* and not a quantity: everywhere else here a bar's length is how much of something
a racer has, and here the row is drawn full width in every frame because a corridor is a place. What
moves is the marker, and the walls.

**The walls expand.** They are the lowest low and the highest high **so far**, not over the whole
span. A fixed ruler with a dot sliding along it would be a gauge, and the picture would measure
today against the extremes of a range that had not happened yet; an expanding corridor is a record,
and it visibly widens as the years pass — which is also why a pair can sit at 100% and stay there:
100% is "the dearest this pair has ever been in this span", not a limit being touched.

**Every pair is measured against itself, and that is the whole trick and the whole cost.** 157.92 on
USD/JPY and 1.1245 on EUR/USD are not two points on one scale, and normalising each corridor is what
lets six pairs share one board. The cost is that a narrow corridor and a wide one are drawn alike,
so the floor and the ceiling are printed under every row — the only place on the frame that says
which is which. Without those two numbers the board would be six bars of the same length.

**Two lists, because the source's coverage is not one shape.** Measured 2026-10-02:

| list | pairs | coverage |
|---|---|---|
| renminbi | USD/CNY 316 months from 2005-10; EUR, HKD, GBP, AUD, CAD 124 from 2016-01 | not one start |
| crosses | EUR/USD, GBP/USD, AUD/USD, USD/JPY, USD/CHF, USD/CAD — 325 months each, all from 2005-07 | one start |

On one board together, what a viewer reads is when the source started quoting each pair, which
nobody asked about. The renminbi list also means the board is not full at its longest span: five of
its six pairs have no rate before 2016, and a pair with no rate is not a pair at 0% — it has no
position, so it is left off the board and out of the ranking rather than pinned to the floor.

**Monthly, and one request per pair.** 325 months against a 430-month ceiling, so the whole history
comes back in one reply and "as far back as there is" costs six requests instead of a hundred and
twenty. Unadjusted, on the same `RawBarsAsync` path the A+H page uses: a currency has no dividend
and no split, and an adjustment on one side of a comparison compares two different things.

**A month the source has not finished is not on it**, which is `CandlesFromAsync`'s settled-period
rule and not this page's — fetch on 2 October and the last month on the board is September. It cost
three failing checks to find, and the failing side was the script: `verify-fxcorridor.py` fetched
the month in progress, so it carried one month more than the app, and a corridor measured over a
different set of months has different walls and a different last close — 59.5% against the page's
61%, 1.8% against 0%. The app was right all three times. The rule is now stated in the script and
asserted against the source file, and the tolerance is back to one percentage point: 61 against
61.4, and 0 against 0.5.

**Measured 2026-10-02**, renminbi list, ten years: 113 months (the source's monthly coverage of a
ten-year window is 113–114, not 120 — it carries no bar for a handful of months), 6 pairs, highest
GBP/CNY at 61% of its own corridor, lowest CAD/CNY at 0%. The crosses over the same span put
USD/JPY highest at 89% and USD/CHF lowest at 27% — a board whose top and bottom are both far from
the middle, which is what a decade of one-way dollar strength looks like when each pair is measured
against itself. `verify-fxcorridor.py` is 37 checks, 37 pass.

**Owed on this page:** the English interface has not been driven through it (a pair's name is an ISO
code, the same in all fourteen languages, so there is no `INST*` key to miss — but the group names,
the card and the status line have not been read in English); no export has been run at any format;
the custom span has not been exercised; nor has the "longest" span been taken through either list.

## The thirteenth page: the index long run

**A row is a gain, not a level.** 3,800 on the Shanghai Composite and 5,700 on the S&P 500 are not
two points on one scale, and a board of levels would be a board about where each index happened to
start counting — so every row is how far its index has come since its own first month in the range.
Twelve indices, three markets, one axis, and `SectorRaceRenderer` with `RaceMetric.Return`: the same
renderer the sector race, the market-cap board and extreme days use, which is now four pages deep.

**Each index is measured from its own first month, and that is what makes the board fill up.** The
S&P reaches back to 1950, the Dow only to 2009, the Hang Seng Tech index starts in 2020. Measuring
from the window's first month instead would leave every late index with decades of nothing before
its first bar, which is a picture of when a source began quoting rather than of how the index did.

**A row that has not joined is absent, not parked at 0.00%.** Parked there it would rank above every
index that was ever down, and read as a market in which nothing happened. This is the one thing this
page asks of the shared renderer that no page before it did, and it cost two small additions:

- `SectorRaceSeries` grew an optional fifth slot, `Starts` — the month each row joins — and
  `StartOf(k)`, defaulting to zero, so the twelve existing usages draw exactly as they did.
- `SectorRaceRenderer` builds its ranking field from the rows that are on the board at that moment
  and appends the rest behind them, keeps late rows out of the axis range, and skips them in
  `DrawRows` before `HideEmptyRows` gets a say.

Only the first is a data-layer fact; all three are needed, and the ordering is not decoration: build
the field first, sort second. The comparison has to be wrapped — `Array.Sort(array, index, length,
lambda)` does not compile, a lambda is not a `Comparer<int>` — and the eleventh page's rule still
holds, that anything the ranking table depends on has to be a constructor argument, because the
table is precomputed in the constructor and an object initialiser runs after it.

**Six, three, three — and the list is a judgement, not a query.** The market-cap board taught that a
hand-written pool is a mistake: the source can be asked for the top 200 by market capitalisation, and
a list written by hand will be missing whatever listed last month. Nothing here can be asked. There
is no index-ranking service, and a benchmark is not chosen by a formula — so the twelve are named in
`WorldIndexLists` and the honest description is that they are the indices a Chinese viewer would
name. That is a different kind of list from the market-cap board's, and it carries a different kind of
debt: by headcount the all-twelve board is half mainland, which a viewer may read as a weighting.

**Monthly, one request per index, unadjusted.** The same `RawBarsAsync` path the A+H and corridor
pages take: an index pays no dividend, but the reason is the other one — an adjustment rebases a
series, and two rebased series side by side are not comparable. The 430-month ceiling means the whole
history comes back in one reply, so "as far back as there is" costs twelve requests and no paging.

**Only `newfqkline` answers with the whole history.** Measured 2026-10-02: `usINX` returns 922 months
from 1950-01, where `fqkline` returns ten months for the same code and one for `usDJI`. The rule is
in `MEMORY.md` now (and in the skill), because it is a trap that looks like a thin index.

**A defect in the shared renderer that this page found.** Every row draws its value at the end of its
bar, right-aligned to it. When a bar ran to the left edge of the drawing area there was no room left
of the bar either, so the label was placed to the left of it — over the name column. The frame read
`恒生科技−40.55%` as one string, name and value glued together, and it only shows up on a board whose
worst row is negative enough to reach that edge. The label now goes to the right of the zero axis in
that case, which is where the eye already is. Fixed in the shared renderer, so the sector race, the
market-cap board and extreme days inherit it.

**Counting rows in the picture.** "The board has not filled up yet" is a fact about the frame and not
about any string in the UI, so `verify-indexrace.py` counts bars from pixels: a scanline is inside a
row when it holds a run of four or more saturated pixels, and rows are the bands of those scanlines
within the canvas interior. Calibrated against four boards whose row count is known — the twelve, the
Americas' three, AH premium's fifteen and extreme days' fifteen all come out exact. Where two rows'
glows touch the bands merge, so a count can come out low and never high; that is why the assertions
are "the last frame is full" and "the first frame is not", with only the three-row group asserted as
an exact number. Both statements are the picture saying what the data layer says.

**Measured 2026-10-02**, all twelve over ten years: 120 months (the index monthly coverage of a
ten-year window is fuller than the currency one's 113–114), 纳斯达克 leading at +417.64%, 恒生科技 last
at −40.55%; the first frame of the run draws ten or eleven rows because the Hang Seng Tech index has
not joined. The Americas alone: 纳斯达克 +417.64%, 道琼斯 +180.59%, and the bottom of the board moves
off 恒生科技. `verify-indexrace.py` is 39 checks, 39 pass.

**Owed on this page:** the English interface has not been driven through it (the index names are the
`INST*` keys the other pages already carry, the group names are new — none of it has been read in
English); no export has been run at any format; neither the custom span nor the "longest" span has
been exercised; and the twelve-index list is a judgement that nobody has reviewed.

## The fourteenth page: asset classes, and the adjustment that cannot go the other way

**What is raced here is money, not a number.** The index race puts twelve published numbers on one
axis; this one puts eight things a mainland account can actually buy — a fund per asset class. That
single difference decides the one thing that matters:

**Adjusted, where the index race is unadjusted.** Same arithmetic, opposite series, and therefore no
shared loader: the reason has to sit where the call is made. Two measurements say why it cannot go
the other way:

- The money-market fund's price goes from 100.161 to 100.901 across thirteen years — +0.0%
  unadjusted. Cash is the one row on this board that has never fallen, and unadjusted it would be
  drawn last: the board would say that holding cash was the worst available choice. Adjusted it is
  +18.76% over the last ten years.
- A Nasdaq fund quoted at 0.998 in 2013 and 2.352 today reads, unadjusted, as +136% over thirteen
  years. The index it tracks rose sixfold over the last decade alone. The gap is a share split, which
  multiplied the holder's units by exactly what it divided their price by.

Both are wrong in the same direction and by a lot, which is why this is not a matter of taste.

**The adjusted series was checked, because an adjustment is wrong plausibly.** A fund that split its
units is exactly the case where a factor can be off by a multiple without looking odd, so the one
number nobody can eyeball was put against its own index: over the same ten years the Nasdaq-100 rose
+600.4% and the dollar gained +3.6% on the yuan — +625.4% converted — against the fund's +681.4%.
Nine per cent apart, which is dividends and a cross-border premium, and the same order of magnitude,
which is what rules out the factor error that would make the whole row nonsense.

**Eight funds, all quoted on a mainland exchange.** Same money, same broker, and the two overseas rows
carry the exchange rate inside them — which is what a mainland holder's return actually was. The
roster is a judgement, as the index list is: there is no service that ranks asset classes. It carries
one debt of its own — the commodity fund only starts in 2019, so the ten-year board opens with seven
rows and fills in.

**Four of the eight already had `INST*` names.** sh510300, sh510500, sh518880 and sh513100 are in the
`Markets.cs` presets the plan, holding and candle pages offer, so those keys belong to that line. The
first port run rewrote them, which would have moved three other pages' preset labels; they were put
back from `HEAD` and verified value by value in all fourteen files. One key, one owner — the port
script now writes only the four new ones and says why in a comment.

**Verified 41 ways** (`tools/verify-assetrace.py`), including recomputing the leader and the loser
from the source's own *adjusted* bars: they match to 0.01 of a percentage point, which is what proves
the adjustment rather than merely asserting it. One assertion is written against the call rather than
the name, because this page's own comment names `RawBarsAsync` on purpose — to explain why it is not
used — so "the string appears" does not mean "the wrong path was taken". The index race was re-run
afterwards and still passes 39.

Measured 2026-10-02, ten years: 120 months, the Nasdaq fund +578.20%, gold +209.59%, the CSI 300 fund
+49.02%, and the money-market fund +18.76% behind.

**Owed on this page:** no export at any format; the custom span and the longest span have not been
exercised; the English interface has not been driven through it; and nobody has checked the roster
against anything but the judgement that wrote it.

## The fifteenth page: depth, and the months back out of it

**The asset race's other half, and taken together they are the whole question.** That board says what
each holding earned in ten years; this one says what it cost to stay for it. Same eight funds, same
loader, same loader *arguments* — the roster and the arithmetic are not repeated anywhere, and the two
pages stand beside each other in the navigation for the reason they stand beside each other here.

**What a row is.** A filled curve hanging below the holding's own high-water line, deepening month by
month, with the high-water line itself drawn as a rule across the row. A row at its own high has no
curve under it at all, which is why that rule has to be there: the flat row is the claim, and without
the line there is nothing to see it is level with.

**Why a curve and not a bar.** Every other board here draws a value as a length, and a length can only
say how deep the water is at this instant. A depth is a shape over time — the low and the climb out of
it are two places on the curve, and the distance between them across the frame is the months it took.
That distance is the half of the story a bar cannot hold.

**The two numbers do not rise together**, which is the entire reason the page is worth building. Over
the ten years measured here:

* the CSI 300 fund fell 33.04% and took twenty-nine months to regain the high;
* the CSI 500 fund fell *further* — 36.10% — and was level again in **nineteen**;
* the Hang Seng fund went deepest of the three at 43.90% and took thirty-five.

So the deepest fall is not the longest recovery, and the second-deepest was the quickest of them all.
A board printing only the depth ranks those rows and says nothing about which fall a holder could
have sat through. This is also why the verification asserts the pair exists rather than asserting
"the leader changed" — the leader can legitimately be the same row on two different rosters, which
is a mistake the asset race's own script made once.

**The range decides the numbers, and the probe that sized the page used a different one.** Every
figure above is the ten-year window, which is the page's default. Over the *whole* history — which is
what the sizing probe asked for — the CSI 500 fund fell 56.07% and took eighty-six months. Both are
correct; they are answers to different spans, and a page whose whole subject is depth is a page where
that distinction has to be visible in the copy rather than assumed.

**One depth scale for the whole board.** Scaling each row to its own worst would draw the money-market
fund's 0.23% as a chasm the size of the CSI 500's 36%, on a board whose entire claim is that those two
are not comparable. So that row is a flat line pinned to its own high-water line, and the flatness is
what it says. The cost is that a shallow row is a thin line — which is the honest picture of a
holding that did not fall.

**The depth and the climb are measured in that order, and getting it wrong is invisible.** The first
draft of the probe that sized this page measured both in one pass, and every holding came back
"healed in one or two months" — on a board where one of them took seven years. A shallow dip early in
the range sets the clock, and the real fall is then never timed. So there are two passes: the deepest
month first, then the first close back at *the high that month fell from* — not the first month back
at "zero below its own high", which a holding can reach by setting a new high on the way up without
ever having recovered the fall.

Nothing about that bug shows in the picture. The curves are drawn either way, the rows still sort,
the status line still prints a number. The verification recomputes both numbers the same two-pass way
and compares; that is the only thing that catches it.

**Still under water is a state, not a zero.** Gold and the commodity fund had not regained their highs
when this was measured, and the right gutter says so in words ("not recovered yet") rather than
printing a large number that looks like the others. The three lines in that gutter are the whole row
compressed: where it is now, how deep it got, how long the climb took.

**Verified 43 ways** (`tools/verify-drawdown.py`), including recomputing the deepest fall, the months
back and the shallowest row from the source's own adjusted bars — and asserting that at least one row
is still unhealed, so that branch is known to be live rather than assumed. The row count comes off the
pixels: two bands from a filled curve merge far too easily for the race pages' "longest run of colour"
method, so this page counts the **names** instead — each row has exactly one, in a fixed column, and a
saturated curve cannot be mistaken for one.

Measured 2026-10-02, ten years, 120 months: the Hang Seng fund deepest at -43.90% (35 months back),
the Nasdaq fund closest to its high at 0.00%, and gold, the commodity fund and cash still under water.

**Owed on this page:** no export at any format; the custom span and the longest span have not been
exercised; the English interface has not been driven through it; and nobody has checked the roster or
the depth scale against anything but the reasoning above.
