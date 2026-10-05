using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The position page: one purchase, held, and what the years did to it — the question
/// this page is asked with is a person and a date, "what if I'd held a million of
/// 中国平安 since 2015".
///
/// **And the same question asked of several instruments at once**, which is how it is
/// usually asked: whether to have held this or that is one question, and answering it on
/// two frames is not answering it. The holdings come from the reader's own list — the one
/// every roster board shares — with a chip per holding deciding whether it is on this
/// frame; the one-tap row above it is the market's own list of names a long-term holding
/// is plausibly a story about.
///
/// Two terms, both controls, for the same reason as the plan page: the point is the
/// arithmetic between them. The simulation is the plainest thing that can honestly be
/// called a holding; <see cref="PositionLoader"/> carries the reasoning about what was
/// deliberately left out — dividends above all, which a long holding of a bank stock is a
/// large fraction of, and which the frame's subtitle says is not counted.
///
/// No renderer of its own pipeline: <see cref="PositionRenderer"/> draws the frames, this
/// page is a loader that turns a list and two terms into the board it draws — the same
/// split the calendar and the plan pages make.
/// </summary>
public sealed partial class PositionPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>
    /// Carried by the span list's own entry rather than by a count, so that it stays
    /// distinguishable from "as far back as there is" — which is a span too, and which
    /// the walk itself has to discover.
    /// </summary>
    private const int CustomMonths = -1;

    /// <summary>
    /// The holding's spans, as a number of months. Zero means as far back as the
    /// source still has data, which the walk in <see cref="HistoryWalk"/> finds on
    /// its own — and it is the default, because a holding's story starts where the
    /// holder says it did, and "since 2015" is a span no fixed choice covers.
    ///
    /// The last entry is that span typed out: two dates, because a holder asking
    /// about their own holding names the day they bought on.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (120, "DcaRange10Y"),
        (0, "DcaRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("Position.");

    /// <summary>
    /// How many trading days the scrolling window holds to begin with — about a quarter, which
    /// is short enough that a move is visible and long enough that a move is not just noise.
    ///
    /// The ends of the range are here rather than in the renderer because a window is a reading
    /// of marks that have already been fetched: a typed number is worth drawing, and only the
    /// two extremes are worth refusing to. See <see cref="ChosenWindow"/>.
    /// </summary>
    private const int DefaultWindow = 60;

    private const int MinWindow = 10;

    private const int MaxWindow = 500;

    private PositionBoard? _board;

    /// <summary>The market in force: it names the presets, it is what the list is kept to,
    /// and its currency names the amounts.</summary>
    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    /// <summary>Whether the page is finished being built; see the handlers that read it.</summary>
    private bool _ready;

    public PositionPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // "As far back as there is": a holding is a years-long story by default, and
        // the walk stops where the listing's own history does.
        RangeCombo.SelectedIndex = 3;

        // Two ways of reading the same marks; see PositionMotion. Growing is
        // first and default, because on a holding the whole span at once is the answer to the
        // question the page is asked — the window is for looking closer at part of it.
        foreach (var (motion, key) in new[]
                 {
                     (PositionMotion.Grow, "PositionMotionGrow"),
                     (PositionMotion.Scroll, "PositionMotionScroll"),
                 })
        {
            MotionCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)motion });
        }

        MotionCombo.SelectedIndex = 0;

        // The two pickers cannot ask for a span one walk cannot gather: past that the
        // walk runs out of requests before it runs out of range, and the holding would
        // begin on whatever day the twentieth request happened to reach. See
        // <see cref="HistoryWalk.MostDays"/>.
        var now = DateTimeOffset.Now;
        var oldest = now.AddDays(-HistoryWalk.MostDays);

        FromDate.MinYear = oldest;
        FromDate.MaxYear = now;
        ToDate.MinYear = oldest;
        ToDate.MaxYear = now;

        foreach (var entry in _market.PositionInstruments)
        {
            Presets.Items.Add(new MatrixPreset(entry.Code, InstrumentNames.Display(entry.Code, entry.Name)));
        }

        // The picker has no panel of its own to write into, so what it has to say is said here.
        Watch.Notice += message => ShowStatus(InfoBarSeverity.Error, message);

        // A pick added or removed here changes the list on every roster board, all five sharing
        // one, and on this one it retires the board that was drawn from the old list: a frame
        // still showing five holdings under a chip row that no longer lists one of them is a
        // frame about a list nobody chose.
        Watch.Changed += OnWatchChanged;

        VideoSettings.AllowHideTitle = true;
        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            SavePreferences();
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        // Named before it has ever been pressed: the button is an icon, so the tooltip and
        // the name a screen reader announces are the only words it has, and neither can
        // wait for the first toggle to appear.
        SetPlaybackState(playing: false);

        // After every control exists and every handler is attached, so a restored value
        // reaches the preview through the same path a typed one does.
        RestorePreferences();
        ApplyPreviewSettings();

        _ready = true;
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("PositionPageTitle.Text");

    // ---- what is being drawn ---------------------------------------------------------

    /// <summary>
    /// The picks this frame will draw: the reader's list, kept to the market in force.
    ///
    /// The list itself is deliberately cross-market — it is shared with four boards that put
    /// three venues on one axis — while the amounts here are the market in force's currency and
    /// its walk is the one that knows the venue's adjustment. So a pick from another venue is
    /// not drawn rather than drawn in the wrong money, and the fetch says so when that leaves
    /// nothing at all.
    /// </summary>
    private IReadOnlyList<RaceEntry> Chosen() =>
        [.. Watch.SelectedEntries.Where(e => _market.Accepts(e.Code))];

    // ---- the holding's terms ---------------------------------------------------------

    /// <summary>
    /// The capital that goes in once, or zero while the box holds nothing parsable.
    /// Zero is the fetch's refusal, not a silent substitute: a holding with no
    /// capital is not a holding. The interface's culture reads it first, the
    /// invariant one second — an amount is a number before it is a localised one,
    /// and "1000000" must mean a million everywhere.
    /// </summary>
    private double ChosenCapital
    {
        get
        {
            var text = CapitalBox.Text.Trim();

            return double.TryParse(text, NumberStyles.Float, CultureInfo.CurrentUICulture, out var capital) ? capital
                : double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out capital) ? capital
                : 0;
        }
    }

    private int ChosenMonths() =>
        RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 0;

    private PositionMotion ChosenMotion() =>
        MotionCombo.SelectedItem is ComboBoxItem { Tag: int motion }
            ? (PositionMotion)motion
            : PositionMotion.Grow;

    /// <summary>
    /// How many trading days the scrolling window holds.
    ///
    /// Clamped rather than refused, unlike the capital: an amount of zero is not a holding, while
    /// a window is only a reading of marks that have already been fetched — and the two ends of
    /// the range are still readings. The interface's culture is tried first and the invariant one
    /// second, the same order the capital box uses. A window as long as the range is legitimate
    /// and simply leaves nothing to scroll; see <see cref="PositionRenderer"/>.
    /// </summary>
    private int ChosenWindow()
    {
        var text = WindowBox.Text.Trim();

        var window = int.TryParse(text, NumberStyles.Integer, CultureInfo.CurrentUICulture, out var parsed) ? parsed
            : int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out parsed) ? parsed
            : DefaultWindow;

        return Math.Clamp(window, MinWindow, MaxWindow);
    }

    /// <summary>
    /// The motion or the window changed. Neither is a term of the fetch — both read the marks
    /// already on the page — so this redraws and stops there.
    /// </summary>
    private void OnLookChanged(object sender, object e)
    {
        if (!_ready)
        {
            return;
        }

        ApplyPreviewSettings();
        SavePreferences();
    }

    /// <summary>The two dates in the pickers. The span in force only when custom is chosen.</summary>
    private (DateOnly From, DateOnly To) CustomSpan() =>
        (DateOnly.FromDateTime(FromDate.Date.DateTime), DateOnly.FromDateTime(ToDate.Date.DateTime));

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = ChosenMonths();
        var today = DateOnly.FromDateTime(DateTime.Now);

        if (months == CustomMonths)
        {
            var (from, to) = CustomSpan();

            // An end in the future is an end today: nothing after today has a price to
            // mark the holding with, and the picker's own ceiling says as much.
            return (from, to > today ? today : to);
        }

        // "As far back as there is": ask for thirteen years and let the walk stop where
        // the source does. Clamped to the source's own ceiling so the first request
        // already carries the full 640-bar window.
        return months == 0 ? (today.AddYears(-13), today) : (today.AddMonths(-months), today);
    }

    // ---- preview ---------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_board is { } board)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, board.Dates.Count, board.Peak);

            Preview.Renderer = new PositionRenderer(board, plan, ChosenMotion(), ChosenWindow())
            {
                Title = title,
                ShowTitle = showTitle,
                CurrencyKey = _market.CurrencyKey,
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        // The window is a term of the scrolling motion alone; offered at any other time it
        // reads as a setting the chart is ignoring.
        WindowBox.IsEnabled = ChosenMotion() is PositionMotion.Scroll;

        VideoSettings.TitlePlaceholder = DefaultTitle();

        var ready = _board is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>
    /// The title the frame will draw: the typed one, or the default naming what is on it. The
    /// renderer is rebuilt on every change, so the placeholder follows the selection even before
    /// a fetch has confirmed the holdings' proper names.
    /// </summary>
    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : DefaultTitle();

    /// <summary>
    /// “持仓收益：中国平安”, or the holdings named against each other when there is more than one.
    ///
    /// Read off the fetched board when there is one, because a fetch is what corrects a typed
    /// code to the name the venue actually calls it; off the selection before that, so the
    /// placeholder says something about what is about to be drawn.
    /// </summary>
    private string DefaultTitle()
    {
        if (_board is { } board)
        {
            return board.Comparing
                ? Compared([.. board.Tracks.Select(t => t.Name)])
                : Strings.Format("PositionDefaultTitle", board.Tracks[0].Name);
        }

        var names = Chosen().Select(e => InstrumentNames.Display(e.Code, e.Name)).ToArray();

        return names.Length switch
        {
            0 => Strings.Format("PositionDefaultTitle", _market.PositionInstruments[0].Name),
            1 => Strings.Format("PositionDefaultTitle", names[0]),
            _ => Compared(names),
        };
    }

    private static string Compared(string[] names) => names.Length == 2
        ? Strings.Format("PositionVsTitle", names[0], names[1])
        : Strings.Format("PositionCompareMany", names[0], names.Length);

    // ---- picking ---------------------------------------------------------------------

    private void OnWatchChanged(object? sender, EventArgs e)
    {
        _board = null;
        SavePreferences();
        ApplyPreviewSettings();
    }

    private void OnPresetClick(object sender, RoutedEventArgs e)
    {
        if ((sender as FrameworkElement)?.Tag is not string code)
        {
            return;
        }

        var name = Presets.Items.OfType<MatrixPreset>().FirstOrDefault(p => p.Code == code)?.Name ?? code;

        if (!Watchlist.Has(code) && !Watchlist.Add(code, name))
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("SectorTooManyStocks", Watchlist.Most));
            return;
        }

        // On the list *and* switched on for this frame in one press. The row is one-tap by
        // design: a pick that arrived on the list but switched off would draw nothing at all,
        // which reads as a broken button rather than as a setting.
        Watch.Include(code);

        Fetch();
    }

    // ---- fetching --------------------------------------------------------------------

    private async void Fetch()
    {
        var capital = ChosenCapital;

        if (capital <= 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("PositionCapitalInvalid"));
            return;
        }

        var (start, end) = ChosenRange();

        // A typed span is the only one that can be wrong in a way the source would
        // answer badly: for two dates in the wrong order it would report "too few days"
        // and leave the last holding standing under a pair of dates it never ran over.
        // Refused here, before a request is made.
        if (ChosenMonths() == CustomMonths && start >= end)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
            return;
        }

        var chosen = Chosen();

        if (chosen.Count == 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("PositionNoMarketPicks", _market.Name));
            return;
        }

        // Refused rather than trimmed: a frame drawn from six of the nine holdings somebody
        // ticked answers about a list nobody chose, and it looks entirely plausible while it
        // does — the same reason the roster boards never quietly drop a row.
        if (chosen.Count > PositionLoader.MostTracks)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format(
                "PositionTooMany", PositionLoader.MostTracks, chosen.Count));
            return;
        }

        // Six minutes, not the calendar's two: one holding reaching back a dozen years is up to
        // twenty requests answered one after another, and this page now draws up to six of them.
        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var board = await PositionLoader.LoadAsync(
                Services.Quotes, chosen, capital, start, end, progress, cancellation);

            _board = board;

            // A typed pick is renamed to what the endpoint calls it, which is also the name the
            // other roster boards will read off the shared list.
            foreach (var track in board.Tracks)
            {
                Watchlist.Rename(track.Code, InstrumentNames.Display(track.Code, track.Name));
            }

            ApplyPreviewSettings();

            // Parked on the last frame: the closing statistics are what someone wants to
            // look at before deciding whether to export.
            ShowMoment(1);

            var fetched = board.Comparing
                ? Strings.Format(
                    "PositionBoardFetched",
                    board.Tracks.Count,
                    board.Dates.Count,
                    PositionRenderer.Iso(board.Start),
                    PositionRenderer.Iso(board.End))
                : Strings.Format(
                    "PositionFetched",
                    board.Dates.Count,
                    PositionRenderer.Iso(board.Start),
                    PositionRenderer.Iso(board.End),
                    board.End.DayNumber - board.Start.DayNumber);

            if (board.Skipped.Count == 0)
            {
                ShowStatus(InfoBarSeverity.Success, fetched);
            }
            else
            {
                // Named rather than counted: which instrument the range could not hold is the
                // thing the reader has to act on, and the frame is one line short without it.
                ShowStatus(InfoBarSeverity.Warning, $"{fetched} {Strings.Format(
                    "PositionSkipped", board.Skipped.Count, string.Join(", ", board.Skipped))}");
            }
        }, TimeSpan.FromMinutes(6));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    // ---- playback --------------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnHoldingChanged(object sender, object e)
    {
        // Raised by the selection assignment in the constructor, before the page exists
        // well enough to save anything.
        if (RangeCombo is null)
        {
            return;
        }

        // The two pickers belong to the custom span alone. Set before the guard below,
        // so that a saved custom span comes back with them already showing rather than
        // with a pair of dates the person has to guess are there.
        CustomRange.Visibility = ChosenMonths() == CustomMonths
            ? Visibility.Visible
            : Visibility.Collapsed;

        if (!_ready)
        {
            return;
        }

        SavePreferences();
    }

    /// <summary>
    /// One of the two typed dates moved. Remembered, and nothing else: a holding over a
    /// dozen years is twenty requests answered one after another, and a fetch per change
    /// would be a fetch per keystroke of a date. Fetching is a button on this page, and
    /// it stays one.
    /// </summary>
    private void OnCustomRangeChanged(object sender, DatePickerValueChangedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        SavePreferences();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e)
    {
        // Moving the slider is an instruction to look at one moment, which means stopping the
        // playback wherever it had got to — and moving the position a press afterwards will
        // start from. See the longer note on MarketTurnoverPage.
        _playback?.Seek(Scrub.Value);
    }

    private void RefreshScrubText()
    {
        var total = VideoSettings.Duration;
        var at = TimeSpan.FromSeconds(total.TotalSeconds * Math.Clamp(Preview.Progress, 0, 1));

        ScrubText.Text = Strings.Format("StudioScrubPosition", Clock(at), Clock(total));
    }

    private void OnPlay(object sender, RoutedEventArgs e)
    {
        // At the end there is nothing left to run, and a play button that does nothing
        // reads as a broken one. Starting again is what the press meant: these clips run
        // for a minute or two, so watching one twice is an ordinary thing to do.
        //
        // Through the seek rather than by setting the preview's progress directly, so that
        // the position playback counts from is the position the picture is showing. Two
        // places to put the position are two places to disagree about it.
        if (!_playback.IsPlaying && Preview.Progress >= 0.999)
        {
            _playback.Seek(0);
        }

        _playback.Toggle();
    }

    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) => SetPlaybackState(playing);

    /// <summary>
    /// Points the button at what it will do next: ▶ to run the animation, ⏸ to hold it.
    ///
    /// An icon carries no text of its own, so the same word that picks the glyph is put on
    /// the tooltip and on the name a screen reader announces. Without that the button is
    /// unnamed, and "unnamed button" is what a reader has to say about a control whose
    /// whole meaning is a shape.
    /// </summary>
    private void SetPlaybackState(bool playing)
    {
        var label = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

        PlayIcon.Glyph = playing ? "\uE769" : "\uE768";

        ToolTipService.SetToolTip(PlayButton, label);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export ----------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _board is not { } board || App.Window is not { } window)
        {
            return;
        }

        // Read before the work starts, so touching a slider mid-export cannot change the
        // format halfway through the file.
        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;
        var label = ResolvedTitle();

        CancelButton.IsEnabled = true;

        var limit = TimeSpan.FromMinutes(5) + (duration * 4);

        await RunAsync(ExportButton, async cancellation =>
        {
            var folder = await OutputFolder.TryGetAsync() ?? await OutputFolder.ChooseAsync(window);

            if (folder is null)
            {
                ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioExportCancelled"));
                return;
            }

            var clock = System.Diagnostics.Stopwatch.StartNew();

            var report = new Progress<double>(fraction =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("StudioExporting", (int)(fraction * 100))));

            var file = await VideoExporter.EncodeAsync(
                renderer, format, margins, duration, folder,
                VideoExporter.VideoName(label, board.Start, board.End, format),
                report, cancellation);

            clock.Stop();

            var properties = await file.GetBasicPropertiesAsync();

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioExported",
                file.Name,
                (properties.Size / 1048576.0).ToString("0.0", CultureInfo.InvariantCulture),
                clock.Elapsed.TotalSeconds.ToString("0.0", CultureInfo.InvariantCulture),
                ((int)duration.TotalSeconds).ToString(CultureInfo.InvariantCulture),
                folder.Path));
        }, limit);

        CancelButton.IsEnabled = false;
    }

    private async void OnSaveCover(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _board is not { } board || App.Window is not { } window)
        {
            return;
        }

        await RunAsync(CoverButton, async cancellation =>
        {
            var folder = await OutputFolder.TryGetAsync() ?? await OutputFolder.ChooseAsync(window);

            if (folder is null)
            {
                ShowStatus(InfoBarSeverity.Informational, Strings.Get("StudioCoverCancelled"));
                return;
            }

            var format = VideoSettings.Format;

            var file = await FrameExporter.SavePngAsync(
                renderer, format, VideoSettings.Margins, Preview.Progress, folder,
                FrameExporter.CoverName(ResolvedTitle(), board.Start, board.End, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences -----------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var capital = _prefs.GetDouble("Capital", 1_000_000);
        CapitalBox.Text = capital > 0
            ? capital.ToString("0.##", CultureInfo.InvariantCulture)
            : "1000000";

        var months = _prefs.GetInt("Months", 0);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 3;

        // The motion is one of the two entries the constructor added, and the window goes back
        // through the same clamp a typed one does — a remembered 600 comes back as 500.
        MotionCombo.SelectedIndex = _prefs.GetInt("Motion", (int)PositionMotion.Grow) == (int)PositionMotion.Scroll ? 1 : 0;
        WindowBox.Text = Math.Clamp(_prefs.GetInt("Window", DefaultWindow), MinWindow, MaxWindow)
            .ToString(CultureInfo.InvariantCulture);

        // Three years, so the two pickers say something sensible the first time the
        // custom span is chosen instead of opening on today and today.
        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-3);
        ToDate.Date = today;

        if (DateOnly.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = new DateTimeOffset(from, TimeOnly.MinValue, TimeSpan.Zero);
        }

        if (DateOnly.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = new DateTimeOffset(to, TimeOnly.MinValue, TimeSpan.Zero);
        }

        VideoSettings.Restore(_prefs);

        // The holdings are the shared list, which the picker loads on its own — there is
        // nothing instrument-shaped left to remember here. What is remembered is the list
        // itself, and it is remembered for five pages at once.
        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        _prefs.Save("Capital", ChosenCapital > 0 ? ChosenCapital : 1_000_000);
        _prefs.Save("Months", ChosenMonths());
        _prefs.Save("Motion", (int)ChosenMotion());
        _prefs.Save("Window", ChosenWindow());
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
