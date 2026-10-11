using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;

namespace MarketMotionStudio.Pages;

/// <summary>
/// The same question the holdings page asks — one purchase, held, and what the years
/// did to it — asked of a coin.
///
/// Everything about the arithmetic is <see cref="PositionLoader"/>'s and is not repeated
/// here: this page picks coins, an amount and a span, and the board that comes back is
/// the same board the stock page draws, through the same renderer. The one thing that
/// differs is where the closes come from, and even that is not a branch in the loader —
/// <see cref="ICloseWalk"/> is what the loader asks for, and this page hands it the walk
/// that reads a crypto source.
///
/// The differences that do matter are the ones a coin has rather than the ones this page
/// has. **A coin trades every day of the year**, so a span is calendar days and the
/// counts on the status line say "days" rather than "trading days" — a coin's year is
/// three hundred and sixty-five of them, and calling them trading days would understate
/// a decade by a third. And **there is nothing to adjust for**: no dividend, no split,
/// so the close is the whole return and the frame's disclaimer says so instead of
/// promising a reinvestment that never happened.
///
/// The page is only on the menu when a crypto source can be reached at all; see
/// <see cref="CryptoQuotes.ReachableAsync"/>. That is not a nicety — three pages
/// offering data they cannot fetch are three pages that fail.
/// </summary>
public sealed partial class CryptoPositionPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>Marks the two typed dates, as on the stock page.</summary>
    private const int CustomMonths = -1;

    /// <summary>
    /// The spans offered, as a number of months. Zero is "as far back as the source
    /// goes", which for a coin is the source's own ceiling rather than a discovery —
    /// see <see cref="Oldest"/>.
    /// </summary>
    private static readonly (int Months, string Key)[] Ranges =
    [
        (36, "DcaRange3Y"),
        (60, "DcaRange5Y"),
        (120, "DcaRange10Y"),
        (0, "DcaRangeMax"),
        (CustomMonths, "StudioRangeCustom"),
    ];

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("CryptoPosition.");

    private const int DefaultWindow = 60;

    private const int MinWindow = 10;

    private const int MaxWindow = 500;

    private PositionBoard? _board;

    /// <summary>Whether the page is finished being built; see the handlers that read it.</summary>
    private bool _ready;

    public CryptoPositionPage()
    {
        InitializeComponent();

        foreach (var (months, key) in Ranges)
        {
            RangeCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = months });
        }

        // Three years rather than "as far back as there is": a coin's decade is a
        // hundredfold and a chart of it is a hockey stick, which is the wrong shape to
        // open on.
        RangeCombo.SelectedIndex = 0;

        foreach (var (motion, key) in new[]
                 {
                     (PositionMotion.Grow, "PositionMotionGrow"),
                     (PositionMotion.Scroll, "PositionMotionScroll"),
                 })
        {
            MotionCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)motion });
        }

        MotionCombo.SelectedIndex = 0;

        var now = DateTimeOffset.Now;
        var oldest = now.AddDays(-CryptoQuotes.YahooMostDays);

        FromDate.MinYear = oldest;
        FromDate.MaxYear = now;
        ToDate.MinYear = oldest;
        ToDate.MaxYear = now;

        // Which coins are on the frame is a choice shared with the other two crypto
        // pages, and changing it retires the board: a frame still showing a coin that
        // is no longer switched on is a frame about a list nobody chose.
        Coins.Changed += OnCoinsChanged;

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

    protected override string JobName => Strings.Get("CryptoPositionPageTitle.Text");

    // ---- what is being drawn ---------------------------------------------------------

    private IReadOnlyList<RaceEntry> Chosen() => [.. Coins.Selected];

    // ---- the holding's terms ---------------------------------------------------------

    private double ChosenCapital
    {
        get
        {
            var text = CapitalBox.Text.Trim();

            return double.TryParse(text, NumberStyles.Float, CultureInfo.CurrentUICulture, out var capital) ? capital
                : double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out capital) ? capital
                : 0;
        }
    }

    private int ChosenMonths() =>
        RangeCombo.SelectedItem is ComboBoxItem { Tag: int months } ? months : 0;

    private PositionMotion ChosenMotion() =>
        MotionCombo.SelectedItem is ComboBoxItem { Tag: int motion }
            ? (PositionMotion)motion
            : PositionMotion.Grow;

    private bool CrossSafeRight() => CrossCheck.IsChecked is true;

    private int ChosenWindow()
    {
        var text = WindowBox.Text.Trim();

        var window = int.TryParse(text, NumberStyles.Integer, CultureInfo.CurrentUICulture, out var parsed) ? parsed
            : int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out parsed) ? parsed
            : DefaultWindow;

        return Math.Clamp(window, MinWindow, MaxWindow);
    }

    private void OnLookChanged(object sender, object e)
    {
        if (!_ready)
        {
            return;
        }

        ApplyPreviewSettings();
        SavePreferences();
    }

    private (DateOnly From, DateOnly To) CustomSpan() =>
        (DateOnly.FromDateTime(FromDate.Date.DateTime), DateOnly.FromDateTime(ToDate.Date.DateTime));

    /// <summary>
    /// The oldest day a span can start on: the source's own ceiling.
    ///
    /// Ten years for Yahoo, and one for CoinGecko — see
    /// <see cref="CryptoQuotes.GeckoMostDays"/>. The shorter of the two is not known
    /// until a source has answered, so the widest is offered and a range the source
    /// cannot fill comes back shorter, which the status line says rather than hides.
    /// </summary>
    private static DateOnly Oldest =>
        DateOnly.FromDateTime(DateTime.Now).AddDays(-CryptoQuotes.YahooMostDays);

    private (DateOnly Start, DateOnly End) ChosenRange()
    {
        var months = ChosenMonths();
        var today = DateOnly.FromDateTime(DateTime.Now);

        if (months == CustomMonths)
        {
            var (from, to) = CustomSpan();

            return (from, to > today ? today : to);
        }

        return months == 0 ? (Oldest, today) : (today.AddMonths(-months), today);
    }

    // ---- preview ---------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = ResolvedTitle();
        var showTitle = VideoSettings.ShowTitle;

        if (_board is { } board)
        {
            var plan = AnimationPlan.For(VideoSettings.Duration, board.Dates.Count, board.Peak);

            Preview.Renderer = new PositionRenderer(
                board, plan, ChosenMotion(), ChosenWindow(), CrossSafeRight())
            {
                Title = title,
                ShowTitle = showTitle,

                // The coins are quoted in dollars on both sources, whatever language the
                // interface is in — see `CryptoQuotes`.
                CurrencyKey = "DcaCurrencyUsd",
            };
        }
        else
        {
            _stage.Title = title;
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        WindowBox.IsEnabled = ChosenMotion() is PositionMotion.Scroll;

        VideoSettings.TitlePlaceholder = DefaultTitle();

        var ready = _board is not null;

        PlayButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        CoverButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    private string ResolvedTitle() =>
        VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : DefaultTitle();

    private string DefaultTitle()
    {
        if (_board is { } board)
        {
            return board.Comparing
                ? Compared([.. board.Tracks.Select(t => t.Name)])
                : Strings.Format("CryptoPositionDefaultTitle", board.Tracks[0].Name);
        }

        var names = Chosen().Select(e => InstrumentNames.Display(e.Code, e.Name)).ToArray();

        return names.Length switch
        {
            0 => Strings.Format("CryptoPositionDefaultTitle", CryptoAsset.All[0].Display),
            1 => Strings.Format("CryptoPositionDefaultTitle", names[0]),
            _ => Compared(names),
        };
    }

    private static string Compared(string[] names) => names.Length == 2
        ? Strings.Format("PositionVsTitle", names[0], names[1])
        : Strings.Format("PositionCompareMany", names[0], names.Length);

    // ---- picking ---------------------------------------------------------------------

    private void OnCoinsChanged(object? sender, EventArgs e)
    {
        _board = null;
        SavePreferences();
        ApplyPreviewSettings();
    }

    // ---- fetching --------------------------------------------------------------------

    private async void Fetch()
    {
        var capital = ChosenCapital;

        if (capital <= 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("PositionCapitalInvalid"));
            return;
        }

        var (start, end) = ChosenRange();

        if (ChosenMonths() == CustomMonths && start >= end)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("TurnoverRangeReversed"));
            return;
        }

        var chosen = Chosen();

        if (chosen.Count == 0)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Get("CryptoPickOne"));
            return;
        }

        if (chosen.Count > PositionLoader.MostTracks)
        {
            ShowStatus(InfoBarSeverity.Error, Strings.Format(
                "PositionTooMany", PositionLoader.MostTracks, chosen.Count));
            return;
        }

        await RunAsync(FetchButton, async cancellation =>
        {
            var progress = new Progress<string>(message => ShowStatus(InfoBarSeverity.Informational, message));

            var board = await PositionLoader.LoadAsync(
                Services.CryptoCloses, chosen, capital, start, end, progress, cancellation);

            _board = board;

            ApplyPreviewSettings();

            ShowMoment(1);

            var fetched = board.Comparing
                ? Strings.Format(
                    "CryptoPositionBoardFetched",
                    board.Tracks.Count,
                    board.Dates.Count,
                    PositionRenderer.Iso(board.Start),
                    PositionRenderer.Iso(board.End))
                : Strings.Format(
                    "CryptoPositionFetched",
                    board.Dates.Count,
                    PositionRenderer.Iso(board.Start),
                    PositionRenderer.Iso(board.End));

            if (board.Skipped.Count == 0)
            {
                ShowStatus(InfoBarSeverity.Success, fetched);
            }
            else
            {
                ShowStatus(InfoBarSeverity.Warning, $"{fetched} {Strings.Format(
                    "PositionSkipped", board.Skipped.Count, string.Join(", ", board.Skipped))}");
            }

            // A span the source could not fill is not a shorter span somebody chose. The
            // fallback carries a year, so asking it for ten is answered with one — see
            // `CryptoQuotes.GeckoMostDays`.
            if (board.Start > start.AddDays(30))
            {
                ShowStatus(InfoBarSeverity.Warning, Strings.Format(
                    "CryptoRangeShort", PositionRenderer.Iso(board.Start)));
            }
        }, TimeSpan.FromMinutes(6));
    }

    private void OnFetch(object sender, RoutedEventArgs e) => Fetch();

    // ---- playback --------------------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
    }

    private void OnHoldingChanged(object sender, object e)
    {
        if (RangeCombo is null)
        {
            return;
        }

        CustomRange.Visibility = ChosenMonths() == CustomMonths
            ? Visibility.Visible
            : Visibility.Collapsed;

        if (!_ready)
        {
            return;
        }

        SavePreferences();
    }

    private void OnCustomRangeChanged(object sender, DatePickerValueChangedEventArgs e)
    {
        if (!_ready)
        {
            return;
        }

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

    // ---- export ----------------------------------------------------------------------

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || _board is not { } board || App.Window is not { } window)
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
                VideoExporter.VideoName(label, board.Start, board.End, format),
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

    // ---- preferences -----------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        var capital = _prefs.GetDouble("Capital", 10_000);
        CapitalBox.Text = capital > 0
            ? capital.ToString("0.##", CultureInfo.InvariantCulture)
            : "10000";

        var months = _prefs.GetInt("Months", 36);
        var index = Array.FindIndex(Ranges, r => r.Months == months);
        RangeCombo.SelectedIndex = index >= 0 ? index : 0;

        MotionCombo.SelectedIndex = _prefs.GetInt("Motion", (int)PositionMotion.Grow) == (int)PositionMotion.Scroll ? 1 : 0;
        WindowBox.Text = Math.Clamp(_prefs.GetInt("Window", DefaultWindow), MinWindow, MaxWindow)
            .ToString(CultureInfo.InvariantCulture);

        CrossCheck.IsChecked = _prefs.GetInt("CrossSafeRight", 0) != 0;

        var today = DateTimeOffset.Now;
        FromDate.Date = today.AddYears(-3);
        ToDate.Date = today;

        if (DateOnly.TryParse(_prefs.GetString("From", string.Empty), out var from))
        {
            FromDate.Date = new DateTimeOffset(from, TimeOnly.MinValue, TimeSpan.Zero);
        }

        if (DateOnly.TryParse(_prefs.GetString("To", string.Empty), out var to))
        {
            ToDate.Date = new DateTimeOffset(to, TimeOnly.MinValue, TimeSpan.Zero);
        }

        Coins.Select(_prefs.GetString("Coins", "BTC").Split(';', StringSplitOptions.RemoveEmptyEntries));

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        _prefs.Save("Capital", ChosenCapital > 0 ? ChosenCapital : 10_000);
        _prefs.Save("Months", ChosenMonths());
        _prefs.Save("Motion", (int)ChosenMotion());
        _prefs.Save("Window", ChosenWindow());
        _prefs.Save("CrossSafeRight", CrossSafeRight() ? 1 : 0);
        _prefs.Save("From", FromDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("To", ToDate.Date.ToString("yyyy-MM-dd"));
        _prefs.Save("Coins", string.Join(";", Chosen().Select(c => c.Code)));

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
