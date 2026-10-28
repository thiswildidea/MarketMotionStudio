using System.Globalization;
using MarketMotionStudio.Localization;
using MarketMotionStudio.Market;
using MarketMotionStudio.Render;
using MarketMotionStudio.Views;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Windows.UI;

namespace MarketMotionStudio.Pages;

/// <summary>
/// One frame, two halves: the reader's book above, the two markets below.
///
/// <para>
/// **The page exists because the two things are read together.** A day's profit means nothing
/// without the market it was made in: 上证 down one per cent and the book down a fifth of that is
/// a different sentence from the same book down twice as much. The two pictures already existed on
/// two pages, one after the other in the menu, and reading them together meant holding one in the
/// head while looking at the other. Here they share a clock, so a reader can see the book turn at
/// the minute the index turned.
/// </para>
///
/// <para>
/// **Which market this page is for is decided by the menu, not by the fetch.** It is offered only
/// while the app's market is A 股 — see <c>MainWindow.ApplyMarket</c> — because the lower half is
/// explicitly a mainland-plus-Hong-Kong board, and offering it under 美股 or 加密 would be offering
/// a page whose subject the chosen market does not contain. The book, once drawn, is whatever the
/// reader holds: the two are separate questions and the page keeps them separate.
/// </para>
///
/// <para>
/// **The book is read, never edited, here.** It has an editor on the intraday page, on a dialog
/// with room for four editable fields per row. A second editor for one file would be a second way
/// to get the same numbers wrong, so this page draws the book and points at the page that owns it.
/// </para>
/// </summary>
public sealed partial class BoardPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("Board.");

    /// <summary>The timer behind "refresh while the market is open", the same beat as the
    /// intraday page's.</summary>
    private readonly DispatcherTimer _auto = new() { Interval = TimeSpan.FromSeconds(30) };

    private PortfolioSession? _session;

    /// <summary>Every selected index's day, in the order the page draws them.</summary>
    private readonly List<IndexIntradaySeries> _indexes = [];

    /// <summary>The renderer on the preview, so the read-out can ask where "now" is.</summary>
    private BoardSplitRenderer? _board;

    /// <summary>Guards against a timer tick landing on top of a fetch already in flight.</summary>
    private bool _busy;

    /// <summary>
    /// Which minute the list was last built for. Playback calls back sixty times a second and a
    /// session has two hundred and forty odd minutes: rebuilding the item list on every callback
    /// would rebuild it four times a second for numbers that have not moved.
    /// </summary>
    private int _listed = int.MinValue;

    /// <summary>
    /// The indexes the page offers, both venues, from the catalog the index race page reads.
    ///
    /// Two lists and not one: 11:30 and 13:00 are Shanghai's and Shenzhen's, noon and one are Hong
    /// Kong's, and a single list would leave the reader to guess which line stops at three.
    /// </summary>
    private static readonly (string Key, RaceEntry[] Entries)[] Groups =
    [
        ("BoardSectionMainland", WorldIndexLists.AShare),
        ("BoardSectionKong", WorldIndexLists.HongKong),
    ];

    /// <summary>
    /// What the page opens with: one index from each venue.
    ///
    /// Not "everything", which would draw six lines into two hundred pixels of height and make the
    /// page's own point — that the two markets keep different hours — the hardest thing on it to
    /// read. Not one, either: a single index leaves the 15:00 rule unexplained.
    /// </summary>
    private static readonly string[] DefaultPicks = ["sh000001", "hkHSI"];

    private readonly List<CheckBox> _boxes = [];

    public BoardPage()
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

        BuildIndexBoxes();

        RestorePreferences();
        ApplyPreviewSettings();
        RefreshBook();

        _auto.Tick += OnAutoTick;

        Loaded += async (_, _) =>
        {
            UpdateAutoTimer();

            if (_session is null && Portfolio.Holdings.Count > 0)
            {
                await RefreshAsync(report: false);
            }
        };

        Unloaded += (_, _) => _auto.Stop();
    }

    protected override InfoBar StatusControl => Status;

    protected override string JobName => Strings.Get("BoardPageTitle.Text");

    // ---- parameters --------------------------------------------------------------------

    /// <summary>
    /// The two groups of checkboxes, built from the catalog rather than written in the markup: a
    /// board added to the index race page is a board offered here, and there is no second list to
    /// forget to update.
    /// </summary>
    private void BuildIndexBoxes()
    {
        foreach (var (_, entries) in Groups)
        {
            var panel = ReferenceEquals(entries, WorldIndexLists.AShare) ? MainlandBoxes : KongBoxes;

            foreach (var entry in entries)
            {
                var box = new CheckBox
                {
                    Content = entry.Name,
                    Tag = entry,
                    MinWidth = 0,
                };

                box.Checked += OnIndexToggled;
                box.Unchecked += OnIndexToggled;

                panel.Children.Add(box);
                _boxes.Add(box);
            }
        }
    }

    /// <summary>The codes currently ticked.</summary>
    private List<RaceEntry> Picked() =>
        [.. _boxes.Where(b => b.IsChecked is true).Select(b => (RaceEntry)b.Tag)];

    private async void OnIndexToggled(object sender, RoutedEventArgs e)
    {
        if (_prefs.Restoring)
        {
            return;
        }

        SavePreferences();

        // Redrawn at once, because the axis rule is the point: ticking 恒生指数 takes the clock
        // out to 16:00 and draws the 15:00 rule, and that has to happen on the frame the reader
        // is looking at rather than after the next fetch.
        ApplyPreviewSettings();

        // A newly ticked index has no series yet. Read just the missing ones — a whole re-fetch
        // would re-read a book that has not changed, at a request per holding.
        await FillMissingAsync();
    }

    /// <summary>
    /// Reads the indexes that are ticked but not yet on hand, and leaves the rest alone.
    ///
    /// Separate from the fetch because the two are asked for at different times: the book is read
    /// when the page opens and on the timer, an index when the reader ticks it.
    /// </summary>
    private async Task FillMissingAsync()
    {
        var picked = Picked();
        var missing = picked.Where(p => _indexes.All(s => !Same(s.Code, p.Code))).ToList();
        var dropped = _indexes.Where(s => picked.All(p => !Same(s.Code, p.Code))).ToList();

        foreach (var gone in dropped)
        {
            _indexes.Remove(gone);
        }

        if (missing.Count == 0 || _busy)
        {
            return;
        }

        _busy = true;

        try
        {
            using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(30));

            var loaded = await IndexIntraday.LoadAsync(Services.Http, missing, cancellation.Token);

            // In the catalog's order, so the legend does not reorder itself as the reader ticks.
            foreach (var series in loaded)
            {
                if (_indexes.All(s => !Same(s.Code, series.Code)))
                {
                    _indexes.Add(series);
                }
            }

            ApplyPreviewSettings();
        }
        catch (Exception)
        {
            // A missing index is drawn as a missing line; the next fetch asks again. Putting an
            // error bar across a frame that is still correct is worse than the gap.
        }
        finally
        {
            _busy = false;
        }
    }

    private static bool Same(string a, string b) => string.Equals(a, b, StringComparison.OrdinalIgnoreCase);

    // ---- picture -----------------------------------------------------------------------

    private void ApplyPreviewSettings()
    {
        Preview.Format = VideoSettings.Format;
        Preview.Margins = VideoSettings.Margins;
        Preview.ShowGuides = VideoSettings.ShowGuides;

        var title = VideoSettings.TitleText;
        var showTitle = VideoSettings.ShowTitle;

        if (_session is { Samples.Count: > 1 } session)
        {
            // The clock runs over the book's own minutes, because that is what both halves are
            // measured in; the indexes' lines are clipped to the same window.
            var plan = AnimationPlan.For(
                VideoSettings.Duration,
                session.Samples.Count,
                Math.Max(Math.Abs(session.Peak), Math.Abs(session.Trough)));

            var renderer = new BoardSplitRenderer(session, _indexes, plan)
            {
                Title = title,
                ShowTitle = showTitle,
            };

            Preview.Renderer = renderer;
            _board = renderer;
        }
        else
        {
            _stage.Title = title.Length > 0 ? title : Strings.Get("BoardTitle");
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
            _board = null;
        }

        VideoSettings.TitlePlaceholder = Strings.Get("BoardTitle");

        var ready = _session is { Samples.Count: > 1 };

        CoverButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        PlayButton.IsEnabled = ready;

        ShowMoment(Preview.Progress);
    }

    /// <summary>
    /// Rebuilds the book's list from the session at the minute the preview is drawing, the way the
    /// intraday page does: the shares shown have to be the shares the curve above them was drawn on.
    /// </summary>
    private void RefreshBook(int index = -1)
    {
        var rows = new List<HoldingRow>();

        var moment = _session is { Moments.Count: > 0 } live
            ? live.Moments[index < 0 ? live.Moments.Count - 1 : Math.Min(index, live.Moments.Count - 1)]
            : null;

        foreach (var holding in Portfolio.Holdings)
        {
            var priced = _session?.Holdings.FirstOrDefault(h =>
                string.Equals(h.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            var shares = moment is not null && moment.Shares.TryGetValue(holding.Code, out var held)
                ? held
                : holding.Shares;

            var cost = moment is not null && moment.Costs.TryGetValue(holding.Code, out var paid)
                ? paid
                : holding.Cost;

            var money = (holding.IsHongKong ? "HK$" : "¥")
                + cost.ToString("0.###", CultureInfo.InvariantCulture);

            var detail = shares > 0
                ? Strings.Format(
                    "PortfolioPnlRowDetail",
                    shares.ToString("#,##0", CultureInfo.InvariantCulture),
                    money)
                : Strings.Get("PortfolioPnlRowCleared");

            double? made = moment is not null && moment.Contributions.TryGetValue(holding.Code, out var sofar)
                ? sofar
                : priced?.DayPnl;

            var (text, tone) = priced switch
            {
                { HasSession: false } => (Strings.Get("PortfolioPnlRowClosed"), Palette.Muted),
                _ when made is { } value =>
                    (PortfolioPnlRenderer.Money(value), value >= 0 ? Palette.Emphasis : Palette.Fall),
                _ => (string.Empty, Palette.Muted),
            };

            rows.Add(new HoldingRow(InstrumentNames.Display(holding.Code, holding.Name), detail, text, tone));
        }

        Holdings.ItemsSource = rows;
        EmptyNote.Visibility = rows.Count == 0 ? Visibility.Visible : Visibility.Collapsed;
    }

    // ---- fetching ----------------------------------------------------------------------

    private async void OnFetch(object sender, RoutedEventArgs e) => await FetchAsync(report: true);

    private async Task FetchAsync(bool report)
    {
        if (_busy)
        {
            return;
        }

        var picked = Picked();

        if (picked.Count == 0)
        {
            ShowStatus(InfoBarSeverity.Warning, Strings.Get("BoardNeedIndex"));

            return;
        }

        _busy = true;

        try
        {
            await RunAsync(FetchButton, async cancellation =>
            {
                var progress = new Progress<string>(message =>
                    ShowStatus(InfoBarSeverity.Informational, message));

                // Both halves in one pass, in parallel: two round trips that do not depend on
                // each other, and a frame that showed the book before the indexes arrived would
                // be a frame with half its subject missing.
                async Task<PortfolioSession?> ReadBookAsync()
                {
                    if (Portfolio.Holdings.Count == 0)
                    {
                        return null;
                    }

                    return await IntradayPnl.LoadAsync(
                        Services.Http, Services.Stocks, [.. Portfolio.Holdings],
                        [.. Portfolio.Trades], progress, cancellation,
                        FeeSchedule.Mainland, Portfolio.Settled);
                }

                var bookTask = ReadBookAsync();
                var indexTask = IndexIntraday.LoadAsync(Services.Http, picked, cancellation);

                var session = await bookTask;
                var indexes = await indexTask;

                Adopt(session, indexes, picked.Count);
            }, TimeSpan.FromMinutes(3));
        }
        finally
        {
            _busy = false;
        }
    }

    /// <summary>
    /// Puts a fetched day on the page, keeping the reader's position in the clip.
    /// </summary>
    private void Adopt(PortfolioSession? session, List<IndexIntradaySeries> indexes, int asked)
    {
        var wasAtEnd = Preview.Progress >= 0.999 || _session is null;

        if (session is { Samples.Count: > 1 })
        {
            _session = session;
        }

        _indexes.Clear();
        _indexes.AddRange(indexes);

        _listed = int.MinValue;

        ApplyPreviewSettings();
        RefreshBook();

        ShowMoment(wasAtEnd ? 1 : Preview.Progress);

        if (_session is { } day)
        {
            SummaryText.Text = Strings.Format(
                "BoardFetched",
                indexes.Count.ToString(CultureInfo.InvariantCulture),
                asked.ToString(CultureInfo.InvariantCulture),
                day.Samples.Count.ToString(CultureInfo.InvariantCulture),
                PortfolioPnlRenderer.Money(day.Last));

            UpdatedText.Text = Strings.Format(
                "PortfolioPnlUpdated",
                day.FetchedAt.ToString("HH:mm:ss", CultureInfo.InvariantCulture));

            HideStatus();
        }
    }

    /// <summary>
    /// The timer's own read: no buttons touched, no progress line, and a failure that says nothing
    /// when there was nothing worth saying — the same contract the intraday page keeps.
    /// </summary>
    private async Task RefreshAsync(bool report)
    {
        if (_busy)
        {
            return;
        }

        _busy = true;

        try
        {
            using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(90));

            var picked = Picked();

            var session = await IntradayPnl.LoadAsync(
                Services.Http, Services.Stocks, [.. Portfolio.Holdings],
                [.. Portfolio.Trades], null, cancellation.Token,
                FeeSchedule.Mainland, Portfolio.Settled);

            var indexes = await IndexIntraday.LoadAsync(Services.Http, picked, cancellation.Token);

            Adopt(session, indexes, picked.Count);
        }
        catch (OperationCanceledException)
        {
            // The next tick asks again.
        }
        catch (Exception)
        {
            if (report)
            {
                ShowStatus(InfoBarSeverity.Error, Strings.Get("BoardFetchFailed"));
            }
        }
        finally
        {
            _busy = false;
        }
    }

    private void OnAutoRefreshToggled(object sender, RoutedEventArgs e)
    {
        UpdateAutoTimer();
        SavePreferences();
    }

    private void OnAutoTick(object? sender, object e)
    {
        if (AutoRefresh.IsOn)
        {
            _ = RefreshAsync(report: false);
        }
    }

    /// <summary>
    /// Asks the source again while a session could still be moving.
    ///
    /// A settled day costs a request per holding every thirty seconds and answers with the same
    /// numbers, so the timer is a clock rather than a preference: off before the open, on while
    /// either venue is trading, off once both have rung.
    /// </summary>
    private void UpdateAutoTimer()
    {
        if (AutoRefresh.IsOn)
        {
            _auto.Start();
        }
        else
        {
            _auto.Stop();
        }
    }

    // ---- playback and export -----------------------------------------------------------

    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        var index = _board?.ShownIndex(progress) ?? -1;

        if (index != _listed)
        {
            _listed = index;
            RefreshBook(index);
        }

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

        var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : Strings.Get("BoardTitle");

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

            var label = VideoSettings.TitleText.Length > 0 ? VideoSettings.TitleText : Strings.Get("BoardTitle");
            var format = VideoSettings.Format;

            var file = await FrameExporter.SavePngAsync(
                renderer, format, VideoSettings.Margins, Preview.Progress, folder,
                FrameExporter.CoverName(label, range.From, range.To, format),
                cancellation);

            ShowStatus(InfoBarSeverity.Success, Strings.Format(
                "StudioCoverSaved", file.Name, format.Width, format.Height, folder.Path));
        }, TimeSpan.FromSeconds(90));
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();

    // ---- preferences -------------------------------------------------------------------

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        AutoRefresh.IsOn = _prefs.GetBool("Auto", true);

        var saved = _prefs.GetString("Indexes", string.Empty);
        var picks = saved.Length > 0
            ? [.. saved.Split(',', StringSplitOptions.RemoveEmptyEntries)]
            : DefaultPicks;

        foreach (var box in _boxes)
        {
            var entry = (RaceEntry)box.Tag;

            box.IsChecked = picks.Any(code => Same(code, entry.Code));
        }

        // A page with nothing ticked would draw a book over an empty lower half and explain
        // nothing; the default comes back instead.
        if (Picked().Count == 0)
        {
            foreach (var box in _boxes)
            {
                box.IsChecked = DefaultPicks.Any(code => Same(code, ((RaceEntry)box.Tag).Code));
            }
        }

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
        _prefs.Save("Indexes", string.Join(',', Picked().Select(p => p.Code)));

        VideoSettings.Save(_prefs);
    }
}
