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
/// The 24-hour movers board: each coin's change versus the previous day, raced day by day.
///
/// No renderer of its own: the board is the sector race on <see cref="RaceMetric.Return"/>, but with
/// the bars coloured by sign (red up, green down) and ranked by magnitude — a movers board is about
/// the biggest moves either way, not a signed ladder. CoinGecko's live 24h ranking is the natural
/// source and is used when reachable; when it is not, the move is the daily close-over-previous-close
/// from CoinMetrics, which the page's note names as the proxy it is.
/// </summary>
public sealed partial class CryptoMoversPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>The span that hands the two date pickers over instead of a month count.</summary>
    private const int CustomMonths = 0;

    /// <summary>
    /// The spans offered. Sixty days by default: a movers board is a race through recent days, and a
    /// fortnight is too few frames to see the ranking shuffle.
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
    private readonly StudioPreferences _prefs = new("CryptoMovers.");

    /// <summary>The fetched board, or null before anything has been fetched.</summary>
    private SectorRaceSeries? _series;

    public CryptoMoversPage()
    {
        InitializeComponent();

        // Late-landing logos repaint the preview; the marshal keeps the hop on
        // the UI thread, the way the cache's contract asks for.
        CompanyLogoCache.Shared.Marshal = a => DispatcherQueue.TryEnqueue(() => a());
        CompanyLogoCache.Shared.Invalidated = () => Preview.Redraw();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 2;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-5);
        ToDate.Date = today;

        Coins.Limit = MaxCoins;
        Coins.Changed += OnCoinsChanged;

        AutomationProperties.SetAutomationId(RangeCombo, "CryptoMoversRange");

        VideoSettings.AllowHideTitle = false;
        VideoSettings.AllowTitleText = false;
        VideoSettings.Changed += (_, _) =>
        {
            ApplyPreviewSettings();
            VideoSettings.Save(_prefs);
        };

        // 标题区的样式与文字归 TitlePanel：面板的标题框和隐藏开关都不再是编辑入口。
        TitlePanel.Changed += (_, _) =>
        {
            VideoSettings.SetTitleText(TitlePanel.TitleText);
            ApplyPreviewSettings();
            SavePreferences();
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
    protected override string JobName => Strings.Get("CryptoMoversPageTitle.Text");

    /// <summary>The coins on the frame, read off the picker rather than kept here.</summary>
    private IReadOnlyList<CryptoAsset> Chosen() =>
        [.. Coins.Selected.Select(entry => CryptoAsset.Of(entry.Code)).OfType<CryptoAsset>()];

    /// <summary>The headline the frame draws: the typed title, or the page's own name.</summary>
    private string AutoTitle() => Strings.Get("CryptoMoversPageTitle.Text");

    // ---- preview -------------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : AutoTitle();
        var showTitle = !TitlePanel.HideTitle;
        var subtitle = TitlePanel.SubtitleText;

        // 徽章画合并后的主标题：标题文字走 title（含默认回退）。
        TitlePanel.TitleText = title;

        if (_series is { } series)
        {
            // Ranked by magnitude — a +8% and a −7% belong next to each other, not on opposite ends
            // of a signed ladder — and coloured by sign so a rise and a fall read at a glance. The
            // first day has no prior close and reads zero, so empty rows are left off the board.
            Preview.Renderer = new SectorRaceRenderer(
                series, RaceMetric.Return, VideoSettings.Duration, series.Racers, rankByMagnitude: true,
                TitlePanel.MainStyle, TitlePanel.SubtitleStyle)
            {
                Style = RaceStyleCombo.ChosenStyle,
                Faces = CompanyLogoCache.Shared,
                Title = title,
                ShowTitle = showTitle,
                Subtitle = subtitle,
                ListLabel = AutoTitle(),
                UnitWord = Strings.Get("CryptoUnitCoins"),
                SpanWord = Strings.Get("CryptoDaysUnit"),
                ColourBySign = true,
                HideEmptyRows = true,
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
        var months = RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 60;

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
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CryptoPickOne"));
            return;
        }

        var (start, end) = ChosenRange();

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var series = await CryptoMovers.LoadAsync(
                Services.CryptoCaps, chosen, start, end, progress, cancellation);

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var champion = series.Standings(RaceMetric.Return)[0];
            var leader = series.Entries[champion.Index].Name;

            ShowFetched(
                Strings.Format(
                    "CryptoMoversFetched",
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

        var months = _prefs.GetInt("Months", 60);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 2;

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
        TitlePanel.Restore(_prefs);
        RaceStyleCombo.Bind(_prefs);
        RaceStyleCombo.Chosen += (_, _) => ApplyPreviewSettings();

        _prefs.Restoring = false;

        _ready = true;
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 60);
        _prefs.Save("From", FromDate.Date.ToString("O"));
        _prefs.Save("To", ToDate.Date.ToString("O"));
        _prefs.Save("Coins", string.Join(",", Chosen().Select(asset => asset.Code)));

        VideoSettings.Save(_prefs);
        TitlePanel.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
