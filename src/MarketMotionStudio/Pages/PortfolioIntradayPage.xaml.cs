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

    /// <summary>
    /// The three headline treatments, in the order the page offers them.
    ///
    /// The keys keep their <c>.Content</c> suffix because these lines are not set through
    /// <c>x:Uid</c>: the menu is filled in code, and <see cref="Strings.Get"/> reads the dotted
    /// name as a path — a key with the suffix left off resolves to nothing and the menu comes out
    /// reading <c>[PortfolioPnlTitlePlain]</c>.
    /// </summary>
    private static readonly (TitleSkin Skin, string Key)[] Skins =
    [
        (TitleSkin.Plain, "PortfolioPnlTitlePlain.Content"),
        (TitleSkin.Gilded, "PortfolioPnlTitleGilded.Content"),
        (TitleSkin.Engraved, "PortfolioPnlTitleEngraved.Content"),
    ];

    /// <summary>The headline colour the reader picked, as <c>#RRGGBB</c>; empty means
    /// "whichever this treatment comes with".</summary>
    private string _titleColour = string.Empty;

    /// <summary>True while the page is setting the picker's own colour, so the change it raises
    /// on itself is not read back as a choice.</summary>
    private bool _painting;

    private PortfolioSession? _session;

    /// <summary>
    /// The span actually drawn, whichever door it came in by.
    ///
    /// Kept because the frame's own label is written for a reader and cannot be parsed back into
    /// two dates reliably — <c>10/30</c> reads as a day under one Windows calendar and as nothing
    /// under another, and the exporter names files from these.
    /// </summary>
    private (DateOnly From, DateOnly To)? _span;

    /// <summary>
    /// Whether the next session to land should park on its first minute rather than its last.
    ///
    /// Set when the reader picks a different range and consumed once, by <see cref="Adopt"/>: a
    /// refresh of the same range keeps the playhead (that is what a background re-read is for), but
    /// a new question deserves the picture at its beginning instead of its end.
    /// </summary>
    private bool _parkAtStart;

    /// <summary>
    /// Which book the page is reading: the mainland holdings alone, or those plus the Hong Kong
    /// positions held through 港股通.
    ///
    /// **It decides more than which rows are drawn.** The Hong Kong side has no snapshot behind
    /// it, so a past day cannot be rebuilt for it — which is why this scope forces the page onto
    /// today and hides the span picker rather than answering a week with a curve built from
    /// nothing. Switching it switches the baseline underneath as well, the two books being two
    /// different mornings' figures.
    /// </summary>
    private PortfolioScope _scope = PortfolioScope.AShare;

    /// <summary>
    /// The session whose closing figures have already been written into the 港股通 baseline.
    ///
    /// Reference comparison, not a flag: a fresh session (a thirty-second auto-refresh, a range
    /// re-read) is a new object and earns its own sync, while the frames after the last on the
    /// same session — every scrub and redraw that lands on the closing frame — must not rewrite
    /// the file each time. Only the 港股通 book is synced; see <see cref="Ledger.SyncKongClose"/>.
    /// </summary>
    private PortfolioSession? _synced;

    /// <summary>
    /// True while <see cref="Adopt"/> is parking the playhead, so the closing-baseline sync does
    /// not read a background refresh as the end of an animation.
    ///
    /// **A parked frame is not an ending.** A thirty-second auto-refresh that lands while the
    /// playhead happens to sit on the last frame re-shows that frame — and a sync wired to "the
    /// final frame is showing" would rewrite the baseline with it, clobbering an initial position
    /// the reader had imported seconds earlier (实测：导入 888 股，一轮刷新后回到收盘股数). The
    /// reader-driven ends — a playback that runs to completion, a scrub to the close — leave this
    /// false, and those are the endings the baseline follows.
    /// </summary>
    private bool _adopting;

    /// <summary>
    /// The returns history behind the picture, while a span rather than a day is on screen.
    ///
    /// <see cref="SpanFrame.ToSession"/> has already written it into <see cref="_session"/>, so
    /// nothing reads this to draw. It is kept because two other figures ask it different
    /// questions — the export's file name wants its own days, and the index half of the
    /// double-screen page wants the same axis — and both deserve the object rather than a copy.
    /// </summary>
    private ReturnHistory? _history;

    /// <summary>
    /// What the reader asked for, before the snapshot had its say.
    ///
    /// Kept only to be compared with what was drawn: a request for a year against a snapshot taken
    /// this morning answers with one day, and a page showing "10/30" without saying why would read
    /// as broken rather than as bounded.
    /// </summary>
    private DateOnly? _asked;

    /// <summary>The renderer the preview is drawing with, so the list can ask it where "now" is.</summary>
    private PortfolioPnlRenderer? _ticking;

    /// <summary>
    /// Which sample the list was last rebuilt for.
    ///
    /// Playback calls back sixty times a second and a session is 242 samples, so rebuilding on
    /// every callback would rebuild the whole item list four times a second for a number that has
    /// not changed since the last one. The list is rebuilt when the *sample* moves, and at that
    /// rate it is the list that moves with the picture.
    /// </summary>
    private int _listed = int.MinValue;

    /// <summary>Guards against a timer tick landing on top of a fetch already in flight.</summary>
    private bool _busy;

    /// <summary>
    /// Set when the book itself has just been edited by hand, cleared by the next
    /// <see cref="Adopt"/>.
    ///
    /// The list prefers the session's per-minute moments over the stored book, and the moments
    /// were built from the book as it was **before** the edit — showing them after an edit would
    /// put the old numbers straight back up (实测：改成 777，关掉对话框，列表还是 100). With the
    /// flag on, the list reads the stored book — the figures the reader just typed — and the
    /// replay semantics come back when the re-fetch has rebuilt the session around the new book.
    /// </summary>
    private bool _bookDirty;

    /// <summary>
    /// Waits for the typing in a fee box to stop.
    ///
    /// `ValueChanged` fires on every keystroke, and each load is a request per holding — so the
    /// rate is applied when the reader stops rather than while they are still writing "0.1".
    /// </summary>
    private readonly DispatcherTimer _feeTimer = new() { Interval = TimeSpan.FromSeconds(0.8) };

    public PortfolioIntradayPage()
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

        foreach (var (skin, key) in Skins)
        {
            // The tag carries the skin rather than its position in the menu, so a treatment
            // added in the middle cannot silently become another one.
            TitleSkinCombo.Items.Add(new ComboBoxItem { Content = Strings.Get(key), Tag = (int)skin });
        }

        RestorePreferences();
        ApplyPreviewSettings();
        RefreshBook();

        // Bound after the restore rather than inside it: the picker's own remembered value arrives
        // before this line, and a change arriving from it is not the reader asking for anything.
        SpanPicker.Bind(_prefs);
        SpanPicker.Changed += OnRangeChanged;

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

            var renderer = new PortfolioPnlRenderer(
                session, plan,
                crossSafeRight: CrossCheck.IsChecked is true,
                mascot: MascotCheck.IsChecked is true,
                dynamicAxis: DynamicAxisCheck.IsChecked is true,
                lunchBreak: LunchCheck.IsChecked is true,
                skin: SelectedSkin(),
                titleColour: ChosenTitleColour())
            {
                Title = title,
                ShowTitle = showTitle,
            };

            Preview.Renderer = renderer;
            _ticking = renderer;
        }
        else
        {
            _stage.Title = title.Length > 0 ? title : Strings.Get("PortfolioPnlTitle");
            _stage.ShowTitle = showTitle;
            Preview.Renderer = _stage;
            _ticking = null;
        }

        VideoSettings.TitlePlaceholder = Strings.Get("PortfolioPnlTitle");

        var ready = _session is { Samples.Count: > 1 };

        CoverButton.IsEnabled = ready;
        ExportButton.IsEnabled = ready;
        PlayButton.IsEnabled = ready;

        // Through `ShowMoment` rather than a bare `Redraw`: a switch rebuilds the renderer, and
        // the list has to be read off the same minute the new one is drawing.
        ShowMoment(Preview.Progress);
    }

    /// <summary>
    /// Rebuilds the book's list from the stored holdings — as they stand at the minute the
    /// preview is drawing.
    /// </summary>
    /// <param name="index">
    /// Which of the session's minutes to ask. Negative (or a session with no minutes) reads the
    /// closing figures: the book's own shares, and the profit the day ended with. Those two never
    /// went together — a reader watching the 09:35 sale go past saw the position behind it stay
    /// at 5,900 shares — and the point of putting the fills on a clock is that the position moves.
    /// </param>
    private void RefreshBook(int index = -1)
    {
        var rows = new List<HoldingRow>();

        var live = !_bookDirty ? _session : null;

        var moment = live is { Moments.Count: > 0 } ticking
            ? ticking.Moments[index < 0
                ? ticking.Moments.Count - 1
                : Math.Min(index, ticking.Moments.Count - 1)]
            : null;

        // **At the head of the range the list answers with the previous close, not with the first
        // sample.** A range begins on a morning, and the position the reader recognises as "where I
        // started" is the one the book held when the *previous* session ended — every fill before it
        // applied, none of the first day's applied yet. The first sample is a minute later and can
        // already carry a 09:30 fill, which is why the engine hands over the opening book separately
        // rather than letting the list borrow whatever the axis happened to start on.
        if (live is { Opening.Count: > 0 } span && index <= 0)
        {
            moment = new PnlMoment(
                -1,
                span.Opening!,
                span.OpeningCosts ?? span.Opening!,
                new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase),
                new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase));
        }

        var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var holding in BookRows())
        {
            seen.Add(holding.Code);

            var priced = _session?.Holdings.FirstOrDefault(h =>
                string.Equals(h.Code, holding.Code, StringComparison.OrdinalIgnoreCase));

            // The minute being drawn when there is one; the stored book when there is not. The
            // cost comes from the same minute, because a sale moves it — 中望软件's 700 shares at
            // 33.448 cost 300 shares at 14.444 by the close, and showing the morning's figure
            // beside the evening's share count would be a row that never existed.
            var shares = moment is not null && moment.Shares.TryGetValue(holding.Code, out var held)
                ? held
                : holding.Shares;

            var cost = moment is not null && moment.Costs.TryGetValue(holding.Code, out var paid)
                ? paid
                : holding.Cost;

            var money = (holding.IsHongKong ? "HK$" : "¥")
                + cost.ToString("0.###", CultureInfo.InvariantCulture);

            // Sold out is a state the list has to be able to say out loud. The row stays where it
            // is — dropping it would relayout the list under the reader's eye mid-animation — and
            // "0 股" on its own reads like a typo rather than like the sale that happened at
            // 09:40. The cost goes with the shares: the diluted figure on a position of zero is a
            // zero, and a zero is not what the row used to cost.
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
        // fill that opens one mid-session (顺丰 at 13:55, 公牛 at 14:56) exists in the moments
        // alone — and a list that iterates the book never grows a row for it, so the curve
        // announces the 买入 and the list sits there unmoved (实测：播放过 13:55，列表 8 行原样).
        // From its first fill's minute onward the position gets a row of its own, appended at
        // the bottom so no row the reader is watching changes place; if the day later sells it
        // flat the row stays and reads 已清仓, the same rule the book's own rows follow.
        if (moment is not null && _session is { } session)
        {
            foreach (var trade in session.Trades)
            {
                if (!seen.Add(trade.Code))
                {
                    continue;
                }

                if (moment.Minute < trade.Minute)
                {
                    continue;
                }

                moment.Shares.TryGetValue(trade.Code, out var shares);
                moment.Costs.TryGetValue(trade.Code, out var cost);

                // **A fill that leaves no position is not a row.** A code that appears in the
                // day's journal only as a sale was never held in this book — nothing opened it —
                // and appending it would add a «已清仓» line for a position that never existed
                // (实测：整表导入三行之后，列表多出六行已清仓，正是账本里已经没有的那六只
                // 当天卖出). Rows are positions; a position needs shares behind it.
                if (shares <= 0)
                {
                    continue;
                }

                var money = (trade.Code.StartsWith("hk", StringComparison.OrdinalIgnoreCase) ? "HK$" : "¥")
                    + cost.ToString("0.###", CultureInfo.InvariantCulture);

                var detail = shares > 0
                    ? Strings.Format(
                        "PortfolioPnlRowDetail",
                        shares.ToString("#,##0", CultureInfo.InvariantCulture),
                        money)
                    : Strings.Get("PortfolioPnlRowCleared");

                double? made = moment.Contributions.TryGetValue(trade.Code, out var sofar)
                    ? sofar
                    : null;

                var (text, tone) = made is { } value
                    ? (PortfolioPnlRenderer.Money(value), value >= 0 ? Palette.Emphasis : Palette.Fall)
                    : (string.Empty, Palette.Muted);

                rows.Add(new HoldingRow(InstrumentNames.Display(trade.Code, trade.Name), detail, text, tone));
            }
        }

        // **Any position held at this minute gets a row, wherever it was opened.** The loop above
        // leans on the session's fill list, and a span session carries none — `Trades: []`, because
        // the fills live in the archive rather than in the frame — so a position bought after the
        // range began never reached the list at all: 公牛集团 and 三峡水利 were both bought inside
        // the span and neither was on the page, while the curve had already been carrying them
        // (实测：10/21 各买 100 股，列表里一只都没有). The moments know what is held at the minute
        // being drawn; ask them instead of asking a list that may be empty.
        if (moment is not null && _session is { } holdingSession)
        {
            foreach (var (code, held) in moment.Shares)
            {
                if (held <= 0 || !seen.Add(code))
                {
                    continue;
                }

                moment.Costs.TryGetValue(code, out var paid);

                var name = holdingSession.Holdings
                    .FirstOrDefault(h => string.Equals(h.Code, code, StringComparison.OrdinalIgnoreCase))
                    ?.Name ?? code;

                var money = (code.StartsWith("hk", StringComparison.OrdinalIgnoreCase) ? "HK$" : "¥")
                    + paid.ToString("0.###", CultureInfo.InvariantCulture);

                var detail = Strings.Format(
                    "PortfolioPnlRowDetail",
                    held.ToString("#,##0", CultureInfo.InvariantCulture),
                    money);

                double? made = moment.Contributions.TryGetValue(code, out var sofar) ? sofar : null;

                var (text, tone) = made is { } value
                    ? (PortfolioPnlRenderer.Money(value), value >= 0 ? Palette.Emphasis : Palette.Fall)
                    : (string.Empty, Palette.Muted);

                rows.Add(new HoldingRow(InstrumentNames.Display(code, name), detail, text, tone));
            }
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

                try
                {
                    Adopt(await ReadAsync(progress, cancellation));

                    // No success bar: `Adopt` has just written the same sentence into the line
                    // under the switch, and it stays there. The bar is for what the page cannot
                    // say itself — progress while it reads, and why a read failed.
                    HideStatus();
                }
                catch (InvalidOperationException ex)
                {
                    // What the engine throws when there is no snapshot to measure a span from: an
                    // answer about "further back than this app knows", not a failure of the
                    // network, so it is said as an answer rather than as an error.
                    ShowFailure("PortfolioSpanNoBaseline", ex);
                }
            }, TimeSpan.FromMinutes(2));
        }
        finally
        {
            _busy = false;
        }
    }

    /// <summary>
    /// One read, whichever question is being asked: today's minutes, or a span's own history.
    ///
    /// <para>
    /// **今日 keeps the intraday loader.** It is built for one session and its dial — the live
    /// rail, the fills on their own minutes, the scrubbing clock — and none of that has a meaning
    /// across a month. **Everything else asks <see cref="HoldingReturns"/>**, which reads the
    /// snapshot and the archive and rebuilds the book over the days asked for.
    /// </para>
    ///
    /// <para>
    /// Both answers come back as a <see cref="PortfolioSession"/>, which is why every renderer,
    /// exporter and list on this page is unchanged: a span is <em>fitted</em> to the one shape the
    /// frames draw rather than the frames learning a second one.
    /// </para>
    /// </summary>
    private async Task<PortfolioSession> ReadAsync(
        IProgress<string>? progress, CancellationToken cancellation)
    {
        // **港股通 is a question about today, and only about today.** The Hong Kong book is walked
        // from this morning's opening position through today's fills, both of them in full, and
        // there is no snapshot behind it that could rebuild an earlier day. So this scope answers
        // today however the span picker is left, rather than reading a span into a curve whose
        // Hong Kong rows have no history to be rebuilt from.
        if (_scope is PortfolioScope.WithKong)
        {
            _span = null;
            _history = null;
            _asked = null;

            return await IntradayPnl.LoadAsync(
                Services.Http, Services.Stocks, [.. Portfolio.Holdings],
                [.. Portfolio.Trades], progress, cancellation, Fees(), Portfolio.Settled);
        }

        // **The mainland book leaves the Hong Kong rows out of every one of its parts**: the
        // baseline it opens on, the fills it replays, and the position it draws today. Left in, a
        // Hong Kong fill would move a mainland curve in a currency that curve is not labelled in.
        var mainland = BookRows();
        var mainlandTrades = BookTrades();

        if (SpanPicker.Span == RangeSpan.Today)
        {
            _span = null;
            _history = null;
            _asked = null;

            var live = await IntradayPnl.LoadAsync(
                Services.Http, Services.Stocks, mainland,
                mainlandTrades, progress, cancellation, Fees(), Portfolio.Settled);

            // **A past day is answered by the other machinery.** This loader draws *today's* book
            // walked through *today's* un-folded fills, which is exactly right while the market is
            // open and exactly wrong the morning after: 10/30's fills are folded into the book by
            // then, so a page asked about 10/30 drew a book that already ended at 10/30's close,
            // skipped every fill as settled, and reported 成交 0 笔 with no markers (实测：10/30 买了
            // 11,300 股超图，画面写着 成交 0 笔). The span read rebuilds the opening from the
            // snapshot and replays the archive instead — so a past day is read as a span one day
            // wide, which is what it is.
            var today = DateTime.Today.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

            if (string.Equals(live.Day, today, StringComparison.Ordinal) ||
                !DateOnly.TryParseExact(
                    live.Day, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var past))
            {
                return live;
            }

            var pastHistory = await HoldingReturns.LoadAsync(
                Services.Http, Services.Quotes, past, past, progress, cancellation, Fees(),
                PortfolioScope.AShare);

            _history = pastHistory;
            _span = (pastHistory.From, pastHistory.To);
            _asked = past;

            return SpanFrame.ToSession(pastHistory, SpanFrame.AxisFor(pastHistory));
        }

        if (SpanPicker.Range is not { } wanted)
        {
            // A custom range whose second day has not been picked yet: nothing to read and nothing
            // to say, rather than a read of yesterday-to-the-beginning-of-time.
            throw new InvalidOperationException(Strings.Get("PortfolioSpanIncomplete"));
        }

        var history = await HoldingReturns.LoadAsync(
            Services.Http, Services.Quotes, wanted.From, wanted.To, progress, cancellation, Fees(),
            PortfolioScope.AShare);

        _history = history;
        _span = (history.From, history.To);
        _asked = wanted.From;

        return SpanFrame.ToSession(history, SpanFrame.AxisFor(history));
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

            Adopt(await ReadAsync(null, cancellation.Token));
        }
        catch (OperationCanceledException)
        {
            // The window closed, or the source took longer than a refresh interval. The next
            // tick will ask again.
        }
        catch (InvalidOperationException)
        {
            // Nothing to re-read every thirty seconds, either: a span with no snapshot behind it
            // stays as it is, and the background going quiet about it is the right behaviour —
            // the reader's own fetch already said why.
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

    /// <summary>
    /// The span moved: everything about the picture changes, so it is all read again.
    ///
    /// Not a redraw. Different days are a different set of instruments, a different number of
    /// samples and a different axis — which is also why the page cannot keep the reader's position
    /// in the clip: a scrub set to seventy per cent of a day means nothing when the frame is a year.
    /// </summary>
    /// <summary>
    /// What the chosen book changes about the page, besides the rows it draws: the questions it
    /// can be asked, and the two fields that only one of them has an answer for.
    ///
    /// **The span picker goes away under 港股通 rather than being left to answer.** A Hong Kong
    /// position is walked from this morning's opening through today's fills — there is no
    /// snapshot to rebuild a past day from — so a week asked under this scope would be drawn from
    /// a book that only exists for today. Hidden, the page simply does not offer the question.
    ///
    /// The Connect's two fee boxes go with it: they are about a venue the mainland book does not
    /// trade in, and a box that cannot affect any number on the frame is noise.
    /// </summary>
    private void ApplyScope()
    {
        var kong = _scope is PortfolioScope.WithKong;

        SpanPicker.Visibility = kong ? Visibility.Collapsed : Visibility.Visible;

        FeeKongCommission.Visibility = kong ? Visibility.Visible : Visibility.Collapsed;
        FeeKongMinimum.Visibility = kong ? Visibility.Visible : Visibility.Collapsed;
    }

    /// <summary>
    /// The rows of the book the page is reading: every holding under 港股通, and the mainland ones
    /// alone under the other scope.
    ///
    /// One method rather than a filter at each of the three places that need it — the read, the
    /// list and the dialog — because the three have to agree: a row on the list that the curve
    /// does not carry is a position whose profit never moves, which is the kind of disagreement
    /// that gets reported as a bug in the arithmetic rather than as a row.
    /// </summary>
    private IReadOnlyList<Holding> BookRows() =>
        _scope is PortfolioScope.WithKong
            ? [.. Portfolio.Holdings]
            : [.. Portfolio.Holdings.Where(h => !h.IsHongKong)];

    /// <summary>
    /// The fills of the book the page is reading, in the same terms: all of them under 港股通, and
    /// the ones made on mainland exchanges otherwise.
    /// </summary>
    private IReadOnlyList<PortfolioTrade> BookTrades() =>
        _scope is PortfolioScope.WithKong
            ? [.. Portfolio.Trades]
            : [.. Portfolio.Trades.Where(t => !t.IsHongKong)];

    /// <summary>
    /// The book changed: read the other one, from its first minute.
    /// </summary>
    private async void OnScopeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _scope = ScopeCombo.SelectedIndex == 1 ? PortfolioScope.WithKong : PortfolioScope.AShare;

        ApplyScope();
        SavePreferences();

        // A different book is a different picture, for the same reason a new range is: the
        // playhead was sitting on the live edge of the other one, and "seventy per cent through"
        // means nothing in a span that has just changed length.
        _parkAtStart = true;

        UpdateAutoTimer();

        await FetchAsync(report: true);
    }

    private async void OnRangeChanged(object? sender, EventArgs e)
    {
        UpdateAutoTimer();
        SavePreferences();

        // **A new range is a new story, told from its first minute.** Holding the playhead where it
        // was — on the live edge, almost always — left the list on the range's *closing* figures, so
        // a reader who had just asked for 近一月 saw today's position beside a curve that starts a
        // month earlier. They asked about a span; the list answers with where that span begins, and
        // the playback is then what moves it forward.
        _parkAtStart = true;

        await FetchAsync(report: false);
    }

    /// <summary>Puts a fetched session on the page, keeping the reader's position in the clip.</summary>
    private void Adopt(PortfolioSession session)
    {
        var wasAtEnd = Preview.Progress >= 0.999 || _session is null;

        // **A span opens on its own first minute.** The playhead belongs to the range it was left
        // on, so a page that comes back up on 近一周 — or a reader switching to 近一月 — would
        // otherwise be shown the range's *closing* book beside a curve that begins a week earlier.
        // A re-read of the same range keeps the position, because that is what a background refresh
        // is for: it must not walk the frame out from under whoever is watching it.
        var moved = _session is { } previous &&
            !string.Equals(previous.Day, session.Day, StringComparison.Ordinal);

        var atStart = _parkAtStart || (session.IsSpan && (_session is null || moved));

        _parkAtStart = false;

        _session = session;
        _bookDirty = false;

        // The list is rebuilt from the new session at whatever minute is on screen, so the cache
        // of "which minute is it showing" has to be thrown away first — otherwise a re-read that
        // landed on the same minute index leaves the old numbers up.
        _listed = int.MinValue;

        // The flag covers ApplyPreviewSettings as well, not only the park below: it re-shows the
        // current frame through its own ShowMoment call, and with the playhead already on the
        // close that park is indistinguishable from an ending until the flag is up (实测：导入的
        // 基准在一轮自动刷新后回到收盘股数，写它的正是这条路).
        _adopting = true;

        try
        {
            ApplyPreviewSettings();
            RefreshBook();

            // Parked on the live edge: this page's last frame is "now", which is the frame a reader
            // wants after a refresh. A re-read that jumped the preview back to 09:30 would undo the
            // one thing they were watching.
            //
            // A reader who had scrubbed into the middle stays there — including the list, which is
            // rebuilt from the minute they are looking at rather than jumping to the close under it.
            ShowMoment(atStart ? 0 : wasAtEnd ? 1 : Preview.Progress);
        }
        finally
        {
            _adopting = false;
        }

        // The two lines belong together and are written together: this is the number the frame is
        // drawing, said in words, and the minute it was true. Set from here rather than from the
        // fetch button, because every other path to a new session — an import, a background tick
        // — comes through `Adopt` too, and a line that only the button updates lies for the rest
        // of the day.
        SummaryText.Text = Strings.Format(
            session.SlotIsDaily ? "PortfolioPnlFetchedDays" : "PortfolioPnlFetched",
            session.Day,
            session.Samples.Count,
            PortfolioPnlRenderer.Money(session.Last));

        // **Said out loud when the snapshot shortened the range.** The requirement is that a start
        // before the snapshot is pulled forward to it; a reader who asked for a year and got a day
        // is owed the reason, or the page reads as broken rather than as bounded.
        if (_asked is { } asked && _span is { } drawn && drawn.From > asked)
        {
            // **Two different shortenings, two different sentences.** A start pulled forward to
            // the snapshot is the requirement working; a start that begins later because the minute
            // source keeps five sessions is the source's own limit. Saying "aligned to the
            // snapshot" for the second one tells the reader to go and change a setting that would
            // not help (实测：基准日 10-19、请求近一周，起点是 10/26 —— 分时只有 5 天).
            var snapped = Ledger.BaselineDayOf(_scope) == drawn.From;

            SummaryText.Text += "  " + Strings.Format(
                snapped ? "PortfolioSpanTrimmed" : "PortfolioSpanShallow",
                drawn.From.ToString("M/d", CultureInfo.InvariantCulture));
        }

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
    /// A look switch moved: rebuild the renderer and stop there.
    ///
    /// Nothing is re-read, because none of the three changes a number — they change where the same
    /// numbers sit. Re-fetching would cost a request per holding to answer the same thing, and
    /// during a session it would also move the frame under the reader.
    /// </summary>
    private void OnLookChanged(object sender, RoutedEventArgs e)
    {
        ApplyPreviewSettings();
        SavePreferences();
    }

    private void OnTitleSkinChanged(object sender, SelectionChangedEventArgs e)
    {
        // The swatch and the picker are both answerable to the treatment: until a colour is chosen
        // each shows the one this treatment comes with, so switching treatments moves both. A
        // picker left on the previous treatment's colour is worse than a stale swatch — it is the
        // control the reader would then *touch*, and touching it writes the colour it was showing:
        // switch to 镀金, open the picker, nudge it, and the headline turns white.
        PaintPicker();
        PaintSwatch();

        ApplyPreviewSettings();
        SavePreferences();
    }

    private void OnTitleColourChanged(ColorPicker sender, ColorChangedEventArgs args)
    {
        if (_prefs.Restoring || _painting)
        {
            return;
        }

        var ink = args.NewColor;

        _titleColour = string.Format(
            CultureInfo.InvariantCulture, "#{0:X2}{1:X2}{2:X2}", ink.R, ink.G, ink.B);

        PaintSwatch();
        ApplyPreviewSettings();
        SavePreferences();
    }

    /// <summary>
    /// Hands the colour back to the treatment.
    ///
    /// A picker cannot show "nothing chosen": it always has a colour, and once the reader has
    /// touched it that colour is a choice whether they meant it as one or not. So the way back
    /// to "whichever this treatment comes with" has to be a control of its own.
    /// </summary>
    private void OnTitleColourDefault(object sender, RoutedEventArgs e)
    {
        _titleColour = string.Empty;

        PaintPicker();
        PaintSwatch();

        ApplyPreviewSettings();
        SavePreferences();
    }

    private TitleSkin SelectedSkin() =>
        TitleSkinCombo.SelectedItem is ComboBoxItem { Tag: int tag } ? (TitleSkin)tag : TitleSkin.Plain;

    /// <summary>The colour the reader picked, or null when they have not picked one.</summary>
    private Color? ChosenTitleColour()
    {
        var hex = _titleColour;

        if (hex.Length != 7 || hex[0] != '#')
        {
            return null;
        }

        return byte.TryParse(hex[1..3], NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var r)
            && byte.TryParse(hex[3..5], NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var g)
            && byte.TryParse(hex[5..7], NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var b)
            ? Color.FromArgb(255, r, g, b)
            : null;
    }

    private void PaintSwatch() =>
        TitleSwatch.Fill = new SolidColorBrush(ChosenTitleColour() ?? TitleSkins.Default(SelectedSkin()));

    private void PaintPicker()
    {
        _painting = true;

        TitleColour.Color = ChosenTitleColour() ?? TitleSkins.Default(SelectedSkin());

        _painting = false;
    }

    /// <summary>
    /// Runs the timer only while the market is open, the switch is on, and today is what is drawn.
    ///
    /// The clock is the weekday and the session's own hours, coarse on purpose: this is a
    /// polling interval, not a trading calendar, and a holiday simply means the numbers do not
    /// change between two ticks.
    ///
    /// A span excludes itself, because polling every thirty seconds for a month that closed six
    /// weeks ago costs the source a request per holding and answers with yesterday's same numbers
    /// forever — and worse, it would quietly redraw a picture the reader had left alone.
    /// </summary>
    private void UpdateAutoTimer()
    {
        var now = DateTime.Now;
        var minute = (now.Hour * 60) + now.Minute;

        // 港股通 is drawn for today however the span picker is left — the picker is hidden under
        // it — so the timer reads it as a day rather than as a span.
        var open = AutoRefresh.IsOn &&
                   (_scope is PortfolioScope.WithKong || SpanPicker.Span == RangeSpan.Today) &&
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

    /// <summary>
    /// Refreshes the session after the book or the journal changed underneath it.
    ///
    /// **The wait matters.** <see cref="SilentRefreshAsync"/> quietly returns when a fetch is
    /// already in flight — the right answer for a timer tick, and exactly the wrong one here: the
    /// in-flight fetch is holding a snapshot taken **before** the change, so skipping means the
    /// session never learns about the new trades or the new book, and a playback run afterwards
    /// walks a day whose fills never reach the list (实测：导入后立刻播放，列表不动). So this
    /// waits the in-flight one out and then fetches for real.
    /// </summary>
    private async Task RefreshAfterChangeAsync(bool report)
    {
        while (_busy)
        {
            await Task.Delay(120);
        }

        await SilentRefreshAsync(report);
    }

    private async void OnManage(object sender, RoutedEventArgs e)
    {
        if (App.Window is not { } window)
        {
            return;
        }

        // **The book the page is reading is the one the dialog edits.** Otherwise a reader who
        // switched to 港股通 and pressed 管理持仓 would correct the mainland rows and file them
        // against a snapshot the page has stopped reading.
        var dialog = new PortfolioDialog(null, _scope) { XamlRoot = XamlRoot };

        await Dialogs.ShowAsync(dialog);

        // Whatever was on the stage was drawn from the book that just changed. Dropped rather
        // than left standing, for the reason every other page drops its series when its
        // parameters move: a frame of nine holdings under a list of eight is a plausible
        // picture of the wrong thing.
        //
        // The list is rebuilt **from the stored book** here — the moment override is switched off
        // by `_bookDirty` — because the moments on hand were built from the book as it was before
        // the edit, and showing them would put the old numbers straight back up.
        _bookDirty = true;
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

        // **The dialog does all of it.** Both imports — the day's list and the whole record —
        // apply their own rows while it is open, because the archive is on the dialog and a table
        // that does not move when rows are added to it is worse than no table. What is left here
        // is the part the dialog cannot do: the session on screen was built before the import, and
        // a playback started on it would walk a day whose fills never reach the list.
        if (dialog.ArchiveChanged)
        {
            await RefreshAfterChangeAsync(report: true);
        }
    }

    /// <summary>
    /// The day an import is stamped with: **the day the page is drawing**, not the day the clock
    /// says it is.
    ///
    /// The page draws the last session that traded, and before the market opens that is not
    /// today — it is yesterday. Filling the dialog with `DateTime.Today` then stamps the fills
    /// with a day nothing has traded on, so an import the dialog reports as "已导入 5 笔" lands
    /// where the reader cannot see it: the curve does not move, the header's count stays at zero,
    /// and nothing on the page says why. The picker is filled in with this day and the reader can
    /// still change it — a screenshot of Monday's fills really can be imported on Tuesday.
    /// </summary>
    private DateOnly ImportDay() =>
        _session is { Day.Length: > 0 } session && DateOnly.TryParse(session.Day, out var day)
            ? day
            : DateOnly.FromDateTime(DateTime.Today);

    /// <summary>
    /// The span the picture draws, for the file names.
    ///
    /// Read from <see cref="_span"/> when a span was fetched, because the frame's own label is
    /// written to be read by a person — <c>10/16–10/30</c> — and parsing that back into two dates
    /// asks `DateOnly.TryParse` to guess which calendar wrote it.
    /// </summary>
    private (DateOnly From, DateOnly To)? RangeDays() =>
        _span ?? (_session is { } session && DateOnly.TryParse(session.Day, out var day)
            ? (day, day)
            : null);

    /// <summary>The one day this page draws, or the span it draws, for the file names.</summary>
    private (DateOnly From, DateOnly To)? Range() => RangeDays();

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

    /// <summary>
    /// Moves the preview and the scrub bar together — and the book's list with them.
    ///
    /// The list is the picture in words, so it cannot be one step behind it: at 09:35 the curve
    /// is drawn on 3,000 shares of 超图软件 because the other 5,900 were sold, and a list still
    /// reading 5,900 would have the reader counting shares that are not there.
    /// </summary>
    private void ShowMoment(double progress)
    {
        Preview.Progress = progress;

        Scrub.ValueChanged -= OnScrub;
        Scrub.Value = progress;
        Scrub.ValueChanged += OnScrub;

        // Per sample, not per frame: sixty callbacks a second over 242 samples would rebuild the
        // item list four times a second to show the same numbers.
        var index = _ticking?.ShownIndex(progress) ?? -1;

        if (index != _listed)
        {
            _listed = index;
            RefreshBook(index);
        }

        // **The 港股通 book's baseline is where the curve ends, not where the reader filed it.**
        // Reaching the final frame — by playing there or by scrubbing there — is the day being
        // over, so the book's next session starts from this one's close. Only that scope: the
        // mainland baseline is one fixed morning the spans measure from, and an animation ending
        // on a different day's close must never move it. The progress test stands beside the
        // index one because the double-screen renderer's index ramp can sit a sample short of the
        // last while the playhead itself is already at the end.
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

    private void RestorePreferences()
    {
        _prefs.Restoring = true;

        // The mainland book is what the page opens on: the app is pointed at the A-share market
        // and the account behind it is an A-share one, so the Hong Kong rows are the addition
        // rather than the default and asking for them is the choice.
        _scope = _prefs.GetInt("Scope", 0) == 1 ? PortfolioScope.WithKong : PortfolioScope.AShare;
        ScopeCombo.SelectedIndex = (int)_scope;

        AutoRefresh.IsOn = _prefs.GetBool("Auto", true);

        CrossCheck.IsChecked = _prefs.GetBool("CrossSafeRight", false);
        MascotCheck.IsChecked = _prefs.GetBool("Mascot", false);
        DynamicAxisCheck.IsChecked = _prefs.GetBool("DynamicAxis", false);

        // On by default: it is what the day looks like, and the other three switches are off
        // because they are additions to it rather than subtractions.
        LunchCheck.IsChecked = _prefs.GetBool("Lunch", true);

        _titleColour = _prefs.GetString("TitleColour", string.Empty);
        TitleSkinCombo.SelectedIndex = _prefs.GetInt("TitleSkin", 0);

        // The mainland's own figures unless the reader has set their own. The box is filled
        // rather than left blank: a blank one reads as "nothing is charged", which is the one
        // answer here that cannot be right for anybody with a broker.
        FeeCommission.Value = _prefs.GetDouble("FeeCommission", FeeSchedule.Mainland.Commission);
        FeeMinimum.Value = _prefs.GetDouble("FeeMinimum", FeeSchedule.Mainland.Minimum);
        FeeStamp.Value = _prefs.GetDouble("FeeStamp", FeeSchedule.Mainland.Stamp);
        FeeTransfer.Value = _prefs.GetDouble("FeeTransfer", FeeSchedule.Mainland.Transfer);
        FeeKongCommission.Value = _prefs.GetDouble("FeeKongCommission", HongKongFees.Connect.Commission);
        FeeKongMinimum.Value = _prefs.GetDouble("FeeKongFloor", HongKongFees.Connect.Minimum);

        PaintPicker();
        PaintSwatch();

        VideoSettings.Restore(_prefs);

        _prefs.Restoring = false;

        ApplyScope();
    }

    private void SavePreferences()
    {
        if (_prefs.Restoring)
        {
            return;
        }

        _prefs.Save("Scope", (int)_scope);
        _prefs.Save("Auto", AutoRefresh.IsOn);

        _prefs.Save("CrossSafeRight", CrossCheck.IsChecked is true);
        _prefs.Save("Mascot", MascotCheck.IsChecked is true);
        _prefs.Save("DynamicAxis", DynamicAxisCheck.IsChecked is true);
        _prefs.Save("Lunch", LunchCheck.IsChecked is true);
        _prefs.Save("TitleSkin", TitleSkinCombo.SelectedIndex);
        _prefs.Save("TitleColour", _titleColour);

        _prefs.Save("FeeCommission", Read(FeeCommission, FeeSchedule.Mainland.Commission));
        _prefs.Save("FeeMinimum", Read(FeeMinimum, FeeSchedule.Mainland.Minimum));
        _prefs.Save("FeeStamp", Read(FeeStamp, FeeSchedule.Mainland.Stamp));
        _prefs.Save("FeeTransfer", Read(FeeTransfer, FeeSchedule.Mainland.Transfer));
        _prefs.Save("FeeKongCommission", Read(FeeKongCommission, HongKongFees.Connect.Commission));
        _prefs.Save("FeeKongFloor", Read(FeeKongMinimum, HongKongFees.Connect.Minimum));

        VideoSettings.Save(_prefs);
    }

    /// <summary>What it costs to trade, as the four boxes on the page currently read.</summary>
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
    /// A rate box's value, falling back when it has not got one.
    ///
    /// `NaN` is what a `NumberBox` holds while it is empty or half-typed — including the moment
    /// before the reader finishes clearing it to type something else. Reading that as zero would
    /// drop every fee for as long as the box was mid-edit, and the day's profit would jump up
    /// and come back down again for no reason the page explains.
    /// </summary>
    private static double Read(NumberBox box, double fallback) =>
        double.IsFinite(box.Value) ? box.Value : fallback;

    /// <summary>
    /// A rate changed. Remembered at once, applied when the typing stops.
    /// </summary>
    private void OnFeeChanged(object sender, NumberBoxValueChangedEventArgs e)
    {
        // Setting the boxes from the stored preferences raises this too, and making that a
        // change would re-read the day on every visit to the page.
        if (_prefs.Restoring)
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

        await FetchAsync(report: false);
    }

    private void OnCancel(object sender, RoutedEventArgs e) => CancelRunning();
}
