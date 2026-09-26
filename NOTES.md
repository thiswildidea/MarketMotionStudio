# Working notes

Open questions and unfinished edges, kept out of the README because they describe the state of
the work rather than the tool. Settled reasoning lives in commit messages; this file is only
for what is still owed.

Last reviewed: 2026-09-26 (after the seventh page — Position Return; see the end).

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

**Package identity is decided once.** `Identity Name` and `Publisher` come from the name
reserved in Partner Center and cannot be changed for that product afterwards; the display name
can. The manifest still carries the development placeholder `MarketMotionStudio.Dev` with a
self-signed publisher, so the identity is still open — but only until the first submission.
The name to reserve is **Market Motion Studio**. (The package identity `MarketMotionStudio`
is frozen and never changes — only the display name and Store listing name were renamed when
the app grew beyond A-shares to Hong Kong and US markets.)

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
all fourteen help documents parse to 24 blocks; every generated PNG is 32-bit with a
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
