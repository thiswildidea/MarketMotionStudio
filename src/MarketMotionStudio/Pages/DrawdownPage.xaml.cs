using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The underwater board: the same eight holdings the asset race runs, measured against themselves
/// instead of against each other.
///
/// The fourteenth page answers "what did it earn". This one answers the question that decides
/// whether anybody could have stayed for it: how far below its own high a holder sat, and how many
/// months it took to get back. Those are two numbers and they do not rise together — over the last
/// ten years the Nasdaq fund fell 25.5% and was level again in six months, while the CSI 500 fund
/// fell 56% and took eighty-six. Printed as one number, the second looks like more of the same
/// thing as the first and is not.
///
/// **The curve is the point.** Every other board here draws a value as a length, which can only
/// say how deep the water is at this instant. A depth is a shape over time: the low and the climb
/// out of it are two places on the curve, and the distance between them across the frame is the
/// months between them — the one thing a bar cannot show.
///
/// **One depth scale for the whole board.** Scaling each row to its own worst would draw the
/// money-market fund's 0.2% as a chasm the size of the CSI 500's 56%, on a board whose entire
/// claim is that those are not comparable. So that row is a flat line pinned to its high-water
/// line, and the flatness is what it says.
///
/// Adjusted, monthly, and measured from each holding's own first month — all three for the reasons
/// the asset race gives. This board is the counterpart to that one and shares its roster, its
/// loader's arithmetic and its colours, so a holding looks like the same holding on both.
/// </summary>
public sealed partial class DrawdownPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();

    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("Drawdown.");

    private DrawdownSeries? _series;

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
        (0, "AssetRaceRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    // The roster is the asset race's, and so are its names: the same eight holdings appear on
    // both boards, and a group called two different things on two boards that are meant to be read
    // together is a group the reader has to translate.
    private static readonly (string Key, string Label)[] Lists =
    [
        (AssetClassLists.AllKey, "AssetRaceListAll"),
        (AssetClassLists.EquityKey, "AssetRaceListEquity"),
        (AssetClassLists.NonEquityKey, "AssetRaceListNonEquity"),
    ];

    public DrawdownPage()
    {
        InitializeComponent();

        foreach (var (key, label) in Lists)
        {
            ListCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(label), Tag = key });
        }

        ListCombo.SelectedIndex = 0;

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // Ten years: long enough that every holding but the commodity fund — which starts in 2019
        // — has a fall in it, and short enough that the falls are this decade's.
        RangeCombo.SelectedIndex = 2;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-5);
        ToDate.Date = today;

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

    protected override string JobName => Strings.Get("DrawdownPageTitle.Text");

    /// <summary>“回撤与修复” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("DrawdownPageTitle.Text");

    private IReadOnlyList<RaceEntry> ChosenList()
    {
        var key = ListCombo.SelectedItem is ComboBoxItem { Tag: string chosen } ? chosen : AssetClassLists.AllKey;

        return AssetClassLists.Of(key);
    }

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            Preview.Renderer = new UnderwaterRenderer(series, VideoSettings.Duration)
            {
                Title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle(),
                ShowTitle = VideoSettings.ShowTitle,
                UnitWord = Strings.Get("AssetRaceUnitAssets"),

                // Monthly, so the header counts months — the renderer's own fallback names
                // trading days, and the page says it because the page is what asked for months.
                SpanWord = Strings.Get("MarketCapUnitMonths"),
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("DrawdownStageTitle");
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

    private void OnListChanged(object sender, SelectionChangedEventArgs e)
    {
        // A different group is a different board, so whatever was fetched is no longer what the
        // panel describes. Nothing is fetched until the button is pressed — see the same rule on
        // the candle page.
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
                // "As far back as there is" — asked for generously and trimmed by the loader,
                // which clips to the range and keeps whatever the source answers with.
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

        _ = RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message =>
                ShowStatus(InfoBarSeverity.Informational, Strings.Format("SectorFetching", message)));

            var series = await Drawdown.LoadAsync(
                Services.Quotes, ChosenList(), start, end, progress, cancellation);

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = Drawdown.Standings(series);

            if (standings.Length == 0)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("DrawdownTooFew"));
                return;
            }

            // The two ends of the board mean different things here. The top is the holding
            // closest to its own high; the bottom of *this* status line is the one that fell
            // furthest at any point, which is not the same holding as the one deepest today.
            var worst = Drawdown.Worst(series);
            var shallowest = standings[0];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "DrawdownFetched",
                Drawdown.Quoted(series),
                series.Days,
                series.Entries[worst.Index].Name,
                FormatValue(worst.Value),
                HealedText(series.HealedMonths[worst.Index]),
                series.Entries[shallowest.Index].Name));
        }, TimeSpan.FromMinutes(6));
    }

    /// <summary>“−56.07%” — every depth is below zero, so the sign is not optional decoration.</summary>
    private static string FormatValue(double value) =>
        "−" + Math.Abs(value).ToString("0.00", CultureInfo.InvariantCulture) + "%";

    /// <summary>How long the climb took, in the frame's own words: “86 个月修复” or “至今未修复”.</summary>
    private static string HealedText(int months) => months switch
    {
        Drawdown.NotHealed => Strings.Get("DrawdownNotHealed"),
        Drawdown.NeverFell => Strings.Get("DrawdownNeverFell"),
        _ => Strings.Format("DrawdownHealed", months.ToString(CultureInfo.InvariantCulture)),
    };

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

        _prefs.Save("List", ListCombo.SelectedItem is ComboBoxItem { Tag: string key } ? key : AssetClassLists.AllKey);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        var key = _prefs.GetString("List", AssetClassLists.AllKey);

        ListCombo.SelectedItem =
            ListCombo.Items.OfType<ComboBoxItem>().FirstOrDefault(i => i.Tag is string c && c == key)
            ?? ListCombo.Items[0];

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
