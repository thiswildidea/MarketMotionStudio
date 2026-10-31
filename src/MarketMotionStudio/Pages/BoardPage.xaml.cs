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
/// **The book is edited here through the same two doors as on the intraday page.** 管理持仓 and
/// 导入成交 are the same dialogs over the same portfolio.json — one editor for one file, offered
/// from both pages that draw it — and an edit on either page is the other page's next fetch.
/// The page draws the book and hands the reader the levers, rather than pointing at another page.
/// </para>
/// </summary>
public sealed partial class BoardPage : StudioPage, IPlaybackHost
{
    private readonly StageRenderer _stage = new();
    private readonly Playback _playback;

    /// <summary>Remembers this page's parameters. Prefixed, because the video panel is shared.</summary>
    private readonly StudioPreferences _prefs = new("Board.");

    /// <summary>
    /// The switches and rates this page shares with the intraday page, under that page's own
    /// prefix: one setting, two pages, and a change on either is what the other reads. The four
    /// look switches and the fee schedule are facts about the *book*, not about the page showing
    /// it, which is why they do not live under "Board.".
    /// </summary>
    private readonly StudioPreferences _shared = new("Portfolio.");

    /// <summary>The timer behind "refresh while the market is open", the same beat as the
    /// intraday page's.</summary>
    private readonly DispatcherTimer _auto = new() { Interval = TimeSpan.FromSeconds(30) };

    private PortfolioSession? _session;

    /// <summary>
    /// The session whose closing figures have already been written into the 港股通 baseline —
    /// reference compared, so a fresh auto-refresh earns its own sync and the frames after the
    /// last rewrite nothing. See the intraday page's note on the same field; the two pages draw
    /// one book and either may be the one playing when the day ends.
    /// </summary>
    private PortfolioSession? _synced;

    /// <summary>
    /// True while <see cref="Adopt"/> parks the playhead, so a background refresh that lands on
    /// the last frame is not read as the end of an animation — the reader-driven ends (a playback
    /// run to completion, a scrub to the close) are the ones the baseline follows, and a park must
    /// not clobber an initial position imported moments earlier. See the intraday page's note.
    /// </summary>
    private bool _adopting;

    /// <summary>
    /// The span actually drawn, which is not always the span that was asked for.
    ///
    /// Named after its job rather than after the picker because the two differ: the picker's answer
    /// is what was requested, and this is what the engine could answer for, starting no earlier
    /// than the snapshot. The frame's label, the index half's axis and the exported file's name
    /// all read this one, so all three say the same thing about the same span.
    /// </summary>
    private (DateOnly From, DateOnly To)? _span;

    /// <summary>The span's own history, kept for the index half to be read against.</summary>
    private ReturnHistory? _history;

    /// <summary>What was asked for, before the snapshot pulled the start forward.</summary>
    private DateOnly? _asked;

    /// <summary>Every selected index's day, in the order the page draws them.</summary>
    private readonly List<IndexIntradaySeries> _indexes = [];

    /// <summary>The renderer on the preview, so the read-out can ask where "now" is.</summary>
    private BoardSplitRenderer? _board;

    /// <summary>
    /// Which book the page is reading: the mainland holdings alone, or those plus the Hong Kong
    /// positions held through 港股通. Shared with the intraday page under `Portfolio.`, because it
    /// is a fact about the book and not about the page showing it — a reader who switched on one
    /// has switched it for both.
    /// </summary>
    private PortfolioScope _scope = PortfolioScope.AShare;

    /// <summary>Guards against a timer tick landing on top of a fetch already in flight.</summary>
    private bool _busy;

    /// <summary>
    /// Waits for the typing in a fee box to stop. `ValueChanged` fires on every keystroke, and
    /// each load is a request per holding — so the rate is applied when the reader stops.
    /// </summary>
    private readonly DispatcherTimer _feeTimer = new() { Interval = TimeSpan.FromSeconds(0.8) };

    /// <summary>
    /// Set when the book itself has just been edited by hand, cleared by the next fetch. The list
    /// prefers the session's per-minute moments over the stored book, and those moments were built
    /// from the book as it was **before** the edit — with the flag on, the list reads the stored
    /// book until the re-fetch rebuilds the session around it.
    /// </summary>
    private bool _bookDirty;

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

        _feeTimer.Tick += OnFeeSettled;

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

        // Bound after the restore: the value arriving from preferences is not the reader asking
        // for anything, and a fetch raised there would be one nobody requested.
        SpanPicker.Bind(_shared);
        SpanPicker.Changed += OnRangeChanged;

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

    /// <summary>
    /// The ticked codes the **current book** can be read against: under A 股 the Hong Kong boxes
    /// are out of the reads (and off the rail, see <see cref="ApplyScope"/>), even while their
    /// ticks survive in the preferences for the switch back. Every fetch path asks this one, so
    /// a hidden box cannot keep costing requests for lines the frame will not draw.
    /// </summary>
    private List<RaceEntry> Wanted() =>
        _scope is PortfolioScope.WithKong
            ? Picked()
            : [.. Picked().Where(p => !IndexIntraday.IsHongKong(p.Code))];

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
        var picked = Wanted();
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

            var renderer = new BoardSplitRenderer(session, _indexes, plan,
                crossSafeRight: CrossCheck.IsChecked is true,
                mascot: MascotCheck.IsChecked is true,
                dynamicAxis: DynamicAxisCheck.IsChecked is true,
                lunchBreak: LunchCheck.IsChecked is true,
                indexOnTop: IndexTopCheck.IsChecked is true,
                maskNames: MaskCheck.IsChecked is true)
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

        // A book just edited by hand has a stale session behind it — the moments on hand were
        // built before the edit, and showing them would put the old numbers straight back up.
        var moment = !_bookDirty && _session is { Moments.Count: > 0 } live
            ? live.Moments[index < 0 ? live.Moments.Count - 1 : Math.Min(index, live.Moments.Count - 1)]
            : null;

        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var holding in BookRows())
        {
            seen.Add(holding.Code);

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

        // **当天买出来的仓位也要有行。** The book only carries positions held at the open; a
        // fill that opens one mid-session exists in the moments alone. From its first fill's
        // minute onward the position gets a row of its own, appended at the bottom; a code the
        // day's journal only ever sold was never held, and gets no row.
        if (moment is not null && _session is { } day)
        {
            foreach (var trade in day.Trades)
            {
                if (!seen.Add(trade.Code) || moment.Minute < trade.Minute)
                {
                    continue;
                }

                moment.Shares.TryGetValue(trade.Code, out var shares);
                moment.Costs.TryGetValue(trade.Code, out var cost);

                if (shares <= 0)
                {
                    continue;
                }

                var money = (trade.Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase) ? "HK$" : "¥")
                    + cost.ToString("0.###", CultureInfo.InvariantCulture);

                var detail = Strings.Format(
                    "PortfolioPnlRowDetail",
                    shares.ToString("#,##0", CultureInfo.InvariantCulture),
                    money);

                var made = moment.Contributions.TryGetValue(trade.Code, out var sofar) ? sofar : 0d;

                rows.Add(new HoldingRow(
                    InstrumentNames.Display(trade.Code, trade.Name),
                    detail,
                    PortfolioPnlRenderer.Money(made),
                    made >= 0 ? Palette.Emphasis : Palette.Fall));
            }
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

        var picked = Wanted();

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

                // Both halves in one pass. Today they race each other, because neither knows
                // anything the other would tell it.
                //
                // **The index read takes the span's own numbering when there is one.** The lower
                // half exists to be read against the upper, and two series plotted on two
                // numberings — the index on its own clock while the book is counted in slots —
                // would let the reader line any day of one against any minute of the other. So a
                // span's indexes are read *for the slots the book already has*, which is also the
                // only way either half knows which days the other actually traded.
                // Whether the book is being asked about one day. Decided here rather than inside
                // `ReadBookAsync` because the index half has to agree with it: which days a range
                // contains comes from the book's own read, and the two halves are drawn on one
                // axis. 港股通 is always one day — see the note on `_scope`.
                var wholeDay = _scope is PortfolioScope.WithKong || SpanPicker.Span == RangeSpan.Today;

                async Task<PortfolioSession?> ReadBookAsync()
                {
                    if (Portfolio.Holdings.Count == 0)
                    {
                        return null;
                    }

                    // **港股通 is answered about today whatever the picker says** — see the note
                    // on `_scope`. The picker is hidden under it, so today is not a guess at the
                    // reader's meaning; it is the only day this book can be drawn for.
                    if (wholeDay)
                    {
                        return await IntradayPnl.LoadAsync(
                            Services.Http, Services.Stocks, BookRows(),
                            BookTrades(), progress, cancellation,
                            Fees(), Portfolio.Settled);
                    }

                    if (SpanPicker.Range is not { } wanted)
                    {
                        throw new InvalidOperationException(Strings.Get("PortfolioSpanIncomplete"));
                    }

                    var history = await HoldingReturns.LoadAsync(
                        Services.Http, Services.Quotes, wanted.From, wanted.To, progress, cancellation,
                        Fees(), PortfolioScope.AShare);

                    _history = history;
                    _span = (history.From, history.To);
                    _asked = wanted.From;

                    return SpanFrame.ToSession(history, SpanFrame.AxisFor(history));
                }

                async Task<List<IndexIntradaySeries>> ReadIndexSpanAsync() =>
                    _history is { } history
                        ? await IndexSpan.LoadAsync(
                            Services.Http, Services.Quotes, picked,
                            SpanFrame.AxisFor(history), history.Grain, cancellation)
                        : [];

                var bookTask = ReadBookAsync();

                // Today's two halves race each other, because neither knows anything the other
                // would tell it. **A span's cannot**: which days a range contains is decided by the
                // instruments the reader held through it, and only the book's own read knows that.
                // So that half is asked afterwards, with the answer in hand — two guesses in
                // parallel would be two different answers about where Tuesday is.
                var todayIndexes = wholeDay
                    ? IndexIntraday.LoadAsync(Services.Http, picked, cancellation)
                    : null;

                var session = await bookTask;
                var indexes = todayIndexes is { } racing
                    ? await racing
                    : await ReadIndexSpanAsync();

                Adopt(session, indexes, picked.Count);
            }, TimeSpan.FromMinutes(3));
        }
        catch (InvalidOperationException ex)
        {
            // Nothing to measure a span against — see the note on the intraday page's version.
            ShowFailure("PortfolioSpanNoBaseline", ex);
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
            _bookDirty = false;
        }

        _indexes.Clear();
        _indexes.AddRange(indexes);

        _listed = int.MinValue;

        // The flag covers ApplyPreviewSettings too — it re-shows the frame through its own
        // ShowMoment call, and a park at progress 1 must not read as an animation's end (see the
        // intraday page's note; 实测：导入的基准在一轮自动刷新后回到收盘股数，正是这条路写的).
        _adopting = true;

        try
        {
            ApplyPreviewSettings();
            RefreshBook();

            ShowMoment(wasAtEnd ? 1 : Preview.Progress);
        }
        finally
        {
            _adopting = false;
        }

        if (_session is { } day)
        {
            // A span is counted in days and a session in minutes; saying "分钟" over ten closes
            // would be ten numbers claiming to be twenty thousand.
            SummaryText.Text = Strings.Format(
                day.SlotIsDaily ? "BoardFetchedDays" : "BoardFetched",
                indexes.Count.ToString(CultureInfo.InvariantCulture),
                asked.ToString(CultureInfo.InvariantCulture),
                day.Samples.Count.ToString(CultureInfo.InvariantCulture),
                PortfolioPnlRenderer.Money(day.Last));

            // A range the snapshot had to shorten says so: a reader who asked for a year and got
            // ten days is owed the reason, or the page reads as broken rather than as bounded.
            if (_asked is { } wantedFrom && _span is { } drawn && drawn.From > wantedFrom)
            {
                // Two shortenings, two sentences — see the note on the intraday page's copy.
                var snapped = Ledger.BaselineDayOf(_scope) == drawn.From;

                SummaryText.Text += "  " + Strings.Format(
                    snapped ? "PortfolioSpanTrimmed" : "PortfolioSpanShallow",
                    drawn.From.ToString("M/d", CultureInfo.InvariantCulture));
            }

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

            var picked = Wanted();

            var session = await IntradayPnl.LoadAsync(
                Services.Http, Services.Stocks, BookRows(),
                BookTrades(), null, cancellation.Token,
                Fees(), Portfolio.Settled);

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
        // A span excludes itself from the timer: re-reading a month every thirty seconds costs the
        // source a request per holding and answers with the same closes all afternoon, and worse
        // than the cost, it would redraw a picture the reader had left alone.
        //
        // 港股通 is today whatever the (hidden) picker is left on, so it is on the timer too.
        if (AutoRefresh.IsOn &&
            (_scope is PortfolioScope.WithKong || SpanPicker.Span == RangeSpan.Today))
        {
            _auto.Start();
        }
        else
        {
            _auto.Stop();
        }
    }

    /// <summary>
    /// The span moved, and with it both halves of the frame: a different set of days is a different
    /// picture, not the same one redrawn.
    ///
    /// Everything downstream follows from that — the instruments the range prices, how many points
    /// the curve has, and which index lines can be read against it — so this asks again rather than
    /// trying to keep any part of the old frame.
    /// </summary>
    private async void OnRangeChanged(object? sender, EventArgs e)
    {
        UpdateAutoTimer();
        SavePreferences();

        await FetchAsync(report: false);
    }

    /// <summary>
    /// What the chosen book changes about the page: the span it can be asked about, and the two
    /// fee fields only one of the two books has an answer for.
    ///
    /// Same reasoning as the intraday page's, and the same caption on the picker, because the two
    /// pages draw one book and a reader who switched on one of them has switched it for both.
    /// </summary>
    private void ApplyScope()
    {
        var kong = _scope is PortfolioScope.WithKong;

        SpanPicker.Visibility = kong ? Visibility.Collapsed : Visibility.Visible;

        // The Hong Kong group goes with the book it belongs to: a mainland book is not read
        // against an index of a market it never touched, and offering the boxes would invite
        // exactly that. The ticks survive the hiding — restoring them is what switching back
        // means, and a preference silently erased is a preference lost.
        KongHeader.Visibility = kong ? Visibility.Visible : Visibility.Collapsed;
        KongBoxes.Visibility = kong ? Visibility.Visible : Visibility.Collapsed;

        FeeKongCommission.Visibility = kong ? Visibility.Visible : Visibility.Collapsed;
        FeeKongMinimum.Visibility = kong ? Visibility.Visible : Visibility.Collapsed;
    }

    /// <summary>The book changed: read the other one. Shared with the intraday page, so both move.</summary>
    private async void OnScopeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_prefs.Restoring || _shared.Restoring)
        {
            return;
        }

        _scope = ScopeCombo.SelectedIndex == 1 ? PortfolioScope.WithKong : PortfolioScope.AShare;

        ApplyScope();
        SavePreferences();

        UpdateAutoTimer();

        await FetchAsync(report: false);
    }

    /// <summary>
    /// The rows of the book the page is reading: every holding under 港股通, the mainland ones
    /// alone otherwise.
    /// </summary>
    private IReadOnlyList<Holding> BookRows() =>
        _scope is PortfolioScope.WithKong
            ? [.. Portfolio.Holdings]
            : [.. Portfolio.Holdings.Where(h => !h.IsHongKong)];

    /// <summary>The fills of the book the page is reading, in the same terms.</summary>
    private IReadOnlyList<PortfolioTrade> BookTrades() =>
        _scope is PortfolioScope.WithKong
            ? [.. Portfolio.Trades]
            : [.. Portfolio.Trades.Where(t => !t.IsHongKong)];

    // ---- the book's two doors ----------------------------------------------------------

    /// <summary>
    /// A look switch moved: rebuild the renderer and stop there. Nothing is re-read, because none
    /// of these changes a number — they change where the same numbers sit or how they are named.
    /// </summary>
    private void OnLookChanged(object sender, RoutedEventArgs e)
    {
        ApplyPreviewSettings();
        SavePreferences();
    }

    private async void OnManage(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var dialog = new PortfolioDialog(null, _scope) { XamlRoot = XamlRoot };

        await Dialogs.ShowAsync(dialog);

        _bookDirty = true;
        RefreshBook();

        if (Portfolio.Holdings.Count == 0)
        {
            _session = null;

            SummaryText.Text = string.Empty;
            UpdatedText.Text = string.Empty;

            ApplyPreviewSettings();
            return;
        }

        // Waits out any fetch already running — the in-flight one holds a snapshot taken before
        // the edit, so skipping would leave the session blind to the new book.
        await RefreshAfterChangeAsync(report: true);
    }

    private async void OnImport(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        var dialog = new TradeImportDialog(ImportDay()) { XamlRoot = XamlRoot };

        await Dialogs.ShowAsync(dialog);

        // The dialog applies its own imports — see the note on the intraday page's copy. All that
        // is left here is re-reading: the session on screen was built before the rows were filed.
        if (dialog.ArchiveChanged)
        {
            await RefreshAfterChangeAsync(report: true);
        }
    }

    /// <summary>
    /// The day an import is stamped with: **the day the page is drawing**, not the day the clock
    /// says it is — before the open that is yesterday, and a fill stamped with today lands on a
    /// day nothing has traded on.
    /// </summary>
    private DateOnly ImportDay() =>
        _session is { Day.Length: > 0 } session && DateOnly.TryParse(session.Day, out var day)
            ? day
            : DateOnly.FromDateTime(DateTime.Today);

    /// <summary>
    /// Refreshes after the book or the journal changed underneath the page. Waits the in-flight
    /// fetch out, then re-reads **only the book**: the indexes on hand are untouched by an edit,
    /// and re-asking the source for them is a request each for numbers that did not move.
    /// </summary>
    private async Task RefreshAfterChangeAsync(bool report)
    {
        while (_busy)
        {
            await Task.Delay(120);
        }

        if (_busy || Portfolio.Holdings.Count == 0)
        {
            return;
        }

        _busy = true;

        try
        {
            using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(90));

            var session = await IntradayPnl.LoadAsync(
                Services.Http, Services.Stocks, BookRows(),
                BookTrades(), null, cancellation.Token,
                Fees(), Portfolio.Settled);

            Adopt(session, [.. _indexes], _indexes.Count);
        }
        catch (OperationCanceledException)
        {
            // The next fetch or tick asks again.
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

    // ---- fees --------------------------------------------------------------------------

    /// <summary>What it costs to trade, as the four boxes currently read — the same schedule the
    /// intraday page computes from the same stored rates.</summary>
    /// <summary>
    /// Both bills: the mainland's four rates and the Connect's two.
    ///
    /// The Hong Kong side asks only for what a broker sets — the rate and the floor — because every
    /// other line on a 港股通 ticket is a statutory charge with a published rate (stamp duty, the
    /// exchange's trading fee, the SFC and AFRC levies, CCASS settlement) and belongs in code, not
    /// in a settings box the reader has to look up.
    /// </summary>
    private FeeTable Fees() => new(
        new FeeSchedule(
            Read(FeeCommission, FeeSchedule.Mainland.Commission),
            Read(FeeMinimum, FeeSchedule.Mainland.Minimum),
            Read(FeeStamp, FeeSchedule.Mainland.Stamp),
            Read(FeeTransfer, FeeSchedule.Mainland.Transfer)),
        new HongKongFees(
            Read(FeeKongCommission, HongKongFees.Connect.Commission),
            Read(FeeKongMinimum, HongKongFees.Connect.Minimum)));

    /// <summary>
    /// A rate box's value, falling back when it has not got one. `NaN` is what a NumberBox holds
    /// while it is empty or half-typed — reading that as zero would drop every fee mid-edit.
    /// </summary>
    private static double Read(NumberBox box, double fallback) =>
        double.IsFinite(box.Value) ? box.Value : fallback;

    private void OnFeeChanged(object sender, NumberBoxValueChangedEventArgs e)
    {
        if (_prefs.Restoring || _shared.Restoring)
        {
            return;
        }

        SavePreferences();

        _feeTimer.Stop();
        _feeTimer.Start();
    }

    private async void OnFeeSettled(object? sender, object e)
    {
        _feeTimer.Stop();

        // The indexes did not move; only the book's arithmetic did.
        await RefreshAfterChangeAsync(report: false);
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

        // The same closing-baseline sync the intraday page runs: the 港股通 book's baseline
        // becomes the curve's final frame, the mainland book never moves. Whichever page the
        // reader is watching when the day ends is the one that writes it. The progress test
        // stands beside the index one because this renderer's index ramp can sit a sample short
        // of the last while the playhead itself is already at the end.
        if (!_adopting &&
            _scope is PortfolioScope.WithKong &&
            _session is { Moments.Count: > 0 } live &&
            (progress >= 0.999 || index >= live.Moments.Count - 1) &&
            !ReferenceEquals(_synced, live))
        {
            _synced = live;
            Ledger.SyncKongClose(live);
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
        _span ?? (_session is { } session && DateOnly.TryParse(session.Day, out var day)
            ? (day, day)
            : null);

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
        _shared.Restoring = true;

        AutoRefresh.IsOn = _prefs.GetBool("Auto", true);

        // The book is shared with the intraday page, so the scope is too: whichever page the
        // reader switched it on is the one both open with.
        _scope = _shared.GetInt("Scope", 0) == 1 ? PortfolioScope.WithKong : PortfolioScope.AShare;
        ScopeCombo.SelectedIndex = (int)_scope;

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

        // The switches and rates the intraday page also reads, from the same stored values —
        // whatever that page last saved is what this page opens with.
        IndexTopCheck.IsChecked = _prefs.GetBool("IndexOnTop", false);
        MaskCheck.IsChecked = _prefs.GetBool("MaskNames", false);

        CrossCheck.IsChecked = _shared.GetBool("CrossSafeRight", false);
        MascotCheck.IsChecked = _shared.GetBool("Mascot", false);
        DynamicAxisCheck.IsChecked = _shared.GetBool("DynamicAxis", false);
        LunchCheck.IsChecked = _shared.GetBool("Lunch", true);

        FeeCommission.Value = _shared.GetDouble("FeeCommission", FeeSchedule.Mainland.Commission);
        FeeMinimum.Value = _shared.GetDouble("FeeMinimum", FeeSchedule.Mainland.Minimum);
        FeeStamp.Value = _shared.GetDouble("FeeStamp", FeeSchedule.Mainland.Stamp);
        FeeTransfer.Value = _shared.GetDouble("FeeTransfer", FeeSchedule.Mainland.Transfer);
        FeeKongCommission.Value = _shared.GetDouble("FeeKongCommission", HongKongFees.Connect.Commission);

        // A new key, not a new default: the old "FeeKongMinimum" was written down at five dollars
        // by any reader who touched any other setting on this page, and a stored five would keep
        // overriding the corrected floor for ever. Renaming the key is what lets the hundred apply.
        FeeKongMinimum.Value = _shared.GetDouble("FeeKongFloor", HongKongFees.Connect.Minimum);

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;
        _shared.Restoring = false;

        ApplyScope();
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring || _shared.Restoring)
        {
            return;
        }

        _prefs.Save("Auto", AutoRefresh.IsOn);
        _prefs.Save("Indexes", string.Join(',', Picked().Select(p => p.Code)));
        _prefs.Save("IndexOnTop", IndexTopCheck.IsChecked is true);
        _prefs.Save("MaskNames", MaskCheck.IsChecked is true);

        // The shared settings under the intraday page's prefix, so the two pages read one truth.
        _shared.Save("Scope", (int)_scope);
        _shared.Save("CrossSafeRight", CrossCheck.IsChecked is true);
        _shared.Save("Mascot", MascotCheck.IsChecked is true);
        _shared.Save("DynamicAxis", DynamicAxisCheck.IsChecked is true);
        _shared.Save("Lunch", LunchCheck.IsChecked is true);

        _shared.Save("FeeCommission", Read(FeeCommission, FeeSchedule.Mainland.Commission));
        _shared.Save("FeeMinimum", Read(FeeMinimum, FeeSchedule.Mainland.Minimum));
        _shared.Save("FeeStamp", Read(FeeStamp, FeeSchedule.Mainland.Stamp));
        _shared.Save("FeeTransfer", Read(FeeTransfer, FeeSchedule.Mainland.Transfer));
        _shared.Save("FeeKongCommission", Read(FeeKongCommission, HongKongFees.Connect.Commission));
        _shared.Save("FeeKongFloor", Read(FeeKongMinimum, HongKongFees.Connect.Minimum));

        VideoSettings.Save(_prefs);
    }
}
