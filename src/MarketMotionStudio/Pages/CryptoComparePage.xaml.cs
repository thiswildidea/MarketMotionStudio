using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Automation;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// Several coins' prices, each rebased to 100 on the first shared day, raced as cumulative returns.
///
/// No renderer of its own: the race is the sector race on <see cref="RaceMetric.Return"/>, exactly the
/// metric a rebased-to-100 line is — every coin starts at 0% (its own 100) and the bars are "whose
/// price grew faster from the same line". The loader is the only new thing: daily prices from
/// CoinMetrics, aligned and rebased. Coloured by coin, not by sign, because the rows are coins to
/// follow, not one-day moves.
/// </summary>
public sealed partial class CryptoComparePage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>The span that hands the two date pickers over instead of a month count.</summary>
    private const int CustomMonths = 0;

    /// <summary>
    /// The spans offered. Two years is the default and the shortest that means anything: a normalized
    /// line is a question about a trend, and a month of two flat-ish coins is a picture of noise.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (12, "StudioRange12M"),
        (24, "StudioRange24M"),
        (60, "StudioRange60M"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    /// <summary>How many coins one frame holds — the palette's own ceiling, a refusal rather than a trim.</summary>
    private const int MaxCoins = 6;

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("CryptoCompare.");

    /// <summary>The fetched race, or null before anything has been fetched.</summary>
    private SectorRaceSeries? _series;

    public CryptoComparePage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 1;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-2);
        ToDate.Date = today;

        Coins.Limit = MaxCoins;
        Coins.Changed += OnCoinsChanged;

        // Its own id, though the range box is the same control the other pages use: the two pages
        // never sit on screen together, but a judgement that asks for one by id must not be handed
        // the other one's.
        AutomationProperties.SetAutomationId(RangeCombo, "CryptoCompareRange");

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

        SetPlaybackState(playing: false);

        RestorePreferences();
        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("CryptoComparePageTitle.Text");

    /// <summary>The coins on the frame, read off the picker rather than kept here.</summary>
    private IReadOnlyList<CryptoAsset> Chosen() =>
        [.. Coins.Selected.Select(entry => CryptoAsset.Of(entry.Code)).OfType<CryptoAsset>()];

    /// <summary>The headline the frame draws: the typed title, or the page's own name.</summary>
    private string AutoTitle() => Strings.Get("CryptoComparePageTitle.Text");

    // ---- preview -------------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_series is { } series)
        {
            // `showTop` is the whole field: a normalized comparison is a small set of coins meant to
            // be read together, so every row is drawn rather than the top few.
            Preview.Renderer = new SectorRaceRenderer(
                series, RaceMetric.Return, VideoSettings.Duration, series.Racers)
            {
                Title = title,
                ShowTitle = showTitle,
                ListLabel = AutoTitle(),

                // Days, not months: this series is daily, and the header counts whatever the axis is.
                UnitWord = Strings.Get("CryptoUnitCoins"),
                SpanWord = Strings.Get("CryptoDaysUnit"),
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = AutoTitle();

        var ready = _series is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 24;

        if (months == CustomMonths)
        {
            return (DateOnly.FromDateTime(FromDate.Date.DateTime),
                    DateOnly.FromDateTime(ToDate.Date.DateTime));
        }

        var today = DateOnly.FromDateTime(DateTime.Now);
        return (today.AddMonths(-months), today);
    }

    // ---- fetch ---------------------------------------------------------------------------

    private async void Fetch()
    {
        var chosen = Chosen();

        if (chosen.Count == 0)
        {
            // The picker keeps at least one on by itself, so this is the arm that lands here if that
            // ever stops being true — and it is the honest thing to say rather than fetching nothing.
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CryptoPickOne"));
            return;
        }

        var (start, end) = ChosenRange();

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var series = await CryptoCompare.LoadAsync(
                Services.CryptoCaps, chosen, start, end, progress, cancellation);

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var champion = series.Standings(RaceMetric.Return)[0];
            var leader = series.Entries[champion.Index].Name;

            ShowFetched(
                Strings.Format(
                    "CryptoCompareFetched",
                    series.Racers,
                    series.Days,
                    TurnoverRenderer.Iso(series.Dates[0]),
                    TurnoverRenderer.Iso(series.Dates[^1]),
                    leader),
                InfoBarSeverity.Success,
                series.Dates[0],
                start,
                Strings.Format("CryptoRangeShort", TurnoverRenderer.Iso(series.Dates[0])));
        }, TimeSpan.FromMinutes(5));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    private void OnCoinsChanged(object? sender, EventArgs e)
    {
        _series = null;
        SavePreferences();

        if (_ready)
        {
            ApplyPreviewSettings();
        }
    }

    // ---- playback -----------------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnRangeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CustomRange is null)
        {
            return;
        }

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: CustomMonths };
        CustomRange.Visibility = custom ? Visibility.Visible : Visibility.Collapsed;

        SavePreferences();
    }

    private void OnScrub(object sender, RangeBaseValueChangedEventArgs e) => _playback?.Seek(Scrub.Value);

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
        AutomationProperties.SetName(PlayButton, label);
    }

    TimeSpan IPlaybackHost.PlaybackDuration => VideoSettings.Duration;

    // ---- export -------------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _series is not { } series || App.Window is not { } window)
        {
            return;
        }

        if (!await MarketMotionStudio.Views.SubscriptionOffer.PermitAsync(XamlRoot, window))
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;
        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle();

        CancelButton.IsEnabled = true;

        var limit = TimeSpan.FromMinutes(5) + (duration * 4);

        Diagnostics.CrashLog.Note($"export: clicked, {format.Width}x{format.Height} dur={duration}");

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
                VideoExporter.VideoName(label, series.Dates[0], series.Dates[^1], format),
                report, cancellation);

            clock.Stop();

            var properties = await file.GetBasicPropertiesAsync();

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioExported",
                file.Name,
                (properties.Size / 1048576.0).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture),
                clock.Elapsed.TotalSeconds.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture),
                ((int)duration.TotalSeconds).ToString(System.Globalization.CultureInfo.InvariantCulture),
                folder.Path));
        }, limit);

        CancelButton.IsEnabled = false;
    }

    private async void OnSaveCover(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _series is not { } series || App.Window is not { } window)
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

            var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle();

            var file = await FrameExporter.SavePngAsync(
                renderer, format, VideoSettings.Margins, Preview.Progress, folder,
                FrameExporter.CoverName(label, series.Dates[0], series.Dates[^1], format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences --------------------------------------------------------------------

    private bool _ready;

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var months = _prefs.GetInt("Months", 24);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 1;

        if (DateTime.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = from;
        }

        if (DateTime.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = to;
        }

        Coins.Select(_prefs.GetString("Coins", string.Empty).Split(
            ',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;

        _ready = true;
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 24);
        _prefs.Save("From", FromDate.Date.ToString("O"));
        _prefs.Save("To", ToDate.Date.ToString("O"));
        _prefs.Save("Coins", string.Join(",", Chosen().Select(asset => asset.Code)));

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
