using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The A+H page: one company, two listings, two currencies — ranked by how much more expensive
/// the mainland listing is.
///
/// The tenth page and the third to use the horizontal race, which is the point of the page as
/// much as the data is: every row is a different company rather than a different day, and the
/// ranking across them reverses over the years.
///
/// **What the frame shows is the dearest fifteen, and all of them are dear.** The premium is
/// structurally positive — sixty-seven of the sixty-nine are in September 2026, from +2% to
/// +194% — so the bars grow right from a zero axis at the far left. Only 招商银行 and 药明康德
/// trade the other way, their H shares above their A shares, and at −6% and −9% they sit at the
/// bottom of the list where a top-fifteen board never reaches. The bars therefore say "how much
/// dearer" and not "which side", and the manual, the card and this comment all say so — a frame
/// drawn with a bar poking left would contradict all three.
///
/// Two things make it unlike the market-cap board it otherwise resembles.
///
/// **Nothing is derived.** A past market value had to be today's value times an adjusted ratio,
/// because a share count's history is not served. A premium is two prices and a rate, all three
/// served, and the page fetches the *unadjusted* series for exactly that reason — see
/// <see cref="AhPremiumSeries"/>.
///
/// **The field is what it is.** The pairs are listed in the source file, and the page reports how
/// many of them survived the span rather than promising a number: a pair whose Hong Kong listing
/// is four years old is dropped from a ten-year run and present in a three-year one. That is why
/// the count on the card is a count and not a name.
/// </summary>
public sealed partial class AhPremiumPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("AhPremium.");

    private SectorRaceSeries? _series;

    /// <summary>
    /// -1 is the custom span and 0 is "as far back as the rate series goes", which is what the
    /// plan and holding pages already mean by 0. The two cannot share a number: this page offers
    /// a longest span *and* a custom one, and the page that introduced 0 was one where they were
    /// the same thing.
    /// </summary>
    private const int CustomMonths = -1;

    private static readonly (int Months, string Key)[] Ranges =
    [
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (0, "AhRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    public AhPremiumPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // Five years: long enough for a premium to have moved, short enough to carry the pairs
        // whose Hong Kong listing is a few years old.
        RangeCombo.SelectedIndex = 1;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-5);
        ToDate.Date = today;

        ListText.Text = Strings.Get("AhPremiumCount");

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

    protected override string JobName => Strings.Get("AhPremiumPageTitle.Text");

    /// <summary>“AH 溢价” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("AhPremiumPageTitle.Text");

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            // The race renderer on its **return** metric: a premium is a percentage, and that is
            // the metric whose value labels end in % and whose decimals — two — suit a spread of
            // percentage points. The renderer puts the zero axis wherever the data needs it, so
            // with every drawn value positive the bars grow from the left edge.
            //
            // `showTop`: the field is sixty-odd pairs and the frame draws fifteen of them, the
            // fifteen that were dearest at each moment.
            Preview.Renderer = new SectorRaceRenderer(
                series, RaceMetric.Return, VideoSettings.Duration, AhPairs.Board)
            {
                Title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle(),
                ShowTitle = VideoSettings.ShowTitle,
                ListLabel = Strings.Get("AhPremiumListLabel"),
                UnitWord = Strings.Get("AhPremiumUnitPairs"),

                // Monthly, so the header counts months. `MarketCapUnitMonths` rather than a key
                // of this page's own: "个月" is one string in this app, not two that happen to
                // agree today, and the same rule already keeps "近 5 年" shared with the plan page.
                SpanWord = Strings.Get("MarketCapUnitMonths"),
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("AhPremiumStageTitle");
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
                // "As far back as there is" — asked for generously and trimmed by the data, which
                // is the only thing that knows where the rate series starts.
                return (today.AddYears(-12), today);
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

            var series = await AhPremiumSeries.LoadAsync(
                Services.Quotes, start, end, progress, cancellation);

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = series.Standings(RaceMetric.Return);
            var dearest = standings[0];

            // The dearest and the cheapest **of the fifteen drawn**, not of the field. The field
            // holds pairs the frame never shows, and "cheapest" naming a company nobody can see on
            // the frame is a sentence about the data rather than about the picture.
            var cheapest = standings[Math.Min(AhPairs.Board, standings.Length) - 1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "AhPremiumFetched",
                series.Racers,
                series.Days,
                series.Entries[dearest.Index].Name,
                FormatValue(dearest.Value),
                series.Entries[cheapest.Index].Name,
                FormatValue(cheapest.Value)));
        }, TimeSpan.FromMinutes(6));
    }

    private static string FormatValue(double value) =>
        (value >= 0 ? "+" : "−") + Math.Abs(value).ToString("0.0", CultureInfo.InvariantCulture) + "%";

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

        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 60);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        var months = _prefs.GetInt("Months", 60);
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
