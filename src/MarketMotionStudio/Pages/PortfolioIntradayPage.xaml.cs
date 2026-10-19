using System.Collections.ObjectModel;
using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using MarketMotionStudio.Views;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Xaml.Media;
using Windows.UI;

namespace MarketMotionStudio.Pages;

/// <summary>One row of the book, already formatted: the list renders strings, not numbers.</summary>
public sealed class HoldingRow
{
    public HoldingRow(string name, string detail, string pnl, Color tone)
    {
        Name = name;
        Detail = detail;
        Pnl = pnl;
        Tone = new SolidColorBrush(tone);
    }

    /// <summary>The instrument, in the interface's language.</summary>
    public string Name { get; }

    /// <summary>Shares and cost, in the venue's currency.</summary>
    public string Detail { get; }

    /// <summary>Today's contribution, already signed — empty before the first fetch.</summary>
    public string Pnl { get; }

    /// <summary>Red for a gain, green for a loss, muted when there is nothing to say yet.</summary>
    public Brush Tone { get; }
}

/// <summary>
/// A portfolio's day, live: the running profit or loss from 09:30, refreshed while the market is
/// open, with the book edited by hand or by importing the broker's own filled orders.
///
/// <para>
/// **This page is the only one here whose subject is the reader.** Every other page draws a
/// market or an instrument, and the reader chooses one to look at; this one draws what they hold.
/// That is why it carries its own state — a book, a journal of confirmed trades — where the other
/// pages carry only parameters, and why the book is stored in a file rather than in preferences:
/// losing it means re-entering a position by hand from a phone screenshot.
/// </para>
///
/// <para>
/// **Live means two different things at two different moments.** During the session the page
/// re-reads the minute endpoints on a timer and the curve grows; after the close it shows the
/// finished day and the timer stops asking. The distinction is a clock, not a preference: polling
/// a settled day every thirty seconds costs the source a request per holding and answers with the
/// same numbers.
/// </para>
/// </summary>
public sealed partial class PortfolioIntradayPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("Portfolio.");

    /// <summary>The timer behind "refresh while the market is open".</summary>
    private readonly DispatcherTimer _auto = new() { Interval = TimeSpan.FromSeconds(30) };

    private PortfolioSession? _session;

    /// <summary>Guards against a timer tick landing on top of a fetch already in flight.</summary>
    private bool _busy;

    public PortfolioIntradayPage()
    {
        InitializeComponent();

        Portfolio.EnsureLoaded();

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
        RefreshBook();

        _auto.Tick += OnAutoTick;

        // The book is what this page is about, so it reads it on arrival rather than waiting for
        // a button. A page that opens empty and says "press fetch" would be showing the reader
        // their own holdings as a task.
        Loaded += async (_, _) =>
        {
            UpdateAutoTimer();

            if (_session is null)
            {
                await SilentRefreshAsync(report: false);
            }
        };

        Unloaded += (_, _) => _auto.Stop();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("PortfolioPnlPageTitle.Text");

    /// <summary>Pushes the panel's values into the preview and redraws once.</summary>
    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = VideoSettings.TitleText;
        var showTitle = VideoSettings.ShowTitle;

        if (_session is { } session && session.Samples.Count > 1)
        {
            // Scaled to the day's larger excursion on either side, so the axis holds the whole
            // session from the first frame: a chart that rescales as the curve grows makes the
            // shape of the morning unreadable while it is being drawn.
            var plan = AnimationPlan.For(
                VideoSettings.Duration,
                session.Samples.Count,
                Math.Max(Math.Abs(session.Peak), Math.Abs(session.Trough)));

            Preview.Renderer = new PortfolioPnlRenderer(session, plan) { Title = title, ShowTitle = showTitle };
        }
        else
        {
            _stage.Title = title.Length > 0 ? title : Strings.Get("PortfolioPnlTitle");
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
        }

        VideoSettings.TitlePlaceholder = Strings.Get("PortfolioPnlTitle");

        var ready = _session is { Samples.Count: > 1 };

        CoverButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        PlayButton.IsEnabled = ready;

        RefreshScrubText();
        Preview.Redraw();
    }

    /// <summary>Rebuilds the book's list from the stored holdings and today's numbers.</summary>
    private void RefreshBook()
    {
        var rows = new List<HoldingRow>();

        foreach (var holding in Portfolio.Holdings)
        {
            var priced = _session?.Holdings.FirstOrDefault(h =>
                string.Equals(h.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            var cost = holding.IsHongKong
                ? "HK$" + holding.Cost.ToString("0.###", CultureInfo.InvariantCulture)
                : "¥" + holding.Cost.ToString("0.###", CultureInfo.InvariantCulture);

            var detail = Strings.Format(
                "PortfolioPnlRowDetail",
                holding.Shares.ToString("#,##0", CultureInfo.InvariantCulture),
                cost);

            var (text, tone) = priced switch
            {
                { HasSession: false } => (Strings.Get("PortfolioPnlRowClosed"), Palette.Muted),
                { } p => (PortfolioPnlRenderer.Money(p.DayPnl), p.DayPnl >= 0 ? Palette.Emphasis : Palette.Fall),
                _ => (string.Empty, Palette.Muted),
            };

            rows.Add(new HoldingRow(InstrumentNames.Display(holding.Code, holding.Name), detail, text, tone));
        }

        Holdings.ItemsSource = rows;
        EmptyNote.Visibility = rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
    }

    private async void OnFetch(object sender, RoutedEventArgs e) => await FetchAsync(report: true);

    private async Task FetchAsync(bool report)
    {
        if (_busy)
        {
            return;
        }

        _busy = true;

        try
        {
            await RunAsync(FetchButton, async cancellation =>
            {
                var progress = new Progress<string>(message =>
                    ShowStatus(InfoBarSeverity.Informational, message));

                var session = await IntradayPnl.LoadAsync(
                    Services.Http, Services.Stocks, [.. Portfolio.Holdings],
                    [.. Portfolio.TradesOn(Today())], progress, cancellation);

                Adopt(session);

                ShowStatus(
                    InfoBarSeverity.Success,
                    Strings.Format(
                        "PortfolioPnlFetched",
                        session.Day,
                        session.Samples.Count,
                        PortfolioPnlRenderer.Money(session.Last)));
            }, TimeSpan.FromMinutes(2));
        }
        finally
        {
            _busy = false;
        }
    }

    /// <summary>
    /// The timer's own fetch: no buttons disabled, no progress line, and a failure that says
    /// nothing when there was nothing to say.
    ///
    /// Separate from <see cref="FetchAsync"/> rather than a flag on it because the two want
    /// different failures. A fetch the reader asked for that fails must say so; a background
    /// re-read that fails (the phone lost its connection for a moment) must not put an error
    /// across a frame that is still correct.
    /// </summary>
    private async Task SilentRefreshAsync(bool report)
    {
        if (_busy || Portfolio.Holdings.Count == 0)
        {
            return;
        }

        _busy = true;

        try
        {
            using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(90));

            var session = await IntradayPnl.LoadAsync(
                Services.Http, Services.Stocks, [.. Portfolio.Holdings],
                [.. Portfolio.TradesOn(Today())], null, cancellation.Token);

            Adopt(session);
        }
        catch (OperationCanceledException)
        {
            // The window closed, or the source took longer than a refresh interval. The next
            // tick will ask again.
        }
        catch (Exception ex)
        {
            if (report)
            {
                ShowFailure("PortfolioPnlFetchFailed", ex);
            }
        }
        finally
        {
            _busy = false;
        }
    }

    /// <summary>Puts a fetched session on the page, keeping the reader's position in the clip.</summary>
    private void Adopt(PortfolioSession session)
    {
        var wasAtEnd = Preview.Progress >= 0.999 || _session is null;

        _session = session;

        ApplyPreviewSettings();
        RefreshBook();

        // Parked on the live edge: this page's last frame is "now", which is the frame a reader
        // wants after a refresh. A re-read that jumped the preview back to 09:30 would undo the
        // one thing they were watching.
        if (wasAtEnd)
        {
            ShowMoment(1);
        }

        // The two lines belong together and are written together: this is the number the frame is
        // drawing, said in words, and the minute it was true. Set from here rather than from the
        // fetch button, because every other path to a new session — an import, a background tick
        // — comes through `Adopt` too, and a line that only the button updates lies for the rest
        // of the day.
        SummaryText.Text = Strings.Format(
            "PortfolioPnlFetched",
            session.Day,
            session.Samples.Count,
            PortfolioPnlRenderer.Money(session.Last));

        UpdatedText.Text = Strings.Format(
            "PortfolioPnlUpdated",
            session.FetchedAt.ToString("HH:mm:ss", CultureInfo.InvariantCulture));
    }

    private void OnAutoRefreshToggled(object sender, RoutedEventArgs e)
    {
        UpdateAutoTimer();
        SavePreferences();
    }

    /// <summary>
    /// Runs the timer only while the market is open and the switch is on.
    ///
    /// The clock is the weekday and the session's own hours, coarse on purpose: this is a
    /// polling interval, not a trading calendar, and a holiday simply means the numbers do not
    /// change between two ticks.
    /// </summary>
    private void UpdateAutoTimer()
    {
        var now = DateTime.Now;
        var minute = (now.Hour * 60) + now.Minute;

        var open = AutoRefresh.IsOn &&
                   now.DayOfWeek is not (DayOfWeek.Saturday or DayOfWeek.Sunday) &&
                   minute >= (9 * 60) + 15 &&
                   minute <= (16 * 60) + 10;

        if (open)
        {
            _auto.Start();
        }
        else
        {
            _auto.Stop();
        }
    }

    private async void OnAutoTick(object? sender, object e) => await SilentRefreshAsync(report: false);

    private async void OnManage(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var dialog = new PortfolioDialog { XamlRoot = XamlRoot };

        await Dialogs.ShowAsync(dialog);

        // Whatever was on the stage was drawn from the book that just changed. Dropped rather
        // than left standing, for the reason every other page drops its series when its
        // parameters move: a frame of nine holdings under a list of eight is a plausible
        // picture of the wrong thing.
        RefreshBook();

        if (Portfolio.Holdings.Count == 0)
        {
            _session = null;

            // An empty book draws nothing, so nothing can be said about it. Left standing, the
            // line would report a profit nobody holds.
            SummaryText.Text = string.Empty;
            UpdatedText.Text = string.Empty;

            ApplyPreviewSettings();
            return;
        }

        await SilentRefreshAsync(report: true);
    }

    private async void OnImport(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var dialog = new TradeImportDialog(DateOnly.FromDateTime(DateTime.Today)) { XamlRoot = XamlRoot };

        if (await Dialogs.ShowAsync(dialog) != ContentDialogResult.Primary ||
            dialog.Trades.Count == 0)
        {
            return;
        }

        var result = Portfolio.Apply(dialog.Trades);

        RefreshBook();

        ShowStatus(
            result.Unmatched > 0 ? InfoBarSeverity.Warning : InfoBarSeverity.Success,
            Strings.Format("PortfolioPnlImported", result.Applied, result.Duplicates, result.Unmatched));

        await SilentRefreshAsync(report: true);
    }

    private static string Today() => DateTime.Today.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    /// <summary>The one day this page draws, for the file names.</summary>
    private (DateOnly From, DateOnly To)? Range() =>
        _session is { } session && DateOnly.TryParse(session.Day, out var day) ? (day, day) : null;

    private async void OnExport(object sender, RoutedEventArgs e)
    {
        if (Preview.Renderer is not { } renderer || Range() is not { } range || App.Window is not { } window)
        {
            return;
        }

        if (!await SubscriptionOffer.PermitAsync(XamlRoot, window))
        {
            return;
        }

        var format = VideoSettings.Format;
        var margins = VideoSettings.Margins;
        var duration = VideoSettings.Duration;

        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : Strings.Get("PortfolioPnlTitle");

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
                VideoExporter.VideoName(label, range.From, range.To, format),
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
        if (Preview.Renderer is not { } renderer || Range() is not { } range || App.Window is not { } window)
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

            var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : Strings.Get("PortfolioPnlTitle");
            var format = VideoSettings.Format;

            var file = await FrameExporter.SavePngAsync(
                renderer, format, VideoSettings.Margins, Preview.Progress, folder,
                FrameExporter.CoverName(label, range.From, range.To, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    /// <summary>Moves the preview and the scrub bar together.</summary>
    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        RefreshScrubText();
        Preview.Redraw();
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

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        AutoRefresh.IsOn = _prefs.GetBool("Auto", true);

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Auto", AutoRefresh.IsOn);

        VideoSettings.Save(_prefs);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
