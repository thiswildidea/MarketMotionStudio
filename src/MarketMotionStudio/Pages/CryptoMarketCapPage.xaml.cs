using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The value board for coins: the fifteen largest, over the span, ranked at every moment.
///
/// No renderer of its own: the value board is the sector race drawing
/// <see cref="RaceMetric.Amount"/>, exactly as the stock market-cap board is. What
/// differs is where the field comes from — a ranking fetched at fetch time rather than
/// a roster written into the app — and that is why this page has nothing to tick: the
/// board is whoever is large today.
/// </summary>
public sealed partial class CryptoMarketCapPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>The span that hands the two date pickers over instead of a month count.</summary>
    private const int CustomMonths = 0;

    /// <summary>
    /// The spans offered. Seven years is the longest that means anything here, because
    /// the value source's estimate begins in 2019 — a longer entry would be a button
    /// that always draws the same picture and never says why.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (12, "StudioRange12M"),
        (24, "StudioRange24M"),
        (60, "StudioRange60M"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("CryptoMarketCap.");

    /// <summary>The fetched board, or null before anything has been fetched.</summary>
    private SectorRaceSeries? _series;

    public CryptoMarketCapPage()
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

        RangeCombo.SelectedIndex = 1;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-5);
        ToDate.Date = today;

        // Its own id, though the coin page's range box is the same control: the two pages
        // never sit on screen together, but a judgement that asks for one by id must not
        // be handed the other one's.
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(RangeCombo, "CryptoMarketCapRange");

        ListText.Text = Strings.Format("CryptoMarketCapCount", CryptoCapBoard.Board);

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
    protected override string JobName => Strings.Get("CryptoMarketCapPageTitle.Text");

    /// <summary>
    /// “市值前 15”. The stock board's own label, reused rather than reworded: it names a
    /// count of rows and not a market, and two keys saying the same thing is how a title
    /// comes to disagree with the frame's own corner.
    /// </summary>
    private string AutoTitle() => Strings.Format("MarketCapListLabel", CryptoCapBoard.Board);

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
            // `showTop`: the board is fifteen coins and the frame draws all fifteen of
            // them, ranked at every moment — which is what makes membership visible as
            // coins trade places rather than as a fixed list of names.
            Preview.Renderer = new SectorRaceRenderer(
                series, RaceMetric.Amount, VideoSettings.Duration, CryptoCapBoard.Board,
                titleStyle: TitlePanel.MainStyle, subtitleStyle: TitlePanel.SubtitleStyle)
            {
                Style = RaceStyleCombo.ChosenStyle,
                Faces = CompanyLogoCache.Shared,
                Title = title,
                ShowTitle = showTitle,
                Subtitle = subtitle,
                ListLabel = AutoTitle(),
                UnitWord = Strings.Get("CryptoUnitCoins"),

                // Days, not months, unlike the stock board: this series is daily, and the
                // header counts whatever the axis is made of.
                SpanWord = Strings.Get("CryptoDaysUnit"),
                UnitKey = "MarketCapUnitUsd",
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
        var (start, end) = ChosenRange();

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var series = await CryptoCapBoard.LoadAsync(
                Services.CryptoCaps, start, end, progress, cancellation);

            _series = series;

            ApplyPreviewSettings();
            ShowMoment(1);

            var champion = series.Standings(RaceMetric.Amount)[0];
            var leader = series.Entries[champion.Index].Name;

            ShowFetched(
                Strings.Format(
                    "CryptoMarketCapFetched",
                    series.Racers,
                    series.Days,
                    TurnoverRenderer.Iso(series.Dates[0]),
                    TurnoverRenderer.Iso(series.Dates[^1]),
                    leader),
                InfoBarSeverity.Success,
                series.Dates[0],
                start,
                Strings.Format("CryptoRangeShort", TurnoverRenderer.Iso(series.Dates[0])));

            // Five minutes, not the three the other pages run on. A board is two questions
            // to two hosts and then one walked across as many pages as the coins need; the
            // worst case is a batch this source refuses, which is then asked coin by coin.
            // Three minutes is enough for every other page on this app because every other
            // page asks one host one question.
        }, TimeSpan.FromMinutes(5));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

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
        // Raised by the selection assignment in the constructor, before CustomRange exists.
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
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetName(PlayButton, label);
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

        VideoSettings.Restore(_prefs);
        TitlePanel.Restore(_prefs);
        RaceStyleCombo.Bind(_prefs);
        RaceStyleCombo.Chosen += (_, _) => ApplyPreviewSettings();

        _prefs.Restoring = false;
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

        VideoSettings.Save(_prefs);
        TitlePanel.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
