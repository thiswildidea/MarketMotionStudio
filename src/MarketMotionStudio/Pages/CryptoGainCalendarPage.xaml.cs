using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The gain-loss calendar on a coin.
///
/// No renderer of its own: the calendar grid is metric-driven and takes a
/// <see cref="TurnoverSeries"/>, so this page is only a different loader — one coin's
/// daily bars shaped into that record — behind the same
/// <see cref="CalendarHeatmapRenderer"/> drawing <see cref="Metric.Return"/>.
///
/// **Why a calendar is the one stock page that reads better here.** The grid is drawn
/// over calendar days, and a stock's year is a third empty: weekends, holidays, the
/// fortnight a company was suspended. A coin trades every day of every week, so the
/// whole year fills in — a calendar that is complete rather than one that is missing
/// two days in five. The page's subtitle says so, because a full grid looks like a page
/// that failed to leave the gaps out.
/// </summary>
public sealed partial class CryptoGainCalendarPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>
    /// The ranges offered, as a number of months. Zero means the custom range, which is
    /// the only one that consults the date pickers.
    ///
    /// A year is the longest of the fixed spans, and that is the grid's own shape rather
    /// than a ceiling inherited from somewhere: twelve months is what a calendar page is
    /// *for*, and a three-year span is three grids stacked, each small enough that the
    /// cells stop being readable. The custom range is where a longer one lives, and it is
    /// clipped to what the source carries like the other three crypto pages.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (3, "StudioRange3M"),
        (6, "StudioRange6M"),
        (12, "StudioRange12M"),
        (0, "StudioRangeCustom"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("CryptoCalendar.");

    /// <summary>The fetched grid, or null before anything has been fetched.</summary>
    private TurnoverSeries? _fetched;

    /// <summary>The coin the grid is drawn for.</summary>
    private CryptoAsset _asset = CryptoAsset.All[0];

    /// <summary>
    /// The furthest back a range can reach, which is the source's own reach rather than
    /// a number chosen for how it sounds — see the other crypto pages' <c>Oldest</c>.
    /// </summary>
    private static DateOnly Oldest =>
        DateOnly.FromDateTime(DateTime.Now).AddDays(-CryptoQuotes.YahooMostDays);

    public CryptoGainCalendarPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        RangeCombo.SelectedIndex = 1;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddMonths(-6);
        ToDate.Date = today;

        // The coins are the market's own list, in its own order, under the name the
        // current language has for them — the same twelve the other three crypto pages
        // offer, and read back from the same place rather than written out again.
        foreach (var asset in CryptoAsset.All)
        {
            CoinCombo.Items.Add(new ComboBoxItem { Content = asset.Display, Tag = asset.Code });
        }

        CoinCombo.SelectedIndex = 0;

        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(CoinCombo, "CryptoCalendarCoin");
        Microsoft.UI.Xaml.Automation.AutomationProperties.SetAutomationId(RangeCombo, "CryptoCalendarRange");

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

        // After every control exists and every handler is attached, so a restored value
        // reaches the preview through the same path a typed one does.
        RestorePreferences();
        ApplyPreviewSettings();
    }

    protected override InfoBar StatusControl => Status;

    /// <summary>Reuses the page title as the job label, as the other pages do.</summary>
    protected override string JobName => Strings.Get("CryptoCalendarPageTitle.Text");

    // ---- preview -------------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_fetched is { } fetched)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, fetched.Count, fetched.Peak);

            Preview.Renderer = new CalendarHeatmapRenderer(fetched, plan, Metric.Return)
                { Title = title, ShowTitle = showTitle };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = Strings.Format("GainCalendarDefaultTitle", _asset.Display);

        var ready = _fetched is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>
    /// The title the frame will draw: the typed one, or the default naming the coin.
    /// Resolved here rather than in the renderer because the default follows the page's
    /// coin, not the metric's fixed one.
    /// </summary>
    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0
            ? VideoSettings.TitleText
            : Strings.Format("GainCalendarDefaultTitle", _asset.Display);

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 6;

        if (months == 0)
        {
            var from = DateOnly.FromDateTime(FromDate.Date.DateTime);
            var to = DateOnly.FromDateTime(ToDate.Date.DateTime);

            // Clipped to the source's reach rather than refused, as on the other three
            // crypto pages: a range reaching past it is answered with the part that
            // exists and a note saying where the picture now starts.
            return (from < Oldest ? Oldest : from, to);
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
    }

    private async void Fetch()
    {
        var (start, end) = ChosenRange();

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var fetched = await CryptoCalendar.LoadAsync(
                Services.Crypto, _asset, start, end, progress, cancellation);

            _fetched = fetched;

            ApplyPreviewSettings();

            // Parked on the last frame: the closing statistics are what someone wants to
            // look at before deciding whether to export, and frame zero shows an empty
            // grid instead.
            ShowMoment(1);

            // Natural days, not trading days: a coin's market does not close, so every
            // day in the span is a day it traded.
            ShowFetched(
                Strings.Format(
                    "CryptoCalendarFetched",
                    fetched.Count,
                    TurnoverRenderer.Iso(fetched.Dates[0]),
                    TurnoverRenderer.Iso(fetched.Dates[^1]),
                    fetched.UpDays,
                    fetched.DownDays),
                InfoBarSeverity.Success,
                fetched.Dates[0],
                start,
                Strings.Format("CryptoRangeShort", TurnoverRenderer.Iso(fetched.Dates[0])));
        }, TimeSpan.FromMinutes(2));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    // ---- playback -----------------------------------------------------------------------

    /// <summary>
    /// Moves the preview and the scrub bar together, without the slider's own handler
    /// stopping the playback that might be driving it.
    /// </summary>
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

        var custom = RangeCombo.SelectedItem is ComboBoxItem { Tag: 0 };
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
        // At the end there is nothing left to run, and a play button that does nothing
        // reads as a broken one — see the longer note on the stock calendar.
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
    /// An icon carries no text of its own, so the same word that picks the glyph is put
    /// on the tooltip and on the name a screen reader announces.
    /// </summary>
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
        if (Preview.Renderer is not { } renderer || _fetched is not { } fetched || App.Window is not { } window)
        {
            return;
        }

        // One gate, asked by every page. Writing the file — as opposed to drawing it —
        // is what the subscription buys, and the one place allowed to answer that is
        // asked before anything is read for the encode.
        if (!await MarketMotionStudio.Views.SubscriptionOffer.PermitAsync(XamlRoot, window))
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
                VideoExporter.VideoName(label, fetched.Dates[0], fetched.Dates[^1], format),
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
        if (Preview.Renderer is not { } renderer || _fetched is not { } fetched || App.Window is not { } window)
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
                FrameExporter.CoverName(ResolvedTitle(), fetched.Dates[0], fetched.Dates[^1], format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    // ---- preferences --------------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var months = _prefs.GetInt("Months", 6);
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

        var code = _prefs.GetString("Code", CryptoAsset.All[0].Code);
        var coin = Array.FindIndex(CryptoAsset.All, a => a.Code == code);

        CoinCombo.SelectedIndex = coin >= 0 ? coin : 0;
        _asset = CryptoAsset.All[CoinCombo.SelectedIndex];

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Months", RangeCombo.SelectedItem is ComboBoxItem { Tag: int m } ? m : 6);
        _prefs.Save("From", FromDate.Date.ToString("O"));
        _prefs.Save("To", ToDate.Date.ToString("O"));
        _prefs.Save("Code", _asset.Code);

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
