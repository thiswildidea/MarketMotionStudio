using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The currency corridor: six pairs, each on its own row, each measured against the range it has
/// actually traded in.
///
/// The twelfth page, and the first whose row is a **place** rather than a quantity. Every other
/// board here is a race: a row's value is how much of something it has, and the bar is that
/// amount. A corridor's row is a range — the floor and the ceiling the pair has been between —
/// and what is read off it is where inside that range the rate sits. So the row is drawn full
/// width in every frame and it is the marker that moves, which is also why the board cannot
/// rescale: there is no axis to rescale, because six pairs on six scales have nothing in common
/// to share one.
///
/// **Two lists, offered separately.** Not because one is domestic — because the source's coverage
/// is not the same for both. The crosses all begin in 2005-07 and carry 325 months; of the
/// renminbi pairs only USD/CNY reaches back that far, the other five begin in 2016-01. Put them
/// on one board and the picture is a comment on when the source started quoting each pair, which
/// nobody reading it asked about.
///
/// **Monthly, and one request per pair.** The endpoint returns a whole monthly history in one
/// reply — 325 months against a 430-month ceiling — so there is no walk here and no paging, and
/// "as far back as there is" costs six requests rather than a hundred and twenty. A daily corridor
/// would buy a picture of noise: a rate that moves a few points a year does not need a marker
/// that moves two hundred times.
///
/// **No adjustment of any kind.** A currency has no dividend and no split, and the source's
/// adjusted series for these codes is the same numbers — but the corridor is drawn from
/// <see cref="TencentKline.RawBarsAsync"/> for the same reason the A+H page uses it: an
/// adjustment applied to one side of a comparison is a comparison of two different things, and
/// the raw call is the one that cannot be something else by accident.
/// </summary>
public sealed partial class FxCorridorPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    private readonly StudioPreferences _prefs = new("FxCorridor.");

    private FxCorridorSeries? _series;

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
        (0, "FxCorridorRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    private static readonly (string Key, string Label)[] Lists =
    [
        (FxLists.CnyKey, "FxCorridorListCny"),
        (FxLists.CrossesKey, "FxCorridorListCrosses"),
    ];

    public FxCorridorPage()
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

        // Ten years: long enough that a corridor has been walked in, short enough that the five
        // renminbi pairs quoted only from 2016 are on the board for all of it.
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

    protected override string JobName => Strings.Get("FxCorridorPageTitle.Text");

    /// <summary>“汇率走廊” — what the frame says when no title was typed.</summary>
    private static string AutoTitle() => Strings.Get("FxCorridorPageTitle.Text");

    private IReadOnlyList<FxPair> ChosenList()
    {
        var key = ListCombo.SelectedItem is ComboBoxItem { Tag: string chosen } ? chosen : FxLists.CnyKey;

        return FxLists.Of(key);
    }

    // ---- the picture -------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        if (_series is { } series)
        {
            Preview.Renderer = new FxCorridorRenderer(series, VideoSettings.Duration)
            {
                Title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle(),
                ShowTitle = VideoSettings.ShowTitle,

                // Both by the page, and both for the reason the race renderer learned the hard
                // way: the interval and the list are what the page chose, and a renderer that
                // names either from its own table names the wrong one on the page that differs.
                SpanWord = Strings.Get("MarketCapUnitMonths"),
                UnitWord = Strings.Get("AhPremiumUnitPairs"),
            };
        }
        else
        {
            _stage.Title = VideoSettings.TitleText.Length > 0
                ? VideoSettings.TitleText
                : Strings.Get("FxCorridorStageTitle");
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
        // A different list is a different board, so whatever was fetched is no longer what the
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

            var series = await FxRates.LoadAsync(
                Services.Quotes, ChosenList(), start, end, progress, cancellation);

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var standings = FxRates.Standings(series);

            if (standings.Length == 0)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("FxCorridorTooFew"));
                return;
            }

            var ceiling = standings[0];
            var floor = standings[^1];

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "FxCorridorFetched",
                series.Quoted,
                series.Months,
                series.Pairs[ceiling.Index].Pair,
                Percent(ceiling.Position),
                series.Pairs[floor.Index].Pair,
                Percent(floor.Position)));
        }, TimeSpan.FromMinutes(6));
    }

    private static string Percent(double position) =>
        ((int)Math.Round(position * 100)).ToString(CultureInfo.InvariantCulture) + "%";

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

        // One gate, asked by every page. Writing the file — as opposed to
        // drawing it — is what the subscription buys, and the one place allowed
        // to answer that is asked before anything is read for the encode.
        if (!await MarketMotionStudio.Views.SubscriptionOffer.PermitAsync(XamlRoot, window))
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

        _prefs.Save("List", ListCombo.SelectedItem is ComboBoxItem { Tag: string key } ? key : FxLists.CnyKey);
        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 120);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
    }

    private void RestorePreferences()
    {
        var key = _prefs.GetString("List", FxLists.CnyKey);

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
