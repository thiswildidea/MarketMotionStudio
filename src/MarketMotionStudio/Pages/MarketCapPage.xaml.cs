using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The market-cap board: one market's largest listings as horizontal bars racing on market value,
/// their order changing to the last frame.
///
/// The ninth page and the sector race's sibling in every mechanical way — same renderer, same
/// animation, same two-gutters shape — but a different question. The race asks which sector
/// performed; this asks which company *is*, which is the one question where the last ten years of
/// this market have a clear answer and a clear upset in them.
///
/// There is no roster picker and no metric picker, on purpose. The field is fifteen fixed
/// listings (see <see cref="MarketCapLists"/>: a per-day top fifteen would need the whole market's
/// history, which is thousands of requests), and the measure is market value. A panel offering one
/// choice is a panel that does not need to exist.
/// </summary>
public sealed partial class MarketCapPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("MarketCap.");

    /// <summary>
    /// The market in force. It names the field and it is the only thing that knows what the
    /// snapshot's market-value field is denominated in — 元, 港元 or dollars — which is the
    /// difference between a label and a label naming the wrong currency.
    /// </summary>
    private readonly MarketProfile _market = Markets.Of(MarketSettings.Current);

    private SectorRaceSeries? _series;

    /// <summary>
    /// The spans on offer. The year entries are the plan page's keys: "近 5 年" is one string in
    /// this app, not two that happen to agree today, and a second set of keys for the same three
    /// words is how a translation drifts apart between two pages that meant the same thing.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (12, "StudioRange12M"),
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (120, "DcaRange10Y"),
        (0, "StudioRangeCustom"),
    ];

    public MarketCapPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // Ten years, which is the page's own name. A decade over fifteen listings is about ninety
        // requests — the walk asks for one two-and-a-half-year page at a time — so the shorter
        // spans are there for a slow connection rather than as decoration.
        RangeCombo.SelectedIndex = 3;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-10);
        ToDate.Date = today;

        ListText.Text = Strings.Format("MarketCapCount", MarketCapLists.Board);

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

    protected override string JobName => Strings.Get("MarketCapPageTitle.Text");

    /// <summary>
    /// “市值前 15” — what the frame says when no title was typed.
    ///
    /// The list label *is* the title. It used to be wrapped in a second key of its own
    /// (“{0}市值榜”), which read as “市值前 15市值榜” — two keys that each name the same page, and
    /// the duplication is invisible until a frame is drawn with both of them in it.
    /// </summary>
    private string AutoTitle() => Strings.Format("MarketCapListLabel", MarketCapLists.Board);

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            // The race renderer on its amount metric. A market value is an amount: all positive,
            // so the zero axis sits at the left and the bars grow out of it, and the ranking is
            // the interpolated thing the renderer already knows how to draw.
            // `showTop`: the field is sixty listings and the frame draws fifteen of them — the
            // fifteen that were largest at each moment, which is what makes membership change.
            Preview.Renderer = new SectorRaceRenderer(
                series, RaceMetric.Amount, VideoSettings.Duration, MarketCapLists.Board)
            {
                Title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle(),
                ShowTitle = VideoSettings.ShowTitle,
                ListLabel = Strings.Format("MarketCapListLabel", MarketCapLists.Board),
                UnitWord = Strings.Get("MarketCapUnitCandidates"),

                // The series is monthly (see `MarketCapSeries`), so the header line's count of
                // them is a count of months and not of trading days. It said "个交易日" until
                // somebody read a frame: the renderer had the daily word baked in, and a share
                // race and a monthly board draw the same header.
                SpanWord = Strings.Get("MarketCapUnitMonths"),
                UnitKey = MarketCapLists.UnitKey(_market.Id),
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("MarketCapStageTitle");
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

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CustomRange is null)
        {
            return;
        }

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 };
        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        if (RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } && months > 0)
        {
            var today = DateOnly.FromDateTime(DateTime.Now);
            return (today.AddMonths(-months), today);
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

        // The walk's own ceiling rather than a number that sounds right: past it the walk runs out
        // of requests before it runs out of range, and the series quietly starts later than asked.
        if (end.DayNumber - start.DayNumber > HistoryWalk.MostDays)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format("TurnoverRangeTooLong", HistoryWalk.MostDays));
            return;
        }

        _ = RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("SectorFetching", message)));

            var series = await MarketCapSeries.LoadAsync(
                Services.Quotes, Services.Stocks, _market.Id, start, end, progress, cancellation);

            // Every month's ranking is already in the series — the renderer is what decides that
            // only the top fifteen places get drawn.

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = series.Standings(RaceMetric.Amount);
            var top = standings[0];

            // The board's own last place, not the field's. The field is sixty-two wide and holds
            // companies that have been delisted or absorbed — 中国重工 was merged into 中国船舶 —
            // so "last" is a listing worth nothing with no rows at all, which is true and not
            // what the sentence is about.
            var last = standings[Math.Min(MarketCapLists.Board, standings.Length) - 1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "MarketCapFetched",
                series.Racers,
                series.Days,
                series.Entries[top.Index].Name,
                FormatValue(top.Value),
                series.Entries[last.Index].Name,
                FormatValue(last.Value)));
        }, TimeSpan.FromMinutes(6));
    }

    private string FormatValue(double value) =>
        value.ToString("N0", CultureInfo.InvariantCulture) + Strings.Get(MarketCapLists.UnitKey(_market.Id));

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
        // At the end there is nothing left to run, and a play button that does nothing reads as a
        // broken one. These clips run for a minute or two, so watching one twice is ordinary.
        if (!_playback.IsPlaying && Preview.Progress >= 0.999)
        {
            _playback.Seek(0);
        }

        _playback.Toggle();
    }

    void IPlaybackHost.ShowMoment(double progress) => ShowMoment(progress);

    void IPlaybackHost.ShowPlaybackState(bool playing) => SetPlaybackState(playing);

    /// <summary>
    /// Points the button at what it will do next: ▶ to run the animation, ⏸ to hold it. An icon
    /// carries no text of its own, so the same word that picks the glyph goes on the tooltip and
    /// on the name a screen reader announces.
    /// </summary>
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

        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
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
