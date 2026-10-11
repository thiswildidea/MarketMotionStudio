using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// A coin's market value over the years, with its price under it.
///
/// No renderer of its own: the value-history renderer takes a <see cref="CapBoard"/>
/// and draws the two panels, so this page is a loader and a set of choices. The two
/// panels are the point of the page, and they are the stock page's reason too — a
/// value line that climbs while the price line does not is coins being minted, and a
/// price that climbs faster than the value is a supply being burned. On a coin the
/// first of those is ordinary: bitcoin mints until 2140, so the two lines come apart
/// every single day.
///
/// **The value here is measured, not recovered.** The stock page multiplies a share
/// count it worked out of the turnover rate by a price, and says so. This page is
/// handed the value: CoinMetrics publishes it daily, back to 2010 on bitcoin and to
/// 2019 on coins it carries only as an estimate. Which of the two a coin got is not
/// shown, because the difference is under a percent where they overlap and the point
/// of the page is the shape, not the sixth digit.
/// </summary>
public sealed partial class CryptoCapHistoryPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>The span that hands the two date pickers over instead of a month count.</summary>
    private const int CustomMonths = 0;

    /// <summary>
    /// The spans offered, none of them shorter than a year.
    ///
    /// Unlike the stock page's list this one has no month-scale entry, and that is the
    /// subject rather than the source: a coin's value moves with its supply, which is a
    /// slow variable, and thirty days of it is a price chart with a different label.
    /// Thirty years is the longest, which is past every coin — the span is clipped to
    /// what the source carries and the page says where the picture really starts.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (12, "StudioRange12M"),
        (24, "StudioRange24M"),
        (60, "StudioRange60M"),
        (120, "StudioRange120M"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("CryptoCapHistory.");

    /// <summary>The fetched board, or null before anything has been fetched.</summary>
    private CapBoard? _board;

    /// <summary>The coin the board is drawn for.</summary>
    private CryptoAsset _asset = CryptoAsset.All[0];

    /// <summary>Whether the page is finished being built; see the handlers that read it.</summary>
    private bool _ready;

    public CryptoCapHistoryPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 2;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-10);
        ToDate.Date = today;

        foreach (var asset in CryptoAsset.All)
        {
            CoinCombo.Items.Add(new ComboBoxItem { Content = asset.Display, Tag = asset.Code });
        }

        CoinCombo.SelectedIndex = 0;

        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(CoinCombo, "CryptoCapCoin");
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(RangeCombo, "CryptoCapRange");

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

        SetPlaybackState(playing: false);

        RestorePreferences();
        ApplyPreviewSettings();

        _ready = true;
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("CryptoCapHistoryPageTitle.Text");

    private void OnLookChanged(object sender, RoutedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

        ApplyPreviewSettings();
        SavePreferences();
    }

    private bool CrossSafeRight() => CrossCheck.IsChecked is true;

    // ---- preview -------------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_board is { } board)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, board.Count, board.CapPeak);

            // Absolute, always: this page draws one coin, and a value rebased to 100 at
            // its own first day says nothing that the two lines do not already say.
            Preview.Renderer = new CapHistoryRenderer(board, plan, CapAxis.Absolute, CrossSafeRight())
            {
                Title = title,
                ShowTitle = showTitle,
                Code = board.Tracks[0].Code,

                // Every word the frame says about the figures comes from here, because a
                // renderer that named its own data would go on naming it on whichever
                // page came to share it.
                CapWord = Strings.Get("CryptoCapWord"),
                CapUnitWord = Strings.Format("CapHistoryCapUnit", Strings.Get("DcaCurrencyUsd")),
                PriceWord = Strings.Get("CryptoPriceWord"),
                PriceUnitWord = Strings.Get("DcaCurrencyUsd"),
                SpanWord = Strings.Get("CryptoDaysUnit"),
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = ResolvedTitle();

        var ready = _board is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>The title the frame will draw: the typed one, or the default naming the coin.</summary>
    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0
            ? VideoSettings.TitleText
            : Strings.Format("CryptoCapDefaultTitle", _asset.Display);

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

    private void OnCoinChanged(object sender, SelectionChangedEventArgs e)
    {
        if (CoinCombo.SelectedItem is ComboBoxItem { Tag: string code }
            && CryptoAsset.Of(code) is { } asset)
        {
            _asset = asset;
        }

        SavePreferences();

        if (_ready)
        {
            ApplyPreviewSettings();
        }
    }

    private async void Fetch()
    {
        var (start, end) = ChosenRange();

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var board = await CryptoCapLoader.LoadAsync(
                Services.CryptoCaps, _asset, start, end, progress, cancellation);

            _board = board;

            ApplyPreviewSettings();
            ShowMoment(1);

            ShowFetched(
                Strings.Format(
                    "CryptoCapFetched",
                    board.Count,
                    TurnoverRenderer.Iso(board.Start),
                    TurnoverRenderer.Iso(board.End),
                    board.Tracks[0].FinalCap.ToString("N0", System.Globalization.CultureInfo.CurrentCulture)),
                InfoBarSeverity.Success,
                board.Start,
                start,
                Strings.Format("CryptoRangeShort", TurnoverRenderer.Iso(board.Start)));
        }, TimeSpan.FromMinutes(3));
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
        if (Preview.Renderer is not { } renderer || _board is null || App.Window is not { } window)
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
        var label = ResolvedTitle();
        var board = _board;

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
                VideoExporter.VideoName(label, board.Start, board.End, format),
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

    // ---- preferences --------------------------------------------------------------------

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

        var code = _prefs.GetString("Code", CryptoAsset.All[0].Code);
        var coin = Array.FindIndex(CryptoAsset.All, a => a.Code == code);

        CoinCombo.SelectedIndex = coin >= 0 ? coin : 0;
        _asset = CryptoAsset.All[CoinCombo.SelectedIndex];

        CrossCheck.IsChecked = _prefs.GetInt("Cross", 0) == 1;

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
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
        _prefs.Save("Code", _asset.Code);
        _prefs.Save("Cross", CrossSafeRight() ? 1 : 0);

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
