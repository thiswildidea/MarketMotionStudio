using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The extreme-day board: one instrument, and its largest single-day moves, ranked by size.
///
/// The eleventh page and the fourth on the horizontal race — and the one that turns the race
/// inside out. Every other board gives a row a value that changes day by day; this one gives a
/// row a value that never changes, because **the row is a day**. What moves is the membership:
/// a day is worth nothing until it happens, so the board fills in as the years pass, and a day
/// larger than the fifteenth takes its place and pushes someone off the bottom.
///
/// Three things the renderer is asked for that no other page asks for, and why:
///
/// **Rank by magnitude.** A board of moves is board of *moves*: −7.7% belongs next to +8.1%.
/// Ranking the signed values would file every fall below every rise, however small the rise,
/// and the board would be a list of good days with the crashes filed underneath.
///
/// **Leave the empty rows out.** Before its day arrives a row is worth zero, and twenty-four
/// candidates of which five have happened still fill a fifteen-row frame — ten rows reading
/// 0.00% is what the first month of the video would look like without this.
///
/// **Colour by sign.** One colour per row is how a viewer follows a company up a market-cap
/// board; a day is not a thing to follow. So the bar is red for a rise and green for a fall,
/// which is also how the value label beside it already reads.
///
/// The change is the change in the **adjusted** close. For an index that is the index; for a
/// single stock it is the total return, so a stock going ex-dividend does not show a fall that
/// nobody suffered. An unadjusted series would put that fall at the top of the board.
/// </summary>
public sealed partial class ExtremeDaysPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("ExtremeDays.");

    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    private SectorRaceSeries? _series;

    /// <summary>
    /// -1 is the custom span and 0 is "as far back as the source goes", which is what the plan
    /// and holding pages already mean by 0.
    /// </summary>
    private const int CustomMonths = -1;

    private static readonly (int Months, string Key)[] Ranges =
    [
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (120, "DcaRange10Y"),
        (0, "ExtremeDaysRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    public ExtremeDaysPage()
    {
        InitializeComponent();

        // The market's broad indices: the whole point of the page is one instrument's history,
        // and an index is the instrument whose single-day move is a sentence about the market.
        foreach (var entry in _market.BroadIndices)
        {
            InstrumentCombo.Items.Add(new ComboBoxItem
            {
                Content = InstrumentNames.Display(entry.Code, entry.Name),
                Tag = entry.Code,
            });
        }

        InstrumentCombo.SelectedIndex = 0;

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // Ten years: long enough to carry a crash and a rally, short enough that the board is
        // not twenty years of 1990s limit-rule days with nothing recent on it.
        RangeCombo.SelectedIndex = 2;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-5);
        ToDate.Date = today;

        // Formatted, because the string names the number of rows the frame draws. Read with
        // `Strings.Get` the card showed a literal "{0}" — the same defect the A+H page had.
        ListText.Text = Strings.Format("ExtremeDaysCount", ExtremeDayBoard.Board);

        VideoSettings.AllowHideTitle = true;

        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            VideoSettings.Save(_prefs);
        };

        _stage.Subtitle = Strings.Get("StudioStageNoData");
        _stage.Credit = Strings.Get("StudioCredit");

        Preview.Renderer = _stage;

        _playback = new Playback(this);

        // Named before it has ever been pressed: the button is an icon, so the tooltip and the
        // name a screen reader announces are the only words it has.
        SetPlaybackState(playing: false);

        _prefs.Restoring = true;
        VideoSettings.Restore(_prefs);
        RestorePreferences();
        _prefs.Restoring = false;

        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("ExtremeDaysPageTitle.Text");

    /// <summary>“极端交易日” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("ExtremeDaysPageTitle.Text");

    private RaceEntry ChosenInstrument()
    {
        var code = InstrumentCombo.SelectedItem is ComboBoxItem { Tag: string chosen } ? chosen : string.Empty;

        return _market.BroadIndices.FirstOrDefault(e => e.Code == code, _market.BroadIndices[0]);
    }

    private string ChosenInstrumentName() =>
        InstrumentNames.Display(ChosenInstrument().Code, ChosenInstrument().Name);

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            // The race renderer on its **return** metric: a move is a percentage, and that is
            // the metric whose labels end in %. `showTop`: twenty-four candidate days race for
            // fifteen places. The three flags are this page's own — see the note on the class.
            // `rankByMagnitude` as the constructor's argument, not as a property set below: the
            // ranking table is built inside the constructor, so an initialiser would be read too
            // late and the frame would be sorted by sign — see the note on that parameter.
            Preview.Renderer = new SectorRaceRenderer(
                series, RaceMetric.Return, VideoSettings.Duration, ExtremeDayBoard.Board,
                rankByMagnitude: true)
            {
                Title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle(),
                ShowTitle = VideoSettings.ShowTitle,
                ListLabel = ChosenInstrumentName(),
                UnitWord = Strings.Get("ExtremeDaysUnitCandidates"),

                // Daily, so the header counts trading days — the renderer's own fallback is the
                // same string, and the page says it because the page is what chose the interval.
                SpanWord = Strings.Get("StockTradingDaysUnit"),
                HideEmptyRows = true,
                ColourBySign = true,
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("ExtremeDaysStageTitle");
            _stage.ShowTitle = VideoSettings.ShowTitle;
            Preview.Renderer = _stage;
        }

        var ready = _series is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    // ---- range ---------------------------------------------------------------------------

    private void OnInstrumentChanged(object sender, SelectionChangedEventArgs e)
    {
        // A different instrument is a different board, so whatever was fetched is no longer
        // what the panel describes. Nothing is fetched until the button is pressed — see the
        // same rule on the candle page.
        SavePreferences();
        ApplyPreviewSettings();
    }

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CustomRange is null)
        {
            return;
        }

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } && months == CustomMonths;

        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        if (RangeCombo.SelectedItem is ComboBoxItem { Tag: int months })
        {
            var today = DateOnly.FromDateTime(DateTime.Now);

            if (months > 0)
            {
                return (today.AddMonths(-months), today);
            }

            if (months == 0)
            {
                // "As far back as there is" — asked for generously and trimmed by the walk,
                // which is the only thing that knows where the source's history starts.
                return (today.AddYears(-30), today);
            }
        }

        return (
            DateOnly.FromDateTime(FromDate.Date.DateTime),
            DateOnly.FromDateTime(ToDate.Date.DateTime));
    }

    // ---- fetching ------------------------------------------------------------------------

    private void OnFetch(object sender, RoutedEventArgs e)
    {
        var (start, end) = ChosenRange();

        if (start >= end)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
            return;
        }

        if (end.DayNumber - start.DayNumber > HistoryWalk.MostDays)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("TurnoverRangeTooLong", HistoryWalk.MostDays));
            return;
        }

        _ = RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("SectorFetching", message)));

            var series = await ExtremeDaySeries.LoadAsync(
                Services.Quotes, _market, ChosenInstrument(), start, end, progress, cancellation);

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = ExtremeDaySeries.ByMagnitude(series);
            var biggest = standings[0];

            // The largest and the smallest **of the fifteen the frame draws**, not of the field:
            // the field holds days the board never shows, and "the smallest move" naming a day
            // nobody can see is a sentence about the data rather than about the picture.
            var smallest = standings[Math.Min(ExtremeDayBoard.Board, standings.Length) - 1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "ExtremeDaysFetched",
                series.Racers,
                series.Days,
                series.Entries[biggest.Index].Name,
                FormatValue(biggest.Value),
                series.Entries[smallest.Index].Name,
                FormatValue(smallest.Value)));
        }, TimeSpan.FromMinutes(6));
    }

    private static string FormatValue(double value) =>
        (value >= 0 ? "+" : "−") + Math.Abs(value).ToString("0.00", CultureInfo.InvariantCulture) + "%";

    // ---- preview transport -----------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e)
    {
        // Moving the slider is an instruction to look at one moment, which means stopping the
        // playback wherever it had got to. See the longer note on MarketTurnoverPage.
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
        if (!_playback.IsPlaying && Preview.Progress >= 0.999)
        {
            _playback.Seek(0);
        }

        _playback.Toggle();
    }

    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) => SetPlaybackState(playing);

    private void SetPlaybackState(bool playing)
    {
        var label = Strings.Get(playing ? "StudioPause.Content" : "StudioPlay.Content");

        PlayIcon.Glyph = playing ? "\uE769" : "\uE768";

        ToolTipService.SetToolTip(PlayButton, label);
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export -----------------------------------------------------------------------------

    private string CapFileName(VideoFormat format, string extension)
    {
        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle();

        var safe = new string([.. label.Where(c => !Path.GetInvalidFileNameChars().Contains(c))]).Trim();

        if (safe.Length > 40)
        {
            safe = safe[..40];
        }

        return $"{safe}_{_series!.Dates[0]:yyyy-MM-dd}_{_series.Dates[^1]:yyyy-MM-dd}_{format.NameSuffix}.{extension}";
    }

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _series is null || App.Window is not { } window)
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;

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
                CapFileName(format, "mp4"),
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
        if (Preview.Renderer is not { } renderer || _series is null || App.Window is not { } window)
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
                CapFileName(format, "png"),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    // ---- persistence ---------------------------------------------------------------------------

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Code", ChosenInstrument().Code);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        var code = _prefs.GetString("Code", _market.BroadIndices[0].Code);

        InstrumentCombo.SelectedItem =
            InstrumentCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is string c && c == code)
            ?? InstrumentCombo.Items[0];

        var months = _prefs.GetInt("Months", 120);
        var match = RangeCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is int m && m == months);

        if (match is not null)
        {
            RangeCombo.SelectedItem = match;
        }

        if (DateOnly.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = new DateTimeOffset(from, TimeOnly.MinValue, TimeSpan.Zero);
        }

        if (DateOnly.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = new DateTimeOffset(to, TimeOnly.MinValue, TimeSpan.Zero);
        }
    }
}
